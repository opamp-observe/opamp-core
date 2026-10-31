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

# Release Notes

## 0.7.0 (Unreleased)

Development changes from 10 October 2026 onward are assigned to this release.
The release date is to be confirmed.

### Configuration Service and Fluent Bit catalogs

* Consolidated Config Service configuration, catalog definitions, and generated schema inputs
  under the packaged `config-service/src/config_service` tree, removing the requirement for a
  duplicate top-level artifact tree.
* Updated Config Service runtime discovery, CLI support, catalog-service sources, provider demo
  configurations, documentation, and quick-reference generators to use the canonical packaged
  tree while retaining appropriate standalone-install fallbacks.
* Extended the Fluent Bit documentation generator to reconcile scraped fields with the nearest
  earlier semantic version, or an explicitly selected previous version, and carry forward values
  that cannot be determined reliably from the newer documentation.
* Added machine-readable JSON and reviewable Markdown reports for inherited values, changed
  values, plugin and field additions, missing plugins or fields, parser limitations, naming
  collisions, and pages whose structure does not match the expected documentation pattern.
* Added mandatory, atomic ZIP backups of the packaged configuration, catalog, and schema trees
  before Fluent Bit generation or removal changes. Backup destinations are configurable and a
  backup failure stops the operation before mutation.
* Added `--remove-version` support for deleting a named Fluent Bit catalog and its associated
  generated artifacts and registry entries. Removing a current default requires an existing
  replacement version, and the operation produces JSON and Markdown audit reports.
* Added command options for explicit previous-version selection, disabling inheritance, changing
  report and backup locations, and controlling registration and runtime-schema generation.
* Added detailed scraper documentation covering source selection, GitHub-to-website fallback,
  parsing assumptions, plugin-name detection, reconciliation, incomplete-page diagnostics,
  backups, removal, reporting, and extension points for future Fluentd support.
* Removed the provisional Fluent Bit 5.1.3 catalog data after preserving the pre-change
  configuration in a timestamped backup and producing an auditable removal report.
* Expanded unit coverage for canonical path resolution, configuration backups, catalog
  reconciliation, generator orchestration, version removal, and runtime schema generation.

### CLI, packaging, and developer tooling

* Added `opamp-cli --version`, sourced from packaged component metadata with a safe fallback for
  incomplete installations, and extended unit and end-to-end coverage for the command.
* Added the ST-010 packaging and release container, which builds every packaged wheel and source
  distribution, performs isolated wheel installations, generates and validates CycloneDX SBOMs,
  and verifies installed CLI help and version entry points.
* Updated the container regression runner to include ST-004B, ST-007, ST-009, ST-010, and ST-011,
  create their evidence directories, and retain focused `--only` and `--skip` execution support.
* Added a shared container source-staging helper so test images can install tracked and
  non-ignored source safely from read-only workspace mounts.
* Aligned the developer-tools package license declaration with the current Python packaging
  metadata format.
* Added a developer CLI purge command for repository-local `*.cache`, `*.egg`, and `*.egg-info`
  directories, including dry-run preview, guided-mode access, and traversal safeguards.
* Added a developer CLI report that compares the newest retained Fluent Bit catalog with its
  nearest earlier version, identifies candidate new plugins and attributes on existing plugins,
  separates wildcard representation changes, and writes machine-readable JSON plus reviewable
  Markdown output.
* Extended the Fluent Bit additions report with an online mode that builds a transient catalog
  from a named upstream documentation version, or resolves the current stable GitHub release
  when no version is supplied. Online comparisons retain a selected local version as the
  baseline and do not register or write the retrieved catalog into the configuration tree.
* Moved Fluent Bit catalog comparison beneath the new top-level `fluent-resources` CLI command,
  keeping Fluent configuration-resource workflows separate from general repository maintenance
  commands.
* Removed the obsolete `sync config-service-json` developer command. Config Service now packages
  its canonical JSON definitions and schemas directly from `src/config_service`, so recreating
  top-level mirror trees was redundant and contradicted the consolidated source-tree design.
* Added `opamp-dev-cli help`, which renders the complete command hierarchy from the active
  argument parser, and aligned guided-menu Tab completion with `opamp-cli` by preferring
  prompt-toolkit with a readline fallback.
* Added validated component-owned developer-tool discovery. Config Service now conditionally
  publishes Fluent Bit asset and Markdown generation beneath `fluent-resources` without the
  developer CLI importing or duplicating Config Service implementation code.
* Added current-stable Fluent Bit asset generation when no version is supplied, while retaining
  named and repeated version generation, version removal, mandatory backups, reconciliation,
  registration, schema compilation, and summary controls through the consolidated CLI.
