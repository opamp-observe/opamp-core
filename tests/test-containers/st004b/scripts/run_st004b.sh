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

# Run one or all ST-004B authorization and TLS profiles with retained evidence.
set -euo pipefail

readonly all_profiles=(
  no-auth
  static-opamp
  static-ui
  static-both
  mcp-disabled
  jwt-negative
  tls
)
readonly compose_wait_timeout_seconds=180

requested_profile="${1:-all}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "${script_dir}/.." && pwd)"
repo_root="$(cd "${scenario_dir}/../../.." && pwd)"
compose_file="${scenario_dir}/docker-compose.yml"
provider_port="${ST004B_PROVIDER_PORT:-18084}"
issuer_port="${ST004B_ISSUER_PORT:-18085}"
output_root="${ST004B_OUTPUT_DIR:-${repo_root}/dist/test-reports/st004b}"
python_command=()

resolve_python_command() {
  # Select a real host Python interpreter, avoiding Windows Store aliases.
  if [[ -n "${OPAMP_PYTHON:-}" ]] && "${OPAMP_PYTHON}" -c "import sys" >/dev/null 2>&1; then
    python_command=("${OPAMP_PYTHON}")
  elif python3 -c "import sys" >/dev/null 2>&1; then
    python_command=(python3)
  elif python -c "import sys" >/dev/null 2>&1; then
    python_command=(python)
  elif py -3 -c "import sys" >/dev/null 2>&1; then
    python_command=(py -3)
  else
    printf 'could not find a working Python interpreter\n' >&2
    return 127
  fi
}

validate_profile() {
  # Reject unknown profile names before any Compose resources are changed.
  local candidate_profile="$1"
  if [[ "${candidate_profile}" == "all" ]]; then
    return 0
  fi
  local known_profile
  for known_profile in "${all_profiles[@]}"; do
    if [[ "${candidate_profile}" == "${known_profile}" ]]; then
      return 0
    fi
  done
  printf 'usage: %s [all|%s]\n' "$0" "$(IFS='|'; printf '%s' "${all_profiles[*]}")" >&2
  return 2
}

profile_services() {
  # Return the consumer services needed by one profile after provider startup.
  local active_profile="$1"
  case "${active_profile}" in
    no-auth|static-ui|static-both)
      printf '%s\n' consumer-valid
      ;;
    static-opamp|tls)
      printf '%s\n' consumer-valid consumer-invalid
      ;;
    mcp-disabled|jwt-negative)
      ;;
  esac
}

run_profile() {
  # Start, verify, capture, and tear down one isolated Compose profile.
  local active_profile="$1"
  local project_name="opamp-st004b-${active_profile}"
  local output_dir="${output_root}/${active_profile}"
  local base_scheme=http
  local verify_status=0
  local profile_service_list=()
  if [[ "${active_profile}" == "tls" ]]; then
    base_scheme=https
  fi
  while IFS= read -r service_name; do
    [[ -n "${service_name}" ]] && profile_service_list+=("${service_name}")
  done < <(profile_services "${active_profile}")

  mkdir -p "${output_dir}"
  export ST004B_PROFILE="${active_profile}"
  export ST004B_PROVIDER_PORT="${provider_port}"
  export ST004B_ISSUER_PORT="${issuer_port}"

  docker compose -p "${project_name}" -f "${compose_file}" down --remove-orphans
  set +e
  docker compose -p "${project_name}" -f "${compose_file}" up --build -d --wait \
    --wait-timeout "${compose_wait_timeout_seconds}" \
    provider "${profile_service_list[@]}"
  local startup_status=$?
  set -e
  if [[ "${startup_status}" -ne 0 ]]; then
    docker compose -p "${project_name}" -f "${compose_file}" logs --no-color \
      > "${output_dir}/compose.log" || true
    docker compose -p "${project_name}" -f "${compose_file}" down --remove-orphans
    return "${startup_status}"
  fi

  local verify_arguments=(
    --profile "${active_profile}"
    --base-url "${base_scheme}://127.0.0.1:${provider_port}"
    --issuer-url "http://127.0.0.1:${issuer_port}"
    --compose-file "${compose_file}"
    --compose-project "${project_name}"
    --output-dir "${output_dir}"
  )
  if [[ "${active_profile}" == "tls" ]]; then
    verify_arguments+=(--ca-file "${output_dir}/certs/provider-cert.pem")
  fi

  set +e
  "${python_command[@]}" "${scenario_dir}/scripts/verify_st004b.py" \
    "${verify_arguments[@]}" > "${output_dir}/verify.log" 2>&1
  verify_status=$?
  set -e
  docker compose -p "${project_name}" -f "${compose_file}" logs --no-color \
    > "${output_dir}/compose.log" || true
  docker compose -p "${project_name}" -f "${compose_file}" down --remove-orphans
  return "${verify_status}"
}

validate_profile "${requested_profile}"
resolve_python_command
mkdir -p "${output_root}"

profiles_to_run=("${requested_profile}")
if [[ "${requested_profile}" == "all" ]]; then
  profiles_to_run=("${all_profiles[@]}")
fi

overall_status=0
profile_results=()
for active_profile in "${profiles_to_run[@]}"; do
  printf '[ST-004B] running profile=%s\n' "${active_profile}"
  if run_profile "${active_profile}"; then
    profile_results+=("${active_profile}: passed")
  else
    profile_results+=("${active_profile}: failed")
    overall_status=1
  fi
done

if [[ "${requested_profile}" == "all" ]]; then
  aggregate_result=passed
  if [[ "${overall_status}" -ne 0 ]]; then
    aggregate_result=failed
  fi
  {
    printf '# ST-004B Aggregate Results\n\n'
    printf -- '- Result: %s\n' "${aggregate_result}"
    printf '\n## Profiles\n\n'
    for profile_result in "${profile_results[@]}"; do
      printf -- '- %s\n' "${profile_result}"
    done
  } > "${output_root}/results.md"
fi

exit "${overall_status}"
