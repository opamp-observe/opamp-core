<!--
Licensed under the Apache License, Version 2.0.
Copyright 2026 mp3monster.org
-->

# ST-002 Transport Baseline Scaffolding

This folder currently repeats the provider plus simulator transport baseline over WebSocket and HTTP. It does not yet queue remote configuration or assert config-status transitions, on-disk updates, backup behavior, content-type rejection, or hash mismatch handling. It is therefore scaffolding rather than complete ST-002 coverage.

The socket profile is the priority path:

```bash
tests/test-containers/st002/scripts/run_st002.sh socket
```

Run the HTTP parity path:

```bash
tests/test-containers/st002/scripts/run_st002.sh http
```

Run both:

```bash
tests/test-containers/st002/scripts/run_st002.sh all
```

## What Starts

- `provider`: retrieves the source code, installs the provider from that source,
  and starts `opamp_provider.server` with `config/provider/opamp-provider.json`.
- `consumer-socket`: retrieves its own source copy, installs the consumer, and
  starts the simulator client with WebSocket transport.
- `consumer-http`: same simulator client using HTTP transport.

By default the containers retrieve source from the mounted local checkout using
`git ls-files`, so uncommitted tracked source changes are included while ignored
runtime folders are not. Set `ST002_USE_LOCAL_SOURCE=false` to clone from
`ST002_SOURCE_REPO` and `ST002_SOURCE_REF` instead.

## Verification

`scripts/verify_st002.py` checks:

- provider readiness via `GET /api/clients`
- live client registration
- `last_channel=websocket` for the socket profile, or `last_channel=http` for
  the HTTP profile
- presence of instance UID, agent description, capabilities, and health
- matching live agent from `GET /tool/otelAgents`
- clean disconnect after writing `OpAMPSupervisor.signal`

Evidence is written under:

```text
dist/test-reports/st002/<socket|http>/
```

The primary review file is `results.md`; raw API captures are written beside it
as JSON.

## Remaining ST-002 Coverage

Add remote-config queueing and status assertions to both transport profiles, then add pinned Fluent Bit and Fluentd profiles for file replacement, preservation, and rejection behavior. The existing `tests/test-containers/opamp-consumer-deployment` harness can supply the packaged real-agent base.
