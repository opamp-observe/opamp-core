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

# ST-007 Credentials Manager Connection Settings Container

ST-007 is a single containerized scenario with three independently reported layers. It validates
the credentials manager against its own unit/API suite, a live provider with two simulator
consumers, and the browser UI. The source checkout is mounted read-only and copied into an
isolated staging tree before packages are installed, so the run does not change the checkout.

## Coverage

The API/unit layer runs the complete `svr-credentials-mgr` and plaintext-keyring test suites. This
covers definition CRUD, schema validation, authorization modes, persistence, mapping constraints,
reconciliation, protobuf construction, provider delivery, and fallback behavior.

The live integration layer starts one provider, two simulator consumers with stable identities,
and an isolated credentials-manager service. It then verifies:

- complete `opamp`, `own_metrics`, `own_traces`, `own_logs`, and `other_connections` definitions
- rejection of unsupported URL schemes and malformed header, proxy, and `other_settings` objects
- sensitive definition values remain in the plaintext test keyring and never enter mapping storage
- many-client assignment, one-client reassignment, assigned-definition delete rejection, and stale
  mapping reconciliation
- provider queue delivery to only the assigned simulator
- the current consumer behavior, which receives and reports connection settings as unsupported
- one complete JSONL fallback record per intended client when the provider is unreachable

The Playwright layer creates a complete definition, assigns two development-mode mock clients,
applies it through the fallback path, checks reconciliation and status messages, verifies the
connection list does not expose the confidential marker, and retains a full-page screenshot and
browser trace evidence.

All services use debug logging. The credentials-manager instances use temporary plaintext storage
inside the result tree; no production keyring or production configuration is read or changed.

## Run Directly

From the repository root:

```bash
mkdir -p dist/test-reports/st007
docker build -f tests/test-containers/st007/Dockerfile -t opamp-st007-test .
docker run --rm --ipc=host \
  -e OPAMP_REPO=/workspace/opamp \
  -e RESULTS_DIR=/host-output \
  -v "$PWD:/workspace/opamp:ro" \
  -v "$PWD/dist/test-reports/st007:/host-output" \
  opamp-st007-test
```

On PowerShell, the same scenario is easiest to run through the regression pack:

```powershell
py -3.11 tests/test-containers/run_regression_pack.py --only st007
```

The container exits non-zero if any layer fails. A failure in one layer does not prevent the later
layers from running, which maximizes the evidence collected in one invocation.

## Evidence

Evidence is written under `dist/test-reports/st007/`:

| Evidence | Purpose |
|---|---|
| `summary.json`, `results.md` | Aggregate status for the API, integration, and browser layers. |
| `api-junit.xml`, `api-tests.log` | Full credentials-manager automated test result and output. |
| `connection-api.json`, `validation-errors.json` | CRUD response and malformed-definition rejections. |
| `mappings-before-reassignment.json` | Initial many-client assignment. |
| `mapping-before-reconciliation.json`, `mapping-after-reconciliation.json` | Stale mapping input and service cleanup result. |
| `mapping-storage.json`, `plaintext-test-backend.json` | Evidence that assignments and sensitive definitions use separate stores. |
| `provider-request-capture.json` | Credentials-manager response for the live provider queue request. |
| `provider-clients-before-apply.json`, `provider-clients-after-apply.json` | Provider client state before and after delivery. |
| `consumer-a.log`, `consumer-b.log` | Assigned-client isolation and current unsupported-capability diagnostics. |
| `fallback-deliveries.jsonl`, `fallback-apply-response.json` | Per-client fallback records and API response. |
| `playwright-junit.xml`, `playwright.log`, `playwright/` | Browser result, log, and trace files. |
| `screenshots/st007-browser-workflow.png` | Completed browser workflow. |

The randomly suffixed directories named `integration-runtime-*` and `ui-runtime.*` are isolated
test fixtures. They can contain synthetic confidential markers and must not be reused as
deployment configuration. A unique directory is created on every run so retained evidence from
an earlier invocation cannot change the next result.

## Troubleshooting

- If a simulator never appears, inspect `provider.log` and the corresponding consumer log. Both
  consumers require the development feature gate, which the harness sets explicitly.
- If provider delivery falls back unexpectedly, inspect `credentials-manager.log` and confirm the
  provider exposed the connection-settings endpoint on port `18080`.
- If Playwright cannot launch Chromium, rebuild the image so its Playwright package and base image
  remain on version `1.64.0`, and keep `--ipc=host` on the container run.
- If the browser test times out before navigation, inspect `ui-service.log`; the harness refuses to
  start Playwright unless the credentials-manager health endpoint becomes ready.

