#!/usr/bin/env bash
# Licensed under the Apache License, Version 2.0.
# Copyright 2026 opamp.info
#
# Install and start the simulator consumer. The mounted /config directory
# chooses either the valid or wrong-audience Keycloak client.
set -euo pipefail

source_dir="$(st004-prepare-source)"

python -m pip install --no-cache-dir -e "${source_dir}/consumer"

export PYTHONPATH="${source_dir}/consumer/src:${source_dir}:${PYTHONPATH:-}"
export APP_ENABLE_DEV_FEATURES="${APP_ENABLE_DEV_FEATURES:-true}"

cd "${source_dir}"

exec python -m opamp_consumer.client \
  --config-path /config/opamp-consumer.json \
  --agent-config-path /config/simulator-agent.yaml

