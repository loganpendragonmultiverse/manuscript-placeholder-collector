import os
from pathlib import Path

from manuscript_placeholders.cli import main


def test_missing_output_parent_is_actionable_without_partial_ledger(
    tmp_path: Path, capsys
):
    source = tmp_path / "draft.md"
    source.write_text("TODO: verify bridge", encoding="utf-8")
    ledger = tmp_path / "ledger.json"
    assert (
        main(
            [
                str(source),
                "--output",
                str(tmp_path / "missing/report.json"),
                "--ledger-output",
                str(ledger),
            ]
        )
        == 2
    )
    assert "output directory does not exist" in capsys.readouterr().err
    assert not ledger.exists()
    assert source.read_text() == "TODO: verify bridge"


def test_output_write_failure_is_actionable(tmp_path: Path, capsys, monkeypatch):
    source = tmp_path / "draft.md"
    source.write_text("TODO: verify bridge", encoding="utf-8")
    original = os.open

    def fail_report(path, flags, *args, **kwargs):
        if flags & os.O_EXCL and Path(path).name == "report.json":
            raise PermissionError("fixture write denied")
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", fail_report)
    assert main([str(source), "--output", str(tmp_path / "report.json")]) == 2
    assert "fixture write denied" in capsys.readouterr().err
