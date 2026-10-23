"""Conformance and compatibility corpus tests for public package boundaries."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from jsonschema.protocols import Validator
from jsonschema.validators import validator_for

from spdx_sorter import sort_document, validate_document
from spdx_sorter.sorting import (
    EXPERIMENTAL_ARRAY_SORT_RULES,
    PRIMITIVE_SET_KEYS,
    STABLE_ARRAY_SORT_RULES,
)

FIXTURES = Path(__file__).parent / "fixtures"
NORMATIVE = FIXTURES / "spdx-spec"
PRODUCERS = FIXTURES / "producers"
SCHEMAS = NORMATIVE / "schemas"
HAS_SPDX_TOOLS = importlib.util.find_spec("spdx_tools") is not None


def _json_files(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.json"))


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _spdx_version(document) -> str:
    version = document["spdxVersion"]
    if version == "SPDX-2.2":
        return "2.2"
    if version == "SPDX-2.3":
        return "2.3"
    raise AssertionError(f"unexpected fixture SPDX version: {version}")


def _schema_validator(document) -> Validator:
    schema_path = SCHEMAS / _spdx_version(document) / "spdx-schema.json"
    schema = _load(schema_path)
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    return validator_class(schema)


SORTABLE_ARRAY_KEYS = frozenset(
    set(STABLE_ARRAY_SORT_RULES)
    | set(EXPERIMENTAL_ARRAY_SORT_RULES)
    | PRIMITIVE_SET_KEYS
)


def _ignore_order(value, array_key: str | None = None):
    """Normalize only list order the sorter is explicitly allowed to change."""
    if isinstance(value, dict):
        return {key: _ignore_order(child, key) for key, child in value.items()}
    if isinstance(value, list):
        normalized = [_ignore_order(child) for child in value]
        if array_key in SORTABLE_ARRAY_KEYS:
            return sorted(
                normalized,
                key=lambda child: json.dumps(child, ensure_ascii=False, sort_keys=True),
            )
        return normalized
    return value


def test_producer_fixture_comparison_detects_unknown_array_reordering():
    """A producer extension array reordered by the sorter must be reported."""
    original = {"producerOrder": [{"position": 1}, {"position": 2}]}
    reordered = {"producerOrder": [{"position": 2}, {"position": 1}]}

    assert _ignore_order(original) != _ignore_order(reordered)


def test_fixture_corpus_has_each_required_category():
    assert (SCHEMAS / "2.2" / "spdx-schema.json").is_file()
    assert (SCHEMAS / "2.3" / "spdx-schema.json").is_file()
    assert list(_json_files(NORMATIVE / "valid"))
    assert list(_json_files(NORMATIVE / "invalid"))
    assert list(_json_files(PRODUCERS))


@pytest.mark.parametrize("path", _json_files(NORMATIVE / "valid"), ids=lambda p: p.name)
def test_valid_normative_fixtures_validate_against_official_json_schema(path):
    document = _load(path)

    assert sorted(_schema_validator(document).iter_errors(document), key=str) == []


@pytest.mark.parametrize(
    "path", _json_files(NORMATIVE / "invalid"), ids=lambda p: p.name
)
def test_local_negative_mutations_fail_official_json_schema(path):
    document = _load(path)

    assert sorted(_schema_validator(document).iter_errors(document), key=str)


@pytest.mark.parametrize("path", _json_files(NORMATIVE / "valid"), ids=lambda p: p.name)
@pytest.mark.skipif(
    not HAS_SPDX_TOOLS, reason="spdx-tools validation extra unavailable"
)
def test_valid_normative_fixtures_validate_through_optional_adapter(path):
    assert validate_document(_load(path)) == ()


@pytest.mark.parametrize(
    "path", _json_files(NORMATIVE / "invalid"), ids=lambda p: p.name
)
@pytest.mark.skipif(
    not HAS_SPDX_TOOLS, reason="spdx-tools validation extra unavailable"
)
def test_invalid_normative_fixtures_produce_validation_issues(path):
    assert validate_document(_load(path))


@pytest.mark.parametrize(
    "path",
    list(_json_files(NORMATIVE / "valid"))
    + list(_json_files(NORMATIVE / "invalid"))
    + list(_json_files(PRODUCERS)),
    ids=lambda p: p.name,
)
def test_every_corpus_fixture_sorts_idempotently(path):
    sorted_once = sort_document(_load(path))
    assert sort_document(sorted_once) == sorted_once


@pytest.mark.parametrize("path", _json_files(PRODUCERS), ids=lambda p: p.name)
def test_producer_compatibility_fixtures_preserve_data_apart_from_order(path):
    original = _load(path)
    sorted_document = sort_document(original)

    assert _ignore_order(sorted_document) == _ignore_order(original)
