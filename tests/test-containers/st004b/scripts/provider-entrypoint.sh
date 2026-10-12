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

# Install and start the provider for the selected ST-004B profile.
set -euo pipefail

profile="${ST004B_PROFILE:-no-auth}"
staged_root="$(st004b-prepare-source)"
config_path="/scenario-config/provider/${profile}.json"

if [[ ! -f "${config_path}" ]]; then
  printf 'unknown ST-004B provider profile: %s\n' "${profile}" >&2
  exit 2
fi

if [[ "${profile}" == "tls" ]]; then
  certificate_dir="/evidence/tls/certs"
  certificate_file="${certificate_dir}/provider-cert.pem"
  private_key_file="${certificate_dir}/provider-key.pem"
  mkdir -p "${certificate_dir}"
  openssl req -x509 -newkey rsa:2048 -sha256 -nodes \
    -keyout "${private_key_file}" \
    -out "${certificate_file}" \
    -days 2 \
    -subj "/CN=provider" \
    -addext "subjectAltName=DNS:provider,DNS:localhost,IP:127.0.0.1" \
    -addext "basicConstraints=critical,CA:TRUE" \
    >/dev/null 2>&1
  chmod 600 "${private_key_file}"
fi

python -m pip install --no-cache-dir -e "${staged_root}/provider"
export PYTHONPATH="${staged_root}/provider/src:${staged_root}:${PYTHONPATH:-}"

exec python -m opamp_provider.server \
  --config-path "${config_path}" \
  --host 0.0.0.0 \
  --port 8080 \
  --log-level DEBUG
