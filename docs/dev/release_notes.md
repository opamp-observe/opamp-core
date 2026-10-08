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

## 5.1
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

### Cloud Deployments
* Added equivalent two-VM regression and demonstration environments for AWS CloudFormation and Azure Resource Manager, including networking, restricted administrative access, OpAMP server and consumer roles, Keycloak, OAuth2 Proxy, Nginx, and OpenTelemetry Collectors.
* Added Bash and Windows PowerShell deployment, teardown, and artifact-packaging commands, plus GitHub Actions cloud deployments using OIDC credentials without external marketplace actions.
* Added automatic Python wheel packaging and Linux bootstrap staging, including cross-platform UTF-8 and LF normalization for scripts and wheel manifests produced on Windows.
* Added optional AWS EC2 key-pair creation with protected local PEM storage, existing-key inference from PEM filenames, automatic administrator CIDR detection, and regional key validation.
* Added timestamped retained S3 and Azure Blob storage outside the ordinary infrastructure teardown boundary, with private regression-result retention, single-target storage cleanup, and `--all` cleanup for generated OpAMP retention storage.
* Added generated Markdown connection guides containing service URLs and ready-to-run SSH commands, retained locally and in cloud storage alongside provider deployment outputs.
* Added a provider-neutral regression command that runs selected test sets and uploads complete local evidence, including failed-run status manifests, to retained AWS or Azure storage.
* Added an Azure, AWS, or build-only deployment selector to the main GitHub Actions workflow, controlled by the `CLOUD_PROVIDER` repository variable or a manual-run override. Pushes to `main` default to AWS, deploy the CloudFormation regression environment, run retained regression evidence upload, and fail the workflow when regression fails.
* Added a provider-aware GitHub OIDC setup helper that creates or updates the AWS IAM role or Azure Microsoft Entra application, configures branch-scoped GitHub federated credentials, and can write repository secrets and variables through the GitHub REST API.
* Added application-aware deployment completion and diagnostics: AWS wait conditions report VM bootstrap failures, server installer and startup logs are retained, and Keycloak readiness is checked before realm configuration.
* Added cloud regression troubleshooting notes covering GitHub action policy limits, OIDC setup gaps, mounted-checkout Git ownership checks, Windows-to-Linux line endings, consumer plugin import cycles, ST scenario evidence, and Playwright image/version drift.
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
