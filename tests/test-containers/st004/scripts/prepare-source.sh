#!/usr/bin/env bash
# Licensed under the Apache License, Version 2.0.
# Copyright 2026 mp3monster.org
#
# Stage source code inside a container and print the staged path on stdout.
set -euo pipefail

destination="${OPAMP_SOURCE_DIR:-/opt/opamp/source}"
local_source="${OPAMP_LOCAL_SOURCE:-/workspace/source}"
source_repo="${OPAMP_SOURCE_REPO:-https://github.com/mp3monster/fluent-opamp.git}"
source_ref="${OPAMP_SOURCE_REF:-main}"
use_local="${OPAMP_USE_LOCAL_SOURCE:-false}"

mkdir -p "${destination}"

if [[ "${use_local}" == "true" && -d "${local_source}" ]]; then
  if [[ -d "${local_source}/.git" ]]; then
    echo "[st004] retrieving source from mounted checkout ${local_source}" >&2
    find "${destination}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    (
      cd "${local_source}"
      git config --global --add safe.directory "${local_source}"
      git ls-files -z -co --exclude-standard \
        | while IFS= read -r -d '' path; do
            [[ -e "${path}" ]] && printf '%s\0' "${path}"
          done \
        | tar --null -T - -cf - \
        | tar -C "${destination}" -xf -
    )
    echo "${destination}"
    exit 0
  fi

  if [[ -d "${local_source}/provider" && -d "${local_source}/consumer" ]]; then
    echo "[st004] copying mounted source tree ${local_source}" >&2
    find "${destination}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    tar -C "${local_source}" -cf - . | tar -C "${destination}" -xf -
    echo "${destination}"
    exit 0
  fi
fi

if [[ ! -d "${destination}/.git" ]]; then
  echo "[st004] cloning ${source_repo} into ${destination}" >&2
  find "${destination}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  if ! git clone --depth 1 --branch "${source_ref}" "${source_repo}" "${destination}"; then
    find "${destination}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    git clone "${source_repo}" "${destination}"
    git -C "${destination}" checkout "${source_ref}"
  fi
else
  echo "[st004] refreshing existing checkout ${destination}" >&2
  git -C "${destination}" fetch --all --tags
  git -C "${destination}" checkout "${source_ref}"
fi

echo "${destination}"

