"""Preflight a PyPI upload against the immutable files already published."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


class PreflightError(RuntimeError):
    """Raised when PyPI state cannot be safely compared with local files."""


def parse_release_files(payload: object, expected_version: str) -> dict[str, str]:
    """Return published filename-to-SHA-256 mappings from a PyPI response."""

    if not isinstance(payload, dict):
        raise PreflightError("PyPI response is not an object")
    info = payload.get("info")
    if not isinstance(info, dict) or info.get("version") != expected_version:
        raise PreflightError(
            "PyPI response version does not match the requested release version"
        )
    urls = payload.get("urls")
    if not isinstance(urls, list):
        raise PreflightError("PyPI response is missing a urls list")
    if not urls:
        raise PreflightError("PyPI response has a non-empty urls list")

    files: dict[str, str] = {}
    for index, item in enumerate(urls):
        if not isinstance(item, dict):
            raise PreflightError(f"PyPI response urls[{index}] is not an object")
        filename = item.get("filename")
        digests = item.get("digests")
        digest = digests.get("sha256") if isinstance(digests, dict) else None
        if not isinstance(filename, str) or not filename:
            raise PreflightError(f"PyPI response urls[{index}] has no filename")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise PreflightError(f"PyPI response has no valid sha256 for {filename!r}")
        previous = files.get(filename)
        if previous is not None and previous != digest:
            raise PreflightError(
                f"PyPI response has conflicting digests for {filename}"
            )
        files[filename] = digest
    return files


def filter_uploads(
    directory: Path, existing_files: Mapping[str, str] | None
) -> list[Path]:
    """Remove exact matches and return files that still need publication.

    All conflicts are checked before any matching file is removed, so a failed
    preflight leaves the upload directory untouched.
    """

    local_files = sorted(
        (path for path in directory.iterdir() if path.is_file()),
        key=lambda path: path.name,
    )
    existing = {} if existing_files is None else dict(existing_files)
    matching: list[Path] = []
    for path in local_files:
        published_digest = existing.get(path.name)
        if published_digest is None:
            continue
        local_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if local_digest != published_digest:
            raise PreflightError(
                f"PyPI digest conflict for {path.name}: "
                f"published {published_digest}, local {local_digest}"
            )
        matching.append(path)

    for path in matching:
        path.unlink()
    return [path for path in local_files if path not in matching]


def fetch_release_files(project: str, version: str) -> dict[str, str] | None:
    """Fetch the PyPI file index, returning ``None`` when version is absent."""

    project_part = urllib.parse.quote(project, safe="")
    version_part = urllib.parse.quote(version, safe="")
    endpoint = f"https://pypi.org/pypi/{project_part}/{version_part}/json"
    request = urllib.request.Request(endpoint, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
            raw_payload = response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise PreflightError(
            f"PyPI API returned HTTP {error.code}; refusing to publish"
        ) from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise PreflightError(
            f"PyPI API request failed; refusing to publish: {error}"
        ) from error

    try:
        payload: Any = json.loads(raw_payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PreflightError(
            "PyPI API returned invalid JSON; refusing to publish"
        ) from error
    return parse_release_files(payload, version)


def _write_github_output(publish: bool) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file is None:
        return
    with open(output_file, "a", encoding="utf-8") as handle:
        handle.write(f"publish={'true' if publish else 'false'}\n")


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("directory", type=Path)
    parser.add_argument("--project", default="spdx-sorter")
    options = parser.parse_args(arguments)

    try:
        existing_files = fetch_release_files(options.project, options.version)
        remaining = filter_uploads(options.directory, existing_files)
    except (OSError, PreflightError) as error:
        print(f"PyPI preflight failed: {error}", file=sys.stderr)
        return 1

    _write_github_output(bool(remaining))
    print(f"PyPI preflight: {len(remaining)} file(s) remain to publish")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
