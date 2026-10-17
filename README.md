# Manuscript Placeholder Collector

> ⭐ **Gold Star Project**
> I consider this project complete. Fixes, maintenance and good new ideas are still welcome.
> [About Gold Stars](https://www.loganpendragonforge.com/open-source/?gold=1)

## Gold scope — reviewed for v1.5.2

Gold means no meaningful unfinished contribution is currently identified within this tool's documented purpose: collect recognizable drafting markers from supported local manuscript text into a private revision checklist while preserving source files. The seven reviewed coverage, text extraction, review-provenance and failure-recovery groups are complete in [v1.5.2](https://github.com/loganpendragonmultiverse/manuscript-placeholder-collector/releases/tag/v1.5.2).

The prior v1.5.1 qualification included 111 source tests, 111 tests against the actual tag-built wheel, protected OS/Python CI and CodeQL, independent code review, public artifact digest checks and real non-root LibreOffice conversion with unchanged DOC/DOCX input hashes. These are regression and acceptance checks, not 111 distinct user journeys or physical-device certification.

The boundary remains explicit local text-marker collection. Unsupported embedded or linked content is reported, not silently declared scanned. OCR, rendering, remote fetching, manuscript rewriting and semantic completeness are outside this purpose. Compatibility, security/dependency fixes and further platform testing remain maintenance work; new evidence can reopen this assessment.

## Current release 1.5.2

Word visibility labels respect explicit on/off values: `w:vanish` set to `0`, `false` or `off` no longer labels visible text as hidden. A mixed paragraph is labelled “paragraph contains hidden text”, so the label describes paragraph context rather than claiming that every finding is hidden. This reads explicit XML properties; it does not resolve inherited Word styles or rendered visibility.

Bare marker tokens end at a word boundary, so ordinary words such as Tkinter and Roman numerals such as XXXV are not drafting notes. Whole-token repeated conventions such as TKTK and XXXX remain recognized.

## Previous release 1.5.1

Bind report provenance to the source that was scanned. The CLI hashes the bounded input before scanning and confirms the same hash after collection. If an ordinary edit changes the manuscript during that interval, it exits 2 before writing a report or ledger; save the manuscript and retry. The reported hash belongs to the verified scan input. This is an ordinary edit guard, not a file lock or a hostile change-and-restore guarantee. The 100 MB input limit and read-only source behavior are unchanged.

## Previous release 1.5.0

Collect local drafting markers with explicit source coverage and document-scoped review records. DOCX uses one story walker for body, content controls, custom XML wrappers and opt-in tables, text boxes, comments, footnotes, endnotes, headers and footers. Tabs and breaks are preserved. The current-text view includes insertions/move-to and excludes deletions/move-from; `--revisions include-revisions` includes and labels revision content. Hidden text is included and labelled. Only cached field results are read; fields are never evaluated.

```bash
manuscript-placeholders draft.docx --docx-tables --docx-textboxes --docx-comments --docx-footnotes --docx-endnotes --docx-headers --docx-footers --format json --output review.json --ledger-output ledger.json
manuscript-placeholders draft.md --multiline --format json --output multiline.json
manuscript-placeholders draft.docx --ledger ledger.json --baseline review.json --format html --output next-review.html
```

JSON reports and ledgers use version 2, recording a stable document identity, source SHA-256, scanner version and actual scan coverage. Identity defaults to a hash of the absolute source path; use an explicit private `--document-id` consistently when moving a manuscript. Findings are scoped to that identity. Legacy or cross-document review files require `--allow-cross-document` after deliberate review; imported statuses only apply to matching fingerprints. Coverage changes put missing findings in `unverified_removals`, never imply resolution. Open/resolved/ignored totals describe currently observed findings; `--fail-on-findings` still exits 1 whenever any markers are observed, regardless of ledger status.

EPUB reads structural text in spine order, includes non-linear spine items, honours declared XML encoding, follows supported local fallback chains and reports unsupported resources as partial coverage. Locations identify package, resource and element, not rendered pages. No scripts or remote resources are executed or fetched. DOCX linked unsupported altChunk, glossary and subdocument content is inventoried; absence of findings is never proof a manuscript is complete.

Package preflight rejects duplicate/encrypted entries, over 10,000 entries or over 100 MB expanded content before parsing. Inputs are limited to 100 MB. Legacy converters have a 30-second timeout; their name/version and body-only scope are recorded. Invalid text decoding fails rather than replacing characters silently. Custom patterns use a 100 ms per-block timeout, a five-second aggregate budget, a 2048-character pattern limit and bounded finding counts; empty matches are rejected. Optional text multiline scanning preserves contiguous lines within one Markdown section. Built-in bracket/angle markers have an 8192-character bound; oversized candidate markers fail actionably rather than producing a falsely complete report. Prefix length does not split a short marker.

Sources and existing outputs remain unchanged. Ordinary report/ledger write failures remain retryable; this is not a power-loss transaction. Unsupported/encrypted resources are reported or rejected, never guessed. This is a local text-marker collector, not OCR, a renderer, a revision editor or a semantic completeness checker.

## Previous release 1.4.0


Find drafting notes in DOCX endnotes with `--docx-endnotes`. Normal endnotes in the declared local XML part are scanned once; separator records are skipped. Add `--docx-tables` to include endnote table paragraphs. Reports identify the part, endnote ID and XML paragraph position (including empty and skipped paragraphs), with offsets in the extracted text. These are source locations, not rendered page numbers.

Body-only scanning remains the default. Missing endnote parts, malformed XML, duplicate IDs and unmatched references fail before any report or ledger is written. Existing output files and source manuscripts stay unchanged.

## Updates in 1.3.1

Recover cleanly when writing a report and its companion file fails.

Report and ledger/decision/history files are prepared together. If an ordinary write fails, the command removes only unchanged files it created, so you can fix the destination and retry. Existing files, source inputs and files changed by another process are preserved. Outputs are UTF-8 with LF endings. This handles ordinary write failures; it does not promise a multi-file transaction through power loss or recall text already read from stdout.

## Updates in 1.3.0

Find drafting notes in DOCX headers and footers when you choose to include them.

Use --docx-headers and --docx-footers to scan all referenced header/footer XML parts, including first/even parts even when their display switches are off. Shared parts are scanned once. Add --docx-tables to include paragraphs inside header/footer tables. Locations identify the XML part and paragraph; they do not guess rendered page numbers. Endnotes are available with `--docx-endnotes`; text boxes and explicit revision policies are available in 1.5.0.

## Updates in 1.2.2

Convert legacy DOC files with a disposable LibreOffice profile.

The LibreOffice fallback creates a disposable profile inside its conversion directory. It does not reuse an open desktop session or require changing your normal LibreOffice configuration. Antiword and catdoc priority is unchanged.

## Updates in 1.2.1

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
- DOCX tables, comments and footnotes are scanned only when their explicit flags are enabled. Headers, footers and endnotes require their explicit flags. Text boxes require `--docx-textboxes`; revision policy and actual coverage are documented above.
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

DOCX body paragraphs remain the default. Optional structures identify XML part, table/row/cell/paragraph or comment/footnote IDs, plus character offsets within extracted paragraph text. Text files retain line positions. Reports explicitly list enabled/skipped optional structures; headers and footers are available with the 1.3.0 flags; endnotes are available with `--docx-endnotes`; 1.5.0 adds text boxes and bounded converter provenance. Historical 1.2.0 --ledger reads a version 1 items object keyed by finding fingerprint with open/resolved/ignored status and a private note. --ledger-output writes a new ledger preserving old entries. --baseline compares a previous fingerprinted JSON report. Fingerprints include source location, marker offset and marker text, so moved text can appear new. A missing marker does not prove an issue was resolved. Source manuscripts and existing outputs remain untouched.
