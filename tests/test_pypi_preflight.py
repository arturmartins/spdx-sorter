from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

_HELPER_PATH = Path(__file__).parents[1] / "scripts" / "pypi_preflight.py"
_HELPER_SPEC = importlib.util.spec_from_file_location("pypi_preflight", _HELPER_PATH)
if _HELPER_SPEC is None or _HELPER_SPEC.loader is None:
    raise RuntimeError(f"cannot load {_HELPER_PATH}")
_HELPER_MODULE: ModuleType = importlib.util.module_from_spec(_HELPER_SPEC)
_HELPER_SPEC.loader.exec_module(_HELPER_MODULE)
PreflightError = _HELPER_MODULE.PreflightError
filter_uploads = _HELPER_MODULE.filter_uploads
parse_release_files = _HELPER_MODULE.parse_release_files


def _write(path: Path, content: bytes) -> str:
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def test_absent_release_keeps_every_local_file(tmp_path: Path) -> None:
    wheel = tmp_path / "spdx_sorter-0.1.0-py3-none-any.whl"
    source = tmp_path / "spdx-sorter-0.1.0.tar.gz"
    _write(wheel, b"wheel")
    _write(source, b"source")

    remaining = filter_uploads(tmp_path, None)

    assert remaining == [source, wheel]
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "spdx-sorter-0.1.0.tar.gz",
        "spdx_sorter-0.1.0-py3-none-any.whl",
    ]


def test_exact_match_is_removed_from_upload_set(tmp_path: Path) -> None:
    wheel = tmp_path / "spdx_sorter-0.1.0-py3-none-any.whl"
    digest = _write(wheel, b"wheel")

    remaining = filter_uploads(tmp_path, {wheel.name: digest})

    assert remaining == []
    assert not wheel.exists()


def test_digest_conflict_fails_before_removing_any_file(tmp_path: Path) -> None:
    wheel = tmp_path / "spdx_sorter-0.1.0-py3-none-any.whl"
    source = tmp_path / "spdx-sorter-0.1.0.tar.gz"
    _write(wheel, b"wheel")
    _write(source, b"source")

    with pytest.raises(PreflightError, match="digest conflict"):
        filter_uploads(tmp_path, {wheel.name: "0" * 64})

    assert wheel.exists()
    assert source.exists()


def test_mixed_upload_set_removes_only_exact_matches(tmp_path: Path) -> None:
    wheel = tmp_path / "spdx_sorter-0.1.0-py3-none-any.whl"
    source = tmp_path / "spdx-sorter-0.1.0.tar.gz"
    wheel_digest = _write(wheel, b"wheel")
    _write(source, b"source")

    remaining = filter_uploads(tmp_path, {wheel.name: wheel_digest})

    assert remaining == [source]
    assert not wheel.exists()
    assert source.exists()


def test_malformed_release_response_is_rejected() -> None:
    with pytest.raises(PreflightError, match="urls"):
        parse_release_files({"info": {"version": "0.1.0"}}, "0.1.0")


def test_empty_release_response_is_rejected() -> None:
    with pytest.raises(PreflightError, match="non-empty urls"):
        parse_release_files({"info": {"version": "0.1.0"}, "urls": []}, "0.1.0")


def test_release_response_requires_exact_requested_version() -> None:
    payload = {
        "info": {"version": "0.1.1"},
        "urls": [
            {
                "filename": "spdx-sorter-0.1.0.tar.gz",
                "digests": {"sha256": "a" * 64},
            }
        ],
    }

    with pytest.raises(PreflightError, match="version"):
        parse_release_files(payload, "0.1.0")


def test_release_response_requires_version_field() -> None:
    payload = {
        "info": {},
        "urls": [
            {
                "filename": "spdx-sorter-0.1.0.tar.gz",
                "digests": {"sha256": "a" * 64},
            }
        ],
    }

    with pytest.raises(PreflightError, match="version"):
        parse_release_files(payload, "0.1.0")


def test_release_response_must_contain_valid_sha256() -> None:
    payload = {
        "info": {"version": "0.1.0"},
        "urls": [
            {
                "filename": "spdx-sorter-0.1.0.tar.gz",
                "digests": {"sha256": "not-a-digest"},
            }
        ],
    }

    with pytest.raises(PreflightError, match="sha256"):
        parse_release_files(payload, "0.1.0")


def test_release_response_json_is_decoded_without_network() -> None:
    payload = {
        "urls": [
            {
                "filename": "spdx-sorter-0.1.0.tar.gz",
                "digests": {"sha256": "a" * 64},
            }
        ]
    }

    decoded = json.loads(json.dumps({**payload, "info": {"version": "0.1.0"}}))

    assert parse_release_files(decoded, "0.1.0") == {
        "spdx-sorter-0.1.0.tar.gz": "a" * 64
    }
