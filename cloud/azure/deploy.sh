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

# Orchestrate packaging, retained blob storage, ARM deployment, and output
# capture from the operator workstation.
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
RESOURCE_GROUP="${RESOURCE_GROUP:-opamp-regression-rg}"
RETENTION_RESOURCE_GROUP="${RETENTION_RESOURCE_GROUP:-}"
LOCATION="${LOCATION:-uksouth}"
PARAMETERS_FILE="${PARAMETERS_FILE:-$REPO_ROOT/cloud/azure/parameters.example.json}"
TEMPLATE_FILE="${TEMPLATE_FILE:-$REPO_ROOT/cloud/azure/mainTemplate.json}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-}"
ARTIFACT_CONTAINER="${ARTIFACT_CONTAINER:-opamp-cloud}"
RESULTS_CONTAINER="${RESULTS_CONTAINER:-opamp-regression-results}"
ARTIFACT_DIRECTORY="${ARTIFACT_DIRECTORY:-$REPO_ROOT/dist/cloud-azure-artifacts}"
STORAGE_ACCOUNT_FILE="${STORAGE_ACCOUNT_FILE:-$REPO_ROOT/dist/azure-retention-storage-account.txt}"
SSH_PRIVATE_KEY_FILE="${SSH_PRIVATE_KEY_FILE:-}"
SKIP_PACKAGE="${SKIP_PACKAGE:-false}"
DEPLOYMENT_TIMESTAMP="$(date -u +%Y%m%d%H%M%S)"

# Phase 1: validate local tools and the operator-owned parameter file.
for required_command in az python; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    echo "$required_command is required." >&2
    exit 1
  fi
done
if [[ ! -f "$PARAMETERS_FILE" ]]; then
  echo "Parameter file not found: $PARAMETERS_FILE" >&2
  exit 1
fi

# Phase 2: build wheels and shared bootstrap scripts unless reuse was explicit.
if [[ "$SKIP_PACKAGE" != "true" ]]; then
  REPO_ROOT="$REPO_ROOT" OUTPUT_DIR="$ARTIFACT_DIRECTORY" \
    bash "$REPO_ROOT/cloud/azure/scripts/package-cloud-artifacts.sh"
fi
if [[ ! -d "$ARTIFACT_DIRECTORY" ]]; then
  echo "Artifact directory not found: $ARTIFACT_DIRECTORY" >&2
  exit 1
fi

# Phase 3: retained storage lives outside the VM resource group so normal
# teardown preserves artifacts and regression results.
if [[ -z "$STORAGE_ACCOUNT" ]]; then
  subscription_id="$(az account show --query id --output tsv)"
  subscription_suffix="$(printf "%s" "$subscription_id" | tr -d '-' | cut -c1-5)"
  STORAGE_ACCOUNT="opamp${DEPLOYMENT_TIMESTAMP}${subscription_suffix,,}"
  RETENTION_RESOURCE_GROUP="${RETENTION_RESOURCE_GROUP:-${RESOURCE_GROUP}-retained}"
  if [[ "${RETENTION_RESOURCE_GROUP,,}" == "${RESOURCE_GROUP,,}" ]]; then
    echo "RETENTION_RESOURCE_GROUP must differ from RESOURCE_GROUP." >&2
    exit 1
  fi
  az group create --name "$RETENTION_RESOURCE_GROUP" --location "$LOCATION" >/dev/null
  az storage account create \
    --resource-group "$RETENTION_RESOURCE_GROUP" \
    --name "$STORAGE_ACCOUNT" \
    --location "$LOCATION" \
    --sku Standard_LRS \
    --kind StorageV2 \
    --min-tls-version TLS1_2 \
    --https-only true \
    --allow-blob-public-access true \
    --tags Project=opamp Purpose=regression-retention CreatedAt="$DEPLOYMENT_TIMESTAMP" >/dev/null
  echo "Created retained Azure storage account $STORAGE_ACCOUNT"
else
  storage_resource_group="$(az storage account show \
    --name "$STORAGE_ACCOUNT" \
    --query resourceGroup \
    --output tsv)"
  if [[ "${storage_resource_group,,}" == "${RESOURCE_GROUP,,}" ]]; then
    echo "Storage account $STORAGE_ACCOUNT is inside deployment resource group $RESOURCE_GROUP." >&2
    exit 1
  fi
  echo "Using retained Azure storage account $STORAGE_ACCOUNT"
fi

mkdir -p "$(dirname "$STORAGE_ACCOUNT_FILE")"
printf "%s\n" "$STORAGE_ACCOUNT" > "$STORAGE_ACCOUNT_FILE"

# VM extensions need anonymous read access to bootstrap artifacts. Regression
# outputs use a separate private container.
az storage container create \
  --account-name "$STORAGE_ACCOUNT" \
  --name "$ARTIFACT_CONTAINER" \
  --public-access blob \
  --auth-mode key >/dev/null
az storage container create \
  --account-name "$STORAGE_ACCOUNT" \
  --name "$RESULTS_CONTAINER" \
  --public-access off \
  --auth-mode key >/dev/null
az storage blob upload-batch \
  --account-name "$STORAGE_ACCOUNT" \
  --destination "$ARTIFACT_CONTAINER" \
  --source "$ARTIFACT_DIRECTORY" \
  --auth-mode key \
  --overwrite >/dev/null

artifact_base_url="https://${STORAGE_ACCOUNT}.blob.core.windows.net/${ARTIFACT_CONTAINER}"
results_directory="$REPO_ROOT/dist/azure-regression-results/$DEPLOYMENT_TIMESTAMP"
connection_guide_file="$results_directory/connection_details.md"
deployment_outputs_file="$results_directory/deployment-outputs.json"
mkdir -p "$results_directory"

# Phase 4: ARM creates or updates infrastructure and runs both VM extensions.
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" >/dev/null
az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "$TEMPLATE_FILE" \
  --parameters "@$PARAMETERS_FILE" \
  artifactBaseUrl="$artifact_base_url" \
  wheelArtifactBaseUrl="$artifact_base_url" \
  --query properties.outputs \
  --output json > "$deployment_outputs_file"
# Phase 5: produce the common operator guide and retain both output artifacts.
python "$REPO_ROOT/scripts/generate_cloud_connection_guide.py" \
  --provider azure \
  --outputs-file "$deployment_outputs_file" \
  --output-file "$connection_guide_file" \
  --ssh-private-key "$SSH_PRIVATE_KEY_FILE"

az storage blob upload \
  --account-name "$STORAGE_ACCOUNT" \
  --container-name "$RESULTS_CONTAINER" \
  --name "$DEPLOYMENT_TIMESTAMP/deployment-outputs.json" \
  --file "$deployment_outputs_file" \
  --auth-mode key \
  --overwrite >/dev/null
az storage blob upload \
  --account-name "$STORAGE_ACCOUNT" \
  --container-name "$RESULTS_CONTAINER" \
  --name "$DEPLOYMENT_TIMESTAMP/connection_details.md" \
  --file "$connection_guide_file" \
  --auth-mode key \
  --overwrite >/dev/null

cat "$deployment_outputs_file"
echo "Retained storage account: $STORAGE_ACCOUNT"
echo "Retained deployment results: $RESULTS_CONTAINER/$DEPLOYMENT_TIMESTAMP/"
echo "Connection guide: $connection_guide_file"
