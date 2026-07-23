# Manuscript Placeholder Collector

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
- Word tables, headers, footnotes, comments, and tracked changes are not scanned.
- Natural-language notes that do not match a marker require a custom regular expression.
- The collector does not rewrite the original manuscript or decide when an item is resolved.

## Development

```bash
python -m pip install -e . pytest build
python -m pytest
python -m build
```

## Project status

**Feature complete for v1.1.** Format expansions should preserve local-only processing and stable location evidence.

Released under the [MIT License](LICENSE).

## More open-source projects

This project is part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Browse the catalog for other released tools, source repositories, live demos, and downloads.
