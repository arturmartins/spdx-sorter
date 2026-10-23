# Ticket 06E — Correct first Release Please bootstrap state

## Model

Use `gpt-5.6-luna` with high reasoning, or `gpt-5.6-terra` with medium
reasoning if Luna is unavailable. Never use Sol High.

## Problem

The repository has no tags or public releases, but
`.release-please-manifest.json` currently maps `.` to `0.1.0`. Release Please
defines that value as the latest released/current version, so the current state
can cause the first release PR to target a version after `0.1.0` or fail to
locate the supposed previous release. Documentation targets `v0.1.0` as the
first release.

Authoritative reference:
<https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md>

## Work

1. Determine the correct manual bootstrap state for release type `python` and
   a first `v0.1.0` release using current official Release Please behavior.
2. Correct `release-please-config.json`, `.release-please-manifest.json`, and
   the initial changelog/version placeholders without implying an existing
   release.
3. Run a read-only/dry-run Release Please invocation against a temporary or
   explicitly non-publishing context and prove the proposed first tag/version
   is exactly `v0.1.0`.
4. Add a bounded regression/static check where practical and update release
   documentation with the verified bootstrap/removal procedure.
5. Independently review the result before enabling the hosted release workflow.

## Boundaries

Use official Release Please documentation and current pinned workflow inputs.
Preserve the dirty shared worktree. Do not create a GitHub Release, tag, release
PR, commit, push, publish, or mutate remote repository settings.

## Pinned dry-run command

The workflow pins `release-please-action` v4.3.0, whose lockfile resolves
Release Please 17.1.2. After correcting the bootstrap files, run:

```bash
npx --yes release-please@17.1.2 release-pr \
  --token="${RELEASE_PLEASE_TOKEN}" \
  --repo-url=arturmartins/spdx-sorter \
  --target-branch=main \
  --config-file=release-please-config.json \
  --manifest-file=.release-please-manifest.json \
  --dry-run > release-please-dry-run.txt 2>&1
```

Retain the output with the ticket review and first release PR. It must propose
exactly `0.1.0`/`v0.1.0` and the intended changelog without remote mutation.
