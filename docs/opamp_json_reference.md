# `config/opamp.json` Reference Map

This page is a navigation guide for the default repository configuration file:

- `config/opamp.json`

It does not try to duplicate every field description. Instead, it points each top-level section to the
existing guide that already explains that part of the configuration in more depth.

## Top-level sections

| `config/opamp.json` area | Purpose | Primary documentation |
| --- | --- | --- |
| `consumer` | Consumer/client connection, transport, launch, and agent reporting settings | [`consumer/README.md`](../consumer/README.md) |
| `provider` | Provider/server listener, UI, state, auth, and remote-control settings | [`provider_config_reference.md`](provider_config_reference.md) |
| `otlp-endpoints` | Shared OTLP logs, metrics, and traces export settings | [`otlp_observability.md`](otlp_observability.md) |
| `component-entry-points` | Additional Quart features exposed through the server feature menu | [`provider/README.md#web-ui`](../provider/README.md#web-ui) |
| `opamp.config_catalog` | Catalog UI routes, scan sources, metadata, and help behavior | [`opamp_config_catalog_ui.md`](opamp_config_catalog_ui.md) |
| `opamp.client_config_generator` | Schema-driven client configuration generator settings | [`client_config_generator_service.md`](client_config_generator_service.md) |

## `consumer`

The `consumer` section controls how the client connects to the server and how it supervises or reports on
the local agent process.

Use these docs:

- [`consumer/README.md#example-opampjson`](../consumer/README.md#example-opampjson) for a worked example
  configuration.
- [`consumer/README.md#consumer-config-keys`](../consumer/README.md#consumer-config-keys) for the main field
  reference.
- [`consumer/README.md#update-controllers`](../consumer/README.md#update-controllers) for
  `full_update_controller` behavior.
- [`consumer/README.md#fluentd-consumer`](../consumer/README.md#fluentd-consumer) for Fluentd-specific notes.
- [`consumer/README.md#simulator-consumer`](../consumer/README.md#simulator-consumer) for simulator-specific
  settings.
- [`self_signed_tls_setup.md#2-fluentd-consumer-config-consumeropamp-fluentdjson`](self_signed_tls_setup.md#2-fluentd-consumer-config-consumeropamp-fluentdjson)
  if you are turning on TLS for local development.

Common fields from the default `config/opamp.json` that are covered there include:

- `consumer.server_url`
- `consumer.log_level`
- `consumer.transport`
- `consumer.tls`
- `consumer.server-authorization`
- `consumer.agent_config_path`
- `consumer.agent_additional_params`
- `consumer.heartbeat_frequency`
- `consumer.full_update_controller`
- `consumer.full_update_controller_type`
- `consumer.allow_custom_capabilities`
- `consumer.agent_capabilities`
- `consumer.preserve_previous_config`

## `provider`

The `provider` section controls the main server runtime, including the web console, OpAMP endpoint
behavior, state retention, and authorization modes.

Use these docs:

- [`provider_config_reference.md`](provider_config_reference.md) for the dedicated provider field reference.
- [`provider/README.md#configuration`](../provider/README.md#configuration) for the default config location and
  example.
- [`provider/README.md#state-persistence-and-restore`](../provider/README.md#state-persistence-and-restore) for
  `provider.state_persistence`.
- [`authentication.md`](authentication.md) for `provider.opamp-use-authorization` and
  `provider.ui-use-authorization`.
- [`self_signed_tls_setup.md#1-provider-config-configopampjson`](self_signed_tls_setup.md#1-provider-config-configopampjson)
  for `provider.tls` when serving HTTPS locally.

Common fields from the default `config/opamp.json` that are covered there include:

- `provider.webui_port`
- `provider.default_heartbeat_frequency`
- `provider.latest_docs_url`
- `provider.human_in_loop_approval`
- `provider.allow-remote-config`
- `provider.allow-effective-config`
- `provider.allow-connection-settings`
- `provider.allow-connection-settings-request`
- `provider.allow-mcp`
- `provider.opamp-use-authorization`
- `provider.ui-use-authorization`
- `provider.state_persistence`

`provider.latest_docs_url` controls the redirect target behind `GET /doc-set`, which is the route used by
the UI `Latest docs` links.

## `component-entry-points`

The `component-entry-points` section lets the server register extra Quart-based features that can appear in
the server feature menu.

Use these docs:

- [`provider/README.md#web-ui`](../provider/README.md#web-ui) for how menu entries are exposed in the server UI.
- [`opamp_config_catalog_ui.md#provider-ui-feature-menu-integration`](opamp_config_catalog_ui.md#provider-ui-feature-menu-integration)
  for an example of feature registration using config-driven menu metadata.

The current default `config/opamp.json` uses this section for:

- `component-entry-points.quart`
- `component-entry-points.quart[*].label`
- `component-entry-points.quart[*].url`
- `config_service.opamp_integration:register_config_service_feature`
- `client_config_generator_service.opamp_integration:register_client_config_generator_feature`

When a feature entry is enabled and the target page is hosted inside the provider, the embedded page
shows `Server Console` and `Back` buttons in its header. In standalone deployments those buttons stay
hidden.

## `otlp-endpoints`

The `otlp-endpoints` section enables OpenTelemetry OTLP export for supported runtimes.

Use these docs:

- [`otlp_observability.md`](otlp_observability.md) for the shared config shape, precedence rules,
  and runtime behavior.
- [`../agent_broker/README.md`](../agent_broker/README.md) for the broker-specific inheritance note.

## `opamp.config_catalog`

The `opamp.config_catalog` section enables and shapes the optional configuration catalog feature exposed by
the server.

Use these docs:

- [`opamp_config_catalog_ui.md#configuration`](opamp_config_catalog_ui.md#configuration) for the config block and
  field descriptions.
- [`opamp_config_catalog_ui.md#header-metadata-format`](opamp_config_catalog_ui.md#header-metadata-format) for
  extracted metadata columns.
- [`opamp_config_catalog_ui.md#selection-checkbox-direction`](opamp_config_catalog_ui.md#selection-checkbox-direction)
  for the always-available selection checkbox behavior.
- [`../catalog-service/README.md`](../catalog-service/README.md) for the optional standalone catalog service
  context.

Common fields from the default `config/opamp.json` that are covered there include:

- `opamp.config_catalog.enabled`
- `opamp.config_catalog.menu_label`
- `opamp.config_catalog.route_path`
- `opamp.config_catalog.help_path`
- `opamp.config_catalog.ui_base_css_path`
- `opamp.config_catalog.sources`

## Related configuration variants

If you are looking for other repo-provided server config variants, also check:

- `config/opamp.provider-with-editor-service.json`
- `config/opamp.provider-with-editor-and-credentials-service.json`
- `config/opamp.provider-with-editor-and-catalog-services.json`

Those variants are introduced in [`provider/README.md#configuration`](../provider/README.md#configuration).
