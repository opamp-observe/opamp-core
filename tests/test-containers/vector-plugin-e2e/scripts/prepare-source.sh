#!/usr/bin/env bash
# Licensed under the Apache License, Version 2.0.
# Copyright 2026 mp3monster.org

set -euo pipefail

if [[ "${OPAMP_USE_LOCAL_SOURCE:-true}" == "true" ]]; then
  printf '%s\n' "${OPAMP_LOCAL_SOURCE}"
  exit 0
else
  rm -rf "${OPAMP_SOURCE_DIR}"
  git clone "${OPAMP_SOURCE_REPO}" "${OPAMP_SOURCE_DIR}"
  git -C "${OPAMP_SOURCE_DIR}" checkout "${OPAMP_SOURCE_REF}"
fi

printf '%s\n' "${OPAMP_SOURCE_DIR}"
