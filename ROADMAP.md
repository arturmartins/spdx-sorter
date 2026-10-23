# SPDX Sorter Roadmap

This roadmap implements the [SPDX Sorter improvement plan](docs/plan/README.md).
Phases are ordered by dependency. A phase is complete only when its exit
criteria are demonstrated; completing files or checklist items alone is not
enough.

## Status key

- `[ ]` Not started
- `[~]` In progress
- `[x]` Complete and verified

## Phase 0 — Preserve the baseline

**Status:** `[x]`

**Purpose:** Start from the useful existing work without losing uncommitted
changes, and encode the confirmed defects as regression tests.

**Deliverables:**

- Inventory the current README, legacy script, package, CI workflow, review,
  and test modules.
- Preserve or deliberately migrate every user-owned change.
- Add failing regressions for nested-array idempotence and mode preservation.
- Record representative CLI output as migration acceptance behavior.

**Exit criteria:** Both confirmed defects reproduce in focused tests; the
existing suite still runs; no pre-existing worktree change is lost.

## Phase 1 — Build the resilient core

**Status:** `[x]`

**Depends on:** Phase 0

**Purpose:** Establish the package boundaries and safe public contracts in the
[development plan](docs/plan/development.md).

**Deliverables:**

- `src/spdx_sorter` package and public type/API surface.
- Child-first, type-aware canonicalization.
- Conservative malformed-array behavior.
- Safe-by-default `spdx-sort` CLI.
- Permission-preserving, symlink-aware atomic writes.
- Dependency-free, lossless stdlib JSON sorting path that never serializes
  sorted output through `spdx-tools`.

**Exit criteria:** One pass converges; input objects are not mutated; CLI exit
codes match the contract; failure injection never corrupts the destination.

## Phase 2 — Add validation and package metadata

**Status:** `[x]`

**Depends on:** Phase 1

**Purpose:** Make the project installable and offer an honest SPDX conformance
boundary.

**Deliverables:**

- Isolated `spdx-tools` adapter and `--validate` behavior.
- Optional `validation` extra; base sorting installation stays dependency-free.
- Pinned official `spdx-spec` 2.2/2.3 schemas plus representative fixtures
  from official SPDX organization repositories as the normative conformance
  corpus, with separate provenance and expected outcomes.
- ScanCode Toolkit and lib4sbom output fixtures as a separate compatibility
  corpus only, with no runtime dependency on either tool.
- Experimental 3.x labeling and fixtures, explicitly outside stable
  conformance.
- Complete `pyproject.toml`, typed marker, wheel, and sdist.
- Clean-environment installation tests.
- Target PyPI name and fallback policy documented; final availability is
  rechecked immediately before publication.

**Exit criteria:** Wheel and sdist pass metadata checks; installed API and CLI
work without the source tree; a base installation sorts without third-party
runtime dependencies; official SPDX 2.2/2.3 schemas and attributable upstream
fixtures produce the expected conformance results; producer compatibility fixtures remain
non-normative; and sorted output is never serialized through `spdx-tools`.

## Phase 3 — Enforce quality gates

**Status:** `[x]`

**Depends on:** Phase 2

**Purpose:** Implement the [quality plan](docs/plan/quality.md) before expanding
release automation.

**Deliverables:**

- Pytest suite migrated from the current tests.
- Hypothesis idempotence, permutation, preservation, and type invariants.
- Tests for the pinned official conformance corpus and distinct ScanCode
  Toolkit/lib4sbom compatibility corpus.
- Ruff, strict typing, coverage, artifact, and cross-platform jobs.
- Required Python 3.10–3.14 matrix and non-blocking 3.15 preview.

**Exit criteria:** Required CI is green; coverage is at least 95% lines and 90%
branches; the source test matrix covers every supported Python version; clean
wheel and sdist smoke tests pass on the latest supported Python.

## Phase 4 — Produce container artifacts

**Status:** `[~]`

**Depends on:** Phase 3

**Purpose:** Implement the container half of the
[packaging plan](docs/plan/packaging-and-containers.md).

