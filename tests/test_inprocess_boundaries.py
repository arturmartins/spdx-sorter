"""In-process behavioral tests for package entry points and defensive paths."""

from __future__ import annotations

import builtins
import importlib
import importlib.metadata
import io
import json
import os
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import spdx_sorter.version as version_module
from spdx_sorter import ValidationIssue, ValidationUnavailableError, cli
from spdx_sorter.io import _sync_directory, atomic_write, read_text
from spdx_sorter.validation import _parser_issues, _validation_issue, validate_document
from spdx_sorter.version import detect_spdx_version

UNSORTED = {
    "spdxVersion": "SPDX-2.3",
    "packages": [{"SPDXID": "SPDXRef-B"}, {"SPDXID": "SPDXRef-A"}],
}


def test_cli_main_sorts_stdin_without_spawning_a_process(monkeypatch, capsys):
    """Changing the CLI's stdin branch must still emit canonical JSON."""
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(UNSORTED)))

    assert cli.main([]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["packages"][0]["SPDXID"] == "SPDXRef-A"


def test_cli_main_validation_issues_stop_before_output(monkeypatch, capsys):
    """Changing validation failure handling must prevent a sorted document escaping."""
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(UNSORTED)))
    monkeypatch.setattr(
        cli,
        "validate_document",
        lambda _: (ValidationIssue("bad package"),),
    )

    assert cli.main(["--validate"]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "<stdin>: validation: bad package\n"


def test_cli_main_reports_missing_validation_extra(monkeypatch, capsys):
    """Changing optional-extra handling must retain an actionable installation hint."""
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(UNSORTED)))

    def unavailable(_: object) -> tuple[ValidationIssue, ...]:
        raise ValidationUnavailableError

    monkeypatch.setattr(cli, "validate_document", unavailable)

    assert cli.main(["--validate"]) == 2

    assert "pip install 'spdx-sorter[validation]'" in capsys.readouterr().err


def test_cli_main_replaces_the_requested_file(tmp_path, capsys):
    """Changing in-place dispatch must not leave the input document unsorted."""
    path = tmp_path / "document.spdx.json"
    path.write_text(json.dumps(UNSORTED), encoding="utf-8")

    assert cli.main(["--in-place", str(path)]) == 0

    assert capsys.readouterr().out == ""
    output = json.loads(path.read_text(encoding="utf-8"))
    assert output["packages"][0]["SPDXID"] == "SPDXRef-A"


def test_cli_main_reports_input_decoding_errors(monkeypatch, capsys):
    """Changing JSON error handling must keep malformed stdin from a traceback."""
    monkeypatch.setattr(sys, "stdin", io.StringIO("{broken"))

    assert cli.main([]) == 2

    assert capsys.readouterr().err.startswith("error: ")


def test_cli_check_reports_noncanonical_file_without_replacing_it(tmp_path, capsys):
    """Changing check mode must report unsorted files while leaving them untouched."""
    path = tmp_path / "document.spdx.json"
    original = json.dumps(UNSORTED)
    path.write_text(original, encoding="utf-8")

    assert cli.main(["--check", str(path)]) == 1

    assert capsys.readouterr().err == f"{path}: not sorted\n"
    assert path.read_text(encoding="utf-8") == original


@pytest.mark.parametrize(
    ("document", "warning"),
    [
        (
            {"@context": "https://spdx.org/rdf/3.0.1/spdx-context.jsonld"},
            "warning: SPDX 3.0.1 support is experimental\n",
        ),
        (
            {"spdxVersion": "SPDX-1.2"},
            "warning: SPDX 1.2 is unsupported; sorting conservatively\n",
        ),
    ],
)
def test_cli_main_warns_for_nonstable_versions(monkeypatch, capsys, document, warning):
    """Changing warnings must distinguish experimental and unsupported input."""
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(document)))

    assert cli.main([]) == 0

    assert capsys.readouterr().err == warning


def test_cli_rejects_in_place_stdin_before_reading(monkeypatch):
    """Changing argument validation must reject an in-place stdin request."""
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(UNSORTED)))

    with pytest.raises(SystemExit, match="2"):
        cli.main(["--in-place"])


def test_module_entry_point_exits_with_the_cli_result(monkeypatch, capsys):
    """Changing module startup must still delegate to the packaged CLI."""
    monkeypatch.setattr(sys, "argv", ["spdx_sorter"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(UNSORTED)))

    with pytest.raises(SystemExit, match="0"):
        runpy.run_module("spdx_sorter.__main__", run_name="__main__")

    output = json.loads(capsys.readouterr().out)
    assert output["packages"][0]["SPDXID"] == "SPDXRef-A"


def test_read_text_and_atomic_write_publish_utf8_content(tmp_path):
    """Changing file I/O must preserve UTF-8 text while atomically replacing it."""
    path = tmp_path / "document.spdx.json"
    path.write_text("before", encoding="utf-8")

    atomic_write(path, "after café")

    assert read_text(path) == "after café"


