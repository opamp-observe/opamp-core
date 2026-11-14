# OpAMP CLI Docs

This directory contains component-specific documentation for the OpAMP CLI.

## Documents

- `CLI_EXTENSION_GUIDE.md`: architecture, dependencies, extension rules, and worked examples for extending the CLI
- `CLI_CONFIGURATION.md`: source and runtime CLI configuration files, including demo profile and container-entry attributes
- `CLI_REBUILD_PROMPT.md`: prompt document for recreating the CLI component from scratch, including docs and deployment expectations
- `TEST_CASES.md`: maintained index of CLI unit and end-to-end test scenarios

## Current Feature Areas

- Guided lifecycle commands: `start`, `stop`, `restart`
- Runtime inspection: `status`, `list`
- Script generation: `script`
- Repository setup: `setup-venv`
- Development regression execution: `dev-tests all|unit|e2e|security|list|terminate`
- Demo/profile configuration from `cli/config/demo_consumer_profiles.json`
- Development test-suite configuration from `cli/config/dev_test_suites.json`
- Runtime preferences in `cli/runtime/settings.json`
- Config-service-backed config workflows when available:
  - `config validate <path>`
  - `config metadata <path>`

## Related Files

- `../README.md`: component overview, usage, and startup instructions
- `../../docs/dev/tooling.md`: repository-level tooling inventory and setup details
- `../src/opamp_cli/`: implementation package
- `../runtime/`: generated runtime metadata, including managed process state
