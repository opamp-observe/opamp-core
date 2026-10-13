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

# Developer Maintenance Commands

The `dev` command group contains repository maintenance and artifact transfer
operations.

## Validate Config Service schemas

```bash
opamp-dev-cli dev validate-schemas
```

Validates the canonical Config Service JSON definitions and schema artifacts.
Validation findings are recorded as issues rather than hidden in console-only
output.

## Set the repository version

```bash
opamp-dev-cli dev set version --version 0.7.0
```

Updates repository-maintained version locations. Omitting `--version` allows
the workflow to request the value interactively.

## Install repository pre-commit logic

```bash
opamp-dev-cli dev apply precommit-logic
```

Configures the repository-managed Git hook behavior.

## Clean managed container images

```bash
opamp-dev-cli dev clean-images --dry-run
opamp-dev-cli dev clean-images --runtime podman
opamp-dev-cli dev clean-images --include-legacy --force
```

The command selects `--runtime`, then `OPAMP_CONTAINER_RUNTIME`, then performs
Docker/Podman auto-detection. By default it removes images labelled
`opamp-observe.managed=true`. `--include-legacy` also matches unlabelled
repositories whose final name begins with `opamp-`. Use `--dry-run` to inspect
targets before removal.

## Purge cache and egg folders

```bash
opamp-dev-cli dev purge-cache-egg --dry-run
opamp-dev-cli dev purge-cache-egg
```

Removes repository-local `*.cache`, `*.egg`, and `*.egg-info` directories. The
scan does not traverse `.git`, virtual environments, `node_modules`, or
directory links. It intentionally does not match `.pytest_cache` or
`.ruff_cache`.

## Publish and retain wheels

`upload-wheels` obtains wheels from the local `dist` tree, AWS, or Azure and
publishes them to a GitHub release:

```bash
opamp-dev-cli dev upload-wheels --origin local --release v0.7.0
opamp-dev-cli dev upload-wheels --origin aws --release v0.7.0
opamp-dev-cli dev upload-wheels --origin azure --release v0.7.0
```

`push-to-cloud` sends the newest local wheel for every package to an AWS or
Azure release folder:

```bash
opamp-dev-cli dev push-to-cloud --origin aws --release v0.7.0
opamp-dev-cli dev push-to-cloud --origin azure --release v0.7.0
```

Both commands support `--dry-run`. Use contextual `--help` for storage names,
containers, prefixes, authentication modes, and GitHub repository overrides.
