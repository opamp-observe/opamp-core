# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Copyright 2026 mp3monster.org

FROM cr.fluentbit.io/fluent/fluent-bit:5.0.3 AS fluent-bit-runtime
FROM timberio/vector:0.58.0-debian AS vector-runtime
FROM docker.elastic.co/elastic-agent/elastic-agent:9.3.3 AS elastic-agent-runtime

FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    LD_LIBRARY_PATH=/opt/fluent-bit/lib

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        ca-certificates \
        curl \
        git \
        libpq5 \
        libssl-dev \
        pkg-config \
        ruby \
        ruby-dev \
        tini \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir --upgrade pip setuptools wheel

COPY tests/test-containers/opamp-consumer-deployment/scripts/bootstrap.py /opt/opamp-test/bootstrap.py
COPY tests/test-containers/opamp-consumer-deployment/defaults /opt/opamp-test/defaults
COPY tests/test-containers/agent-shutdown-e2e/scripts/provider-entrypoint.sh /usr/local/bin/agent-shutdown-provider-entrypoint
COPY tests/test-containers/agent-shutdown-e2e/scripts/consumer-entrypoint.sh /usr/local/bin/agent-shutdown-consumer-entrypoint
COPY --from=fluent-bit-runtime /fluent-bit /opt/fluent-bit
COPY --from=vector-runtime /usr/bin/vector /usr/local/bin/vector
COPY --from=elastic-agent-runtime /usr/share/elastic-agent /usr/share/elastic-agent

RUN sed -i 's/\r$//' \
        /opt/opamp-test/bootstrap.py \
        /usr/local/bin/agent-shutdown-provider-entrypoint \
        /usr/local/bin/agent-shutdown-consumer-entrypoint \
    && ln -s /opt/fluent-bit/bin/fluent-bit /usr/local/bin/fluent-bit \
    && chmod +x \
        /opt/opamp-test/bootstrap.py \
        /usr/local/bin/agent-shutdown-provider-entrypoint \
        /usr/local/bin/agent-shutdown-consumer-entrypoint

WORKDIR /work

VOLUME ["/workspace/source", "/config", "/evidence", "/host-assets"]

ENTRYPOINT ["/usr/bin/tini", "--"]
