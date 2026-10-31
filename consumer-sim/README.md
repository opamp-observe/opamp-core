# Consumer Simulator Launcher

This tool starts/stops batches of OpAMP consumer instances from one config file.

It also exports a generic, embeddable async lifecycle API for integration packages. This API does
not import or depend on SignalGenerator and does not alter provider behavior:

```python
from opamp_consumer_sim import (
    SimulatorIdentity,
    SimulatorInstance,
    SimulatorInstanceConfig,
    SimulatorResponsePlan,
)

instance = SimulatorInstance(
    SimulatorInstanceConfig(
        name="demo",
        consumer_config_path=consumer_path,
        response_plan=SimulatorResponsePlan(responses_path),
        identity=SimulatorIdentity("demo-01", "1.0.0", "scenario-1"),
    )
)
await instance.start()
health = instance.health()  # passive; no request or scripted response is consumed
await instance.logical_restart()
await instance.stop()
```

The host owns the event loop and cancellation. `start`, `stop`, `logical_restart`, and
`apply_config` are awaitable; shutdown cancels and awaits the heartbeat task and finalizes the
connection. `APP_ENABLE_DEV_FEATURES=true` remains mandatory. These public types follow the
`opamp-consumer-sim` `0.6.x` compatibility line.

Detailed schema/parameter reference:

- `consumer-sim/consumer_instances.md`
- `consumer-sim/simulator_design.md` (design intent and server-testing focus)
- `consumer-sim/config/consumer_instances.schema.json` (machine-readable JSON schema)

## Production Scope

The simulator tooling is not intended for production deployment.

- `consumer-sim` launcher/config/docs are for test and validation workflows.
- Production deployments should run real consumer agent types (`fluentbit` or `fluentd`) and should not deploy simulator instances.

## Command

```bash
python consumer-sim/src/consumer_sim_launcher.py start
python consumer-sim/src/consumer_sim_launcher.py stop
python consumer-sim/src/consumer_sim_launcher.py --help
python consumer-sim/src/consumer_sim_launcher.py --version
```

Packaged installation entrypoint:

```bash
opamp-consumer-sim start
opamp-consumer-sim stop
```

The launcher accepts one positional argument only: `start` or `stop`.
`--help` and `--version` include git commit/date derived component version metadata.

## Required Dev Flag

Simulator startup is gated by environment flag `APP_ENABLE_DEV_FEATURES`.

- If `APP_ENABLE_DEV_FEATURES` is unset or false-like, simulator startup is blocked.
- The simulator logs the startup failure and exits gracefully before sending any details to the server.
- The CLI demo-consumer flow sets this flag to `true` automatically for simulator startup.
- If you launch the simulator directly (without wrappers), set it explicitly:

```bash
export APP_ENABLE_DEV_FEATURES=true
python consumer-sim/src/consumer_sim_launcher.py start
```

```cmd
set APP_ENABLE_DEV_FEATURES=true
python consumer-sim\src\consumer_sim_launcher.py start
```

## Config file

Default config file path:

- `consumer-sim/config/consumer_instances.json`

Installed package default config path:

- Linux/macOS: `~/.config/opamp/consumer-sim/consumer_instances.json`
- Windows: `%APPDATA%\opamp\consumer-sim\consumer_instances.json`

Override via environment variable:

- `CONSUMER_SIM_CONFIG=/path/to/file.json`

The default `consumer-sim/config/consumer_instances.json` includes simulator instance definitions only.

## What `start` does

1. Reads the launch config (`instances` list).
1. Validates launch config against `consumer-sim/config/consumer_instances.schema.json`.
1. If schema validation fails, launcher exits immediately with a fatal message that includes config path, schema path, and validation issue locations.
1. Removes stale `OpAMPSupervisor.signal` files from each instance working directory.
1. Launches each consumer with:
   - configured consumer config path (`config_path`)
   - optional `agent_config_path`
   - command-line override flags from `overrides`
1. Logs each launch to console with instance name, PID, working directory, and full command.
1. Writes launcher state (including process IDs) to:
   - `consumer-sim/runtime/launcher_state.json` (or `state_file` from config)
   - installed package fallback: user state area under `opamp/consumer-sim/runtime/launcher_state.json`
1. Exits after all instances are launched.

## What `stop` does

1. Reads launcher state file.
1. Marks each simulator record in the launcher state file with status `shutdown`.
1. Simulators poll that process record every 30 seconds, mark themselves `shuttingdown`, then exit gracefully.
1. Waits up to 90 seconds for each simulator to exit gracefully.
1. If graceful stop fails or times out, escalates to brute-force termination.
1. Removes each stopped process record from the state file immediately.
1. Removes the state file once all processes have stopped.

During stop, console emphasis markers are used:
- `----- ... -----` when a simulator is observed changing to `shuttingdown`
- `====== ... ======` when a simulator process is no longer detected

## Config schema (summary)

Top-level:

- `state_file` (optional string path)
- `instances` (required array)

Each instance:

- `name` (required)
- `entrypoint` (optional: `simulator`; default `simulator`)
- `command` (optional custom command string or argv list; overrides `entrypoint`, but must launch simulator client)
- `config_path` (required)
- `agent_config_path` (optional)
- `overrides` (optional key/value map converted to CLI flags)
- `env` (optional environment variable map)
- `working_dir` (optional)

## Simulator Client Behavior

The simulator is a concrete `service_type` that replays scripted actions for each
incoming `ServerToAgent` request type.

- Set `consumer.service_type` to `simulator`.
- Set `consumer.simulator_responses_path` to a JSON file.
- Each request type maps to a non-empty list of actions.
- Action lists cycle: once the end of a list is reached, the simulator returns to the first entry.
- Ready-to-run config: `consumer/opamp-simulator.json`

Simulator identity/version overrides can be passed through `--agent-additional-params`
as a single JSON object string:

```bash
--agent-additional-params '{"service_instance_uid":"sim-01","client_version":"1.2.3","config_version":"cfg-009"}'
```

Supported JSON keys:
- `service_instance_uid` (alias: `service_instance_id`) -> reported as `service.instance.id`
- `client_version` -> reported as `service.version`
- `config_version` -> reported as non-identifying attribute `config.version`

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

Supported actions:
- `accept` (run default handler behavior)
- `ignore` (skip handling)
- `error` (raise a simulated `AgentException`; optional `message`)

Example simulator responses file:

```json
{
  "responses": {
    "command": ["ignore", "accept"],
    "remote_config": [
      "accept",
      {
        "action": "error",
        "message": "simulated remote config rejection"
      }
    ],
    "*": ["accept"]
  }
}
```
