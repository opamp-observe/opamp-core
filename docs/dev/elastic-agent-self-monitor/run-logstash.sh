#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
CONFIG_FILE="$SCRIPT_DIR/logstash.conf"
OUT_DIR="$SCRIPT_DIR/out"
TEMP_CONFIG="${TMPDIR:-/tmp}/opamp-logstash.conf"
CONTAINER_NAME="opamp-logstash"
CONTAINER_CONFIG="/usr/share/logstash/pipeline/logstash.conf"
CONTAINER_OUT="/usr/share/logstash/out"
CONTAINER_RUNTIME="docker"
RUNTIME_REPLACE_ARG=()

if [[ $# -gt 1 ]]; then
    echo "Usage: $(basename "$0") [docker|podman]"
    exit 1
fi

if [[ $# -eq 1 ]]; then
    case "${1,,}" in
        podman)
            CONTAINER_RUNTIME="podman"
            RUNTIME_REPLACE_ARG=(--replace)
            ;;
        docker)
            CONTAINER_RUNTIME="docker"
            ;;
        *)
            echo "Usage: $(basename "$0") [docker|podman]"
            exit 1
            ;;
    esac
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Missing Logstash config: \"$CONFIG_FILE\""
    exit 1
fi

if ! command -v "$CONTAINER_RUNTIME" >/dev/null 2>&1; then
    echo "Container runtime not found: $CONTAINER_RUNTIME"
    exit 1
fi

mkdir -p "$OUT_DIR"

if [[ -z "${LOGSTASH_IMAGE:-}" ]]; then
    LOGSTASH_IMAGE="docker.elastic.co/logstash/logstash:9.5.1"
fi

sed \
    -e "s|D:/dev/opamp/tests/logstash/out|$CONTAINER_OUT|g" \
    -e "s|D:\\\\dev\\\\opamp\\\\tests\\\\logstash\\\\out|$CONTAINER_OUT|g" \
    "$CONFIG_FILE" > "$TEMP_CONFIG"

echo "Using image: $LOGSTASH_IMAGE"
echo "Using runtime: $CONTAINER_RUNTIME"
echo "Using config: $CONFIG_FILE"
echo "Writing output under: $OUT_DIR"
echo

"$CONTAINER_RUNTIME" run --rm \
    "${RUNTIME_REPLACE_ARG[@]}" \
    --name "$CONTAINER_NAME" \
    -p 127.0.0.1:5044:5044 \
    -v "$TEMP_CONFIG:$CONTAINER_CONFIG:ro" \
    -v "$OUT_DIR:$CONTAINER_OUT" \
    "$LOGSTASH_IMAGE" \
    logstash -f "$CONTAINER_CONFIG" --path.logs "$CONTAINER_OUT/logs"
