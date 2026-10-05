# Simulator Consumer Configuration

This page covers configuration that is specific to the `simulator` consumer plugin.
Shared consumer keys are documented in [consumer/README.md](../../README.md).
For the built-in implementation capability matrix, see
[docs/consumer_implementations.md](../../../docs/consumer_implementations.md).

The simulator is a development-only consumer. It does not launch a real telemetry
agent; it reports synthetic local health and replays scripted responses to server
requests.

## Plugin Identity

Built-in plugin key:

- `consumer.service_type`: `simulator`

Built-in entry point:

```json
{
  "service_type": "simulator",
  "entry_point": "opamp_consumer.simulator.client:main",
  "enabled": true
}
```

Installed command:

```bash
opamp-consumer-simulator --config-path ./opamp.json
```

Unified command:

```bash
opamp-consumer --config-path ./opamp.json
```

## Required Development Flag

Simulator startup is blocked unless development features are explicitly enabled:

```bash
APP_ENABLE_DEV_FEATURES=true opamp-consumer-simulator --config-path ./opamp.json
```

## Consumer Keys

| Key | Required | Notes |
|---|---:|---|
| `consumer.simulator_responses_path` | Yes | JSON file describing scripted responses for server request types. |
| `consumer.agent_additional_params` | No | Can carry simulator metadata JSON used for service instance/version/config metadata. |
| `consumer.agent_config_path` | No | Not used to launch an agent. Metadata normally comes from `agent_additional_params`. |
| `consumer.processTracking` | No | Simulator launch/terminate/restart are no-ops; process tracking is normally irrelevant. |
| `consumer.agent_capabilities` | No | Supports `AcceptsRemoteConfig`, `ReportsEffectiveConfig`, and `ReportsHeartbeat` in addition to mandatory capabilities. |

## Scripted Responses

The response file root can be either a request map or an object with a `responses`
property.

Supported request keys:

- `error_response`
- `remote_config`
- `connection_settings`
- `packages_available`
- `flags`
- `capabilities`
- `agent_identification`
- `command`
- `custom_capabilities`
- `custom_message`
- `*`

Each value can be a string, an object, or a list of strings/objects. Supported
actions are:

- `accept`: run the normal handler
- `ignore`: suppress the handler
- `error`: raise a simulated error

Example:

```json
{
  "responses": {
    "*": "accept",
    "command": [
      {
        "action": "accept"
      },
      {
        "action": "error",
        "message": "simulated command failure"
      }
    ],
    "remote_config": {
      "action": "ignore"
    }
  }
}
```

When a request type is omitted, the simulator uses the `*` fallback when present,
otherwise it defaults to `accept`.

## Metadata

Simulator metadata can be passed in `consumer.agent_additional_params` as JSON.
The plugin can consume:

- `service_instance_uid`
- `service_instance_id`
- `client_version`
- `config_version`

Example:

```json
{
  "consumer": {
    "agent_additional_params": [
      "{\"service_instance_id\":\"sim-1\",\"client_version\":\"scripted-1\",\"config_version\":\"demo\"}"
    ]
  }
}
```

## Launcher Process Record

The simulator can cooperate with a launcher-owned process record file:

- `OPAMP_SIM_PROCESS_RECORD_FILE`
- `OPAMP_SIM_PROCESS_RECORD_NAME`

When the matching record status becomes `shutdown`, the simulator updates it to
`shuttingdown` and exits gracefully.

## Minimal Example

```json
{
  "consumer": {
    "server_url": "http://localhost:4320",
    "server-authorization": "none",
    "service_type": "simulator",
    "simulator_responses_path": "./simulator-responses.json",
    "agent_capabilities": [
      "AcceptsRemoteConfig",
      "ReportsHeartbeat"
    ],
    "heartbeat_frequency": 30
  }
}
```

Additional simulator launcher documentation:

- [consumer-sim/README.md](../../../consumer-sim/README.md#simulator-client-behavior)
- [consumer-sim/consumer_instances.md](../../../consumer-sim/consumer_instances.md)
