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
# Copyright 2026 opamp.info

set -euo pipefail

mounted_source_dir="/workspace/source"
source_dir="$(mktemp -d /tmp/opamp-agent-shutdown-provider.XXXXXX)"

(
  cd "${mounted_source_dir}"
  git config --global --add safe.directory "${mounted_source_dir}"
  git ls-files -z -co --exclude-standard \
    | while IFS= read -r -d '' source_path; do
        [[ -e "${source_path}" ]] && printf '%s\0' "${source_path}"
      done \
    | tar --null -T - -cf - \
    | tar -C "${source_dir}" -xf -
)

python3 -m pip install --no-cache-dir \
  -e "${source_dir}/shared" \
  -e "${source_dir}/provider"
export PYTHONPATH="${source_dir}/provider/src:${source_dir}:${PYTHONPATH:-}"

exec python3 -m opamp_provider.server \
  --config-path /config/opamp-provider.json \
  --host 0.0.0.0 \
  --port 8080