* Split developer CLI guidance into focused pages for hierarchy and completion, maintenance,
  Fluent resources, builds and releases, certificates and authentication, and extension
  manifests, with contextual links from the developer-tools README.
* Hardened Python artifact builds by clearing each component's local `build` tree before
  packaging, preventing deleted or renamed modules from leaking into wheels through stale
  setuptools output.

### Consumer and simulator

* Added an explicit `APP_ENABLE_DEV_FEATURES=true` gate before the consumer simulator launcher
  can create child processes, preventing accidental simulator startup in normal deployments.
* Removed the duplicate flat simulator metadata helper and retained
  `opamp_consumer.simulator.config_metadata` as the single package-owned implementation, with a
  package-layout regression test.
* Added the ST-009 container scenario for launcher schema validation, stale-state handling,
  scripted response behavior, and a real ten-client HTTP batch. It verifies unique identities,
  PID state, provider visibility, clean shutdown, state-file removal, and disconnect records.
* Corrected consumer hot-deploy documentation to describe Fluentd HTTP RPC reload behavior when
  an RPC endpoint is configured.

### Authentication, TLS, and security

* Added the ST-004B seven-profile container matrix covering no-auth behavior, independent static
  OpAMP and UI token scopes, cross-scope rejection, MCP disablement, malformed and expired JWTs,
  wrong issuer and audience claims, unsigned JWT rejection, and trusted versus untrusted TLS
  clients.
* Added structured evidence for authentication rejection diagnostics, route results, consumer
  registration, TLS certificates, Compose logs, and per-profile and aggregate results.
* Documented browser-origin and service-origin security boundaries, including CSRF protection,
  strict CORS and origin checks, replay controls, workload identity, and separation of UI,
  automation, agent, and MCP routes.
* Expanded authentication and self-signed TLS guidance with direct commands for running the
  complementary ST-004 Keycloak and ST-004B static-token, JWT-negative, and TLS tests.
* Documented narrowly scoped Gitleaks and detect-secrets false-positive annotations for public
  JWT audience fixtures and non-credential report keys without excluding the test tree from
  secret scanning.

### Credentials manager

* Added the ST-007 container scenario for credentials-manager CRUD and validation, assignment
  constraints, stale-mapping reconciliation, sensitive-storage separation, assigned-only live
  provider delivery to two simulator consumers, and unavailable-provider JSONL fallback.
* Added Playwright coverage for creating a complete connection definition, assigning clients,
  applying the definition, checking reconciliation and result messages, and ensuring broad list
  responses do not expose confidential definition values.
* Integrated ST-007 into the container regression pack with JUnit, API, mapping, provider,
  consumer, fallback, screenshot, trace, and aggregate result evidence.

### MCP, broker, and integration verification

* Added the ST-011 container suite for the provider MCP transport gate, JSON-RPC protocol,
  authentication, SSE/messages endpoints, client-configuration and build tools, broker startup,
  tool discovery, constrained planning, sessions, the Slack adapter, and broker proxy behavior.
* Kept ST-011 deterministic and self-contained by using local Slack and language-model doubles,
  with no external writes or model calls in its default scenario.
* Added JUnit, machine-readable summary, Markdown, and diagnostic log evidence for the new
  container scenarios.
* Clarified that the current ST-002 containers provide reusable socket and HTTP transport
  scaffolding rather than complete remote-configuration lifecycle coverage, and documented the
  remaining configuration-status, file mutation, backup, rejection, and real-agent work.

### Documentation and roadmap

* Expanded the roadmap with OpenObserve, Loggie, and generic script-driven agent candidates;
  remote-configuration UI and catalog callback concepts; SBOM, UI-minification, and OpenAPI
  refresh automation; further Azure and OCI work; and component-specific security testing.
* Updated Config Service documentation and quick references to describe canonical packaged paths
  and the revised generator, catalog, validation, and standalone packaging behavior.
* Added explicit roadmap items for future Fluentd catalog generation and complete
  remote-configuration lifecycle regression coverage, and established a repository rule that
  release-note recommendations must be reflected in the roadmap.
* Added or normalized Apache 2.0 attribution headers across the documentation changed for this
  release.

## 0.6.0

### Consumer
* Address some gaps found in the decoupling work
* Addition of the Vector agent
* Added a browser-driven container regression for UI-requested shutdown across all six built-in consumer types, including provider disconnect and process-exit evidence.
* Fixed built-in custom command discovery for consumers without an agent-specific handler directory, allowing the shared shutdown handler to be advertised and executed.
* Fixed Fluentd monitor endpoint discovery so a local bind address no longer replaces the remote OpAMP provider hostname.

