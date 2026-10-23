# Ticket 06D3 — Locked and reproducible Python release build

## Model

Use `gpt-5.6-luna` with high reasoning. Never use Sol High. Run this ticket
after 06D2 so the committed lock includes final test/schema dependencies.

## Ownership

- `pyproject.toml`
- `uv.lock`
- `.github/workflows/_build-python.yml`
- Python lock/freshness portions of `.github/workflows/ci.yml`
- Relevant dependency/build docs and constraints comments
- `.superpowers/sdd/ROADMAP/task-06d3-report.md`

## Work

1. Generate and commit a complete `uv.lock` for project extras/dependency
   groups, including the exact Hatchling backend and all transitive release,
   test, validation, schema, build, lint, type, and coverage dependencies.
2. Make the reusable Python release job use a current full-SHA pinned
   `astral-sh/setup-uv`, `uv sync --frozen` with the required groups/extra, and
   `uv run --no-sync python -m build --no-isolation`. It must not resolve a
   floating isolated Hatchling environment.
3. Add a CI lock freshness gate (`uv lock --check` or current official
   equivalent) and ensure clean artifact tests use the built files, not source.
4. Keep `dependencies = []` for the base runtime and retain optional
   `spdx-tools` validation.
5. Reconcile or document Docker-specific exact constraints versus the project
   lock; do not silently maintain contradictory Hatchling pins.

## Boundaries

Use apply_patch for edits and `uv lock` only for the mechanical lock rewrite.
Official uv docs only. Preserve shared work. No subagents, commit/push/publish,
or remote mutations. Verify `uv lock --check`, frozen sync, build, tests,
Ruff/mypy, actionlint, and diff check; write the report.