def test_directory_sync_failures_do_not_undo_a_completed_replacement(tmp_path):
    """Changing durability best-effort handling must retain completed writes."""
    path = tmp_path / "document.spdx.json"
    path.write_text("before", encoding="utf-8")

    original_open = os.open

    def open_without_directory_sync(candidate, *args):
        if isinstance(candidate, Path):
            raise OSError("unsupported")
        return original_open(candidate, *args)

    with patch("spdx_sorter.io.os.open", side_effect=open_without_directory_sync):
        atomic_write(path, "after")

    assert path.read_text(encoding="utf-8") == "after"


def test_sync_directory_closes_descriptor_when_fsync_is_unavailable(tmp_path):
    """Changing directory-sync cleanup must close descriptors after an fsync failure."""
    with (
        patch("spdx_sorter.io.os.open", return_value=17),
        patch("spdx_sorter.io.os.fsync", side_effect=OSError("unsupported")),
        patch("spdx_sorter.io.os.close") as close,
    ):
        _sync_directory(tmp_path)

    close.assert_called_once_with(17)


def test_atomic_write_surfaces_primary_error_when_temp_cleanup_fails(tmp_path):
    """Changing failure cleanup must not replace the original after a metadata error."""
    path = tmp_path / "document.spdx.json"
    path.write_text("before", encoding="utf-8")

    with (
        patch("spdx_sorter.io.os.chmod", side_effect=OSError("metadata failed")),
        patch.object(Path, "unlink", side_effect=OSError("cleanup failed")),
        pytest.raises(OSError, match="metadata failed"),
    ):
        atomic_write(path, "after")

    temporary_paths = list(tmp_path.glob(".document.spdx.json.*.tmp"))
    assert path.read_text(encoding="utf-8") == "before"
    assert len(temporary_paths) == 1
    temporary_paths[0].unlink()


def test_parser_errors_are_split_deduplicated_and_have_a_fallback_message():
    """Changing parser exception conversion must keep adapter errors useful."""

    class ParseError(Exception):
        parsing_errors = [
            type("Message", (), {"message": "second\nfirst\nsecond"})(),
            type("Message", (), {"message": ""})(),
        ]

    assert _parser_issues(ParseError()) == (
        ValidationIssue("first"),
        ValidationIssue("second"),
    )
    assert _parser_issues(Exception()) == (
        ValidationIssue("unable to parse SPDX document"),
    )


def test_validation_message_uses_parent_context_and_string_fallbacks():
    """Changing adapter conversion must retain incomplete upstream context."""

    class Message:
        validation_message = object()
        context = type(
            "Context",
            (),
            {"spdx_id": None, "parent_id": "SPDXRef-parent", "element_type": 3},
        )()

        def __str__(self):
            return "fallback message"

    assert _validation_issue(Message()) == ValidationIssue(
        "fallback message", "3", "SPDXRef-parent"
    )


def test_validation_parser_exception_uses_project_owned_issues(monkeypatch):
    """Changing parser exception handling must not leak third-party exceptions."""

    class Parser:
        def parse(self, _: object) -> object:
            error = Exception("raw parser error")
            error.parsing_errors = [type("Message", (), {"message": "bad input"})()]
            raise error

    parser_module = "spdx_tools.spdx.parser.jsonlikedict.json_like_dict_parser"
    parser = __import__(parser_module, fromlist=["JsonLikeDictParser"])
    monkeypatch.setattr(parser, "JsonLikeDictParser", Parser)

    assert validate_document({"spdxVersion": "SPDX-2.3"}) == (
        ValidationIssue("bad input"),
    )


def test_validation_unavailable_import_becomes_project_error(monkeypatch):
    """Changing optional-dependency imports must preserve the public exception type."""
    original_import = builtins.__import__

    def missing_spdx_tools(name, *args, **kwargs):
        if name.startswith("spdx_tools"):
            raise ModuleNotFoundError(name=name)
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing_spdx_tools)

    with pytest.raises(ValidationUnavailableError):
        validate_document({"spdxVersion": "SPDX-2.3"})


def test_version_detection_handles_empty_alternate_and_non_string_fields():
    """Changing version boundaries must not classify malformed metadata as supported."""
    assert detect_spdx_version([]) is None
    alternate = detect_spdx_version({"spdxVersion": "", "specVersion": "SPDX-2.2"})
    assert alternate is not None
    assert alternate.support == "stable"
    assert detect_spdx_version({"spdxVersion": 23, "@context": 1}) is None


def test_version_module_uses_fallback_without_installed_distribution_metadata():
    """Changing source-tree fallback must retain a usable public version string."""
    missing = importlib.metadata.PackageNotFoundError("spdx-sorter")
    with patch("importlib.metadata.version", side_effect=missing):
        fallback_module = importlib.reload(version_module)
        assert fallback_module.__version__ == "0.1.0"

    importlib.reload(version_module)
