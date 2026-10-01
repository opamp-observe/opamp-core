# OpAMP Consumer Deployment Test Container

This container is intended for testing OpAMP consumer deployments from a wheel.
It installs Fluent Bit, Fluentd, or Elastic Heartbeat itself and can stage
Elastic Agent, Vector, or simulator deployments when the runtime image already
contains the required executable.
It can also optionally download ELK stack component archives and a GitHub-hosted log generator.

## What It Does

At container startup it:

1. Reads a simple `KEY=VALUE` config file.
2. Unpacks the provided consumer wheel into `/work/runtime/wheel-unpacked`.
3. Installs the wheel with dev extras (`[dev]`) and pulls dependencies.
4. Installs Fluent Bit, Fluentd, or Elastic Heartbeat for the configured version,
   or uses a preinstalled executable when `SKIP_AGENT_INSTALL=true`.
5. Stages agent and consumer config files into `/work/runtime/config` so they are writable/modifiable in-container.
6. Rewrites consumer config runtime paths (`consumer.agent_config_path`) plus service type and server URL/transport.
7. Optionally downloads ELK component archives into `/work/runtime/downloads/elk`.
8. Optionally clones a log generator repository (and optional release archive) into `/work/runtime/downloads/log-generator`.
9. Runs either:
   - `opamp-consumer` (default), or
   - agent only (`AGENT_ONLY=true`).

## Config File Format

Use plain key/value lines:

```env
KEY=value
```

- Blank lines and lines starting with `#` are ignored.
- The default config file path in the container is `/config/test-container.env`.

## Keys

| Key | Required | Description | Example |
|---|---|---|---|
| `DEPLOYMENT_TYPE` | Yes | Consumer type to launch. Allowed: `fluentbit`, `fluentd`, `elastic_agent`, `elastic_heartbeat`, `vector`, `simulator`. | `fluentbit` |
| `AGENT_VERSION` | Yes | Agent version. Used by the built-in Fluent Bit, Fluentd, and Elastic Heartbeat installers. | `5.0.3` |
| `WHEEL_PATH` | Yes | Path (inside container) to a consumer wheel, a directory containing wheels, or a glob expression. Directory/glob values use the newest matching wheel. | `/host-assets/dist/consumer` |
| `AGENT_CONFIG_PATH` | No | Path (inside container) to host agent config file. If empty, a default dummy input + file output config is generated. | `/host-assets/consumer/fluent-bit.yaml` |
| `CONSUMER_CONFIG_PATH` | No | Path (inside container) to host consumer config JSON. If empty, a minimal config is generated. | `/host-assets/tests/opamp.json` |
| `CONSUMER_TRANSPORT` | No | Transport mode written into consumer config. Allowed: `http`, `websocket`. Default: `http`. | `http` |
| `OPAMP_HTTP_URL` | No | Provider URL used when transport is `http` (unless `SERVER_URL` is set). | `http://host.docker.internal:8080` |
| `OPAMP_WEBSOCKET_URL` | No | Provider URL used when transport is `websocket` (unless `SERVER_URL` is set). | `ws://host.docker.internal:4320` |
| `SERVER_URL` | No | Explicit server URL override for consumer config. | `http://host.docker.internal:8080` |
| `AGENT_ONLY` | No | If `true`, run the selected agent without `opamp-consumer`. Default: `false`. | `false` |
| `SMOKE_ONLY` | No | If `true`, install the consumer wheel, verify plugin entry points, stage the selected agent/consumer config, then exit before launching long-running processes. Default: `false`. | `true` |
| `SKIP_AGENT_INSTALL` | No | If `true`, skip agent installation. Intended for smoke-only regression runs that validate consumer packaging and config staging without external agent downloads. Default: `false`. | `true` |
| `HOSTNAME_OVERRIDE` | No | Optional hostname label injected into staged agent config as `service_instance_id` comment. | `consumer-a-01` |
| `SERVICE_NAME_OVERRIDE` | No | Optional override for `consumer.service_name`. | `Fluentbit` |
| `SERVICE_NAMESPACE_OVERRIDE` | No | Optional override for `consumer.service_namespace`. | `ContainerTests` |
| `SERVICE_INSTANCE_ID_OVERRIDE` | No | Optional stable override for `consumer.service_instance_id`. | `consumer-a-01` |
| `SIMULATOR_RESPONSES_PATH` | No | Scripted response JSON used by simulator deployments. Defaults to the bundled accept-all responses. | `/config/simulator-responses.json` |
| `APP_ENABLE_DEV_FEATURES` | No | Enables development-only consumer modes such as simulator. | `true` |
| `OUTPUT_HOST_DIR` | No | Path (inside container) where log/output files are written. Default: `/host-output`. | `/host-output` |
| `FLUENTBIT_DOWNLOAD_URL` | No | Explicit Fluent Bit tarball URL override if auto asset discovery is not sufficient. | `https://.../fluent-bit-<ver>-linux-amd64.tar.gz` |
| `HEARTBEAT_DOWNLOAD_URL` | No | Explicit Heartbeat tarball URL override. | `https://artifacts.elastic.co/downloads/beats/heartbeat/heartbeat-9.3.3-linux-x86_64.tar.gz` |
| `DOWNLOAD_ELK_COMPONENTS` | No | If `true`, download ELK component archives into runtime downloads folder. Default: `false`. | `true` |
| `ELK_VERSION` | No | Version used for ELK artifact URLs. Defaults to `AGENT_VERSION` when unset. | `9.3.3` |
| `ELK_COMPONENTS` | No | Comma-separated components to download. Supported: `elasticsearch`, `kibana`, `logstash`, `elastic-agent`, `fleet-server`, `heartbeat`. Default: `elasticsearch,kibana,logstash`. | `elasticsearch,kibana,logstash,elastic-agent` |
| `EXTRACT_ELK_COMPONENTS` | No | If `true`, extract each downloaded ELK tarball under `/work/runtime/downloads/elk`. Default: `false`. | `true` |
| `ELASTICSEARCH_DOWNLOAD_URL` | No | Optional explicit Elasticsearch artifact URL override. | `https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-9.3.3-linux-x86_64.tar.gz` |
| `KIBANA_DOWNLOAD_URL` | No | Optional explicit Kibana artifact URL override. | `https://artifacts.elastic.co/downloads/kibana/kibana-9.3.3-linux-x86_64.tar.gz` |
| `LOGSTASH_DOWNLOAD_URL` | No | Optional explicit Logstash artifact URL override. | `https://artifacts.elastic.co/downloads/logstash/logstash-9.3.3-linux-x86_64.tar.gz` |
| `ELASTIC_AGENT_DOWNLOAD_URL` | No | Optional explicit Elastic Agent artifact URL override. | `https://artifacts.elastic.co/downloads/beats/elastic-agent/elastic-agent-9.3.3-linux-x86_64.tar.gz` |
| `FLEET_SERVER_DOWNLOAD_URL` | No | Optional explicit Fleet Server artifact URL override. | `https://artifacts.elastic.co/downloads/fleet-server/fleet-server-9.3.3-linux-x86_64.tar.gz` |
| `DOWNLOAD_LOG_GENERATOR` | No | If `true`, download a log-generator GitHub repo into runtime downloads. Default: `false`. | `true` |
| `LOG_GENERATOR_GITHUB_REPO` | No | Git repository URL for log generator source. Defaults to `https://github.com/mingrammer/flog.git`. | `https://github.com/mingrammer/flog.git` |
| `LOG_GENERATOR_GIT_REF` | No | Optional branch/tag to checkout when cloning the log-generator repo. | `v0.4.4` |
| `LOG_GENERATOR_RELEASE_URL` | No | Optional log-generator release tarball URL to download and extract. | `https://github.com/mingrammer/flog/releases/download/v0.4.4/flog_0.4.4_linux_amd64.tar.gz` |

