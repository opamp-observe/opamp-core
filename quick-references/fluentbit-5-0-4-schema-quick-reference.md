# Fluent Bit 5.0.4 Schema Quick Reference

Generated from the local Fluent Bit 5.0.4 JSON schema only:
- `config-service\src\config_service\json-schemas\fluentbit-5.0.4-config-schema.json`

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
- **Inputs**: [`blob`](#inputs-blob), [`collectd`](#inputs-collectd), [`cpu`](#inputs-cpu), [`disk`](#inputs-disk), [`docker`](#inputs-docker), [`docker_events`](#inputs-docker-events), [`dummy`](#inputs-dummy), [`ebpf`](#inputs-ebpf), [`elasticsearch`](#inputs-elasticsearch), [`exec`](#inputs-exec), [`exec_wasi`](#inputs-exec-wasi), [`fluentbit_logs`](#inputs-fluentbit-logs), [`fluentbit_metrics`](#inputs-fluentbit-metrics), [`forward`](#inputs-forward), [`gpu_metrics`](#inputs-gpu-metrics), [`head`](#inputs-head), [`health`](#inputs-health), [`http`](#inputs-http), [`kafka`](#inputs-kafka), [`kmsg`](#inputs-kmsg), [`kubernetes_events`](#inputs-kubernetes-events), [`mem`](#inputs-mem), [`mqtt`](#inputs-mqtt), [`netif`](#inputs-netif), [`nginx_metrics`](#inputs-nginx-metrics), [`node_exporter_metrics`](#inputs-node-exporter-metrics), [`opentelemetry`](#inputs-opentelemetry), [`podman_metrics`](#inputs-podman-metrics), [`proc`](#inputs-proc), [`process_exporter_metrics`](#inputs-process-exporter-metrics), [`prometheus-textfile`](#inputs-prometheus-textfile), [`prometheus_remote_write`](#inputs-prometheus-remote-write), [`prometheus_scrape`](#inputs-prometheus-scrape), [`random`](#inputs-random), [`serial`](#inputs-serial), [`splunk`](#inputs-splunk), [`statsd`](#inputs-statsd), [`stdin`](#inputs-stdin), [`syslog`](#inputs-syslog), [`systemd`](#inputs-systemd), [`tail`](#inputs-tail), [`tcp`](#inputs-tcp), [`thermal`](#inputs-thermal), [`udp`](#inputs-udp), [`windows_exporter_metrics`](#inputs-windows-exporter-metrics), [`winevtlog`](#inputs-winevtlog), [`winlog`](#inputs-winlog), [`winstat`](#inputs-winstat)
- **Filters**: [`aws`](#filters-aws), [`checklist`](#filters-checklist), [`ecs`](#filters-ecs), [`expect`](#filters-expect), [`geoip2`](#filters-geoip2), [`grep`](#filters-grep), [`kubernetes`](#filters-kubernetes), [`log_to_metrics`](#filters-log-to-metrics), [`lua`](#filters-lua), [`modify`](#filters-modify), [`multiline`](#filters-multiline), [`nest`](#filters-nest), [`nightfall`](#filters-nightfall), [`parser`](#filters-parser), [`record_modifier`](#filters-record-modifier), [`rewrite_tag`](#filters-rewrite-tag), [`stdout`](#filters-stdout), [`sysinfo`](#filters-sysinfo), [`tensorflow`](#filters-tensorflow), [`throttle`](#filters-throttle), [`type_converter`](#filters-type-converter), [`wasm`](#filters-wasm)
- **Outputs**: [`azure`](#outputs-azure), [`azure_blob`](#outputs-azure-blob), [`azure_kusto`](#outputs-azure-kusto), [`azure_logs_ingestion`](#outputs-azure-logs-ingestion), [`bigquery`](#outputs-bigquery), [`chronicle`](#outputs-chronicle), [`cloudwatch_logs`](#outputs-cloudwatch-logs), [`counter`](#outputs-counter), [`dash0`](#outputs-dash0), [`datadog`](#outputs-datadog), [`dynatrace`](#outputs-dynatrace), [`es`](#outputs-es), [`exit`](#outputs-exit), [`file`](#outputs-file), [`flowcounter`](#outputs-flowcounter), [`forward`](#outputs-forward), [`gelf`](#outputs-gelf), [`http`](#outputs-http), [`influxdb`](#outputs-influxdb), [`kafka`](#outputs-kafka), [`kafka-rest`](#outputs-kafka-rest), [`kinesis_firehose`](#outputs-kinesis-firehose), [`kinesis_streams`](#outputs-kinesis-streams), [`logdna`](#outputs-logdna), [`loki`](#outputs-loki), [`nats`](#outputs-nats), [`nrlogs`](#outputs-nrlogs), [`null`](#outputs-null), [`observe`](#outputs-observe), [`openobserve`](#outputs-openobserve), [`opensearch`](#outputs-opensearch), [`opentelemetry`](#outputs-opentelemetry), [`oracle_log_analytics`](#outputs-oracle-log-analytics), [`parseable`](#outputs-parseable), [`pgsql`](#outputs-pgsql), [`plot`](#outputs-plot), [`prometheus_exporter`](#outputs-prometheus-exporter), [`prometheus_remote_write`](#outputs-prometheus-remote-write), [`s3`](#outputs-s3), [`skywalking`](#outputs-skywalking), [`slack`](#outputs-slack), [`splunk`](#outputs-splunk), [`stackdriver`](#outputs-stackdriver), [`stackdriver_special_fields`](#outputs-stackdriver-special-fields), [`stdout`](#outputs-stdout), [`syslog`](#outputs-syslog), [`tcp`](#outputs-tcp), [`td`](#outputs-td), [`udp`](#outputs-udp), [`vivo_exporter`](#outputs-vivo-exporter), [`websocket`](#outputs-websocket)

<a id="environment-env"></a>
## Environment Variables

Quick reference for the optional Fluent Bit YAML `env` section.
Fluent Bit page: [Environment variables](https://docs.fluentbit.io/manual/5.0/administration/configuring-fluent-bit/yaml/environment-variables-section)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`env`](https://docs.fluentbit.io/manual/5.0/administration/configuring-fluent-bit/yaml/environment-variables-section) | No | `{}` | Object map of local environment variables available to this configuration file. |
| [`<ENV_VAR_NAME>`](https://docs.fluentbit.io/manual/5.0/administration/configuring-fluent-bit/yaml/environment-variables-section) | No |  | Variable key name. Use uppercase letters, digits, and `_`, and avoid spaces or punctuation. |
| [`<ENV_VAR_NAME>` value](https://docs.fluentbit.io/manual/5.0/administration/configuring-fluent-bit/yaml/environment-variables-section) | No |  | Variable value consumed with `${ENV_VAR_NAME}` in Fluent Bit configuration fields. |

<a id="upstream-servers-upstream-servers"></a>
## Upstream Servers

Quick reference for optional Fluent Bit YAML `upstream_servers` groups.
Fluent Bit page: [Upstream servers](https://docs.fluentbit.io/manual/5.0/administration/configuring-fluent-bit/yaml/upstream-servers-section)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`upstream_servers`](https://docs.fluentbit.io/manual/5.0/administration/configuring-fluent-bit/yaml/upstream-servers-section) | No | `[]` | List of upstream groups used by supporting output plugins for round-robin endpoint selection. |
| [`upstream_servers[].name`](https://docs.fluentbit.io/manual/5.0/administration/configuring-fluent-bit/yaml/upstream-servers-section) | Yes |  | Upstream group name. |
| [`upstream_servers[].nodes`](https://docs.fluentbit.io/manual/5.0/administration/configuring-fluent-bit/yaml/upstream-servers-section) | Yes |  | List of node endpoints in the group. |
| [`upstream_servers[].nodes[].name`](https://docs.fluentbit.io/manual/5.0/administration/configuring-fluent-bit/yaml/upstream-servers-section) | Yes |  | Node name. |
| [`upstream_servers[].nodes[].host`](https://docs.fluentbit.io/manual/5.0/administration/configuring-fluent-bit/yaml/upstream-servers-section) | Yes |  | Node host/IP endpoint. |
| [`upstream_servers[].nodes[].port`](https://docs.fluentbit.io/manual/5.0/administration/configuring-fluent-bit/yaml/upstream-servers-section) | Yes |  | Node TCP port. |
| [`upstream_servers[].nodes[].tls`](https://docs.fluentbit.io/manual/5.0/administration/configuring-fluent-bit/yaml/upstream-servers-section) | No |  | Enable TLS for this node connection. |
| [`upstream_servers[].nodes[].tls_verify`](https://docs.fluentbit.io/manual/5.0/administration/configuring-fluent-bit/yaml/upstream-servers-section) | No |  | Verify TLS certificate for this node. |
| [`upstream_servers[].nodes[].shared_key`](https://docs.fluentbit.io/manual/5.0/administration/configuring-fluent-bit/yaml/upstream-servers-section) | No |  | Shared key for secure node communication. |

## Inputs

[`blob`](#inputs-blob), [`collectd`](#inputs-collectd), [`cpu`](#inputs-cpu), [`disk`](#inputs-disk), [`docker`](#inputs-docker), [`docker_events`](#inputs-docker-events), [`dummy`](#inputs-dummy), [`ebpf`](#inputs-ebpf), [`elasticsearch`](#inputs-elasticsearch), [`exec`](#inputs-exec), [`exec_wasi`](#inputs-exec-wasi), [`fluentbit_logs`](#inputs-fluentbit-logs), [`fluentbit_metrics`](#inputs-fluentbit-metrics), [`forward`](#inputs-forward), [`gpu_metrics`](#inputs-gpu-metrics), [`head`](#inputs-head), [`health`](#inputs-health), [`http`](#inputs-http), [`kafka`](#inputs-kafka), [`kmsg`](#inputs-kmsg), [`kubernetes_events`](#inputs-kubernetes-events), [`mem`](#inputs-mem), [`mqtt`](#inputs-mqtt), [`netif`](#inputs-netif), [`nginx_metrics`](#inputs-nginx-metrics), [`node_exporter_metrics`](#inputs-node-exporter-metrics), [`opentelemetry`](#inputs-opentelemetry), [`podman_metrics`](#inputs-podman-metrics), [`proc`](#inputs-proc), [`process_exporter_metrics`](#inputs-process-exporter-metrics), [`prometheus-textfile`](#inputs-prometheus-textfile), [`prometheus_remote_write`](#inputs-prometheus-remote-write), [`prometheus_scrape`](#inputs-prometheus-scrape), [`random`](#inputs-random), [`serial`](#inputs-serial), [`splunk`](#inputs-splunk), [`statsd`](#inputs-statsd), [`stdin`](#inputs-stdin), [`syslog`](#inputs-syslog), [`systemd`](#inputs-systemd), [`tail`](#inputs-tail), [`tcp`](#inputs-tcp), [`thermal`](#inputs-thermal), [`udp`](#inputs-udp), [`windows_exporter_metrics`](#inputs-windows-exporter-metrics), [`winevtlog`](#inputs-winevtlog), [`winlog`](#inputs-winlog), [`winstat`](#inputs-winstat)

<a id="inputs-blob"></a>
### `blob`: Blob
Fluent Bit page: [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | Yes | `blob` | Plugin identifier. |
| [`log_suppress_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | Yes | `0` | Suppresses log messages from this input plugin that appear similar within a specified time interval. |
| [`mem_buf_limit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | Yes | `0` | Set a memory buffer limit for the input plugin instance in bytes. |
| [`path`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | Yes |  | Path to scan for blob (binary) files. |
| [`scan_refresh_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | Yes | `2s` | Set the interval time to scan for new files. |
| [`alias`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No |  | Sets an alias for multiple instances of the same input plugin. |
| [`database_file`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No |  | Specify a database file to keep track of processed files and their state. |
| [`exclude_pattern`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No |  | Set one or multiple shell patterns separated by commas to exclude files matching certain criteria. |
| [`log_level`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No | `info` | Specifies the log level for this input plugin. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No |  |  |
| [`routable`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No | `true` | If true, the data generated by the plugin can be forwarded to other plugins or outputs. |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No |  |  |
| [`storage.pause_on_chunks_overlimit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No | `false` | Enable pausing on an input when it reaches its chunks limit. |
| [`storage.type`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No | `memory` | Sets the storage type for this input. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No |  | Set a tag for the events generated by this input plugin. |
| [`thread.ring_buffer.capacity`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No | `1024` | Set custom ring buffer capacity when the input runs in threaded mode. |
| [`thread.ring_buffer.window`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No | `5` | Set custom ring buffer window percentage for threaded inputs. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |
| [`upload_failure_action`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No |  | Action to perform on the file after upload failure. |
| [`upload_failure_message`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No |  | Message to emit as a log record after upload failure. |
| [`upload_failure_suffix`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No |  | Suffix to append to the filename after upload failure. |
| [`upload_success_action`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No |  | Action to perform on the file after successful upload. |
| [`upload_success_message`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No |  | Message to emit as a log record after successful upload. |
| [`upload_success_suffix`](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) | No |  | Suffix to append to the filename after successful upload. |

<a id="inputs-collectd"></a>
### `collectd`: Collectd
Fluent Bit page: [Collectd](https://docs.fluentbit.io/manual/data-pipeline/inputs/collectd#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/collectd#configuration-parameters) | Yes | `collectd` | Plugin identifier. |
| [`listen`](https://docs.fluentbit.io/manual/data-pipeline/inputs/collectd#configuration-parameters) | No | `0.0.0.0` | Set the address to listen to. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/collectd#configuration-parameters) | No | `25826` | Set the port to listen to. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/collectd#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/collectd#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/collectd#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/collectd#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |
| [`typesdb`](https://docs.fluentbit.io/manual/data-pipeline/inputs/collectd#configuration-parameters) | No | `/usr/share/collectd/types.db` | Set the data specification file. |

<a id="inputs-cpu"></a>
### `cpu`: CPU metrics
Fluent Bit page: [CPU metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/cpu-metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/cpu-metrics#configuration-parameters) | Yes | `cpu` | Plugin identifier. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/cpu-metrics#configuration-parameters) | No | `0` | Polling interval in nanoseconds. |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/cpu-metrics#configuration-parameters) | No | `1` | Polling interval in seconds. |
| [`pid`](https://docs.fluentbit.io/manual/data-pipeline/inputs/cpu-metrics#configuration-parameters) | No |  | Specify the process ID (PID) of a running process in the system. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/cpu-metrics#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/cpu-metrics#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/cpu-metrics#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/cpu-metrics#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-disk"></a>
### `disk`: Disk I/O metrics
Fluent Bit page: [Disk I/O metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/disk-io-metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/disk-io-metrics#configuration-parameters) | Yes | `disk` | Plugin identifier. |
| [`dev_name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/disk-io-metrics#configuration-parameters) | No | `all disks` | Device name to limit the target (for example, sda). |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/disk-io-metrics#configuration-parameters) | No | `0` | Polling interval in nanoseconds. |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/disk-io-metrics#configuration-parameters) | No | `1` | Polling interval in seconds. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/disk-io-metrics#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/disk-io-metrics#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/disk-io-metrics#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/disk-io-metrics#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-docker"></a>
### `docker`: Docker metrics
Fluent Bit page: [Docker metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) | Yes | `docker` | Plugin identifier. |
| [`exclude`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) | No |  | A space-separated list of containers to exclude. |
| [`include`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) | No |  | A space-separated list of containers to include. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) | No | `0` | Polling interval in nanoseconds. |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) | No | `1` | Polling interval in seconds. |
| [`path.containers`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) | No | `/var/lib/docker/containers` | Container directory path, for custom Docker data-root configurations. |
| [`path.sysfs`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) | No | `/sys/fs/cgroup` | Sysfs cgroup mount point. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-docker-events"></a>
### `docker_events`: Docker events
Fluent Bit page: [Docker events](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) | Yes | `docker_events` | Plugin identifier. |
| [`buffer_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) | No | `8192` | The size of the buffer used to read docker events in bytes. |
| [`key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) | No | `message` | When a message is unstructured (no parser applied), it's appended as a string under the key name message. |
| [`parser`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) | No |  | Specify the name of a parser to interpret the entry as a structured message. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) | No |  |  |
| [`reconnect.retry_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) | No | `1` | The retry interval in seconds. |
| [`reconnect.retry_limits`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) | No | `5` | The maximum number of retries allowed. |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |
| [`unix_path`](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) | No | `/var/run/docker.sock` | The docker socket Unix path. |

<a id="inputs-dummy"></a>
### `dummy`: Dummy
Fluent Bit page: [Dummy](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | Yes | `dummy` | Plugin identifier. |
| [`copies`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No | `1` | Number of messages to generate each time messages are generated. |
| [`dummy`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No | `{"message":"dummy"}` | Dummy JSON record. |
| [`fixed_timestamp`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No | `false` | If enabled, use a fixed timestamp. |
| [`flush_on_startup`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No | `false` | If set to true, the first dummy event is generated at startup. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No | `0` | Set time interval, in nanoseconds, at which every message is generated. |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No | `0` | Set time interval, in seconds, at which every message is generated. |
| [`metadata`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No | `{}` | Dummy JSON metadata. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No |  |  |
| [`rate`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No | `1` | Rate at which messages are generated, expressed in how many times per second. |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No |  |  |
| [`samples`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No | `0` | Limit the number of events generated. |
| [`start_time_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No | `-1` | Set a dummy base timestamp, in nanoseconds. |
| [`start_time_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No | `-1` | Set a dummy base timestamp, in seconds. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`test_hang_on_exit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No | `false` | Test-only option that simulates a hang during shutdown for hot reload watchdog testing. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-ebpf"></a>
### `ebpf`: eBPF
Fluent Bit page: [eBPF](https://docs.fluentbit.io/manual/data-pipeline/inputs/ebpf#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/ebpf#configuration-parameters) | Yes | `ebpf` | Plugin identifier. |
| [`poll_ms`](https://docs.fluentbit.io/manual/data-pipeline/inputs/ebpf#configuration-parameters) | No | `1000` | Set the polling interval in milliseconds for collecting events from the ring buffer. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/ebpf#configuration-parameters) | No |  |  |
| [`ringbuf_map_name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/ebpf#configuration-parameters) | No | `events` | Set the name of the eBPF ring buffer map to read events from. |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/ebpf#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/ebpf#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`trace`](https://docs.fluentbit.io/manual/data-pipeline/inputs/ebpf#configuration-parameters) | No |  | Set the eBPF trace to enable (for example, trace_bind, trace_malloc, trace_signal, trace_tcp, trace_vfs). |

<a id="inputs-elasticsearch"></a>
### `elasticsearch`: Elasticsearch
Fluent Bit page: [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | Yes | `elasticsearch` | Plugin identifier. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No | `512K` | Set the buffer chunk size. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No | `4M` | Set the maximum size of buffer. |
| [`hostname`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No | `localhost` | Specify hostname or fully qualified domain name. |
| [`http2`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No | `true` | Enable HTTP/2 support. |
| [`http_server.ingress_queue_byte_limit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No | `256M` | Maximum size of the deferred ingress queue. |
| [`http_server.ingress_queue_event_limit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No | `8192` | Maximum number of deferred ingress queue entries. |
| [`http_server.max_connections`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No | `0` | Maximum number of concurrent active HTTP connections. |
| [`http_server.workers`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No | `1` | Number of HTTP listener worker threads. |
| [`listen`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No | `0.0.0.0` | The address to listen on. |
| [`meta_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No | `@meta` | Specify a key name for meta information. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No | `9200` | The port for Fluent Bit to listen on. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`tag_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No | `NULL` | Specify a key name for extracting as a tag. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |
| [`version`](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) | No | `8.0.0` | Specify the Elasticsearch version that Fluent Bit reports to clients during sniffing and API requests. |

<a id="inputs-exec"></a>
### `exec`: Exec
Fluent Bit page: [Exec](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) | Yes | `exec` | Plugin identifier. |
| [`buf_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) | No | `4096` | Size of the buffer. |
| [`command`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) | No |  | The command to execute, passed to [popen](https://man7.org/linux/man-pages/man3/popen.3.html) without any additional escaping or processing. |
| [`exit_after_oneshot`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) | No | `false` | Exit as soon as the one-shot command exits. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) | No | `0` | Polling interval (nanoseconds). |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) | No | `1` | Polling interval (seconds). |
| [`oneshot`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) | No | `false` | Only run once at startup. |
| [`parser`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) | No |  | Specify the name of a parser to interpret the entry as a structured message. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) | No |  |  |
| [`propagate_exit_code`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) | No | `false` | Cause Fluent Bit to exit with the exit code of the command exited by this plugin. |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-exec-wasi"></a>
### `exec_wasi`: Exec WASI
Fluent Bit page: [Exec WASI](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) | Yes | `exec_wasi` | Plugin identifier. |
| [`accessible_paths`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) | No | `.` | Specify the allowed list of paths to be able to access paths from Wasm programs. |
| [`buf_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) | No | `4096` | Size of the buffer. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) | No | `0` | Polling interval (nanosecond). |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) | No | `1` | Polling interval (seconds). |
| [`oneshot`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) | No | `false` | Execute the command only once at startup. |
| [`parser`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) | No |  | Specify the name of a parser to interpret the entry as a structured message. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |
| [`wasi_path`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) | No |  | The location of a Wasm program file. |
| [`wasm_heap_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) | No | `8192` | Size of the heap size of Wasm execution. |
| [`wasm_stack_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) | No | `8192` | Size of the stack size of Wasm execution. |

<a id="inputs-fluentbit-logs"></a>
### `fluentbit_logs`: Fluent Bit logs
Fluent Bit page: [Fluent Bit logs](https://docs.fluentbit.io/manual/data-pipeline/router)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/router) | Yes | `fluentbit_logs` | Plugin identifier. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/router) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/router) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/router) | No |  | Tag assigned to records emitted by this input plugin. |

<a id="inputs-fluentbit-metrics"></a>
### `fluentbit_metrics`: Fluent Bit metrics
Fluent Bit page: [Fluent Bit metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/fluentbit-metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/fluentbit-metrics#configuration-parameters) | Yes | `fluentbit_metrics` | Plugin identifier. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/fluentbit-metrics#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/fluentbit-metrics#configuration-parameters) | No |  |  |
| [`scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/fluentbit-metrics#configuration-parameters) | No | `2` seconds` | The rate at which Fluent Bit internal metrics are collected. |
| [`scrape_on_start`](https://docs.fluentbit.io/manual/data-pipeline/inputs/fluentbit-metrics#configuration-parameters) | No | `false` | Scrape metrics upon start, use to avoid waiting for scrape_interval for the first round of metrics. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/fluentbit-metrics#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/fluentbit-metrics#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-forward"></a>
### `forward`: Forward
Fluent Bit page: [Forward](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | Yes | `forward` | Plugin identifier. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | Yes | `1024000` | By default the buffer to store the incoming Forward messages, don't allocate the maximum memory allowed, instead it allocate memory when it's required. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | Yes | `6144000` | Specify the maximum buffer memory size used to receive a Forward message. |
| [`empty_shared_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | No | `false` | Enable secure forward protocol with a zero-length shared key. |
| [`listen`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | No | `0.0.0.0` | Listener network interface. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | No | `24224` | TCP port to listen for incoming connections. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | No |  |  |
| [`security.users`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | No |  | Specify the username and password pairs for secure forward authentication. |
| [`self_hostname`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | No | `localhost` | Hostname for secure forward authentication. |
| [`shared_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | No |  | Shared key for secure forward authentication. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | No |  | Override the tag of the forwarded events with the defined value. |
| [`tag_prefix`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | No |  | Prefix incoming tag with the defined value. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |
| [`unix_path`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | No |  | Specify the path to Unix socket to receive a Forward message. |
| [`unix_perm`](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) | No |  | Set the permission of the Unix socket file. |

<a id="inputs-gpu-metrics"></a>
### `gpu_metrics`: GPU metrics
Fluent Bit page: [GPU metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) | Yes | `gpu_metrics` | Plugin identifier. |
| [`cards_exclude`](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) | No |  | Pattern specifying which GPU cards to exclude from monitoring. |
| [`cards_include`](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) | No | `*` | Pattern specifying which GPU cards to monitor. |
| [`enable_power`](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) | No | `true` | Enable collection of power consumption metrics (gpu_power_watts). |
| [`enable_temperature`](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) | No | `true` | Enable collection of temperature metrics (gpu_temperature_celsius). |
| [`path_sysfs`](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) | No | `/sys` | Path to the sysfs root directory. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) | No |  |  |
| [`scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) | No | `5` | Interval in seconds between metric collection cycles. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |

<a id="inputs-head"></a>
### `head`: Head
Fluent Bit page: [Head](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) | Yes | `head` | Plugin identifier. |
| [`add_path`](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) | No | `false` | If enabled, the path is appended to each record. |
| [`buf_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) | No | `256` | Buffer size to read the file. |
| [`file`](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) | No |  | Absolute path to the target file. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) | No | `0` | Polling interval (nanoseconds). |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) | No | `1` | Polling interval (seconds). |
| [`key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) | No | `head` | Rename a key. |
| [`lines`](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) | No | `0` | Line number to read. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) | No |  |  |
| [`split_line`](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) | No | `false` | If enabled, in_head generates key-value pair per line. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-health"></a>
### `health`: Health
Fluent Bit page: [Health](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) | Yes | `health` | Plugin identifier. |
| [`add_host`](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) | No | `false` | If enabled, hostname is appended to each record. |
| [`add_port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) | No | `false` | If enabled, port number is appended to each record. |
| [`alert`](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) | No | `false` | If enabled, it generates messages only when the target TCP service is down. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) | No |  | Name of the target host or IP address. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) | No | `0` | Specify a nanoseconds interval for service checks. |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) | No | `1` | Interval in seconds between the service checks. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) | No |  | TCP port where to perform the connection request. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-http"></a>
### `http`: HTTP
Fluent Bit page: [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | Yes | `http` | Plugin identifier. |
| [`oauth2.issuer`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | Yes |  | Expected issuer (iss) claim. |
| [`oauth2.jwks_url`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | Yes |  | JWKS endpoint URL used to fetch public keys for JWT validation. |
| [`add_remote_addr`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `false` | Adds a REMOTE_ADDR field to the record. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `512K` | This sets the chunk size for incoming JSON messages. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `4M` | Specify the maximum buffer size to receive a JSON message. |
| [`enable_health_endpoint`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `false` | Enable a GET /health endpoint for this input instance. |
| [`http2`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `true` | Enable HTTP/2 support. |
| [`http_server.ingress_queue_byte_limit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `256M` | Maximum size of the deferred ingress queue. |
| [`http_server.ingress_queue_event_limit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `8192` | Maximum number of deferred ingress queue entries. |
| [`http_server.max_connections`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `0` | Maximum number of concurrent active HTTP connections. |
| [`http_server.workers`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `1` | Number of HTTP listener worker threads. |
| [`listen`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `0.0.0.0` | The address to listen on. |
| [`oauth2.allowed_audience`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No |  | Audience claim to enforce when validating incoming OAuth 2.0 JWT tokens. |
| [`oauth2.allowed_clients`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No |  | Authorized client_id or azp claim values. |
| [`oauth2.jwks_refresh_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `300` | How often in seconds to refresh the cached JWKS keys from oauth2.jwks_url. |
| [`oauth2.validate`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `false` | Enable OAuth 2.0 JWT validation for incoming requests. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `9880` | The port for Fluent Bit to listen on. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No |  |  |
| [`remote_addr_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `REMOTE_ADDR` | Key name for the remote address field added to the record when add_remote_addr is enabled. |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No |  |  |
| [`success_header`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No |  | Add an HTTP header key/value pair on success. |
| [`successful_response_code`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `201` | Allows setting successful response code. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`tag_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No |  | Specify the key name to overwrite a tag. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-kafka"></a>
### `kafka`: Kafka
Fluent Bit page: [Kafka](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) | Yes | `kafka` | Plugin identifier. |
| [`brokers`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) | No |  | Single or multiple list of Kafka Brokers. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) | No | `4M` | Specify the maximum size of buffer per cycle to poll Kafka messages from subscribed topics. |
| [`client_id`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) | No |  | Client id passed to librdkafka. |
| [`enable_auto_commit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) | No | `false` | Rely on Kafka auto-commit and commit messages in batches. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) | No | `none` | Serialization format of the messages. |
| [`group_id`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) | No | `fluent-bit` | Group id passed to librdkafka. |
| [`poll_ms`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) | No | `500` | Kafka brokers polling interval in milliseconds. |
| [`poll_timeout_ms`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) | No | `1` | Timeout in milliseconds for Kafka consumer poll operations. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) | No |  |  |
| [`rdkafka.{property}`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) | No |  | {property} can be any [librdkafka properties](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md). |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |
| [`topics`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) | No |  | Single entry or list of comma-separated topics (, ) that Fluent Bit will subscribe to. |

<a id="inputs-kmsg"></a>
### `kmsg`: Kernel logs
Fluent Bit page: [Kernel logs](https://docs.fluentbit.io/manual/data-pipeline/inputs/kernel-logs#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kernel-logs#configuration-parameters) | Yes | `kmsg` | Plugin identifier. |
| [`prio_level`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kernel-logs#configuration-parameters) | No | `8` | The log level to filter. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kernel-logs#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kernel-logs#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kernel-logs#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kernel-logs#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-kubernetes-events"></a>
### `kubernetes_events`: Kubernetes events
Fluent Bit page: [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | Yes | `kubernetes_events` | Plugin identifier. |
| [`db`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No |  | Set a database file to keep track of recorded Kubernetes events. |
| [`db.journal_mode`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No | `WAL` | Set the journal mode for databases. |
| [`db.locking`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No | `false` | Specify that the database will be accessed only by Fluent Bit. |
| [`db.sync`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No | `normal` | Set a database sync method. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No | `500000000` | Set the reconnect interval (sub seconds: nanoseconds). |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No | `0` | Set the reconnect interval (seconds). |
| [`kube_ca_file`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No | `/var/run/secrets/kubernetes.io/serviceaccount/ca.crt` | Kubernetes TLS CA file. |
| [`kube_ca_path`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No |  | Kubernetes TLS CA path. |
| [`kube_namespace`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No |  | Kubernetes namespace to query events from. |
| [`kube_request_limit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No | `0` | Kubernetes limit parameter for events query. |
| [`kube_retention_time`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No | `1h` | Kubernetes retention time for events. |
| [`kube_token_file`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No | `/var/run/secrets/kubernetes.io/serviceaccount/token` | Kubernetes authorization token file. |
| [`kube_token_ttl`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No | `10m` | Kubernetes token time to live, until it's read again from the token file. |
| [`kube_url`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No | `https://kubernetes.default.svc` | API Server endpoint. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`tls.debug`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No | `0` | Set TLS debug level: 0 (no debug), 1 (error), 2 (state change), 3 (info), and 4 (verbose). |
| [`tls.verify`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No | `true` | Enable or disable verification of TLS peer certificate. |
| [`tls.vhost`](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) | No |  | Set optional TLS virtual host. |

<a id="inputs-mem"></a>
### `mem`: Memory metrics
Fluent Bit page: [Memory metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/memory-metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/memory-metrics#configuration-parameters) | Yes | `mem` | Plugin identifier. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/memory-metrics#configuration-parameters) | No | `0` | Polling interval in nanoseconds. |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/memory-metrics#configuration-parameters) | No | `1` | Polling interval in seconds. |
| [`pid`](https://docs.fluentbit.io/manual/data-pipeline/inputs/memory-metrics#configuration-parameters) | No |  | Process ID to measure. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/memory-metrics#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/memory-metrics#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/memory-metrics#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/memory-metrics#configuration-parameters) | No | `false` | Run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-mqtt"></a>
### `mqtt`: MQTT
Fluent Bit page: [MQTT](https://docs.fluentbit.io/manual/data-pipeline/inputs/mqtt#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/mqtt#configuration-parameters) | Yes | `mqtt` | Plugin identifier. |
| [`buffer_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/mqtt#configuration-parameters) | No | `2048` | Maximum payload size (in bytes) for a single MQTT message. |
| [`listen`](https://docs.fluentbit.io/manual/data-pipeline/inputs/mqtt#configuration-parameters) | No | `0.0.0.0` | Listener network interface. |
| [`payload_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/mqtt#configuration-parameters) | No |  | Field name where the MQTT message payload will be stored in the output record. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/mqtt#configuration-parameters) | No | `1883` | TCP port where listening for connections. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/mqtt#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/mqtt#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/mqtt#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/mqtt#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-netif"></a>
### `netif`: Network I/O metrics
Fluent Bit page: [Network I/O metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) | Yes | `netif` | Plugin identifier. |
| [`interface`](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) | No |  | Specify the network interface to monitor. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) | No | `0` | Polling interval in nanoseconds. |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) | No | `1` | Polling interval in seconds. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`test_at_init`](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) | No | `false` | If true, test if the network interface is valid at initialization. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |
| [`verbose`](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) | No | `false` | If true, gather metrics precisely. |

<a id="inputs-nginx-metrics"></a>
### `nginx_metrics`: NGINX exporter metrics
Fluent Bit page: [NGINX exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) | Yes | `nginx_metrics` | Plugin identifier. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) | No | `localhost` | Name of the target host or IP address. |
| [`nginx_plus`](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) | No | `true` | Turn on NGINX Plus mode. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) | No | `80` | Port of the target NGINX service to connect to. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) | No |  |  |
| [`scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) | No | `5s` | The interval to scrape metrics from the NGINX service. |
| [`status_url`](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) | No | `/status` | The URL of the stub status handler. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-node-exporter-metrics"></a>
### `node_exporter_metrics`: Node exporter metrics
Fluent Bit page: [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | Yes | `node_exporter_metrics` | Plugin identifier. |
| [`collector.cpu.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which cpu metrics are collected from the host operating system. |
| [`collector.cpufreq.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which cpufreq metrics are collected from the host operating system. |
| [`collector.diskstats.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which diskstats metrics are collected from the host operating system. |
| [`collector.filefd.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which filefd metrics are collected from the host operating system. |
| [`collector.filesystem.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which filesystem metrics are collected from the host operating system. |
| [`collector.hwmon.chip-exclude`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `Not set by default.` | Regex of chips to exclude for the hwmon collector. |
| [`collector.hwmon.chip-include`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `Not set by default.` | Regex of chips to include for the hwmon collector. |
| [`collector.hwmon.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which hwmon metrics are collected from the host operating system. |
| [`collector.hwmon.sensor-exclude`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `Not set by default.` | Regex of sensors to exclude for the hwmon collector. |
| [`collector.hwmon.sensor-include`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `Not set by default.` | Regex of sensors to include for the hwmon collector. |
| [`collector.loadavg.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which loadavg metrics are collected from the host operating system. |
| [`collector.meminfo.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which meminfo metrics are collected from the host operating system. |
| [`collector.netdev.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which netdev metrics are collected from the host operating system. |
| [`collector.netstat.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which netstat metrics are collected from the host operating system. |
| [`collector.nvme.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which nvme metrics are collected from the host operating system. |
| [`collector.processes.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which system-level process metrics are collected from the host operating system. |
| [`collector.sockstat.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which sockstat metrics are collected from the host operating system. |
| [`collector.stat.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which stat metrics are collected from the host operating system. |
| [`collector.systemd.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which systemd metrics are collected from the host operating system. |
| [`collector.textfile.path`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `Not set by default.` | Specify path or directory to collect textfile metrics from the host operating system. |
| [`collector.textfile.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which textfile metrics are collected from the host operating system. |
| [`collector.thermalzone.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which thermal_zone metrics are collected from the host operating system. |
| [`collector.time.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which time metrics are collected from the host operating system. |
| [`collector.uname.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which uname metrics are collected from the host operating system. |
| [`collector.vmstat.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `0` | The rate in seconds at which vmstat metrics are collected from the host operating system. |
| [`diskstats.ignore_device_regex`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `^(ram\` | Specify the regular expression for the diskstats to prevent collection of/ignore. |
| [`filesystem.ignore_filesystem_type_regex`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `^(autofs\` | Specify the regular expression for the filesystem types to prevent collection of or ignore. |
| [`filesystem.ignore_mount_point_regex`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `^/(dev\` | Specify the regular expression for the mount points to prevent collection of/ignore. |
| [`metrics`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `"cpu, cpufreq, meminfo, diskstats, filesystem, uname, stat, time, loadavg, vmstat, netdev, netstat, sockstat, filefd, systemd, nvme, thermal_zone, hwmon"` | Specify which metrics are collected from the host operating system. |
| [`path.procfs`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `/proc` | The mount point used to collect process information and metrics. |
| [`path.rootfs`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `/` | The root filesystem mount point. |
| [`path.sysfs`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `/sys` | The path in the filesystem used to collect system metrics. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No |  |  |
| [`scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `5` | The rate in seconds at which metrics are collected from the host operating system. |
| [`systemd_exclude_pattern`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `.+\\.(automount\` | Regular expression to determine which units are excluded in the metrics produced by the systemd collector. |
| [`systemd_include_pattern`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `Not applied unless explicitly set.` | Regular expression to determine which units are included in the metrics produced by the systemd collector. |
| [`systemd_include_service_task_metrics`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `false` | Determines if the collector will include service task metrics. |
| [`systemd_service_restart_metrics`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `false` | Determines if the collector will include service restart metrics. |
| [`systemd_unit_start_time_metrics`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No | `false` | Determines if the collector will include unit start time metrics. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |

<a id="inputs-opentelemetry"></a>
### `opentelemetry`: OpenTelemetry
Fluent Bit page: [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | Yes | `opentelemetry` | Plugin identifier. |
| [`alias`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Sets an alias for multiple instances of the same input plugin. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `512K` | Size of each buffer chunk allocated for HTTP requests (advanced users only). |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `4M` | Maximum size of the HTTP request buffer in KB, MB, or GB. |
| [`encode_profiles_as_log`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `true` | Encode profiles received as text and ingest them in the logging pipeline. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `localhost` | The hostname. |
| [`http2`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `true` | Enable HTTP/2 protocol support for the OpenTelemetry receiver. |
| [`http_server.ingress_queue_byte_limit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `256M` | Maximum size of the deferred ingress queue. |
| [`http_server.ingress_queue_event_limit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `8192` | Maximum number of deferred ingress queue entries. |
| [`http_server.max_connections`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `0` | Maximum number of concurrent active HTTP connections. |
| [`http_server.workers`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `1` | Number of HTTP listener worker threads. |
| [`listen`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `0.0.0.0` | The network address to listen on. |
| [`log_level`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `info` | Specifies the log level for this plugin. |
| [`log_suppress_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `0` | Suppresses log messages from this plugin that appear similar within a specified time interval. |
| [`logs_body_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Specify a body key. |
| [`logs_metadata_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `otlp` | Key name to store OpenTelemetry logs metadata in the record. |
| [`mem_buf_limit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `0` | Set a memory buffer limit for the input plugin. |
| [`net.accept_timeout`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `10s` | Set maximum time allowed to establish an incoming connection. |
| [`net.accept_timeout_log_error`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `true` | On client accept timeout, specify if it should log an error. |
| [`net.backlog`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `128` | Set the backlog size for listening sockets. |
| [`net.io_timeout`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `0s` | Set maximum time a connection can stay idle. |
| [`net.keepalive`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `true` | Enable or disable keepalive support. |
| [`net.share_port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `false` | Allow multiple plugins to bind to the same port. |
| [`oauth2.allowed_audience`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Audience claim to enforce when validating incoming OAuth 2.0 JSON Web Token (JWT) tokens. |
| [`oauth2.allowed_clients`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Authorized client_id or azp claim values. |
| [`oauth2.issuer`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Expected issuer (iss) claim for OAuth 2.0 JWT validation. |
| [`oauth2.jwks_refresh_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `300` | How often in seconds to refresh the cached JSON Web Key Set (JWKS) keys from oauth2.jwks_url. |
| [`oauth2.jwks_url`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | JWKS endpoint URL used to fetch public keys for OAuth 2.0 JWT validation. |
| [`oauth2.validate`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `false` | Enable OAuth 2.0 JWT validation for incoming requests. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `4318` | The port for Fluent Bit to listen for incoming connections. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  |  |
| [`profiles_support`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `false` | This is an experimental feature, feel free to test it but don't enable this in production environments. |
| [`raw_traces`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `false` | Forward traces without processing. |
| [`routable`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `true` | If set to true, the data generated by the plugin will be routable, meaning that it can be forwarded to other plugins or outputs. |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  |  |
| [`storage.pause_on_chunks_overlimit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Enable pausing on an input when they reach their chunks limit. |
| [`storage.type`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `memory` | Sets the storage type for this input, one of: filesystem, memory or memrb. |
| [`successful_response_code`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `201` | Allows for setting a successful response code. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Set a tag for the events generated by this input plugin. |
| [`tag_from_uri`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `true` | If no explicit tag is set, the tag is created from the URI. |
| [`tag_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Record accessor key to use for generating tags from incoming records. |
| [`thread.ring_buffer.capacity`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `1024` | Number of slots in the ring buffer for data entries when running in [threaded](/manual/administration/multithreading.md) mode. |
| [`thread.ring_buffer.window`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `5` | Percentage threshold (1-100) of the ring buffer capacity at which a flush is triggered when running in [threaded](/manual/administration/multithreading.md) mode. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `false` | Enable [multithreading](/manual/administration/multithreading.md) for this input to run in a separate dedicated thread. |
| [`tls`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `off` | Enable or disable TLS/SSL support. |
| [`tls.ca_file`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Absolute path to CA certificate file. |
| [`tls.ca_path`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Absolute path to scan for certificate files. |
| [`tls.ciphers`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Specify TLS ciphers up to TLSv1.2. |
| [`tls.crt_file`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Absolute path to Certificate file. |
| [`tls.debug`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `1` | Set TLS debug level. |
| [`tls.key_file`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Absolute path to private Key file. |
| [`tls.key_passwd`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Optional password for tls.key_file file. |
| [`tls.max_version`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Specify the maximum version of TLS. |
| [`tls.min_version`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Specify the minimum version of TLS. |
| [`tls.verify`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `on` | Force certificate validation. |
| [`tls.verify_hostname`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No | `off` | Enable or disable to verify hostname. |
| [`tls.vhost`](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) | No |  | Hostname to be used for TLS SNI extension. |

<a id="inputs-podman-metrics"></a>
### `podman_metrics`: Podman metrics
Fluent Bit page: [Podman metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) | Yes | `podman_metrics` | Plugin identifier. |
| [`path.config`](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) | No | `/var/lib/containers/storage/overlay-containers/containers.json` | Custom path to the Podman containers configuration file. |
| [`path.procfs`](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) | No | `/proc` | Custom path to the proc subsystem directory. |
| [`path.sysfs`](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) | No | `/sys/fs/cgroup` | Custom path to the sysfs subsystem directory. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) | No |  |  |
| [`scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) | No | `30` | Interval between each scrape of Podman data (in seconds). |
| [`scrape_on_start`](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) | No | `false` | Sets whether this plugin scrapes Podman data on startup. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-proc"></a>
### `proc`: Process metrics
Fluent Bit page: [Process metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) | Yes | `proc` | Plugin identifier. |
| [`alert`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) | No | `false` | If enabled, the plugin will only generate messages if the target process is down. |
| [`fd`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) | No | `true` | If enabled, a number of fd is appended to each record. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) | No | `0` | Specifies the interval between service checks, in nanoseconds. |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) | No | `1` | Specifies the interval between service checks, in seconds. |
| [`mem`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) | No | `true` | If enabled, memory usage of the process is appended to each record. |
| [`proc_name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) | No |  | The name of the target process to check. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) | No | `false` | Specifies whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-process-exporter-metrics"></a>
### `process_exporter_metrics`: Process exporter metrics
Fluent Bit page: [Process exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/process-exporter-metrics#configuration)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process-exporter-metrics#configuration) | Yes | `process_exporter_metrics` | Plugin identifier. |
| [`metrics`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process-exporter-metrics#configuration) | No | `cpu, io, memory, state, context_switches, fd, start_time, thread_wchan, thread` | Specify which process level of metrics are collected from the host operating system. |
| [`path.procfs`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process-exporter-metrics#configuration) | No | `/proc` | The mount point used to collect process information and metrics. |
| [`process_exclude_pattern`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process-exporter-metrics#configuration) | No | `NULL` | Regular expression to determine which names of processes are excluded in the metrics produced by this plugin. |
| [`process_include_pattern`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process-exporter-metrics#configuration) | No | `.+` | Regular expression to determine which names of processes are included in the metrics produced by this plugin. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process-exporter-metrics#configuration) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process-exporter-metrics#configuration) | No |  |  |
| [`scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process-exporter-metrics#configuration) | No | `5` | The rate, in seconds, at which metrics are collected. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/process-exporter-metrics#configuration) | No |  | Tag assigned to records emitted by this input plugin. |

<a id="inputs-prometheus-textfile"></a>
### `prometheus-textfile`: Prometheus text file
Fluent Bit page: [Prometheus text file](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | Yes | `prometheus-textfile` | Plugin identifier. |
| [`alias`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | No |  | Sets an alias. |
| [`log_level`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | No | `info` | Specifies the log level for input plugin. |
| [`log_suppress_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | No | `0` | Suppresses log messages from input plugin that appear similar within a specified time interval. |
| [`mem_buf_limit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | No | `0` | Set a memory buffer limit for the input plugin. |
| [`path`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | No |  | Comma-separated list of files or glob patterns to read. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | No |  |  |
| [`routable`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | No | `true` | If set to true, the data generated by the plugin will be routable, meaning that it can be forwarded to other plugins or outputs. |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | No |  |  |
| [`scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | No | `10s` | Interval between file scans. |
| [`storage.pause_on_chunks_overlimit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | No |  | Enable pausing on an input when they reach their chunks limit. |
| [`storage.type`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | No | `memory` | Sets the storage type for this input, one of: filesystem, memory or memrb. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | No |  | Set a tag for the events generated by this input plugin. |
| [`thread.ring_buffer.capacity`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | No | `1024` | Set custom ring buffer capacity when the input runs in threaded mode. |
| [`thread.ring_buffer.window`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | No | `5` | Set custom ring buffer window percentage for threaded inputs. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) | No | `false` | Enable threading on an input. |

<a id="inputs-prometheus-remote-write"></a>
### `prometheus_remote_write`: Prometheus remote write
Fluent Bit page: [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | Yes | `prometheus_remote_write` | Plugin identifier. |
| [`tag_from_uri`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | Yes | `true` | If true, a tag will be created from the uri parameter (for example, api_prom_push from /api/prom/push), and any tag specified in the configuration will be ignored. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | No | `512K` | Sets the chunk size for incoming data. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | No | `4M` | Specifies the maximum buffer size to receive a request. |
| [`http2`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | No | `true` | Enable HTTP/2 support. |
| [`http_server.ingress_queue_byte_limit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | No | `256M` | Maximum size of the deferred ingress queue. |
| [`http_server.ingress_queue_event_limit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | No | `8192` | Maximum number of deferred ingress queue entries. |
| [`http_server.max_connections`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | No | `0` | Maximum number of concurrent active HTTP connections. |
| [`http_server.workers`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | No | `1` | Number of HTTP listener worker threads. |
| [`listen`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | No | `0.0.0.0` | The address to listen on. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | No | `8080` | The port to listen on. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | No |  |  |
| [`successful_response_code`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | No | `201` | Specifies the success response code. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | No | `false` | Specifies whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |
| [`uri`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) | No |  | Specifies an optional HTTP URI for the target web server listening for Prometheus remote write payloads (for example, /api/prom/push). |

<a id="inputs-prometheus-scrape"></a>
### `prometheus_scrape`: Prometheus scrape Metrics
Fluent Bit page: [Prometheus scrape Metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) | Yes | `prometheus_scrape` | Plugin identifier. |
| [`metrics_path`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) | Yes | `/metrics` | The metrics URI endpoint, which must start with a forward slash (/). |
| [`bearer_token`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) | No |  | Set the bearer token for authentication with the Prometheus endpoint. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) | No | `10M` | Set the maximum buffer size for the HTTP response. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) | No | `localhost` | The host of the Prometheus metric endpoint to scrape. |
| [`http_passwd`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) | No | `""` | Set the password for HTTP basic authentication. |
| [`http_user`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) | No |  | Set the username for HTTP basic authentication. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) | No | `9100` | The port of the Prometheus metric endpoint to scrape. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) | No |  |  |
| [`scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) | No | `10s` | The interval to scrape metrics. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-random"></a>
### `random`: Random
Fluent Bit page: [Random](https://docs.fluentbit.io/manual/data-pipeline/inputs/random#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/random#configuration-parameters) | Yes | `random` | Plugin identifier. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/random#configuration-parameters) | No | `0` | Set the interval between generated samples, in nanoseconds. |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/random#configuration-parameters) | No | `1` | Set the interval between generated samples, in seconds. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/random#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/random#configuration-parameters) | No |  |  |
| [`samples`](https://docs.fluentbit.io/manual/data-pipeline/inputs/random#configuration-parameters) | No | `-1` | Set the number of samples to generate. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/random#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/random#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-serial"></a>
### `serial`: Serial interface
Fluent Bit page: [Serial interface](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) | Yes | `serial` | Plugin identifier. |
| [`bitrate`](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) | No |  | The bit rate for the communication. |
| [`file`](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) | No |  | Absolute path to the device entry. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) | No | `none` | Specify the format of the incoming data stream. |
| [`min_bytes`](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) | No | `1` | The serial interface expects at least min_bytes to be available before processing the message. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) | No |  |  |
| [`separator`](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) | No |  | Specify a separator string that's used to determine when a message ends. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-splunk"></a>
### `splunk`: Splunk
Fluent Bit page: [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | Yes | `splunk` | Plugin identifier. |
| [`add_remote_addr`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No | `false` | Inject a remote address field into the record, using the X-Forwarded-For header or the connection address as the value. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No | `512K` | Set the chunk size for incoming JSON messages. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No | `4M` | Set the maximum buffer size to receive a JSON message. |
| [`http2`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No | `true` | Enable HTTP/2 support. |
| [`http_server.ingress_queue_byte_limit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No | `256M` | Maximum size of the deferred ingress queue. |
| [`http_server.ingress_queue_event_limit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No | `8192` | Maximum number of deferred ingress queue entries. |
| [`http_server.max_connections`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No | `0` | Maximum number of concurrent active HTTP connections. |
| [`http_server.workers`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No | `1` | Number of HTTP listener worker threads. |
| [`listen`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No | `0.0.0.0` | The address to listen on. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No | `8088` | The port for Fluent Bit to listen on. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No |  |  |
| [`remote_addr_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No | `remote_addr` | Record key name used to store the remote address when add_remote_addr is enabled. |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No |  |  |
| [`splunk_token`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No |  | Specify a Splunk token for HTTP HEC authentication. |
| [`splunk_token_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No | `@splunk_token` | Set a record key for storing the Splunk token for HTTP HEC. |
| [`store_token_in_metadata`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No | `true` | Store Splunk HEC tokens in the Fluent Bit metadata. |
| [`success_header`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No |  | Add an HTTP header key/value pair on success. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`tag_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No |  | Specify the key name to overwrite a tag. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-statsd"></a>
### `statsd`: StatsD
Fluent Bit page: [StatsD](https://docs.fluentbit.io/manual/data-pipeline/inputs/statsd#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/statsd#configuration-parameters) | Yes | `statsd` | Plugin identifier. |
| [`listen`](https://docs.fluentbit.io/manual/data-pipeline/inputs/statsd#configuration-parameters) | No | `0.0.0.0` | Specify the network interface to bind. |
| [`metrics`](https://docs.fluentbit.io/manual/data-pipeline/inputs/statsd#configuration-parameters) | No | `off` | Ingest as metric events rather than log events. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/statsd#configuration-parameters) | No | `8125` | Specify the UDP port to listen for incoming connections. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/statsd#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/statsd#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/statsd#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/statsd#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-stdin"></a>
### `stdin`: Standard input
Fluent Bit page: [Standard input](https://docs.fluentbit.io/manual/data-pipeline/inputs/standard-input#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/standard-input#configuration-parameters) | Yes | `stdin` | Plugin identifier. |
| [`buffer_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/standard-input#configuration-parameters) | Yes | `16k` | Set the buffer size to read data. |
| [`parser`](https://docs.fluentbit.io/manual/data-pipeline/inputs/standard-input#configuration-parameters) | No |  | The name of the parser to invoke instead of the default JSON input parser. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/standard-input#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/standard-input#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/standard-input#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/standard-input#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-syslog"></a>
### `syslog`: Syslog
Fluent Bit page: [Syslog](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | Yes | `syslog` | Plugin identifier. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No | `32KB` | Set the buffer size to store incoming syslog messages. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No |  | Specify the maximum buffer size to receive a syslog message. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No | `newline` | Specify the TCP framing format. |
| [`listen`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No | `0.0.0.0` | If mode is set to tcp or udp, specify the network interface to bind. |
| [`mode`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No | `unix_udp` | Defines transport protocol mode: UDP over Unix socket (unix_udp), TCP over Unix socket (unix_tcp), tcp, or udp |
| [`parser`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No |  | Specify an alternative parser for the message. |
| [`path`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No |  | If mode is set to unix_tcp or unix_udp, set the absolute path to the Unix socket file. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No | `5140` | If mode is set to tcp or udp, specify the port to listen for incoming messages. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No |  |  |
| [`raw_message_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No |  | Specify the key where the original raw syslog message will be preserved. |
| [`receive_buffer_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No |  | Specify the maximum socket receive buffer size. |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No |  |  |
| [`source_address_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No |  | Specify the key where the source address will be injected. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |
| [`unix_perm`](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) | No | `644` | If mode is set to unix_tcp or unix_udp, set the permission of the Unix socket file. |

<a id="inputs-systemd"></a>
### `systemd`: Systemd
Fluent Bit page: [Systemd](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) | Yes | `systemd` | Plugin identifier. |
| [`db`](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) | No |  | Specify the absolute path of a database file to keep track of the journald cursor. |
| [`db.sync`](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) | No | `full` | Set a default synchronization (I/O) method. |
| [`lowercase`](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) | No | `false` | Lowercase the journald field (key). |
| [`max_entries`](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) | No | `5000` | When Fluent Bit starts, the Journal might have a high number of logs in the queue. |
| [`max_fields`](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) | No | `8000` | Set a maximum number of fields (keys) allowed per record. |
| [`path`](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) | No |  | Optional path to the Systemd journal directory. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) | No |  |  |
| [`read_from_tail`](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) | No | `false` | Start reading new entries. |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) | No |  |  |
| [`strip_underscores`](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) | No | `false` | Remove the leading underscore of the journald field (key). |
| [`systemd_filter`](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) | No |  | Perform a query over logs that contain specific journald key/value pairs. |
| [`systemd_filter_type`](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) | No | `or` | Define the filter type when systemd_filter is specified multiple times. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) | No |  | Fluent Bit uses tags to route messages. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-tail"></a>
### `tail`: Tail
Fluent Bit page: [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | Yes | `tail` | Plugin identifier. |
| [`buffer_chunk_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | Yes | `32k` | Set the initial buffer size to read file data. |
| [`buffer_max_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | Yes | `32k` | Set the limit of the buffer size per monitored file. |
| [`docker_mode_parser`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | Yes |  | Specify an optional parser for the first line of the Docker multiline mode. |
| [`db`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No |  | Specify the database file to keep track of monitored files and offsets. |
| [`db.compare_filename`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `false` | This option determines whether to review both inode and filename when retrieving stored file information from the database. |
| [`db.journal_mode`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `wal` | Sets the journal mode for databases (wal). |
| [`db.locking`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `false` | Specify that the database will be accessed only by Fluent Bit. |
| [`db.sync`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `normal` | Set a default synchronization (I/O) method. |
| [`docker_mode`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `false` | If enabled, the plugin will recombine split Docker log lines before passing them to any parser. |
| [`docker_mode_flush`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `4` | Wait period time in seconds to flush queued unfinished split lines. |
| [`event_batch_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `50M` | Set the maximum number of bytes to process per iteration for files monitored in event mode (files promoted from static to event-based monitoring). |
| [`exclude_path`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No |  | Set one or multiple shell patterns separated by commas to exclude files matching certain criteria. |
| [`exit_on_eof`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `false` | When reading a file, exit as soon as it reaches the end of the file. |
| [`file_cache_advise`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `true` | Set the posix_fadvise in POSIX_FADV_DONTNEED mode. |
| [`generic.encoding`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No |  | Set the non-Unicode encoding of the file data. |
| [`ignore_active_older_files`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `false` | Ignore files that are older than the value set in ignore_older even if the file is being ingested. |
| [`ignore_older`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `Read all.` | Ignores files older than ignore_older. |
| [`inotify_watcher`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `true` | Set to false to use file stat watcher instead of inotify. |
| [`key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `log` | When a message is unstructured (no parser applied), it's appended as a string under the key name log. |
| [`mem_buf_limit`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No |  | Set a memory limit that the Tail plugin can use when appending data to the engine. |
| [`offset_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No |  | If enabled, Fluent Bit appends the offset of the current monitored file as part of the record. |
| [`parser`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No |  | Specify the name of a parser to interpret the entry as a structured message. |
| [`path`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No |  | Pattern specifying a specific log file or multiple ones through the use of common wildcards. |
| [`path_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No |  | If enabled, it appends the name of the monitored file as part of the record. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No |  |  |
| [`progress_check_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `2s` | Set the interval for checking file progress. |
| [`progress_check_interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `0` | Set the nanosecond component of the progress check interval. |
| [`read_from_head`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `false` | For new discovered files on start (without a database offset/position), read the content from the head of the file, not tail. |
| [`read_newly_discovered_files_from_head`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `true` | For newly discovered files after startup (without a database offset/position), read the content from the head of the file, not tail. |
| [`refresh_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `60` | The interval of refreshing the list of watched files in seconds. |
| [`rotate_wait`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `5` | Specify the number of extra time in seconds to monitor a file once it's rotated in case some pending data is flushed. |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No |  |  |
| [`skip_empty_lines`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `false` | Skips empty lines in the log file from any further processing or output. |
| [`skip_long_lines`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `false` | When a monitored file reaches its buffer capacity due to a very long line (buffer_max_size), the default behavior is to stop monitoring that file. |
| [`static_batch_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `50M` | Set the maximum number of bytes to process per iteration for the monitored static files (files that already exist upon Fluent Bit start). |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No |  | Set a tag with regexextract fields that will be placed on lines read. |
| [`tag_regex`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No |  | Set a regular expression to extract fields from the filename. |
| [`thread.ring_buffer.capacity`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `1024` | Number of slots in the ring buffer for data entries when running in [threaded](/manual/administration/multithreading.md) mode. |
| [`thread.ring_buffer.window`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `5` | Percentage threshold (1-100) of the ring buffer capacity at which a flush is triggered when running in [threaded](/manual/administration/multithreading.md) mode. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |
| [`truncate_long_lines`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `false` | When enabled, truncates lines that exceed the buffer capacity after input encoding conversion to UTF-8. |
| [`unicode.encoding`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No |  | Set the Unicode character encoding of the file data. |
| [`watcher_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) | No | `2s` | Set the interval for the watcher that monitors symbolic link rotation. |

<a id="inputs-tcp"></a>
### `tcp`: TCP
Fluent Bit page: [TCP](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) | Yes | `tcp` | Plugin identifier. |
| [`chunk_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) | Yes | `32` | The default buffer to store the incoming JSON messages. |
| [`buffer_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) | No | `chunk_size` | Specify the maximum buffer size in KB to receive a JSON message. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) | No | `json` | Specify the expected payload format. |
| [`listen`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) | No | `0.0.0.0` | Listener network interface. |
| [`parser`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) | No |  | Optional [parser](/manual/data-pipeline/parsers.md) for line-delimited records. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) | No | `5170` | TCP port to listen for connections. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) | No |  |  |
| [`separator`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) | No | `LF` or `0x10` (break line)` | When format is set to none, Fluent Bit needs a separator string to split the records. |
| [`source_address_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) | No |  | Specify the key to inject the source address. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-thermal"></a>
### `thermal`: Thermal
Fluent Bit page: [Thermal](https://docs.fluentbit.io/manual/data-pipeline/inputs/thermal#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/thermal#configuration-parameters) | Yes | `thermal` | Plugin identifier. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/thermal#configuration-parameters) | No | `0` | Polling interval (nanoseconds). |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/thermal#configuration-parameters) | No | `1` | Polling interval (seconds). |
| [`name_regex`](https://docs.fluentbit.io/manual/data-pipeline/inputs/thermal#configuration-parameters) | No |  | Optional name filter regular expression. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/thermal#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/thermal#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/thermal#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/thermal#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |
| [`type_regex`](https://docs.fluentbit.io/manual/data-pipeline/inputs/thermal#configuration-parameters) | No |  | Optional type filter regular expression. |

<a id="inputs-udp"></a>
### `udp`: UDP
Fluent Bit page: [UDP](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) | Yes | `udp` | Plugin identifier. |
| [`chunk_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) | Yes | `32` | The default buffer to store incoming JSON messages. |
| [`buffer_size`](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) | No | `chunk_size` | Specify the maximum buffer size in KB to receive a JSON message. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) | No | `json` | Specify the expected payload format. |
| [`listen`](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) | No | `0.0.0.0` | Listener network interface. |
| [`parser`](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) | No |  | Optional [parser](/manual/data-pipeline/parsers.md) for line-delimited records. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) | No | `5170` | UDP port used to listen for connections. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) | No |  |  |
| [`separator`](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) | No | `LF` or `0x10` (break line)` | When format is set to none, Fluent Bit needs a separator string to split the records. |
| [`source_address_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) | No |  | Specify the key where the source address will be injected. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

<a id="inputs-windows-exporter-metrics"></a>
### `windows_exporter_metrics`: Windows exporter metrics
Fluent Bit page: [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | Yes | `windows_exporter_metrics` | Plugin identifier. |
| [`collector.cache.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `0` | The rate in seconds at which cache metrics are collected. |
| [`collector.cpu.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `0` | The rate in seconds at which cpu metrics are collected. |
| [`collector.cpu_info.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `0` | The rate in seconds at which cpu_info metrics are collected. |
| [`collector.cs.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `0` | The rate in seconds at which cs metrics are collected. |
| [`collector.logical_disk.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `0` | The rate in seconds at which logical_disk metrics are collected. |
| [`collector.logon.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `0` | The rate in seconds at which logon metrics are collected. |
| [`collector.memory.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `0` | The rate in seconds at which memory metrics are collected. |
| [`collector.net.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `0` | The rate in seconds at which net metrics are collected. |
| [`collector.os.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `0` | The rate in seconds at which os metrics are collected. |
| [`collector.paging_file.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `0` | The rate in seconds at which paging_file metrics are collected. |
| [`collector.process.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `0` | The rate in seconds at which process metrics are collected. |
| [`collector.service.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `0` | The rate in seconds at which service metrics are collected. |
| [`collector.system.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `0` | The rate in seconds at which system metrics are collected. |
| [`collector.tcp.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `0` | The rate in seconds at which tcp metrics are collected. |
| [`collector.thermalzone.scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `0` | The rate in seconds at which thermalzone metrics are collected. |
| [`enable_collector`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No |  | Enable one collector by name. |
| [`metrics`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `"cpu, cpu_info, os, net, logical_disk, cs, cache, thermalzone, logon, system, service, tcp"` | Specify which metrics are collected. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No |  |  |
| [`scrape_interval`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `1` | The rate in seconds at which metrics are collected from the Windows host. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No |  | Tag assigned to records emitted by this input plugin. |
| [`we.logical_disk.allow_disk_regex`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `"/.+/"` (all)` | Specify the regular expression for logical disk metrics to allow collection of. |
| [`we.logical_disk.deny_disk_regex`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `NULL` (all)` | Specify the regular expression for logical disk metrics to prevent collection of or ignore. |
| [`we.net.allow_nic_regex`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `"/.+/"` (all)` | Specify the regular expression for network metrics captured by the name of the NIC. |
| [`we.process.allow_process_regex`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `"/.+/"` (all)` | Specify the regular expression covering the process metrics to collect. |
| [`we.process.deny_process_regex`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `NULL` (all)` | Specify the regular expression for process metrics to prevent collection of or ignore. |
| [`we.service.exclude`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `NULL` | Specify the key value pairs for the exclude condition for the WHERE clause of service metrics. |
| [`we.service.include`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `NULL` | Specify the key value pairs for the include condition for the WHERE clause of service metrics. |
| [`we.service.where`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) | No | `NULL` | Specify the WHERE clause for retrieving service metrics. |

<a id="inputs-winevtlog"></a>
### `winevtlog`: Windows Event logs (winevtlog)
Fluent Bit page: [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | Yes | `winevtlog` | Plugin identifier. |
| [`channels`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No |  | A comma-separated list of channels to read from. |
| [`db`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No |  | Optional. |
| [`event_query`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `*` | Specify XML query for filtering events. |
| [`ignore_missing_channels`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `false` | Optional. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `0` | Optional. |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `1` | Optional. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No |  |  |
| [`read_existing_events`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `false` | Optional. |
| [`read_limit_per_cycle`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `512KiB` | Specify read limit per cycle. |
| [`reconnect.base_ms`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `500` | Base reconnect delay in milliseconds after a subscription failure. |
| [`reconnect.jitter_pct`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `20` | Jitter percentage applied to the reconnect delay to avoid synchronized retries. |
| [`reconnect.max_ms`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `30000` | Maximum reconnect delay in milliseconds. |
| [`reconnect.max_retries`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `8` | Maximum number of reconnect attempts before the channel stops retrying. |
| [`reconnect.multiplier`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `2.0` | Backoff multiplier applied between reconnect attempts. |
| [`remote.domain`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No |  | Specify domain name of remote access for Windows EventLog. |
| [`remote.password`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No |  | Specify password of remote access for Windows EventLog. |
| [`remote.server`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No |  | Specify server name of remote access for Windows EventLog. |
| [`remote.username`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No |  | Specify user name of remote access for Windows EventLog. |
| [`render_event_as_text`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `false` | Optional. |
| [`render_event_as_xml`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `false` | Optional. |
| [`render_event_text_key`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `log` | Optional. |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No |  |  |
| [`string_inserts`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `true` | Optional. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |
| [`use_ansi`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) | No | `false` | Optional. |

<a id="inputs-winlog"></a>
### `winlog`: Windows Event logs (winlog)
Fluent Bit page: [Windows Event logs (winlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) | Yes | `winlog` | Plugin identifier. |
| [`channels`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) | No |  | A comma-separated list of channels to read from. |
| [`db`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) | No |  | Set the path to save the read offsets. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) | No | `0` | Set the polling interval for each channel in nanoseconds. |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) | No | `1` | Set the polling interval for each channel. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) | No |  |  |
| [`string_inserts`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) | No | `true` | Whether to include string inserts in output records. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |
| [`use_ansi`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) | No | `false` | Use ANSI encoding for Event Log messages. |

<a id="inputs-winstat"></a>
### `winstat`: Windows System Statistics (winstat)
Fluent Bit page: [Windows System Statistics (winstat)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-system-statistics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-system-statistics#configuration-parameters) | Yes | `winstat` | Plugin identifier. |
| [`interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-system-statistics#configuration-parameters) | No | `0` | Polling interval in nanoseconds. |
| [`interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-system-statistics#configuration-parameters) | No | `1` | Polling interval in seconds. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-system-statistics#configuration-parameters) | No |  |  |
| [`route`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-system-statistics#configuration-parameters) | No |  |  |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-system-statistics#configuration-parameters) | No |  | Tag assigned to records emitted by this input plugin. |
| [`threaded`](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-system-statistics#configuration-parameters) | No | `false` | Indicates whether to run this input in its own [thread](/manual/administration/multithreading.md#inputs). |

## Filters

[`aws`](#filters-aws), [`checklist`](#filters-checklist), [`ecs`](#filters-ecs), [`expect`](#filters-expect), [`geoip2`](#filters-geoip2), [`grep`](#filters-grep), [`kubernetes`](#filters-kubernetes), [`log_to_metrics`](#filters-log-to-metrics), [`lua`](#filters-lua), [`modify`](#filters-modify), [`multiline`](#filters-multiline), [`nest`](#filters-nest), [`nightfall`](#filters-nightfall), [`parser`](#filters-parser), [`record_modifier`](#filters-record-modifier), [`rewrite_tag`](#filters-rewrite-tag), [`stdout`](#filters-stdout), [`sysinfo`](#filters-sysinfo), [`tensorflow`](#filters-tensorflow), [`throttle`](#filters-throttle), [`type_converter`](#filters-type-converter), [`wasm`](#filters-wasm)

<a id="filters-aws"></a>
### `aws`: AWS metadata
Fluent Bit page: [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | Yes | `aws` | Plugin identifier. |
| [`tags_enabled`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | Yes | `false` | Specifies whether to attach EC2 instance tags. |
| [`tags_exclude`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | Yes |  | Defines a list of specific EC2 tag keys not to inject into the logs. |
| [`tags_include`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | Yes |  | Defines a list of specific EC2 tag keys to inject into the logs. |
| [`account_id`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | No | `false` | The account ID for the current EC2 instance. |
| [`ami_id`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | No | `false` | The EC2 instance image ID. |
| [`az`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | No | `true` | The [availability zone](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html), such as us-east-1a. |
| [`ec2_instance_id`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | No | `true` | The EC2 instance ID. |
| [`ec2_instance_type`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | No | `false` | The EC2 instance type. |
| [`enable_entity`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | No | `false` | Enables entity prefix for fields used for constructing entity. |
| [`hostname`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | No | `false` | The hostname for the current EC2 instance. |
| [`imds_version`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | No | `v2` | Specify which version of the instance metadata service to use. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`private_ip`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | No | `false` | The EC2 instance private IP. |
| [`retry_interval_s`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | No | `300` | Defines minimum duration in seconds between retries for fetching EC2 instance tags. |
| [`vpc_id`](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) | No | `false` | The VPC ID for the current EC2 instance. |

<a id="filters-checklist"></a>
### `checklist`: CheckList
Fluent Bit page: [CheckList](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters) | Yes | `checklist` | Plugin identifier. |
| [`file`](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters) | No |  | The single value file that Fluent Bit will use as a lookup table to determine if the specified lookup_key exists. |
| [`ignore_case`](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters) | No | `false` | Compare strings by ignoring case. |
| [`lookup_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters) | No | `log` | The specific key to look up and determine if it exists. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`mode`](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters) | No | `exact` | Set the check mode. |
| [`print_query_time`](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters) | No | `false` | Print to stdout the elapsed query time for every matched record. |
| [`record`](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters) | No |  | The record to add if the lookup_key is found in the specified file. |

<a id="filters-ecs"></a>
### `ecs`: ECS metadata
Fluent Bit page: [ECS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) | Yes | `ecs` | Plugin identifier. |
| [`ecs_tag_prefix`](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) | Yes | `""` | Similar to the kube_tag_prefix option in the [Kubernetes filter](/manual/data-pipeline/filters/kubernetes.md) and performs the same function. |
| [`add`](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) | No |  | Similar to the add option in the [modify filter](/manual/data-pipeline/filters/modify.md). |
| [`agent_endpoint_retries`](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) | No | `2` | Number of retries for failed metadata requests to the ECS Agent Introspection endpoint. |
| [`cluster_metadata_only`](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) | No | `false` | When enabled, the plugin only attempts to attach cluster metadata values. |
| [`ecs_meta_cache_ttl`](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) | No | `1h` | The filter builds a hash table in memory mapping each unique container short ID to its metadata. |
| [`ecs_meta_host`](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) | No | `127.0.0.1` | The host name at which the ECS Agent Introspection endpoint is reachable. |
| [`ecs_meta_port`](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) | No | `51678` | The port at which the ECS Agent Introspection endpoint is reachable. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |

<a id="filters-expect"></a>
### `expect`: Expect
Fluent Bit page: [Expect](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) | Yes | `expect` | Plugin identifier. |
| [`action`](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) | No | `warn` | Action to take when a rule doesn't match. |
| [`key_exists`](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) | No |  | Check if a key with a given name exists in the record. |
| [`key_not_exists`](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) | No |  | Check if a key doesn't exist in the record. |
| [`key_val_eq`](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) | No |  | Check that the value of the key equals the given value in the configuration. |
| [`key_val_is_not_null`](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) | No |  | Check that the value of the key is NOT NULL. |
| [`key_val_is_null`](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) | No |  | Check that the value of the key is NULL. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`result_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) | No | `matched` | Specify a key name for the matching result added when action is set to result_key. |

<a id="filters-geoip2"></a>
### `geoip2`: GeoIP2 filter
Fluent Bit page: [GeoIP2 filter](https://docs.fluentbit.io/manual/data-pipeline/filters/geoip2-filter#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/geoip2-filter#configuration-parameters) | Yes | `geoip2` | Plugin identifier. |
| [`database`](https://docs.fluentbit.io/manual/data-pipeline/filters/geoip2-filter#configuration-parameters) | No |  | Path to the GeoIP2 database. |
| [`lookup_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/geoip2-filter#configuration-parameters) | No |  | Field name to process. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/geoip2-filter#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/geoip2-filter#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`record`](https://docs.fluentbit.io/manual/data-pipeline/filters/geoip2-filter#configuration-parameters) | No |  | Defines the KEY LOOKUP_KEY VALUE triplet. |

<a id="filters-grep"></a>
### `grep`: Grep
Fluent Bit page: [Grep](https://docs.fluentbit.io/manual/data-pipeline/filters/grep#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/grep#configuration-parameters) | Yes | `grep` | Plugin identifier. |
| [`exclude`](https://docs.fluentbit.io/manual/data-pipeline/filters/grep#configuration-parameters) | No |  | Exclude records where the content of KEY matches the regular expression. |
| [`logical_op`](https://docs.fluentbit.io/manual/data-pipeline/filters/grep#configuration-parameters) | No | `legacy` | Specify a logical operator: AND, OR or legacy. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/grep#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/grep#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/grep#configuration-parameters) | No |  | Keep records where the content of KEY matches the regular expression. |

<a id="filters-kubernetes"></a>
### `kubernetes`: Kubernetes
Fluent Bit page: [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | Yes | `kubernetes` | Plugin identifier. |
| [`aws_use_pod_association`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | Yes | `Off` | Enable custom endpoint to get pod-to-service name mapping. |
| [`buffer_size`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | Yes | `32k` | Set the buffer size for HTTP client when reading responses from Kubernetes API server. |
| [`regex_parser`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | Yes |  | Set an alternative Parser to process record tags and extract pod_name, namespace_name, container_name, and docker_id. |
| [`annotations`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `On` | Include Kubernetes pod resource annotations in the extra metadata. |
| [`aws_pod_association_endpoint`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `/kubernetes/pod-to-service-env-map` | Endpoint path for pod-to-service name association. |
| [`aws_pod_association_host`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `cloudwatch-agent.amazon-cloudwatch` | Host to connect with when performing pod-to-service name association. |
| [`aws_pod_association_host_client_cert_file`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `/etc/amazon-cloudwatch-observability-agent-client-cert/client.crt` | Client certificate path for enabling mTLS on calls to the agent server. |
| [`aws_pod_association_host_client_key_file`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `/etc/amazon-cloudwatch-observability-agent-client-cert/client.key` | Client certificate key path for enabling mTLS on calls to the agent server. |
| [`aws_pod_association_host_server_ca_file`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `/etc/amazon-cloudwatch-observability-agent-server-cert/tls-ca.crt` | TLS CA certificate path for communication with the agent server. |
| [`aws_pod_association_host_tls_debug`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `0` | TLS debug level for agent server connection: 0 (no debug), 1 (error), 2 (state change), 3 (info), 4 (verbose). |
| [`aws_pod_association_host_tls_verify`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `On` | Enable or disable verification of TLS peer certificate for agent server connection. |
| [`aws_pod_association_port`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `4311` | Port to connect with for pod-to-service name association. |
| [`aws_pod_service_map_refresh_interval`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `60` | Refresh interval in seconds for the pod-to-service map. |
| [`aws_pod_service_map_ttl`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `0` | Time-To-Live (TTL) for pod-to-service map cache entries. |
| [`aws_pod_service_preload_cache_dir`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No |  | Directory containing pod-to-service map files for pre-loading cache. |
| [`cache_use_docker_id`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | When enabled, metadata will be fetched from Kubernetes when docker_id is changed. |
| [`dns_retries`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `6` | Number of DNS lookup retries until the network starts working. |
| [`dns_wait_time`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `30` | DNS lookup interval between network status checks. |
| [`dummy_meta`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | If set, use dummy-meta data (for test/dev purposes). |
| [`k8s-logging.exclude`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | Allow Kubernetes pods to exclude their logs from the log processor. |
| [`k8s-logging.parser`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | Allow Kubernetes pods to suggest a pre-defined parser. |
| [`keep_log`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `On` | When keep_log is disabled and merge_log enabled, the log field is removed from the incoming message once it has been successfully merged. |
| [`kube_ca_file`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `/var/run/secrets/kubernetes.io/serviceaccount/ca.crt` | CA certificate file |
| [`kube_ca_path`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No |  | Absolute path to scan for certificate files |
| [`kube_meta_cache_ttl`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `0` | Configurable time-to-live for Kubernetes cached pod metadata. |
| [`kube_meta_namespace_cache_ttl`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `900` (seconds)` | Configurable time-to-live for Kubernetes cached namespace metadata. |
| [`kube_meta_preload_cache_dir`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No |  | If set, Kubernetes metadata can be cached or pre-loaded from files in JSON format in this directory, named namespace-pod.meta. |
| [`kube_tag_prefix`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `kube.var.log.containers.` | When the source records come from the tail input plugin, this option specifies the prefix used in tail configuration. |
| [`kube_token_command`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `NULL` | Command to get Kubernetes authorization token. |
| [`kube_token_file`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `/var/run/secrets/kubernetes.io/serviceaccount/token` | Token file |
| [`kube_token_ttl`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `600` | Configurable time-to-live for the Kubernetes token. |
| [`kube_url`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `https://kubernetes.default.svc:443` | API Server endpoint |
| [`kubelet_host`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `127.0.0.1` | Kubelet host to use for HTTP requests. |
| [`kubelet_port`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `10250` | Kubelet port to use for HTTP requests. |
| [`labels`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `On` | Include Kubernetes pod resource labels in the extra metadata. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`merge_log`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | When enabled, check if the log field content is a JSON string map. |
| [`merge_log_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No |  | When merge_log is enabled, the filter assumes the log field from the incoming message is a JSON string message and attempts to create a structured representation of it at the same level of the log field in the map. |
| [`merge_log_trim`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `On` | When merge_log is enabled, trim (remove possible \n or \r\) field values. |
| [`merge_parser`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No |  | Optional parser name to specify how to parse the data contained in the log key. |
| [`namespace_annotations`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | Include Kubernetes namespace resource annotations in the extra metadata. |
| [`namespace_labels`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | Include Kubernetes namespace resource labels in the extra metadata. |
| [`namespace_metadata_only`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | Include Kubernetes namespace metadata and no pod metadata. |
| [`owner_references`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | Include Kubernetes owner references in the extra metadata. |
| [`set_platform`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `Auto-detected` | Manually set the Kubernetes platform type. |
| [`tls.debug`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `-1` | Debug level between 0 (no information) and 4 (all details). |
| [`tls.verify`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `On` | When enabled, turns on certificate validation when connecting to the Kubernetes API server. |
| [`tls.verify_hostname`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | When enabled, turns on hostname validation for certificates. |
| [`tls.vhost`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No |  | Set an optional TLS virtual host for the Kubernetes API server connection. |
| [`use_journal`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | When enabled, the filter reads logs in Journald format. |
| [`use_kubelet`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | Optional feature flag to get metadata information from Kubelet instead of calling Kube Server API to enhance the log. |
| [`use_pod_association`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | Deprecated alias for aws_use_pod_association. |
| [`use_tag_for_meta`](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) | No | `Off` | When enabled, Kubernetes metadata (for example, pod_name, container_name, and namespace_name) will be extracted from the tag itself. |

<a id="filters-log-to-metrics"></a>
### `log_to_metrics`: Logs to metrics
Fluent Bit page: [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | Yes | `log_to_metrics` | Plugin identifier. |
| [`value_field`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | Yes |  | Required for modes gauge and histogram. |
| [`add_label`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Adds a custom label NAME and set the value to the value of KEY. |
| [`bucket`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Optional for metric_mode histogram. |
| [`discard_logs`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No | `false` | Flag that defines if logs should be discarded after processing. |
| [`emitter_mem_buf_limit`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No | `10M` | Buffer limit for the internal metrics emitter. |
| [`emitter_name`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Name of the emitter (advanced users). |
| [`exclude`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Excludes records in which the content of KEY matches the regular expression REGEX. |
| [`flush_interval_nsec`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No | `0` | The interval for metrics emission, in nanoseconds. |
| [`flush_interval_sec`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No | `0` | The interval for metrics emission, in seconds. |
| [`kubernetes_mode`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No | `false` | If enabled, adds pod_id, pod_name, namespace_name, docker_id and container_name to the metric as labels. |
| [`label_field`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Includes a record field as label dimension in the metric. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`metric_description`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Sets a description for the metric. |
| [`metric_mode`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No | `counter` | Defines the mode for the metric. |
| [`metric_name`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No | `a` | Sets the name of the metric. |
| [`metric_namespace`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No | `log_metric` | Sets the namespace of the metric. |
| [`metric_subsystem`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Subsystem of the metric. |
| [`regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Includes records in which the content of KEY matches the regular expression REGEX. |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) | No |  | Defines the tag for the generated metrics record. |

<a id="filters-lua"></a>
### `lua`: Lua
Fluent Bit page: [Lua](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) | Yes | `lua` | Plugin identifier. |
| [`call`](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) | No |  | The Lua function name that will be triggered to do filtering. |
| [`code`](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) | No |  | Inline Lua code instead of loading from a path defined in script. |
| [`enable_flb_null`](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) | No |  | If enabled, null will be converted to flb_null in Lua. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`protected_mode`](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) | No |  | If enabled, the Lua script will be executed in protected mode. |
| [`script`](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) | No |  | Path to the Lua script that will be used. |
| [`time_as_table`](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) | No |  | By default, when the Lua script is invoked, the record timestamp is passed as a floating number, which might lead to precision loss when it's converted back. |
| [`type_array_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) | No |  | If these keys are matched, the fields are handled as array. |
| [`type_int_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) | No |  | If these keys are matched, the fields are converted to integers. |

<a id="filters-modify"></a>
### `modify`: Modify
Fluent Bit page: [Modify](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) | Yes | `modify` | Plugin identifier. |
| [`add`](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) | No |  | Add a key/value pair with key KEY and value VALUE if KEY doesn't exist. |
| [`copy`](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) | No |  | Copy a key/value pair with key KEY to COPIED_KEY if KEY exists and COPIED_KEY doesn't exist. |
| [`hard_copy`](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) | No |  | Copy a key/value pair with key KEY to COPIED_KEY if KEY exists. |
| [`hard_rename`](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) | No |  | Rename a key/value pair with key KEY to RENAMED_KEY if KEY exists. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`move_to_end`](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) | No |  | Move key/value pairs with keys matching KEY to the end of the message. |
| [`move_to_start`](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) | No |  | Move key/value pairs with keys matching KEY to the start of the message. |
| [`remove`](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) | No |  | Remove a key/value pair with key KEY if it exists. |
| [`remove_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) | No |  | Remove all key/value pairs with key matching regexp KEY. |
| [`remove_wildcard`](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) | No |  | Remove all key/value pairs with key matching wildcard KEY. |
| [`rename`](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) | No |  | Rename a key/value pair with key KEY to RENAMED_KEY if KEY exists and RENAMED_KEY doesn't exist. |
| [`set`](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) | No |  | Add a key/value pair with key KEY and value VALUE. |

<a id="filters-multiline"></a>
### `multiline`: Multiline
Fluent Bit page: [Multiline](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) | Yes | `multiline` | Plugin identifier. |
| [`buffer`](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Enable buffered mode. |
| [`debug_flush`](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Enable debug logging for flush operations. |
| [`emitter_mem_buf_limit`](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Set a limit on the amount of memory the emitter can consume if the outputs provide backpressure. |
| [`emitter_name`](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Name for the emitter input instance which re-emits the completed records at the beginning of the pipeline. |
| [`emitter_storage.type`](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | The storage type for the emitter input instance. |
| [`flush_ms`](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Flush time for pending multiline records. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`mode`](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Mode can be parser for regular expression concatenation, or partial_message to concatenate split Docker logs. |
| [`multiline.key_content`](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Key name that holds the content to process. |
| [`multiline.parser`](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) | No |  | Specify one or multiple [Multiline Parser definitions](/manual/data-pipeline/parsers/multiline-parsing.md) to apply to the content. |

<a id="filters-nest"></a>
### `nest`: Nest
Fluent Bit page: [Nest](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters) | Yes | `nest` | Plugin identifier. |
| [`add_prefix`](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters) | No |  | Prefix affected keys with this string |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`nest_under`](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters) | No |  | Nest records matching the wildcard under this key |
| [`nested_under`](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters) | No |  | Lift records nested under the nested_under key |
| [`operation`](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters) | No |  | Select the operation nest or lift |
| [`remove_prefix`](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters) | No |  | Remove prefix from affected keys if it matches this string |
| [`wildcard`](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters) | No |  | Nest records which field matches the wildcard |

<a id="filters-nightfall"></a>
### `nightfall`: Nightfall
Fluent Bit page: [Nightfall](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) | Yes | `nightfall` | Plugin identifier. |
| [`sampling_rate`](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) | Yes | `1` | The rate controlling how much of your logs you wish to be scanned. |
| [`tls.ca_path`](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) | Yes |  | Absolute path to root certificates, required if tls.verify is true. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`nightfall_api_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) | No |  | The Nightfall API key to scan your logs with, obtainable from the [Nightfall Dashboard](https://app.nightfall.ai) |
| [`policy_id`](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) | No |  | The Nightfall developer platform policy to scan your logs with, configurable in the [Nightfall Dashboard](https://app.nightfall.ai/developer-platform/policies). |
| [`tls.debug`](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) | No | `0` | Debug level between 0 (nothing) and 4 (every detail). |
| [`tls.verify`](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) | No | `true` | When enabled, turns on certificate validation when connecting to the Nightfall API. |
| [`tls.vhost`](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) | No |  | Set an optional TLS virtual host for the Nightfall API connection. |

<a id="filters-parser"></a>
### `parser`: Parser
Fluent Bit page: [Parser](https://docs.fluentbit.io/manual/data-pipeline/filters/parser#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/parser#configuration-parameters) | Yes | `parser` | Plugin identifier. |
| [`key_name`](https://docs.fluentbit.io/manual/data-pipeline/filters/parser#configuration-parameters) | No |  | Specify field name in record to parse. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/parser#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/parser#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`parser`](https://docs.fluentbit.io/manual/data-pipeline/filters/parser#configuration-parameters) | No |  | Specify the parser name to interpret the field. |
| [`preserve_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/parser#configuration-parameters) | No | `false` | Keep the original key_name field in the parsed result. |
| [`reserve_data`](https://docs.fluentbit.io/manual/data-pipeline/filters/parser#configuration-parameters) | No | `false` | Keep all other original fields in the parsed result. |
| [`unescape_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/parser#configuration-parameters) | No | `*deprecated*` | Deprecated. |

<a id="filters-record-modifier"></a>
### `record_modifier`: Record modifier
Fluent Bit page: [Record modifier](https://docs.fluentbit.io/manual/data-pipeline/filters/record-modifier#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/record-modifier#configuration-parameters) | Yes | `record_modifier` | Plugin identifier. |
| [`allowlist_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/record-modifier#configuration-parameters) | No |  | If the key isn't matched, that field is removed. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/record-modifier#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/record-modifier#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`record`](https://docs.fluentbit.io/manual/data-pipeline/filters/record-modifier#configuration-parameters) | No |  | Append fields. |
| [`remove_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/record-modifier#configuration-parameters) | No |  | If the key is matched, that field is removed. |
| [`uuid_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/record-modifier#configuration-parameters) | No |  | If set, the plugin appends UUID to each record. |
| [`whitelist_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/record-modifier#configuration-parameters) | No |  | An alias of allowlist_key for backwards compatibility. |

<a id="filters-rewrite-tag"></a>
### `rewrite_tag`: Rewrite tag
Fluent Bit page: [Rewrite tag](https://docs.fluentbit.io/manual/data-pipeline/filters/rewrite-tag#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/rewrite-tag#configuration-parameters) | Yes | `rewrite_tag` | Plugin identifier. |
| [`emitter_mem_buf_limit`](https://docs.fluentbit.io/manual/data-pipeline/filters/rewrite-tag#configuration-parameters) | No |  | Set a limit on the amount of memory the tag rewrite emitter can consume if the outputs provide backpressure. |
| [`emitter_name`](https://docs.fluentbit.io/manual/data-pipeline/filters/rewrite-tag#configuration-parameters) | No |  | Use this property to configure an optional name for the internal emitter plugin that handles filters emitting a record under the new tag. |
| [`emitter_storage.type`](https://docs.fluentbit.io/manual/data-pipeline/filters/rewrite-tag#configuration-parameters) | No |  | Define a buffering mechanism for the new records created. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/rewrite-tag#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/rewrite-tag#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`rule`](https://docs.fluentbit.io/manual/data-pipeline/filters/rewrite-tag#configuration-parameters) | No |  | Defines the matching criteria and the format of the tag for the matching record. |

<a id="filters-stdout"></a>
### `stdout`: Standard output
Fluent Bit page: [Standard output](https://docs.fluentbit.io/manual/data-pipeline/router)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/router) | Yes | `stdout` | Plugin identifier. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/router) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/router) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |

<a id="filters-sysinfo"></a>
### `sysinfo`: Sysinfo
Fluent Bit page: [Sysinfo](https://docs.fluentbit.io/manual/data-pipeline/filters/sysinfo#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/sysinfo#configuration-parameters) | Yes | `sysinfo` | Plugin identifier. |
| [`fluentbit_version_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/sysinfo#configuration-parameters) | No |  | Specify the key name for the Fluent Bit version. |
| [`hostname_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/sysinfo#configuration-parameters) | No |  | Specify the key name for hostname. |
| [`kernel_version_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/sysinfo#configuration-parameters) | No |  | Specify the key name for kernel version. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/sysinfo#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/sysinfo#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`os_name_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/sysinfo#configuration-parameters) | No |  | Specify the key name for operating system name. |
| [`os_version_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/sysinfo#configuration-parameters) | No |  | Specify the key name for the operating system version. |

<a id="filters-tensorflow"></a>
### `tensorflow`: Tensorflow
Fluent Bit page: [Tensorflow](https://docs.fluentbit.io/manual/data-pipeline/filters/tensorflow#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/tensorflow#configuration-parameters) | Yes | `tensorflow` | Plugin identifier. |
| [`include_input_fields`](https://docs.fluentbit.io/manual/data-pipeline/filters/tensorflow#configuration-parameters) | No | `true` | Include all input fields in filter's output. |
| [`input_field`](https://docs.fluentbit.io/manual/data-pipeline/filters/tensorflow#configuration-parameters) | No |  | Specify the name of the field in the record to apply inference on. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/tensorflow#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/tensorflow#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`model_file`](https://docs.fluentbit.io/manual/data-pipeline/filters/tensorflow#configuration-parameters) | No |  | Path to the model file (.tflite) to be loaded by Tensorflow Lite. |
| [`normalization_value`](https://docs.fluentbit.io/manual/data-pipeline/filters/tensorflow#configuration-parameters) | No |  | Divide input values to normalization_value. |

<a id="filters-throttle"></a>
### `throttle`: Throttle
Fluent Bit page: [Throttle](https://docs.fluentbit.io/manual/data-pipeline/filters/throttle#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/throttle#configuration-parameters) | Yes | `throttle` | Plugin identifier. |
| [`interval`](https://docs.fluentbit.io/manual/data-pipeline/filters/throttle#configuration-parameters) | No |  | Time interval, expressed in sleep format. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/throttle#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/throttle#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`print_status`](https://docs.fluentbit.io/manual/data-pipeline/filters/throttle#configuration-parameters) | No |  | Whether to print status messages with current rate and the limits to information logs. |
| [`rate`](https://docs.fluentbit.io/manual/data-pipeline/filters/throttle#configuration-parameters) | No |  | Amount of messages for the time. |
| [`window`](https://docs.fluentbit.io/manual/data-pipeline/filters/throttle#configuration-parameters) | No |  | Amount of intervals to calculate average over. |

<a id="filters-type-converter"></a>
### `type_converter`: Type converter
Fluent Bit page: [Type converter](https://docs.fluentbit.io/manual/data-pipeline/filters/type-converter#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/type-converter#configuration-parameters) | Yes | `type_converter` | Plugin identifier. |
| [`float_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/type-converter#configuration-parameters) | No |  | This parameter is for a float source. |
| [`int_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/type-converter#configuration-parameters) | No |  | This parameter is for an integer source. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/type-converter#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/type-converter#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`str_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/type-converter#configuration-parameters) | No |  | This parameter is for a string source. |
| [`uint_key`](https://docs.fluentbit.io/manual/data-pipeline/filters/type-converter#configuration-parameters) | No |  | This parameter is for an unsigned integer source. |

<a id="filters-wasm"></a>
### `wasm`: Wasm
Fluent Bit page: [Wasm](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters) | Yes | `wasm` | Plugin identifier. |
| [`accessible_paths`](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters) | No |  | Specify the allowlist of paths to be able to access paths from Wasm programs. |
| [`event_format`](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters) | No |  | Define event format to interact with Wasm programs: msgpack or json. |
| [`function_name`](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters) | No |  | Wasm function name that will be triggered to do filtering. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`wasm_heap_size`](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters) | No |  | Size of the heap size of Wasm execution. |
| [`wasm_path`](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters) | No |  | Path to the built Wasm program that will be used. |
| [`wasm_stack_size`](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters) | No |  | Size of the stack size of Wasm execution. |

## Outputs

[`azure`](#outputs-azure), [`azure_blob`](#outputs-azure-blob), [`azure_kusto`](#outputs-azure-kusto), [`azure_logs_ingestion`](#outputs-azure-logs-ingestion), [`bigquery`](#outputs-bigquery), [`chronicle`](#outputs-chronicle), [`cloudwatch_logs`](#outputs-cloudwatch-logs), [`counter`](#outputs-counter), [`dash0`](#outputs-dash0), [`datadog`](#outputs-datadog), [`dynatrace`](#outputs-dynatrace), [`es`](#outputs-es), [`exit`](#outputs-exit), [`file`](#outputs-file), [`flowcounter`](#outputs-flowcounter), [`forward`](#outputs-forward), [`gelf`](#outputs-gelf), [`http`](#outputs-http), [`influxdb`](#outputs-influxdb), [`kafka`](#outputs-kafka), [`kafka-rest`](#outputs-kafka-rest), [`kinesis_firehose`](#outputs-kinesis-firehose), [`kinesis_streams`](#outputs-kinesis-streams), [`logdna`](#outputs-logdna), [`loki`](#outputs-loki), [`nats`](#outputs-nats), [`nrlogs`](#outputs-nrlogs), [`null`](#outputs-null), [`observe`](#outputs-observe), [`openobserve`](#outputs-openobserve), [`opensearch`](#outputs-opensearch), [`opentelemetry`](#outputs-opentelemetry), [`oracle_log_analytics`](#outputs-oracle-log-analytics), [`parseable`](#outputs-parseable), [`pgsql`](#outputs-pgsql), [`plot`](#outputs-plot), [`prometheus_exporter`](#outputs-prometheus-exporter), [`prometheus_remote_write`](#outputs-prometheus-remote-write), [`s3`](#outputs-s3), [`skywalking`](#outputs-skywalking), [`slack`](#outputs-slack), [`splunk`](#outputs-splunk), [`stackdriver`](#outputs-stackdriver), [`stackdriver_special_fields`](#outputs-stackdriver-special-fields), [`stdout`](#outputs-stdout), [`syslog`](#outputs-syslog), [`tcp`](#outputs-tcp), [`td`](#outputs-td), [`udp`](#outputs-udp), [`vivo_exporter`](#outputs-vivo-exporter), [`websocket`](#outputs-websocket)

<a id="outputs-azure"></a>
### `azure`: Azure Log Analytics
Fluent Bit page: [Azure Log Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) | Yes | `azure` | Plugin identifier. |
| [`customer_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) | No |  | Customer ID or WorkspaceID string. |
| [`log_type`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) | No | `fluentbit` | The name of the event type. |
| [`log_type_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) | No |  | If included, the value for this key checked in the record and if present, will overwrite the log_type. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) | No |  |  |
| [`shared_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) | No |  | The primary or the secondary Connected Sources client authentication key. |
| [`time_generated`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) | No | `false` | If enabled, the HTTP request header time-generated-field will be included so Azure can override the timestamp with the key specified by time_key option. |
| [`time_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) | No | `@timestamp` | Optional. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-azure-blob"></a>
### `azure_blob`: Azure Blob
Fluent Bit page: [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | Yes | `azure_blob` | Plugin identifier. |
| [`account_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No |  | Azure Storage account name. |
| [`auth_type`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `key` | Specify the type to authenticate against the service. |
| [`auto_create_container`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `true` | If container_name doesn't exist in the remote service, enabling this option handles the exception and auto-creates the container. |
| [`azure_blob_buffer_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `key` | Set the Azure Blob buffer key which needs to be specified when using multiple instances of Azure Blob output plugin and buffering is enabled. |
| [`blob_type`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `appendblob` | Specify the desired blob type. |
| [`blob_uri_length`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `64` | Set the length of the generated blob URI used when creating and uploading objects to Azure Blob Storage. |
| [`buffer_dir`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `/tmp/fluent-bit/azure-blob/` | Specifies the location of directory where the buffered data will be stored. |
| [`buffer_file_delete_early`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `false` | Whether to delete the buffered file early after successful blob creation. |
| [`buffering_enabled`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `false` | Enable buffering into disk before ingesting into Azure Blob. |
| [`compress`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No |  | Sets payload compression in network transfer. |
| [`compress_blob`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `false` | Enables compression in the final blockblob file. |
| [`configuration_endpoint_bearer_token`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No |  | Bearer token for the configuration endpoint. |
| [`configuration_endpoint_password`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No |  | Basic authentication password for the configuration endpoint. |
| [`configuration_endpoint_url`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No |  | Configuration endpoint URL. |
| [`configuration_endpoint_username`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No |  | Basic authentication username for the configuration endpoint. |
| [`container_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No |  | Name of the container that will contain the blobs. |
| [`database_file`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No |  | Absolute path to a database file used to store blob file contexts. |
| [`date_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `@timestamp` | Key name used to store the record timestamp. |
| [`delete_on_max_upload_error`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `false` | Whether to delete the buffer file on maximum upload errors. |
| [`emulator_mode`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `false` | To send data to an Azure emulator service like [Azurite](https://github.com/Azure/Azurite), enable this option to format the requests in the expected format. |
| [`endpoint`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No |  | When using an emulator, this option lets you specify the absolute HTTP address of such service. |
| [`file_delivery_attempt_limit`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `1` | Maximum number of delivery attempts for a file. |
| [`io_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `60s` | HTTP IO timeout. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`part_delivery_attempt_limit`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `1` | Maximum number of delivery attempts for a file part. |
| [`part_size`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `25M` | Size of each part when uploading blob files. |
| [`path`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No |  | Optional. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No |  |  |
| [`sas_token`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No |  | Specify the Azure Storage shared access signatures to authenticate against the service. |
| [`scheduler_max_retries`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `3` | Maximum number of retries for the scheduler send blob. |
| [`shared_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No |  | Specify the Azure Storage Shared Key to authenticate against the service. |
| [`store_dir_limit_size`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `8G` | Set the max size of the buffer directory. |
| [`tls`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `off` | Enable or disable TLS encryption. |
| [`unify_tag`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `false` | Whether to create a single buffer file when buffering mode is enabled. |
| [`upload_file_size`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `200M` | Specifies the size of files to be uploaded in MB. |
| [`upload_part_freshness_limit`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `6D` | Maximum lifespan of an uncommitted file part. |
| [`upload_parts_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `10M` | Timeout for uploading parts of a blob file. |
| [`upload_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `30m` | Optional. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-azure-kusto"></a>
### `azure_kusto`: Azure Data Explorer
Fluent Bit page: [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | Yes | `azure_kusto` | Plugin identifier. |
| [`azure_kusto_buffer_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | Yes | `key` | When buffering is true, set the Azure Kusto buffer key which must be specified when using multiple instances of Azure Kusto output plugin and buffering is enabled. |
| [`client_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | Yes |  | Required if managed_identity_client_id isn't set. |
| [`tenant_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | Yes |  | Required if managed_identity_client_id isn't set. |
| [`alias`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Sets an alias, use to define multiple instances of the same output plugin. |
| [`auth_type`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `service_principal` | Set the authentication type: service_principal, managed_identity, or workload_identity. |
| [`blob_uri_length`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `64` | Set the length of generated blob URI before ingesting to Kusto. |
| [`buffer_dir`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `/tmp/fluent-bit/azure-kusto/` | When buffering is true, specifies the location of directory where the buffered data will be stored. |
| [`buffer_file_delete_early`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `false` | When buffering is true, whether to delete the buffered file early after successful blob creation. |
| [`buffering_enabled`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `false` | Enable buffering into disk before ingesting into Azure Kusto. |
| [`client_secret`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Set the client secret (Application Password) of the AAD application used for authentication. |
| [`compression_enabled`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `true` | If enabled, sends compressed HTTP payload (gzip) to Kusto. |
| [`database_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | The database name. |
| [`delete_on_max_upload_error`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `false` | When buffering is true, whether to delete the buffer file on maximum upload errors. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target HTTP server. |
| [`include_tag_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `true` | If enabled, a tag is appended to output. |
| [`include_time_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `true` | If enabled, a timestamp is appended to output. |
| [`ingestion_endpoint`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | The cluster's ingestion endpoint, usually in the form https://ingest-cluster_name.region.kusto.windows.net. |
| [`ingestion_endpoint_connect_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `60` | The connection timeout of various Kusto endpoints in seconds. |
| [`ingestion_mapping_reference`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | The name of a [JSON ingestion mapping](https://docs.microsoft.com/en-us/azure/data-explorer/kusto/management/mappings#json-mapping) that will be used to map the ingested payload into the table columns. |
| [`ingestion_resources_refresh_interval`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `3600` | Set the Azure Kusto ingestion resources refresh interval. |
| [`io_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `60s` | Configure the HTTP IO timeout for uploads. |
| [`log_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `log` | Key name of the log content. |
| [`log_level`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `info` | Specifies the log level for output plugin. |
| [`log_supress_interval`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `0` | Suppresses log messages from output plugin that appear similar within a specified time interval. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Set a tag pattern to match records that output should process. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Set a regular expression to match tags for output routing. |
| [`net.connect_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `10s` | Set maximum time allowed to establish a connection, this time includes the TLS handshake. |
| [`net.connect_timeout_log_error`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `true` | On connection timeout, specify if it should log an error. |
| [`net.dns.mode`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Select the primary DNS connection type (TCP or UDP). |
| [`net.dns.prefer_ipv4`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `false` | Select the primary DNS resolver type (LEGACY or ASYNC). |
| [`net.dns.prefer_ipv6`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `false` | Prioritize IPv6 DNS results when trying to establish a connection. |
| [`net.dns.resolver`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `LEGACY` | Select the primary DNS resolver type (LEGACY or ASYNC). |
| [`net.io_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `0s` | Set maximum time a connection can stay idle while assigned. |
| [`net.keepalive`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `false` | Enable or disable Keepalive support. |
| [`net.keepalive_idle_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `false` | Set maximum time allowed for an idle Keepalive connection.. |
| [`net.keepalive_max_recycle`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `2000` | Set maximum number of times a keepalive connection can be used before it's retried. |
| [`net.max_worker_connections`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `0` | Set the maximum number of active TCP connections that can be used per worker thread. |
| [`net.proxy_env_ignore`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `false` | Ignore the environment variables HTTP_PROXY, HTTPS_PROXY and NO_PROXY when set. |
| [`net.source_address`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Specify network address to bind for data traffic. |
| [`net.tcp_keepalive`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `off` | Enable or disable Keepalive support. |
| [`net.tcp_keepalive_interval`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `-1` | Interval between TCP keepalive probes when no response is received on a keepidle probe. |
| [`net.tcp_keepalive_probes`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `-1` | Number of unacknowledged probes to consider a connection dead. |
| [`net.tcp_keepalive_time`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `-1` | Interval between the last data packet sent and the first TCP keepalive probe. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `0` | TCP port of the target HTTP server. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  |  |
| [`retry_limit`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `1` | Set retry limit for output plugin when delivery fails. |
| [`scheduler_max_retries`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `3` | Optional. |
| [`store_dir_limit_size`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `8G` | When buffering is true, set the max size of the buffer directory. |
| [`table_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | The table name. |
| [`tag_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `tag` | The key name of tag. |
| [`time_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `timestamp` | The key name of time. |
| [`tls`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `off` | Enable or disable TLS/SSL support. |
| [`tls.ca_file`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Absolute path to CA certificate file. |
| [`tls.ca_path`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Absolute path to scan for certificate files. |
| [`tls.ciphers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Specify TLS ciphers up to TLSv1.2. |
| [`tls.crt_file`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Absolute path to Certificate file. |
| [`tls.debug`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `1` | Set TLS debug level. |
| [`tls.key_file`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Absolute path to private Key file. |
| [`tls.key_passwd`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Optional password for tls.key_file file. |
| [`tls.max_version`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Specify the maximum version of TLS. |
| [`tls.min_version`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Specify the minimum version of TLS. |
| [`tls.verify`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `on` | Force certificate validation. |
| [`tls.verify_hostname`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `off` | Enable or disable to verify hostname. |
| [`tls.vhost`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Hostname to be used for TLS SNI extension. |
| [`tls.windows.certstore_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Sets the certstore name on an output (Windows). |
| [`tls.windows.use_enterprise_store`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Sets whether using enterprise certificate store or not on an output (Windows). |
| [`unify_tag`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `true` | This creates a single buffer file when the buffering mode is true. |
| [`upload_file_size`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `200MB` | Specifies the size of files to be uploaded in megabytes. |
| [`upload_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No | `30m` | Optionally specify a timeout for uploads. |
| [`workload_identity_token_file`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) | No |  | Set the token path for workload identity authentication. |

<a id="outputs-azure-logs-ingestion"></a>
### `azure_logs_ingestion`: Azure Logs Ingestion API
Fluent Bit page: [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) | Yes | `azure_logs_ingestion` | Plugin identifier. |
| [`auth_url`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) | Yes |  | Override the OAuth 2.0 token endpoint URL. |
| [`tenant_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) | Yes |  | The tenant ID of the Azure Active Directory (AAD) application. |
| [`client_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No |  | The client ID of the AAD application. |
| [`client_secret`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No |  | The client secret of the AAD application ([App Secret](https://docs.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal#option-2-create-a-new-application-secret)). |
| [`compress`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No | `false` | Optional. |
| [`dce_url`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No |  | Data Collection Endpoint (DCE) URL. |
| [`dcr_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No |  | Data Collection Rule (DCR) [immutable ID](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/tutorial-logs-ingestion-portal#collect-information-from-the-dcr). |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No |  |  |
| [`table_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No |  | The name of the custom log table (include the _CL suffix as well if applicable). |
| [`time_generated`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No | `false` | Optional. |
| [`time_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No | `@timestamp` | Optional. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-bigquery"></a>
### `bigquery`: Google Cloud BigQuery
Fluent Bit page: [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | Yes | `bigquery` | Plugin identifier. |
| [`dataset_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | Yes |  | The dataset ID of the BigQuery dataset to write into. |
| [`google_service_account`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | Yes |  | The email address of the Google service account to impersonate. |
| [`table_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | Yes |  | The table ID of the BigQuery table to write into. |
| [`aws_region`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | No |  | Used to construct a regional endpoint for AWS STS to verify AWS credentials obtained by Fluent Bit. |
| [`enable_identity_federation`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | No | `Off` | Enables workload identity federation as an alternative authentication method. |
| [`google_service_credentials`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | No | `Value of the environment variable `$GOOGLE_SERVICE_CREDENTIALS`.` | Absolute path to a Google Cloud credentials JSON file. |
| [`ignore_unknown_values`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | No | `Off` | Accept rows that contain values that don't match the schema. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`pool_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | No |  | GCP workload identity pool where the identity provider was created. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | No |  |  |
| [`project_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | No | `Value of the `project_id` in the credentials file.` | The project ID containing the BigQuery dataset to stream into. |
| [`project_number`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | No |  | GCP project number where the identity provider was created. |
| [`provider_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | No |  | GCP workload identity provider. |
| [`service_account_email`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | No |  | The service account email address. |
| [`service_account_secret`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | No |  | The service account private key. |
| [`skip_invalid_rows`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | No | `Off` | Insert all valid rows of a request, even if invalid rows exist. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-chronicle"></a>
### `chronicle`: Google Chronicle
Fluent Bit page: [Google Chronicle](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) | Yes | `chronicle` | Plugin identifier. |
| [`customer_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) | No |  | The customer ID identifying the Google Chronicle tenant to stream into. |
| [`google_service_credentials`](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) | No | `Value of the environment variable `$GOOGLE_SERVICE_CREDENTIALS` | Absolute path to a Google Cloud credentials JSON file. |
| [`log_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) | No |  | By default, the whole log record is sent to Google Chronicle. |
| [`log_type`](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) | No |  | The log type to parse logs as. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) | No |  |  |
| [`project_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) | No | `Value of the `project_id` in the credentials file` | The project ID containing the Google Chronicle tenant to stream into. |
| [`region`](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) | No |  | The GCP region in which to store security logs. |
| [`service_account_email`](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) | No | `Value of the environment variable `$SERVICE_ACCOUNT_EMAIL` | Account email associated with the service. |
| [`service_account_secret`](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) | No | `Value of the environment variable `$SERVICE_ACCOUNT_SECRET` | Private key content associated with the service account. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-cloudwatch-logs"></a>
### `cloudwatch_logs`: Amazon CloudWatch
Fluent Bit page: [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | Yes | `cloudwatch_logs` | Plugin identifier. |
| [`region`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | Yes |  | The AWS region to send logs to. |
| [`add_entity`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No | `false` | Add entity to PutLogEvent calls. |
| [`alias`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Sets an alias, use for multiple instances of the same output plugin. |
| [`auto_create_group`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No | `false` | Automatically create the log group. |
| [`auto_retry_requests`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No | `true` | Immediately retry failed requests to AWS services once. |
| [`endpoint`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Specify a custom endpoint for the CloudWatch Logs API. |
| [`external_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Specify an external ID for the STS API, can be used with the role_arn parameter if your role requires an external ID. |
| [`extra_user_agent`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | This option appends a string to the default user agent. |
| [`log_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | An optional parameter that can be used to tell CloudWatch the format of the data. |
| [`log_group_class`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No | `STANDARD` | Specifies the log storage class for new log groups when auto_create_group is set to true. |
| [`log_group_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | The name of the CloudWatch log group that you want log records sent to. |
| [`log_group_template`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Template for CW Log Group name using record accessor syntax. |
| [`log_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | By default, the whole log record will be sent to CloudWatch. |
| [`log_level`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No | `info` | Specifies the log level for output plugin. |
| [`log_retention_days`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No | `0` | If set to a number greater than zero, and newly create log group's retention policy is set to this many days. |
| [`log_stream_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | The name of the CloudWatch log stream that you want log records sent to. |
| [`log_stream_prefix`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Prefix for the log stream name. |
| [`log_stream_template`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Template for CloudWatch Log Stream name using record accessor syntax. |
| [`log_suppress_interval`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No | `0` | Suppresses log messages from output plugin that appear similar within a specified time interval. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Set a tag pattern to match records that output should process. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Set a regular expression to match tags for output routing. |
| [`metric_dimensions`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Metric dimensions is a list of lists. |
| [`metric_namespace`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | An optional string representing the CloudWatch namespace for the metrics. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  |  |
| [`profile`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Option to specify an AWS Profile for credentials. |
| [`retry_limit`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No | `1` | Set retry limit for output plugin when delivery fails. |
| [`role_arn`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | ARN of an IAM role to assume for cross account access. |
| [`sts_endpoint`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Specify a custom STS endpoint for the AWS STS API. |
| [`tls.windows.certstore_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Sets the certificate store name on an output (Windows). |
| [`tls.windows.use_enterprise_store`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No |  | Sets whether using enterprise certificate store or not on an output (Windows). |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) | No | `1` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-counter"></a>
### `counter`: Counter
Fluent Bit page: [Counter](https://docs.fluentbit.io/manual/data-pipeline/router)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/router) | Yes | `counter` | Plugin identifier. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/router) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/router) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/router) | No |  |  |

<a id="outputs-dash0"></a>
### `dash0`: Dash0
Fluent Bit page: [Dash0](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) | Yes | `dash0` | Plugin identifier. |
| [`header`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) | No | `Authorization Bearer {your-Auth-token-here}` | The specific header for bearer authorization, where {your-Auth-token-here} is your Dash0 Auth Token. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) | No | `ingress.eu-west-1.aws.dash0.com` | Your Dash0 ingress endpoint. |
| [`logs_uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) | No | `/v1/logs` | Specify an optional HTTP URI for the target web server listening for logs. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`metrics_uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) | No | `/v1/metrics` | Specify an optional HTTP URI for the target web server listening for metrics. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) | No | `443` | TCP port of your Dash0 ingress endpoint. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) | No |  |  |
| [`traces_uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) | No | `/v1/traces` | Specify an optional HTTP URI for the target web server listening for traces. |

<a id="outputs-datadog"></a>
### `datadog`: Datadog
Fluent Bit page: [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | Yes | `datadog` | Plugin identifier. |
| [`apikey`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No |  | Your [Datadog API key](https://app.datadoghq.com/account/settings#api). |
| [`compress`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No | `false` | Compresses the payload in GZIP format. |
| [`dd_hostname`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No |  | The host the emitted logs should be associated with. |
| [`dd_message_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No | `log` | By default, the plugin searches for the key log and remaps the value to the key message. |
| [`dd_service`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No |  | Recommended. |
| [`dd_source`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No |  | Recommended. |
| [`dd_tags`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No |  | The [tags](https://docs.datadoghq.com/getting_started/tagging/) you want to assign to your logs in Datadog. |
| [`header`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No |  | Add additional arbitrary HTTP header key/value pair. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No | `http-intake.logs.datadoghq.com` | The Datadog server where you are sending your logs. |
| [`include_tag_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No | `false` | If enabled, a tag is appended to the output. |
| [`json_date_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No | `timestamp` | Date key name for output. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No |  |  |
| [`provider`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No |  | To activate remapping, specify the configuration flag provider with the value ecs. |
| [`proxy`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No |  | Specifies an HTTP proxy. |
| [`tag_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No | `tagkey` | The key name of tag. |
| [`tls`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No | `off` | End-to-end security communications protocol. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-dynatrace"></a>
### `dynatrace`: Dynatrace
Fluent Bit page: [Dynatrace](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) | Yes | `dynatrace` | Plugin identifier. |
| [`allow_duplicated_headers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) | No | `false` | Specifies duplicated header use. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) | No | `json` | The data format to be used in the HTTP request body. |
| [`header`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) | No | `Content-Type application/json; charset=utf-8` | The specific header for content-type. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) | No | `{your-environment-id}.live.dynatrace.com` | Your Dynatrace environment hostname where {your-environment-id} is your environment ID. |
| [`json_date_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) | No | `iso8601` | Date format standard for JSON. |
| [`json_date_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) | No | `timestamp` | Field name specifying message timestamp. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) | No | `443` | TCP port of your Dynatrace host. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) | No |  |  |
| [`tls`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) | No | `on` | Specify to use TLS. |
| [`tls.verify`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) | No | `on` | TLS verification. |
| [`uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) | No | `/api/v2/logs/ingest` | Specify the HTTP URI for Dynatrace log ingest API. |

<a id="outputs-es"></a>
### `es`: Elasticsearch
Fluent Bit page: [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | Yes | `es` | Plugin identifier. |
| [`buffer_size`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | Yes | `512k` | Specify the buffer size used to read the response from the Elasticsearch HTTP service. |
| [`http_api_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | Yes |  | API key for authenticating with Elasticsearch. |
| [`replace_dots`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | Yes | `Off` | When enabled, replace field name dots with underscore. |
| [`aws_auth`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | Enable AWS Sigv4 Authentication for Amazon OpenSearch Service. |
| [`aws_external_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | External ID for the AWS IAM Role specified with aws_role_arn. |
| [`aws_profile`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | AWS profile name. |
| [`aws_region`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Specify the AWS region for Amazon OpenSearch Service. |
| [`aws_role_arn`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | AWS IAM Role to assume to put records to your Amazon cluster. |
| [`aws_service_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `es` | Service name to use in AWS Sigv4 signature. |
| [`aws_sts_endpoint`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Specify the custom STS endpoint to be used with STS API for Amazon OpenSearch Service. |
| [`cloud_auth`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Specify the credentials to use to connect to Elastic's Elasticsearch Service running on Elastic Cloud. |
| [`cloud_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | If using Elastic's Elasticsearch Service you can specify the cloud_id of the cluster running. |
| [`compress`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Set payload compression mechanism. |
| [`current_time_index`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | Use current time for index generation instead of message record. |
| [`generate_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | When enabled, generate _id for outgoing records. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target Elasticsearch instance. |
| [`http_passwd`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Password for user defined in http_user. |
| [`http_user`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Optional username credential for Elastic X-Pack access. |
| [`id_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | If set, _id will be the value of the key from the incoming record and generate_id option is ignored. |
| [`include_tag_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | When enabled, appends the Tag name to the record. |
| [`index`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `fluent-bit` | Index name. |
| [`logstash_dateformat`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `%Y.%m.%d` | Time format based on [strftime](https://man7.org/linux/man-pages/man3/strftime.3.html) to generate the second part of the Index name. |
| [`logstash_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | Enable Logstash format compatibility. |
| [`logstash_prefix`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `logstash` | When logstash_format is enabled, the Index name is composed using a prefix and the date. |
| [`logstash_prefix_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | When included, the value of the key in the record is evaluated as a key reference and overrides logstash_prefix for index generation. |
| [`logstash_prefix_separator`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `-` | Set a separator between logstash_prefix and date. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`path`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Elasticsearch accepts new data on HTTP query path /_bulk. |
| [`pipeline`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  | Define which pipeline the database should use. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `9200` | TCP port of the target Elasticsearch instance. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No |  |  |
| [`suppress_type_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | When enabled, mapping types is removed and type option is ignored. |
| [`tag_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `flb-key` | When include_tag_key is enabled, this property defines the key name for the tag. |
| [`time_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `@timestamp` | When logstash_format is enabled, each record will get a new timestamp field. |
| [`time_key_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `%Y-%m-%dT%H:%M:%S` | When logstash_format is enabled, this property defines the format of the timestamp. |
| [`time_key_nanos`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | When logstash_format is enabled, enabling this property sends nanosecond precision timestamps. |
| [`trace_error`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | If Elasticsearch returns an error, print the Elasticsearch API request and response for diagnostics. |
| [`trace_output`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `Off` | Print all Elasticsearch API request payloads to stdout for diagnostics. |
| [`type`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `_doc` | Type name. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `2` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |
| [`write_operation`](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) | No | `create` | Operation type for records. |

<a id="outputs-exit"></a>
### `exit`: Exit
Fluent Bit page: [Exit](https://docs.fluentbit.io/manual/data-pipeline/outputs/exit#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/exit#configuration-parameters) | Yes | `exit` | Plugin identifier. |
| [`flush_count`](https://docs.fluentbit.io/manual/data-pipeline/outputs/exit#configuration-parameters) | No | `-1` | Number of flushes to wait for before exiting. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/exit#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/exit#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/exit#configuration-parameters) | No |  |  |
| [`record_count`](https://docs.fluentbit.io/manual/data-pipeline/outputs/exit#configuration-parameters) | No | `-1` | Number of records to wait for before exiting. |
| [`time_count`](https://docs.fluentbit.io/manual/data-pipeline/outputs/exit#configuration-parameters) | No | `-1` | Number of seconds to wait for before exiting. |

<a id="outputs-file"></a>
### `file`: File
Fluent Bit page: [File](https://docs.fluentbit.io/manual/data-pipeline/outputs/file#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/file#configuration-parameters) | Yes | `file` | Plugin identifier. |
| [`file`](https://docs.fluentbit.io/manual/data-pipeline/outputs/file#configuration-parameters) | No |  | Set filename to store the records. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/file#configuration-parameters) | No |  | The [format](#format) of the file content. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/file#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/file#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`mkdir`](https://docs.fluentbit.io/manual/data-pipeline/outputs/file#configuration-parameters) | No | `false` | Recursively create output directory if it doesn't exist. |
| [`path`](https://docs.fluentbit.io/manual/data-pipeline/outputs/file#configuration-parameters) | No |  | Directory path to store files. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/file#configuration-parameters) | No |  |  |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/file#configuration-parameters) | No | `1` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-flowcounter"></a>
### `flowcounter`: Flow counter
Fluent Bit page: [Flow counter](https://docs.fluentbit.io/manual/data-pipeline/outputs/flowcounter#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/flowcounter#configuration-parameters) | Yes | `flowcounter` | Plugin identifier. |
| [`event_based`](https://docs.fluentbit.io/manual/data-pipeline/outputs/flowcounter#configuration-parameters) | No | `false` | When enabled, use the timestamp from the log event for time bucketing instead of the current wall-clock time. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/flowcounter#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/flowcounter#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/flowcounter#configuration-parameters) | No |  |  |
| [`unit`](https://docs.fluentbit.io/manual/data-pipeline/outputs/flowcounter#configuration-parameters) | No | `minute` | The unit of duration. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/flowcounter#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-forward"></a>
### `forward`: Forward
Fluent Bit page: [Forward](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | Yes | `forward` | Plugin identifier. |
| [`add_option`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No |  | Add an extra Forward protocol option. |
| [`compress`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No |  | Set to gzip to enable gzip compression. |
| [`fluentd_compat`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No | `false` | Send metrics and traces using a Fluentd-compatible format. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No | `127.0.0.1` | Target host where Fluent Bit or Fluentd are listening for Forward messages. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No | `24224` | TCP port of the target service. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No |  |  |
| [`require_ack_response`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No | `false` | Send the chunk option and wait for an ack response from the server. |
| [`retain_metadata_in_forward_mode`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No | `false` | Retain metadata when operating in forward mode. |
| [`send_options`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No | `false` | Always send Forward protocol options, including "size". |
| [`tag`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No |  | Overwrite the tag as Fluent Bit transmits. |
| [`time_as_integer`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No | `false` | Set timestamps in integer format. |
| [`unix_path`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No |  | Specify the path to a Unix socket to send a Forward message. |
| [`upstream`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No |  | If Forward connects to an upstream definition instead of a basic host, this property defines the absolute path for the upstream configuration file. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) | No | `2` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-gelf"></a>
### `gelf`: Graylog Extended Log Format (GELF)
Fluent Bit page: [Graylog Extended Log Format (GELF)](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | Yes | `gelf` | Plugin identifier. |
| [`gelf_host_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | Yes |  | Key whose value is used as the name of the host, source, or application that sent this message. |
| [`gelf_level_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | Yes |  | Key to be used as the log level. |
| [`gelf_short_message_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | Yes |  | A short descriptive message. |
| [`compress`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | No | `true` | If transport protocol is udp, set this to compress UDP packets. |
| [`gelf_full_message_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | No |  | Key to use as the long message that can, for example, contain a backtrace. |
| [`gelf_tag_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | No |  | Key to be used for tag. |
| [`gelf_timestamp_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | No |  | Your log timestamp. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target Graylog server. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | No |  | Pattern to match which tags of logs to be sent by this plugin. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`mode`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | No | `udp` | The protocol to use. |
| [`packet_size`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | No | `1420` | If transport protocol is udp, you can set the size of packets to be sent. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | No | `12201` | The port that your Graylog GELF input is listening on. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | No |  |  |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-http"></a>
### `http`: HTTP
Fluent Bit page: [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | Yes | `http` | Plugin identifier. |
| [`body_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | Yes |  | Specify the key to use as the body of the request (must prefix with $). |
| [`headers_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | Yes |  | Specify the key to use as the headers of the request (must prefix with $). |
| [`allow_duplicated_headers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `true` | Specify if duplicated headers are allowed. |
| [`aws_auth`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `false` | Enable AWS SigV4 authentication. |
| [`aws_external_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | External ID for the AWS IAM Role specified with aws_role_arn, used by SigV4 authentication. |
| [`aws_profile`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | AWS Profile name. |
| [`aws_region`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Specify the AWS region of your service, used by SigV4 authentication. |
| [`aws_role_arn`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | AWS IAM Role to assume, used by SigV4 authentication. |
| [`aws_service`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Specify the AWS service code of your service, used by SigV4 authentication (for example, es, xray). |
| [`aws_sts_endpoint`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Specify the custom STS endpoint to be used by STS API. |
| [`compress`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Set payload compression mechanism. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `json` | Specify the data format to be used in the HTTP request body. |
| [`gelf_full_message_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Specify the key to use for the full message in gelf format. |
| [`gelf_host_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Specify the key to use for the host in gelf format. |
| [`gelf_level_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Specify the key to use for the level in gelf format. |
| [`gelf_short_message_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Specify the key to use as the short message in gelf format. |
| [`gelf_timestamp_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Specify the key to use for timestamp in gelf format. |
| [`header`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Add a HTTP header key/value pair. |
| [`header_tag`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Specify an optional HTTP header field for the original message tag. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target HTTP Server. |
| [`http.read_idle_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `0s` | Set maximum allowed time between two consecutive reads. |
| [`http.response_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `60s` | Set maximum time to wait for a server response. |
| [`http_method`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `POST` | Specify POST versus PUT HTTP method. |
| [`http_passwd`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Basic Auth password. |
| [`http_user`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Basic Auth username. |
| [`json_date_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Specify the format of the date. |
| [`json_date_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `date` | Specify the name of the time key in the output record. |
| [`log_response_payload`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `true` | Specify if the response payload should be logged or not. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`oauth2.audience`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Optional OAuth 2.0 audience parameter. |
| [`oauth2.auth_method`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `basic` | OAuth 2.0 client authentication method. |
| [`oauth2.client_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | OAuth 2.0 client ID. |
| [`oauth2.client_secret`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | OAuth 2.0 client secret. |
| [`oauth2.connect_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `0s` | Connect timeout for OAuth 2.0 token requests. |
| [`oauth2.enable`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `false` | Enable OAuth 2.0 client credentials for outgoing requests. |
| [`oauth2.jwt_aud`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Audience for private_key_jwt JSON Web Token (JWT) assertion. |
| [`oauth2.jwt_cert_file`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Path to certificate file used by private_key_jwt. |
| [`oauth2.jwt_header`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `kid` | JWT header claim name for private_key_jwt thumbprint. |
| [`oauth2.jwt_key_file`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Path to PEM private key file used by private_key_jwt. |
| [`oauth2.jwt_ttl_seconds`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `300` | Lifetime in seconds for private_key_jwt JWT client assertions. |
| [`oauth2.refresh_skew_seconds`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `60` | Seconds before expiry at which to refresh the access token. |
| [`oauth2.resource`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Optional OAuth 2.0 resource parameter. |
| [`oauth2.scope`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Optional OAuth 2.0 scope. |
| [`oauth2.timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `0s` | Timeout for OAuth 2.0 token requests. |
| [`oauth2.token_url`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | OAuth 2.0 token endpoint URL. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `80` | TCP port of the target HTTP Server. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  |  |
| [`proxy`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Specify an HTTP Proxy. |
| [`uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No |  | Specify an optional HTTP URI for the target web server. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) | No | `2` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-influxdb"></a>
### `influxdb`: InfluxDB
Fluent Bit page: [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | Yes | `influxdb` | Plugin identifier. |
| [`add_integer_suffix`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No | `false` | Use integer type of [InfluxDB's line protocol](https://docs.influxdata.com/influxdb/v1/write_protocols/line_protocol_reference/). |
| [`auto_tags`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No | `false` | Automatically tag keys where value is string. |
| [`bucket`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No |  | InfluxDB bucket name where records will be inserted. |
| [`database`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No | `fluentbit` | InfluxDB database name where records will be inserted. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target InfluxDB service. |
| [`http_header`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No |  | Add a HTTP header key/value pair. |
| [`http_passwd`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No |  | Password for user defined in http_user. |
| [`http_token`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No |  | Authentication token used with InfluxDB v2. |
| [`http_user`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No |  | Optional username for HTTP Basic Authentication. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`org`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No | `fluent` | InfluxDB organization name where the bucket is (v2 only). |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No | `8086` | TCP port of the target InfluxDB service. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No |  |  |
| [`sequence_tag`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No |  | The name of the tag whose value is incremented for consecutive simultaneous events. |
| [`tag_keys`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No |  | Space-separated list of keys to tag. |
| [`uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No |  | Custom URI endpoint. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-kafka"></a>
### `kafka`: Kafka Producer
Fluent Bit page: [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | Yes | `kafka` | Plugin identifier. |
| [`aws_msk_iam_cluster_arn`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | Yes |  | Full ARN of the MSK cluster used for region extraction. |
| [`aws_msk_iam`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No | `false` | Enable AWS MSK IAM authentication. |
| [`brokers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | Single or multiple list of Kafka brokers. |
| [`client_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | Client ID to use when connecting to Kafka. |
| [`dynamic_topic`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No | `false` | Adds unknown topics (found in topic_key) to topics. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No | `json` | Specify data format. |
| [`gelf_full_message_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | Key to use as the long message for GELF format output. |
| [`gelf_host_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | Key to use as the host for GELF format output. |
| [`gelf_level_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | Key to use as the log level for GELF format output. |
| [`gelf_short_message_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | Key to use as the short message for GELF format output. |
| [`gelf_timestamp_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | Key to use as the timestamp for GELF format output. |
| [`group_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | Consumer group ID. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`message_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | Optional key to store the message. |
| [`message_key_field`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | If set, the value of message_key_field in the record will indicate the message key. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  |  |
| [`queue_full_retries`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No | `10` | Number of local retries to enqueue data when the rdkafka queue is full. |
| [`raw_log_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | When using the raw format, the value of raw_log_key in the record is sent to Kafka as the payload. |
| [`rdkafka.{property}`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | {property} can be any [librdkafka property](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md). |
| [`schema_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | Avro schema ID. |
| [`schema_str`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | Avro schema string. |
| [`timestamp_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No | `double` | Specify the timestamp format. |
| [`timestamp_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No | `@timestamp` | Key to store the record timestamp. |
| [`topic_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No |  | If multiple topics exist, the value of topic_key in the record indicates the topic to use. |
| [`topics`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No | `fluent-bit` | Single topic or comma-separated list of topics that Fluent Bit will use to send messages to Kafka. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-kafka-rest"></a>
### `kafka-rest`: Kafka REST Proxy
Fluent Bit page: [Kafka REST Proxy](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | Yes | `kafka-rest` | Plugin identifier. |
| [`avro_http_header`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `false` | Include Avro header in the HTTP request. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target Kafka REST Proxy server. |
| [`include_tag_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `false` | Append the tag name to the final record. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`message_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No |  | Optional message key to set. |
| [`partition`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `-1` | Optional partition number. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `8082` | TCP port of the target Kafka REST Proxy server. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No |  |  |
| [`tag_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `_flb-key` | If include_tag_key is enabled, defines the key name for the tag. |
| [`time_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `@timestamp` | Name of the field that holds the record timestamp. |
| [`time_key_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `%Y-%m-%dT%H:%M:%S` | Format of the timestamp. |
| [`topic`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `fluent-bit` | Set the Kafka topic. |
| [`url_path`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No |  | Optional HTTP URL path for the target web server. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-kinesis-firehose"></a>
### `kinesis_firehose`: Amazon Kinesis Data Firehose
Fluent Bit page: [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | Yes | `kinesis_firehose` | Plugin identifier. |
| [`region`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | Yes |  | The AWS region. |
| [`auto_retry_requests`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No | `true` | Immediately retry failed requests to AWS services once. |
| [`compression`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No |  | Compression type for records sent to Firehose. |
| [`delivery_stream`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No |  | The name of the Kinesis Firehose Delivery stream that you want log records sent to. |
| [`endpoint`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No |  | Specify a custom endpoint for the Firehose API. |
| [`external_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No |  | Specify an external ID for the STS API. |
| [`log_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No |  | By default, the whole log record will be sent to Firehose. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No |  |  |
| [`profile`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No |  | AWS profile name to use. |
| [`role_arn`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No |  | ARN of an IAM role to assume (for cross-account access). |
| [`simple_aggregation`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No | `false` | Enable record aggregation to combine multiple records into single API calls. |
| [`sts_endpoint`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No |  | Custom endpoint for the STS API. |
| [`time_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No |  | Add the timestamp to the record under this key. |
| [`time_key_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No |  | strftime compliant format string for the timestamp; for example, the default is %Y-%m-%dT%H:%M:%S. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) | No | `1` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-kinesis-streams"></a>
### `kinesis_streams`: Amazon Kinesis Data Streams
Fluent Bit page: [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | Yes | `kinesis_streams` | Plugin identifier. |
| [`region`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | Yes |  | The AWS region. |
| [`auto_retry_requests`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No | `true` | Immediately retry failed requests to AWS services once. |
| [`compression`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No |  | Compression type for records sent to Kinesis Data Streams. |
| [`endpoint`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No |  | Specify a custom endpoint for the Kinesis API. |
| [`external_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No |  | Specify an external ID for the STS API. |
| [`log_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No |  | By default, the whole log record will be sent to Kinesis. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No | `443` | TCP port of the Kinesis Streams service. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No |  |  |
| [`profile`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No |  | AWS profile name to use. |
| [`role_arn`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No |  | ARN of an IAM role to assume (for cross-account access). |
| [`simple_aggregation`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No | `false` | Enable record aggregation to combine multiple records into single API calls. |
| [`stream`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No |  | The name of the Kinesis stream that you want log records sent to. |
| [`sts_endpoint`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No |  | Custom endpoint for the STS API. |
| [`time_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No |  | Add the timestamp to the record under this key. |
| [`time_key_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No |  | The strftime compliant format string for the timestamp. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) | No | `1` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-logdna"></a>
### `logdna`: LogDNA
Fluent Bit page: [LogDNA](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) | Yes | `logdna` | Plugin identifier. |
| [`api_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) | Yes |  | Required. |
| [`app`](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) | No | `Fluent Bit` | Name of the application. |
| [`file`](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) | No |  | Optional name of a file being monitored. |
| [`hostname`](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) | No |  | Name of the local machine or device where Fluent Bit is running. |
| [`ip`](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) | No |  | The IP address of the local hostname. |
| [`logdna_endpoint`](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) | No | `/logs/ingest` | The LogDNA ingestion endpoint. |
| [`logdna_host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) | No | `logs.logdna.com` | The LogDNA API host address. |
| [`logdna_port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) | No | `443` | The LogDNA TCP port. |
| [`mac`](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) | No |  | The MAC address. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) | No |  |  |
| [`tags`](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) | No |  | A list of comma-separated strings to group records in LogDNA and simplify the query with filters. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-loki"></a>
### `loki`: Loki
Fluent Bit page: [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | Yes | `loki` | Plugin identifier. |
| [`uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | Yes | `/loki/api/v1/push` | Specify a custom HTTP URI. |
| [`auto_kubernetes_labels`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No | `false` | If set to true, adds all Kubernetes labels to the stream labels. |
| [`bearer_token`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  | Set bearer token authentication token value. |
| [`buffer_size`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No | `512KB` | Maximum HTTP response buffer size. |
| [`compress`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  | Set payload compression mechanism. |
| [`drop_single_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  | When set to true and after extracting labels only a single key remains, the log line sent to Loki will be the value of that key in line_format. |
| [`header`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  | Add additional arbitrary HTTP header key/value pair. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No | `127.0.0.1` | Loki base hostname or IP address. |
| [`http_passwd`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  | Set HTTP basic authentication password. |
| [`http_user`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  | Set HTTP basic authentication user name. |
| [`label_keys`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  | (Optional.) List of record keys that will be placed as stream labels. |
| [`label_map_path`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  | Specify the label map path. |
| [`labels`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No | `job=fluent-bit` | Stream labels for API request. |
| [`line_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No | `json` | Format to use when flattening the record to a log line. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No | `3100` | The Loki TCP port. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  |  |
| [`remove_keys`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  | (Optional.) List of keys to remove. |
| [`structured_metadata`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  | (Optional.) Comma-separated list of key=value strings specifying structured metadata for the log line. |
| [`structured_metadata_map_keys`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  | (Optional.) Comma-separated list of record key strings specifying record values of type map, used to dynamically populate structured metadata for the log line. |
| [`tenant_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  | Tenant ID used by default to push logs to Loki. |
| [`tenant_id_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No |  | Specify the name of the key from the original record that contains the Tenant ID. |
| [`tls`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No | `off` | Use TLS authentication. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-nats"></a>
### `nats`: NATS
Fluent Bit page: [NATS](https://docs.fluentbit.io/manual/data-pipeline/outputs/nats#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/nats#configuration-parameters) | Yes | `nats` | Plugin identifier. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/nats#configuration-parameters) | No | `127.0.0.1` | The IP address or hostname of the NATS server. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/nats#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/nats#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/nats#configuration-parameters) | No | `4222` | The TCP port of the target NATS server. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/nats#configuration-parameters) | No |  |  |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/nats#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-nrlogs"></a>
### `nrlogs`: New Relic
Fluent Bit page: [New Relic](https://docs.fluentbit.io/manual/data-pipeline/outputs/new-relic#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/new-relic#configuration-parameters) | Yes | `nrlogs` | Plugin identifier. |
| [`api_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/new-relic#configuration-parameters) | Yes |  | Your [New Relic API key](https://docs.newrelic.com/docs/apis/intro-apis/new-relic-api-keys/). |
| [`license_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/new-relic#configuration-parameters) | Yes |  | Your [New Relic license key](https://docs.newrelic.com/docs/apis/intro-apis/new-relic-api-keys/). |
| [`base_uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/new-relic#configuration-parameters) | No | `https://log-api.newrelic.com/log/v1` | The New Relic API endpoint. |
| [`compress`](https://docs.fluentbit.io/manual/data-pipeline/outputs/new-relic#configuration-parameters) | No | `gzip` | Sets the compression mechanism for the payload. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/new-relic#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/new-relic#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/new-relic#configuration-parameters) | No |  |  |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/new-relic#configuration-parameters) | No | `0` | Sets the number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-null"></a>
### `null`: Null
Fluent Bit page: [Null](https://docs.fluentbit.io/manual/data-pipeline/outputs/null#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/null#configuration-parameters) | Yes | `null` | Plugin identifier. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/null#configuration-parameters) | No | `msgpack` | Specify the data format. |
| [`json_date_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/null#configuration-parameters) | No | `double` | Specify the format of the date. |
| [`json_date_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/null#configuration-parameters) | No | `date` | Specify the name of the time key in the output record. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/null#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/null#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/null#configuration-parameters) | No |  |  |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/null#configuration-parameters) | No | `1` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-observe"></a>
### `observe`: Observe
Fluent Bit page: [Observe](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) | Yes | `observe` | Plugin identifier. |
| [`compress`](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) | No | `gzip` | Sets the payload compression mechanism. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) | No | `msgpack` | The data format to be used in the HTTP request body. |
| [`header`](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) | No | `Authorization Bearer ${OBSERVE_TOKEN}` | The specific header that provides the Observe token needed to authorize sending data [into a data stream](https://docs.observeinc.com/en/latest/content/data-ingestion/datastreams.html?highlight=ingest%20token#create-a-datastream). |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) | No | `OBSERVE_CUSTOMER.collect.observeinc.com` | IP address or hostname of the Observe data collection endpoint. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) | No | `443` | TCP port to use when sending data to Observe. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) | No |  |  |
| [`tls`](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) | No | `on` | Specifies whether to use TLS. |
| [`tls.ca_file`](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) | No |  | For Windows only: the path to the root cert. |
| [`uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) | No | `/v1/http/fluentbit` | Specifies the HTTP URI for Observe. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-openobserve"></a>
### `openobserve`: OpenObserve
Fluent Bit page: [OpenObserve](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) | Yes | `openobserve` | Plugin identifier. |
| [`compress`](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) | No |  | Recommended. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) | No | `json` | The format of the log payload. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) | No | `localhost` | The OpenObserve server where you are sending logs. |
| [`http_passwd`](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) | No |  | Password for HTTP authentication. |
| [`http_user`](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) | No |  | Username for HTTP authentication. |
| [`include_tag_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) | No | `false` | If true, a tag is appended to the output. |
| [`json_date_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) | No | `iso8601` | Optional. |
| [`json_date_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) | No | `timestamp` | Optional. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) | No |  |  |
| [`tls`](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) | No | `on` | Enable end-to-end security using TLS. |
| [`uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) | No | `/api/default/default/_json` | The API path used to send logs. |

<a id="outputs-opensearch"></a>
### `opensearch`: OpenSearch
Fluent Bit page: [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | Yes | `opensearch` | Plugin identifier. |
| [`buffer_size`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | Yes | `512k` | Specify the buffer size used to read the response from the OpenSearch HTTP service. |
| [`aws_auth`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | Enable AWS Sigv4 Authentication for Amazon OpenSearch Service. |
| [`aws_external_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No |  | External ID for the AWS IAM Role specified with aws_role_arn. |
| [`aws_profile`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `default` | AWS profile name. |
| [`aws_region`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No |  | Specify the AWS region for Amazon OpenSearch Service. |
| [`aws_role_arn`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No |  | AWS IAM Role to assume to put records to your Amazon cluster. |
| [`aws_service_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `es` | Service name to be used in AWS Sigv4 signature. |
| [`aws_sts_endpoint`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No |  | Specify the custom STS endpoint to be used with STS API for Amazon OpenSearch Service. |
| [`compress`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No |  | Set payload compression mechanism. |
| [`current_time_index`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | Use current time for index generation instead of message record. |
| [`generate_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | When enabled, generate _id for outgoing records. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target OpenSearch instance. |
| [`http_passwd`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No |  | Password for user defined in http_user. |
| [`http_user`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No |  | Optional username credential for HTTP basic authentication. |
| [`id_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No |  | If set, _id will be the value of the key from incoming record and generate_id option is ignored. |
| [`include_tag_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | When enabled, append the Tag name to the record. |
| [`index`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `fluent-bit` | Index name, supports [Record Accessor syntax](/manual/administration/configuring-fluent-bit/classic-mode/record-accessor.md) from 2.0.5 or later. |
| [`logstash_dateformat`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `%Y.%m.%d` | Time format, based on [strftime](https://man7.org/linux/man-pages/man3/strftime.3.html), to generate the second part of the index name. |
| [`logstash_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | Enable Logstash format compatibility. |
| [`logstash_prefix`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `logstash` | When logstash_format is enabled, the index name is composed using a prefix and the date. |
| [`logstash_prefix_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No |  | When included, the value of the key in the record will be evaluated as key reference and overrides logstash_prefix for index generation. |
| [`logstash_prefix_separator`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `-` | Set a separator between logstash_prefix and the date. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`path`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No |  | OpenSearch accepts new data on HTTP query path /_bulk. |
| [`pipeline`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No |  | OpenSearch lets you set up filters called pipelines. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `9200` | TCP port of the target OpenSearch instance. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No |  |  |
| [`replace_dots`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | When enabled, replace field name dots (.) with underscores (_). |
| [`suppress_type_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | When enabled, mapping types is removed and the type option is ignored. |
| [`tag_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `flb-key` | When include_tag_key is enabled, this property defines the key name for the tag. |
| [`time_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `@timestamp` | When logstash_format is enabled, each record will get a new timestamp field. |
| [`time_key_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `%Y-%m-%dT%H:%M:%S` | When logstash_format is enabled, this property defines the format of the timestamp. |
| [`time_key_nanos`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | When logstash_format is enabled, enabling this property sends nanosecond precision timestamps. |
| [`trace_error`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | When enabled, print the OpenSearch API calls to stdout when OpenSearch returns an error (for diagnostics only). |
| [`trace_output`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `Off` | When enabled, print the OpenSearch API calls to stdout (for diagnostics only). |
| [`type`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `_doc` | Type name. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |
| [`write_operation`](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) | No | `create` | Operation to use to write in bulk requests. |

<a id="outputs-opentelemetry"></a>
### `opentelemetry`: OpenTelemetry
Fluent Bit page: [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/router)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/router) | Yes | `opentelemetry` | Plugin identifier. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/router) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/router) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/router) | No |  |  |

<a id="outputs-oracle-log-analytics"></a>
### `oracle_log_analytics`: Oracle Cloud Infrastructure Logging Analytics
Fluent Bit page: [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | Yes | `oracle_log_analytics` | Plugin identifier. |
| [`oci_la_log_group_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | Yes |  | Required. |
| [`oci_la_log_source_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | Yes |  | Required. |
| [`config_file_location`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | The location of the [configuration file](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm#SDK_and_CLI_Configuration_File) that contains OCI authentication details. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`namespace`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | The OCI tenancy namespace to upload log data to. |
| [`oci_config_in_record`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No | `false` | If set to true, the following oci_la_ parameters will be read from the record itself instead of the output plugin configuration. |
| [`oci_la_entity_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | The OCID of the Log Analytics entity. |
| [`oci_la_entity_type`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | The entity type of the Log Analytics entity. |
| [`oci_la_global_metadata`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | Specifies additional global metadata along with original log content to Log Analytics. |
| [`oci_la_log_path`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | Specifies the original location of the log files. |
| [`oci_la_log_set_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | The OCID of the Log Analytics log set. |
| [`oci_la_metadata`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | Specifies additional metadata for a log event along with original log content to Log Analytics. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  |  |
| [`profile_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No | `DEFAULT` | The OCI configuration profile name to be used from the configuration file. |
| [`proxy`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | The proxy name, in http://host:port format. |
| [`uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No |  | The URI for the OCI Log Analytics REST API request. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) | No | `1` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-parseable"></a>
### `parseable`: Parseable
Fluent Bit page: [Parseable](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) | Yes | `parseable` | Plugin identifier. |
| [`header`](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) | Yes |  | Required headers for Parseable integration. |
| [`add_label`](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) | No |  | Add custom labels to the telemetry data. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) | No | `parseable` | Your Parseable Ingestor hostname or IP address. |
| [`http_passwd`](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) | No | `admin` | Password for HTTP basic authentication. |
| [`http_user`](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) | No | `admin` | Username for HTTP basic authentication. |
| [`log_response_payload`](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) | No | `false` | Log the response payload from the server for debugging. |
| [`logs_uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) | No | `/v1/logs` | Specify the HTTP URI for the target web server listening for logs. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`metrics_uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) | No | `/v1/metrics` | Specify the HTTP URI for the target web server listening for metrics. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) | No | `8000` | TCP port of your Parseable Ingestor. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) | No |  |  |
| [`tls`](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) | No | `off` | Enable or disable TLS/SSL encryption. |
| [`traces_uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) | No | `/v1/traces` | Specify the HTTP URI for the target web server listening for traces. |

<a id="outputs-pgsql"></a>
### `pgsql`: PostgreSQL
Fluent Bit page: [PostgreSQL](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) | Yes | `pgsql` | Plugin identifier. |
| [`cockroachdb`](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) | No | `false` | Set to true if you will connect the plugin with a CockroachDB. |
| [`connection_options`](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) | No | `_none_` | Specifies any valid [PostgreSQL connection options](https://www.postgresql.org/docs/devel/libpq-connect.html#LIBPQ-CONNECT-OPTIONS). |
| [`database`](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) | No | `fluentbit` | Database name to connect to. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) | No | `127.0.0.1` | Hostname/IP address of the PostgreSQL instance. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`password`](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) | No | `_none_` | Password of PostgreSQL username. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) | No | `5432` | PostgreSQL port. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) | No |  |  |
| [`table`](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) | No | `fluentbit` | Table name where to store data. |
| [`user`](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) | No | `_none_` | PostgreSQL username. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) | No | `1` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-plot"></a>
### `plot`: Plot
Fluent Bit page: [Plot](https://docs.fluentbit.io/manual/data-pipeline/outputs/plot#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/plot#configuration-parameters) | Yes | `plot` | Plugin identifier. |
| [`key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/plot#configuration-parameters) | Yes |  | Specify the key name from the record to extract as the value. |
| [`file`](https://docs.fluentbit.io/manual/data-pipeline/outputs/plot#configuration-parameters) | No |  | Set filename to store the records. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/plot#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/plot#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/plot#configuration-parameters) | No |  |  |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/plot#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-prometheus-exporter"></a>
### `prometheus_exporter`: Prometheus exporter
Fluent Bit page: [Prometheus exporter](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter#configuration-parameters) | Yes | `prometheus_exporter` | Plugin identifier. |
| [`add_label`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter#configuration-parameters) | No |  | This lets you add custom labels to all metrics exposed through the Prometheus exporter. |
| [`add_timestamp`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter#configuration-parameters) | No | `false` | Add timestamp to every metric honoring collection time. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter#configuration-parameters) | No | `0.0.0.0` | IP address or hostname Fluent Bit will bind to when hosting Prometheus metrics. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter#configuration-parameters) | No | `2021` | TCP port Fluent Bit will bind to when hosting Prometheus metrics. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter#configuration-parameters) | No |  |  |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-prometheus-remote-write"></a>
### `prometheus_remote_write`: Prometheus remote write
Fluent Bit page: [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | Yes | `prometheus_remote_write` | Plugin identifier. |
| [`add_label`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No |  | This lets you add custom labels to all metrics sent by the prometheus_remote_write output. |
| [`aws_auth`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No | `false` | Enable AWS SigV4 authentication. |
| [`aws_external_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No |  | External ID for the AWS IAM Role specified with aws_role_arn, used by SigV4 authentication. |
| [`aws_profile`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No |  | AWS profile name. |
| [`aws_region`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No |  | Region of your Amazon Managed Service for Prometheus workspace. |
| [`aws_role_arn`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No |  | AWS IAM Role to assume, used by SigV4 authentication. |
| [`aws_service`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No | `aps` | AWS destination service code, used by SigV4 authentication. |
| [`aws_sts_endpoint`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No |  | Specify the custom STS endpoint to be used with STS API, used with the aws_role_arn option, used by SigV4 authentication. |
| [`compression`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No | `snappy` | Payload compression algorithm. |
| [`header`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No |  | Add a HTTP header key/value pair. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target HTTP server. |
| [`http_passwd`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No |  | Basic Auth password. |
| [`http_user`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No |  | Basic Auth username. |
| [`log_response_payload`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No | `true` | Log the response payload within the Fluent Bit log. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No | `80` | TCP port of the target HTTP server. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No |  |  |
| [`proxy`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No |  | Specify an HTTP proxy. |
| [`uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No |  | Specify an optional HTTP URI for the target web server, for example /someuri. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) | No | `2` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-s3"></a>
### `s3`: Amazon S3
Fluent Bit page: [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | Yes | `s3` | Plugin identifier. |
| [`region`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | Yes | `us-east-1` | The AWS region of your S3 bucket. |
| [`s3_key_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | Yes | `/fluent-bit-logs/$TAG/%Y/%m/%d/%H/%M/%S` | Format string for keys in S3. |
| [`send_content_md5`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | Yes | `false` | Send the Content-MD5 header with PutObject and UploadPart requests, as is required when Object Lock is enabled. |
| [`alias`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Sets an alias, use for multiple instances of the same output plugin. |
| [`authorization_endpoint_bearer_token`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Authorization endpoint bearer token. |
| [`authorization_endpoint_password`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Authorization endpoint basic authentication password. |
| [`authorization_endpoint_url`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Authorization endpoint URL. |
| [`authorization_endpoint_username`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Authorization endpoint basic authentication username. |
| [`auto_retry_requests`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `true` | Immediately retry failed requests to AWS services once. |
| [`blob_database_file`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Absolute path to a database file to be used to store blob files contexts. |
| [`bucket`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | S3 bucket name. |
| [`canned_acl`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | [Predefined Canned ACL policy](https://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#canned-acl) for S3 objects. |
| [`compression`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Compression type for S3 objects. |
| [`content_type`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | A standard MIME type for the S3 object, set as the Content-Type HTTP header. |
| [`endpoint`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Custom endpoint for the S3 API. |
| [`external_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Specify an external ID for the STS API. |
| [`file_delivery_attempt_limit`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `1` | File delivery attempt limit. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target HTTP server. |
| [`json_date_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Specify the format of the date. |
| [`json_date_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `date` | Specify the name of the date key in the output record. |
| [`log_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | By default, the whole log record is sent to S3. |
| [`log_level`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `info` | Specifies the log level for output plugin. |
| [`log_suppress_interval`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `0` | Suppresses log messages from output plugin that appear similar within a specified time interval. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Set a tag pattern to match records that output should process. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Set a regular expression to match tags for output routing. |
| [`net.connect_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `10s` | Set maximum time allowed to establish a connection, this time includes the TLS handshake. |
| [`net.connect_timeout_log_error`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `true` | On connection timeout, specify if it should log an error. |
| [`net.dns.mode`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Select the primary DNS connection type (TCP or UDP). |
| [`net.dns.prefer_ipv4`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Select the primary DNS resolver type (LEGACY or ASYNC). |
| [`net.dns.prefer_ipv6`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Prioritize IPv6 DNS results when trying to establish a connection. |
| [`net.io_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `0s` | Set maximum time a connection can stay idle while assigned. |
| [`net.keepalive_max_recycle`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `2000` | Set maximum number of times a keepalive connection can be used before it retries. |
| [`net.max_worker_connections`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `0` | Set the maximum number of active TCP connections that can be used per worker thread. |
| [`net.proxy_env_ignore`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `false` | Ignore the environment variables HTTP_PROXY, HTTPS_PROXY and NO_PROXY when set. |
| [`net.source_address`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Specify network address to bind for data traffic. |
| [`net.tcp_keepalive`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `off` | Enable or disable Keepalive support. |
| [`net.tcp_keepalive_interval`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `-1` | Interval between TCP keepalive probes when no response is received on a keepidle probe. |
| [`net.tcp_keepalive_probes`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `-1` | Number of unacknowledged probes to consider a connection dead. |
| [`net.tcp_keepalive_time`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `-1` | Interval between the last data packet sent and the first TCP keepalive probe. |
| [`part_delivery_attempt_limit`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `1` | File part delivery attempt limit. |
| [`part_size`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `25M` | Size of each part when uploading blob files. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `80` | TCP port of the target HTTP server. |
| [`preserve_data_ordering`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `true` | When an upload request fails, the last received chunk might swap with a later chunk, resulting in data shuffling. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  |  |
| [`profile`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Option to specify an AWS Profile for credentials. |
| [`retry_limit`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `5` | Set the maximum number of retries for the S3 plugin's internal retry system. |
| [`role_arn`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | ARN of an IAM role to assume (for example, for cross account access). |
| [`s3_key_format_tag_delimiters`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `.` | A series of characters which will be used to split the tag into parts for use with the s3_key_format option. |
| [`static_file_path`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `false` | Disables behavior where UUID string appends to the end of the S3 key name when $UUID isn't provided in s3_key_format. |
| [`storage_class`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Specify the [storage class](https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html#AmazonS3-PutObject-request-header-StorageClass) for S3 objects. |
| [`store_dir`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `/tmp/fluent-bit/s3` | Directory to locally buffer data before sending. |
| [`store_dir_limit_size`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `0` | S3 plugin has its own buffering system with files in the store_dir. |
| [`sts_endpoint`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Custom endpoint for the STS API. |
| [`tls`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `off` | Enable or disable TLS/SSL support. |
| [`tls.ca_file`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Absolute path to CA certificate file. |
| [`tls.ca_path`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Absolute path to scan for certificate files. |
| [`tls.ciphers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Specify TLS ciphers up to TLSv1.2. |
| [`tls.crt_file`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Absolute path to Certificate file. |
| [`tls.debug`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `1` | Set TLS debug level. |
| [`tls.key_file`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Absolute path to private Key file. |
| [`tls.key_passwd`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Optional password for tls.key_file file. |
| [`tls.max_version`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Specify the maximum version of TLS. |
| [`tls.min_version`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Specify the minimum version of TLS. |
| [`tls.verify`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `on` | Force certificate validation. |
| [`tls.verify_hostname`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `off` | Enable or disable to verify hostname. |
| [`tls.vhost`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Hostname to be used for TLS SNI extension. |
| [`tls.windows.certstore_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Sets the certstore name on an output (Windows). |
| [`tls.windows.use_enterprise_store`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No |  | Sets whether using enterprise certstore or not on an output (Windows). |
| [`total_file_size`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `100000000` | Specify file size in S3. |
| [`upload_chunk_size`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `5242880` | The size of each part for multipart uploads. |
| [`upload_part_freshness_limit`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `6D` | Maximum lifespan of an uncommitted file part. |
| [`upload_parts_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `10m` | Timeout to upload parts of a blob file. |
| [`upload_timeout`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `10m` | When this amount of time elapses, Fluent Bit uploads and creates a new file in S3. |
| [`use_put_object`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `false` | Use the S3 PutObject API instead of the multipart upload API. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) | No | `1` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-skywalking"></a>
### `skywalking`: Apache SkyWalking
Fluent Bit page: [Apache SkyWalking](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) | Yes | `skywalking` | Plugin identifier. |
| [`auth_token`](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) | No |  | Authentication token if needed for Apache SkyWalking OAP. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) | No | `127.0.0.1` | Hostname of Apache SkyWalking OAP. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) | No | `12800` | TCP port of the Apache SkyWalking OAP. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) | No |  |  |
| [`svc_inst_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) | No | `fluent-bit` | Service instance name of Fluent Bit. |
| [`svc_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) | No | `sw-service` | Service name that Fluent Bit belongs to. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-slack"></a>
### `slack`: Slack
Fluent Bit page: [Slack](https://docs.fluentbit.io/manual/data-pipeline/outputs/slack#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/slack#configuration-parameters) | Yes | `slack` | Plugin identifier. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/slack#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/slack#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/slack#configuration-parameters) | No |  |  |
| [`webhook`](https://docs.fluentbit.io/manual/data-pipeline/outputs/slack#configuration-parameters) | No |  | Absolute address of the webhook provided by Slack. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/slack#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-splunk"></a>
### `splunk`: Splunk
Fluent Bit page: [Splunk](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) | Yes | `splunk` | Plugin identifier. |
| [`channel`](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) | No |  | Specify X-Splunk-Request-Channel header for the HTTP Event Collector interface. |
| [`compress`](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) | No |  | Set payload compression mechanism. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target Splunk service. |
| [`http_buffer_size`](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) | No |  | Buffer size used to receive Splunk HTTP responses. |
| [`http_debug_bad_request`](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) | No | `false` | If the HTTP server response code is 400 (bad request) and this flag is enabled, it will print the full HTTP request and response to the stdout interface. |
| [`http_passwd`](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) | No |  | Password for user defined in http_user. |
| [`http_user`](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) | No |  | Optional username for basic authentication on HEC. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) | No | `8088` | TCP port of the target Splunk service. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) | No |  |  |
| [`splunk_token`](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) | No |  | Specify the authentication token for the HTTP Event Collector interface. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) | No | `2` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-stackdriver"></a>
### `stackdriver`: Stackdriver
Fluent Bit page: [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | Yes | `stackdriver` | Plugin identifier. |
| [`job`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | Yes |  | An identifier for a grouping of related tasks, such as the name of a microservice or distributed batch. |
| [`k8s_cluster_location`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | Yes |  | The physical location of the cluster that contains (node or pod based on the resource type) the container. |
| [`k8s_cluster_name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | Yes |  | The name of the cluster that the container (node or pod based on the resource type) is running in. |
| [`location`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | Yes |  | The GCP or AWS region in which to store data about the resource. |
| [`namespace`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | Yes |  | A namespace identifier, such as a cluster name or environment. |
| [`node_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | Yes |  | A unique identifier for the node within the namespace, such as a hostname or IP address. |
| [`tag_prefix`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | Yes | `k8s_container.`, `k8s_pod.`, `k8s_node.` | Set the tag_prefix used to validate the tag of logs with Kubernetes resource type. |
| [`task_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | Yes |  | A unique identifier for the task within the namespace and job, such as a replica index identifying the task within the job. |
| [`autoformat_stackdriver_trace`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `false` | Rewrite the trace field to include the projectID and format it for use with Cloud Trace. |
| [`cloud_logging_base_url`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `https://logging.googleapis.com` | Set the base Cloud Logging API URL to use for the /v2/entries:write API request. |
| [`compress`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No |  | Set payload compression mechanism. |
| [`custom_k8s_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `(?<pod_name>[a-z0-9](?:[-a-z0-9]*[a-z0-9])?(?:\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*)_(?<namespace_name>[^_]+)_(?<container_name>.+)-(?<docker_id>[a-z0-9]{64})\.log$` | Set a custom regular expression to extract fields like pod_name, namespace_name, container_name, and docker_id from the local_resource_id in logs. |
| [`export_to_project_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `The `project_id` in the `google_service_credentials` file, or the `project_id` from Google's `metadata.google.internal` server.` | The GCP project that should receive these logs. |
| [`google_service_credentials`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `Value of environment variable `$GOOGLE_APPLICATION_CREDENTIALS` | Absolute path to a Google Cloud credentials JSON file. |
| [`http_request_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `logging.googleapis.com/http_request` | The name of the key from the original record that contains the LogEntry's httpRequest. |
| [`labels`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No |  | Optional list of comma-separated strings specifying key=value pairs. |
| [`labels_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `logging.googleapis.com/labels` | The name of the key from the original record that contains the LogEntry's labels. |
| [`log_name_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `logging.googleapis.com/logName` | The name of the key from the original record that contains the logName value. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`metadata_server`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `Value of environment variable `$METADATA_SERVER`, or `http://metadata.google.internal` if unset.` | Prefix for a metadata server. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No |  |  |
| [`project_id_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `logging.googleapis.com/projectId`. See [Stackdriver Special Fields](/manual/data-pipeline/outputs/stackdriver_special_fields.md#log-entry-fields) for more info.` | The value of this field is used by the Stackdriver output plugin to find the GCP projectID from jsonPayload and then extract the value of it to set the PROJECT_ID within LogEntry logName, which controls the GCP project that should receive these logs. |
| [`resource`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `global` | Set resource type of data. |
| [`resource_labels`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No |  | An optional list of comma-separated strings specifying resource label plain text assignments (new=value) and mappings from an original field in the log entry to a destination field (destination=$original). |
| [`service_account_email`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `Value of environment variable `$SERVICE_ACCOUNT_EMAIL` | Account email associated with the service. |
| [`service_account_secret`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `Value of environment variable `$SERVICE_ACCOUNT_SECRET` | Private key content associated with the service account. |
| [`severity_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `logging.googleapis.com/severity` | The name of the key from the original record that contains the severity. |
| [`span_id_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `logging.googleapis.com/spanId` | The name of the key from the original record that contains the span ID. |
| [`stackdriver_agent`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No |  | Set a custom User-Agent header value for requests sent to Cloud Logging. |
| [`test_log_entry_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `false` | Test-only option that prints the generated Cloud Logging payload without sending it. |
| [`text_payload_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No |  | Set the key from the record to use as the textPayload field in the log entry. |
| [`trace_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `logging.googleapis.com/trace` | The name of the key from the original record that contains the trace value. |
| [`trace_sampled_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `logging.googleapis.com/traceSampled` | The name of the key from the original record that contains the trace sampled flag. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) | No | `1` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-stackdriver-special-fields"></a>
### `stackdriver_special_fields`: Stackdriver special fields
Fluent Bit page: [Stackdriver special fields](https://docs.fluentbit.io/manual/data-pipeline/router)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/router) | Yes | `stackdriver_special_fields` | Plugin identifier. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/router) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/router) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/router) | No |  |  |

<a id="outputs-stdout"></a>
### `stdout`: Standard output
Fluent Bit page: [Standard output](https://docs.fluentbit.io/manual/data-pipeline/outputs/standard-output#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/standard-output#configuration-parameters) | Yes | `stdout` | Plugin identifier. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/standard-output#configuration-parameters) | No | `msgpack` | Specify the data format to be printed. |
| [`json_date_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/standard-output#configuration-parameters) | No | `double` | Specify the format of the date. |
| [`json_date_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/standard-output#configuration-parameters) | No | `date` | Specify the name of the time key in the output record. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/standard-output#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/standard-output#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/standard-output#configuration-parameters) | No |  |  |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/standard-output#configuration-parameters) | No | `1` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-syslog"></a>
### `syslog`: Syslog
Fluent Bit page: [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | Yes | `syslog` | Plugin identifier. |
| [`syslog_maxsize`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | Yes | `0` | The maximum size allowed per message. |
| [`syslog_message_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | Yes |  | Required. |
| [`allow_longer_sd_id`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No | `false` | If true, Fluent Bit allows SD-ID values longer than 32 characters. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No | `127.0.0.1` | Domain or IP address of the remote Syslog server. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`mode`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No | `udp` | Desired transport type. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No | `514` | TCP or UDP port of the remote Syslog server. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No |  |  |
| [`syslog_appname_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No |  | Optional. |
| [`syslog_appname_preset`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No |  | Optional. |
| [`syslog_facility_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No |  | Optional. |
| [`syslog_facility_preset`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No | `1` | Optional. |
| [`syslog_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No | `rfc5424` | The Syslog protocol format to use. |
| [`syslog_hostname_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No |  | Optional. |
| [`syslog_hostname_preset`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No |  | Optional. |
| [`syslog_msgid_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No |  | Optional. |
| [`syslog_msgid_preset`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No |  | Optional. |
| [`syslog_procid_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No |  | Optional. |
| [`syslog_procid_preset`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No |  | Optional. |
| [`syslog_sd_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No |  | Optional. |
| [`syslog_severity_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No |  | Optional. |
| [`syslog_severity_preset`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No | `6` | Optional. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-tcp"></a>
### `tcp`: TCP and TLS
Fluent Bit page: [TCP and TLS](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) | Yes | `tcp` | Plugin identifier. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) | No | `msgpack` | Specify the data format to be printed. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) | No | `127.0.0.1` | Target host where Fluent Bit or Fluentd are listening for Forward messages. |
| [`json_date_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) | No | `double` | Specify the format of the date. |
| [`json_date_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) | No | `date` | Specify the name of the time key in the output record. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) | No | `5170` | TCP port of the target service. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) | No |  |  |
| [`raw_message_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) | No |  | If set, the value of this key is sent as the raw message payload without additional formatting. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) | No | `2` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-td"></a>
### `td`: Treasure Data
Fluent Bit page: [Treasure Data](https://docs.fluentbit.io/manual/data-pipeline/outputs/treasure-data#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/treasure-data#configuration-parameters) | Yes | `td` | Plugin identifier. |
| [`api`](https://docs.fluentbit.io/manual/data-pipeline/outputs/treasure-data#configuration-parameters) | No |  | The Treasure Data API key. |
| [`database`](https://docs.fluentbit.io/manual/data-pipeline/outputs/treasure-data#configuration-parameters) | No |  | Specify the name of your target database. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/treasure-data#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/treasure-data#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/treasure-data#configuration-parameters) | No |  |  |
| [`region`](https://docs.fluentbit.io/manual/data-pipeline/outputs/treasure-data#configuration-parameters) | No | `US` | Set the service region. |
| [`table`](https://docs.fluentbit.io/manual/data-pipeline/outputs/treasure-data#configuration-parameters) | No |  | Specify the name of your target table where the records will be stored. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/treasure-data#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-udp"></a>
### `udp`: UDP
Fluent Bit page: [UDP](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) | Yes | `udp` | Plugin identifier. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) | No | `json_lines` | Specify the data format to be printed. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) | No | `127.0.0.1` | Target host where the UDP server is listening. |
| [`json_date_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) | No | `double` | Specify the format of the date. |
| [`json_date_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) | No | `date` | Specify the name of the time key in the output record. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) | No | `5170` | UDP port of the target service. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) | No |  |  |
| [`raw_message_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) | No |  | Use a raw message key for the message. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) | No | `2` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-vivo-exporter"></a>
### `vivo_exporter`: Vivo Exporter
Fluent Bit page: [Vivo Exporter](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) | Yes | `vivo_exporter` | Plugin identifier. |
| [`empty_stream_on_read`](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) | No | `off` | If enabled, when an HTTP client consumes the data from a stream, the stream content will be removed. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) | No | `0.0.0.0` | The network address for the HTTP server to listen on. |
| [`http_cors_allow_origin`](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) | No |  | Specify the value for the HTTP Access-Control-Allow-Origin header (CORS). |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) | No | `2025` | The TCP port for the HTTP server to listen on. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) | No |  |  |
| [`stream_queue_size`](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) | No | `20M` | Specify the maximum queue size per stream. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) | No | `1` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |

<a id="outputs-websocket"></a>
### `websocket`: WebSocket
Fluent Bit page: [WebSocket](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters)

| Attribute | Mandatory | Default | Description |
| --- | --- | --- | --- |
| [`name`](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) | Yes | `websocket` | Plugin identifier. |
| [`format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) | No |  | Specify the data format to be used in the HTTP request body. |
| [`header`](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) | No |  | Add a HTTP header key/value pair. |
| [`host`](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) | No | `127.0.0.1` | IP address or hostname of the target WebSocket Server. |
| [`json_date_format`](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) | No | `double` | Specify the format of the date. |
| [`json_date_key`](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) | No | `date` | Specify the name of the date field in output. |
| [`match`](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) | No |  | Tag match pattern used to route records to this plugin. Supports '*' wildcard matching. |
| [`match_regex`](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) | No |  | Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set. |
| [`port`](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) | No | `80` | TCP port of the target WebSocket Server. |
| [`processors`](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) | No |  |  |
| [`uri`](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) | No |  | Specify an optional HTTP URI for the target WebSocket server. |
| [`workers`](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) | No | `0` | The number of [workers](/manual/administration/multithreading.md#outputs) to perform flush operations for this output. |
