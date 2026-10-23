# Contributing to SPDX Sorter

Thanks for contributing. This project supports Python 3.10 through 3.14;
Python 3.15 prerelease coverage is informative until it is generally available.

## Local setup and checks

Install [uv](https://docs.astral.sh/uv/) and a supported Python version from
3.10 through 3.14. Python 3.15 prerelease results are informative until 3.15 is
generally available. A running Docker daemon is required only for the final
container build/smoke checks. Use uv to install only the groups needed for the
work. The
committed `uv.lock` includes the exact Hatchling 1.27.0 backend and every
project extra/development group. The validation extra is required for the full
test suite.

```bash
uv lock --check
uv sync --frozen --group test --group lint --group type --group coverage --group build --extra validation
uv run --no-sync pytest
uv run --no-sync ruff format --check .
uv run --no-sync ruff check .
uv run --no-sync mypy
uv run --no-sync coverage run -m pytest
uv run --no-sync coverage report
uv run --no-sync python -m build --no-isolation
uv run --no-sync python -m twine check dist/*
docker build -t spdx-sorter:local .
```

CI requires at least 95% line coverage and 90% branch coverage. The workflow
calculates those percentages separately from `coverage.json`; a combined
`coverage report` percentage alone is not the merge gate.

The base package intentionally has no required third-party runtime dependency.
Install `.[validation]` only when using or testing `--validate`.

The Docker build is intentionally constrained separately for its Python 3.13
builder: `requirements/build-constraints.txt` pins Hatchling 1.27.0 and its
reviewed closure, while `requirements/validation-constraints.txt` pins the
image's optional validator closure. These image-only constraints must be
reviewed alongside `uv.lock`; they do not replace or silently override the
project's public dependency contract.

## Changes and tests

Keep the sorting contract deterministic and lossless. A sorting-rule change
must include focused invariant tests (at least idempotence and permutation
coverage) and representative fixtures. Normative conformance fixtures must
identify their pinned official SPDX source; producer fixtures must retain their
source attribution and remain compatibility—not normative—inputs.

Update user documentation and the relevant `docs/plan/` contract when changing
a public interface, package/container behavior, workflow, or release policy.

## Pull requests and releases

Use a Conventional Commit PR title because the title becomes the squash commit
on `main`. Examples: `fix(cli): preserve input mode`,
`feat(sorter): order external references`, and `docs: clarify validation`.
Use `!` or a `BREAKING CHANGE:` footer for a breaking change.

`main` is intended to accept squash merges only. `fix:` drives a patch release,
`feat:` drives a minor release, and breaking changes advance the minor version
while the project remains below 1.0. Release Please proposes releases; a
maintainer authorizes them by merging the release PR. Do not publish from a
workstation or manually create a release tag.

Read [SECURITY.md](SECURITY.md) before reporting a vulnerability. By
contributing, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
