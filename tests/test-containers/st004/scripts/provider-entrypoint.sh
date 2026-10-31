#!/usr/bin/env bash
# Licensed under the Apache License, Version 2.0.
# Copyright 2026 opamp.info
#
# Install and start the provider with Keycloak/JWT route protection enabled.
set -euo pipefail

source_dir="$(st004-prepare-source)"

python -m pip install --no-cache-dir -e "${source_dir}/provider"

export PYTHONPATH="${source_dir}/provider/src:${source_dir}:${PYTHONPATH:-}"

exec python -m opamp_provider.server \
  --config-path /config/opamp-provider.json \
  --host 0.0.0.0 \
  --port 8080

