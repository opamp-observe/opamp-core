#!/usr/bin/env bash
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
#
# Copyright 2026 mp3monster.org

set -euo pipefail

config_path="${TEST_CONTAINER_CONFIG:-/config/test-container.env}"
exit_code_path="/evidence/consumer-exit-code.txt"
finished_path="/evidence/consumer-finished"

export TEST_CONTAINER_CONFIG="${config_path}"
export PYTHONPATH="/host-assets:${PYTHONPATH:-}"

if [[ ! -f "${config_path}" ]]; then
  echo "Consumer scenario config not found: ${config_path}" >&2
  exit 2
fi

rm -f "${exit_code_path}" "${finished_path}"

set +e
python3 /opt/opamp-test/bootstrap.py
consumer_exit_code=$?
set -e

printf '%s\n' "${consumer_exit_code}" > "${exit_code_path}"
touch "${finished_path}"

# Keep the container namespace alive so the verifier can prove that both the
# supervisor and its managed process have disappeared after the UI command.
while true; do
  sleep 1
done
