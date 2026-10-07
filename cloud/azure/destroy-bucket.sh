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
DELETE_ALL_RETAINED_STORAGE=false
if [[ "$STORAGE_ACCOUNT" == "--all" ]]; then
  DELETE_ALL_RETAINED_STORAGE=true
  STORAGE_ACCOUNT=""
fi

# Resolve the owning resource group and permanently delete one retained account.
delete_retained_storage_account() {
  local storage_account="$1"
  local storage_resource_group
  storage_resource_group="$(az storage account show \
    --name "$storage_account" \
    --query resourceGroup \
    --output tsv)"
  az storage account delete \
    --name "$storage_account" \
    --resource-group "$storage_resource_group" \
    --yes
  echo "Deleted retained Azure storage account $storage_account and all of its containers."
}

if [[ "$DELETE_ALL_RETAINED_STORAGE" == "true" ]]; then
  mapfile -t retained_storage_accounts < <(
    az storage account list \
      --query "[?tags.Project=='opamp' && tags.Purpose=='regression-retention'].[name,resourceGroup]" \
      --output tsv | sed '/^$/d'
  )
  if [[ "${#retained_storage_accounts[@]}" -eq 0 ]]; then
    echo "No tagged OpAMP regression retention storage accounts were found."
    exit 0
  fi
  for retained_storage_account_record in "${retained_storage_accounts[@]}"; do
    storage_account="$(printf "%s" "$retained_storage_account_record" | awk '{print $1}')"
    storage_resource_group="$(printf "%s" "$retained_storage_account_record" | awk '{print $2}')"
    az storage account delete \
      --name "$storage_account" \
      --resource-group "$storage_resource_group" \
      --yes
    echo "Deleted retained Azure storage account $storage_account and all of its containers."
  done
  exit 0
fi

# This command permanently removes the account and every artifact and result
# container within it; ordinary VM teardown never calls it.
if [[ -z "$STORAGE_ACCOUNT" ]]; then
  echo "Provide the retained storage account name as STORAGE_ACCOUNT, BUCKET_NAME, or the first argument." >&2
  exit 1
fi

delete_retained_storage_account "$STORAGE_ACCOUNT"
