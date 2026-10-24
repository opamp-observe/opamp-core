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

# Development Tooling

This page is the repository-level tooling inventory for local development. Use
it with the component-specific READMEs when setting up or auditing a machine.

## One Command Setup

The OpAMP CLI can create or update a repository-level virtual environment:

```bash
python cli/main.py setup-venv
```

When `opamp-cli` is already installed, the equivalent command is:

```bash
opamp-cli setup-venv
```

Useful options:

| Option | Purpose |
|---|---|
| `--venv <path>` | Use a virtual environment path other than `.venv`. Relative paths resolve from the repository root. |
| `--dry-run` | Print the planned setup commands without creating the environment or installing packages. |
| `--skip-node` | Install only Python dependencies and skip `npm install` steps. |

The command runs these setup phases:

1. Create/update the Python environment with `python -m venv .venv`.
2. Upgrade installer/build tooling: `pip`, `setuptools>=82`, `wheel`, `build`, and `hatchling>=1.25`.
3. Install root `requirements.txt`.
4. Install each local Python component editable with its `dev` extra.
5. Run `npm install` for checked-in Node tooling packages, unless `--skip-node` is supplied.

## Python Components

The setup command installs these Python component directories when their
`pyproject.toml` files are present:

| Path | Package | Build backend | Console scripts |
|---|---|---|---|
| `cli` | `opamp-cli` | `setuptools.build_meta` | `opamp-cli` |
| `provider` | `opamp-server` | `hatchling.build` | `opamp-provider` |
| `consumer` | `opamp-consumer` | `hatchling.build` | `opamp-consumer`, `opamp-consumer-fluentd`, `opamp-consumer-simulator` |
| `consumer-sim` | `opamp-consumer-sim` | `setuptools.build_meta` | `opamp-consumer-sim` |
| `config-service` | `config-service` | `setuptools.build_meta` | `config-service` |
| `catalog-service` | `catalog-service` | `setuptools.build_meta` | `catalog-service` |
| `agent_broker` | `opamp-broker` | `hatchling.build` | `opamp-broker` |
| `mcp` | `opamp-mcp-config` | `setuptools.build_meta` | `opamp-mcp-config` |
| `dev-tools` | `opamp-dev-tools` | `setuptools.build_meta` | `opamp-dev-tools` |
| `svr-credentials-mgr/plaintext-keyring` | `opamp-plaintext-keyring` | `setuptools.build_meta` | keyring backend entry point |
| `svr-credentials-mgr` | `svr-credentials-manager-service` | `setuptools.build_meta` | `svr-credentials-manager-service` |

## Python Runtime Libraries

Core runtime libraries declared across components include:

