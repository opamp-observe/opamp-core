# Consumer Plugin Startup Regression

This containerized regression test verifies that every built-in OpAMP consumer
plugin can be selected, loaded, configured, and brought to the client
construction boundary without startup errors.

Covered service types:

- `fluentbit`
- `fluentd`
- `elastic_agent`
- `elastic_heartbeat`
- `simulator`
- `vector`

The probe intentionally stops before launching external agent binaries or
connecting to an OpAMP provider. That keeps the test deterministic while still
exercising the consumer plugin registry, config loading, plugin-specific config
processing, and client startup initialization.

## Run

From the repository root:

```bash
docker build \
  -f tests/test-containers/consumer-plugin-startup/Dockerfile \
  -t opamp-consumer-plugin-startup-regression:latest \
  tests/test-containers/consumer-plugin-startup

docker run --rm \
  -v "$PWD:/workspace/opamp" \
  opamp-consumer-plugin-startup-regression:latest
```

Reports are written under:

```text
dist/test-reports/consumer-plugin-startup/
```

Or run it through the regression pack:

```bash
python tests/test-containers/run_regression_pack.py --only consumer-plugin-startup
```
