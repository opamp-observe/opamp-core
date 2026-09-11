# Vector Consumer Plugin

The Vector plugin lets `opamp-consumer` supervise a Vector process and report it through OpAMP.

## Consumer Configuration

```json
{
  "consumer": {
    "server_url": "http://localhost:8080",
    "transport": "http",
    "agent_config_path": "docs/vector-self-monitor/vector-self-monitor.yaml",
    "agent_additional_params": [],
    "heartbeat_frequency": 5,
    "service_type": "vector",
    "service_name": "Vector",
    "service_namespace": "VectorNS"
  }
}
```

The plugin defaults to `vector` from `PATH`, `127.0.0.1:8686` for the health API, and a 5 second status timeout. It also derives the Vector status port from `api.address` in the Vector YAML file. Add a `consumer.vector` block only when you need to override those plugin defaults.

## Runtime Behavior

- Starts Vector with `vector --config <agent_config_path>`.
- Polls Vector health at `/health`.
- Reports service type `Vector` to the provider UI.
- Supports remote-config and effective-config capabilities through the shared consumer file handling.
