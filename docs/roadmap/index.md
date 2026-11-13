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

# Roadmap

This roadmap records potential future work and does not commit to delivery dates. Items are grouped
by maturity so that delivered foundations are not confused with work that remains proposed.

Status terms used here:

- **Delivered foundation**: implemented behavior exists, but follow-up work may remain.
- **Planned**: sufficiently defined to begin implementation when prioritized.
- **Research**: requires design or product decisions before implementation.

Last reviewed: 13 November 2026.

## Detailed roadmap specifications

- [Multi-agent configuration editor and Vector support](vector_multi_agent_configuration_editor.md)
  (**Planned**) — refactor `config-service` around format adapters and add schema-driven Vector
  editing as the first graph-oriented configuration format.
- [Alternate credentials mapping persistence](alternate_persistence_implementation_prompt.md)
  (**Planned**) — add a durable backend behind the existing credentials-manager persistence
  abstraction while preserving JSON compatibility and reconciliation behavior.

## Delivered foundations

The following capabilities are already present and should be extended rather than reimplemented:

- The client config generator service creates Supervisor and Observer consumer configurations as
  a provider plugin or standalone service.
- The provider implements `allow-remote-config`, capability-aware remote-config controls, file
  selection and validation, and queued remote-config offers.
- Elastic Agent, Fluent Bit, and Vector self-monitoring configuration examples are maintained under
  `docs/`.
- Local TLS certificate generation, HTTPS test deployments, Keycloak setup guidance, and
  authentication documentation are available. End-to-end mTLS remains future work.
- Components build as separate distributions, with `opamp-shared` as a runtime dependency and
  `opamp-suite` as the installation-profile meta package.
- Release tooling builds and validates component wheels and CycloneDX SBOMs, checks dependency
  closure, and publishes through `uv publish`. The GitHub release workflow separates unprivileged
  builds from PyPI Trusted Publishing, uses short-lived OIDC credentials, and generates PEP 740
  attestations.
- The repository security gate runs Ruff security rules, `detect-secrets`, `pip-audit`, Semgrep,
  and Bandit reporting.
- OWASP ZAP runs against isolated HTTP and HTTPS full-app targets, supports acknowledged active
  scans, and retains HTML, JSON, XML, and Markdown reports.

## Priority implementation areas

### Complete the remote-configuration lifecycle

The provider-side selection and offer flow is established. Remaining work should cover the complete
agent lifecycle rather than adding more transport-only demonstrations:

- configuration-status exchanges for accepted, applied, rejected, and failed terminal states;
- real configuration-file mutation with validation, atomic backup, restoration, and rollback;
- actionable diagnostics for malformed or unsupported configurations;
- recovery from interrupted or partially applied updates; and
- regression coverage using at least one real supported agent process as well as the simulator.

The catalog integration should support an explicit selection callback contract. When a caller
provides an approved callback, the catalog UI should return the ordered list of selected files to
the provider configuration workflow without weakening origin, path, or authorization checks.

### Extend the configuration editor

Implement the adapter architecture in the
[multi-agent editor specification](vector_multi_agent_configuration_editor.md). Vector is the first
planned format after Fluent Bit and Fluentd. Later candidates include:

- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/);
- [Elastic Agent](https://www.elastic.co/elastic-agent); and
- remaining [Elastic Beats](https://www.elastic.co/beats/), including
  [Heartbeat](https://www.elastic.co/beats/heartbeat).

The editor must preserve native document structure and round-trip behavior instead of forcing every
agent configuration into Fluent Bit's plugin-array model.

### Add alternate credentials mapping persistence

Implement a second `MappingPersistenceBackend` for `svr-credentials-mgr`. SQLite is the preferred
first durable backend because it preserves standalone deployment; PostgreSQL can follow if shared or
scaled deployments demonstrate the need. Keep JSON as the backward-compatible default and retain
all current stale-mapping reconciliation behavior.

See the [alternate persistence implementation prompt](alternate_persistence_implementation_prompt.md)
for configuration, testing, and acceptance criteria.

### Complete self-monitoring delivery

Build on the existing Elastic Agent, Fluent Bit, and Vector examples to support OpAMP-delivered
self-monitoring destinations. The design should:

- map OpAMP connection settings to agent-native configuration;
- use templates or adapters where agent formats differ;
- avoid embedding credentials in generated configuration when a managed reference is available;
- validate and preview generated configuration before delivery; and
- test logs, metrics, and traces independently.

### Extend security coverage

- Add authenticated ZAP Automation Framework plans for browser sessions and protected APIs.
- Add OpenAPI-driven API scans when protected HTTP surfaces publish maintained contracts.
- Add JavaScript dependency and static-analysis gates, including reviewed `npm audit`, ESLint
  security rules, and Semgrep DOM/XSS coverage.
- Add container image and runtime checks with Trivy or Grype, non-root assertions, minimal-package
  checks, and reviewed seccomp or AppArmor profiles.
- Evaluate complementary API fuzzing only after ZAP coverage and ownership are stable.

## Configuration intelligence

**Research.** Track configuration provenance and versions consistently across supported agent types,
including version-specific Fluent Bit behavior. A reusable solution should include:

- agent-specific best-practice analysis;
- relevant [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/);
- version-aware source acquisition and provenance;
- catalog reconciliation and incomplete-page diagnostics; and
- schema generation through source adapters that do not inherit Fluent Bit-specific assumptions.

Extend the existing documentation-scraping and reconciliation workflow to Fluentd before adding
further sources.

## Additional agent types

**Research.** Evaluate support based on configuration ownership, health APIs, lifecycle controls,
licensing, and realistic regression environments. Candidates include:

- [OpenObserve](https://openobserve.ai/) and its pipeline capabilities;
- [Datadog](https://www.datadoghq.com/);
- remaining [Elastic Beats](https://www.elastic.co/beats/);
- [Loggie](https://github.com/loggie-io/loggie); and
- a generic scripted agent whose lifecycle stages are supplied by deployment-owned commands.

## Automation and deployment

### Managed client deployment

**Research.** Consider an optional deployment capability that can:

- establish an authenticated connection to a client host;
- deploy a consumer in Supervisor or Observer mode;
- install or update a supported observability agent;
- deploy an initial container or configuration; and
- run as an explicit operation rather than an implicit side effect of server startup.

Prefer constrained custom commands or an external deployment integration over unrestricted SSH.
The design must define client permissions, host verification, credential ownership, audit logging,
rollback, and failure recovery before implementation.

### Supply-chain and release automation

- Register the trusted publisher for every public PyPI project and protect the GitHub `pypi`
  environment with the repository's release-approval policy.
- Evaluate [Sigstore](https://www.sigstore.dev/) signing and verification for released wheels,
  containers, SBOMs, and provenance attestations.
- Extend the version-bump workflow so requested release preparation can regenerate and validate
  SBOMs, compact UI assets, and maintained OpenAPI documents in one reviewable operation.
- Define uninstall and cleanup behavior for generated logs, state, and runtime artifacts without
  deleting deployment-owned data.

### Multi-cloud regression environments

Continue aligning AWS and Azure regression environments, then evaluate OCI support. Keep provider-
neutral evidence manifests, retained test results, targeted cleanup, and equivalent security
boundaries across implementations.

## Enhanced tooling

- Integrate the [OpAMP Signal Generator](https://github.com/opamp-observe/SignalGenerator) into
  repeatable regression scenarios where it provides coverage beyond the existing simulator.
- Add metrics and traces simulation alongside current log-oriented examples.
- Add failure injection for reconnects, timeouts, partial configuration application, and corrupted
  retained state.
- Keep generated OpenAPI contracts synchronized with protected API behavior and DAST inputs.

## Component-specific testing strategy

| Component | Primary risk areas | Recommended follow-up tests |
| --- | --- | --- |
| `config-service` browser UI | XSS, unsafe DOM writes, brittle event flows | Playwright happy/error paths, Vitest unit tests, ESLint security rules, and focused mutation tests |
| `config-service` Quart API | Authorization gaps, path traversal, validation bypass | pytest API tests, schema tests, YAML/JSON fuzzing, and negative authorization tests |
| `provider`, `consumer`, and `agent_broker` | Trust boundaries, message tampering, replay, partial failure | Contract tests, malformed-message tests, timeout/failure injection, and replay controls where protocol state permits |
| Shared schemas and models | Inconsistent validation and unsafe defaults | Compatibility tests, required-field regressions, and version upgrade/downgrade tests |
| Containers and runtime | Vulnerable images and excessive privileges | Image scans, non-root checks, minimal-package checks, and runtime profile verification |
