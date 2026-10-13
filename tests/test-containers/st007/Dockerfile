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

FROM mcr.microsoft.com/playwright:v1.64.0-noble

LABEL opamp-observe.managed="true"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/st007-venv/bin:${PATH}

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        git \
        python3 \
        python3-pip \
        python3-venv \
        tini \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/st007-venv \
    && python -m pip install --no-cache-dir --upgrade pip setuptools wheel

WORKDIR /runner
RUN npm init -y >/dev/null 2>&1 \
    && npm install --no-audit --no-fund --no-save @playwright/test@1.64.0

COPY tests/test-containers/scripts/prepare_source.sh /runner/prepare_source.sh
COPY tests/test-containers/st007/entrypoint.sh /runner/entrypoint.sh
COPY tests/test-containers/st007/scripts/playwright.config.js /runner/playwright.config.js
COPY tests/test-containers/st007/scripts/serve_credentials_manager.py /runner/serve_credentials_manager.py
COPY tests/test-containers/st007/scripts/st007_ui.spec.js /runner/st007_ui.spec.js
COPY tests/test-containers/st007/scripts/verify_st007.py /runner/verify_st007.py

RUN sed -i 's/\r$//' /runner/prepare_source.sh /runner/entrypoint.sh \
    && chmod +x /runner/prepare_source.sh /runner/entrypoint.sh /runner/verify_st007.py

VOLUME ["/workspace/opamp", "/host-output"]
ENTRYPOINT ["/usr/bin/tini", "--", "/runner/entrypoint.sh"]
