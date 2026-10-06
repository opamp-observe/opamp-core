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

# Build one Linux-ready archive containing all component wheels and shared VM
# bootstrap scripts. This script runs locally, not on an EC2 instance.
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/dist/cloud-aws-artifacts}"
ARCHIVE_PATH="${ARCHIVE_PATH:-$REPO_ROOT/dist/opamp-cloud-artifacts.tar.gz}"
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

# Recursive cleanup is allowed only under the repository's generated dist tree.
case "$OUTPUT_DIR" in
  "$REPO_ROOT"/dist/*) ;;
  *)
    echo "OUTPUT_DIR must be inside $REPO_ROOT/dist" >&2
    exit 1
    ;;
esac

rm -rf "$OUTPUT_DIR"
rm -f "$ARCHIVE_PATH"
mkdir -p "$WHEEL_DIR" "$OUTPUT_DIR/scripts"

# Build all packages once so server and consumer instances can install from the
# same immutable archive.
python -m pip install --upgrade build
for component_path in "${COMPONENT_PATHS[@]}"; do
  python -m build --wheel --outdir "$WHEEL_DIR" "$REPO_ROOT/$component_path"
done

# These scripts are provider-neutral despite their historical Azure location.
cp "$REPO_ROOT/cloud/azure/scripts/install-opamp.sh" "$OUTPUT_DIR/scripts/"
cp "$REPO_ROOT/cloud/azure/scripts/start-opamp-consumer.sh" "$OUTPUT_DIR/scripts/"
cp "$REPO_ROOT/cloud/azure/scripts/start-opamp-server.sh" "$OUTPUT_DIR/scripts/"
cp "$REPO_ROOT/cloud/azure/scripts/upgrade-opamp-wheels.sh" "$OUTPUT_DIR/scripts/"
find "$OUTPUT_DIR/scripts" -type f -name "*.sh" -exec chmod +x {} \;
# The VM installer reads this manifest instead of discovering arbitrary files.
(cd "$WHEEL_DIR" && printf "%s\n" ./*.whl | sed "s#^./##" | sort > wheels.txt)

cat > "$OUTPUT_DIR/README.txt" <<EOF
This archive contains the OpAMP wheels and platform-neutral VM bootstrap scripts
used by cloud/aws/template.yaml. Upload the generated tar.gz file to the private
S3 bucket and object key supplied to cloud/aws/deploy.sh or deploy.ps1.
EOF

# AWS user data downloads one object, so archive the complete staging directory.
tar -czf "$ARCHIVE_PATH" -C "$OUTPUT_DIR" .
echo "Packaged AWS artifacts in $ARCHIVE_PATH"
