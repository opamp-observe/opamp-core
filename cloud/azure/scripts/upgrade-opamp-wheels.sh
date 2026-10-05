#!/usr/bin/env bash
# Copyright 2026 mp3monster.org
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

OPAMP_ROLE="${OPAMP_ROLE:-all}"
OPAMP_HOME="${OPAMP_HOME:-/opt/opamp}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this script as root or with sudo." >&2
  exit 1
fi

# Stop services for the selected server or consumer role before replacing wheels.
# The first parameter is the role name.
stop_role() {
  local role="$1"
  case "$role" in
    server)
      systemctl stop opamp-provider config-service catalog-service svr-credentials-manager-service opamp-broker || true
      ;;
    consumer)
      systemctl stop opamp-consumer-simulator || true
      ;;
  esac
}

# Restart the role by invoking its platform-neutral startup script.
# The first parameter is the role name.
start_role() {
  local role="$1"
  case "$role" in
    server)
      bash "$SCRIPT_DIR/start-opamp-server.sh"
      ;;
    consumer)
      bash "$SCRIPT_DIR/start-opamp-consumer.sh"
      ;;
  esac
}

case "$OPAMP_ROLE" in
  server|consumer)
    stop_role "$OPAMP_ROLE"
    OPAMP_ROLE="$OPAMP_ROLE" bash "$SCRIPT_DIR/install-opamp.sh"
    start_role "$OPAMP_ROLE"
    ;;
  all)
    for role in server consumer; do
      stop_role "$role"
      OPAMP_ROLE="$role" bash "$SCRIPT_DIR/install-opamp.sh"
      start_role "$role"
    done
    ;;
  *)
    echo "Unsupported OPAMP_ROLE=$OPAMP_ROLE. Use server, consumer, or all." >&2
    exit 1
    ;;
esac

echo "Upgrade completed for OPAMP_ROLE=$OPAMP_ROLE"
