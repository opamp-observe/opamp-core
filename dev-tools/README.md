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
publishing, and certificate helpers.

Run from the repository root during development:

```bash
python3 dev-tools/main.py --help
python3 dev-tools/main.py build artefact all
python3 dev-tools/main.py build js-complexity
python3 dev-tools/main.py dev validate-schemas
```

Installed packages expose `opamp-dev-cli`, `opamp-cli-dev`, and the legacy
`opamp-dev-tools` command as equivalent entry points.

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

AWS uses `--storage-name` or `dist/aws-artifact-bucket.txt`; Azure uses
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

Extension guidance lives in `dev-tools/docs/CLI_EXTENSION_GUIDE.md`.
