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

# ST-004B Expected Results

## Artefacts

| Artefact | Purpose |
|---|---|
| `docker-compose.yml` | Provides the shared issuer, provider, and positive/negative consumer services. |
| `config/provider/*.json` | Isolates provider auth, MCP, and TLS modes by profile. |
| `config/consumer/*/*.json` | Defines valid and intentionally rejected simulator consumers. |
| `scripts/jwt_issuer.py` | Serves local JWKS and controlled valid/invalid JWTs without an external IdP. |
| `scripts/verify_st004b.py` | Executes route, registration, log, JWT, and TLS assertions and writes evidence. |
| `scripts/run_st004b.sh` | Runs profiles sequentially and aggregates their results. |

## Expected Result

All seven profiles report `passed`. Authorization profiles must emit structured
provider rejection logs containing mode, method, path, and reason. Negative
consumers must remain absent from provider state, and their logs must identify
the authorization or certificate failure.

The authoritative per-run results are generated under
`dist/test-reports/st004b/`; this document describes the expected outcome and
does not represent a recorded execution.
