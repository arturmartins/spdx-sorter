# SPDX Sorter Improvement Plan

This document set records the design contracts used to turn the original SPDX
JSON sorting script into a resilient, well-tested Python package and container
image with an attested release process. The repository files are implemented;
this is not release readiness. External verification and publication gates
remain open.

The target first public release is `0.1.0`. The stable compatibility promise is
SPDX 2.2 and 2.3. SPDX 3.x remains explicitly experimental until its behavior
is backed by official schemas and fixtures.

## Current state

> **Status:** Implementation files are present and locally review-clean; the
> first release is blocked on the external gates listed below.

The legacy `sort_spdx.py` entry point has been replaced by the typed
`src/spdx_sorter` package. The dependency-free sorting core, safe CLI and
atomic I/O, optional `spdx-tools` validation adapter, official SPDX 2.2/2.3
offline corpus, Python packaging, container definition, quality gates,
governance files, Release Please workflow, and release/attestation workflows
are implemented and independently reviewed. The first-release manifest
bootstrap remains a known configuration correction in
[Ticket 06E](../../.planning/tickets/06e-release-please-bootstrap.md).

Fresh local evidence on 2026-08-30 includes 142 tests plus 9 subtests, Ruff
formatting and lint, strict mypy, 99.65% line coverage, 94.79% branch coverage,
locked wheel/sdist builds, independent clean artifact smokes, actionlint, and
full-SHA action-pin checks. See the [roadmap](../../ROADMAP.md) for phase-level
evidence and remaining exit criteria.

The project is not published. Native container runtime and multi-architecture
evidence still requires a Docker daemon. Branch rules, protected environments,
trusted publishing, registry configuration, hosted publication, and consumer
attestation verification remain maintainer-controlled prerequisites. No public
`0.1.0` release or SLSA Build Level 3 achievement is claimed.

## Locked decisions

| Area | Decision |
|---|---|
| Stable SPDX support | SPDX 2.2 and 2.3 |
| SPDX 3.x | Experimental, best effort |
| Sorting core | Dependency-free, lossless stdlib JSON transformation |
| Validation | Opt-in `--validate`, installed with the `validation` extra and backed by `spdx-tools` |
| Serialization boundary | Never serialize sorted output through `spdx-tools` |
| Conformance inputs | Pinned official SPDX schemas and upstream fixture documents are normative |
| Producer compatibility | ScanCode Toolkit and lib4sbom outputs are fixtures only, never runtime dependencies |
| Distribution | Target `spdx-sorter`; recheck at publication and fall back to `spdx-json-sorter` if unavailable |
| Import namespace | `spdx_sorter` |
| CLI | `spdx-sort` only; no legacy script shim |
| File safety | Output to stdout by default; mutation requires `--in-place` |
| Python | 3.10–3.14 supported; 3.15 prerelease non-blocking until GA |
| Test gates | 95% line coverage and 90% branch coverage |
| Containers | GHCR and Docker Hub |
| Architectures | `linux/amd64`, `linux/arm64`, `linux/arm/v7` |
| Release automation | Release Please, Conventional Commits, GitHub Releases |
| Merge policy | Squash-only, Conventional Commit PR titles |
| Supply chain | Target SLSA v1 Build Level 3 using reusable workflows and attestations |

## Documents

- [Development](development.md) defines the package architecture, public API,
  sorting contract, CLI, and safe file I/O.
- [Quality](quality.md) defines tests, static analysis, supported runtimes, and
  merge gates.
- [Packaging and containers](packaging-and-containers.md) defines Python and
  OCI artifact construction and user-facing installation behavior.
- [Release management](release-management.md) defines versioning, Release
  Please, publication, tags, and failure recovery.
- [Supply-chain security](supply-chain-security.md) defines provenance, SBOMs,
  reusable workflows, permissions, and verification.
- [Governance](governance.md) defines repository controls and maintainer
  responsibilities.
- [Roadmap](../../ROADMAP.md) sequences the work and supplies exit criteria.

## Goals

- Make every supported input converge after one sorting pass.
- Preserve every JSON value outside the documented ordering changes; sorting
  must not round-trip a document through an SPDX object model.
- Never mutate an input unless the user explicitly requests it.
- Make failures actionable and leave the original file intact.
- Offer a useful library API as well as a Unix-friendly CLI.
- Prove behavior with examples, integration tests, and general invariants.
- Publish the same release through PyPI, GitHub Releases, GHCR, and Docker Hub.
- Let consumers verify where release artifacts were built.

## Non-goals for 0.1.0

- Full or stable SPDX 3.x conformance.
- Requiring `spdx-tools`, ScanCode Toolkit, or lib4sbom for ordinary sorting.
- Sorting YAML, XML, RDF, or SPDX tag/value documents.
- Schema-derived ordering without curated semantic rules.
- Streaming transformation of documents too large to fit in memory.
- Automatic repair of invalid SPDX documents.
- Backward compatibility with the unpublished `sort_spdx.py` CLI.
