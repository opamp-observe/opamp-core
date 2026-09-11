# OpAMP Consumer Configuration

This document consolidates all consumer configuration options and their CLI override support.

## Table of Contents

- [OpAMP Consumer Configuration](#opamp-consumer-configuration)
  - [Table of Contents](#table-of-contents)
  - [Config Source](#config-source)
  - [Override Precedence](#override-precedence)
  - [Quick Start Minimal Config](#quick-start-minimal-config)
  - [Run Scripts](#run-scripts)
  - [Process Tracking Modes](#process-tracking-modes)
  - [Semaphore Shutdown File](#semaphore-shutdown-file)
  - [Custom Handlers](#custom-handlers)
  - [Update Controllers](#update-controllers)
  - [Example `opamp.json`](#example-opampjson)
  - [Consumer Config Keys](#consumer-config-keys)
  - [Default Capabilities](#default-capabilities)
  - [Agent Capability Reference](#agent-capability-reference)
  - [Connection Settings](#connection-settings)
  - [Fluent Bit Comment Metadata](#fluent-bit-comment-metadata)
  - [CLI Example](#cli-example)
  - [Running As A Service/Daemon](#running-as-a-servicedaemon)
  - [Installed CLI Commands](#installed-cli-commands)
  - [Elastic Heartbeat Consumer](#elastic-heartbeat-consumer)
  - [Fluentd Consumer](#fluentd-consumer)
    - [Required Fluentd Monitor Source](#required-fluentd-monitor-source)
  - [Simulator Consumer](#simulator-consumer)

## Config Source

The consumer reads `opamp.json` from the current working directory by default.

You can override config path with:
- environment variable: `OPAMP_CONFIG_PATH`
- CLI flag: `--config-path`

## Override Precedence

Configuration is applied in this order (later wins):
1. Built-in defaults
2. `opamp.json` values
3. CLI parameters (these are overrides for config file values)
4. Agent config file parsing (`agent_config_path`) for runtime HTTP settings

Notes:
- If a CLI parameter is provided, it overrides the corresponding `opamp.json` value.
- Values parsed from the agent config file (`http_port`, `http_listen`, `http_server`) populate runtime fields:
  - `client_status_port`
  - `agent_http_port`
  - `agent_http_listen`
  - `agent_http_server`

## Quick Start Minimal Config

Use this minimal config for a fast local startup:

```json
{
  "consumer": {
    "server_url": "http://localhost",
    "tls": {
      "verify_server": true
    },
    "server-authorization": "none",
    "service_type": "fluentbit",
    "agent_config_path": "./fluent-bit.conf",
    "agent_additional_params": [],
    "heartbeat_frequency": 30,
    "full_update_controller": {
      "fullResendAfter": 1
    },
    "full_update_controller_type": "SentCount"
  }
}
```

## Run Scripts

Preferred local launch paths are the installed CLI commands or direct Python entrypoints for the consumer components.

Fluent Bit writes to `logs/supervisor_fluentbit.log` and Fluentd writes to
`logs/supervisor_fluentd.log` (each rotates on startup).

Default config resolution:
- Fluent Bit supervisor: `tests/opamp.json` -> `config/opamp.json`
- Fluentd supervisor: `consumer/opamp-fluentd.json` -> `tests/opamp.json` -> `config/opamp.json`
- Fluentd runtime config path: `consumer/fluentd.conf`

## Process Tracking Modes

The consumer supports two runtime process tracking strategies:

- `Supervisor` (default): launches and manages the agent process directly.
- `Observer`: does not launch a process; instead, discovers and tracks an external process by regex.

Configuration keys:

- `consumer.processTracking`: `Supervisor` or `Observer` (case-insensitive)
- `consumer.processDetectionRegex`: required when `processTracking=Observer`

Observer behavior:

- launch attaches to a running process resolved from `processDetectionRegex`
- restart uses terminate/reattach flow via process utilities
- terminate attempts graceful signal first (when supported) and then force termination if needed

## Semaphore Shutdown File

The agent can be shutdown through the use of a Semaphore file in the event of having problems communicating with the agent properly. The consumer checks for a local semaphore file named:

- `OpAMPSupervisor.signal`

Behavior:

- The check applies to all consumer service types.
- The file is checked in the consumer process working directory.
- If present, the consumer sends a disconnect, transitions to shutdown, and exits gracefully.

Operational intent:

- This mechanism is a last-resort emergency stop path and is not recommended for normal production operations.
- Because it is a shared local file signal, every consumer process that can see this file will stop.
- In shared development/test working directories, this can stop multiple local agents unintentionally.
- The server command capability path does not use `OpAMPSupervisor.signal`.

Operational guidance:

- Create the file only when you intend to stop all consumers in that working directory scope.
- Prefer server command capability for normal controlled shutdown orchestration.
- Remove stale `OpAMPSupervisor.signal` files after the incident/maintenance window so subsequent starts are not immediately signaled to stop.

## Custom Handlers

Custom capability handlers are documented here:

- `../docs/dev/consumer_custom_handlers.md`

That guide includes:

1. built-in handlers (`ChatOpsCommand`, `ShutdownCommand`, `NullCommand`)
2. runtime discovery and execution flow
3. implementation and deployment checklist for adding a new handler

Shared provider+consumer custom action implementation/deployment guide:

- `../docs/dev/adding_your_own_custom_action.md`

## Update Controllers

Update-controller behavior and extension guidance are documented here:

- `../docs/dev/consumer_update_controllers.md`

That guide includes:

1. existing controller strategies (`SentCount`, `AlwaysSend`, `TimeSend`)
2. reporting-flag send lifecycle behavior
3. implementation steps for adding a new controller type

## Example `opamp.json`

```json
{
  "consumer": {
    "server_url": "http://localhost",
    "server_port": 4320,
    "client_status_port": 2020,
    "chat_ops_port": 8888,
    "transport": "http",
    "tls": {
      "verify_server": true,
      "ca_file": "certs/ca-root.pem"
    },
    "server-authorization": "none",
    "OpAMP-token": "optional-config-token",
    "idp-token-url": "https://idp.example.com/realms/opamp/protocol/openid-connect/token",
    "idp-client-id": "opamp-consumer",
    "idp-client-secret": "replace-me",
    "idp-scope": "opamp",
    "idp-grant-type": "client_credentials",
    "service_type": "fluentbit",
    "log_agent_api_responses": false,
    "agent_config_path": "./fluent-bit.conf",
    "agent_additional_params": ["-R"],
    "processTracking": "Supervisor",
    "heartbeat_frequency": 30,
    "full_update_controller": {
      "fullResendAfter": 1
    },
    "full_update_controller_type": "SentCount",
    "allow_custom_capabilities": true,
    "agent_capabilities": [
      "AcceptsRemoteConfig",
      "ReportsHeartbeat"
    ],
    "log_level": "debug",
    "service_name": "Fluentbit",
    "service_namespace": "FluentBitNS"
  }
}
```

## Consumer Config Keys

`CLI` indicates direct CLI override support.

| Key | Type | CLI | Description | Example |
|---|---|---|---|---|
| `consumer.server_url` | string | Yes (`--server-url`) | OpAMP provider base URL. | `"http://localhost"` |
| `consumer.server_port` | integer | Yes (`--server-port`) | Optional port hint used by startup logic. | `4320` |
| `consumer.agent_config_path` | string | Yes (`--agent-config-path`) | Path to agent config file loaded by consumer. | `"./fluent-bit.conf"` |
| `consumer.agent_additional_params` | array[string] | Yes (`--agent-additional-params`) | Extra args passed to the launched agent process. | `["-R"]` |
| `consumer.processTracking` | string | No | Process lifecycle strategy: `Supervisor` or `Observer`. Defaults to `Supervisor`. | `"Supervisor"` |
| `consumer.processDetectionRegex` | string | No | Required when `processTracking=Observer`; regex used to detect/attach to an already-running process. | `"fluent-bit\\s+-c"` |
| `consumer.heartbeat_frequency` | integer | Yes (`--heartbeat-frequency`) | Heartbeat interval in seconds. | `30` |
| `consumer.full_update_controller` | object | Yes (`--full-update-controller`, JSON string) | Full update controller settings. `fullResendAfter` controls when all reporting flags are reset to `true`. | `{"fullResendAfter":1}` |
| `consumer.full_update_controller_type` | string | No | Full update controller implementation name (`SentCount`, `AlwaysSend`, `TimeSend`). | `"SentCount"` |
| `consumer.service_type` | string | No | Concrete consumer implementation (`fluentbit`, `fluentd`, `elastic_agent`, `elastic_heartbeat`, `simulator`, `vector`) or a configured plugin key. Default `fluentbit`. | `"fluentbit"` |
| `consumer.simulator_responses_path` | string | No | Required when `service_type=simulator`; path to simulator scripted server-request response JSON. | `"./consumer/simulator-responses.example.json"` |
| `consumer.log_level` | string | Yes (`--log-level`) | Consumer log level name (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). Resolved via Python `logging` names. | `"debug"` |
| `consumer.transport` | string | No | OpAMP transport mode (`http` or `websocket`). | `"http"` |
| `consumer.tls.verify_server` | boolean | No | Enables HTTPS/WSS certificate validation for provider connections. Default `true`. | `true` |
| `consumer.tls.ca_file` | string | No | Optional custom CA bundle file for HTTPS/WSS validation. Must exist when set. | `"certs/ca-root.pem"` |
| `consumer.server-authorization` | string | No | Outbound provider auth mode: `none`, `env-var`, `config-var`, or `idp`. | `"none"` |
| `consumer.OpAMP-token` | string | No | Static token used when `server-authorization=config-var`. | `"token-value"` |
| `consumer.idp-token-url` | string | No | IdP OAuth token endpoint URL used when `server-authorization=idp`. | `"https://idp.example.com/.../token"` |
| `consumer.idp-client-id` | string | No | IdP OAuth client ID for `idp` mode. | `"opamp-consumer"` |
| `consumer.idp-client-secret` | string | No | IdP OAuth client secret for `idp` mode. | `"replace-me"` |
| `consumer.idp-scope` | string | No | Optional OAuth scope for `idp` mode. | `"opamp"` |
| `consumer.idp-grant-type` | string | No | OAuth grant type for `idp` mode. Default `client_credentials`. | `"client_credentials"` |
| `consumer.log_agent_api_responses` | boolean | No | Enables verbose logging of local API responses. | `false` |
| `consumer.allow_custom_capabilities` | boolean | No | Enables publishing/discovery of custom capabilities. | `true` |
| `consumer.agent_capabilities` | integer, string, or array[string] | No | Optional capability enable list or mask. Configured values are merged with the mandatory capabilities, deduplicated, then intersected with the concrete client's supported-capability list. Unsupported configured values are warned and ignored. | `["AcceptsRemoteConfig","ReportsHeartbeat"]` |
| `consumer.preserve_previous_config` | boolean | No | When `true`, an existing remote-config target file is renamed to `.replaced_yyyy-mm-dd--hh-mm-ss` before the new content is written. | `false` |
| `consumer.service_name` | string | No | Reported service name in agent description. | `"Fluentbit"` |
| `consumer.service_namespace` | string | No | Reported service namespace in agent description. | `"FluentBitNS"` |
| `consumer.client_status_port` | integer | No | Local status polling port. If unset, parsed from agent config `http_port`. | `2020` |
| `consumer.chat_ops_port` | integer | No | Local ChatOps port used by custom command handler. Defaults to `8888` when unset. | `8888` |

Authorization mode behavior:
- `none`: no outbound `Authorization` header.
- `env-var`: token is read from `OpAMP-token` environment variable.
- `config-var`: token is read from `consumer.OpAMP-token`.
- `idp`: token is requested from the configured IdP token endpoint and cached in
  runtime config header fields (`server_authorization_header_name/value`).
  If provider returns auth errors (`401`/`403`), the client renegotiates and retries once.

TLS transport behavior:
- HTTP mode uses `consumer.server_url` directly (`http://` or `https://`).
- WebSocket mode normalizes URL scheme before connecting:
  - `http://...` -> `ws://...`
  - `https://...` -> `wss://...`

## Default Capabilities

When `consumer.agent_capabilities` is not set, the consumer advertises these mandatory capabilities:
- `ReportsStatus`
- `AcceptsRestartCommand`
- `ReportsHealth`

If the selected `consumer.service_type` supports additional capabilities, you can enable them via `consumer.agent_capabilities`, for example:
- `AcceptsRemoteConfig`
- `ReportsHeartbeat`

Configured capabilities are merged with the mandatory list above. Any capability supported by the client but not configured is left disabled and logged at `INFO`. Any configured capability not supported by the client is ignored and logged at `WARNING`.

Notes:

- `consumer.agent_capabilities` accepts an integer mask, a comma-separated string, or an array of capability names.
- Mandatory capabilities do not need to be repeated in config; they are added automatically.
- Duplicate configured capability names are ignored after normalization.

## Agent Capability Reference

The `consumer.agent_capabilities` setting accepts any `AgentCapabilities` name from the shared OpAMP enum.

Current built-in consumer support:

- All built-in consumer types support `ReportsStatus`, `AcceptsRestartCommand`, and `ReportsHealth`.
- Current built-in consumer types (`fluentbit`, `fluentd`, `elastic_agent`, `elastic_heartbeat`, `simulator`, and `vector`) support the mandatory capabilities. Fluent Bit, Fluentd, Elastic Agent, Elastic Heartbeat, simulator, and Vector also support `ReportsHeartbeat`, `AcceptsRemoteConfig`, and `ReportsEffectiveConfig`.
- Other names in the table below are valid OpAMP capability names, but current built-in consumer clients do not enable them because they are not in their supported-capability lists.

| Capability | Mask | Meaning | Current built-in consumer support |
|---|---:|---|---|
| `ReportsStatus` | `0x00000001` | Agent sends normal status-bearing `AgentToServer` updates. | Yes |
| `AcceptsRemoteConfig` | `0x00000002` | Agent can receive and apply server-provided remote configuration. | Yes |
| `ReportsEffectiveConfig` | `0x00000004` | Agent reports the effective configuration currently running after processing config inputs. | No |
| `AcceptsPackages` | `0x00000008` | Agent can receive package installation or upgrade offers from the server. | No |
| `ReportsPackageStatuses` | `0x00000010` | Agent reports package download/install state back to the server. | No |
| `ReportsOwnTraces` | `0x00000020` | Agent can report connection settings or status for its own trace export pipeline. | No |
| `ReportsOwnMetrics` | `0x00000040` | Agent can report connection settings or status for its own metrics export pipeline. | No |
| `ReportsOwnLogs` | `0x00000080` | Agent can report connection settings or status for its own logs export pipeline. | No |
| `AcceptsOpAMPConnectionSettings` | `0x00000100` | Agent accepts server-driven changes to the OpAMP transport connection settings. | No |
| `AcceptsOtherConnectionSettings` | `0x00000200` | Agent accepts server-driven changes to non-OpAMP connection settings. | No |
| `AcceptsRestartCommand` | `0x00000400` | Agent accepts a server-issued restart command. | Yes |
| `ReportsHealth` | `0x00000800` | Agent reports health state for itself and optionally sub-components. | Yes |
| `ReportsRemoteConfig` | `0x00001000` | Agent reports status for the last remote-config application attempt. | No |
| `ReportsHeartbeat` | `0x00002000` | Agent reports heartbeat-related runtime information through the consumer heartbeat path. | Yes |
| `ReportsAvailableComponents` | `0x00004000` | Agent can report a component inventory / component map. | No |
| `ReportsConnectionSettingsStatus` | `0x00008000` | Agent reports status for previously offered connection settings. | No |

## Connection Settings

We currently do not support `ReportsOwnTraces`, `ReportsOwnMetrics`, or
`ReportsOwnLogs` as configurable connection-settings features in this project.

Design rationale:

- Fluent Bit and Fluentd operational configuration is expected to define
  observability pipelines directly.
- The OpAMP protocol already lets us deploy updated agent configuration when
  pipeline changes are needed.
- In practice, include-based configuration structure and variable injection can
  make runtime connection-settings mutation error-prone and harder to operate
  safely across environments.

Recommended pattern:

- Keep each agent's standard configuration responsible for its own
  observability outputs.
- Use include files (for example environment-specific included fragments) to
  manage traces/metrics/logs destinations and credentials.
- Use OpAMP-delivered config updates to roll out those include/file changes in
  a controlled way.

## Fluent Bit Comment Metadata

The consumer reads optional metadata comments from the agent config file:
- `# agent_description: ...`
- `# service_instance_id: ...`

Supported tokens in `service_instance_id`:
- `__IP__` -> local host IP
- `__hostname__` -> local hostname
- `__mac-ad__` -> local MAC address

Example:

```ini
# service_instance_id: fb-__hostname__-__IP__-__mac-ad__
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

## Running As A Service/Daemon

For Linux `systemd` and Windows service examples (including required permissions so the consumer can launch `fluent-bit` or `fluentd`), see:

- `../docs/service_daemon_setup.md`

## Installed CLI Commands

When installed as a package, console scripts are available:

- `opamp-consumer` -> `opamp_consumer.client:main` (routes by `consumer.service_type`)
- `opamp-consumer-elastic-heartbeat` -> `opamp_consumer.elastic_heartbeat.client:main`
- `opamp-consumer-fluentd` -> `opamp_consumer.fluentd.client:main`
- `opamp-consumer-simulator` -> `opamp_consumer.simulator.client:main`
- `opamp-consumer-vector` -> `opamp_consumer.vector.client:main`

Each consumer `--help` response prints JSON config/help content and includes
`component_version` (git commit/date derived version metadata).

## Built-In Plugin Registry

Built-in `consumer.service_type` mappings are loaded at startup from
`src/opamp_consumer/builtin_consumer_plugins.json`. The packaged file defines
the default Fluent Bit, Fluentd, Elastic Agent, Elastic Heartbeat, simulator,
and Vector entry points.

Set `OPAMP_CONSUMER_BUILTIN_PLUGINS_PATH` to point at an alternate JSON file
when a deployment needs to replace that startup registry without modifying
Python code. Per-consumer `consumer.plugins` entries are still applied after
the startup registry and can add, override, or disable service types.

## Elastic Heartbeat Consumer

The `elastic_heartbeat` plugin supervises Elastic Heartbeat with
`heartbeat -e -c <config>`, reads the Beat HTTP monitoring API, and can be used
as the reference implementation for other Elastic Beat monitor plugins.

See [consumer/docs/plugins/elastic-heartbeat.md](docs/plugins/elastic-heartbeat.md)
for config keys, demo files, and container regression coverage.

## Vector Consumer

The `vector` plugin supervises Vector with `vector --config`, polls the Vector
health API, and supports the self-monitoring demo under
[docs/vector-self-monitor](../docs/vector-self-monitor/readme.md).

See [consumer/docs/plugins/vector.md](docs/plugins/vector.md) for plugin-specific settings.

## Fluentd Consumer

An alternate concrete consumer implementation is available for Fluentd use cases.

- Module entrypoint: `python -m opamp_consumer.fluentd.client`

### Required Fluentd Monitor Source

For OpAMP to read Fluentd health/version data, the Fluentd config must include a `monitor_agent` source (core Fluentd functionality).

Example:

```conf
<source>
  @type monitor_agent
  bind 0.0.0.0
  port 24220
  log_level info
</source>
```

If `monitor_agent` is not configured, the consumer cannot poll Fluentd runtime status endpoints.

Example:

```bash
python -m opamp_consumer.fluentd.client \
  --config-path ./opamp.json \
  --agent-config-path ./fluentd.conf \
  --server-url http://localhost:4320
```

## Simulator Consumer

Simulator behavior, response scripting, and request/action reference were moved to:

- [consumer-sim/README.md](../consumer-sim/README.md#simulator-client-behavior)
- [consumer-sim/consumer_instances.md](../consumer-sim/consumer_instances.md)
