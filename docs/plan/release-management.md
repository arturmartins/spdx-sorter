# Release Management Plan

## Versioning and commit convention

Use Semantic Versioning driven by Conventional Commit squash titles:

- `fix:` produces a patch release.
- `feat:` produces a minor release.
- `type!:` or a `BREAKING CHANGE:` footer marks a breaking release.
- Before 1.0, a breaking change advances the minor version.
- Documentation, tests, refactors, and chores appear in the changelog only when
  configured as user-relevant and do not force a release by default.

Pull requests are squash-merged so each accepted PR becomes one meaningful
commit on `main`. A required status check validates the PR title before merge.

## Release Please

Use Release Please's manifest strategy with release type `python` and package
path `.`. Commit both `release-please-config.json` and
`.release-please-manifest.json`.

The first release is bootstrapped explicitly as `0.1.0`. Release Please's
manifest records the latest released/current version, not the desired next
version. Because this repository has no release yet, the first hosted run must
use a valid bootstrap state and a dry run must prove that the proposed tag is
exactly `v0.1.0`; a manifest entry of `0.1.0` must not be mistaken for a request
to create `0.1.0`. Follow the
[official manifest bootstrap procedure](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md)
and complete [Ticket 06E](../../.planning/tickets/06e-release-please-bootstrap.md)
before enabling the workflow. Remove any one-time bootstrap override after the
first release.

Release Please owns:

- The release pull request.
- Version updates in package metadata.
- `CHANGELOG.md` entries.
- The `v<version>` tag.
- The corresponding published GitHub Release.

It does not build or publish package-manager artifacts. Its release-created
output gates the reusable build and publication jobs in the same workflow;
this avoids depending on a second workflow event that a `GITHUB_TOKEN`-created
release might not trigger.

## Release pipeline

After the release PR is merged:

1. Release Please creates the tag and GitHub Release.
2. The reusable Python workflow checks out the exact tag, tests it, builds the
   wheel and sdist, verifies them, and generates provenance.
3. The protected PyPI publication job downloads those exact artifacts and
   publishes through trusted publishing.
4. The reusable container workflow builds the three-platform manifest once in
   GHCR, verifies and attests the canonical digest, checksums the transferred
   SBOM and metadata, then a protected Docker Hub job verifies that transfer,
   copies the exact digest without rebuilding, and attests the Docker Hub
   identity.
5. Checksums and Python distributions are attached to the GitHub Release.
6. Consumer-style verification checks the PyPI files and both OCI identities.
7. The orchestrating workflow succeeds only after every publication channel
   and immutable release-asset check succeeds; workflow success is the release
   completion signal.

Publication jobs use environments and job-scoped permissions. PyPI uses OIDC
trusted publishing and stores no API token. Docker Hub credentials are scoped
to its publication environment. GHCR uses the repository token with only
`packages: write` for the relevant job.

## Failure and rerun policy

Release artifacts are immutable. A rerun performs a PyPI JSON API preflight
before uploading:

- If an expected filename or tag is absent, publish it.
- If it exists with the expected digest, treat that item as complete.
- If it exists with a different digest, stop and require a new version.
- Never silently replace a conflicting PyPI file or immutable version tag.

Stable OCI releases publish the exact version, `<major>.<minor>`, `<major>`,
and `latest`; prereleases publish only the exact version. Floating OCI tags may
be repaired only after the exact version digest verifies. A partially published
release remains visible with a failure note until the missing channel is
repaired. Do not delete and recreate a published PyPI version.

The workflow supports a `repository_dispatch` event of type `recover-release`,
accepting only an existing Release Please tag in
`github.event.client_payload.tag`. Because repository dispatch uses the
default-branch workflow definition, recovery validates the strict SemVer tag,
requires its GitHub Release, fetches the exact tag, and proves its commit is an
ancestor of `origin/main` before any release-capable downstream job runs. It
rebuilds from that immutable tag and applies the same digest checks; it cannot
choose an arbitrary ref or version. A maintainer requests it with:

> **Hard gate:** the requested tag and its GitHub Release must already exist.
> Recovery cannot create the first release or select an arbitrary branch/ref.

```bash
gh api repos/arturmartins/spdx-sorter/dispatches \
  --method POST \
  -f event_type=recover-release \
  -f 'client_payload[tag]=v0.1.0'
```

## Required release setup

These are maintainer-controlled external settings, not settings that workflow
files can enable. Their completion must be recorded using
[the repository setup checklist](../REPOSITORY_SETUP.md).

- Create protected GitHub environments for `pypi` and `docker-hub`.
- Register the exact repository, workflow, and environment as the PyPI trusted
  publisher.
- Create Docker Hub's `arturmartins/spdx-sorter` repository and a narrowly
  scoped automation token.
- Enable GHCR package publication for the repository.
- Confirm GitHub Actions may create pull requests for Release Please.

## Acceptance criteria

- A `feat:` test change proposes the expected pre-1.0 minor release.
- Merging the release PR creates exactly one tag and GitHub Release.
- Every published artifact reports the same version.
- A no-op rerun succeeds only through matching hashes.
- A simulated hash conflict fails without overwriting the registry artifact.
