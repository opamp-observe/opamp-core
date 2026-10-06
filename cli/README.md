# OpAMP CLI Component

This component provides a prompt-driven command tool for local OpAMP workflows.
Autocomplete support is provided via `prompt_toolkit` (cross-platform).
Its guided `start`, `stop`, and `restart` flows run components directly instead of depending on repo wrapper scripts.
Guided starts record launched PIDs in `cli/runtime/managed_processes.json`.
CLI-managed process logs are written under `cli/runtime/logs/`.
Managed process entries are only recorded after the launched utility survives the CLI startup liveness check.
The CLI can also open a separate tail shell for managed process logs when `enable-process-tail` is enabled.

## Structure

- `README.md`: component overview and startup guide
- `scripts/`: shell-specific helper scripts for alias / macro setup
- `docs/`: component-specific documentation and implementation notes
- `src/opamp_cli/`: implementation package
- `runtime/`: generated runtime metadata, process state, and log files
- `pyproject.toml`: packaging metadata and console entrypoint
- `requirements.txt`: runtime requirements

## How To Run

You can run the CLI either from the repository root or from inside the `cli/` directory.

From repository root:

- `python3 cli/main.py`
- `PYTHONPATH=cli/src python3 -m opamp_cli`
- `python3 -m cli`
- `python3 -m pip install -e cli && opamp-cli`

From the `cli/` directory:

- `python3 main.py`
- `PYTHONPATH=src python3 -m opamp_cli`
- `python3 -m pip install -e . && opamp-cli`

## Shell Setup

If you want a persistent shell shortcut for `opamp-cli` and `opamp`, use the helper script for your shell:

Linux / macOS shells:

```bash
./cli/scripts/install_cli_aliases.sh
```

Windows `cmd.exe`:

```cmd
cli\scripts\install_cli_aliases.cmd
```

Windows PowerShell:

```powershell
.\cli\scripts\install_cli_aliases.ps1
```

What these do:

- `install_cli_aliases.sh`: updates `~/.bashrc` and `~/.zshrc`
- `install_cli_aliases.cmd`: writes a `doskey` macro file and shows the optional `AutoRun` command
- `install_cli_aliases.ps1`: updates the current PowerShell profile and legacy Windows PowerShell profile when needed

All three create:

- `opamp-cli`
- `opamp`

Both shortcuts run the compatibility entrypoint:

- `python .../cli/main.py`

## Documentation

- [docs/README.md](/mnt/d/dev/opamp/cli/docs/README.md)
- [docs/CLI_CONFIGURATION.md](/mnt/d/dev/opamp/cli/docs/CLI_CONFIGURATION.md)
- [docs/CLI_EXTENSION_GUIDE.md](/mnt/d/dev/opamp/cli/docs/CLI_EXTENSION_GUIDE.md)
- [docs/CLI_REBUILD_PROMPT.md](/mnt/d/dev/opamp/cli/docs/CLI_REBUILD_PROMPT.md)

## Basic Usage

- Guided multi-stage flow:
  - Type `start` in interactive mode, then choose what to start
    (for example `server`, `catalog`, `config editor`, `broker`, `simulator`, `fluentbit client`, `fluentd client`, `vector client`).
  - Type `stop` in interactive mode, then choose what to stop.
  - `stop all` stops all CLI-managed recorded processes.
  - Type `restart` in interactive mode, then choose what to restart.
  - You can also run guided actions directly on one line, for example `start server`, `stop config editor`, or `restart server`.
  - Type `status` in interactive mode to list the effective OpAMP config file,
    config load status, managed processes, PID liveness, and log paths.
  - Type `cli-config view` to print the active CLI demo profile config file in full, followed by its absolute path.
  - Type `cli-config summary` to print a brief bullet summary of the active CLI demo profile config and its absolute path.
  - Type `cli-config change-config` to prompt for a replacement CLI demo profile config file. The CLI loads the replacement before saving it as active; if loading fails, the current config remains unchanged and the console reports the cause.
  - Type `clear-logs` to remove CLI-managed log files plus log files discovered
    from the effective OpAMP config and demo profile defaults.
  - Type `setup-venv` to create or update the repository-level `.venv`, install
    Python dependencies and editable dev extras, and install Node tooling.
  - Type `list` in interactive mode to display the current command hierarchy, guided options, and available `config` subcommands when config-service support is present.
  - Type `enable-process-tail` to open a separate tail shell for each future managed start log.
  - Type `disable-process-tail` to turn that behavior off again.
  - When `APP_ENABLE_DEV_FEATURES=true` and the Fluent Bit generator scripts are present, type `dev-flb-config` to open a guided prompt for the Fluent Bit asset/markdown utilities.
  - When `APP_ENABLE_DEV_FEATURES=true`, type `dev-pid-lookup` to prompt for a regular expression and report matching running process IDs with process details.
  - `Catalog` is shown when catalog sources are configured in `config/opamp.json`. The CLI writes a temporary runtime config under `cli/runtime/` so the catalog can be launched without editing the repo config.
