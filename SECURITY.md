# Security Policy

## Supported versions

No public release exists yet, so there is currently no supported release
channel. Unreleased commits are development snapshots and receive fixes through
normal review rather than coordinated release support.

After `0.1.0` is published, security fixes will target the latest released
`0.1.x` version. The project is pre-1.0; superseded releases will not be
supported unless this policy says otherwise. Maintainers review the policy at
least quarterly and before each minor release.

## Reporting a vulnerability

Please use the repository's
[private vulnerability-report form](https://github.com/arturmartins/spdx-sorter/security/advisories/new)
once it is enabled. Do not open a public issue, publish an exploit, or include
secrets in a report. If the private form is unavailable, contact the repository
owner privately through the contact method on the
[owner's GitHub profile](https://github.com/arturmartins) and include a concise
reproduction, impact, and affected version.

Maintainers aim to acknowledge reports within seven calendar days and provide
an initial assessment or status update within 30 days. These are targets, not a
guarantee of a fix timeline.

## Disclosure and release handling

We will coordinate disclosure with the reporter, credit them when requested,
and publish a fix in a new version where practical. Do not rely on replacing a
published PyPI artifact, version tag, or immutable release asset: releases are
treated as immutable. Security fixes follow the normal review and release
authority described in [CONTRIBUTING.md](CONTRIBUTING.md).

Repository files can express this policy and run checks; private reporting,
secret scanning, push protection, Dependabot alerts, and security advisories
are GitHub settings that require maintainer verification. See the exact setup
checklist in [docs/REPOSITORY_SETUP.md](docs/REPOSITORY_SETUP.md).
