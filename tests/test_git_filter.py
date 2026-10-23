"""End-to-end test of spdx-sort as a git clean filter."""

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

from support import SRC_DIR


@unittest.skipUnless(shutil.which("git"), "git is not installed")
class GitCleanFilterTests(unittest.TestCase):
    def test_git_add_stores_sorted_blob_and_keeps_worktree(self):
        document = {
            "spdxVersion": "SPDX-2.3",
            "packages": [
                {"SPDXID": "SPDXRef-B", "name": "b"},
                {"SPDXID": "SPDXRef-A", "name": "a"},
            ],
        }
        with tempfile.TemporaryDirectory() as repo:
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(SRC_DIR)
            command = f"{shlex.quote(sys.executable)} -m spdx_sorter"

            def git(*args):
                return subprocess.run(  # noqa: S603
                    ["git", *args],  # noqa: S607
                    cwd=repo,
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=True,
                )

            git("init", "-q")
            with open(os.path.join(repo, ".gitattributes"), "w") as stream:
                stream.write("*.spdx.json filter=spdx-sort\n")
            git("config", "filter.spdx-sort.clean", command)
            git("config", "filter.spdx-sort.smudge", "cat")
            git("config", "filter.spdx-sort.required", "true")
            path = os.path.join(repo, "a.spdx.json")
            with open(path, "w", encoding="utf-8") as stream:
                json.dump(document, stream)
            git("add", ".")

            staged = git("show", ":a.spdx.json").stdout
            self.assertEqual(
                [p["SPDXID"] for p in json.loads(staged)["packages"]],
                ["SPDXRef-A", "SPDXRef-B"],
            )
            with open(path, encoding="utf-8") as stream:
                worktree = json.load(stream)
            self.assertEqual(worktree["packages"][0]["SPDXID"], "SPDXRef-B")


if __name__ == "__main__":
    unittest.main()