- Config file workflows:
  - Type `config validate <file-or-folder>` to validate one supported config file or every supported config file beneath a directory.
  - Type `config metadata <file-or-folder>` to add missing config-service metadata headers for config type and version.
  - Supported file extensions are `.yaml`, `.yml`, and `.conf`.
  - These commands are only shown and enabled when the CLI can detect config-service logic in the repository or installed environment.
  - Each run writes a timestamped report file under `cli/runtime/logs/` and also prints the same report to the console.
  - Reports include the file path plus either `Validation result: no error` or a normalized issue list.
  - Multi-file reports use three blank lines between file sections for readability.
  - `config metadata` does not overwrite existing `config-service` header values when both config type and version are already present.
- If the first word is `script`, a script file is generated for the current OS:
  - Linux/macOS: `.sh`
  - Windows: `.cmd`
- Otherwise, the command is executed immediately.
- Direct Python script commands are supported. If a command starts with a `.py`/`.pyw` file path
  (for example `cli/main.py --help`), the CLI automatically runs it via Python.

Examples:

```text
script demo-start-clients python -m opamp_consumer.fluentbit.client
python -m pytest -s
cli/main.py --help
opamp-cli status
opamp-cli list
opamp-cli cli-config view
opamp-cli cli-config summary
opamp-cli cli-config change-config
opamp-cli config validate ./example/fluent-bit.yaml
opamp-cli config metadata ./example/configs
opamp-cli setup-venv --dry-run
opamp-cli setup-venv
opamp-cli enable-process-tail
APP_ENABLE_DEV_FEATURES=true opamp-cli dev-flb-config
APP_ENABLE_DEV_FEATURES=true opamp-cli dev-pid-lookup
APP_ENABLE_DEV_FEATURES=true opamp-cli dev-version-bump
APP_ENABLE_DEV_FEATURES=true opamp-cli dev-version-bump 0.5.0
opamp-cli dev-containers
```

When `SMART_LOG_VIEWER=true` is used with `enable-process-tail`,
`smart-log-viewer` also needs a `tail` executable on `PATH`. On Windows,
install Microsoft Coreutils with:

```powershell
winget install --id Microsoft.Coreutils --exact
```

Guided examples:

```text
opamp-cli start server
opamp-cli stop all

opamp-cli
opamp> start config editor
```

Demo consumer mode:

- Set `OPAMP_DEMO=true` to expose profile-based demo consumer actions in guided `start` and `stop`.
- Demo profiles are loaded from `cli/config/demo_consumer_profiles.json`.
- `cli-config change-config` can select a different JSON file with the same
  profile schema. The selected absolute path is stored in
  `cli/runtime/settings.json` as runtime state, not source configuration.
- Each demo profile can include a `scenario_description` field.
- In interactive or direct CLI mode, `demo` acts as shorthand for `start demo consumers`.
- In guided `start` / `stop` selection, type `d<number>` to view the selected profile's scenario description before launching or stopping it.
- Each profile maps a logical profile name to:
  - scenario description text
  - simulator instances file
  - Fluent Bit OpAMP config, with optional agent config override
  - Fluentd OpAMP config, with optional agent config override
  - Elastic Agent OpAMP config, with optional agent config override
  - Elastic Heartbeat OpAMP config, with optional agent config override
  - Vector OpAMP config, with optional agent config override
  - optional container start commands
- New demo profiles should put agent config paths in `consumer.agent_config_path`
  inside the OpAMP JSON config and omit profile-level overrides unless a legacy
  config requires one.
