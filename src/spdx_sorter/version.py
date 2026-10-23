"""SPDX version detection without validation side effects."""

from __future__ import annotations

import re
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Literal

from spdx_sorter.sorting import JSONValue

SupportLevel = Literal["stable", "experimental", "unsupported"]

_STABLE_VERSIONS = frozenset({"2.2", "2.3"})
_CONTEXT_PATTERN = re.compile(
    r"^https://spdx\.org/rdf/(?P<version>\d+\.\d+(?:\.\d+)?)/spdx-context\.jsonld$"
)

try:
    __version__ = version("spdx-sorter")
except PackageNotFoundError:
    __version__ = "0.1.0"


@dataclass(frozen=True)
class SpdxVersion:
    """Detected SPDX version and this package's support classification."""

    label: str
    normalized: str
    support: SupportLevel


def _classify(label: str, normalized: str) -> SpdxVersion:
    if normalized in _STABLE_VERSIONS:
        support: SupportLevel = "stable"
    elif normalized.startswith("3."):
        support = "experimental"
    else:
        support = "unsupported"
    return SpdxVersion(label=label, normalized=normalized, support=support)


def detect_spdx_version(value: JSONValue) -> SpdxVersion | None:
    """Detect an SPDX version from recognized top-level document fields."""
    if not isinstance(value, dict):
        return None

    spdx_version = value.get("spdxVersion")
    if isinstance(spdx_version, str) and spdx_version:
        normalized = spdx_version.removeprefix("SPDX-")
        return _classify(spdx_version, normalized)

    spec_version = value.get("specVersion")
    if isinstance(spec_version, str) and spec_version:
        normalized = spec_version.removeprefix("SPDX-")
        return _classify(spec_version, normalized)

    context = value.get("@context")
    if isinstance(context, str):
        match = _CONTEXT_PATTERN.fullmatch(context)
        if match is not None:
            normalized = match.group("version")
            return _classify(f"SPDX-{normalized}", normalized)

    return None