## Build

From repo root:

```bash
docker build \
  -f tests/test-containers/opamp-consumer-deployment/Dockerfile \
  -t opamp-consumer-deployment-test:latest \
  tests/test-containers/opamp-consumer-deployment
```

## Example Config

See:

- `tests/test-containers/opamp-consumer-deployment/examples/test-container.env`
- `tests/test-containers/opamp-consumer-deployment/examples/regression-fluentbit.env`
- `tests/test-containers/opamp-consumer-deployment/examples/regression-fluentd.env`
- `tests/test-containers/opamp-consumer-deployment/examples/regression-elastic-heartbeat.env`

## Run Example

This mounts:

- repo root as `/host-assets` (wheel and config source files)
- config file folder as `/config`
- host output folder as `/host-output`

```bash
mkdir -p ./tmp/test-container-output

docker run --rm -it \
  -v "$PWD:/host-assets" \
  -v "$PWD/tests/test-containers/opamp-consumer-deployment/examples:/config" \
  -v "$PWD/tmp/test-container-output:/host-output" \
  --add-host host.docker.internal:host-gateway \
  -e TEST_CONTAINER_CONFIG=/config/test-container.env \
  opamp-consumer-deployment-test:latest
```

## Regression Pack

The smoke-only Fluent Bit, Fluentd, and Elastic Heartbeat variants are included in the container
regression pack:

```bash
python tests/test-containers/run_regression_pack.py --only opamp-consumer-deployment-smoke
```

## Host Connectivity Notes

- `host.docker.internal` is used by default for both HTTP and WebSocket routes.
- `--add-host host.docker.internal:host-gateway` is included above for Linux Docker engines.
- Override with `OPAMP_HTTP_URL`, `OPAMP_WEBSOCKET_URL`, or `SERVER_URL` as needed.

## Runtime Output Locations

- Container-staged configs: `/work/runtime/config`
- Wheel unpack location: `/work/runtime/wheel-unpacked`
- Download cache: `/work/runtime/downloads`
- ELK downloads: `/work/runtime/downloads/elk`
- Log generator downloads: `/work/runtime/downloads/log-generator`
- Host-mounted outputs/logs: `OUTPUT_HOST_DIR` (default `/host-output`)
