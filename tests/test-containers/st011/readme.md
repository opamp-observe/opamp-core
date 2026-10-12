# ST-011 MCP and Conversation Broker Container

Copyright 2026 mp3monster.org. Licensed under the Apache License, Version 2.0.

This container runs the provider MCP transport gate, JSON-RPC protocol, authentication, SSE/messages, client-configuration, build-tool, broker startup, tool-discovery, constrained planner, session, Slack-adapter, and broker proxy suites. Slack and LLM behavior use deterministic local doubles; the default scenario performs no external writes or model calls.

Run from the repository root:

```bash
docker build -f tests/test-containers/st011/Dockerfile -t opamp-st011-test .
docker run --rm \
  -v "$PWD:/workspace/opamp:ro" \
  -v "$PWD/dist/test-reports/st011:/host-output" \
  opamp-st011-test
```

Evidence is written to `dist/test-reports/st011/` as a JUnit report, full verification log, machine-readable summary, and Markdown result.
