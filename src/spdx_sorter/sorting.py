"""Pure functions for deterministic SPDX JSON sorting."""

from __future__ import annotations

import json
import math
from typing import Any, TypeAlias, cast

JSONScalar: TypeAlias = None | bool | int | float | str
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]

STABLE_ARRAY_SORT_RULES: dict[str, tuple[str, ...]] = {
    "packages": ("SPDXID", "spdxId", "name"),
    "files": ("SPDXID", "spdxId", "fileName"),
    "relationships": (
        "spdxElementId",
        "relationshipType",
        "relatedSpdxElement",
    ),
    "externalRefs": (
        "referenceCategory",
        "referenceType",
        "referenceLocator",
    ),
    "annotations": ("annotationDate", "annotator"),
    "checksums": ("algorithm", "checksumValue"),
    "hasExtractedLicensingInfos": ("licenseId", "name"),
    "snippets": ("SPDXID", "name"),
    "externalDocumentRefs": ("externalDocumentId", "spdxDocument"),
}

EXPERIMENTAL_ARRAY_SORT_RULES: dict[str, tuple[str, ...]] = {
    "elements": ("spdxId", "type", "name"),
}

PRIMITIVE_SET_KEYS = frozenset(
    {
        "documentDescribes",
        "licenseInfoInFiles",
        "licenseInfoFromFiles",
        "fileTypes",
        "seeAlsos",
    }
)

_MISSING = object()


def _canonical_json(value: JSONValue) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _number_token(value: int | float) -> tuple[int, int | float, int, int]:
    """Return a totally ordered token for JSON numbers.

    Non-finite floats cannot participate directly in ordering because NaN is
    not equal to, less than, or greater than itself. Finite integers and
    floats retain distinct type markers, and negative zero remains distinct
    from positive zero.
    """
    if isinstance(value, int):
        return (1, value, 0, 0)
    if math.isnan(value):
        return (3, 0, 1, 0)
    if math.isinf(value):
        return (0 if value < 0 else 2, 0, 1, 0)
    return (1, value, 1, int(math.copysign(1.0, value) < 0))


def _value_token(value: object) -> tuple[int, Any]:
    if value is _MISSING:
        return (0, "")
    if value is None:
        return (1, "")
    if isinstance(value, bool):
        return (2, value)
    if isinstance(value, (int, float)):
        return (3, _number_token(value))
    if isinstance(value, str):
        return (4, value)
    if isinstance(value, list):
        return (5, _canonical_json(cast(JSONValue, value)))
    return (6, _canonical_json(cast(JSONValue, value)))


def _object_sort_key(
    item: dict[str, JSONValue],
    fields: tuple[str, ...],
) -> tuple[tuple[int, object], ...]:
    primary = tuple(_value_token(item.get(field, _MISSING)) for field in fields)
    return primary + ((7, _canonical_json(item)),)


def _can_sort_object_array(
    values: list[JSONValue],
    fields: tuple[str, ...],
) -> bool:
    return all(
        isinstance(item, dict) and any(field in item for field in fields)
        for item in values
    )


def _sort_known_array(key: str, values: list[JSONValue]) -> list[JSONValue]:
    if key in PRIMITIVE_SET_KEYS and all(isinstance(item, str) for item in values):
        return cast(list[JSONValue], sorted(cast(list[str], values)))

    fields = STABLE_ARRAY_SORT_RULES.get(key) or EXPERIMENTAL_ARRAY_SORT_RULES.get(key)
    if fields is None or not _can_sort_object_array(values, fields):
        return values

    object_values = cast(list[dict[str, JSONValue]], values)
    return cast(
        list[JSONValue],
        sorted(object_values, key=lambda item: _object_sort_key(item, fields)),
    )


def sort_document(value: JSONValue) -> JSONValue:
    """Return a deeply copied, deterministically sorted JSON value."""
    if isinstance(value, dict):
        result: dict[str, JSONValue] = {}
        for key in sorted(value):
            child = sort_document(value[key])
            if isinstance(child, list):
                child = _sort_known_array(key, child)
            result[key] = child
        return result

    if isinstance(value, list):
        return [sort_document(item) for item in value]

    return value


def sort_json(text: str) -> str:
    """Parse and deterministically render a JSON value."""
    value = cast(JSONValue, json.loads(text))
    return json.dumps(sort_document(value), indent=2, ensure_ascii=False) + "\n"
