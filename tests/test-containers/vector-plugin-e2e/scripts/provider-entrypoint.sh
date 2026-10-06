#!/usr/bin/env bash
# Licensed under the Apache License, Version 2.0.
# Copyright 2026 mp3monster.org

set -euo pipefail

source_dir="$(vector-e2e-prepare-source)"

python3 -m pip install --break-system-packages --no-cache-dir -e "${source_dir}/provider"

export PYTHONPATH="${source_dir}/provider/src:${source_dir}:${PYTHONPATH:-}"

exec python3 -m opamp_provider.server \
  --config-path /config/opamp-provider.json \
  --host 0.0.0.0 \
  --port 8080
