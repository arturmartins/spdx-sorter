"""File-system operations for SPDX JSON documents."""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path


def read_text(path: str | Path) -> str:
    """Read a UTF-8 text file."""
    return Path(path).read_text(encoding="utf-8")


def _sync_directory(directory: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY

    try:
        descriptor = os.open(directory, flags)
    except OSError:
        return

    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def atomic_write(path: str | Path, text: str) -> None:
    """Atomically replace an existing file while preserving its mode.

    Symbolic links are resolved so that the target is replaced while the link
    remains intact.
    """
    target = Path(path).resolve(strict=True)
    original_mode = stat.S_IMODE(target.stat().st_mode)
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(text)
            temporary.flush()
            os.fsync(temporary.fileno())

        os.chmod(temporary_path, original_mode)
        os.replace(temporary_path, target)
        temporary_path = None
        _sync_directory(target.parent)
    except BaseException:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                pass
        raise
