# Copyright 2026 mp3monster.org
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

FROM python:3.11-slim

LABEL opamp-observe.managed="true"

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    OPAMP_REPO=/workspace/source

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        git \
        openssl \
        tini \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && python -m pip install --no-cache-dir "cryptography>=42.0" "PyJWT>=2.8"

COPY tests/test-containers/scripts/prepare_source.sh /usr/local/bin/st004b-prepare-source
COPY tests/test-containers/st004b/scripts/consumer-entrypoint.sh /usr/local/bin/st004b-consumer-entrypoint
COPY tests/test-containers/st004b/scripts/jwt_issuer.py /usr/local/bin/st004b-jwt-issuer
COPY tests/test-containers/st004b/scripts/provider-entrypoint.sh /usr/local/bin/st004b-provider-entrypoint

RUN sed -i 's/\r$//' \
      /usr/local/bin/st004b-prepare-source \
      /usr/local/bin/st004b-consumer-entrypoint \
      /usr/local/bin/st004b-provider-entrypoint \
    && chmod +x \
      /usr/local/bin/st004b-prepare-source \
      /usr/local/bin/st004b-consumer-entrypoint \
      /usr/local/bin/st004b-jwt-issuer \
      /usr/local/bin/st004b-provider-entrypoint

WORKDIR /opt/opamp

VOLUME ["/workspace/source", "/scenario-config", "/evidence"]

ENTRYPOINT ["/usr/bin/tini", "--"]
