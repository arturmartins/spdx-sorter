# Supply-Chain Security Plan

## Objective

Target SLSA v1 Build Level 3 for Python and OCI release artifacts by combining
hosted GitHub Actions, separately reusable build workflows, and signed artifact
attestations. The claim is made only after the implemented workflow and its
verification results have been checked against the SLSA requirements; adding
an attestation action alone provides Build Level 2, not Level 3.

## Trusted build architecture

The release orchestrator may request a build but cannot inject build steps.
Build instructions and attestation generation live in these reusable
workflows:

- `.github/workflows/_build-python.yml`
- `.github/workflows/_build-container.yml`

Each reusable workflow accepts a release tag and expected version, verifies
that the tag belongs to this repository and matches the package metadata, and
checks out the immutable tag. It rejects arbitrary branches and pull-request
refs. The workflow builds, tests, and attests its subject before returning
artifact identifiers to publication jobs.

Both caller and reusable workflows receive only the permissions required by
GitHub's reusable-attestation model. Container construction uses `contents:
read`, `id-token: write`, `attestations: write`, and `packages: write` only for
the canonical GHCR build job. Docker Hub credentials are exposed only to the
separate protected Docker Hub job, which authenticates to GHCR with
`packages: read`, copies the accepted GHCR digest, and uses `id-token: write`
plus `attestations: write` for that registry identity. Pull-request CI
receives no OIDC or publication permission.

## Dependency and workflow integrity

- Pin every external GitHub Action to a full commit SHA and retain a readable
  version comment.
- Update pinned actions and dependencies through reviewed automation.
- Lock repository build and runtime dependencies; release builds fail on stale
  locks.
- Pin the container base by digest.
- Keep release credentials in protected environments and out of build jobs
  wherever OIDC can replace them.
- Require dependency review for new or upgraded dependencies.
- Run CodeQL and secret scanning in addition to functional CI.

## Provenance

Use `actions/attest` inside the reusable workflow that builds each subject.
Generate provenance for:

- The wheel.
- The source distribution.
- `ghcr.io/arturmartins/spdx-sorter` at the release manifest digest.
- `docker.io/arturmartins/spdx-sorter` after copying the same release manifest
  digest from GHCR without rebuilding.

Push OCI attestations to both registries. The current personal-account design
sets `create-storage-record: false` for OCI subjects, so their attestations are
registry-attached rather than stored as GitHub attestation records. Python
distribution attestations use GitHub's attestation service. Public-repository
signatures use Sigstore's public-good instance and transparency log.

PyPI trusted publishing also produces PyPI publish attestations automatically.
Those complement rather than replace the SLSA build provenance generated where
the distributions are built.

## SBOM

Generate an SPDX or CycloneDX JSON SBOM from the final multi-platform image.
Attest the SBOM against both fully qualified OCI subject names and the exact
manifest digest. Attach the human-downloadable SBOM and its checksum to the
GitHub Release.

The SBOM must describe the final runtime content, not only the source checkout
or builder stage. Generation failure blocks publication.

## Release channel inspection

Before attestation verification, prove that the expected files and image
identities exist and agree. For the first stable release:

```bash
export RELEASE_VERSION=0.1.0
export PYPI_PROJECT=spdx-sorter
export WHEEL_STEM=spdx_sorter

curl --fail --silent --show-error \
  "https://pypi.org/pypi/${PYPI_PROJECT}/${RELEASE_VERSION}/json" \
  | python -m json.tool > pypi-release.json
python -m pip download --no-deps --dest release-download \
  "${PYPI_PROJECT}==${RELEASE_VERSION}"
gh release download "v${RELEASE_VERSION}" \
  --pattern SHA256SUMS-python.txt --dir release-download
(cd release-download && sha256sum --check SHA256SUMS-python.txt)

GHCR_DIGEST="$(docker buildx imagetools inspect \
  "ghcr.io/arturmartins/spdx-sorter:${RELEASE_VERSION}" \
  --format '{{.Manifest.Digest}}')"
