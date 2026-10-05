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

OPAMP_ROLE="${OPAMP_ROLE:-server}"
OPAMP_HOME="${OPAMP_HOME:-/opt/opamp}"
OPAMP_USER="${OPAMP_USER:-opamp}"
OPAMP_WHEEL_SOURCE_DIR="${OPAMP_WHEEL_SOURCE_DIR:-}"
OPAMP_WHEEL_SOURCE_URL="${OPAMP_WHEEL_SOURCE_URL:-}"
OPAMP_SOURCE_REPO="${OPAMP_SOURCE_REPO:-https://github.com/opamp-observe/opamp-core.git}"
OPAMP_SOURCE_REF="${OPAMP_SOURCE_REF:-main}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

COMPONENT_PATHS=(
  "provider"
  "consumer"
  "consumer-sim"
  "config-service"
  "client-config-generator-service"
  "catalog-service"
  "cli"
  "agent_broker"
  "mcp"
  "svr-credentials-mgr/plaintext-keyring"
  "svr-credentials-mgr"
  "dev-tools"
)

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this script as root or with sudo." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  docker.io \
  docker-compose-plugin \
  git \
  jq \
  nginx \
  openssl \
  python3 \
  python3-pip \
  python3-venv
rm -rf /var/lib/apt/lists/*

if ! id "$OPAMP_USER" >/dev/null 2>&1; then
  useradd --system --create-home --home-dir "$OPAMP_HOME" --shell /usr/sbin/nologin "$OPAMP_USER"
fi

install -d -o "$OPAMP_USER" -g "$OPAMP_USER" "$OPAMP_HOME"/{bin,config,logs,runtime,wheels,venvs,source}
install -d -m 0755 /etc/opamp /var/log/opamp

systemctl enable --now docker

# Download the wheel manifest and its referenced wheels from an HTTPS artifact location.
# The first parameter is the base URL containing the wheels directory.
stage_wheels_from_url() {
  local base_url="$1"
  local manifest="$OPAMP_HOME/wheels/wheels.txt"
  curl -fsSL "$base_url/wheels/wheels.txt" -o "$manifest"
  while IFS= read -r wheel_name; do
    [[ -z "$wheel_name" ]] && continue
    curl -fsSL "$base_url/wheels/$wheel_name" -o "$OPAMP_HOME/wheels/$wheel_name"
  done < "$manifest"
}

# Copy the wheel manifest and its referenced wheels from a locally extracted artifact pack.
# The first parameter is the artifact root containing the wheels directory.
stage_wheels_from_directory() {
  local artifact_root="$1"
  local source_manifest="$artifact_root/wheels/wheels.txt"
  if [[ ! -s "$source_manifest" ]]; then
    echo "Wheel manifest not found at $source_manifest" >&2
    exit 1
  fi
  while IFS= read -r wheel_name; do
    [[ -z "$wheel_name" ]] && continue
    cp "$artifact_root/wheels/$wheel_name" "$OPAMP_HOME/wheels/$wheel_name"
  done < "$source_manifest"
  cp "$source_manifest" "$OPAMP_HOME/wheels/wheels.txt"
}

# Build all deployable component wheels from a Git checkout when no artifact pack is supplied.
stage_wheels_from_source() {
  local checkout="$OPAMP_HOME/source/current"
  rm -rf "$checkout"
  git clone "$OPAMP_SOURCE_REPO" "$checkout"
  git -C "$checkout" checkout "$OPAMP_SOURCE_REF"
  "$PYTHON_BIN" -m pip install --upgrade build
  for component_path in "${COMPONENT_PATHS[@]}"; do
    "$PYTHON_BIN" -m build --wheel --outdir "$OPAMP_HOME/wheels" "$checkout/$component_path"
  done
  (cd "$OPAMP_HOME/wheels" && ls -1 *.whl > wheels.txt)
}

rm -rf "$OPAMP_HOME/wheels"
install -d -o "$OPAMP_USER" -g "$OPAMP_USER" "$OPAMP_HOME/wheels"
if [[ -n "$OPAMP_WHEEL_SOURCE_DIR" ]]; then
  stage_wheels_from_directory "$OPAMP_WHEEL_SOURCE_DIR"
elif [[ -n "$OPAMP_WHEEL_SOURCE_URL" ]]; then
  stage_wheels_from_url "$OPAMP_WHEEL_SOURCE_URL"
else
  stage_wheels_from_source
fi

# Create an isolated virtual environment for one deployed OpAMP role.
# The first parameter is the environment name under the OpAMP home directory.
create_venv() {
  local name="$1"
  "$PYTHON_BIN" -m venv "$OPAMP_HOME/venvs/$name"
  "$OPAMP_HOME/venvs/$name/bin/python" -m pip install --upgrade pip setuptools wheel
}

# Install the newest wheel matching a component pattern into a selected environment.
# Parameters are the virtual environment name followed by the wheel filename pattern.
install_matching_wheel() {
  local venv="$1"
  local pattern="$2"
  local match
  match="$(find "$OPAMP_HOME/wheels" -maxdepth 1 -name "$pattern" | sort | tail -n 1)"
  if [[ -z "$match" ]]; then
    echo "No wheel matched $pattern" >&2
    exit 1
  fi
  "$OPAMP_HOME/venvs/$venv/bin/python" -m pip install --find-links "$OPAMP_HOME/wheels" "$match"
}

rm -rf "$OPAMP_HOME/venvs/server" "$OPAMP_HOME/venvs/consumer"
case "$OPAMP_ROLE" in
  server)
    create_venv server
    install_matching_wheel server "opamp_server-*.whl"
    install_matching_wheel server "config_service-*.whl"
    install_matching_wheel server "client_config_generator_service-*.whl"
    install_matching_wheel server "catalog_service-*.whl"
    install_matching_wheel server "svr_credentials_manager_service-*.whl"
    install_matching_wheel server "opamp_broker-*.whl"
    install_matching_wheel server "opamp_cli-*.whl"
    "$OPAMP_HOME/venvs/server/bin/python" -m pip check
    ;;
  consumer)
    create_venv consumer
    install_matching_wheel consumer "opamp_consumer-*.whl"
    install_matching_wheel consumer "opamp_consumer_sim-*.whl"
    install_matching_wheel consumer "opamp_cli-*.whl"
    "$OPAMP_HOME/venvs/consumer/bin/python" -m pip check
    ;;
  all)
    OPAMP_ROLE=server "$0"
    OPAMP_ROLE=consumer "$0"
    ;;
  *)
    echo "Unsupported OPAMP_ROLE=$OPAMP_ROLE. Use server, consumer, or all." >&2
    exit 1
    ;;
esac

chown -R "$OPAMP_USER:$OPAMP_USER" "$OPAMP_HOME" /var/log/opamp /etc/opamp
echo "Installed OpAMP role $OPAMP_ROLE from wheels in $OPAMP_HOME/wheels"
