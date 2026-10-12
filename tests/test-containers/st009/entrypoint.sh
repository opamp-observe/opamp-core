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

# Install the staged components and run the ST-009 safety, failure, and scale checks.
set -euo pipefail

results_dir="${RESULTS_DIR:-/host-output}"
staged_root="$(/runner/prepare_source.sh)"
mkdir -p "${results_dir}"

python -m pip install --no-cache-dir "${staged_root}/consumer" "${staged_root}/consumer-sim" "${staged_root}/provider"

set +e
{
  cd /tmp || exit 1
  scenario_status=0
  python -m pytest -q \
    -o addopts= \
    "${staged_root}/tests/test_consumer_sim_launcher.py" \
    "${staged_root}/consumer/tests/simulator/test_simulator_client.py" \
    --junitxml="${results_dir}/junit.xml" || scenario_status=$?
  python /runner/verify_st009.py \
    --output-dir "${results_dir}" \
    --scale-count 10 || scenario_status=$?
  exit "${scenario_status}"
} 2>&1 | tee "${results_dir}/verify.log"
scenario_status=${PIPESTATUS[0]}
set -e

scenario_result="passed"
if [[ "${scenario_status}" -ne 0 ]]; then
  scenario_result="failed"
fi
printf '{\n  "scenario": "ST-009",\n  "passed": %s,\n  "scale_count": 10\n}\n' \
  "$([[ "${scenario_status}" -eq 0 ]] && printf true || printf false)" \
  > "${results_dir}/summary.json"
printf '# ST-009 Container Results\n\n- Result: %s\n- Scale count: 10\n- Evidence: `verify.log`, `junit.xml`, `clients-connected.json`, `clients-disconnected.json`\n' \
  "${scenario_result}" > "${results_dir}/results.md"

exit "${scenario_status}"
