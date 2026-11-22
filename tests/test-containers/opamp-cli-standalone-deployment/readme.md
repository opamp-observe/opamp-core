# Standalone `opamp-cli` Deployment Test

Copyright 2026 opamp.info. Licensed under the Apache License, Version 2.0.

This container builds and installs only the `opamp-cli` wheel and its runtime
dependencies. It deliberately excludes `opamp-dev-tools`, then verifies:

- the developer distribution and Python module are absent;
- none of the developer CLI executable aliases are installed;
- `opamp-cli --help` does not advertise `dev`, `dev-tests`, or `opamp-dev-cli`;
- `opamp-cli list` does not present `dev` or `dev-tests` as top-level commands.

Run it from the repository root:

```bash
docker build \
  -f tests/test-containers/opamp-cli-standalone-deployment/Dockerfile \
  -t opamp-cli-standalone-deployment:latest \
  .
docker run --rm \
  -v "$PWD/dist/test-reports/opamp-cli-standalone-deployment:/host-output" \
  opamp-cli-standalone-deployment:latest
```

Evidence is written to
`dist/test-reports/opamp-cli-standalone-deployment/` as JSON, Markdown, and a
compact summary.
