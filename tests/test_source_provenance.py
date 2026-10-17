import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from manuscript_placeholders import __version__, cli


def test_edit_during_collection_fails_before_report_or_ledger(
    tmp_path, monkeypatch, capsys
):
    source = tmp_path / "draft.txt"
    source.write_text("[TODO original scanned marker]")
    report = tmp_path / "report.json"
    ledger = tmp_path / "ledger.json"
    real_collect = cli.collect

    def interleaving(*args, **kwargs):
        findings = real_collect(*args, **kwargs)
        source.write_text("New text saved by another editor")
        return findings

    monkeypatch.setattr(cli, "collect", interleaving)
    assert (
        cli.main(
            [
                str(source),
                "--format",
                "json",
                "--output",
                str(report),
                "--ledger-output",
                str(ledger),
            ]
        )
        == 2
    )
    assert not report.exists() and not ledger.exists()
    captured = capsys.readouterr()
    assert "changed during scan" in captured.err and not captured.out
    assert source.read_text() == "New text saved by another editor"


def test_unchanged_source_reports_verified_hash_and_package_version(tmp_path, capsys):
    source = tmp_path / "draft.txt"
    raw = "[TODO Ω unchanged]".encode()
    source.write_bytes(raw)
    assert cli.main([str(source), "--format", "json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["provenance"]["source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert data["provenance"]["scanner_version"] == __version__
    assert data["provenance"]["coverage"]["scanner_version"] == __version__
    assert source.read_bytes() == raw


def test_hash_rejects_oversized_source_before_opening():
    path = Mock(spec=Path)
    path.stat.return_value = SimpleNamespace(st_size=100 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match="100 MB"):
        cli._source_sha256(path)
    path.open.assert_not_called()


def test_hash_bounds_stream_growth(tmp_path, monkeypatch):
    source = tmp_path / "draft.txt"
    source.write_bytes(b"123456789")
    monkeypatch.setattr(cli, "_MAX_SOURCE_BYTES", 8)
    real_stat = Path.stat
    monkeypatch.setattr(
        Path,
        "stat",
        lambda path, *a, **kw: (
            SimpleNamespace(st_size=8) if path == source else real_stat(path, *a, **kw)
        ),
    )
    with pytest.raises(ValueError, match="100 MB"):
        cli._source_sha256(source)
    assert source.read_bytes() == b"123456789"
