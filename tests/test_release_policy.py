from pathlib import Path

ROOT = Path(__file__).parents[1]
WORKFLOW = (ROOT / ".github/workflows/release.yml").read_text()
CONTAINER_WORKFLOW = (ROOT / ".github/workflows/_build-container.yml").read_text()


def _job_block(workflow: str, job_name: str) -> str:
    marker = f"\n  {job_name}:\n"
    start = workflow.index(marker)
    next_job = workflow.find("\n  ", start + len(marker))
    while next_job != -1 and workflow[next_job + 3] == " ":
        next_job = workflow.find("\n  ", next_job + 1)
    if next_job == -1:
        return workflow[start:]
    return workflow[start:next_job]


def test_recovery_uses_default_branch_repository_dispatch_payload() -> None:
    assert "repository_dispatch:" in WORKFLOW
    assert "types: [recover-release]" in WORKFLOW
    assert "github.event.client_payload.tag" in WORKFLOW
    assert "workflow_dispatch:" not in WORKFLOW
    assert "inputs.release_tag" not in WORKFLOW


def test_recovery_verifies_release_and_main_ancestry() -> None:
    assert 'gh release view "${RELEASE_TAG}"' in WORKFLOW
    assert "git fetch" in WORKFLOW
    assert "git merge-base --is-ancestor" in WORKFLOW


def test_pypi_publish_is_preflighted_and_skippable() -> None:
    assert "scripts/pypi_preflight.py" in WORKFLOW
    assert "pypi-preflight.outputs.publish == 'true'" in WORKFLOW
    assert "pypi-dist" in WORKFLOW


def test_container_build_job_has_no_docker_hub_environment_or_secrets() -> None:
    build_job = _job_block(CONTAINER_WORKFLOW, "build")

    assert "name: docker-hub" not in build_job
    assert "secrets.DOCKERHUB" not in build_job
    assert "registry: docker.io" not in build_job
    assert "DOCKER_IMAGE:" not in build_job


def test_docker_hub_job_is_protected_digest_copy_without_rebuild() -> None:
    docker_hub_job = _job_block(CONTAINER_WORKFLOW, "docker-hub")

    assert "name: docker-hub" in docker_hub_job
    assert "packages: read" in docker_hub_job
    assert "registry: ghcr.io" in docker_hub_job
    assert "secrets.GITHUB_TOKEN" in docker_hub_job
    assert "secrets.DOCKERHUB_USERNAME" in docker_hub_job
    assert "secrets.DOCKERHUB_TOKEN" in docker_hub_job
    assert "docker/build-push-action" not in docker_hub_job
    assert "packages: write" not in docker_hub_job
    assert '"${GHCR_IMAGE}@${BUILD_DIGEST}"' in docker_hub_job


def test_container_tag_policy_is_tested_and_used_by_release_workflow() -> None:
    assert "scripts/container_tags.py" in CONTAINER_WORKFLOW
    assert "container-tags.txt" in CONTAINER_WORKFLOW
    assert "tail -n +2 container-tags.txt" in CONTAINER_WORKFLOW
    assert "tail -n +2 container-release/container-tags.txt" in CONTAINER_WORKFLOW


def test_exact_tag_preflight_uses_authenticated_registry_api_helper() -> None:
    build_job = _job_block(CONTAINER_WORKFLOW, "build")
    docker_hub_job = _job_block(CONTAINER_WORKFLOW, "docker-hub")

    assert "2>/dev/null" not in CONTAINER_WORKFLOW
    assert "classify_inspect_failure" not in CONTAINER_WORKFLOW
    assert CONTAINER_WORKFLOW.count("scripts/oci_tag_preflight.py") == 2
    assert "--registry ghcr.io" in build_job
    assert "--registry docker.io" in docker_hub_job
    assert "REGISTRY_PASSWORD: ${{ secrets.GITHUB_TOKEN }}" in build_job
    assert "REGISTRY_PASSWORD: ${{ secrets.DOCKERHUB_TOKEN }}" in docker_hub_job


def test_docker_hub_job_verifies_transferred_metadata_before_registry_operations() -> (
    None
):
    build_job = _job_block(CONTAINER_WORKFLOW, "build")
    docker_hub_job = _job_block(CONTAINER_WORKFLOW, "docker-hub")
    metadata = docker_hub_job.index("Verify downloaded container metadata")
    buildx_setup = docker_hub_job.index("Set up Docker Buildx")
    ghcr_login = docker_hub_job.index("Log in to GitHub Container Registry")
    docker_login = docker_hub_job.index("Log in to Docker Hub")
    registry_inspect = docker_hub_job.index("Verify canonical GHCR digest")

    assert "Checksum transferred release metadata" in build_job
    assert "container-metadata.txt" in build_job
    assert "container-tags.txt > SHA256SUMS-container.txt" in build_job
    assert metadata < buildx_setup < ghcr_login < docker_login < registry_inspect
    assert "sha256sum --check SHA256SUMS-container.txt" in docker_hub_job
    assert "awk 'END {print NR}' SHA256SUMS-container.txt" in docker_hub_job
    assert "awk 'END {print NR}' container-metadata.txt" in docker_hub_job
    assert "ghcr_image" in docker_hub_job
    assert "digest" in docker_hub_job
    assert "cmp -s" in docker_hub_job
