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

# Quickstart

## Prerequisites
- Python 3.10+

## Start with convenience scripts
### Linux/macOS
1. `config-service/scripts/dev-up.sh`
2. Stop with `Ctrl+C` in the same terminal

### Windows
1. `config-service\scripts\dev-up.cmd`
2. Stop with `Ctrl+C` in the same terminal

Notes:
- `dev-up` sets `APP_ENABLE_DEV_FEATURES=1` by default when not already set.
- Logs are written under `config-service/.run/`.
- `dev-up` now runs in the foreground and does not fork the Python server into a separate process.
- The listen port is configuration-driven. By default it resolves from `config/opamp.json`
  and now prefers `config-service/src/config_service/config/config-service.json` before falling back to `config/opamp.json` and `8080`.
- In dev mode (`APP_ENABLE_DEV_FEATURES` truthy), backend logs are mirrored to both
  console and `config-service/.run/logs/backend.log`.
- Quart component registration is configuration-driven via
  `component-entry-points.quart` in `config-service/src/config_service/config/config-service.json`.

## Manual start (without convenience scripts)
### Backend + UI (single Python process)
From repository root:
```bash
PYTHONPATH=config-service/src python3 -m config_service
```

To point at a specific config-tool file:
```bash
PYTHONPATH=config-service/src python3 -m config_service --config-path config-service/src/config_service/config/config-service.json
```

## Verify service health
- Backend: `http://localhost:8080/config-service/api/v1/health`
- UI: `http://localhost:8080/config-service/ui`

If the editor is mounted inside the provider instead of launched standalone, the same UI route gains
provider navigation controls (`Server Console`, conditional `Back`, and the shared feature dropdown).

## Run browser UI behavior tests
From repository root:

```bash
config-service/dev-tools/run_ui_quality_checks.sh
```

This runs the Playwright suite against the Python-served UI on port `8091`.