### Client Config Generator Service
* Added an independently packaged, schema-driven server plugin and standalone UI for generating Supervisor and Observer consumer configurations.
* Added versioned list, load, validate, and atomic-save API controls with configured-directory containment and read-only deployment support.
* Added provider deployment discovery, build/version registration, static help, documentation, and container validation for enabled and disabled deployments.

### CLI
* Improvements around the CLI to clean up log files
* make it easier to startup demos
* base configuration enhanced to provide additional demo scenarios
* Added `cli-config` commands to view, summarize, and safely switch the active CLI demo profile configuration, with autocomplete support and friendlier interactive error messages.
* Fixed Broker startup from the CLI and source-tree command line by ensuring repo-level shared modules are importable.
* Improved background startup failures so Broker and other managed processes report a useful log detail alongside the exit code and log path.
* Added developer CLI commands to clean labelled Docker or Podman regression images and optionally include legacy `opamp-*` images.
* Added release wheel publishing from local, AWS, or Azure origins into GitHub, with automatic discovery of the newest retained AWS bucket, cloud deployment artifact fallbacks, and a separate `push-to-cloud` command for local-to-cloud transfers.
* Updated the full repository security gate to use pytest importlib mode so duplicate test filenames in component-specific test directories collect independently.

### Cloud Deployments
* Added equivalent two-VM regression and demonstration environments for AWS CloudFormation and Azure Resource Manager, including networking, restricted administrative access, OpAMP server and consumer roles, Keycloak, OAuth2 Proxy, Nginx, and OpenTelemetry Collectors.
* Added Bash and Windows PowerShell deployment, teardown, and artifact-packaging commands, plus GitHub Actions cloud deployments using OIDC credentials without external marketplace actions.
* Added automatic Python wheel packaging and Linux bootstrap staging, including cross-platform UTF-8 and LF normalization for scripts and wheel manifests produced on Windows.
* Added optional AWS EC2 key-pair creation with protected local PEM storage, existing-key inference from PEM filenames, automatic administrator CIDR detection, and regional key validation.
* Added timestamped retained S3 and Azure Blob storage outside the ordinary infrastructure teardown boundary, with private regression-result retention, single-target storage cleanup, and `--all` cleanup for generated OpAMP retention storage.
* Updated retained deployment and regression result folder names to use hyphen-separated UTC timestamps such as `yyyy-mm-dd-hh-mm-ss` without creating a nested date path hierarchy.
* Normalized agent-shutdown container evidence permissions before container removal so AWS retained-result uploads do not skip restrictive Elastic Heartbeat output files and exit with status 2.
* Added generated Markdown connection guides containing service URLs and ready-to-run SSH commands, retained locally and in cloud storage alongside provider deployment outputs.
* Added a provider-neutral regression command that runs selected test sets and uploads complete local evidence, including failed-run status manifests, to retained AWS or Azure storage.
* Added an Azure, AWS, or build-only deployment selector to the main GitHub Actions workflow, controlled by the `CLOUD_PROVIDER` repository variable or a manual-run override. Pushes to `main` default to AWS, deploy the CloudFormation regression environment, run retained regression evidence upload, and fail the workflow when regression fails.
* Added a provider-aware GitHub OIDC setup helper that creates or updates the AWS IAM role or Azure Microsoft Entra application, configures branch-scoped GitHub federated credentials, and can write repository secrets and variables through the GitHub REST API.
* Added application-aware deployment completion and diagnostics: AWS wait conditions report VM bootstrap failures, server installer and startup logs are retained, and Keycloak readiness is checked before realm configuration.
* Added cloud regression troubleshooting notes covering GitHub action policy limits, OIDC setup gaps, mounted-checkout Git ownership checks, Windows-to-Linux line endings, consumer plugin import cycles, ST scenario evidence, and Playwright image/version drift.
* Improved the AWS regression workflow failure message so a passing regression pack followed by retained evidence upload failure is reported as an upload problem, with the local upload manifest printed in the job log.
* Added deployment cost guidance, cleanup instructions, safe-rerun behavior, provider terminology, resource ownership, and failure recovery documentation in the [cloud operator guide](../../cloud/operator_guide.md), [AWS guide](../../cloud/aws/readme.md), and [Azure guide](../../cloud/azure/README.md).

### 5.0
* Decoupling of the agent logic so that the consumer is easier to extend and implement users own custom plugins if wanted


## 4.1

### Consumer
* Refinement of the output configuratios for Fluent Bit 4.2
* Client (consumer) startup as an observer refined 

### CLI
+

### Configuration Service
* Enhanced JSON schema so called_enum_options is now enum_options, and the validation process only needs to validation kind, the enum values come from enum_options not values now.
