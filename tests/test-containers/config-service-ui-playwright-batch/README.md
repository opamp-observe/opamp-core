# config-service-ui-playwright-batch

Container harness for running Config Editor chapter-YAML validation using Playwright.

Run via convenience script:

```bash
config-service/dev-tools/run_playwright_chapter_batch_with_podman.sh
```

It is also included in the container regression pack:

```bash
python tests/test-containers/run_regression_pack.py --only config-service-ui-playwright-batch
```

The default batch config targets direct Fluent Bit chapter configuration files that are expected to survive the editor load, mutate, render, and save workflow. It excludes known non-direct artifacts, including Helm values, Kubernetes manifests, Prometheus config, Docker Compose files, and the duplicate-key `hello-world-2B.yaml` source sample. It also excludes advanced or answer/expected samples whose current syntax is not a valid single editor document or whose parser/filter shorthand is not yet expected to round-trip one-for-one through the UI mutation workflow.
