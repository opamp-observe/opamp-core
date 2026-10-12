#!/usr/bin/env bash
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

# Install and start the simulator consumer selected by profile and role.
set -euo pipefail

profile="${ST004B_PROFILE:-no-auth}"
consumer_role="${ST004B_CONSUMER_ROLE:-valid}"
staged_root="$(st004b-prepare-source)"
config_path="/scenario-config/consumer/${profile}/${consumer_role}.json"

if [[ ! -f "${config_path}" ]]; then
  printf 'missing ST-004B consumer config profile=%s role=%s\n' \
    "${profile}" "${consumer_role}" >&2
  exit 2
fi

python -m pip install --no-cache-dir -e "${staged_root}/consumer"
export PYTHONPATH="${staged_root}/consumer/src:${staged_root}:${PYTHONPATH:-}"
export APP_ENABLE_DEV_FEATURES="${APP_ENABLE_DEV_FEATURES:-true}"

cd "${staged_root}"
exec python -m opamp_consumer.client \
  --config-path "${config_path}" \
  --agent-config-path /scenario-config/consumer/common/simulator-agent.yaml
