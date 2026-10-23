# Ticket 06D4 — Docker Hub credential isolation and stable aliases

## Model

Primary: `gpt-5.6-terra`, high reasoning. Quota fallback: `gpt-5.5`, high
reasoning. Never use Sol High.

## Ownership

- `.github/workflows/_build-container.yml`
- Container caller/output wiring in `.github/workflows/release.yml`
- Container release/setup documentation
- Focused static/helper tests for tag computation if introduced
- `.superpowers/sdd/ROADMAP/task-06d4-report.md`

## Work

1. Remove the protected `docker-hub` environment and its credentials from the
   build job. Build/push the multi-platform canonical GHCR manifest once using
   only the job-scoped GHCR token; verify exact version/revision labels,
   generate the final-image SPDX SBOM, and attest GHCR there.
2. Add a separate job protected by the `docker-hub` environment. It downloads
   only the needed SBOM/metadata, logs into Docker Hub, copies the exact GHCR
   manifest digest without rebuilding, performs Docker Hub exact-version
   conflict checks, promotes tags, and creates Docker Hub provenance/SBOM
   attestations.
3. For stable versions promote exact, `<major>.<minor>`, `<major>`, and
   `latest` in both registries. For prereleases promote exact only. Exact-tag
   digest conflicts fail; floating aliases may be repaired only after exact
   acceptance. Serialize same-version operations.
4. Keep caller and both jobs least privilege. Never expose Docker Hub secrets
   to the GHCR build job or pull-request workflows.

## Boundaries

Preserve shared work and existing exact-tag/revision/preflight logic. Use
apply_patch. No subagents, commit/push/publish/login/remote mutation. Run YAML,
actionlint, full-SHA, permission/secret-flow, tag-policy, and diff checks; write
the report. Hosted registry behavior remains an explicit concern.
