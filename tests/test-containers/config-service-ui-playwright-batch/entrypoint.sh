#!/usr/bin/env bash
# Licensed under the Apache License, Version 2.0.
# Copyright 2026 mp3monster.org
#
# Build a disposable Config Service browser-test runtime, start the service,
# and run the Fluent Bit chapter batch through Playwright.
set -euo pipefail

OPAMP_REPO="${OPAMP_REPO:-/workspace/opamp}"
CONFIG_SERVICE_DIR="${CONFIG_SERVICE_DIR:-${OPAMP_REPO}/config-service}"
CONFIG_SERVICE_CONFIG_PATH="${CONFIG_SERVICE_CONFIG_PATH:-${CONFIG_SERVICE_DIR}/config/config-service.json}"
WHEEL_DIR="${WHEEL_DIR:-${CONFIG_SERVICE_DIR}/dist}"
RESULTS_DIR="${RESULTS_DIR:-${CONFIG_SERVICE_DIR}/dev-tools/playwright-batch-artifacts}"
LOGS_REPO_URL="${LOGS_REPO_URL:-https://github.com/mp3monster/Logs-and-Telemetry--Using-Fluent-Bit.git}"
LOGS_REPO_DIR="${LOGS_REPO_DIR:-/workspace/external/Logs-and-Telemetry--Using-Fluent-Bit}"
PLAYWRIGHT_BATCH_CONFIG="${PLAYWRIGHT_BATCH_CONFIG:-${CONFIG_SERVICE_DIR}/dev-tools/playwright-batch-config/default-batch-config.json}"
CONFIG_SERVICE_PORT="${CONFIG_SERVICE_PORT:-8091}"
BASE_URL="${BASE_URL:-http://127.0.0.1:${CONFIG_SERVICE_PORT}/config-service/ui}"

mkdir -p "${RESULTS_DIR}" "${RESULTS_DIR}/modified" "${RESULTS_DIR}/discrepancies"

if ! ls -1 "${WHEEL_DIR}"/*.whl >/dev/null 2>&1; then
  echo "No wheel files found in ${WHEEL_DIR}. Build a wheel on host first." >&2
  exit 1
fi

LATEST_WHEEL="$(ls -1t "${WHEEL_DIR}"/*.whl | head -n1)"
echo "Installing latest wheel: ${LATEST_WHEEL}"
python3 -m venv /opt/config-service-venv
. /opt/config-service-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --force-reinstall "${LATEST_WHEEL}"
export PYTHONPATH="${OPAMP_REPO}:${PYTHONPATH:-}"

if [ ! -d "${LOGS_REPO_DIR}/.git" ]; then
  echo "Cloning Fluent Bit sample repository into ${LOGS_REPO_DIR}"
  mkdir -p "$(dirname "${LOGS_REPO_DIR}")"
  git clone --depth 1 "${LOGS_REPO_URL}" "${LOGS_REPO_DIR}"
else
  echo "Refreshing existing Fluent Bit sample repository"
  git -C "${LOGS_REPO_DIR}" fetch --depth 1 origin
  git -C "${LOGS_REPO_DIR}" reset --hard origin/HEAD
fi

cd "${CONFIG_SERVICE_DIR}"

if [ -f package-lock.json ]; then
  npm ci || {
    echo "npm ci failed; falling back to npm install because package-lock.json is not in sync."
    npm install
  }
else
  echo "package-lock.json missing in ${CONFIG_SERVICE_DIR}; using npm install." >&2
  npm install
fi

if [ ! -d node_modules ]; then
  echo "npm dependencies missing after install; retrying npm install."
  npm install
fi

SERVER_LOG="${RESULTS_DIR}/config-service-server.log"
RUN_LOG="${RESULTS_DIR}/batch-run.log"
REPORT_FILE="${RESULTS_DIR}/execution-report.json"

: > "${SERVER_LOG}"
: > "${RUN_LOG}"

APP_ENABLE_DEV_FEATURES=1 \
  CONFIG_SERVICE_PORT="${CONFIG_SERVICE_PORT}" \
  config-service --config-path "${CONFIG_SERVICE_CONFIG_PATH}" --port "${CONFIG_SERVICE_PORT}" \
  >"${SERVER_LOG}" 2>&1 &
SERVER_PID=$!

cleanup() {
  if kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "Waiting for config-service to become healthy on port ${CONFIG_SERVICE_PORT}"
for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${CONFIG_SERVICE_PORT}/config-service/api/v1/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "http://127.0.0.1:${CONFIG_SERVICE_PORT}/config-service/api/v1/health" >/dev/null 2>&1; then
  echo "config-service failed to become healthy; see ${SERVER_LOG}" >&2
  exit 1
fi

set +e
node "${CONFIG_SERVICE_DIR}/dev-tools/playwright_chapter_batch_runner.mjs" \
  --base-url "${BASE_URL}" \
  --source-root "${LOGS_REPO_DIR}" \
  --config-file "${PLAYWRIGHT_BATCH_CONFIG}" \
  --report-file "${REPORT_FILE}" \
  --output-dir "${RESULTS_DIR}/modified" \
  --discrepancy-dir "${RESULTS_DIR}/discrepancies" \
  2>&1 | tee "${RUN_LOG}"
RUN_EXIT=${PIPESTATUS[0]}
set -e

if [ "${RUN_EXIT}" -ne 0 ]; then
  echo "Batch run completed with failures. See ${REPORT_FILE} and ${RESULTS_DIR}/discrepancies" >&2
else
  echo "Batch run completed successfully. Report: ${REPORT_FILE}"
fi

exit "${RUN_EXIT}"
