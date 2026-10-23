"""Subprocess tests for the packaged spdx-sort command."""

import json
import os
import stat
import tempfile
import unittest

from support import run_cli


class PackageCliTests(unittest.TestCase):
    UNSORTED_DOC = {
        "spdxVersion": "SPDX-2.3",
        "packages": [
            {"SPDXID": "SPDXRef-B", "name": "b"},
            {"SPDXID": "SPDXRef-A", "name": "a"},
        ],
    }

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.directory = self._tmpdir.name

    def _write_document(self, name="document.spdx.json"):
        path = os.path.join(self.directory, name)
        with open(path, "w", encoding="utf-8") as stream:
            json.dump(self.UNSORTED_DOC, stream, indent=2)
            stream.write("\n")
        return path

    def test_file_input_writes_stdout_without_mutating_source(self):
        path = self._write_document()
        with open(path, encoding="utf-8") as stream:
            original = stream.read()

        process = run_cli([path])

        self.assertEqual(process.returncode, 0)
        self.assertEqual(
            [item["SPDXID"] for item in json.loads(process.stdout)["packages"]],
            ["SPDXRef-A", "SPDXRef-B"],
        )
        self.assertEqual(process.stderr, "")
        with open(path, encoding="utf-8") as stream:
            self.assertEqual(stream.read(), original)

    def test_check_reports_unsorted_without_writing(self):
        path = self._write_document()
        with open(path, encoding="utf-8") as stream:
            original = stream.read()

        process = run_cli(["--check", path])

        self.assertEqual(process.returncode, 1)
        self.assertEqual(process.stdout, "")
        self.assertEqual(process.stderr, f"{path}: not sorted\n")
        with open(path, encoding="utf-8") as stream:
            self.assertEqual(stream.read(), original)

    def test_check_accepts_canonical_stdin(self):
        canonical = run_cli([], stdin_text=json.dumps(self.UNSORTED_DOC)).stdout

        process = run_cli(["--check"], stdin_text=canonical)

        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stdout, "")
        self.assertEqual(process.stderr, "")

    @unittest.skipIf(os.name == "nt", "POSIX symlinks and modes are not portable")
    def test_in_place_follows_symlink_and_preserves_target_mode(self):
        target = self._write_document("target.spdx.json")
        link = os.path.join(self.directory, "link.spdx.json")
        os.symlink(target, link)
        os.chmod(target, 0o640)

        process = run_cli(["--in-place", link])

        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stdout, "")
        self.assertEqual(process.stderr, "")
        self.assertTrue(os.path.islink(link))
        self.assertEqual(stat.S_IMODE(os.stat(target).st_mode), 0o640)
        with open(target, encoding="utf-8") as stream:
            self.assertEqual(
                [item["SPDXID"] for item in json.load(stream)["packages"]],
                ["SPDXRef-A", "SPDXRef-B"],
            )

    def test_in_place_requires_file_input(self):
        process = run_cli(["--in-place"], stdin_text=json.dumps(self.UNSORTED_DOC))

        self.assertEqual(process.returncode, 2)
        self.assertIn("--in-place requires INPUT", process.stderr)

    def test_in_place_rejects_explicit_stdin(self):
        process = run_cli(["--in-place", "-"], stdin_text=json.dumps(self.UNSORTED_DOC))

        self.assertEqual(process.returncode, 2)
        self.assertIn("--in-place requires INPUT", process.stderr)

    def test_check_and_in_place_are_mutually_exclusive(self):
        path = self._write_document()

        process = run_cli(["--check", "--in-place", path])

        self.assertEqual(process.returncode, 2)
        self.assertIn("not allowed with argument", process.stderr)

    def test_invalid_json_is_a_usage_failure_without_traceback(self):
        process = run_cli([], stdin_text="{not json")

        self.assertEqual(process.returncode, 2)
        self.assertIn("error:", process.stderr)
        self.assertNotIn("Traceback", process.stderr)

    def test_missing_file_is_an_io_failure_without_traceback(self):
        missing = os.path.join(self.directory, "missing.spdx.json")

        process = run_cli([missing])

        self.assertEqual(process.returncode, 2)
        self.assertIn("error:", process.stderr)
        self.assertNotIn("Traceback", process.stderr)

    def test_non_utf8_file_is_an_io_failure_without_traceback(self):
        path = os.path.join(self.directory, "invalid-utf8.spdx.json")
        with open(path, "wb") as stream:
            stream.write(b"\xff")

        process = run_cli([path])

        self.assertEqual(process.returncode, 2)
        self.assertIn("error:", process.stderr)
        self.assertNotIn("Traceback", process.stderr)

    def test_validate_without_extra_is_actionable_and_does_not_write(self):
        path = self._write_document()
        with open(path, encoding="utf-8") as stream:
            original = stream.read()
        blocker = os.path.join(self.directory, "without-extra")
        os.mkdir(blocker)
        with open(os.path.join(blocker, "spdx_tools.py"), "w", encoding="utf-8"):
            pass

        process = run_cli(
            ["--validate", "--in-place", path],
            extra_pythonpath=blocker,
        )

        self.assertEqual(process.returncode, 2)
        self.assertEqual(process.stdout, "")
        self.assertIn("pip install 'spdx-sorter[validation]'", process.stderr)
        with open(path, encoding="utf-8") as stream:
            self.assertEqual(stream.read(), original)

    def test_validate_rejects_unsupported_version_before_writing(self):
        path = self._write_document()
        with open(path, "w", encoding="utf-8") as stream:
            stream.write('{"spdxVersion": "SPDX-1.2"}\n')
        with open(path, encoding="utf-8") as stream:
            unsupported = stream.read()

        process = run_cli(["--validate", "--in-place", path])

        self.assertEqual(process.returncode, 2)
        self.assertEqual(process.stdout, "")
        self.assertEqual(
            process.stderr,
            f"{path}: validation: validation supports SPDX 2.2 and 2.3; detected 1.2\n",
        )
        with open(path, encoding="utf-8") as stream:
            self.assertEqual(stream.read(), unsupported)


if __name__ == "__main__":
    unittest.main()
