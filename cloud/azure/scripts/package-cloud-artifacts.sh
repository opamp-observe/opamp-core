#!/usr/bin/env bash
set -euo pipefail

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

rm -rf "$OUTPUT_DIR"
mkdir -p "$WHEEL_DIR" "$OUTPUT_DIR/scripts"

python -m pip install --upgrade build
for component_path in "${COMPONENT_PATHS[@]}"; do
  python -m build --wheel --outdir "$WHEEL_DIR" "$REPO_ROOT/$component_path"
done

cp "$REPO_ROOT"/cloud/azure/scripts/*.sh "$OUTPUT_DIR/scripts/"
find "$OUTPUT_DIR/scripts" -type f -name "*.sh" -exec chmod +x {} \;
(cd "$WHEEL_DIR" && ls -1 *.whl > wheels.txt)

cat > "$OUTPUT_DIR/README.txt" <<EOF
Upload the contents of this folder to an HTTPS location, for example an Azure
Storage blob container. Use that base URL for both artifactBaseUrl and
wheelArtifactBaseUrl in cloud/azure/parameters.example.json.
EOF

echo "Packaged Azure artifacts in $OUTPUT_DIR"
