# Copyright 2026 opamp.info
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

FROM python:3.12-slim AS builder

ARG UV_VERSION=0.10.12

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN python -m pip install --no-cache-dir "uv==${UV_VERSION}"

WORKDIR /build

COPY shared /build/shared
COPY provider /build/provider
COPY config-service /build/config-service
COPY catalog-service /build/catalog-service
COPY client-config-generator-service /build/client-config-generator-service
COPY consumer /build/consumer
COPY svr-credentials-mgr /build/svr-credentials-mgr
COPY opamp-suite /build/opamp-suite

# The provider's general-purpose wheel metadata references repository support folders. The DAST
# runtime needs none of their contents, so empty build-only placeholders satisfy wheel creation
# without copying documentation, scripts, developer notes, or test tools into the runtime image.
RUN mkdir -p /build/docs /build/scripts /build/mcp \
    && touch /build/docs/.dast-build-placeholder \
        /build/scripts/.dast-build-placeholder \
        /build/mcp/.dast-build-placeholder \
    && uv sync \
        --project /build/opamp-suite \
        --locked \
        --extra server \
        --no-dev \
        --no-editable \
    && rm -rf \
        /build/opamp-suite/.venv/lib/python*/site-packages/docs \
        /build/opamp-suite/.venv/lib/python*/site-packages/scripts \
    && rm -f \
        /build/opamp-suite/.venv/lib/python*/site-packages/mcp/.dast-build-placeholder

FROM python:3.12-slim AS runtime

LABEL opamp-observe.managed="true" \
      opamp-observe.purpose="dast-target"

ENV OPAMP_CONFIG_PATH=/app/config/opamp.json \
    PATH=/opt/opamp/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONNOUSERSITE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system opamp \
    && useradd --system --gid opamp --home-dir /app opamp \
    && mkdir -p \
        /app/config \
        /app/data/catalog \
        /app/data/connection-files \
        /app/data/generated-client-configs \
    && chown -R opamp:opamp /app

COPY --from=builder /build/opamp-suite/.venv /opt/opamp
COPY --chown=opamp:opamp dev-tools/docker/dast/opamp.json /app/config/opamp.json

USER opamp
WORKDIR /app

EXPOSE 8080

HEALTHCHECK --interval=2s --timeout=2s --start-period=10s --retries=60 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/ui', timeout=1).read(1)"]

ENTRYPOINT ["python", "-m", "opamp_provider.server"]
CMD ["--host", "0.0.0.0", "--port", "8080", "--config-path", "/app/config/opamp.json", "--log-level", "DEBUG"]
