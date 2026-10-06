# Component Wheel Deployment Container

This test starts from a clean container filesystem each run, builds all Python
component wheels, and verifies each wheel can be installed into its own fresh
virtual environment.

The test validates these components:

- `provider`
- `consumer`
- `consumer-sim`
- `config-service`
- `client-config-generator-service`
- `catalog-service`
- `cli`
- `agent_broker`
- `mcp`
- `svr-credentials-mgr/plaintext-keyring`
- `svr-credentials-mgr`
- `dev-tools`

For each component, the harness:

- builds the wheel into a shared wheelhouse
- creates a new virtual environment
- installs the component wheel using the shared wheelhouse for local package resolution
- runs `pip check`
- imports the component's primary modules
- verifies console scripts and package entry points declared in `pyproject.toml`

Run from the repository root:

```bash
docker build -f tests/test-containers/component-wheel-deployment/Dockerfile \
  -t opamp-component-wheel-deployment:latest \
  tests/test-containers/component-wheel-deployment

docker run --rm \
  -e OPAMP_REPO=/workspace/opamp \
  -e RESULTS_DIR=/host-output \
  -v "$PWD:/workspace/opamp" \
  -v "$PWD/dist/test-reports/component-wheel-deployment:/host-output" \
  opamp-component-wheel-deployment:latest
```

Results are written to:

```text
dist/test-reports/component-wheel-deployment/
```
