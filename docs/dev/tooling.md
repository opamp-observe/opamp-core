<!--
Copyright 2026 opamp.info
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
The checked-in `pyproject.toml`, `package.json`, workflow, and container files
remain the version source of truth; this page explains where each tool is used.

## Workstation Tools

| Tool | Requirement | Repository use |
|---|---|---|
| [Git](https://git-scm.com/) | Required | Source control, version metadata, hooks, release tags, and GitHub checkouts. |
| [Python](https://www.python.org/) 3.10 or later | Required | Services, consumers, CLIs, tests, build utilities, and cloud orchestration. |
| [uv](https://docs.astral.sh/uv/) | Required for the preferred workflow | Project synchronization, locked execution, wheel and source builds, and PyPI publication. |
| [Node.js](https://nodejs.org/) with [npm](https://docs.npmjs.com/) and [npx](https://docs.npmjs.com/cli/commands/npx) | Required for browser/UI work | Playwright and Vitest tests, Vite builds, Mermaid rendering, ESLint complexity checks, and esbuild minification. |
| [Docker](https://docs.docker.com/) or [Podman](https://podman.io/) | Required for container tests | Integration environments, isolated DAST targets, ZAP, Keycloak, and deployment tests. Docker Desktop is the normal Windows implementation. |
| [Bash](https://www.gnu.org/software/bash/) and [PowerShell](https://learn.microsoft.com/powershell/) | Platform/workflow dependent | Cross-platform setup, cloud deployment, certificate, Keycloak, and regression scripts. |
| [curl](https://curl.se/) | Workflow dependent | Health checks, GitHub API calls, downloads, and Keycloak/OIDC setup. |
| [jq](https://jqlang.org/) | Workflow dependent | JSON processing in release, Linux cloud, and bootstrap scripts. |
| [OpenSSL](https://www.openssl.org/) | Workflow dependent | Test TLS certificates, signing requests, and deployment secrets. |
| [GitHub CLI](https://cli.github.com/) | Optional | Authenticated repository configuration and token discovery for cloud/OIDC setup. |
| [AWS CLI](https://aws.amazon.com/cli/) | AWS workflows only | CloudFormation, EC2, S3, IAM/OIDC, retained evidence, and regression deployment. |
| [Azure CLI](https://learn.microsoft.com/cli/azure/) | Azure workflows only | ARM deployments, storage, OIDC login, retained evidence, and resource cleanup. |

## Preferred uv Workflow

Each deployable Python component is an independent project. [uv](https://docs.astral.sh/uv/)
resolves and executes these projects. Runtime packages
declare `opamp-shared` normally for published installations and use
`[tool.uv.sources]` to resolve the repository's `shared/` project during local
development. This keeps component wheels independent without copying the
`shared` import package into them.

Run component commands from the repository root on Windows or Linux:

```bash
uv sync --project provider --extra dev
uv run --project provider --locked python -m pytest -q -s
uv build --wheel provider
```

Use the same pattern with another component directory. The developer CLI also
uses `uv build` for repository artifact and release-wheel builds.

## Aggregate Environment Setup

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
2. Upgrade installer/build tooling: [pip](https://pip.pypa.io/),
   [setuptools](https://setuptools.pypa.io/), [wheel](https://wheel.readthedocs.io/),
   [build](https://build.pypa.io/), and [Hatchling](https://hatch.pypa.io/latest/config/build/).
3. Install root `requirements.txt`.
4. Install each local Python component editable with its `dev` extra.
5. Run `npm install` for checked-in Node tooling packages, unless `--skip-node` is supplied.

## Python Components

The setup command installs these Python component directories when their
`pyproject.toml` files are present:

| Path | Package | Build backend | Console scripts |
|---|---|---|---|
| `shared` | `opamp-shared` | [setuptools](https://setuptools.pypa.io/) | library only |
| `opamp-suite` | `opamp-suite` | [setuptools](https://setuptools.pypa.io/) | metadata package only |
| `cli` | `opamp-cli` | [setuptools](https://setuptools.pypa.io/) | `opamp-cli` |
| `provider` | `opamp-server` | [Hatchling](https://hatch.pypa.io/latest/config/build/) | `opamp-provider` |
| `consumer` | `opamp-consumer` | [Hatchling](https://hatch.pypa.io/latest/config/build/) | `opamp-consumer`, `opamp-consumer-fluentd`, `opamp-consumer-simulator` |
| `consumer-sim` | `opamp-consumer-sim` | [setuptools](https://setuptools.pypa.io/) | `opamp-consumer-sim` |
| `config-service` | `config-service` | [setuptools](https://setuptools.pypa.io/) | `config-service` |
| `catalog-service` | `catalog-service` | [setuptools](https://setuptools.pypa.io/) | `catalog-service` |
| `client-config-generator-service` | `client-config-generator-service` | [setuptools](https://setuptools.pypa.io/) | `client-config-generator-service` |
| `agent_broker` | `opamp-broker` | [Hatchling](https://hatch.pypa.io/latest/config/build/) | `opamp-broker` |
| `mcp` | `opamp-mcp-config` | [setuptools](https://setuptools.pypa.io/) | `opamp-mcp-config` |
| `dev-tools` | `opamp-dev-tools` | [setuptools](https://setuptools.pypa.io/) | `opamp-dev-tools` |
| `svr-credentials-mgr/plaintext-keyring` | `opamp-plaintext-keyring` | [setuptools](https://setuptools.pypa.io/) | keyring backend entry point |
| `svr-credentials-mgr` | `svr-credentials-manager-service` | [setuptools](https://setuptools.pypa.io/) | `svr-credentials-manager-service` |

## Python Runtime Libraries

Core runtime libraries declared across components include:

- CLI and terminal UX: [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/).
- HTTP/server frameworks: [Quart](https://quart.palletsprojects.com/),
  [HTTPX](https://www.python-httpx.org/), and [aiohttp](https://docs.aiohttp.org/).
- Protocol/config parsing: [Protocol Buffers](https://protobuf.dev/),
  [gRPC Python tools](https://grpc.io/docs/languages/python/quickstart/),
  [PyYAML](https://pyyaml.org/), [Lark](https://lark-parser.readthedocs.io/),
  [luaparser](https://github.com/boolangery/py-lua-parser),
  [jsonschema](https://python-jsonschema.readthedocs.io/), and
  [defusedxml](https://github.com/tiran/defusedxml).
- OpAMP/provider behavior: [Pydantic](https://docs.pydantic.dev/),
  [FastMCP](https://gofastmcp.com/), [PyJWT](https://pyjwt.readthedocs.io/),
  [PyNaCl](https://pynacl.readthedocs.io/),
  [websockets](https://websockets.readthedocs.io/), [psutil](https://psutil.readthedocs.io/),
  and [uuid-v7](https://pypi.org/project/uuid-v7/).
- Observability: [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/), including
  its API, SDK, OTLP exporter, ASGI instrumentation, and logging instrumentation packages.
- Broker and ChatOps: [Slack Bolt for Python](https://tools.slack.dev/bolt-python/),
  [LangGraph](https://langchain-ai.github.io/langgraph/),
  [LangChain Core](https://python.langchain.com/),
  [python-dotenv](https://github.com/theskumar/python-dotenv), and
  [pandas](https://pandas.pydata.org/).
- Credentials: [keyring](https://keyring.readthedocs.io/) and
  [keyrings.cryptfile](https://pypi.org/project/keyrings.cryptfile/).
- Python 3.10 compatibility: [tomli](https://github.com/hukkin/tomli) supplies
  TOML parsing where the standard-library `tomllib` module is unavailable.

## Python Quality, Test, and Security Tools

| Tool | How it is used |
|---|---|
| [pytest](https://docs.pytest.org/) | Python unit, integration, endpoint, and repository tests. |
| [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) | Async Quart, protocol, and service tests. |
| [pytest-cov](https://pytest-cov.readthedocs.io/) and [Coverage.py](https://coverage.readthedocs.io/) | Branch coverage, terminal missing-line reports, and `coverage.xml`. |
| [Ruff](https://docs.astral.sh/ruff/) | Formatting-independent lint, import ordering, modernization, and blocking security rules. |
| [Pylint](https://pylint.readthedocs.io/) | Module-level static quality checks. |
| [Bandit](https://bandit.readthedocs.io/) | Comparative Python security report retained by the full security gate. |
| [detect-secrets](https://github.com/Yelp/detect-secrets) | Blocking scan for potential credentials in tracked source. |
| [pip-audit](https://github.com/pypa/pip-audit) | Blocking Python dependency vulnerability audit for every packaged project. |
| [Semgrep](https://semgrep.dev/) | Repository-owned Python and JavaScript security rules with SARIF output. |
| [CycloneDX Python](https://cyclonedx-bom-tool.readthedocs.io/) | Per-wheel CycloneDX SBOM generation and validation during release builds. |

The versioned `dev-tools[security]` extra supplies the repository-wide security
toolchain. The repository also contains [Pyright](https://microsoft.github.io/pyright/)
and [Flake8](https://flake8.pycqa.org/) configuration. Those two tools are supported
configuration surfaces but are not installed or run by the current aggregate setup command.

## Test and Security Workflow

Use the developer CLI for consistent component discovery and retained results:

```bash
opamp-dev-cli build test named provider
opamp-dev-cli build test all
opamp-dev-cli build test e2e
opamp-dev-cli build secure named provider
opamp-dev-cli build secure all
opamp-dev-cli build dast baseline
```

The security command combines the configured tests with [Ruff](https://docs.astral.sh/ruff/)
security rules, [detect-secrets](https://github.com/Yelp/detect-secrets),
[pip-audit](https://github.com/pypa/pip-audit), and reviewed
[Semgrep](https://semgrep.dev/) rules. It also produces a
[Bandit](https://bandit.readthedocs.io/) report for comparison with Ruff. See
[Testing and Result Review](testing.md) for test scope, blocking policy, browser
commands, and the exact JUnit, coverage, HTML, SARIF, and JSON result locations.

Dynamic testing uses [OWASP ZAP](https://www.zaproxy.org/) through the
multi-architecture `ghcr.io/zaproxy/zaproxy:2.17.0` image pinned by OCI digest
in the developer CLI. Managed scans test HTTP first and then an HTTPS image
whose self-signed certificate is generated with [OpenSSL](https://www.openssl.org/)
during the Docker build. The CLI mounts only each generated report directory,
adds Docker's cross-platform host gateway when required, and keeps active
scanning behind `--allow-active-scan`. A packaged scan hook suppresses only
reviewed rule `10044` findings whose redirect details name
`https://htmlpreview.github.io`; other redirect findings remain enabled. See
[Dynamic Application Security Testing](dynamic_application_security_testing.md).

## Node And Browser Tooling

`setup-venv` runs `npm install` in these package directories when Node and npm
are available:

| Path | Primary use | Main dependencies |
|---|---|---|
| `catalog-service` | Catalog UI browser tests | [Playwright](https://playwright.dev/) |
| `config-service` | Config-service browser and unit tests | [Playwright](https://playwright.dev/), [Vitest](https://vitest.dev/), [jsdom](https://github.com/jsdom/jsdom), and [js-yaml](https://github.com/nodeca/js-yaml) |
| `config-service/frontend` | Schema-driven editor prototype | [React](https://react.dev/), [React DOM](https://react.dev/reference/react-dom), [RJSF](https://rjsf-team.github.io/react-jsonschema-form/), [AJV](https://ajv.js.org/), [TypeScript](https://www.typescriptlang.org/), and [Vite](https://vite.dev/) |
| `svr-credentials-mgr` | Credentials-manager UI browser tests | [Playwright](https://playwright.dev/) |
| `tools/mermaid` | Diagram rendering | [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) |

Playwright browser installation is still handled by the developer when needed,
for example with `npx playwright install`.

Additional Node tools are invoked on demand rather than installed in every
package:

- [ESLint](https://eslint.org/) 9 and the
  [TypeScript ESLint parser](https://typescript-eslint.io/) enforce configured
  JavaScript and TypeScript cyclomatic-complexity limits.
- [esbuild](https://esbuild.github.io/) generates the provider's checked-in
  `.mini.js` assets.

## Documentation and Asset Generation

| Tool | Repository use |
|---|---|
| [GitHub Pages](https://pages.github.com/) and [Jekyll](https://jekyllrb.com/) | Build and publish the formal `docs/` website. |
| [Jekyll Theme Yat](https://github.com/jeffreytse/jekyll-theme-yat) | Documentation site theme selected by `docs/_config.yml`. |
| [Jekyll Feed](https://github.com/jekyll/jekyll-feed), [Remote Theme](https://github.com/benbalter/jekyll-remote-theme), [SEO Tag](https://github.com/jekyll/jekyll-seo-tag), and [Sitemap](https://github.com/jekyll/jekyll-sitemap) | Plugins used by the GitHub Pages build. |
| [Kramdown](https://kramdown.gettalong.org/) | GitHub-Flavored Markdown processing for the Jekyll site. |
| [Mermaid](https://mermaid.js.org/) and [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) | Source-controlled diagrams and rendered image assets. |
| [ReportLab](https://www.reportlab.com/dev/docs/) | PDF manual generation by `opamp-dev-tools`. |
| [esbuild](https://esbuild.github.io/) | Provider JavaScript minification before packaging and security checks. |

## CI, Release, and Deployment Tools

| Tool | Repository use |
|---|---|
| [GitHub Actions](https://docs.github.com/actions) | Main-branch validation, GitHub Pages, cloud deployment, release verification, and PyPI publication. |
| [checkout](https://github.com/actions/checkout), [setup-python](https://github.com/actions/setup-python), and [setup-uv](https://github.com/astral-sh/setup-uv) actions | Reproducible source checkout and Python/uv setup in release jobs. |
| [GitHub Actions artifacts](https://docs.github.com/actions/using-workflows/storing-workflow-data-as-artifacts) | Transfer validated wheels between the unprivileged build job and the publication job. |
| [Astral attest action](https://github.com/astral-sh/attest-action) | Produce the PEP 740 attestation files uploaded with wheels. |
| [PyPI](https://pypi.org/) and [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) | Publish the ten first-party distributions through short-lived GitHub OIDC credentials. |
| [uv publish](https://docs.astral.sh/uv/guides/publish/) | Validate and upload the complete wheel set to TestPyPI or PyPI. |
| [PEP 740 attestations](https://peps.python.org/pep-0740/) | Generate digital attestations for GitHub-built Python distributions. |
| [AWS CLI](https://aws.amazon.com/cli/) and [AWS CloudFormation](https://aws.amazon.com/cloudformation/) | Provision AWS regression infrastructure, retained S3 evidence, and OIDC roles. |
| [Azure CLI](https://learn.microsoft.com/cli/azure/) and [ARM templates](https://learn.microsoft.com/azure/azure-resource-manager/templates/) | Provision Azure regression infrastructure and retained Blob Storage evidence. |
| [Keycloak](https://www.keycloak.org/) | Local and cloud identity-provider test boundary configured through container scripts and `kcadm.sh`. |
| [OpenID Connect](https://openid.net/developers/how-connect-works/) | Short-lived GitHub-to-cloud and GitHub-to-PyPI authentication. |

## Local Workflow Tools

The main repository-provided workflow surfaces are:

- `opamp-cli`: guided start/stop/restart, status, log cleanup, config validation,
  MCP/dev helpers, container starts, and repository virtual environment setup.
- `opamp-dev-tools`: build, validation, release asset, SBOM, certificate, and
  maintenance workflows, including Docker-backed
  [OWASP ZAP](https://www.zaproxy.org/) runtime scans.
- `mcp/configure_mcp_clients.py` and `opamp-mcp-config`: MCP client setup for
  [Claude](https://claude.ai/), [Codex](https://openai.com/codex/),
  [Visual Studio Code](https://code.visualstudio.com/),
  [LibreChat](https://www.librechat.ai/), and [Gemini](https://gemini.google.com/).
- `scripts/*`: low-level operational helpers that have not been folded into
  `opamp-dev-tools`, such as [Keycloak](https://www.keycloak.org/) setup,
  [Mermaid](https://mermaid.js.org/) rendering, direct
  [Fluentd](https://www.fluentd.org/) start, and direct
  [Fluent Bit](https://fluentbit.io/) termination.

Container workflows use [Docker](https://docs.docker.com/) or
[Podman](https://podman.io/). The CLI chooses
`OPAMP_CONTAINER_RUNTIME` first, then `docker`, then `podman`.

[Model Context Protocol](https://modelcontextprotocol.io/) source-mode
configuration also relies on [uv](https://docs.astral.sh/uv/) and
[FastMCP](https://gofastmcp.com/) for local stdio-style server entries.

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
