# Licensed under the Apache License, Version 2.0.
# Copyright 2026 mp3monster.org

FROM python:3.11-slim

LABEL opamp-observe.managed="true"

# ST-004 follows the same source-at-runtime pattern as ST-001/ST-002 so local
# checkout changes can be exercised without rebuilding a copied-source image.
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    OPAMP_SOURCE_DIR=/opt/opamp/source \
    OPAMP_LOCAL_SOURCE=/workspace/source

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        git \
        tini \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir --upgrade pip setuptools wheel

COPY scripts/prepare-source.sh /usr/local/bin/st004-prepare-source
COPY scripts/provider-entrypoint.sh /usr/local/bin/st004-provider-entrypoint
COPY scripts/consumer-entrypoint.sh /usr/local/bin/st004-consumer-entrypoint

RUN sed -i 's/\r$//' \
    /usr/local/bin/st004-prepare-source \
    /usr/local/bin/st004-provider-entrypoint \
    /usr/local/bin/st004-consumer-entrypoint \
    && chmod +x \
    /usr/local/bin/st004-prepare-source \
    /usr/local/bin/st004-provider-entrypoint \
    /usr/local/bin/st004-consumer-entrypoint

WORKDIR /opt/opamp

VOLUME ["/workspace/source", "/config", "/evidence"]

ENTRYPOINT ["/usr/bin/tini", "--"]

