# Maintainer repository setup checklist

This file is an exact checklist for controls that cannot be enabled by a
repository checkout. It is not evidence that any remote setting is active.
Record completion and verification date in the repository administration log.

## Branch and merge controls

- [ ] Create a `main` branch protection rule or ruleset that applies to
  administrators, requires pull requests, one approving review, dismissed stale
  approvals, resolved conversations, and code-owner review.
- [ ] Require these checks only after each has passed at least once: CI test
  matrix, Quality and coverage, Package build and metadata, Installed wheel
  smoke test, Container artifact, Conventional Commit title, Dependency review,
  and CodeQL.
- [ ] Require the branch to be up to date unless a merge queue supplies that
  guarantee; disable force pushes and deletion; limit bypasses to named
  maintainers and audit their use.
- [ ] Enable squash merging only, disable merge commits and rebase merges, use
  the PR title for the squash subject, and auto-delete merged branches.

## Environments, registries, and publishing

- [ ] Create protected `pypi` and `docker-hub` environments; restrict them to
  release tags from `main` and require maintainer approval until several
  successful releases establish confidence.
- [ ] Register PyPI trusted publishing for repository
  `arturmartins/spdx-sorter`, workflow `.github/workflows/release.yml`, and
  environment `pypi`. Do not create or store a PyPI API token.
- [ ] Create the Docker Hub repository and put only a narrowly scoped,
  rotatable automation credential in the `docker-hub` environment; do not
  expose it to PRs or reusable build jobs.
- [ ] Enable GHCR package publication for this repository. Publication uses the
  job-scoped `GITHUB_TOKEN`, never a committed registry credential.
- [ ] Allow GitHub Actions to create pull requests so Release Please can manage
  its release PR.

## Security features

- [ ] Enable private vulnerability reporting and verify that the link in
  `SECURITY.md` opens a private report form.
- [ ] Enable dependency graph, Dependabot alerts, secret scanning, and push
  protection where the repository plan supports them.
- [ ] Confirm CodeQL alerts are enabled and that `Security` workflow results
  appear in the repository security view.
- [ ] Configure Dependabot secrets only for a proven private dependency need;
  do not copy ordinary repository or release secrets into Dependabot.

## First-release verification

- [ ] Before enabling the release workflow, run Release Please in dry-run mode
  against the intended default branch. Confirm its manifest/bootstrap state
  proposes exactly `v0.1.0` rather than treating `0.1.0` as an already released
  version. Do not proceed until the generated version and changelog are correct.
  [Ticket 06E](../.planning/tickets/06e-release-please-bootstrap.md) must record
  the exact version-pinned command and captured output; do not substitute an
  unpinned `npx` invocation. The current action `v4.3.0` bundles Release Please
  `17.1.2`, so use:

  ```bash
  npx --yes release-please@17.1.2 release-pr \
    --token="${RELEASE_PLEASE_TOKEN}" \
    --repo-url=arturmartins/spdx-sorter \
    --target-branch=main \
    --config-file=release-please-config.json \
    --manifest-file=.release-please-manifest.json \
    --dry-run > release-please-dry-run.txt 2>&1
  ```

  Use a short-lived, least-privilege token and never commit it. Attach
  `release-please-dry-run.txt` to the Ticket 06E review and release PR. The
  output must propose exactly `0.1.0`/`v0.1.0`, update the intended changelog,
  and contain no later version. When the pinned action changes, update this CLI
  version from that action release's lockfile before rerunning the check.
- [ ] Merge a reviewed Conventional Commit release PR through the squash-only
  path; confirm Release Please creates exactly one `v<version>` tag and GitHub
  Release.
- [ ] Confirm protected environment approvals occur, PyPI trusted publishing
  succeeds without a token, and Docker Hub credentials are only available to
  the protected environment job.
- [ ] Verify PyPI distributions, GHCR, and Docker Hub identities against the
  expected repository, signer workflow, version tag, and manifest digest using
  the commands in [the supply-chain plan](plan/supply-chain-security.md).
- [ ] Confirm Docker Hub publication copied the canonical GHCR digest without
  rebuilding and that stable releases expose matching exact, `<major>.<minor>`,
  `<major>`, and `latest` tags while prereleases expose only the exact tag.
- [ ] Confirm checksums, final-image SPDX SBOM, and all attestations are
  attached or discoverable as specified; test recovery by dispatching the
  `recover-release` event with the exact command below, only against an
  existing Release Please tag, and stop on any immutable-artifact hash
  conflict:

  ```bash
  gh api repos/arturmartins/spdx-sorter/dispatches \
    --method POST \
    -f event_type=recover-release \
    -f 'client_payload[tag]=v0.1.0'
  ```

- [ ] Confirm a rerun with already-published PyPI files reports matching
  SHA-256 values and skips trusted publishing; a differing digest must fail
  closed without replacing the published file.
