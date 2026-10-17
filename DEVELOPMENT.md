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

## 1.3.1 acceptance

Recover cleanly when writing a report and its companion file fails.

Report and ledger/decision/history files are prepared together. If an ordinary write fails, the command removes only unchanged files it created, so you can fix the destination and retry. Existing files, source inputs and files changed by another process are preserved. Outputs are UTF-8 with LF endings. This handles ordinary write failures; it does not promise a multi-file transaction through power loss or recall text already read from stdout.

## 1.4.0 endnote acceptance

Use `--docx-endnotes` to scan normal records in the declared local endnotes XML part. XML-part, canonical numeric ID and paragraph positions remain deterministic across repeated scans and table toggles. Paragraph positions count empty paragraphs and skipped table/text-box paragraphs. System separators are excluded; text boxes and tracked-change interpretation remain unsupported.

Verify body-only defaults, custom local part paths, separate footnote IDs, empty and split-run text, source hashes, stable fingerprints, table opt-in, malformed/missing/external parts, duplicate/invalid IDs, unmatched references and all report formats. Exercise report/ledger collisions, partial writes, stdout failure and real non-admin destination failure followed by retry. Do not claim physical-platform acceptance from CI.

## 1.5.0 bounded completeness acceptance

Verify one story-aware DOCX walker across content controls, custom-XML wrappers, text boxes and selected linked stories, with unique paragraph locations and no duplicate AlternateContent text. Verify current/include-revisions views, tabs/breaks, hidden labels and cached field results; never evaluate embedded content. Resolve local optional part relationships with ID/reference validation. Report actual selected scope, unsupported linked content and available reference anchors; reject inapplicable DOCX flags.

Verify EPUB div/list/table text, spine order including non-linear entries, local fallback chains, declared encodings and resource/element locations. Unsupported reading resources produce explicit partial coverage. Reject malformed/unsafe/encrypted packages and duplicate names before parsing. Exercise actual expanded-size rejection.

Verify document-scoped fingerprints and version-2 report/ledger provenance, explicit legacy/cross-document reuse, changed-coverage unverified removals and accurate current status totals. Check bounded multiline positions and overlap deduplication; reject empty and pathological custom expressions. Check strict decoding, converter timeouts and no partial outputs. Retain ordinary write recovery and source/existing-output protection tests. Run full Ruff, mypy, pytest, build and dependency audit, then installed-wheel acceptance and protected CI. Physical-device certification is not claimed.

## 1.5.1 source provenance guard

Hash source bytes with the existing 100 MB bound before collecting, verify the same bounded hash after collecting, and bind reports to that verified digest. An ordinary edit interleaving must return CLI 2 before report/ledger creation; unchanged input must report its actual SHA-256. Reject oversized input before scan and check streaming growth without loading the whole source. Sources and existing outputs stay unchanged. This guard does not lock files or claim protection against hostile A-B-A changes. Scanner-version evidence uses package metadata.

## 1.5.2 explicit Word visibility labels

Respect OOXML on/off values for explicit vanish properties. Disabled properties must not produce hidden labels; enabled properties label paragraph context, including mixed visible/hidden runs. Preserve all markers, source bytes, revision selection and cached-field handling. Inherited styles and rendered visibility are not resolved.
