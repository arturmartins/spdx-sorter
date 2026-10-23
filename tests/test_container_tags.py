import importlib.util
from pathlib import Path

import pytest

HELPER = Path(__file__).parents[1] / "scripts/container_tags.py"
SPEC = importlib.util.spec_from_file_location("container_tags", HELPER)
assert SPEC is not None
assert SPEC.loader is not None
container_tags_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(container_tags_module)
container_tags = container_tags_module.container_tags


def test_stable_release_gets_exact_minor_major_and_latest_tags() -> None:
    assert container_tags("1.2.3") == ["1.2.3", "1.2", "1", "latest"]


@pytest.mark.parametrize(
    "version",
    ["1.2.3-rc.1", "1.2.3-alpha", "1.2.3-0"],
)
def test_prerelease_gets_exact_tag_only(version: str) -> None:
    assert container_tags(version) == [version]


@pytest.mark.parametrize(
    "version",
    ["01.2.3", "1.02.3", "1.2", "1.2.3+build.1"],
)
def test_non_canonical_versions_are_rejected(version: str) -> None:
    with pytest.raises(ValueError):
        container_tags(version)
