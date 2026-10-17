from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import pytest

from manuscript_placeholders import output
from manuscript_placeholders.cli import main

PROJECT = "manuscript-placeholder-collector"


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("index", [0, 1])
def test_late_write_failure_rolls_back_and_retries(
    tmp_path, monkeypatch, reverse, index
):
    pair = [(tmp_path / "report.json", "report"), (tmp_path / "state.json", "state")]
    if reverse:
        pair.reverse()
    original = output._write_final
    count = 0

    def fail(item):
        nonlocal count
        current = count
        count += 1
        if current == index:
            assert item.fd is not None
            item.written = os.write(item.fd, item.data[:2])
            raise OSError("synthetic late write failure")
        return original(item)

    with monkeypatch.context() as patch:
        patch.setattr(output, "_write_final", fail)
        with pytest.raises(OSError, match="synthetic"):
            output.write_new_outputs(pair)
    assert not any(p.exists() for p, _ in pair)
    assert not list(tmp_path.glob(".forge-output-*"))
    output.write_new_outputs(pair)
    assert [p.read_text() for p, _ in pair] == [v for _, v in pair]


@pytest.mark.parametrize("index", [0, 1])
def test_existing_collision_is_preserved(tmp_path, index):
    pair = [
        (tmp_path / "report.json", "new-report"),
        (tmp_path / "state.json", "new-state"),
    ]
    pair[index][0].write_text("existing")
    with pytest.raises(ValueError, match="already exists"):
        output.write_new_outputs(pair)
    assert pair[index][0].read_text() == "existing"
    assert not pair[1 - index][0].exists()


def test_collision_after_preflight_never_overwrites(tmp_path, monkeypatch):
    pair = [(tmp_path / "one", "one"), (tmp_path / "two", "two")]
    original = output.os.open

    def collide(path, flags, *args, **kwargs):
        if Path(path) == pair[1][0] and flags & os.O_EXCL:
            pair[1][0].write_text("concurrent")
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(output.os, "open", collide)
    with pytest.raises(FileExistsError):
        output.write_new_outputs(pair)
    assert not pair[0][0].exists()
    assert pair[1][0].read_text() == "concurrent"


def test_changed_new_file_is_preserved_on_rollback(tmp_path, monkeypatch):
    pair = [(tmp_path / "one", "one"), (tmp_path / "two", "two")]
    original = output._write_final

    def change(item):
        if item.path == pair[1][0]:
            pair[0][0].write_text("concurrent edit")
            raise OSError("synthetic")
        return original(item)

    monkeypatch.setattr(output, "_write_final", change)
    with pytest.raises(OSError, match="kept changed"):
        output.write_new_outputs(pair)
    assert pair[0][0].read_text() == "concurrent edit"
    assert not pair[1][0].exists()


def test_stdout_failure_rolls_back_new_state(tmp_path):
    path = tmp_path / "state"

    def broken():
        raise BrokenPipeError("consumer closed")

    with pytest.raises(BrokenPipeError):
        output.write_new_outputs([(path, "state")], deliver=broken)
    assert not path.exists()


def fixture(tmp_path):
    source = tmp_path / "input.json"
    if PROJECT == "manuscript-placeholder-collector":
        source = tmp_path / "draft.txt"
        source.write_text("[RESEARCH synthetic fixture]")
        return source, []
    game = {"id": "one", "title": "Synthetic game", "platform": "PC"}
    if PROJECT == "game-graveyard":
        game.update(
            reason="Synthetic reason", reason_category="time", abandoned_on="2026-01-01"
        )
    source.write_text(json.dumps({"version": 1, "games": [game]}))
    return source, []


def arguments(source, report, state):
    if PROJECT == "manuscript-placeholder-collector":
        return [
            str(source),
            "--format",
            "json",
            "--output",
            str(report),
            "--ledger-output",
            str(state),
        ]
    if PROJECT == "game-graveyard":
        return [
            str(source),
            "--decision",
            "returned",
            "--game-id",
            "one",
            "--date",
            "2026-10-17",
            "--decision-note",
            "Synthetic review",
            "--decision-output",
            str(state),
            "--output",
            str(report),
            "--format",
            "json",
        ]
    return [
        str(source),
        "--seed",
        "review",
        "--stable-ids",
        "--as-of",
        "2026-10-17",
        "--history-output",
        str(state),
        "--output",
        str(report),
        "--format",
        "json",
    ]


@pytest.mark.skipif(
    os.name != "posix" or getattr(os, "geteuid", lambda: 0)() == 0,
    reason="requires a non-admin POSIX permission boundary",
)
@pytest.mark.parametrize("blocked", ["report", "state"])
def test_real_nonadmin_permission_failure_and_retry(tmp_path, capsys, blocked):
    source, _ = fixture(tmp_path)
    before = source.read_bytes()
    ro = tmp_path / "readonly"
    ro.mkdir()
    ro.chmod(0o555)
    report = (ro if blocked == "report" else tmp_path) / "report.json"
    state = (ro if blocked == "state" else tmp_path) / "state.json"
    try:
        assert main(arguments(source, report, state)) == 2
        capsys.readouterr()
        assert not report.exists() and not state.exists()
        assert not list(tmp_path.rglob(".forge-output-*"))
    finally:
        ro.chmod(0o755)
    assert main(arguments(source, report, state)) == 0
    assert report.exists() and state.exists()
    assert source.read_bytes() == before


@pytest.mark.parametrize("which", ["report", "state"])
def test_cli_collision_preserves_existing_files(tmp_path, capsys, which):
    source, _ = fixture(tmp_path)
    report, state = tmp_path / "report.json", tmp_path / "state.json"
    selected = report if which == "report" else state
    selected.write_text("pre-existing")
    before = source.read_bytes()
    assert main(arguments(source, report, state)) == 2
    capsys.readouterr()
    assert selected.read_text() == "pre-existing"
    assert not (state if which == "report" else report).exists()
    assert source.read_bytes() == before


def test_single_output_failure_cleans_partial_file(tmp_path, monkeypatch):
    path = tmp_path / "only"

    def fail(item):
        assert item.fd is not None
        item.written = os.write(item.fd, item.data[:2])
        raise OSError("partial single output")

    monkeypatch.setattr(output, "_write_final", fail)
    with pytest.raises(OSError):
        output.write_new_outputs([(path, "single output")])
    assert not path.exists()


def test_stdout_cli_failure_leaves_no_state(tmp_path, monkeypatch, capsys):
    source, _ = fixture(tmp_path)
    report, state = tmp_path / "unused", tmp_path / "state.json"
    args = arguments(source, report, state)
    i = args.index("--output")
    del args[i : i + 2]

    class Broken:
        def write(self, text):
            raise BrokenPipeError("synthetic closed pipe")

        def flush(self):
            raise BrokenPipeError("synthetic closed pipe")

    module = importlib.import_module("manuscript_placeholders.cli")
    with monkeypatch.context() as patch:
        patch.setattr(module.sys, "stdout", Broken())
        assert main(args) == 2
    capsys.readouterr()
    assert not state.exists()
