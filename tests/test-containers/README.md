# Test Containers

This folder holds Docker-based test harnesses used by the project test workflow.

- `component-wheel-deployment/` - clean container harness that builds every Python component wheel and installs each component into a fresh virtual environment.
- `client-config-generator-service-deployment/` - clean container validation that the generator UI and feature menu are available only when its provider component entry is enabled.
- `opamp-consumer-deployment/` - config-driven container for testing built-in OpAMP consumer deployment types.
- `agent-shutdown-e2e/` - browser-driven provider UI regression that shuts down all six built-in consumer types and verifies process and provider state.
- `consumer-plugin-startup/` - containerized regression probe that verifies every built-in consumer plugin can load, configure, and instantiate its client.
- `vector-plugin-e2e/` - provider plus Vector-backed consumer scenario that verifies Vector health and self-monitor output.
- `run_regression_pack.py` - runs all container harnesses in the regression pack and writes JSON/Markdown outcome reports under `dist/test-reports/regression-pack/`.
- `regression-pack.md` - documents the e2e tests included in the regression pack.
- `config-service-ui-playwright-batch/` - Playwright-driven container harness for chapter-by-chapter Config Editor validation.
- `opamp-wheel-lab/` - interactive shell-first container with Fluent Bit + Fluentd preinstalled for deploying and testing project wheel files.
