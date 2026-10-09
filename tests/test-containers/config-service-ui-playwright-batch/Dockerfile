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

FROM mcr.microsoft.com/playwright:v1.64.0-noble

LABEL opamp-observe.managed="true"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       python3 \
       python3-pip \
       python3-venv \
       git \
       curl \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY tests/test-containers/config-service-ui-playwright-batch/entrypoint.sh /usr/local/bin/run-config-service-playwright-batch
RUN sed -i 's/\r$//' /usr/local/bin/run-config-service-playwright-batch \
    && chmod +x /usr/local/bin/run-config-service-playwright-batch

ENTRYPOINT ["/usr/local/bin/run-config-service-playwright-batch"]
