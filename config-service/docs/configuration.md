<!--
Copyright 2026 mp3monster.org
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Configuration Reference

## Overview
`config-service` uses JSON configuration files for:
1. Versioned catalog selection
2. Validation profile/ruleset selection
3. Standalone config-tool runtime settings
4. Quart component entrypoint registration

## Files
- Standalone config-tool settings: `config-service/src/config_service/config/config-service.json`
- Catalog registry: `config-service/src/config_service/config/catalog-registry.json`
- Validation registry: `config-service/src/config_service/config/validation-rules-registry.json`
- Service registry: `config-service/src/config_service/config/service-registry.json`
- Parser registry: `config-service/src/config_service/config/parser-registry.json`

## Environment variables
- `CONFIG_TOOL_CONFIG_PATH`
  - Optional path override for the standalone config-tool JSON file.
  - Also set automatically when launching with `python -m config_service --config-path <file>`.
- `CONFIG_SERVICE_WEB_PORT`
  - Optional integer override for the config-service listen port.
  - Takes precedence over JSON file settings.
- `CONFIG_TOOL_LOG_LEVEL`
  - Optional standalone Python logging level override.
  - Useful for forcing `DEBUG` during local development.
- `CONFIG_SERVICE_UI_BASE_CSS_PATH`
  - Optional URL/path override for the primary UI stylesheet.
  - Takes precedence over JSON file settings.
- `APP_ENABLE_DEV_FEATURES`
  - Truthy values: `1`, `true`, `yes`, `on`
  - Enables developer-oriented backend behavior and diagnostics routes used in local development.
- `CONFIG_SERVICE_UI_CSS_OVERRIDE_PATH`
  - Optional single CSS URL/path loaded after default UI CSS.
- `CONFIG_SERVICE_UI_CSS_OVERRIDES`
  - Optional comma-separated CSS URLs/paths loaded after default UI CSS.
- Authentication variables (shared with OpAMP provider auth model):
  - `UI_AUTH_MODE` (`disabled`, `static`, `jwt`)
  - `UI_AUTH_STATIC_TOKEN`
  - `UI_AUTH_JWT_ISSUER`
  - `UI_AUTH_JWT_AUDIENCE`
  - `UI_AUTH_JWT_JWKS_URL`
  - `UI_AUTH_JWT_LEEWAY_SECONDS`

## Catalog registry format
Path: `config-service/src/config_service/config/catalog-registry.json`

Example:
```json
{
  "registry_version": "1.0.0",
  "default_versions": {
    "fluentbit": "5.0.4",
    "fluentd": "1.19"
  },
  "catalogs_by_type": {
    "fluentbit": {
      "3.2.10": "json-definitions/fluent-bit-3.2.10-all-plugins-catalog.json",
      "4.2.4": "json-definitions/fluent-bit-4.2.4-all-plugins-catalog.json",
      "5.0.4": "json-definitions/fluent-bit-5.0.4-all-plugins-catalog.json"
    },
    "fluentd": {
      "1.8": "json-definitions/fluentd-1.8-all-plugins-catalog.json",
      "1.16": "json-definitions/fluentd-1.16-all-plugins-catalog.json",
      "1.19": "json-definitions/fluentd-1.19-all-plugins-catalog.json"
    }
  }
}
```

Rules:
1. `catalogs_by_type` must be a non-empty object.
2. Each engine key must map to a non-empty object of `version -> JSON path`.
3. `default_versions` should provide a default version for each configured engine.

The registry continues to point at the top-level manifest file. Those manifests may
assemble per-version shard directories such as:
1. `config-service/src/config_service/json-definitions/fluent-bit/3.2.10/inputs/`
2. `config-service/src/config_service/json-definitions/fluent-bit/3.2.10/filters/`
3. `config-service/src/config_service/json-definitions/fluent-bit/3.2.10/outputs/`
4. `config-service/src/config_service/json-definitions/fluentd/1.19/inputs/`
5. `config-service/src/config_service/json-schemas/fluentbit/5.0.4/outputs/`

## Service registry format
Path: `config-service/src/config_service/config/service-registry.json`

