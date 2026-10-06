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

"""Prompt-driven command builder and executor for OpAMP workflows.

Behavior:
- If first token is `script`, generate an OS-native script file.
- Otherwise, execute the command immediately.

Extension guide:
- See `cli/docs/CLI_EXTENSION_GUIDE.md` for the component layout, action catalog
  conventions, and step-by-step guidance for adding new commands/components.
"""

from __future__ import annotations

import csv
import importlib
import importlib.util
import json
import logging
import os
import re
import shlex
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

try:
    from .common import (
        _is_windows,
        _normalize_python_script_command,
        _normalized_label,
        _shell_quote,
        _slugify,
        _utc_timestamp,
    )
    from . import (
        consumer_plugins,
        container_management,
        dev_commands,
        process_tail,
        setup_venv,
    )
    from .config_commands import (
        COMMAND_CONFIG_METADATA,
        COMMAND_CONFIG_VALIDATE,
        config_command_available,
        execute_config_command,
    )
    from .constants import (
        ACTION_ID_ALL_CLIENTS,
        ACTION_ID_ALL_MANAGED,
        ACTION_ID_BROKER,
        ACTION_ID_CATALOG_UI,
        ACTION_ID_CONFIG_SERVICE,
        ACTION_ID_FLUENTBIT_CLIENT,
        ACTION_ID_FLUENTD_CLIENT,
        ACTION_ID_VECTOR_CLIENT,
        ACTION_ID_SERVER,
        ACTION_ID_SIMULATOR,
        ACTION_KIND_BACKGROUND_START,
        ACTION_KIND_DEMO_CONSUMERS_START,
        ACTION_KIND_DEMO_CONSUMERS_STOP,
        ACTION_KIND_RESTART,
        ACTION_KIND_SHELL,
        ACTION_KIND_SIMULATOR_START,
        ACTION_KIND_STOP_ALL_RECORDED,
        ACTION_KIND_STOP_RECORDED,
        ACTION_KEY_LOG_NAME,
        ACTION_KEY_METADATA,
        ACTION_KEY_RECORD_NAME,
        ARG_CONFIG_PATH,
        APP_ENABLE_DEV_FEATURES_ENV,
        CLI_COMPONENT_LOG_FILENAME,
        CLI_DEMO_CONFIG_PATH,
        CLI_DEMO_FLAG_ENV,
        CLI_LOG_DIRNAME,
        CLI_PROCESS_STATE_FILENAME,
        CLI_RUNTIME_DIRNAME,
        CLI_SETTING_DEMO_CONFIG_PATH,
        CLI_SETTING_ENABLE_PROCESS_TAIL,
        CLI_SETTINGS_FILENAME,
        COMMAND_CLI_CONFIG,
        COMMAND_CLI_CONFIG_CHANGE,
        COMMAND_CLI_CONFIG_SUMMARY,
        COMMAND_CLI_CONFIG_VIEW,
        COMMAND_CLEAR_LOGS,
        COMMAND_CONFIG,
        COMMAND_DEMO,
        COMMAND_DEV_CONTAINERS,
        COMMAND_DEV_FLB_CONFIG,
        COMMAND_DEV_MCP_CONFIG,
        COMMAND_DEV_PID_LOOKUP,
        COMMAND_DEV_VERSION_BUMP,
        COMMAND_DISABLE_PROCESS_TAIL,
        COMMAND_ENABLE_PROCESS_TAIL,
        COMMAND_EXITED_TEMPLATE,
        COMMAND_EXIT,
        COMMAND_HELP,
        COMMAND_LIST,
        COMMAND_QUIT,
        COMMAND_SETUP_VENV,
        COMMAND_STATUS,
        CONFIG_KEY_AGENT_CONFIG_PATH,
        CONFIG_KEY_CONFIG_PATH,
        DEFAULT_CATALOG_WEB_PORT,
        DEFAULT_SERVER_PORT,
        DEMO_CONSUMERS_SELECTION,
        DEMO_CONSUMER_CLIENT_CONFIG_KEYS,
        DEMO_PROFILE_KEY_ELASTIC_AGENT,
        DEMO_PROFILE_KEY_ELASTIC_HEARTBEAT,
        DEMO_PROFILE_KEY_VECTOR,
        DEMO_PROFILE_KEY_FLUENTBIT,
        DEMO_PROFILE_KEY_FLUENTD,
        ENABLED_FLAG_VALUE,
        GUIDED_ACTION_ALIASES,
        GUIDED_INTENTS,
        GUIDED_START_ACTION_ORDER,
        GUIDED_STOP_ACTION_ORDER,
        HELP_TEXT,
        HTTP_READY_FAILURE_STATUS_THRESHOLD,
        INTERACTIVE_PROMPT,
        INTENT_RESTART,
        INTENT_START,
        INTENT_STOP,
        LABEL_ALL_CLIENTS,
        LABEL_ALL_MANAGED_PROCESSES,
        LABEL_BROKER,
        LABEL_CONFIG_CATALOG_UI,
        LABEL_CONFIG_SERVICE,
        LABEL_FLUENTBIT_CLIENT,
        LABEL_FLUENTD_CLIENT,
        LABEL_VECTOR_CLIENT,
        LABEL_SERVER,
        LABEL_SIMULATOR,
        LOCALHOST_ADDRESS,
        PROCESS_READY_POLL_INTERVAL_SECONDS,
        PROCESS_READY_TIMEOUT_SECONDS,
        PROCESS_START_CHECK_DELAY_SECONDS,
        PROCESS_STOP_POLL_INTERVAL_SECONDS,
        PROCESS_STOP_TIMEOUT_SECONDS,
        OPAMP_CONFIG_PATH_ENV,
        PYTHONPATH_ENV,
        SCRIPT_KEYWORD,
        SIMULATOR_RECORD_PREFIX,
        STARTUP_FAILURE_MARKERS,
        TRUE_VALUES,
    )
    from .script_mode import (
        _resolve_script_path,
        _split_script_directive,
        _write_script,
    )
    from .version_bump import execute_dev_version_bump_workflow
except ImportError:
    # Support direct execution: `python cli/src/opamp_cli/main.py`
    current_dir = Path(__file__).resolve().parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from common import (  # type: ignore[no-redef]
        _is_windows,
        _normalize_python_script_command,
        _normalized_label,
        _shell_quote,
        _slugify,
        _utc_timestamp,
    )
    import consumer_plugins  # type: ignore[no-redef]
    import container_management  # type: ignore[no-redef]
    import dev_commands  # type: ignore[no-redef]
    import process_tail  # type: ignore[no-redef]
    import setup_venv  # type: ignore[no-redef]
    from config_commands import (  # type: ignore[no-redef]
        COMMAND_CONFIG_METADATA,
        COMMAND_CONFIG_VALIDATE,
        config_command_available,
        execute_config_command,
    )
    from constants import (  # type: ignore[no-redef]
        ACTION_ID_ALL_CLIENTS,
        ACTION_ID_ALL_MANAGED,
        ACTION_ID_BROKER,
        ACTION_ID_CATALOG_UI,
        ACTION_ID_CONFIG_SERVICE,
        ACTION_ID_FLUENTBIT_CLIENT,
        ACTION_ID_FLUENTD_CLIENT,
        ACTION_ID_VECTOR_CLIENT,
        ACTION_ID_SERVER,
        ACTION_ID_SIMULATOR,
        ACTION_KIND_BACKGROUND_START,
        ACTION_KIND_DEMO_CONSUMERS_START,
        ACTION_KIND_DEMO_CONSUMERS_STOP,
        ACTION_KIND_RESTART,
        ACTION_KIND_SHELL,
        ACTION_KIND_SIMULATOR_START,
        ACTION_KIND_STOP_ALL_RECORDED,
        ACTION_KIND_STOP_RECORDED,
        ACTION_KEY_LOG_NAME,
        ACTION_KEY_METADATA,
        ACTION_KEY_RECORD_NAME,
        ARG_CONFIG_PATH,
        APP_ENABLE_DEV_FEATURES_ENV,
        CLI_COMPONENT_LOG_FILENAME,
        CLI_DEMO_CONFIG_PATH,
        CLI_DEMO_FLAG_ENV,
        CLI_LOG_DIRNAME,
        CLI_PROCESS_STATE_FILENAME,
        CLI_RUNTIME_DIRNAME,
        CLI_SETTING_DEMO_CONFIG_PATH,
        CLI_SETTING_ENABLE_PROCESS_TAIL,
        CLI_SETTINGS_FILENAME,
        COMMAND_CLI_CONFIG,
        COMMAND_CLI_CONFIG_CHANGE,
        COMMAND_CLI_CONFIG_SUMMARY,
        COMMAND_CLI_CONFIG_VIEW,
        COMMAND_CLEAR_LOGS,
        COMMAND_CONFIG,
        COMMAND_DEMO,
        COMMAND_DEV_CONTAINERS,
        COMMAND_DEV_FLB_CONFIG,
        COMMAND_DEV_MCP_CONFIG,
        COMMAND_DEV_PID_LOOKUP,
        COMMAND_DEV_VERSION_BUMP,
        COMMAND_DISABLE_PROCESS_TAIL,
        COMMAND_ENABLE_PROCESS_TAIL,
        COMMAND_EXITED_TEMPLATE,
        COMMAND_EXIT,
        COMMAND_HELP,
        COMMAND_LIST,
        COMMAND_QUIT,
        COMMAND_SETUP_VENV,
        COMMAND_STATUS,
        CONFIG_KEY_AGENT_CONFIG_PATH,
        CONFIG_KEY_CONFIG_PATH,
        DEFAULT_CATALOG_WEB_PORT,
        DEFAULT_SERVER_PORT,
        DEMO_CONSUMERS_SELECTION,
        DEMO_CONSUMER_CLIENT_CONFIG_KEYS,
        DEMO_PROFILE_KEY_ELASTIC_AGENT,
        DEMO_PROFILE_KEY_ELASTIC_HEARTBEAT,
        DEMO_PROFILE_KEY_VECTOR,
        DEMO_PROFILE_KEY_FLUENTBIT,
        DEMO_PROFILE_KEY_FLUENTD,
        ENABLED_FLAG_VALUE,
        GUIDED_ACTION_ALIASES,
        GUIDED_INTENTS,
        GUIDED_START_ACTION_ORDER,
        GUIDED_STOP_ACTION_ORDER,
        HELP_TEXT,
        HTTP_READY_FAILURE_STATUS_THRESHOLD,
        INTERACTIVE_PROMPT,
        INTENT_RESTART,
        INTENT_START,
        INTENT_STOP,
        LABEL_ALL_CLIENTS,
        LABEL_ALL_MANAGED_PROCESSES,
        LABEL_BROKER,
        LABEL_CONFIG_CATALOG_UI,
        LABEL_CONFIG_SERVICE,
        LABEL_FLUENTBIT_CLIENT,
        LABEL_FLUENTD_CLIENT,
        LABEL_VECTOR_CLIENT,
        LABEL_SERVER,
        LABEL_SIMULATOR,
        LOCALHOST_ADDRESS,
        PROCESS_READY_POLL_INTERVAL_SECONDS,
        PROCESS_READY_TIMEOUT_SECONDS,
        PROCESS_START_CHECK_DELAY_SECONDS,
        PROCESS_STOP_POLL_INTERVAL_SECONDS,
        PROCESS_STOP_TIMEOUT_SECONDS,
        OPAMP_CONFIG_PATH_ENV,
        PYTHONPATH_ENV,
        SCRIPT_KEYWORD,
        SIMULATOR_RECORD_PREFIX,
        STARTUP_FAILURE_MARKERS,
        TRUE_VALUES,
    )
    from script_mode import (  # type: ignore[no-redef]
        _resolve_script_path,
        _split_script_directive,
        _write_script,
    )
    from version_bump import execute_dev_version_bump_workflow  # type: ignore[no-redef]

CLI_LOGGER_NAME = "opamp_cli"
SIMULATOR_STATE_KEY_INSTANCES = "instances"
SIMULATOR_STATE_KEY_NAME = "name"
SIMULATOR_STATE_KEY_PID = "pid"
GUIDED_DESCRIPTION_COMMAND_PREFIX = "d"
GUIDED_DESCRIPTION_LABEL = "scenario description"
SUPERVISOR_SEMAPHORE_FILENAME = "OpAMPSupervisor.signal"
PROCESS_INFO_KEY_PID = "pid"
PROCESS_INFO_KEY_NAME = "name"
PROCESS_INFO_KEY_COMMAND_LINE = "command_line"
LOG_FILE_SUFFIXES = {".json", ".jsonl", ".log", ".ndjson"}
SMART_LOG_VIEWER_CONFIG_DIRNAME = "smart-log-viewer"
SMART_LOG_VIEWER_COLORS = (
    "#58a6ff",
    "#a371f7",
    "#3fb950",
    "#f2cc60",
    "#ff7b72",
    "#39c5cf",
    "#d2a8ff",
    "#ffa657",
)
WINDOWS_PROCESS_SNAPSHOT_COMMAND = [
    "powershell.exe",
    "-NoProfile",
    "-Command",
    (
        "Get-CimInstance Win32_Process | "
        "Select-Object ProcessId,Name,CommandLine | "
        "ConvertTo-Csv -NoTypeInformation"
    ),
]
POSIX_PROCESS_SNAPSHOT_COMMAND = ["ps", "-eo", "pid=,comm=,args="]
_CLI_LOGGER_CACHE: dict[str, logging.Logger | Path | None] = {
    "logger": None,
    "path": None,
}


def _windows_no_console_kwargs() -> dict[str, Any]:
    """Return subprocess kwargs that suppress transient console windows on Windows."""
    if _is_windows() is not True:
        return {}
    creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if creationflags <= 0:
        return {}
    return {"creationflags": creationflags}


def _dev_features_enabled() -> bool:
    """Return whether APP_ENABLE_DEV_FEATURES is enabled for this process."""
    raw_value = os.environ.get(APP_ENABLE_DEV_FEATURES_ENV, "")
    return str(raw_value or "").strip().lower() in TRUE_VALUES


def _demo_mode_enabled() -> bool:
    """Return whether demo-only guided actions should be enabled."""
    raw_value = os.environ.get(CLI_DEMO_FLAG_ENV, "")
    return str(raw_value or "").strip().lower() in TRUE_VALUES


def _repo_root() -> Path:
    """Return repository root for this CLI component."""
    return Path(__file__).resolve().parents[3]


def _default_demo_consumer_config_path() -> Path:
    """Return the checked-in demo consumer profile mapping path."""
    return (_repo_root() / CLI_DEMO_CONFIG_PATH).resolve()


