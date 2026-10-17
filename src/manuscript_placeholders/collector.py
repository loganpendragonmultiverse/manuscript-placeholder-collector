from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from itertools import islice
from pathlib import Path
from typing import Any

import regex

from . import __version__
from .docx_reader import read_docx


@dataclass(frozen=True, slots=True)
class Block:
    number: int
    text: str
    section: str
    location: str = ""


@dataclass(frozen=True, slots=True)
class Placeholder:
    category: str
    marker: str
    section: str
    block: int
    context: str
    location: str = ""
    start: int = 0
    end: int = 0
    fingerprint: str = ""
    start_line: int = 0
    start_column: int = 0
    end_line: int = 0
    end_column: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


PATTERNS = (
    (
        "Research",
        re.compile(r"\[(?:RESEARCH|VERIFY|CHECK|SOURCE)\b[^\]]*\]", re.IGNORECASE),
    ),
    (
        "Missing names",
        re.compile(r"\[(?:NAME|TITLE|SURNAME|PLACE|LOCATION)\b[^\]]*\]", re.IGNORECASE),
    ),
    (
        "Revision notes",
        re.compile(
            r"\[(?:TODO|FIX|REWRITE|REVISE|EXPAND|CUT)\b[^\]]*\]", re.IGNORECASE
        ),
    ),  # placeholder-detector: ignore -- detector vocabulary
    (
        "Revision notes",
        re.compile(r"\b(?:TODO|FIXME|TK|XXX)\s*[:\-]?\s*[^\n]{0,140}", re.IGNORECASE),
    ),  # placeholder-detector: ignore -- detector vocabulary
    (
        "Insertions",
        re.compile(r"<(?:insert|add|describe|write)\b[^>]*>", re.IGNORECASE),
    ),
    ("Uncertain text", re.compile(r"(?<!\?)\?{3,}(?!\?)")),
    ("Bracketed notes", re.compile(r"\[[A-Z][A-Z0-9 _'\-:,.!?]{2,}\]")),
)


def collect(
    path: Path,
    extra_patterns: tuple[str, ...] = (),
    *,
    docx_tables: bool = False,
    docx_comments: bool = False,
    docx_footnotes: bool = False,
    docx_headers: bool = False,
    docx_footers: bool = False,
    docx_endnotes: bool = False,
    docx_textboxes: bool = False,
    revisions: str = "current",
    multiline: bool = False,
    coverage: dict[str, object] | None = None,
    document_id: str | None = None,
) -> tuple[Placeholder, ...]:
    source = path.expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"Not a file: {source}")
    identity = document_id or hashlib.sha256(str(source).encode()).hexdigest()
    inventory: dict[str, object] = {} if coverage is None else coverage
    options = {
        "tables": docx_tables,
        "comments": docx_comments,
        "footnotes": docx_footnotes,
        "headers": docx_headers,
        "footers": docx_footers,
        "endnotes": docx_endnotes,
        "textboxes": docx_textboxes,
    }
    suffix = source.suffix.casefold()
    if suffix != ".docx" and any(options.values()):
        raise ValueError("DOCX structure options apply only to .docx inputs")
    if revisions not in ("current", "include-revisions"):
        raise ValueError("Unknown revision policy")
    if source.stat().st_size > 100 * 1024 * 1024:
        raise ValueError("Input exceeds 100 MB safety limit")
    if suffix == ".docx":
        blocks = [
            Block(n, text, section, location)
            for n, (location, text, section) in enumerate(
                read_docx(source, options, inventory, revisions=revisions), 1
            )
        ]
    elif suffix == ".doc":
        blocks = _legacy_doc_blocks(source)
        inventory.update(
            format="doc",
            converter=_converter_description(),
            scope="converter body text only",
            complete_selected_scope=False,
        )
    elif suffix == ".epub":
        from .epub import read_epub

        blocks = [Block(*item) for item in read_epub(source, inventory)]
    elif suffix in {".txt", ".md", ".markdown"}:
        blocks = _text_blocks(source)
        inventory.update(
            format="text", encoding="utf-8-sig; strict", complete_selected_scope=True
        )
        if multiline:
            combined: list[Block] = []
            chunk: list[Block] = []
            for block in blocks:
                if chunk and (
                    block.number != chunk[-1].number + 1
                    or block.section != chunk[-1].section
                ):
                    combined.append(
                        Block(
                            chunk[0].number,
                            "\n".join(b.text for b in chunk),
                            chunk[0].section,
                            chunk[0].location,
                        )
                    )
                    chunk = []
                chunk.append(block)
            if chunk:
                combined.append(
                    Block(
                        chunk[0].number,
                        "\n".join(b.text for b in chunk),
                        chunk[0].section,
                        chunk[0].location,
                    )
                )
            blocks = combined
    else:
        raise ValueError(
            "Supported formats are .txt, .md, .markdown, .docx, .doc, and .epub"
        )
    inventory.update(
        multiline=multiline,
        scanner_version=__version__,
        custom_patterns=list(extra_patterns),
    )

    patterns: list[tuple[str, Any]] = list(PATTERNS)
    for index, raw in enumerate(extra_patterns, 1):
        try:
            if len(raw) > 2048:
                raise ValueError("Custom pattern exceeds 2048-character limit")
            compiled = regex.compile(raw, regex.IGNORECASE)
            if compiled.search("") is not None:
                raise ValueError("Custom patterns must not match empty text")
            patterns.append(("Custom", compiled))
        except (re.error, regex.error) as exc:
            raise ValueError(f"Invalid custom pattern {index}: {exc}") from exc

    deadline = time.monotonic() + 5
    found: list[Placeholder] = []
    seen: set[tuple[int, int, int, str]] = set()
    opener = re.compile(
        r"\[(?:RESEARCH|VERIFY|CHECK|SOURCE|NAME|TITLE|SURNAME|PLACE|LOCATION|TODO|FIX|REWRITE|REVISE|EXPAND|CUT)\b|<(?:insert|add|describe|write)\b",
        re.IGNORECASE,
    )
    for block in blocks:
        for start in opener.finditer(block.text):
            closing = "]" if start.group(0).startswith("[") else ">"
            end = block.text.find(closing, start.start(), start.start() + 8192)
            if end == -1 and len(block.text) - start.start() > 8192:
                raise ValueError(
                    "Drafting marker exceeds 8192-character bound; no complete report produced"
                )
        for category, pattern in patterns:
            if category == "Custom" and time.monotonic() > deadline:
                raise ValueError("Custom patterns exceeded five-second scan budget")
            try:
                matches = (
                    list(islice(pattern.finditer(block.text, timeout=0.1), 10001))
                    if category == "Custom"
                    else list(islice(pattern.finditer(block.text), 10001))
                )
            except TimeoutError as exc:
                raise ValueError(
                    "Custom pattern exceeded 100 ms processing limit"
                ) from exc
            if len(matches) > 10000 or len(found) > 100000:
                raise ValueError("Finding count exceeds bounded report limit")
            for match in matches:
                if match.start() == match.end():
                    raise ValueError("Custom patterns must not match empty text")
                if category != "Custom" and any(
                    item.block == block.number
                    and item.start <= match.start() < item.end
                    for item in found
                ):
                    continue
                policy = (
                    "custom:" + pattern.pattern if category == "Custom" else "builtin"
                )
                key = (block.number, match.start(), match.end(), policy)
                if key in seen:
                    continue
                seen.add(key)
                location = block.location or f"block[{block.number}]"
                fingerprint = hashlib.sha256(
                    f"{identity}\0{location}\0{match.start()}\0{match.group(0)}\0{policy}".encode()
                ).hexdigest()
                found.append(
                    Placeholder(
                        category,
                        match.group(0).strip(),
                        block.section,
                        block.number,
                        _context(block.text, match.start(), match.end()),
                        location,
                        match.start(),
                        match.end(),
                        fingerprint,
                        block.number + block.text[: match.start()].count("\n"),
                        len(block.text[: match.start()].rsplit("\n", 1)[-1]) + 1,
                        block.number + block.text[: match.end()].count("\n"),
                        len(block.text[: match.end()].rsplit("\n", 1)[-1]) + 1,
                    )
                )
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
            blocks.append(Block(number, line, section, f"line[{number}]"))
    return blocks


