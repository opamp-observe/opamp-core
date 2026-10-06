# Elastic Agent Consumer Configuration

This page covers configuration that is specific to the `elastic_agent` consumer plugin.
Shared consumer keys are documented in [consumer/README.md](../../README.md).
For the built-in implementation capability matrix, see
[docs/consumer_implementations.md](../../../docs/consumer_implementations.md).

## Plugin Identity

Built-in plugin key:

- `consumer.service_type`: `elastic_agent`

Built-in entry point:

```json
{
  "service_type": "elastic_agent",
  "entry_point": "opamp_consumer.elastic_agent.client:main",
  "enabled": true
}
```

Installed command:

```bash
opamp-consumer-elastic-agent --config-path ./opamp.json
```

Unified command:

```bash
opamp-consumer --config-path ./opamp.json
```

## Consumer Keys

| Key | Required | Notes |
|---|---:|---|
| `consumer.agent_config_path` | Yes | Elastic Agent YAML passed to `elastic-agent run -c`. |
| `consumer.agent_additional_params` | No | Extra args appended to the Elastic Agent run command. |
| `consumer.elastic_agent.executable_path` | No | Path or PATH-resolved command for `elastic-agent`. Environment override: `OPAMP_ELASTIC_AGENT_EXECUTABLE_PATH`. |
| `consumer.elastic_agent.home_path` | No | Working directory for Elastic Agent CLI calls. Environment override: `OPAMP_ELASTIC_AGENT_HOME_PATH`. |
| `consumer.elastic_agent.api_host` | No | Host/address for Elastic Agent monitoring API. Environment override: `OPAMP_ELASTIC_AGENT_API_HOST`. |
| `consumer.elastic_agent.api_port` | No | Monitoring API port and `client_status_port`. Environment override: `OPAMP_ELASTIC_AGENT_API_PORT`. |
| `consumer.elastic_agent.api_failon` | No | `failon` query value for `/liveness`: `heartbeat`, `failed`, or `degraded`. Environment override: `OPAMP_ELASTIC_AGENT_API_FAILON`. |
| `consumer.elastic_agent.status_timeout_seconds` | No | Timeout for Elastic Agent CLI status and monitoring API calls. |
| `consumer.processDetectionRegex` | Recommended | Used to discover an existing foreground `elastic-agent run` process when needed. |
| `consumer.agent_capabilities` | No | Supports `AcceptsRemoteConfig`, `ReportsEffectiveConfig`, and `ReportsHeartbeat` in addition to mandatory capabilities. |

## Required Elastic Agent Monitoring Config

The Elastic Agent YAML must enable the local monitoring HTTP API:

```yaml
agent.monitoring:
  enabled: true
  logs: true
  metrics: true
  use_output: default
  http:
    enabled: true
    host: localhost
    port: 6791
```

## Runtime Behavior

- Start launches `elastic-agent run -c <consumer.agent_config_path>`.
- Restart calls `elastic-agent restart`; if that cannot restart the foreground
  development process, the plugin falls back to stop/start using the tracked PID.
- Stop terminates the tracked foreground Elastic Agent process.
- Status combines `elastic-agent status --output json` with
  `http://<api_host>:<api_port>/liveness?failon=<api_failon>`.

When the Agent YAML contains Logstash outputs, launch preflights those endpoints
with a TCP connection and logs reachable/unreachable status before starting Agent.

## Logstash Demo

Plugin-driven demo config:

- [opamp-consumer-elastic-agent-logstash-plugin.json](../../../tests/logstash/opamp-consumer-elastic-agent-logstash-plugin.json)
- [elastic-agent.yml](../../../tests/logstash/elastic-agent.yml)

The sample `elastic-agent.yml` uses Elastic Agent's env provider for the Logstash
host:

```yaml
outputs:
  default:
    type: logstash
    hosts: ["${env.OPAMP_LOGSTASH_HOST|'127.0.0.1'}:5044"]
```

If Podman publishes `5044` but Windows cannot connect to `127.0.0.1:5044`, set
`OPAMP_LOGSTASH_HOST` to a host address that can reach the Podman machine before
starting the consumer.

Useful Windows checks:

```bat
podman port opamp-logstash
podman machine inspect podman-machine-default
powershell -NoProfile -ExecutionPolicy Bypass -Command "Test-NetConnection 127.0.0.1 -Port 5044"
```

Helper script:

```bat
call D:\dev\opamp\tests\logstash\set-podman-logstash-host.bat
powershell -NoProfile -ExecutionPolicy Bypass -Command "Test-NetConnection $env:OPAMP_LOGSTASH_HOST -Port 5044"
```

Equivalent inline `cmd.exe` command:

```bat
for /f "tokens=4" %i in ('podman machine ssh podman-machine-default "ip -4 -o addr show eth0"') do for /f "tokens=1 delims=/" %j in ("%i") do set OPAMP_LOGSTASH_HOST=%j
```

Start through the dev CLI:

```text
OPAMP_DEMO=true opamp-cli demo "Elastic Agent self-monitoring to Logstash"
```

Manual script order:

```bat
D:\dev\opamp\tests\logstash\run-logstash.bat
D:\dev\opamp\tests\logstash\run-elastic-agent.bat
D:\dev\opamp\.venv\Scripts\opamp-consumer-elastic-agent.exe --config-path D:\dev\opamp\tests\logstash\opamp-consumer-elastic-agent-observer.json
```
