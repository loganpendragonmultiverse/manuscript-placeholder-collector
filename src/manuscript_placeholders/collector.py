from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

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
    elif source.suffix.casefold() in {".txt", ".md", ".markdown"}:
        blocks = _text_blocks(source)
    else:
        raise ValueError("Supported formats are .txt, .md, .markdown, and .docx")

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


def _context(text: str, start: int, end: int) -> str:
    left = max(0, start - 90)
    right = min(len(text), end + 90)
    excerpt = text[left:right].strip()
    return ("…" if left else "") + excerpt + ("…" if right < len(text) else "")
