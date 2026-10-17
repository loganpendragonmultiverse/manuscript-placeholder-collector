# Manuscript Placeholder Collector

## Current release 1.2.2

Convert legacy DOC files with a disposable LibreOffice profile.

The LibreOffice fallback creates a disposable profile inside its conversion directory. It does not reuse an open desktop session or require changing your normal LibreOffice configuration. Antiword and catdoc priority is unchanged.

## Current release 1.2.1

Handle report destination failures without a traceback and make DOCX scan boundaries consistent.

Reports and ledgers require distinct new paths in existing directories. The collector never creates missing parent folders or replaces an existing report. Optional table/comment/footnote scans remain explicit; headers and footers are not claimed.

Writers leave themselves notes while drafting: `[RESEARCH THIS]`, `TODO: fix the argument`, `<insert description>`, `TK`, or a row of question marks. Manuscript Placeholder Collector gathers those scattered reminders into one private revision checklist.

## Supported input

- Plain text (`.txt`)
- Markdown (`.md`, `.markdown`)
- Microsoft Word (`.docx`)
- Legacy Microsoft Word (`.doc`) through a locally installed `antiword`, `catdoc`, or LibreOffice reader
- EPUB (`.epub`)

Markdown headings, Word heading styles, and EPUB heading elements are preserved as section names so each result retains useful context.

## Install

Python 3.10 or newer is required.

```bash
python -m venv .venv
python -m pip install -e .
```

## Usage

```bash
manuscript-placeholders novel.docx
manuscript-placeholders backlist-title.doc
manuscript-placeholders reader-copy.epub
manuscript-placeholders novel.md --format markdown --output revision-checklist.md
manuscript-placeholders novel.docx --format html --output placeholders.html
manuscript-placeholders notes.txt --pattern "FLAGME" --format json --output findings.json
```

Built-in categories include research, missing names, revision notes, insertions, uncertain text, and general uppercase bracketed notes.

## Privacy

The manuscript stays on the computer. No text is uploaded, and no AI or external API is used. Reports necessarily contain the matched note and nearby manuscript context; treat exported reports with the same privacy as the manuscript.

## Limitations

- Legacy `.doc` support depends on `antiword`, `catdoc`, or LibreOffice being installed locally and available on `PATH`; modern `.docx` does not need that extra tool.
- DOCX tables, comments and footnotes are scanned only when their explicit flags are enabled. Headers, footers, endnotes, text boxes and tracked-change interpretation remain outside the supported scan.
- Natural-language notes that do not match a marker require a custom regular expression.
- The collector does not rewrite the original manuscript or decide when an item is resolved.

## Development

```bash
python -m pip install -e . pytest build
python -m pytest
python -m build
```

## Project status

Current maintenance preserves local-only processing, stable location evidence and the explicit supported-structure boundary.

Released under the [MIT License](LICENSE).

## More open-source projects

This project is part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Browse the catalog for other released tools, source repositories, live demos, and downloads.

## Version 1.2.0: reviewed improvements

Repair formatting and add opt-in DOCX table/comment/footnote scanning with source locations and a private resolution ledger with baseline comparisons.

```bash
manuscript-placeholders draft.docx --docx-tables --docx-comments --docx-footnotes --format json --output review.json --ledger-output resolution.json
```

DOCX body paragraphs remain the default. Optional structures identify XML part, table/row/cell/paragraph or comment/footnote IDs, plus character offsets within extracted paragraph text. Text files retain line positions. Reports explicitly list enabled/skipped optional structures; headers, footers, endnotes, text boxes and legacy DOC converter behavior are not expanded. --ledger reads a version 1 items object keyed by finding fingerprint with open/resolved/ignored status and a private note. --ledger-output writes a new ledger preserving old entries. --baseline compares a previous fingerprinted JSON report. Fingerprints include source location, marker offset and marker text, so moved text can appear new. A missing marker does not prove an issue was resolved. Source manuscripts and existing outputs remain untouched.
