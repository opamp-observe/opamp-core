#!/usr/bin/env bash
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
#
# Copyright 2026 mp3monster.org

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "${script_dir}/.." && pwd)"
repo_root="$(cd "${scenario_dir}/../../.." && pwd)"
compose_file="${scenario_dir}/docker-compose.yml"
output_root="${AGENT_SHUTDOWN_OUTPUT_DIR:-${repo_root}/dist/test-reports/agent-shutdown-e2e}"
provider_port="${AGENT_SHUTDOWN_PROVIDER_PORT:-18190}"
provider_base_url="http://127.0.0.1:${provider_port}"
project_name="opamp-agent-shutdown-e2e"
network_name="opamp-agent-shutdown-e2e-network"
runtime_image="opamp-agent-shutdown-e2e-runtime:latest"
ui_image="opamp-agent-shutdown-e2e-ui:latest"
active_consumer=""

python_command=()
if command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
  python_command=(python3)
elif command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
  python_command=(python)
elif command -v py >/dev/null 2>&1 && py -3 --version >/dev/null 2>&1; then
  python_command=(py -3)
else
  echo "No usable Python executable found for agent shutdown verifier." >&2
  exit 1
fi

cleanup() {
  if [[ -n "${active_consumer}" ]]; then
    docker logs "${active_consumer}" \
      > "${scenario_output}/consumer-container.log" 2>&1 || true
    docker rm -f "${active_consumer}" >/dev/null 2>&1 || true
  fi
  docker compose -p "${project_name}" -f "${compose_file}" logs --no-color \
    > "${output_root}/compose.log" 2>&1 || true
  docker compose -p "${project_name}" -f "${compose_file}" down --remove-orphans \
    >/dev/null 2>&1 || true
}
trap cleanup EXIT

mkdir -p "${output_root}" "${repo_root}/dist/consumer"

docker version > "${output_root}/docker-preflight.log" 2>&1

"${python_command[@]}" -m pip install --upgrade build
"${python_command[@]}" -m build \
  --wheel \
  --outdir "${repo_root}/dist/consumer" \
  "${repo_root}/consumer"

docker compose -p "${project_name}" -f "${compose_file}" down --remove-orphans
docker compose -p "${project_name}" -f "${compose_file}" up --build -d provider
docker build \
  -f "${scenario_dir}/Dockerfile.ui" \
  -t "${ui_image}" \
  "${repo_root}"

read -r -a agent_types <<< "${AGENT_SHUTDOWN_AGENT_TYPES:-fluentbit fluentd elastic_agent elastic_heartbeat vector simulator}"
for agent_type in "${agent_types[@]}"; do
  service_instance_id="shutdown-e2e-${agent_type//_/-}"
  scenario_output="${output_root}/${agent_type}"
  active_consumer="opamp-agent-shutdown-${agent_type//_/-}"
  mkdir -p "${scenario_output}"

  docker rm -f "${active_consumer}" >/dev/null 2>&1 || true
  MSYS_NO_PATHCONV=1 docker run -d \
    --name "${active_consumer}" \
    --network "${network_name}" \
    -e "TEST_CONTAINER_CONFIG=/config/${agent_type}.env" \
    -v "${repo_root}:/host-assets:ro" \
    -v "${scenario_dir}/config/consumer:/config:ro" \
    -v "${scenario_dir}/config/consumer:/scenario-config:ro" \
    -v "${scenario_output}:/evidence" \
    "${runtime_image}" \
    /usr/local/bin/agent-shutdown-consumer-entrypoint >/dev/null

  "${python_command[@]}" "${script_dir}/verify_agent_shutdown.py" \
    --phase ready \
    --agent-type "${agent_type}" \
    --base-url "${provider_base_url}" \
    --container-name "${active_consumer}" \
    --service-instance-id "${service_instance_id}" \
    --output-dir "${scenario_output}"

  MSYS_NO_PATHCONV=1 docker run --rm \
    --network "${network_name}" \
    -e "PROVIDER_BASE_URL=http://provider:8080" \
    -e "SERVICE_INSTANCE_ID=${service_instance_id}" \
    -v "${scenario_output}:/evidence" \
    "${ui_image}"

  "${python_command[@]}" "${script_dir}/verify_agent_shutdown.py" \
    --phase confirm \
    --agent-type "${agent_type}" \
    --base-url "${provider_base_url}" \
    --container-name "${active_consumer}" \
    --service-instance-id "${service_instance_id}" \
    --output-dir "${scenario_output}"

  docker logs "${active_consumer}" > "${scenario_output}/consumer-container.log" 2>&1 || true
  docker rm -f "${active_consumer}" >/dev/null
  active_consumer=""
done

aggregate_agent_args=()
for agent_type in "${agent_types[@]}"; do
  aggregate_agent_args+=(--required-agent-type "${agent_type}")
done
"${python_command[@]}" "${script_dir}/verify_agent_shutdown.py" \
  --phase aggregate \
  "${aggregate_agent_args[@]}" \
  --output-dir "${output_root}"
