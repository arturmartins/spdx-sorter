"""Shared helpers for tests that exercise the source-tree package."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_DIR = TESTS_DIR.parent
SRC_DIR = REPO_DIR / "src"


def run_cli(
    args: Sequence[str],
    stdin_text: str | None = None,
    extra_pythonpath: str | os.PathLike[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the package CLI from the source tree."""

    python_paths = [str(SRC_DIR)]
    if extra_pythonpath is not None:
        python_paths.insert(0, os.fspath(extra_pythonpath))
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(python_paths)
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "spdx_sorter", *args],
        cwd=REPO_DIR,
        env=environment,
        input=stdin_text,
        capture_output=True,
        text=True,
        check=False,
    )
