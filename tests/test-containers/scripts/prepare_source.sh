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

# Stage tracked and non-ignored source into writable container-local storage.
set -euo pipefail

source_root="${OPAMP_REPO:-/workspace/opamp}"
staging_parent="${OPAMP_STAGING_PARENT:-/tmp}"

if [[ -z "${staging_parent}" || "${staging_parent}" == "/" ]]; then
  printf 'unsafe staging parent: %s\n' "${staging_parent}" >&2
  exit 2
fi
mkdir -p "${staging_parent}"
staged_root="$(mktemp -d "${staging_parent%/}/opamp-source.XXXXXX")"

if [[ -d "${source_root}/.git" ]]; then
  git config --global --add safe.directory "${source_root}"
  (
    cd "${source_root}"
    git ls-files -z -co --exclude-standard \
      | while IFS= read -r -d '' source_path; do
          [[ -e "${source_path}" ]] && printf '%s\0' "${source_path}"
        done \
      | tar --null -T - -cf - \
      | tar -C "${staged_root}" -xf -
  )
else
  tar -C "${source_root}" -cf - . | tar -C "${staged_root}" -xf -
fi

printf '%s\n' "${staged_root}"
