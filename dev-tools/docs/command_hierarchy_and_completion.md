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

# Command Hierarchy and Guided Completion

`opamp-dev-cli help` renders the complete active command hierarchy from the
same `argparse` graph used for execution. The tree therefore includes
component-owned commands discovered in the selected repository:

```text
opamp-dev-cli
|-- dev
|-- fluent-resources
|-- build
|-- certificate
`-- help
```

Use standard contextual help to inspect options for one command:

```bash
opamp-dev-cli fluent-resources generate-fluentbit-assets --help
opamp-dev-cli build release-assets --help
```

## Guided mode

Starting the CLI without a command opens a guided session:

```bash
opamp-dev-cli
```

Selections accept either the displayed number or the complete option name.
Interactive terminals support case-insensitive Tab completion. The reader
prefers `prompt_toolkit`, falls back to readline when it is available, and
uses ordinary `input` for redirected or non-interactive input.

The global `--repo-root` option controls component and command discovery. The
global `--python` option selects the interpreter used for Python child tools:

```bash
opamp-dev-cli --repo-root D:/dev/opamp2 --python py help
```

## Logs and exit behavior

Executed commands write structured issue and error logs beneath
`dev-tools/runtime/logs`. Hierarchy help does not create empty command logs.
The CLI distinguishes successful completion, tool-reported issues, and runtime
errors through separate exit codes and guided-mode messages.
