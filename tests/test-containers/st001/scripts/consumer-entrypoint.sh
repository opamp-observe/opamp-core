#!/usr/bin/env bash
# Licensed under the Apache License, Version 2.0.
# Copyright 2026 opamp.info
#
# Install and start the simulator consumer for the active profile. The profile
# config mounted at /config chooses WebSocket or HTTP transport.
set -euo pipefail

source_dir="$(st001-prepare-source)"

# Use an editable install so the consumer runs the same staged source as the
# provider, avoiding wheel/version drift in the baseline harness.
python -m pip install --no-cache-dir -e "${source_dir}/consumer"

export PYTHONPATH="${source_dir}/consumer/src:${source_dir}:${PYTHONPATH:-}"
# Simulator mode uses development-only switches that are intentionally explicit
# here rather than hidden inside the image.
export APP_ENABLE_DEV_FEATURES="${APP_ENABLE_DEV_FEATURES:-true}"

# Run from the source root because the supervisor signal is written relative to
# this tree by the verifier when it checks disconnect handling.
cd "${source_dir}"

exec python -m opamp_consumer.client \
  --config-path /config/opamp-consumer.json \
  --agent-config-path /config/simulator-agent.yaml
