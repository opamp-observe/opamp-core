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

# Configure the complete server role after install-opamp.sh creates its Python
# environment. Containers provide identity and telemetry; systemd runs OpAMP services.
OPAMP_HOME="${OPAMP_HOME:-/opt/opamp}"
OPAMP_USER="${OPAMP_USER:-opamp}"
OPAMP_PUBLIC_HOST="${OPAMP_PUBLIC_HOST:-$(hostname -f)}"
OPAMP_SERVER_PRIVATE_IP="${OPAMP_SERVER_PRIVATE_IP:-10.42.0.10}"
KEYCLOAK_ADMIN="${KEYCLOAK_ADMIN:-admin}"
KEYCLOAK_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-opamp}"
KEYCLOAK_CLIENT_ID="${KEYCLOAK_CLIENT_ID:-opamp-ui}"
KEYCLOAK_CLIENT_SECRET="${KEYCLOAK_CLIENT_SECRET:-}"
OPAMP_UI_USER="${OPAMP_UI_USER:-opampuser}"
OPAMP_UI_PASSWORD="${OPAMP_UI_PASSWORD:-}"
OAUTH2_PROXY_COOKIE_SECRET="${OAUTH2_PROXY_COOKIE_SECRET:-}"
KEYCLOAK_CONTAINER_NAME="opamp-keycloak"
KEYCLOAK_IMAGE="quay.io/keycloak/keycloak:25.0"
KEYCLOAK_READY_ATTEMPTS="${KEYCLOAK_READY_ATTEMPTS:-60}"
KEYCLOAK_READY_INTERVAL_SECONDS="${KEYCLOAK_READY_INTERVAL_SECONDS:-5}"
KEYCLOAK_READY_URL="http://127.0.0.1:8081/realms/master"