**Deliverables:**

- Digest-pinned multi-stage Dockerfile.
- Non-root, read-only-compatible runtime behavior.
- OCI labels and version parity with the Python package.
- `amd64`, `arm64`, and `arm/v7` manifest build.
- Container integration and architecture smoke tests.

**Exit criteria:** Each architecture processes the same fixtures identically;
the image runs non-root with a read-only root filesystem; no build tools or
credentials appear in the runtime image.

**Verification note:** Static Docker/workflow checks passed, but native Docker
build and runtime/non-root/read-only/multi-architecture smokes remain pending
because the local Docker client has no server socket.

## Phase 5 — Establish release and governance controls

**Status:** `[~]`

**Depends on:** Phase 3; Phase 4 for image publication

**Purpose:** Put the [release](docs/plan/release-management.md) and
[governance](docs/plan/governance.md) policies under automation and repository
enforcement.

**Deliverables:**

- Conventional PR-title check and squash-only configuration.
- Protected `main` with required status checks.
- Release Please manifest/configuration and `0.1.0` bootstrap.
- Protected publication environments and trusted publisher setup.
- GHCR and Docker Hub repositories and credentials.
- Release dry run including partial-failure recovery.

**Exit criteria:** Repository settings match the governance document; a test
release PR proposes the expected version/changelog; publication jobs cannot run
from a pull request or arbitrary ref; matching-hash reruns are safe.

**Verification note:** Repository-controlled workflow and governance checks,
including trusted recovery and immutable PyPI rerun policy, passed independent
review. Remote repository settings, protected environments, trusted publishers,
registry configuration, and hosted release evidence remain pending maintainer
action. The first Release Please bootstrap state also requires the dry-run
correction recorded in Ticket 06E before the workflow is enabled.

## Phase 6 — Attest the supply chain

**Status:** `[~]`

**Depends on:** Phase 5

**Purpose:** Implement and verify the
[supply-chain security plan](docs/plan/supply-chain-security.md).

**Deliverables:**

- Reusable Python and container build workflows.
- SLSA provenance for wheel, sdist, GHCR, and Docker Hub subjects.
- Final-image SBOM attested against both OCI identities.
- SHA-pinned actions, least-privilege permissions, and locked inputs.
- Exact-signer consumer verification documentation.

**Exit criteria:** Verification rejects the wrong repository, workflow, ref,
or digest and accepts every intended release subject. The implemented design is
checked against SLSA v1 Build Level 3 requirements before making that claim.

**Verification note:** Local action pinning, permissions, locked builds,
credential isolation, registry preflight policy, packaging, and static checks
passed independent review. Hosted provenance/SBOM publication and exact-signer
consumer verification remain pending; SLSA Build Level 3 is not claimed.

## Phase 7 — Publish 0.1.0

**Status:** `[ ]`

**Depends on:** Phases 0–6

**Purpose:** Publish and independently verify the first public release.

**Deliverables:**

- Merged Release Please `0.1.0` pull request.
- Final PyPI name confirmation, with metadata and installation docs changed to
  the documented fallback before publication if necessary.
- `v0.1.0` tag and GitHub Release.
- PyPI wheel and sdist.
- GHCR and Docker Hub multi-platform images.
- Checksums, provenance, and image SBOM.
- Removal of the one-time Release Please bootstrap override.

**Exit criteria:** A clean consumer environment can install, run, and verify
the Python package and both image identities; every channel reports `0.1.0` and
the same source revision; all immutable artifact digests are recorded.

## After 0.1.0

- Promote Python 3.15 when generally available and passing as a required job.
- Gather real-world SPDX producer fixtures and refine conservative fallback
  behavior without weakening idempotence.
- Promote SPDX 3.x only after official schema/model fixtures, version-specific
  rules, and validation are stable.
- Evaluate streaming only if measured SBOM sizes show memory is a practical
  constraint.
- Consider 1.0 when the CLI, library API, and stable sorting registry have
  survived multiple releases without incompatible changes.
