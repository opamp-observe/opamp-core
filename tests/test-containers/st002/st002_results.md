<!--
Licensed under the Apache License, Version 2.0.
Copyright 2026 mp3monster.org
-->

# ST-002 Creation and Verification Results

Generated: 2026-08-11

## Outcome

The ST-002 container artefacts were created under `tests/test-containers/st002`.
The WebSocket-priority Docker Compose run could not be executed in this WSL
environment because the `docker` command is not available:

```text
The command 'docker' could not be found in this WSL 2 distro.
```

As a substitute verification of the socket transport behavior, the repository
socket E2E test was run with local socket permissions and passed:

```bash
OPAMP_SOCKET_E2E_SUMMARY_PATH=/mnt/d/dev/opamp/dist/test-reports/st002/local-socket/socket_e2e_summary.json \
python3 -m pytest -s -q tests/test_socket_e2e.py
```

Result:

```text
1 passed in 11.35s
```

Evidence:

- `dist/test-reports/st002/local-socket/socket_e2e_summary.json`

## Created Resources

| Resource | Purpose |
|---|---|
| `Dockerfile` | Shared runtime image for provider and consumer containers. |
| `docker-compose.yml` | Two-container harness with `socket` and `http` profiles. |
| `scripts/prepare-source.sh` | Retrieves source into each container from the mounted checkout or a configured Git repo/ref. |
| `scripts/provider-entrypoint.sh` | Installs provider dependencies from retrieved source and starts the provider. |
| `scripts/consumer-entrypoint.sh` | Installs consumer dependencies from retrieved source and starts simulator mode. |
| `scripts/run_st002.sh` | Builds, starts, verifies, captures logs, and tears down one or both profiles. |
| `scripts/verify_st002.py` | Verifies provider registration, channel, `/tool/otelAgents`, and disconnect evidence. |
| `config/provider/opamp-provider.json` | Provider config with auth/TLS/state persistence disabled for baseline. |
| `config/consumer/socket/*` | WebSocket-priority simulator consumer config and response data. |
| `config/consumer/http/*` | HTTP simulator consumer config and response data. |
| `readme.md` | Triggering and verification instructions. |

## Reconciliation Against ST-002

This implementation currently proves only the reusable transport baseline. Remote-config lifecycle, status, file mutation/backup, and rejection checks remain unimplemented, so this folder must not be treated as a complete ST-002 pass.

| ST-002 requirement | Coverage |
|---|---|
| Provider starts | `provider` service starts `opamp_provider.server`; verifier polls `/api/clients`. |
| Consumer connects | `consumer-socket` and `consumer-http` services run simulator consumer configs. |
| Source retrieved by containers | Each container runs `prepare-source.sh` into its own `/opt/opamp/source`. |
| Own configuration files | Provider and each consumer profile mount separate config folders read-only. |
| Socket/WebSocket connectivity prioritized | `socket` profile is the default documented path; verifier requires `last_channel=websocket`. |
| HTTP connectivity supported | `http` profile is available; verifier requires `last_channel=http`. |
| Provider records client metadata | Verifier checks instance UID, agent description, capabilities, and health. |
| `/tool/otelAgents` visibility | Verifier captures and checks `/tool/otelAgents?service_instance_id=...`. |
| Disconnect handling | Verifier writes `OpAMPSupervisor.signal` and waits for `disconnected=true`. |
| Evidence retained | `dist/test-reports/st002/<profile>/` receives JSON, logs, summary, and `results.md`. |
| Fluent Bit/Fluentd optional variants | Documented as optional follow-up using the existing deployment harness. |

## Agent Standard Review

The artefacts were reviewed against `agent.md` and updated where the file
formats allow it:

- Apache 2.0 attribution comments were added to scripts, Docker/Compose files,
  YAML metadata files, and Markdown docs.
- Provider logging was set to `DEBUG` to match the project logging baseline.
- Shell scripts now explain source staging, profile orchestration, evidence
  capture, and cleanup decisions.
- Verifier helper methods now include parameter-focused docstrings, named
  constants for API keys and evidence fields, and no single-letter variables.
- Markdown artefact names were changed to lowercase snake_case.
- JSON configs remain valid JSON, so license/comment text is kept in adjacent
  script and Markdown artefacts rather than embedded in those files.

## Commands Checked

```bash
bash -n tests/test-containers/st002/scripts/prepare-source.sh
bash -n tests/test-containers/st002/scripts/provider-entrypoint.sh
bash -n tests/test-containers/st002/scripts/consumer-entrypoint.sh
bash -n tests/test-containers/st002/scripts/run_st002.sh
python3 -m py_compile tests/test-containers/st002/scripts/verify_st002.py
python3 -m ruff check tests/test-containers/st002/scripts/verify_st002.py
python3 -m json.tool tests/test-containers/st002/config/provider/opamp-provider.json
python3 -m json.tool tests/test-containers/st002/config/consumer/socket/opamp-consumer.json
python3 -m json.tool tests/test-containers/st002/config/consumer/socket/simulator-responses.json
python3 -m json.tool tests/test-containers/st002/config/consumer/http/opamp-consumer.json
python3 -m json.tool tests/test-containers/st002/config/consumer/http/simulator-responses.json
```

All syntax/config checks passed.

## Remaining Verification

Run this on a host with Docker Compose available:

```bash
tests/test-containers/st002/scripts/run_st002.sh all
```

That will produce the full container evidence under `dist/test-reports/st002/socket`
and `dist/test-reports/st002/http`.
