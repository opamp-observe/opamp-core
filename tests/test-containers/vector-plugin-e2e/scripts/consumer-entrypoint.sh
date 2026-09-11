#!/usr/bin/env bash
# Licensed under the Apache License, Version 2.0.
# Copyright 2026 mp3monster.org

set -euo pipefail

source_dir="$(vector-e2e-prepare-source)"

python3 -m pip install --break-system-packages --no-cache-dir -e "${source_dir}/consumer"

export PYTHONPATH="${source_dir}/consumer/src:${source_dir}:${PYTHONPATH:-}"
export APP_ENABLE_DEV_FEATURES="${APP_ENABLE_DEV_FEATURES:-true}"

mkdir -p /tmp/opamp-vector-e2e
cd /tmp/opamp-vector-e2e

exec python3 -m opamp_consumer.client \
  --config-path /config/opamp-consumer-vector.json \
  --agent-config-path /config/vector-self-monitor.yaml
