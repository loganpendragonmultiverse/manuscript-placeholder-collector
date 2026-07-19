from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

from docx import Document


@dataclass(frozen=True, slots=True)
class Block:
    number: int
    text: str
    section: str


@dataclass(frozen=True, slots=True)
class Placeholder:
    category: str
    marker: str
    section: str
    block: int
    context: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


PATTERNS = (
    ("Research", re.compile(r"\[(?:RESEARCH|VERIFY|CHECK|SOURCE)\b[^\]]*\]", re.I)),
    ("Missing names", re.compile(r"\[(?:NAME|TITLE|SURNAME|PLACE|LOCATION)\b[^\]]*\]", re.I)),
    ("Revision notes", re.compile(r"\[(?:TODO|FIX|REWRITE|REVISE|EXPAND|CUT)\b[^\]]*\]", re.I)),  # placeholder-detector: ignore -- detector vocabulary
    ("Revision notes", re.compile(r"\b(?:TODO|FIXME|TK|XXX)\s*[:\-]?\s*[^\n]{0,140}", re.I)),  # placeholder-detector: ignore -- detector vocabulary
    ("Insertions", re.compile(r"<(?:insert|add|describe|write)\b[^>]*>", re.I)),
    ("Uncertain text", re.compile(r"(?<!\?)\?{3,}(?!\?)")),
    ("Bracketed notes", re.compile(r"\[[A-Z][A-Z0-9 _'\-:,.!?]{2,}\]")),
)


def collect(path: Path, extra_patterns: tuple[str, ...] = ()) -> tuple[Placeholder, ...]:
    source = path.expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"Not a file: {source}")
    if source.suffix.casefold() == ".docx":
        blocks = _docx_blocks(source)
    elif source.suffix.casefold() == ".doc":
        blocks = _legacy_doc_blocks(source)
    elif source.suffix.casefold() == ".epub":
        blocks = _epub_blocks(source)
    elif source.suffix.casefold() in {".txt", ".md", ".markdown"}:
        blocks = _text_blocks(source)
    else:
        raise ValueError("Supported formats are .txt, .md, .markdown, .docx, .doc, and .epub")

    patterns = list(PATTERNS)
    for index, raw in enumerate(extra_patterns, 1):
        try:
            patterns.append(("Custom", re.compile(raw, re.I)))
        except re.error as exc:
            raise ValueError(f"Invalid custom pattern {index}: {exc}") from exc

    found: list[Placeholder] = []
    seen: set[tuple[int, int, int]] = set()
    for block in blocks:
        for category, pattern in patterns:
            for match in pattern.finditer(block.text):
                key = (block.number, match.start(), match.end())
                if key in seen:
                    continue
                seen.add(key)
                found.append(Placeholder(category, match.group(0).strip(), block.section, block.number, _context(block.text, match.start(), match.end())))
    found.sort(key=lambda item: (item.block, item.category, item.marker.casefold()))
    return tuple(found)


def _text_blocks(path: Path) -> list[Block]:
    blocks: list[Block] = []
    section = "Document"
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        stripped = line.strip()
        heading = re.match(r"^#{1,6}\s+(.+)$", stripped)
        if heading:
            section = heading.group(1).strip()
        if stripped:
            blocks.append(Block(number, stripped, section))
    return blocks


def _docx_blocks(path: Path) -> list[Block]:
    document = Document(path)
    blocks: list[Block] = []
    section = "Document"
    for number, paragraph in enumerate(document.paragraphs, 1):
        text = paragraph.text.strip()
        if not text:
            continue
        if paragraph.style and paragraph.style.name.casefold().startswith("heading"):
            section = text
        blocks.append(Block(number, text, section))
    return blocks


