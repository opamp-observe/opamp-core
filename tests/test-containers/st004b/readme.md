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

# ST-004B Authentication and TLS Completion Profiles

ST-004B complements the Keycloak integration in `../st004/` and closes the
remaining ST-004 authorization, route-protection, and TLS scenarios. The
harness starts each profile independently so configuration and retained logs
cannot leak between authentication modes.

## Run

Run the complete matrix:

```bash
tests/test-containers/st004b/scripts/run_st004b.sh all
```

Run one profile:

```bash
tests/test-containers/st004b/scripts/run_st004b.sh static-both
tests/test-containers/st004b/scripts/run_st004b.sh tls
```

Supported profiles are `no-auth`, `static-opamp`, `static-ui`, `static-both`,
`mcp-disabled`, `jwt-negative`, and `tls`.

## Coverage Matrix

| Profile | Coverage |
|---|---|
| `no-auth` | UI, API, tool, metrics, and OpAMP routes accept unauthenticated requests; a token-free simulator registers. |
| `static-opamp` | OpAMP rejects missing, malformed, and wrong tokens; UI/API remains public; the correct-token consumer registers and the wrong-token consumer does not. |
| `static-ui` | API, tool, metrics, SSE, messages, and MCP routes require the UI token; OpAMP remains public and an unauthenticated consumer registers. |
| `static-both` | UI and OpAMP tokens work only in their own scopes, including cross-scope rejection; the correct OpAMP consumer registers. |
| `mcp-disabled` | `/mcp` remains unavailable with `allow-mcp=false`, even with a valid UI token. |
| `jwt-negative` | A local JWKS issuer produces valid, malformed, expired, wrong-issuer, wrong-audience, and unsigned tokens; UI and OpAMP reject every invalid variant and accept the valid signed token. |
| `tls` | Plain HTTP and default system trust fail against the HTTPS listener; the generated CA succeeds; the trusted consumer registers and the untrusted consumer remains absent with actionable certificate diagnostics. |

The original `../st004/` Keycloak profile additionally verifies real
client-credentials acquisition, valid Keycloak consumers, wrong-audience
consumers, and authenticated UI/API/tool/MCP access. Together, ST-004 and
ST-004B provide the complete ST-004 scenario coverage.

## Runtime Design

- `jwt-issuer` serves an ephemeral RSA JWKS and controlled token variants.
- `provider` selects `config/provider/<profile>.json`.
- `consumer-valid` and `consumer-invalid` select profile-specific simulator
  configuration where a live consumer is part of the assertion.
- The TLS provider generates a two-day self-signed certificate with SANs for
  `provider`, `localhost`, and `127.0.0.1`. The certificate is retained only in
  ignored test evidence.
- All components stage tracked and non-ignored source into writable
  container-local storage before installation.

## Secret-Scanner Handling

The static-token values are deliberately low-risk, test-only fixtures and can
be overridden with `ST004B_OPAMP_TOKEN` and `ST004B_UI_TOKEN`. Never reuse them
as deployment credentials.

The two JWT audience values in `docker-compose.yml` are public claim selectors,
not credentials. The repository's Gitleaks pre-commit hook nevertheless matches
their `*_AUTH_JWT_AUDIENCE` variable names with its generic API-key rule. Each
of those two lines therefore carries a narrowly scoped `# gitleaks:allow`
annotation. Do not broaden the exclusion to the file or test tree. The verifier
report key named `passed` similarly carries detect-secrets' line-level
allowlist annotation because its keyword detector interprets `pass` as a
credential hint.

Validate both scanners after changing authentication fixtures:

```bash
gitleaks git --pre-commit --staged --redact --verbose
python -m detect_secrets scan --force-use-all-plugins tests/test-containers/st004b
```

Both commands must report no findings. The Gitleaks command inspects the staged
version, so stage the intended ST-004B changes before running it.

## Evidence

Each profile writes to:

```text
dist/test-reports/st004b/<profile>/
```

Evidence includes `results.md`, `summary.json`, `route-matrix.json`,
`provider.log`, `compose.log`, and `verify.log`. Negative consumer profiles also
retain `consumer-invalid.log`. The TLS profile retains its generated certificate
and private key under `tls/certs/`; these are local test artefacts and must not be
published as deployment credentials.

An aggregate result is written to:

```text
dist/test-reports/st004b/results.md
```

## Validation Commands

```bash
bash -n tests/test-containers/st004b/scripts/provider-entrypoint.sh
bash -n tests/test-containers/st004b/scripts/consumer-entrypoint.sh
bash -n tests/test-containers/st004b/scripts/run_st004b.sh
python -m py_compile tests/test-containers/st004b/scripts/jwt_issuer.py
python -m py_compile tests/test-containers/st004b/scripts/verify_st004b.py
python -m pytest -q -s tests/test_st004b_verifier.py tests/test_container_regression_pack.py
docker compose -f tests/test-containers/st004b/docker-compose.yml config --quiet
```

The complete harness requires Docker Compose and available host ports `18084`
and `18085`. Override them with `ST004B_PROVIDER_PORT` and
`ST004B_ISSUER_PORT`.
