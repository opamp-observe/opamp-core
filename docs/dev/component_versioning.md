# Component Versioning

Component version metadata is derived from the current git `HEAD` commit, commit date, and latest reachable git label/tag.

- `git_commit`: short commit reference (`git rev-parse --short=12 HEAD`)
- `git_commit_date`: commit timestamp (`git show -s --format=%cI HEAD`)
- `git_commit_date_friendly`: human-friendly datetime text (for example `23 Apr 2026 00:59:06 UTC+01:00`)
- `git_label`: latest reachable label/tag from `git describe --tags --abbrev=0` (empty when no label is available)
- `effective_label`: label used in rendered `version` text:
  - commit distance is computed with `git rev-list --count <git_label>..HEAD`
  - semver labels (for example `1.2.3` or `v1.2.3`) are patch-advanced by `(<commits_since_label> + 1)`
    - examples: `1.2.3` -> `1.2.4` at label commit, `1.2.5` after one additional commit
  - `major.minor` labels (for example `1.2` or `v1.2`) are normalized as `major.minor.0`, then patch-advanced by `(<commits_since_label> + 1)`
    - examples: `1.2` -> `1.2.1` at label commit, `1.2.2` after one additional commit
  - non-semver labels are used unchanged
- `version`: formatted as:
  - `<effective_label> <git_commit> (<git_commit_date_friendly>)` when a label exists
  - `<git_commit> (<git_commit_date_friendly>)` when no label exists

Generated files:

- `provider/src/opamp_provider/version.json`
- `agent_broker/opamp_broker/version.json`
- `consumer/src/opamp_consumer/version.json`
- `consumer-sim/version.json`

The generator script is:

- `scripts/update_component_versions.py`

## Shared-core note

Version generation logic is centralized in one place (`scripts/update_component_versions.py`) and feeds all service `version.json` files.

Runtime loading remains component-local (`component_version.py` in each service) to preserve packaging boundaries:

- provider and consumer package independently
- broker package remains standalone
- consumer-sim launcher runs from its own source root

## Where version is shown

- Server CLI: `opamp-provider --help` and `opamp-provider --version`
- Server UI help page: `http://localhost:8080/help`
- Server UI Global Settings Version tab: the `opamp-server` package version from `provider/pyproject.toml` in a source checkout, or installed distribution metadata in a wheel. `opamp-cli dev-version-bump` updates the source package version; the Git-derived `version.json` is refreshed separately by the hook and build tooling.
- Broker CLI: `python -m opamp_broker.broker_app --help` and `--version`
- Consumer CLI help payload (`--help`): includes `component_version` in JSON output
- Consumer simulator launcher: `python consumer-sim/src/consumer_sim_launcher.py --help` and `--version`

## Git hook integration

The pre-commit hook updates and stages component version files automatically:

- `.githooks/pre-commit`

Install hook path once per clone:

- Linux/macOS: `./scripts/install_git_hooks.sh`
- Windows: `scripts\\install_git_hooks.cmd`

GUI clients:

- GitKraken commits use the repository git config, so after running the install script the hook is triggered for GUI commits as well.
- The installer also writes a fallback shim at `.git/hooks/pre-commit` (without overriding unrelated custom hooks) to cover clients that rely on legacy hook lookup.
- Verify current setup with:
  - `git config --local --get core.hooksPath` (expected: `.githooks`)

## Build and packaging integration

Build/package scripts refresh component version metadata before producing artifacts:

- `scripts/build_artifacts.sh`
- `scripts/build_artifacts.cmd`
- `python dev-tools/main.py build release-assets`
- `agent_broker/scripts/package.sh`
- `agent_broker/scripts/package.ps1`
