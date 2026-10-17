# Changelog

## 1.2.2 - 2026-10-17

- Use a per-conversion temporary LibreOffice profile instead of the caller’s normal profile
- Work when the caller cannot create a normal LibreOffice user profile
- Cover isolated-profile arguments and unchanged source bytes

## 1.2.1 - 2026-10-17

- Return actionable errors for missing output directories and report write failures
- Preserve new-file-only report and ledger writes
- Correct optional DOCX structure documentation and current lint compatibility

## 1.2.0 - 2026-09-07

- Repair formatting and add opt-in DOCX table/comment/footnote scanning with source locations and a private resolution ledger with baseline comparisons.
- Added regression coverage for the audited behavior and invalid inputs.

## 1.1.0 - 2026-07-18

- Added section-aware EPUB ingestion in publication spine order.
- Added legacy `.doc` ingestion through locally installed `antiword`, `catdoc`, or LibreOffice readers.
- Expanded format validation, tests, package metadata, privacy guidance, and usage documentation.

## 1.0.0 - 2026-07-18

- Added local placeholder collection for text, Markdown, and DOCX manuscripts.
- Added section-aware research, name, revision, insertion, uncertainty, and bracket-note categories.
- Added custom regular expressions and text, Markdown, JSON, and static HTML reports.
