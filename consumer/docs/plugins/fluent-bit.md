# Fluent Bit Consumer Configuration

This page covers configuration that is specific to the `fluentbit` consumer plugin.
Shared consumer keys such as `server_url`, `transport`, TLS, auth, process tracking,
capabilities, and update controllers are documented in [consumer/README.md](../../README.md).
For the built-in implementation capability matrix, see
[docs/consumer_implementations.md](../../../docs/consumer_implementations.md).

## Plugin Identity

Built-in plugin key:

- `consumer.service_type`: `fluentbit`

Built-in entry point:

```json
{
  "service_type": "fluentbit",
  "entry_point": "opamp_consumer.fluentbit.client:main",
  "enabled": true
}
```

Installed command:

```bash
opamp-consumer --config-path ./opamp.json
```

Direct module form:

```bash
python -m opamp_consumer.fluentbit.client --config-path ./opamp.json
```

## Consumer Keys

| Key | Required | Notes |
|---|---:|---|
| `consumer.agent_config_path` | Yes | Fluent Bit config loaded by the consumer and passed to `fluent-bit -c`. |
| `consumer.agent_additional_params` | No | Extra Fluent Bit CLI args. Remote-config hot reload can add `-Y` / `--enable-hot-reload` when needed. |
| `consumer.client_status_port` | Usually no | If omitted, the consumer parses the Fluent Bit HTTP server port from `agent_config_path`. |
| `consumer.processTracking` | No | `Supervisor` launches Fluent Bit. `Observer` attaches by regex. |
| `consumer.processDetectionRegex` | Observer only | Regex used to discover an already running Fluent Bit process. |
| `consumer.agent_capabilities` | No | Supports `AcceptsRemoteConfig`, `ReportsEffectiveConfig`, and `ReportsHeartbeat` in addition to mandatory capabilities. |

## Fluent Bit HTTP Server

The consumer polls Fluent Bit's local HTTP API for health, version, uptime, and metrics.
The Fluent Bit config should enable the HTTP server:

```ini
[SERVICE]
    HTTP_Server  On
    HTTP_Listen  0.0.0.0
    HTTP_Port    2020
```

When `HTTP_Listen` is `0.0.0.0`, the consumer uses loopback for local polling.

## Metadata Comments

The Fluent Bit consumer reads optional metadata comments from the agent config file:

```ini
# agent_description: Fluent Bit demo agent
# service_instance_id: fb-__hostname__-__IP__-__mac-ad__
```

Supported `service_instance_id` tokens:

- `__IP__`
- `__hostname__`
- `__mac-ad__`

## Remote Config And Reload

When `AcceptsRemoteConfig` is enabled, the consumer can apply provider-delivered
config files. For supervised Fluent Bit processes, launch-time hot reload is enabled
when needed by adding one of the Fluent Bit hot-reload flags if it is not already present.

After a remote config is written, the consumer tries:

```text
POST /api/v2/reload
```

The reload endpoint is built from the parsed Fluent Bit HTTP host and port.

## Minimal Example

```json
{
  "consumer": {
    "server_url": "http://localhost:4320",
    "server-authorization": "none",
    "service_type": "fluentbit",
    "agent_config_path": "./fluent-bit.conf",
    "agent_additional_params": [],
    "agent_capabilities": [
      "AcceptsRemoteConfig",
      "ReportsHeartbeat"
    ],
    "heartbeat_frequency": 30
  }
}
```

## CLI Example

```bash
python -m opamp_consumer.fluentbit.client \
  --config-path ./opamp.json \
  --server-url http://localhost:4320 \
  --server-port 4320 \
  --agent-config-path ./fluent-bit.conf \
  --agent-additional-params -R \
  --heartbeat-frequency 15 \
  --log-level INFO \
  --full-update-controller '{"fullResendAfter":1}'
```
