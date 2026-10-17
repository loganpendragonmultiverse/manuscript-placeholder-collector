# Testing

Run `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`, and `python -m build`. CI also audits dependencies and runs the supported OS/Python matrix.

## 1.2.0 regression acceptance

Run the complete existing suite plus the new regression fixtures. Confirm the documented command produces the selected output, malformed input remains actionable, and source files remain unchanged. Repair formatting and add opt-in DOCX table/comment/footnote scanning with source locations and a private resolution ledger with baseline comparisons.

## 1.2.1 acceptance

Handle report destination failures without a traceback and make DOCX scan boundaries consistent.

Verify Return actionable errors for missing output directories and report write failures; Preserve new-file-only report and ledger writes; Correct optional DOCX structure documentation and current lint compatibility. Run the full existing quality and build gates; release only through protected PR checks and verified tag artifacts.
