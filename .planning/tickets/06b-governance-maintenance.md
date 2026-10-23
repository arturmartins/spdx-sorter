# Ticket 06B — Governance and maintenance controls

## Assigned model

Use `gpt-5.6-terra` with medium reasoning. Do not use a Sol model. This is a
bounded policy/template/configuration task performed only after Ticket 06A is
review-clean.

## Objective

Implement the repository-controlled governance and maintenance portion of
`.superpowers/sdd/ROADMAP/task-release-governance-brief.md` without changing
remote GitHub, PyPI, or Docker Hub settings.

## Owned files

- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `.github/CODEOWNERS`
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/*`
- `.github/dependabot.yml`
- `.github/workflows/security.yml` and/or focused security workflows
- `docs/REPOSITORY_SETUP.md`
- Governance/setup sections of `README.md` and `docs/plan/*.md`
- `.superpowers/sdd/ROADMAP/task-governance-report.md`

## Requirements

1. Contributor commands must match the actual pyproject dependency groups,
   tests, formatting, lint, typing, coverage, package, and container contracts.
2. Document Conventional Commit PR titles, squash-only merging, sorting
   invariant/fixture expectations, security reporting, supported versions, and
   release authority.
3. Add useful PR and issue templates plus CODEOWNERS for source/tests,
   packaging/dependencies, workflows/release config, and security/governance.
4. Configure Dependabot for pip, GitHub Actions, and Docker with a predictable
   cadence. Add dependency review and CodeQL using least privilege and full-SHA
   action pins; PR workflows must not gain release permissions.
5. Add an exact maintainer checklist for branch/ruleset controls, squash merge,
   required checks, protected `pypi`/`docker-hub` environments, PyPI trusted
   publisher identity, Docker Hub secrets, GHCR, private vulnerability
   reporting, secret scanning/push protection, and first-release verification.
6. Clearly distinguish repository files already implemented from external
   controls that remain unverified. Do not claim remote settings are active.
7. Do not commit, push, publish, create releases, or mutate remote settings.

## Verification and report

Parse YAML, validate action pins/permissions, check internal links and commands,
run focused tests plus `git diff --check`, and record evidence and external
follow-ups in the report.

## Review gate

An independent `gpt-5.6-terra` reviewer must approve spec compliance and
quality before Ticket 06C begins. Fix all Critical/Important findings.
