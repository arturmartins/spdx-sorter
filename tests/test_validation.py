"""Contract tests for the public SPDX validation adapter."""

import importlib.util
import os
import subprocess
import sys
import unittest
from dataclasses import dataclass
from enum import Enum

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(TESTS_DIR)
SRC_DIR = os.path.join(REPO_DIR, "src")
sys.path.insert(0, SRC_DIR)

from spdx_sorter import (  # noqa: E402
    ValidationIssue,
    validate_document,
)
from spdx_sorter.validation import _validation_issue  # noqa: E402

HAS_SPDX_TOOLS = importlib.util.find_spec("spdx_tools") is not None


class ElementType(Enum):
    PACKAGE = "Package"


@dataclass(frozen=True)
class ValidationContext:
    spdx_id: str | None
    parent_id: str | None
    element_type: ElementType


@dataclass(frozen=True)
class ValidationMessage:
    validation_message: str
    context: ValidationContext


def minimal_spdx_document():
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "validation-example",
        "documentNamespace": "https://example.com/spdx/validation-example",
        "creationInfo": {
            "created": "2026-08-28T00:00:00Z",
            "creators": ["Tool: spdx-sorter-0.1.0"],
        },
        "packages": [
            {
                "SPDXID": "SPDXRef-Package",
                "name": "validation-example-package",
                "downloadLocation": "NOASSERTION",
            }
        ],
    }


class ValidationTests(unittest.TestCase):
    def test_validation_message_context_is_adapted_at_boundary(self):
        upstream_message = ValidationMessage(
            validation_message="package has an invalid license",
            context=ValidationContext(
                spdx_id="SPDXRef-Package",
                parent_id="SPDXRef-Document",
                element_type=ElementType.PACKAGE,
            ),
        )

        self.assertEqual(
            _validation_issue(upstream_message),
            ValidationIssue(
                message="package has an invalid license",
                location="PACKAGE",
                element_id="SPDXRef-Package",
            ),
        )

    @unittest.skipUnless(HAS_SPDX_TOOLS, "spdx-tools validation extra unavailable")
    def test_valid_spdx_2_3_document_has_no_issues(self):
        issues = validate_document(minimal_spdx_document())

        self.assertEqual(issues, ())

    @unittest.skipUnless(HAS_SPDX_TOOLS, "spdx-tools validation extra unavailable")
    def test_invalid_spdx_document_returns_stable_project_issues(self):
        document = minimal_spdx_document()
        del document["creationInfo"]

        issues = validate_document(document)

        self.assertTrue(issues)
        self.assertTrue(all(isinstance(issue, ValidationIssue) for issue in issues))
        self.assertTrue(any("creation" in issue.message.lower() for issue in issues))

    def test_experimental_version_is_not_presented_as_validated(self):
        issues = validate_document(
            {
                "@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
                "type": "SpdxDocument",
            }
        )

        self.assertEqual(
            issues,
            (
                ValidationIssue(
                    message="validation supports SPDX 2.2 and 2.3; detected 3.0.1"
                ),
            ),
        )

    def test_unknown_version_is_not_presented_as_validated(self):
        self.assertEqual(
            validate_document({"name": "not-versioned"}),
            (
                ValidationIssue(
                    message=(
                        "validation supports SPDX 2.2 and 2.3; "
                        "SPDX version could not be detected"
                    )
                ),
            ),
        )

    def test_validation_issue_is_immutable(self):
        issue = ValidationIssue("problem", location="creationInfo", element_id="x")

        with self.assertRaises(AttributeError):
            issue.message = "changed"

    def test_missing_validation_extra_raises_project_error(self):
        script = """
import sys
sys.modules['spdx_tools'] = None
from spdx_sorter import ValidationUnavailableError, validate_document
try:
    validate_document({'spdxVersion': 'SPDX-2.3'})
except ValidationUnavailableError:
    raise SystemExit(0)
raise SystemExit(1)
"""
        environment = os.environ.copy()
        environment["PYTHONPATH"] = SRC_DIR

        process = subprocess.run(
            [sys.executable, "-c", script],
            cwd=REPO_DIR,
            env=environment,
            capture_output=True,
            text=True,
        )

        self.assertEqual(process.returncode, 0, process.stderr)


if __name__ == "__main__":
    unittest.main()
