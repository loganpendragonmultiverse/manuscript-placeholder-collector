"""Opt-in DOCX structures and private author resolution records."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def extra_docx_blocks(
    path: Path, *, tables: bool, comments: bool, footnotes: bool
) -> list[tuple[str, str]]:
    result = []
    with zipfile.ZipFile(path) as archive:
        if sum(info.file_size for info in archive.infolist()) > 100 * 1024 * 1024:
            raise ValueError("DOCX exceeds 100 MB uncompressed limit")
        if tables:
            document = ET.fromstring(archive.read("word/document.xml"))
            for table_index, table in enumerate(document.iter(W + "tbl"), 1):
                for row_index, row in enumerate(table.findall(W + "tr"), 1):
                    for cell_index, cell in enumerate(row.findall(W + "tc"), 1):
                        for paragraph_index, paragraph in enumerate(
                            cell.findall(W + "p"), 1
                        ):
                            text = "".join(
                                node.text or "" for node in paragraph.iter(W + "t")
                            )
                            result.append(
                                (
                                    f"word/document.xml/table[{table_index}]/row[{row_index}]/cell[{cell_index}]/paragraph[{paragraph_index}]",
                                    text,
                                )
                            )
        for enabled, part, tag in [
            (comments, "comments", "comment"),
            (footnotes, "footnotes", "footnote"),
        ]:
            name = f"word/{part}.xml"
            if enabled and name in archive.namelist():
                document = ET.fromstring(archive.read(name))
                for record in document.findall(W + tag):
                    identifier = record.get(W + "id", "unknown")
                    if record.get(W + "type") in ("separator", "continuationSeparator"):
                        continue
                    for index, paragraph in enumerate(record.iter(W + "p"), 1):
                        text = "".join(
                            node.text or "" for node in paragraph.iter(W + "t")
                        )
                        result.append(
                            (f"{name}/{tag}[{identifier}]/paragraph[{index}]", text)
                        )
    return result


def review_findings(
    findings: list[dict[str, Any]], ledger: Any, baseline: Any = None
) -> dict[str, Any]:
    if (
        not isinstance(ledger, dict)
        or ledger.get("version", 1) != 1
        or not isinstance(ledger.get("items", {}), dict)
    ):
        raise ValueError("resolution ledger must be version 1 with an items object")
    statuses = ledger.get("items", {})
    for identifier, entry in statuses.items():
        if (
            not isinstance(entry, dict)
            or entry.get("status") not in ("open", "resolved", "ignored")
            or not isinstance(entry.get("note", ""), str)
        ):
            raise ValueError(
                f"ledger item {identifier} needs open/resolved/ignored status and a text note"
            )
    items = dict(statuses)
    current = {item["fingerprint"] for item in findings}
    for identifier in sorted(current):
        items.setdefault(identifier, {"status": "open", "note": ""})
    old: set[str] = set()
    if baseline is not None:
        if not isinstance(baseline, dict) or not isinstance(
            baseline.get("placeholders"), list
        ):
            raise ValueError("baseline must contain a placeholders array")
        for item in baseline["placeholders"]:
            if not isinstance(item, dict) or not isinstance(
                item.get("fingerprint"), str
            ):
                raise TypeError("baseline requires fingerprinted findings")
            old.add(item["fingerprint"])
    return {
        "ledger": {"version": 1, "items": items},
        "not_currently_observed": sorted(set(statuses) - current),
        "comparison": {
            "new": sorted(current - old),
            "no_longer_observed": sorted(old - current),
            "unchanged": sorted(old & current),
        },
        "note": "Resolution is the author's assertion. A missing marker is not proof that the underlying writing issue was fixed.",
    }
