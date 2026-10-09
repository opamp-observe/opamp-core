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

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace/opamp

COPY entrypoint.sh /opt/opamp-regression/entrypoint.sh
COPY scripts/run_consumer_plugin_startup.py /opt/opamp-regression/run_consumer_plugin_startup.py

RUN sed -i 's/\r$//' /opt/opamp-regression/entrypoint.sh /opt/opamp-regression/run_consumer_plugin_startup.py \
    && chmod +x /opt/opamp-regression/entrypoint.sh \
    && python -m pip install --no-cache-dir --upgrade pip setuptools wheel

VOLUME ["/workspace/opamp"]

ENTRYPOINT ["/opt/opamp-regression/entrypoint.sh"]
