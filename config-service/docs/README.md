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

# Config-Service User Documentation

This folder contains user-facing documentation for running, configuring, and extending `config-service`.

## Contents
1. [Quickstart](./quickstart.md)
2. [Configuration Reference](./configuration.md)
3. [UI User Guide](./ui-user-guide.md)
4. [Catalog Management](./catalog-management.md)
5. [Plugin JSON File Format](./plugin-json-file-format.md)
6. [Custom Validation Logic](./custom-validation.md)
7. [API Reference](./api-reference.md)
8. [Troubleshooting](./troubleshooting.md)
9. [Standalone Packaging](./standalone-packaging.md)
10. [UI Testing](./ui-testing.md)
11. [Developer Tools](./dev-tools.md)
12. [Fluent Bit Documentation Scraper](./fluentbit_scraper.md)
13. [Test Cases](./TEST_CASES.md)
14. [UI Framework Decision](./ui-framework-decision.md)

## What this service provides
- Versioned Fluent Bit catalog loading from config.
- Versioned Fluentd catalog loading from config, including nested section metadata.
- Schema compilation for configuration editing.
- Validation using schema/semantic checks plus pluggable rule profiles.
- YAML rendering for Fluent Bit and standard `.conf` rendering for Fluentd.
- Python-served schema-driven UI for plugin-driven config authoring.
- Read-only server mode controlled by backend configuration.
- Browser-based Playwright tests for UI behavior such as dropdowns, links, hover text, and partial file loads.
- Developer tooling for schema generation, reference generation, SBOM generation, and quality checks.

## Generated artifacts
- Fluent Bit and Fluentd version catalogs: `config-service/src/config_service/json-definitions/`
- Per-version catalog shards: `config-service/src/config_service/json-definitions/fluent-bit/<version>/` and `config-service/src/config_service/json-definitions/fluentd/<version>/`
- Versioned service/system option definitions: `config-service/src/config_service/json-definitions/`
- Generated runtime JSON Schemas: `config-service/src/config_service/json-schemas/`
- Per-version schema shards: `config-service/src/config_service/json-schemas/<config_type>/<version>/`

The packaged source tree is canonical; generators do not maintain duplicate top-level artifact
trees. The Fluent Bit generator backs up packaged configuration to `config-service/backups/`
before changing it.

## Primary runtime entry points
- Backend app: `config-service/src/config_service/app.py`
- Backend package root: `config-service/src/config_service/`
- Python-served UI: `http://localhost:8080/config-service/ui`
- Local convenience scripts: `config-service/scripts`
- Developer tooling and generators: `config-service/dev-tools`
- Backend lint/test entrypoint: `config-service/dev-tools/run_backend_quality_checks.py`
- Backend coverage reports: `config-service/coverage.xml` and `config-service/htmlcov/index.html`
- UI browser-test entrypoint: `config-service/dev-tools/run_ui_quality_checks.sh`
- Fluent Bit asset generator: `config-service/dev-tools/generate_fluentbit_assets.py`
- Fluent Bit markdown generator: `config-service/dev-tools/generate_fluentbit_markdown.py`
- Fluent Bit quick-reference generator: `config-service/dev-tools/quick-references/generate_fluentbit_schema_quick_reference.py`
