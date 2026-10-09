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

# Developer CLI Extension Guide

The developer CLI lives under `dev-tools/src/opamp_dev_tools`.

## Layout

- `cli.py`: command tree and dispatch
- `runtime.py`: shared logging, subprocess execution, and prompt helpers
- `components.py`: buildable component discovery plus build/test/doc helpers
- `schema_validation.py`: config-service JSON schema/definition validation
- `versioning.py`: repository version bump logic
- `version_metadata.py`: shared git-derived version metadata helpers
- `security.py`: repository and component security checks
- `certificates.py`: self-signed certificate and Keycloak guided helpers
- `container_images.py`: Docker/Podman runtime selection and managed image cleanup
- `wheel_publish.py`: local/cloud wheel retrieval, GitHub publishing, and cloud pushes
- `release_assets.py`: release assembly and shared GitHub release API publishing

## Adding a New Command

1. Add the subparser in `cli.py`.
2. Implement the command in the closest focused module.
3. Return `True` when the command found tool issues that should cause a non-zero
   exit code without being treated as a CLI/runtime failure.
4. Record user-facing findings with `CommandRuntime.record_issue(...)`.
5. Record unexpected failures with `CommandRuntime.record_error(...)` or by
   raising an exception and letting the CLI wrapper log it.

## Logging Model

Each command writes two JSON log files into `dev-tools/runtime/logs`:

- `*-issues.json`: validation findings and tool-detected problems
- `*-errors.json`: CLI/runtime failures such as missing dependencies or failed commands

Console output mirrors the same information for interactive use.

## Compatibility Strategy

When existing repository scripts are absorbed into this CLI, keep a thin wrapper
in `scripts/` only when preserving the old entrypoint avoids breaking current
workflows or tests.
