"""Behavior tests for the public spdx_sorter package API."""

import copy
import json
import os
import sys
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(TESTS_DIR)
SRC_DIR = os.path.join(REPO_DIR, "src")
sys.path.insert(0, SRC_DIR)

from spdx_sorter import sort_document, sort_json  # noqa: E402


class PublicApiTests(unittest.TestCase):
    def test_stable_object_array_rules(self):
        cases = {
            "packages": (
                [{"SPDXID": "SPDXRef-B"}, {"SPDXID": "SPDXRef-A"}],
                "SPDXID",
                "SPDXRef-A",
            ),
            "files": (
                [{"SPDXID": "SPDXRef-File-B"}, {"SPDXID": "SPDXRef-File-A"}],
                "SPDXID",
                "SPDXRef-File-A",
            ),
            "relationships": (
                [
                    {
                        "spdxElementId": "SPDXRef-B",
                        "relationshipType": "DEPENDS_ON",
                        "relatedSpdxElement": "SPDXRef-C",
                    },
                    {
                        "spdxElementId": "SPDXRef-A",
                        "relationshipType": "CONTAINS",
                        "relatedSpdxElement": "SPDXRef-B",
                    },
                ],
                "spdxElementId",
                "SPDXRef-A",
            ),
            "externalRefs": (
                [
                    {"referenceCategory": "SECURITY", "referenceType": "cpe23Type"},
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                    },
                ],
                "referenceCategory",
                "PACKAGE-MANAGER",
            ),
            "annotations": (
                [
                    {"annotationDate": "2026-02-01", "annotator": "Tool: b"},
                    {"annotationDate": "2026-01-01", "annotator": "Tool: a"},
                ],
                "annotationDate",
                "2026-01-01",
            ),
            "checksums": (
                [
                    {"algorithm": "SHA256", "checksumValue": "b"},
                    {"algorithm": "SHA1", "checksumValue": "a"},
                ],
                "algorithm",
                "SHA1",
            ),
            "hasExtractedLicensingInfos": (
                [{"licenseId": "LicenseRef-B"}, {"licenseId": "LicenseRef-A"}],
                "licenseId",
                "LicenseRef-A",
            ),
            "snippets": (
                [{"SPDXID": "SPDXRef-Snippet-B"}, {"SPDXID": "SPDXRef-Snippet-A"}],
                "SPDXID",
                "SPDXRef-Snippet-A",
            ),
            "externalDocumentRefs": (
                [
                    {"externalDocumentId": "DocumentRef-B"},
                    {"externalDocumentId": "DocumentRef-A"},
                ],
                "externalDocumentId",
                "DocumentRef-A",
            ),
        }

        for key, (values, identity, expected) in cases.items():
            with self.subTest(key=key):
                result = sort_document({key: values})
                self.assertEqual(result[key][0][identity], expected)

    def test_experimental_elements_rule(self):
        document = {
            "elements": [
                {"spdxId": "urn:spdx:b", "type": "Package"},
                {"spdxId": "urn:spdx:a", "type": "File"},
            ]
        }

        result = sort_document(document)

        self.assertEqual(
            [element["spdxId"] for element in result["elements"]],
            ["urn:spdx:a", "urn:spdx:b"],
        )

    def test_sort_document_does_not_mutate_input(self):
        document = {
            "packages": [
                {"SPDXID": "SPDXRef-B", "name": "b"},
                {"SPDXID": "SPDXRef-A", "name": "a"},
            ],
            "documentDescribes": ["SPDXRef-B", "SPDXRef-A"],
        }
        original = copy.deepcopy(document)

        result = sort_document(document)

        self.assertEqual(document, original)
        self.assertIsNot(result, document)
        self.assertIsNot(result["packages"][0], document["packages"][0])
        self.assertEqual(
            [package["SPDXID"] for package in result["packages"]],
            ["SPDXRef-A", "SPDXRef-B"],
        )

    def test_type_aware_tie_breaker_is_independent_of_input_order(self):
        number_id = {"SPDXID": 1, "name": "same"}
        string_id = {"SPDXID": "1", "name": "same"}

        forward = sort_document({"packages": [number_id, string_id]})
        reverse = sort_document({"packages": [string_id, number_id]})

        self.assertEqual(forward, reverse)

    def test_nan_identity_values_have_deterministic_tie_breakers(self):
        forward = sort_document(
            {
                "packages": [
                    {"SPDXID": float("nan"), "name": "b"},
                    {"SPDXID": float("nan"), "name": "a"},
                ]
            }
        )
        reverse = sort_document(
            {
                "packages": [
                    {"SPDXID": float("nan"), "name": "a"},
                    {"SPDXID": float("nan"), "name": "b"},
                ]
            }
        )

        self.assertEqual([item["name"] for item in forward["packages"]], ["a", "b"])
        self.assertEqual([item["name"] for item in reverse["packages"]], ["a", "b"])

    def test_nonfinite_and_finite_identity_values_have_a_total_order(self):
        values = [
            {"SPDXID": float("nan"), "name": "nan"},
            {"SPDXID": float("inf"), "name": "positive infinity"},
            {"SPDXID": 1.0, "name": "float"},
            {"SPDXID": 1, "name": "integer"},
            {"SPDXID": float("-inf"), "name": "negative infinity"},
        ]

        result = sort_document({"packages": values})

        self.assertEqual(
            [item["name"] for item in result["packages"]],
            ["negative infinity", "integer", "float", "positive infinity", "nan"],
        )

    def test_boolean_identity_remains_distinct_from_numeric_identity(self):
        result = sort_document(
            {
                "packages": [
                    {"SPDXID": 1, "name": "number"},
                    {"SPDXID": True, "name": "boolean"},
                ]
            }
        )

        self.assertEqual(
            [item["name"] for item in result["packages"]],
            ["boolean", "number"],
        )

    def test_container_identity_values_have_a_deterministic_order(self):
        """Changing heterogeneous keys must not make sorting raise TypeError."""
        result = sort_document(
            {
                "packages": [
                    {"SPDXID": {"name": "object"}, "name": "object"},
                    {"SPDXID": ["list"], "name": "list"},
                ]
            }
        )

        self.assertEqual(
            [item["name"] for item in result["packages"]], ["list", "object"]
        )

    def test_malformed_recognized_array_preserves_order(self):
        document = {
            "packages": [
                {"name": "second", "SPDXID": "SPDXRef-B"},
                "producer-extension",
                {"name": "first", "SPDXID": "SPDXRef-A"},
            ]
        }

        result = sort_document(document)

        self.assertEqual(
            result["packages"],
            [
                {"SPDXID": "SPDXRef-B", "name": "second"},
                "producer-extension",
                {"SPDXID": "SPDXRef-A", "name": "first"},
            ],
        )

    def test_sort_json_has_stable_rendering(self):
        text = '{"z": 1, "name": "café", "a": 2}'

        result = sort_json(text)

        self.assertEqual(
            result,
            '{\n  "a": 2,\n  "name": "café",\n  "z": 1\n}\n',
        )
        self.assertEqual(json.loads(result), {"a": 2, "name": "café", "z": 1})

    def test_tied_items_with_nested_set_arrays_converge_in_one_pass(self):
        document = {
            "packages": [
                {
                    "SPDXID": "SPDXRef-Same",
                    "documentDescribes": ["SPDXRef-Z", "SPDXRef-A"],
                },
                {
                    "SPDXID": "SPDXRef-Same",
                    "documentDescribes": ["SPDXRef-M", "SPDXRef-B"],
                },
            ]
        }

        once = sort_document(document)

        self.assertEqual(sort_document(once), once)

    def test_nested_children_are_canonicalized_before_parent_tie_breaking(self):
        """Changing child-first recursion must not make a second sort reorder ties."""
        document = {
            "packages": [
                {
                    "SPDXID": "SPDXRef-Same",
                    "checksums": [
                        {"algorithm": "SHA256", "checksumValue": "b"},
                        {"algorithm": "SHA1", "checksumValue": "a"},
                    ],
                },
                {
                    "SPDXID": "SPDXRef-Same",
                    "checksums": [
                        {"algorithm": "SHA512", "checksumValue": "d"},
                        {"algorithm": "SHA1", "checksumValue": "c"},
                    ],
                },
            ]
        }

        once = sort_document(document)

        self.assertEqual(sort_document(once), once)

    def test_unknown_primitive_array_preserves_order(self):
        document = {"producerOrder": ["z", "a", "m"]}

        result = sort_document(document)

        self.assertEqual(result["producerOrder"], ["z", "a", "m"])

    def test_unknown_object_array_preserves_order(self):
        document = {
            "producerOrder": [
                {"rank": "z", "name": "first"},
                {"rank": "a", "name": "second"},
            ]
        }

        result = sort_document(document)

        self.assertEqual(
            [entry["name"] for entry in result["producerOrder"]],
            ["first", "second"],
        )


if __name__ == "__main__":
    unittest.main()
