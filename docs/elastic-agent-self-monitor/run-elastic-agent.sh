#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
CONFIG_FILE="$SCRIPT_DIR/elastic-agent.yml"
OUT_DIR="$SCRIPT_DIR/out"
AGENT_LOG_DIR="$OUT_DIR/elastic-agent-logs"
TEMP_CONFIG="${TMPDIR:-/tmp}/opamp-elastic-agent.yml"

if [[ -z "${ELASTIC_AGENT_HOME:-}" ]]; then
    ELASTIC_AGENT_HOME="${HOME}/dev-tools/elastic-agent/elastic-agent-9.5.0-linux-x86_64"
fi

AGENT_EXE="$ELASTIC_AGENT_HOME/elastic-agent"

if [[ ! -x "$AGENT_EXE" ]]; then
    echo "Missing Elastic Agent executable: \"$AGENT_EXE\""
    echo "Set ELASTIC_AGENT_HOME to the Elastic Agent directory and rerun this script."
    exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Missing Elastic Agent config: \"$CONFIG_FILE\""
    exit 1
fi

mkdir -p "$OUT_DIR" "$AGENT_LOG_DIR"

sed \
    -e "s|D:/dev/opamp/tests/logstash/out/elastic-agent-logs|$AGENT_LOG_DIR|g" \
    -e "s|D:\\\\dev\\\\opamp\\\\tests\\\\logstash\\\\out\\\\elastic-agent-logs|$AGENT_LOG_DIR|g" \
    "$CONFIG_FILE" > "$TEMP_CONFIG"

echo "Using Elastic Agent: $AGENT_EXE"
echo "Using config: $CONFIG_FILE"
if [[ -n "${OPAMP_LOGSTASH_HOST:-}" ]]; then
    echo "Sending self-monitoring logs and metrics to Logstash at ${OPAMP_LOGSTASH_HOST}:5044"
else
    echo "Sending self-monitoring logs and metrics to Logstash at 127.0.0.1:5044"
fi
echo "Agent file logs: $AGENT_LOG_DIR"
echo
echo "Start Logstash first with:"
echo "  \"$SCRIPT_DIR/run-logstash.sh\""
echo

cd "$ELASTIC_AGENT_HOME"
exec "$AGENT_EXE" run -c "$TEMP_CONFIG"
