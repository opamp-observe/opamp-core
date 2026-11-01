# Fluent Bit 5.0.4 Plugin Attribute Reference

Generated from the local catalog JSON only.
- `config-service\src\config_service\json-definitions\fluent-bit-5.0.4-all-plugins-catalog.json`

Scope: this reference includes the field-based `inputs`, `filters`, and `outputs` plugin groups from the catalog JSON. The `custom_plugins` block is not tabulated because it does not provide per-attribute documentation links in the same structure.

## Inputs

| Plugin Name | Attribute Name | Fluent Bit Page |
| --- | --- | --- |
| `blob` | `alias` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `database_file` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `exclude_pattern` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `log_level` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `log_suppress_interval` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `mem_buf_limit` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `path` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `routable` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `scan_refresh_interval` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `storage.pause_on_chunks_overlimit` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `storage.type` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `tag` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `blob` | `threaded` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `thread.ring_buffer.capacity` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `thread.ring_buffer.window` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `upload_failure_action` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `upload_failure_message` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `upload_failure_suffix` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `upload_success_action` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `upload_success_message` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `blob` | `upload_success_suffix` | [Blob](https://docs.fluentbit.io/manual/data-pipeline/inputs/blob#configuration-parameters) |
| `collectd` | `listen` | [Collectd](https://docs.fluentbit.io/manual/data-pipeline/inputs/collectd#configuration-parameters) |
| `collectd` | `port` | [Collectd](https://docs.fluentbit.io/manual/data-pipeline/inputs/collectd#configuration-parameters) |
| `collectd` | `threaded` | [Collectd](https://docs.fluentbit.io/manual/data-pipeline/inputs/collectd#configuration-parameters) |
| `collectd` | `typesdb` | [Collectd](https://docs.fluentbit.io/manual/data-pipeline/inputs/collectd#configuration-parameters) |
| `collectd` | `tag` | [Collectd](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `cpu` | `interval_nsec` | [CPU metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/cpu-metrics#configuration-parameters) |
| `cpu` | `interval_sec` | [CPU metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/cpu-metrics#configuration-parameters) |
| `cpu` | `pid` | [CPU metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/cpu-metrics#configuration-parameters) |
| `cpu` | `threaded` | [CPU metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/cpu-metrics#configuration-parameters) |
| `cpu` | `tag` | [CPU metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `disk` | `dev_name` | [Disk I/O metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/disk-io-metrics#configuration-parameters) |
| `disk` | `interval_nsec` | [Disk I/O metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/disk-io-metrics#configuration-parameters) |
| `disk` | `interval_sec` | [Disk I/O metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/disk-io-metrics#configuration-parameters) |
| `disk` | `threaded` | [Disk I/O metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/disk-io-metrics#configuration-parameters) |
| `disk` | `tag` | [Disk I/O metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `docker` | `exclude` | [Docker metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) |
| `docker` | `include` | [Docker metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) |
| `docker` | `interval_nsec` | [Docker metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) |
| `docker` | `interval_sec` | [Docker metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) |
| `docker` | `path.containers` | [Docker metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) |
| `docker` | `path.sysfs` | [Docker metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) |
| `docker` | `threaded` | [Docker metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-metrics#configuration-parameters) |
| `docker` | `tag` | [Docker metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `docker_events` | `buffer_size` | [Docker events](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) |
| `docker_events` | `key` | [Docker events](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) |
| `docker_events` | `parser` | [Docker events](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) |
| `docker_events` | `reconnect.retry_interval` | [Docker events](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) |
| `docker_events` | `reconnect.retry_limits` | [Docker events](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) |
| `docker_events` | `threaded` | [Docker events](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) |
| `docker_events` | `unix_path` | [Docker events](https://docs.fluentbit.io/manual/data-pipeline/inputs/docker-events#configuration-parameters) |
| `docker_events` | `tag` | [Docker events](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `dummy` | `copies` | [Dummy](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `dummy` | [Dummy](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `fixed_timestamp` | [Dummy](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `flush_on_startup` | [Dummy](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `interval_nsec` | [Dummy](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `interval_sec` | [Dummy](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `metadata` | [Dummy](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `rate` | [Dummy](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `samples` | [Dummy](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `start_time_nsec` | [Dummy](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `start_time_sec` | [Dummy](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `test_hang_on_exit` | [Dummy](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `threaded` | [Dummy](https://docs.fluentbit.io/manual/data-pipeline/inputs/dummy#configuration-parameters) |
| `dummy` | `tag` | [Dummy](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `ebpf` | `poll_ms` | [eBPF](https://docs.fluentbit.io/manual/data-pipeline/inputs/ebpf#configuration-parameters) |
| `ebpf` | `ringbuf_map_name` | [eBPF](https://docs.fluentbit.io/manual/data-pipeline/inputs/ebpf#configuration-parameters) |
| `ebpf` | `trace` | [eBPF](https://docs.fluentbit.io/manual/data-pipeline/inputs/ebpf#configuration-parameters) |
| `ebpf` | `tag` | [eBPF](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `elasticsearch` | `buffer_chunk_size` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `buffer_max_size` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `hostname` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `http2` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `http_server.max_connections` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `http_server.workers` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `http_server.ingress_queue_event_limit` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `http_server.ingress_queue_byte_limit` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `listen` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `meta_key` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `port` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `tag_key` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `threaded` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `version` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/inputs/elasticsearch#configuration-parameters) |
| `elasticsearch` | `tag` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `exec` | `buf_size` | [Exec](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) |
| `exec` | `command` | [Exec](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) |
| `exec` | `exit_after_oneshot` | [Exec](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) |
| `exec` | `interval_nsec` | [Exec](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) |
| `exec` | `interval_sec` | [Exec](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) |
| `exec` | `oneshot` | [Exec](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) |
| `exec` | `parser` | [Exec](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) |
| `exec` | `propagate_exit_code` | [Exec](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) |
| `exec` | `threaded` | [Exec](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec#configuration-parameters) |
| `exec` | `tag` | [Exec](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `exec_wasi` | `accessible_paths` | [Exec WASI](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `buf_size` | [Exec WASI](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `interval_nsec` | [Exec WASI](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `interval_sec` | [Exec WASI](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `oneshot` | [Exec WASI](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `parser` | [Exec WASI](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `threaded` | [Exec WASI](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `wasi_path` | [Exec WASI](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `wasm_heap_size` | [Exec WASI](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `wasm_stack_size` | [Exec WASI](https://docs.fluentbit.io/manual/data-pipeline/inputs/exec-wasi#configuration-parameters) |
| `exec_wasi` | `tag` | [Exec WASI](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `fluentbit_logs` | `level` | [Fluent Bit logs](https://docs.fluentbit.io/manual/data-pipeline/inputs/fluentbit-logs#record-format) |
| `fluentbit_logs` | `message` | [Fluent Bit logs](https://docs.fluentbit.io/manual/data-pipeline/inputs/fluentbit-logs#record-format) |
| `fluentbit_logs` | `tag` | [Fluent Bit logs](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `fluentbit_metrics` | `scrape_interval` | [Fluent Bit metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/fluentbit-metrics#configuration-parameters) |
| `fluentbit_metrics` | `scrape_on_start` | [Fluent Bit metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/fluentbit-metrics#configuration-parameters) |
| `fluentbit_metrics` | `threaded` | [Fluent Bit metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/fluentbit-metrics#configuration-parameters) |
| `fluentbit_metrics` | `tag` | [Fluent Bit metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `forward` | `buffer_chunk_size` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) |
| `forward` | `buffer_max_size` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) |
| `forward` | `empty_shared_key` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) |
| `forward` | `listen` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) |
| `forward` | `port` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) |
| `forward` | `security.users` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) |
| `forward` | `self_hostname` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) |
| `forward` | `shared_key` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) |
| `forward` | `tag` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `forward` | `tag_prefix` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) |
| `forward` | `threaded` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) |
| `forward` | `unix_path` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) |
| `forward` | `unix_perm` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/inputs/forward#configuration-parameters) |
| `gpu_metrics` | `cards_exclude` | [GPU metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) |
| `gpu_metrics` | `cards_include` | [GPU metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) |
| `gpu_metrics` | `enable_power` | [GPU metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) |
| `gpu_metrics` | `enable_temperature` | [GPU metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) |
| `gpu_metrics` | `path_sysfs` | [GPU metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) |
| `gpu_metrics` | `scrape_interval` | [GPU metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/gpu-metrics#configuration-parameters) |
| `gpu_metrics` | `tag` | [GPU metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `head` | `add_path` | [Head](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) |
| `head` | `buf_size` | [Head](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) |
| `head` | `file` | [Head](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) |
| `head` | `interval_nsec` | [Head](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) |
| `head` | `interval_sec` | [Head](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) |
| `head` | `key` | [Head](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) |
| `head` | `lines` | [Head](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) |
| `head` | `split_line` | [Head](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) |
| `head` | `threaded` | [Head](https://docs.fluentbit.io/manual/data-pipeline/inputs/head#configuration-parameters) |
| `head` | `tag` | [Head](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `health` | `add_host` | [Health](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) |
| `health` | `add_port` | [Health](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) |
| `health` | `alert` | [Health](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) |
| `health` | `host` | [Health](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) |
| `health` | `interval_nsec` | [Health](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) |
| `health` | `interval_sec` | [Health](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) |
| `health` | `port` | [Health](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) |
| `health` | `threaded` | [Health](https://docs.fluentbit.io/manual/data-pipeline/inputs/health#configuration-parameters) |
| `health` | `tag` | [Health](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `http` | `add_remote_addr` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `buffer_chunk_size` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `buffer_max_size` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `enable_health_endpoint` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `http2` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `http_server.max_connections` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `http_server.workers` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `http_server.ingress_queue_event_limit` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `http_server.ingress_queue_byte_limit` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `listen` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `oauth2.allowed_audience` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `oauth2.allowed_clients` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `oauth2.issuer` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `oauth2.jwks_refresh_interval` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `oauth2.jwks_url` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `oauth2.validate` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `port` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `remote_addr_key` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `success_header` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `successful_response_code` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `tag_key` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `threaded` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/inputs/http#configuration-parameters) |
| `http` | `tag` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `kafka` | `brokers` | [Kafka](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `buffer_max_size` | [Kafka](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `client_id` | [Kafka](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `enable_auto_commit` | [Kafka](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `format` | [Kafka](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `group_id` | [Kafka](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `poll_ms` | [Kafka](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `poll_timeout_ms` | [Kafka](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `rdkafka.{property}` | [Kafka](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `threaded` | [Kafka](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `topics` | [Kafka](https://docs.fluentbit.io/manual/data-pipeline/inputs/kafka#configuration-parameters) |
| `kafka` | `tag` | [Kafka](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `kmsg` | `prio_level` | [Kernel logs](https://docs.fluentbit.io/manual/data-pipeline/inputs/kernel-logs#configuration-parameters) |
| `kmsg` | `threaded` | [Kernel logs](https://docs.fluentbit.io/manual/data-pipeline/inputs/kernel-logs#configuration-parameters) |
| `kmsg` | `tag` | [Kernel logs](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `kubernetes_events` | `db` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `db.journal_mode` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `db.locking` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `db.sync` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `interval_nsec` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `interval_sec` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `kube_ca_file` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `kube_ca_path` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `kube_namespace` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `kube_request_limit` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `kube_retention_time` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `kube_token_file` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `kube_token_ttl` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `kube_url` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `tls.debug` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `tls.verify` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `tls.vhost` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/inputs/kubernetes-events#configuration-parameters) |
| `kubernetes_events` | `tag` | [Kubernetes events](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `mem` | `interval_nsec` | [Memory metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/memory-metrics#configuration-parameters) |
| `mem` | `interval_sec` | [Memory metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/memory-metrics#configuration-parameters) |
| `mem` | `pid` | [Memory metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/memory-metrics#configuration-parameters) |
| `mem` | `threaded` | [Memory metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/memory-metrics#configuration-parameters) |
| `mem` | `tag` | [Memory metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `mqtt` | `buffer_size` | [MQTT](https://docs.fluentbit.io/manual/data-pipeline/inputs/mqtt#configuration-parameters) |
| `mqtt` | `listen` | [MQTT](https://docs.fluentbit.io/manual/data-pipeline/inputs/mqtt#configuration-parameters) |
| `mqtt` | `payload_key` | [MQTT](https://docs.fluentbit.io/manual/data-pipeline/inputs/mqtt#configuration-parameters) |
| `mqtt` | `port` | [MQTT](https://docs.fluentbit.io/manual/data-pipeline/inputs/mqtt#configuration-parameters) |
| `mqtt` | `threaded` | [MQTT](https://docs.fluentbit.io/manual/data-pipeline/inputs/mqtt#configuration-parameters) |
| `mqtt` | `tag` | [MQTT](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `netif` | `interface` | [Network I/O metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) |
| `netif` | `interval_nsec` | [Network I/O metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) |
| `netif` | `interval_sec` | [Network I/O metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) |
| `netif` | `test_at_init` | [Network I/O metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) |
| `netif` | `threaded` | [Network I/O metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) |
| `netif` | `verbose` | [Network I/O metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/network-io-metrics#configuration-parameters) |
| `netif` | `tag` | [Network I/O metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `nginx_metrics` | `host` | [NGINX exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) |
| `nginx_metrics` | `nginx_plus` | [NGINX exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) |
| `nginx_metrics` | `port` | [NGINX exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) |
| `nginx_metrics` | `scrape_interval` | [NGINX exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) |
| `nginx_metrics` | `status_url` | [NGINX exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) |
| `nginx_metrics` | `threaded` | [NGINX exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters) |
| `nginx_metrics` | `tag` | [NGINX exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `node_exporter_metrics` | `collector.cpu.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.cpufreq.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.diskstats.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.filefd.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.filesystem.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.hwmon.chip-exclude` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.hwmon.chip-include` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.hwmon.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.hwmon.sensor-exclude` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.hwmon.sensor-include` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.loadavg.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.meminfo.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.netdev.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.netstat.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.nvme.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.processes.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.sockstat.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.stat.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.systemd.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.textfile.path` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.textfile.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.thermalzone.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.time.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.uname.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `collector.vmstat.scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `diskstats.ignore_device_regex` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `filesystem.ignore_filesystem_type_regex` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `filesystem.ignore_mount_point_regex` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `metrics` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `path.procfs` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `path.rootfs` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `path.sysfs` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `scrape_interval` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `systemd_exclude_pattern` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `systemd_include_pattern` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `systemd_include_service_task_metrics` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `systemd_service_restart_metrics` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `systemd_unit_start_time_metrics` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/node-exporter-metrics#configuration-parameters) |
| `node_exporter_metrics` | `tag` | [Node exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `opentelemetry` | `alias` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `buffer_chunk_size` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `buffer_max_size` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `encode_profiles_as_log` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `host` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `http2` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `http_server.max_connections` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `http_server.workers` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `http_server.ingress_queue_event_limit` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `http_server.ingress_queue_byte_limit` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `listen` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `log_level` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `log_suppress_interval` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `logs_body_key` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `logs_metadata_key` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `mem_buf_limit` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `net.accept_timeout` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `net.accept_timeout_log_error` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `net.backlog` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `net.io_timeout` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `net.keepalive` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `net.share_port` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `oauth2.allowed_audience` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `oauth2.allowed_clients` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `oauth2.issuer` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `oauth2.jwks_refresh_interval` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `oauth2.jwks_url` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `oauth2.validate` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `port` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `profiles_support` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `raw_traces` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `routable` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `storage.pause_on_chunks_overlimit` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `storage.type` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `successful_response_code` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `tag` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `opentelemetry` | `tag_from_uri` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `tag_key` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `thread.ring_buffer.capacity` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `thread.ring_buffer.window` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `threaded` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `tls` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `tls.ca_file` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `tls.ca_path` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `tls.ciphers` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `tls.crt_file` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `tls.debug` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `tls.key_file` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `tls.key_passwd` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `tls.max_version` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `tls.min_version` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `tls.verify` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `tls.verify_hostname` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `opentelemetry` | `tls.vhost` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/inputs/opentelemetry#configuration) |
| `podman_metrics` | `path.config` | [Podman metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) |
| `podman_metrics` | `path.procfs` | [Podman metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) |
| `podman_metrics` | `path.sysfs` | [Podman metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) |
| `podman_metrics` | `scrape_interval` | [Podman metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) |
| `podman_metrics` | `scrape_on_start` | [Podman metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) |
| `podman_metrics` | `threaded` | [Podman metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/podman-metrics#configuration-parameters) |
| `podman_metrics` | `tag` | [Podman metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `proc` | `alert` | [Process metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) |
| `proc` | `fd` | [Process metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) |
| `proc` | `interval_nsec` | [Process metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) |
| `proc` | `interval_sec` | [Process metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) |
| `proc` | `mem` | [Process metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) |
| `proc` | `proc_name` | [Process metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) |
| `proc` | `threaded` | [Process metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/process#configuration-parameters) |
| `proc` | `tag` | [Process metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `process_exporter_metrics` | `metrics` | [Process exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/process-exporter-metrics#configuration) |
| `process_exporter_metrics` | `path.procfs` | [Process exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/process-exporter-metrics#configuration) |
| `process_exporter_metrics` | `process_exclude_pattern` | [Process exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/process-exporter-metrics#configuration) |
| `process_exporter_metrics` | `process_include_pattern` | [Process exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/process-exporter-metrics#configuration) |
| `process_exporter_metrics` | `scrape_interval` | [Process exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/process-exporter-metrics#configuration) |
| `process_exporter_metrics` | `tag` | [Process exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `prometheus-textfile` | `alias` | [Prometheus text file](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) |
| `prometheus-textfile` | `log_level` | [Prometheus text file](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) |
| `prometheus-textfile` | `log_suppress_interval` | [Prometheus text file](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) |
| `prometheus-textfile` | `mem_buf_limit` | [Prometheus text file](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) |
| `prometheus-textfile` | `path` | [Prometheus text file](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) |
| `prometheus-textfile` | `routable` | [Prometheus text file](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) |
| `prometheus-textfile` | `scrape_interval` | [Prometheus text file](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) |
| `prometheus-textfile` | `storage.pause_on_chunks_overlimit` | [Prometheus text file](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) |
| `prometheus-textfile` | `storage.type` | [Prometheus text file](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) |
| `prometheus-textfile` | `tag` | [Prometheus text file](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `prometheus-textfile` | `thread.ring_buffer.capacity` | [Prometheus text file](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) |
| `prometheus-textfile` | `thread.ring_buffer.window` | [Prometheus text file](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) |
| `prometheus-textfile` | `threaded` | [Prometheus text file](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-textfile#configuration-parameters) |
| `prometheus_remote_write` | `buffer_chunk_size` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `buffer_max_size` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `http2` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `http_server.max_connections` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `http_server.workers` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `http_server.ingress_queue_event_limit` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `http_server.ingress_queue_byte_limit` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `listen` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `port` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `successful_response_code` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `tag_from_uri` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `threaded` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `uri` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `tag` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `prometheus_scrape` | `bearer_token` | [Prometheus scrape Metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) |
| `prometheus_scrape` | `buffer_max_size` | [Prometheus scrape Metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) |
| `prometheus_scrape` | `host` | [Prometheus scrape Metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) |
| `prometheus_scrape` | `http_passwd` | [Prometheus scrape Metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) |
| `prometheus_scrape` | `http_user` | [Prometheus scrape Metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) |
| `prometheus_scrape` | `metrics_path` | [Prometheus scrape Metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) |
| `prometheus_scrape` | `port` | [Prometheus scrape Metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) |
| `prometheus_scrape` | `scrape_interval` | [Prometheus scrape Metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) |
| `prometheus_scrape` | `threaded` | [Prometheus scrape Metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/prometheus-scrape-metrics#configuration) |
| `prometheus_scrape` | `tag` | [Prometheus scrape Metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `random` | `interval_nsec` | [Random](https://docs.fluentbit.io/manual/data-pipeline/inputs/random#configuration-parameters) |
| `random` | `interval_sec` | [Random](https://docs.fluentbit.io/manual/data-pipeline/inputs/random#configuration-parameters) |
| `random` | `samples` | [Random](https://docs.fluentbit.io/manual/data-pipeline/inputs/random#configuration-parameters) |
| `random` | `threaded` | [Random](https://docs.fluentbit.io/manual/data-pipeline/inputs/random#configuration-parameters) |
| `random` | `tag` | [Random](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `serial` | `bitrate` | [Serial interface](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) |
| `serial` | `file` | [Serial interface](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) |
| `serial` | `format` | [Serial interface](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) |
| `serial` | `min_bytes` | [Serial interface](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) |
| `serial` | `separator` | [Serial interface](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) |
| `serial` | `threaded` | [Serial interface](https://docs.fluentbit.io/manual/data-pipeline/inputs/serial-interface#configuration-parameters) |
| `serial` | `tag` | [Serial interface](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `splunk` | `add_remote_addr` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `buffer_chunk_size` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `buffer_max_size` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `http2` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `http_server.max_connections` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `http_server.workers` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `http_server.ingress_queue_event_limit` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `http_server.ingress_queue_byte_limit` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `listen` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `port` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `remote_addr_key` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `splunk_token` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `splunk_token_key` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `store_token_in_metadata` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `success_header` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `tag_key` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `threaded` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/inputs/splunk#configuration-parameters) |
| `splunk` | `tag` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `statsd` | `listen` | [StatsD](https://docs.fluentbit.io/manual/data-pipeline/inputs/statsd#configuration-parameters) |
| `statsd` | `metrics` | [StatsD](https://docs.fluentbit.io/manual/data-pipeline/inputs/statsd#configuration-parameters) |
| `statsd` | `port` | [StatsD](https://docs.fluentbit.io/manual/data-pipeline/inputs/statsd#configuration-parameters) |
| `statsd` | `threaded` | [StatsD](https://docs.fluentbit.io/manual/data-pipeline/inputs/statsd#configuration-parameters) |
| `statsd` | `tag` | [StatsD](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `stdin` | `buffer_size` | [Standard input](https://docs.fluentbit.io/manual/data-pipeline/inputs/standard-input#configuration-parameters) |
| `stdin` | `parser` | [Standard input](https://docs.fluentbit.io/manual/data-pipeline/inputs/standard-input#configuration-parameters) |
| `stdin` | `threaded` | [Standard input](https://docs.fluentbit.io/manual/data-pipeline/inputs/standard-input#configuration-parameters) |
| `stdin` | `tag` | [Standard input](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `syslog` | `buffer_chunk_size` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `buffer_max_size` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `format` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `listen` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `mode` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `parser` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `path` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `port` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `raw_message_key` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `receive_buffer_size` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `source_address_key` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `threaded` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `unix_perm` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/inputs/syslog#configuration-parameters) |
| `syslog` | `tag` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `systemd` | `db` | [Systemd](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `db.sync` | [Systemd](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `lowercase` | [Systemd](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `max_entries` | [Systemd](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `max_fields` | [Systemd](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `path` | [Systemd](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `read_from_tail` | [Systemd](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `strip_underscores` | [Systemd](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `systemd_filter` | [Systemd](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `systemd_filter_type` | [Systemd](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) |
| `systemd` | `tag` | [Systemd](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `systemd` | `threaded` | [Systemd](https://docs.fluentbit.io/manual/data-pipeline/inputs/systemd#configuration-parameters) |
| `tail` | `buffer_chunk_size` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `buffer_max_size` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `db` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `db.compare_filename` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `db.journal_mode` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `db.locking` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `db.sync` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `docker_mode` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `docker_mode_flush` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `docker_mode_parser` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `event_batch_size` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `exclude_path` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `exit_on_eof` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `file_cache_advise` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `generic.encoding` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `ignore_active_older_files` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `ignore_older` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `inotify_watcher` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `key` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `mem_buf_limit` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `offset_key` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `parser` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `path` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `path_key` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `progress_check_interval` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `progress_check_interval_nsec` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `read_from_head` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `read_newly_discovered_files_from_head` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `refresh_interval` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `rotate_wait` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `skip_empty_lines` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `skip_long_lines` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `static_batch_size` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `tag` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `tail` | `tag_regex` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `thread.ring_buffer.capacity` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `thread.ring_buffer.window` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `threaded` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `truncate_long_lines` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `unicode.encoding` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tail` | `watcher_interval` | [Tail](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters) |
| `tcp` | `buffer_size` | [TCP](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `chunk_size` | [TCP](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `format` | [TCP](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `listen` | [TCP](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `parser` | [TCP](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `port` | [TCP](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `separator` | [TCP](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `source_address_key` | [TCP](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `threaded` | [TCP](https://docs.fluentbit.io/manual/data-pipeline/inputs/tcp#configuration-parameters) |
| `tcp` | `tag` | [TCP](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `thermal` | `interval_nsec` | [Thermal](https://docs.fluentbit.io/manual/data-pipeline/inputs/thermal#configuration-parameters) |
| `thermal` | `interval_sec` | [Thermal](https://docs.fluentbit.io/manual/data-pipeline/inputs/thermal#configuration-parameters) |
| `thermal` | `name_regex` | [Thermal](https://docs.fluentbit.io/manual/data-pipeline/inputs/thermal#configuration-parameters) |
| `thermal` | `threaded` | [Thermal](https://docs.fluentbit.io/manual/data-pipeline/inputs/thermal#configuration-parameters) |
| `thermal` | `type_regex` | [Thermal](https://docs.fluentbit.io/manual/data-pipeline/inputs/thermal#configuration-parameters) |
| `thermal` | `tag` | [Thermal](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `udp` | `buffer_size` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) |
| `udp` | `chunk_size` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) |
| `udp` | `format` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) |
| `udp` | `listen` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) |
| `udp` | `parser` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) |
| `udp` | `port` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) |
| `udp` | `separator` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) |
| `udp` | `source_address_key` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) |
| `udp` | `threaded` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/inputs/udp#configuration-parameters) |
| `udp` | `tag` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `windows_exporter_metrics` | `scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `enable_collector` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.logical_disk.allow_disk_regex` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.logical_disk.deny_disk_regex` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.net.allow_nic_regex` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.service.where` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.service.include` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.service.exclude` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.process.allow_process_regex` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `we.process.deny_process_regex` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.cpu.scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.net.scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.logical_disk.scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.cs.scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.os.scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.thermalzone.scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.cpu_info.scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.logon.scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.system.scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.service.scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.memory.scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.paging_file.scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.process.scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.tcp.scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `collector.cache.scrape_interval` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `metrics` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-exporter-metrics#configuration) |
| `windows_exporter_metrics` | `tag` | [Windows exporter metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `winevtlog` | `channels` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `db` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `event_query` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `ignore_missing_channels` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `interval_nsec` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `interval_sec` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `read_existing_events` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `read_limit_per_cycle` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `remote.domain` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `remote.password` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `remote.server` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `remote.username` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `reconnect.base_ms` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `reconnect.max_ms` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `reconnect.multiplier` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `reconnect.jitter_pct` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `reconnect.max_retries` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `render_event_as_text` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `render_event_as_xml` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `render_event_text_key` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `string_inserts` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `threaded` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `use_ansi` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log-winevtlog#configuration-parameters) |
| `winevtlog` | `tag` | [Windows Event logs (winevtlog)](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `winlog` | `channels` | [Windows Event logs (winlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) |
| `winlog` | `db` | [Windows Event logs (winlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) |
| `winlog` | `interval_sec` | [Windows Event logs (winlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) |
| `winlog` | `interval_nsec` | [Windows Event logs (winlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) |
| `winlog` | `string_inserts` | [Windows Event logs (winlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) |
| `winlog` | `threaded` | [Windows Event logs (winlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) |
| `winlog` | `use_ansi` | [Windows Event logs (winlog)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-event-log#configuration-parameters) |
| `winlog` | `tag` | [Windows Event logs (winlog)](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `winstat` | `interval_sec` | [Windows System Statistics (winstat)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-system-statistics#configuration-parameters) |
| `winstat` | `interval_nsec` | [Windows System Statistics (winstat)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-system-statistics#configuration-parameters) |
| `winstat` | `threaded` | [Windows System Statistics (winstat)](https://docs.fluentbit.io/manual/data-pipeline/inputs/windows-system-statistics#configuration-parameters) |
| `winstat` | `tag` | [Windows System Statistics (winstat)](https://docs.fluentbit.io/manual/data-pipeline/router) |

## Filters

| Plugin Name | Attribute Name | Fluent Bit Page |
| --- | --- | --- |
| `aws` | `account_id` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `ami_id` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `az` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `ec2_instance_id` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `ec2_instance_type` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `enable_entity` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `hostname` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `imds_version` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `private_ip` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `retry_interval_s` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `tags_enabled` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `tags_exclude` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `tags_include` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `vpc_id` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/aws-metadata#configuration-parameters) |
| `aws` | `match` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `aws` | `match_regex` | [AWS metadata](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `checklist` | `file` | [CheckList](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters) |
| `checklist` | `ignore_case` | [CheckList](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters) |
| `checklist` | `lookup_key` | [CheckList](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters) |
| `checklist` | `mode` | [CheckList](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters) |
| `checklist` | `print_query_time` | [CheckList](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters) |
| `checklist` | `record` | [CheckList](https://docs.fluentbit.io/manual/data-pipeline/filters/checklist#configuration-parameters) |
| `checklist` | `match` | [CheckList](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `checklist` | `match_regex` | [CheckList](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `ecs` | `add` | [ECS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) |
| `ecs` | `agent_endpoint_retries` | [ECS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) |
| `ecs` | `cluster_metadata_only` | [ECS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) |
| `ecs` | `ecs_meta_cache_ttl` | [ECS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) |
| `ecs` | `ecs_meta_host` | [ECS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) |
| `ecs` | `ecs_meta_port` | [ECS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) |
| `ecs` | `ecs_tag_prefix` | [ECS metadata](https://docs.fluentbit.io/manual/data-pipeline/filters/ecs-metadata#configuration-parameters) |
| `ecs` | `match` | [ECS metadata](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `ecs` | `match_regex` | [ECS metadata](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `expect` | `action` | [Expect](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) |
| `expect` | `key_exists` | [Expect](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) |
| `expect` | `key_not_exists` | [Expect](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) |
| `expect` | `key_val_eq` | [Expect](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) |
| `expect` | `key_val_is_not_null` | [Expect](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) |
| `expect` | `key_val_is_null` | [Expect](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) |
| `expect` | `result_key` | [Expect](https://docs.fluentbit.io/manual/data-pipeline/filters/expect#configuration-parameters) |
| `expect` | `match` | [Expect](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `expect` | `match_regex` | [Expect](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `geoip2` | `database` | [GeoIP2 filter](https://docs.fluentbit.io/manual/data-pipeline/filters/geoip2-filter#configuration-parameters) |
| `geoip2` | `lookup_key` | [GeoIP2 filter](https://docs.fluentbit.io/manual/data-pipeline/filters/geoip2-filter#configuration-parameters) |
| `geoip2` | `record` | [GeoIP2 filter](https://docs.fluentbit.io/manual/data-pipeline/filters/geoip2-filter#configuration-parameters) |
| `geoip2` | `match` | [GeoIP2 filter](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `geoip2` | `match_regex` | [GeoIP2 filter](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `grep` | `exclude` | [Grep](https://docs.fluentbit.io/manual/data-pipeline/filters/grep#configuration-parameters) |
| `grep` | `logical_op` | [Grep](https://docs.fluentbit.io/manual/data-pipeline/filters/grep#configuration-parameters) |
| `grep` | `regex` | [Grep](https://docs.fluentbit.io/manual/data-pipeline/filters/grep#configuration-parameters) |
| `grep` | `match` | [Grep](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `grep` | `match_regex` | [Grep](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `kubernetes` | `annotations` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `aws_pod_association_endpoint` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `aws_pod_association_host` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `aws_pod_association_host_client_cert_file` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `aws_pod_association_host_client_key_file` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `aws_pod_association_host_server_ca_file` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `aws_pod_association_host_tls_debug` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `aws_pod_association_host_tls_verify` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `aws_pod_association_port` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `aws_pod_service_map_refresh_interval` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `aws_pod_service_map_ttl` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `aws_pod_service_preload_cache_dir` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `aws_use_pod_association` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `buffer_size` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `cache_use_docker_id` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `dns_retries` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `dns_wait_time` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `dummy_meta` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `k8s-logging.exclude` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `k8s-logging.parser` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `keep_log` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_ca_file` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_ca_path` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_meta_cache_ttl` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_meta_namespace_cache_ttl` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_meta_preload_cache_dir` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_tag_prefix` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_token_command` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_token_file` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_token_ttl` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kube_url` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kubelet_host` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `kubelet_port` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `labels` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `merge_log` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `merge_log_key` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `merge_log_trim` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `merge_parser` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `namespace_annotations` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `namespace_labels` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `namespace_metadata_only` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `owner_references` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `regex_parser` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `set_platform` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `tls.debug` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `tls.verify` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `tls.verify_hostname` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `tls.vhost` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `use_journal` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `use_kubelet` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `use_pod_association` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `use_tag_for_meta` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes#configuration-parameters) |
| `kubernetes` | `match` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `kubernetes` | `match_regex` | [Kubernetes](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `log_to_metrics` | `add_label` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `bucket` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `discard_logs` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `emitter_mem_buf_limit` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `emitter_name` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `exclude` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `flush_interval_nsec` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `flush_interval_sec` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `kubernetes_mode` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `label_field` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `metric_description` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `metric_mode` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `metric_name` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `metric_namespace` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `metric_subsystem` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `regex` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `tag` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `value_field` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics#configuration-parameters) |
| `log_to_metrics` | `match` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `log_to_metrics` | `match_regex` | [Logs to metrics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `lua` | `call` | [Lua](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) |
| `lua` | `code` | [Lua](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) |
| `lua` | `enable_flb_null` | [Lua](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) |
| `lua` | `protected_mode` | [Lua](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) |
| `lua` | `script` | [Lua](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) |
| `lua` | `time_as_table` | [Lua](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) |
| `lua` | `type_array_key` | [Lua](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) |
| `lua` | `type_int_key` | [Lua](https://docs.fluentbit.io/manual/data-pipeline/filters/lua#configuration-parameters) |
| `lua` | `match` | [Lua](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `lua` | `match_regex` | [Lua](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `modify` | `set` | [Modify](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) |
| `modify` | `add` | [Modify](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) |
| `modify` | `remove` | [Modify](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) |
| `modify` | `remove_wildcard` | [Modify](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) |
| `modify` | `remove_regex` | [Modify](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) |
| `modify` | `rename` | [Modify](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) |
| `modify` | `hard_rename` | [Modify](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) |
| `modify` | `copy` | [Modify](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) |
| `modify` | `hard_copy` | [Modify](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) |
| `modify` | `move_to_start` | [Modify](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) |
| `modify` | `move_to_end` | [Modify](https://docs.fluentbit.io/manual/data-pipeline/filters/modify#configuration-parameters) |
| `modify` | `match` | [Modify](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `modify` | `match_regex` | [Modify](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `multiline` | `buffer` | [Multiline](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `debug_flush` | [Multiline](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `emitter_mem_buf_limit` | [Multiline](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `emitter_name` | [Multiline](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `emitter_storage.type` | [Multiline](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `flush_ms` | [Multiline](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `mode` | [Multiline](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `multiline.key_content` | [Multiline](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `multiline.parser` | [Multiline](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace#configuration-parameters) |
| `multiline` | `match` | [Multiline](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `multiline` | `match_regex` | [Multiline](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `nest` | `add_prefix` | [Nest](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters) |
| `nest` | `nest_under` | [Nest](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters) |
| `nest` | `nested_under` | [Nest](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters) |
| `nest` | `operation` | [Nest](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters) |
| `nest` | `remove_prefix` | [Nest](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters) |
| `nest` | `wildcard` | [Nest](https://docs.fluentbit.io/manual/data-pipeline/filters/nest#configuration-parameters) |
| `nest` | `match` | [Nest](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `nest` | `match_regex` | [Nest](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `nightfall` | `nightfall_api_key` | [Nightfall](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) |
| `nightfall` | `policy_id` | [Nightfall](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) |
| `nightfall` | `sampling_rate` | [Nightfall](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) |
| `nightfall` | `tls.ca_path` | [Nightfall](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) |
| `nightfall` | `tls.debug` | [Nightfall](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) |
| `nightfall` | `tls.verify` | [Nightfall](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) |
| `nightfall` | `tls.vhost` | [Nightfall](https://docs.fluentbit.io/manual/data-pipeline/filters/nightfall#configuration-parameters) |
| `nightfall` | `match` | [Nightfall](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `nightfall` | `match_regex` | [Nightfall](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `parser` | `key_name` | [Parser](https://docs.fluentbit.io/manual/data-pipeline/filters/parser#configuration-parameters) |
| `parser` | `parser` | [Parser](https://docs.fluentbit.io/manual/data-pipeline/filters/parser#configuration-parameters) |
| `parser` | `preserve_key` | [Parser](https://docs.fluentbit.io/manual/data-pipeline/filters/parser#configuration-parameters) |
| `parser` | `reserve_data` | [Parser](https://docs.fluentbit.io/manual/data-pipeline/filters/parser#configuration-parameters) |
| `parser` | `unescape_key` | [Parser](https://docs.fluentbit.io/manual/data-pipeline/filters/parser#configuration-parameters) |
| `parser` | `match` | [Parser](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `parser` | `match_regex` | [Parser](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `record_modifier` | `allowlist_key` | [Record modifier](https://docs.fluentbit.io/manual/data-pipeline/filters/record-modifier#configuration-parameters) |
| `record_modifier` | `record` | [Record modifier](https://docs.fluentbit.io/manual/data-pipeline/filters/record-modifier#configuration-parameters) |
| `record_modifier` | `remove_key` | [Record modifier](https://docs.fluentbit.io/manual/data-pipeline/filters/record-modifier#configuration-parameters) |
| `record_modifier` | `uuid_key` | [Record modifier](https://docs.fluentbit.io/manual/data-pipeline/filters/record-modifier#configuration-parameters) |
| `record_modifier` | `whitelist_key` | [Record modifier](https://docs.fluentbit.io/manual/data-pipeline/filters/record-modifier#configuration-parameters) |
| `record_modifier` | `match` | [Record modifier](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `record_modifier` | `match_regex` | [Record modifier](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `rewrite_tag` | `emitter_mem_buf_limit` | [Rewrite tag](https://docs.fluentbit.io/manual/data-pipeline/filters/rewrite-tag#configuration-parameters) |
| `rewrite_tag` | `emitter_name` | [Rewrite tag](https://docs.fluentbit.io/manual/data-pipeline/filters/rewrite-tag#configuration-parameters) |
| `rewrite_tag` | `emitter_storage.type` | [Rewrite tag](https://docs.fluentbit.io/manual/data-pipeline/filters/rewrite-tag#configuration-parameters) |
| `rewrite_tag` | `rule` | [Rewrite tag](https://docs.fluentbit.io/manual/data-pipeline/filters/rewrite-tag#configuration-parameters) |
| `rewrite_tag` | `match` | [Rewrite tag](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `rewrite_tag` | `match_regex` | [Rewrite tag](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `stdout` | `match` | [Standard output](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `stdout` | `match_regex` | [Standard output](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `sysinfo` | `fluentbit_version_key` | [Sysinfo](https://docs.fluentbit.io/manual/data-pipeline/filters/sysinfo#configuration-parameters) |
| `sysinfo` | `hostname_key` | [Sysinfo](https://docs.fluentbit.io/manual/data-pipeline/filters/sysinfo#configuration-parameters) |
| `sysinfo` | `kernel_version_key` | [Sysinfo](https://docs.fluentbit.io/manual/data-pipeline/filters/sysinfo#configuration-parameters) |
| `sysinfo` | `os_name_key` | [Sysinfo](https://docs.fluentbit.io/manual/data-pipeline/filters/sysinfo#configuration-parameters) |
| `sysinfo` | `os_version_key` | [Sysinfo](https://docs.fluentbit.io/manual/data-pipeline/filters/sysinfo#configuration-parameters) |
| `sysinfo` | `match` | [Sysinfo](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `sysinfo` | `match_regex` | [Sysinfo](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `tensorflow` | `include_input_fields` | [Tensorflow](https://docs.fluentbit.io/manual/data-pipeline/filters/tensorflow#configuration-parameters) |
| `tensorflow` | `input_field` | [Tensorflow](https://docs.fluentbit.io/manual/data-pipeline/filters/tensorflow#configuration-parameters) |
| `tensorflow` | `model_file` | [Tensorflow](https://docs.fluentbit.io/manual/data-pipeline/filters/tensorflow#configuration-parameters) |
| `tensorflow` | `normalization_value` | [Tensorflow](https://docs.fluentbit.io/manual/data-pipeline/filters/tensorflow#configuration-parameters) |
| `tensorflow` | `match` | [Tensorflow](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `tensorflow` | `match_regex` | [Tensorflow](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `throttle` | `interval` | [Throttle](https://docs.fluentbit.io/manual/data-pipeline/filters/throttle#configuration-parameters) |
| `throttle` | `print_status` | [Throttle](https://docs.fluentbit.io/manual/data-pipeline/filters/throttle#configuration-parameters) |
| `throttle` | `rate` | [Throttle](https://docs.fluentbit.io/manual/data-pipeline/filters/throttle#configuration-parameters) |
| `throttle` | `window` | [Throttle](https://docs.fluentbit.io/manual/data-pipeline/filters/throttle#configuration-parameters) |
| `throttle` | `match` | [Throttle](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `throttle` | `match_regex` | [Throttle](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `type_converter` | `float_key` | [Type converter](https://docs.fluentbit.io/manual/data-pipeline/filters/type-converter#configuration-parameters) |
| `type_converter` | `int_key` | [Type converter](https://docs.fluentbit.io/manual/data-pipeline/filters/type-converter#configuration-parameters) |
| `type_converter` | `str_key` | [Type converter](https://docs.fluentbit.io/manual/data-pipeline/filters/type-converter#configuration-parameters) |
| `type_converter` | `uint_key` | [Type converter](https://docs.fluentbit.io/manual/data-pipeline/filters/type-converter#configuration-parameters) |
| `type_converter` | `match` | [Type converter](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `type_converter` | `match_regex` | [Type converter](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `wasm` | `accessible_paths` | [Wasm](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters) |
| `wasm` | `event_format` | [Wasm](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters) |
| `wasm` | `function_name` | [Wasm](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters) |
| `wasm` | `wasm_heap_size` | [Wasm](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters) |
| `wasm` | `wasm_path` | [Wasm](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters) |
| `wasm` | `wasm_stack_size` | [Wasm](https://docs.fluentbit.io/manual/data-pipeline/filters/wasm#configuration-parameters) |
| `wasm` | `match` | [Wasm](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `wasm` | `match_regex` | [Wasm](https://docs.fluentbit.io/manual/data-pipeline/router) |

## Outputs

| Plugin Name | Attribute Name | Fluent Bit Page |
| --- | --- | --- |
| `azure` | `customer_id` | [Azure Log Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) |
| `azure` | `log_type` | [Azure Log Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) |
| `azure` | `log_type_key` | [Azure Log Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) |
| `azure` | `shared_key` | [Azure Log Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) |
| `azure` | `time_generated` | [Azure Log Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) |
| `azure` | `time_key` | [Azure Log Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) |
| `azure` | `workers` | [Azure Log Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure#configuration-parameters) |
| `azure` | `match` | [Azure Log Analytics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `azure` | `match_regex` | [Azure Log Analytics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `azure_blob` | `account_name` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `auth_type` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `auto_create_container` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `azure_blob_buffer_key` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `blob_type` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `blob_uri_length` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `buffer_dir` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `buffer_file_delete_early` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `buffering_enabled` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `compress` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `compress_blob` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `configuration_endpoint_bearer_token` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `configuration_endpoint_password` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `configuration_endpoint_url` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `configuration_endpoint_username` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `container_name` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `database_file` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `date_key` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `delete_on_max_upload_error` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `emulator_mode` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `endpoint` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `file_delivery_attempt_limit` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `io_timeout` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `part_delivery_attempt_limit` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `part_size` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `path` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `sas_token` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `scheduler_max_retries` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `shared_key` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `store_dir_limit_size` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `tls` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `unify_tag` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `upload_file_size` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `upload_part_freshness_limit` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `upload_parts_timeout` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `upload_timeout` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `workers` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_blob#configuration-parameters) |
| `azure_blob` | `match` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `azure_blob` | `match_regex` | [Azure Blob](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `azure_kusto` | `alias` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `auth_type` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `azure_kusto_buffer_key` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `blob_uri_length` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `buffer_dir` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `buffer_file_delete_early` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `buffering_enabled` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `client_id` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `client_secret` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `compression_enabled` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `database_name` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `delete_on_max_upload_error` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `host` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `include_tag_key` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `include_time_key` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `ingestion_endpoint` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `ingestion_endpoint_connect_timeout` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `ingestion_mapping_reference` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `ingestion_resources_refresh_interval` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `io_timeout` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `log_key` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `log_level` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `log_supress_interval` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `match` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `match_regex` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.connect_timeout` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.connect_timeout_log_error` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.dns.mode` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.dns.prefer_ipv4` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.dns.prefer_ipv6` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.dns.resolver` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.io_timeout` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.keepalive` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.keepalive_idle_timeout` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.keepalive_max_recycle` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.max_worker_connections` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.proxy_env_ignore` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.source_address` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.tcp_keepalive` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.tcp_keepalive_interval` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.tcp_keepalive_probes` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `net.tcp_keepalive_time` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `port` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `retry_limit` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `scheduler_max_retries` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `store_dir_limit_size` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `table_name` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tag_key` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tenant_id` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `time_key` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tls` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tls.ca_file` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tls.ca_path` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tls.ciphers` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tls.crt_file` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tls.debug` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tls.key_file` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tls.key_passwd` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tls.max_version` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tls.min_version` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tls.verify` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tls.verify_hostname` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tls.vhost` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tls.windows.certstore_name` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `tls.windows.use_enterprise_store` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `unify_tag` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `upload_file_size` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `upload_timeout` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_kusto` | `workload_identity_token_file` | [Azure Data Explorer](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_kusto#configuration-parameters) |
| `azure_logs_ingestion` | `auth_url` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `client_id` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `client_secret` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `compress` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `dce_url` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `dcr_id` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `table_name` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `tenant_id` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `time_generated` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `time_key` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `workers` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/data-pipeline/outputs/azure_logs_ingestion#configuration-parameters) |
| `azure_logs_ingestion` | `match` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `azure_logs_ingestion` | `match_regex` | [Azure Logs Ingestion API](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `bigquery` | `aws_region` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) |
| `bigquery` | `dataset_id` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) |
| `bigquery` | `enable_identity_federation` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) |
| `bigquery` | `google_service_account` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) |
| `bigquery` | `google_service_credentials` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) |
| `bigquery` | `ignore_unknown_values` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) |
| `bigquery` | `pool_id` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) |
| `bigquery` | `project_id` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) |
| `bigquery` | `project_number` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) |
| `bigquery` | `provider_id` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) |
| `bigquery` | `service_account_email` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) |
| `bigquery` | `service_account_secret` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) |
| `bigquery` | `skip_invalid_rows` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) |
| `bigquery` | `table_id` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) |
| `bigquery` | `workers` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/outputs/bigquery#configuration-parameters) |
| `bigquery` | `match` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `bigquery` | `match_regex` | [Google Cloud BigQuery](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `chronicle` | `customer_id` | [Google Chronicle](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) |
| `chronicle` | `google_service_credentials` | [Google Chronicle](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) |
| `chronicle` | `log_key` | [Google Chronicle](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) |
| `chronicle` | `log_type` | [Google Chronicle](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) |
| `chronicle` | `project_id` | [Google Chronicle](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) |
| `chronicle` | `region` | [Google Chronicle](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) |
| `chronicle` | `service_account_email` | [Google Chronicle](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) |
| `chronicle` | `service_account_secret` | [Google Chronicle](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) |
| `chronicle` | `workers` | [Google Chronicle](https://docs.fluentbit.io/manual/data-pipeline/outputs/chronicle#configuration-parameters) |
| `chronicle` | `match` | [Google Chronicle](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `chronicle` | `match_regex` | [Google Chronicle](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `cloudwatch_logs` | `add_entity` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `alias` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `auto_create_group` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `auto_retry_requests` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `endpoint` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `external_id` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `extra_user_agent` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_format` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_group_class` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_group_name` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_group_template` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_key` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_level` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_retention_days` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_stream_name` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_stream_prefix` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_stream_template` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `log_suppress_interval` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `match` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `match_regex` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `metric_dimensions` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `metric_namespace` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `profile` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `region` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `retry_limit` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `role_arn` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `sts_endpoint` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `tls.windows.certstore_name` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `tls.windows.use_enterprise_store` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `cloudwatch_logs` | `workers` | [Amazon CloudWatch](https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch#configuration-parameters) |
| `counter` | `match` | [Counter](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `counter` | `match_regex` | [Counter](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `dash0` | `header` | [Dash0](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) |
| `dash0` | `host` | [Dash0](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) |
| `dash0` | `logs_uri` | [Dash0](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) |
| `dash0` | `metrics_uri` | [Dash0](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) |
| `dash0` | `port` | [Dash0](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) |
| `dash0` | `traces_uri` | [Dash0](https://docs.fluentbit.io/manual/data-pipeline/outputs/dash0#configuration-parameters) |
| `dash0` | `match` | [Dash0](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `dash0` | `match_regex` | [Dash0](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `datadog` | `apikey` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `compress` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `dd_hostname` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `dd_message_key` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `dd_service` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `dd_source` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `dd_tags` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `header` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `host` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `include_tag_key` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `json_date_key` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `provider` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `proxy` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `tag_key` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `tls` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `workers` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/outputs/datadog#configuration-parameters) |
| `datadog` | `match` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `datadog` | `match_regex` | [Datadog](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `dynatrace` | `allow_duplicated_headers` | [Dynatrace](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `format` | [Dynatrace](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `header` | [Dynatrace](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `host` | [Dynatrace](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `json_date_format` | [Dynatrace](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `json_date_key` | [Dynatrace](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `port` | [Dynatrace](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `tls` | [Dynatrace](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `tls.verify` | [Dynatrace](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `uri` | [Dynatrace](https://docs.fluentbit.io/manual/data-pipeline/outputs/dynatrace#configuration-parameters) |
| `dynatrace` | `match` | [Dynatrace](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `dynatrace` | `match_regex` | [Dynatrace](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `es` | `aws_auth` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `aws_external_id` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `aws_profile` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `aws_region` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `aws_role_arn` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `aws_service_name` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `aws_sts_endpoint` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `buffer_size` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `cloud_auth` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `cloud_id` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `compress` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `current_time_index` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `generate_id` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `host` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `http_api_key` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `http_passwd` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `http_user` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `id_key` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `include_tag_key` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `index` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `logstash_dateformat` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `logstash_format` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `logstash_prefix` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `logstash_prefix_key` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `logstash_prefix_separator` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `path` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `pipeline` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `port` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `replace_dots` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `suppress_type_name` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `tag_key` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `time_key` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `time_key_format` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `time_key_nanos` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `trace_error` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `trace_output` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `type` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `workers` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `write_operation` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch#configuration-parameters) |
| `es` | `match` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `es` | `match_regex` | [Elasticsearch](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `exit` | `flush_count` | [Exit](https://docs.fluentbit.io/manual/data-pipeline/outputs/exit#configuration-parameters) |
| `exit` | `record_count` | [Exit](https://docs.fluentbit.io/manual/data-pipeline/outputs/exit#configuration-parameters) |
| `exit` | `time_count` | [Exit](https://docs.fluentbit.io/manual/data-pipeline/outputs/exit#configuration-parameters) |
| `exit` | `match` | [Exit](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `exit` | `match_regex` | [Exit](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `file` | `file` | [File](https://docs.fluentbit.io/manual/data-pipeline/outputs/file#configuration-parameters) |
| `file` | `format` | [File](https://docs.fluentbit.io/manual/data-pipeline/outputs/file#configuration-parameters) |
| `file` | `mkdir` | [File](https://docs.fluentbit.io/manual/data-pipeline/outputs/file#configuration-parameters) |
| `file` | `path` | [File](https://docs.fluentbit.io/manual/data-pipeline/outputs/file#configuration-parameters) |
| `file` | `workers` | [File](https://docs.fluentbit.io/manual/data-pipeline/outputs/file#configuration-parameters) |
| `file` | `match` | [File](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `file` | `match_regex` | [File](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `flowcounter` | `event_based` | [Flow counter](https://docs.fluentbit.io/manual/data-pipeline/outputs/flowcounter#configuration-parameters) |
| `flowcounter` | `unit` | [Flow counter](https://docs.fluentbit.io/manual/data-pipeline/outputs/flowcounter#configuration-parameters) |
| `flowcounter` | `workers` | [Flow counter](https://docs.fluentbit.io/manual/data-pipeline/outputs/flowcounter#configuration-parameters) |
| `flowcounter` | `match` | [Flow counter](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `flowcounter` | `match_regex` | [Flow counter](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `forward` | `host` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) |
| `forward` | `port` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) |
| `forward` | `time_as_integer` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) |
| `forward` | `upstream` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) |
| `forward` | `unix_path` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) |
| `forward` | `tag` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) |
| `forward` | `send_options` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) |
| `forward` | `require_ack_response` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) |
| `forward` | `compress` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) |
| `forward` | `fluentd_compat` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) |
| `forward` | `retain_metadata_in_forward_mode` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) |
| `forward` | `add_option` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) |
| `forward` | `workers` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/outputs/forward#configuration-parameters) |
| `forward` | `match` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `forward` | `match_regex` | [Forward](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `gelf` | `compress` | [Graylog Extended Log Format (GELF)](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `gelf_full_message_key` | [Graylog Extended Log Format (GELF)](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `gelf_host_key` | [Graylog Extended Log Format (GELF)](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `gelf_level_key` | [Graylog Extended Log Format (GELF)](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `gelf_short_message_key` | [Graylog Extended Log Format (GELF)](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `gelf_tag_key` | [Graylog Extended Log Format (GELF)](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `gelf_timestamp_key` | [Graylog Extended Log Format (GELF)](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `host` | [Graylog Extended Log Format (GELF)](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `match` | [Graylog Extended Log Format (GELF)](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `mode` | [Graylog Extended Log Format (GELF)](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `packet_size` | [Graylog Extended Log Format (GELF)](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `port` | [Graylog Extended Log Format (GELF)](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `workers` | [Graylog Extended Log Format (GELF)](https://docs.fluentbit.io/manual/data-pipeline/outputs/gelf#configuration-parameters) |
| `gelf` | `match_regex` | [Graylog Extended Log Format (GELF)](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `http` | `allow_duplicated_headers` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `aws_auth` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `aws_external_id` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `aws_profile` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `aws_region` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `aws_role_arn` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `aws_service` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `aws_sts_endpoint` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `body_key` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `compress` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `format` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `gelf_full_message_key` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `gelf_host_key` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `gelf_level_key` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `gelf_short_message_key` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `gelf_timestamp_key` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `header` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `header_tag` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `headers_key` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `host` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `http.read_idle_timeout` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `http.response_timeout` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `http_method` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `http_passwd` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `http_user` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `json_date_format` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `json_date_key` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `log_response_payload` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.audience` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.auth_method` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.client_id` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.client_secret` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.connect_timeout` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.enable` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.jwt_aud` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.jwt_cert_file` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.jwt_header` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.jwt_key_file` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.jwt_ttl_seconds` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.refresh_skew_seconds` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.resource` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.scope` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.timeout` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `oauth2.token_url` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `port` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `proxy` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `uri` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `workers` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/outputs/http#configuration-parameters) |
| `http` | `match` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `http` | `match_regex` | [HTTP](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `influxdb` | `add_integer_suffix` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `auto_tags` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `bucket` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `database` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `host` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `http_header` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `http_passwd` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `http_token` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `http_user` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `org` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `port` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `sequence_tag` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `tag_keys` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `uri` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `workers` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/outputs/influxdb#configuration-parameters) |
| `influxdb` | `match` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `influxdb` | `match_regex` | [InfluxDB](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `kafka` | `aws_msk_iam` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `aws_msk_iam_cluster_arn` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `brokers` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `client_id` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `dynamic_topic` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `format` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `gelf_full_message_key` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `gelf_host_key` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `gelf_level_key` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `gelf_short_message_key` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `gelf_timestamp_key` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `group_id` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `message_key` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `message_key_field` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `queue_full_retries` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `raw_log_key` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `rdkafka.{property}` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `schema_id` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `schema_str` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `timestamp_format` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `timestamp_key` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `topic_key` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `topics` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `workers` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka#configuration-parameters) |
| `kafka` | `match` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `kafka` | `match_regex` | [Kafka Producer](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `kafka-rest` | `avro_http_header` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `host` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `include_tag_key` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `message_key` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `partition` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `port` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `tag_key` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `time_key` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `time_key_format` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `topic` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `url_path` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `workers` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/data-pipeline/outputs/kafka-rest-proxy#configuration-parameters) |
| `kafka-rest` | `match` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `kafka-rest` | `match_regex` | [Kafka REST Proxy](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `kinesis_firehose` | `auto_retry_requests` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `compression` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `delivery_stream` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `endpoint` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `external_id` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `log_key` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `profile` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `region` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `role_arn` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `simple_aggregation` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `sts_endpoint` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `time_key` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `time_key_format` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `workers` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/outputs/firehose#configuration-parameters) |
| `kinesis_firehose` | `match` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `kinesis_firehose` | `match_regex` | [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `kinesis_streams` | `auto_retry_requests` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `compression` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `endpoint` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `external_id` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `log_key` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `port` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `profile` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `region` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `role_arn` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `simple_aggregation` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `stream` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `sts_endpoint` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `time_key` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `time_key_format` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `workers` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/outputs/kinesis#configuration-parameters) |
| `kinesis_streams` | `match` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `kinesis_streams` | `match_regex` | [Amazon Kinesis Data Streams](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `logdna` | `api_key` | [LogDNA](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `app` | [LogDNA](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `file` | [LogDNA](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `hostname` | [LogDNA](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `ip` | [LogDNA](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `logdna_endpoint` | [LogDNA](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `logdna_host` | [LogDNA](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `logdna_port` | [LogDNA](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `mac` | [LogDNA](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `tags` | [LogDNA](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `workers` | [LogDNA](https://docs.fluentbit.io/manual/data-pipeline/outputs/logdna#configuration-parameters) |
| `logdna` | `match` | [LogDNA](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `logdna` | `match_regex` | [LogDNA](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `loki` | `host` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `uri` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `port` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `tls` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `http_user` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `http_passwd` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `bearer_token` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `header` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `tenant_id` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `labels` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `label_keys` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `label_map_path` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `structured_metadata` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `structured_metadata_map_keys` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `remove_keys` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `drop_single_key` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `line_format` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `auto_kubernetes_labels` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `tenant_id_key` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `buffer_size` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `compress` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `workers` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki#configuration-parameters) |
| `loki` | `match` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `loki` | `match_regex` | [Loki](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `nats` | `host` | [NATS](https://docs.fluentbit.io/manual/data-pipeline/outputs/nats#configuration-parameters) |
| `nats` | `port` | [NATS](https://docs.fluentbit.io/manual/data-pipeline/outputs/nats#configuration-parameters) |
| `nats` | `workers` | [NATS](https://docs.fluentbit.io/manual/data-pipeline/outputs/nats#configuration-parameters) |
| `nats` | `match` | [NATS](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `nats` | `match_regex` | [NATS](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `nrlogs` | `api_key` | [New Relic](https://docs.fluentbit.io/manual/data-pipeline/outputs/new-relic#configuration-parameters) |
| `nrlogs` | `base_uri` | [New Relic](https://docs.fluentbit.io/manual/data-pipeline/outputs/new-relic#configuration-parameters) |
| `nrlogs` | `compress` | [New Relic](https://docs.fluentbit.io/manual/data-pipeline/outputs/new-relic#configuration-parameters) |
| `nrlogs` | `license_key` | [New Relic](https://docs.fluentbit.io/manual/data-pipeline/outputs/new-relic#configuration-parameters) |
| `nrlogs` | `workers` | [New Relic](https://docs.fluentbit.io/manual/data-pipeline/outputs/new-relic#configuration-parameters) |
| `nrlogs` | `match` | [New Relic](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `nrlogs` | `match_regex` | [New Relic](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `null` | `format` | [Null](https://docs.fluentbit.io/manual/data-pipeline/outputs/null#configuration-parameters) |
| `null` | `json_date_format` | [Null](https://docs.fluentbit.io/manual/data-pipeline/outputs/null#configuration-parameters) |
| `null` | `json_date_key` | [Null](https://docs.fluentbit.io/manual/data-pipeline/outputs/null#configuration-parameters) |
| `null` | `workers` | [Null](https://docs.fluentbit.io/manual/data-pipeline/outputs/null#configuration-parameters) |
| `null` | `match` | [Null](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `null` | `match_regex` | [Null](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `observe` | `compress` | [Observe](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) |
| `observe` | `format` | [Observe](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) |
| `observe` | `header` | [Observe](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) |
| `observe` | `host` | [Observe](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) |
| `observe` | `port` | [Observe](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) |
| `observe` | `tls` | [Observe](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) |
| `observe` | `tls.ca_file` | [Observe](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) |
| `observe` | `uri` | [Observe](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) |
| `observe` | `workers` | [Observe](https://docs.fluentbit.io/manual/data-pipeline/outputs/observe#configuration-parameters) |
| `observe` | `match` | [Observe](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `observe` | `match_regex` | [Observe](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `openobserve` | `compress` | [OpenObserve](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) |
| `openobserve` | `format` | [OpenObserve](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) |
| `openobserve` | `host` | [OpenObserve](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) |
| `openobserve` | `http_passwd` | [OpenObserve](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) |
| `openobserve` | `http_user` | [OpenObserve](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) |
| `openobserve` | `include_tag_key` | [OpenObserve](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) |
| `openobserve` | `json_date_format` | [OpenObserve](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) |
| `openobserve` | `json_date_key` | [OpenObserve](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) |
| `openobserve` | `tls` | [OpenObserve](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) |
| `openobserve` | `uri` | [OpenObserve](https://docs.fluentbit.io/manual/data-pipeline/outputs/openobserve#configuration-parameters) |
| `openobserve` | `match` | [OpenObserve](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `openobserve` | `match_regex` | [OpenObserve](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `opensearch` | `aws_auth` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `aws_external_id` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `aws_profile` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `aws_region` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `aws_role_arn` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `aws_service_name` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `aws_sts_endpoint` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `buffer_size` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `compress` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `current_time_index` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `generate_id` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `host` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `http_passwd` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `http_user` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `id_key` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `include_tag_key` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `index` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `logstash_dateformat` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `logstash_format` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `logstash_prefix` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `logstash_prefix_key` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `logstash_prefix_separator` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `path` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `pipeline` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `port` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `replace_dots` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `suppress_type_name` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `tag_key` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `time_key` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `time_key_format` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `time_key_nanos` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `trace_error` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `trace_output` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `type` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `workers` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `write_operation` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/outputs/opensearch#configuration-parameters) |
| `opensearch` | `match` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `opensearch` | `match_regex` | [OpenSearch](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `opentelemetry` | `match` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `opentelemetry` | `match_regex` | [OpenTelemetry](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `oracle_log_analytics` | `config_file_location` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `namespace` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `oci_config_in_record` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `oci_la_entity_id` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `oci_la_entity_type` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `oci_la_global_metadata` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `oci_la_log_group_id` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `oci_la_log_path` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `oci_la_log_set_id` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `oci_la_log_source_name` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `oci_la_metadata` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `profile_name` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `proxy` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `uri` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `workers` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/outputs/oci-logging-analytics#configuration-parameters) |
| `oracle_log_analytics` | `match` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `oracle_log_analytics` | `match_regex` | [Oracle Cloud Infrastructure Logging Analytics](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `parseable` | `add_label` | [Parseable](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) |
| `parseable` | `header` | [Parseable](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) |
| `parseable` | `host` | [Parseable](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) |
| `parseable` | `http_passwd` | [Parseable](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) |
| `parseable` | `http_user` | [Parseable](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) |
| `parseable` | `log_response_payload` | [Parseable](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) |
| `parseable` | `logs_uri` | [Parseable](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) |
| `parseable` | `metrics_uri` | [Parseable](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) |
| `parseable` | `port` | [Parseable](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) |
| `parseable` | `tls` | [Parseable](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) |
| `parseable` | `traces_uri` | [Parseable](https://docs.fluentbit.io/manual/data-pipeline/outputs/parseable#configuration-parameters) |
| `parseable` | `match` | [Parseable](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `parseable` | `match_regex` | [Parseable](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `pgsql` | `cockroachdb` | [PostgreSQL](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `connection_options` | [PostgreSQL](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `database` | [PostgreSQL](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `host` | [PostgreSQL](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `password` | [PostgreSQL](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `port` | [PostgreSQL](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `table` | [PostgreSQL](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `user` | [PostgreSQL](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `workers` | [PostgreSQL](https://docs.fluentbit.io/manual/data-pipeline/outputs/postgresql#configuration-parameters) |
| `pgsql` | `match` | [PostgreSQL](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `pgsql` | `match_regex` | [PostgreSQL](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `plot` | `file` | [Plot](https://docs.fluentbit.io/manual/data-pipeline/outputs/plot#configuration-parameters) |
| `plot` | `key` | [Plot](https://docs.fluentbit.io/manual/data-pipeline/outputs/plot#configuration-parameters) |
| `plot` | `workers` | [Plot](https://docs.fluentbit.io/manual/data-pipeline/outputs/plot#configuration-parameters) |
| `plot` | `match` | [Plot](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `plot` | `match_regex` | [Plot](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `prometheus_exporter` | `add_label` | [Prometheus exporter](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter#configuration-parameters) |
| `prometheus_exporter` | `add_timestamp` | [Prometheus exporter](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter#configuration-parameters) |
| `prometheus_exporter` | `host` | [Prometheus exporter](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter#configuration-parameters) |
| `prometheus_exporter` | `port` | [Prometheus exporter](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter#configuration-parameters) |
| `prometheus_exporter` | `workers` | [Prometheus exporter](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter#configuration-parameters) |
| `prometheus_exporter` | `match` | [Prometheus exporter](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `prometheus_exporter` | `match_regex` | [Prometheus exporter](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `prometheus_remote_write` | `add_label` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `aws_auth` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `aws_external_id` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `aws_profile` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `aws_region` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `aws_role_arn` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `aws_service` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `aws_sts_endpoint` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `compression` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `header` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `host` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `http_passwd` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `http_user` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `log_response_payload` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `port` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `proxy` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `uri` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `workers` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write#configuration-parameters) |
| `prometheus_remote_write` | `match` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `prometheus_remote_write` | `match_regex` | [Prometheus remote write](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `s3` | `alias` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `authorization_endpoint_bearer_token` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `authorization_endpoint_password` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `authorization_endpoint_url` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `authorization_endpoint_username` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `auto_retry_requests` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `blob_database_file` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `bucket` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `canned_acl` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `compression` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `content_type` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `endpoint` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `external_id` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `file_delivery_attempt_limit` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `host` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `json_date_format` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `json_date_key` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `log_key` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `log_level` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `log_suppress_interval` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `match` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `match_regex` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `net.connect_timeout` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `net.connect_timeout_log_error` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `net.dns.mode` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `net.dns.prefer_ipv4` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `net.dns.prefer_ipv6` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `net.io_timeout` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `net.keepalive_max_recycle` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `net.max_worker_connections` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `net.proxy_env_ignore` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `net.source_address` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `net.tcp_keepalive` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `net.tcp_keepalive_interval` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `net.tcp_keepalive_probes` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `net.tcp_keepalive_time` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `part_delivery_attempt_limit` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `part_size` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `port` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `preserve_data_ordering` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `profile` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `region` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `retry_limit` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `role_arn` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `s3_key_format` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `s3_key_format_tag_delimiters` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `send_content_md5` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `static_file_path` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `store_dir` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `store_dir_limit_size` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `storage_class` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `sts_endpoint` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `tls` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `tls.ca_file` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `tls.ca_path` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `tls.ciphers` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `tls.crt_file` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `tls.debug` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `tls.key_file` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `tls.key_passwd` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `tls.max_version` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `tls.min_version` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `tls.verify` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `tls.verify_hostname` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `tls.vhost` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `tls.windows.certstore_name` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `tls.windows.use_enterprise_store` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `total_file_size` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `upload_chunk_size` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `upload_part_freshness_limit` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `upload_parts_timeout` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `upload_timeout` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `use_put_object` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `s3` | `workers` | [Amazon S3](https://docs.fluentbit.io/manual/data-pipeline/outputs/s3#configuration-parameters) |
| `skywalking` | `auth_token` | [Apache SkyWalking](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) |
| `skywalking` | `host` | [Apache SkyWalking](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) |
| `skywalking` | `port` | [Apache SkyWalking](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) |
| `skywalking` | `svc_inst_name` | [Apache SkyWalking](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) |
| `skywalking` | `svc_name` | [Apache SkyWalking](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) |
| `skywalking` | `workers` | [Apache SkyWalking](https://docs.fluentbit.io/manual/data-pipeline/outputs/skywalking#configuration-parameters) |
| `skywalking` | `match` | [Apache SkyWalking](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `skywalking` | `match_regex` | [Apache SkyWalking](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `slack` | `webhook` | [Slack](https://docs.fluentbit.io/manual/data-pipeline/outputs/slack#configuration-parameters) |
| `slack` | `workers` | [Slack](https://docs.fluentbit.io/manual/data-pipeline/outputs/slack#configuration-parameters) |
| `slack` | `match` | [Slack](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `slack` | `match_regex` | [Slack](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `splunk` | `channel` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `compress` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `host` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `http_buffer_size` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `http_debug_bad_request` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `http_passwd` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `http_user` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `port` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `splunk_token` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `workers` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/outputs/splunk#configuration-parameters) |
| `splunk` | `match` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `splunk` | `match_regex` | [Splunk](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `stackdriver` | `autoformat_stackdriver_trace` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `cloud_logging_base_url` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `compress` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `custom_k8s_regex` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `export_to_project_id` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `google_service_credentials` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `http_request_key` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `job` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `k8s_cluster_location` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `k8s_cluster_name` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `labels` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `labels_key` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `location` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `log_name_key` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `metadata_server` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `namespace` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `node_id` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `project_id_key` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `resource` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `resource_labels` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `service_account_email` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `service_account_secret` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `severity_key` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `span_id_key` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `stackdriver_agent` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `tag_prefix` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `task_id` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `test_log_entry_format` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `text_payload_key` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `trace_key` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `trace_sampled_key` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `workers` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/outputs/stackdriver#configuration-parameters) |
| `stackdriver` | `match` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `stackdriver` | `match_regex` | [Stackdriver](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `stackdriver_special_fields` | `match` | [Stackdriver special fields](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `stackdriver_special_fields` | `match_regex` | [Stackdriver special fields](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `stdout` | `format` | [Standard output](https://docs.fluentbit.io/manual/data-pipeline/outputs/standard-output#configuration-parameters) |
| `stdout` | `json_date_format` | [Standard output](https://docs.fluentbit.io/manual/data-pipeline/outputs/standard-output#configuration-parameters) |
| `stdout` | `json_date_key` | [Standard output](https://docs.fluentbit.io/manual/data-pipeline/outputs/standard-output#configuration-parameters) |
| `stdout` | `workers` | [Standard output](https://docs.fluentbit.io/manual/data-pipeline/outputs/standard-output#configuration-parameters) |
| `stdout` | `match` | [Standard output](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `stdout` | `match_regex` | [Standard output](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `syslog` | `allow_longer_sd_id` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `host` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `mode` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `port` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_appname_key` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_appname_preset` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_facility_key` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_facility_preset` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_format` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_hostname_key` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_hostname_preset` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_maxsize` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_message_key` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_msgid_key` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_msgid_preset` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_procid_key` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_procid_preset` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_sd_key` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_severity_key` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `syslog_severity_preset` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `workers` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/outputs/syslog#configuration-parameters) |
| `syslog` | `match` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `syslog` | `match_regex` | [Syslog](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `tcp` | `format` | [TCP and TLS](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) |
| `tcp` | `host` | [TCP and TLS](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) |
| `tcp` | `json_date_format` | [TCP and TLS](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) |
| `tcp` | `json_date_key` | [TCP and TLS](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) |
| `tcp` | `port` | [TCP and TLS](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) |
| `tcp` | `raw_message_key` | [TCP and TLS](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) |
| `tcp` | `workers` | [TCP and TLS](https://docs.fluentbit.io/manual/data-pipeline/outputs/tcp-and-tls#configuration-parameters) |
| `tcp` | `match` | [TCP and TLS](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `tcp` | `match_regex` | [TCP and TLS](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `td` | `api` | [Treasure Data](https://docs.fluentbit.io/manual/data-pipeline/outputs/treasure-data#configuration-parameters) |
| `td` | `database` | [Treasure Data](https://docs.fluentbit.io/manual/data-pipeline/outputs/treasure-data#configuration-parameters) |
| `td` | `region` | [Treasure Data](https://docs.fluentbit.io/manual/data-pipeline/outputs/treasure-data#configuration-parameters) |
| `td` | `table` | [Treasure Data](https://docs.fluentbit.io/manual/data-pipeline/outputs/treasure-data#configuration-parameters) |
| `td` | `workers` | [Treasure Data](https://docs.fluentbit.io/manual/data-pipeline/outputs/treasure-data#configuration-parameters) |
| `td` | `match` | [Treasure Data](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `td` | `match_regex` | [Treasure Data](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `udp` | `format` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) |
| `udp` | `host` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) |
| `udp` | `json_date_format` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) |
| `udp` | `json_date_key` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) |
| `udp` | `port` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) |
| `udp` | `raw_message_key` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) |
| `udp` | `workers` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/outputs/udp#configuration-parameters) |
| `udp` | `match` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `udp` | `match_regex` | [UDP](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `vivo_exporter` | `empty_stream_on_read` | [Vivo Exporter](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) |
| `vivo_exporter` | `host` | [Vivo Exporter](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) |
| `vivo_exporter` | `http_cors_allow_origin` | [Vivo Exporter](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) |
| `vivo_exporter` | `port` | [Vivo Exporter](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) |
| `vivo_exporter` | `stream_queue_size` | [Vivo Exporter](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) |
| `vivo_exporter` | `workers` | [Vivo Exporter](https://docs.fluentbit.io/manual/data-pipeline/outputs/vivo-exporter#configuration-parameters) |
| `vivo_exporter` | `match` | [Vivo Exporter](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `vivo_exporter` | `match_regex` | [Vivo Exporter](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `websocket` | `format` | [WebSocket](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `header` | [WebSocket](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `host` | [WebSocket](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `json_date_format` | [WebSocket](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `json_date_key` | [WebSocket](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `port` | [WebSocket](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `uri` | [WebSocket](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `workers` | [WebSocket](https://docs.fluentbit.io/manual/data-pipeline/outputs/websocket#configuration-parameters) |
| `websocket` | `match` | [WebSocket](https://docs.fluentbit.io/manual/data-pipeline/router) |
| `websocket` | `match_regex` | [WebSocket](https://docs.fluentbit.io/manual/data-pipeline/router) |
