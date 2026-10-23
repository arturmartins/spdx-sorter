# SPDX JSON Sorter

`spdx-sorter` canonicalizes SPDX JSON deterministically so version-control
diffs show meaningful changes instead of ordering noise. Sorting uses only the
Python standard library and preserves producer-specific JSON fields.

## Installation

Python 3.10 through 3.14 is supported. Python 3.15 prerelease CI is
non-blocking until 3.15 is generally available; newer versions are untested.

The first public release has not been published yet. Until `0.1.0` is
available on PyPI, install a checkout from the repository root:

```bash
python -m pip install .
python -m pip install '.[validation]'  # optional SPDX validation
```

After the first release, install the published distribution with:

```bash
python -m pip install spdx-sorter
```

Validation is optional and installs `spdx-tools` separately:

```bash
python -m pip install 'spdx-sorter[validation]'
```

Use the repository's [GitHub Releases page](https://github.com/arturmartins/spdx-sorter/releases)
as the authoritative release-status source; a version in a source checkout is
not proof that it was published.

## Command line

Read a file and write canonical JSON to stdout; the input file is unchanged:

```bash
spdx-sort input.spdx.json > sorted.spdx.json
```

The command can also act as a stdin/stdout filter:

```bash
spdx-sort < input.spdx.json > sorted.spdx.json
```

Do not redirect stdout onto the same input path (`spdx-sort input > input`):
the shell truncates the destination before the command reads it. Use
`--in-place` for atomic replacement.

Check canonical form without writing, or explicitly replace a file atomically:

```bash
spdx-sort --check input.spdx.json
spdx-sort --in-place input.spdx.json
```

Validate before checking, printing, or replacing:

```bash
spdx-sort --validate input.spdx.json
spdx-sort --validate --in-place input.spdx.json
```

`python -m spdx_sorter` accepts the same arguments as `spdx-sort`.

## Git filter

Use `spdx-sort` as a git clean filter so SPDX documents are stored sorted
while your working copy stays untouched. Install it first (for example
`uv tool install spdx-sorter`), then in the repository:

```bash
echo '*.spdx.json filter=spdx-sort' >> .gitattributes
git config filter.spdx-sort.clean spdx-sort
git config filter.spdx-sort.smudge cat
git config filter.spdx-sort.required true
```

`git add` then stores the sorted form. Filter configuration lives in
`.git/config` and is not cloned, so each contributor repeats the `git config`
lines. Make sure the `spdx-sort` found on `PATH` is the one you installed,
or give the absolute path in `filter.spdx-sort.clean`. Invalid JSON makes the
filter fail (exit `2`), and `required` then aborts the `git add`.

## Container

The standard image includes the `validation` extra, so `--validate` is
available as well as the dependency-free sorting command. No public image is
claimed before the first release. Build it locally with:

```bash
docker build -t spdx-sorter:local .
```

It has `spdx-sort` as its entrypoint and no default input, making it a
stdin/stdout filter:

```bash
docker run --rm -i spdx-sorter:local < input.spdx.json > sorted.spdx.json
docker run --rm --read-only -i spdx-sorter:local --check < sorted.spdx.json
```

For file input, mount a working directory at `/work`. The image runs as the
numeric unprivileged user `65532:65532` and uses `/work` as its working
directory:

```bash
docker run --rm \
  --mount type=bind,source="$PWD",target=/work,readonly \
  spdx-sorter:local --validate input.spdx.json
```

The stable exit codes are:

- `0`: sorting/validation succeeded, or `--check` found canonical input
- `1`: `--check` found input that needs normalization
- `2`: usage, JSON parsing, validation, or I/O failure

JSON output is written only to stdout. Diagnostics and version warnings are
written to stderr. `--in-place` requires a file path; `--check` and
`--in-place` are mutually exclusive.

## Validation

Validation supports SPDX 2.2 and 2.3. Unknown, unsupported, and experimental
versions produce a validation issue instead of being presented as validated.
If the optional extra is missing, `--validate` prints the installation command
and exits before writing anything.

Validation parses a deep copy with `spdx-tools`, but output is always rendered
from the original JSON values by this project's standard-library sorter. No
upstream writer is used, so validation cannot silently rewrite or discard
producer extensions.

Without the validation extra, sorting, `--check`, `--in-place`, `sort_document`,
and `sort_json` remain available. Only `--validate` and `validate_document`
require `spdx-tools`.

## Python API

```python
from spdx_sorter import sort_document, sort_json, validate_document

canonical_value = sort_document(spdx_json_value)
canonical_text = sort_json(spdx_json_text)
issues = validate_document(spdx_json_value)
```

