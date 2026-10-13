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

"""Launch/stop multiple OpAMP consumer instances from one configuration file.

Usage:
    python consumer-sim/src/consumer_sim_launcher.py start
    python consumer-sim/src/consumer_sim_launcher.py stop

Configuration file path defaults to:
`consumer-sim/config/consumer_instances.json`

Set `CONSUMER_SIM_CONFIG` to override configuration file path.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import shlex
import signal
import subprocess
import sys
import time
from typing import Any

from component_version import component_version_text
from opamp_consumer_sim.resources import (
    CONFIG_FILENAME,
    SCHEMA_FILENAME,
    ensure_user_default_config,
    read_packaged_text,
    source_component_root,
    source_repo_root,
    source_resource_path,
    user_state_root,
)

try:
    from jsonschema import Draft202012Validator as JSON_SCHEMA_VALIDATOR
    from jsonschema.exceptions import SchemaError
except ModuleNotFoundError:  # pragma: no cover - dependency availability varies by env.
    JSON_SCHEMA_VALIDATOR = None  # type: ignore[assignment]

    class SchemaError(Exception):
        """Fallback schema error when jsonschema dependency is unavailable."""

ACTION_START = "start"
ACTION_STOP = "stop"
VALID_ACTIONS = (ACTION_START, ACTION_STOP)

KEY_INSTANCES = "instances"
KEY_NAME = "name"
KEY_ENTRYPOINT = "entrypoint"
KEY_COMMAND = "command"
KEY_CONFIG_PATH = "config_path"
KEY_AGENT_CONFIG_PATH = "agent_config_path"
KEY_OVERRIDES = "overrides"
KEY_ENV = "env"
KEY_WORKING_DIR = "working_dir"
KEY_STATE_FILE = "state_file"
KEY_LAUNCHED_AT = "launched_at"
KEY_PID = "pid"
KEY_PROCESS_GROUP_ID = "process_group_id"
KEY_STATUS = "status"

ENTRYPOINT_SIMULATOR = "simulator"
STATUS_RUNNING = "running"
STATUS_SHUTDOWN = "shutdown"
STATUS_SHUTTING_DOWN = "shuttingdown"

ENV_SIM_PROCESS_RECORD_FILE = "OPAMP_SIM_PROCESS_RECORD_FILE"
ENV_SIM_PROCESS_RECORD_NAME = "OPAMP_SIM_PROCESS_RECORD_NAME"
ENV_APP_ENABLE_DEV_FEATURES = "APP_ENABLE_DEV_FEATURES"
ENABLED_ENV_VALUES = frozenset({"1", "on", "true", "yes"})

GRACEFUL_SHUTDOWN_WAIT_SECONDS = 90.0
TERMINATE_WAIT_SECONDS = 5.0
POLL_INTERVAL_SECONDS = 0.25
SEMAPHORE_FILENAME = "OpAMPSupervisor.signal"


def _is_windows() -> bool:
    """Return True when the launcher runs on Windows."""
    return os.name == "nt"
SIGKILL_SIGNAL = getattr(signal, "SIGKILL", signal.SIGTERM)


def _default_config_path() -> pathlib.Path:
    """Return default launcher configuration path."""
    config_path = source_resource_path(CONFIG_FILENAME)
    if config_path is not None:
        return config_path
    return ensure_user_default_config()


def _resolve_launcher_config_path() -> pathlib.Path:
    """Return launcher config path from env override or default."""
    override = str(os.getenv("CONSUMER_SIM_CONFIG", "") or "").strip()
    if override:
        return pathlib.Path(override).expanduser().resolve()
    return _default_config_path()


def _require_dev_features() -> None:
    """Block simulator startup unless the explicit development feature flag is enabled."""
    configured_value = str(os.getenv(ENV_APP_ENABLE_DEV_FEATURES, "") or "").strip().lower()
    if configured_value not in ENABLED_ENV_VALUES:
        raise RuntimeError(
            "consumer-sim startup requires APP_ENABLE_DEV_FEATURES=true; "
            "no simulator processes were launched"
        )


def _json_path(path_parts: list[Any]) -> str:
    """Convert jsonschema path parts to dotted/jsonpath-like notation."""
    location = "$"
    for part in path_parts:
        if isinstance(part, int):
            location += f"[{part}]"
        else:
            location += f".{part}"
    return location


def _resolve_path(raw: str | None, *, base_dir: pathlib.Path) -> pathlib.Path | None:
    """Resolve optional file path; relative paths are based on `base_dir`."""
    if raw is None:
        return None
    normalized = str(raw).strip()
    if not normalized:
        return None
    candidate = pathlib.Path(normalized).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (base_dir / candidate).resolve()


def _load_launcher_payload(config_path: pathlib.Path) -> dict[str, Any]:
    """Load launcher JSON payload from disk."""
    if not config_path.is_file():
        raise FileNotFoundError(
            f"consumer launcher config file not found: {config_path}"
        )
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("launcher config root must be a JSON object")
    return payload


def _validate_payload_against_schema(
    payload: dict[str, Any],
    *,
    config_path: pathlib.Path,
) -> None:
    """Validate launcher payload against JSON schema and fail with actionable detail."""
    if JSON_SCHEMA_VALIDATOR is None:
        raise RuntimeError(
            "FATAL: launcher schema validation dependency is missing. "
            "Install Python package 'jsonschema' before running consumer-sim."
        )

    schema_path = pathlib.Path(f"<package:{SCHEMA_FILENAME}>")
    try:
        source_schema_path = source_resource_path(SCHEMA_FILENAME)
        if source_schema_path is not None:
            schema_path = source_schema_path
            schema_text = schema_path.read_text(encoding="utf-8")
        else:
            schema_path = pathlib.Path(f"<package:{SCHEMA_FILENAME}>")
            schema_text = read_packaged_text(SCHEMA_FILENAME)
        schema_payload = json.loads(schema_text)
    except (OSError, ValueError, TypeError) as exc:
        raise RuntimeError(
            "FATAL: launcher schema file is unreadable or invalid JSON. "
            f"schema-file={schema_path} error={exc}"
        ) from exc
    if not isinstance(schema_payload, dict):
        raise RuntimeError(
            "FATAL: launcher schema root must be a JSON object. "
            f"schema-file={schema_path}"
        )

    try:
        JSON_SCHEMA_VALIDATOR.check_schema(schema_payload)
    except SchemaError as exc:
        raise RuntimeError(
            "FATAL: launcher JSON schema is invalid. "
            f"schema-file={schema_path} issue={exc.message}"
        ) from exc

    validator = JSON_SCHEMA_VALIDATOR(schema_payload)
    violations = sorted(
        validator.iter_errors(payload),
        key=lambda err: [str(part) for part in err.absolute_path],
    )
    if not violations:
        return

    lines: list[str] = []
    for index, violation in enumerate(violations[:5], start=1):
        lines.append(
            f"{index}. location={_json_path(list(violation.absolute_path))} "
            f"message={violation.message}"
        )
    remaining = len(violations) - len(lines)
    if remaining > 0:
        lines.append(f"... and {remaining} additional validation issue(s).")

    raise RuntimeError(
        "FATAL CONFIG SCHEMA VALIDATION FAILED.\n"
        f"config-file={config_path}\n"
        f"schema-file={schema_path}\n"
        "Fix the configuration file before starting consumer-sim.\n"
        "Validation issues:\n"
        + "\n".join(lines)
    )


def _state_file_path(
    config_path: pathlib.Path,
    payload: dict[str, Any] | None = None,
) -> pathlib.Path:
    """Resolve state-file path from payload or fallback default."""
    base_dir = config_path.parent
    if isinstance(payload, dict):
        resolved = _resolve_path(payload.get(KEY_STATE_FILE), base_dir=base_dir)
        if resolved is not None:
            return resolved
    component_root = source_component_root()
    if component_root is not None:
        return (component_root / "runtime" / "launcher_state.json").resolve()
    return (user_state_root() / "runtime" / "launcher_state.json").resolve()


def _build_entrypoint_command(entrypoint: str) -> list[str]:
    """Return python module command for supported simulator entrypoints."""
    lowered = entrypoint.strip().lower()
    if lowered == ENTRYPOINT_SIMULATOR:
        return [sys.executable, "-m", "opamp_consumer.simulator.client"]
    raise ValueError(
        f"unsupported entrypoint '{entrypoint}'; consumer-sim launcher supports "
        f"'{ENTRYPOINT_SIMULATOR}' only"
    )


def _normalize_command(raw_command: str | list[Any]) -> list[str]:
    """Convert configured command into argv list."""
    if isinstance(raw_command, list):
        command = [str(item).strip() for item in raw_command if str(item).strip()]
        if not command:
            raise ValueError("instance.command list must contain at least one token")
        return command
    if isinstance(raw_command, str):
        command = [token for token in shlex.split(raw_command) if token.strip()]
        if not command:
            raise ValueError("instance.command string must contain at least one token")
        return command
    raise ValueError("instance.command must be a string or list of strings")


def _validate_simulator_command(*, command: list[str], instance_name: str) -> None:
    """Ensure custom command targets the simulator client only."""
    command_text = " ".join(command).strip().lower()
    if any(
        token in command_text
        for token in (
            "opamp_consumer.simulator.client",
            "opamp-consumer-simulator",
            "simulator/client.py",
        )
    ):
        return
    raise ValueError(
        f"instance '{instance_name}' command must launch the simulator client"
    )


def _normalize_flag_name(raw_key: str) -> str:
    """Normalize override key into CLI flag token."""
    key = str(raw_key).strip()
    if not key:
        raise ValueError("override key cannot be empty")
    if key.startswith("-"):
        return key
    return f"--{key.replace('_', '-')}"


def _append_flag_value(command: list[str], flag: str, value: Any) -> None:
    """Append one override value to command list."""
    if isinstance(value, bool):
        if value:
            command.append(flag)
        else:
            command.extend([flag, "false"])
        return
    if isinstance(value, list):
        command.append(flag)
        command.extend(str(item) for item in value)
        return
    command.extend([flag, str(value)])


def _build_instance_command(
    instance: dict[str, Any],
    *,
    base_dir: pathlib.Path,
) -> tuple[str, list[str], pathlib.Path]:
    """Build full command line for one instance and return its name + cwd."""
    name = str(instance.get(KEY_NAME, "") or "").strip()
    if not name:
        raise ValueError("instance.name is required")

    if KEY_COMMAND in instance:
        command = _normalize_command(instance.get(KEY_COMMAND))
        _validate_simulator_command(command=command, instance_name=name)
    else:
        entrypoint = str(instance.get(KEY_ENTRYPOINT, ENTRYPOINT_SIMULATOR))
        command = _build_entrypoint_command(entrypoint)

    config_path = _resolve_path(instance.get(KEY_CONFIG_PATH), base_dir=base_dir)
    if config_path is None:
        raise ValueError(f"instance '{name}' is missing required '{KEY_CONFIG_PATH}'")
    command.extend(["--config-path", str(config_path)])

    agent_config_path = _resolve_path(instance.get(KEY_AGENT_CONFIG_PATH), base_dir=base_dir)
    if agent_config_path is not None:
        command.extend(["--agent-config-path", str(agent_config_path)])

    overrides = instance.get(KEY_OVERRIDES, {})
    if not isinstance(overrides, dict):
        raise ValueError(f"instance '{name}' field '{KEY_OVERRIDES}' must be an object")
    for raw_key, raw_value in overrides.items():
        flag = _normalize_flag_name(str(raw_key))
        _append_flag_value(command, flag, raw_value)

    working_dir = _resolve_path(instance.get(KEY_WORKING_DIR), base_dir=base_dir)
    if working_dir is None:
        working_dir = source_repo_root() or pathlib.Path.cwd().resolve()

    return name, command, working_dir


def _build_process_environment(
    instance: dict[str, Any],
    *,
    repo_root: pathlib.Path | None,
    process_record_file: pathlib.Path,
    instance_name: str,
) -> dict[str, str]:
    """Build environment for launched consumer process."""
    env = os.environ.copy()

    if repo_root is not None:
        pythonpath_entries = [
            str(repo_root / "consumer" / "src"),
            str(repo_root),
        ]
        existing_pythonpath = str(env.get("PYTHONPATH", "") or "").strip()
        if existing_pythonpath:
            pythonpath_entries.append(existing_pythonpath)
        env["PYTHONPATH"] = os.pathsep.join(
            entry for entry in pythonpath_entries if entry.strip()
        )

    raw_env = instance.get(KEY_ENV, {})
    if not isinstance(raw_env, dict):
        raise ValueError(
            f"instance '{instance.get(KEY_NAME, '<unknown>')}' field '{KEY_ENV}' must be an object"
        )
    for key, value in raw_env.items():
        env[str(key)] = str(value)
    env[ENV_SIM_PROCESS_RECORD_FILE] = str(process_record_file)
    env[ENV_SIM_PROCESS_RECORD_NAME] = str(instance_name)
    return env


def _clear_stale_shutdown_semaphore(*, working_dir: pathlib.Path) -> None:
    """Remove stale supervisor semaphore so new starts are not self-terminated."""
    semaphore_file = (working_dir / SEMAPHORE_FILENAME).resolve()
    if not semaphore_file.exists():
        return
    try:
        semaphore_file.unlink()
    except OSError as exc:
        raise RuntimeError(
            f"failed to remove stale shutdown semaphore {semaphore_file}: {exc}"
        ) from exc
    print(
        "[consumer-sim] removed stale shutdown semaphore "
        f"file={semaphore_file}"
    )


def _is_process_running(pid: int) -> bool:
    """Return True when process ID appears alive."""
    if pid <= 0:
        return False
    if _is_windows():
        return _is_process_running_windows(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _is_process_running_windows(pid: int) -> bool:
    """Return True when `tasklist` still reports one Windows PID."""
    try:
        completed = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False

    if completed.returncode != 0:
        return False

    output = str(completed.stdout or "").strip()
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


def _wait_for_exit(pid: int, timeout_seconds: float) -> bool:
    """Wait until process exits; return True if exited before timeout."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not _is_process_running(pid):
            return True
        time.sleep(POLL_INTERVAL_SECONDS)
    return not _is_process_running(pid)


