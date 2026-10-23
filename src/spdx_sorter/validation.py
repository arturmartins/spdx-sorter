"""Optional SPDX 2.2/2.3 validation adapter.

The third-party validator is imported only when validation is requested.  Its
models, exceptions, and validation message objects never cross this module's
public boundary.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, cast

from spdx_sorter.sorting import JSONValue
from spdx_sorter.version import detect_spdx_version


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """A stable, project-owned description of an SPDX validation problem."""

    message: str
    location: str | None = None
    element_id: str | None = None


class ValidationUnavailableError(RuntimeError):
    """Raised when optional SPDX validation dependencies are unavailable."""


def _unsupported_version_issue(value: JSONValue) -> ValidationIssue | None:
    version = detect_spdx_version(value)
    if version is None:
        return ValidationIssue(
            "validation supports SPDX 2.2 and 2.3; SPDX version could not be detected"
        )
    if version.normalized not in {"2.2", "2.3"}:
        return ValidationIssue(
            f"validation supports SPDX 2.2 and 2.3; detected {version.normalized}"
        )
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    name = getattr(value, "name", None)
    if isinstance(name, str):
        return name
    if isinstance(value, (bool, int, float)):
        return str(value)
    return None


def _parser_issues(error: Exception) -> tuple[ValidationIssue, ...]:
    upstream_errors = getattr(error, "parsing_errors", None)
    if not isinstance(upstream_errors, (list, tuple)):
        upstream_errors = (error,)

    messages: set[str] = set()
    for upstream_error in upstream_errors:
        message = _text(getattr(upstream_error, "message", None))
        if message is None:
            message = str(upstream_error)
        messages.update(line.strip() for line in message.splitlines() if line.strip())
    if not messages:
        messages.add("unable to parse SPDX document")
    return tuple(ValidationIssue(message) for message in sorted(messages))


def _validation_issue(upstream_message: Any) -> ValidationIssue:
    message = _text(getattr(upstream_message, "validation_message", None))
    if message is None:
        message = str(upstream_message)

    context = getattr(upstream_message, "context", None)
    element_id = None
    location = None
    if context is not None:
        element_id = _text(getattr(context, "spdx_id", None))
        if element_id is None:
            element_id = _text(getattr(context, "parent_id", None))
        location = _text(getattr(context, "element_type", None))
    return ValidationIssue(message.strip(), location, element_id)


def validate_document(value: JSONValue) -> tuple[ValidationIssue, ...]:
    """Validate an SPDX 2.2 or 2.3 JSON value without mutating it.

    Raises:
        ValidationUnavailableError: if the optional ``validation`` extra is
            not installed.
    """
    version_issue = _unsupported_version_issue(value)
    if version_issue is not None:
        return (version_issue,)

    try:
        from spdx_tools.spdx.parser.jsonlikedict.json_like_dict_parser import (
            JsonLikeDictParser,
        )
        from spdx_tools.spdx.validation.document_validator import (
            validate_full_spdx_document,
        )
    except ImportError as error:
        raise ValidationUnavailableError(
            "SPDX validation requires the optional validation extra"
        ) from error

    try:
        document_data = copy.deepcopy(cast(dict[str, Any], value))
        # spdx-tools has no type stubs; contain the untyped adapter call here.
        document = JsonLikeDictParser().parse(document_data)  # type: ignore[no-untyped-call]
    except Exception as error:  # upstream exposes several parser error types
        return _parser_issues(error)

    issues = (
        _validation_issue(message) for message in validate_full_spdx_document(document)
    )
    return tuple(
        sorted(
            issues,
            key=lambda issue: (
                issue.message,
                issue.location or "",
                issue.element_id or "",
            ),
        )
    )