def _legacy_doc_blocks(path: Path) -> list[Block]:
    for tool in ("antiword", "catdoc"):
        executable = shutil.which(tool)
        if executable:
            completed = subprocess.run([executable, str(path)], capture_output=True, check=False)
            if completed.returncode != 0:
                message = completed.stderr.decode("utf-8", errors="replace").strip()
                raise ValueError(f"{tool} could not read the DOC file: {message or 'unknown conversion error'}")
            text = completed.stdout.decode("utf-8", errors="replace")
            return _text_content_blocks(text)

    office = shutil.which("soffice") or shutil.which("libreoffice")
    if office:
        with tempfile.TemporaryDirectory(prefix="manuscript-doc-") as temporary:
            completed = subprocess.run(
                [office, "--headless", "--convert-to", "docx", "--outdir", temporary, str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
            converted = Path(temporary) / f"{path.stem}.docx"
            if completed.returncode != 0 or not converted.is_file():
                message = completed.stderr.strip() or completed.stdout.strip()
                raise ValueError(f"LibreOffice could not convert the DOC file: {message or 'unknown conversion error'}")
            return _docx_blocks(converted)

    raise ValueError("Legacy .doc files need antiword, catdoc, or LibreOffice installed and available on PATH")


def _text_content_blocks(text: str) -> list[Block]:
    return [Block(number, line.strip(), "Document") for number, line in enumerate(text.splitlines(), 1) if line.strip()]


class _DocumentTextParser(HTMLParser):
    BLOCK_TAGS = {"p", "li", "blockquote", "pre", "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.current: str | None = None
        self.depth = 0
        self.buffer: list[str] = []
        self.blocks: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.BLOCK_TAGS:
            if self.current is None:
                self.current = tag
                self.depth = 1
                self.buffer = []
            else:
                self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self.current is None or tag not in self.BLOCK_TAGS:
            return
        self.depth -= 1
        if self.depth == 0:
            text = " ".join("".join(self.buffer).split())
            if text:
                self.blocks.append((self.current, text))
            self.current = None
            self.buffer = []

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.buffer.append(data)


def _epub_blocks(path: Path) -> list[Block]:
    try:
        with zipfile.ZipFile(path) as archive:
            entries = [item for item in archive.infolist() if not item.is_dir()]
            if len(entries) > 10_000 or sum(item.file_size for item in entries) > 100 * 1024 * 1024:
                raise ValueError("EPUB exceeds the 10,000-entry or 100 MB uncompressed safety limit")
            container = ElementTree.fromstring(archive.read("META-INF/container.xml"))
            rootfile = container.find(".//{*}rootfile")
            if rootfile is None or not rootfile.get("full-path"):
                raise ValueError("EPUB container does not identify a package document")
            package_name = _safe_epub_name(rootfile.get("full-path", ""))
            package = ElementTree.fromstring(archive.read(package_name))
            base = PurePosixPath(package_name).parent
            manifest = {
                item.get("id", ""): _safe_epub_name(str(base / item.get("href", "")))
                for item in package.findall(".//{*}manifest/{*}item")
                if item.get("id") and item.get("href") and item.get("media-type") in {"application/xhtml+xml", "text/html"}
            }
            ordered = [manifest[item.get("idref", "")] for item in package.findall(".//{*}spine/{*}itemref") if item.get("idref", "") in manifest]
            blocks: list[Block] = []
            section = "Document"
            number = 0
            for item_name in ordered:
                parser = _DocumentTextParser()
                parser.feed(archive.read(item_name).decode("utf-8", errors="replace"))
                for tag, text in parser.blocks:
                    number += 1
                    if tag.startswith("h"):
                        section = text
                    blocks.append(Block(number, text, section))
            return blocks
    except (KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        raise ValueError(f"EPUB cannot be read: {exc}") from exc


def _safe_epub_name(name: str) -> str:
    decoded = unquote(urlsplit(name).path)
    pure = PurePosixPath(decoded.replace("\\", "/"))
    if pure.is_absolute() or not pure.parts or ".." in pure.parts:
        raise ValueError(f"EPUB contains an unsafe path: {name}")
    return str(pure)


def _context(text: str, start: int, end: int) -> str:
    left = max(0, start - 90)
    right = min(len(text), end + 90)
    excerpt = text[left:right].strip()
    return ("…" if left else "") + excerpt + ("…" if right < len(text) else "")
