# Testing

Run `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`, and `python -m build`. CI also audits dependencies and runs the supported OS/Python matrix.

## 1.2.0 regression acceptance

Run the complete existing suite plus the new regression fixtures. Confirm the documented command produces the selected output, malformed input remains actionable, and source files remain unchanged. Repair formatting and add opt-in DOCX table/comment/footnote scanning with source locations and a private resolution ledger with baseline comparisons.

## 1.2.1 acceptance

Handle report destination failures without a traceback and make DOCX scan boundaries consistent.

Verify Return actionable errors for missing output directories and report write failures; Preserve new-file-only report and ledger writes; Correct optional DOCX structure documentation and current lint compatibility. Run the full existing quality and build gates; release only through protected PR checks and verified tag artifacts.

## 1.2.2 acceptance

Convert legacy DOC files with a disposable LibreOffice profile.

Verify Use a per-conversion temporary LibreOffice profile instead of the caller’s normal profile; Work when the caller cannot create a normal LibreOffice user profile; Cover isolated-profile arguments and unchanged source bytes. Run the full existing quality and build gates; release only through protected PR checks and verified tag artifacts.

## 1.3.0 acceptance

Find drafting notes in DOCX headers and footers when you choose to include them.

Verify Add --docx-headers and --docx-footers with source-part and paragraph locations; Scan referenced default, first-page and even-page parts once even when shared by sections; Keep body-only defaults, explicit table coverage and original manuscript bytes. Run the full existing quality and build gates; release only through protected PR checks and verified tag artifacts.

## 1.3.1 acceptance

Recover cleanly when writing a report and its companion file fails.

Verify Stage every file before reserving new output names and never overwrite existing destinations; Roll back only unchanged files created by the failed command, preserving concurrent changes; Keep stdout delivery inside the output operation and test permission failures, collisions and retry. Run the full existing quality and build gates; release only through protected PR checks and verified tag artifacts.

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
