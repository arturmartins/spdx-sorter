"""Tests for pure SPDX version detection and CLI warnings."""

import os
import sys
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(TESTS_DIR)
SRC_DIR = os.path.join(REPO_DIR, "src")
sys.path.insert(0, TESTS_DIR)
sys.path.insert(0, SRC_DIR)

from support import run_cli  # noqa: E402

from spdx_sorter.version import detect_spdx_version  # noqa: E402


class VersionDetectionTests(unittest.TestCase):
    def test_spdx_2_3_is_stable(self):
        version = detect_spdx_version({"spdxVersion": "SPDX-2.3"})

        self.assertIsNotNone(version)
        self.assertEqual(version.label, "SPDX-2.3")
        self.assertEqual(version.normalized, "2.3")
        self.assertEqual(version.support, "stable")

    def test_spdx_3_context_is_experimental(self):
        version = detect_spdx_version(
            {"@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld"}
        )

        self.assertIsNotNone(version)
        self.assertEqual(version.normalized, "3.0.1")
        self.assertEqual(version.support, "experimental")

    def test_unrelated_json_ld_context_is_not_spdx(self):
        version = detect_spdx_version({"@context": "https://schema.org"})

        self.assertIsNone(version)

    def test_unsupported_version_is_classified(self):
        version = detect_spdx_version({"spdxVersion": "SPDX-1.2"})

        self.assertIsNotNone(version)
        self.assertEqual(version.support, "unsupported")

    def test_experimental_version_warns_on_cli(self):
        process = run_cli(
            [],
            stdin_text=(
                '{"@context": '
                '"https://spdx.org/rdf/3.0.1/spdx-context.jsonld", '
                '"type": "SpdxDocument"}'
            ),
        )

        self.assertEqual(process.returncode, 0)
        self.assertEqual(
            process.stderr,
            "warning: SPDX 3.0.1 support is experimental\n",
        )

    def test_unsupported_version_warns_on_cli(self):
        process = run_cli([], stdin_text='{"spdxVersion": "SPDX-1.2"}')

        self.assertEqual(process.returncode, 0)
        self.assertEqual(
            process.stderr,
            "warning: SPDX 1.2 is unsupported; sorting conservatively\n",
        )


if __name__ == "__main__":
    unittest.main()
