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

# Client Config Generator Service

The Client Config Generator is an OpAMP server plugin enabled by the default server config and also available as a standalone service. It creates consumer JSON configuration files from a packaged JSON Schema rather than a fixed HTML form. The same schema controls field labels, help text, default values, mode-specific visibility, and server-side validation.

## Process modes

The generator supports both consumer process lifecycle strategies:

- `Supervisor` displays agent configuration and launch-parameter controls because the consumer starts and manages the agent process.
- `Observer` displays `processDetectionRegex`, which is required so the consumer can discover an externally managed process.

Common connection, TLS, authorization, identity, heartbeat, capability, logging, and update-controller settings remain available in both modes.

## Deployment behavior

The plugin uses the provider's normal `component-entry-points.quart` discovery. This makes route and feature-menu availability configuration-driven:

```json
{
  "component-entry-points": {
    "quart": [
      {
        "entry_point": "client_config_generator_service.opamp_integration:register_client_config_generator_feature",
        "label": "Client Config Generator",
        "url": "/client-config-generator-service/ui",
        "enabled": true
      }
    ]
  }
}
```

If the entry is missing or disabled, the provider does not import the component, its menu item is omitted, and its routes do not exist. The default server config, `config/opamp.json`, enables the generator. The smaller provider example `config/opamp.provider-with-client-config-generator-service.json` shows the generator entry without the other default feature entries.

Install the component wheel in the same environment as the provider before enabling the entry point. The cloud/server install scripts include it in the default server environment. Source-tree launches discover `client-config-generator-service/src` through the provider's optional-component path handling.

For standalone use:

```bash
client-config-generator-service --config-path ./config/opamp.provider-with-client-config-generator-service.json
```

The default standalone port is `8095`; `--port` overrides it.

## Runtime configuration

Component settings use the shared `opamp.client_config_generator` object:

```json
{
  "opamp": {
    "client_config_generator": {
      "web_port": 8095,
      "log_level": "DEBUG",
      "read_only": false,
      "storage": {
        "configuration_directory": "../generated-client-configs"
      }
    }
  }
}
```

Relative directories resolve from the selected JSON configuration file. Runtime precedence is explicit argument, environment variable, shared OpAMP JSON, then the code default. Supported environment overrides are:

- `CLIENT_CONFIG_GENERATOR_CONFIG_PATH`
- `CLIENT_CONFIG_GENERATOR_CONFIG_DIR`
- `CLIENT_CONFIG_GENERATOR_LOG_LEVEL`
- `CLIENT_CONFIG_GENERATOR_READ_ONLY`
- `CLIENT_CONFIG_GENERATOR_WEB_PORT`

## UI and file safety

The UI can start from schema defaults or load a selected saved JSON file. Validation can be run without saving, and a JSON preview shows the payload that will be persisted. Saves use atomic file replacement.

The backend limits access to `.json` files beneath `storage.configuration_directory`; absolute escapes and parent traversal are rejected. Set `read_only` to `true` to retain schema, list, load, and validation operations while disabling writes. UI/API authentication is inherited from the provider when its authentication stack is available, without a manual browser token field.

The packaged static help page is available at `/client-config-generator-service/ui/help`.

## API controls

The API prefix is `/client-config-generator-service/api/v1`:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/status` | Return deployment mode and read-only state |
| `GET` | `/schema` | Return the consumer JSON Schema |
| `GET` | `/configurations` | List selectable saved JSON files |
| `GET` | `/configurations/<name>` | Load a selected configuration |
| `POST` | `/validate` | Validate an unsaved configuration |
| `PUT` | `/configurations/<name>` | Validate and atomically save a configuration |

## Build, packaging, versioning, and tests

The component is an independently versioned wheel with a console entry point. It is included in the component-wheel deployment matrix and the CLI version-target manifest. Build it directly with:

```bash
python -m build --wheel client-config-generator-service
```

Focused quality checks:

```bash
cd client-config-generator-service
python -m ruff check src tests
python -m pylint src/client_config_generator_service
python -m pytest -q -s
```

The `client-config-generator-service-deployment` container scenario verifies that enabled deployments expose the menu and route, while disabled deployments expose neither.
