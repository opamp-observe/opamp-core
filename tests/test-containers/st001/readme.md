<!--
Licensed under the Apache License, Version 2.0.
Copyright 2026 opamp.info
-->

# ST-001 Provider and Consumer Baseline Containers

This folder contains the Docker artefacts for ST-001: provider plus simulator
consumer baseline OpAMP sessions over WebSocket and HTTP.

The socket profile is the priority path:

```bash
tests/test-containers/st001/scripts/run_st001.sh socket
```

Run the HTTP parity path:

```bash
tests/test-containers/st001/scripts/run_st001.sh http
```

Run both:

```bash
tests/test-containers/st001/scripts/run_st001.sh all
```

## What Starts

- `provider`: retrieves the source code, installs the provider from that source,
  and starts `opamp_provider.server` with `config/provider/opamp-provider.json`.
- `consumer-socket`: retrieves its own source copy, installs the consumer, and
  starts the simulator client with WebSocket transport.
- `consumer-http`: same simulator client using HTTP transport.

By default the containers retrieve source from the mounted local checkout using
`git ls-files`, so uncommitted tracked source changes are included while ignored
runtime folders are not. Set `ST001_USE_LOCAL_SOURCE=false` to clone from
`ST001_SOURCE_REPO` and `ST001_SOURCE_REF` instead.

## Verification

`scripts/verify_st001.py` checks:

- provider readiness via `GET /api/clients`
- live client registration
- `last_channel=websocket` for the socket profile, or `last_channel=http` for
  the HTTP profile
- presence of instance UID, agent description, capabilities, and health
- matching live agent from `GET /tool/otelAgents`
- clean disconnect after writing `OpAMPSupervisor.signal`

Evidence is written under:

```text
dist/test-reports/st001/<socket|http>/
```

The primary review file is `results.md`; raw API captures are written beside it
as JSON.

## Optional Real-Agent Variants

ST-001 defines Fluent Bit and Fluentd real-agent flows as optional when those
binaries are available. This folder keeps the mandatory simulator coverage
runnable without downloading real agent binaries. Use the existing
`tests/test-containers/opamp-consumer-deployment` harness for Fluent Bit/Fluentd
wheel deployment experiments, or add new ST-001 profiles here when a pinned
agent download source is required.
