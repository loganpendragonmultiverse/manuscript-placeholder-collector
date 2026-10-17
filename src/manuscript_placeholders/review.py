"""Opt-in DOCX structures and private author resolution records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def extra_docx_blocks(
    path: Path,
    *,
    tables: bool,
    comments: bool,
    footnotes: bool,
    headers: bool = False,
    footers: bool = False,
    endnotes: bool = False,
) -> list[tuple[str, str]]:
    from .docx_reader import read_docx

    records = read_docx(
        path,
        {
            "tables": tables,
            "comments": comments,
            "footnotes": footnotes,
            "headers": headers,
            "footers": footers,
            "endnotes": endnotes,
        },
        {},
    )
    return [
        (location, text)
        for location, text, _ in records
        if not location.startswith("word/document.xml/paragraph[")
    ]


def review_findings(
    findings: list[dict[str, Any]],
    ledger: Any,
    baseline: Any = None,
    *,
    provenance: dict[str, Any] | None = None,
    allow_cross_document: bool = False,
) -> dict[str, Any]:
    if (
        not isinstance(ledger, dict)
        or ledger.get("version", 1) not in (1, 2)
        or not isinstance(ledger.get("items", {}), dict)
    ):
        raise ValueError("resolution ledger must be version 1 with an items object")
    if baseline is not None and (
        not isinstance(baseline, dict)
        or not isinstance(baseline.get("placeholders"), list)
    ):
        raise ValueError("baseline must contain a placeholders array")
    coverage_changed = False
    if provenance is not None:
        for label, prior in (("ledger", ledger), ("baseline", baseline)):
            if not prior:
                continue
            metadata = prior.get("provenance", {}) if isinstance(prior, dict) else {}
            if not metadata and label == "baseline" and isinstance(prior, dict):
                nested = prior.get("review", {})
                if not isinstance(nested, dict):
                    raise ValueError("baseline review metadata must be an object")
                metadata = nested.get("provenance", {})
            if not isinstance(metadata, dict):
                raise TypeError(f"{label} provenance must be an object")
            has_content = bool(
                prior.get("items") if label == "ledger" else prior.get("placeholders")
            )
            if (
                has_content
                and metadata.get("document_id") != provenance["document_id"]
                and not allow_cross_document
            ):
                raise ValueError(
                    f"{label} belongs to another document or lacks identity; use --allow-cross-document only after reviewing the source"
                )
            if (
                label == "baseline"
                and metadata.get("coverage") != provenance["coverage"]
            ):
                coverage_changed = True
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
    output_ledger: dict[str, Any] = {"version": 1, "items": items}
    if provenance is not None:
        output_ledger.update(version=2, provenance=provenance)
    totals = {
        status: sum(items[identifier]["status"] == status for identifier in current)
        for status in ("open", "resolved", "ignored")
    }
    return {
        "ledger": output_ledger,
        "provenance": provenance,
        "status_totals": totals,
        "coverage_changed": coverage_changed,
        "unverified_removals": sorted(old - current) if coverage_changed else [],
        "not_currently_observed": sorted(set(statuses) - current),
        "comparison": {
            "new": sorted(current - old),
            "no_longer_observed": [] if coverage_changed else sorted(old - current),
            "unchanged": sorted(old & current),
        },
        "note": "Resolution is the author's assertion. A missing marker is not proof that the underlying writing issue was fixed.",
    }
