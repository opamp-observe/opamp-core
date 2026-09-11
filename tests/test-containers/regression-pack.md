# Container Regression Pack

The container regression pack is the project-level end-to-end regression
process for Docker-backed tests. Run it from the repository root:

```bash
python tests/test-containers/run_regression_pack.py
```

List available tests without running them:

```bash
python tests/test-containers/run_regression_pack.py --list
```

Reports are written to:

```text
dist/test-reports/regression-pack/
```

## Included Tests

| Test id | Coverage |
|---|---|
| `component-wheel-deployment` | Starts from a clean container filesystem, builds every Python component wheel, installs each wheel into its own fresh virtual environment, runs `pip check`, imports primary modules, and verifies declared scripts and entry points. |
| `consumer-plugin-startup` | Builds and runs the consumer plugin startup container. It checks `fluentbit`, `fluentd`, `elastic_agent`, `elastic_heartbeat`, and `simulator` plugin selection, config loading, plugin-specific config processing, and client initialization. |
| `opamp-consumer-deployment-smoke` | Builds the current consumer wheel, builds the deployment test container, then runs Fluent Bit, Fluentd, and Elastic Heartbeat smoke-only deployments through wheel install, consumer plugin entry-point verification, and config staging. |
| `st001` | Runs the ST-001 provider/consumer simulator socket and HTTP container scenarios. |
| `st002` | Runs the ST-002 provider/consumer simulator socket and HTTP container scenarios. |
| `st004` | Runs the ST-004 provider/consumer Keycloak authorization container scenario. |
| `vector-plugin-e2e` | Starts a provider and Vector-backed consumer, then verifies the provider can see the Vector plugin reporting health and the Vector self-monitoring config writes output. |
| `config-service-ui-playwright-batch` | Builds the Config Service wheel, builds the Playwright batch container, starts Config Service in-container, and runs chapter YAML validation through Playwright. |

The pack stops on the first failing test by default. Use
`--continue-on-failure` to collect outcomes for the remaining tests.

Generated build and evidence artifacts are kept under:

- `dist/consumer/`
- `dist/test-reports/component-wheel-deployment/`
- `config-service/dist/`
- `dist/test-reports/`
