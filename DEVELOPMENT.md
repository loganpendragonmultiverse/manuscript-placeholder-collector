# Development handoff

## 1.1.0 input-format expansion

- Added EPUB parsing in spine order without uploading or rewriting the book.
- Added legacy `.doc` support through local `antiword`, `catdoc`, or LibreOffice discovery; never bundle or silently download a converter.
- Every format expansion must update package metadata, README support and limitations, tests, changelog, GitHub release copy, repository description/topics, and the Forge catalog together.

The collector is local-only and must never modify manuscripts. New document formats need explicit coverage of skipped structures, malformed files, location semantics, and privacy implications. Do not add remote AI analysis to the core tool.

## 1.2.0 improvement session

Repair formatting and add opt-in DOCX table/comment/footnote scanning with source locations and a private resolution ledger with baseline comparisons.

DOCX body paragraphs remain the default. Optional structures identify XML part, table/row/cell/paragraph or comment/footnote IDs, plus character offsets within extracted paragraph text. Text files retain line positions. Reports explicitly list enabled/skipped optional structures; headers, footers, endnotes, text boxes and legacy DOC converter behavior are not expanded. --ledger reads a version 1 items object keyed by finding fingerprint with open/resolved/ignored status and a private note. --ledger-output writes a new ledger preserving old entries. --baseline compares a previous fingerprinted JSON report. Fingerprints include source location, marker offset and marker text, so moved text can appear new. A missing marker does not prove an issue was resolved. Source manuscripts and existing outputs remain untouched.

Local formatting, lint, strict types and regression tests pass. Public release completion requires the protected CI/CodeQL matrix, tagged artifacts and matching Forge catalog/detail deployment.

## 1.2.1 acceptance

Handle report destination failures without a traceback and make DOCX scan boundaries consistent.

Reports and ledgers require distinct new paths in existing directories. The collector never creates missing parent folders or replaces an existing report. Optional table/comment/footnote scans remain explicit; headers and footers are not claimed.

## 1.2.2 acceptance

Convert legacy DOC files with a disposable LibreOffice profile.

The LibreOffice fallback creates a disposable profile inside its conversion directory. It does not reuse an open desktop session or require changing your normal LibreOffice configuration. Antiword and catdoc priority is unchanged.

## 1.3.0 acceptance

Find drafting notes in DOCX headers and footers when you choose to include them.

Use --docx-headers and --docx-footers to scan all referenced header/footer XML parts, including first/even parts even when their display switches are off. Shared parts are scanned once. Add --docx-tables to include paragraphs inside header/footer tables. Locations identify the XML part and paragraph; they do not guess rendered page numbers. Endnotes, text boxes and tracked-change interpretation remain unsupported.
