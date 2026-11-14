#!/usr/bin/env bash
# Licensed under the Apache License, Version 2.0.
# Copyright 2026 opamp.info
#
# Install and start the provider from the staged source tree. The editable
# install keeps the container faithful to the source mounted or cloned for this
# specific scenario run.
set -euo pipefail

source_dir="$(st001-prepare-source)"

# Install inside the runtime container rather than baking the project into the
# image so uncommitted local changes can be exercised without rebuilding images
# from a copied source context.
python -m pip install --no-cache-dir \
  -e "${source_dir}/shared" \
  -e "${source_dir}/provider"

# PYTHONPATH includes the repo root for shared modules used by the provider.
export PYTHONPATH="${source_dir}/provider/src:${source_dir}:${PYTHONPATH:-}"

# Bind to all container interfaces; Docker publishes the host-facing port.
exec python -m opamp_provider.server \
  --config-path /config/opamp-provider.json \
  --host 0.0.0.0 \
  --port 8080
