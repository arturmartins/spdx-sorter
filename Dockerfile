# syntax=docker/dockerfile:1
ARG PYTHON_IMAGE=python:3.13-slim-bookworm@sha256:c45a22ea000adfd9cda29364bbe7edd23001ce5cc2ad15857cfbf7766943b9ca

FROM ${PYTHON_IMAGE} AS builder

ENV BUILD_VIRTUAL_ENV=/opt/build-venv \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN python -m venv ${BUILD_VIRTUAL_ENV}

COPY pyproject.toml README.md LICENSE ./
COPY requirements/ requirements/
COPY src/ src/

# Install the exact build backend before disabling PEP 517's unpinned isolated
# environment. The public validation extra remains declared in pyproject.toml.
RUN ${BUILD_VIRTUAL_ENV}/bin/python -m pip install \
        --constraint requirements/build-constraints.txt \
        --constraint requirements/validation-constraints.txt \
        hatchling==1.27.0

RUN ${BUILD_VIRTUAL_ENV}/bin/python -m pip wheel \
        --no-build-isolation \
        --no-deps \
        --wheel-dir /tmp/wheelhouse \
        . \
    && python -m venv /opt/venv \
    && WHEEL="$(find /tmp/wheelhouse -maxdepth 1 -name '*.whl' -print -quit)" \
    && test -n "${WHEEL}" \
    && /opt/venv/bin/python -m pip install \
        --constraint requirements/validation-constraints.txt \
        "spdx-sorter[validation] @ file://${WHEEL}"

FROM ${PYTHON_IMAGE} AS runtime

ARG BUILD_DATE=1970-01-01T00:00:00Z
ARG VCS_REF=unknown
ARG VERSION=0.1.0
ARG SOURCE=https://github.com/arturmartins/spdx-sorter
ARG TITLE=spdx-sorter
ARG DESCRIPTION="Deterministically canonicalize SPDX JSON for meaningful diffs"
ARG LICENSE=MIT
ARG BASE_IMAGE=python:3.13-slim-bookworm@sha256:c45a22ea000adfd9cda29364bbe7edd23001ce5cc2ad15857cfbf7766943b9ca

LABEL org.opencontainers.image.title=${TITLE} \
      org.opencontainers.image.description=${DESCRIPTION} \
      org.opencontainers.image.source=${SOURCE} \
      org.opencontainers.image.revision=${VCS_REF} \
      org.opencontainers.image.version=${VERSION} \
      org.opencontainers.image.licenses=${LICENSE} \
      org.opencontainers.image.created=${BUILD_DATE} \
      org.opencontainers.image.base.name=${BASE_IMAGE}

ENV PATH=/opt/venv/bin:${PATH} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# The build virtual environment, source tree, and wheelhouse stay in builder.
COPY --from=builder --chown=65532:65532 /opt/venv /opt/venv

RUN mkdir /work && chown 65532:65532 /work

WORKDIR /work
USER 65532:65532

HEALTHCHECK NONE
ENTRYPOINT ["spdx-sort"]
