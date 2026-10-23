"""Compute OCI release tags from the canonical release version."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

CORE = (
    r"(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
)
IDENTIFIER = r"(?:0|[1-9]\d*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
SEMVER = re.compile(rf"{CORE}(?P<prerelease>-(?:{IDENTIFIER})(?:\.(?:{IDENTIFIER}))*)?")


def container_tags(version: str) -> list[str]:
    """Return exact and floating OCI tags for a canonical SemVer release."""
    if "+" in version:
        raise ValueError("version must be canonical SemVer without build metadata")

    match = SEMVER.fullmatch(version)
    if match is None:
        raise ValueError("version must be canonical SemVer")

    tags = [version]
    if match.group("prerelease") is None:
        major = match.group("major")
        minor = match.group("minor")
        tags.extend([f"{major}.{minor}", major, "latest"])
    return tags


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("version")
    parser.add_argument("output_file", type=Path)
    args = parser.parse_args()

    args.output_file.write_text("\n".join(container_tags(args.version)) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
