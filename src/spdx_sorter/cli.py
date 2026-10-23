"""Command-line interface for SPDX JSON sorting."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import cast

from spdx_sorter.io import atomic_write, read_text
from spdx_sorter.sorting import JSONValue, sort_document
from spdx_sorter.validation import ValidationUnavailableError, validate_document
from spdx_sorter.version import SpdxVersion, detect_spdx_version


def _render(value: JSONValue) -> str:
    return json.dumps(sort_document(value), indent=2, ensure_ascii=False) + "\n"


def _warn_for_version(version: SpdxVersion | None) -> None:
    if version is None or version.support == "stable":
        return
    if version.support == "experimental":
        print(
            f"warning: SPDX {version.normalized} support is experimental",
            file=sys.stderr,
        )
        return
    print(
        f"warning: SPDX {version.normalized} is unsupported; sorting conservatively",
        file=sys.stderr,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spdx-sort",
        description="Sort SPDX JSON deterministically for stable diffs.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="exit 1 when the input is not already sorted",
    )
    mode.add_argument(
        "--in-place",
        action="store_true",
        help="atomically replace INPUT instead of writing to stdout",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="validate SPDX 2.2/2.3 input before sorting or writing",
    )
    parser.add_argument("input", nargs="?", metavar="INPUT")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface and return its process exit code."""
    parser = _parser()
    arguments = parser.parse_args(argv)
    if arguments.in_place and (arguments.input is None or arguments.input == "-"):
        parser.error("--in-place requires INPUT")

    try:
        if arguments.input is None or arguments.input == "-":
            input_name = "<stdin>"
            input_text = sys.stdin.read()
        else:
            input_name = arguments.input
            input_text = read_text(arguments.input)

        value = cast(JSONValue, json.loads(input_text))
        if arguments.validate:
            try:
                issues = validate_document(value)
            except ValidationUnavailableError:
                print(
                    f"{input_name}: validation unavailable; install it with "
                    "pip install 'spdx-sorter[validation]'",
                    file=sys.stderr,
                )
                return 2
            if issues:
                for issue in issues:
                    print(
                        f"{input_name}: validation: {issue.message}",
                        file=sys.stderr,
                    )
                return 2
        _warn_for_version(detect_spdx_version(value))
        output_text = _render(value)
        if arguments.check:
            if output_text == input_text:
                return 0
            print(f"{input_name}: not sorted", file=sys.stderr)
            return 1

        if arguments.in_place:
            atomic_write(arguments.input, output_text)
            return 0

        sys.stdout.write(output_text)
        return 0
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