if [[ "$OPAMP_PUBLIC_HOST" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  OPAMP_PUBLIC_SAN="IP:$OPAMP_PUBLIC_HOST"
else
  OPAMP_PUBLIC_SAN="DNS:$OPAMP_PUBLIC_HOST"
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this script as root or with sudo." >&2
  exit 1
fi
if [[ -z "$KEYCLOAK_ADMIN_PASSWORD" ]]; then
  echo "KEYCLOAK_ADMIN_PASSWORD is required." >&2
  exit 1
fi

install -d -m 0755 /etc/opamp /etc/opamp/certs /var/log/opamp "$OPAMP_HOME/config" "$OPAMP_HOME/runtime"
chown -R "$OPAMP_USER:$OPAMP_USER" "$OPAMP_HOME" /var/log/opamp /etc/opamp

# Phase 1: create the regression TLS identity and application secrets locally.
# Generated values are persisted so rerunning startup does not rotate credentials.
if [[ ! -s /etc/opamp/certs/opamp-selfsigned.crt || ! -s /etc/opamp/certs/opamp-selfsigned.key ]]; then
  openssl req -x509 -nodes -newkey rsa:4096 -days 365 \
    -subj "/CN=$OPAMP_PUBLIC_HOST" \
    -addext "subjectAltName=$OPAMP_PUBLIC_SAN,IP:$OPAMP_SERVER_PRIVATE_IP" \
    -keyout /etc/opamp/certs/opamp-selfsigned.key \
    -out /etc/opamp/certs/opamp-selfsigned.crt
fi

if [[ -z "$KEYCLOAK_CLIENT_SECRET" ]]; then
  if [[ -s /etc/opamp/keycloak-client-secret ]]; then
    KEYCLOAK_CLIENT_SECRET="$(cat /etc/opamp/keycloak-client-secret)"
  else
    KEYCLOAK_CLIENT_SECRET="$(openssl rand -hex 32)"
    printf "%s" "$KEYCLOAK_CLIENT_SECRET" > /etc/opamp/keycloak-client-secret
  fi
fi
if [[ -z "$OPAMP_UI_PASSWORD" ]]; then
  if [[ -s /etc/opamp/opamp-ui-password ]]; then
    OPAMP_UI_PASSWORD="$(cat /etc/opamp/opamp-ui-password)"
  else
    OPAMP_UI_PASSWORD="$(openssl rand -base64 24)"
    printf "%s" "$OPAMP_UI_PASSWORD" > /etc/opamp/opamp-ui-password
  fi
fi
if [[ -z "$OAUTH2_PROXY_COOKIE_SECRET" ]]; then
  if [[ -s /etc/opamp/oauth2-cookie-secret ]]; then
    OAUTH2_PROXY_COOKIE_SECRET="$(cat /etc/opamp/oauth2-cookie-secret)"
  else
    OAUTH2_PROXY_COOKIE_SECRET="$(openssl rand -base64 32 | tr -d '\n' | cut -c1-32)"
    printf "%s" "$OAUTH2_PROXY_COOKIE_SECRET" > /etc/opamp/oauth2-cookie-secret
  fi
fi
cat > /etc/opamp/opamp-ui-user.txt <<EOF
Keycloak realm: $KEYCLOAK_REALM
UI username: $OPAMP_UI_USER
UI password: $OPAMP_UI_PASSWORD
EOF
chmod 0600 /etc/opamp/keycloak-client-secret /etc/opamp/opamp-ui-password /etc/opamp/oauth2-cookie-secret /etc/opamp/opamp-ui-user.txt

# Phase 2: write provider and collector configuration consumed by later services.
cat > /etc/opamp/opamp-provider.json <<'EOF'
{
  "provider": {
    "webui_port": 8080,
    "delayed_comms_seconds": 60,
    "significant_comms_seconds": 300,
    "minutes_keep_disconnected": 30,
    "retryAfterSeconds": 30,
    "client_event_history_size": 200,
    "log_level": "DEBUG",
    "human_in_loop_approval": false,
    "allow-remote-config": true,
    "allow-effective-config": true,
    "allow-connection-settings": true,
    "allow-connection-settings-request": true,
    "opamp-use-authorization": "none",
    "ui-use-authorization": "none",
    "state_persistence": {
      "enabled": true,
      "state_file_prefix": "/opt/opamp/runtime/opamp_server_state",
      "retention_count": 10,
      "flush_mode": "graceful_shutdown",
      "autosave_interval_seconds_since_change": 60
    }
  },
  "component-entry-points": {
    "quart": [
      {
        "entry_point": "config_service.opamp_integration:register_config_service_feature",
        "label": "Config Editor",
        "url": "/config-service/ui",
        "enabled": true
      },
      {
        "entry_point": "client_config_generator_service.opamp_integration:register_client_config_generator_feature",
        "label": "Client Config Generator",
        "url": "/client-config-generator-service/ui",
        "enabled": true
      }
    ]
  },
  "opamp": {
    "client_config_generator": {
      "web_port": 8095,
      "log_level": "DEBUG",
      "read_only": false,
      "storage": {
        "configuration_directory": "/opt/opamp/generated-client-configs"
      }
    }
  },
  "observability": {
    "enabled": true,
    "service_name": "opamp-provider",
    "otlp_endpoint": "http://127.0.0.1:4317",
    "traces_enabled": true,
    "metrics_enabled": true,
    "logs_enabled": true
  }
}
EOF

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

# Phase 3: start containerized telemetry and identity dependencies before any
# Python services that publish telemetry or require browser authentication.
docker rm -f opamp-otel-collector >/dev/null 2>&1 || true
docker run -d --name opamp-otel-collector --restart unless-stopped --network host \
  -v /etc/opamp/otel-collector.yaml:/etc/otelcol-contrib/config.yaml:ro \
  -v /var/log/opamp:/var/log/opamp \
  otel/opentelemetry-collector-contrib:0.104.0

docker rm -f "$KEYCLOAK_CONTAINER_NAME" >/dev/null 2>&1 || true
docker run -d --name "$KEYCLOAK_CONTAINER_NAME" --restart unless-stopped --network host \
  -e KEYCLOAK_ADMIN="$KEYCLOAK_ADMIN" \
  -e KEYCLOAK_ADMIN_PASSWORD="$KEYCLOAK_ADMIN_PASSWORD" \
  "$KEYCLOAK_IMAGE" \
  start-dev --http-port=8081 --hostname="https://$OPAMP_PUBLIC_HOST:8443" --proxy-headers=xforwarded

# Wait until Keycloak accepts realm requests before running its administration CLI.
# The configured attempt count and interval bound startup time on smaller cloud instances.
wait_for_keycloak() {
  local attempt_number
  local container_status

  for ((attempt_number = 1; attempt_number <= KEYCLOAK_READY_ATTEMPTS; attempt_number++)); do
    container_status="$(docker inspect --format '{{.State.Status}}' "$KEYCLOAK_CONTAINER_NAME" 2>/dev/null || true)"
    if [[ "$container_status" == "running" ]] &&
      curl -fsS "$KEYCLOAK_READY_URL" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$KEYCLOAK_READY_INTERVAL_SECONDS"
  done

  container_status="$(docker inspect --format '{{.State.Status}}' "$KEYCLOAK_CONTAINER_NAME" 2>/dev/null || true)"
  echo "Keycloak did not become ready; container status: ${container_status:-unknown}" >&2
  docker logs --tail 80 "$KEYCLOAK_CONTAINER_NAME" >&2 || true
  return 1
}

if ! wait_for_keycloak; then
  exit 1
fi

docker exec "$KEYCLOAK_CONTAINER_NAME" /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://127.0.0.1:8081 --realm master \
  --user "$KEYCLOAK_ADMIN" --password "$KEYCLOAK_ADMIN_PASSWORD"
docker exec "$KEYCLOAK_CONTAINER_NAME" /opt/keycloak/bin/kcadm.sh create realms \
  -s realm="$KEYCLOAK_REALM" -s enabled=true >/dev/null 2>&1 || true
docker exec "$KEYCLOAK_CONTAINER_NAME" /opt/keycloak/bin/kcadm.sh create clients -r "$KEYCLOAK_REALM" \
  -s clientId="$KEYCLOAK_CLIENT_ID" \
  -s enabled=true \
  -s publicClient=false \
  -s secret="$KEYCLOAK_CLIENT_SECRET" \
  -s standardFlowEnabled=true \
  -s directAccessGrantsEnabled=true \
  -s 'redirectUris=["https://'"$OPAMP_PUBLIC_HOST"'/oauth2/callback"]' >/dev/null 2>&1 || true
docker exec "$KEYCLOAK_CONTAINER_NAME" /opt/keycloak/bin/kcadm.sh create users -r "$KEYCLOAK_REALM" \
  -s username="$OPAMP_UI_USER" -s enabled=true >/dev/null 2>&1 || true
docker exec "$KEYCLOAK_CONTAINER_NAME" /opt/keycloak/bin/kcadm.sh set-password -r "$KEYCLOAK_REALM" \
  --username "$OPAMP_UI_USER" --new-password "$OPAMP_UI_PASSWORD" --temporary=false

# OAuth2 Proxy translates the Keycloak browser session into Nginx auth decisions.
docker rm -f opamp-oauth2-proxy >/dev/null 2>&1 || true
docker run -d --name opamp-oauth2-proxy --restart unless-stopped --network host \
  quay.io/oauth2-proxy/oauth2-proxy:v7.6.0 \
  --http-address=127.0.0.1:4180 \
  --provider=keycloak-oidc \
  --client-id="$KEYCLOAK_CLIENT_ID" \
  --client-secret="$KEYCLOAK_CLIENT_SECRET" \
  --cookie-secret="$OAUTH2_PROXY_COOKIE_SECRET" \
  --cookie-secure=true \
  --email-domain="*" \
  --redirect-url="https://$OPAMP_PUBLIC_HOST/oauth2/callback" \
  --oidc-issuer-url="https://$OPAMP_PUBLIC_HOST:8443/realms/$KEYCLOAK_REALM" \
  --ssl-insecure-skip-verify=true \
  --upstream=file:///dev/null

# Phase 4: define systemd units for durable process supervision and restart behavior.
cat > /etc/systemd/system/opamp-provider.service <<EOF
[Unit]
Description=OpAMP Provider
After=network-online.target opamp-otel-collector.service
Wants=network-online.target

[Service]
User=$OPAMP_USER
Group=$OPAMP_USER
WorkingDirectory=$OPAMP_HOME
Environment=OPAMP_CONFIG_PATH=/etc/opamp/opamp-provider.json
Environment=OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4317
Environment=OTEL_SERVICE_NAME=opamp-provider
ExecStart=$OPAMP_HOME/venvs/server/bin/opamp-provider --config-path /etc/opamp/opamp-provider.json --host 127.0.0.1 --port 8080 --restore
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/config-service.service <<EOF
[Unit]
Description=OpAMP Config Service
After=network-online.target
Wants=network-online.target

[Service]
User=$OPAMP_USER
Group=$OPAMP_USER
WorkingDirectory=$OPAMP_HOME
Environment=OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4317
Environment=OTEL_SERVICE_NAME=config-service
ExecStart=$OPAMP_HOME/venvs/server/bin/config-service --host 127.0.0.1 --port 8090
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/catalog-service.service <<EOF
[Unit]
Description=OpAMP Catalog Service
After=network-online.target
Wants=network-online.target

[Service]
User=$OPAMP_USER
Group=$OPAMP_USER
WorkingDirectory=$OPAMP_HOME
Environment=OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4317
Environment=OTEL_SERVICE_NAME=catalog-service
ExecStart=$OPAMP_HOME/venvs/server/bin/catalog-service --host 127.0.0.1 --port 8092
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/svr-credentials-manager-service.service <<EOF
[Unit]
Description=OpAMP Server Credentials Manager Service
After=network-online.target
Wants=network-online.target

[Service]
User=$OPAMP_USER
Group=$OPAMP_USER
WorkingDirectory=$OPAMP_HOME
Environment=OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4317
Environment=OTEL_SERVICE_NAME=svr-credentials-manager-service
ExecStart=$OPAMP_HOME/venvs/server/bin/svr-credentials-manager-service --host 127.0.0.1 --port 8091
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/opamp-broker.service <<EOF
[Unit]
Description=OpAMP Broker
After=network-online.target
Wants=network-online.target

[Service]
User=$OPAMP_USER
Group=$OPAMP_USER
WorkingDirectory=$OPAMP_HOME
Environment=OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4317
Environment=OTEL_SERVICE_NAME=opamp-broker
ExecStart=$OPAMP_HOME/venvs/server/bin/opamp-broker --verify-startup none
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Phase 5: Nginx terminates self-signed TLS, delegates browser authentication to
# OAuth2 Proxy, and publishes Keycloak separately on port 8443.
cat > /etc/nginx/sites-available/opamp <<EOF
server {
    listen 443 ssl;
    server_name $OPAMP_PUBLIC_HOST;

    ssl_certificate /etc/opamp/certs/opamp-selfsigned.crt;
    ssl_certificate_key /etc/opamp/certs/opamp-selfsigned.key;

    location /oauth2/ {
        proxy_pass http://127.0.0.1:4180;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Scheme https;
        proxy_set_header X-Auth-Request-Redirect \$request_uri;
    }

    location = /oauth2/auth {
        proxy_pass http://127.0.0.1:4180/oauth2/auth;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Scheme https;
        proxy_set_header Content-Length "";
        proxy_pass_request_body off;
    }

    location / {
        auth_request /oauth2/auth;
        error_page 401 = /oauth2/sign_in;
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}

server {
    listen 8443 ssl;
    server_name $OPAMP_PUBLIC_HOST;

    ssl_certificate /etc/opamp/certs/opamp-selfsigned.crt;
    ssl_certificate_key /etc/opamp/certs/opamp-selfsigned.key;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host \$host:8443;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port 8443;
    }
}
EOF

ln -sf /etc/nginx/sites-available/opamp /etc/nginx/sites-enabled/opamp
rm -f /etc/nginx/sites-enabled/default
nginx -t

# Enable services only after all configuration validates, then restart them to
# apply this run's generated files deterministically.
systemctl daemon-reload
systemctl enable --now opamp-provider config-service catalog-service svr-credentials-manager-service opamp-broker nginx
systemctl restart opamp-provider config-service catalog-service svr-credentials-manager-service opamp-broker nginx

echo "OpAMP UI: https://$OPAMP_PUBLIC_HOST/"
echo "Keycloak: https://$OPAMP_PUBLIC_HOST:8443/"
echo "UI credentials are stored in /etc/opamp/opamp-ui-user.txt"
