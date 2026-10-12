# ST-010 CLI Lifecycle, Packaging, and Release Container

Copyright 2026 mp3monster.org. Licensed under the Apache License, Version 2.0.

This container runs the CLI lifecycle/configuration test suites, builds and clean-installs every packaged component wheel, builds every component source distribution, generates and validates per-wheel CycloneDX SBOMs, and checks the installed `opamp-cli --help` and `opamp-cli --version` surfaces. Existing tests cover managed-process state, optional services, demo profiles, invalid targets, stale/dead state, and configuration reports.

Run from the repository root:

```bash
docker build -f tests/test-containers/st010/Dockerfile -t opamp-st010-test .
docker run --rm \
  -v "$PWD:/workspace/opamp:ro" \
  -v "$PWD/dist/test-reports/st010:/host-output" \
  opamp-st010-test
```

Evidence is written under `dist/test-reports/st010/`. The `artifacts.json` file inventories sdists, SBOMs, and installed CLI output; `wheel-deployment/` contains per-component clean-install results.
