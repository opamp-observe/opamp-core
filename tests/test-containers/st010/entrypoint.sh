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

# Exercise CLI behavior and build/install/release assets from a writable staged checkout.
set -euo pipefail

results_dir="${RESULTS_DIR:-/host-output}"
staged_root="$(/runner/prepare_source.sh)"
clean_root="/tmp/opamp-st010"
wheel_results_dir="${results_dir}/wheel-deployment"
mkdir -p "${results_dir}" "${wheel_results_dir}"

python -m pip install --no-cache-dir \
  "${staged_root}/cli[dev]" \
  "${staged_root}/config-service" \
  "${staged_root}/dev-tools[dev]"

set +e
{
  cd /tmp || exit 1
  scenario_status=0
  python -m pytest -q \
    -o addopts= \
    "${staged_root}/cli/tests/test_component_version.py" \
    "${staged_root}/cli/tests/test_main_e2e.py" \
    "${staged_root}/cli/tests/test_main_unit.py" \
    "${staged_root}/dev-tools/tests/test_release_assets.py" \
    "${staged_root}/tests/test_packaging_warnings.py" \
    --junitxml="${results_dir}/junit.xml" || scenario_status=$?
  python /runner/run_component_wheel_deployment.py \
    --repo-root "${staged_root}" \
    --results-dir "${wheel_results_dir}" \
    --clean-root "${clean_root}" || scenario_status=$?
  python /runner/verify_st010.py \
    --repo-root "${staged_root}" \
    --clean-root "${clean_root}" \
    --output-dir "${results_dir}" || scenario_status=$?
  exit "${scenario_status}"
} 2>&1 | tee "${results_dir}/verify.log"
scenario_status=${PIPESTATUS[0]}
set -e

scenario_result="passed"
if [[ "${scenario_status}" -ne 0 ]]; then
  scenario_result="failed"
fi
printf '{\n  "scenario": "ST-010",\n  "passed": %s\n}\n' \
  "$([[ "${scenario_status}" -eq 0 ]] && printf true || printf false)" \
  > "${results_dir}/summary.json"
printf '# ST-010 Container Results\n\n- Result: %s\n- Evidence: `verify.log`, `junit.xml`, `artifacts.json`, `wheel-deployment/`\n' \
  "${scenario_result}" > "${results_dir}/results.md"

exit "${scenario_status}"
