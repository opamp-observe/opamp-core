#!/usr/bin/env bash
# Copyright 2026 opamp.info
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

if [[ "${OPAMP_USE_LOCAL_SOURCE:-true}" == "true" ]]; then
  rm -rf "${OPAMP_SOURCE_DIR}"
  mkdir -p "${OPAMP_SOURCE_DIR}"
  (
    cd "${OPAMP_LOCAL_SOURCE}"
    git config --global --add safe.directory "${OPAMP_LOCAL_SOURCE}"
    git ls-files -z -co --exclude-standard \
      | while IFS= read -r -d '' source_path; do
          [[ -e "${source_path}" ]] && printf '%s\0' "${source_path}"
        done \
      | tar --null -T - -cf - \
      | tar -C "${OPAMP_SOURCE_DIR}" -xf -
  )
  printf '%s\n' "${OPAMP_SOURCE_DIR}"
  exit 0
else
  rm -rf "${OPAMP_SOURCE_DIR}"
  git clone "${OPAMP_SOURCE_REPO}" "${OPAMP_SOURCE_DIR}"
  git -C "${OPAMP_SOURCE_DIR}" checkout "${OPAMP_SOURCE_REF}"
fi

printf '%s\n' "${OPAMP_SOURCE_DIR}"
