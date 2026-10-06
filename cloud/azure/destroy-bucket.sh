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

STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-${BUCKET_NAME:-${1:-}}}"

# This command permanently removes the account and every artifact and result
# container within it; ordinary VM teardown never calls it.
if [[ -z "$STORAGE_ACCOUNT" ]]; then
  echo "Provide the retained storage account name as STORAGE_ACCOUNT, BUCKET_NAME, or the first argument." >&2
  exit 1
fi

storage_resource_group="$(az storage account show \
  --name "$STORAGE_ACCOUNT" \
  --query resourceGroup \
  --output tsv)"
az storage account delete \
  --name "$STORAGE_ACCOUNT" \
  --resource-group "$storage_resource_group" \
  --yes
echo "Deleted retained Azure storage account $STORAGE_ACCOUNT and all of its containers."
