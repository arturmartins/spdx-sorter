# Packaging and Container Plan

## Python distribution

The preferred distribution name is `spdx-sorter`. If that global PyPI name is
unavailable at publication time, the distribution alone becomes
`spdx-json-sorter`; the `spdx_sorter` import, `spdx-sort` command, repository,
and image names do not change.

Use standards-based `pyproject.toml` metadata with:

- Initial version `0.1.0`.
- `requires-python = ">=3.10"` and classifiers through Python 3.14.
- MIT license expression and included `LICENSE` file.
- README as the long description.
- Project, source, issue, changelog, and documentation URLs.
- `spdx-sort = "spdx_sorter.cli:main"` as the console entry point.
- No required third-party runtime dependencies for sorting.
- `spdx-tools>=0.8.5,<0.9` in a `validation` optional-dependency extra for
  `--validate` only.
- A typed-package marker and complete sdist inclusion rules.
- Separate development groups for test, lint, type, build, and release tools.

The exact Hatchling 1.27.0 build backend and all project extras/development
groups are recorded in `uv.lock`. Repository and release workflows run
`uv sync --frozen` and fail when the lock is stale rather than resolving an
unreviewed environment during publication. Release builds use the already
synced backend with `uv run --no-sync python -m build --no-isolation`, so PEP
517 does not create a second floating Hatchling environment.

Every release builds one pure-Python wheel and one source distribution. The
workflow verifies their metadata, filenames, version, contents, and clean
installation before either file is published.

## Installation and use

Before the first public release, users install a checkout from the repository
root with `python -m pip install .`; the local validation extra is installed
with `python -m pip install '.[validation]'`. After publication, the README
makes these the primary PyPI paths:

```bash
python -m pip install spdx-sorter
spdx-sort input.spdx.json > sorted.spdx.json
spdx-sort --check input.spdx.json
python -m pip install 'spdx-sorter[validation]'
spdx-sort --validate --in-place input.spdx.json
```

The fallback distribution name affects only the installation command. The base
wheel and runtime container must sort with the standard library alone. Images
that advertise `--validate` install the `validation` extra, but even there the
sorted JSON is never serialized through `spdx-tools`.

## Container contract

Publish equivalent images as:

- `ghcr.io/arturmartins/spdx-sorter`
- `docker.io/arturmartins/spdx-sorter`

The image uses `ENTRYPOINT ["spdx-sort"]`, has no default input argument, and
therefore works naturally as a filter:

```bash
docker run --rm -i ghcr.io/arturmartins/spdx-sorter:0.1.0 < input.spdx.json
```

Users can mount a working directory for file input or explicit in-place use.
The image runs as an unprivileged numeric user, has a predictable `/work`
working directory, and supports a read-only root filesystem.

## Image construction

- Use a multi-stage Dockerfile and a slim official Python base supported on all
  advertised architectures.
- Pin the base image by manifest-list digest and update it through reviewed
  automation.
- Build/install the project from the release source and locked dependency set.
- The standard image includes the validation extra solely to support
  `--validate`; sorting itself continues to use only the standard library.
- Constrain the image build to the reviewed `spdx-tools==0.8.5` runtime
  dependency closure while leaving the public optional-extra declaration in
  `pyproject.toml` as the dependency contract.
- Install the exact, reviewed Hatchling build-backend closure before building
  with `--no-build-isolation`. Refresh `requirements/build-constraints.txt`
  intentionally with this dry-run report command, then review the report and
  resulting pins with the validation constraints before changing the image:

  ```bash
  python -m pip install --dry-run --ignore-installed \
    --report /tmp/hatchling-report.json 'hatchling==1.27.0'
  ```

  The Docker constraints are image-only because that builder targets Python
  3.13; they must retain the same Hatchling 1.27.0 pin as `pyproject.toml` and
  `uv.lock`, and any transitive-version difference must be an explicit,
  reviewed compatibility choice rather than an accidental second pin.
- Copy only the runtime environment into the final stage.
- Exclude compilers, package-manager caches, test tools, source-control data,
  and credentials from the runtime image.
- Add standard OCI source, revision, version, license, title, and description
  labels.
- Include a container health check only if a meaningful non-I/O readiness
  signal is later introduced; a short-lived CLI does not need one.

The release manifest contains:

- `linux/amd64`
- `linux/arm64`
- `linux/arm/v7`

## Image tags

For stable `0.1.0`, publish `0.1.0`, `0.1`, `0`, and `latest`. For a prerelease,
publish only its exact version; prereleases never update floating tags.

GHCR is the canonical build registry. Docker Hub publication copies that exact
GHCR manifest digest from a separate protected job and does not rebuild the
image. All tags in both registries must resolve to equivalent manifest content.
The release records the canonical digest and fails if registry results
disagree. Tags are treated as release pointers; verification and automation
should pin the digest.

## Acceptance criteria

- Wheel and sdist install from a clean environment and expose identical APIs.
- The container reports the same version as the Python distribution.
- All three image architectures pass release smoke tests.
- The runtime user is non-root and the tool works with a read-only root.
- GHCR and Docker Hub manifests expose the same platforms and canonical digest.
