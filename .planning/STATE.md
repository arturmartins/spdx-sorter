# Project State

## Project Reference

SPDX Sorter is being hardened into a dependency-free, lossless Python sorting
library and CLI with optional SPDX validation, tested package/container
artifacts, automated releases, governance, and verifiable supply-chain
provenance.

## Current Position

- Phase: 4–6 of 7 — container, release, governance, and supply-chain evidence
- Task: 6 of 7 — repository implementation review-clean; external evidence pending
- Progress: `[█████████░]` approximately 90%
- Branch: `main`, deliberately dirty with the approved uncommitted migration

## Completed

- Architecture and external-library boundaries documented and reviewed.
- Resilient sorting core, safe CLI/I/O, and optional validation implemented.
- Python packaging, property/fixture tests, and quality gates implemented.
- Container artifact implemented and statically review-clean; Docker Hub
  credentials are isolated from the canonical GHCR build and publication copies
  the accepted manifest digest without rebuilding. Native Docker runtime
  evidence is pending daemon availability.
- Trusted recovery, immutable PyPI rerun preflight, a complete `uv.lock`, frozen
  non-isolated release builds, and a pinned official SPDX 2.2/2.3 conformance
  corpus are implemented and independently reviewed.
- Fresh controller verification passed: 142 tests plus 9 subtests, Ruff
  format/lint, strict mypy, 99.65% line and 94.79% branch coverage, wheel/sdist
  build and clean artifact smokes, JSON/YAML/action pin checks, actionlint, and
  `git diff --check`.
- Units 06A–06D4 and the final whole-branch review are complete; evidence is
  recorded under `.superpowers/sdd/ROADMAP/`.

## Active Work

- Obtain native Docker build/runtime/read-only/non-root/multi-architecture
  evidence when a daemon is available.
- Apply the documented remote GitHub, PyPI, GHCR, and Docker Hub settings.
- Exercise a hosted dry-run/recovery path and verify published attestations
  before starting Phase 7.

## Concerns

- Docker daemon is unavailable, so native container smoke tests remain pending.
- Remote GitHub/PyPI/Docker Hub settings require maintainer action after the
  repository-controlled implementation is reviewed.
- Hosted release, publication, provenance, SBOM, and exact-signer verification
  evidence remain pending; do not claim publication or achieved SLSA Build
  Level 3.
- Ticket 06E must correct and dry-run the Release Please manifest bootstrap:
  the current `0.1.0` entry denotes a prior/current release even though no
  public release exists.

## Session Continuity

- Last session: 2026-08-30
- Stopped at: Task 6 repository implementation and whole-branch review complete;
  external Docker/hosted evidence pending.
- Resumed at: 2026-08-30, completed tickets 06D1–06D4, the deterministic sweep,
  and final independent review.
- Resume file: `.planning/.continue-here.md`
