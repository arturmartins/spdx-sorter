# Ticket 06A — Release Please and SLSA release workflows

## Assigned model

Use `gpt-5.6-terra` with high reasoning. Do not use a Sol model. This is a
multi-file integration and supply-chain workflow task; Luna is too lightweight
for the permission/event/artifact-identity judgments.

## Objective

Implement the release and artifact-build portion of
`.superpowers/sdd/ROADMAP/task-release-governance-brief.md` without publishing
or changing remote settings.

## Owned files

- `.release-please-manifest.json`
- `release-please-config.json`
- `CHANGELOG.md`
- `.github/workflows/release.yml`
- `.github/workflows/_build-python.yml`
- `.github/workflows/_build-container.yml`
- `.github/workflows/pr-title.yml`
- Release-specific sections of `README.md` and `docs/plan/*.md`
- `.superpowers/sdd/ROADMAP/task-release-workflows-report.md`

## Requirements

1. Manifest-based Release Please, Python release type, initial `0.1.0`,
   Conventional Commit changelog, and `v<version>` tags.
2. Release jobs run only after Release Please reports a created release, or a
   manual recovery validates an existing `v<version>` GitHub Release.
3. Reusable Python/container workflows reject arbitrary refs, check out the
   exact tag, verify package/tag version parity, and build/attest the subjects.
4. Wheel and sdist are built once, tested/checked, attested with current
   `actions/attest`, uploaded once, then consumed by PyPI OIDC and GitHub Release
   jobs without rebuilds.
5. The container is built once for amd64, arm64, and arm/v7, pushed to GHCR and
   Docker Hub, and gets build-provenance plus final-image SPDX JSON SBOM
   attestations for both fully-qualified identities at the same digest.
6. Default permissions are empty/read-only. OIDC, attestations, packages, and
   contents write are job-scoped. Pull-request workflows receive no release
   permissions or protected environments.
7. Every external action is pinned to a current full commit SHA with a readable
   version comment. Verify syntax against official upstream sources.
8. No tag, release, registry login, publication, commit, push, or remote setting
   mutation during implementation.

## Verification and report

Parse all JSON/YAML, check full-SHA action refs and permissions/event gates,
run `git diff --check`, and write exact evidence plus unresolved hosted checks
to the report. Return only status, changed-file summary, tests, and concerns.

## Review gate

An independent `gpt-5.6-terra` reviewer must approve spec compliance and
quality before Unit 06B begins. Fix all Critical/Important findings.
