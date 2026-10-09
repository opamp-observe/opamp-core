# Copyright 2026 mp3monster.org
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
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
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        ca-certificates \
        curl \
        git \
        ruby \
        ruby-dev \
        tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work

COPY scripts/bootstrap.py /opt/opamp-test/bootstrap.py
COPY entrypoint.sh /opt/opamp-test/entrypoint.sh
COPY defaults /opt/opamp-test/defaults

RUN sed -i 's/\r$//' /opt/opamp-test/bootstrap.py /opt/opamp-test/entrypoint.sh \
    && chmod +x /opt/opamp-test/bootstrap.py /opt/opamp-test/entrypoint.sh \
    && python -m pip install --no-cache-dir --upgrade pip setuptools wheel

VOLUME ["/config", "/host-assets", "/host-output"]

ENTRYPOINT ["/usr/bin/tini", "--", "/opt/opamp-test/entrypoint.sh"]
