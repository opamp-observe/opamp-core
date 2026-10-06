---
layout: framework
title: Documentation
permalink: /
---
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

# Documentation

Welcome to the Fluent Bit & Fluentd OpAMP implementation docs. This page links to the core guides and outlines where to look for configuration, scripts, and feature notes.

## Build quick map

Use these docs for repository builds and deployable artefacts:

- [Scripts](scripts.md) — repo-wide build, packaging, SBOM, and helper script reference.
- [Setup README](README.md) — overall component and runtime map.
- [Component Versioning](dev/component_versioning.md) — how git-derived version metadata is refreshed before packaging.
- [MCP scripts and usage](../mcp/README.md) — MCP tool wheel, sdist, and SBOM flow.
- [Standalone Packaging](../config-service/docs/standalone-packaging.md) — standalone config-service packaging and SBOM flow.
- [AWS deployment](../cloud/aws/readme.md) — command-line and GitHub Actions deployment of the two-instance regression environment.
- [Azure deployment](../cloud/azure/README.md) — ARM deployment of the equivalent two-VM regression environment.

Primary repository-wide build outputs now include independent artefacts for:

- `provider`
- `consumer`
- `catalog-service`
- `cli`
- `consumer-sim`

## Core guides

- [Setup README](README.md) — full setup and run instructions.
- [Features - spec alignment](features.md) — feature notes and design direction.
- [Roadmap](roadmap/index.md) — future ideas under consideration, without timeline commitments.
- [UI examples](screenshots.md) - Some of the elements of the UI to illustrate the user experience.
- [Client (consumer)_diagrams (as images)](consumer_client_diagrams.md) — rendered consumer diagrams with explanation per diagram panel.
- [Consumer implementations](consumer_implementations.md) — built-in consumer/client matrix with OpAMP capability support and upstream agent reference links.
- [Server_(provider) diagrams (as images)](provider_server_diagrams.md) — rendered provider/server diagrams plus links to auth, endpoints, and command docs.
- [Authentication](authentication.md) — bearer token auth modes, static-token setup, Keycloak/JWT setup, and MCP token usage.
- [Web Endpoints](endpoints.md) — provider endpoint inventory, including UI/API/tool/MCP routes and `/doc-set`.
- [Provider metrics reference](provider_metrics_reference.md) — metric-by-metric explanation of the provider scrape endpoint and internal graph data.
- [Prometheus and collector setup](provider_metrics_prometheus_setup.md) — how to scrape `/metrics` securely from Prometheus or the OpenTelemetry Collector.
- The provider-hosted `Latest docs` entry point is `http://localhost:8080/doc-set`, which redirects to the URL configured in `provider.latest_docs_url`.
- [OpAMP JSON reference map](opamp_json_reference.md) — guide to which docs explain each top-level section of `config/opamp.json`.
- [Provider config reference](provider_config_reference.md) — dedicated reference for `provider.*` values, defaults, and UI editability.
- [OTLP observability config](otlp_observability.md) — shared `otlp-endpoints` settings for logs, metrics, and traces export.
- [OpAMP Config Catalog UI](opamp_config_catalog_ui.md) — configuration-driven catalog index page and help route details.
- [Self_signed_TLS_setup](self_signed_tls_setup.md) — generate local self-signed cert/key and apply config values for HTTPS testing.
- [API_gateway_suggested use and requirements](api_gateway_requirements.md) — recommended API gateway controls, internal vs external client profiles, and required auth/route hardening updates.
- [Service_daemon_setup](service_daemon_setup.md) — running provider/consumer as `systemd` or Windows services, including Fluent Bit/Fluentd launch permissions.
- [Client README](../consumer/README.md) — client/agent (aka consumer) configuration and CLI usage.
- [Server README](../provider/README.md) — server (aka provider) configuration and web UI notes.
- [Server state persistence](../provider/README.md#state-persistence-and-restore) — snapshot naming, `--restore` usage, fallback behavior, and retention.
- [MCP scripts and usage](../mcp/README.md) — MCP wrapper/canonical script behavior, FastMCP client role, command-line parameters, and verification.
- [Agent broker README](../agent_broker/README.md) — optional standalone conversation broker overview and run steps.
- [Agent broker docs index](../agent_broker/docs/README.md) — broker runbooks (startup/shutdown/logging, Slack setup, architecture notes).
- [Scripts](scripts.md) — script reference table by platform.

## Development guides

- [Development docs index](dev/index.md) — implementation internals, extension points, build workflows, and source diagrams.
- [Design & Implementation principles](dev/implementation_philosophy.md) — project architecture and engineering principles.
- [Command_process_implementation_notes](dev/command_process_implementation_note.md) — command API/queue/dispatch implementation details.
- [How to add_your_own_custom_action](dev/adding_your_own_custom_action.md) — how to implement and deploy a custom provider+consumer action using `nullcommand` as the baseline.
- [Client (consumer)_diagram (in Mermaid format)](<dev/client(consumer)/consumer_client_diagram.md>) — consumer client architecture and runtime relationship diagrams.
- [Server (provider)_server_diagrams (in Mermaid format)](<dev/server(provider)/provider_server_diagram.md>) — provider/server Mermaid source diagrams.
- [Client (consumer) use of mixins](<dev/client(consumer)/consumer_mixins.md>) — how consumer mixins are composed, dispatched, and overridden.
- [Client (consumer) custom_handlers](<dev/client(consumer)/consumer_custom_handlers.md>) — built-in custom handlers, runtime discovery, and how to implement/deploy additional handlers.
- [Client (consumer)_update_controllers](<dev/client(consumer)/consumer_update_controllers.md>) — how full update controllers drive reporting flags and outbound message field cadence.
- [OpAMP Config Catalog Service Prompt](dev/opamp_config_catalog_service_prompt.md) — implementation prompt and scope for the catalog service.
- [UI Consistency Checklist](dev/ui_consistency_checklist.md) — PR checklist for consistent UI architecture, libraries, routing, and verification.
- [Component Versioning](dev/component_versioning.md) — git commit/date version metadata and where it appears in CLI/UI help.

## Optional components

- `agent_broker` is optional and runs as a separate process.
- Provider/server and consumer/client do not require the broker to run.
- If used, start and stop the broker independently from provider and consumer.

## Documentation Rules

- Treat `dev-notes/` as internal working notes only.
- Do not cross reference `dev-notes/` content from formal project documentation (`README.md`, `docs/`, component READMEs, broker docs, or UI help pages).

## Project layout (quick view)

- `agent_broker` — optional standalone conversation broker package and docs.
- `config` — default configuration files (including `opamp.json`).
- `consumer` — the OpAMP consumer (client) package, tests, and config samples.
- `dist` — generated wheels, source distributions, manuals, and SBOM outputs
- `docs` — project documentation.
- `logs` — runtime logs created by scripts.
- `server-state` — state snapshot folder created when provider state persistence writes snapshots (folder name follows `provider.state_persistence.state_file_prefix` parent path).
- `proto` — protobuf definitions and generated artifacts.
- `provider` — the OpAMP provider (server) package, UI, and tests.
- `scripts` — helper run and shutdown scripts.
- `shared` — shared utilities used by provider/consumer.
- `src` — top-level Python package glue (if needed for tooling).
- `tests` — repository-level tests.

## Reference 3rd Party Documents

- [Open Agent Management Protocol (OpAMP) Specification](https://opentelemetry.io/docs/specs/opamp/)
- [Cloud Native Computing Foundation (CNCF)](https://www.cncf.io/)
- [OpenTelemetry at CNCF](https://www.cncf.io/projects/opentelemetry/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/specification/2025-11-25) specification - optional feature
- [Fluentd](https://www.fluentd.org/)
- [Fluent Bit](https://fluentbit.io/)
- [Manning - Logging in Action](https://www.manning.com/books/logging-in-action?query=fluent) — Fluentd-focused coverage with Kubernetes and related observability workflows.
- [Manning - Logs and Telemetry](https://www.manning.com/books/logs-and-telemetry) — Fluent Bit, Kubernetes, streaming, and OpenTelemetry-oriented coverage.
- [Quart](https://quart.palletsprojects.com/en/latest/) (foundation of the implementation)
- [HAProxy](https://www.haproxy.com/) (optional feature, to support advanced security permutations)
- [OpAMP posts on blog.mp3monster.org](https://blog.mp3monster.org/category/technology/fluent-observability/opamp/) — external blog posts and updates.


## 3rd Party Development Tools

- [pytest](https://docs.pytest.org/) — unit and integration test execution.
- [Ruff](https://docs.astral.sh/ruff/) — linting/security checks (including `--select S` rules).
- [detect-secrets](https://github.com/Yelp/detect-secrets) — repository secret scanning during security checks.
- [pip-audit](https://pypi.org/project/pip-audit/) — Python dependency vulnerability scanning.
- [esbuild](https://esbuild.github.io/) — JavaScript minification for provider UI compact assets.
- [CycloneDX](https://cyclonedx.org/) — SBOM format used for generated deployable artifact manifests.
