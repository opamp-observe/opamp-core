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

# Build the directory uploaded to Azure Blob Storage. This script runs on the
# operator workstation; VM extensions later consume its contents over HTTPS.
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/dist/cloud-azure-artifacts}"
WHEEL_DIR="$OUTPUT_DIR/wheels"

COMPONENT_PATHS=(
  "provider"
  "consumer"
  "consumer-sim"
  "config-service"
  "client-config-generator-service"
  "catalog-service"
  "cli"
  "agent_broker"
  "mcp"
  "svr-credentials-mgr/plaintext-keyring"
  "svr-credentials-mgr"
  "dev-tools"
)

# Constrain recursive cleanup to generated content under the repository's dist tree.
case "$OUTPUT_DIR" in
  "$REPO_ROOT"/dist/*) ;;
  *)
    echo "OUTPUT_DIR must be inside $REPO_ROOT/dist" >&2
    exit 1
    ;;
esac

rm -rf "$OUTPUT_DIR"
mkdir -p "$WHEEL_DIR" "$OUTPUT_DIR/scripts"

# Build all packages once so both VM roles use the same component versions.
python -m pip install --upgrade build
for component_path in "${COMPONENT_PATHS[@]}"; do
  python -m build --wheel --outdir "$WHEEL_DIR" "$REPO_ROOT/$component_path"
done

# Runtime scripts are shared by AWS and Azure and execute only after VM creation.
cp "$REPO_ROOT"/cloud/azure/scripts/*.sh "$OUTPUT_DIR/scripts/"
find "$OUTPUT_DIR/scripts" -type f -name "*.sh" -exec chmod +x {} \;
# The installer uses the manifest as the authoritative wheel list.
(cd "$WHEEL_DIR" && ls -1 *.whl > wheels.txt)

cat > "$OUTPUT_DIR/README.txt" <<EOF
Upload the contents of this folder to an HTTPS location, for example an Azure
Storage blob container. Use that base URL for both artifactBaseUrl and
wheelArtifactBaseUrl in cloud/azure/parameters.example.json.
EOF

echo "Packaged Azure artifacts in $OUTPUT_DIR"
