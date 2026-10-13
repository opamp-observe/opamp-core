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

# Standalone Packaging

## Standalone config file
The standalone service now prefers:
1. `config-service/src/config_service/config/config-service.json`

That file stores config-service runtime settings under:
1. `config-tool`
2. `component-entry-points`

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
    "web_port": 8080,
    "ui_base_css_path": "/config-service/ui/assets/config_ui.css",
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

For the complete list of supported `ui_collapsed_sections` values and aliases, see [Configuration Reference](./configuration.md).

## Build the wheel
From repository root:
```bash
cd config-service
python3 -m build --wheel
```

Repository-wide coordinated packaging alternative:

```bash
python3 dev-tools/main.py build release-assets --components provider,consumer,catalog-service,cli,consumer-sim
```

Use the standalone command above when you only want the `config-service` wheel.
Use the repository-wide builder when you want the coordinated deployable artefacts
and SBOMs for the main independently deployed components.

During wheel creation, the packaging flow checks whether the OpAMP CLI is available.
If the CLI cannot be detected in the workspace or as an installed distribution, the build prints
a warning because the CLI is packaged separately as `opamp-cli` and may need to be installed or
deployed alongside the standalone service.

Output:
1. `config-service/dist/*.whl`

## Install and run standalone
```bash
pip install config-service/dist/config_service-0.1.0-py3-none-any.whl
config-service --config-path /path/to/config-service.json
```

If you also want the guided launcher and process-management experience, install the CLI separately:

```bash
pip install cli/dist/opamp_cli-*.whl
opamp-cli --help
```

### Windows PowerShell logging (`Tee-Object`) note
When running a Python module in PowerShell with `2>&1 | Tee-Object`, output written to stderr can appear as a red `NativeCommandError` wrapper even when the service is healthy.

Use this pattern to capture logs and avoid the wrapper:

```powershell
$old = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$PSNativeCommandUseErrorActionPreference = $false

python -m config_service --config-path D:\dev\opamp\config-service\src\config_service\config\config-service.json 2>&1 |
  ForEach-Object { "$_" } |
  Tee-Object -FilePath D:\dev\opamp\logs\config-service.log

$ErrorActionPreference = $old
```

Optional: write stdout and stderr to separate files:

```powershell
python -m config_service --config-path D:\dev\opamp\config-service\src\config_service\config\config-service.json `
  1> D:\dev\opamp\logs\config-service.stdout.log `
  2> D:\dev\opamp\logs\config-service.stderr.log
```

## Generate the SBOM
From repository root:
```bash
python3 config-service/dev-tools/generate_sbom.py
```
The script ensures `cyclonedx-bom` is available and uses `cyclonedx-py` for SBOM generation.

This SBOM flow is specific to `config-service`. The repository-wide wheel publisher
uses the developer-tool helper under `dev-tools/src/opamp_dev_tools/sbom.py` for the main deployable
component SBOM generation.

Output:
1. `config-service/sbom/config-service-sbom.cdx.json`