def _demo_consumer_config_path() -> Path:
    """Return the active demo consumer profile mapping path."""
    configured_path = str(
        _load_cli_settings().get(CLI_SETTING_DEMO_CONFIG_PATH) or ""
    ).strip()
    if not configured_path:
        return _default_demo_consumer_config_path()
    path = Path(configured_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (_repo_root() / path).resolve()


def _cli_runtime_dir() -> Path:
    """Return CLI runtime metadata directory."""
    runtime_dir = (_repo_root() / "cli" / CLI_RUNTIME_DIRNAME).resolve()
    runtime_dir.mkdir(parents=True, exist_ok=True)
    return runtime_dir


def _cli_process_state_path() -> Path:
    """Return CLI-managed process state file path."""
    return (_cli_runtime_dir() / CLI_PROCESS_STATE_FILENAME).resolve()


def _cli_settings_path() -> Path:
    """Return CLI settings file path."""
    return (_cli_runtime_dir() / CLI_SETTINGS_FILENAME).resolve()


def _cli_log_dir() -> Path:
    """Return log directory used for CLI-started background processes."""
    log_dir = (_cli_runtime_dir() / CLI_LOG_DIRNAME).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _cli_component_log_path() -> Path:
    """Return the component log file used for CLI lifecycle and error events."""
    return (_cli_log_dir() / CLI_COMPONENT_LOG_FILENAME).resolve()


def _get_logger() -> logging.Logger:
    """Return a configured component logger that writes to the CLI runtime log."""
    log_path = _cli_component_log_path()
    cached_logger = _CLI_LOGGER_CACHE.get("logger")
    cached_path = _CLI_LOGGER_CACHE.get("path")
    if isinstance(cached_logger, logging.Logger) and cached_path == log_path:
        return cached_logger

    logger = logging.getLogger(CLI_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:  # pragma: no cover - defensive handler cleanup
            pass

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    logger.addHandler(file_handler)

    _CLI_LOGGER_CACHE["logger"] = logger
    _CLI_LOGGER_CACHE["path"] = log_path
    return logger


def _close_cli_logger() -> None:
    """Close the CLI file logger so its log file can be deleted on Windows."""
    cached_logger = _CLI_LOGGER_CACHE.get("logger")
    if isinstance(cached_logger, logging.Logger):
        for handler in list(cached_logger.handlers):
            cached_logger.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass
    _CLI_LOGGER_CACHE["logger"] = None
    _CLI_LOGGER_CACHE["path"] = None


def _execute_command(command_text: str) -> int:
    """Execute command text immediately in a shell."""
    logger = _get_logger()
    normalized_command = _normalize_python_script_command(
        command_text,
        launcher=sys.executable,
    )
    logger.info("executing direct command command=%s", normalized_command)
    completed = subprocess.run(normalized_command, shell=True, check=False)
    if int(completed.returncode) != 0:
        logger.warning(
            "direct command exited non-zero command=%s exit_code=%s",
            normalized_command,
            int(completed.returncode),
        )
    else:
        logger.info("direct command completed command=%s exit_code=0", normalized_command)
    return int(completed.returncode)


def _load_module_from_path(*, module_name: str, path: Path) -> Any | None:
    """Load one Python module from a file path, returning None on failure."""
    inserted_parent = False
    parent_text = str(path.parent.resolve())
    if parent_text not in sys.path:
        sys.path.insert(0, parent_text)
        inserted_parent = True
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
    except Exception:
        if inserted_parent:
            try:
                sys.path.remove(parent_text)
            except ValueError:
                pass
        return None
    if spec is None or spec.loader is None:
        if inserted_parent:
            try:
                sys.path.remove(parent_text)
            except ValueError:
                pass
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        if inserted_parent:
            try:
                sys.path.remove(parent_text)
            except ValueError:
                pass
        return None
    if inserted_parent:
        try:
            sys.path.remove(parent_text)
        except ValueError:
            pass
    return module


def _command_text_from_args(args: list[str]) -> str:
    """Reconstruct shell-safe command text from parsed CLI argv items."""
    return " ".join(_shell_quote(arg) for arg in args)


def _command_match_text(command_text: str) -> str:
    """Return command text normalized for internal command matching."""
    text = str(command_text or "").strip()
    if not text:
        return ""
    try:
        tokens = shlex.split(text, posix=True)
    except ValueError:
        tokens = text.split()
    if not tokens:
        return ""
    return " ".join(str(token or "").strip().strip("\"'") for token in tokens)


def _split_internal_command_args(command_text: str) -> list[str]:
    """Split internal command text and trim paired shell quotes from tokens."""
    try:
        tokens = shlex.split(str(command_text or ""), posix=not _is_windows())
    except ValueError:
        tokens = str(command_text or "").split()
    return [str(token or "").strip().strip("\"'") for token in tokens]


def _script_mode_enabled(command_text: str) -> bool:
    """Return whether command begins with `script`."""
    stripped = command_text.lstrip()
    if not stripped:
        return False
    first, *_ = stripped.split(maxsplit=1)
    return first.lower() == SCRIPT_KEYWORD


def _handle_command(
    raw_command: str,
    *,
    input_reader: Callable[[str], str] | None = None,
) -> int:  # noqa: PLR0911
    """Process one command line."""
    logger = _get_logger()
    command_text = raw_command.strip()
    if not command_text:
        logger.info("ignored empty command input")
        return 0

    match_text = _command_match_text(command_text)
    lowered = match_text.lower()
    if lowered in {
        COMMAND_ENABLE_PROCESS_TAIL,
        "enable process-tail",
        "enable process tail",
        f"enable {COMMAND_ENABLE_PROCESS_TAIL}",
    }:
        logger.info("enabling process tail feature")
        process_tail.set_process_tail_enabled(
            True,
            load_settings=_load_cli_settings,
            save_settings=_save_cli_settings,
            settings_path=_cli_settings_path,
            logger=logger,
        )
        return 0
    if lowered in {
        COMMAND_DISABLE_PROCESS_TAIL,
        "disable process-tail",
        "disable process tail",
        f"disable {COMMAND_ENABLE_PROCESS_TAIL}",
    }:
        logger.info("disabling process tail feature")
        process_tail.set_process_tail_enabled(
            False,
            load_settings=_load_cli_settings,
            save_settings=_save_cli_settings,
            settings_path=_cli_settings_path,
            logger=logger,
        )
        return 0
    if lowered == COMMAND_STATUS:
        logger.info("printing CLI status")
        return _print_status()
    if lowered in {COMMAND_CLEAR_LOGS, "clear logs"}:
        logger.info("clearing CLI-discovered logs")
        return _clear_logs()
    if lowered == COMMAND_SETUP_VENV or lowered.startswith(f"{COMMAND_SETUP_VENV} "):
        logger.info("starting virtual environment setup workflow command=%s", command_text)
        setup_args = _split_internal_command_args(command_text)
        return setup_venv.execute_setup_venv_workflow(
            setup_args[1:],
            repo_root=_repo_root(),
            is_windows=_is_windows(),
            command_text_from_args=_command_text_from_args,
            windows_no_console_kwargs=_windows_no_console_kwargs,
            prompt_activation=lambda venv_dir: setup_venv.prompt_setup_venv_activation(
                venv_dir,
                prompt_text=lambda prompt: _prompt_text(prompt, input_reader=input_reader),
                parse_yes_no=lambda value, default: _parse_yes_no(value, default=default),
                open_shell=lambda path: setup_venv.open_setup_venv_shell(
                    path,
                    repo_root=_repo_root(),
                    is_windows=_is_windows(),
                ),
            ),
        )
    if lowered == COMMAND_LIST:
        logger.info("printing CLI option hierarchy")
        return _print_option_hierarchy()
    if lowered == COMMAND_CLI_CONFIG or lowered.startswith(f"{COMMAND_CLI_CONFIG} "):
        logger.info("starting CLI config workflow command=%s", command_text)
        cli_config_args = _split_internal_command_args(command_text)
        return _execute_cli_config_command(
            cli_config_args[1:],
            input_reader=input_reader,
        )
    if lowered == COMMAND_DEV_FLB_CONFIG:
        logger.info("starting dev fluent bit config workflow")
        return dev_commands.execute_dev_tool_workflow(
            command_name=COMMAND_DEV_FLB_CONFIG,
            tool_family_label="Fluent Bit",
            specs=_fluentbit_dev_tool_specs(),
            dev_features_enabled=_dev_features_enabled(),
            prompt_text=lambda prompt: _prompt_text(prompt, input_reader=input_reader),
            parse_yes_no=lambda value, default: _parse_yes_no(value, default=default),
            command_text_from_args=_command_text_from_args,
            repo_root=_repo_root(),
            build_exec_env=_build_exec_env,
            logger=logger,
        )
    if lowered == COMMAND_DEV_MCP_CONFIG:
        logger.info("starting dev mcp config workflow")
        return dev_commands.execute_dev_tool_workflow(
            command_name=COMMAND_DEV_MCP_CONFIG,
            tool_family_label="MCP",
            specs=_mcp_dev_tool_specs(),
            dev_features_enabled=_dev_features_enabled(),
            prompt_text=lambda prompt: _prompt_text(prompt, input_reader=input_reader),
            parse_yes_no=lambda value, default: _parse_yes_no(value, default=default),
            command_text_from_args=_command_text_from_args,
            repo_root=_repo_root(),
            build_exec_env=_build_exec_env,
            logger=logger,
        )
    if lowered == COMMAND_DEV_PID_LOOKUP:
        logger.info("starting dev pid lookup workflow")
        return dev_commands.execute_dev_pid_lookup_workflow(
            command_name=COMMAND_DEV_PID_LOOKUP,
            dev_features_enabled=_dev_pid_lookup_available(),
            prompt_text=lambda prompt: _prompt_text(prompt, input_reader=input_reader),
            running_process_entries=_running_process_entries,
            process_entries_matching_pattern=lambda processes, pattern: _process_entries_matching_pattern(
                processes,
                pattern=pattern,
            ),
            print_pid_lookup_results=_print_pid_lookup_results,
        )
    if lowered == COMMAND_DEV_VERSION_BUMP or lowered.startswith(f"{COMMAND_DEV_VERSION_BUMP} "):
        logger.info("starting dev version bump workflow command=%s", command_text)
        version_args = _split_internal_command_args(command_text)
        return execute_dev_version_bump_workflow(
            version_args[1:],
            repo_root_provider=_repo_root,
            dev_features_enabled=_dev_features_enabled,
        )
    if lowered == COMMAND_DEV_CONTAINERS or lowered.startswith(f"{COMMAND_DEV_CONTAINERS} "):
        logger.info("starting dev container workflow command=%s", command_text)
        selection = match_text[len(COMMAND_DEV_CONTAINERS) :].strip()
        return dev_commands.execute_dev_container_workflow(
            command_name=COMMAND_DEV_CONTAINERS,
            selection=selection,
            container_runtime_executable=container_management.container_runtime_executable,
            container_runtime_ready=lambda runtime: container_management.container_runtime_ready(
                runtime,
                windows_no_console_kwargs=_windows_no_console_kwargs,
            ),
            print_container_runtime_unavailable=container_management.print_container_runtime_unavailable,
            configured_container_start_actions=_configured_container_start_actions,
            action_matches_alias=_action_matches_alias,
            select_guided_action=lambda intent, actions: _select_guided_action(
                intent=intent,
                actions=actions,
            ),
            launch_background_process=_launch_background_process,
        )
    if lowered == COMMAND_CONFIG or lowered.startswith(f"{COMMAND_CONFIG} "):
        logger.info("starting config workflow command=%s", command_text)
        config_args = _split_internal_command_args(command_text)
        if not config_args:
            raise ValueError("config command is missing arguments")
        return execute_config_command(
            argv=config_args[1:],
            repo_root=_repo_root(),
            log_dir=_cli_log_dir(),
        )

    if _script_mode_enabled(match_text):
        output_name, script_command = _split_script_directive(match_text)
        output_path = _resolve_script_path(output_name)
        _write_script(output_path, script_command)
        logger.info(
            "generated script output_path=%s command=%s",
            output_path,
            script_command,
        )
        print(f"Generated script: {output_path}")
        return 0

    return _execute_command(command_text)


def _top_level_commands() -> list[str]:
    """Return top-level interactive commands and common executables."""
    commands = [
        COMMAND_HELP,
        "--help",
        "-h",
        INTENT_START,
        INTENT_STOP,
        INTENT_RESTART,
        COMMAND_LIST,
        COMMAND_STATUS,
        COMMAND_CLI_CONFIG,
        COMMAND_CLEAR_LOGS,
        COMMAND_SETUP_VENV,
        COMMAND_ENABLE_PROCESS_TAIL,
        COMMAND_DISABLE_PROCESS_TAIL,
        COMMAND_EXIT,
        COMMAND_QUIT,
        SCRIPT_KEYWORD,
        "python",
        "python3",
        "py",
        "uv",
        "curl",
    ]
    if config_command_available(repo_root=_repo_root()):
        commands.append(COMMAND_CONFIG)
    if _demo_mode_enabled():
        commands.append(COMMAND_DEMO)
    if _fluentbit_dev_tool_available():
        commands.append(COMMAND_DEV_FLB_CONFIG)
    if _mcp_dev_tool_available():
        commands.append(COMMAND_DEV_MCP_CONFIG)
    if _dev_pid_lookup_available():
        commands.append(COMMAND_DEV_PID_LOOKUP)
    if _dev_version_bump_available():
        commands.append(COMMAND_DEV_VERSION_BUMP)
    if container_management.container_runtime_executable() and _configured_container_start_actions():
        commands.append(COMMAND_DEV_CONTAINERS)
    return commands


def _config_subcommands() -> tuple[str, ...]:
    """Return supported interactive `config` subcommands."""
    return (COMMAND_CONFIG_VALIDATE, COMMAND_CONFIG_METADATA)


def _cli_config_subcommands() -> tuple[str, ...]:
    """Return supported interactive `cli-config` subcommands."""
    return (
        COMMAND_CLI_CONFIG_VIEW,
        COMMAND_CLI_CONFIG_SUMMARY,
        COMMAND_CLI_CONFIG_CHANGE,
    )


def _config_subcommand_prefix(buffer_text: str) -> str | None:
    """Return the in-progress `config` subcommand token, when applicable."""
    stripped = str(buffer_text or "").lstrip()
    lowered = stripped.lower()
    if lowered.startswith(f"{COMMAND_CONFIG} ") is not True:
        return None
    remainder = stripped[len(COMMAND_CONFIG) + 1 :]
    if " " in remainder:
        return None
    return remainder


def _config_subcommand_completion_context(buffer_text: str) -> tuple[str, str] | None:
    """Return prefix-preserving context for completing `config` subcommands."""
    buffer_value = str(buffer_text or "")
    stripped = buffer_value.lstrip()
    if stripped:
        leading = buffer_value[: len(buffer_value) - len(stripped)]
    else:
        leading = ""
    lowered = stripped.lower()
    if lowered.startswith(f"{COMMAND_CONFIG} ") is not True:
        return None
    remainder = stripped[len(COMMAND_CONFIG) + 1 :]
    if " " in remainder:
        return None
    return (f"{leading}{stripped[: len(COMMAND_CONFIG) + 1]}", remainder)


def _cli_config_subcommand_prefix(buffer_text: str) -> str | None:
    """Return the in-progress `cli-config` subcommand token, when applicable."""
    stripped = str(buffer_text or "").lstrip()
    lowered = stripped.lower()
    if lowered.startswith(f"{COMMAND_CLI_CONFIG} ") is not True:
        return None
    remainder = stripped[len(COMMAND_CLI_CONFIG) + 1 :]
    if " " in remainder:
        return None
    return remainder


def _cli_config_subcommand_completion_context(buffer_text: str) -> tuple[str, str] | None:
    """Return prefix-preserving context for completing `cli-config` subcommands."""
    buffer_value = str(buffer_text or "")
    stripped = buffer_value.lstrip()
    leading = buffer_value[: len(buffer_value) - len(stripped)] if stripped else ""
    lowered = stripped.lower()
    if lowered.startswith(f"{COMMAND_CLI_CONFIG} ") is not True:
        return None
    remainder = stripped[len(COMMAND_CLI_CONFIG) + 1 :]
    if " " in remainder:
        return None
    return (f"{leading}{stripped[: len(COMMAND_CLI_CONFIG) + 1]}", remainder)


def _completion_entries(words: Iterable[str]) -> list[str]:
    """Return full-line completion entries for non-contextual completion backends."""
    return sorted({str(word).strip() for word in words if str(word).strip()})


def _completion_candidates(
    buffer_text: str,
    *,
    entries: Iterable[str],
) -> tuple[str, str, list[str]]:
    """Return completion base, token prefix, and candidate values for one buffer."""
    config_context = _config_subcommand_completion_context(buffer_text)
    if config_context is not None:
        completion_base, prefix = config_context
        lowered_prefix = prefix.lower()
        matches = [
            subcommand
            for subcommand in _config_subcommands()
            if subcommand.startswith(lowered_prefix)
        ]
        return (completion_base, prefix, matches)

    cli_config_context = _cli_config_subcommand_completion_context(buffer_text)
    if cli_config_context is not None:
        completion_base, prefix = cli_config_context
        lowered_prefix = prefix.lower()
        matches = [
            subcommand
            for subcommand in _cli_config_subcommands()
            if subcommand.startswith(lowered_prefix)
        ]
        return (completion_base, prefix, matches)

    prefix = str(buffer_text or "")
    lowered_prefix = prefix.lower()
    matches = [entry for entry in entries if entry.lower().startswith(lowered_prefix)]
    return ("", prefix, matches)


def _fluentbit_dev_tool_script_paths() -> list[Path]:
    """Return known Fluent Bit dev-tool script paths in repo-relative order."""
    repo_root = _repo_root()
    return [
        (repo_root / "config-service" / "dev-tools" / "generate_fluentbit_assets.py").resolve(),
        (repo_root / "config-service" / "dev-tools" / "generate_fluentbit_markdown.py").resolve(),
    ]


def _fluentbit_dev_tool_specs() -> list[dict[str, Any]]:
    """Return discovered Fluent Bit dev-tool specs when dev mode is enabled."""
    if _dev_features_enabled() is not True:
        return []
    specs: list[dict[str, Any]] = []
    for script_path in _fluentbit_dev_tool_script_paths():
        spec = dev_commands.load_dev_tool_spec_from_script(
            script_path,
            load_module_from_path=lambda module_name, path: _load_module_from_path(
                module_name=module_name,
                path=path,
            ),
        )
        if isinstance(spec, dict):
            specs.append(spec)
    return specs


def _fluentbit_dev_tool_available() -> bool:
    """Return whether the dev Fluent Bit workflow should be exposed."""
    return bool(_fluentbit_dev_tool_specs())


def _mcp_dev_tool_script_paths() -> list[Path]:
    """Return known MCP dev-tool script paths in repo-relative order."""
    repo_root = _repo_root()
    return [
        (repo_root / "mcp" / "configure_mcp_clients.py").resolve(),
    ]


def _mcp_dev_tool_specs() -> list[dict[str, Any]]:
    """Return discovered MCP dev-tool specs when dev mode is enabled."""
    if _dev_features_enabled() is not True:
        return []
    specs: list[dict[str, Any]] = []
    for script_path in _mcp_dev_tool_script_paths():
        spec = dev_commands.load_dev_tool_spec_from_script(
            script_path,
            load_module_from_path=lambda module_name, path: _load_module_from_path(
                module_name=module_name,
                path=path,
            ),
        )
        if isinstance(spec, dict):
            specs.append(spec)
    return specs


def _mcp_dev_tool_available() -> bool:
    """Return whether the dev MCP workflow should be exposed."""
    return bool(_mcp_dev_tool_specs())


def _dev_pid_lookup_available() -> bool:
    """Return whether the dev PID lookup workflow should be exposed."""
    return _dev_features_enabled()


def _dev_version_bump_available() -> bool:
    """Return whether the dev version bump workflow should be exposed."""
    return _dev_features_enabled()


def _prompt_text(
    prompt_text: str,
    *,
    input_reader: Callable[[str], str] | None = None,
) -> str:
    """Read one prompt value via provided reader or built-in input."""
    if input_reader is not None:
        return str(input_reader(prompt_text))
    return input(prompt_text)


def _parse_yes_no(value: str, *, default: bool) -> bool | None:
    """Parse one yes/no value, returning None when it is invalid."""
    cleaned = str(value or "").strip().lower()
    if not cleaned:
        return default
    if cleaned in {"y", "yes", "true", "1", "on"}:
        return True
    if cleaned in {"n", "no", "false", "0", "off"}:
        return False
    return None


def _running_process_entries() -> tuple[bool, list[dict[str, Any]]]:
    """Return a snapshot of running process details for the current platform."""
    if _is_windows():
        return _windows_process_entries()
    return _posix_process_entries()


def _windows_process_entries() -> tuple[bool, list[dict[str, Any]]]:
    """Return running process details from Windows CIM process output."""
    try:
        completed = subprocess.run(
            WINDOWS_PROCESS_SNAPSHOT_COMMAND,
            check=False,
            capture_output=True,
            text=True,
            **_windows_no_console_kwargs(),
        )
    except OSError:
        return False, []
    if completed.returncode != 0:
        return False, []
    processes: list[dict[str, Any]] = []
    for row in csv.DictReader((completed.stdout or "").splitlines()):
        pid_text = str(row.get("ProcessId") or "").strip()
        if pid_text.isdigit() is not True:
            continue
        processes.append(
            {
                PROCESS_INFO_KEY_PID: int(pid_text),
                PROCESS_INFO_KEY_NAME: str(row.get("Name") or "").strip(),
                PROCESS_INFO_KEY_COMMAND_LINE: str(row.get("CommandLine") or "").strip(),
            }
        )
    return True, processes


def _posix_process_entries() -> tuple[bool, list[dict[str, Any]]]:
    """Return running process details from POSIX `ps` output."""
    try:
        completed = subprocess.run(
            POSIX_PROCESS_SNAPSHOT_COMMAND,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False, []
    if completed.returncode != 0:
        return False, []
    processes: list[dict[str, Any]] = []
    for line in (completed.stdout or "").splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) < 2 or parts[0].isdigit() is not True:
            continue
        processes.append(
            {
                PROCESS_INFO_KEY_PID: int(parts[0]),
                PROCESS_INFO_KEY_NAME: parts[1].strip(),
                PROCESS_INFO_KEY_COMMAND_LINE: parts[2].strip() if len(parts) > 2 else "",
            }
        )
    return True, processes


def _process_entries_matching_pattern(
    processes: list[dict[str, Any]],
    *,
    pattern: re.Pattern[str],
) -> list[dict[str, Any]]:
    """Return process entries whose PID, name, or command line match the regex."""
    matches: list[dict[str, Any]] = []
    for process in processes:
        if pattern.search(_process_entry_match_text(process)) is None:
            continue
        matches.append(process)
    return matches


def _process_entry_match_text(process: dict[str, Any]) -> str:
    """Return the normalized text searched by the PID lookup workflow."""
    # Keep this search surface aligned with the consumer observer locator in
    # consumer/src/opamp_consumer/process_utils.py:ProcessUtils.find_pid_by_regex
    # so the dev-only PID lookup mirrors observer-mode process detection.
    return " ".join(
        [
            str(process.get(PROCESS_INFO_KEY_PID) or "").strip(),
            str(process.get(PROCESS_INFO_KEY_NAME) or "").strip(),
            str(process.get(PROCESS_INFO_KEY_COMMAND_LINE) or "").strip(),
        ]
    ).strip()


def _print_pid_lookup_results(
    pattern_text: str,
    matches: list[dict[str, Any]],
) -> None:
    """Print the PID lookup result summary and matched process details."""
    print(f"Regex: {pattern_text}")
    if not matches:
        print("No running processes matched the regular expression.")
        return
    print(f"Matched {len(matches)} process(es):")
    for index, process in enumerate(matches, start=1):
        print(f"{index}. {process.get(PROCESS_INFO_KEY_NAME) or 'process'}")
        print(f"   pid: {process.get(PROCESS_INFO_KEY_PID) or ''}")
        command_line = str(process.get(PROCESS_INFO_KEY_COMMAND_LINE) or "").strip()
        if command_line:
            print(f"   command_line: {command_line}")


def _catalog_start_available() -> bool:
    """Return whether the catalog UI start action should be available."""
    repo_root = _repo_root()
    opamp_config_path = (repo_root / "config" / "opamp.json").resolve()
    opamp_config = _load_json_file(opamp_config_path)
    opamp_section = opamp_config.get("opamp", {})
    if not isinstance(opamp_section, dict):
        return False
    catalog_config = opamp_section.get("config_catalog", {})
    if not isinstance(catalog_config, dict):
        return False
    sources = catalog_config.get("sources", [])
    return isinstance(sources, list) and bool(sources)


def _materialize_ordered_actions(
    *,
    order: list[str],
    action_map: dict[str, dict[str, Any]],
) -> list[tuple[str, dict[str, Any]]]:
    """Return ordered `(label, action)` pairs from one action map.

    The `order` list is intentionally position-sensitive because the interactive
    numbered menus expose this exact sequence to the user.
    """
    actions: list[tuple[str, dict[str, Any]]] = []
    for action_id in order:
        action = action_map.get(action_id)
        if not action:
            continue
        label = str(action.get("label") or action_id)
        actions.append((label, action))
    return actions


def _start_action_labels() -> list[str]:
    """Return start labels without constructing launch actions."""
    return [label for label, _action in _start_actions()]


def _stop_action_labels() -> list[str]:
    """Return stop labels without constructing stop actions."""
    return [label for label, _action in _stop_actions()]


def _restart_action_labels() -> list[str]:
    """Return restart labels without constructing restart actions."""
    return [label for label, _action in _restart_actions()]


def _guided_action_aliases(action: dict[str, Any]) -> list[str]:
    """Return labels and short aliases accepted for guided selections."""
    label = str(action.get("label") or "").strip()
    action_id = str(action.get("id") or _slugify(label).replace("-", "_")).strip()
    normalized = _normalized_label(label)
    aliases: list[str] = [label, str(label).lower(), _slugify(label)]
    aliases.extend(
        str(item).strip()
        for item in action.get("aliases", [])
        if str(item).strip()
    )
    aliases.extend(GUIDED_ACTION_ALIASES.get(action_id, []))
    if action_id == normalized:
        aliases.extend(GUIDED_ACTION_ALIASES.get(normalized, []))

    deduped: list[str] = []
    seen: set[str] = set()
    for entry in aliases:
        cleaned = str(entry or "").strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(cleaned)
    return deduped


def _guided_labels_for_intent(intent: str) -> list[str]:
    """Return guided labels for the requested intent."""
    if intent == INTENT_START:
        return _start_action_labels()
    if intent == INTENT_STOP:
        return _stop_action_labels()
    if intent == INTENT_RESTART:
        return _restart_action_labels()
    return []


def _matches_guided_label(selection: str, label: str) -> bool:
    """Return whether a selection matches a guided label or one of its aliases."""
    normalized = _normalized_label(selection)
    if not normalized:
        return False
    action = _resolve_guided_action_by_label(label)
    if action is None:
        return False
    for candidate in _guided_action_aliases(action):
        if _normalized_label(candidate) == normalized:
            return True
    return False


def _matching_guided_labels(intent: str, partial_selection: str) -> list[str]:
    """Return guided labels that match a partial typed selection."""
    normalized_prefix = _normalized_label(partial_selection)
    matches: list[str] = []
    for label in _guided_labels_for_intent(intent):
        if not normalized_prefix:
            matches.append(label)
            continue
        action = _resolve_guided_action_by_label(label, intent=intent)
        if action is None:
            continue
        for alias in _guided_action_aliases(action):
            if _normalized_label(alias).startswith(normalized_prefix):
                matches.append(label)
                break
    return matches


def _setup_readline_completion(words: Iterable[str]) -> None:
    """Enable simple TAB completion when readline is available."""
    try:
        readline = importlib.import_module("readline")
    except ImportError:
        return

    entries = _completion_entries(words)

    def completer(text: str, state: int) -> str | None:
        line_buffer = str(readline.get_line_buffer() or "")
        subcommand_prefix = _config_subcommand_prefix(line_buffer)
        if subcommand_prefix is not None:
            lowered_text = str(text or "").lower()
            matches = [
                subcommand
                for subcommand in _config_subcommands()
                if subcommand.startswith(lowered_text)
            ]
        elif _cli_config_subcommand_prefix(line_buffer) is not None:
            lowered_text = str(text or "").lower()
            matches = [
                subcommand
                for subcommand in _cli_config_subcommands()
                if subcommand.startswith(lowered_text)
            ]
        else:
            lowered_text = str(text or "").lower()
            matches = [entry for entry in entries if entry.lower().startswith(lowered_text)]
        if state < len(matches):
            return matches[state]
        return None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")


def _prompt_toolkit_input_reader(words: Iterable[str]) -> Callable[[str], str] | None:
    """Return prompt_toolkit-backed input reader with autocomplete when available."""
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return None
    try:
        pt_prompt = importlib.import_module("prompt_toolkit").prompt
        pt_completion = importlib.import_module("prompt_toolkit.completion")
    except ImportError:
        return None
    Completer = pt_completion.Completer
    Completion = pt_completion.Completion
    PathCompleter = pt_completion.PathCompleter

    top_level_words = sorted({str(word).strip() for word in words if str(word).strip()})
    config_subcommands = list(_config_subcommands())
    cli_config_subcommands = list(_cli_config_subcommands())
    path_completer = PathCompleter(expanduser=True)

    def _line_prefix(document: Any) -> str:
        """Return the current token-like prefix up to the cursor."""
        before_cursor = str(document.text_before_cursor or "")
        if not before_cursor:
            return ""
        last_space = max(before_cursor.rfind(" "), before_cursor.rfind("\t"))
        if last_space < 0:
            return before_cursor
        return before_cursor[last_space + 1 :]

    def _yield_word_matches(
        *,
        options: Iterable[str],
        prefix: str,
    ) -> Iterable[Any]:
        lowered_prefix = prefix.lower()
        start_position = -len(prefix)
        seen: set[str] = set()
        for option in options:
            text = str(option or "").strip()
            if not text:
                continue
            lowered = text.lower()
            if lowered in seen:
                continue
            if lowered_prefix and lowered.startswith(lowered_prefix) is not True:
                continue
            seen.add(lowered)
            yield Completion(text, start_position=start_position)

    class _OpampCliCompleter(Completer):
        """Context-aware completer for top-level and guided CLI commands."""

        def get_completions(self, document: Any, complete_event: Any) -> Iterable[Any]:  # noqa: PLR0911
            text = str(document.text_before_cursor or "")
            stripped = text.lstrip()
            lowered = stripped.lower()

            if not stripped:
                yield from _yield_word_matches(options=top_level_words, prefix="")
                return

            if lowered.startswith("start "):
                selection = stripped[6:]
                yield from _yield_word_matches(
                    options=_matching_guided_labels(INTENT_START, selection),
                    prefix=selection,
                )
                return

            if lowered == INTENT_START:
                yield Completion(f"{INTENT_START} ", start_position=0)
                return

            if lowered.startswith("stop "):
                selection = stripped[5:]
                yield from _yield_word_matches(
                    options=_matching_guided_labels(INTENT_STOP, selection),
                    prefix=selection,
                )
                return

            if lowered == INTENT_STOP:
                yield Completion(f"{INTENT_STOP} ", start_position=0)
                return

            if lowered.startswith("restart "):
                selection = stripped[8:]
                yield from _yield_word_matches(
                    options=_matching_guided_labels(INTENT_RESTART, selection),
                    prefix=selection,
                )
                return

            if lowered == INTENT_RESTART:
                yield Completion(f"{INTENT_RESTART} ", start_position=0)
                return

            if lowered == COMMAND_CONFIG:
                yield Completion(f"{COMMAND_CONFIG} ", start_position=0)
                return

            if lowered == COMMAND_CLI_CONFIG:
                yield Completion(f"{COMMAND_CLI_CONFIG} ", start_position=0)
                return

            config_subcommand_prefix = _config_subcommand_prefix(text)
            if config_subcommand_prefix is not None:
                yield from _yield_word_matches(
                    options=config_subcommands,
                    prefix=config_subcommand_prefix,
                )
                return

            cli_config_subcommand_prefix = _cli_config_subcommand_prefix(text)
            if cli_config_subcommand_prefix is not None:
                yield from _yield_word_matches(
                    options=cli_config_subcommands,
                    prefix=cli_config_subcommand_prefix,
                )
                return

            if (
                lowered.startswith(f"{COMMAND_CONFIG} {COMMAND_CONFIG_VALIDATE} ")
                or lowered.startswith(f"{COMMAND_CONFIG} {COMMAND_CONFIG_METADATA} ")
                or lowered.startswith(f"{COMMAND_CLI_CONFIG} {COMMAND_CLI_CONFIG_CHANGE} ")
            ):
                yield from path_completer.get_completions(document, complete_event)
                return

            line_prefix = _line_prefix(document)
            if len(stripped.split()) <= 1:
                yield from _yield_word_matches(options=top_level_words, prefix=line_prefix)

            pathish = (
                "/" in line_prefix
                or "\\" in line_prefix
                or line_prefix.startswith((".", "~"))
                or (":" in line_prefix and _is_windows())
                or line_prefix.endswith(".py")
                or line_prefix.endswith(".json")
            )
            if pathish or lowered.startswith("script ") or lowered.startswith("python ") or lowered.startswith("python3 ") or lowered.startswith("py "):
                yield from path_completer.get_completions(document, complete_event)

    completer = _OpampCliCompleter()

    def reader(prompt_text: str) -> str:
        return str(
            pt_prompt(
                prompt_text,
                completer=completer,
                complete_while_typing=True,
            )
        )

    return reader


def _builtin_tty_input_reader(words: Iterable[str]) -> Callable[[str], str] | None:  # noqa: PLR0915
    """Return a lightweight built-in reader with tab completion for TTY use.

    This is primarily a Windows fallback for direct `python cli/main.py` runs
    where `prompt_toolkit` is not installed and `readline` is unavailable.
    """
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return None
    if _is_windows() is not True:
        return None

    try:
        msvcrt = importlib.import_module("msvcrt")
    except ImportError:
        return None

    entries = _completion_entries(words)

    def _render_prompt(prompt_text: str, buffer_text: str) -> None:
        sys.stdout.write("\r")
        sys.stdout.write(f"{prompt_text}{buffer_text}")
        sys.stdout.write(" ")
        sys.stdout.write("\r")
        sys.stdout.write(f"{prompt_text}{buffer_text}")
        sys.stdout.flush()

    def reader(prompt_text: str) -> str:  # noqa: PLR0912,PLR0915
        buffer: list[str] = []
        tab_prefix = ""
        tab_base = ""
        tab_matches: list[str] = []
        tab_index = -1

        sys.stdout.write(prompt_text)
        sys.stdout.flush()

        while True:
            char = msvcrt.getwch()
            if char in {"\r", "\n"}:
                sys.stdout.write("\n")
                sys.stdout.flush()
                return "".join(buffer)
            if char == "\003":
                raise KeyboardInterrupt
            if char == "\x1a":
                raise EOFError
            if char in {"\x00", "\xe0"}:
                msvcrt.getwch()
                continue
            if char in {"\b", "\x7f"}:
                if buffer:
                    buffer.pop()
                    _render_prompt(prompt_text, "".join(buffer))
                tab_prefix = ""
                tab_matches = []
                tab_index = -1
                continue
            if char == "\t":
                current = "".join(buffer)
                completion_base, token_prefix, matches = _completion_candidates(
                    current,
                    entries=entries,
                )
                if not matches:
                    sys.stdout.write("\a")
                    sys.stdout.flush()
                    continue
                if len(matches) == 1:
                    completion = f"{completion_base}{matches[0]}"
                    buffer = list(completion)
                    _render_prompt(prompt_text, completion)
                    tab_prefix = current
                    tab_base = completion_base
                    tab_matches = matches
                    tab_index = 0
                    continue
                common_prefix = os.path.commonprefix(matches)
                if len(common_prefix) > len(token_prefix):
                    completion = f"{completion_base}{common_prefix}"
                    buffer = list(completion)
                    _render_prompt(prompt_text, completion)
                    tab_prefix = completion
                    tab_base = completion_base
                    tab_matches = [
                        match for match in matches if match.startswith(common_prefix)
                    ]
                    tab_index = -1
                    continue
                if current != tab_prefix or completion_base != tab_base or matches != tab_matches:
                    tab_prefix = current
                    tab_base = completion_base
                    tab_matches = matches
                    tab_index = 0
                else:
                    tab_index = (tab_index + 1) % len(tab_matches)
                completion = f"{tab_base}{tab_matches[tab_index]}"
                buffer = list(completion)
                _render_prompt(prompt_text, completion)
                continue
            if char.isprintable():
                buffer.append(char)
                sys.stdout.write(char)
                sys.stdout.flush()
                tab_prefix = ""
                tab_base = ""
                tab_matches = []
                tab_index = -1

    return reader


def _is_process_running(pid: int) -> bool:
    """Return whether a process ID appears to still be running."""
    if pid <= 0:
        return False
    if _is_windows():
        return _is_process_running_windows(pid)
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _is_process_running_windows(pid: int) -> bool:
    """Return whether a Windows process ID appears in `tasklist` output."""
    try:
        completed = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            check=False,
            capture_output=True,
            text=True,
            **_windows_no_console_kwargs(),
        )
    except OSError:
        return False

    if completed.returncode != 0:
        return False

    output = (completed.stdout or "").strip()
    if not output:
        return False

    for line in output.splitlines():
        row = line.strip()
        if not row or row.upper().startswith("INFO:"):
            continue
        try:
            columns = next(csv.reader([row]))
        except csv.Error:
            continue
        if len(columns) >= 2 and columns[1].strip() == str(pid):
            return True
    return False


def _load_cli_process_state() -> dict[str, Any]:
    """Load persisted CLI-managed process records."""
    state_path = _cli_process_state_path()
    if state_path.is_file() is not True:
        return {"processes": []}
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {"processes": []}
    if not isinstance(payload, dict):
        return {"processes": []}
    processes = payload.get("processes", [])
    if not isinstance(processes, list):
        processes = []
    return {"processes": [item for item in processes if isinstance(item, dict)]}


def _load_cli_settings() -> dict[str, Any]:
    """Load persisted CLI settings."""
    settings_path = _cli_settings_path()
    if settings_path.is_file() is not True:
        return {}
    try:
        payload = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _save_cli_process_state(payload: dict[str, Any]) -> None:
    """Persist CLI-managed process records to disk."""
    state_path = _cli_process_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = {
        "updated_at": _utc_timestamp(),
        "processes": payload.get("processes", []),
    }
    state_path.write_text(json.dumps(normalized, indent=2) + "\n", encoding="utf-8")


def _save_cli_settings(payload: dict[str, Any]) -> None:
    """Persist CLI settings to disk."""
    settings_path = _cli_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = dict(payload)
    normalized["updated_at"] = _utc_timestamp()
    settings_path.write_text(json.dumps(normalized, indent=2) + "\n", encoding="utf-8")


def _prune_cli_process_state() -> dict[str, Any]:
    """Remove stale process records and persist the cleaned state."""
    payload = _load_cli_process_state()
    active: list[dict[str, Any]] = []
    for record in payload.get("processes", []):
        pid = int(record.get("pid", 0) or 0)
        if _is_process_running(pid):
            active.append(record)
    cleaned = {"processes": active}
    _save_cli_process_state(cleaned)
    return cleaned


def _record_cli_process(  # noqa: PLR0913
    *,
    name: str,
    pid: int,
    command_text: str,
    cwd: Path,
    log_file: Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Append one managed process record to CLI state."""
    payload = _prune_cli_process_state()
    payload.setdefault("processes", [])
    payload["processes"].append(
        {
            "name": str(name),
            "pid": int(pid),
            "command": str(command_text),
            "cwd": str(cwd.resolve()),
            "log_file": str(log_file.resolve()) if log_file is not None else "",
            "started_at": _utc_timestamp(),
            ACTION_KEY_METADATA: metadata or {},
        }
    )
    _save_cli_process_state(payload)


def _append_log_line(log_file: Path, text: str) -> None:
    """Append one UTF-8 log line to a managed CLI log file."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(text.rstrip("\n") + "\n")


def _prepare_launch_log(*, label: str, command_text: str, cwd: Path, log_name: str) -> Path:
    """Create a launch log file and write a small banner before execution."""
    log_file = (_cli_log_dir() / f"{log_name}.log").resolve()
    # Reset per-process launch logs so stale startup markers from previous runs
    # do not trigger false negatives in current startup checks.
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text("", encoding="utf-8")
    _append_log_line(log_file, f"[{_utc_timestamp()}] launch={label}")
    _append_log_line(log_file, f"[{_utc_timestamp()}] cwd={cwd}")
    _append_log_line(log_file, f"[{_utc_timestamp()}] command={command_text}")
    return log_file


def _terminate_process(pid: int) -> None:
    """Best-effort termination of one managed process ID."""
    if pid <= 0:
        return
    try:
        if _is_windows():
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **_windows_no_console_kwargs(),
            )
        else:
            os.kill(pid, 15)
    except OSError:
        return


def _log_has_startup_failure(log_file: Path) -> str | None:
    """Return a matching startup failure marker from the log, if present."""
    if log_file.is_file() is not True:
        return None
    try:
        contents = log_file.read_text(encoding="utf-8").lower()
    except OSError:
        return None
    for marker in STARTUP_FAILURE_MARKERS:
        if marker in contents:
            return marker
    return None


def _last_non_empty_log_line(log_file: Path) -> str:
    """Return the last non-empty line from one log file, or an empty string."""
    if log_file.is_file() is not True:
        return ""
    try:
        lines = log_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    for line in reversed(lines):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _last_process_output_log_line(log_file: Path) -> str:
    """Return the last non-empty non-CLI-metadata line from a process log."""
    if log_file.is_file() is not True:
        return ""
    try:
        lines = log_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    metadata_pattern = re.compile(
        r"^\[[^\]]+\] "
        r"(launch=|cwd=|command=|launch_failed=|exited_early=|"
        r"startup_check_failed=|pid=)"
    )
    for line in reversed(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if metadata_pattern.match(stripped):
            continue
        return stripped
    return ""


def _running_simulator_instance_names(state_file: Path) -> list[str]:
    """Return running simulator instance names from one launcher state file."""
    payload = _load_json_file(state_file)
    instances = payload.get(SIMULATOR_STATE_KEY_INSTANCES, [])
    if not isinstance(instances, list):
        return []

    running_names: list[str] = []
    for instance in instances:
        if not isinstance(instance, dict):
            continue
        pid = int(instance.get(SIMULATOR_STATE_KEY_PID, 0) or 0)
        if pid <= 0 or _is_process_running(pid) is not True:
            continue
        name = str(instance.get(SIMULATOR_STATE_KEY_NAME) or "simulator").strip() or "simulator"
        running_names.append(name)
    return running_names


def _http_ready(url: str) -> bool:
    """Return whether an HTTP endpoint responds successfully."""
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=1.0) as response:
            return (
                int(getattr(response, "status", 200))
                < HTTP_READY_FAILURE_STATUS_THRESHOLD
            )
    except (urllib.error.URLError, TimeoutError, ValueError):
        return False


def _tcp_ready(endpoint: str) -> bool:
    """Return whether a TCP endpoint accepts a connection."""
    host, separator, port_text = endpoint.rpartition(":")
    if not separator:
        return False
    host = host.strip("[]") or LOCALHOST_ADDRESS
    try:
        port = int(port_text)
    except ValueError:
        return False
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False


def _wait_for_background_start(
    *,
    process: subprocess.Popen[Any],
    log_file: Path,
    readiness_url: str,
    readiness_tcp: str = "",
) -> tuple[bool, str]:
    """Wait for early exit, startup failure markers, and optional readiness."""
    deadline = time.monotonic() + PROCESS_READY_TIMEOUT_SECONDS
    ready_seen = False
    readiness_target = readiness_url or readiness_tcp
    while time.monotonic() < deadline:
        exit_code = process.poll()
        if exit_code is not None:
            return False, f"exited early with code {int(exit_code)}"
        failure_marker = _log_has_startup_failure(log_file)
        if failure_marker:
            return False, f"startup failure detected: {failure_marker}"
        if readiness_url:
            if _http_ready(readiness_url):
                ready_seen = True
        elif readiness_tcp:
            if _tcp_ready(readiness_tcp):
                ready_seen = True
        else:
            return True, ""
        if ready_seen:
            return True, ""
        time.sleep(PROCESS_READY_POLL_INTERVAL_SECONDS)
    if readiness_target:
        if ready_seen and process.poll() is None and _log_has_startup_failure(log_file) is None:
            return True, ""
        return False, f"readiness probe timed out for {readiness_target}"
    return True, ""


def _remove_cli_process_records(names: Iterable[str]) -> None:
    """Remove managed process records for the provided names."""
    target_names = {str(name) for name in names}
    payload = _load_cli_process_state()
    kept = [
        record
        for record in payload.get("processes", [])
        if str(record.get("name")) not in target_names
    ]
    _save_cli_process_state({"processes": kept})


def _resolve_path_relative_to(raw_path: str, base_dir: Path) -> Path:
    """Resolve one path relative to a config file directory."""
    candidate = Path(str(raw_path or "").strip()).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (base_dir / candidate).resolve()


def _strip_config_scalar(value: str) -> str:
    """Return a simple YAML-ish scalar without wrapping quotes or comments."""
    text = str(value or "").strip()
    if "#" in text:
        text = text.split("#", 1)[0].strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    return text


def _resolve_config_env_refs(value: str) -> str:
    """Resolve simple Elastic/Vector-style environment placeholders in paths."""
    text = str(value or "")

    def replace_braced(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        if body.startswith("env."):
            parts = [part.strip() for part in body.split("|")]
            for part in parts:
                if part.startswith("env."):
                    resolved = os.environ.get(part[4:])
                    if resolved:
                        return resolved
                    continue
                if len(part) >= 2 and part[0] == part[-1] and part[0] in {"'", '"'}:
                    return part[1:-1]
                if part:
                    return part
            return ""
        if ":" in body:
            name, fallback = body.split(":", 1)
            return os.environ.get(name.strip(), fallback.strip())
        return os.environ.get(body, match.group(0))

    return re.sub(r"\$\{([^}]+)\}", replace_braced, text)


def _resolve_config_path_value(raw_path: str, base_dir: Path) -> Path:
    """Resolve a config path after environment-placeholder expansion."""
    return _resolve_path_relative_to(_resolve_config_env_refs(raw_path), base_dir)


def _agent_log_locations_from_config(config_path: Path) -> tuple[set[Path], set[Path]]:
    """Return log dirs/files declared by one Elastic, Beat, or Vector YAML config."""
    if config_path.is_file() is not True:
        return set(), set()
    try:
        lines = config_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return set(), set()

    log_dirs: set[Path] = set()
    log_files: set[Path] = set()
    in_logging_files = False
    logging_indent = -1
    current_logging_path = ""
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if stripped.startswith(("agent.logging.files:", "logging.files:")):
            in_logging_files = True
            logging_indent = indent
            current_logging_path = ""
            continue
        if in_logging_files and indent <= logging_indent:
            in_logging_files = False
        if in_logging_files and stripped.startswith("path:"):
            raw_value = _strip_config_scalar(stripped.split(":", 1)[1])
            if raw_value:
                current_logging_path = raw_value
                log_dirs.add(_resolve_config_path_value(raw_value, config_path.parent))
        if in_logging_files and stripped.startswith("name:") and current_logging_path:
            raw_name = _strip_config_scalar(stripped.split(":", 1)[1])
            if raw_name:
                log_dir = _resolve_config_path_value(current_logging_path, config_path.parent)
                for suffix in ("", ".log", ".ndjson", ".jsonl"):
                    log_files.add((log_dir / f"{raw_name}{suffix}").resolve())
        if stripped.startswith("path:") and not in_logging_files:
            raw_value = _strip_config_scalar(stripped.split(":", 1)[1])
            if raw_value and Path(raw_value).suffix.lower() in LOG_FILE_SUFFIXES:
                log_files.add(_resolve_config_path_value(raw_value, config_path.parent))
    return log_dirs, log_files


def _elastic_agent_log_dirs_from_config(config_path: Path) -> set[Path]:
    """Return Elastic Agent or Beat log directories declared by one YAML config file."""
    log_dirs, _log_files = _agent_log_locations_from_config(config_path)
    return log_dirs


def _log_file_entry_path(entry: Any) -> str:
    """Return a configured log-file path from a string/object entry."""
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        return str(entry.get("path") or entry.get("file") or "").strip()
    return ""


def _configured_log_locations_from_entry(
    entry: dict[str, Any],
) -> tuple[set[Path], set[Path]]:
    """Return explicit log dirs/files from one CLI config entry."""
    log_dirs: set[Path] = set()
    log_files: set[Path] = set()
    for key in ("log_dirs", "agent_log_dirs"):
        for raw_path in entry.get(key, []):
            if str(raw_path or "").strip():
                log_dirs.add(_resolve_path_from_repo(str(raw_path)))
    for key in ("log_files", "agent_log_files"):
        for item in entry.get(key, []):
            raw_path = _log_file_entry_path(item)
            if raw_path:
                log_files.add(_resolve_path_from_repo(raw_path))
    return log_dirs, log_files


def _configured_log_source_overrides_from_entry(
    entry: dict[str, Any],
) -> dict[Path, dict[str, str]]:
    """Return Smart Log Viewer source fields from configured log-file entries."""
    overrides: dict[Path, dict[str, str]] = {}
    for key in ("log_files", "agent_log_files"):
        for item in entry.get(key, []):
            if not isinstance(item, dict):
                continue
            raw_path = _log_file_entry_path(item)
            if not raw_path:
                continue
            source: dict[str, str] = {}
            tag_name = str(
                item.get("tagName") or item.get("tag") or item.get("label") or ""
            ).strip()
            color = str(item.get("color") or "").strip()
            if tag_name:
                source["tagName"] = tag_name
            if color:
                source["color"] = color
            if source:
                overrides[_resolve_path_from_repo(raw_path)] = source
    return overrides


def _smart_log_viewer_overrides_from_demo_config() -> dict[Path, dict[str, str]]:
    """Return configured Smart Log Viewer source fields from the demo config."""
    overrides: dict[Path, dict[str, str]] = {}
    payload = _load_json_file(_demo_consumer_config_path())
    overrides.update(_configured_log_source_overrides_from_entry(payload))
    for entry in container_management.configured_container_entries(
        demo_config_path=_demo_consumer_config_path(),
        demo_profiles=_load_demo_consumer_profiles(),
    ):
        overrides.update(_configured_log_source_overrides_from_entry(entry))
    for profile in _load_demo_consumer_profiles():
        overrides.update(_configured_log_source_overrides_from_entry(profile))
        for section_name in DEMO_CONSUMER_CLIENT_CONFIG_KEYS:
            section = profile.get(section_name, {})
            if isinstance(section, dict):
                overrides.update(_configured_log_source_overrides_from_entry(section))
    return overrides


def _configured_agent_config_paths_from_opamp_config(config_path: Path) -> set[Path]:
    """Return agent config paths referenced by one OpAMP JSON config."""
    payload = _load_json_file(config_path)
    consumer = payload.get("consumer", {})
    if not isinstance(consumer, dict):
        return set()
    raw_path = str(consumer.get(CONFIG_KEY_AGENT_CONFIG_PATH) or "").strip()
    if not raw_path:
        return set()
    return {_resolve_path_relative_to(raw_path, config_path.parent)}


def _log_locations_from_demo_config() -> tuple[set[Path], set[Path]]:
    """Return log directories and files discovered from demo profile config."""
    log_dirs: set[Path] = set()
    log_files: set[Path] = set()
    payload = _load_json_file(_demo_consumer_config_path())
    explicit_dirs, explicit_files = _configured_log_locations_from_entry(payload)
    log_dirs.update(explicit_dirs)
    log_files.update(explicit_files)
    for entry in container_management.configured_container_entries(
        demo_config_path=_demo_consumer_config_path(),
        demo_profiles=_load_demo_consumer_profiles(),
    ):
        explicit_dirs, explicit_files = _configured_log_locations_from_entry(entry)
        log_dirs.update(explicit_dirs)
        log_files.update(explicit_files)
        volumes = [
            dict(volume)
            for volume in entry.get("volumes", [])
            if isinstance(volume, dict)
        ]
        for raw_dir in entry.get("ensure_dirs", []):
            if str(raw_dir or "").strip():
                log_dirs.add(_resolve_path_from_repo(str(raw_dir)))
        command = [str(item) for item in entry.get("command", [])]
        for index, part in enumerate(command):
            if part == "--path.logs" and index + 1 < len(command):
                mapped_path = container_management.mapped_container_path_to_host_path(
                    container_path=command[index + 1],
                    volumes=volumes,
                    resolve_path_from_repo=_resolve_path_from_repo,
                )
                if mapped_path is not None:
                    log_dirs.add(mapped_path)

    for profile in _load_demo_consumer_profiles():
        explicit_dirs, explicit_files = _configured_log_locations_from_entry(profile)
        log_dirs.update(explicit_dirs)
        log_files.update(explicit_files)
        for section_name in DEMO_CONSUMER_CLIENT_CONFIG_KEYS:
            section = profile.get(section_name, {})
            if not isinstance(section, dict):
                continue
            explicit_dirs, explicit_files = _configured_log_locations_from_entry(section)
            log_dirs.update(explicit_dirs)
            log_files.update(explicit_files)
            raw_config = str(section.get(CONFIG_KEY_CONFIG_PATH) or "").strip()
            if raw_config:
                agent_paths = _configured_agent_config_paths_from_opamp_config(
                    _resolve_path_from_repo(raw_config)
                )
                for agent_path in agent_paths:
                    agent_dirs, agent_files = _agent_log_locations_from_config(agent_path)
                    log_dirs.update(agent_dirs)
                    log_files.update(agent_files)
            raw_agent = str(section.get(CONFIG_KEY_AGENT_CONFIG_PATH) or "").strip()
            if raw_agent:
                agent_dirs, agent_files = _agent_log_locations_from_config(
                    _resolve_path_from_repo(raw_agent)
                )
                log_dirs.update(agent_dirs)
                log_files.update(agent_files)
    return log_dirs, log_files


def _discover_log_locations() -> tuple[set[Path], set[Path]]:
    """Return log directories and exact log files known to the CLI."""
    log_dirs: set[Path] = {_cli_log_dir()}
    log_files: set[Path] = {_cli_component_log_path()}

    state_payload = _load_cli_process_state()
    for record in state_payload.get("processes", []):
        if not isinstance(record, dict):
            continue
        raw_log_file = str(record.get("log_file") or "").strip()
        if raw_log_file:
            log_files.add(Path(raw_log_file).expanduser().resolve())

    opamp_config_path, _source = _effective_opamp_config_path()
    for agent_path in _configured_agent_config_paths_from_opamp_config(opamp_config_path):
        agent_dirs, agent_files = _agent_log_locations_from_config(agent_path)
        log_dirs.update(agent_dirs)
        log_files.update(agent_files)

    demo_dirs, demo_files = _log_locations_from_demo_config()
    log_dirs.update(demo_dirs)
    log_files.update(demo_files)
    return log_dirs, log_files


def _iter_log_files(directory: Path) -> Iterable[Path]:
    """Yield log-like files beneath a directory."""
    if directory.is_dir() is not True:
        return
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in LOG_FILE_SUFFIXES:
            yield path.resolve()


def _smart_log_viewer_config_dir() -> Path:
    """Return the Smart Log Viewer config directory managed by the CLI."""
    return (_cli_runtime_dir() / SMART_LOG_VIEWER_CONFIG_DIRNAME).resolve()


def _smart_log_viewer_tag(path: Path) -> str:
    """Return a concise source tag for a log path."""
    try:
        relative = path.resolve().relative_to(_repo_root().resolve())
        parts = list(relative.parts)
        if len(parts) >= 2:
            return "/".join(parts[-2:])
        return str(relative)
    except ValueError:
        return path.stem


def _smart_log_viewer_sources(
    *,
    active_label: str,
    active_log_file: Path,
) -> list[dict[str, str]]:
    """Build Smart Log Viewer source entries from all discovered client logs."""
    _active_label = str(active_label or "").strip()
    log_dirs, exact_log_files = _discover_log_locations()
    source_overrides = _smart_log_viewer_overrides_from_demo_config()
    candidates: set[Path] = {active_log_file.resolve(), *exact_log_files}
    for directory in log_dirs:
        candidates.update(_iter_log_files(directory))

    sources: list[dict[str, str]] = []
    for index, path in enumerate(sorted(candidates, key=lambda item: str(item).lower())):
        tag = _smart_log_viewer_tag(path)
        if path.resolve() == active_log_file.resolve() and _active_label:
            tag = _active_label
        source = {
            "path": str(path.resolve()),
            "tagName": tag,
            "color": SMART_LOG_VIEWER_COLORS[index % len(SMART_LOG_VIEWER_COLORS)],
        }
        source.update(source_overrides.get(path.resolve(), {}))
        sources.append(source)
    return sources


def _open_log_viewer_for_process_if_enabled(
    *,
    label: str,
    log_file: Path,
    logger: Any,
) -> None:
    """Open either Smart Log Viewer or the traditional tail shell."""
    tail_enabled = process_tail.process_tail_enabled(load_settings=_load_cli_settings)
    if process_tail.smart_log_viewer_enabled():
        if tail_enabled is not True:
            logger.info(
                "smart-log-viewer skipped because process tailing is disabled label=%s",
                label,
            )
            return
        config_dir = _smart_log_viewer_config_dir()
        sources = _smart_log_viewer_sources(
            active_label=label,
            active_log_file=log_file,
        )
        config_path = process_tail.write_smart_log_viewer_config(
            config_dir=config_dir,
            sources=sources,
        )
        logger.info(
            "smart-log-viewer config written config_path=%s sources=%s",
            config_path,
            len(sources),
        )
        process_tail.launch_smart_log_viewer(
            config_dir=config_dir,
            repo_root=_repo_root(),
            logger=logger,
        )
        return

    process_tail.open_process_tail_if_enabled(
        label=label,
        log_file=log_file,
        enabled=tail_enabled,
        logger=logger,
        repo_root=_repo_root(),
        is_windows=_is_windows(),
        shell_quote=_shell_quote,
    )


def _clear_logs() -> int:
    """Clear log files discovered from CLI defaults and configured paths."""
    log_dirs, exact_log_files = _discover_log_locations()
    _close_cli_logger()

    candidates: set[Path] = set()
    candidates.update(path for path in exact_log_files if path.exists())
    for directory in log_dirs:
        candidates.update(_iter_log_files(directory))

    deleted = 0
    errors: list[str] = []
    for path in sorted(candidates, key=lambda item: str(item).lower()):
        try:
            if path.is_file():
                path.unlink()
                deleted += 1
        except OSError as exc:
            errors.append(f"{path}: {exc}")

    print(f"Log directories checked: {len(log_dirs)}")
    for directory in sorted(log_dirs, key=lambda item: str(item).lower()):
        print(f"  {directory}")
    print(f"Log files deleted: {deleted}")
    if errors:
        print("Log files not deleted:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    return 0


def _effective_opamp_config_path() -> tuple[Path, str]:
    """Return the effective OpAMP config path and where it was selected from."""
    configured_path = str(os.environ.get(OPAMP_CONFIG_PATH_ENV) or "").strip()
    if configured_path:
        path = Path(configured_path).expanduser()
        if not path.is_absolute():
            path = (_repo_root() / path).resolve()
        else:
            path = path.resolve()
        return path, OPAMP_CONFIG_PATH_ENV
    return (_repo_root() / "config" / "opamp.json").resolve(), "default"


def _opamp_config_load_status(path: Path) -> str:
    """Return a human-readable load status for an OpAMP JSON config file."""
    if not path.is_file():
        return "no (missing)"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        return f"no (invalid JSON: {exc})"
    if not isinstance(payload, dict):
        return "no (config root is not an object)"
    return "yes"


def _print_status() -> int:
    """Print a summary of managed processes and current PID liveness."""
    settings_path = _cli_settings_path()
    state_path = _cli_process_state_path()
    log_dir = _cli_log_dir()
    cli_log_path = _cli_component_log_path()
    opamp_config_path, opamp_config_source = _effective_opamp_config_path()
    cli_config_path = _demo_consumer_config_path()
    payload = _load_cli_process_state()
    processes = payload.get("processes", [])

    print(f"Settings file: {settings_path}")
    print(f"CLI config file: {cli_config_path}")
    print(f"OpAMP config file: {opamp_config_path} ({opamp_config_source})")
    print(f"OpAMP config loaded: {_opamp_config_load_status(opamp_config_path)}")
    print(f"State file: {state_path}")
    print(f"Log directory: {log_dir}")
    print(f"CLI log file: {cli_log_path}")
    process_tailing = process_tail.process_tail_enabled(load_settings=_load_cli_settings)
    print(f"Process tailing: {'enabled' if process_tailing else 'disabled'}")

    if state_path.exists() is not True:
        print("Managed processes: none recorded")
        return 0

    print(f"Managed processes: {len(processes)}")
    if not processes:
        return 0

    for index, record in enumerate(processes, start=1):
        name = str(record.get("name") or "process")
        pid = int(record.get("pid", 0) or 0)
        started_at = str(record.get("started_at") or "")
        cwd = str(record.get("cwd") or "")
        log_file = str(record.get("log_file") or "")
        status = "running" if _is_process_running(pid) else "stopped"
        print(f"{index}. {name}")
        print(f"   pid: {pid}")
        print(f"   status: {status}")
        if started_at:
            print(f"   started_at: {started_at}")
        if cwd:
            print(f"   cwd: {cwd}")
        if log_file:
            print(f"   log: {log_file}")
    return 0


def _print_option_hierarchy() -> int:
    """Print top-level commands and guided action hierarchy."""
    print("Control flags:")
    print(f"  {CLI_DEMO_FLAG_ENV}: {'enabled' if _demo_mode_enabled() else 'disabled'}")
    print(
        f"  {APP_ENABLE_DEV_FEATURES_ENV}: "
        f"{'enabled' if _dev_features_enabled() else 'disabled'}"
    )
    process_tailing = process_tail.process_tail_enabled(load_settings=_load_cli_settings)
    print(f"  {CLI_SETTING_ENABLE_PROCESS_TAIL}: {'enabled' if process_tailing else 'disabled'}")
    print("")
    print("Top-level commands:")
    for command in _top_level_commands():
        print(f"  - {command}")
    if config_command_available(repo_root=_repo_root()):
        print("")
        print("Config commands:")
        print("  config:")
        print("    - validate <path>")
        print("    - metadata <path>")
    print("")
    print("CLI config commands:")
    print("  cli-config:")
    print("    - view")
    print("    - summary")
    print("    - change-config")
    container_actions = _configured_container_start_actions()
    if container_actions:
        print("")
        print("Configured container starts:")
        for label, _action in container_actions:
            print(f"  - {label}")
    print("")
    print("Guided actions:")
    for intent in GUIDED_INTENTS:
        print(f"  {intent}:")
        actions = _guided_actions_for_intent(intent)
        for label, _action in actions:
            print(f"    - {label}")
        if not actions:
            print("    - (none)")
    return 0


def _detected_behavior_flags() -> list[str]:
    """Return enabled behavior-affecting flags/settings for startup display."""
    detected: list[str] = []
    if _demo_mode_enabled():
        detected.append(f"{CLI_DEMO_FLAG_ENV}=true")
    if _dev_features_enabled():
        detected.append(f"{APP_ENABLE_DEV_FEATURES_ENV}={ENABLED_FLAG_VALUE}")
    if process_tail.process_tail_enabled(load_settings=_load_cli_settings):
        detected.append(f"{CLI_SETTING_ENABLE_PROCESS_TAIL}=true")
    if process_tail.smart_log_viewer_enabled():
        detected.append("SMART_LOG_VIEWER=true")
    return detected


def _existing_path(*candidates: Path) -> Path | None:
    """Return the first existing path from ordered candidates."""
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def _shell_command(
    *,
    command_text: str,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> str:
    """Return one shell command with optional cwd and environment prefixes."""
    parts: list[str] = []
    if cwd is not None:
        if _is_windows():
            parts.append(f"cd /d {_shell_quote(str(cwd.resolve()))}")
        else:
            parts.append(f"cd {_shell_quote(str(cwd.resolve()))}")
    for key, value in (env or {}).items():
        if _is_windows():
            parts.append(f"set {_shell_quote(f'{key}={value}')}")
        else:
            parts.append(f"{key}={_shell_quote(value)}")
    if _is_windows():
        parts.append(command_text)
        return " && ".join(parts)
    if env:
        env_prefix = " ".join(parts[-len(env):]) if env else ""
        prefix_parts = parts[:-len(env)] if env else parts
        if env_prefix:
            prefix = " && ".join(prefix_parts) if prefix_parts else ""
            if prefix:
                return f"{prefix} && {env_prefix} {command_text}"
            return f"{env_prefix} {command_text}"
    prefix = " && ".join(parts)
    if prefix:
        return f"{prefix} && {command_text}"
    return command_text


def _python_module_command(
    *,
    module_name: str,
    python_paths: list[Path] | None = None,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> str:
    """Build a current-platform command for `python -m <module>` with PYTHONPATH."""
    interpreter = _shell_quote(sys.executable)
    module_bits = [interpreter, "-m", module_name]
    for arg in args or []:
        module_bits.append(_shell_quote(arg))
    module_command = " ".join(module_bits)

    extra_paths = [str(path.resolve()) for path in (python_paths or [])]
    existing = os.environ.get(PYTHONPATH_ENV, "")
    all_paths = [*extra_paths]
    if existing.strip():
        all_paths.append(existing)
    merged_env = dict(env or {})
    if all_paths:
        merged_env[PYTHONPATH_ENV] = os.pathsep.join(all_paths)
    return _shell_command(command_text=module_command, env=merged_env, cwd=cwd)


def _python_module_argv(
    *,
    module_name: str,
    args: list[str] | None = None,
) -> list[str]:
    """Return argv list for `python -m <module>` launches."""
    return [sys.executable, "-m", module_name, *(args or [])]


def _python_script_argv(
    *,
    script_path: Path,
    args: list[str] | None = None,
) -> list[str]:
    """Return argv list for direct Python script launches."""
    return [sys.executable, str(script_path.resolve()), *(args or [])]


def _build_exec_env(
    *,
    python_paths: list[Path] | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build child-process environment including merged PYTHONPATH."""
    merged = dict(os.environ)
    merged.update(env or {})
    extra_paths = [str(path.resolve()) for path in (python_paths or [])]
    existing = str(merged.get(PYTHONPATH_ENV, "")).strip()
    if existing:
        extra_paths.append(existing)
    if extra_paths:
        merged[PYTHONPATH_ENV] = os.pathsep.join(extra_paths)
    merged.setdefault("PYTHONUNBUFFERED", "1")
    return merged


def _load_json_file(path: Path) -> dict[str, Any]:
    """Load one JSON file into a dictionary, or return an empty mapping."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_cli_config_payload(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Load and validate one CLI demo profile config file."""
    if path.is_file() is not True:
        return None, f"file not found: {path}"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc}"
    except (OSError, TypeError) as exc:
        return None, f"could not read file: {exc}"
    if not isinstance(payload, dict):
        return None, "config root must be a JSON object"
    profiles = payload.get("profiles")
    if not isinstance(profiles, list):
        return None, "config must contain a 'profiles' list"
    return payload, None


def _resolve_cli_config_input_path(raw_path: str) -> Path:
    """Resolve a user-provided CLI config path from the current working directory."""
    candidate = Path(str(raw_path or "").strip()).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (Path.cwd() / candidate).resolve()


def _execute_cli_config_command(
    argv: list[str],
    *,
    input_reader: Callable[[str], str] | None = None,
) -> int:
    """Execute one `cli-config` command."""
    if not argv:
        print(
            "Error: cli-config requires one of: view, summary, change-config",
            file=sys.stderr,
        )
        return 2
    subcommand = str(argv[0] or "").strip().lower()
    if subcommand == COMMAND_CLI_CONFIG_VIEW:
        return _print_cli_config_view()
    if subcommand == COMMAND_CLI_CONFIG_SUMMARY:
        return _print_cli_config_summary_for_path(_demo_consumer_config_path())
    if subcommand == COMMAND_CLI_CONFIG_CHANGE:
        raw_path = str(argv[1] if len(argv) > 1 else "").strip()
        if not raw_path:
            raw_path = _prompt_text(
                "New CLI config path: ",
                input_reader=input_reader,
            ).strip()
        if not raw_path:
            print("Error: no replacement CLI config path was provided.", file=sys.stderr)
            return 1
        return _change_cli_config(raw_path)
    print(f"Error: unknown cli-config command: {subcommand}", file=sys.stderr)
    return 2


def _interactive_failure_message(raw_command: str, code: int) -> str:
    """Return a friendly interactive failure message for one command."""
    match_text = _command_match_text(raw_command)
    lowered = match_text.lower()
    if lowered == COMMAND_CLI_CONFIG or lowered.startswith(f"{COMMAND_CLI_CONFIG} "):
        if int(code) == 2:
            return (
                "CLI config command was not understood. Use `cli-config view`, "
                "`cli-config summary`, or `cli-config change-config`."
            )
        return "CLI config command did not complete. Review the message above and try again."
    return COMMAND_EXITED_TEMPLATE.format(code=code)


def _print_cli_config_view() -> int:
    """Print the active CLI config file in full followed by its absolute path."""
    config_path = _demo_consumer_config_path()
    _payload, error = _load_cli_config_payload(config_path)
    if _payload is None:
        print(f"Error: failed to load active CLI config: {error}", file=sys.stderr)
        print(f"CLI config file: {config_path}", file=sys.stderr)
        return 1
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Error: failed to read active CLI config: {exc}", file=sys.stderr)
        print(f"CLI config file: {config_path}", file=sys.stderr)
        return 1
    print(text, end="" if text.endswith("\n") else "\n")
    print(f"CLI config file: {config_path}")
    return 0


def _print_cli_config_summary_for_path(config_path: Path) -> int:
    """Print a short summary for one CLI config path."""
    payload, error = _load_cli_config_payload(config_path)
    if payload is None:
        print(f"Error: failed to load CLI config: {error}", file=sys.stderr)
        print(f"CLI config file: {config_path}", file=sys.stderr)
        return 1
    _print_cli_config_summary(config_path=config_path, payload=payload)
    return 0


def _change_cli_config(raw_path: str) -> int:
    """Persist a replacement active CLI config path after loading it successfully."""
    current_path = _demo_consumer_config_path()
    replacement_path = _resolve_cli_config_input_path(raw_path)
    payload, error = _load_cli_config_payload(replacement_path)
    if payload is None:
        print("ERROR: CLI config was NOT changed.", file=sys.stderr)
        print(
            f"Failed to load replacement CLI config: {replacement_path}",
            file=sys.stderr,
        )
        print(f"Cause: {error}", file=sys.stderr)
        print(f"Current CLI config remains: {current_path}", file=sys.stderr)
        return 1
    settings = _load_cli_settings()
    settings[CLI_SETTING_DEMO_CONFIG_PATH] = str(replacement_path)
    _save_cli_settings(settings)
    print(f"CLI config changed: {replacement_path}")
    _print_cli_config_summary(config_path=replacement_path, payload=payload)
    return 0


def _print_cli_config_summary(
    *,
    config_path: Path,
    payload: dict[str, Any],
) -> None:
    """Print a brief bullet summary of key CLI profile config entries."""
    profiles = _normalize_demo_consumer_profiles(payload)
    raw_profiles = payload.get("profiles", [])
    raw_profile_count = len(raw_profiles) if isinstance(raw_profiles, list) else 0
    component_counts = _cli_config_component_counts(profiles)
    names = [str(profile.get("name") or "").strip() for profile in profiles]
    print("CLI config summary:")
    if raw_profile_count == len(profiles):
        print(f"- Demo configs: {len(profiles)}")
    else:
        print(f"- Demo configs: {len(profiles)} launchable, {raw_profile_count} configured")
    if names:
        print(f"- Profiles: {', '.join(names)}")
    for label, count in component_counts:
        if count > 0:
            print(f"- {label}: {count}")
    print(f"- CLI config file: {config_path}")


def _cli_config_component_counts(
    profiles: list[dict[str, Any]],
) -> list[tuple[str, int]]:
    """Return user-facing component counts for CLI profile summaries."""
    component_specs = [
        ("Simulators", "simulator", "instances_path"),
        ("Fluent Bit configs", DEMO_PROFILE_KEY_FLUENTBIT, CONFIG_KEY_CONFIG_PATH),
        ("Fluentd configs", DEMO_PROFILE_KEY_FLUENTD, CONFIG_KEY_CONFIG_PATH),
        ("Elastic Agent configs", DEMO_PROFILE_KEY_ELASTIC_AGENT, CONFIG_KEY_CONFIG_PATH),
        (
            "Elastic Heartbeat configs",
            DEMO_PROFILE_KEY_ELASTIC_HEARTBEAT,
            CONFIG_KEY_CONFIG_PATH,
        ),
        ("Vector configs", DEMO_PROFILE_KEY_VECTOR, CONFIG_KEY_CONFIG_PATH),
    ]
    counts: list[tuple[str, int]] = []
    for label, section_name, key in component_specs:
        count = 0
        for profile in profiles:
            section = profile.get(section_name, {})
            if isinstance(section, dict) and str(section.get(key) or "").strip():
                count += 1
        counts.append((label, count))
    container_count = 0
    for profile in profiles:
        containers = profile.get("containers", [])
        if isinstance(containers, list):
            container_count += len(containers)
    counts.append(("Container starts", container_count))
    return counts


def _resolve_path_from_repo(raw_path: str) -> Path:
    """Resolve one path relative to repository root."""
    candidate = Path(str(raw_path or "").strip()).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (_repo_root() / candidate).resolve()


def _resolve_optional_path_from_repo(raw_path: str) -> Path | None:
    """Resolve one optional repo-relative path, returning None when blank."""
    cleaned = str(raw_path or "").strip()
    if not cleaned:
        return None
    return _resolve_path_from_repo(cleaned)


def _load_demo_consumer_profiles() -> list[dict[str, Any]]:
    """Load validated demo consumer profile entries from JSON mapping."""
    config_path = _demo_consumer_config_path()
    payload = _load_json_file(config_path)
    return _normalize_demo_consumer_profiles(payload)


def _normalize_demo_consumer_profiles(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return launchable demo consumer profile entries from a config payload."""
    profiles_raw = payload.get("profiles", [])
    if not isinstance(profiles_raw, list):
        return []
    profiles: list[dict[str, Any]] = []
    for index, entry in enumerate(profiles_raw, start=1):
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        if not name:
            continue
        fluentbit = entry.get(DEMO_PROFILE_KEY_FLUENTBIT, {})
        fluentd = entry.get(DEMO_PROFILE_KEY_FLUENTD, {})
        simulator = entry.get("simulator", {})
        elastic_agent = entry.get(DEMO_PROFILE_KEY_ELASTIC_AGENT, {})
        elastic_heartbeat = entry.get(DEMO_PROFILE_KEY_ELASTIC_HEARTBEAT, {})
        vector = entry.get(DEMO_PROFILE_KEY_VECTOR, {})
        containers = entry.get("containers", [])
        if (
            not isinstance(fluentbit, dict)
            or not isinstance(fluentd, dict)
            or not isinstance(simulator, dict)
            or not isinstance(elastic_agent, dict)
            or not isinstance(elastic_heartbeat, dict)
            or not isinstance(vector, dict)
        ):
            continue
        if not isinstance(containers, list):
            containers = []
        profiles.append(
            {
                "profile_index": index,
                "name": name,
                "scenario_description": _demo_profile_scenario_description(entry),
                DEMO_PROFILE_KEY_FLUENTBIT: dict(fluentbit),
                DEMO_PROFILE_KEY_FLUENTD: dict(fluentd),
                "simulator": dict(simulator),
                DEMO_PROFILE_KEY_ELASTIC_AGENT: dict(elastic_agent),
                DEMO_PROFILE_KEY_ELASTIC_HEARTBEAT: dict(elastic_heartbeat),
                DEMO_PROFILE_KEY_VECTOR: dict(vector),
                "containers": [
                    dict(container)
                    for container in containers
                    if isinstance(container, dict)
                ],
            }
        )
    return profiles


def _demo_profile_scenario_description(entry: dict[str, Any]) -> str:
    """Return the normalized scenario description for one demo profile entry."""
    scenario_description = str(entry.get("scenario_description") or "").strip()
    if scenario_description:
        return scenario_description
    return str(entry.get("description") or "").strip()


def _demo_profile_by_name(profile_name: str) -> dict[str, Any] | None:
    """Return one demo profile entry by logical name."""
    normalized = _normalized_label(profile_name)
    if not normalized:
        return None
    for profile in _load_demo_consumer_profiles():
        if normalized == str(profile.get("profile_index") or "").strip():
            return profile
        if _normalized_label(str(profile.get("name") or "")) == normalized:
            return profile
    return None


def _demo_profile_label(profile: dict[str, Any]) -> str:
    """Return guided demo label text including the stable profile number."""
    profile_name = str(profile.get("name") or "").strip()
    profile_index = int(profile.get("profile_index") or 0)
    if profile_index > 0:
        return f"Demo consumers ({profile_index}: {profile_name})"
    return f"Demo consumers ({profile_name})"


def _demo_record_prefix(profile_name: str) -> str:
    """Return record-name prefix used for one demo profile."""
    return f"Demo:{profile_name}"


def _configured_container_start_actions() -> list[tuple[str, dict[str, Any]]]:
    """Return configured container start actions when a runtime is available."""
    runtime = container_management.container_runtime_executable()
    if not runtime:
        return []
    actions: list[tuple[str, dict[str, Any]]] = []
    for entry in container_management.configured_container_entries(
        demo_config_path=_demo_consumer_config_path(),
        demo_profiles=_load_demo_consumer_profiles(),
    ):
        action = container_management.container_start_action_from_entry(
            entry,
            runtime=runtime,
            repo_root=_repo_root(),
            resolve_path_from_repo=_resolve_path_from_repo,
            command_text_from_args=_command_text_from_args,
            background_start_action=_background_start_action,
            build_exec_env=_build_exec_env,
            demo_record_prefix=_demo_record_prefix,
        )
        if action is None:
            continue
        actions.append((str(action.get("label") or ""), action))
    return actions


def _action_matches_alias(action: dict[str, Any], selection: str) -> bool:
    """Return whether a free-form selection matches one standalone action."""
    normalized = _normalized_label(selection)
    if not normalized:
        return False
    for alias in _guided_action_aliases(action):
        if _normalized_label(alias) == normalized:
            return True
    return False


def _simulator_state_path_from_profile(profile: dict[str, Any]) -> Path:
    """Return expected simulator launcher state-file path for one profile."""
    simulator = dict(profile.get("simulator", {}))
    instances_path = _resolve_optional_path_from_repo(str(simulator.get("instances_path") or ""))
    if instances_path is None:
        return (_repo_root() / "consumer-sim" / "runtime" / "launcher_state.json").resolve()
    payload = _load_json_file(instances_path)
    state_file_raw = ""
    if payload:
        state_file_raw = str(payload.get("state_file") or "").strip()
    if state_file_raw:
        state_candidate = Path(state_file_raw).expanduser()
        if state_candidate.is_absolute():
            return state_candidate.resolve()
        return (instances_path.parent / state_candidate).resolve()
    return (_repo_root() / "consumer-sim" / "runtime" / "launcher_state.json").resolve()


def _catalog_launch_config_path(
    *,
    base_config_path: Path,
    base_config: dict[str, Any],
) -> Path | None:
    """Write a CLI runtime config that enables the provider catalog feature."""
    opamp_config = base_config.get("opamp", {})
    if not isinstance(opamp_config, dict):
        return None
    catalog_config = opamp_config.get("config_catalog", {})
    if not isinstance(catalog_config, dict):
        return None
    sources = catalog_config.get("sources", [])
    if not isinstance(sources, list) or not sources:
        return None

    payload = json.loads(json.dumps(base_config))
    payload.setdefault("opamp", {})
    payload["opamp"].setdefault("config_catalog", {})
    payload["opamp"]["config_catalog"]["enabled"] = True
    payload["_generated_from"] = str(base_config_path.resolve())

    runtime_config_path = (_cli_runtime_dir() / "catalog-service.json").resolve()
    runtime_config_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return runtime_config_path


def _python_script_command(
    *,
    script_path: Path,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> str:
    """Build a current-platform command for a Python script path."""
    interpreter = _shell_quote(sys.executable)
    parts = [interpreter, _shell_quote(str(script_path.resolve()))]
    for arg in args or []:
        parts.append(_shell_quote(arg))
    return _shell_command(command_text=" ".join(parts), env=env, cwd=cwd)


def _background_start_action(  # noqa: PLR0913
    *,
    action_id: str,
    label: str,
    command_text: str,
    argv: list[str],
    cwd: Path,
    env: dict[str, str],
    launch_url: str | None = None,
    readiness_url: str | None = None,
    readiness_tcp: str | None = None,
    clear_supervisor_signal: bool = False,
) -> dict[str, Any]:
    """Create one background-launch guided action."""
    return {
        "id": action_id,
        "kind": ACTION_KIND_BACKGROUND_START,
        "label": label,
        "command_text": command_text,
        "argv": argv,
        "cwd": str(cwd.resolve()),
        "env": env,
        ACTION_KEY_RECORD_NAME: label,
        ACTION_KEY_LOG_NAME: _slugify(label),
        "launch_url": str(launch_url or "").strip(),
        "readiness_url": str(readiness_url or "").strip(),
        "readiness_tcp": str(readiness_tcp or "").strip(),
        "clear_supervisor_signal": clear_supervisor_signal,
    }


def _clear_stale_supervisor_signal(*, cwd: Path) -> None:
    """Remove an old supervisor stop signal before launching a managed client."""
    signal_path = cwd / SUPERVISOR_SEMAPHORE_FILENAME
    if not signal_path.exists():
        return
    try:
        signal_path.unlink()
    except OSError as exc:
        _get_logger().warning(
            "failed to remove stale supervisor signal path=%s error=%s",
            signal_path,
            exc,
        )
        return
    _get_logger().info("removed stale supervisor signal path=%s", signal_path)


def _simulator_start_action(  # noqa: PLR0913
    *,
    action_id: str,
    label: str,
    command_text: str,
    argv: list[str],
    cwd: Path,
    env: dict[str, str],
    state_file: Path,
) -> dict[str, Any]:
    """Create one simulator batch-start guided action."""
    return {
        "id": action_id,
        "kind": ACTION_KIND_SIMULATOR_START,
        "label": label,
        "command_text": command_text,
        "argv": argv,
        "cwd": str(cwd.resolve()),
        "env": env,
        "state_file": str(state_file.resolve()),
    }


def _stop_recorded_action(
    *,
    action_id: str | None = None,
    label: str,
    record_names: list[str],
) -> dict[str, Any]:
    """Create one stop action that terminates recorded managed processes."""
    return {
        "id": str(action_id or _slugify(label).replace("-", "_")).strip(),
        "kind": ACTION_KIND_STOP_RECORDED,
        "label": label,
        "record_names": list(record_names),
    }


def _demo_consumer_start_action(profile: dict[str, Any]) -> dict[str, Any]:
    """Create one guided demo-consumer start action for one profile."""
    profile_name = str(profile.get("name") or "").strip()
    profile_slug = _slugify(profile_name).replace("-", "_")
    profile_index = int(profile.get("profile_index") or 0)
    return {
        "id": f"demo_consumers_{profile_slug}",
        "kind": ACTION_KIND_DEMO_CONSUMERS_START,
        "label": _demo_profile_label(profile),
        "profile_name": profile_name,
        "profile_index": profile_index,
        "scenario_description": _action_scenario_description(profile),
        "aliases": [
            f"{DEMO_CONSUMERS_SELECTION} {profile_name}",
            f"demo {profile_name}",
            f"consumers {profile_name}",
            *(
                [
                    f"{DEMO_CONSUMERS_SELECTION} {profile_index}",
                    f"demo {profile_index}",
                    f"consumers {profile_index}",
                ]
                if profile_index > 0
                else []
            ),
        ],
    }


def _demo_consumer_stop_action(profile: dict[str, Any]) -> dict[str, Any]:
    """Create one guided demo-consumer stop action for one profile."""
    profile_name = str(profile.get("name") or "").strip()
    profile_slug = _slugify(profile_name).replace("-", "_")
    profile_index = int(profile.get("profile_index") or 0)
    return {
        "id": f"demo_consumers_{profile_slug}",
        "kind": ACTION_KIND_DEMO_CONSUMERS_STOP,
        "label": _demo_profile_label(profile),
        "profile_name": profile_name,
        "profile_index": profile_index,
        "scenario_description": _action_scenario_description(profile),
        "aliases": [
            f"{DEMO_CONSUMERS_SELECTION} {profile_name}",
            f"demo {profile_name}",
            f"consumers {profile_name}",
            *(
                [
                    f"{DEMO_CONSUMERS_SELECTION} {profile_index}",
                    f"demo {profile_index}",
                    f"consumers {profile_index}",
                ]
                if profile_index > 0
                else []
            ),
        ],
    }


def _start_actions() -> list[tuple[str, dict[str, Any]]]:  # noqa: PLR0915
    """Return guided start actions available in current workspace."""
    action_map: dict[str, dict[str, Any]] = {}
    repo_root = _repo_root()
    opamp_config_path = (repo_root / "config" / "opamp.json").resolve()

    server_args = ["--port", str(DEFAULT_SERVER_PORT)]
    server_env = {OPAMP_CONFIG_PATH_ENV: str(opamp_config_path)}
    server_cmd = _python_module_command(
        module_name="opamp_provider.server",
        python_paths=[repo_root / "provider" / "src"],
        args=server_args,
        env=server_env,
        cwd=repo_root,
    )
    action_map[ACTION_ID_SERVER] = _background_start_action(
        action_id=ACTION_ID_SERVER,
        label=LABEL_SERVER,
        command_text=server_cmd,
        argv=_python_module_argv(module_name="opamp_provider.server", args=server_args),
        cwd=repo_root,
        env=_build_exec_env(
            python_paths=[repo_root / "provider" / "src"],
            env=server_env,
        ),
        launch_url=f"http://{LOCALHOST_ADDRESS}:{DEFAULT_SERVER_PORT}/ui",
        readiness_url=f"http://{LOCALHOST_ADDRESS}:{DEFAULT_SERVER_PORT}/ui",
    )

    catalog_service_config_path = (
        repo_root / "catalog-service" / "src" / "catalog_service" / "config" / "catalog-service.json"
    ).resolve()
    if catalog_service_config_path.is_file():
        catalog_payload = _load_json_file(catalog_service_config_path)
        catalog_opamp = catalog_payload.get("opamp", {})
        if isinstance(catalog_opamp, dict):
            catalog_config = catalog_opamp.get("config_catalog", {})
        else:
            catalog_config = {}
        if not isinstance(catalog_config, dict):
            catalog_config = {}
        catalog_route_path = str(catalog_config.get("route_path") or "/catalog").strip() or "/catalog"
        if not catalog_route_path.startswith("/"):
            catalog_route_path = "/" + catalog_route_path
        try:
            catalog_port = int(catalog_config.get("web_port") or DEFAULT_CATALOG_WEB_PORT)
        except (TypeError, ValueError):
            catalog_port = DEFAULT_CATALOG_WEB_PORT
        catalog_args = [ARG_CONFIG_PATH, str(catalog_service_config_path)]
        catalog_server_cmd = _python_module_command(
            module_name="catalog_service",
            python_paths=[repo_root / "catalog-service" / "src"],
            args=catalog_args,
            cwd=repo_root,
        )
        action_map[ACTION_ID_CATALOG_UI] = _background_start_action(
            action_id=ACTION_ID_CATALOG_UI,
            label=LABEL_CONFIG_CATALOG_UI,
            command_text=catalog_server_cmd,
            argv=_python_module_argv(module_name="catalog_service", args=catalog_args),
            cwd=repo_root,
            env=_build_exec_env(
                python_paths=[repo_root / "catalog-service" / "src"],
            ),
            launch_url=f"http://{LOCALHOST_ADDRESS}:{catalog_port}{catalog_route_path}",
            readiness_url=f"http://{LOCALHOST_ADDRESS}:{catalog_port}{catalog_route_path}",
        )

    config_service_args = [
        ARG_CONFIG_PATH,
        str(
            repo_root
            / "config-service"
            / "src"
            / "config_service"
            / "config"
            / "config-service.json"
        ),
    ]
    config_service_cmd = _python_module_command(
        module_name="config_service",
        python_paths=[
            repo_root / "config-service" / "src",
            repo_root / "provider" / "src",
        ],
        args=config_service_args,
        cwd=repo_root,
    )
    action_map[ACTION_ID_CONFIG_SERVICE] = _background_start_action(
        action_id=ACTION_ID_CONFIG_SERVICE,
        label=LABEL_CONFIG_SERVICE,
        command_text=config_service_cmd,
        argv=_python_module_argv(module_name="config_service", args=config_service_args),
        cwd=repo_root,
        env=_build_exec_env(
            python_paths=[
                repo_root / "config-service" / "src",
                repo_root / "provider" / "src",
            ],
        ),
        launch_url=f"http://{LOCALHOST_ADDRESS}:8080/config-service/ui",
        readiness_url=f"http://{LOCALHOST_ADDRESS}:8080/config-service/ui",
    )

    broker_env = {
        "BROKER_CONFIG_PATH": str(
            (repo_root / "agent_broker" / "opamp_broker" / "config" / "broker.ui_responses.json").resolve()
        ),
        "PYTHONUNBUFFERED": "1",
    }
    broker_cmd = _python_module_command(
        module_name="opamp_broker.broker_app",
        python_paths=[repo_root / "agent_broker", repo_root],
        env=broker_env,
        cwd=repo_root / "agent_broker",
    )
    action_map[ACTION_ID_BROKER] = _background_start_action(
        action_id=ACTION_ID_BROKER,
        label=LABEL_BROKER,
        command_text=broker_cmd,
        argv=_python_module_argv(module_name="opamp_broker.broker_app"),
        cwd=repo_root / "agent_broker",
        env=_build_exec_env(
            python_paths=[repo_root / "agent_broker", repo_root],
            env=broker_env,
        ),
    )

    simulator_env = {APP_ENABLE_DEV_FEATURES_ENV: ENABLED_FLAG_VALUE}
    simulator_state_file = repo_root / "consumer-sim" / "runtime" / "launcher_state.json"
    simulator_cmd = _python_script_command(
        script_path=repo_root / "consumer-sim" / "src" / "consumer_sim_launcher.py",
        args=["start"],
        env=simulator_env,
        cwd=repo_root,
    )
    action_map[ACTION_ID_SIMULATOR] = _simulator_start_action(
        action_id=ACTION_ID_SIMULATOR,
        label=LABEL_SIMULATOR,
        command_text=simulator_cmd,
        argv=_python_script_argv(
            script_path=repo_root / "consumer-sim" / "src" / "consumer_sim_launcher.py",
            args=["start"],
        ),
        cwd=repo_root,
        env=_build_exec_env(env=simulator_env),
        state_file=simulator_state_file,
    )

    action_map[ACTION_ID_FLUENTBIT_CLIENT] = consumer_plugins.default_fluentbit_start_action(
        repo_root=repo_root,
        existing_path=_existing_path,
        python_module_command=_python_module_command,
        python_module_argv=_python_module_argv,
        background_start_action=_background_start_action,
        build_exec_env=_build_exec_env,
    )
    action_map[ACTION_ID_FLUENTD_CLIENT] = consumer_plugins.default_fluentd_start_action(
        repo_root=repo_root,
        existing_path=_existing_path,
        python_module_command=_python_module_command,
        python_module_argv=_python_module_argv,
        background_start_action=_background_start_action,
        build_exec_env=_build_exec_env,
    )
    action_map[ACTION_ID_VECTOR_CLIENT] = consumer_plugins.default_vector_start_action(
        repo_root=repo_root,
        existing_path=_existing_path,
        python_module_command=_python_module_command,
        python_module_argv=_python_module_argv,
        background_start_action=_background_start_action,
        build_exec_env=_build_exec_env,
    )

    actions = _materialize_ordered_actions(
        order=GUIDED_START_ACTION_ORDER,
        action_map=action_map,
    )
    if _demo_mode_enabled():
        for profile in _load_demo_consumer_profiles():
            demo_action = _demo_consumer_start_action(profile)
            actions.append(
                (
                    str(demo_action.get("label") or ""),
                    demo_action,
                )
            )
    return actions


def _stop_actions() -> list[tuple[str, dict[str, Any]]]:
    """Return guided stop actions available in current workspace."""
    action_map: dict[str, dict[str, Any]] = {}
    repo_root = _repo_root()

    server_stop_cmd = (
        f"curl -sS -X POST http://{LOCALHOST_ADDRESS}:{DEFAULT_SERVER_PORT}/api/shutdown "
        "-H \"Content-Type: application/json\" -d \"{\\\"confirm\\\": true}\""
    )
    action_map[ACTION_ID_SERVER] = {
        "id": ACTION_ID_SERVER,
        "kind": ACTION_KIND_SHELL,
        "label": LABEL_SERVER,
        "command_text": server_stop_cmd,
    }

    action_map[ACTION_ID_BROKER] = _stop_recorded_action(
        action_id=ACTION_ID_BROKER,
        label=LABEL_BROKER,
        record_names=[LABEL_BROKER],
    )

    action_map[ACTION_ID_CATALOG_UI] = _stop_recorded_action(
        action_id=ACTION_ID_CATALOG_UI,
        label=LABEL_CONFIG_CATALOG_UI,
        record_names=[LABEL_CONFIG_CATALOG_UI],
    )

    simulator_stop_cmd = _python_script_command(
        script_path=repo_root / "consumer-sim" / "src" / "consumer_sim_launcher.py",
        args=["stop"],
        cwd=repo_root,
    )
    action_map[ACTION_ID_SIMULATOR] = {
        "id": ACTION_ID_SIMULATOR,
        "kind": ACTION_KIND_SHELL,
        "label": LABEL_SIMULATOR,
        "command_text": simulator_stop_cmd,
    }

    action_map[ACTION_ID_CONFIG_SERVICE] = _stop_recorded_action(
        action_id=ACTION_ID_CONFIG_SERVICE,
        label=LABEL_CONFIG_SERVICE,
        record_names=[LABEL_CONFIG_SERVICE],
    )
    action_map[ACTION_ID_FLUENTBIT_CLIENT] = _stop_recorded_action(
        action_id=ACTION_ID_FLUENTBIT_CLIENT,
        label=LABEL_FLUENTBIT_CLIENT,
        record_names=[LABEL_FLUENTBIT_CLIENT],
    )
    action_map[ACTION_ID_FLUENTD_CLIENT] = _stop_recorded_action(
        action_id=ACTION_ID_FLUENTD_CLIENT,
        label=LABEL_FLUENTD_CLIENT,
        record_names=[LABEL_FLUENTD_CLIENT],
    )
    action_map[ACTION_ID_VECTOR_CLIENT] = _stop_recorded_action(
        action_id=ACTION_ID_VECTOR_CLIENT,
        label=LABEL_VECTOR_CLIENT,
        record_names=[LABEL_VECTOR_CLIENT],
    )

    semaphore_path = repo_root / "OpAMPSupervisor.signal"
    if _is_windows():
        client_stop_cmd = _shell_command(
            command_text=(
                f"type nul > {_shell_quote(str(semaphore_path.resolve()))} "
                "&& powershell -NoProfile -Command "
                "\"Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "
                "'opamp_consumer\\.fluentbit\\.client|opamp_consumer\\.fluentd\\.client|opamp_consumer\\.client' } | "
                "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }\""
            ),
            cwd=repo_root,
        )
    else:
        client_stop_cmd = _shell_command(
            command_text=(
                f"touch {_shell_quote(str(semaphore_path.resolve()))} "
                "&& pkill -TERM -f 'opamp_consumer\\.fluentbit\\.client' || true "
                "&& pkill -TERM -f 'opamp_consumer\\.fluentd\\.client' || true "
                "&& pkill -TERM -f 'opamp_consumer\\.client' || true"
            ),
            cwd=repo_root,
        )
    action_map[ACTION_ID_ALL_CLIENTS] = {
        "id": ACTION_ID_ALL_CLIENTS,
        "kind": ACTION_KIND_SHELL,
        "label": LABEL_ALL_CLIENTS,
        "command_text": client_stop_cmd,
    }
    action_map[ACTION_ID_ALL_MANAGED] = {
        "id": ACTION_ID_ALL_MANAGED,
        "kind": ACTION_KIND_STOP_ALL_RECORDED,
        "label": LABEL_ALL_MANAGED_PROCESSES,
    }
    actions = _materialize_ordered_actions(
        order=GUIDED_STOP_ACTION_ORDER,
        action_map=action_map,
    )
    if _demo_mode_enabled():
        for profile in _load_demo_consumer_profiles():
            demo_action = _demo_consumer_stop_action(profile)
            actions.append(
                (
                    str(demo_action.get("label") or ""),
                    demo_action,
                )
            )
    return actions


def _restart_actions() -> list[tuple[str, dict[str, Any]]]:
    """Return guided restart actions available in current workspace."""
    start_actions = _start_actions()
    stop_actions_by_id = {
        str(action.get("id") or "").strip(): action
        for _label, action in _stop_actions()
    }
    actions: list[tuple[str, dict[str, Any]]] = []
    for label, start_action in start_actions:
        action_id = str(start_action.get("id") or "").strip()
        if not action_id:
            continue
        stop_action = stop_actions_by_id.get(action_id)
        if stop_action is None:
            continue
        actions.append(
            (
                label,
                {
                    "id": action_id,
                    "kind": ACTION_KIND_RESTART,
                    "label": label,
                    "start_action": start_action,
                    "stop_action": stop_action,
                },
            )
        )
    return actions


def _guided_actions_for_intent(intent: str) -> list[tuple[str, dict[str, Any]]]:
    """Return guided action list for one intent."""
    if intent == INTENT_START:
        return _start_actions()
    if intent == INTENT_STOP:
        return _stop_actions()
    if intent == INTENT_RESTART:
        return _restart_actions()
    return []


def _select_guided_action(
    *,
    input_reader: Callable[[str], str] | None,
    intent: str,
    actions: list[tuple[str, Any]],
) -> Any | None:
    """Prompt for one guided action and return command text or None."""
    if not actions:
        print(f"No {intent} options are currently available.")
        return None
    print(f"Choose what to {intent}:")
    for index, (label, _command) in enumerate(actions, start=1):
        print(f"  {index}. {label}")
    if _guided_actions_have_descriptions(actions):
        print(f"  {GUIDED_DESCRIPTION_COMMAND_PREFIX}<number>. view {GUIDED_DESCRIPTION_LABEL}")
    print("  0. cancel")

    while True:
        try:
            # Always use plain input for numbered guided selection so only
            # explicit options are shown, not global autocomplete words.
            selected = input(f"{intent}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if selected in {"0", "cancel", "c", ""}:
            return None
        description_index = _guided_description_index(selected, actions=actions)
        if description_index is not None:
            _print_guided_action_description(actions[description_index])
            continue
        if selected.isdigit():
            index = int(selected)
            if 1 <= index <= len(actions):
                return actions[index - 1][1]
        normalized = _normalized_label(selected)
        if normalized:
            for label, action in actions:
                if _matches_guided_label(selected, label):
                    return action
        print("Please choose a valid number from the list.")


def _guided_actions_have_descriptions(actions: list[tuple[str, Any]]) -> bool:
    """Return whether any guided action exposes a scenario description."""
    return any(_action_scenario_description(action) for _label, action in actions)


def _guided_description_index(
    selection: str,
    *,
    actions: list[tuple[str, Any]],
) -> int | None:
    """Return the requested description index from guided-selection input."""
    candidate = str(selection or "").strip()
    if len(candidate) <= 1:
        return None
    if candidate[0].lower() != GUIDED_DESCRIPTION_COMMAND_PREFIX:
        return None
    numeric_portion = candidate[1:]
    if numeric_portion.isdigit() is not True:
        return None
    index = int(numeric_portion) - 1
    if 0 <= index < len(actions):
        return index
    print("Please choose a valid number from the list.")
    return None


def _action_scenario_description(action: dict[str, Any]) -> str:
    """Return the normalized scenario description text for one action payload."""
    return str(
        action.get("scenario_description")
        or action.get("description")
        or ""
    ).strip()


def _print_guided_action_description(action_entry: tuple[str, Any]) -> None:
    """Print the scenario description for one guided action entry."""
    label, action = action_entry
    description = _action_scenario_description(action)
    print()
    print(f"{label} {GUIDED_DESCRIPTION_LABEL}:")
    if description:
        print(description)
    else:
        print("No scenario description is configured.")
    print()


def _split_guided_command(command_text: str) -> tuple[str, str] | None:
    """Return guided intent and selection for `start`/`stop`/`restart` commands."""
    stripped = str(command_text or "").strip()
    if not stripped:
        return None
    try:
        tokens = shlex.split(stripped, posix=True)
    except ValueError:
        tokens = stripped.split()
    if tokens:
        intent = str(tokens[0] or "").strip().strip("\"'").lower()
        if intent in GUIDED_INTENTS:
            selection = " ".join(
                str(token or "").strip().strip("\"'")
                for token in tokens[1:]
            ).strip()
            return intent, selection
    for intent in GUIDED_INTENTS:
        if stripped.lower() == intent:
            return intent, ""
        if stripped.lower().startswith(f"{intent} "):
            return intent, stripped[len(intent) :].strip()
    demo_command = _split_demo_shorthand_command(stripped)
    if demo_command is not None:
        return demo_command
    return None


def _split_demo_shorthand_command(command_text: str) -> tuple[str, str] | None:
    """Return start-intent mapping for demo shorthand commands."""
    if _demo_mode_enabled() is not True:
        return None
    stripped = str(command_text or "").strip()
    if not stripped:
        return None
    lowered = stripped.lower()
    if lowered == COMMAND_DEMO:
        return INTENT_START, DEMO_CONSUMERS_SELECTION
    if lowered == DEMO_CONSUMERS_SELECTION:
        return INTENT_START, DEMO_CONSUMERS_SELECTION
    if lowered.startswith(f"{COMMAND_DEMO} "):
        return INTENT_START, stripped
    return None


def _resolve_guided_action(intent: str, selection: str) -> dict[str, Any] | None:
    """Resolve one guided action from a typed selection."""
    actions = _guided_actions_for_intent(intent)
    for label, action in actions:
        if _matches_guided_label(selection, label):
            return action
    selected = str(selection or "").strip()
    if selected.isdigit():
        index = int(selected)
        if 1 <= index <= len(actions):
            return actions[index - 1][1]
    return None


def _resolve_guided_action_by_label(
    label: str,
    *,
    intent: str | None = None,
) -> dict[str, Any] | None:
    """Resolve one action from its current display label."""
    intents = [intent] if intent in GUIDED_INTENTS else list(GUIDED_INTENTS)
    for current_intent in intents:
        actions = _guided_actions_for_intent(current_intent)
        for current_label, action in actions:
            if current_label == label:
                return action
    return None


def _execute_start_action(action: dict[str, Any]) -> int:
    """Execute one start action by kind."""
    kind = str(action.get("kind", "")).strip().lower()
    if kind == ACTION_KIND_BACKGROUND_START:
        return _launch_background_process(action)
    if kind == ACTION_KIND_SIMULATOR_START:
        return _record_simulator_batch(action)
    if kind == ACTION_KIND_DEMO_CONSUMERS_START:
        return _start_demo_consumers(action)
    raise ValueError(f"unsupported start action kind: {kind}")


def _execute_stop_action(action: dict[str, Any]) -> int:
    """Execute one stop action by kind."""
    kind = str(action.get("kind", "")).strip().lower()
    if kind == ACTION_KIND_SHELL:
        command_text = str(action.get("command_text") or "").strip()
        print(f"Executing: {command_text}")
        return _handle_command(command_text)
    if kind == ACTION_KIND_STOP_RECORDED:
        return _stop_recorded_processes(
            [str(item) for item in action.get("record_names", [])]
        )
    if kind == ACTION_KIND_STOP_ALL_RECORDED:
        return _stop_all_recorded_processes()
    if kind == ACTION_KIND_DEMO_CONSUMERS_STOP:
        return _stop_demo_consumers(action)
    raise ValueError(f"unsupported stop action kind: {kind}")


def _record_name_matches_restart(
    *,
    action_id: str,
    record_name: str,
    tracked_names: set[str],
) -> bool:
    """Return whether one record name should be tracked for restart waiting."""
    if record_name in tracked_names:
        return True
    if action_id == ACTION_ID_SIMULATOR and record_name.startswith(
        f"{SIMULATOR_RECORD_PREFIX}:"
    ):
        return True
    return False


def _tracked_restart_pids(*, action_id: str, start_action: dict[str, Any], stop_action: dict[str, Any]) -> list[int]:
    """Return running process IDs to watch while restarting one action."""
    tracked_names = {
        str(item).strip()
        for item in stop_action.get("record_names", [])
        if str(item).strip()
    }
    start_record_name = str(start_action.get(ACTION_KEY_RECORD_NAME) or "").strip()
    if start_record_name:
        tracked_names.add(start_record_name)

    if not tracked_names and action_id != ACTION_ID_SIMULATOR:
        return []

    payload = _prune_cli_process_state()
    pids: list[int] = []
    for record in payload.get("processes", []):
        if not isinstance(record, dict):
            continue
        record_name = str(record.get("name") or "").strip()
        if not _record_name_matches_restart(
            action_id=action_id,
            record_name=record_name,
            tracked_names=tracked_names,
        ):
            continue
        pid = int(record.get("pid", 0) or 0)
        if pid <= 0:
            continue
        if _is_process_running(pid):
            pids.append(pid)
    return sorted(set(pids))


def _wait_for_pids_to_exit(*, pids: list[int], timeout_seconds: float) -> tuple[bool, list[int]]:
    """Wait until all provided process IDs are no longer running."""
    if not pids:
        return True, []
    deadline = time.monotonic() + max(0.0, float(timeout_seconds))
    while True:
        remaining = [pid for pid in pids if _is_process_running(pid)]
        if not remaining:
            return True, []
        if time.monotonic() >= deadline:
            return False, remaining
        time.sleep(PROCESS_STOP_POLL_INTERVAL_SECONDS)


def _execute_restart_action(action: dict[str, Any]) -> int:
    """Restart one guided component by stop, wait, cleanup, and start."""
    logger = _get_logger()
    label = str(action.get("label") or "component")
    start_action = dict(action.get("start_action", {}))
    stop_action = dict(action.get("stop_action", {}))
    action_id = str(action.get("id") or start_action.get("id") or "").strip()
    if not action_id:
        raise ValueError("restart action is missing id")
    if not start_action or not stop_action:
        raise ValueError(f"restart action is incomplete for {label}")

    tracked_pids = _tracked_restart_pids(
        action_id=action_id,
        start_action=start_action,
        stop_action=stop_action,
    )
    logger.info(
        "restart requested label=%s action_id=%s tracked_pids=%s",
        label,
        action_id,
        tracked_pids,
    )
    print(f"Restarting {label}...")

    stop_code = _execute_stop_action(stop_action)
    if int(stop_code) != 0:
        logger.warning(
            "restart aborted because stop failed label=%s action_id=%s exit_code=%s",
            label,
            action_id,
            int(stop_code),
        )
        return int(stop_code)

    exited, remaining = _wait_for_pids_to_exit(
        pids=tracked_pids,
        timeout_seconds=PROCESS_STOP_TIMEOUT_SECONDS,
    )
    if not exited:
        logger.warning(
            "restart timed out waiting for process exit label=%s action_id=%s remaining=%s",
            label,
            action_id,
            remaining,
        )
        print(
            f"Restart wait timed out for {label}; still running pids: {', '.join(str(pid) for pid in remaining)}",
            file=sys.stderr,
        )
        return 1

    _prune_cli_process_state()
    logger.info("restart cleanup completed label=%s action_id=%s", label, action_id)
    return _execute_start_action(start_action)


def _execute_guided_action(
    *,
    input_reader: Callable[[str], str] | None,
    intent: str,
    selection: str,
) -> int:
    """Execute a guided start/stop/restart action from prompt or direct text."""
    logger = _get_logger()
    actions = _guided_actions_for_intent(intent)
    selected_action = None
    if selection:
        selected_action = _resolve_guided_action(intent, selection)
        if selected_action is None:
            partial_matches = _matching_guided_labels(intent, selection)
            if partial_matches:
                match_set = set(partial_matches)
                matched_actions = [
                    (label, action)
                    for label, action in actions
                    if label in match_set
                ]
                selected_action = _select_guided_action(
                    input_reader=input_reader,
                    intent=intent,
                    actions=matched_actions,
                )
                if not selected_action:
                    logger.info(
                        "guided partial selection cancelled intent=%s selection=%s matches=%s",
                        intent,
                        selection,
                        partial_matches,
                    )
                    return 0
            else:
                available = ", ".join(label for label, _action in actions)
                logger.warning(
                    "rejected guided action intent=%s selection=%s available=%s",
                    intent,
                    selection,
                    available,
                )
                print(
                    f"Unknown {intent} target '{selection}'. Available: {available}",
                    file=sys.stderr,
                )
                return 1
    else:
        selected_action = _select_guided_action(
            input_reader=input_reader,
            intent=intent,
            actions=actions,
        )
        if not selected_action:
            logger.info("guided selection cancelled intent=%s", intent)
            return 0

    kind = str(selected_action.get("kind", "")).strip().lower()
    logger.info(
        "executing guided action intent=%s label=%s kind=%s",
        intent,
        selected_action.get("label", f"{intent} action"),
        kind,
    )
    print(f"Selected: {selected_action.get('label', f'{intent} action')}")
    if intent == INTENT_START:
        return _execute_start_action(selected_action)
    if intent == INTENT_STOP:
        return _execute_stop_action(selected_action)
    if intent == INTENT_RESTART:
        return _execute_restart_action(selected_action)
    raise ValueError(f"unsupported guided intent: {intent}")


def _recorded_names_with_prefix(prefix: str) -> list[str]:
    """Return recorded process names that begin with one prefix."""
    payload = _prune_cli_process_state()
    names: list[str] = []
    for record in payload.get("processes", []):
        name = str(record.get("name") or "").strip()
        if name.startswith(prefix):
            names.append(name)
    return sorted(set(names))


def _stop_recorded_processes_by_prefix(
    *,
    prefix: str,
    allow_empty: bool = True,
) -> int:
    """Stop recorded managed processes that match one name prefix."""
    names = _recorded_names_with_prefix(prefix)
    if not names:
        if not allow_empty:
            print(f"No recorded process IDs found for profile prefix '{prefix}'.")
        return 0
    return _stop_recorded_processes(names)


def _start_demo_consumers(action: dict[str, Any]) -> int:
    """Start simulator + consumer clients for one demo profile."""
    logger = _get_logger()
    profile_name = str(action.get("profile_name") or "").strip()
    profile = _demo_profile_by_name(profile_name)
    if profile is None:
        print(f"Demo profile not found: {profile_name}", file=sys.stderr)
        return 1

    fluentbit = dict(profile.get(DEMO_PROFILE_KEY_FLUENTBIT, {}))
    fluentd = dict(profile.get(DEMO_PROFILE_KEY_FLUENTD, {}))
    simulator = dict(profile.get("simulator", {}))
    elastic_agent = dict(profile.get(DEMO_PROFILE_KEY_ELASTIC_AGENT, {}))
    elastic_heartbeat = dict(profile.get(DEMO_PROFILE_KEY_ELASTIC_HEARTBEAT, {}))
    vector = dict(profile.get(DEMO_PROFILE_KEY_VECTOR, {}))
    containers = [
        dict(item)
        for item in profile.get("containers", [])
        if isinstance(item, dict)
    ]

    fluentbit_config = _resolve_optional_path_from_repo(str(fluentbit.get(CONFIG_KEY_CONFIG_PATH) or ""))
    fluentbit_agent = _resolve_optional_path_from_repo(str(fluentbit.get(CONFIG_KEY_AGENT_CONFIG_PATH) or ""))
    fluentd_config = _resolve_optional_path_from_repo(str(fluentd.get(CONFIG_KEY_CONFIG_PATH) or ""))
    fluentd_agent = _resolve_optional_path_from_repo(str(fluentd.get(CONFIG_KEY_AGENT_CONFIG_PATH) or ""))
    simulator_instances = _resolve_optional_path_from_repo(str(simulator.get("instances_path") or ""))
    elastic_agent_config = _resolve_optional_path_from_repo(str(elastic_agent.get(CONFIG_KEY_CONFIG_PATH) or ""))
    elastic_agent_agent = _resolve_optional_path_from_repo(str(elastic_agent.get(CONFIG_KEY_AGENT_CONFIG_PATH) or ""))
    elastic_heartbeat_config = _resolve_optional_path_from_repo(str(elastic_heartbeat.get(CONFIG_KEY_CONFIG_PATH) or ""))
    elastic_heartbeat_agent = _resolve_optional_path_from_repo(
        str(elastic_heartbeat.get(CONFIG_KEY_AGENT_CONFIG_PATH) or "")
    )
    vector_config = _resolve_optional_path_from_repo(str(vector.get(CONFIG_KEY_CONFIG_PATH) or ""))
    vector_agent = _resolve_optional_path_from_repo(str(vector.get(CONFIG_KEY_AGENT_CONFIG_PATH) or ""))
    simulator_state_file = _simulator_state_path_from_profile(profile)

    configured_components = 0
    if containers:
        configured_components += 1
    if fluentbit_config is not None or fluentbit_agent is not None:
        configured_components += 1
        if fluentbit_config is None:
            print(
                "Demo profile Fluent Bit configuration is incomplete: "
                "`config_path` is required when Fluent Bit is configured.",
                file=sys.stderr,
            )
            return 1
    if fluentd_config is not None or fluentd_agent is not None:
        configured_components += 1
        if fluentd_config is None:
            print(
                "Demo profile Fluentd configuration is incomplete: "
                "`config_path` is required when Fluentd is configured.",
                file=sys.stderr,
            )
            return 1
    if elastic_agent_config is not None or elastic_agent_agent is not None:
        configured_components += 1
        if elastic_agent_config is None:
            print(
                "Demo profile Elastic Agent configuration is incomplete: "
                "`config_path` is required when Elastic Agent is configured.",
                file=sys.stderr,
            )
            return 1
    if elastic_heartbeat_config is not None or elastic_heartbeat_agent is not None:
        configured_components += 1
        if elastic_heartbeat_config is None:
            print(
                "Demo profile Elastic Heartbeat configuration is incomplete: "
                "`config_path` is required when Elastic Heartbeat is configured.",
                file=sys.stderr,
            )
            return 1
    if vector_config is not None or vector_agent is not None:
        configured_components += 1
        if vector_config is None:
            print(
                "Demo profile Vector configuration is incomplete: "
                "`config_path` is required when Vector is configured.",
                file=sys.stderr,
            )
            return 1
    if simulator_instances is not None:
        configured_components += 1
    if configured_components == 0:
        print(
            f"Demo profile '{profile_name}' does not configure any launchable components.",
            file=sys.stderr,
        )
        return 1

    required_paths = [
        path
        for path in [
            fluentbit_config,
            fluentbit_agent,
            fluentd_config,
            fluentd_agent,
            elastic_agent_config,
            elastic_agent_agent,
            elastic_heartbeat_config,
            elastic_heartbeat_agent,
            vector_config,
            vector_agent,
            simulator_instances,
        ]
        if path is not None
    ]
    for required in required_paths:
        if required.is_file() is not True:
            print(
                f"Demo profile path not found: {required} but does exist {required.exists()}",
                file=sys.stderr,
            )
            return 1

    repo_root = _repo_root()
    prefix = _demo_record_prefix(profile_name)
    common_metadata = {"demo_profile": profile_name}

    sequence: list[dict[str, Any]] = []
    if containers:
        runtime = container_management.container_runtime_executable()
        if not runtime:
            print(
                "Demo profile container starts require docker or podman, but neither runtime was found.",
                file=sys.stderr,
            )
            return 1
        runtime_ready, runtime_details = container_management.container_runtime_ready(
            runtime,
            windows_no_console_kwargs=_windows_no_console_kwargs,
        )
        if runtime_ready is not True:
            container_management.print_container_runtime_unavailable(runtime, runtime_details)
            return 1
        for container_entry in containers:
            container_action = container_management.container_start_action_from_entry(
                container_entry,
                runtime=runtime,
                repo_root=_repo_root(),
                profile_name=profile_name,
                resolve_path_from_repo=_resolve_path_from_repo,
                command_text_from_args=_command_text_from_args,
                background_start_action=_background_start_action,
                build_exec_env=_build_exec_env,
                demo_record_prefix=_demo_record_prefix,
            )
            if container_action is None:
                print(
                    "Demo profile container start is incomplete: "
                    f"{container_management.container_entry_id(container_entry)}",
                    file=sys.stderr,
                )
                return 1
            sequence.append(container_action)

    if simulator_instances is not None:
        simulator_action = _simulator_start_action(
            action_id=f"demo_simulator_{_slugify(profile_name)}",
            label=f"{LABEL_SIMULATOR} ({profile_name})",
            command_text=_python_script_command(
                script_path=repo_root / "consumer-sim" / "src" / "consumer_sim_launcher.py",
                args=["start"],
                env={
                    APP_ENABLE_DEV_FEATURES_ENV: ENABLED_FLAG_VALUE,
                    "CONSUMER_SIM_CONFIG": str(simulator_instances),
                },
                cwd=repo_root,
            ),
            argv=_python_script_argv(
                script_path=repo_root / "consumer-sim" / "src" / "consumer_sim_launcher.py",
                args=["start"],
            ),
            cwd=repo_root,
            env=_build_exec_env(
                env={
                    APP_ENABLE_DEV_FEATURES_ENV: ENABLED_FLAG_VALUE,
                    "CONSUMER_SIM_CONFIG": str(simulator_instances),
                }
            ),
            state_file=simulator_state_file,
        )
        simulator_action["record_prefix"] = prefix
        simulator_action["record_metadata"] = dict(common_metadata)
        sequence.append(simulator_action)

    if fluentbit_config is not None:
        sequence.append(
            consumer_plugins.demo_fluentbit_start_action(
                repo_root=repo_root,
                profile_name=profile_name,
                prefix=prefix,
                config_path=fluentbit_config,
                agent_config_path=fluentbit_agent,
                common_metadata=common_metadata,
                python_module_command=_python_module_command,
                python_module_argv=_python_module_argv,
                background_start_action=_background_start_action,
                build_exec_env=_build_exec_env,
            )
        )

    if fluentd_config is not None:
        sequence.append(
            consumer_plugins.demo_fluentd_start_action(
                repo_root=repo_root,
                profile_name=profile_name,
                prefix=prefix,
                config_path=fluentd_config,
                agent_config_path=fluentd_agent,
                common_metadata=common_metadata,
                python_module_command=_python_module_command,
                python_module_argv=_python_module_argv,
                background_start_action=_background_start_action,
                build_exec_env=_build_exec_env,
            )
        )

    if elastic_agent_config is not None:
        sequence.append(
            consumer_plugins.demo_elastic_agent_start_action(
                repo_root=repo_root,
                profile_name=profile_name,
                prefix=prefix,
                config_path=elastic_agent_config,
                agent_config_path=elastic_agent_agent,
                common_metadata=common_metadata,
                python_module_command=_python_module_command,
                python_module_argv=_python_module_argv,
                background_start_action=_background_start_action,
                build_exec_env=_build_exec_env,
            )
        )

    if elastic_heartbeat_config is not None:
        sequence.append(
            consumer_plugins.demo_elastic_heartbeat_start_action(
                repo_root=repo_root,
                profile_name=profile_name,
                prefix=prefix,
                config_path=elastic_heartbeat_config,
                agent_config_path=elastic_heartbeat_agent,
                common_metadata=common_metadata,
                python_module_command=_python_module_command,
                python_module_argv=_python_module_argv,
                background_start_action=_background_start_action,
                build_exec_env=_build_exec_env,
            )
        )
    if vector_config is not None:
        sequence.append(
            consumer_plugins.demo_vector_start_action(
                repo_root=repo_root,
                profile_name=profile_name,
                prefix=prefix,
                config_path=vector_config,
                agent_config_path=vector_agent,
                common_metadata=common_metadata,
                python_module_command=_python_module_command,
                python_module_argv=_python_module_argv,
                background_start_action=_background_start_action,
                build_exec_env=_build_exec_env,
            )
        )
    for sub_action in sequence:
        sub_kind = str(sub_action.get("kind") or "").strip()
        if sub_kind == ACTION_KIND_SIMULATOR_START:
            code = _record_simulator_batch(sub_action)
        else:
            code = _launch_background_process(sub_action)
        if int(code) != 0:
            logger.warning(
                "demo profile start failed profile=%s step_kind=%s exit_code=%s",
                profile_name,
                sub_kind,
                int(code),
            )
            _stop_recorded_processes_by_prefix(prefix=prefix)
            return int(code)

    print(f"Started demo consumers for profile '{profile_name}'.")
    return 0


def _stop_demo_consumers(action: dict[str, Any]) -> int:
    """Stop simulator + consumer clients for one demo profile."""
    profile_name = str(action.get("profile_name") or "").strip()
    prefix = _demo_record_prefix(profile_name)
    code = _stop_recorded_processes_by_prefix(prefix=prefix, allow_empty=False)
    if int(code) == 0:
        print(f"Stop request completed for demo profile '{profile_name}'.")
    return int(code)


def _launch_background_process(action: dict[str, Any]) -> int:
    """Launch one long-running process in background and record its PID."""
    logger = _get_logger()
    label = str(action.get("label", "Process"))
    argv = [str(item) for item in action.get("argv", [])]
    cwd = Path(str(action.get("cwd") or _repo_root())).resolve()
    env = {
        str(key): str(value)
        for key, value in dict(action.get("env", {})).items()
    }
    if bool(action.get("clear_supervisor_signal", False)):
        _clear_stale_supervisor_signal(cwd=cwd)
    for raw_path in action.get("ensure_dirs", []):
        directory = Path(str(raw_path or "")).expanduser()
        if str(directory):
            directory.mkdir(parents=True, exist_ok=True)
    log_name = str(action.get(ACTION_KEY_LOG_NAME) or _slugify(label))
    log_file = _prepare_launch_log(
        label=label,
        command_text=str(action.get("command_text") or ""),
        cwd=cwd,
        log_name=log_name,
    )

    log_handle = log_file.open("a", encoding="utf-8")
    popen_kwargs: dict[str, Any] = {
        "cwd": str(cwd),
        "env": env,
        "stdin": subprocess.DEVNULL,
        "stdout": log_handle,
        "stderr": subprocess.STDOUT,
    }
    if _is_windows():
        creationflags = 0
        creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        creationflags |= getattr(subprocess, "DETACHED_PROCESS", 0)
        creationflags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)
        if creationflags:
            popen_kwargs["creationflags"] = creationflags
    else:
        popen_kwargs["start_new_session"] = True

    try:
        process = subprocess.Popen(argv, **popen_kwargs)  # pylint: disable=consider-using-with
    except Exception as exc:
        log_handle.close()
        _append_log_line(log_file, f"[{_utc_timestamp()}] launch_failed={exc}")
        logger.exception(
            "background process launch failed label=%s cwd=%s argv=%s log_file=%s",
            label,
            cwd,
            argv,
            log_file,
            exc_info=exc,
        )
        raise
    finally:
        log_handle.close()

    logger.info(
        "background process spawned label=%s pid=%s cwd=%s log_file=%s",
        label,
        process.pid,
        cwd,
        log_file,
    )
    time.sleep(PROCESS_START_CHECK_DELAY_SECONDS)
    exit_code = process.poll()
    if exit_code is not None:
        _append_log_line(log_file, f"[{_utc_timestamp()}] exited_early={int(exit_code)}")
        failure_detail = _last_process_output_log_line(log_file)
        logger.warning(
            "background process exited before startup completed label=%s pid=%s exit_code=%s log_file=%s detail=%s",
            label,
            process.pid,
            int(exit_code),
            log_file,
            failure_detail,
        )
        detail_text = f" detail={failure_detail}" if failure_detail else ""
        print(
            f"{label} exited before it was considered started "
            f"(exit_code={int(exit_code)}){detail_text} log={log_file}",
            file=sys.stderr,
        )
        return int(exit_code) if int(exit_code) != 0 else 1

    readiness_url = str(action.get("readiness_url") or "").strip()
    readiness_tcp = str(action.get("readiness_tcp") or "").strip()
    ready, reason = _wait_for_background_start(
        process=process,
        log_file=log_file,
        readiness_url=readiness_url,
        readiness_tcp=readiness_tcp,
    )
    if ready is not True:
        _append_log_line(log_file, f"[{_utc_timestamp()}] startup_check_failed={reason}")
        _terminate_process(process.pid)
        logger.warning(
            "background process failed startup check label=%s pid=%s reason=%s log_file=%s",
            label,
            process.pid,
            reason,
            log_file,
        )
        print(f"{label} failed startup check: {reason} log={log_file}", file=sys.stderr)
        return 1

    _record_cli_process(
        name=str(action.get(ACTION_KEY_RECORD_NAME) or label),
        pid=process.pid,
        command_text=str(action.get("command_text") or ""),
        cwd=cwd,
        log_file=log_file,
        metadata={
            str(key): value
            for key, value in dict(action.get(ACTION_KEY_METADATA, {})).items()
        },
    )
    _append_log_line(log_file, f"[{_utc_timestamp()}] pid={process.pid}")
    logger.info(
        "background process recorded label=%s record_name=%s pid=%s readiness_url=%s log_file=%s",
        label,
        str(action.get(ACTION_KEY_RECORD_NAME) or label),
        process.pid,
        readiness_url,
        log_file,
    )
    print(f"Started {label} pid={process.pid} log={log_file}")
    launch_url = str(action.get("launch_url") or "").strip()
    if launch_url:
        print(f"Open: {launch_url}")
    _open_log_viewer_for_process_if_enabled(
        label=label,
        log_file=log_file,
        logger=logger,
    )
    return 0


def _record_simulator_batch(action: dict[str, Any]) -> int:
    """Run simulator launcher start and record all spawned instance PIDs."""
    logger = _get_logger()
    label = str(action.get("label") or LABEL_SIMULATOR)
    state_file = Path(str(action.get("state_file") or "")).resolve()
    running_names = _running_simulator_instance_names(state_file)
    if running_names:
        logger.info(
            "simulator batch start skipped because instances are already running "
            "label=%s state_file=%s instances=%s",
            label,
            state_file,
            running_names,
        )
        print(
            f"{label} already running: {', '.join(running_names)}. "
            "Stop simulator before starting it again.",
            file=sys.stderr,
        )
        return 1

    argv = [str(item) for item in action.get("argv", [])]
    cwd = Path(str(action.get("cwd") or _repo_root())).resolve()
    env = {
        str(key): str(value)
        for key, value in dict(action.get("env", {})).items()
    }
    log_file = _prepare_launch_log(
        label=label,
        command_text=str(action.get("command_text") or ""),
        cwd=cwd,
        log_name=_slugify(label),
    )
    with log_file.open("a", encoding="utf-8") as log_handle:
        completed = subprocess.run(
            argv,
            cwd=str(cwd),
            env=env,
            check=False,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            **_windows_no_console_kwargs(),
        )
    if int(completed.returncode) != 0:
        logger.warning(
            "simulator batch launcher exited non-zero argv=%s cwd=%s exit_code=%s log_file=%s",
            argv,
            cwd,
            int(completed.returncode),
            log_file,
        )
        failure_detail = _last_non_empty_log_line(log_file)
        if failure_detail:
            print(
                f"{label} failed to start: {failure_detail} log={log_file}",
                file=sys.stderr,
            )
        else:
            print(
                f"{label} failed to start: launcher exit code {int(completed.returncode)} "
                f"log={log_file}",
                file=sys.stderr,
            )
        _append_log_line(log_file, f"[{_utc_timestamp()}] exit_code={int(completed.returncode)}")
        return int(completed.returncode)
    _append_log_line(log_file, f"[{_utc_timestamp()}] exit_code={int(completed.returncode)}")

    if state_file.is_file() is not True:
        logger.warning(
            "simulator batch rejected because state file was not created state_file=%s",
            state_file,
        )
        print(f"Simulator state file not found after start: {state_file}")
        return 1
    try:
        payload = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        logger.exception(
            "failed to read simulator state file state_file=%s",
            state_file,
            exc_info=exc,
        )
        print(f"Failed to read simulator state file {state_file}: {exc}", file=sys.stderr)
        return 1
    instances = payload.get("instances", []) if isinstance(payload, dict) else []
    if not isinstance(instances, list):
        instances = []
    record_prefix = str(action.get("record_prefix") or "").strip()
    extra_metadata = dict(action.get("record_metadata", {}))
    recorded = 0
    for instance in instances:
        if not isinstance(instance, dict):
            continue
        pid = int(instance.get("pid", 0) or 0)
        name = str(instance.get("name", "simulator")).strip() or "simulator"
        if pid <= 0:
            continue
        if _is_process_running(pid) is not True:
            _append_log_line(log_file, f"[{_utc_timestamp()}] simulator_not_running={name}:{pid}")
            logger.warning(
                "simulator instance was not running when discovered name=%s pid=%s state_file=%s",
                name,
                pid,
                state_file,
            )
            continue
        record_name = f"{SIMULATOR_RECORD_PREFIX}:{name}"
        if record_prefix:
            record_name = f"{record_prefix}:{SIMULATOR_RECORD_PREFIX}:{name}"
        metadata = {"state_file": str(state_file)}
        for key, value in extra_metadata.items():
            metadata[str(key)] = value
        _record_cli_process(
            name=record_name,
            pid=pid,
            command_text=str(action.get("command_text") or ""),
            cwd=Path(str(instance.get("working_dir") or cwd)).resolve(),
            log_file=log_file,
            metadata=metadata,
        )
        recorded += 1
    logger.info(
        "simulator batch recorded instances recorded=%s state_file=%s log_file=%s",
        recorded,
        state_file,
        log_file,
    )
    print(f"Started Simulator batch with {recorded} recorded process(es)")
    _open_log_viewer_for_process_if_enabled(
        label=str(action.get("label") or LABEL_SIMULATOR),
        log_file=log_file,
        logger=logger,
    )
    return 0


def _stop_recorded_processes(record_names: list[str]) -> int:
    """Stop all recorded managed processes that match provided names."""
    logger = _get_logger()
    payload = _prune_cli_process_state()
    targets = {str(name) for name in record_names}
    matches = [
        record
        for record in payload.get("processes", [])
        if str(record.get("name")) in targets
    ]
    if not matches:
        logger.info("no recorded processes matched stop request targets=%s", sorted(targets))
        print("No recorded process IDs found for that selection.")
        return 0

    for record in matches:
        pid = int(record.get("pid", 0) or 0)
        name = str(record.get("name") or "process")
        if container_management.stop_recorded_container(
            record,
            logger=logger,
            windows_no_console_kwargs=_windows_no_console_kwargs,
        ):
            logger.info("stopped recorded process name=%s pid=%s", name, pid)
            print(f"Stopped {name} pid={pid}")
            continue
        if pid <= 0:
            continue
        try:
            if _is_windows():
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    **_windows_no_console_kwargs(),
                )
            else:
                os.kill(pid, 15)
        except OSError:
            pass
        logger.info("stopped recorded process name=%s pid=%s", name, pid)
        print(f"Stopped {name} pid={pid}")

    _remove_cli_process_records(targets)
    return 0


def _stop_all_recorded_processes() -> int:
    """Stop every currently recorded managed process."""
    payload = _prune_cli_process_state()
    names: list[str] = []
    for record in payload.get("processes", []):
        if not isinstance(record, dict):
            continue
        name = str(record.get("name") or "").strip()
        if not name:
            continue
        names.append(name)
    unique_names = sorted(set(names))
    if not unique_names:
        print("No recorded managed processes to stop.")
        return 0
    return _stop_recorded_processes(unique_names)


def _interactive_loop() -> int:  # noqa: PLR0912,PLR0915
    """Run a REPL that executes or generates on each submitted line."""
    logger = _get_logger()
    words = _top_level_commands()
    input_reader = _prompt_toolkit_input_reader(words)
    if input_reader is None:
        input_reader = _builtin_tty_input_reader(words)
    if input_reader is None:
        _setup_readline_completion(words)
        if _is_windows():
            print(
                "Autocomplete fallback is unavailable in this terminal. "
                "Install prompt_toolkit with: python -m pip install prompt_toolkit"
            )
    print("Prompt CLI ready. Prefix with 'script' to generate a script file.")
    print(
        "Example: script demo-start-clients "
        "python -m opamp_consumer.fluentbit.client"
    )
    print(f"Use '{COMMAND_LIST}' to see all available commands.")
    print("You can type `start server`, `stop config editor`, or `restart server` directly.")
    if _fluentbit_dev_tool_available():
        print(f"Use `{COMMAND_DEV_FLB_CONFIG}` for the Fluent Bit dev generator workflow.")
    if _mcp_dev_tool_available():
        print(f"Use `{COMMAND_DEV_MCP_CONFIG}` for the MCP client configuration workflow.")
    if _dev_pid_lookup_available():
        print(f"Use `{COMMAND_DEV_PID_LOOKUP}` to find running process IDs by regex.")
    if _dev_version_bump_available():
        print(f"Use `{COMMAND_DEV_VERSION_BUMP}` to bump configured component versions.")
    print(f"Use `{COMMAND_SETUP_VENV}` to create/update the repository virtual environment.")
    print("Use `enable-process-tail` to tail managed process logs in a new shell.")
    detected_flags = _detected_behavior_flags()
    if detected_flags:
        print("Detected behavior flags/settings:")
        for entry in detected_flags:
            print(f"  - {entry}")
    print("Type 'exit' or press Ctrl+D to quit.")
    logger.info("interactive CLI loop started")

    while True:
        try:
            if input_reader is not None:
                raw = input_reader(INTERACTIVE_PROMPT)
            else:
                raw = input(INTERACTIVE_PROMPT)
        except EOFError:
            logger.info("interactive CLI loop exited via EOF")
            print()
            return 0
        except KeyboardInterrupt:
            logger.info("interactive CLI input interrupted by user")
            print()
            continue

        if raw.strip().lower() in {COMMAND_EXIT, COMMAND_QUIT}:
            logger.info("interactive CLI loop exited via explicit command")
            return 0
        if raw.strip().lower() in {COMMAND_HELP, "-h", "--help"}:
            logger.info("interactive help requested")
            print(HELP_TEXT)
            continue
        guided = _split_guided_command(raw)
        if guided is not None:
            intent, selection = guided
            try:
                code = _execute_guided_action(
                    input_reader=input_reader,
                    intent=intent,
                    selection=selection,
                )
            except Exception as exc:  # pragma: no cover - defensive CLI guard
                logger.exception(
                    "guided action failed in interactive loop intent=%s selection=%s",
                    intent,
                    selection,
                    exc_info=exc,
                )
                print(f"Error: {exc}", file=sys.stderr)
                code = 1
            if code != 0:
                print(_interactive_failure_message(raw, code))
            continue

        try:
            code = _handle_command(raw, input_reader=input_reader)
        except Exception as exc:  # pragma: no cover - defensive CLI guard
            logger.exception("interactive command failed raw=%s", raw, exc_info=exc)
            print(f"Error: {exc}", file=sys.stderr)
            code = 1

        if code != 0:
            print(_interactive_failure_message(raw, code))


def main(argv: list[str] | None = None) -> int:
    """Program entry point."""
    logger = _get_logger()
    args = list(sys.argv[1:] if argv is None else argv)
    logger.info("CLI main started argv=%s", args)
    if not args:
        exit_code = _interactive_loop()
        logger.info("CLI main completed interactive exit_code=%s", exit_code)
        return exit_code
    if args[0] in {"-h", "--help", COMMAND_HELP}:
        logger.info("CLI help requested argv=%s", args)
        print(HELP_TEXT)
        return 0

    raw_command = _command_text_from_args(args)
    try:
        guided = _split_guided_command(raw_command)
        if guided is not None:
            intent, selection = guided
            exit_code = _execute_guided_action(
                input_reader=None,
                intent=intent,
                selection=selection,
            )
            logger.info(
                "CLI main completed guided command intent=%s selection=%s exit_code=%s",
                intent,
                selection,
                exit_code,
            )
            return exit_code
        exit_code = _handle_command(raw_command)
        logger.info("CLI main completed command raw=%s exit_code=%s", raw_command, exit_code)
        return exit_code
    except ValueError as exc:
        logger.warning("CLI rejected command raw=%s error=%s", raw_command, exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - defensive CLI guard
        logger.exception("CLI main failed raw=%s", raw_command, exc_info=exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
