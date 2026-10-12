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

# ST-004 Keycloak Authentication Containers

This folder contains the runnable ST-004 local scenario for provider
authentication with Keycloak. It provides a Docker Compose harness that can be
run from a checkout without external SaaS services. The complementary
`../st004b/` harness covers no-auth, static-token scope separation, additional
JWT rejection cases, MCP disablement, and TLS.

Run the scenario:

```bash
tests/test-containers/st004/scripts/run_st004.sh
```

The script builds the runtime image, starts Keycloak, starts the authenticated
provider, starts one valid simulator consumer, starts one wrong-audience
simulator consumer, verifies the route matrix, captures logs, and tears the
compose project down.

## What Starts

- `keycloak`: local Keycloak with the imported `opamp` realm.
- `provider`: OpAMP provider with `opamp-use-authorization=idp`,
  `ui-use-authorization=idp`, and `allow-mcp=true`.
- `consumer-valid`: simulator consumer using Keycloak client credentials with
  the `opamp-consumer` audience.
- `consumer-wrong-audience`: simulator consumer using a valid Keycloak token
  signed by the same realm but with the wrong audience.

By default the containers retrieve source from the mounted local checkout using
`git ls-files`, so uncommitted tracked source changes are included while ignored
runtime folders are not. Set `ST004_USE_LOCAL_SOURCE=false` to clone from
`ST004_SOURCE_REPO` and `ST004_SOURCE_REF` instead.

## Verification

`scripts/verify_st004.py` checks:

- Keycloak client-credentials tokens can be acquired for UI, OpAMP, and
  wrong-audience clients.
- `/ui` rejects missing and wrong-audience bearer tokens.
- `/ui` accepts the UI-scope Keycloak token.
- `/api/clients` accepts the UI-scope Keycloak token.
- `/tool/otelAgents` accepts the UI-scope Keycloak token and exposes the valid
  simulator agent.
- `/v1/opamp` rejects missing and wrong-audience bearer tokens.
- `/v1/opamp` accepts the OpAMP-scope Keycloak token and reaches the protocol
  handler.
- the valid simulator consumer registers with the provider.
- the wrong-audience simulator consumer does not register.
- `/mcp` rejects missing and wrong-audience bearer tokens.
- `/mcp` with a valid UI-scope token reaches the MCP transport rather than
  being rejected by auth.

Evidence is written under:

```text
dist/test-reports/st004/keycloak/
```

The primary review file is `results.md`; raw route matrix, API captures, and
the wrong-audience consumer log are written beside it as evidence.

## Ports

Defaults:

| Service | Host port | Container port |
|---|---:|---:|
| Keycloak | `18082` | `8080` |
| Provider | `18083` | `8080` |

Override them when needed:

```bash
ST004_KEYCLOAK_PORT=19082 ST004_PROVIDER_PORT=19083 \
  tests/test-containers/st004/scripts/run_st004.sh
```

## Notes

This scenario intentionally uses HTTP inside the compose network and remains
focused on Keycloak/JWT route protection. The `../st004b/` TLS profile verifies
HTTPS enforcement, explicit CA trust, and rejection without trust material.
Together the two harnesses provide complete ST-004 coverage.
