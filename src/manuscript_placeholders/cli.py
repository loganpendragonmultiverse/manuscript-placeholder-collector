from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter
from pathlib import Path

from .collector import Placeholder, collect


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="manuscript-placeholders", description="Collect manuscript placeholders into a revision checklist.")
    parser.add_argument("manuscript")
    parser.add_argument("--format", choices=("text", "markdown", "json", "html"), default="text")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pattern", action="append", default=[], help="additional regular expression; repeat as needed")
    parser.add_argument("--fail-on-findings", action="store_true")
    args = parser.parse_args(argv)
    try:
        items = collect(Path(args.manuscript), tuple(args.pattern))
    except (OSError, ValueError) as exc:
        print(f"manuscript-placeholders: {exc}", file=sys.stderr)
        return 2
    report = _render(items, args.format, Path(args.manuscript).name)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
        print(f"Wrote {args.format} report to {args.output}")
    else:
        print(report)
    return 1 if args.fail_on_findings and items else 0


def _render(items: tuple[Placeholder, ...], format_name: str, source: str) -> str:
    if format_name == "json":
        return json.dumps({"source": source, "count": len(items), "placeholders": [item.to_dict() for item in items]}, indent=2, ensure_ascii=False) + "\n"
    categories = Counter(item.category for item in items)
    if format_name == "markdown":
        lines = ["# Manuscript placeholder report", "", f"Source: `{source}`  ", f"Open items: **{len(items)}**", ""]
        for category in sorted(categories):
            lines.extend((f"## {category} ({categories[category]})", ""))
            for item in (entry for entry in items if entry.category == category):
                lines.append(f"- [ ] **{item.section} · block {item.block}:** `{item.marker}` — {item.context}")
            lines.append("")
        return "\n".join(lines)
    if format_name == "html":
        cards = "".join(f"<article><p class=\"category\">{html.escape(item.category)}</p><h2>{html.escape(item.marker)}</h2><p>{html.escape(item.context)}</p><small>{html.escape(item.section)} · block {item.block}</small></article>" for item in items) or "<p>No placeholders found.</p>"
        return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Manuscript placeholders</title><style>body{{font:16px/1.55 Georgia,serif;background:#f3eee5;color:#29241f;margin:0}}main{{max-width:900px;margin:auto;padding:3rem 1rem}}article{{background:white;padding:1.25rem;margin:1rem 0;border-left:5px solid #9c552f}}.category,small{{color:#775d4d;font:13px system-ui}}h2{{font-size:1.15rem}}</style></head><body><main><h1>Manuscript placeholder report</h1><p>{html.escape(source)} · {len(items)} open items</p>{cards}</main></body></html>'
    lines = [f"Manuscript placeholders: {len(items)}", f"Source: {source}", ""]
    for item in items:
        lines.extend((f"{item.category.upper()} · {item.section} · block {item.block}", f"  {item.marker}", f"  {item.context}", ""))
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
