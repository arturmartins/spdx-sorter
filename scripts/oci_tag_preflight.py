"""Fail-closed OCI exact-tag preflight using the Docker Registry HTTP API."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from email.message import Message
from typing import Any, Protocol, cast

OCI_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
MANIFEST_ACCEPT = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)


class PreflightError(RuntimeError):
    """Registry preflight failed closed."""


class Response(Protocol):
    headers: Message[str, str]

    def __enter__(self) -> Response: ...

    def __exit__(self, *args: object) -> bool | None: ...

    def read(self) -> bytes: ...


class OpenUrl(Protocol):
    def __call__(
        self, request: urllib.request.Request, *, timeout: int
    ) -> Response: ...


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Return direct 3xx responses to the caller instead of following Location."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: object,
        code: int,
        msg: str,
        headers: Message[str, str],
        newurl: str,
    ) -> urllib.request.Request | None:
        return None


@dataclass(frozen=True)
class Registry:
    api_base: str
    auth_url: str
    service: str


REGISTRIES = {
    "ghcr.io": Registry(
        api_base="https://ghcr.io/v2",
        auth_url="https://ghcr.io/token",
        service="ghcr.io",
    ),
    "docker.io": Registry(
        api_base="https://registry-1.docker.io/v2",
        auth_url="https://auth.docker.io/token",
        service="registry.docker.io",
    ),
}
NO_REDIRECT_OPENER = urllib.request.build_opener(NoRedirectHandler)


def _basic_auth(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
    return f"Basic {token}"


def _request(
    opener: OpenUrl,
    url: str,
    *,
    method: str,
    headers: dict[str, str],
    timeout: int,
) -> tuple[int, Message[str, str], bytes]:
    request = urllib.request.Request(url, method=method, headers=headers)  # noqa: S310
    try:
        with opener(request, timeout=timeout) as response:
            return _response_status(response), response.headers, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers, error.read()
    except (TimeoutError, urllib.error.URLError, OSError) as error:
        raise PreflightError(f"registry request failed: {error}") from error


def _response_status(response: Response) -> int:
    status = getattr(response, "status", None)
    if status is None:
        getcode = getattr(response, "getcode", None)
        if callable(getcode):
            status = getcode()
    if not isinstance(status, int):
        raise PreflightError("registry response omitted HTTP status")
    return status


def _registry(name: str) -> Registry:
    try:
        return REGISTRIES[name]
    except KeyError as error:
        supported = ", ".join(sorted(REGISTRIES))
        raise PreflightError(
            f"unsupported registry {name!r}; expected one of {supported}"
        ) from error


def _bearer_token(
    registry: Registry,
    repository: str,
    username: str,
    password: str,
    *,
    opener: OpenUrl,
    timeout: int,
) -> str:
    query = urllib.parse.urlencode(
        {
            "service": registry.service,
            "scope": f"repository:{repository}:pull",
        }
    )
    status, _headers, body = _request(
        opener,
        f"{registry.auth_url}?{query}",
        method="GET",
        headers={
            "Accept": "application/json",
            "Authorization": _basic_auth(username, password),
        },
        timeout=timeout,
    )
    if status != 200:
        raise PreflightError(f"registry token endpoint returned HTTP {status}")

    try:
        payload: Any = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PreflightError(
            "registry token endpoint returned malformed JSON"
        ) from error

    token = payload.get("token") or payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise PreflightError("registry token endpoint returned no bearer token")
    return token


def _manifest_digest(
    registry: Registry,
    repository: str,
    tag: str,
    bearer_token: str,
    *,
    opener: OpenUrl,
    timeout: int,
) -> str | None:
    manifest_url = f"{registry.api_base}/{repository}/manifests/{tag}"
    headers = {
        "Accept": MANIFEST_ACCEPT,
        "Authorization": f"Bearer {bearer_token}",
    }
    status, response_headers, _body = _request(
        opener,
        manifest_url,
        method="HEAD",
        headers=headers,
        timeout=timeout,
    )
    if status == 405:
        status, response_headers, _body = _request(
            opener,
            manifest_url,
            method="GET",
            headers=headers,
            timeout=timeout,
        )
    if status == 404:
        return None
    if status != 200:
        raise PreflightError(f"manifest endpoint returned HTTP {status}")

    digest = response_headers.get("Docker-Content-Digest")
    if digest is None:
        raise PreflightError("manifest response omitted Docker-Content-Digest")
    if not OCI_DIGEST.fullmatch(digest):
        raise PreflightError("manifest response returned malformed digest")
    return digest


def check_exact_tag(
    registry_name: str,
    repository: str,
    tag: str,
    expected_digest: str,
    username: str,
    password: str,
    *,
    opener: OpenUrl | None = None,
    timeout: int = 20,
) -> str:
    if not OCI_DIGEST.fullmatch(expected_digest):
        raise PreflightError("expected digest must be sha256:<64 lowercase hex>")
    if not username or not password:
        raise PreflightError("registry username and password must be set")

    if opener is None:
        opener = _urlopen

    registry = _registry(registry_name)
    token = _bearer_token(
        registry,
        repository,
        username,
        password,
        opener=opener,
        timeout=timeout,
    )
    digest = _manifest_digest(
        registry,
        repository,
        tag,
        token,
        opener=opener,
        timeout=timeout,
    )
    if digest is None:
        return "absent"
    if digest != expected_digest:
        raise PreflightError(
            f"immutable tag digest conflict: expected {expected_digest}, found {digest}"
        )
    return "matches"


def _urlopen(request: urllib.request.Request, *, timeout: int) -> Response:
    return cast(Response, NO_REDIRECT_OPENER.open(request, timeout=timeout))  # noqa: S310


def main(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True, choices=sorted(REGISTRIES))
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--expected-digest", required=True)
    parser.add_argument("--username-env", required=True)
    parser.add_argument("--password-env", required=True)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(arguments)

    username = os.environ.get(args.username_env, "")
    password = os.environ.get(args.password_env, "")
    try:
        result = check_exact_tag(
            args.registry,
            args.repository,
            args.tag,
            args.expected_digest,
            username,
            password,
            timeout=args.timeout,
        )
    except PreflightError as error:
        print(f"OCI exact-tag preflight failed: {error}", file=sys.stderr)
        return 1

    image_ref = f"{args.registry}/{args.repository}:{args.tag}"
    print(f"OCI exact-tag preflight {result}: {image_ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
