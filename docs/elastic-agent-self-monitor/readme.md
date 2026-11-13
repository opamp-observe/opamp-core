# Configuring Elastic Agent Self Monitoring

The OpAMP protocol supports sharing observability configuration with a connected client so the client can send its own logs and metrics to a backend destination.

The files in this folder illustrate that idea for Elastic Agent. The sample `elastic-agent.yml` enables Elastic Agent self monitoring and sends the agent's own logs and metrics to Logstash over the Beats input on port `5044`. Logstash then writes the received events to a local JSON lines file under `out/`.

## Folder Contents

- `elastic-agent.yml` configures Elastic Agent in local management mode, enables self monitoring, and routes monitoring signals to Logstash.
- `logstash.conf` is the host-side Logstash pipeline used by the run scripts.
- `logstash.container.conf` is the same pipeline with the output path already written for the container filesystem.
- `run-logstash.bat` and `run-logstash.sh` start Logstash in Docker or Podman.
- `run-elastic-agent.bat` and `run-elastic-agent.sh` start Elastic Agent with the sample configuration.
- `out/` is created at runtime and receives Logstash output plus Elastic Agent file logs.

## Running The Example

Start Logstash first:

```bash
./run-logstash.sh
```

or, with Podman:

```bash
./run-logstash.sh podman
```

Then start Elastic Agent:

```bash
ELASTIC_AGENT_HOME=/path/to/elastic-agent ./run-elastic-agent.sh
```

On Windows, use the matching `.bat` scripts instead.

By default, Elastic Agent sends self-monitoring events to `127.0.0.1:5044`. Set `OPAMP_LOGSTASH_HOST` if Logstash is reachable through a different host name or address.
