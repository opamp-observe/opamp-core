# Full Multi-Agent Demo

This demo runs five OpAMP consumers against one provider:

| Agent | Consumer mode | Active config | Replacement config |
|---|---|---|---|
| Fluent Bit | Supervisor | `active/fluent-bit.yaml` | `replacements/fluent-bit.yaml` |
| Fluentd | Supervisor | `active/fluentd.conf` | `replacements/fluentd.conf` |
| Vector | Observer | `active/vector.yaml` | `replacements/vector.yaml` |
| Elastic Agent | Observer | `active/elastic-agent.yml` | `replacements/elastic-agent.yml` |
| Elastic Heartbeat | Observer | `active/heartbeat.yml` | `replacements/heartbeat.yml` |

Fluent Bit and Vector connect to the provider over the OpAMP WebSocket transport. Fluentd, Elastic Agent, and Elastic Heartbeat use the OpAMP HTTP transport.

The provider config in `provider/opamp-provider-full-demo.json` enables remote config, effective config reporting, and the embedded Config Catalog. The catalog scans `active/`, `replacements/`, and `consumers/`, so the files are visible in the server UI at `/catalog`.

For a presentation-ready explanation with diagrams, see `presentation-overview.md`.

## Start

Prepare a demo shell with the expected local agent tools on `PATH`:

```cmd
cmd /k "call docs\full-demo\use-demo-agent-paths.cmd && powershell"
```

Run the remaining PowerShell commands from that inherited shell.

Start the provider with the full-demo provider config:

```powershell
$repo = "D:\dev\opamp2"
$env:PYTHONPATH = "$repo\provider\src;$repo\config-service\src;$repo\catalog-service\src;$env:PYTHONPATH"
$env:OPAMP_CONFIG_PATH = "$repo\docs\full-demo\provider\opamp-provider-full-demo.json"
python -m opamp_provider.server --config-path $env:OPAMP_CONFIG_PATH --host 127.0.0.1 --port 8080
```

Start the Logstash container and all five consumers from the CLI demo profile:

```powershell
$env:OPAMP_DEMO = "true"
opamp-cli start "Demo setup (Full multi-agent remote config)"
```

Start the observer-mode agents before or immediately after starting the consumers:

```powershell
powershell -ExecutionPolicy Bypass -File docs\full-demo\start-observed-agents.ps1
```

The helper script accepts command names from `PATH` or explicit executable paths. By default it looks for these commands on `PATH`:

- `vector`
- `elastic-agent`
- `heartbeat`

Use `use-demo-agent-paths.cmd` for the default `D:\dev-tools` layout, or set `PATH` yourself if your local tool layout differs. The script also auto-checks common Vector locations, including `D:\dev-tools\vector\bin\vector.exe`.

For Vector specifically, you can also set one of these before running the script:

```powershell
$env:OPAMP_VECTOR_EXECUTABLE_PATH = "D:\dev-tools\vector\bin\vector.exe"
$env:OPAMP_VECTOR_HOME = "D:\dev-tools\vector\bin"
```

If your Vector install lives somewhere else permanently, edit `$VectorCandidatePaths` in `docs/full-demo/start-observed-agents.ps1`.

You can also pass absolute paths directly:

```powershell
powershell -ExecutionPolicy Bypass -File docs\full-demo\start-observed-agents.ps1 `
  -VectorExe "D:\dev-tools\vector\bin\vector.exe" `
  -ElasticAgentExe "D:\dev-tools\elastic-agent\elastic-agent-9.5.0-windows-x86_64\elastic-agent.exe" `
  -HeartbeatExe "D:\dev-tools\elastic-heartbeat\heartbeat-9.5.3-windows-x86_64\heartbeat.exe"
```

## Remote Config Demo

Open `http://127.0.0.1:8080/ui`, select a connected client, choose `Select Configs`, and pick the matching file from `docs/full-demo/replacements`. The replacement files keep the same `service_instance_id` values and change output paths or polling/logging behavior so the deployment is easy to spot.

## Stop

```powershell
opamp-cli stop "Demo setup (Full multi-agent remote config)"
powershell -ExecutionPolicy Bypass -File docs\full-demo\stop-observed-agents.ps1
```

The Logstash container writes demo events under `docs/full-demo/out/logstash`.
