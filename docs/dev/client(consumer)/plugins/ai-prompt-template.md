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

# AI Prompt Template

This guide is meant to be usable without AI assistance. Still, if a developer
does want to generate a first draft with an AI tool, use a prompt like this and
then review the generated code carefully.

Replace the bracketed sections before sending the prompt.

```text
You are working in the OpAMP consumer repository.

Goal:
Create a new OpAMP consumer plugin for [AGENT NAME]. The plugin service_type
must be [SERVICE_TYPE]. The plugin should support [SUPERVISOR, OBSERVER, OR BOTH]
mode.

Read these existing docs first:
- docs/dev/client(consumer)/plugins/index.md
- docs/dev/client(consumer)/plugins/architecture-and-loading.md
- docs/dev/client(consumer)/plugins/implementation-contract.md
- docs/dev/client(consumer)/plugins/configuration-hooks.md
- docs/dev/client(consumer)/plugins/testing-a-plugin.md
- docs/dev/client(consumer)/plugins/packaging-and-deployment.md
- docs/dev/client(consumer)/consumer_client_diagram.md
- docs/dev/client(consumer)/consumer_mixins.md
- consumer/README.md

Existing code to inspect:
- consumer/src/opamp_consumer/plugin_loader.py
- consumer/src/opamp_consumer/plugin_config.py
- consumer/src/opamp_consumer/abstract_client.py
- consumer/src/opamp_consumer/client_runtime_mixin.py
- consumer/src/opamp_consumer/client_supervisor_mixin.py
- consumer/src/opamp_consumer/client_observer_mixin.py
- consumer/src/opamp_consumer/fluentbit/client.py
- consumer/src/opamp_consumer/fluentd/client.py
- consumer/src/opamp_consumer/elastic_agent/client.py
- consumer/src/opamp_consumer/simulator/client.py

Agent details:
- executable command: [COMMAND]
- config file flag: [CONFIG FLAG, FOR EXAMPLE -c OR --config]
- local health/status endpoints: [ENDPOINTS AND PORT RULES]
- version discovery method: [HTTP ENDPOINT, CLI COMMAND, FILE, OR NONE]
- remote config support: [YES/NO, WITH DETAILS]
- hot reload support: [YES/NO, WITH DETAILS]
- process detection regex for observer mode: [REGEX]
- plugin-specific config fields: [FIELDS, TYPES, DEFAULTS, ENV OVERRIDES]
- expected capabilities: [CAPABILITY NAMES]

Implementation requirements:
1. Create the plugin package at [PACKAGE LOCATION].
2. Provide a zero-argument main() entry point.
3. Use the shared common CLI parser and config loading helpers.
4. Configure logging and call log_consumer_startup_banner().
5. Implement process_consumer_config(context) if plugin-specific config is needed.
6. Subclass AbstractOpAMPClient unless there is a clear reason not to.
7. Use the shared supervisor/observer lifecycle strategy unless the agent truly
   needs a custom lifecycle.
8. Add or update entry points under opamp_consumer.plugins.
9. Add operator-facing plugin configuration docs under consumer/docs/plugins/.
10. Add developer-facing notes only if this plugin has unusual lifecycle,
    config, or packaging behavior.

Testing requirements:
1. Add plugin-specific tests under consumer/tests/[SERVICE_TYPE]/ or the
   external plugin package's own tests directory.
2. Add config hook coverage for consumer.[SERVICE_TYPE].
3. Add plugin loader coverage if the registry behavior changes.
4. Add entrypoint/routing coverage if the startup path changes.
5. Add supervisor and observer mode tests or explain why one mode is not
   supported.
6. Run the relevant pytest commands and report the results.

Documentation requirements:
1. Update consumer/docs/plugins/[SERVICE_TYPE].md with config examples.
2. Update consumer/README.md plugin links if this is an in-repo plugin.
3. Reference the developer plugin guide rather than duplicating architecture
   explanations.
4. Include packaging/deployment instructions for the plugin.

Constraints:
- Use Apache 2.0 license headers with `Copyright 2026 opamp.info`, following
  the repository root `license.txt`.
- Keep edits scoped to the plugin and required shared extension points.
- Do not add plugin-specific branches to consumer/src/opamp_consumer/config.py
  when a process_consumer_config hook can own the behavior.
- Preserve existing tests and behavior for Fluent Bit, Fluentd, Elastic Agent,
  Elastic Heartbeat, and simulator.
- Use existing code style and type hints.
- Avoid broad refactors.

Deliverables:
- code
- tests
- docs
- packaging metadata
- verification summary
```

The generated result should be treated as a draft. A human reviewer still needs
to check process lifecycle behavior, config path handling, capability choices,
and deployment packaging.

