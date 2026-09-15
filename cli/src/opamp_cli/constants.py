#!/usr/bin/env python3
# Copyright 2026 mp3monster.org
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Shared constants for the OpAMP CLI."""

from __future__ import annotations

from pathlib import Path

# Keep shared command names, action IDs, labels, and runtime filenames here so
# guided menus, execution logic, docs, and tests stay aligned.
TRUE_VALUES = {"1", "true", "yes", "on"}
ENABLED_FLAG_VALUE = "true"
SCRIPT_KEYWORD = "script"
LOCALHOST_ADDRESS = "127.0.0.1"
INTERACTIVE_PROMPT = "opamp> "
COMMAND_EXITED_TEMPLATE = "Command exited with code {code}"
DEMO_CONSUMERS_SELECTION = "demo consumers"
DEFAULT_OUTPUT_DIR = Path("scripts")
CLI_RUNTIME_DIRNAME = "runtime"
CLI_LOG_DIRNAME = "logs"
CLI_PROCESS_STATE_FILENAME = "managed_processes.json"
CLI_SETTINGS_FILENAME = "settings.json"
CLI_COMPONENT_LOG_FILENAME = "opamp_cli.log"
CLI_SETTING_ENABLE_PROCESS_TAIL = "enable_process_tail"
CLI_DEMO_FLAG_ENV = "OPAMP_DEMO"
APP_ENABLE_DEV_FEATURES_ENV = "APP_ENABLE_DEV_FEATURES"
OPAMP_CONFIG_PATH_ENV = "OPAMP_CONFIG_PATH"
PYTHONPATH_ENV = "PYTHONPATH"
CLI_DEMO_CONFIG_PATH = Path("cli/config/demo_consumer_profiles.json")
CLI_VERSION_TARGETS_CONFIG_PATH = Path("cli/config/version_targets.json")
ARG_CONFIG_PATH = "--config-path"
ARG_AGENT_CONFIG_PATH = "--agent-config-path"
DEFAULT_SERVER_PORT = 8080
DEFAULT_CATALOG_WEB_PORT = 8090
PROCESS_START_CHECK_DELAY_SECONDS = 1.0
PROCESS_READY_TIMEOUT_SECONDS = 30.0
PROCESS_READY_POLL_INTERVAL_SECONDS = 0.25
PROCESS_STOP_TIMEOUT_SECONDS = 20.0
PROCESS_STOP_POLL_INTERVAL_SECONDS = 0.25
PROCESS_TAIL_INITIAL_LINES = 50
HTTP_READY_FAILURE_STATUS_THRESHOLD = 500
STARTUP_FAILURE_MARKERS = (
    "address already in use",
    "traceback (most recent call last):",
    "modulenotfounderror:",
    "importerror:",
)
INTENT_START = "start"
INTENT_STOP = "stop"
INTENT_RESTART = "restart"
GUIDED_INTENTS = (INTENT_START, INTENT_STOP, INTENT_RESTART)
COMMAND_HELP = "help"
COMMAND_LIST = "list"
COMMAND_STATUS = "status"
COMMAND_CONFIG = "config"
COMMAND_EXIT = "exit"
COMMAND_QUIT = "quit"
COMMAND_DEMO = "demo"
COMMAND_CLEAR_LOGS = "clear-logs"
COMMAND_SETUP_VENV = "setup-venv"
COMMAND_ENABLE_PROCESS_TAIL = "enable-process-tail"
COMMAND_DISABLE_PROCESS_TAIL = "disable-process-tail"
COMMAND_DEV_FLB_CONFIG = "dev-flb-config"
COMMAND_DEV_MCP_CONFIG = "dev-mcp-config"
COMMAND_DEV_PID_LOOKUP = "dev-pid-lookup"
COMMAND_DEV_CONTAINERS = "dev-containers"
COMMAND_DEV_VERSION_BUMP = "dev-version-bump"
ACTION_KIND_BACKGROUND_START = "background_start"
ACTION_KIND_SIMULATOR_START = "simulator_start"
ACTION_KIND_DEMO_CONSUMERS_START = "demo_consumers_start"
ACTION_KIND_STOP_RECORDED = "stop_recorded"
ACTION_KIND_STOP_ALL_RECORDED = "stop_all_recorded"
ACTION_KIND_DEMO_CONSUMERS_STOP = "demo_consumers_stop"
ACTION_KIND_RESTART = "restart"
ACTION_KIND_SHELL = "shell"
ACTION_KEY_RECORD_NAME = "record_name"
ACTION_KEY_METADATA = "metadata"
ACTION_KEY_LOG_NAME = "log_name"
CONFIG_KEY_CONFIG_PATH = "config_path"
CONFIG_KEY_AGENT_CONFIG_PATH = "agent_config_path"
ACTION_ID_SERVER = "server"
ACTION_ID_CATALOG_UI = "catalog_ui"
ACTION_ID_CONFIG_SERVICE = "config_service"
ACTION_ID_BROKER = "broker"
ACTION_ID_SIMULATOR = "simulator"
ACTION_ID_FLUENTBIT_CLIENT = "fluentbit_client"
ACTION_ID_FLUENTD_CLIENT = "fluentd_client"
ACTION_ID_VECTOR_CLIENT = "vector_client"
ACTION_ID_ALL_CLIENTS = "all_clients"
ACTION_ID_ALL_MANAGED = "all_managed"
LABEL_SERVER = "Server"
LABEL_CONFIG_CATALOG_UI = "Catalog"
LABEL_CONFIG_SERVICE = "Config Editor"
LABEL_BROKER = "Broker"
LABEL_SIMULATOR = "Simulator"
LABEL_FLUENTBIT_CLIENT = "Fluent Bit client"
LABEL_FLUENTD_CLIENT = "Fluentd client"
LABEL_VECTOR_CLIENT = "Vector client"
LABEL_ALL_CLIENTS = "All clients"
LABEL_ALL_MANAGED_PROCESSES = "All managed processes"
SIMULATOR_RECORD_PREFIX = "Simulator"
DEMO_PROFILE_KEY_FLUENTBIT = "fluentbit"
DEMO_PROFILE_KEY_FLUENTD = "fluentd"
DEMO_PROFILE_KEY_ELASTIC_AGENT = "elastic_agent"
DEMO_PROFILE_KEY_ELASTIC_HEARTBEAT = "elastic_heartbeat"
DEMO_PROFILE_KEY_VECTOR = "vector"
DEMO_CONSUMER_CLIENT_CONFIG_KEYS = (
    DEMO_PROFILE_KEY_FLUENTBIT,
    DEMO_PROFILE_KEY_FLUENTD,
    DEMO_PROFILE_KEY_ELASTIC_AGENT,
    DEMO_PROFILE_KEY_ELASTIC_HEARTBEAT,
    DEMO_PROFILE_KEY_VECTOR,
)

# The order of these identifiers is user-visible and position-sensitive.
# It defines:
# - the numbered menu order shown by interactive `start` / `stop`
# - the examples in help/docs
# - which item a user gets when they type a menu number
# Update docs/tests alongside any reordering.
GUIDED_START_ACTION_ORDER = [
    ACTION_ID_SERVER,
    ACTION_ID_CATALOG_UI,
    ACTION_ID_CONFIG_SERVICE,
    ACTION_ID_BROKER,
    ACTION_ID_SIMULATOR,
    ACTION_ID_FLUENTBIT_CLIENT,
    ACTION_ID_FLUENTD_CLIENT,
    ACTION_ID_VECTOR_CLIENT,
]
GUIDED_STOP_ACTION_ORDER = [
    ACTION_ID_SERVER,
    ACTION_ID_CATALOG_UI,
    ACTION_ID_BROKER,
    ACTION_ID_SIMULATOR,
    ACTION_ID_CONFIG_SERVICE,
    ACTION_ID_FLUENTBIT_CLIENT,
    ACTION_ID_FLUENTD_CLIENT,
    ACTION_ID_VECTOR_CLIENT,
    ACTION_ID_ALL_CLIENTS,
    ACTION_ID_ALL_MANAGED,
]
GUIDED_ACTION_ALIASES = {
    ACTION_ID_SERVER: ["srv"],
    ACTION_ID_CATALOG_UI: ["catalog", "catalog ui", "config catalog", "config catalog ui"],
    ACTION_ID_CONFIG_SERVICE: ["config", "cfg", "editor", "config editor", "config-editor", "config service", "config-service"],
    ACTION_ID_BROKER: ["brk"],
    ACTION_ID_SIMULATOR: ["sim"],
    ACTION_ID_FLUENTBIT_CLIENT: ["fluent bit", "fluentbit", "fluent bit client", "fb"],
    ACTION_ID_FLUENTD_CLIENT: ["fluentd", "fluentd client", "fd"],
    ACTION_ID_VECTOR_CLIENT: ["vector", "vector client"],
    ACTION_ID_ALL_CLIENTS: ["clients"],
    ACTION_ID_ALL_MANAGED: ["all", "everything"],
}

HELP_TEXT = """Usage:
  opamp-cli
  opamp-cli script <output_name> <command...>
  opamp-cli <command...>
  opamp-cli help
  opamp-cli list
  opamp-cli status
  opamp-cli config validate <path>
  opamp-cli config metadata <path>
  opamp-cli demo
  opamp-cli clear-logs
  opamp-cli setup-venv [--venv <path>] [--dry-run] [--skip-node]
  opamp-cli enable-process-tail
  opamp-cli disable-process-tail
  opamp-cli dev-flb-config
  opamp-cli dev-mcp-config
  opamp-cli dev-pid-lookup
  opamp-cli dev-containers
  opamp-cli dev-version-bump [VERSION] [--config <path>]

