#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${PLAYWRIGHT_DOCKER_IMAGE:-mcr.microsoft.com/playwright:v1.64.0-noble}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI not found in PATH. Install Docker or enable Docker Desktop WSL integration first." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  cat >&2 <<'MSG'
Docker daemon is not reachable.

If you are running in WSL:
1. Start Docker Desktop.
2. Enable WSL integration for this distro in Docker Desktop settings.
3. Re-open the shell and retry.
MSG
  exit 1
fi

PLAYWRIGHT_ARGS=""
if [ "$#" -gt 0 ]; then
  for arg in "$@"; do
    printf -v escaped '%q' "$arg"
    PLAYWRIGHT_ARGS+=" ${escaped}"
  done
fi

echo "Running Playwright UI checks in container image: ${IMAGE}"
docker run --rm -t \
  --ipc=host \
  -u "$(id -u):$(id -g)" \
  -e CI=1 \
  -e HOME=/tmp \
  -v "${ROOT_DIR}":/work \
  -w /work/config-service \
  "${IMAGE}" \
  bash -lc "set -euo pipefail; python3 -m pip install --upgrade pip; pip3 install -e .; npm ci; node ./node_modules/playwright/cli.js test${PLAYWRIGHT_ARGS}"