Example:
```json
{
  "registry_version": "1.0.0",
  "default_versions": {
    "fluentbit": "5.0.4",
    "fluentd": "1.19"
  },
  "service_definitions_by_type": {
    "fluentbit": {
      "3.2.10": "json-definitions/fluent-bit-3.2.10-service-options.json",
      "4.2.4": "json-definitions/fluent-bit-4.2.4-service-options.json",
      "5.0.4": "json-definitions/fluent-bit-5.0.4-service-options.json"
    },
    "fluentd": {
      "1.8": "json-definitions/fluentd-1.8-service-options.json",
      "1.16": "json-definitions/fluentd-1.16-service-options.json",
      "1.19": "json-definitions/fluentd-1.19-service-options.json"
    }
  }
}
```

Rules:
1. `service_definitions_by_type` must be a non-empty object.
2. Each engine key must map to a non-empty object of `version -> JSON path`.
3. Each referenced version maps to a JSON file that defines:
   1. `section: service`
   2. `cardinality.maximum: 1`
   3. `options[]` metadata for UI and validation typing.

## Parser registry format
Path: `config-service/src/config_service/config/parser-registry.json`

Example:
```json
{
  "registry_version": "1.0.0",
  "default_versions": {
    "fluentbit": "5.0.4"
  },
  "parser_definitions_by_type": {
    "fluentbit": {
      "3.2.10": "json-definitions/fluent-bit-3.2.10-parser-options.json",
      "4.2.4": "json-definitions/fluent-bit-4.2.4-parser-options.json",
      "5.0.4": "json-definitions/fluent-bit-5.0.4-parser-options.json"
    }
  }
}
```

Rules:
1. `parser_definitions_by_type` must be a non-empty object.
2. Each engine key must map to a non-empty object of `version -> JSON path`.
3. Each referenced version maps to a JSON file that defines:
   1. `section: parsers`
   2. `builtin_parser_names[]`
   3. `parser_formats` keyed by parser format (`json`, `regex`, `ltsv`, `logfmt`, and so on)

## Validation registry format
Path: `config-service/src/config_service/config/validation-rules-registry.json`

Key sections:
1. `default_profile`
2. `profiles`
3. `rulesets`
4. `version_overrides`

Behavior:
1. A profile selects one or more named rulesets.
2. Each ruleset points to an adapter via `adapter` (for example `builtin.data_type_enforcement`).
3. `version_overrides.<version>.additional_rulesets` adds version-specific rule evaluation.

## Backend mode
- `standalone`: launched directly by `python -m config_service`
- `embedded`: mounted into OpAMP provider via `src/config_service/opamp_integration.py`

## Listen port resolution
`config-service` resolves its standalone listen port in this order:
1. Environment variable `CONFIG_SERVICE_WEB_PORT`
2. `config-tool.web_port` in `config-service/src/config_service/config/config-service.json`
3. Legacy `config_service.web_port` in the JSON config file referenced by `OPAMP_CONFIG_PATH`
4. `provider.webui_port` in that same fallback JSON config file
5. Default `8080`

## Standalone log level resolution
`config-service` resolves its standalone Python log level in this order:
1. Environment variable `CONFIG_TOOL_LOG_LEVEL`
2. `config-tool.log_level` in `config-service/src/config_service/config/config-service.json`
3. `provider.log_level` in the JSON config file referenced by `OPAMP_CONFIG_PATH`
4. Default `INFO`

Default config file path:
- `config-service/src/config_service/config/config-service.json`

Fallback config path:
- `config/opamp.json`

Example:
```json
{
  "component-entry-points": {
    "quart": [
      "opamp_tools.config_app:register_api_component",
      "opamp_tools.config_app:register_ui_component"
    ]
  },
  "config-tool": {
    "web_port": 8090,
    "log_level": "INFO",
    "ui_base_css_path": "/ui/assets/web_ui.css",
    "ui_css_overrides": [],
    "ui_collapsed_sections": [
      "environment_variables",
      "metadata_environment_variables",
      "upstream_servers",
      "parsers",
      "service",
      "rendered_configuration"
    ],
    "read_only": false
  }
}
```

Root runtime keys:
1. `component-entry-points`: dynamic component registration for host frameworks.
2. `component-entry-points.quart`: ordered list of Python entrypoints loaded into Quart.
3. Each entry can be:
   1. a string (`module:function`)
   2. or an object with `entry_point` (and optional `enabled` boolean)