def _docx_blocks(path: Path) -> list[Block]:
    return [
        Block(n, text, section, location)
        for n, (location, text, section) in enumerate(read_docx(path, {}, {}), 1)
    ]


def _legacy_doc_blocks(path: Path) -> list[Block]:
    for tool in ("antiword", "catdoc"):
        executable = shutil.which(tool)
        if executable:
            completed = subprocess.run(
                [executable, str(path)], capture_output=True, check=False, timeout=30
            )
            if completed.returncode != 0:
                message = completed.stderr.decode("utf-8", errors="replace").strip()
                raise ValueError(
                    f"{tool} could not read the DOC file: {message or 'unknown conversion error'}"
                )
            try:
                text = completed.stdout.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(
                    f"{tool} output is not valid UTF-8; no report produced"
                ) from exc
            return _text_content_blocks(text)

    office = shutil.which("soffice") or shutil.which("libreoffice")
    if office:
        with tempfile.TemporaryDirectory(prefix="manuscript-doc-") as temporary:
            office_result = subprocess.run(
                [
                    office,
                    "-env:UserInstallation=" + (Path(temporary) / "profile").as_uri(),
                    "--headless",
                    "--convert-to",
                    "docx",
                    "--outdir",
                    temporary,
                    str(path),
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            converted = Path(temporary) / f"{path.stem}.docx"
            if office_result.returncode != 0 or not converted.is_file():
                message = office_result.stderr.strip() or office_result.stdout.strip()
                raise ValueError(
                    f"LibreOffice could not convert the DOC file: {message or 'unknown conversion error'}"
                )
            return _docx_blocks(converted)

    raise ValueError(
        "Legacy .doc files need antiword, catdoc, or LibreOffice installed and available on PATH"
    )


def _text_content_blocks(text: str) -> list[Block]:
    return [
        Block(number, line.strip(), "Document")
        for number, line in enumerate(text.splitlines(), 1)
        if line.strip()
    ]


def _converter_description() -> dict[str, str]:
    for name in ("antiword", "catdoc", "soffice", "libreoffice"):
        executable = shutil.which(name)
        if executable:
            try:
                run = subprocess.run(
                    [executable, "--version"],
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
                version = (
                    (run.stdout or run.stderr)
                    .decode("utf-8", errors="replace")
                    .splitlines()
                )
                return {
                    "name": name,
                    "version": version[0][:200] if version else "not reported",
                }
            except (OSError, subprocess.TimeoutExpired):
                return {"name": name, "version": "unavailable"}
    return {"name": "unavailable", "version": "unavailable"}


def _context(text: str, start: int, end: int) -> str:
    left = max(0, start - 90)
    right = min(len(text), end + 90)
    excerpt = text[left:right].strip()
    return ("…" if left else "") + excerpt + ("…" if right < len(text) else "")
