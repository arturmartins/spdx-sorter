# Repository Governance Plan

## Objective

Make the repository settings enforce the development and release policies
described in this plan. Workflow files alone are insufficient while `main` is
unprotected and every merge strategy remains enabled.

## Implementation status

The repository contains contributor and security policies, ownership and issue
templates, Dependabot configuration, and a least-privilege security workflow.
Those files define the intended controls, but cannot enable GitHub branch
rulesets, protected environments, trusted publishing, registry access, private
vulnerability reporting, or secret-scanning features. Maintainers must verify
each external setting using [the repository setup checklist](../REPOSITORY_SETUP.md);
the checklist is deliberately not evidence that any setting is active.

## Main branch policy

Configure `main` with:

- Pull requests required before merging.
- At least one approving review; dismiss approval when relevant code changes.
- Required conversation resolution.
- Required status checks for tests, quality, package build, container smoke,
  dependency review, and Conventional Commit PR title.
- Branch required to be up to date before merge when GitHub merge queues are
  not enabled.
- Force pushes and deletion disabled.
- Rules applied to administrators, with an emergency bypass limited to named
  maintainers and visible in the audit log.

Enable squash merge only. Disable merge commits and rebase merging. Use the PR
title as the default squash commit subject and delete merged branches
automatically.

## Contribution policy

Keep `CONTRIBUTING.md` current with:

- Supported Python setup and canonical local check command.
- Test and documentation expectations.
- Conventional Commit PR-title examples.
- The squash-merge model and release effect of `fix`, `feat`, and breaking
  changes.
- A rule that sorting changes include invariant tests and fixtures.
- A rule that public interfaces and workflows update their owning plan or user
  documentation.

Pull-request templates prompt for behavior, tests, compatibility, security,
and documentation. Issue templates separate defects, sorting-rule proposals,
and support requests.

## Ownership and review

Add `CODEOWNERS` for:

- Core package and tests.
- Packaging and dependency metadata.
- GitHub workflows and release configuration.
- Security and governance documents.

Workflow, publication, permission, and dependency-lock changes require review
from the release/security owner. Contributors may not approve their own pull
requests.

## Environments and secrets

Create protected `pypi` and `docker-hub` environments. Restrict them to release
tags created from `main` and require maintainer approval until the release
pipeline has completed several successful releases.

- PyPI uses trusted publishing and stores no long-lived token.
- Docker Hub stores one narrowly scoped automation credential.
- GHCR uses the job token with `packages: write` only in publication jobs.
- Dependabot secrets are added only if a required private dependency appears.
- Secret values never pass into reusable build jobs unnecessarily.

## Security and maintenance

- Keep `SECURITY.md` current with supported versions, private reporting instructions,
  response expectations, and disclosure policy.
- Enable private vulnerability reporting, secret scanning, push protection,
  dependency graph, Dependabot alerts, and dependency review where available.
- Enable CodeQL for Python and workflow analysis.
- Automate dependency and SHA-pinned action updates on a predictable schedule.
- Review supported Python and SPDX versions at least quarterly and before each
  minor release.
- Keep the changelog user-focused and the roadmap current after each phase.

## Release authority

Release Please proposes versions; maintainers authorize them by merging the
release PR. Publication workflows accept only Release Please tags. Manual
recovery may retry an existing tag but cannot create a new version or build an
arbitrary ref.

No maintainer should publish PyPI or mutable release images from a workstation.
Emergency remediation uses a new version, except for repairing a floating OCI
tag to an already verified immutable digest.

## Governance acceptance criteria

- GitHub reports `main` protected and only squash merge enabled.
- Every named required check has run successfully at least once before being
  made mandatory.
- A malformed PR title and a failing dependency review both block merge.
- Pull-request workflows cannot access protected environment secrets.
- Maintainers can identify who approves code, workflows, and releases.
- Security reporting and supported-version policies are public.
