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

# Developer CLI Documentation

The developer CLI provides repository maintenance, generated-resource,
build, release, test, security, certificate, and authentication workflows.
It can be run as `opamp-dev-cli`, `opamp-cli-dev`, `opamp-dev-tools`, or from
the checkout with `python3 dev-tools/main.py`.

Detailed guides:

- [Command hierarchy and guided completion](command_hierarchy_and_completion.md)
- [Developer maintenance commands](developer_maintenance.md)
- [Fluent resource commands](fluent_resources.md)
- [Build, test, and release commands](build_test_and_release.md)
- [Certificate and authentication commands](certificate_and_authentication.md)
- [Developer CLI extension and component discovery](cli_extension_guide.md)

Run `opamp-dev-cli help` to see the commands available in the current
checkout. Component-owned commands are conditional and may not appear when
their publishing component is absent.
