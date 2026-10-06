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

# Configure and start the consumer role after install-opamp.sh has populated its
# virtual environment. This script is provider-neutral; platform values affect labels.
OPAMP_HOME="${OPAMP_HOME:-/opt/opamp}"
OPAMP_USER="${OPAMP_USER:-opamp}"
OPAMP_SERVER_URL="${OPAMP_SERVER_URL:-https://10.42.0.10}"
OPAMP_SERVER_HOST="${OPAMP_SERVER_HOST:-opamp-server}"
OPAMP_DEPLOYMENT_PLATFORM="${OPAMP_DEPLOYMENT_PLATFORM:-Azure}"
OPAMP_DEPLOYMENT_SLUG="${OPAMP_DEPLOYMENT_PLATFORM,,}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this script as root or with sudo." >&2
  exit 1
fi

install -d -m 0755 /etc/opamp /var/log/opamp "$OPAMP_HOME/config" "$OPAMP_HOME/runtime"
chown -R "$OPAMP_USER:$OPAMP_USER" "$OPAMP_HOME" /var/log/opamp /etc/opamp

# Phase 1: run a local collector for simulator self-telemetry. Host networking
# lets the Python service use the same loopback OTLP endpoint on either cloud.
cat > /etc/opamp/otel-collector.yaml <<'EOF'
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
processors:
  batch:
exporters:
  debug:
    verbosity: basic
  file:
    path: /var/log/opamp/otel-collector.json
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug, file]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug, file]
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug, file]
EOF

docker rm -f opamp-otel-collector >/dev/null 2>&1 || true
docker run -d --name opamp-otel-collector --restart unless-stopped --network host \
  -v /etc/opamp/otel-collector.yaml:/etc/otelcol-contrib/config.yaml:ro \
  -v /var/log/opamp:/var/log/opamp \
  otel/opentelemetry-collector-contrib:0.104.0

# Phase 2: write the simulated agent and OpAMP client configuration. Server TLS
# verification is disabled because regression environments use a self-signed certificate.
cat > "$OPAMP_HOME/config/simulator-agent.yaml" <<'EOF'
service:
  pipelines:
    logs:
      receivers: [self]
      processors: []
      exporters: [self]
EOF

cat > "$OPAMP_HOME/config/simulator-responses.json" <<EOF
{
  "remote_config": {
    "status": "applied",
    "last_remote_config_hash": "$OPAMP_DEPLOYMENT_SLUG-bootstrap"
  }
}
EOF

cat > /etc/opamp/opamp-consumer-simulator.json <<EOF
{
  "consumer": {
    "server_url": "$OPAMP_SERVER_URL",
    "server_port": 443,
    "client_status_port": 2020,
    "chat_ops_port": 8888,
    "transport": "http",
    "tls": {
      "verify_server": false,
      "server_hostname": "$OPAMP_SERVER_HOST"
    },
    "server-authorization": "none",
    "log_agent_api_responses": true,
    "agent_config_path": "$OPAMP_HOME/config/simulator-agent.yaml",
    "agent_additional_params": [
      "{\"service_instance_uid\":\"$OPAMP_DEPLOYMENT_SLUG-consumer-simulator\",\"client_version\":\"$OPAMP_DEPLOYMENT_PLATFORM wheel deployment\",\"config_version\":\"$OPAMP_DEPLOYMENT_SLUG-bootstrap\"}"
    ],
    "heartbeat_frequency": 10,
    "service_type": "simulator",
    "simulator_responses_path": "$OPAMP_HOME/config/simulator-responses.json",
    "full_update_controller": {
      "fullResendAfter": 1
    },
    "full_update_controller_type": "SentCount",
    "allow_custom_capabilities": true,
    "log_level": "debug",
    "service_name": "$OPAMP_DEPLOYMENT_PLATFORM Consumer Simulator",
    "service_namespace": "$OPAMP_DEPLOYMENT_PLATFORM"
  }
}
EOF

# Phase 3: systemd owns long-running process supervision after bootstrap exits.
cat > /etc/systemd/system/opamp-consumer-simulator.service <<EOF
[Unit]
Description=OpAMP Consumer Simulator
After=network-online.target
Wants=network-online.target

[Service]
User=$OPAMP_USER
Group=$OPAMP_USER
WorkingDirectory=$OPAMP_HOME
Environment=OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4317
Environment=OTEL_SERVICE_NAME=opamp-consumer-simulator
ExecStart=$OPAMP_HOME/venvs/consumer/bin/opamp-consumer-simulator --config-path /etc/opamp/opamp-consumer-simulator.json
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

chown -R "$OPAMP_USER:$OPAMP_USER" "$OPAMP_HOME" /etc/opamp /var/log/opamp
systemctl daemon-reload
systemctl enable --now opamp-consumer-simulator
systemctl restart opamp-consumer-simulator

echo "Consumer simulator started against $OPAMP_SERVER_URL"
