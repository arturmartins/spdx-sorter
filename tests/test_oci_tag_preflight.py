from __future__ import annotations

import importlib.util
import sys
from email.message import Message
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

HELPER = Path(__file__).parents[1] / "scripts/oci_tag_preflight.py"
SPEC = importlib.util.spec_from_file_location("oci_tag_preflight", HELPER)
assert SPEC is not None
assert SPEC.loader is not None
oci_tag_preflight = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = oci_tag_preflight
SPEC.loader.exec_module(oci_tag_preflight)
NoRedirectHandler = oci_tag_preflight.NoRedirectHandler
PreflightError = oci_tag_preflight.PreflightError
check_exact_tag = oci_tag_preflight.check_exact_tag

EXPECTED_DIGEST = "sha256:" + "a" * 64
OTHER_DIGEST = "sha256:" + "b" * 64


class FakeResponse:
    def __init__(
        self,
        body: bytes = b"",
        digest: str | None = None,
        status: int = 200,
    ) -> None:
        self.headers = Message()
        if digest is not None:
            self.headers["Docker-Content-Digest"] = digest
        self.body = body
        self.status = status

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


_created_errors: list[HTTPError] = []


@pytest.fixture(autouse=True)
def _close_http_errors():
    """Close fabricated errors; Python 3.14 warns when unclosed ones are collected."""
    yield
    while _created_errors:
        _created_errors.pop().close()


def http_error(status: int, body: bytes = b"") -> HTTPError:
    error = HTTPError(
        url="https://example.invalid/v2/repo/manifests/1.2.3",
        code=status,
        msg="error",
        hdrs=Message(),
        fp=BytesIO(body),
    )
    _created_errors.append(error)
    return error


def opener_for(*items: FakeResponse | BaseException):
    calls = []
    queue = list(items)

    def opener(request, *, timeout):
        calls.append((request, timeout))
        item = queue.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    opener.calls = calls  # type: ignore[attr-defined]
    return opener


def token_response() -> FakeResponse:
    return FakeResponse(b'{"token": "registry-token"}')


def test_ghcr_exact_tag_match_checks_manifest_with_bearer_token() -> None:
    opener = opener_for(token_response(), FakeResponse(digest=EXPECTED_DIGEST))

    result = check_exact_tag(
        "ghcr.io",
        "arturmartins/spdx-sorter",
        "1.2.3",
        EXPECTED_DIGEST,
        "actor",
        "token",
        opener=opener,
    )

    assert result == "matches"
    token_request = opener.calls[0][0]
    manifest_request = opener.calls[1][0]
    assert token_request.full_url.startswith("https://ghcr.io/token?")
    assert "repository%3Aarturmartins%2Fspdx-sorter%3Apull" in token_request.full_url
    assert token_request.headers["Authorization"].startswith("Basic ")
    assert manifest_request.get_method() == "HEAD"
    assert manifest_request.full_url == (
        "https://ghcr.io/v2/arturmartins/spdx-sorter/manifests/1.2.3"
    )
    assert manifest_request.headers["Authorization"] == "Bearer registry-token"


def test_docker_hub_exact_tag_absent_only_on_http_404() -> None:
    opener = opener_for(token_response(), http_error(404, b"unauthorized"))

    assert (
        check_exact_tag(
            "docker.io",
            "arturmartins/spdx-sorter",
            "1.2.3",
            EXPECTED_DIGEST,
            "docker-user",
            "docker-token",
            opener=opener,
        )
        == "absent"
    )
    assert opener.calls[0][0].full_url.startswith("https://auth.docker.io/token?")
    assert opener.calls[1][0].full_url == (
        "https://registry-1.docker.io/v2/arturmartins/spdx-sorter/manifests/1.2.3"
    )


@pytest.mark.parametrize("status", [201, 202])
def test_token_endpoint_requires_exact_http_200(status: int) -> None:
    opener = opener_for(FakeResponse(b'{"token": "registry-token"}', status=status))

    with pytest.raises(PreflightError, match=f"HTTP {status}"):
        check_exact_tag(
            "ghcr.io",
            "arturmartins/spdx-sorter",
            "1.2.3",
            EXPECTED_DIGEST,
            "actor",
            "token",
            opener=opener,
        )


@pytest.mark.parametrize("status", [201, 202])
def test_manifest_endpoint_requires_exact_http_200(status: int) -> None:
    opener = opener_for(
        token_response(),
        FakeResponse(digest=EXPECTED_DIGEST, status=status),
    )

    with pytest.raises(PreflightError, match=f"HTTP {status}"):
        check_exact_tag(
            "ghcr.io",
            "arturmartins/spdx-sorter",
            "1.2.3",
            EXPECTED_DIGEST,
            "actor",
            "token",
            opener=opener,
        )


