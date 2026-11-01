# Fluent Bit 3.2.10 Schema Quick Reference

Generated from the local Fluent Bit 3.2.10 JSON schema only:
- `config-service\src\config_service\json-schemas\fluentbit-3.2.10-config-schema.json`

Scope:
1. Environment variable map definition for `env`
2. Upstream server groups for `upstream_servers`
3. Pipeline plugin definitions
4. Grouped by `inputs`, `filters`, and `outputs`
5. Includes mandatory flags, defaults, descriptions, and Fluent Bit documentation links
6. Excludes internal optional `_meta` comment metadata fields because they are not part of the Fluent Bit specification

## Jump Lists

- **Environment**: [`env`](#environment-env)
- **Upstream Servers**: [`upstream_servers`](#upstream-servers-upstream-servers)
- **Inputs**: [`collectd`](#inputs-collectd), [`cpu`](#inputs-cpu), [`disk`](#inputs-disk), [`docker-metrics`](#inputs-docker-metrics), [`docker_events`](#inputs-docker-events), [`dummy`](#inputs-dummy), [`ebpf`](#inputs-ebpf), [`elasticsearch`](#inputs-elasticsearch), [`exec`](#inputs-exec), [`exec_wasi`](#inputs-exec-wasi), [`fluentbit_metrics`](#inputs-fluentbit-metrics), [`forward`](#inputs-forward), [`head`](#inputs-head), [`health`](#inputs-health), [`http`](#inputs-http), [`kafka`](#inputs-kafka), [`kmsg`](#inputs-kmsg), [`kubernetes_events`](#inputs-kubernetes-events), [`mem`](#inputs-mem), [`mqtt`](#inputs-mqtt), [`netif`](#inputs-netif), [`nginx_metrics`](#inputs-nginx-metrics), [`node_exporter_metrics`](#inputs-node-exporter-metrics), [`opentelemetry`](#inputs-opentelemetry), [`podman_metrics`](#inputs-podman-metrics), [`proc`](#inputs-proc), [`process_exporter_metrics`](#inputs-process-exporter-metrics), [`prometheus_remote_write`](#inputs-prometheus-remote-write), [`prometheus_scrape`](#inputs-prometheus-scrape), [`random`](#inputs-random), [`serial`](#inputs-serial), [`splunk`](#inputs-splunk), [`statsd`](#inputs-statsd), [`stdin`](#inputs-stdin), [`syslog`](#inputs-syslog), [`systemd`](#inputs-systemd), [`tail`](#inputs-tail), [`tcp`](#inputs-tcp), [`thermal`](#inputs-thermal), [`udp`](#inputs-udp), [`windows_exporter_metrics`](#inputs-windows-exporter-metrics), [`winevtlog`](#inputs-winevtlog), [`winlog`](#inputs-winlog)
- **Filters**: [`aws`](#filters-aws), [`checklist`](#filters-checklist), [`ecs`](#filters-ecs), [`expect`](#filters-expect), [`geoip2`](#filters-geoip2), [`grep`](#filters-grep), [`kubernetes`](#filters-kubernetes), [`log_to_metrics`](#filters-log-to-metrics), [`lua`](#filters-lua), [`modify`](#filters-modify), [`multiline`](#filters-multiline), [`nest`](#filters-nest), [`nightfall`](#filters-nightfall), [`parser`](#filters-parser), [`record_modifier`](#filters-record-modifier), [`rewrite_tag`](#filters-rewrite-tag), [`stdout`](#filters-stdout), [`sysinfo`](#filters-sysinfo), [`tensorflow`](#filters-tensorflow), [`throttle`](#filters-throttle), [`type_converter`](#filters-type-converter), [`wasm`](#filters-wasm)
- **Outputs**: [`azure`](#outputs-azure), [`azure_blob`](#outputs-azure-blob), [`azure_kusto`](#outputs-azure-kusto), [`azure_logs_ingestion`](#outputs-azure-logs-ingestion), [`bigquery`](#outputs-bigquery), [`chronicle`](#outputs-chronicle), [`cloudwatch_logs`](#outputs-cloudwatch-logs), [`counter`](#outputs-counter), [`dash0`](#outputs-dash0), [`datadog`](#outputs-datadog), [`dynatrace`](#outputs-dynatrace), [`es`](#outputs-es), [`file`](#outputs-file), [`flowcounter`](#outputs-flowcounter), [`forward`](#outputs-forward), [`gelf`](#outputs-gelf), [`http`](#outputs-http), [`influxdb`](#outputs-influxdb), [`kafka`](#outputs-kafka), [`kafka-rest`](#outputs-kafka-rest), [`kinesis_firehose`](#outputs-kinesis-firehose), [`kinesis_streams`](#outputs-kinesis-streams), [`logdna`](#outputs-logdna), [`loki`](#outputs-loki), [`nats`](#outputs-nats), [`newrelic`](#outputs-newrelic), [`null`](#outputs-null), [`observe`](#outputs-observe), [`openobserve`](#outputs-openobserve), [`opensearch`](#outputs-opensearch), [`opentelemetry`](#outputs-opentelemetry), [`oracle_log_analytics`](#outputs-oracle-log-analytics), [`pgsql`](#outputs-pgsql), [`prometheus_exporter`](#outputs-prometheus-exporter), [`prometheus_remote_write`](#outputs-prometheus-remote-write), [`s3`](#outputs-s3), [`skywalking`](#outputs-skywalking), [`slack`](#outputs-slack), [`splunk`](#outputs-splunk), [`stackdriver`](#outputs-stackdriver), [`stdout`](#outputs-stdout), [`syslog`](#outputs-syslog), [`tcp`](#outputs-tcp), [`td`](#outputs-td), [`vivo_exporter`](#outputs-vivo-exporter), [`websocket`](#outputs-websocket)

<a id="environment-env"></a>
## Environment Variables

Quick reference for the optional Fluent Bit YAML `env` section.
Fluent Bit page: [Environment variables](https://docs.fluentbit.io/manual/3.2/administration/configuring-fluent-bit/yaml/environment-variables-section)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`env`](https://docs.fluentbit.io/manual/3.2/administration/configuring-fluent-bit/yaml/environment-variables-section) | No | `{}` | Object map of local environment variables available to this configuration file. |
| [`<ENV_VAR_NAME>`](https://docs.fluentbit.io/manual/3.2/administration/configuring-fluent-bit/yaml/environment-variables-section) | No |  | Variable key name. Use uppercase letters, digits, and `_`, and avoid spaces or punctuation. |
| [`<ENV_VAR_NAME>` value](https://docs.fluentbit.io/manual/3.2/administration/configuring-fluent-bit/yaml/environment-variables-section) | No |  | Variable value consumed with `${ENV_VAR_NAME}` in Fluent Bit configuration fields. |

<a id="upstream-servers-upstream-servers"></a>
## Upstream Servers

Quick reference for optional Fluent Bit YAML `upstream_servers` groups.
Fluent Bit page: [Upstream servers](https://docs.fluentbit.io/manual/3.2/administration/configuring-fluent-bit/yaml/upstream-servers-section)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`upstream_servers`](https://docs.fluentbit.io/manual/3.2/administration/configuring-fluent-bit/yaml/upstream-servers-section) | No | `[]` | List of upstream groups used by supporting output plugins for round-robin endpoint selection. |
| [`upstream_servers[].name`](https://docs.fluentbit.io/manual/3.2/administration/configuring-fluent-bit/yaml/upstream-servers-section) | Yes |  | Upstream group name. |
| [`upstream_servers[].nodes`](https://docs.fluentbit.io/manual/3.2/administration/configuring-fluent-bit/yaml/upstream-servers-section) | Yes |  | List of node endpoints in the group. |
| [`upstream_servers[].nodes[].name`](https://docs.fluentbit.io/manual/3.2/administration/configuring-fluent-bit/yaml/upstream-servers-section) | Yes |  | Node name. |
| [`upstream_servers[].nodes[].host`](https://docs.fluentbit.io/manual/3.2/administration/configuring-fluent-bit/yaml/upstream-servers-section) | Yes |  | Node host/IP endpoint. |
| [`upstream_servers[].nodes[].port`](https://docs.fluentbit.io/manual/3.2/administration/configuring-fluent-bit/yaml/upstream-servers-section) | Yes |  | Node TCP port. |
| [`upstream_servers[].nodes[].tls`](https://docs.fluentbit.io/manual/3.2/administration/configuring-fluent-bit/yaml/upstream-servers-section) | No |  | Enable TLS for this node connection. |
| [`upstream_servers[].nodes[].tls_verify`](https://docs.fluentbit.io/manual/3.2/administration/configuring-fluent-bit/yaml/upstream-servers-section) | No |  | Verify TLS certificate for this node. |
| [`upstream_servers[].nodes[].shared_key`](https://docs.fluentbit.io/manual/3.2/administration/configuring-fluent-bit/yaml/upstream-servers-section) | No |  | Shared key for secure node communication. |

## Inputs

[`collectd`](#inputs-collectd), [`cpu`](#inputs-cpu), [`disk`](#inputs-disk), [`docker-metrics`](#inputs-docker-metrics), [`docker_events`](#inputs-docker-events), [`dummy`](#inputs-dummy), [`ebpf`](#inputs-ebpf), [`elasticsearch`](#inputs-elasticsearch), [`exec`](#inputs-exec), [`exec_wasi`](#inputs-exec-wasi), [`fluentbit_metrics`](#inputs-fluentbit-metrics), [`forward`](#inputs-forward), [`head`](#inputs-head), [`health`](#inputs-health), [`http`](#inputs-http), [`kafka`](#inputs-kafka), [`kmsg`](#inputs-kmsg), [`kubernetes_events`](#inputs-kubernetes-events), [`mem`](#inputs-mem), [`mqtt`](#inputs-mqtt), [`netif`](#inputs-netif), [`nginx_metrics`](#inputs-nginx-metrics), [`node_exporter_metrics`](#inputs-node-exporter-metrics), [`opentelemetry`](#inputs-opentelemetry), [`podman_metrics`](#inputs-podman-metrics), [`proc`](#inputs-proc), [`process_exporter_metrics`](#inputs-process-exporter-metrics), [`prometheus_remote_write`](#inputs-prometheus-remote-write), [`prometheus_scrape`](#inputs-prometheus-scrape), [`random`](#inputs-random), [`serial`](#inputs-serial), [`splunk`](#inputs-splunk), [`statsd`](#inputs-statsd), [`stdin`](#inputs-stdin), [`syslog`](#inputs-syslog), [`systemd`](#inputs-systemd), [`tail`](#inputs-tail), [`tcp`](#inputs-tcp), [`thermal`](#inputs-thermal), [`udp`](#inputs-udp), [`windows_exporter_metrics`](#inputs-windows-exporter-metrics), [`winevtlog`](#inputs-winevtlog), [`winlog`](#inputs-winlog)

<a id="inputs-collectd"></a>
### `collectd`: Collectd
Fluent Bit page: [Collectd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/collectd#configuration-parameters-a-hrefconfig-idconfiga)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/collectd#configuration-parameters-a-hrefconfig-idconfiga) | Yes | `collectd` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/collectd#configuration-parameters-a-hrefconfig-idconfiga) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`listen`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/collectd#configuration-parameters-a-hrefconfig-idconfiga) | No | `0.0.0.0` | Set the address to listen to |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/collectd#configuration-parameters-a-hrefconfig-idconfiga) | No | `25826` | Set the port to listen to |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/collectd#configuration-parameters-a-hrefconfig-idconfiga) | No |  |  |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/collectd#configuration-parameters-a-hrefconfig-idconfiga) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |
| [`typesdb`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/collectd#configuration-parameters-a-hrefconfig-idconfiga) | No | `/usr/share/collectd/types.db` | Set the data specification file |

<a id="inputs-cpu"></a>
### `cpu`: CPU Log Based Metrics
Fluent Bit page: [CPU Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/cpu-metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/cpu-metrics#configuration-parameters) | Yes | `cpu` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/cpu-metrics#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/cpu-metrics#configuration-parameters) | No | `0` | Polling interval in nanoseconds |
| [`interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/cpu-metrics#configuration-parameters) | No | `1` | Polling interval in seconds |
| [`pid`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/cpu-metrics#configuration-parameters) | No |  | Specify the ID (PID) of a running process in the system. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/cpu-metrics#configuration-parameters) | No |  |  |

<a id="inputs-disk"></a>
### `disk`: Disk I/O Log Based Metrics
Fluent Bit page: [Disk I/O Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/disk-io-metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/disk-io-metrics#configuration-parameters) | Yes | `disk` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/disk-io-metrics#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`dev_name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/disk-io-metrics#configuration-parameters) | No | `all disks` | Device name to limit the target. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/disk-io-metrics#configuration-parameters) | No | `0` | Polling interval (nanosecond). |
| [`interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/disk-io-metrics#configuration-parameters) | No | `1` | Polling interval (seconds). |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/disk-io-metrics#configuration-parameters) | No |  |  |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/disk-io-metrics#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-docker-metrics"></a>
### `docker-metrics`: Docker Log Based Metrics
Fluent Bit page: [Docker Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-metrics#configuration-parameters) | Yes | `docker-metrics` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-metrics#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`exclude`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-metrics#configuration-parameters) | No |  | A space-separated list of containers to exclude |
| [`include`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-metrics#configuration-parameters) | No |  | A space-separated list of containers to include |
| [`interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-metrics#configuration-parameters) | No | `1` | Polling interval in seconds |
| [`path.containers`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-metrics#configuration-parameters) | No | `/var/lib/docker/containers` | Used to specify the container directory if Docker is configured with a custom "data-root" directory. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-metrics#configuration-parameters) | No |  |  |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-metrics#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-docker-events"></a>
### `docker_events`: Docker Events
Fluent Bit page: [Docker Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) | Yes | `docker_events` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`buffer_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) | No | `8192` | The size of the buffer used to read docker events (in bytes) |
| [`key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) | No | `message` | When a message is unstructured (no parser applied), it's appended as a string under the key name message. |
| [`parser`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) | No |  | Specify the name of a parser to interpret the entry as a structured message. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) | No |  |  |
| [`reconnect.retry_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) | No | `1` | The retrying interval. |
| [`reconnect.retry_limits`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) | No | `5` | The maximum number of retries allowed. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |
| [`unix_path`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) | No | `/var/run/docker.sock` | The docker socket unix path |

<a id="inputs-dummy"></a>
### `dummy`: Dummy
Fluent Bit page: [Dummy](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) | Yes | `dummy` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`copies`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) | No | `1` | Number of messages to generate each time they are generated. |
| [`dummy`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) | No | `{"message":"dummy"}` | Dummy JSON record. |
| [`flush_on_startup`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) | No | `false` | If set to true, the first dummy event is generated at startup. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) | No | `0` | Set time interval, in nanoseconds, at which every message is generated. |
| [`interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) | No | `0` | Set time interval, in seconds, at which every message is generated. |
| [`metadata`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) | No | `{}` | Dummy JSON metadata. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) | No |  |  |
| [`rate`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) | No | `1` | Rate at which messages are generated expressed in how many times per second. |
| [`samples`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) | No |  | If set, the events number will be limited. |
| [`start_time_nsec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) | No | `0` | Dummy base timestamp, in nanoseconds. |
| [`start_time_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) | No | `0` | Dummy base timestamp, in seconds. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-ebpf"></a>
### `ebpf`: Ebpf
Fluent Bit page: [Ebpf](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | Yes | `ebpf` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  |  |

<a id="inputs-elasticsearch"></a>
### `elasticsearch`: Elasticsearch
Fluent Bit page: [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) | Yes | `elasticsearch` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) | No | `512K` | Set the buffer chunk size. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) | No | `4M` | Set the maximum size of buffer. |
| [`hostname`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) | No | `"localhost"` | Specify hostname or FQDN. |
| [`meta_key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) | No | `"@meta"` | Specify a key name for meta information. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) | No |  |  |
| [`tag_key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) | No | `NULL` | Specify a key name for extracting as a tag. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |
| [`version`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) | No | `"8.0.0"` | Specify Elasticsearch server version. |

<a id="inputs-exec"></a>
### `exec`: Exec
Fluent Bit page: [Exec](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) | Yes | `exec` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`buf_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) | No |  | Size of the buffer (check [unit sizes](/manual/3.2/administration/configuring-fluent-bit/unit-sizes.md) for allowed values) |
| [`command`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) | No |  | The command to execute, passed to [popen(...)](https://man7.org/linux/man-pages/man3/popen.3.html) without any additional escaping or processing. |
| [`exit_after_oneshot`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) | No |  | Exit as soon as the one-shot command exits. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) | No |  | Polling interval (nanosecond). |
| [`interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) | No |  | Polling interval (seconds). |
| [`oneshot`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) | No |  | Only run once at startup. |
| [`parser`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) | No |  | Specify the name of a parser to interpret the entry as a structured message. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) | No |  |  |
| [`propagate_exit_code`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) | No |  | When exiting due to Exit_After_Oneshot, cause fluent-bit to exit with the exit code of the command exited by this plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) | No |  | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-exec-wasi"></a>
### `exec_wasi`: Exec Wasi
Fluent Bit page: [Exec Wasi](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) | Yes | `exec_wasi` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`accessible_paths`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) | No |  | Specify the whitelist of paths to be able to access paths from WASM programs. |
| [`buf_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) | No |  | Size of the buffer (check [unit sizes](/manual/3.2/administration/configuring-fluent-bit/unit-sizes.md) for allowed values) |
| [`interval_nsec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) | No |  | Polling interval (nanosecond). |
| [`interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) | No |  | Polling interval (seconds). |
| [`oneshot`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) | No |  | Only run once at startup. |
| [`parser`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) | No |  | Specify the name of a parser to interpret the entry as a structured message. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) | No |  |  |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) | No |  | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |
| [`wasi_path`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) | No |  | The place of a WASM program file. |
| [`wasm_heap_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) | No |  | Size of the heap size of Wasm execution. |
| [`wasm_stack_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) | No |  | Size of the stack size of Wasm execution. |

<a id="inputs-fluentbit-metrics"></a>
### `fluentbit_metrics`: Fluent Bit Metrics
Fluent Bit page: [Fluent Bit Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/fluentbit-metrics#configuration)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/fluentbit-metrics#configuration) | Yes | `fluentbit_metrics` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/fluentbit-metrics#configuration) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/fluentbit-metrics#configuration) | No |  |  |
| [`scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/fluentbit-metrics#configuration) | No | `2 seconds` | The rate at which metrics are collected from the host operating system |
| [`scrape_on_start`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/fluentbit-metrics#configuration) | No | `false` | Scrape metrics upon start, useful to avoid waiting for 'scrape_interval' for the first round of metrics. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/fluentbit-metrics#configuration) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-forward"></a>
### `forward`: Forward
Fluent Bit page: [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) | Yes | `forward` | Plugin identifier. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) | Yes | `1024000` | By default the buffer to store the incoming Forward messages, do not allocate the maximum memory allowed, instead it allocate memory when is required. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) | Yes | `6144000` | Specify the maximum buffer memory size used to receive a Forward message. |
| [`empty_shared_key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) | No | `false` | Use this option to connect to Fluentd with a zero-length shared key. |
| [`listen`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) | No | `0.0.0.0` | Listener network interface. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) | No | `24224` | TCP port to listen for incoming connections. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) | No |  |  |
| [`security.users`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) | No |  | Specify the username and password pairs for secure forward authentication. |
| [`self_hostname`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) | No |  | Hostname for secure forward authentication. |
| [`shared_key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) | No |  | Shared key for secure forward authentication. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) | No |  | Override the tag of the forwarded events with the defined value. |
| [`tag_prefix`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) | No |  | Prefix incoming tag with the defined value. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |
| [`unix_path`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) | No |  | Specify the path to unix socket to receive a Forward message. |
| [`unix_perm`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) | No |  | Set the permission of the unix socket file. |

<a id="inputs-head"></a>
### `head`: Head
Fluent Bit page: [Head](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) | Yes | `head` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`add_path`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) | No |  | If enabled, filepath is appended to each records. |
| [`buf_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) | No |  | Buffer size to read the file. |
| [`file`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) | No |  | Absolute path to the target file, e.g: /proc/uptime |
| [`interval_nsec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) | No |  | Polling interval (nanosecond). |
| [`interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) | No |  | Polling interval (seconds). |
| [`key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) | No |  | Rename a key. |
| [`lines`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) | No |  | Line number to read. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) | No |  |  |
| [`split_line`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) | No |  | If enabled, in_head generates key-value pair per line. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) | No |  | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-health"></a>
### `health`: Health
Fluent Bit page: [Health](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) | Yes | `health` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`add_host`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) | No |  | If enabled, hostname is appended to each records. |
| [`add_port`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) | No |  | If enabled, port number is appended to each records. |
| [`alert`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) | No |  | If enabled, it will only generate messages if the target TCP service is down. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) | No |  | Name of the target host or IP address to check. |
| [`internal_nsec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) | No |  | Specify a nanoseconds interval for service checks, it works in conjunction with the Interval_Sec configuration key. |
| [`interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) | No |  | Interval in seconds between the service checks. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) | No |  | TCP port where to perform the connection check. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) | No |  |  |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) | No |  | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-http"></a>
### `http`: HTTP
Fluent Bit page: [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) | Yes | `http` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) | No | `512K` | This sets the chunk size for incoming incoming JSON messages. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) | No | `4M` | Specify the maximum buffer size in KB to receive a JSON message. |
| [`listen`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) | No | `0.0.0.0` | The address to listen on |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) | No | `9880` | The port for Fluent Bit to listen on |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) | No |  |  |
| [`success_header`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) | No |  | Add an HTTP header key/value pair on success. |
| [`successful_response_code`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) | No | `201` | It allows to set successful response code. |
| [`tag_key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) | No |  | Specify the key name to overwrite a tag. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-kafka"></a>
### `kafka`: Kafka
Fluent Bit page: [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) | Yes | `kafka` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`brokers`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) | No |  | Single or multiple list of Kafka Brokers, e.g: 192.168.1.3:9092, 192.168.1.4:9092. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) | No | `4M` | Specify the maximum size of buffer per cycle to poll kafka messages from subscribed topics. |
| [`client_id`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) | No |  | Client id passed to librdkafka. |
| [`format`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) | No |  | Serialization format of the messages. |
| [`group_id`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) | No | `fluent-bit` | Group id passed to librdkafka. |
| [`poll_ms`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) | No | `500` | Kafka brokers polling interval in milliseconds. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) | No |  |  |
| [`rdkafka.{property}`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) | No |  | {property} can be any [librdkafka properties](https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md) |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |
| [`topics`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) | No |  | Single entry or list of topics separated by comma (, ) that Fluent Bit will subscribe to. |

<a id="inputs-kmsg"></a>
### `kmsg`: Kernel Logs
Fluent Bit page: [Kernel Logs](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kernel-logs#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kernel-logs#configuration-parameters) | Yes | `kmsg` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kernel-logs#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`prio_level`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kernel-logs#configuration-parameters) | No | `8` | The log level to filter. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kernel-logs#configuration-parameters) | No |  |  |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kernel-logs#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-kubernetes-events"></a>
### `kubernetes_events`: Kubernetes Events
Fluent Bit page: [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | Yes | `kubernetes_events` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`db`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No |  | Set a database file to keep track of recorded Kubernetes events |
| [`db.sync`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No | `normal` | Set a database sync method. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No | `500000000` | Set the reconnect interval (sub seconds: nanoseconds)\ |
| [`interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No | `0` | Set the reconnect interval (seconds)\ |
| [`kube_ca_file`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No | `/var/run/secrets/kubernetes.io/serviceaccount/ca.crt` | Kubernetes TLS CA file |
| [`kube_ca_path`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No |  | Kubernetes TLS ca path |
| [`kube_namespace`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No |  | Kubernetes namespace to query events from. |
| [`kube_request_limit`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No | `0` | kubernetes limit parameter for events query, no limit applied when set to 0. |
| [`kube_retention_time`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No | `1h` | Kubernetes retention time for events. |
| [`kube_token_file`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No | `/var/run/secrets/kubernetes.io/serviceaccount/token` | Kubernetes authorization token file. |
| [`kube_token_ttl`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No | `10m` | kubernetes token ttl, until it is reread from the token file. |
| [`kube_url`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No | `<https://kubernetes.default.svc>` | API Server end-point |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No |  |  |
| [`tls.debug`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No | `0` | Debug level between 0 (nothing) and 4 (every detail). |
| [`tls.verify`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No | `On` | Enable or disable verification of TLS peer certificate. |
| [`tls.vhost`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) | No |  | Set optional TLS virtual host. |

<a id="inputs-mem"></a>
### `mem`: Memory Metrics
Fluent Bit page: [Memory Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | Yes | `mem` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  |  |

<a id="inputs-mqtt"></a>
### `mqtt`: MQTT
Fluent Bit page: [MQTT](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/mqtt#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/mqtt#configuration-parameters) | Yes | `mqtt` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/mqtt#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`listen`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/mqtt#configuration-parameters) | No | `0.0.0.0` | Listener network interface. |
| [`payload_key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/mqtt#configuration-parameters) | No |  | Specify the key where the payload key/value will be preserved. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/mqtt#configuration-parameters) | No | `1883` | TCP port where listening for connections. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/mqtt#configuration-parameters) | No |  |  |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/mqtt#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-netif"></a>
### `netif`: Network I/O Log Based Metrics
Fluent Bit page: [Network I/O Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters) | Yes | `netif` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`interface`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters) | No |  | Specify the network interface to monitor. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters) | No | `0` | Polling interval (nanosecond). |
| [`interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters) | No | `1` | Polling interval (seconds). |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters) | No |  |  |
| [`test_at_init`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters) | No | `false` | If true, testing if the network interface is valid at initialization. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |
| [`verbose`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters) | No | `false` | If true, gather metrics precisely. |

<a id="inputs-nginx-metrics"></a>
### `nginx_metrics`: NGINX Exporter Metrics
Fluent Bit page: [NGINX Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/nginx#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/nginx#configuration-parameters) | Yes | `nginx_metrics` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/nginx#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/nginx#configuration-parameters) | No | `localhost` | Name of the target host or IP address to check. |
| [`nginx_plus`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/nginx#configuration-parameters) | No | `true` | Turn on NGINX plus mode. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/nginx#configuration-parameters) | No | `80` | Port of the target nginx service to connect to. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/nginx#configuration-parameters) | No |  |  |
| [`status_url`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/nginx#configuration-parameters) | No | `/status` | The URL of the Stub Status Handler. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/nginx#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-node-exporter-metrics"></a>
### `node_exporter_metrics`: Node Exporter Metrics
Fluent Bit page: [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | Yes | `node_exporter_metrics` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`collector.cpu.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which cpu metrics are collected from the host operating system. |
| [`collector.cpufreq.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which cpufreq metrics are collected from the host operating system. |
| [`collector.diskstats.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which diskstats metrics are collected from the host operating system. |
| [`collector.filefd.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which filefd metrics are collected from the host operating system. |
| [`collector.filesystem.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which filesystem metrics are collected from the host operating system. |
| [`collector.loadavg.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which loadavg metrics are collected from the host operating system. |
| [`collector.meminfo.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which meminfo metrics are collected from the host operating system. |
| [`collector.nvme.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which nvme metrics are collected from the host operating system. |
| [`collector.processes.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which system level of process metrics are collected from the host operating system. |
| [`collector.stat.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which stat metrics are collected from the host operating system. |
| [`collector.thermal_zone.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which thermal_zone metrics are collected from the host operating system. |
| [`collector.time.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which time metrics are collected from the host operating system. |
| [`collector.uname.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which uname metrics are collected from the host operating system. |
| [`collector.vmstat.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which vmstat metrics are collected from the host operating system. |
| [`diskstats.ignore_device_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `\`^(ram` | Specify the regex for the diskstats to prevent collection of/ignore. |
| [`filesystem.ignore_filesystem_type_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `\`^(autofs` | Specify the regex for the filesystem types to prevent collection of/ignore. |
| [`filesystem.ignore_mount_point_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `\`^/(dev` | Specify the regex for the mount points to prevent collection of/ignore. |
| [`metrics`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `"cpu, cpufreq, meminfo, diskstats, filesystem, uname, stat, time, loadavg, vmstat, netdev, filefd"` | To specify which metrics are collected from the host operating system. |
| [`path.procfs`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `/proc/` | The mount point used to collect process information and metrics |
| [`path.sysfs`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `/sys/` | The path in the filesystem used to collect system metrics |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No |  |  |
| [`scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `5 seconds` | The rate at which metrics are collected from the host operating system |
| [`systemd_exclude_pattern`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `\`.+\\.(automount` | regex to determine which units are excluded in the metrics produced by the systemd collector |
| [`systemd_include_pattern`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `It is not applied unless explicitly set` | regex to determine which units are included in the metrics produced by the systemd collector |
| [`systemd_include_service_task_metrics`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `false` | Determines if the collector will include service task metrics |
| [`systemd_service_restart_metrics`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `false` | Determines if the collector will include service restart metrics |
| [`systemd_unit_start_time_metrics`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) | No | `false` | Determines if the collector will include unit start time metrics |

<a id="inputs-opentelemetry"></a>
### `opentelemetry`: OpenTelemetry
Fluent Bit page: [OpenTelemetry](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) | Yes | `opentelemetry` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) | Yes |  | Tag for all the data ingested by this plugin. |
| [`tag_from_uri`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) | Yes | `true` | By default, tag will be created from uri. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) | No | `512K` | Initial size and allocation strategy to store the payload (advanced users only) |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) | No | `4M` | Specify the maximum buffer size in KB/MB/GB to the HTTP payload. |
| [`listen`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) | No | `0.0.0.0` | The network address to listen. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) | No | `4318` | The port for Fluent Bit to listen for incoming connections. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) | No |  |  |
| [`raw_traces`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) | No | `false` | Route trace data as a log |
| [`successful_response_code`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) | No | `201` | It allows to set successful response code. |
| [`tag_key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) | No |  | Specify the key name to overwrite a tag. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-podman-metrics"></a>
### `podman_metrics`: Podman Metrics
Fluent Bit page: [Podman Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters) | Yes | `podman_metrics` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`path.config`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters) | No | `/var/lib/containers/storage/overlay-containers/containers.json` | Custom path to podman containers configuration file |
| [`path.procfs`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters) | No | `/proc` | Custom path to proc subsystem directory |
| [`path.sysfs`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters) | No | `/sys/fs/cgroup` | Custom path to sysfs subsystem directory |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters) | No |  |  |
| [`scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters) | No | `30` | Interval between each scrape of podman data (in seconds) |
| [`scrape_on_start`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters) | No | `false` | Should this plugin scrape podman data after it is started |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-proc"></a>
### `proc`: Process Log Based Metrics
Fluent Bit page: [Process Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) | Yes | `proc` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`alert`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) | No |  | If enabled, it will only generate messages if the target process is down. |
| [`fd`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) | No |  | If enabled, a number of fd is appended to each records. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) | No |  | Specify a nanoseconds interval for service checks, it works in conjunction with the Interval_Sec configuration key. |
| [`interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) | No |  | Interval in seconds between the service checks. |
| [`mem`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) | No |  | If enabled, memory usage of the process is appended to each records. |
| [`proc_name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) | No |  | Name of the target Process to check. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) | No |  |  |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) | No |  | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-process-exporter-metrics"></a>
### `process_exporter_metrics`: Process Exporter Metrics
Fluent Bit page: [Process Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process-exporter-metrics#configuration)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process-exporter-metrics#configuration) | Yes | `process_exporter_metrics` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process-exporter-metrics#configuration) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`metrics`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process-exporter-metrics#configuration) | No | `cpu, io, memory, state, context_switches, fd, start_time, thread_wchan, thread` | To specify which process level of metrics are collected from the host operating system. |
| [`path.procfs`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process-exporter-metrics#configuration) | No | `/proc/` | The mount point used to collect process information and metrics. |
| [`process_exclude_pattern`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process-exporter-metrics#configuration) | No | `It is not applied unless explicitly set. Default is `NULL`.` | regex to determine which names of processes are excluded in the metrics produced by this plugin |
| [`process_include_pattern`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process-exporter-metrics#configuration) | No | `It is applied for all process unless explicitly set. Default is `.+`.` | regex to determine which names of processes are included in the metrics produced by this plugin |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process-exporter-metrics#configuration) | No |  |  |
| [`scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process-exporter-metrics#configuration) | No | `5 seconds` | The rate at which metrics are collected. |

<a id="inputs-prometheus-remote-write"></a>
### `prometheus_remote_write`: Prometheus Remote Write
Fluent Bit page: [Prometheus Remote Write](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) | Yes | `prometheus_remote_write` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`tag_from_uri`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) | Yes | `true` | If true, tag will be created from uri, e.g. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) | No | `512K` | This sets the chunk size for incoming incoming JSON messages. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) | No | `4M` | Specify the maximum buffer size in KB to receive a JSON message. |
| [`listen`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) | No | `0.0.0.0` | The address to listen on |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) | No | `8080` | The port for Fluent Bit to listen on |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) | No |  |  |
| [`successful_response_code`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) | No | `201` | It allows to set successful response code. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |
| [`uri`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) | No |  | Specify an optional HTTP URI for the target web server listening for prometheus remote write payloads, e.g: /api/prom/push |

<a id="inputs-prometheus-scrape"></a>
### `prometheus_scrape`: Prometheus Scrape Metrics
Fluent Bit page: [Prometheus Scrape Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-scrape-metrics#configuration-a-hrefconfiguration-idconfigurationa)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-scrape-metrics#configuration-a-hrefconfiguration-idconfigurationa) | Yes | `prometheus_scrape` | Plugin identifier. |
| [`metrics_path`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-scrape-metrics#configuration-a-hrefconfiguration-idconfigurationa) | Yes | `/metrics` | <p>The metrics URI endpoint, that must start with a forward slash.<br><br>Note: Parameters can also be added to the path by using <code>?</code></p> |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-scrape-metrics#configuration-a-hrefconfiguration-idconfigurationa) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-scrape-metrics#configuration-a-hrefconfiguration-idconfigurationa) | No |  | The host of the prometheus metric endpoint that you want to scrape |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-scrape-metrics#configuration-a-hrefconfiguration-idconfigurationa) | No |  | The port of the prometheus metric endpoint that you want to scrape |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-scrape-metrics#configuration-a-hrefconfiguration-idconfigurationa) | No |  |  |
| [`scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-scrape-metrics#configuration-a-hrefconfiguration-idconfigurationa) | No | `10s` | The interval to scrape metrics |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-scrape-metrics#configuration-a-hrefconfiguration-idconfigurationa) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-random"></a>
### `random`: Random
Fluent Bit page: [Random](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/random#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/random#configuration-parameters) | Yes | `random` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/random#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/random#configuration-parameters) | No |  | Specify a nanoseconds interval for samples generation, it works in conjunction with the Interval_Sec configuration key. |
| [`interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/random#configuration-parameters) | No |  | Interval in seconds between samples generation. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/random#configuration-parameters) | No |  |  |
| [`samples`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/random#configuration-parameters) | No |  | If set, it will only generate a specific number of samples. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/random#configuration-parameters) | No |  | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-serial"></a>
### `serial`: Serial Interface
Fluent Bit page: [Serial Interface](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters) | Yes | `serial` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`bitrate`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters) | No |  | The bitrate for the communication, e.g: 9600, 38400, 115200, etc |
| [`file`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters) | No |  | Absolute path to the device entry, e.g: /dev/ttyS0 |
| [`format`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters) | No |  | Specify the format of the incoming data stream. |
| [`min_bytes`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters) | No |  | The serial interface will expect at least Min_Bytes to be available before to process the message (default: 1) |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters) | No |  |  |
| [`separator`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters) | No |  | Allows to specify a separator string that's used to determinate when a message ends. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters) | No |  | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-splunk"></a>
### `splunk`: Splunk
Fluent Bit page: [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) | Yes | `splunk` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) | No | `512K` | This sets the chunk size for incoming incoming JSON messages. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) | No | `4M` | Specify the maximum buffer size in KB to receive a JSON message. |
| [`listen`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) | No | `0.0.0.0` | The address to listen on |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) | No | `9880` | The port for Fluent Bit to listen on |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) | No |  |  |
| [`splunk_token`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) | No |  | Specify a Splunk token for HTTP HEC authentication. |
| [`splunk_token_key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) | No | `@splunk\_token` | Use the specified key for storing the Splunk token for HTTP HEC. |
| [`store_token_in_metadata`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) | No | `true` | Store Splunk HEC tokens in the Fluent Bit metadata. |
| [`successful_response_code`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) | No | `201` | It allows to set successful response code. |
| [`tag_key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) | No |  | Specify the key name to overwrite a tag. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-statsd"></a>
### `statsd`: StatsD
Fluent Bit page: [StatsD](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/statsd#configuration-parameters-a-hrefconfig-idconfiga)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/statsd#configuration-parameters-a-hrefconfig-idconfiga) | Yes | `statsd` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/statsd#configuration-parameters-a-hrefconfig-idconfiga) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`listen`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/statsd#configuration-parameters-a-hrefconfig-idconfiga) | No | `0.0.0.0` | Listener network interface. |
| [`metrics`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/statsd#configuration-parameters-a-hrefconfig-idconfiga) | No | `off` | Ingested record will be marked as a metric record rather than a log record. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/statsd#configuration-parameters-a-hrefconfig-idconfiga) | No | `8125` | UDP port where listening for connections |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/statsd#configuration-parameters-a-hrefconfig-idconfiga) | No |  |  |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/statsd#configuration-parameters-a-hrefconfig-idconfiga) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-stdin"></a>
### `stdin`: Standard Input
Fluent Bit page: [Standard Input](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/standard-input#configuration-parameters-a-hrefconfig-idconfiga)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/standard-input#configuration-parameters-a-hrefconfig-idconfiga) | Yes | `stdin` | Plugin identifier. |
| [`buffer_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/standard-input#configuration-parameters-a-hrefconfig-idconfiga) | Yes | `16k` | Set the buffer size to read data. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/standard-input#configuration-parameters-a-hrefconfig-idconfiga) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`parser`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/standard-input#configuration-parameters-a-hrefconfig-idconfiga) | No |  | The name of the parser to invoke instead of the default JSON input parser |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/standard-input#configuration-parameters-a-hrefconfig-idconfiga) | No |  |  |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/standard-input#configuration-parameters-a-hrefconfig-idconfiga) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-syslog"></a>
### `syslog`: Syslog
Fluent Bit page: [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) | Yes | `syslog` | Plugin identifier. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) | Yes |  | By default the buffer to store the incoming Syslog messages, do not allocate the maximum memory allowed, instead it allocate memory when is required. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) | No |  | Specify the maximum buffer size to receive a Syslog message. |
| [`listen`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) | No | `0.0.0.0` | If Mode is set to tcp or udp, specify the network interface to bind. |
| [`mode`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) | No | `unix\_udp` | Defines transport protocol mode: unix_udp (UDP over Unix socket), unix_tcp (TCP over Unix socket), tcp or udp |
| [`parser`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) | No |  | Specify an alternative parser for the message. |
| [`path`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) | No |  | If Mode is set to unix_tcp or unix_udp, set the absolute path to the Unix socket file. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) | No | `5140` | If Mode is set to tcp or udp, specify the TCP port to listen for incoming connections. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) | No |  |  |
| [`receive_buffer_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) | No |  | Specify the maximum socket receive buffer size. |
| [`source_address_key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) | No |  | Specify the key where the source address will be injected. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |
| [`unix_perm`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) | No | `644` | If Mode is set to unix_tcp or unix_udp, set the permission of the Unix socket file. |

<a id="inputs-systemd"></a>
### `systemd`: Systemd
Fluent Bit page: [Systemd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) | Yes | `systemd` | Plugin identifier. |
| [`systemd_filter`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) | Yes |  | Allows to perform a query over logs that contains a specific Journald key/value pairs, e.g: _SYSTEMD_UNIT=UNIT. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) | Yes |  | The tag is used to route messages but on Systemd plugin there is an extra functionality: if the tag includes a star/wildcard, it will be expanded with the Systemd Unit file (_SYSTEMD_UNIT, e.g. |
| [`db`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) | No |  | Specify the absolute path of a database file to keep track of Journald cursor. |
| [`db.sync`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) | No | `Full` | Set a default synchronization (I/O) method. |
| [`lowercase`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) | No | `Off` | Lowercase the Journald field (key). |
| [`max_entries`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) | No | `5000` | When Fluent Bit starts, the Journal might have a high number of logs in the queue. |
| [`max_fields`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) | No | `8000` | Set a maximum number of fields (keys) allowed per record. |
| [`path`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) | No |  | Optional path to the Systemd journal directory, if not set, the plugin will use default paths to read local-only logs. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) | No |  |  |
| [`read_from_tail`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) | No | `Off` | Start reading new entries. |
| [`strip_underscores`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) | No | `Off` | Remove the leading underscore of the Journald field (key). |
| [`systemd_filter_type`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) | No | `Or` | Define the filter type when Systemd_Filter is specified multiple times. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-tail"></a>
### `tail`: Tail
Fluent Bit page: [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | Yes | `tail` | Plugin identifier. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | Yes | `32k` | Set the initial buffer size to read files data. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | Yes | `32k` | Set the limit of the buffer size per monitored file. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | Yes |  | Set a tag (with regex-extract fields) that will be placed on lines read. |
| [`db`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Specify the database file to keep track of monitored files and offsets. |
| [`db.compare_filename`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No | `false` | This option determines whether to check both the inode and the filename when retrieving stored file information from the database. |
| [`db.journal_mode`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No | `WAL` | sets the journal mode for databases (WAL). |
| [`db.locking`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No | `false` | Specify that the database will be accessed only by Fluent Bit. |
| [`db.sync`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No | `normal` | Set a default synchronization (I/O) method. |
| [`exclude_path`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Set one or multiple shell patterns separated by commas to exclude files matching certain criteria, e.g: Exclude_Path .gz, .zip |
| [`exit_on_eof`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No | `false` | When reading a file will exit as soon as it reach the end of the file. |
| [`file_cache_advise`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No | `On` | Set the posix_fadvise in POSIX_FADV_DONTNEED mode. |
| [`ignore_older`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Ignores files older than ignore_older. |
| [`inotify_watcher`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No | `true` | Set to false to use file stat watcher instead of inotify. |
| [`key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No | `log` | When a message is unstructured (no parser applied), it's appended as a string under the key name log. |
| [`mem_buf_limit`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Set a limit of memory that Tail plugin can use when appending data to the Engine. |
| [`offset_key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No |  | If enabled, Fluent Bit appends the offset of the current monitored file as part of the record. |
| [`parser`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Specify the name of a parser to interpret the entry as a structured message. |
| [`path`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Pattern specifying a specific log file or multiple ones through the use of common wildcards. |
| [`path_key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No |  | If enabled, it appends the name of the monitored file as part of the record. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No |  |  |
| [`read_from_head`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No | `false` | For new discovered files on start (without a database offset/position), read the content from the head of the file, not tail. |
| [`refresh_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No | `60` | The interval of refreshing the list of watched files in seconds. |
| [`rotate_wait`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No | `5` | Specify the number of extra time in seconds to monitor a file once is rotated in case some pending data is flushed. |
| [`skip_empty_lines`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No | `Off` | Skips empty lines in the log file from any further processing or output. |
| [`skip_long_lines`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No | `Off` | When a monitored file reaches its buffer capacity due to a very long line (Buffer_Max_Size), the default behavior is to stop monitoring that file. |
| [`static_batch_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No | `50M` | Set the maximum number of bytes to process per iteration for the monitored static files (files that already exists upon Fluent Bit start). |
| [`tag_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Set a regex to extract fields from the file name. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-tcp"></a>
### `tcp`: TCP
Fluent Bit page: [TCP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) | Yes | `tcp` | Plugin identifier. |
| [`chunk_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) | Yes | `32` | By default the buffer to store the incoming JSON messages, do not allocate the maximum memory allowed, instead it allocate memory when is required. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`buffer_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) | No |  | Specify the maximum buffer size in KB to receive a JSON message. |
| [`format`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) | No | `json` | Specify the expected payload format. |
| [`listen`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) | No | `0.0.0.0` | Listener network interface. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) | No | `5170` | TCP port where listening for connections |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) | No |  |  |
| [`separator`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) | No |  | When the expected Format is set to none, Fluent Bit needs a separator string to split the records. |
| [`source_address_key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) | No |  | Specify the key where the source address will be injected. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-thermal"></a>
### `thermal`: Thermal
Fluent Bit page: [Thermal](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/thermal#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/thermal#configuration-parameters) | Yes | `thermal` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/thermal#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/thermal#configuration-parameters) | No |  | Polling interval (nanoseconds). |
| [`interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/thermal#configuration-parameters) | No |  | Polling interval (seconds). |
| [`name_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/thermal#configuration-parameters) | No |  | Optional name filter regex. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/thermal#configuration-parameters) | No |  |  |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/thermal#configuration-parameters) | No |  | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |
| [`type_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/thermal#configuration-parameters) | No |  | Optional type filter regex. |

<a id="inputs-udp"></a>
### `udp`: UDP
Fluent Bit page: [UDP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) | Yes | `udp` | Plugin identifier. |
| [`chunk_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) | Yes | `32` | By default the buffer to store the incoming JSON messages, do not allocate the maximum memory allowed, instead it allocate memory when is required. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`buffer_size`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) | No |  | Specify the maximum buffer size in KB to receive a JSON message. |
| [`format`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) | No | `json` | Specify the expected payload format. |
| [`listen`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) | No | `0.0.0.0` | Listener network interface. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) | No | `5170` | UDP port where listening for connections |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) | No |  |  |
| [`separator`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) | No |  | When the expected Format is set to none, Fluent Bit needs a separator string to split the records. |
| [`source_address_key`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) | No |  | Specify the key where the source address will be injected. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

<a id="inputs-windows-exporter-metrics"></a>
### `windows_exporter_metrics`: Windows Exporter Metrics
Fluent Bit page: [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | Yes | `windows_exporter_metrics` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`collector.cpu.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which cpu metrics are collected from the host operating system. |
| [`collector.cpu_info.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which cpu_info metrics are collected from the host operating system. |
| [`collector.cs.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which cs metrics are collected from the host operating system. |
| [`collector.logical_disk.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which logical_disk metrics are collected from the host operating system. |
| [`collector.logon.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which logon metrics are collected from the host operating system. |
| [`collector.memory.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which memory metrics are collected from the host operating system. |
| [`collector.net.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which net metrics are collected from the host operating system. |
| [`collector.os.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which os metrics are collected from the host operating system. |
| [`collector.paging_file.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which paging_file metrics are collected from the host operating system. |
| [`collector.process.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which process metrics are collected from the host operating system. |
| [`collector.service.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which service metrics are collected from the host operating system. |
| [`collector.system.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which system metrics are collected from the host operating system. |
| [`collector.thermalzone.scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `0 seconds` | The rate in seconds at which thermalzone metrics are collected from the host operating system. |
| [`metrics`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `"cpu, cpu_info, os, net, logical_disk, cs, thermalzone, logon, system, service"` | To specify which metrics are collected from the host operating system. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No |  |  |
| [`scrape_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `5 seconds` | The rate at which metrics are collected from the host operating system |
| [`we.logical_disk.allow_disk_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `"/.+/"` | Specify the regex for logical disk metrics to allow collection of. |
| [`we.logical_disk.deny_disk_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `NULL` | Specify the regex for logical disk metrics to prevent collection of/ignore. |
| [`we.net.allow_nic_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `"/.+/"` | Specify the regex for network metrics captured by the name of the NIC, by default captures all NICs but to exclude adjust the regex. |
| [`we.process.allow_process_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `"/.+/"` | Specify the regex covering the process metrics to collect. |
| [`we.process.deny_process_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `NULL` | Specify the regex for process metrics to prevent collection of/ignore. |
| [`we.service.exclude`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `NULL` | Specify the key value pairs for the exclude condition for the WHERE clause of service metrics. |
| [`we.service.include`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `NULL` | Specify the key value pairs for the include condition for the WHERE clause of service metrics. |
| [`we.service.where`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) | No | `NULL` | Specify the WHERE clause for retrieving service metrics. |

<a id="inputs-winevtlog"></a>
### `winevtlog`: Windows Event Log (winevtlog)
Fluent Bit page: [Windows Event Log (winevtlog)](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) | Yes | `winevtlog` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`channels`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) | No |  | A comma-separated list of channels to read from. |
| [`db`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Set the path to save the read offsets. |
| [`event_query`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) | No | `*` | Specify XML query for filtering events. |
| [`ignore_missing_channels`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) | No | `false` | Whether to ignore event channels not present in the event log, and continue running with subscribed channels. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) | No | `0` | Set the polling interval for each channel (sub seconds. |
| [`interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) | No | `1` | Set the polling interval for each channel. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) | No |  |  |
| [`read_existing_events`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) | No | `false` | Whether to read existing events from head or tailing events at last on subscribing. |
| [`read_limit_per_cycle`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) | No | `512KiB` | Specify read limit per cycle. |
| [`render_event_as_xml`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) | No | `false` | Whether to render system part of event as XML string or not. |
| [`string_inserts`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) | No | `true` | Whether to include StringInserts in output records. |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |
| [`use_ansi`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) | No | `false` | Use ANSI encoding on eventlog messages. |

<a id="inputs-winlog"></a>
### `winlog`: Windows Event Log
Fluent Bit page: [Windows Event Log](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log#configuration-parameters-a-hrefconfig-idconfiga)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log#configuration-parameters-a-hrefconfig-idconfiga) | Yes | `winlog` | Plugin identifier. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log#configuration-parameters-a-hrefconfig-idconfiga) | Yes |  | Tag assigned to records emitted by this input plugin. |
| [`channels`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log#configuration-parameters-a-hrefconfig-idconfiga) | No |  | A comma-separated list of channels to read from. |
| [`db`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Set the path to save the read offsets. |
| [`interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log#configuration-parameters-a-hrefconfig-idconfiga) | No | `1` | Set the polling interval for each channel. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log#configuration-parameters-a-hrefconfig-idconfiga) | No |  |  |
| [`threaded`](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log#configuration-parameters-a-hrefconfig-idconfiga) | No | `false` | Indicates whether to run this input in its own [thread](/manual/3.2/administration/multithreading.md#inputs). |

## Filters

[`aws`](#filters-aws), [`checklist`](#filters-checklist), [`ecs`](#filters-ecs), [`expect`](#filters-expect), [`geoip2`](#filters-geoip2), [`grep`](#filters-grep), [`kubernetes`](#filters-kubernetes), [`log_to_metrics`](#filters-log-to-metrics), [`lua`](#filters-lua), [`modify`](#filters-modify), [`multiline`](#filters-multiline), [`nest`](#filters-nest), [`nightfall`](#filters-nightfall), [`parser`](#filters-parser), [`record_modifier`](#filters-record-modifier), [`rewrite_tag`](#filters-rewrite-tag), [`stdout`](#filters-stdout), [`sysinfo`](#filters-sysinfo), [`tensorflow`](#filters-tensorflow), [`throttle`](#filters-throttle), [`type_converter`](#filters-type-converter), [`wasm`](#filters-wasm)

<a id="filters-aws"></a>
### `aws`: AWS Metadata
Fluent Bit page: [AWS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | Yes | `aws` | Plugin identifier. |
| [`tags_enabled`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | Yes | `false` | Specifies if should attach EC2 instance tags. |
| [`tags_exclude`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | Yes |  | Defines list of specific EC2 tag keys not to inject into the logs. |
| [`tags_include`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | Yes |  | Defines list of specific EC2 tag keys to inject into the logs. |
| [`account_id`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | No | `false` | The account ID for current EC2 instance. |
| [`ami_id`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | No | `false` | The EC2 instance image id. |
| [`az`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | No | `true` | The [availability zone](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html); for example, "us-east-1a". |
| [`ec2_instance_id`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | No | `true` | The EC2 instance ID. |
| [`ec2_instance_type`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | No | `false` | The EC2 instance type. |
| [`hostname`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | No | `false` | The hostname for current EC2 instance. |
| [`imds_version`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | No | `v2` | Specify which version of the instance metadata service to use. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`private_ip`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | No | `false` | The EC2 instance private ip. |
| [`retry_interval_s`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | No | `300` | Defines minimum duration between retries for fetching EC2 instance tags. |
| [`vpc_id`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) | No | `false` | The VPC ID for current EC2 instance. |

<a id="filters-checklist"></a>
### `checklist`: CheckList
Fluent Bit page: [CheckList](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters) | Yes | `checklist` | Plugin identifier. |
| [`file`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters) | No |  | The single value file that Fluent Bit will use as a lookup table to determine if the specified lookup_key exists |
| [`ignore_case`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters) | No |  | Compare strings by ignoring case. |
| [`lookup_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters) | No |  | The specific key to look up and determine if it exists, supports record accessor |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`mode`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters) | No |  | Set the check mode. |
| [`print_query_time`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters) | No |  | Print to stdout the elapseed query time for every matched record. |
| [`record`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters) | No |  | The record to add if the lookup_key is found in the specified file. |

<a id="filters-ecs"></a>
### `ecs`: ECS Metadata
Fluent Bit page: [ECS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/ecs-metadata#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/ecs-metadata#configuration-parameters) | Yes | `ecs` | Plugin identifier. |
| [`ecs_tag_prefix`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/ecs-metadata#configuration-parameters) | Yes | `emptry string` | This parameter is similar to the Kube_Tag_Prefix option in the [Kubernetes filter](https://docs.fluentbit.io/manual/pipeline/filters/kubernetes) and performs the same function. |
| [`add`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/ecs-metadata#configuration-parameters) | No | `No default` | This parameter is similar to the ADD option in the [modify filter](https://docs.fluentbit.io/manual/pipeline/filters/modify). |
| [`cluster_metadata_only`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/ecs-metadata#configuration-parameters) | No | `Off` | When enabled, the plugin will only attempt to attach cluster metadata values. |
| [`ecs_meta_cache_ttl`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/ecs-metadata#configuration-parameters) | No | `1h (1 hour)` | The filter builds a hash table in memory mapping each unique container short ID to its metadata. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/ecs-metadata#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/ecs-metadata#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |

<a id="filters-expect"></a>
### `expect`: Expect
Fluent Bit page: [Expect](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) | Yes | `expect` | Plugin identifier. |
| [`action`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) | No |  | action to take when a rule does not match. |
| [`key_exists`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) | No |  | Check if a key with a given name exists in the record. |
| [`key_not_exists`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) | No |  | Check if a key does not exist in the record. |
| [`key_val_eq`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) | No |  | check that the value of the key equals the given value in the configuration. |
| [`key_val_is_not_null`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) | No |  | check that the value of the key is NOT NULL. |
| [`key_val_is_null`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) | No |  | check that the value of the key is NULL. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`result_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) | No |  | specify a key name of matching result. |

<a id="filters-geoip2"></a>
### `geoip2`: GeoIP2 Filter
Fluent Bit page: [GeoIP2 Filter](https://docs.fluentbit.io/manual/3.2/pipeline/filters/geoip2-filter#configuration-parameters-a-hrefconfig-idconfiga)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/geoip2-filter#configuration-parameters-a-hrefconfig-idconfiga) | Yes | `geoip2` | Plugin identifier. |
| [`database`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/geoip2-filter#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Path to the GeoIP2 database. |
| [`lookup_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/geoip2-filter#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Field name to process |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/geoip2-filter#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/geoip2-filter#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`record`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/geoip2-filter#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Defines the KEY LOOKUP_KEY VALUE triplet. |

<a id="filters-grep"></a>
### `grep`: Grep
Fluent Bit page: [Grep](https://docs.fluentbit.io/manual/3.2/pipeline/filters/grep#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/grep#configuration-parameters) | Yes | `grep` | Plugin identifier. |
| [`exclude`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/grep#configuration-parameters) | No |  | Exclude records where the content of KEY matches the regular expression. |
| [`logical_op`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/grep#configuration-parameters) | No |  | Specify a logical operator: AND, OR or legacy (default). |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/grep#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/grep#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/grep#configuration-parameters) | No |  | Keep records where the content of KEY matches the regular expression. |

<a id="filters-kubernetes"></a>
### `kubernetes`: Kubernetes
Fluent Bit page: [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | Yes | `kubernetes` | Plugin identifier. |
| [`buffer_size`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | Yes | `32k` | Set the buffer size for HTTP client when reading responses from Kubernetes API server. |
| [`keep_log`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | Yes | `On` | When Keep_Log is disabled, the log field is removed from the incoming message once it has been successfully merged (Merge_Log must be enabled as well). |
| [`regex_parser`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | Yes |  | Set an alternative Parser to process record Tag and extract pod_name, namespace_name, container_name and docker_id. |
| [`annotations`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `On` | Include Kubernetes pod resource annotations in the extra metadata. |
| [`cache_use_docker_id`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | When enabled, metadata will be fetched from K8s when docker_id is changed. |
| [`dns_retries`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `6` | DNS lookup retries N times until the network start working |
| [`dns_wait_time`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `30` | DNS lookup interval between network status checks |
| [`dummy_meta`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | If set, use dummy-meta data (for test/dev purposes) |
| [`k8s-logging.exclude`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | Allow Kubernetes Pods to exclude their logs from the log processor (read more about it in Kubernetes Annotations section). |
| [`k8s-logging.parser`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | Allow Kubernetes Pods to suggest a pre-defined Parser (read more about it in Kubernetes Annotations section) |
| [`kube_ca_file`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `/var/run/secrets/kubernetes.io/serviceaccount/ca.crt` | CA certificate file |
| [`kube_ca_path`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No |  | Absolute path to scan for certificate files |
| [`kube_meta_cache_ttl`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `0` | configurable TTL for K8s cached pod metadata. |
| [`kube_meta_namespace_cache_ttl`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `900` | configurable TTL for K8s cached namespace metadata. |
| [`kube_meta_preload_cache_dir`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No |  | If set, Kubernetes meta-data can be cached/pre-loaded from files in JSON format in this directory, named as namespace-pod.meta |
| [`kube_tag_prefix`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `kube.var.log.containers.` | When the source records comes from Tail input plugin, this option allows to specify what's the prefix used in Tail configuration. |
| [`kube_token_command`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No |  | Command to get Kubernetes authorization token. |
| [`kube_token_file`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `/var/run/secrets/kubernetes.io/serviceaccount/token` | Token file |
| [`kube_token_ttl`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `600` | configurable 'time to live' for the K8s token. |
| [`kube_url`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `<https://kubernetes.default.svc:443>` | API Server end-point |
| [`kubelet_host`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `127.0.0.1` | kubelet host using for HTTP request, this only works when Use_Kubelet set to On. |
| [`kubelet_port`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `10250` | kubelet port using for HTTP request, this only works when Use_Kubelet set to On. |
| [`labels`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `On` | Include Kubernetes pod resource labels in the extra metadata. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`merge_log`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | When enabled, it checks if the log field content is a JSON string map, if so, it append the map fields as part of the log structure. |
| [`merge_log_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No |  | When Merge_Log is enabled, the filter tries to assume the log field from the incoming message is a JSON string message and make a structured representation of it at the same level of the log field in the map. |
| [`merge_log_trim`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `On` | When Merge_Log is enabled, trim (remove possible \n or \r) field values. |
| [`merge_parser`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No |  | Optional parser name to specify how to parse the data contained in the log key. |
| [`namespace_annotations`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | Include Kubernetes namespace resource annotations in the extra metadata. |
| [`namespace_labels`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | Include Kubernetes namespace resource labels in the extra metadata. |
| [`namespace_metadata_only`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | Include Kubernetes namespace metadata only and no pod metadata. |
| [`owner_references`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | Include Kubernetes owner references in the extra metadata |
| [`tls.debug`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `-1` | Debug level between 0 (nothing) and 4 (every detail). |
| [`tls.verify`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `On` | When enabled, turns on certificate validation when connecting to the Kubernetes API server. |
| [`tls.verify_hostname`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | When enabled, turns on hostname validation for certificates |
| [`use_journal`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | When enabled, the filter reads logs coming in Journald format. |
| [`use_kubelet`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | this is an optional feature flag to get metadata information from kubelet instead of calling Kube Server API to enhance the log. |
| [`use_tag_for_meta`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | When enabled, Kubernetes metadata (e.g., pod_name, container_name, namespace_name etc) will be extracted from the tag itself. |

<a id="filters-log-to-metrics"></a>
### `log_to_metrics`: Log to Metrics
Fluent Bit page: [Log to Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | Yes | `log_to_metrics` | Plugin identifier. |
| [`add_label`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Add a custom label NAME and set the value to the value of KEY |
| [`bucket`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Defines a bucket for histogram |
| [`exclude`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Exclude records in which the content of KEY matches the regular expression. |
| [`flush_interval_nsec`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | No |  | The interval for metrics emission, in nanoseconds. |
| [`flush_interval_sec`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | No |  | The interval for metrics emission, in seconds. |
| [`kubernetes_mode`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | No |  | If enabled, it will automatically put pod_id, pod_name, namespace_name, docker_id and container_name into the metric as labels. |
| [`label_field`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Includes a record field as label dimension in the metric. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`metric_description`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Sets a help text for the metric. |
| [`metric_mode`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Defines the mode for the metric. |
| [`metric_name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Sets the name of the metric. |
| [`regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Include records in which the content of KEY matches the regular expression. |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Defines the tag for the generated metrics record |
| [`value_field`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Specify the record field that holds a numerical value |

<a id="filters-lua"></a>
### `lua`: Lua
Fluent Bit page: [Lua](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) | Yes | `lua` | Plugin identifier. |
| [`call`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Lua function name that will be triggered to do filtering. |
| [`code`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Inline LUA code instead of loading from a path via script. |
| [`enable_flb_null`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) | No |  | If enabled, null will be converted to flb_null in Lua. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`protected_mode`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) | No |  | If enabled, Lua script will be executed in protected mode. |
| [`script`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Path to the Lua script that will be used. |
| [`time_as_table`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) | No |  | By default when the Lua script is invoked, the record timestamp is passed as a floating number which might lead to precision loss when it is converted back. |
| [`type_array_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) | No |  | If these keys are matched, the fields are handled as array. |
| [`type_int_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) | No |  | If these keys are matched, the fields are converted to integer. |

<a id="filters-modify"></a>
### `modify`: Modify
Fluent Bit page: [Modify](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) | Yes | `modify` | Plugin identifier. |
| [`add`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) | No |  | Add a key/value pair with key KEY and value VALUE if KEY does not exist |
| [`copy`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) | No |  | Copy a key/value pair with key KEY to COPIED_KEY if KEY exists AND COPIED_KEY does not exist |
| [`hard_copy`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) | No |  | Copy a key/value pair with key KEY to COPIED_KEY if KEY exists. |
| [`hard_rename`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) | No |  | Rename a key/value pair with key KEY to RENAMED_KEY if KEY exists. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`move_to_end`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) | No |  | Move key/value pairs with keys matching KEY to the end of the message |
| [`move_to_start`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) | No |  | Move key/value pairs with keys matching KEY to the start of the message |
| [`remove`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) | No |  | Remove a key/value pair with key KEY if it exists |
| [`remove_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) | No |  | Remove all key/value pairs with key matching regexp KEY |
| [`remove_wildcard`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) | No |  | Remove all key/value pairs with key matching wildcard KEY |
| [`rename`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) | No |  | Rename a key/value pair with key KEY to RENAMED_KEY if KEY exists AND RENAMED_KEY does not exist |
| [`set`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) | No |  | Add a key/value pair with key KEY and value VALUE. |

<a id="filters-multiline"></a>
### `multiline`: Multiline
Fluent Bit page: [Multiline](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) | Yes | `multiline` | Plugin identifier. |
| [`buffer`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Enable buffered mode. |
| [`emitter_mem_buf_limit`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Set a limit on the amount of memory the emitter can consume if the outputs provide backpressure. |
| [`emitter_name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Name for the emitter input instance which re-emits the completed records at the beginning of the pipeline. |
| [`emitter_storage.type`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | The storage type for the emitter input instance. |
| [`flush_ms`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Flush time for pending multiline records. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`mode`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Mode can be parser for regex concat, or partial_message to concat split docker logs. |
| [`multiline.key_content`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Key name that holds the content to process. |
| [`multiline.parser`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Specify one or multiple [Multiline Parser definitions](/manual/3.2/administration/configuring-fluent-bit/multiline-parsing.md) to apply to the content. |

<a id="filters-nest"></a>
### `nest`: Nest
Fluent Bit page: [Nest](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters) | Yes | `nest` | Plugin identifier. |
| [`add_prefix`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters) | No |  | Prefix affected keys with this string |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`nest_under`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters) | No |  | Nest records matching the Wildcard under this key |
| [`nested_under`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters) | No |  | Lift records nested under the Nested_under key |
| [`operation`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters) | No |  | Select the operation nest or lift |
| [`remove_prefix`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters) | No |  | Remove prefix from affected keys if it matches this string |
| [`wildcard`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters) | No |  | Nest records which field matches the wildcard |

<a id="filters-nightfall"></a>
### `nightfall`: Nightfall
Fluent Bit page: [Nightfall](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters) | Yes | `nightfall` | Plugin identifier. |
| [`sampling_rate`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters) | Yes | `1` | The rate controlling how much of your logs you wish to be scanned, must be a float between (0, 1]. |
| [`tls.ca_path`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters) | Yes |  | Absolute path to root certificates, required if tls.verify is true. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`nightfall_api_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters) | No |  | The Nightfall API key to scan your logs with, obtainable from the [Nightfall Dashboard](https://app.nightfall.ai) |
| [`policy_id`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters) | No |  | The Nightfall dev platform policy to scan your logs with, configurable in the [Nightfall Dashboard](https://app.nightfall.ai/developer-platform/policies). |
| [`tls.debug`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters) | No | `0` | Debug level between 0 (nothing) and 4 (every detail). |
| [`tls.verify`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters) | No | `true` | When enabled, turns on certificate validation when connecting to the Nightfall API. |

<a id="filters-parser"></a>
### `parser`: Parser
Fluent Bit page: [Parser](https://docs.fluentbit.io/manual/3.2/pipeline/filters/parser#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/parser#configuration-parameters) | Yes | `parser` | Plugin identifier. |
| [`key_name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/parser#configuration-parameters) | No |  | Specify field name in record to parse. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/parser#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/parser#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`parser`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/parser#configuration-parameters) | No |  | Specify the parser name to interpret the field. |
| [`preserve_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/parser#configuration-parameters) | No | `false` | Keep original Key_Name field in the parsed result. |
| [`reserve_data`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/parser#configuration-parameters) | No | `false` | Keep all other original fields in the parsed result. |

<a id="filters-record-modifier"></a>
### `record_modifier`: Record Modifier
Fluent Bit page: [Record Modifier](https://docs.fluentbit.io/manual/3.2/pipeline/filters/record-modifier#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/record-modifier#configuration-parameters) | Yes | `record_modifier` | Plugin identifier. |
| [`allowlist_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/record-modifier#configuration-parameters) | No |  | If the key isn't matched, that field is removed. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/record-modifier#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/record-modifier#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`record`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/record-modifier#configuration-parameters) | No |  | Append fields. |
| [`remove_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/record-modifier#configuration-parameters) | No |  | If the key is matched, that field is removed. |
| [`uuid_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/record-modifier#configuration-parameters) | No |  | If set, the plugin appends Uuid to each record. |
| [`whitelist_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/record-modifier#configuration-parameters) | No |  | An alias of Allowlist_key for backwards compatibility. |

<a id="filters-rewrite-tag"></a>
### `rewrite_tag`: Rewrite Tag
Fluent Bit page: [Rewrite Tag](https://docs.fluentbit.io/manual/3.2/pipeline/filters/rewrite-tag#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/rewrite-tag#configuration-parameters) | Yes | `rewrite_tag` | Plugin identifier. |
| [`emitter_mem_buf_limit`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/rewrite-tag#configuration-parameters) | No |  | Set a limit on the amount of memory the tag rewrite emitter can consume if the outputs provide backpressure. |
| [`emitter_name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/rewrite-tag#configuration-parameters) | No |  | When the filter emits a record under the new Tag, there is an internal emitter plugin that takes care of the job. |
| [`emitter_storage.type`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/rewrite-tag#configuration-parameters) | No |  | Define a buffering mechanism for the new records created. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/rewrite-tag#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/rewrite-tag#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`rule`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/rewrite-tag#configuration-parameters) | No |  | Defines the matching criteria and the format of the Tag for the matching record. |

<a id="filters-stdout"></a>
### `stdout`: Standard Output
Fluent Bit page: [Standard Output](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | Yes | `stdout` | Plugin identifier. |
| [`match`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |

<a id="filters-sysinfo"></a>
### `sysinfo`: Sysinfo
Fluent Bit page: [Sysinfo](https://docs.fluentbit.io/manual/3.2/pipeline/filters/sysinfo#configuration-prameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/sysinfo#configuration-prameters) | Yes | `sysinfo` | Plugin identifier. |
| [`fluentbit_version_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/sysinfo#configuration-prameters) | No |  | Specify the key name for fluent-bit version. |
| [`hostname_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/sysinfo#configuration-prameters) | No |  | Specify the key name for hostname. |
| [`kernel_version_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/sysinfo#configuration-prameters) | No |  | Specify the key name for kernel version. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/sysinfo#configuration-prameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/sysinfo#configuration-prameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`os_name_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/sysinfo#configuration-prameters) | No |  | Specify the key name for os name. |
| [`os_version_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/sysinfo#configuration-prameters) | No |  | Specify the key name for os version. |

<a id="filters-tensorflow"></a>
### `tensorflow`: Tensorflow
Fluent Bit page: [Tensorflow](https://docs.fluentbit.io/manual/3.2/pipeline/filters/tensorflow#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/tensorflow#configuration-parameters) | Yes | `tensorflow` | Plugin identifier. |
| [`include_input_fields`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/tensorflow#configuration-parameters) | No | `true` | Include all input filed in filter's output |
| [`input_field`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/tensorflow#configuration-parameters) | No |  | Specify the name of the field in the record to apply inference on. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/tensorflow#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/tensorflow#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`model_file`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/tensorflow#configuration-parameters) | No |  | Path to the model file (.tflite) to be loaded by Tensorflow Lite. |
| [`normalization_value`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/tensorflow#configuration-parameters) | No |  | Divide input values to normalization_value |

<a id="filters-throttle"></a>
### `throttle`: Throttle
Fluent Bit page: [Throttle](https://docs.fluentbit.io/manual/3.2/pipeline/filters/throttle#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/throttle#configuration-parameters) | Yes | `throttle` | Plugin identifier. |
| [`interval`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/throttle#configuration-parameters) | No |  | Time interval, expressed in "sleep" format. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/throttle#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/throttle#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`print_status`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/throttle#configuration-parameters) | No |  | Whether to print status messages with current rate and the limits to information logs |
| [`rate`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/throttle#configuration-parameters) | No |  | Amount of messages for the time. |
| [`window`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/throttle#configuration-parameters) | No |  | Amount of intervals to calculate average over. |

<a id="filters-type-converter"></a>
### `type_converter`: Type Converter
Fluent Bit page: [Type Converter](https://docs.fluentbit.io/manual/3.2/pipeline/filters/type-converter#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/type-converter#configuration-parameters) | Yes | `type_converter` | Plugin identifier. |
| [`float_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/type-converter#configuration-parameters) | No |  | This parameter is for float source. |
| [`int_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/type-converter#configuration-parameters) | No |  | This parameter is for integer source. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/type-converter#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/type-converter#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`str_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/type-converter#configuration-parameters) | No |  | This parameter is for string source. |
| [`uint_key`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/type-converter#configuration-parameters) | No |  | This parameter is for unsigned integer source. |

<a id="filters-wasm"></a>
### `wasm`: Wasm
Fluent Bit page: [Wasm](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga) | Yes | `wasm` | Plugin identifier. |
| [`accessible_paths`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Specify the whitelist of paths to be able to access paths from WASM programs. |
| [`event_format`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Define event format to interact with Wasm programs: msgpack or json. |
| [`function_name`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Wasm function name that will be triggered to do filtering. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`wasm_heap_size`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Size of the heap size of Wasm execution. |
| [`wasm_path`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Path to the built Wasm program that will be used. |
| [`wasm_stack_size`](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga) | No |  | Size of the stack size of Wasm execution. |

## Outputs

[`azure`](#outputs-azure), [`azure_blob`](#outputs-azure-blob), [`azure_kusto`](#outputs-azure-kusto), [`azure_logs_ingestion`](#outputs-azure-logs-ingestion), [`bigquery`](#outputs-bigquery), [`chronicle`](#outputs-chronicle), [`cloudwatch_logs`](#outputs-cloudwatch-logs), [`counter`](#outputs-counter), [`dash0`](#outputs-dash0), [`datadog`](#outputs-datadog), [`dynatrace`](#outputs-dynatrace), [`es`](#outputs-es), [`file`](#outputs-file), [`flowcounter`](#outputs-flowcounter), [`forward`](#outputs-forward), [`gelf`](#outputs-gelf), [`http`](#outputs-http), [`influxdb`](#outputs-influxdb), [`kafka`](#outputs-kafka), [`kafka-rest`](#outputs-kafka-rest), [`kinesis_firehose`](#outputs-kinesis-firehose), [`kinesis_streams`](#outputs-kinesis-streams), [`logdna`](#outputs-logdna), [`loki`](#outputs-loki), [`nats`](#outputs-nats), [`newrelic`](#outputs-newrelic), [`null`](#outputs-null), [`observe`](#outputs-observe), [`openobserve`](#outputs-openobserve), [`opensearch`](#outputs-opensearch), [`opentelemetry`](#outputs-opentelemetry), [`oracle_log_analytics`](#outputs-oracle-log-analytics), [`pgsql`](#outputs-pgsql), [`prometheus_exporter`](#outputs-prometheus-exporter), [`prometheus_remote_write`](#outputs-prometheus-remote-write), [`s3`](#outputs-s3), [`skywalking`](#outputs-skywalking), [`slack`](#outputs-slack), [`splunk`](#outputs-splunk), [`stackdriver`](#outputs-stackdriver), [`stdout`](#outputs-stdout), [`syslog`](#outputs-syslog), [`tcp`](#outputs-tcp), [`td`](#outputs-td), [`vivo_exporter`](#outputs-vivo-exporter), [`websocket`](#outputs-websocket)

<a id="outputs-azure"></a>
### `azure`: Azure Log Analytics
Fluent Bit page: [Azure Log Analytics](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) | Yes | `azure` | Plugin identifier. |
| [`customer_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) | No |  | Customer ID or WorkspaceID string. |
| [`log_type`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) | No | `fluentbit` | The name of the event type. |
| [`log_type_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) | No |  | If included, the value for this key will be looked upon in the record and if present, will over-write the log_type. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) | No |  |  |
| [`shared_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) | No |  | The primary or the secondary Connected Sources client authentication key. |
| [`time_generated`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) | No | `off` | If enabled, the HTTP request header 'time-generated-field' will be included so Azure can override the timestamp with the key specified by 'time_key' option. |
| [`time_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) | No | `@timestamp` | Optional parameter to specify the key name where the timestamp will be stored. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-azure-blob"></a>
### `azure_blob`: Azure Blob
Fluent Bit page: [Azure Blob](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | Yes | `azure_blob` | Plugin identifier. |
| [`account_name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | No |  | Azure Storage account name. |
| [`auth_type`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | No | `key` | Specify the type to authenticate against the service. |
| [`auto_create_container`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | No | `on` | If container_name does not exist in the remote service, enabling this option will handle the exception and auto-create the container. |
| [`blob_type`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | No | `appendblob` | Specify the desired blob type. |
| [`container_name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | No |  | Name of the container that will contain the blobs. |
| [`emulator_mode`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | No | `off` | If you want to send data to an Azure emulator service like [Azurite](https://github.com/Azure/Azurite), enable this option so the plugin will format the requests to the expected format. |
| [`endpoint`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | No |  | If you are using an emulator, this option allows you to specify the absolute HTTP address of such service. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`path`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | No |  | Optional path to store your blobs. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | No |  |  |
| [`sas_token`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | No |  | Specify the Azure Storage shared access signatures to authenticate against the service. |
| [`shared_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | No |  | Specify the Azure Storage Shared Key to authenticate against the service. |
| [`tls`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | No | `off` | Enable or disable TLS encryption. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-azure-kusto"></a>
### `azure_kusto`: Azure Data Explorer
Fluent Bit page: [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | Yes | `azure_kusto` | Plugin identifier. |
| [`client_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | Yes |  | Required - The client ID of the AAD registered application. |
| [`client_secret`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | Yes |  | Required - The client secret of the AAD registered application ([App Secret](https://docs.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal#option-2-create-a-new-application-secret)). |
| [`database_name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | Yes |  | Required - The database name. |
| [`ingestion_endpoint`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | Yes |  | Required - The cluster's ingestion endpoint, usually in the form \<https://ingest-cluster\_name.region.kusto.windows.net> |
| [`table_name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | Yes |  | Required - The table name. |
| [`tenant_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | Yes |  | Required - The tenant/domain ID of the AAD registered application. |
| [`compression_enabled`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | No | `true` | If enabled, sends compressed HTTP payload (gzip) to Kusto. |
| [`include_tag_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | No | `On` | If enabled, a tag is appended to output. |
| [`include_time_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | No | `On` | If enabled, a timestamp is appended to output. |
| [`ingestion_endpoint_connect_timeout`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | No | `60` | The connection timeout of various Kusto endpoints in seconds. |
| [`ingestion_mapping_reference`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Optional - The name of a [JSON ingestion mapping](https://docs.microsoft.com/en-us/azure/data-explorer/kusto/management/mappings#json-mapping) that will be used to map the ingested payload into the table columns. |
| [`ingestion_resources_refresh_interval`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | No | `3600` | The ingestion resources refresh interval of Kusto endpoint in seconds. |
| [`log_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | No | `log` | Key name of the log content. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | No |  |  |
| [`tag_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | No | `tag` | The key name of tag. |
| [`time_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | No | `timestamp` | The key name of time. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-azure-logs-ingestion"></a>
### `azure_logs_ingestion`: Azure Logs Ingestion API
Fluent Bit page: [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) | Yes | `azure_logs_ingestion` | Plugin identifier. |
| [`client_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) | Yes |  | Required - The client ID of the AAD application. |
| [`client_secret`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) | Yes |  | Required - The client secret of the AAD application ([App Secret](https://docs.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal#option-2-create-a-new-application-secret)). |
| [`dce_url`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) | Yes |  | Required - Data Collection Endpoint(DCE) URL. |
| [`dcr_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) | Yes |  | Required - Data Collection Rule (DCR) immutable ID (see [this document](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/tutorial-logs-ingestion-portal#collect-information-from-the-dcr) to collect the immutable id) |
| [`table_name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) | Yes |  | Required - The name of the custom log table (include the _CL suffix as well if applicable) |
| [`tenant_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) | Yes |  | Required - The tenant ID of the AAD application. |
| [`compress`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No | `true` | Optional - Enable HTTP payload gzip compression. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No |  |  |
| [`time_generated`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No | `true` | Optional - If enabled, will generate a timestamp and append it to JSON. |
| [`time_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No | `@timestamp` | Optional - Specify the key name where the timestamp will be stored. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-bigquery"></a>
### `bigquery`: Google Cloud BigQuery
Fluent Bit page: [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | Yes | `bigquery` | Plugin identifier. |
| [`dataset_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | Yes |  | The dataset id of the BigQuery dataset to write into. |
| [`google_service_account`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | Yes |  | Email address of the Google service account to impersonate. |
| [`table_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | Yes |  | The table id of the BigQuery table to write into. |
| [`aws_region`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | No |  | Used to construct a regional endpoint for AWS STS to verify AWS credentials obtained by Fluent Bit. |
| [`enable_workload_identity_federation`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | No | `Off` | Enables workload identity federation as an alternative authentication method. |
| [`google_service_credentials`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | No | `Value of the environment variable *$GOOGLE\_SERVICE\_CREDENTIALS*` | Absolute path to a Google Cloud credentials JSON file. |
| [`ignore_unknown_values`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | No | `Off` | Accept rows that contain values that do not match the schema. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`pool_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | No |  | GCP workload identity pool where the identity provider was created. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | No |  |  |
| [`project_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | No | `The value of the `project_id` in the credentials file` | The project id containing the BigQuery dataset to stream into. |
| [`project_number`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | No |  | GCP project number where the identity provider was created. |
| [`provider_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | No |  | GCP workload identity provider. |
| [`skip_invalid_rows`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | No | `Off` | Insert all valid rows of a request, even if invalid rows exist. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-chronicle"></a>
### `chronicle`: Google Chronicle
Fluent Bit page: [Google Chronicle](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) | Yes | `chronicle` | Plugin identifier. |
| [`customer_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) | No |  | The customer id to identify the tenant of Google Chronicle to stream into. |
| [`google_service_credentials`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) | No | `Value of the environment variable *$GOOGLE\_SERVICE\_CREDENTIALS*` | Absolute path to a Google Cloud credentials JSON file. |
| [`log_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) | No |  | By default, the whole log record will be sent to Google Chronicle. |
| [`log_type`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) | No |  | The log type to parse logs as. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) | No |  |  |
| [`project_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) | No | `The value of the `project_id` in the credentials file` | The project id containing the tenant of Google Chronicle to stream into. |
| [`region`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) | No |  | The GCP region in which to store security logs. |
| [`service_account_email`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) | No | `Value of environment variable *$SERVICE\_ACCOUNT\_EMAIL*` | Account email associated with the service. |
| [`service_account_secret`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) | No | `Value of environment variable *$SERVICE\_ACCOUNT\_SECRET*` | Private key content associated with the service account. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-cloudwatch-logs"></a>
### `cloudwatch_logs`: Amazon CloudWatch
Fluent Bit page: [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | Yes | `cloudwatch_logs` | Plugin identifier. |
| [`log_group_template`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | Yes |  | Template for Log Group name using Fluent Bit [record_accessor](https://docs.fluentbit.io/manual/administration/configuring-fluent-bit/classic-mode/record-accessor) syntax. |
| [`log_stream_template`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | Yes |  | Template for Log Stream name using Fluent Bit [record_accessor](https://docs.fluentbit.io/manual/administration/configuring-fluent-bit/classic-mode/record-accessor) syntax. |
| [`metric_dimensions`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | Yes |  | A list of lists containing the dimension keys that will be applied to all metrics. |
| [`auto_create_group`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Automatically create the log group. |
| [`auto_retry_requests`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Immediately retry failed requests to AWS services once. |
| [`endpoint`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Specify a custom endpoint for the CloudWatch Logs API. |
| [`external_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Specify an external ID for the STS API, can be used with the role_arn parameter if your role requires an external ID. |
| [`log_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | An optional parameter that can be used to tell CloudWatch the format of the data. |
| [`log_group_name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | The name of the CloudWatch Log Group that you want log records sent to. |
| [`log_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | By default, the whole log record will be sent to CloudWatch. |
| [`log_retention_days`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | If set to a number greater than zero, and newly create log group's retention policy is set to this many days. |
| [`log_stream_name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | The name of the CloudWatch Log Stream that you want log records sent to. |
| [`log_stream_prefix`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Prefix for the Log Stream name. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`metric_namespace`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | An optional string representing the CloudWatch namespace for the metrics. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  |  |
| [`profile`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Option to specify an AWS Profile for credentials. |
| [`region`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | The AWS region. |
| [`role_arn`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | ARN of an IAM role to assume (for cross account access). |
| [`sts_endpoint`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Specify a custom STS endpoint for the AWS STS API. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) | No |  | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-counter"></a>
### `counter`: Counter
Fluent Bit page: [Counter](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | Yes | `counter` | Plugin identifier. |
| [`match`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  |  |

<a id="outputs-dash0"></a>
### `dash0`: Dash0
Fluent Bit page: [Dash0](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) | Yes | `dash0` | Plugin identifier. |
| [`header`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) | No | `Authorization Bearer {your-Auth-token-here}` | The specific header for bearer authorization, where {your-Auth-token-here} is your Dash0 Auth Token. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) | No | `ingress.eu-west-1.aws.dash0.com` | Your Dash0 ingress endpoint. |
| [`logs_uri`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) | No | `/v1/logs` | Specify an optional HTTP URI for the target web server listening for logs |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`metrics_uri`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) | No | `/v1/metrics` | Specify an optional HTTP URI for the target web server listening for metrics |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) | No | `443` | TCP port of your Dash0 ingress endpoint. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) | No |  |  |
| [`traces_uri`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) | No | `/v1/traces` | Specify an optional HTTP URI for the target web server listening for traces |

<a id="outputs-datadog"></a>
### `datadog`: Datadog
Fluent Bit page: [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | Yes | `datadog` | Plugin identifier. |
| [`apikey`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | Yes |  | Required - Your [Datadog API key](https://app.datadoghq.com/account/settings#api). |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | Yes | `http-intake.logs.datadoghq.com` | Required - The Datadog server where you are sending your logs. |
| [`tls`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | Yes | `off` | Required - End-to-end security communications security protocol. |
| [`compress`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No |  | Recommended - compresses the payload in GZIP format, Datadog supports and recommends setting this to gzip. |
| [`dd_hostname`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No |  | The host the emitted logs should be associated with. |
| [`dd_message_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No |  | By default, the plugin searches for the key 'log' and remap the value to the key 'message'. |
| [`dd_service`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No |  | Recommended - The human readable name for your service generating the logs (e.g. |
| [`dd_source`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No |  | Recommended - A human readable name for the underlying technology of your service (e.g. |
| [`dd_tags`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No |  | Optional - The [tags](https://docs.datadoghq.com/tagging/) you want to assign to your logs in Datadog. |
| [`header`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No |  | Add additional arbitrary HTTP header key/value pair. |
| [`include_tag_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No | `false` | If enabled, a tag is appended to output. |
| [`json_date_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No | `timestamp` | Date key name for output. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No |  |  |
| [`provider`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No |  | To activate the remapping, specify configuration flag provider with value ecs. |
| [`proxy`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No |  | Optional - Specify an HTTP Proxy. |
| [`tag_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No | `tagkey` | The key name of tag. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-dynatrace"></a>
### `dynatrace`: Dynatrace
Fluent Bit page: [Dynatrace](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) | Yes | `dynatrace` | Plugin identifier. |
| [`allow_duplicated_headers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) | No | `false` | Specifies duplicated header use. |
| [`format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) | No | `json` | The data format to be used in the HTTP request body. |
| [`header`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) | No | `Content-Type application/json; charset=utf-8` | The specific header for content-type. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) | No | `{your-environment-id}.live.dynatrace.com` | Your Dynatrace environment hostname where {your-environment-id} is your environment ID. |
| [`json_date_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) | No | `iso8601` | Date format standard for JSON. |
| [`json_date_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) | No | `timestamp` | Fieldname specifying message timestamp. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) | No | `443` | TCP port of your Dynatrace host. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) | No |  |  |
| [`tls`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) | No | `on` | Specify to use TLS. |
| [`tls.verify`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) | No | `on` | TLS verification. |
| [`uri`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) | No | `/api/v2/logs/ingest` | Specify the HTTP URI for Dynatrace log ingest API. |

<a id="outputs-es"></a>
### `es`: Elasticsearch
Fluent Bit page: [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | Yes | `es` | Plugin identifier. |
| [`buffer_size`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | Yes | `512KB` | Specify the buffer size used to read the response from the Elasticsearch HTTP service. |
| [`replace_dots`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | Yes | `Off` | When enabled, replace field name dots with underscore. |
| [`aws_auth`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | Enable AWS Sigv4 Authentication for Amazon OpenSearch Service. |
| [`aws_external_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No |  | External ID for the AWS IAM Role specified with aws_role_arn |
| [`aws_profile`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `default` | AWS profile name |
| [`aws_region`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Specify the AWS region for Amazon OpenSearch Service. |
| [`aws_role_arn`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No |  | AWS IAM Role to assume to put records to your Amazon cluster |
| [`aws_service_name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `es` | Service name to use in AWS Sigv4 signature. |
| [`aws_sts_endpoint`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Specify the custom STS endpoint to be used with STS API for Amazon OpenSearch Service |
| [`cloud_auth`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Specify the credentials to use to connect to Elastic's Elasticsearch Service running on Elastic Cloud |
| [`cloud_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No |  | If using Elastic's Elasticsearch Service you can specify the cloud_id of the cluster running. |
| [`compress`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Set payload compression mechanism. |
| [`current_time_index`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | Use current time for index generation instead of message record. |
| [`generate_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | When enabled, generate _id for outgoing records. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target Elasticsearch instance |
| [`http_passwd`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Password for user defined in HTTP_User |
| [`http_user`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Optional username credential for Elastic X-Pack access |
| [`id_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No |  | If set, _id will be the value of the key from incoming record and Generate_ID option is ignored. |
| [`include_tag_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | When enabled, it append the Tag name to the record. |
| [`index`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `fluent-bit` | Index name |
| [`logstash_dateformat`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `%Y.%m.%d` | Time format based on [strftime](http://man7.org/linux/man-pages/man3/strftime.3.html) to generate the second part of the Index name. |
| [`logstash_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | Enable Logstash format compatibility. |
| [`logstash_prefix`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `logstash` | When Logstash_Format is enabled, the Index name is composed using a prefix and the date, e.g: If Logstash_Prefix is equal to mydata your index will become mydata-YYYY.MM.DD. |
| [`logstash_prefix_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No |  | When included: the value of the key in the record will be evaluated as key reference and overrides Logstash_Prefix for index generation. |
| [`logstash_prefix_separator`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `-` | Set a separator between Logstash_Prefix and date. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`path`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `Empty string` | Elasticsearch accepts new data on HTTP query path /_bulk. |
| [`pipeline`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Define which pipeline the database should use. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `9200` | TCP port of the target Elasticsearch instance |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No |  |  |
| [`suppress_type_name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | When enabled, mapping types is removed and Type option is ignored. |
| [`tag_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `_flb-key` | When Include_Tag_Key is enabled, this property defines the key name for the tag. |
| [`time_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `@timestamp` | When Logstash_Format is enabled, each record will get a new timestamp field. |
| [`time_key_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `%Y-%m-%dT%H:%M:%S` | When Logstash_Format is enabled, this property defines the format of the timestamp. |
| [`time_key_nanos`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | When Logstash_Format is enabled, enabling this property sends nanosecond precision timestamps. |
| [`trace_error`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | If ElasticSearch returns an error, print the ElasticSearch API request and response for diagnostics. |
| [`trace_output`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | Print all ElasticSearch API request payloads to stdout for diagnostics. |
| [`type`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `_doc` | Type name |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `2` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |
| [`write_operation`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) | No | `create` | Write_operation can be any of: create, index, update, upsert. |

<a id="outputs-file"></a>
### `file`: File
Fluent Bit page: [File](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/file#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/file#configuration-parameters) | Yes | `file` | Plugin identifier. |
| [`file`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/file#configuration-parameters) | No |  | Set file name to store the records. |
| [`format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/file#configuration-parameters) | No |  | The format of the file content. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/file#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/file#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`mkdir`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/file#configuration-parameters) | No |  | Recursively create output directory if it does not exist. |
| [`path`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/file#configuration-parameters) | No |  | Directory path to store files. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/file#configuration-parameters) | No |  |  |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/file#configuration-parameters) | No | `1` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-flowcounter"></a>
### `flowcounter`: FlowCounter
Fluent Bit page: [FlowCounter](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/flowcounter#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/flowcounter#configuration-parameters) | Yes | `flowcounter` | Plugin identifier. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/flowcounter#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/flowcounter#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/flowcounter#configuration-parameters) | No |  |  |
| [`unit`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/flowcounter#configuration-parameters) | No | `minute` | The unit of duration. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/flowcounter#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-forward"></a>
### `forward`: Forward
Fluent Bit page: [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) | Yes | `forward` | Plugin identifier. |
| [`compress`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) | No |  | Set to 'gzip' to enable gzip compression. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) | No | `127.0.0.1` | Target host where Fluent-Bit or Fluentd are listening for Forward messages. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) | No | `24224` | TCP Port of the target service. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) | No |  |  |
| [`require_ack_response`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) | No | `false` | Send "chunk"-option and wait for "ack" response from server. |
| [`send_options`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) | No | `false` | Always send options (with "size"=count of messages) |
| [`tag`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) | No |  | Overwrite the tag as we transmit. |
| [`time_as_integer`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) | No | `false` | Set timestamps in integer format, it enable compatibility mode for Fluentd v0.12 series. |
| [`unix_path`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) | No |  | Specify the path to unix socket to send a Forward message. |
| [`upstream`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) | No |  | If Forward will connect to an Upstream instead of a simple host, this property defines the absolute path for the Upstream configuration file, for more details about this refer to the [Upstream Servers ](/manual/3.2/administration/configuring-fluent-bit/classic-mode/upstream-servers.md)documentation section. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) | No | `2` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-gelf"></a>
### `gelf`: GELF
Fluent Bit page: [GELF](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | Yes | `gelf` | Plugin identifier. |
| [`gelf_host_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | Yes | `host` | Key which its value is used as the name of the host, source or application that sent this message. |
| [`gelf_level_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | Yes | `level` | Key to be used as the log level. |
| [`gelf_short_message_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | Yes | `short\_message` | A short descriptive message (MUST be set in GELF) |
| [`compress`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | No | `true` | If transport protocol is udp, you can set this if you want your UDP packets to be compressed. |
| [`gelf_full_message_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | No | `full\_message` | Key to use as the long message that can i.e. |
| [`gelf_tag_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | No |  | Key to be used for tag. |
| [`gelf_timestamp_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | No | `timestamp` | Your log timestamp (SHOULD be set in GELF) |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target Graylog server |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | No |  | Pattern to match which tags of logs to be outputted by this plugin |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`mode`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | No | `udp` | The protocol to use (tls, tcp or udp) |
| [`packet_size`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | No | `1420` | If transport protocol is udp, you can set the size of packets to be sent. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | No | `12201` | The port that your Graylog GELF input is listening on |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | No |  |  |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-http"></a>
### `http`: HTTP
Fluent Bit page: [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | Yes | `http` | Plugin identifier. |
| [`body_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | Yes |  | Specify the key to use as the body of the request (must prefix with "$"). |
| [`headers_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | Yes |  | Specify the key to use as the headers of the request (must prefix with "$"). |
| [`allow_duplicated_headers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No | `true` | Specify if duplicated headers are allowed. |
| [`aws_auth`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No | `false` | Enable AWS SigV4 authentication |
| [`aws_external_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | External ID for the AWS IAM Role specified with aws_role_arn, used by SigV4 authentication |
| [`aws_region`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Specify the AWS region of your service, used by SigV4 authentication |
| [`aws_role_arn`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | AWS IAM Role to assume, used by SigV4 authentication |
| [`aws_service`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Specify the AWS service code, i.e. |
| [`aws_sts_endpoint`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Specify the custom sts endpoint to be used with STS API, used with the AWS_Role_ARN option, used by SigV4 authentication |
| [`compress`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Set payload compression mechanism. |
| [`format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No | `msgpack` | Specify the data format to be used in the HTTP request body, by default it uses msgpack. |
| [`gelf_full_message_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Specify the key to use for the full message in gelf format |
| [`gelf_host_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Specify the key to use for the host in gelf format |
| [`gelf_level_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Specify the key to use for the level in gelf format |
| [`gelf_short_message_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Specify the key to use as the short message in gelf format |
| [`gelf_timestamp_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Specify the key to use for timestamp in gelf format |
| [`header`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Add a HTTP header key/value pair. |
| [`header_tag`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Specify an optional HTTP header field for the original message tag. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target HTTP Server |
| [`http_passwd`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Basic Auth Password. |
| [`http_user`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Basic Auth Username |
| [`json_date_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No | `double` | Specify the format of the date. |
| [`json_date_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No | `date` | Specify the name of the time key in the output record. |
| [`log_response_payload`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No | `true` | Specify if the response paylod should be logged or not. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No | `80` | TCP port of the target HTTP Server |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  |  |
| [`proxy`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No |  | Specify an HTTP Proxy. |
| [`uri`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No | `/` | Specify an optional HTTP URI for the target web server, e.g: /something |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) | No | `2` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-influxdb"></a>
### `influxdb`: InfluxDB
Fluent Bit page: [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | Yes | `influxdb` | Plugin identifier. |
| [`add_integer_suffix`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No | `False`, ` On` | Use integer type of [influxdb's line protocol](https://docs.influxdata.com/influxdb/v1/write_protocols/line_protocol_reference/). |
| [`auto_tags`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No | `Off` | Automatically tag keys where value is string. |
| [`bucket`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No |  | InfluxDB bucket name where records will be inserted - if specified, database is ignored and v2 of API is used |
| [`database`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No | `fluentbit` | InfluxDB database name where records will be inserted |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target InfluxDB service |
| [`http_header`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No |  | Add a HTTP header key/value pair. |
| [`http_passwd`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No |  | Password for user defined in HTTP_User |
| [`http_token`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No |  | Authentication token used with InfluDB v2 - if specified, both HTTP_User and HTTP_Passwd are ignored |
| [`http_user`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No |  | Optional username for HTTP Basic Authentication |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`org`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No | `fluent` | InfluxDB organization name where the bucket is (v2 only) |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No | `8086` | TCP port of the target InfluxDB service |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No |  |  |
| [`sequence_tag`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No | `\_seq` | The name of the tag whose value is incremented for the consecutive simultaneous events. |
| [`tag_keys`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No |  | Space separated list of keys that needs to be tagged |
| [`uri`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No |  | Custom URI endpoint |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-kafka"></a>
### `kafka`: Kafka
Fluent Bit page: [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | Yes | `kafka` | Plugin identifier. |
| [`brokers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No |  | Single or multiple list of Kafka Brokers, e.g: 192.168.1.3:9092, 192.168.1.4:9092. |
| [`dynamic_topic`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No | `Off` | adds unknown topics (found in Topic_Key) to Topics. |
| [`format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No | `json` | Specify data format, options available: json, msgpack, raw. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`message_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No |  | Optional key to store the message |
| [`message_key_field`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No |  | If set, the value of Message_Key_Field in the record will indicate the message key. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No |  |  |
| [`queue_full_retries`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No | `10` | Fluent Bit queues data into rdkafka library, if for some reason the underlying library cannot flush the records the queue might fills up blocking new addition of records. |
| [`raw_log_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No |  | When using the raw format and set, the value of raw_log_key in the record will be send to kafka as the payload. |
| [`rdkafka.{property}`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No |  | {property} can be any [librdkafka properties](https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md) |
| [`timestamp_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No | `double` | Specify timestamp format, should be 'double', '[iso8601](https://en.wikipedia.org/wiki/ISO_8601)' (seconds precision) or 'iso8601_ns' (fractional seconds precision) |
| [`timestamp_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No | `@timestamp` | Set the key to store the record timestamp |
| [`topic_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No |  | If multiple Topics exists, the value of Topic_Key in the record will indicate the topic to use. |
| [`topics`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No | `fluent-bit` | Single entry or list of topics separated by comma (, ) that Fluent Bit will use to send messages to Kafka. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-kafka-rest"></a>
### `kafka-rest`: Kafka REST Proxy
Fluent Bit page: [Kafka REST Proxy](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) | Yes | `kafka-rest` | Plugin identifier. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target Kafka REST Proxy server |
| [`include_tag_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `Off` | Append the Tag name to the final record. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`message_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No |  | Set a message key (optional) |
| [`partition`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No |  | Set the partition number (optional) |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `8082` | TCP port of the target Kafka REST Proxy server |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No |  |  |
| [`tag_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `\_flb-key` | If Include_Tag_Key is enabled, this property defines the key name for the tag. |
| [`time_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `@timestamp` | The Time_Key property defines the name of the field that holds the record timestamp. |
| [`time_key_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `%Y-%m-%dT%H:%M:%S` | Defines the format of the timestamp. |
| [`topic`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `fluent-bit` | Set the Kafka topic |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-kinesis-firehose"></a>
### `kinesis_firehose`: Amazon Kinesis Data Firehose
Fluent Bit page: [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | Yes | `kinesis_firehose` | Plugin identifier. |
| [`auto_retry_requests`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  | Immediately retry failed requests to AWS services once. |
| [`compression`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  | Compression type for Firehose records. |
| [`delivery_stream`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  | The name of the Kinesis Firehose Delivery stream that you want log records sent to. |
| [`endpoint`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  | Specify a custom endpoint for the Firehose API. |
| [`external_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  | Specify an external ID for the STS API, can be used with the role_arn parameter if your role requires an external ID. |
| [`log_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  | By default, the whole log record will be sent to Firehose. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  |  |
| [`profile`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  | AWS profile name to use. |
| [`region`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  | The AWS region. |
| [`role_arn`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  | ARN of an IAM role to assume (for cross account access). |
| [`sts_endpoint`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  | Custom endpoint for the STS API. |
| [`time_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  | Add the timestamp to the record under this key. |
| [`time_key_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  | strftime compliant format string for the timestamp; for example, the default is '%Y-%m-%dT%H:%M:%S'. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) | No |  | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-kinesis-streams"></a>
### `kinesis_streams`: Amazon Kinesis Data Streams
Fluent Bit page: [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | Yes | `kinesis_streams` | Plugin identifier. |
| [`auto_retry_requests`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  | Immediately retry failed requests to AWS services once. |
| [`endpoint`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  | Specify a custom endpoint for the Kinesis API. |
| [`external_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  | Specify an external ID for the STS API, can be used with the role_arn parameter if your role requires an external ID. |
| [`log_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  | By default, the whole log record will be sent to Kinesis. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  | TCP port of the Kinesis Streams service. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  |  |
| [`profile`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  | AWS profile name to use. |
| [`region`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  | The AWS region. |
| [`role_arn`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  | ARN of an IAM role to assume (for cross account access). |
| [`stream`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  | The name of the Kinesis Streams Delivery stream that you want log records sent to. |
| [`sts_endpoint`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  | Custom endpoint for the STS API. |
| [`time_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  | Add the timestamp to the record under this key. |
| [`time_key_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  | strftime compliant format string for the timestamp; for example, the default is '%Y-%m-%dT%H:%M:%S'. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) | No |  | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-logdna"></a>
### `logdna`: LogDNA
Fluent Bit page: [LogDNA](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) | Yes | `logdna` | Plugin identifier. |
| [`api_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) | No |  | API key to get access to the service. |
| [`app`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) | No | `Fluent Bit` | Name of the application. |
| [`file`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) | No |  | Optional name of a file being monitored. |
| [`hostname`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) | No |  | <p>Name of the local machine or device where Fluent Bit is running.<br></p><p>When this value is not set, Fluent Bit lookup the hostname and auto populate the value. |
| [`ip`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) | No |  | IP address of the local hostname. |
| [`logdna_endpoint`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) | No | `/logs/ingest` | LogDNA ingestion endpoint |
| [`logdna_host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) | No | `logs.logdna.com` | LogDNA API host address |
| [`logdna_port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) | No | `443` | LogDNA TCP Port |
| [`mac`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) | No |  | Mac address. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) | No |  |  |
| [`tags`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) | No |  | A list of comma separated strings to group records in LogDNA and simplify the query with filters. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) | No | `\`0\` | The number of [workers](https://docs.fluentbit.io/manual/administration/multithreading#outputs) to perform flush operations for this output. |

<a id="outputs-loki"></a>
### `loki`: Loki
Fluent Bit page: [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | Yes | `loki` | Plugin identifier. |
| [`uri`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | Yes | `/loki/api/v1/push` | Specify a custom HTTP URI. |
| [`auto_kubernetes_labels`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No | `off` | If set to true, it will add all Kubernetes labels to the Stream labels |
| [`bearer_token`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No |  | Set bearer token authentication token value. |
| [`compress`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No |  | Set payload compression mechanism. |
| [`drop_single_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No | `off` | If set to true and after extracting labels only a single key remains, the log line sent to Loki will be the value of that key in line_format. |
| [`header`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No |  | Add additional arbitrary HTTP header key/value pair. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No | `127.0.0.1` | Loki hostname or IP address. |
| [`http_passwd`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No |  | Set HTTP basic authentication password |
| [`http_user`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No |  | Set HTTP basic authentication user name |
| [`label_keys`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No |  | Optional list of record keys that will be placed as stream labels. |
| [`label_map_path`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No |  | Specify the label map file path. |
| [`labels`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No | `job=fluent-bit` | Stream labels for API request. |
| [`line_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No | `json` | Format to use when flattening the record to a log line. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No | `3100` | Loki TCP port |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No |  |  |
| [`remove_keys`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No |  | Optional list of keys to remove. |
| [`structured_metadata`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No |  | Optional comma-separated list of key=value strings specifying structured metadata for the log line. |
| [`structured_metadata_map_keys`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No |  | Optional comma-separated list of record key strings specifying record values of type map, used to dynamically populate structured metadata for the log line. |
| [`tenant_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No |  | Tenant ID used by default to push logs to Loki. |
| [`tenant_id_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No |  | Specify the name of the key from the original record that contains the Tenant ID. |
| [`tls`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No | `off` | Use TLS authentication |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-nats"></a>
### `nats`: NATS
Fluent Bit page: [NATS](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/nats#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/nats#configuration-parameters) | Yes | `nats` | Plugin identifier. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/nats#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the NATS Server |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/nats#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/nats#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/nats#configuration-parameters) | No | `4222` | TCP port of the target NATS Server |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/nats#configuration-parameters) | No |  |  |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/nats#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-newrelic"></a>
### `newrelic`: New Relic
Fluent Bit page: [New Relic](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | Yes | `newrelic` | Plugin identifier. |
| [`match`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  |  |

<a id="outputs-null"></a>
### `null`: NULL
Fluent Bit page: [NULL](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | Yes | `null` | Plugin identifier. |
| [`match`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  |  |

<a id="outputs-observe"></a>
### `observe`: Observe
Fluent Bit page: [Observe](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) | Yes | `observe` | Plugin identifier. |
| [`compress`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) | No | `gzip` | Set payload compression mechanism. |
| [`format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) | No | `msgpack` | The data format to be used in the HTTP request body |
| [`header`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) | No | `Authorization Bearer ${OBSERVE\_TOKEN}` | The specific header that provides the Observe token needed to authorize sending data [into a datastream](https://docs.observeinc.com/en/latest/content/data-ingestion/datastreams.html?highlight=ingest%20token#create-a-datastream). |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) | No | `OBSERVE\_CUSTOMER.collect.observeinc.com` | IP address or hostname of Observe's data collection endpoint. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) | No | `443` | TCP port of to employ when sending to Observe |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) | No |  |  |
| [`tls`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) | No | `on` | Specify to use tls |
| [`tls.ca_file`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) | No |  | For use with Windows: provide path to root cert |
| [`uri`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) | No | `/v1/http/fluentbit` | Specify the HTTP URI for the Observe's data ingest |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-openobserve"></a>
### `openobserve`: OpenObserve
Fluent Bit page: [OpenObserve](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | Yes | `openobserve` | Plugin identifier. |
| [`match`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  |  |

<a id="outputs-opensearch"></a>
### `opensearch`: OpenSearch
Fluent Bit page: [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | Yes | `opensearch` | Plugin identifier. |
| [`buffer_size`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | Yes | `4KB` | Specify the buffer size used to read the response from the OpenSearch HTTP service. |
| [`aws_auth`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | Enable AWS Sigv4 Authentication for Amazon OpenSearch Service |
| [`aws_external_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No |  | External ID for the AWS IAM Role specified with aws_role_arn |
| [`aws_profile`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `default` | AWS profile name |
| [`aws_region`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No |  | Specify the AWS region for Amazon OpenSearch Service |
| [`aws_role_arn`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No |  | AWS IAM Role to assume to put records to your Amazon cluster |
| [`aws_service_name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `es` | Service name to be used in AWS Sigv4 signature. |
| [`aws_sts_endpoint`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No |  | Specify the custom sts endpoint to be used with STS API for Amazon OpenSearch Service |
| [`compress`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No |  | Set payload compression mechanism. |
| [`current_time_index`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | Use current time for index generation instead of message record |
| [`generate_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | When enabled, generate _id for outgoing records. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target OpenSearch instance |
| [`http_passwd`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No |  | Password for user defined in HTTP_User |
| [`http_user`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No |  | Optional username credential for access |
| [`id_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No |  | If set, _id will be the value of the key from incoming record and Generate_ID option is ignored. |
| [`include_tag_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | When enabled, it append the Tag name to the record. |
| [`index`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `fluent-bit` | Index name, supports [Record Accessor syntax](/manual/3.2/administration/configuring-fluent-bit/classic-mode/record-accessor.md) from 2.0.5 onwards. |
| [`logstash_dateformat`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `%Y.%m.%d` | Time format (based on [strftime](http://man7.org/linux/man-pages/man3/strftime.3.html)) to generate the second part of the Index name. |
| [`logstash_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | Enable Logstash format compatibility. |
| [`logstash_prefix`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `logstash` | When Logstash_Format is enabled, the Index name is composed using a prefix and the date, e.g: If Logstash_Prefix is equals to 'mydata' your index will become 'mydata-YYYY.MM.DD'. |
| [`logstash_prefix_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No |  | When included: the value of the key in the record will be evaluated as key reference and overrides Logstash_Prefix for index generation. |
| [`logstash_prefix_separator`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No |  | Set a separator between logstash_prefix and date. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`path`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `Empty string` | OpenSearch accepts new data on HTTP query path "/_bulk". |
| [`pipeline`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No |  | OpenSearch allows to setup filters called pipelines. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `9200` | TCP port of the target OpenSearch instance |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No |  |  |
| [`replace_dots`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | When enabled, replace field name dots with underscore. |
| [`suppress_type_name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | When enabled, mapping types is removed and Type option is ignored. |
| [`tag_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `\_flb-key` | When Include_Tag_Key is enabled, this property defines the key name for the tag. |
| [`time_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `@timestamp` | When Logstash_Format is enabled, each record will get a new timestamp field. |
| [`time_key_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `%Y-%m-%dT%H:%M:%S` | When Logstash_Format is enabled, this property defines the format of the timestamp. |
| [`time_key_nanos`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | When Logstash_Format is enabled, enabling this property sends nanosecond precision timestamps. |
| [`trace_error`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | When enabled print the OpenSearch API calls to stdout when OpenSearch returns an error (for diag only) |
| [`trace_output`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | When enabled print the OpenSearch API calls to stdout (for diag only) |
| [`type`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `\_doc` | Type name. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |
| [`write_operation`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) | No | `create` | Operation to use to write in bulk requests. |

<a id="outputs-opentelemetry"></a>
### `opentelemetry`: OpenTelemetry
Fluent Bit page: [OpenTelemetry](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | Yes | `opentelemetry` | Plugin identifier. |
| [`match`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  |  |

<a id="outputs-oracle-log-analytics"></a>
### `oracle_log_analytics`: Oracle Log Analytics
Fluent Bit page: [Oracle Log Analytics](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/oci-logging-analytics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/oci-logging-analytics#configuration-parameters) | Yes | `oracle_log_analytics` | Plugin identifier. |
| [`proxy`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/oci-logging-analytics#configuration-parameters) | Yes |  | define proxy if required, in [http://host:port](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http:/host:port) format, supports only http protocol |
| [`config_file_location`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | The location of the configuration file containing OCI authentication details. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`namespace`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | OCI Tenancy Namespace in which the collected log data is to be uploaded |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  |  |
| [`profile_name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/oci-logging-analytics#configuration-parameters) | No | `DEFAULT` | OCI Config Profile Name to be used from the configuration file |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/oci-logging-analytics#configuration-parameters) | No | `1` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-pgsql"></a>
### `pgsql`: PostgreSQL
Fluent Bit page: [PostgreSQL](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | Yes | `pgsql` | Plugin identifier. |
| [`async`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No | `false` | Define if we will use async or sync connections |
| [`cockroachdb`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No | `false` | Set to true if you will connect the plugin with a CockroachDB |
| [`connection_options`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No |  | Specifies any valid [PostgreSQL connection options](https://www.postgresql.org/docs/devel/libpq-connect.html#LIBPQ-CONNECT-OPTIONS) |
| [`database`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No | `- (current user)` | Database name to connect to |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No | `- (127.0.0.1)` | Hostname/IP address of the PostgreSQL instance |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`max_pool_size`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No | `4` | Maximum amount of connections in async mode |
| [`min_pool_size`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No | `1` | Minimum number of connection in async mode |
| [`password`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No |  | Password of PostgreSQL username |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No | `- (5432)` | PostgreSQL port |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No |  |  |
| [`table`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No |  | Table name where to store data |
| [`timestamp_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No | `date` | Key in the JSON object containing the record timestamp |
| [`user`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No | `- (current user)` | PostgreSQL username |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-prometheus-exporter"></a>
### `prometheus_exporter`: Prometheus Exporter
Fluent Bit page: [Prometheus Exporter](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | Yes | `prometheus_exporter` | Plugin identifier. |
| [`match`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  |  |

<a id="outputs-prometheus-remote-write"></a>
### `prometheus_remote_write`: Prometheus Remote Write
Fluent Bit page: [Prometheus Remote Write](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | Yes | `prometheus_remote_write` | Plugin identifier. |
| [`match`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) | No |  |  |

<a id="outputs-s3"></a>
### `s3`: Amazon S3
Fluent Bit page: [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | Yes | `s3` | Plugin identifier. |
| [`s3_key_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | Yes | `/fluent-bit-logs/$TAG/%Y/%m/%d/%H/%M/%S` | Format string for keys in S3. |
| [`send_content_md5`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | Yes | `false` | Send the Content-MD5 header with PutObject and UploadPart requests, as is required when Object Lock is enabled. |
| [`auto_retry_requests`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `true` | Immediately retry failed requests to AWS services once. |
| [`bucket`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No |  | S3 Bucket name |
| [`canned_acl`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No |  | [Predefined Canned ACL policy](https://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#canned-acl) for S3 objects. |
| [`compression`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No |  | Compression type for S3 objects. |
| [`content_type`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No |  | A standard MIME type for the S3 object, set as the Content-Type HTTP header. |
| [`endpoint`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No |  | Custom endpoint for the S3 API. |
| [`external_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No |  | Specify an external ID for the STS API. |
| [`json_date_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `iso8601` | Specify the format of the date. |
| [`json_date_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `date` | Specify the time key name in the output record. |
| [`log_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No |  | By default, the whole log record will be sent to S3. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`preserve_data_ordering`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `true` | When an upload request fails, the last received chunk might swap with a later chunk, resulting in data shuffling. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No |  |  |
| [`profile`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `default` | Option to specify an AWS Profile for credentials. |
| [`region`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `us-east-1` | The AWS region of your S3 bucket. |
| [`retry_limit`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `1` | Integer value to set the maximum number of retries allowed. |
| [`role_arn`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No |  | ARN of an IAM role to assume (for example, for cross account access.) |
| [`s3_key_format_tag_delimiters`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `.` | A series of characters used to split the tag into parts for use with s3_key_format. |
| [`static_file_path`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `false` | Disables behavior where UUID string appends to the end of the S3 key name when $UUID isn't provided in s3_key_format. |
| [`storage_class`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No |  | Specify the [storage class](https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html#AmazonS3-PutObject-request-header-StorageClass) for S3 objects. |
| [`store_dir`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `/tmp/fluent-bit/s3` | Directory to locally buffer data before sending. |
| [`store_dir_limit_size`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `0` (unlimited)` | Size limit for disk usage in S3. |
| [`sts_endpoint`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No |  | Custom endpoint for the STS API. |
| [`total_file_size`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `100M` | Specify file size in S3. |
| [`upload_chunk_size`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `5, 242, 880 bytes` | The size of each part for multipart uploads. |
| [`upload_timeout`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `10m` | When this amount of time elapses, Fluent Bit uploads and creates a new file in S3. |
| [`use_put_object`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `false` | Use the S3 PutObject API instead of the multipart upload API. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) | No | `1` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-skywalking"></a>
### `skywalking`: SkyWalking
Fluent Bit page: [SkyWalking](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) | Yes | `skywalking` | Plugin identifier. |
| [`auth_token`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) | No |  | Authentication token if needed for Apache SkyWalking OAP |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) | No | `127.0.0.1` | Hostname of Apache SkyWalking OAP |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) | No | `12800` | TCP port of the Apache SkyWalking OAP |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) | No |  |  |
| [`svc_inst_name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) | No | `fluent-bit` | Service instance name of fluent-bit |
| [`svc_name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) | No | `sw-service` | Service name that fluent-bit belongs to |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-slack"></a>
### `slack`: Slack
Fluent Bit page: [Slack](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/slack#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/slack#configuration-parameters) | Yes | `slack` | Plugin identifier. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/slack#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/slack#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/slack#configuration-parameters) | No |  |  |
| [`webhook`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/slack#configuration-parameters) | No |  | Absolute address of the Webhook provided by Slack |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/slack#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-splunk"></a>
### `splunk`: Splunk
Fluent Bit page: [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) | Yes | `splunk` | Plugin identifier. |
| [`channel`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) | No |  | Specify X-Splunk-Request-Channel Header for the HTTP Event Collector interface. |
| [`compress`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) | No |  | Set payload compression mechanism. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target Splunk service. |
| [`http_buffer_size`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) | No | `2M` | Buffer size used to receive Splunk HTTP responses |
| [`http_debug_bad_request`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) | No |  | If the HTTP server response code is 400 (bad request) and this flag is enabled, it will print the full HTTP request and response to the stdout interface. |
| [`http_passwd`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) | No |  | Password for user defined in HTTP_User |
| [`http_user`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) | No |  | Optional username for Basic Authentication on HEC |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) | No | `8088` | TCP port of the target Splunk service. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) | No |  |  |
| [`splunk_token`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) | No |  | Specify the Authentication Token for the HTTP Event Collector interface. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) | No | `2` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-stackdriver"></a>
### `stackdriver`: Stackdriver
Fluent Bit page: [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | Yes | `stackdriver` | Plugin identifier. |
| [`job`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | Yes |  | An identifier for a grouping of related task, such as the name of a microservice or distributed batch. |
| [`k8s_cluster_location`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | Yes |  | The physical location of the cluster that contains (node or pod based on the resource type) the container. |
| [`k8s_cluster_name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | Yes |  | The name of the cluster that the container (node or pod based on the resource type) is running in. |
| [`location`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | Yes |  | The GCP or AWS region in which to store data about the resource. |
| [`namespace`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | Yes |  | A namespace identifier, such as a cluster name or environment. |
| [`node_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | Yes |  | A unique identifier for the node within the namespace, such as hostname or IP address. |
| [`tag_prefix`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | Yes | `k8s\_container., k8s\_pod., k8s\_node.` | Set the tag_prefix used to validate the tag of logs with k8s resource type. |
| [`task_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | Yes |  | A unique identifier for the task within the namespace and job, such as a replica index identifying the task within the job. |
| [`autoformat_stackdriver_trace`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No | `false` | Rewrite the trace field to include the projectID and format it for use with Cloud Trace. |
| [`cloud_logging_base_url`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No | `<https://logging.googleapis.com>` | Set the base Cloud Logging API URL to use for the /v2/entries:write API request. |
| [`compress`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No |  | Set payload compression mechanism. |
| [`custom_k8s_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No | `(?<pod_name>[a-z0-9](?:[-a-z0-9]*[a-z0-9])?(?:\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*)_(?<namespace_name>[^_]+)_(?<container_name>.+)-(?<docker_id>[a-z0-9]{64})\.log$` | Set a custom regex to extract field like pod_name, namespace_name, container_name and docker_id from the local_resource_id in logs. |
| [`export_to_project_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No | `Defaults to the project ID of the google\_service\_credentials file, or the project\_id from Google's metadata.google.internal server.` | The GCP project that should receive these logs. |
| [`google_service_credentials`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No | `Value of environment variable *$GOOGLE\_APPLICATION\_CREDENTIALS*` | Absolute path to a Google Cloud credentials JSON file |
| [`labels`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No |  | Optional list of comma separated of strings specifying key=value pairs. |
| [`labels_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No | `logging.googleapis.com/labels`. See [Stackdriver Special Fields](https://github.com/fluent/fluent-bit-docs/blob/master/pipeline/outputs/stackdriver_special_fields.md#log-entry-fields) for more info.` | The value of this field is used by the Stackdriver output plugin to find the related labels from jsonPayload and then extract the value of it to set the LogEntry Labels. |
| [`log_name_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No | `logging.googleapis.com/logName`. See [Stackdriver Special Fields](https://github.com/fluent/fluent-bit-docs/blob/master/pipeline/outputs/stackdriver_special_fields.md#log-entry-fields) for more info.` | The value of this field is used by the Stackdriver output plugin to extract logName from jsonPayload and set the logName field. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`metadata_server`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No | `<http://metadata.google.internal>` | Prefix for a metadata server. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No |  |  |
| [`project_id_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No | `logging.googleapis.com/projectId`. See [Stackdriver Special Fields](https://github.com/fluent/fluent-bit-docs/blob/master/pipeline/outputs/stackdriver_special_fields.md#log-entry-fields) for more info.` | The value of this field is used by the Stackdriver output plugin to find the gcp project id from jsonPayload and then extract the value of it to set the PROJECT_ID within LogEntry logName, which controls the gcp project that should receive these logs. |
| [`resource`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No | `global, gce\_instance` | Set resource type of data. |
| [`resource_labels`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No |  | An optional list of comma separated strings specifying resource labels plaintext assignments (new=value) and/or mappings from an original field in the log entry to a destination field (destination=$original). |
| [`service_account_email`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No | `Value of environment variable *$SERVICE\_ACCOUNT\_EMAIL*` | Account email associated to the service. |
| [`service_account_secret`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No | `Value of environment variable *$SERVICE\_ACCOUNT\_SECRET*` | Private key content associated with the service account. |
| [`severity_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No | `logging.googleapis.com/severity`. See [Stackdriver Special Fields](https://github.com/fluent/fluent-bit-docs/blob/master/pipeline/outputs/stackdriver_special_fields.md#log-entry-fields) for more info.` | Specify the name of the key from the original record that contains the severity information. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) | No | `1` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-stdout"></a>
### `stdout`: Standard Output
Fluent Bit page: [Standard Output](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/standard-output#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/standard-output#configuration-parameters) | Yes | `stdout` | Plugin identifier. |
| [`format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/standard-output#configuration-parameters) | No | `msgpack` | Specify the data format to be printed. |
| [`json_date_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/standard-output#configuration-parameters) | No | `double` | Specify the format of the date. |
| [`json_date_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/standard-output#configuration-parameters) | No | `date` | Specify the name of the time key in the output record. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/standard-output#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/standard-output#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/standard-output#configuration-parameters) | No |  |  |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/standard-output#configuration-parameters) | No | `1` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-syslog"></a>
### `syslog`: Syslog
Fluent Bit page: [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | Yes | `syslog` | Plugin identifier. |
| [`syslog_maxsize`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | Yes |  | <p>The maximum size allowed per message. |
| [`allow_longer_sd_id`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No | `false` | If true, Fluent-bit allows SD-ID that is longer than 32 characters. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No | `127.0.0.1` | Domain or IP address of the remote Syslog server. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`mode`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No | `udp` | Desired transport type. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No | `514` | TCP or UDP port of the remote Syslog server. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No |  |  |
| [`syslog_appname_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No |  | The key name from the original record that contains the application name that generated the message. |
| [`syslog_appname_preset`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No |  | The preset application name. |
| [`syslog_facility_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No |  | The key name from the original record that contains the Syslog facility number. |
| [`syslog_facility_preset`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No | `1` | The preset facility number. |
| [`syslog_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No | `rfc5424` | The Syslog protocol format to use. |
| [`syslog_hostname_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No |  | The key name from the original record that contains the hostname that generated the message. |
| [`syslog_hostname_preset`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No |  | The preset hostname. |
| [`syslog_message_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No |  | The key name from the original record that contains the message to deliver. |
| [`syslog_msgid_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No |  | The key name from the original record that contains the Message ID associated to the message. |
| [`syslog_msgid_preset`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No |  | The preset message ID. |
| [`syslog_procid_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No |  | The key name from the original record that contains the Process ID that generated the message. |
| [`syslog_procid_preset`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No |  | The preset process ID. |
| [`syslog_sd_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No |  | The key name from the original record that contains a map of key/value pairs to use as Structured Data (SD) content. |
| [`syslog_severity_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No |  | The key name from the original record that contains the Syslog severity number. |
| [`syslog_severity_preset`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No | `6` | The preset severity number. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-tcp"></a>
### `tcp`: TCP & TLS
Fluent Bit page: [TCP & TLS](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) | Yes | `tcp` | Plugin identifier. |
| [`format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) | No | `msgpack` | Specify the data format to be printed. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) | No | `127.0.0.1` | Target host where Fluent-Bit or Fluentd are listening for Forward messages. |
| [`json_date_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) | No | `double` | Specify the format of the date. |
| [`json_date_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) | No | `date` | Specify the name of the time key in the output record. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) | No | `5170` | TCP Port of the target service. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) | No |  |  |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) | No | `2` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-td"></a>
### `td`: Treasure Data
Fluent Bit page: [Treasure Data](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/treasure-data#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/treasure-data#configuration-parameters) | Yes | `td` | Plugin identifier. |
| [`api`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/treasure-data#configuration-parameters) | No |  | The [Treasure Data](http://treasuredata.com) API key. |
| [`database`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/treasure-data#configuration-parameters) | No |  | Specify the name of your target database. |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/treasure-data#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/treasure-data#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/treasure-data#configuration-parameters) | No |  |  |
| [`region`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/treasure-data#configuration-parameters) | No | `US` | Set the service region, available values: US and JP |
| [`table`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/treasure-data#configuration-parameters) | No |  | Specify the name of your target table where the records will be stored. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/treasure-data#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-vivo-exporter"></a>
### `vivo_exporter`: Vivo Exporter
Fluent Bit page: [Vivo Exporter](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/vivo-exporter#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/vivo-exporter#configuration-parameters) | Yes | `vivo_exporter` | Plugin identifier. |
| [`empty_stream_on_read`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/vivo-exporter#configuration-parameters) | No | `Off` | If enabled, when an HTTP client consumes the data from a stream, the stream content will be removed. |
| [`http_cors_allow_origin`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/vivo-exporter#configuration-parameters) | No |  | Specify the value for the HTTP Access-Control-Allow-Origin header (CORS). |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/vivo-exporter#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/vivo-exporter#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/vivo-exporter#configuration-parameters) | No |  |  |
| [`stream_queue_size`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/vivo-exporter#configuration-parameters) | No | `20M` | Specify the maximum queue size per stream. |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/vivo-exporter#configuration-parameters) | No | `1` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-websocket"></a>
### `websocket`: WebSocket
Fluent Bit page: [WebSocket](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) | Yes | `websocket` | Plugin identifier. |
| [`format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) | No | `msgpack` | Specify the data format to be used in the HTTP request body, by default it uses msgpack. |
| [`header`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) | No |  | Add a HTTP header key/value pair. |
| [`host`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target WebSocket Server |
| [`json_date_format`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) | No | `double` | Specify the format of the date. |
| [`json_date_key`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) | No | `date` | Specify the name of the date field in output |
| [`match`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) | No | `80` | TCP port of the target WebSocket Server |
| [`processors`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) | No |  |  |
| [`uri`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) | No | `/` | Specify an optional HTTP URI for the target websocket server, e.g: /something |
| [`workers`](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) | No | `0` | The number of [workers](/manual/3.2/administration/multithreading.md#outputs) to perform flush operations for this output. |