- CLI records profile-scoped PIDs in `cli/runtime/managed_processes.json`, so `stop` can terminate one demo profile independently.
- The `Demo setup (Elastic Agent self-monitoring to Logstash)` profile starts the configured Logstash container first, then starts the plugin-driven `opamp_consumer.client` Elastic Agent consumer with `tests/logstash/opamp-consumer-elastic-agent-logstash-plugin.json`.
- The `Demo setup (Elastic Heartbeat supervisor to Logstash)` profile starts a Logstash container first, then starts the plugin-driven `opamp_consumer.client` Elastic Heartbeat consumer with `tests/logstash/opamp-consumer-elastic-heartbeat-logstash-plugin.json`.
- The `Demo setup (Vector self-monitor)` profile starts the plugin-driven `opamp_consumer.client` Vector consumer with `consumer/opamp-vector.json` and `docs/vector-self-monitor/vector-self-monitor.yaml`.
- The `Demo setup (Full multi-agent remote config)` profile starts the full `docs/full-demo` scenario: Logstash, Fluent Bit and Fluentd in supervisor mode, plus Vector, Elastic Agent, and Elastic Heartbeat in observer mode. Its profile entries point only at consumer OpAMP JSON files; agent paths come from those configs. Its provider/catalog config and replacement configs live under `docs/full-demo`.

Example:

```text
OPAMP_DEMO=true opamp-cli start
d1
OPAMP_DEMO=true opamp-cli demo
OPAMP_DEMO=true opamp-cli stop "demo consumers script-defaults"
```

Development container starts:

- `opamp-cli dev-containers` appears when `podman` or `docker` is available and the CLI profile config contains container start commands.
- Container starts are loaded from `cli/config/demo_consumer_profiles.json`.
- The profile and container-entry schema is documented in [docs/CLI_CONFIGURATION.md](/mnt/d/dev/opamp/cli/docs/CLI_CONFIGURATION.md).
- The Logstash entry mirrors `tests/logstash/run-logstash.bat`: it runs Logstash on host port `5044`, mounts the pipeline config, and writes output under `tests/logstash/out`.
- You can launch it directly with `opamp-cli dev-containers logstash`.
- Set `OPAMP_CONTAINER_RUNTIME` to choose a specific runtime executable; otherwise the CLI prefers `docker`, then `podman`.

Repository virtual environment setup:

- `opamp-cli setup-venv` creates or updates `.venv` at the repository root.
- It upgrades `pip`, `setuptools>=82`, `wheel`, `build`, and `hatchling>=1.25`.
- It installs root `requirements.txt`.
- It installs local Python components editable with their `dev` extras:
  `cli`, `provider`, `consumer`, `consumer-sim`, `config-service`,
  `catalog-service`, `agent_broker`, `mcp`, `dev-tools`,
  `svr-credentials-mgr/plaintext-keyring`, and `svr-credentials-mgr`.
- It runs `npm install` in checked-in Node tooling directories:
  `catalog-service`, `config-service`, `config-service/frontend`,
  `svr-credentials-mgr`, and `tools/mermaid`.
- In an interactive terminal, it prompts to open a shell with the virtual
  environment activated. Type `exit` in that shell to return.
- Use `--dry-run` to preview commands, `--venv <path>` to choose a different
  environment path, or `--skip-node` to skip Node tooling.

Type `exit` or `quit` to leave interactive mode.
Type `help` (or `-h` / `--help`) to print CLI usage and examples.
The process-tail preference is stored in `cli/runtime/settings.json`.

## Config Reports

- `config validate` writes log files named like `config-validate-<timestamp>.log`.
- `config metadata` writes log files named like `config-metadata-<timestamp>.log`.
- The CLI prints the generated report path at the end of each run.
- Validation reports list parser and validation issues when present.
- Metadata reports show whether values already existed or which metadata fields were applied.

## Autocomplete

- Press `Tab` in interactive mode for suggestions.
- `start` and `stop` suggestions are context-aware, so the CLI offers guided targets like `Config Editor` instead of unrelated global words.
- `start`, `stop`, and `restart` suggestions are context-aware, so the CLI offers guided targets like `Config Editor` instead of unrelated global words.
- File and script arguments use path completion when `prompt_toolkit` is available.
- Direct `python cli/main.py` runs on Windows include a built-in Tab completion fallback even when `prompt_toolkit` is not installed.
- On Windows, install dependencies first so `prompt_toolkit` is available:

```bash
python -m pip install -e cli
```

## Windows Note

If PowerShell reports an error such as:

`Start-Process ... The system cannot find the file specified`

it usually means a `.py` file was being launched as if it were an executable.
Use `python cli/main.py` directly, or run it through this CLI which now auto-prefixes
direct `.py` commands with Python.