@pytest.mark.parametrize("status", [301, 302, 307, 308])
def test_token_redirects_fail_closed_without_manifest_request(status: int) -> None:
    opener = opener_for(http_error(status, b'{"token": "registry-token"}'))

    with pytest.raises(PreflightError, match=f"HTTP {status}"):
        check_exact_tag(
            "ghcr.io",
            "arturmartins/spdx-sorter",
            "1.2.3",
            EXPECTED_DIGEST,
            "actor",
            "token",
            opener=opener,
        )

    assert len(opener.calls) == 1


@pytest.mark.parametrize("status", [301, 302, 307, 308])
def test_manifest_redirects_fail_closed_without_following_location(status: int) -> None:
    opener = opener_for(token_response(), http_error(status, b"not found"))

    with pytest.raises(PreflightError, match=f"HTTP {status}"):
        check_exact_tag(
            "ghcr.io",
            "arturmartins/spdx-sorter",
            "1.2.3",
            EXPECTED_DIGEST,
            "actor",
            "token",
            opener=opener,
        )

    assert len(opener.calls) == 2
    assert opener.calls[1][0].get_method() == "HEAD"


def test_no_redirect_handler_refuses_to_forward_authorization() -> None:
    request = Request(
        "https://ghcr.io/v2/arturmartins/spdx-sorter/manifests/1.2.3",
        headers={"Authorization": "Bearer registry-token"},
    )
    headers = Message()
    headers["Location"] = "https://example.invalid/capture"

    redirected = NoRedirectHandler().redirect_request(
        request,
        None,
        302,
        "Found",
        headers,
        "https://example.invalid/capture",
    )

    assert redirected is None


@pytest.mark.parametrize("status", [401, 403, 429, 500, 503])
def test_manifest_errors_fail_closed_even_with_misleading_not_found_body(
    status: int,
) -> None:
    opener = opener_for(token_response(), http_error(status, b"manifest unknown"))

    with pytest.raises(PreflightError, match=f"HTTP {status}"):
        check_exact_tag(
            "docker.io",
            "arturmartins/spdx-sorter",
            "1.2.3",
            EXPECTED_DIGEST,
            "docker-user",
            "docker-token",
            opener=opener,
        )


def test_manifest_digest_mismatch_fails_closed() -> None:
    opener = opener_for(token_response(), FakeResponse(digest=OTHER_DIGEST))

    with pytest.raises(PreflightError, match="digest conflict"):
        check_exact_tag(
            "ghcr.io",
            "arturmartins/spdx-sorter",
            "1.2.3",
            EXPECTED_DIGEST,
            "actor",
            "token",
            opener=opener,
        )


@pytest.mark.parametrize("digest", [None, "sha256:not-hex"])
def test_missing_or_malformed_manifest_digest_fails_closed(
    digest: str | None,
) -> None:
    opener = opener_for(token_response(), FakeResponse(digest=digest))

    with pytest.raises(PreflightError, match="[Dd]igest"):
        check_exact_tag(
            "ghcr.io",
            "arturmartins/spdx-sorter",
            "1.2.3",
            EXPECTED_DIGEST,
            "actor",
            "token",
            opener=opener,
        )


def test_head_method_not_allowed_falls_back_to_get_without_accepting_errors() -> None:
    opener = opener_for(
        token_response(),
        http_error(405, b""),
        FakeResponse(digest=EXPECTED_DIGEST),
    )

    assert (
        check_exact_tag(
            "ghcr.io",
            "arturmartins/spdx-sorter",
            "1.2.3",
            EXPECTED_DIGEST,
            "actor",
            "token",
            opener=opener,
        )
        == "matches"
    )
    assert opener.calls[1][0].get_method() == "HEAD"
    assert opener.calls[2][0].get_method() == "GET"


def test_network_error_fails_closed() -> None:
    opener = opener_for(token_response(), URLError("temporary failure"))

    with pytest.raises(PreflightError, match="registry request failed"):
        check_exact_tag(
            "ghcr.io",
            "arturmartins/spdx-sorter",
            "1.2.3",
            EXPECTED_DIGEST,
            "actor",
            "token",
            opener=opener,
        )


def test_malformed_token_response_fails_closed() -> None:
    opener = opener_for(FakeResponse(b'{"token": ""}'))

    with pytest.raises(PreflightError, match="no bearer token"):
        check_exact_tag(
            "ghcr.io",
            "arturmartins/spdx-sorter",
            "1.2.3",
            EXPECTED_DIGEST,
            "actor",
            "token",
            opener=opener,
        )
