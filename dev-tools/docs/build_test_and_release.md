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

# Build, Test, and Release Commands

The `build` group discovers packaged components from first-level
`pyproject.toml` files and provides common repository output workflows.

## Package artifacts and SBOMs

```bash
opamp-dev-cli build artefact named config-service
opamp-dev-cli build artefact all
opamp-dev-cli build sbom named provider
opamp-dev-cli build sbom all
```

Artifact and SBOM builds use `uv build` and support `--no-isolation` when existing
environments
must supply the build backend. Before packaging, the CLI clears the selected
component's local `build` tree so deleted or renamed source modules cannot be
copied into a new wheel from stale setuptools output.

## Security and tests

```bash
opamp-dev-cli build secure named config-service
opamp-dev-cli build secure all
opamp-dev-cli build test named provider
opamp-dev-cli build test all
opamp-dev-cli build test e2e
opamp-dev-cli build dast baseline
```

The all-component security path runs the repository security gate. Named paths
use the selected component's configured checks. Test commands use component
metadata to select the appropriate unit and UI workflows.

Python test commands retain JUnit output under
`dev-tools/runtime/test-results/<component>/pytest.xml`; the end-to-end suite uses the `e2e`
scope. Component pytest configuration also writes `coverage.xml` in the component directory.

Playwright suites retain an HTML report, JUnit XML, and failure evidence beneath each component's
`test-results/` directory. Config-service Vitest runs retain
`config-service/test-results/vitest-junit.xml`.

Security runs retain one report set beneath
`dev-tools/runtime/security-reports/<scope>/`, where the scope is `repository` or the selected
component name:

- `pytest.xml` for the tests included in the security gate;
- `ruff.sarif` and `semgrep.sarif` for static-analysis findings;
- `bandit.json` for the report-only Python security comparison;
- `detect-secrets.json` for secret-scan candidates; and
- `pip-audit.json` for a named component's dependency vulnerability result or the repository
  manifest, with full-repository native results retained beneath `pip-audit/` for each packaged
  project's `pyproject.toml` dependencies. Generated inputs beneath `requirements/` contain the
  third-party runtime dependencies extracted from each TOML file; workspace-owned packages are
  audited separately rather than resolved from a public package index.

Ruff, secret detection, dependency auditing, and tests are blocking. Semgrep and Bandit findings
are report-only while the checked-in rules and overlap are evaluated, although scanner execution
failures remain blocking. Independent security steps continue after a failure so every available
report is retained, then the command returns one consolidated failure. Every CLI invocation also
prints the timestamped issue and error log paths written beneath `dev-tools/runtime/logs`.

The DAST command runs a pinned OWASP ZAP container against isolated full-application HTTP and HTTPS
targets on separate private networks by default. HTTP runs first; HTTPS starts only after HTTP
completes successfully and uses test-only certificate material generated inside its disposable
image. The targets contain installed runtime packages without test tools, `node_modules`, coverage
output, documentation, or developer notes, and each is removed after its scan. Use
`--external-target --target <url>` only for an intentionally separately managed deployment, which
runs one scan. Baseline mode is passive and warning-only results are non-blocking by default. Full
mode sends attack payloads and requires `--allow-active-scan`. HTTP reports are retained beneath
`dev-tools/runtime/security-reports/zap/<scope>/<mode>/`; HTTPS reports use its `https/` child
directory. Both contain HTML, JSON, XML, and Markdown formats.

See the repository [testing and result review guide](../../docs/dev/testing.md) for the complete
workflow and review order.

## Documentation and UI outputs

```bash
opamp-dev-cli build pdf
opamp-dev-cli build ui-compaction
opamp-dev-cli build js-complexity
opamp-dev-cli build docs
opamp-dev-cli build diagrams
```

- `pdf` creates the OpAMP manual and accepts an optional `--output` path.
- `ui-compaction` rebuilds provider compact JavaScript assets or removes them
  with `--clean-only`.
- `js-complexity` checks JavaScript and TypeScript functions against a
  configurable `--max-complexity`, with repeatable `--path` overrides.
- `docs` regenerates repository quick references from canonical JSON data.
- `diagrams` renders supported Mermaid diagrams.

## Release assets

```bash
opamp-dev-cli build release-assets --help
```

The composite release workflow builds selected component wheels and SBOMs,
runs the security gate before packaging, optionally builds the PDF manual and
compacted UI, and can publish the resulting assets to GitHub. Publishing,
release tag/name, draft/prerelease state, release notes, component selection,
and explicit SBOM paths are controlled through contextual options.

The default release set contains `opamp-shared`, the complete server plugin
set, `opamp-consumer`, and the `opamp-suite` meta-package so public dependency
closure can be validated before publication.

## Publish wheels to PyPI

Build the release wheels, validate them against TestPyPI without uploading,
then publish when the result has been reviewed:

```bash
opamp-dev-cli build release-assets
opamp-dev-cli dev publish-pypi --index testpypi --dry-run
opamp-dev-cli dev publish-pypi --index testpypi
opamp-dev-cli dev publish-pypi --index pypi
```

Set `UV_PUBLISH_TOKEN` for local token authentication, or use PyPI trusted
publishing in CI. The command checks the standard first-party project set and
its internal wheel dependency closure before calling `uv publish`. Use
`--allow-partial` only for an intentional subset; dependencies referenced by a
selected first-party wheel are still required in that publication set.

The GitHub workflow at `.github/workflows/publish_pypi.yml` first requires a
completed, successful run of `main_fluent-opamp.yml` for the exact commit on
`main`. It then runs the full security and release build before publishing. A
published GitHub release runs the verification, build, and publish jobs
automatically, but stops before building when no matching successful test run
exists. A manual dispatch has the same test gate and always builds and
validates the wheels, but publishes only when `publish_to_pypi` is selected
and the workflow runs from `main`. The build and publish jobs exchange an
immutable GitHub artifact; only the publish job receives `id-token: write` and
access to the protected `pypi` environment.

Create a PyPI Trusted Publisher for each of these projects:

- `opamp-shared`
- `opamp-server`
- `config-service`
- `catalog-service`
- `client-config-generator-service`
- `svr-credentials-manager-service`
- `opamp-consumer`
- `opamp-suite`
- `opamp-cli`
- `opamp-consumer-sim`

Use GitHub owner `opamp-observe`, repository `opamp-core`, workflow filename
`publish_pypi.yml`, and environment `pypi` for every publisher. Create and
protect the matching `pypi` environment in GitHub before the first release.
No PyPI API token is required for this workflow. Keep any locally used
`UV_PUBLISH_TOKEN` out of source control, shell history, and logs.
