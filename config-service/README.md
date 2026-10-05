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

# config-service

The config service can be run as part of the larger OpAMP server, or as a standalone package. When run in a standalone configuration, this effectively becomes a UI driven configuration editor and validation tool. The config-service is composed of a lightweight JavaScript and HTML presentation tier and a Python backend that serves the UI and provides validation logic, I/O, etc. 

The editor currently primarily supports Fluent-Bit YAML, but it also includes some functionality for Fluentd (and will be enhanced over time).  Fluent Bit's Classic format isn't supported because it isn't the strategic format for the future. There is a config converter available [here](https://github.com/mp3monster/fluent-bit-classic-to-yaml-converter).

The proposed multi-agent refactor and schema-driven Vector support are specified in the [multi-agent configuration editor roadmap](../docs/roadmap/vector_multi_agent_configuration_editor.md).

### This package ships:

- the `config_service` Python package
- bundled HTML/CSS/JS UI assets
- bundled catalogue and service definition JSON files, including versioned manifest shards
- generated runtime JSON schemas, including per-version plugin shards
- Tooling to allow definition files to be generated and tailored, so custom plugins (or restricting certain plugins for users) can be applied easily.

### Enhanced use

The behaviour of the config service can be tailored through the configuration file (with details such as enabling the agent implementation's dry-run feature in addition to validation), specifying which configuration elements are open or closed at start.

If the Config service detects the deployment on the `catalog-service` then the two components will interoperate, making it easier to find and open configuration files.

In addition to the two deployment options mentioned, the Config Service can be used more easily with the `opamp-cli`.

### Run after installation:

```bash
config-service --config-path /path/to/config-service.json
```

## Developer Details

Developer quality checks:

```bash
python3 config-service/dev-tools/run_backend_quality_checks.py
```

Coverage reports from backend tests are written to:
- `config-service/coverage.xml`
- `config-service/htmlcov/index.html`

Browser UI quality checks:

```bash
config-service/dev-tools/run_ui_quality_checks.sh
```

In addition to the core functionality, the `opamp-dev-cli` provides additional supporting tools, such as controlling packaging processes, minification of the JavaScript (minification is aimed at making it harder to tamper with the JavaScript and improving efficiency as a result of compacting the code)

### Repository source layout:

- Python backend package: `src/config_service`
- developer tools: `dev-tools` (utilities to help prepare a configuration doc set used by the Config Service)
- user documentation: `docs`