DOCKER_DIGEST="$(docker buildx imagetools inspect \
  "docker.io/arturmartins/spdx-sorter:${RELEASE_VERSION}" \
  --format '{{.Manifest.Digest}}')"
test "${GHCR_DIGEST}" = "${DOCKER_DIGEST}"

EXPECTED_REVISION="$(git rev-list -n 1 "v${RELEASE_VERSION}")"
for RELEASE_IMAGE in \
  ghcr.io/arturmartins/spdx-sorter \
  docker.io/arturmartins/spdx-sorter; do
  test "$(docker buildx imagetools inspect \
    "${RELEASE_IMAGE}:${RELEASE_VERSION}" \
    --format '{{index .Image.Config.Labels "org.opencontainers.image.version"}}')" \
    = "${RELEASE_VERSION}"
  test "$(docker buildx imagetools inspect \
    "${RELEASE_IMAGE}:${RELEASE_VERSION}" \
    --format '{{index .Image.Config.Labels "org.opencontainers.image.revision"}}')" \
    = "${EXPECTED_REVISION}"
done

for RELEASE_TAG in 0.1.0 0.1 0 latest; do
  docker buildx imagetools inspect \
    "ghcr.io/arturmartins/spdx-sorter:${RELEASE_TAG}"
  docker buildx imagetools inspect \
    "docker.io/arturmartins/spdx-sorter:${RELEASE_TAG}"
done
```

The image inspection output must list `linux/amd64`, `linux/arm64`, and
`linux/arm/v7`; the commands above also compare version and revision labels to
the tag and its commit. For a prerelease, inspect only its exact tag; floating
tags must remain unchanged. If Phase 7 selects the fallback PyPI distribution
name, set `PYPI_PROJECT=spdx-json-sorter` and
`WHEEL_STEM=spdx_json_sorter` before running these checks.

## Consumer verification

Python artifacts can be checked with the exact signer workflow:

```bash
gh attestation verify "${WHEEL_STEM}-${RELEASE_VERSION}-py3-none-any.whl" \
  --repo arturmartins/spdx-sorter \
  --signer-workflow arturmartins/spdx-sorter/.github/workflows/_build-python.yml
```

Verify the GHCR image:

```bash
gh attestation verify oci://ghcr.io/arturmartins/spdx-sorter:0.1.0 \
  --repo arturmartins/spdx-sorter \
  --signer-workflow arturmartins/spdx-sorter/.github/workflows/_build-container.yml
```

Verify the Docker Hub image using its `docker.io` identity:

```bash
gh attestation verify oci://docker.io/arturmartins/spdx-sorter:0.1.0 \
  --repo arturmartins/spdx-sorter \
  --signer-workflow arturmartins/spdx-sorter/.github/workflows/_build-container.yml
```

Release documentation also shows digest-pinned pulls. Verification must check
the repository, exact signer workflow, subject digest, and expected release
tag rather than accepting any attestation from the owner.

## Security acceptance criteria

- Pull-request code cannot obtain release OIDC tokens or registry credentials.
- Provenance is generated by the reusable workflow that built the subject.
- Verification rejects an artifact built by a different repository, workflow,
  ref, or digest.
- Both OCI identities have provenance and SBOM attestations.
- Release instructions can be followed from a clean machine with GitHub CLI.
- The achieved SLSA level is documented with evidence and no broader claim than
  the verified build design supports.

The repository workflow design does not itself prove that protected
environments, GitHub security features, or registry configuration are active.
Maintainers must complete and retain evidence for the external controls in
[the repository setup checklist](../REPOSITORY_SETUP.md).

## Authoritative references

- [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations)
- [GitHub guidance for SLSA Build Level 3](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/increase-security-rating)
- [Using artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations)
- [SLSA build requirements](https://slsa.dev/spec/v1.2/build-requirements)
- [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
- [PyPI attestations](https://docs.pypi.org/attestations/producing-attestations/)