Standalone config-tool keys:
1. `web_port`: HTTP listen port for standalone mode.
2. `log_level`: Python backend log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
3. `ui_base_css_path`: URL/path for the primary UI stylesheet.
4. `ui_css_overrides`: extra stylesheet URL/path entries loaded after the base stylesheet.
5. `ui_collapsed_sections`: list of section keys that should render collapsed by default. If omitted, sections default to expanded.
6. `read_only`: when true, disable editing and saving in the UI.
7. `agent_validation`: external agent-validator command configuration.

Quart component entrypoint resolution:
1. `component-entry-points.quart` from the active config file.
2. If missing or empty, defaults to:
   1. `opamp_tools.config_app:register_api_component`
   2. `opamp_tools.config_app:register_ui_component`

`agent_validation` format:
1. `entries`: ordered list of external validator definitions.
2. Each entry includes:
   1. `agent_type` (required): for example `fluentbit` or `fluentd`.
   2. `agent_version` (optional): exact match version. If omitted, the entry acts as fallback for the agent type.
   3. `command_path` (required): executable path or command name.
   4. `command_args` (optional): command arguments.
      - Supports `{config_path}` placeholder when config is provided via file path.
      - Supports `{config_text}` placeholder when embedding config text in an argument.
   5. `send_config_via_stdin` (optional, default `false`): write config text to process stdin.
   6. `adapter` (optional): adapter key (`fluentbit`, `fluentd`, `generic`).
   7. `environment` (optional): extra environment variables for the command.
   8. `working_directory` (optional): command working directory.
   9. `success_exit_codes` (optional, default `[0]`): acceptable command exit codes.
   10. `dry_run_validation_enabled` (optional, default `true`): controls whether the UI/API dry-run action is available for this entry.

Example:

```json
{
  "config-tool": {
    "agent_validation": {
      "entries": [
        {
          "agent_type": "fluentbit",
          "agent_version": "5.0.4",
          "command_path": "fluent-bit",
          "command_args": ["--dry-run", "-c", "{config_path}"],
          "adapter": "fluentbit",
          "send_config_via_stdin": false,
          "dry_run_validation_enabled": true
        },
        {
          "agent_type": "fluentbit",
          "command_path": "fluent-bit",
          "command_args": ["--dry-run", "-c", "{config_path}"],
          "adapter": "fluentbit",
          "send_config_via_stdin": false,
          "dry_run_validation_enabled": false
        }
      ]
    }
  }
}
```

Public package API:
1. `config_service.agent_validation.validate(config_text, agent_type, agent_version=None, config_path=None)`
2. Returns JSON with:
   1. `ok`
   2. `messages`
   3. `requested_agent_version`
   4. `used_agent_version`
   5. `version_mismatch`
   6. `command` / execution metadata

Supported `ui_collapsed_sections` values:
1. `service`
2. `environment_variables` (alias: `env`)
3. `metadata_environment_variables` (aliases: `metadata_env`, legacy `metadata_as_environment_variables`)
4. `upstream_servers` (alias: `upstream`)
5. `parsers`
6. `plugins`
7. `labels`
8. `workers`
9. `validation`
10. `rendered_configuration` (alias: `rendered`)

Read-only mode:
1. Set `config-tool.read_only` to `true` to disable editing and save actions in the UI.
2. File open, validation, render, and help actions remain available.

## Authentication behavior
1. Embedded mode reuses OpAMP provider non-OpAMP HTTP auth checks.
2. Standalone mode also reuses provider auth helpers when `provider/src` is importable.
3. Unauthorized requests return `401` and include `WWW-Authenticate: Bearer ...`.

## UI CSS integration (OpAMP look and feel)
The browser UI can load shared OpAMP stylesheets using:
1. Environment variable `CONFIG_SERVICE_UI_BASE_CSS_PATH` for the primary stylesheet.
2. JSON config key `config-tool.ui_base_css_path` in `config-service/src/config_service/config/config-service.json`.
3. Environment variable `CONFIG_SERVICE_UI_CSS_OVERRIDE_PATH` for one additional override path.
4. Environment variable `CONFIG_SERVICE_UI_CSS_OVERRIDES` for multiple additional override paths.
5. App config override key `CONFIG_SERVICE_UI_CSS_OVERRIDES` (list or comma-separated string).

Fallback theme remains available when no custom base stylesheet is provided.
