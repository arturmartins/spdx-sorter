# Ticket 06D — Final Critical/Important remediation

## Assigned model

Use `gpt-5.5` with high reasoning. Do not use a Sol model. This is a broad
release-security and conformance integration task; apply all findings as one
coherent fix set, then run focused verification. If a separate run is needed,
start from this ticket and the final review package without reconstructing the
conversation.

## Inputs

- `.superpowers/sdd/ROADMAP/review-final-branch.md`
- `.planning/tickets/06a-release-slsa-workflows.md`
- `.planning/tickets/06b-governance-maintenance.md`
- `docs/plan/*.md`
- Current workflows, packaging metadata, constraints, fixtures, and tests

## Required fixes

### 1. Trusted manual recovery (Critical)

Remove branch-selectable `workflow_dispatch` recovery. Use a
`repository_dispatch` recovery event (for example `recover-release`) so GitHub
loads the workflow from the default branch. Accept only `client_payload.tag`,
validate it with `scripts/validate_release.py`, require the GitHub Release to
exist, fetch the exact tag, and prove its commit is an ancestor of protected
`origin/main` before granting release-capable downstream jobs. Keep normal
Release Please push behavior. Document the exact `gh api` recovery command.

### 2. PyPI immutable-file preflight (Important)

Before trusted publishing, query PyPI's JSON API for the target version and
compare every local wheel/sdist filename and SHA-256 digest. Matching existing
files are treated as complete and removed from the upload set; differing
digests fail closed; absent files alone are published. Skip the publish action
when no files remain. Never use a blind `skip-existing` policy.

### 3. Locked release build environment (Important)

Release builds must consume a committed lock/complete exact constraints state,
including the Hatchling backend, test/build tools, validation extra, and their
transitive dependencies. Do not install floating dependency groups or allow an
isolated backend resolver to select a different Hatchling than the committed
build pin. Prefer a committed `uv.lock` with `uv sync --frozen` and
`python -m build --no-isolation`, or an equivalently complete hash/exact lock.
Add/update CI freshness checks. Preserve a dependency-free base runtime wheel.

### 4. Official SPDX conformance corpus (Important)

Vendor attributable official SPDX 2.2 and 2.3 JSON schemas and representative
upstream valid/invalid fixtures at explicit official `spdx/spdx-spec` tags or
commit SHAs. Record source URLs, tag/commit, licenses, local filenames, and
expected outcomes. Add offline schema-based tests in addition to the
`spdx-tools` adapter tests. Keep ScanCode/lib4sbom fixtures explicitly
compatibility-only. If upstream invalid fixtures do not exist, pair official
schemas with clearly labeled project-generated negative mutations; do not call
hand-authored minimal files upstream fixtures.

### 5. Docker Hub credential isolation (Important)

The reusable build job must not receive the protected `docker-hub` environment
or Docker Hub credentials. Build, push, verify, SBOM, and attest the canonical
GHCR multi-platform digest in a build job using only the job-scoped GHCR token.
Use a separate `docker-hub` environment publication job to copy that exact
manifest digest to Docker Hub, perform exact-version conflict checks and stable
alias promotion, and create Docker Hub provenance/SBOM attestations. Pass only
the required digest/SBOM artifact across jobs; do not rebuild.

### 6. Stable OCI aliases (Important)

After exact-version digest verification, stable versions publish/repair
`<major>.<minor>`, `<major>`, and `latest` in both registries as well as the
exact version. Prereleases remain exact-version-only. Exact-version conflicts
fail; floating tags may be repaired only after the exact digest is accepted.

## Verification

- Full JSON/YAML/actionlint and full-SHA scans.
- Focused positive/negative recovery, PyPI digest-preflight, strict SemVer,
  schema-valid/schema-invalid, and registry-tag computation tests or testable
  helper scripts.
- Ruff format/lint and strict mypy for added Python helpers.
- Full pytest suite, packaging tests, lock freshness, and `git diff --check`.
- Update README, setup docs, roadmap/evidence reports, and workflow comments so
  they match the fixed architecture without claiming a hosted run.

## Constraints

Shared dirty worktree: preserve all existing changes. Use `apply_patch` for
edits. Do not commit, tag, push, publish, log into registries, create releases,
or mutate remote settings. Do not spawn subagents. Write remediation evidence
to `.superpowers/sdd/ROADMAP/task-final-fixes-report.md` and return
`DONE_WITH_CONCERNS` for hosted-only gaps.
