"""Stage new outputs, reserve every destination exclusively, and recover failed writes."""

from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class _Output:
    path: Path
    data: bytes
    stage: Path | None = None
    stage_identity: tuple[int, int] | None = None
    fd: int | None = None
    identity: tuple[int, int] | None = None
    written: int = 0


def validate_output_paths(paths: list[Path]) -> None:
    if len({p.resolve() for p in paths}) != len(paths):
        raise ValueError("outputs must be distinct new files")
    for path in paths:
        if os.path.lexists(path):
            raise ValueError(
                f"output already exists: {path}; outputs must be distinct new files"
            )
        if not path.parent.is_dir():
            raise ValueError(f"output directory does not exist: {path.parent}")


def _identity(path: Path) -> tuple[int, int] | None:
    try:
        value = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(value.st_mode):
        return None
    return value.st_dev, value.st_ino


def _digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            result.update(block)
    return result.hexdigest()


def _write_final(item: _Output) -> None:
    assert item.fd is not None
    view = memoryview(item.data)
    while item.written < len(view):
        count = os.write(item.fd, view[item.written : item.written + 65536])
        if count <= 0:
            raise OSError("output write made no progress")
        item.written += count
    os.fsync(item.fd)


def _close(items: list[_Output]) -> None:
    for item in items:
        if item.fd is not None:
            fd, item.fd = item.fd, None
            os.close(fd)


def _rollback(items: list[_Output]) -> list[str]:
    preserved = []
    for item in reversed(items):
        if item.identity is None:
            continue
        try:
            expected = hashlib.sha256(memoryview(item.data)[: item.written]).hexdigest()
            if _identity(item.path) == item.identity and _digest(item.path) == expected:
                # Check identity again after reading; never remove a replacement file.
                if _identity(item.path) == item.identity:
                    item.path.unlink()
                else:
                    preserved.append(str(item.path))
            elif os.path.lexists(item.path):
                preserved.append(str(item.path))
        except OSError:
            preserved.append(str(item.path))
    return preserved


def write_new_outputs(
    outputs: list[tuple[Path, str]], deliver: Callable[[], None] | None = None
) -> None:
    """Write only new files; a failed command removes only its unchanged new outputs.

    Existing and concurrently created/replaced/edited files are always preserved.
    Staging and ordinary write failures are recoverable; this is not a multi-file
    power-loss transaction. stdout cannot be recalled after a consumer reads it.
    """
    validate_output_paths([p for p, _ in outputs])
    items = [_Output(path, text.encode("utf-8")) for path, text in outputs]
    try:
        # Complete every staged write before publishing any destination name.
        for item in items:
            fd, name = tempfile.mkstemp(prefix=".forge-output-", dir=item.path.parent)
            item.stage = Path(name)
            value = os.fstat(fd)
            item.stage_identity = value.st_dev, value.st_ino
            with os.fdopen(fd, "wb") as stream:
                stream.write(item.data)
                stream.flush()
                os.fsync(stream.fileno())
        # Reserve all final names before filling either output. O_EXCL protects
        # existing files, dangling symlinks and collisions after validation.
        for item in items:
            item.fd = os.open(
                item.path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
                0o600,
            )
            value = os.fstat(item.fd)
            item.identity = value.st_dev, value.st_ino
        for item in items:
            _write_final(item)
        _close(items)
        if deliver is not None:
            deliver()
    except BaseException as exc:
        _close(items)
        preserved = _rollback(items)
        if preserved:
            raise OSError(
                "output operation failed; kept changed or inaccessible output files: "
                + ", ".join(preserved)
            ) from exc
        raise
    finally:
        _close(items)
        for item in items:
            if item.stage is not None and _identity(item.stage) == item.stage_identity:
                item.stage.unlink()