- CLI and terminal UX: `prompt_toolkit`.
- HTTP/server frameworks: `quart`, `httpx`, `aiohttp`.
- Protocol/config parsing: `protobuf`, `grpcio-tools`, `PyYAML`, `lark`, `luaparser`, `jsonschema`, `defusedxml`.
- OpAMP/provider behavior: `pydantic`, `fastmcp`, `PyJWT`, `websockets`, `psutil`, `uuid_v7`.
- Observability: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp`,
  `opentelemetry-instrumentation-asgi`, and `opentelemetry-instrumentation-logging`.
- Broker and ChatOps: `slack-bolt`, `langgraph`, `langchain-core`, `python-dotenv`, `pandas`.
- Credentials: `keyring`, `keyrings.cryptfile`.

Development extras are mostly shared across components:

- Tests: `pytest`, `pytest-asyncio`, `pytest-cov`.
- Static checks: `ruff`, `pylint`.
- Packaging/SBOM support: `build`, `hatchling`, component build backends, and dev-tools helpers.

The repository also contains `pyrightconfig.json` and `.flake8`; those files
document supported checker configuration even though the current setup command
does not install Pyright or Flake8.

## Test and Security Workflow

Use the developer CLI for consistent component discovery and retained results:

```bash
opamp-dev-cli build test named provider
opamp-dev-cli build test all
opamp-dev-cli build test e2e
opamp-dev-cli build secure named provider
opamp-dev-cli build secure all
```

The security command combines the configured tests with Ruff security rules,
`detect-secrets`, `pip-audit`, and reviewed Semgrep rules. It also produces a Bandit report for
comparison with Ruff. See [Testing and Result Review](testing.md) for test scope, blocking policy,
browser commands, and the exact JUnit, coverage, HTML, SARIF, and JSON result locations.

## Node And Browser Tooling

`setup-venv` runs `npm install` in these package directories when Node and npm
are available:

| Path | Primary use | Main dependencies |
|---|---|---|
| `catalog-service` | Catalog UI Playwright tests | `@playwright/test` |
| `config-service` | Config-service UI tests and unit tests | `@playwright/test`, `vitest`, `jsdom`, `js-yaml` |
| `config-service/frontend` | React/Vite config editor frontend | `react`, `react-dom`, `@rjsf/core`, `@rjsf/utils`, `@rjsf/validator-ajv8`, `typescript`, `vite`, `@vitejs/plugin-react` |
| `svr-credentials-mgr` | Credentials manager UI Playwright tests | `@playwright/test` |
| `tools/mermaid` | Mermaid diagram rendering | `@mermaid-js/mermaid-cli` |

Playwright browser installation is still handled by the developer when needed,
for example with `npx playwright install`.

## Local Workflow Tools

The main local workflow surfaces are:

- `opamp-cli`: guided start/stop/restart, status, log cleanup, config validation,
  MCP/dev helpers, container starts, and repository virtual environment setup.
- `opamp-dev-tools`: build, validation, release asset, SBOM, certificate, and
  maintenance workflows.
- `mcp/configure_mcp_clients.py` and `opamp-mcp-config`: MCP client setup for
  Claude, Codex, VS Code, LibreChat, and Gemini.
- `scripts/*`: low-level operational helpers that have not been folded into
  `opamp-dev-tools`, such as Keycloak setup, Mermaid rendering, direct Fluentd
  start, and direct Fluent Bit termination.

Container workflows use `docker` or `podman`. The CLI chooses
`OPAMP_CONTAINER_RUNTIME` first, then `docker`, then `podman`.

MCP source-mode configuration also relies on `uv` and `fastmcp` for local
stdio-style server entries.

## Behavior Flags

The most important developer-facing flags are:

| Flag | Purpose |
|---|---|
| `OPAMP_DEMO=true` | Enables demo profile start/stop actions in the CLI. |
| `APP_ENABLE_DEV_FEATURES=true` | Exposes dev-only workflows such as Fluent Bit generator utilities and PID lookup. |
| `OPAMP_CONTAINER_RUNTIME=<podman-or-docker>` | Selects the container runtime for CLI-managed development containers. |
| `OPAMP_CONFIG_PATH=<path>` | Selects the effective OpAMP config for provider/consumer workflows. |
| `PLAYWRIGHT_WATCH=true` | Runs Playwright with a visible browser, one worker, and complete trace/video/screenshot recording. |
| `PLAYWRIGHT_SLOW_MO_MS=250` | Sets the delay between Playwright browser operations in watch mode. |

## Generated State

Local setup and runtime files are intentionally separate from source
configuration:

- `.venv/`: repository-level Python environment created by `setup-venv`.
- `*/node_modules/`: Node package installs.
- `cli/runtime/`: CLI settings, process records, generated launch configs, and logs.
- `dev-tools/runtime/`: dev-tools reports and logs.
- `server-state/`: restored provider state snapshots from the previous workspace.
- `.vscode/`: restored local editor settings from the previous workspace.
- `.playwright-mcp/`: restored local Playwright MCP console logs from the previous workspace.

Do not use generated runtime files as the source of truth for new workflows.
Checked-in manifests, config files, and docs should remain authoritative.
