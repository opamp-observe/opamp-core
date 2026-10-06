#!/usr/bin/env bash
# Licensed under the Apache License, Version 2.0.
# Copyright 2026 mp3monster.org

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scenario_dir="$(cd "${script_dir}/.." && pwd)"
repo_root="$(cd "${scenario_dir}/../../.." && pwd)"
compose_file="${scenario_dir}/docker-compose.yml"
provider_port="${VECTOR_E2E_PROVIDER_PORT:-18180}"
output_root="${VECTOR_E2E_OUTPUT_DIR:-${repo_root}/dist/test-reports/vector-plugin-e2e}"
project="opamp-vector-plugin-e2e"

mkdir -p "${output_root}" "${output_root}/consumer-vector"

python_cmd=()
if command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
  python_cmd=(python3)
elif command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
  python_cmd=(python)
elif command -v py >/dev/null 2>&1 && py -3 --version >/dev/null 2>&1; then
  python_cmd=(py -3)
else
  echo "No usable Python executable found for Vector e2e verifier." >&2
  exit 1
fi

set +e
docker version > "${output_root}/docker-preflight.log" 2>&1
docker_status=$?
set -e
if [ "${docker_status}" -ne 0 ]; then
  generated="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cat > "${output_root}/summary.json" <<JSON
{
  "checks": [
    {
      "name": "docker_engine_available",
      "passed": false,
      "value": "docker version failed; see docker-preflight.log"
    }
  ],
  "evidence": {
    "docker_preflight": "${output_root}/docker-preflight.log"
  },
  "generated_at_utc": "${generated}",
  "result": "failed",
  "service_instance_id": "vector-plugin-e2e"
}
JSON
  cat > "${output_root}/results.md" <<MD
# Vector Plugin E2E Results

- Generated: ${generated}
- Result: failed

| Check | Result | Evidence |
|---|---:|---|
| docker_engine_available | FAIL | \`docker version failed; see docker-preflight.log\` |
MD
  exit "${docker_status}"
fi

docker compose -p "${project}" -f "${compose_file}" down --remove-orphans
set +e
docker compose -p "${project}" -f "${compose_file}" up --build -d
up_status=$?
set -e

if [ "${up_status}" -ne 0 ]; then
  docker compose -p "${project}" -f "${compose_file}" logs --no-color > "${output_root}/compose.log" || true
  docker compose -p "${project}" -f "${compose_file}" down --remove-orphans
  exit "${up_status}"
fi

set +e
"${python_cmd[@]}" "${scenario_dir}/scripts/verify_vector_plugin_e2e.py" \
  --base-url "http://127.0.0.1:${provider_port}" \
  --output-dir "${output_root}" \
  --vector-output "${output_root}/consumer-vector/vector-self-monitor.log" \
  > "${output_root}/verify.log" 2>&1
verify_status=$?
set -e

docker compose -p "${project}" -f "${compose_file}" logs --no-color > "${output_root}/compose.log" || true
docker compose -p "${project}" -f "${compose_file}" down --remove-orphans
exit "${verify_status}"
