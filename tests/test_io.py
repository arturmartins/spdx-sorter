"""Behavior tests for resilient file replacement."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TESTS_DIR = Path(__file__).resolve().parent
REPO_DIR = TESTS_DIR.parent
SRC_DIR = REPO_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from spdx_sorter.io import atomic_write  # noqa: E402


class AtomicWriteTests(unittest.TestCase):
    def test_pre_replace_failure_keeps_destination_and_removes_temp_file(self):
        """A metadata failure cannot publish a partial replacement."""
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "document.spdx.json"
            original = b'{"packages":["before"]}\n'
            destination.write_bytes(original)

            with patch(
                "spdx_sorter.io.os.chmod",
                side_effect=OSError("injected chmod failure"),
            ):
                with self.assertRaisesRegex(OSError, "injected chmod failure"):
                    atomic_write(destination, '{"packages":["after"]}\n')

            self.assertEqual(destination.read_bytes(), original)
            self.assertEqual(
                list(Path(directory).glob(".document.spdx.json.*.tmp")), []
            )


if __name__ == "__main__":
    unittest.main()
