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

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git tini \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir --upgrade pip pytest

WORKDIR /runner
COPY tests/test-containers/scripts/prepare_source.sh /runner/prepare_source.sh
COPY tests/test-containers/st009/entrypoint.sh /runner/entrypoint.sh
COPY tests/test-containers/st009/scripts/verify_st009.py /runner/verify_st009.py
RUN chmod +x /runner/prepare_source.sh /runner/entrypoint.sh /runner/verify_st009.py

VOLUME ["/workspace/opamp", "/host-output"]
ENTRYPOINT ["/usr/bin/tini", "--", "/runner/entrypoint.sh"]
