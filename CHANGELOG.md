# Changelog

## 1.4.0 - 2026-10-17

- Add opt-in DOCX endnote scanning with XML-part, endnote-ID and paragraph locations.
- Include source locations and character offsets in plain-text reports as well as structured formats.
- Follow local endnotes relationships, skip separator records and require explicit table scanning.
- Reject ambiguous parts/IDs and missing references before writing outputs; retain paired-output recovery and source preservation.

## 1.3.1 - 2026-10-17

- Stage every file before reserving new output names and never overwrite existing destinations
- Roll back only unchanged files created by the failed command, preserving concurrent changes
- Keep stdout delivery inside the output operation and test permission failures, collisions and retry

## 1.3.0 - 2026-10-17

- Add --docx-headers and --docx-footers with source-part and paragraph locations
- Scan referenced default, first-page and even-page parts once even when shared by sections
- Keep body-only defaults, explicit table coverage and original manuscript bytes

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
