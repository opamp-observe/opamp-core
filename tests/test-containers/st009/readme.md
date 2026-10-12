# ST-009 Consumer Simulator Scale and Failure Container

Copyright 2026 mp3monster.org. Licensed under the Apache License, Version 2.0.

This container validates the consumer simulator development-feature gate, launcher schema and stale-state handling, scripted simulator response behavior, and a real ten-client HTTP batch against a provider. The integration check verifies unique client identities, launcher PID state, provider visibility, clean launcher shutdown, state-file removal, and provider disconnect records.

Run from the repository root:

```bash
docker build -f tests/test-containers/st009/Dockerfile -t opamp-st009-test .
docker run --rm \
  -v "$PWD:/workspace/opamp:ro" \
  -v "$PWD/dist/test-reports/st009:/host-output" \
  opamp-st009-test
```

Evidence is written to `dist/test-reports/st009/`, including JUnit XML, logs, connected/disconnected provider client payloads, and a summary.
