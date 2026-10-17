"""Bounded local EPUB reading with explicit coverage of spine resources."""

from __future__ import annotations

import codecs
import posixpath
import re
import zipfile
import zlib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

BlockTuple = tuple[int, str, str, str]
_SUPPORTED = {"application/xhtml+xml", "text/html"}
_BOUNDARIES = {
    "address",
    "article",
    "aside",
    "blockquote",
    "div",
    "dl",
    "dt",
    "dd",
    "figure",
    "figcaption",
    "footer",
    "header",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "ul",
    "tr",
}
_VOID = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _resource(href: str, base: str = "") -> str:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or parsed.query:
        raise ValueError(f"EPUB requires a local resource path: {href}")
    decoded = unquote(parsed.path)
    if not decoded or decoded.startswith("/") or "\\" in decoded or "\x00" in decoded:
        raise ValueError(f"EPUB contains an unsafe resource path: {href}")
    result = posixpath.normpath(posixpath.join(base, decoded))
    if result in {".", ".."} or result.startswith("../"):
        raise ValueError(f"EPUB resource escapes the archive: {href}")
    return result


def _preflight(archive: zipfile.ZipFile) -> None:
    entries = archive.infolist()
    if len(entries) > 10_000 or sum(e.file_size for e in entries) > 100 * 1024 * 1024:
        raise ValueError(
            "EPUB exceeds the 10,000-entry or 100 MB expanded safety limit"
        )
    names: set[str] = set()
    for entry in entries:
        name = entry.filename.rstrip("/")
        normalized = _resource(name)
        if normalized != name or normalized in names:
            raise ValueError(
                f"EPUB has duplicate or noncanonical package entries: {name}"
            )
        names.add(normalized)
        if entry.flag_bits & 1:
            raise ValueError(f"EPUB contains an encrypted ZIP entry: {name}")


def _xml(data: bytes, name: str) -> ET.Element:
    # ElementTree honors XML declarations/BOMs. Do not permit custom entities.
    if b"<!ENTITY" in data.upper() or b"<!ENTITY" in data.replace(b"\x00", b"").upper():
        raise ValueError(f"EPUB custom XML entities are unsupported: {name}")
    try:
        return ET.fromstring(data)
    except (ET.ParseError, LookupError, ValueError) as exc:
        raise ValueError(f"EPUB XML cannot be read in {name}: {exc}") from exc


