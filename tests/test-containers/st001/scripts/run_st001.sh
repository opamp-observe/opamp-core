#!/usr/bin/env bash
# Licensed under the Apache License, Version 2.0.
# Copyright 2026 mp3monster.org
#
# Build, run, verify, capture evidence, and tear down one ST-001 profile. The
# script keeps orchestration repeatable so the Markdown and JSON evidence can be
# compared across WebSocket and HTTP runs.
set -euo pipefail

scenario="${1:-socket}"
case "${scenario}" in
  socket|http|all) ;;
  *)
    echo "usage: $0 [socket|http|all]" >&2
    exit 2
    ;;
esac

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "${script_dir}/.." && pwd)"
repo_root="$(cd "${scenario_dir}/../../.." && pwd)"
compose_file="${scenario_dir}/docker-compose.yml"
provider_port="${ST001_PROVIDER_PORT:-18080}"
output_root="${ST001_OUTPUT_DIR:-${repo_root}/dist/test-reports/st001}"
python_command=()

resolve_python_command() {
  # Select a host Python launcher that can execute the verifier. Windows Git
  # Bash can expose Store aliases for python3/python, so each candidate is
  # tested with a real import before it is accepted.
  if python3 -c "import sys" >/dev/null 2>&1; then
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

run_one() {
  # Parameters:
  # - name: profile name to run; must match a compose profile and consumer suffix.
  # The same value is used for evidence paths, compose project isolation, and
  # verifier expectations so profile-specific output stays grouped.
  local name="$1"
  local profile="$1"
  local consumer_service="consumer-${name}"
  local project="opamp-st001-${name}"
  local output_dir="${output_root}/${name}"

  mkdir -p "${output_dir}"
  # Start from a clean compose project to avoid stale containers or networks
  # influencing registration and disconnect assertions.
  docker compose -p "${project}" -f "${compose_file}" --profile "${profile}" down --remove-orphans
  set +e
  docker compose -p "${project}" -f "${compose_file}" --profile "${profile}" up --build -d
  local up_status=$?
  set -e

  if [ "${up_status}" -ne 0 ]; then
    docker compose -p "${project}" -f "${compose_file}" --profile "${profile}" logs \
      --no-color > "${output_dir}/compose.log" || true
    docker compose -p "${project}" -f "${compose_file}" --profile "${profile}" down --remove-orphans
    return "${up_status}"
  fi

  # Capture the verifier status manually so logs and cleanup still run when a
  # check fails; failing evidence is as useful as passing evidence.
  set +e
  "${python_command[@]}" "${scenario_dir}/scripts/verify_st001.py" \
    --scenario "${name}" \
    --base-url "http://127.0.0.1:${provider_port}" \
    --compose-file "${compose_file}" \
    --compose-project "${project}" \
    --consumer-service "${consumer_service}" \
    --output-dir "${output_dir}" \
    > "${output_dir}/verify.log" 2>&1
  local verify_status=$?
  set -e

  # Always retain compose logs beside the JSON evidence, then tear down the
  # profile-specific project to keep repeated local runs deterministic.
  docker compose -p "${project}" -f "${compose_file}" --profile "${profile}" logs \
    --no-color > "${output_dir}/compose.log" || true
  docker compose -p "${project}" -f "${compose_file}" --profile "${profile}" down --remove-orphans
  return "${verify_status}"
}

if [[ "${scenario}" == "all" ]]; then
  run_one socket
  run_one http
else
  run_one "${scenario}"
fi
