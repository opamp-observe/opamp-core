# Vector Plugin E2E Container Test

This scenario validates the Vector consumer plugin against a real provider and a real Vector process.

Success criteria:

- the provider API/UI has a live Vector client entry,
- the Vector plugin reports health through OpAMP,
- the consumer connects over HTTP,
- the Vector self-monitoring configuration writes JSON metric events to `vector-self-monitor.log`.

Run from the repository root:

```bash
bash tests/test-containers/vector-plugin-e2e/scripts/run_vector_plugin_e2e.sh
```

Evidence is written to:

```text
dist/test-reports/vector-plugin-e2e/
```
