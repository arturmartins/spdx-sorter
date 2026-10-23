"""Bounded property tests for the public sorting API."""

from __future__ import annotations

import copy
import json
import math

import pytest

from spdx_sorter import sort_document, sort_json

hypothesis = pytest.importorskip("hypothesis")
given = hypothesis.given
settings = hypothesis.settings
st = hypothesis.strategies


JSON_SCALAR = (
    st.none()
    | st.booleans()
    | st.integers(-1000, 1000)
    | st.floats(
        allow_nan=False,
        allow_infinity=False,
        width=32,
    )
    | st.text(max_size=32)
)
JSON_VALUE = st.recursive(
    JSON_SCALAR,
    lambda children: (
        st.lists(children, max_size=6)
        | st.dictionaries(st.text(min_size=1, max_size=20), children, max_size=6)
    ),
    max_leaves=30,
)

PROPERTY_SETTINGS = settings(max_examples=80, deadline=None)


@PROPERTY_SETTINGS
@given(JSON_VALUE)
def test_sort_document_is_idempotent_for_json_compatible_inputs(value):
    """Sorting an already sorted JSON value changes nothing."""
    assert sort_document(sort_document(value)) == sort_document(value)


@PROPERTY_SETTINGS
@given(JSON_VALUE)
def test_sort_document_does_not_mutate_caller_input(value):
    """The public sorter is pure from the caller's perspective."""
    original = copy.deepcopy(value)

    sort_document(value)

    assert value == original


PACKAGE_IDENTIFIERS = st.lists(
    st.text(min_size=1, max_size=16), min_size=1, max_size=6, unique=True
)


@PROPERTY_SETTINGS
@given(PACKAGE_IDENTIFIERS)
def test_recognized_object_array_permutations_converge(identifiers):
    packages = [
        {"SPDXID": identifier, "name": identifier} for identifier in identifiers
    ]
    reverse = list(reversed(packages))

    assert sort_document({"packages": packages}) == sort_document({"packages": reverse})


@PROPERTY_SETTINGS
@given(st.lists(st.text(min_size=1, max_size=16), max_size=8, unique=True))
def test_set_semantic_string_array_permutations_converge(values):
    assert sort_document({"documentDescribes": values}) == sort_document(
        {"documentDescribes": list(reversed(values))}
    )


@PROPERTY_SETTINGS
@given(st.lists(st.text(max_size=16), max_size=8))
def test_unknown_string_arrays_preserve_their_order(values):
    assert sort_document({"producerOrder": values})["producerOrder"] == values


@PROPERTY_SETTINGS
@given(st.lists(JSON_VALUE, max_size=6))
def test_unknown_and_order_significant_arrays_preserve_their_order(values):
    assert sort_document({"producerOrder": values})["producerOrder"] == values


@PROPERTY_SETTINGS
@given(JSON_VALUE)
def test_rendering_parses_and_has_exactly_one_trailing_newline(value):
    rendered = sort_json(json.dumps(value, ensure_ascii=False))

    assert json.loads(rendered) == sort_document(value)
    assert rendered.endswith("\n")
    assert not rendered.endswith("\n\n")


def test_type_aware_boundaries_have_a_total_deterministic_order():
    items = [
        {"SPDXID": float("nan"), "name": "nan"},
        {"SPDXID": float("inf"), "name": "positive-infinity"},
        {"SPDXID": 1.0, "name": "float"},
        {"SPDXID": 1, "name": "integer"},
        {"SPDXID": True, "name": "boolean"},
        {"SPDXID": "1", "name": "string"},
        {"SPDXID": None, "name": "null"},
        {"SPDXID": float("-inf"), "name": "negative-infinity"},
    ]
    expected = [
        "null",
        "boolean",
        "negative-infinity",
        "integer",
        "float",
        "positive-infinity",
        "nan",
        "string",
    ]

    for candidate in (items, list(reversed(items))):
        result = sort_document({"packages": candidate})
        assert [item["name"] for item in result["packages"]] == expected
        assert math.isnan(result["packages"][-2]["SPDXID"])
