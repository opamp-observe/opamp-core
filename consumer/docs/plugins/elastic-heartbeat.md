# Elastic Heartbeat Consumer Configuration

This page covers configuration that is specific to the `elastic_heartbeat`
consumer plugin. Shared consumer keys are documented in
[consumer/README.md](../../README.md).
For the built-in implementation capability matrix, see
[docs/consumer_implementations.md](../../../docs/consumer_implementations.md).

## Plugin Identity

Built-in plugin key:

- `consumer.service_type`: `elastic_heartbeat`

Built-in entry point:

```json
{
  "service_type": "elastic_heartbeat",
  "entry_point": "opamp_consumer.elastic_heartbeat.client:main",
  "enabled": true
}
```

Installed commands:

```bash
opamp-consumer-elastic-heartbeat --config-path ./opamp.json --agent-config-path ./heartbeat.yml
opamp-consumer --config-path ./opamp.json --agent-config-path ./heartbeat.yml
```

## Consumer Keys

| Key | Required | Notes |
|---|---:|---|
| `consumer.agent_config_path` | Yes | Heartbeat YAML passed to `heartbeat -e -c`. |
| `consumer.agent_additional_params` | No | Extra args appended to the Heartbeat run command. |
| `consumer.elastic_heartbeat.executable_path` | No | Path or PATH-resolved command for `heartbeat`. Environment override: `OPAMP_ELASTIC_HEARTBEAT_EXECUTABLE_PATH`. |
| `consumer.elastic_heartbeat.home_path` | No | Working directory for Heartbeat CLI calls. Environment override: `OPAMP_ELASTIC_HEARTBEAT_HOME_PATH`. |
| `consumer.elastic_heartbeat.api_host` | No | Host/address for the Heartbeat monitoring API. Environment override: `OPAMP_ELASTIC_HEARTBEAT_API_HOST`. |
| `consumer.elastic_heartbeat.api_port` | No | Monitoring API port and `client_status_port`. Environment override: `OPAMP_ELASTIC_HEARTBEAT_API_PORT`. |
| `consumer.elastic_heartbeat.status_timeout_seconds` | No | Timeout for Heartbeat config tests and monitoring API calls. |
| `consumer.processTracking` | Recommended | Use `Supervisor` when the consumer should launch Heartbeat. Use `Observer` only when Heartbeat is already running. |
| `consumer.processDetectionRegex` | Observer only | Regex used to discover an existing Heartbeat process. |
| `consumer.agent_capabilities` | No | Supports `AcceptsRemoteConfig`, `ReportsEffectiveConfig`, and `ReportsHeartbeat` in addition to mandatory capabilities. |

## Required Heartbeat Monitoring Config

The Heartbeat YAML must enable the local monitoring HTTP API:

```yaml
http.enabled: true
http.host: 127.0.0.1
http.port: 5066
```

The plugin reads this API at `http://<api_host>:<api_port>/` and `/stats` for
status, health, and version information.

## Demo Config

The supervisor demo config monitors localhost and `blog.mp3monster.org` every 5
seconds:

```yaml
heartbeat.monitors:
  - type: http
    name: localhost
    urls: ["http://localhost"]
    schedule: "@every 5s"

  - type: http
    name: blog.mp3monster.org
    urls: ["https://blog.mp3monster.org"]
    schedule: "@every 5s"
```

Heartbeat sends events to Logstash. The local Logstash demo writes a JSON Lines
test evidence file at `tests/logstash/out/heartbeat-events.jsonl`.

Demo files:

- [opamp-consumer-elastic-heartbeat-logstash-plugin.json](../../../tests/logstash/opamp-consumer-elastic-heartbeat-logstash-plugin.json)
- [heartbeat.yml](../../../tests/logstash/heartbeat.yml)
- [logstash-heartbeat.container.conf](../../../tests/logstash/logstash-heartbeat.container.conf)

Start through the dev CLI:

```text
OPAMP_DEMO=true opamp-cli demo "Elastic Heartbeat supervisor to Logstash"
```

## Runtime Behavior

- Start launches `heartbeat -e -c <consumer.agent_config_path>`.
- Restart stops the tracked process, then starts Heartbeat again.
- Stop terminates the tracked foreground Heartbeat process.
- Config test runs `heartbeat test config -c <consumer.agent_config_path>`.
- Status reads the Heartbeat HTTP API and maps Beat health into OpAMP health.

When the Heartbeat YAML contains `output.logstash.hosts`, launch preflights
those endpoints with a TCP connection and logs reachable/unreachable status
before starting Heartbeat.

## Reference Pattern For Other Beats

Use `opamp_consumer.elastic_heartbeat.client` as the reference when adding
Filebeat, Metricbeat, Auditbeat, or other Elastic Beat clients:

- Keep Beat-specific defaults in constants near the top of the plugin module.
- Add one `process_consumer_config(context)` hook for the plugin-specific config
  block under `consumer.<service_type>`.
- Parse the Beat YAML for `http.host`, `http.port`, and `output.logstash.hosts`
  so runtime polling and preflight checks follow the actual agent config.
- Subclass `_BaseClientProcessLifecycle` for `launch_agent_process`,
  `terminate_agent_process`, `restart_agent_process`, and `test_config`.
- Subclass `AbstractOpAMPClient` for capabilities, health mapping, agent
  description, and version discovery.
- Register the plugin in `BUILTIN_CONSUMER_PLUGINS`, `pyproject.toml` console
  scripts, and `opamp_consumer.plugins` entry points.

Container regression coverage is in
[tests/test-containers/opamp-consumer-deployment](../../../tests/test-containers/opamp-consumer-deployment/README.md)
and [consumer-plugin-startup](../../../tests/test-containers/consumer-plugin-startup/README.md).
