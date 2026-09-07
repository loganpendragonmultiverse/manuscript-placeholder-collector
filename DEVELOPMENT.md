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