def _taskkill(pid: int, *, force: bool) -> None:
    """Run taskkill for one PID on Windows."""
    cmd = ["taskkill", "/PID", str(pid), "/T"]
    if force:
        cmd.append("/F")
    subprocess.run(
        cmd,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _send_forceful_stop(pid: int, process_group_id: int | None) -> None:
    """Escalate to terminate/kill signals when graceful stop fails."""
    killpg: Any = getattr(os, "killpg", None)
    if os.name == "nt":
        _taskkill(pid, force=True)
        return
    if process_group_id is not None and process_group_id > 0 and killpg is not None:
        killpg(process_group_id, signal.SIGTERM)  # pylint: disable=not-callable
        if _wait_for_exit(pid, TERMINATE_WAIT_SECONDS):
            return
        killpg(process_group_id, SIGKILL_SIGNAL)  # pylint: disable=not-callable
        return
    os.kill(pid, signal.SIGTERM)
    if _wait_for_exit(pid, TERMINATE_WAIT_SECONDS):
        return
    os.kill(pid, SIGKILL_SIGNAL)


def _read_state_file(state_file: pathlib.Path) -> list[dict[str, Any]]:
    """Read launcher state records."""
    if not state_file.is_file():
        return []
    try:
        payload = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        print(f"[consumer-sim] invalid state file {state_file}: {exc}")
        return []
    if not isinstance(payload, dict):
        return []
    instances = payload.get(KEY_INSTANCES, [])
    if not isinstance(instances, list):
        return []
    result: list[dict[str, Any]] = []
    for item in instances:
        if isinstance(item, dict):
            result.append(item)
    return result


def _read_instance_status(
    *,
    state_file: pathlib.Path,
    instance_name: str,
    pid: int,
) -> str | None:
    """Return the current recorded status for a named instance."""
    for instance in _read_state_file(state_file):
        if str(instance.get(KEY_NAME, "")).strip() != instance_name:
            continue
        if _coerce_int(instance.get(KEY_PID), default=0) != pid:
            continue
        status = str(instance.get(KEY_STATUS, "")).strip().lower()
        return status or None
    return None


def _write_state_file(
    state_file: pathlib.Path,
    instances: list[dict[str, Any]],
) -> None:
    """Persist launcher state to disk."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        KEY_LAUNCHED_AT: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        KEY_INSTANCES: instances,
    }
    state_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _start_instances(config_path: pathlib.Path) -> None:  # pylint: disable=too-many-locals
    """Start all configured consumer instances and record their process IDs."""
    _require_dev_features()
    payload = _load_launcher_payload(config_path)
    _validate_payload_against_schema(payload, config_path=config_path)
    state_file = _state_file_path(config_path, payload)
    existing_state = _read_state_file(state_file)
    running = [
        item
        for item in existing_state
        if _is_process_running(_coerce_int(item.get(KEY_PID), default=0))
    ]
    if running:
        names = ", ".join(str(item.get(KEY_NAME, "<unknown>")) for item in running)
        raise RuntimeError(
            f"cannot start: existing launched consumer instances are still running: {names}"
        )

    raw_instances = payload.get(KEY_INSTANCES, [])
    if not isinstance(raw_instances, list) or not raw_instances:
        raise ValueError("launcher config must contain a non-empty 'instances' list")

    launched: list[dict[str, Any]] = []
    base_dir = config_path.parent
    repo_root = source_repo_root()

    try:
        for index, raw_instance in enumerate(raw_instances, start=1):
            if not isinstance(raw_instance, dict):
                raise ValueError(f"instances[{index}] must be an object")
            name, command, working_dir = _build_instance_command(raw_instance, base_dir=base_dir)
            _clear_stale_shutdown_semaphore(working_dir=working_dir)
            env = _build_process_environment(
                raw_instance,
                repo_root=repo_root,
                process_record_file=state_file,
                instance_name=name,
            )

            popen_kwargs: dict[str, Any] = {
                "cwd": str(working_dir),
                "env": env,
            }
            if os.name == "nt":
                popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                popen_kwargs["start_new_session"] = True

            process = subprocess.Popen(  # pylint: disable=consider-using-with
                command,
                **popen_kwargs,
            )
            process_group_id = process.pid if os.name != "nt" else None
            print(
                "[consumer-sim] launched "
                f"name={name} pid={process.pid} cwd={working_dir} cmd={shlex.join(command)}"
            )
            launched.append(
                {
                    KEY_NAME: name,
                    KEY_PID: process.pid,
                    KEY_PROCESS_GROUP_ID: process_group_id,
                    KEY_COMMAND: command,
                    KEY_WORKING_DIR: str(working_dir),
                    KEY_CONFIG_PATH: str(
                        _resolve_path(
                            raw_instance.get(KEY_CONFIG_PATH),
                            base_dir=base_dir,
                        )
                    ),
                    KEY_LAUNCHED_AT: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    KEY_STATUS: STATUS_RUNNING,
                }
            )
    except (OSError, RuntimeError, ValueError, TypeError, subprocess.SubprocessError):
        for launched_instance in launched:
            _stop_single_instance(launched_instance, state_file=state_file)
        raise

    _write_state_file(state_file, launched)
    print(
        "[consumer-sim] start complete; "
        f"launched {len(launched)} instance(s). state-file={state_file}"
    )


def _coerce_int(value: Any, *, default: int = 0) -> int:
    """Safely parse integers from mixed values."""
    if isinstance(value, int):
        return int(value)
    if value is None:
        return default
    text = str(value).strip()
    if text.startswith("-"):
        return -_coerce_int(text[1:], default=abs(default))
    if text.isdigit():
        return int(text)
    return default


def _stop_single_instance(
    instance: dict[str, Any],
    *,
    state_file: pathlib.Path | None = None,
) -> bool:
    """Gracefully stop one launched instance, escalating if needed.

    Returns True when the instance is confirmed stopped (or already gone).
    Returns False when shutdown did not succeed.
    """
    name = str(instance.get(KEY_NAME, "<unknown>"))
    pid = _coerce_int(instance.get(KEY_PID), default=0)
    process_group_id_raw = instance.get(KEY_PROCESS_GROUP_ID)
    process_group_id = (
        _coerce_int(process_group_id_raw, default=0)
        if _coerce_int(process_group_id_raw, default=0) > 0
        else None
    )

    if pid <= 0 or not _is_process_running(pid):
        if pid <= 0:
            print(f"[consumer-sim] skip invalid pid for {name}: {pid}")
        else:
            print(f"[consumer-sim] already stopped name={name} pid={pid}")
        return True

    print(
        "[consumer-sim] waiting for simulator to honor shutdown status "
        f"name={name} pid={pid} timeout={GRACEFUL_SHUTDOWN_WAIT_SECONDS:.0f}s"
    )
    deadline = time.monotonic() + GRACEFUL_SHUTDOWN_WAIT_SECONDS
    last_status: str | None = None
    while time.monotonic() < deadline:
        if not _is_process_running(pid):
            print(
                f"====== [consumer-sim] process no longer detected name={name} "
                f"pid={pid} ======"
            )
            return True
        if state_file is not None:
            status = _read_instance_status(
                state_file=state_file,
                instance_name=name,
                pid=pid,
            )
            if status and status != last_status:
                last_status = status
                if status == STATUS_SHUTTING_DOWN:
                    print(
                        "----- [consumer-sim] simulator state changed to "
                        f"shuttingdown name={name} pid={pid} -----"
                    )
        time.sleep(POLL_INTERVAL_SECONDS)

    print(f"[consumer-sim] forcing stop name={name} pid={pid}")
    try:
        _send_forceful_stop(pid, process_group_id)
    except ProcessLookupError:
        print(f"[consumer-sim] process already exited name={name} pid={pid}")
        return True
    except OSError as exc:
        print(f"[consumer-sim] force stop failed for name={name} pid={pid}: {exc}")
        return False
    if _wait_for_exit(pid, TERMINATE_WAIT_SECONDS):
        print(
            f"====== [consumer-sim] process no longer detected name={name} "
            f"pid={pid} ======"
        )
        return True
    print(f"[consumer-sim] failed to stop name={name} pid={pid}")
    return False


def _stop_instances(config_path: pathlib.Path) -> None:  # pylint: disable=too-many-branches
    """Stop all instances recorded in state file."""
    payload: dict[str, Any] | None = None
    if config_path.is_file():
        try:
            loaded_payload = _load_launcher_payload(config_path)
            payload = loaded_payload if isinstance(loaded_payload, dict) else None
        except (OSError, ValueError, TypeError) as exc:
            print(
                f"[consumer-sim] failed to load launcher config {config_path}; "
                f"using default state-file location: {exc}"
            )
            payload = None
    state_file = _state_file_path(config_path, payload)
    instances = _read_state_file(state_file)
    if not instances:
        print(f"[consumer-sim] no launched instances found in state file: {state_file}")
        return

    for instance in instances:
        instance[KEY_STATUS] = STATUS_SHUTDOWN
    try:
        _write_state_file(state_file, instances)
    except (OSError, ValueError, TypeError) as exc:
        print(
            f"[consumer-sim] failed to persist shutdown requests to {state_file}: {exc}"
        )
        return
    print(
        "[consumer-sim] marked simulator instances with shutdown status "
        f"in state-file={state_file}"
    )

    remaining_instances = list(instances)
    for instance in list(remaining_instances):
        try:
            stopped = _stop_single_instance(instance, state_file=state_file)
        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            instance_name = str(instance.get(KEY_NAME, "<unknown>"))
            instance_pid = _coerce_int(instance.get(KEY_PID), default=0)
            print(
                "[consumer-sim] unexpected shutdown error "
                f"name={instance_name} pid={instance_pid}: {exc}"
            )
            stopped = False

        if not stopped:
            continue
        remaining_instances.remove(instance)
        if remaining_instances:
            try:
                _write_state_file(state_file, remaining_instances)
            except (OSError, ValueError, TypeError) as exc:
                print(
                    "[consumer-sim] failed to persist partial stop state "
                    f"to {state_file}: {exc}"
                )
                continue
            print(
                "[consumer-sim] removed stopped instance from state file; "
                f"remaining={len(remaining_instances)} state-file={state_file}"
            )
        else:
            try:
                state_file.unlink(missing_ok=True)
            except OSError as exc:  # pragma: no cover - best effort cleanup.
                print(f"[consumer-sim] failed to remove state file {state_file}: {exc}")
                return
            print(f"[consumer-sim] stop complete; removed state file: {state_file}")
            return

    try:
        _write_state_file(state_file, remaining_instances)
    except (OSError, ValueError, TypeError) as exc:
        print(
            f"[consumer-sim] failed to persist remaining state file {state_file}: {exc}"
        )
        return
    print(
        "[consumer-sim] stop completed with outstanding instances still running; "
        f"remaining={len(remaining_instances)} state-file={state_file}"
    )


def _build_parser() -> argparse.ArgumentParser:
    """Create action-only CLI parser."""
    version_text = component_version_text()
    parser = argparse.ArgumentParser(
        description=(
            "Start or stop batches of OpAMP consumer instances defined in "
            "consumer-sim/config/consumer_instances.json. "
            f"Version: {version_text}"
        )
    )
    parser.add_argument("action", choices=VALID_ACTIONS)
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version_text}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""
    args = _build_parser().parse_args(argv)
    config_path = _resolve_launcher_config_path()
    try:
        if args.action == ACTION_START:
            _start_instances(config_path)
        else:
            _stop_instances(config_path)
    except (
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"[consumer-sim] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt as exc:
        print("[consumer-sim] interrupted")
        raise SystemExit(130) from exc
