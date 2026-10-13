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

The core developer CLI lives under `dev-tools/src/opamp_dev_tools`. Commands
that inherently belong to another component may be published by that component
without moving or duplicating their implementation.

## Core layout

- `cli.py`: core command tree, guided menus, and dispatch
- `command_help.py`: parser-derived command hierarchy rendering
- `component_tools.py`: component manifest discovery, validation, registration,
  guided metadata, and subprocess execution
- `interactive_completion.py`: guided completion through prompt-toolkit/readline
- `runtime.py`: logging, subprocess execution, and issue/error reporting
- `components.py`: packaged-component discovery and build/test helpers
- `schema_validation.py`: Config Service JSON validation
- `versioning.py`: repository version updates
- `security.py`: repository and component security gates
- `certificates.py`: self-signed certificate and Keycloak helpers
- `container_images.py`: managed image cleanup
- `fluentbit_changes.py`: Fluent Bit catalog comparison and reporting
- `wheel_publish.py`: local/cloud wheel retrieval, publishing, and retention
- `release_assets.py`: composite release assembly and GitHub publication

## Adding a core command

1. Register its parser in `cli.py`.
2. Implement the behavior in the closest focused module.
3. Add guided-mode collection when interactive use is appropriate.
4. Return `True` for tool findings that should use the issues exit code.
5. Record findings with `CommandRuntime.record_issue(...)`.
6. Raise unexpected failures or record them with
   `CommandRuntime.record_error(...)`.
7. Add unit tests and update the relevant focused documentation page.

The parser-derived hierarchy updates automatically. Guided selection menus
pass active labels to the shared completion reader.

## Publishing a component-owned command

A first-level component publishes optional commands by adding:

```text
<component>/dev-tools/opamp_dev_cli_tools.json
```

The manifest uses schema version 1:

```json
{
  "schema_version": 1,
  "tools": [
    {
      "id": "example_tool",
      "command_group": "fluent-resources",
      "command": "generate-example",
      "description": "Generate example component resources",
      "script": "dev-tools/generate_example.py",
      "arguments": [
        {
          "destination": "versions",
          "flags": ["--version"],
          "action": "append",
          "help": "Version to generate",
          "prompt": "Version(s), comma-separated"
        }
      ]
    }
  ]
}
```

Supported argument actions are `store`, `append`, and `store_true`. Scalar
types are `string` and `integer`. Optional `choices`, `required`, `prompt`, and
`default` fields control direct validation and guided collection. Defaults are
used only to explain guided behavior; omitted direct values remain owned by the
component script.

Mutually exclusive operations can reference an `exclusive_group`. Define the
group at tool level with its prompt and no-selection behavior:

```json
{
  "exclusive_groups": [
    {
      "id": "operation",
      "prompt": "Operation",
      "allow_none": true,
      "none_label": "Run the component default operation"
    }
  ]
}
```

Arguments in that group should provide `selection_label` for the guided menu.
Arguments that apply only to selected operations may provide a `guided_for`
array containing argument destinations or `component-default`. This controls
guided questions only; direct command-line validation remains the component
script's responsibility.

## Discovery and safety behavior

The CLI scans only first-level components beneath `--repo-root`. A manifest is
accepted only when:

- it is valid JSON using the supported schema version;
- command, group, and destination identifiers use stable lowercase forms;
- all argument actions and value types are supported;
- referenced exclusive groups exist;
- command paths and destinations are not duplicated; and
- the Python script exists and resolves inside the publishing component.

Invalid optional manifests are ignored and logged at DEBUG level. They cannot
prevent core commands from starting. Scripts are not imported during parser
construction. Execution uses the selected `--python` interpreter through
`CommandRuntime`, with the repository root as the working directory.

Config Service provides the reference implementation in
`config-service/dev-tools/opamp_dev_cli_tools.json`.

## Logging model

Executed commands write two JSON logs beneath `dev-tools/runtime/logs`:

- `*-issues.json`: validation findings and tool-detected problems
- `*-errors.json`: CLI failures, missing dependencies, and failed child commands

Console output mirrors important records for interactive use.

## Compatibility

Keep an old script entry point when existing automation depends on it. The
component manifest should invoke that same implementation so the direct script
and consolidated CLI do not diverge.
