# Fluent Bit 3.2.10 Plugin Attribute Reference

Generated from the local catalog JSON only.
- `config-service\src\config_service\json-definitions\fluent-bit-3.2.10-all-plugins-catalog.json`

Scope: this reference includes the field-based `inputs`, `filters`, and `outputs` plugin groups from the catalog JSON. The `custom_plugins` block is not tabulated because it does not provide per-attribute documentation links in the same structure.

## Inputs

| Plugin Name | Attribute Name | Fluent Bit Page |
| --- | --- | --- |
| `collectd` | `listen` | [Collectd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/collectd#configuration-parameters-a-hrefconfig-idconfiga) |
| `collectd` | `port` | [Collectd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/collectd#configuration-parameters-a-hrefconfig-idconfiga) |
| `collectd` | `typesdb` | [Collectd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/collectd#configuration-parameters-a-hrefconfig-idconfiga) |
| `collectd` | `threaded` | [Collectd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/collectd#configuration-parameters-a-hrefconfig-idconfiga) |
| `collectd` | `tag` | [Collectd](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `cpu` | `interval_sec` | [CPU Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/cpu-metrics#configuration-parameters) |
| `cpu` | `interval_nsec` | [CPU Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/cpu-metrics#configuration-parameters) |
| `cpu` | `pid` | [CPU Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/cpu-metrics#configuration-parameters) |
| `cpu` | `tag` | [CPU Log Based Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `disk` | `interval_sec` | [Disk I/O Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/disk-io-metrics#configuration-parameters) |
| `disk` | `interval_nsec` | [Disk I/O Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/disk-io-metrics#configuration-parameters) |
| `disk` | `dev_name` | [Disk I/O Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/disk-io-metrics#configuration-parameters) |
| `disk` | `threaded` | [Disk I/O Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/disk-io-metrics#configuration-parameters) |
| `disk` | `tag` | [Disk I/O Log Based Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `docker-metrics` | `interval_sec` | [Docker Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-metrics#configuration-parameters) |
| `docker-metrics` | `include` | [Docker Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-metrics#configuration-parameters) |
| `docker-metrics` | `exclude` | [Docker Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-metrics#configuration-parameters) |
| `docker-metrics` | `threaded` | [Docker Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-metrics#configuration-parameters) |
| `docker-metrics` | `path.containers` | [Docker Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-metrics#configuration-parameters) |
| `docker-metrics` | `tag` | [Docker Log Based Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `docker_events` | `unix_path` | [Docker Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) |
| `docker_events` | `buffer_size` | [Docker Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) |
| `docker_events` | `parser` | [Docker Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) |
| `docker_events` | `key` | [Docker Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) |
| `docker_events` | `reconnect.retry_limits` | [Docker Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) |
| `docker_events` | `reconnect.retry_interval` | [Docker Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) |
| `docker_events` | `threaded` | [Docker Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/docker-events#configuration-parameters) |
| `docker_events` | `tag` | [Docker Events](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `dummy` | `dummy` | [Dummy](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `metadata` | [Dummy](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `start_time_sec` | [Dummy](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `start_time_nsec` | [Dummy](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `rate` | [Dummy](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `interval_sec` | [Dummy](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `interval_nsec` | [Dummy](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `samples` | [Dummy](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `copies` | [Dummy](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `flush_on_startup` | [Dummy](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `threaded` | [Dummy](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `tag` | [Dummy](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `ebpf` | `tag` | [eBPF](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `ebpf` | `trace` | [eBPF](https://docs.fluentbit.io/manual/3.2/data-pipeline/inputs/ebpf#configuration-parameters) |
| `elasticsearch` | `buffer_max_size` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `buffer_chunk_size` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `tag_key` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `meta_key` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `hostname` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `version` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `threaded` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `tag` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `exec` | `command` | [Exec](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) |
| `exec` | `parser` | [Exec](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) |
| `exec` | `interval_sec` | [Exec](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) |
| `exec` | `interval_nsec` | [Exec](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) |
| `exec` | `buf_size` | [Exec](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) |
| `exec` | `oneshot` | [Exec](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) |
| `exec` | `exit_after_oneshot` | [Exec](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) |
| `exec` | `propagate_exit_code` | [Exec](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) |
| `exec` | `threaded` | [Exec](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec#configuration-parameters) |
| `exec` | `tag` | [Exec](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `exec_wasi` | `wasi_path` | [Exec WASI](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `parser` | [Exec WASI](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `accessible_paths` | [Exec WASI](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `interval_sec` | [Exec WASI](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `interval_nsec` | [Exec WASI](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `wasm_heap_size` | [Exec WASI](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `wasm_stack_size` | [Exec WASI](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `buf_size` | [Exec WASI](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `oneshot` | [Exec WASI](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `threaded` | [Exec WASI](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `tag` | [Exec WASI](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `fluentbit_metrics` | `scrape_interval` | [Fluent Bit Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/fluentbit-metrics#configuration) |
| `fluentbit_metrics` | `scrape_on_start` | [Fluent Bit Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/fluentbit-metrics#configuration) |
| `fluentbit_metrics` | `threaded` | [Fluent Bit Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/fluentbit-metrics#configuration) |
| `fluentbit_metrics` | `tag` | [Fluent Bit Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `forward` | `listen` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) |
| `forward` | `port` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) |
| `forward` | `unix_path` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) |
| `forward` | `unix_perm` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) |
| `forward` | `buffer_max_size` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) |
| `forward` | `buffer_chunk_size` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) |
| `forward` | `tag_prefix` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) |
| `forward` | `tag` | [Forward](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `forward` | `shared_key` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) |
| `forward` | `empty_shared_key` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) |
| `forward` | `self_hostname` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) |
| `forward` | `security.users` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) |
| `forward` | `threaded` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/forward#configuration-parameters) |
| `head` | `file` | [Head](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) |
| `head` | `buf_size` | [Head](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) |
| `head` | `interval_sec` | [Head](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) |
| `head` | `interval_nsec` | [Head](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) |
| `head` | `add_path` | [Head](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) |
| `head` | `key` | [Head](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) |
| `head` | `lines` | [Head](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) |
| `head` | `split_line` | [Head](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) |
| `head` | `threaded` | [Head](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/head#configuration-parameters) |
| `head` | `tag` | [Head](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `health` | `host` | [Health](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) |
| `health` | `port` | [Health](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) |
| `health` | `interval_sec` | [Health](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) |
| `health` | `internal_nsec` | [Health](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) |
| `health` | `alert` | [Health](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) |
| `health` | `add_host` | [Health](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) |
| `health` | `add_port` | [Health](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) |
| `health` | `threaded` | [Health](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/health#configuration-parameters) |
| `health` | `tag` | [Health](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `http` | `listen` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) |
| `http` | `port` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) |
| `http` | `tag_key` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) |
| `http` | `buffer_max_size` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) |
| `http` | `buffer_chunk_size` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) |
| `http` | `successful_response_code` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) |
| `http` | `success_header` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) |
| `http` | `threaded` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/http#configuration-parameters) |
| `http` | `tag` | [HTTP](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `kafka` | `brokers` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `topics` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `format` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `client_id` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `group_id` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `poll_ms` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `buffer_max_size` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `threaded` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `tag` | [Kafka](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `kafka` | `rdkafka.builtin.features` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.client.id` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.metadata.broker.list` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.bootstrap.servers` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.message.max.bytes` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.message.copy.max.bytes` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.receive.message.max.bytes` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.max.in.flight.requests.per.connection` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.max.in.flight` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.metadata.recovery.strategy` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.metadata.recovery.rebootstrap.trigger.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.topic.metadata.refresh.interval.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.metadata.max.age.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.topic.metadata.refresh.fast.interval.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.topic.metadata.refresh.fast.cnt` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.topic.metadata.refresh.sparse` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.topic.metadata.propagation.max.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.topic.blacklist` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.debug` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.socket.timeout.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.socket.blocking.max.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.socket.send.buffer.bytes - importance low` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.socket.receive.buffer.bytes - importance low` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.socket.keepalive.enable` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.socket.nagle.disable` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.socket.max.fails` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.broker.address.ttl` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.broker.address.family` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.socket.connection.setup.timeout.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.connection.max.idle.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.reconnect.backoff.jitter.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.reconnect.backoff.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.reconnect.backoff.max.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.static.interval.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.enable.events` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.error_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.throttle_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.stats_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.log_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.log_level` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.log.queue` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.log.thread.name` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.enable.random.seed` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.log.connection.close` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.background_event_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.socket_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.connect_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.closesocket_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.open_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.resolve_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.opaque` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.default_topic_conf` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.internal.termination.signal` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.api.version.request` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.api.version.request.timeout.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.api.version.fallback.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.broker.version.fallback` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.allow.auto.create.topics` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.security.protocol` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.cipher.suites` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.curves.list` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.sigalgs.list` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.key.location` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.key.password` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.key.pem` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl_key` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.certificate.loction` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.certificate.pem` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl_certificate` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.ca.location` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.https.ca.location` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.https.ca.pem` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl_ca` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.ca.pem` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.ca.certificate.stores` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.crl.location` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.keystore.location` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.keystore.password` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.providers` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.engine.location` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.engine.id` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl_engine_callback_data` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.enable.ssl.certification.verification` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.endpoint.identification.algorithm` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.ssl.certificate.verify_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.mechanisms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.mechanism` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.kerberos.service.name` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.kerberos.principal` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.kinit.cmd` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.keytab` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.kerberos.min.time.before.relogin` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.username` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.password` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oaurthbearer.config` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.enable.sasl.oauthbearer.unsecure.jwt` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.oauthbearer_token_refresh_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.method` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.client.id` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.client.credentials.id` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.client.credentials.client.secret` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.scope` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.extensions` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.endpoint.url` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.sub.claim.name` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.grant.type` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.assertion.algorithm` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.assertion.private.key.file` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.assertion.private.key.passphrase` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.ssertion.private.key.pem` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.assertion.file` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.assertion.claim.aud` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.assertion.claim.exp.seconds` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.assertion.claim.iss` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.assertion.claimjti.include` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.assertion.claim.nbf.seconds` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.scope` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sasl.oauthbearer.metadata.authentication.type` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.plugin.library.paths` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.interceptors` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.group.id` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.Type` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.group.instance.id` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.partition.assignment.strategy` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.session.timeout.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.heartbeat.interval.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.group.protocol.type` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.group.protocol` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.group.remote.assignor` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.coordinator.query.interval.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.max.poll.interval.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.enable.auto.commit` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.auto.commit.interval.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.enable.auto.offset.store` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.queued.min.messages` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.queued.max.messages.kbytes` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.fetch.wait.max.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.fetch.queue.backoff.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.fetch.message.max.bytes` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.max.partition.fetch.bytes` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.fetch.max.bytes` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.fetch.min.bytes` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.fetch.error.backoff.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.offset.store.method` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.isolation.level` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.consume_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.rebalance_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.offset_commit_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.enable.partition.eof` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.check.crcs` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.client.rack` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.transactional.id` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.transaction.timeout.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.enable.idempotence` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.enable.gapless.guarantee` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.queue.buffering.max.message` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.queue.buffering.max.kbytes` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.queue.buffering.max.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.linger.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.message.send.max.retries` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.retries` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.retry.backoff.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.retry.backoff.max.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.queue.buffering.backpressure.threshold` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.compression.codec` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.compression.type` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.batch.num.messages` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.batch.size` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.delivery.report.only.error` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.dr_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.dr_msg_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.sticky.partitioning.linger.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.client.dns.lookup` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.enable.metrics.push` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.request.required.acks` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.acks` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.request.timeout.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.message.timeout.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.delivery.timeout.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.queuing.strategy` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.produce.offset.report` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.partitioner` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.partitioner_cb` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.msg_order_cmp` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.opaque` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.compression.codec` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.compression.type` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.compression.level` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.auto.commit.enable` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.enable.auto.commit` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.auto.commit.interval.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.auto.offset.reset` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.offset.store.path` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.offset.store.sync.interval.ms` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.offset.store.method` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kafka` | `rdkafka.consume.callback.max.messages` | [Kafka](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md#global-configuration-properties) |
| `kmsg` | `prio_level` | [Kernel Logs](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kernel-logs#configuration-parameters) |
| `kmsg` | `threaded` | [Kernel Logs](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kernel-logs#configuration-parameters) |
| `kmsg` | `tag` | [Kernel Logs](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `kubernetes_events` | `db` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) |
| `kubernetes_events` | `db.sync` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) |
| `kubernetes_events` | `interval_sec` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) |
| `kubernetes_events` | `interval_nsec` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) |
| `kubernetes_events` | `kube_url` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) |
| `kubernetes_events` | `kube_ca_file` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) |
| `kubernetes_events` | `kube_ca_path` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) |
| `kubernetes_events` | `kube_token_file` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) |
| `kubernetes_events` | `kube_token_ttl` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) |
| `kubernetes_events` | `kube_request_limit` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) |
| `kubernetes_events` | `kube_retention_time` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) |
| `kubernetes_events` | `kube_namespace` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) |
| `kubernetes_events` | `tls.debug` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) |
| `kubernetes_events` | `tls.verify` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) |
| `kubernetes_events` | `tls.vhost` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/kubernetes-events#configuration) |
| `kubernetes_events` | `tag` | [Kubernetes Events](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `mem` | `threaded` | [Memory Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/memory-metrics#threading) |
| `mem` | `tag` | [Memory Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `mqtt` | `listen` | [MQTT](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/mqtt#configuration-parameters) |
| `mqtt` | `port` | [MQTT](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/mqtt#configuration-parameters) |
| `mqtt` | `payload_key` | [MQTT](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/mqtt#configuration-parameters) |
| `mqtt` | `threaded` | [MQTT](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/mqtt#configuration-parameters) |
| `mqtt` | `tag` | [MQTT](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `netif` | `interface` | [Network I/O Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters) |
| `netif` | `interval_sec` | [Network I/O Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters) |
| `netif` | `interval_nsec` | [Network I/O Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters) |
| `netif` | `verbose` | [Network I/O Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters) |
| `netif` | `test_at_init` | [Network I/O Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters) |
| `netif` | `threaded` | [Network I/O Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/network-io-metrics#configuration-parameters) |
| `netif` | `tag` | [Network I/O Log Based Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `nginx_metrics` | `host` | [NGINX Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/nginx#configuration-parameters) |
| `nginx_metrics` | `port` | [NGINX Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/nginx#configuration-parameters) |
| `nginx_metrics` | `status_url` | [NGINX Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/nginx#configuration-parameters) |
| `nginx_metrics` | `nginx_plus` | [NGINX Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/nginx#configuration-parameters) |
| `nginx_metrics` | `threaded` | [NGINX Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/nginx#configuration-parameters) |
| `nginx_metrics` | `tag` | [NGINX Exporter Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `node_exporter_metrics` | `scrape_interval` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `path.procfs` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `path.sysfs` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `collector.cpu.scrape_interval` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `collector.cpufreq.scrape_interval` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `collector.meminfo.scrape_interval` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `collector.diskstats.scrape_interval` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `collector.filesystem.scrape_interval` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `collector.uname.scrape_interval` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `collector.stat.scrape_interval` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `collector.time.scrape_interval` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `collector.loadavg.scrape_interval` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `collector.vmstat.scrape_interval` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `collector.thermal_zone.scrape_interval` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `collector.filefd.scrape_interval` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `collector.nvme.scrape_interval` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `collector.processes.scrape_interval` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `metrics` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `filesystem.ignore_mount_point_regex` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `filesystem.ignore_filesystem_type_regex` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `diskstats.ignore_device_regex` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `systemd_service_restart_metrics` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `systemd_unit_start_time_metrics` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `systemd_include_service_task_metrics` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `systemd_include_pattern` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `systemd_exclude_pattern` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/node-exporter-metrics#configuration) |
| `node_exporter_metrics` | `tag` | [Node Exporter Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `opentelemetry` | `listen` | [OpenTelemetry](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) |
| `opentelemetry` | `port` | [OpenTelemetry](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) |
| `opentelemetry` | `tag` | [OpenTelemetry](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `opentelemetry` | `tag_key` | [OpenTelemetry](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) |
| `opentelemetry` | `raw_traces` | [OpenTelemetry](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) |
| `opentelemetry` | `buffer_max_size` | [OpenTelemetry](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) |
| `opentelemetry` | `buffer_chunk_size` | [OpenTelemetry](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) |
| `opentelemetry` | `successful_response_code` | [OpenTelemetry](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) |
| `opentelemetry` | `tag_from_uri` | [OpenTelemetry](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) |
| `opentelemetry` | `threaded` | [OpenTelemetry](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/opentelemetry#configuration-a-hrefconfiguration-idconfigurationa) |
| `podman_metrics` | `scrape_interval` | [Podman Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters) |
| `podman_metrics` | `scrape_on_start` | [Podman Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters) |
| `podman_metrics` | `path.config` | [Podman Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters) |
| `podman_metrics` | `path.sysfs` | [Podman Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters) |
| `podman_metrics` | `path.procfs` | [Podman Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters) |
| `podman_metrics` | `threaded` | [Podman Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/podman-metrics#configuration-parameters) |
| `podman_metrics` | `tag` | [Podman Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `proc` | `proc_name` | [Process Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) |
| `proc` | `interval_sec` | [Process Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) |
| `proc` | `interval_nsec` | [Process Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) |
| `proc` | `alert` | [Process Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) |
| `proc` | `fd` | [Process Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) |
| `proc` | `mem` | [Process Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) |
| `proc` | `threaded` | [Process Log Based Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process#configuration-parameters) |
| `proc` | `tag` | [Process Log Based Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `process_exporter_metrics` | `scrape_interval` | [Process Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process-exporter-metrics#configuration) |
| `process_exporter_metrics` | `path.procfs` | [Process Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process-exporter-metrics#configuration) |
| `process_exporter_metrics` | `process_include_pattern` | [Process Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process-exporter-metrics#configuration) |
| `process_exporter_metrics` | `process_exclude_pattern` | [Process Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process-exporter-metrics#configuration) |
| `process_exporter_metrics` | `metrics` | [Process Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/process-exporter-metrics#configuration) |
| `process_exporter_metrics` | `tag` | [Process Exporter Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `prometheus_remote_write` | `listen` | [Prometheus Remote Write](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) |
| `prometheus_remote_write` | `port` | [Prometheus Remote Write](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) |
| `prometheus_remote_write` | `buffer_max_size` | [Prometheus Remote Write](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) |
| `prometheus_remote_write` | `buffer_chunk_size` | [Prometheus Remote Write](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) |
| `prometheus_remote_write` | `successful_response_code` | [Prometheus Remote Write](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) |
| `prometheus_remote_write` | `tag_from_uri` | [Prometheus Remote Write](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) |
| `prometheus_remote_write` | `uri` | [Prometheus Remote Write](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) |
| `prometheus_remote_write` | `threaded` | [Prometheus Remote Write](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-remote-write#configuration) |
| `prometheus_remote_write` | `tag` | [Prometheus Remote Write](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `prometheus_scrape` | `host` | [Prometheus Scrape Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-scrape-metrics#configuration-a-hrefconfiguration-idconfigurationa) |
| `prometheus_scrape` | `port` | [Prometheus Scrape Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-scrape-metrics#configuration-a-hrefconfiguration-idconfigurationa) |
| `prometheus_scrape` | `scrape_interval` | [Prometheus Scrape Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-scrape-metrics#configuration-a-hrefconfiguration-idconfigurationa) |
| `prometheus_scrape` | `metrics_path` | [Prometheus Scrape Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-scrape-metrics#configuration-a-hrefconfiguration-idconfigurationa) |
| `prometheus_scrape` | `threaded` | [Prometheus Scrape Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/prometheus-scrape-metrics#configuration-a-hrefconfiguration-idconfigurationa) |
| `prometheus_scrape` | `tag` | [Prometheus Scrape Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `random` | `samples` | [Random](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/random#configuration-parameters) |
| `random` | `interval_sec` | [Random](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/random#configuration-parameters) |
| `random` | `interval_nsec` | [Random](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/random#configuration-parameters) |
| `random` | `threaded` | [Random](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/random#configuration-parameters) |
| `random` | `tag` | [Random](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `serial` | `file` | [Serial Interface](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters) |
| `serial` | `bitrate` | [Serial Interface](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters) |
| `serial` | `min_bytes` | [Serial Interface](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters) |
| `serial` | `separator` | [Serial Interface](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters) |
| `serial` | `format` | [Serial Interface](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters) |
| `serial` | `threaded` | [Serial Interface](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/serial-interface#configuration-parameters) |
| `serial` | `tag` | [Serial Interface](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `splunk` | `listen` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `port` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `tag_key` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `buffer_max_size` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `buffer_chunk_size` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `successful_response_code` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `splunk_token` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `store_token_in_metadata` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `splunk_token_key` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `threaded` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `tag` | [Splunk](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `statsd` | `listen` | [StatsD](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/statsd#configuration-parameters-a-hrefconfig-idconfiga) |
| `statsd` | `port` | [StatsD](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/statsd#configuration-parameters-a-hrefconfig-idconfiga) |
| `statsd` | `threaded` | [StatsD](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/statsd#configuration-parameters-a-hrefconfig-idconfiga) |
| `statsd` | `metrics` | [StatsD](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/statsd#configuration-parameters-a-hrefconfig-idconfiga) |
| `statsd` | `tag` | [StatsD](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `stdin` | `buffer_size` | [Standard Input](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/standard-input#configuration-parameters-a-hrefconfig-idconfiga) |
| `stdin` | `parser` | [Standard Input](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/standard-input#configuration-parameters-a-hrefconfig-idconfiga) |
| `stdin` | `threaded` | [Standard Input](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/standard-input#configuration-parameters-a-hrefconfig-idconfiga) |
| `stdin` | `tag` | [Standard Input](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `syslog` | `mode` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `listen` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `port` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `path` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `unix_perm` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `parser` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `buffer_chunk_size` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `buffer_max_size` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `receive_buffer_size` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `source_address_key` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `threaded` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `tag` | [Syslog](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `systemd` | `path` | [Systemd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `max_fields` | [Systemd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `max_entries` | [Systemd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `systemd_filter` | [Systemd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `systemd_filter_type` | [Systemd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `tag` | [Systemd](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `systemd` | `db` | [Systemd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `db.sync` | [Systemd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `read_from_tail` | [Systemd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `lowercase` | [Systemd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `strip_underscores` | [Systemd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `threaded` | [Systemd](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/systemd#configuration-parameters) |
| `tail` | `buffer_chunk_size` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `buffer_max_size` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `path` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `path_key` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `exclude_path` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `offset_key` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `read_from_head` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `refresh_interval` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `rotate_wait` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `ignore_older` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `skip_long_lines` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `skip_empty_lines` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `db` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `db.sync` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `db.locking` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `db.journal_mode` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `db.compare_filename` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `mem_buf_limit` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `exit_on_eof` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `parser` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `key` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `inotify_watcher` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `tag` | [Tail](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `tail` | `tag_regex` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `static_batch_size` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `file_cache_advise` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tail` | `threaded` | [Tail](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tail#configuration-parameters-a-hrefconfig-idconfiga) |
| `tcp` | `listen` | [TCP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `port` | [TCP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `buffer_size` | [TCP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `chunk_size` | [TCP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `format` | [TCP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `separator` | [TCP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `source_address_key` | [TCP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `threaded` | [TCP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `tag` | [TCP](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `thermal` | `interval_sec` | [Thermal](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/thermal#configuration-parameters) |
| `thermal` | `interval_nsec` | [Thermal](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/thermal#configuration-parameters) |
| `thermal` | `name_regex` | [Thermal](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/thermal#configuration-parameters) |
| `thermal` | `type_regex` | [Thermal](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/thermal#configuration-parameters) |
| `thermal` | `threaded` | [Thermal](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/thermal#configuration-parameters) |
| `thermal` | `tag` | [Thermal](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `udp` | `listen` | [UDP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) |
| `udp` | `port` | [UDP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) |
| `udp` | `buffer_size` | [UDP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) |
| `udp` | `chunk_size` | [UDP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) |
| `udp` | `format` | [UDP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) |
| `udp` | `separator` | [UDP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) |
| `udp` | `source_address_key` | [UDP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) |
| `udp` | `threaded` | [UDP](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/udp#configuration-parameters) |
| `udp` | `tag` | [UDP](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `windows_exporter_metrics` | `scrape_interval` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.logical_disk.allow_disk_regex` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.logical_disk.deny_disk_regex` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.net.allow_nic_regex` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.service.where` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.service.include` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.service.exclude` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.process.allow_process_regex` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.process.deny_process_regex` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.cpu.scrape_interval` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.net.scrape_interval` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.logical_disk.scrape_interval` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.cs.scrape_interval` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.os.scrape_interval` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.thermalzone.scrape_interval` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.cpu_info.scrape_interval` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.logon.scrape_interval` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.system.scrape_interval` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.service.scrape_interval` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.memory.scrape_interval` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.paging_file.scrape_interval` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.process.scrape_interval` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `metrics` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `tag` | [Windows Exporter Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `winevtlog` | `channels` | [Windows Event Log (winevtlog)](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) |
| `winevtlog` | `interval_sec` | [Windows Event Log (winevtlog)](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) |
| `winevtlog` | `interval_nsec` | [Windows Event Log (winevtlog)](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) |
| `winevtlog` | `read_existing_events` | [Windows Event Log (winevtlog)](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) |
| `winevtlog` | `db` | [Windows Event Log (winevtlog)](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) |
| `winevtlog` | `string_inserts` | [Windows Event Log (winevtlog)](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) |
| `winevtlog` | `render_event_as_xml` | [Windows Event Log (winevtlog)](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) |
| `winevtlog` | `ignore_missing_channels` | [Windows Event Log (winevtlog)](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) |
| `winevtlog` | `use_ansi` | [Windows Event Log (winevtlog)](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) |
| `winevtlog` | `event_query` | [Windows Event Log (winevtlog)](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) |
| `winevtlog` | `read_limit_per_cycle` | [Windows Event Log (winevtlog)](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) |
| `winevtlog` | `threaded` | [Windows Event Log (winevtlog)](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log-winevtlog#configuration-parameters-a-hrefconfig-idconfiga) |
| `winevtlog` | `tag` | [Windows Event Log (winevtlog)](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `winlog` | `channels` | [Windows Event Log](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log#configuration-parameters-a-hrefconfig-idconfiga) |
| `winlog` | `interval_sec` | [Windows Event Log](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log#configuration-parameters-a-hrefconfig-idconfiga) |
| `winlog` | `db` | [Windows Event Log](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log#configuration-parameters-a-hrefconfig-idconfiga) |
| `winlog` | `threaded` | [Windows Event Log](https://docs.fluentbit.io/manual/3.2/pipeline/inputs/windows-event-log#configuration-parameters-a-hrefconfig-idconfiga) |
| `winlog` | `tag` | [Windows Event Log](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |

## Filters

| Plugin Name | Attribute Name | Fluent Bit Page |
| --- | --- | --- |
| `aws` | `imds_version` | [AWS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `az` | [AWS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `ec2_instance_id` | [AWS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `ec2_instance_type` | [AWS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `private_ip` | [AWS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `ami_id` | [AWS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `account_id` | [AWS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `hostname` | [AWS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `vpc_id` | [AWS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `tags_enabled` | [AWS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `tags_include` | [AWS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `tags_exclude` | [AWS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `retry_interval_s` | [AWS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `match` | [AWS Metadata](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `aws` | `match_regex` | [AWS Metadata](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `checklist` | `file` | [CheckList](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters) |
| `checklist` | `lookup_key` | [CheckList](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters) |
| `checklist` | `record` | [CheckList](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters) |
| `checklist` | `mode` | [CheckList](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters) |
| `checklist` | `print_query_time` | [CheckList](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters) |
| `checklist` | `ignore_case` | [CheckList](https://docs.fluentbit.io/manual/3.2/pipeline/filters/checklist#configuration-parameters) |
| `checklist` | `match` | [CheckList](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `checklist` | `match_regex` | [CheckList](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `ecs` | `add` | [ECS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/ecs-metadata#configuration-parameters) |
| `ecs` | `ecs_tag_prefix` | [ECS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/ecs-metadata#configuration-parameters) |
| `ecs` | `cluster_metadata_only` | [ECS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/ecs-metadata#configuration-parameters) |
| `ecs` | `ecs_meta_cache_ttl` | [ECS Metadata](https://docs.fluentbit.io/manual/3.2/pipeline/filters/ecs-metadata#configuration-parameters) |
| `ecs` | `match` | [ECS Metadata](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `ecs` | `match_regex` | [ECS Metadata](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `expect` | `key_exists` | [Expect](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) |
| `expect` | `key_not_exists` | [Expect](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) |
| `expect` | `key_val_is_null` | [Expect](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) |
| `expect` | `key_val_is_not_null` | [Expect](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) |
| `expect` | `key_val_eq` | [Expect](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) |
| `expect` | `action` | [Expect](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) |
| `expect` | `result_key` | [Expect](https://docs.fluentbit.io/manual/3.2/pipeline/filters/expect#configuration-parameters) |
| `expect` | `match` | [Expect](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `expect` | `match_regex` | [Expect](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `geoip2` | `database` | [GeoIP2 Filter](https://docs.fluentbit.io/manual/3.2/pipeline/filters/geoip2-filter#configuration-parameters-a-hrefconfig-idconfiga) |
| `geoip2` | `lookup_key` | [GeoIP2 Filter](https://docs.fluentbit.io/manual/3.2/pipeline/filters/geoip2-filter#configuration-parameters-a-hrefconfig-idconfiga) |
| `geoip2` | `record` | [GeoIP2 Filter](https://docs.fluentbit.io/manual/3.2/pipeline/filters/geoip2-filter#configuration-parameters-a-hrefconfig-idconfiga) |
| `geoip2` | `match` | [GeoIP2 Filter](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `geoip2` | `match_regex` | [GeoIP2 Filter](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `grep` | `regex` | [Grep](https://docs.fluentbit.io/manual/3.2/pipeline/filters/grep#configuration-parameters) |
| `grep` | `exclude` | [Grep](https://docs.fluentbit.io/manual/3.2/pipeline/filters/grep#configuration-parameters) |
| `grep` | `logical_op` | [Grep](https://docs.fluentbit.io/manual/3.2/pipeline/filters/grep#configuration-parameters) |
| `grep` | `match` | [Grep](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `grep` | `match_regex` | [Grep](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `kubernetes` | `buffer_size` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_url` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_ca_file` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_ca_path` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_token_file` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_tag_prefix` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `merge_log` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `merge_log_key` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `merge_log_trim` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `merge_parser` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `keep_log` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `tls.debug` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `tls.verify` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `tls.verify_hostname` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `use_journal` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `cache_use_docker_id` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `regex_parser` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `k8s-logging.parser` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `k8s-logging.exclude` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `labels` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `annotations` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_meta_preload_cache_dir` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `dummy_meta` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `dns_retries` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `dns_wait_time` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `use_kubelet` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `use_tag_for_meta` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kubelet_port` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kubelet_host` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_meta_cache_ttl` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_token_ttl` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_token_command` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_meta_namespace_cache_ttl` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `namespace_labels` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `namespace_annotations` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `namespace_metadata_only` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `owner_references` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `match` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `kubernetes` | `match_regex` | [Kubernetes](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `log_to_metrics` | `tag` | [Log to Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `metric_mode` | [Log to Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `metric_name` | [Log to Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `metric_description` | [Log to Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `bucket` | [Log to Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `add_label` | [Log to Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `label_field` | [Log to Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `value_field` | [Log to Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `kubernetes_mode` | [Log to Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `regex` | [Log to Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `exclude` | [Log to Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `flush_interval_sec` | [Log to Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `flush_interval_nsec` | [Log to Metrics](https://docs.fluentbit.io/manual/3.2/pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `match` | [Log to Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `log_to_metrics` | `match_regex` | [Log to Metrics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `lua` | `script` | [Lua](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) |
| `lua` | `call` | [Lua](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) |
| `lua` | `type_int_key` | [Lua](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) |
| `lua` | `type_array_key` | [Lua](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) |
| `lua` | `protected_mode` | [Lua](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) |
| `lua` | `time_as_table` | [Lua](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) |
| `lua` | `code` | [Lua](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) |
| `lua` | `enable_flb_null` | [Lua](https://docs.fluentbit.io/manual/3.2/pipeline/filters/lua#configuration-parameters-a-hrefconfig-idconfiga) |
| `lua` | `match` | [Lua](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `lua` | `match_regex` | [Lua](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `modify` | `set` | [Modify](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) |
| `modify` | `add` | [Modify](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) |
| `modify` | `remove` | [Modify](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) |
| `modify` | `remove_wildcard` | [Modify](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) |
| `modify` | `remove_regex` | [Modify](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) |
| `modify` | `rename` | [Modify](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) |
| `modify` | `hard_rename` | [Modify](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) |
| `modify` | `copy` | [Modify](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) |
| `modify` | `hard_copy` | [Modify](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) |
| `modify` | `move_to_start` | [Modify](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) |
| `modify` | `move_to_end` | [Modify](https://docs.fluentbit.io/manual/3.2/pipeline/filters/modify#configuration-parameters) |
| `modify` | `match` | [Modify](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `modify` | `match_regex` | [Modify](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `multiline` | `multiline.parser` | [Multiline](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `multiline.key_content` | [Multiline](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `mode` | [Multiline](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `buffer` | [Multiline](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `flush_ms` | [Multiline](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `emitter_name` | [Multiline](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `emitter_storage.type` | [Multiline](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `emitter_mem_buf_limit` | [Multiline](https://docs.fluentbit.io/manual/3.2/pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `match` | [Multiline](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `multiline` | `match_regex` | [Multiline](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `nest` | `operation` | [Nest](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters) |
| `nest` | `wildcard` | [Nest](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters) |
| `nest` | `nest_under` | [Nest](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters) |
| `nest` | `nested_under` | [Nest](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters) |
| `nest` | `add_prefix` | [Nest](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters) |
| `nest` | `remove_prefix` | [Nest](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nest#configuration-parameters) |
| `nest` | `match` | [Nest](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `nest` | `match_regex` | [Nest](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `nightfall` | `nightfall_api_key` | [Nightfall](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters) |
| `nightfall` | `policy_id` | [Nightfall](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters) |
| `nightfall` | `sampling_rate` | [Nightfall](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters) |
| `nightfall` | `tls.debug` | [Nightfall](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters) |
| `nightfall` | `tls.verify` | [Nightfall](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters) |
| `nightfall` | `tls.ca_path` | [Nightfall](https://docs.fluentbit.io/manual/3.2/pipeline/filters/nightfall#configuration-parameters) |
| `nightfall` | `match` | [Nightfall](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `nightfall` | `match_regex` | [Nightfall](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `parser` | `key_name` | [Parser](https://docs.fluentbit.io/manual/3.2/pipeline/filters/parser#configuration-parameters) |
| `parser` | `parser` | [Parser](https://docs.fluentbit.io/manual/3.2/pipeline/filters/parser#configuration-parameters) |
| `parser` | `preserve_key` | [Parser](https://docs.fluentbit.io/manual/3.2/pipeline/filters/parser#configuration-parameters) |
| `parser` | `reserve_data` | [Parser](https://docs.fluentbit.io/manual/3.2/pipeline/filters/parser#configuration-parameters) |
| `parser` | `match` | [Parser](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `parser` | `match_regex` | [Parser](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `record_modifier` | `record` | [Record Modifier](https://docs.fluentbit.io/manual/3.2/pipeline/filters/record-modifier#configuration-parameters) |
| `record_modifier` | `remove_key` | [Record Modifier](https://docs.fluentbit.io/manual/3.2/pipeline/filters/record-modifier#configuration-parameters) |
| `record_modifier` | `allowlist_key` | [Record Modifier](https://docs.fluentbit.io/manual/3.2/pipeline/filters/record-modifier#configuration-parameters) |
| `record_modifier` | `whitelist_key` | [Record Modifier](https://docs.fluentbit.io/manual/3.2/pipeline/filters/record-modifier#configuration-parameters) |
| `record_modifier` | `uuid_key` | [Record Modifier](https://docs.fluentbit.io/manual/3.2/pipeline/filters/record-modifier#configuration-parameters) |
| `record_modifier` | `match` | [Record Modifier](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `record_modifier` | `match_regex` | [Record Modifier](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `rewrite_tag` | `rule` | [Rewrite Tag](https://docs.fluentbit.io/manual/3.2/pipeline/filters/rewrite-tag#configuration-parameters) |
| `rewrite_tag` | `emitter_name` | [Rewrite Tag](https://docs.fluentbit.io/manual/3.2/pipeline/filters/rewrite-tag#configuration-parameters) |
| `rewrite_tag` | `emitter_storage.type` | [Rewrite Tag](https://docs.fluentbit.io/manual/3.2/pipeline/filters/rewrite-tag#configuration-parameters) |
| `rewrite_tag` | `emitter_mem_buf_limit` | [Rewrite Tag](https://docs.fluentbit.io/manual/3.2/pipeline/filters/rewrite-tag#configuration-parameters) |
| `rewrite_tag` | `match` | [Rewrite Tag](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `rewrite_tag` | `match_regex` | [Rewrite Tag](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `stdout` | `match` | [Standard Output](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `stdout` | `match_regex` | [Standard Output](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `sysinfo` | `fluentbit_version_key` | [Sysinfo](https://docs.fluentbit.io/manual/3.2/pipeline/filters/sysinfo#configuration-prameters) |
| `sysinfo` | `os_name_key` | [Sysinfo](https://docs.fluentbit.io/manual/3.2/pipeline/filters/sysinfo#configuration-prameters) |
| `sysinfo` | `hostname_key` | [Sysinfo](https://docs.fluentbit.io/manual/3.2/pipeline/filters/sysinfo#configuration-prameters) |
| `sysinfo` | `os_version_key` | [Sysinfo](https://docs.fluentbit.io/manual/3.2/pipeline/filters/sysinfo#configuration-prameters) |
| `sysinfo` | `kernel_version_key` | [Sysinfo](https://docs.fluentbit.io/manual/3.2/pipeline/filters/sysinfo#configuration-prameters) |
| `sysinfo` | `match` | [Sysinfo](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `sysinfo` | `match_regex` | [Sysinfo](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `tensorflow` | `input_field` | [Tensorflow](https://docs.fluentbit.io/manual/3.2/pipeline/filters/tensorflow#configuration-parameters) |
| `tensorflow` | `model_file` | [Tensorflow](https://docs.fluentbit.io/manual/3.2/pipeline/filters/tensorflow#configuration-parameters) |
| `tensorflow` | `include_input_fields` | [Tensorflow](https://docs.fluentbit.io/manual/3.2/pipeline/filters/tensorflow#configuration-parameters) |
| `tensorflow` | `normalization_value` | [Tensorflow](https://docs.fluentbit.io/manual/3.2/pipeline/filters/tensorflow#configuration-parameters) |
| `tensorflow` | `match` | [Tensorflow](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `tensorflow` | `match_regex` | [Tensorflow](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `throttle` | `rate` | [Throttle](https://docs.fluentbit.io/manual/3.2/pipeline/filters/throttle#configuration-parameters) |
| `throttle` | `window` | [Throttle](https://docs.fluentbit.io/manual/3.2/pipeline/filters/throttle#configuration-parameters) |
| `throttle` | `interval` | [Throttle](https://docs.fluentbit.io/manual/3.2/pipeline/filters/throttle#configuration-parameters) |
| `throttle` | `print_status` | [Throttle](https://docs.fluentbit.io/manual/3.2/pipeline/filters/throttle#configuration-parameters) |
| `throttle` | `match` | [Throttle](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `throttle` | `match_regex` | [Throttle](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `type_converter` | `int_key` | [Type Converter](https://docs.fluentbit.io/manual/3.2/pipeline/filters/type-converter#configuration-parameters) |
| `type_converter` | `uint_key` | [Type Converter](https://docs.fluentbit.io/manual/3.2/pipeline/filters/type-converter#configuration-parameters) |
| `type_converter` | `float_key` | [Type Converter](https://docs.fluentbit.io/manual/3.2/pipeline/filters/type-converter#configuration-parameters) |
| `type_converter` | `str_key` | [Type Converter](https://docs.fluentbit.io/manual/3.2/pipeline/filters/type-converter#configuration-parameters) |
| `type_converter` | `match` | [Type Converter](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `type_converter` | `match_regex` | [Type Converter](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `wasm` | `wasm_path` | [Wasm](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga) |
| `wasm` | `event_format` | [Wasm](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga) |
| `wasm` | `function_name` | [Wasm](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga) |
| `wasm` | `accessible_paths` | [Wasm](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga) |
| `wasm` | `wasm_heap_size` | [Wasm](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga) |
| `wasm` | `wasm_stack_size` | [Wasm](https://docs.fluentbit.io/manual/3.2/pipeline/filters/wasm#configuration-parameters-a-hrefconfig-idconfiga) |
| `wasm` | `match` | [Wasm](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `wasm` | `match_regex` | [Wasm](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |

## Outputs

| Plugin Name | Attribute Name | Fluent Bit Page |
| --- | --- | --- |
| `azure` | `customer_id` | [Azure Log Analytics](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) |
| `azure` | `shared_key` | [Azure Log Analytics](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) |
| `azure` | `log_type` | [Azure Log Analytics](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) |
| `azure` | `log_type_key` | [Azure Log Analytics](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) |
| `azure` | `time_key` | [Azure Log Analytics](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) |
| `azure` | `time_generated` | [Azure Log Analytics](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) |
| `azure` | `workers` | [Azure Log Analytics](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure#configuration-parameters) |
| `azure` | `match` | [Azure Log Analytics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `azure` | `match_regex` | [Azure Log Analytics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `azure_blob` | `account_name` | [Azure Blob](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `auth_type` | [Azure Blob](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `shared_key` | [Azure Blob](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `sas_token` | [Azure Blob](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `container_name` | [Azure Blob](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `blob_type` | [Azure Blob](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `auto_create_container` | [Azure Blob](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `path` | [Azure Blob](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `emulator_mode` | [Azure Blob](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `endpoint` | [Azure Blob](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `tls` | [Azure Blob](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `workers` | [Azure Blob](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `match` | [Azure Blob](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `azure_blob` | `match_regex` | [Azure Blob](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `azure_kusto` | `tenant_id` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `client_id` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `client_secret` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `ingestion_endpoint` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `database_name` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `table_name` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `ingestion_mapping_reference` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `log_key` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `include_tag_key` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tag_key` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `include_time_key` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `time_key` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `ingestion_endpoint_connect_timeout` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `compression_enabled` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `ingestion_resources_refresh_interval` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `workers` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `match` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `azure_kusto` | `match_regex` | [Azure Data Explorer](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `azure_logs_ingestion` | `tenant_id` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `client_id` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `client_secret` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `dce_url` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `dcr_id` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `table_name` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `time_key` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `time_generated` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `compress` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `workers` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `match` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `azure_logs_ingestion` | `match_regex` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `bigquery` | `google_service_credentials` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) |
| `bigquery` | `project_id` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) |
| `bigquery` | `dataset_id` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) |
| `bigquery` | `table_id` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) |
| `bigquery` | `skip_invalid_rows` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) |
| `bigquery` | `ignore_unknown_values` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) |
| `bigquery` | `enable_workload_identity_federation` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) |
| `bigquery` | `aws_region` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) |
| `bigquery` | `project_number` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) |
| `bigquery` | `pool_id` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) |
| `bigquery` | `provider_id` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) |
| `bigquery` | `google_service_account` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) |
| `bigquery` | `workers` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/bigquery#configurations-parameters) |
| `bigquery` | `match` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `bigquery` | `match_regex` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `chronicle` | `google_service_credentials` | [Google Chronicle](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) |
| `chronicle` | `service_account_email` | [Google Chronicle](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) |
| `chronicle` | `service_account_secret` | [Google Chronicle](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) |
| `chronicle` | `project_id` | [Google Chronicle](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) |
| `chronicle` | `customer_id` | [Google Chronicle](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) |
| `chronicle` | `log_type` | [Google Chronicle](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) |
| `chronicle` | `region` | [Google Chronicle](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) |
| `chronicle` | `log_key` | [Google Chronicle](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) |
| `chronicle` | `workers` | [Google Chronicle](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/chronicle#configurations-parameters) |
| `chronicle` | `match` | [Google Chronicle](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `chronicle` | `match_regex` | [Google Chronicle](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `cloudwatch_logs` | `region` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_group_name` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_group_template` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_stream_name` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_stream_prefix` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_stream_template` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_key` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_format` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `role_arn` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `auto_create_group` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_retention_days` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `endpoint` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `metric_namespace` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `metric_dimensions` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `sts_endpoint` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `profile` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `auto_retry_requests` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `external_id` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `workers` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `match` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `cloudwatch_logs` | `match_regex` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `counter` | `match` | [Counter](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `counter` | `match_regex` | [Counter](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `dash0` | `header` | [Dash0](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) |
| `dash0` | `host` | [Dash0](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) |
| `dash0` | `port` | [Dash0](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) |
| `dash0` | `metrics_uri` | [Dash0](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) |
| `dash0` | `logs_uri` | [Dash0](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) |
| `dash0` | `traces_uri` | [Dash0](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dash0#configuration-parameters) |
| `dash0` | `match` | [Dash0](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `dash0` | `match_regex` | [Dash0](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `datadog` | `host` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `tls` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `compress` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `apikey` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `proxy` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `provider` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `json_date_key` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `include_tag_key` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `tag_key` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `dd_service` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `dd_source` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `dd_tags` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `dd_message_key` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `dd_hostname` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `workers` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `header` | [Datadog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `match` | [Datadog](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `datadog` | `match_regex` | [Datadog](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `dynatrace` | `header` | [Dynatrace](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `allow_duplicated_headers` | [Dynatrace](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `host` | [Dynatrace](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `port` | [Dynatrace](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `uri` | [Dynatrace](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `format` | [Dynatrace](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `json_date_format` | [Dynatrace](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `json_date_key` | [Dynatrace](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `tls` | [Dynatrace](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `tls.verify` | [Dynatrace](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `match` | [Dynatrace](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `dynatrace` | `match_regex` | [Dynatrace](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `es` | `host` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `port` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `path` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `compress` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `buffer_size` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `pipeline` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `aws_auth` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `aws_region` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `aws_sts_endpoint` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `aws_role_arn` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `aws_external_id` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `aws_service_name` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `aws_profile` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `cloud_id` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `cloud_auth` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `http_user` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `http_passwd` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `index` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `type` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `logstash_format` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `logstash_prefix` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `logstash_prefix_key` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `logstash_prefix_separator` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `logstash_dateformat` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `time_key` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `time_key_format` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `time_key_nanos` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `include_tag_key` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `tag_key` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `generate_id` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `id_key` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `write_operation` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `replace_dots` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `trace_output` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `trace_error` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `current_time_index` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `suppress_type_name` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `workers` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `match` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `es` | `match_regex` | [Elasticsearch](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `file` | `path` | [File](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/file#configuration-parameters) |
| `file` | `file` | [File](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/file#configuration-parameters) |
| `file` | `format` | [File](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/file#configuration-parameters) |
| `file` | `mkdir` | [File](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/file#configuration-parameters) |
| `file` | `workers` | [File](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/file#configuration-parameters) |
| `file` | `match` | [File](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `file` | `match_regex` | [File](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `flowcounter` | `unit` | [FlowCounter](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/flowcounter#configuration-parameters) |
| `flowcounter` | `workers` | [FlowCounter](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/flowcounter#configuration-parameters) |
| `flowcounter` | `match` | [FlowCounter](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `flowcounter` | `match_regex` | [FlowCounter](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `forward` | `host` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) |
| `forward` | `port` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) |
| `forward` | `time_as_integer` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) |
| `forward` | `upstream` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) |
| `forward` | `unix_path` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) |
| `forward` | `tag` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) |
| `forward` | `send_options` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) |
| `forward` | `require_ack_response` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) |
| `forward` | `compress` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) |
| `forward` | `workers` | [Forward](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/forward#configuration-parameters) |
| `forward` | `match` | [Forward](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `forward` | `match_regex` | [Forward](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `gelf` | `match` | [GELF](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `host` | [GELF](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `port` | [GELF](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `mode` | [GELF](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `gelf_tag_key` | [GELF](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `gelf_short_message_key` | [GELF](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `gelf_timestamp_key` | [GELF](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `gelf_host_key` | [GELF](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `gelf_full_message_key` | [GELF](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `gelf_level_key` | [GELF](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `packet_size` | [GELF](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `compress` | [GELF](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `workers` | [GELF](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `match_regex` | [GELF](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `http` | `host` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `http_user` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `http_passwd` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `aws_auth` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `aws_service` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `aws_region` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `aws_sts_endpoint` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `aws_role_arn` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `aws_external_id` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `port` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `proxy` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `uri` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `compress` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `format` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `allow_duplicated_headers` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `log_response_payload` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `header_tag` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `header` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `json_date_key` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `json_date_format` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `gelf_timestamp_key` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `gelf_host_key` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `gelf_short_message_key` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `gelf_full_message_key` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `gelf_level_key` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `body_key` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `headers_key` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `workers` | [HTTP](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/http#configuration-parameters) |
| `http` | `match` | [HTTP](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `http` | `match_regex` | [HTTP](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `influxdb` | `host` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `port` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `database` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `bucket` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `org` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `sequence_tag` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `http_user` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `http_passwd` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `http_token` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `http_header` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `tag_keys` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `auto_tags` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `uri` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `add_integer_suffix` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `workers` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `match` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `influxdb` | `match_regex` | [InfluxDB](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `kafka` | `format` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `message_key` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `message_key_field` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `timestamp_key` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `timestamp_format` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `brokers` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `topics` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `topic_key` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `dynamic_topic` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `queue_full_retries` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `rdkafka.{property}` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `raw_log_key` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `workers` | [Kafka](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `match` | [Kafka](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `kafka` | `match_regex` | [Kafka](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `kafka-rest` | `host` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `port` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `topic` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `partition` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `message_key` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `time_key` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `time_key_format` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `include_tag_key` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `tag_key` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `workers` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `match` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `kafka-rest` | `match_regex` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `kinesis_firehose` | `region` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `delivery_stream` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `time_key` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `time_key_format` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `log_key` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `compression` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `role_arn` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `endpoint` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `sts_endpoint` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `auto_retry_requests` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `external_id` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `profile` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `workers` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `match` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `kinesis_firehose` | `match_regex` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `kinesis_streams` | `region` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `stream` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `time_key` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `time_key_format` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `log_key` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `role_arn` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `endpoint` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `port` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `sts_endpoint` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `auto_retry_requests` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `external_id` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `profile` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `workers` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `match` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `kinesis_streams` | `match_regex` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `logdna` | `logdna_host` | [LogDNA](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `logdna_port` | [LogDNA](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `logdna_endpoint` | [LogDNA](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `api_key` | [LogDNA](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `hostname` | [LogDNA](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `mac` | [LogDNA](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `ip` | [LogDNA](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `tags` | [LogDNA](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `file` | [LogDNA](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `app` | [LogDNA](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `workers` | [LogDNA](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `match` | [LogDNA](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `logdna` | `match_regex` | [LogDNA](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `loki` | `host` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `uri` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `port` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `tls` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `http_user` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `http_passwd` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `bearer_token` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `header` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `tenant_id` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `labels` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `label_keys` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `label_map_path` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `structured_metadata` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `structured_metadata_map_keys` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `remove_keys` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `drop_single_key` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `line_format` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `auto_kubernetes_labels` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `tenant_id_key` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `compress` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `workers` | [Loki](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/loki#configuration-parameters) |
| `loki` | `match` | [Loki](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `loki` | `match_regex` | [Loki](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `nats` | `host` | [NATS](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/nats#configuration-parameters) |
| `nats` | `port` | [NATS](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/nats#configuration-parameters) |
| `nats` | `workers` | [NATS](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/nats#configuration-parameters) |
| `nats` | `match` | [NATS](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `nats` | `match_regex` | [NATS](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `newrelic` | `match` | [New Relic](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `newrelic` | `match_regex` | [New Relic](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `null` | `match` | [NULL](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `null` | `match_regex` | [NULL](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `observe` | `host` | [Observe](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) |
| `observe` | `port` | [Observe](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) |
| `observe` | `tls` | [Observe](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) |
| `observe` | `uri` | [Observe](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) |
| `observe` | `format` | [Observe](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) |
| `observe` | `header` | [Observe](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) |
| `observe` | `compress` | [Observe](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) |
| `observe` | `tls.ca_file` | [Observe](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) |
| `observe` | `workers` | [Observe](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/observe#configuration-parameters) |
| `observe` | `match` | [Observe](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `observe` | `match_regex` | [Observe](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `openobserve` | `match` | [OpenObserve](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `openobserve` | `match_regex` | [OpenObserve](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `opensearch` | `host` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `port` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `path` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `buffer_size` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `pipeline` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `aws_auth` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `aws_region` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `aws_sts_endpoint` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `aws_role_arn` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `aws_external_id` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `aws_service_name` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `aws_profile` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `http_user` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `http_passwd` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `index` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `type` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `logstash_format` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `logstash_prefix` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `logstash_prefix_key` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `logstash_prefix_separator` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `logstash_dateformat` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `time_key` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `time_key_format` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `time_key_nanos` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `include_tag_key` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `tag_key` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `generate_id` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `id_key` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `write_operation` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `replace_dots` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `trace_output` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `trace_error` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `current_time_index` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `suppress_type_name` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `workers` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `compress` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `match` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `opensearch` | `match_regex` | [OpenSearch](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `opentelemetry` | `match` | [OpenTelemetry](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `opentelemetry` | `match_regex` | [OpenTelemetry](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `oracle_log_analytics` | `config_file_location` | [Oracle Log Analytics](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `profile_name` | [Oracle Log Analytics](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `namespace` | [Oracle Log Analytics](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `proxy` | [Oracle Log Analytics](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `workers` | [Oracle Log Analytics](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `match` | [Oracle Log Analytics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `oracle_log_analytics` | `match_regex` | [Oracle Log Analytics](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `pgsql` | `host` | [PostgreSQL](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `port` | [PostgreSQL](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `user` | [PostgreSQL](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `password` | [PostgreSQL](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `database` | [PostgreSQL](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `table` | [PostgreSQL](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `connection_options` | [PostgreSQL](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `timestamp_key` | [PostgreSQL](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `async` | [PostgreSQL](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `min_pool_size` | [PostgreSQL](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `max_pool_size` | [PostgreSQL](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `cockroachdb` | [PostgreSQL](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `workers` | [PostgreSQL](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `match` | [PostgreSQL](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `pgsql` | `match_regex` | [PostgreSQL](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `prometheus_exporter` | `match` | [Prometheus Exporter](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `prometheus_exporter` | `match_regex` | [Prometheus Exporter](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `prometheus_remote_write` | `match` | [Prometheus Remote Write](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `prometheus_remote_write` | `match_regex` | [Prometheus Remote Write](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `s3` | `region` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `bucket` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `json_date_key` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `json_date_format` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `total_file_size` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `upload_chunk_size` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `upload_timeout` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `store_dir` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `store_dir_limit_size` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `s3_key_format` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `s3_key_format_tag_delimiters` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `static_file_path` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `use_put_object` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `role_arn` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `endpoint` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `sts_endpoint` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `profile` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `canned_acl` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `compression` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `content_type` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `send_content_md5` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `auto_retry_requests` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `log_key` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `preserve_data_ordering` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `storage_class` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `retry_limit` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `external_id` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `workers` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/s3#configuration-parameters) |
| `s3` | `match` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `s3` | `match_regex` | [Amazon S3](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `skywalking` | `host` | [SkyWalking](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) |
| `skywalking` | `port` | [SkyWalking](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) |
| `skywalking` | `auth_token` | [SkyWalking](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) |
| `skywalking` | `svc_name` | [SkyWalking](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) |
| `skywalking` | `svc_inst_name` | [SkyWalking](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) |
| `skywalking` | `workers` | [SkyWalking](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/skywalking#configuration-parameters) |
| `skywalking` | `match` | [SkyWalking](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `skywalking` | `match_regex` | [SkyWalking](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `slack` | `webhook` | [Slack](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/slack#configuration-parameters) |
| `slack` | `workers` | [Slack](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/slack#configuration-parameters) |
| `slack` | `match` | [Slack](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `slack` | `match_regex` | [Slack](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `splunk` | `host` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `port` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `splunk_token` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `http_user` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `http_passwd` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `http_buffer_size` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `compress` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `channel` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `http_debug_bad_request` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `workers` | [Splunk](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `match` | [Splunk](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `splunk` | `match_regex` | [Splunk](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `stackdriver` | `google_service_credentials` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `service_account_email` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `service_account_secret` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `metadata_server` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `location` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `namespace` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `node_id` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `job` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `task_id` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `export_to_project_id` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `resource` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `k8s_cluster_name` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `k8s_cluster_location` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `labels_key` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `labels` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `log_name_key` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `tag_prefix` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `severity_key` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `project_id_key` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `autoformat_stackdriver_trace` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `workers` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `custom_k8s_regex` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `resource_labels` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `compress` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `cloud_logging_base_url` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `match` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `stackdriver` | `match_regex` | [Stackdriver](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `stdout` | `format` | [Standard Output](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/standard-output#configuration-parameters) |
| `stdout` | `json_date_key` | [Standard Output](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/standard-output#configuration-parameters) |
| `stdout` | `json_date_format` | [Standard Output](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/standard-output#configuration-parameters) |
| `stdout` | `workers` | [Standard Output](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/standard-output#configuration-parameters) |
| `stdout` | `match` | [Standard Output](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `stdout` | `match_regex` | [Standard Output](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `syslog` | `host` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `port` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `mode` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_format` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_maxsize` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_severity_key` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_severity_preset` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_facility_key` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_facility_preset` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_hostname_key` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_hostname_preset` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_appname_key` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_appname_preset` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_procid_key` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_procid_preset` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_msgid_key` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_msgid_preset` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_sd_key` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_message_key` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `allow_longer_sd_id` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `workers` | [Syslog](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `match` | [Syslog](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `syslog` | `match_regex` | [Syslog](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `tcp` | `host` | [TCP & TLS](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) |
| `tcp` | `port` | [TCP & TLS](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) |
| `tcp` | `format` | [TCP & TLS](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) |
| `tcp` | `json_date_key` | [TCP & TLS](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) |
| `tcp` | `json_date_format` | [TCP & TLS](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) |
| `tcp` | `workers` | [TCP & TLS](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/tcp-and-tls#configuration-parameters) |
| `tcp` | `match` | [TCP & TLS](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `tcp` | `match_regex` | [TCP & TLS](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `td` | `api` | [Treasure Data](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/treasure-data#configuration-parameters) |
| `td` | `database` | [Treasure Data](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/treasure-data#configuration-parameters) |
| `td` | `table` | [Treasure Data](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/treasure-data#configuration-parameters) |
| `td` | `region` | [Treasure Data](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/treasure-data#configuration-parameters) |
| `td` | `workers` | [Treasure Data](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/treasure-data#configuration-parameters) |
| `td` | `match` | [Treasure Data](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `td` | `match_regex` | [Treasure Data](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `vivo_exporter` | `empty_stream_on_read` | [Vivo Exporter](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/vivo-exporter#configuration-parameters) |
| `vivo_exporter` | `stream_queue_size` | [Vivo Exporter](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/vivo-exporter#configuration-parameters) |
| `vivo_exporter` | `http_cors_allow_origin` | [Vivo Exporter](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/vivo-exporter#configuration-parameters) |
| `vivo_exporter` | `workers` | [Vivo Exporter](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/vivo-exporter#configuration-parameters) |
| `vivo_exporter` | `match` | [Vivo Exporter](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `vivo_exporter` | `match_regex` | [Vivo Exporter](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `websocket` | `host` | [WebSocket](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `port` | [WebSocket](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `uri` | [WebSocket](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `header` | [WebSocket](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `format` | [WebSocket](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `json_date_key` | [WebSocket](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `json_date_format` | [WebSocket](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `workers` | [WebSocket](https://docs.fluentbit.io/manual/3.2/pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `match` | [WebSocket](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
| `websocket` | `match_regex` | [WebSocket](https://docs.fluentbit.io/manual/3.2/concepts/data-pipeline/router) |
