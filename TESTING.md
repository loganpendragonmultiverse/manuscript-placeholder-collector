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
