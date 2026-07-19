# Development handoff

## 1.1.0 input-format expansion

- Added EPUB parsing in spine order without uploading or rewriting the book.
- Added legacy `.doc` support through local `antiword`, `catdoc`, or LibreOffice discovery; never bundle or silently download a converter.
- Every format expansion must update package metadata, README support and limitations, tests, changelog, GitHub release copy, repository description/topics, and the Forge catalog together.

The collector is local-only and must never modify manuscripts. New document formats need explicit coverage of skipped structures, malformed files, location semantics, and privacy implications. Do not add remote AI analysis to the core tool.
