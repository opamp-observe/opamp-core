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

# OWASP ZAP Policies

Store reviewed OWASP ZAP packaged-scan rule configurations in this directory. Generate an initial
configuration with `opamp-dev-cli build dast baseline --generate-rules`, review every rule, and
copy the resulting `zap_generated_rules.conf` here under a target-specific snake_case name.

Do not store credentials, session tokens, or environment-specific secrets in a rule file. The
complete local workflow and report locations are documented in
[`docs/dev/dynamic_application_security_testing.md`](../../docs/dev/dynamic_application_security_testing.md).
