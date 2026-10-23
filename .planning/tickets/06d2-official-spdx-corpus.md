# Ticket 06D2 — Pinned official SPDX 2.2/2.3 conformance corpus

## Model

Primary: `gpt-5.6-terra`, medium reasoning. Quota fallback:
`gpt-5.6-luna`, high reasoning. Never use Sol High.

## Ownership

- `tests/fixtures/spdx-spec/**`
- `tests/test_fixtures.py` and new focused schema tests/helpers
- Test dependency metadata needed for offline JSON Schema validation
- Corpus sections in docs/plan and README
- `.superpowers/sdd/ROADMAP/task-06d2-report.md`

## Work

1. Obtain official SPDX 2.2 and 2.3 JSON schemas from `spdx/spdx-spec` and
   representative upstream fixture documents from official SPDX organization
   repositories, pinned to explicit release tags/commits. Prefer
   `spdx/spdx-spec`; where that release tree has no same-version JSON example,
   use `spdx/spdx-examples` or `spdx/tools-python` and record the separate
   provenance explicitly. Use primary upstream sources only.
2. Vendor the files for offline tests. Record source URL, tag, commit, upstream
   path, license, local path, checksum, and expected outcome in the corpus
   README.
3. If upstream invalid examples are absent, create clearly labeled local
   negative mutations of attributable upstream valid fixtures. Do not call
   project-authored minimal documents official upstream fixtures.
4. Add offline schema validation tests for both versions plus the existing
   `spdx-tools` adapter assertions. Keep producer compatibility fixtures
   separate and non-normative.
5. Preserve a dependency-free runtime; schema tooling belongs only to test
   dependencies. Do not regenerate the final lock in this unit—Ticket 06D3
   runs after dependency metadata settles.

## Boundaries

Use apply_patch and official SPDX organization primary sources. Preserve shared changes. No
subagents, commits, pushes, tags, publication, or remote mutation. Run focused
tests/Ruff/mypy/diff checks and write the report.
