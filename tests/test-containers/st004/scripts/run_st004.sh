#!/usr/bin/env bash
# Licensed under the Apache License, Version 2.0.
# Copyright 2026 mp3monster.org
#
# Build, run, verify, capture evidence, and tear down the ST-004 Keycloak auth
# scenario. This follows the ST-001/ST-002 local compose harness shape.
set -euo pipefail

scenario="${1:-keycloak}"
case "${scenario}" in
  keycloak) ;;
  *)
    echo "usage: $0 [keycloak]" >&2
    exit 2
    ;;
esac

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "${script_dir}/.." && pwd)"
repo_root="$(cd "${scenario_dir}/../../.." && pwd)"
compose_file="${scenario_dir}/docker-compose.yml"
provider_port="${ST004_PROVIDER_PORT:-18083}"
keycloak_port="${ST004_KEYCLOAK_PORT:-18082}"
output_root="${ST004_OUTPUT_DIR:-${repo_root}/dist/test-reports/st004}"
project="${ST004_COMPOSE_PROJECT:-opamp-st004-keycloak}"
output_dir="${output_root}/${scenario}"
python_command=()

resolve_python_command() {
  # Select a host Python launcher that can execute the verifier. Windows Git
  # Bash can expose Store aliases for python3/python, so each candidate is
  # tested with a real import before it is accepted.
  if [ -n "${OPAMP_PYTHON:-}" ] && "${OPAMP_PYTHON}" -c "import sys" >/dev/null 2>&1; then
    python_command=("${OPAMP_PYTHON}")
  elif python3 -c "import sys" >/dev/null 2>&1; then
    python_command=(python3)
  elif python -c "import sys" >/dev/null 2>&1; then
    python_command=(python)
  elif py -3 -c "import sys" >/dev/null 2>&1; then
    python_command=(py -3)
  else
    echo "could not find a working Python interpreter; install Python 3 or add it to PATH" >&2
    return 127
  fi
}

resolve_python_command

mkdir -p "${output_dir}"

docker compose -p "${project}" -f "${compose_file}" down --remove-orphans
set +e
docker compose -p "${project}" -f "${compose_file}" up --build -d
up_status=$?
set -e

if [ "${up_status}" -ne 0 ]; then
  docker compose -p "${project}" -f "${compose_file}" logs --no-color \
    > "${output_dir}/compose.log" || true
  docker compose -p "${project}" -f "${compose_file}" down --remove-orphans
  exit "${up_status}"
fi

set +e
"${python_command[@]}" "${scenario_dir}/scripts/verify_st004.py" \
  --base-url "http://127.0.0.1:${provider_port}" \
  --keycloak-url "http://127.0.0.1:${keycloak_port}" \
  --compose-file "${compose_file}" \
  --compose-project "${project}" \
  --output-dir "${output_dir}" \
  > "${output_dir}/verify.log" 2>&1
verify_status=$?
set -e

docker compose -p "${project}" -f "${compose_file}" logs --no-color \
  > "${output_dir}/compose.log" || true
docker compose -p "${project}" -f "${compose_file}" down --remove-orphans
exit "${verify_status}"
