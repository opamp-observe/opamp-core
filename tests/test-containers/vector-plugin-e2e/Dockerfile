# Licensed under the Apache License, Version 2.0.
# Copyright 2026 mp3monster.org

FROM timberio/vector:0.58.0-debian

USER root

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
        python3 \
        python3-pip \
        python3-venv \
        tini \
    && rm -rf /var/lib/apt/lists/*

COPY scripts/prepare-source.sh /usr/local/bin/vector-e2e-prepare-source
COPY scripts/provider-entrypoint.sh /usr/local/bin/vector-e2e-provider-entrypoint
COPY scripts/consumer-entrypoint.sh /usr/local/bin/vector-e2e-consumer-entrypoint

RUN chmod +x \
    /usr/local/bin/vector-e2e-prepare-source \
    /usr/local/bin/vector-e2e-provider-entrypoint \
    /usr/local/bin/vector-e2e-consumer-entrypoint

WORKDIR /opt/opamp

VOLUME ["/workspace/source", "/config", "/evidence"]

ENTRYPOINT ["/usr/bin/tini", "--"]
