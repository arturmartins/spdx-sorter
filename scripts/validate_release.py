"""Validate the single release-tag grammar accepted by release workflows."""

from __future__ import annotations

import re
import sys

CORE = r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
IDENTIFIER = r"(?:0|[1-9]\d*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
SEMVER = re.compile(rf"{CORE}(?:-(?:{IDENTIFIER})(?:\.(?:{IDENTIFIER}))*)?")


def main(arguments: list[str]) -> int:
    if len(arguments) != 2:
        print("usage: validate_release.py v<version> <version>", file=sys.stderr)
        return 2

    tag, version = arguments
    if "+" in version or not SEMVER.fullmatch(version):
        print(
            "version must be canonical SemVer without build metadata "
            "(for example, 1.2.3 or 1.2.3-rc.1)",
            file=sys.stderr,
        )
        return 1
    if tag != f"v{version}":
        print("tag must be exactly v<version>", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
