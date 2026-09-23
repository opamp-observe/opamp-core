# Fluentd Consumer Configuration

This page covers configuration that is specific to the `fluentd` consumer plugin.
Shared consumer keys are documented in [consumer/README.md](../../README.md).

## Plugin Identity

Built-in plugin key:

- `consumer.service_type`: `fluentd`

Built-in entry point:

```json
{
  "service_type": "fluentd",
  "entry_point": "opamp_consumer.fluentd.client:main",
  "enabled": true
}
```

Installed command:

```bash
opamp-consumer-fluentd --config-path ./opamp.json
```

Unified command:

```bash
opamp-consumer --config-path ./opamp.json
```

## Consumer Keys

| Key | Required | Notes |
|---|---:|---|
| `consumer.agent_config_path` | Yes | Fluentd config loaded by the consumer and passed to `fluentd -c`. |
| `consumer.agent_additional_params` | No | Extra Fluentd CLI args. Fluentd does not use the Fluent Bit `--enable-hot-reload` flag. |
| `consumer.client_status_port` | Usually no | If omitted, the consumer parses the `monitor_agent` source port from `agent_config_path`. |
| `consumer.processTracking` | No | `Supervisor` launches Fluentd. `Observer` attaches by regex. |
| `consumer.processDetectionRegex` | Observer only | Regex used to discover an already running Fluentd process. |
| `consumer.agent_capabilities` | No | Supports `AcceptsRemoteConfig` and `ReportsHeartbeat` in addition to mandatory capabilities. |

## Required Monitor Source

The consumer reads Fluentd health, config, plugin, and version data through the
Fluentd `monitor_agent` source. The Fluentd config must include one.

Classic Fluentd config:

```conf
<source>
  @type monitor_agent
  bind 0.0.0.0
  port 24220
  log_level info
</source>
```

YAML-style config is also supported when it contains a mapping with
`@type: monitor_agent` or `type: monitor_agent`.

If `monitor_agent` is not configured, the consumer cannot poll Fluentd runtime
status endpoints.

## Optional RPC Reload Endpoint

The consumer can trigger Fluentd config reload after remote config is written
when the Fluentd config enables HTTP RPC:

```conf
<system>
  rpc_endpoint 127.0.0.1:24444
</system>
```

The consumer calls `GET /api/config.reload` on that endpoint. This is separate
from `monitor_agent`; `monitor_agent` provides status endpoints, while HTTP RPC
provides management endpoints such as config reload.

## Bind Handling

When `monitor_agent` is bound to `0.0.0.0`, the consumer rewrites the local status
host to `127.0.0.1` for polling.

## Metadata Comments

The Fluentd consumer reads optional comments from the config file:

```conf
# agent_description: Fluentd demo agent
# config_version: 2026-08-25-demo
# service_instance_id: fluentd-__hostname__
```

`service_instance_id` uses the shared token resolver from the consumer base code.

## Remote Config And Reload

The Fluentd consumer accepts remote config when `AcceptsRemoteConfig` is enabled.
After files are applied, the consumer calls the Fluentd HTTP RPC
`/api/config.reload` endpoint when `rpc_endpoint` is configured. Without
`rpc_endpoint`, remote config files are still written, but the consumer reports
that hot reload was not attempted.

## Minimal Example

```json
{
  "consumer": {
    "server_url": "http://localhost:4320",
    "server-authorization": "none",
    "service_type": "fluentd",
    "agent_config_path": "./fluentd.conf",
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
python -m opamp_consumer.fluentd.client \
  --config-path ./opamp.json \
  --agent-config-path ./fluentd.conf \
  --server-url http://localhost:4320
```