Behavior:
  - Interactive `start`, `stop`, and `restart` commands open guided multi-stage choices.
  - `list` shows the current CLI option hierarchy and guided targets.
  - `status` shows recorded managed processes, PID liveness, and log paths.
  - `clear-logs` removes CLI-managed logs and configured demo log files.
  - `setup-venv` creates or updates a repository-level Python virtual environment, installs local tooling, and can open an activated shell.
  - `config validate` validates one file or directory tree using config-service logic when available.
  - `config metadata` adds missing config-service header metadata without overwriting existing values.
  - `enable-process-tail` opens a new shell tailing each managed process log after start.
  - `disable-process-tail` stops opening log-tail shells for future managed starts.
  - If first token is `script`, generate an OS-native script file.
  - Otherwise execute the command immediately.
  - Direct `.py`/`.pyw` targets are auto-run via Python.

Examples:
  # Start server
  opamp-cli start server

  # Start catalog
  opamp-cli start catalog

  # Stop server
  opamp-cli stop server

  # Stop all CLI-managed processes
  opamp-cli stop all

  # Restart server
  opamp-cli restart server

  # Show managed process status
  opamp-cli status

  # Validate one config file
  opamp-cli config validate ./fluent-bit.yaml

  # Add missing metadata headers to supported files in a folder
  opamp-cli config metadata ./configs

  # Show current command/target hierarchy
  opamp-cli list

  # Open demo profile choices when OPAMP_DEMO=true
  opamp-cli demo

  # Clear CLI-managed and configured demo logs
  opamp-cli clear-logs

  # Create/update the repository-level virtual environment and tooling
  opamp-cli setup-venv

  # Enable log tail windows for future managed starts
  opamp-cli enable-process-tail

  # Disable log tail windows for future managed starts
  opamp-cli disable-process-tail

  # Open the dev-only Fluent Bit generator workflow
  opamp-cli dev-flb-config

  # Open the dev-only MCP client configuration workflow
  opamp-cli dev-mcp-config

  # Prompt for a regex and search running process IDs
  opamp-cli dev-pid-lookup

  # Choose a configured development container start command
  opamp-cli dev-containers

  # Bump each configured component version by one minor version
  opamp-cli dev-version-bump

