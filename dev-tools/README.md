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

# OpAMP Developer Tools

`opamp-dev-tools` is the consolidated developer CLI for repository maintenance
work such as schema validation, version updates, packaging, SBOM generation,
test execution, security checks, container image cleanup, release wheel
publishing, generated-folder cleanup, and certificate helpers.

Run from the repository root during development:

```bash
python3 dev-tools/main.py --help
python3 dev-tools/main.py build artefact all
python3 dev-tools/main.py build js-complexity
python3 dev-tools/main.py dev validate-schemas
```

Installed packages expose `opamp-dev-cli`, `opamp-cli-dev`, and the legacy
`opamp-dev-tools` command as equivalent entry points.

See the [developer CLI documentation index](docs/index.md) for the complete
set of focused command guides.

## Command Hierarchy and Guided Completion

Display the complete parser-derived command tree with:

```bash
opamp-dev-cli help
```

The hierarchy is generated from the same argument parser used to execute
commands, so newly registered command groups and nested commands appear
automatically. Standard contextual help remains available through `--help` at
every command level.

When the CLI runs without a command, guided selection prompts support Tab
completion for the option names displayed by the active menu. As with
`opamp-cli`, `prompt_toolkit` is preferred in an interactive terminal and
readline is used as a fallback when available. Numeric menu selection and
non-interactive standard input continue to work unchanged.

See [command hierarchy and guided completion](docs/command_hierarchy_and_completion.md)
for global options, interactive behavior, logging, and exit handling.

## Container Image Cleanup

Regression Dockerfiles label newly built images with
`opamp-observe.managed=true`. Cleanup uses the runtime selected by
`--runtime`, then `OPAMP_CONTAINER_RUNTIME`, then Docker/Podman auto-detection:

```bash
opamp-dev-cli dev clean-images --dry-run
opamp-dev-cli dev clean-images --runtime podman
opamp-dev-cli dev clean-images --include-legacy --force
```

The default removes only labelled project images. `--include-legacy` also
matches older, unlabelled image repositories whose final name starts with
`opamp-`.

See [developer maintenance commands](docs/developer_maintenance.md) for image
selection safeguards and the other repository maintenance workflows.

## Cache and Egg Folder Cleanup

Use the generated-folder purge to remove repository-local directories matching
`*.cache`, `*.egg`, or `*.egg-info`. The scan stays within `--repo-root`, does
not traverse `.git`, virtual environments, `node_modules`, or directory links.
Preview the exact targets before removing them with `--dry-run`:

```bash
opamp-dev-cli dev purge-cache-egg --dry-run
opamp-dev-cli dev purge-cache-egg
```

The command intentionally does not match underscore-style tool caches such as
`.pytest_cache` or `.ruff_cache`.

See [developer maintenance commands](docs/developer_maintenance.md) for the
full cleanup and artifact-transfer command set.

## Fluent Resources

When Config Service is present, its validated component manifest adds commands
that generate Fluent Bit catalogs, schemas, and Markdown references. Omitting
the version from asset generation resolves the current stable Fluent Bit
release:

```bash
opamp-dev-cli fluent-resources generate-fluentbit-assets
opamp-dev-cli fluent-resources generate-fluentbit-assets --version 5.1.3
opamp-dev-cli fluent-resources generate-fluentbit-markdown --version 5.1.3
```

The catalog additions report compares retained local Fluent Bit catalog data
or transient online documentation:

It lists both candidate new plugins and candidate attributes added to plugins
that exist in both versions. Wildcard/concrete field substitutions are reported
separately as catalog representation changes. With no version arguments it
compares the newest catalog to the nearest earlier semantic version:

```bash
opamp-dev-cli fluent-resources report-fluentbit-changes
opamp-dev-cli fluent-resources report-fluentbit-changes \
  --current-version 5.0.4 \
  --previous-version 4.2.4 \
  --output-dir config-service/reports/fluentbit
```

