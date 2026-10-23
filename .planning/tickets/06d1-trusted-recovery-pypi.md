# Ticket 06D1 — Trusted recovery and immutable PyPI preflight

## Model

Primary: `gpt-5.6-terra`, high reasoning. Quota fallback:
`gpt-5.6-luna`, high reasoning. Never use Sol High.

## Ownership

- `.github/workflows/release.yml`
- `scripts/pypi_preflight.py` (or an equivalently focused helper)
- Focused tests for the helper/recovery policy
- Recovery/PyPI sections in README and release/setup docs
- `.superpowers/sdd/ROADMAP/task-06d1-report.md`

## Work

1. Replace branch-selectable `workflow_dispatch` recovery with
   `repository_dispatch` type `recover-release`, reading only
   `github.event.client_payload.tag`. This guarantees the workflow definition
   comes from the default branch.
2. Validate the tag with the shared strict SemVer helper, require the existing
   GitHub Release, fetch the exact tag, and prove the tagged commit is an
   ancestor of `origin/main` before release-capable downstream jobs.
3. Document an exact `gh api repos/arturmartins/spdx-sorter/dispatches` command.
4. Before PyPI trusted publishing, query the project/version JSON endpoint and
   compare local filenames plus SHA-256. Fail on a differing digest, remove
   matching files from the upload set, publish absent files only, and skip the
   publish action when none remain. Treat HTTP 404 as no existing release;
   fail closed on other network/API errors.
5. Unit-test absent, exact-match, conflict, malformed API response, and mixed
   upload sets without contacting PyPI. Test repository-dispatch/static gates.

## Boundaries

Preserve all shared changes. Use apply_patch. No subagents, commits, pushes,
tags, releases, registry/PyPI calls, or remote setting mutations. Run focused
pytest, Ruff, mypy, YAML/actionlint, SHA scan, and diff check; write the report.
