# Implementation Contract

A consumer plugin is small at the loading boundary but usually not small in
behavior. The loading boundary only asks for a callable. The runtime behavior
comes from the concrete client class you build behind that callable.

Most real plugins should subclass `AbstractOpAMPClient`.

## The ABCs

Here "ABCs" means the abstract base classes and interfaces that define the
shape of a client implementation.

The important types are:

- `OpAMPClientInterface`: the formal interface for send, lifecycle, config,
  health, capability, and shutdown behavior.
- `AbstractOpAMPClient`: the shared base implementation used by concrete
  clients.
- `ClientRuntimeMixin`: delegates process lifecycle work to supervisor or
  observer strategies.
- `ClientTransportAuthorizationMixin`: owns HTTP/WebSocket send behavior and
  outbound authorization.
- `ServerMessageHandlingMixin`: owns server-to-agent message handling.

Read the existing [consumer mixins guide](../consumer_mixins.md) before adding
a non-trivial plugin. It explains how method resolution works and why behavior
is split this way.

## What AbstractOpAMPClient Gives You

`AbstractOpAMPClient` handles most of the OpAMP client plumbing:

- runtime data initialization
- instance UID handling
- full update controller setup
- common agent description fields
- custom handler registry setup
- remote config status tracking
- capability filtering
- shared send/reply behavior via mixins

Your plugin should only override the pieces that are genuinely specific to the
agent you are integrating.

## Methods A Plugin Usually Implements

At minimum, a concrete client normally provides:

```python
class MyAgentOpAMPClient(AbstractOpAMPClient):
    _runtime_agent_command = "my-agent"
    _runtime_config_flag = "--config"
    _heartbeat_paths = ("/health",)
    _value_agent_type = "MyAgent"
    SUPPORTED_AGENT_CAPABILITY_NAMES = (
        *consumer_config.MANDATORY_AGENT_CAPABILITY_NAMES,
        "ReportsHeartbeat",
    )

    def get_custom_handler_folder(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent / "custom_handlers"

    def get_config_metadata(self) -> ConfigMetadata:
        return ConfigMetadata()

    def get_configuration_files(self) -> list[str]:
        return [self.config.agent_config_path]
```

Depending on the agent, you may also override:

- `poll_local_status_with_codes(...)` when the health endpoint is not a simple
  HTTP path list.
- `add_agent_version(...)` when version discovery needs a special endpoint or
  command.
- `get_agent_description(...)` when the agent has richer identity metadata.
- `check_hot_deploy()` and `hot_reload()` when remote config can be applied
  without a process restart.
- `write_config_file(...)` when config delivery needs special file placement
  or validation.

Fluentd and Elastic Agent are useful examples because they override more of
the default behavior than Fluent Bit. Elastic Heartbeat is the reference
example for Elastic Beat-style plugins that launch a Beat process, parse Beat
YAML for HTTP monitoring settings, and use Logstash output preflight checks.

## Supervisor Mode

Supervisor mode is the default lifecycle strategy. In supervisor mode, the
consumer launches and manages the agent process.

The shared supervisor strategy builds a command from:

- `_runtime_agent_command`
- `consumer.agent_additional_params`
- `check_hot_deploy()`
- `_runtime_config_flag`
- `consumer.agent_config_path`

So a typical launch command becomes:

```text
my-agent <additional params> <hot deploy flag> --config <agent config path>
```

Use supervisor mode when the consumer owns the agent process lifecycle. This is
the natural fit for local demos, deployment containers, and service units where
the consumer is meant to start the managed agent.

Configuration:

```json
{
  "consumer": {
    "processTracking": "Supervisor",
    "agent_config_path": "./my-agent.yml",
    "agent_additional_params": []
  }
}
```

## Observer Mode

Observer mode attaches to an externally managed process. The consumer does not
launch the agent itself. Instead, it uses `consumer.processDetectionRegex` to
find a matching process, records the PID, and then continues with OpAMP
communication and heartbeat polling.

Configuration:

```json
{
  "consumer": {
    "processTracking": "Observer",
    "processDetectionRegex": "my-agent.*--config.*my-agent.yml"
  }
}
```

Use observer mode when something else owns the process:

- a system service manager
- a container runtime
- a manually started agent
- an agent with its own daemon/supervisor model

Observer mode still needs the agent's health/status endpoint to be reachable,
because heartbeats and health reporting are independent of process launch.

## When To Override Lifecycle Directly

Most plugins should let `ClientRuntimeMixin` choose supervisor or observer.
That keeps `processTracking` behavior consistent across plugins.

Override lifecycle methods directly only when the agent cannot fit the common
command-and-config-file model. Elastic Agent is the example: it has its own CLI
daemon/status behavior, so `ElasticAgentOpAMPClient` delegates to a specialized
`ElasticAgentCliLifecycle`. Elastic Heartbeat shows the lighter Beat pattern for
a foreground `<beat> -e -c <config>` process.

If you override lifecycle directly, document the reason in the plugin docs and
add tests for both launch and shutdown behavior.

## Plugin Entrypoint Shape

The plugin entry point should be a zero-argument callable. In most plugins,
`main()` should follow the shared bootstrap pattern instead of inventing a new
argument/config loader:

```python
CONFIG = consumer_config.CONFIG


def main() -> None:
    parser = build_common_cli_parser()
    args = parser.parse_args()
    config = load_config_from_cli_args(args)
    consumer_config.set_config(config)
    logger = configure_logging_for_config(config)
    consumer_config_path = log_runtime_config_path(
        logger=logger,
        runtime_name="consumer-my-agent",
        config_path=getattr(args, "config_path", None),
    )
    log_consumer_startup_banner(
        logger=logger,
        config=config,
        runtime_name="consumer-my-agent",
        consumer_config_path=consumer_config_path,
    )
```

The unified router may inject the already loaded config into a module-level
`CONFIG` variable before it calls `main()`. Keeping that variable available
makes config-driven routing and tests easier.

If the plugin can use the default Fluent Bit-style flow, prefer
`run_default_client_main(...)`. If it needs custom startup work, keep that work
after the shared parser/config/logging/banner steps so behavior stays
consistent across plugins.

## Startup Banner

Every plugin startup path should call:

```python
log_consumer_startup_banner(
    logger=logger,
    config=config,
    runtime_name="consumer-my-agent",
    consumer_config_path=consumer_config_path,
)
```

The shared banner lives in `consumer/src/opamp_consumer/startup_banner/`.
If you need to add another startup-wide banner line, add it there rather than
copying new logging into every plugin.