Notes:
  - Interactive autocomplete uses prompt_toolkit when installed.
  - Fallback completion uses readline when available.
  - When interactive mode starts, the startup notes say to use `list` to see all available commands.
  - Guided actions can be run directly, for example `start config editor`.
  - `config` commands are only available when config-service logic can be detected.
  - When OPAMP_DEMO=true, `demo` acts like `start demo consumers`.
  - When APP_ENABLE_DEV_FEATURES=true and the Fluent Bit dev tools are present, `dev-flb-config` opens a guided generator workflow.
  - When APP_ENABLE_DEV_FEATURES=true and the MCP config utility is present, `dev-mcp-config` opens a guided MCP client configuration workflow.
  - When APP_ENABLE_DEV_FEATURES=true, `dev-pid-lookup` prompts for a regex and searches running processes for PID/name/command-line matches.
  - `dev-containers` appears when a container runtime and configured container starts are available.
  - When APP_ENABLE_DEV_FEATURES=true, `dev-version-bump` updates configured component semantic versions independently.
  - `setup-venv` installs Python packages into `.venv`, runs npm installs for checked-in Node tooling, and prompts before opening an activated shell in interactive terminals.
  - Guided start/stop/restart actions run components directly instead of relying on repo wrapper scripts.
  - Set OPAMP_DEMO=true to enable demo consumer options from cli/config/demo_consumer_profiles.json.
  - Guided starts record launched PIDs in cli/runtime/managed_processes.json.
  - Process-tail shells are opened on a best-effort basis and may be unavailable in headless terminals.
  - `clear-logs` discovers log locations from CLI defaults, managed-process state, the effective OpAMP config file, and demo profile config.
"""