`sort_document` returns a new JSON structure and never mutates its argument.
`sort_json` uses two-space indentation, preserves non-ASCII text, and emits
exactly one trailing newline. `validate_document` returns an immutable,
deterministically ordered tuple of project-owned `ValidationIssue` values; it
raises `ValidationUnavailableError` when the optional dependency is absent.

## Canonicalization behavior

Dictionary keys are ordered lexicographically after their children are
normalized. Known SPDX set-semantic string arrays are sorted alphabetically.
Known object arrays—including packages, files, relationships, checksums,
annotations, external references, snippets, external document references, and
extracted licensing information—are sorted by their SPDX identity fields plus
a type-aware normalized JSON tie-breaker.

Mixed, malformed, and unknown arrays retain their input order. SPDX 2.2 and
2.3 rules are stable; detected SPDX 3.x sorting support is experimental and
reported as such on the CLI.

## Scope and limitations

- The tool handles JSON only and loads each document into memory; YAML, XML,
  RDF, tag/value, and streaming transformation are outside the `0.1.x` scope.
- Duplicate names within one JSON object cannot be preserved because the input
  is parsed into a Python mapping. Use a producer that emits unique object
  member names.
- Unknown and order-significant arrays are deliberately preserved rather than
  guessed at. A new sorting rule requires fixtures and invariant tests.
- `--validate` provides stable SPDX 2.2/2.3 validation only. SPDX 3.x behavior
  remains experimental.

## In-place writes

Atomic replacement preserves ordinary permission bits and follows symlinks so
the link itself remains intact. Atomic replacement intentionally breaks
hard-link identity. Ownership and extended-attribute preservation are outside
the 0.1.0 contract.

## Development

Run the locked test suite from the repository root:

```bash
uv lock --check
uv sync --frozen --group test --extra validation
uv run --no-sync pytest
```

The base package has no mandatory third-party runtime dependencies. Tests that
exercise real SPDX validation require the `validation` extra. Offline JSON
Schema conformance tests use vendored, pinned official SPDX schemas and
fixtures under `tests/fixtures/spdx-spec/`; those test-only dependencies are
kept out of the runtime package.

Build and quality environments use the same committed lockfile. For a local
release-style build, install the build group and invoke Hatchling from that
environment without an isolated resolver:

```bash
uv sync --frozen --group test --group build --extra validation
uv run --no-sync python -m build --no-isolation
```

For the complete local test, formatting, lint, typing, coverage, package, and
container commands, see [CONTRIBUTING.md](CONTRIBUTING.md). Pull requests use
Conventional Commit titles and are intended to be squash-merged; those titles
drive Release Please versioning. Repository settings that enforce review,
environment, registry, and security controls are listed—not claimed active—in
[the maintainer setup checklist](docs/REPOSITORY_SETUP.md).

## Releases and provenance

The following policy applies once maintainers enable the documented remote
controls and authorize a release. Release Please creates `v<version>` GitHub
Releases from Conventional Commit titles. The release workflow builds the
Python distributions and canonical multi-platform GHCR container once from
that immutable tag, then copies the
accepted GHCR digest to Docker Hub from a separate protected publication job.
Stable container releases publish the exact version, `<major>.<minor>`,
`<major>`, and `latest`; prereleases publish only the exact version. The
workflow publishes the exact tested files and attaches their checksums and
final-image SPDX SBOM. Manual recovery accepts only an existing GitHub Release
tag supplied through a `recover-release` repository-dispatch event. The
workflow definition comes from the default branch; recovery validates the tag,
its GitHub Release, and ancestry from `main` before building. It stops on an
immutable-asset hash conflict and never replaces a PyPI file or version tag.

To request recovery for an existing Release Please tag, run this exact command
from a maintainer workstation:

> **Hard gate:** the tag and its GitHub Release must already exist. Recovery
> cannot create the first release or publish an arbitrary branch/ref.

```bash
gh api repos/arturmartins/spdx-sorter/dispatches \
  --method POST \
  -f event_type=recover-release \
  -f 'client_payload[tag]=v0.1.0'
```

Before trusted publishing, the workflow queries the PyPI version JSON endpoint.
Files already present with the same SHA-256 are removed from the upload set;
missing files are published, while any differing digest or unexpected API
response fails closed. A rerun with no missing files skips the publish action.

After a hosted release, verify the package and container attestations with the
repository and signer workflow constraints documented in
[the supply-chain plan](docs/plan/supply-chain-security.md).

## License

MIT. See [LICENSE](LICENSE).
