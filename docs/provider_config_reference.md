# Provider Config Reference

This page is the dedicated reference for the `provider` section in `config/opamp.json`.

It is intended to answer three different questions quickly:

- what keys the provider reads
- what built-in default the code uses when a key is omitted
- what value the repository's default development file currently sets

For the implementation source of truth, see `provider/src/opamp_provider/config.py`.

## Scope

This page covers `provider.*` only.

Related top-level configuration sections are documented separately:

- [`opamp_json_reference.md`](opamp_json_reference.md) for the full `config/opamp.json` map
- [`opamp_config_catalog_ui.md`](opamp_config_catalog_ui.md) for `opamp.config_catalog`
- [`provider/README.md#web-ui`](../provider/README.md#web-ui) for `component-entry-points`

## Config source and overrides

- Default config file: `config/opamp.json`
- Environment override: `OPAMP_CONFIG_PATH`
- CLI overrides:
  - `--config-path`
  - `--port` for `provider.webui_port`
  - `--log-level` for `provider.log_level`
  - `--restore` for state restore behavior

The provider README still covers the operational startup flow in more detail:

- [`provider/README.md#configuration`](../provider/README.md#configuration)

## Core provider values

| Key | Type | Built-in default | Default repo value | Editable in UI | Notes |
| --- | --- | --- | --- | --- | --- |
| `provider.delayed_comms_seconds` | integer | `60` | `60` | Yes | Threshold before a client is marked delayed. |
| `provider.significant_comms_seconds` | integer | `300` | `120` | Yes | Threshold before a client is marked significantly delayed. The UI save path enforces this to be greater than `delayed_comms_seconds`. |
| `provider.webui_port` | integer | `8080` | `8080` | No | Main HTTP/HTTPS listener port for `/ui`, `/api`, and `/v1/opamp`. |
| `provider.minutes_keep_disconnected` | integer | `30` | `5` | Yes | Retention window for disconnected clients before purge. |
| `provider.retryAfterSeconds` | integer | `30` | `30` | No | Returned when the server responds with an unavailable/retry-later signal. |
| `provider.client_event_history_size` | integer | `50` | `50` | Yes | Per-client event history retention size. UI/API updates clamp this to a minimum of `1`. |
| `provider.log_level` | string | `INFO` | `DEBUG` | No | Resolved through Python logging level names. |
| `provider.default_heartbeat_frequency` | integer | `30` | `30` | Yes | Default heartbeat value used for global client heartbeat updates. UI/API updates clamp this to a minimum of `1`. |
| `provider.latest_docs_url` | string | `https://htmlpreview.github.io/?https://raw.githubusercontent.com/opamp-observe/opamp-core/main/github-landingpage/index.html` | `https://htmlpreview.github.io/?https://raw.githubusercontent.com/opamp-observe/opamp-core/main/github-landingpage/index.html` | No | Redirect target for `GET /doc-set`, which is also the route used by the UI `Latest docs` links. |
| `provider.human_in_loop_approval` | boolean | `false` | `false` | Yes | Enables the pending-approval workflow for unknown agents. |
| `provider.allow-remote-config` | boolean | `true` | `true` | No | Enables the enhanced Configuration-tab remote file workflow and allows related remote-config queueing endpoints. |
| `provider.allow-effective-config` | boolean | `true` | `true` | No | Controls whether the provider advertises `ServerCapabilities.AcceptsEffectiveConfig` to agents. |
| `provider.allow-connection-settings` | boolean | `false` | `false` | No | Controls whether the provider advertises `ServerCapabilities.OffersConnectionSettings`. |
| `provider.allow-connection-settings-request` | boolean | `false` | `false` | No | Controls whether the provider advertises `ServerCapabilities.AcceptsConnectionSettingsRequest`. |
| `provider.allow-mcp` | boolean | `false` | `true` | No | Enables direct Streamable HTTP MCP access at `/mcp`. When `false`, `/mcp` requests are rejected even if other MCP transports are available. |
| `provider.opamp-use-authorization` | string | `none` | `none` | No | Allowed values: `none`, `config-token`, `idp`. Controls OpAMP transport auth on `/v1/opamp`. |
| `provider.ui-use-authorization` | string | `none` | `none` | No | Allowed values: `none`, `config-token`, `idp`. Controls non-OpAMP auth for `/ui`, `/api`, `/tool`, `/mcp` when enabled, and related routes. |

## Metrics values

| Key | Type | Built-in default | Default repo value | Editable in UI | Notes |
| --- | --- | --- | --- | --- | --- |
| `provider.metrics.enabled` | boolean | `true` | `true` | No | Enables the Prometheus scrape endpoint at `/metrics` and the internal graph endpoint at `/api/metrics/graphs`. |
| `provider.metrics.graph_history_minutes` | integer | `0` | `0` | No | Retention window in minutes for in-memory gauge time-series history used by internal dashboard graphs. `0` disables history retention while still exposing current gauge values. |

## TLS values

The default repository config does not include `provider.tls`, so the provider runs HTTP-only unless you
add this section or use a config variant that already includes it.

| Key | Type | Built-in default | Default repo value | Editable in UI | Notes |
| --- | --- | --- | --- | --- | --- |
| `provider.tls` | object | not set | not set | No | When absent, the provider runs without TLS. |
| `provider.tls.enabled` | boolean | `true` when `provider.tls` exists | not set | No | If `false`, the TLS section is ignored for that run. |
| `provider.tls.cert_file` | string | none | not set | No | Required existing certificate file when TLS is enabled. |
| `provider.tls.key_file` | string | none | not set | No | Required existing private key file when TLS is enabled. |
| `provider.tls.trust_anchor_mode` | string | `full_chain_to_root` | not set | No | Allowed values: `none`, `partial_chain`, `full_chain_to_root`. Invalid values raise a startup config error. |

For local HTTPS and self-signed certificate setup, use:

- [`self_signed_tls_setup.md`](self_signed_tls_setup.md)

## State persistence values

| Key | Type | Built-in default | Default repo value | Editable in UI | Notes |
| --- | --- | --- | --- | --- | --- |
| `provider.state_persistence.enabled` | boolean | `false` | `true` | Yes | Enables persisted provider state snapshots. If the target folder is invalid, persistence is disabled for that run and startup continues. |
| `provider.state_persistence.state_file_prefix` | string | `runtime/opamp_server_state` | `server-state\\opamp_server_state` | Indirectly | UI edits use `state_save_folder`, which updates the parent folder while preserving the snapshot base filename. |
| `provider.state_persistence.retention_count` | integer | `5` | `3` | Yes | Number of newest snapshot files to keep. UI/API updates require a positive integer. |
| `provider.state_persistence.flush_mode` | string | `graceful_shutdown` | `graceful_shutdown` | No | Current persistence mode written into config. |
| `provider.state_persistence.autosave_interval_seconds_since_change` | integer | `600` | `60` | Yes | Autosave interval after non-heartbeat state changes. UI/API updates require a positive integer. |

## Authorization mode notes

Both provider authorization settings normalize to one of these values:

- `none`
- `config-token`
- `idp`

If an invalid value is supplied in `opamp.json`, the provider logs a warning and falls back to `none`.

The auth mode keys select behavior, while secrets and IdP connection details come from environment
variables. For full setup details, use:

- [`authentication.md`](authentication.md)

The metrics scrape endpoint uses the same non-OpAMP auth mode:

- `provider.ui-use-authorization=none` leaves `/metrics` open
- `provider.ui-use-authorization=config-token` requires `UI_AUTH_STATIC_TOKEN`
- `provider.ui-use-authorization=idp` requires a valid bearer token accepted by the configured JWT settings

## UI editability and persistence

These provider-backed settings are editable through **Global Settings** in the server console:

- `provider.delayed_comms_seconds`
- `provider.significant_comms_seconds`
- `provider.minutes_keep_disconnected`
- `provider.client_event_history_size`
- `provider.default_heartbeat_frequency`
- `provider.human_in_loop_approval`
- `provider.state_persistence.enabled`
- `provider.state_persistence.retention_count`
- `provider.state_persistence.autosave_interval_seconds_since_change`

One related UI field is mapped rather than stored directly:

- `state_save_folder` in the UI updates the parent folder of `provider.state_persistence.state_file_prefix`

One provider-managed UI workflow is controlled only through config:

- `provider.allow-remote-config` enables the extra file-based remote configuration panel in each client
  **Configuration** tab. When the catalog feature is also configured, that panel shows
  **Select Configs**, opens the catalog in a popup, and lets the operator drag to reorder or remove
  returned files before using a separate send action.

Server capability advertisement is also configuration-driven:

- `provider.allow-remote-config` controls whether the provider advertises `OffersRemoteConfig`
- `provider.allow-effective-config` controls whether the provider advertises `AcceptsEffectiveConfig`
- `provider.allow-connection-settings` controls whether the provider advertises `OffersConnectionSettings`
- `provider.allow-connection-settings-request` controls whether the provider advertises `AcceptsConnectionSettingsRequest`

When the UI persists provider settings back to `opamp.json`, the provider writes a timestamped backup of
the previous file first.

For the UI behavior and help text, see:

- [`provider/README.md#web-ui`](../provider/README.md#web-ui)
- [`endpoints.md`](endpoints.md)

For the provider metrics endpoints and scrape examples, see:

- [`provider_metrics_reference.md`](provider_metrics_reference.md)
- [`provider_metrics_prometheus_setup.md`](provider_metrics_prometheus_setup.md)

## Related config variants

The repository also includes provider-oriented config variants:

- `config/opamp.provider-with-editor-service.json`
- `config/opamp.provider-with-editor-and-credentials-service.json`
- `config/opamp.provider-with-editor-and-catalog-services.json`

Those are introduced in:

- [`provider/README.md#configuration`](../provider/README.md#configuration)
