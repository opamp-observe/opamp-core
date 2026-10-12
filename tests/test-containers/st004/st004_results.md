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

# ST-004 Keycloak Authentication Results

This folder contains the runnable ST-004 Keycloak authentication harness.
The companion `../st004b/` harness covers the remaining authentication-mode,
JWT-negative, MCP-gate, and TLS matrix.

## Artefacts

| Artefact | Purpose |
|---|---|
| `docker-compose.yml` | Starts Keycloak, authenticated provider, valid consumer, and wrong-audience consumer. |
| `config/keycloak/opamp-realm.json` | Imports the local Keycloak realm and test clients. |
| `config/provider/opamp-provider.json` | Enables provider `idp` auth for OpAMP and UI/API/MCP routes. |
| `config/consumer/valid/` | Valid simulator consumer config using the `opamp-consumer` audience. |
| `config/consumer/wrong-audience/` | Negative simulator consumer config using the wrong JWT audience. |
| `scripts/run_st004.sh` | Builds, starts, verifies, captures logs, and tears down the compose project. |
| `scripts/verify_st004.py` | Captures the route matrix, consumer registration evidence, and MCP auth checks. |

## Validation Commands

```bash
bash -n tests/test-containers/st004/scripts/prepare-source.sh
bash -n tests/test-containers/st004/scripts/provider-entrypoint.sh
bash -n tests/test-containers/st004/scripts/consumer-entrypoint.sh
bash -n tests/test-containers/st004/scripts/run_st004.sh
python3 -m py_compile tests/test-containers/st004/scripts/verify_st004.py
python3 -m json.tool tests/test-containers/st004/config/provider/opamp-provider.json
python3 -m json.tool tests/test-containers/st004/config/consumer/valid/opamp-consumer.json
python3 -m json.tool tests/test-containers/st004/config/consumer/valid/simulator-responses.json
python3 -m json.tool tests/test-containers/st004/config/consumer/wrong-audience/opamp-consumer.json
python3 -m json.tool tests/test-containers/st004/config/consumer/wrong-audience/simulator-responses.json
python3 -m json.tool tests/test-containers/st004/config/keycloak/opamp-realm.json
```

## Run

```bash
tests/test-containers/st004/scripts/run_st004.sh
```

The run produces evidence under:

```text
dist/test-reports/st004/keycloak/
```

## Expected Result

The expected result is `passed`, with the route matrix showing:

- 401 for missing/wrong UI bearer token
- 200 for valid UI bearer token on `/ui`
- 200 for valid UI bearer token on `/api/clients` and `/tool/otelAgents`
- 401 for missing/wrong OpAMP bearer token on `/v1/opamp`
- 200 for valid OpAMP bearer token on `/v1/opamp`
- 401 for missing/wrong MCP bearer token on `/mcp`
- non-401/non-403/non-404 response for valid MCP bearer token on `/mcp`
- registered valid consumer
- absent wrong-audience consumer
