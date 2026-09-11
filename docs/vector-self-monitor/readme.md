# Configuring Vector Self-Monitoring

This folder mirrors the Fluent Bit self-monitoring example for Vector.

Vector exposes its own runtime metrics with the `internal_metrics` source. The demo converts those metrics to log events with `metric_to_log`, then sends the JSON events to both the console and a file sink.

## Files

- `vector-self-monitor.yaml` is the local demo configuration.
- `vector-self-monitor.container.yaml` is the same pipeline with container-safe paths for the E2E test.

## Run Locally

The Windows Vector binary is expected at `D:\dev-tools\vector\bin\vector.exe`.

```powershell
New-Item -ItemType Directory -Force docs/vector-self-monitor/vector-data
D:\dev-tools\vector\bin\vector.exe validate --no-environment docs/vector-self-monitor/vector-self-monitor.yaml
D:\dev-tools\vector\bin\vector.exe --config docs/vector-self-monitor/vector-self-monitor.yaml
```

Successful startup writes Vector internal metric events to standard output and to:

```text
docs/vector-self-monitor/vector-self-monitor.log
```

The OpAMP Vector consumer plugin also reads the top-level `api.address` setting so it can poll Vector health on `http://127.0.0.1:8686/health`.

References:

- Vector internal metrics source: https://vector.dev/docs/reference/configuration/sources/internal_metrics/
- Vector metric-to-log transform: https://vector.dev/docs/reference/configuration/transforms/metric_to_log/
- Vector console sink: https://vector.dev/docs/reference/configuration/sinks/console/
- Vector file sink: https://vector.dev/docs/reference/configuration/sinks/file/
- Vector API configuration: https://vector.dev/docs/reference/configuration/api/
