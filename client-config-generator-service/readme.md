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

`client-config-generator-service` is a schema-driven server plugin and standalone UI for creating OpAMP consumer JSON files. The packaged schema supports both process lifecycle strategies:

- `Supervisor`: the consumer launches and owns the agent process.
- `Observer`: the consumer discovers an externally managed process using `processDetectionRegex`.

The browser UI can select and load an existing configuration, validate edits, preview JSON, and save a configuration beneath an operator-controlled directory. The versioned API provides the same controls.

## Embedded deployment

Install the wheel beside `opamp-server`, then add this entry to `component-entry-points.quart`:

```json
{
  "entry_point": "client_config_generator_service.opamp_integration:register_client_config_generator_feature",
  "label": "Client Config Generator",
  "url": "/client-config-generator-service/ui",
  "enabled": true
}
```

When the entry is absent or has `"enabled": false`, neither the feature-menu item nor the plugin routes are registered.

## Standalone deployment

```bash
client-config-generator-service --config-path ./opamp.json --host 0.0.0.0 --port 8095
```

The UI is available at `http://localhost:8095/client-config-generator-service/ui`. The static help page is at `/client-config-generator-service/ui/help`.

## Shared configuration

Settings live under `opamp.client_config_generator`. Relative storage paths resolve from the JSON configuration file:

```json
{
  "opamp": {
    "client_config_generator": {
      "web_port": 8095,
      "log_level": "DEBUG",
      "read_only": false,
      "storage": {
        "configuration_directory": "generated-client-configs"
      }
    }
  }
}
```

Environment variables have higher precedence:

- `CLIENT_CONFIG_GENERATOR_CONFIG_PATH`
- `CLIENT_CONFIG_GENERATOR_CONFIG_DIR`
- `CLIENT_CONFIG_GENERATOR_LOG_LEVEL`
- `CLIENT_CONFIG_GENERATOR_READ_ONLY`
- `CLIENT_CONFIG_GENERATOR_WEB_PORT`

## API

All endpoints are below `/client-config-generator-service/api/v1`:

- `GET /schema`
- `GET /configurations`
- `GET /configurations/<relative-json-name>`
- `POST /validate`
- `PUT /configurations/<relative-json-name>`

The file service accepts only `.json` targets contained by the configured storage directory and uses atomic replacement on save. Provider-managed UI authentication is reused when the provider auth stack is installed; the UI does not offer manual bearer-token entry.

## Quality and packaging

```bash
python -m pip install -e ".[dev]"
python -m ruff check src tests
python -m pylint src/client_config_generator_service
python -m pytest -q -s
python -m build --wheel
```

The package version is maintained in `pyproject.toml` and `client_config_generator_service.__version__`, and is registered in the repository version-target manifest.
