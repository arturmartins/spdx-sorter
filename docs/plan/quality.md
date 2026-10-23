# Quality Plan

## Outcome

Use executable behavioral guarantees—not example count alone—to prevent
regressions in sorting, validation, file safety, packaging, and containers.

## Test layers

### Unit tests

Small tests cover each stable sorting rule, type-aware tie-breakers, pure
version detection, rendering, validation-message conversion, exit-code
selection, and safe-write helper behavior.

### Property-based tests

Hypothesis generates JSON-compatible structures and SPDX-shaped documents to
check these invariants:

- Idempotence: `sort_document(sort_document(x)) == sort_document(x)`.
- No mutation of the caller's input.
- Equivalent permutations of set-semantic arrays produce equal output.
- Recognized object arrays produce equal output after permutation.
- Unknown and order-significant arrays preserve order.
- Rendering always parses as JSON and ends in one newline.
- JSON types with similar string forms do not collide in total sort keys.

Strategies use bounded depth and size so failures remain readable and CI is
predictable. Every discovered counterexample becomes a named regression test.

### SPDX fixtures and schemas

Pinned official SPDX schemas and upstream fixture documents are the normative
conformance inputs. The offline corpus records each source URL, tag or commit,
upstream path, license, local path, checksum, and expected outcome. Schemas are
vendored from `spdx/spdx-spec`; representative same-version fixture documents
come from official SPDX organization repositories when a specification release
tree does not include one.

The corpus includes:

- Valid SPDX 2.2 and 2.3 documents validated against the matching official
  JSON Schema.
- Clearly labeled local negative mutations of attributable upstream valid
  fixtures when official invalid examples are absent.
- Rich documents covering every stable sorting rule and lossless preservation
  of fields not modeled by the rules.
- Invalid references, license expressions, field types, and required fields.
- Unicode names and identifiers.
- Duplicate and missing identity fields.
- Mixed or malformed arrays that must be preserved conservatively.
- Unsupported 2.x and experimental 3.x documents, with explicit expected
  diagnostics rather than stable-conformance claims.

Producer-output fixtures from ScanCode Toolkit and lib4sbom are a separate
compatibility corpus. They demonstrate tolerant sorting of real-world output;
they do not define normative SPDX conformance and neither producer is a
runtime dependency. Fixtures derived from any upstream source retain their
original license and source attribution.

### CLI integration tests

Run the installed command as a subprocess and cover stdin/stdout, file/stdout,
`--check`, `--validate`, explicit in-place mutation, incompatible flags,
invalid JSON, missing files, permission failures, broken pipes, Unicode,
temporary-file cleanup, mode preservation, and symlink behavior.

Platform-specific assertions are skipped only with an explicit reason. POSIX
mode and directory-`fsync` behavior are tested on Linux; Windows still tests
replacement, cleanup, and diagnostics.

### Artifact smoke tests

- Build wheel and sdist and run `twine check` over both.
- Install the wheel and sdist independently in clean environments without the
  source tree on `PYTHONPATH`.
- For each artifact, import the public API, run `python -m spdx_sorter`, and
  invoke `spdx-sort`.
- Build the container and exercise stdin, `--check`, `--validate`, non-root
  execution, and a read-only root filesystem.
- Run sorting smoke tests in a base install with no third-party runtime
  dependencies; run validation tests only in the `validation` extra
  environment.
- For release candidates, smoke-test every advertised image architecture.

## Static quality gates

- Ruff formatting check.
- Ruff linting with import, correctness, modernization, and security-relevant
  rules enabled deliberately rather than accepting an unreviewed preset.
- Strict static type checking over every production module under `src/`.
- `pytest` with warnings treated as errors for project code.
- Minimum 95% line coverage and 90% branch coverage.
- Package metadata and README rendering checks.

Coverage excludes no project module wholesale. Narrow defensive branches may
be excluded only with an inline justification and review.

## CI matrix

Required jobs:

- Python 3.10, 3.11, 3.12, 3.13, and 3.14 on Linux.
- Latest supported Python on macOS and Windows for filesystem and CLI behavior.
- Quality, build, installed-wheel, and container smoke jobs.

Python 3.15 prerelease runs with prereleases explicitly enabled and is
non-blocking. It becomes required once 3.15 is generally available and the
declared metadata is updated in the same pull request.

CI uses `fail-fast: false` for version matrices so one failure does not hide
compatibility results from other interpreters.

## Merge acceptance

A change may merge only when:

- Required tests and static checks pass.
- Coverage stays above both thresholds.
- New behavior includes behavior-level tests.
- Sorting-rule changes include an idempotence and permutation check.
- Conformance changes identify the pinned official schema or fixture input;
  producer compatibility additions identify their producer and remain outside
  the normative corpus.
- Public interface changes update the development and user documentation.
- Dependency changes pass dependency review and artifact smoke tests.
- Workflow changes keep permissions job-scoped and actions SHA-pinned.
