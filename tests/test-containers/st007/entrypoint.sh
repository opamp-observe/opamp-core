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

# Run ST-007 API, live-delivery, fallback, and browser verification layers.
set -euo pipefail

readonly ui_port=18191
results_dir="${RESULTS_DIR:-/host-output}"
staged_root="$(/runner/prepare_source.sh)"
ui_runtime_dir=""
ui_log_path="${results_dir}/ui-service.log"
ui_process_id=""
ui_ready=0

cleanup() {
  # Stop the browser-test service without hiding the original scenario status.
  if [[ -n "${ui_process_id}" ]] && kill -0 "${ui_process_id}" 2>/dev/null; then
    kill "${ui_process_id}" 2>/dev/null || true
    wait "${ui_process_id}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

mkdir -p "${results_dir}" "${results_dir}/screenshots"
ui_runtime_dir="$(mktemp -d "${results_dir}/ui-runtime.XXXXXX")"

python -m pip install --no-cache-dir \
  -e "${staged_root}/provider" \
  -e "${staged_root}/consumer" \
  -e "${staged_root}/svr-credentials-mgr[dev]"

api_status=0
integration_status=0
ui_status=0

set +e
(
  cd "${staged_root}/svr-credentials-mgr" || exit 1
  python -m pytest -q -s -o addopts= \
    tests \
    plaintext-keyring/tests \
    --junitxml="${results_dir}/api-junit.xml"
) 2>&1 | tee "${results_dir}/api-tests.log"
api_status=${PIPESTATUS[0]}

python /runner/verify_st007.py \
  --repo-root "${staged_root}" \
  --service-script /runner/serve_credentials_manager.py \
  --output-dir "${results_dir}" \
  2>&1 | tee "${results_dir}/integration.log"
integration_status=${PIPESTATUS[0]}

python /runner/serve_credentials_manager.py \
  --runtime-dir "${ui_runtime_dir}" \
  --port "${ui_port}" \
  --provider-base-url http://127.0.0.1:1 \
  --seed-stale-mapping \
  >"${ui_log_path}" 2>&1 &
ui_process_id=$!

for attempt_number in $(seq 1 60); do
  if curl --fail --silent \
    "http://127.0.0.1:${ui_port}/svr-credentials-manager-service/api/v1/health" \
    >/dev/null; then
    ui_ready=1
    break
  fi
  if ! kill -0 "${ui_process_id}" 2>/dev/null; then
    printf 'ST-007 UI service exited before readiness\n' >&2
    ui_status=1
    break
  fi
  sleep 1
done

if [[ "${ui_ready}" -ne 1 ]]; then
  printf 'ST-007 UI service did not become ready within the allowed time\n' >&2
  ui_status=1
fi

if [[ "${ui_status}" -eq 0 ]]; then
  ST007_BASE_URL="http://127.0.0.1:${ui_port}" \
  ST007_RESULTS_DIR="${results_dir}" \
    npx playwright test \
      --config=/runner/playwright.config.js \
      /runner/st007_ui.spec.js \
      2>&1 | tee "${results_dir}/playwright.log"
  ui_status=${PIPESTATUS[0]}
fi
set -e

overall_status=0
if [[ "${api_status}" -ne 0 || "${integration_status}" -ne 0 || "${ui_status}" -ne 0 ]]; then
  overall_status=1
fi

scenario_result=passed
if [[ "${overall_status}" -ne 0 ]]; then
  scenario_result=failed
fi

printf '{\n  "scenario": "ST-007",\n  "passed": %s,\n  "layers": {\n    "api": %s,\n    "integration": %s,\n    "browser": %s\n  }\n}\n' \
  "$([[ "${overall_status}" -eq 0 ]] && printf true || printf false)" \
  "$([[ "${api_status}" -eq 0 ]] && printf true || printf false)" \
  "$([[ "${integration_status}" -eq 0 ]] && printf true || printf false)" \
  "$([[ "${ui_status}" -eq 0 ]] && printf true || printf false)" \
  > "${results_dir}/summary.json"

printf '# ST-007 Container Results\n\n- Result: %s\n- API/unit layer: %s\n- Live/fallback integration layer: %s\n- Browser layer: %s\n- Evidence: `api-junit.xml`, `api-tests.log`, `integration-summary.json`, `provider-request-capture.json`, `fallback-deliveries.jsonl`, `playwright-junit.xml`, `screenshots/`, and `playwright/`\n' \
  "${scenario_result}" \
  "$([[ "${api_status}" -eq 0 ]] && printf passed || printf failed)" \
  "$([[ "${integration_status}" -eq 0 ]] && printf passed || printf failed)" \
  "$([[ "${ui_status}" -eq 0 ]] && printf passed || printf failed)" \
  > "${results_dir}/results.md"

exit "${overall_status}"
