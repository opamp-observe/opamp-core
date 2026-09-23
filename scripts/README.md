# Scripts Folder Reference

This folder now contains the scripts that still need to exist as direct
shell/Python entrypoints, plus a small number of compatibility wrappers.
Most build, packaging, certificate, schema, and maintenance workflows have
been consolidated into `opamp-dev-tools`.

Primary developer CLI:

- `python3 dev-tools/main.py --help`
- `python3 dev-tools/main.py build artefact all`
- `python3 dev-tools/main.py build release-assets`
- `python3 dev-tools/main.py build secure all`
- `python3 dev-tools/main.py build pdf`
- `python3 dev-tools/main.py certificate generate`
- `python3 dev-tools/main.py certificate ensure-provider-config`

## Current scripts

| Script | Purpose | Status |
| --- | --- | --- |
| `check_string_key_literals.py` | Repo validation helper for dictionary/payload key literal usage. | Active standalone helper |
| `configure_keycloak.sh` | Linux/macOS Keycloak setup helper for local auth testing. | Active standalone helper |
| `configure_keycloak.cmd` | Windows `cmd.exe` Keycloak setup helper. | Active standalone helper |
| `configure_keycloak.ps1` | Windows PowerShell Keycloak setup helper. | Active standalone helper |
| `render_mermaid_png.sh` | Local Mermaid-to-PNG render wrapper. | Active standalone helper |
| `security_checks.py` | Compatibility wrapper that delegates to `opamp_dev_tools.security.run_repo_security_checks`. | Kept for continuity |
| `security-checks.cmd` | Windows wrapper for `security_checks.py`. | Kept for continuity |
| `setup_local_venv.sh` | Bash helper that creates or updates the repository-root `.venv` through `python cli/main.py setup-venv`. | Active standalone helper |
| `setup_local_venv.ps1` | PowerShell helper that creates or updates the repository-root `.venv` through `python cli/main.py setup-venv`. | Active standalone helper |
| `setup_local_venv.bat` | Windows batch helper that creates or updates the repository-root `.venv` through `python cli/main.py setup-venv`. | Active standalone helper |
| `start_fluentd.sh` | Direct Fluentd launcher outside the higher-level CLI orchestration flow. | Active low-level helper |
| `start_fluentd.cmd` | Windows direct Fluentd launcher. | Active low-level helper |
| `terminate_fluent_bit.sh` | Direct emergency stop helper for `fluent-bit`. | Active low-level helper |
| `terminate_fluent_bit.cmd` | Windows direct emergency stop helper for `fluent-bit`. | Active low-level helper |
| `terminate_smart_log_viewer.cmd` | Windows helper that stops Smart Log Viewer and verifies its observed TCP ports closed. | Active low-level helper |
| `update_component_versions.py` | Compatibility wrapper for the shared git-derived version metadata logic. | Kept for continuity |

## Workflows moved to `dev-tools`

These older script-style responsibilities now live in the developer CLI:

- artefact builds
  - `python3 dev-tools/main.py build artefact all`
- release wheels + SBOMs
  - `python3 dev-tools/main.py build release-assets`
- schema validation
  - `python3 dev-tools/main.py dev validate-schemas`
- pre-commit / git hook setup
  - `python3 dev-tools/main.py dev apply precommit-logic`
- version update flow
  - `python3 dev-tools/main.py dev set version`
- PDF manual generation
  - `python3 dev-tools/main.py build pdf`
- provider UI JavaScript compaction
  - `python3 dev-tools/main.py build ui-compaction`
- self-signed certificate generation
  - `python3 dev-tools/main.py certificate generate`
- provider TLS config injection
  - `python3 dev-tools/main.py certificate ensure-provider-config`

## Notes

- `security_checks.py` remains useful for the full-repo security gate and for
  callers that still expect a plain script entrypoint.
- `setup_local_venv.sh`, `setup_local_venv.ps1`, and `setup_local_venv.bat`
  are convenience wrappers for the CLI's `setup-venv` command. Pass
  `--dry-run`, `--skip-node`, or other supported `setup-venv` options after
  the script name. After a successful interactive run, the CLI prompts to open
  an activated virtual environment shell.
- `update_component_versions.py` remains as a stable compatibility wrapper, but
  the shared implementation now lives under `dev-tools/src/opamp_dev_tools/`.
- If you are choosing a new entrypoint for development or maintenance work,
  prefer `dev-tools/main.py` unless you specifically need one of the
  low-level operational helpers listed above.
