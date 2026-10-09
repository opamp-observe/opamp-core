# Licensed under the Apache License, Version 2.0.
# Copyright 2026 mp3monster.org

FROM python:3.11-slim

LABEL opamp-observe.managed="true"

# The ST-002 services all use this same image. Source is staged at runtime so
# the containers can test either the mounted working tree or a pinned Git ref.
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    OPAMP_SOURCE_DIR=/opt/opamp/source \
    OPAMP_LOCAL_SOURCE=/workspace/source

# Keep the image deliberately small: only shell, Git, curl for health checks,
# and tini for predictable signal handling are required by the harness.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        git \
        tini \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Scenario-specific wrapper names make compose logs and docker exec commands
# unambiguous when ST-001, ST-002, and later scenarios run on the same host.
COPY scripts/prepare-source.sh /usr/local/bin/st002-prepare-source
COPY scripts/provider-entrypoint.sh /usr/local/bin/st002-provider-entrypoint
COPY scripts/consumer-entrypoint.sh /usr/local/bin/st002-consumer-entrypoint

RUN sed -i 's/\r$//' \
    /usr/local/bin/st002-prepare-source \
    /usr/local/bin/st002-provider-entrypoint \
    /usr/local/bin/st002-consumer-entrypoint \
    && chmod +x \
    /usr/local/bin/st002-prepare-source \
    /usr/local/bin/st002-provider-entrypoint \
    /usr/local/bin/st002-consumer-entrypoint

WORKDIR /opt/opamp

# The harness mounts source, read-only config, and writable evidence separately
# so test output never pollutes the staged source tree.
VOLUME ["/workspace/source", "/config", "/evidence"]

ENTRYPOINT ["/usr/bin/tini", "--"]