Add `--online` to build the target catalog in memory from upstream Fluent Bit
documentation. An omitted `--current-version` resolves the current stable
release from the Fluent Bit GitHub releases API. A named version compares that
version online, while the baseline remains a retained local catalog:

```bash
# Current stable upstream release versus the nearest earlier local catalog
opamp-dev-cli fluent-resources report-fluentbit-changes --online

# Named upstream version versus an explicit retained local baseline
opamp-dev-cli fluent-resources report-fluentbit-changes \
  --online \
  --current-version 5.1.3 \
  --previous-version 5.0.4
```

Online mode defaults to `--source auto`, which tries the Fluent Bit GitHub
documentation first and falls back to the published website. Use
`--source github` or `--source website` to require one source, `--github-ref`
to inspect a specific documentation ref, and `--timeout` to change the
per-request timeout. The transient online catalog is not registered or written
into the configuration tree; only the JSON and Markdown comparison reports are
saved.

The command prints each addition and writes equivalent JSON and Markdown
reports. Its result describes differences in catalog data. It cannot by itself
prove that an apparent addition is an upstream Fluent Bit runtime change,
because documentation coverage, parsing, or plugin naming can also differ
between versions.

See [Fluent resource commands](docs/fluent_resources.md) for generation,
removal, backup, reconciliation, schema, Markdown, and comparison details.

## Release Wheel Uploads

`upload-wheels` publishes release assets to GitHub. Its `--origin` identifies
where the wheels are retrieved from:

```bash
opamp-dev-cli dev upload-wheels --origin local --release v5.1.0
opamp-dev-cli dev upload-wheels --origin aws --release v5.1.0
opamp-dev-cli dev upload-wheels --origin azure --release v5.1.0
```

Local retrieval recursively scans `dist/`. AWS and Azure first retrieve wheels
from `releases/<release>/wheels/` in the latest recorded storage resource. If
that prefix is empty, AWS extracts wheels from
`opamp-cloud/opamp-cloud-artifacts.tar.gz`, while Azure downloads
`opamp-cloud/wheels/*.whl`.

GitHub uploads target `opamp-observe/opamp-core` by default and use
`--github-token`, `GITHUB_TOKEN`, or `GH_TOKEN`. Override the repository with
`--repository owner/name`.

AWS uses `--storage-name` or `dist/aws-artifact-bucket.txt`. When neither is
available, it queries AWS and selects the newest `opamp-regression-*` bucket by
creation time, then records that bucket in the marker file. Azure uses
`--storage-name` or `dist/azure-retention-storage-account.txt`, with the
`opamp-regression-results` release-wheel container by default.

To push locally built wheels into AWS or Azure instead, use the retained
local-to-cloud command:

```bash
opamp-dev-cli dev push-to-cloud --origin aws --release v5.1.0
opamp-dev-cli dev push-to-cloud --origin azure --release v5.1.0
```

Cloud pushes write to `releases/<release>/wheels/`. Use `--dry-run` on either
command to inspect the transfer before it runs.

See [developer maintenance commands](docs/developer_maintenance.md) for all
wheel transfer controls.

## Build, Test, and Release

The `build` group creates artifacts and SBOMs, runs component or repository
tests and security gates, builds documentation and UI outputs, and assembles
release assets.

See [build, test, and release commands](docs/build_test_and_release.md) for the
workflows and examples.

## Certificate and Authentication Helpers

The `certificate` group generates local self-signed certificates, ensures
provider TLS configuration, and guides local Keycloak setup.

See [certificate and authentication commands](docs/certificate_and_authentication.md)
for usage and scope.

## Extending the CLI

Core commands live in the developer-tools package. Component-owned tools can
publish validated manifests and appear conditionally in hierarchy help and
guided completion without being imported during CLI startup.

See the [developer CLI extension guide](docs/cli_extension_guide.md) for the
manifest contract, validation rules, execution model, and compatibility
guidance.
