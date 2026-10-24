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

# catalog-service

Standalone package for the OpAMP configuration catalog backend and Python-served UI.

For product installation of the standalone catalog or the catalog embedded in
the provider, use the
[Product Installation Guide](../docs/installation.md#install-the-config-catalog).
This page retains component behavior and source-checkout details for developers.

This component ships:
- the `catalog_service` Python package
- a standalone Quart app entrypoint
- provider integration via shared component entrypoints
- catalog unit tests

Catalog row behavior is configuration-driven:
- when a configured component endpoint advertises the config-service feature, clicking a row opens the config editor
- otherwise, clicking a row opens the built-in readonly file viewer
- when the catalog is embedded into the provider, the header shows `Server Console` plus a conditional `Back` button; standalone mode hides those provider-navigation controls
- catalog file metadata is cached and refreshed when source file paths, sizes, or modification times change
- the browser refreshes catalog rows every `ui_refresh_seconds` seconds, defaulting to 120, unless one or more selection checkboxes are active

Documented catalog direction:
- the selection checkbox workflow stays available during normal catalog use
- a fixed first column supports direct selected/unselected filtering without a separate selection-mode toggle
- the standalone catalog and provider-without-catalog paths should continue to operate independently

Repository source layout:
- Python backend package: `src/catalog_service`
- example configuration: `config`
- launcher script: `scripts`
- tests: `tests`
- browser tests: `ui-tests`
- user documentation: `docs`

Run after installation:

```bash
catalog-service --config-path /path/to/catalog-service.json
```

Standalone wheel creation checks whether the OpAMP CLI is available.
If the CLI is not detected in the workspace or as an installed distribution, the build prints
a warning because the CLI is packaged separately as `opamp-cli` and may need to be installed or
deployed alongside the catalog service.

Run from the repository:

```bash
PYTHONPATH=catalog-service/src python3 -m catalog_service
```

Temporary repo-local launcher while CLI tooling is still evolving:

```bash
python3 catalog-service/scripts/start_catalog_service.py
```

If you want the shared guided launcher experience, install the CLI separately and use:

```bash
opamp-cli --help
```

## Freestanding Example Config

Use [catalog-service.freestanding.example.json](config/catalog-service.freestanding.example.json)
as a starting point for a standalone deployment that scans folders outside the provider runtime.

The example assumes a local layout like:

```text
your-workspace/
  catalog-service.freestanding.example.json
  configs/
    fluent-bit/
    fluentd/
    shared/
```

Run with the example config:

```bash
catalog-service --config-path /path/to/catalog-service.freestanding.example.json
```

Run the repo-local launcher with an explicit config path:

```bash
python3 catalog-service/scripts/start_catalog_service.py --config-path /path/to/catalog-service.freestanding.example.json
```

The configured source folders are resolved relative to the config file location when they exist there,
which makes the example suitable for a copied freestanding workspace.

`opamp.config_catalog.ui_refresh_seconds` controls the catalog UI polling interval. If omitted or invalid,
the UI refreshes every 120 seconds. Automatic refresh pauses while the user has selected catalog entries so
ordered selections are not disturbed by file-system changes.

## UI Test Coverage

Standalone browser coverage for the catalog UI lives in `ui-tests/`.

The current Playwright scenarios cover:

- freestanding catalog with config-service available
- freestanding catalog without config-service available
- feature-menu navigation to the config-service UI
- row-click navigation into the config editor
- row-click fallback into the readonly file viewer
- selection checkbox filtering and fixed-column behavior
- auto-refresh pause while catalog rows are selected
- prompt guidance for new browser tests in `ui-tests/README.md`
- scenario coverage details in `docs/TEST_CASES.md`
