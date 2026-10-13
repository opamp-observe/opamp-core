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

# Certificate and Authentication Commands

The `certificate` group provides guided local-development helpers. These tools
do not replace deployment-managed certificate authorities or identity
providers.

## Generate a self-signed certificate

```bash
opamp-dev-cli certificate generate
opamp-dev-cli certificate generate \
  --cert-file runtime/certs/provider.crt \
  --key-file runtime/certs/provider.key \
  --common-name localhost \
  --dns-name localhost \
  --ip-address 127.0.0.1
```

The workflow checks the cryptography dependency unless
`--skip-dependency-install` is supplied. Existing outputs require `--force`.

## Ensure provider TLS configuration

```bash
opamp-dev-cli certificate ensure-provider-config \
  --config-file config/opamp.json \
  --cert-file runtime/certs/provider.crt \
  --key-file runtime/certs/provider.key
```

This updates or creates the provider TLS object in the selected OpAMP JSON
configuration. `--trust-anchor-mode` selects the supported trust behavior.

## Configure local Keycloak

```bash
opamp-dev-cli certificate keycloak
```

The guided helper collects and applies the local Keycloak settings required by
the repository's authentication test environment.
