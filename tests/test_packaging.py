"""Distribution metadata and source-tree version contract tests."""

import importlib.metadata
import os
import subprocess
import sys
import unittest

import tomllib

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(TESTS_DIR)
SRC_DIR = os.path.join(REPO_DIR, "src")
sys.path.insert(0, SRC_DIR)

import spdx_sorter  # noqa: E402


class PackagingTests(unittest.TestCase):
    def test_distribution_metadata_matches_public_contract(self):
        with open(os.path.join(REPO_DIR, "pyproject.toml"), "rb") as stream:
            metadata = tomllib.load(stream)

        project = metadata["project"]
        self.assertEqual(project["name"], "spdx-sorter")
        self.assertEqual(project["version"], "0.1.0")
        self.assertEqual(project["requires-python"], ">=3.10")
        self.assertEqual(project["dependencies"], [])
        self.assertEqual(
            project["optional-dependencies"]["validation"],
            ["spdx-tools>=0.8.5,<0.9"],
        )
        self.assertEqual(
            project["scripts"]["spdx-sort"],
            "spdx_sorter.cli:main",
        )

    def test_public_version_uses_installed_distribution_metadata(self):
        self.assertEqual(
            spdx_sorter.__version__,
            importlib.metadata.version("spdx-sorter"),
        )

    def test_source_tree_version_fallback_matches_project_metadata(self):
        script = """
import importlib.metadata
def package_not_found(name):
    raise importlib.metadata.PackageNotFoundError(name)
importlib.metadata.version = package_not_found
from spdx_sorter import __version__
print(__version__)
"""
        environment = os.environ.copy()
        environment["PYTHONPATH"] = SRC_DIR

        process = subprocess.run(
            [sys.executable, "-c", script],
            cwd=REPO_DIR,
            env=environment,
            capture_output=True,
            text=True,
        )

        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stdout, "0.1.0\n")

    def test_typed_marker_exists(self):
        marker = os.path.join(SRC_DIR, "spdx_sorter", "py.typed")

        self.assertTrue(os.path.isfile(marker))


if __name__ == "__main__":
    unittest.main()