class _HTMLTree(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = ET.Element("html")
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = ET.SubElement(self.stack[-1], tag, {k: v or "" for k, v in attrs})
        if tag not in _VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        parent = self.stack[-1]
        if len(parent):
            parent[-1].tail = (parent[-1].tail or "") + data
        else:
            parent.text = (parent.text or "") + data


def _html(data: bytes, name: str) -> ET.Element:
    # XML is preferred even for text/html; HTML fallback respects declared encoding.
    try:
        return _xml(data, name)
    except ValueError:
        if b"<!ENTITY" in data.upper():
            raise
    encoding = "utf-8-sig"
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        encoding = "utf-16"
    else:
        declaration = re.search(
            rb"(?:encoding\s*=\s*|charset\s*=\s*)[\"']?([A-Za-z0-9._-]+)",
            data[:4096],
            re.IGNORECASE,
        )
        if declaration:
            encoding = declaration.group(1).decode("ascii")
    try:
        text = data.decode(encoding)
    except (UnicodeError, LookupError) as exc:
        raise ValueError(f"EPUB text cannot be decoded in {name}: {exc}") from exc
    parser = _HTMLTree()
    parser.feed(text)
    parser.close()
    return parser.root


def _text_blocks(root: ET.Element) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    buffer: list[str] = []
    section = "Document"

    def flush() -> None:
        text = "".join(buffer).strip(" \r\n\t")
        buffer.clear()
        if text:
            output.append((section, text))

    def walk(node: ET.Element, pre: bool = False) -> None:
        nonlocal section
        tag = _local_name(node.tag)
        if tag in {"script", "style", "head", "template"}:
            return
        boundary = tag in _BOUNDARIES
        heading = tag in {"h1", "h2", "h3", "h4", "h5", "h6"}
        if boundary:
            flush()
        if tag == "br":
            buffer.append("\n")
            return
        if tag in {"td", "th"} and buffer:
            buffer.append("\t")
        pre = pre or tag == "pre"

        def append(value: str | None) -> None:
            if value:
                buffer.append(value if pre else re.sub(r"\s+", " ", value))

        append(node.text)
        start = len(output)
        for child in node:
            walk(child, pre)
            append(child.tail)
        if heading:
            title = "".join(buffer).strip()
            if title:
                section = title
            elif len(output) > start:
                section = output[-1][1]
        if boundary:
            flush()

    bodies = [n for n in root.iter() if _local_name(n.tag) == "body"]
    for body in bodies or [root]:
        walk(body)
    flush()
    return output


def read_epub(path: Path, coverage: dict[str, object]) -> list[BlockTuple]:
    """Read local spine content; mutate coverage with honest unsupported-resource details."""
    resources: list[dict[str, object]] = []
    omitted: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            _preflight(archive)
            container = _xml(
                archive.read("META-INF/container.xml"), "META-INF/container.xml"
            )
            rootfiles = container.findall(".//{*}rootfile")
            if not rootfiles:
                raise ValueError("EPUB container does not identify a package document")
            preferred = next(
                (
                    r
                    for r in rootfiles
                    if r.get("media-type") == "application/oebps-package+xml"
                ),
                rootfiles[0],
            )
            package_name = _resource(preferred.get("full-path", ""))
            package = _xml(archive.read(package_name), package_name)
            base = posixpath.dirname(package_name)
            manifest: dict[str, ET.Element] = {}
            for item in package.findall("./{*}manifest/{*}item"):
                identifier = item.get("id", "")
                if not identifier or identifier in manifest or not item.get("href"):
                    raise ValueError(
                        "EPUB manifest contains a missing/duplicate ID or missing href"
                    )
                manifest[identifier] = item
            spine = package.find("./{*}spine")
            if spine is None or not list(spine):
                raise ValueError("EPUB package has no reading-order spine")
            encrypted: set[str] = set()
            if "META-INF/encryption.xml" in archive.namelist():
                encryption = _xml(
                    archive.read("META-INF/encryption.xml"), "META-INF/encryption.xml"
                )
                encrypted = {
                    _resource(n.get("URI", ""))
                    for n in encryption.findall(".//{*}CipherReference")
                }
            blocks: list[BlockTuple] = []
            for index, ref in enumerate(spine, 1):
                identifier = ref.get("idref", "")
                if identifier not in manifest:
                    raise ValueError(
                        f"EPUB spine references a missing manifest ID: {identifier}"
                    )
                current = identifier
                visited: set[str] = set()
                while True:
                    if current in visited:
                        raise ValueError(
                            f"EPUB fallback chain contains a cycle: {identifier}"
                        )
                    visited.add(current)
                    resolved_item = manifest.get(current)
                    if resolved_item is None:
                        raise ValueError(
                            f"EPUB fallback references a missing manifest ID: {current}"
                        )
                    media = resolved_item.get("media-type", "")
                    if media in _SUPPORTED:
                        name = _resource(resolved_item.get("href", ""), base)
                        if name in encrypted:
                            raise ValueError(
                                f"EPUB reading resource is encrypted: {name}; use an unencrypted export"
                            )
                        data = archive.read(name)
                        root = (
                            _xml(data, name)
                            if media == "application/xhtml+xml"
                            else _html(data, name)
                        )
                        for number, (section, text) in enumerate(_text_blocks(root), 1):
                            blocks.append(
                                (
                                    len(blocks) + 1,
                                    text,
                                    section,
                                    f"{name}/spine[{index}]/block[{number}]",
                                )
                            )
                        resources.append(
                            {
                                "id": identifier,
                                "resolved_id": current,
                                "path": name,
                                "media_type": media,
                                "status": "read",
                                "linear": ref.get("linear", "yes"),
                            }
                        )
                        break
                    fallback = resolved_item.get("fallback")
                    if not fallback:
                        message = f"spine item {identifier}: unsupported media type {media or '(missing)'}"
                        omitted.append(message)
                        resources.append(
                            {
                                "id": identifier,
                                "media_type": media,
                                "status": "unsupported",
                            }
                        )
                        break
                    current = fallback
            coverage.update(
                {
                    "epub_status": "partial" if omitted else "complete",
                    "epub_resources": resources,
                    "epub_omissions": omitted,
                    "epub_policy": "All spine entries including non-linear entries; local resources only.",
                }
            )
            return blocks
    except (
        OSError,
        KeyError,
        zipfile.BadZipFile,
        RuntimeError,
        NotImplementedError,
        zlib.error,
        RecursionError,
    ) as exc:
        raise ValueError(
            f"EPUB cannot be read; check that it is an intact, unencrypted package: {exc}"
        ) from exc
