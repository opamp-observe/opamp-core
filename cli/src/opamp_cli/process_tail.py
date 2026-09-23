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

"""Process log tail launching for the OpAMP CLI."""

from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from .constants import (
        CLI_SETTING_ENABLE_PROCESS_TAIL,
        PROCESS_TAIL_INITIAL_LINES,
        TRUE_VALUES,
    )
except ImportError:
    from constants import (  # type: ignore[no-redef]
        CLI_SETTING_ENABLE_PROCESS_TAIL,
        PROCESS_TAIL_INITIAL_LINES,
        TRUE_VALUES,
    )


def powershell_single_quote(value: str | Path) -> str:
    """Return a PowerShell-safe single-quoted string literal."""
    return "'" + str(value).replace("'", "''") + "'"


def process_tail_enabled(*, load_settings: Callable[[], dict[str, Any]]) -> bool:
    """Return whether process tail shells should be opened for managed starts."""
    payload = load_settings()
    value = payload.get(CLI_SETTING_ENABLE_PROCESS_TAIL, False)
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in TRUE_VALUES


def set_process_tail_enabled(
    enabled: bool,
    *,
    load_settings: Callable[[], dict[str, Any]],
    save_settings: Callable[[dict[str, Any]], None],
    settings_path: Callable[[], Path],
    logger: Any,
) -> None:
    """Persist process tail preference and print the resulting state."""
    payload = load_settings()
    payload[CLI_SETTING_ENABLE_PROCESS_TAIL] = bool(enabled)
    save_settings(payload)
    logger.info("process tailing toggled enabled=%s", bool(enabled))
    print(f"Process tailing {'enabled' if enabled else 'disabled'}.")
    print(f"Settings file: {settings_path()}")


SMART_LOG_VIEWER_ENV_NAMES = (
    "SMART_LOG_VIEWER",
    "OPAMP_SMART_LOG_VIEWER",
    "smart-log-viewer",
)
SMART_LOG_VIEWER_DEFAULT_COMMAND = "smart-log-viewer"
SMART_LOG_VIEWER_CONFIG_FILENAME = "config.json"
SMART_LOG_VIEWER_FALSE_VALUES = {"", "0", "false", "no", "off"}
SMART_LOG_VIEWER_DEFAULT_PORT = 3847
SMART_LOG_VIEWER_PORT_ATTEMPTS = 5


def smart_log_viewer_env_value() -> str:
    """Return the configured Smart Log Viewer env value, if any."""
    for name in SMART_LOG_VIEWER_ENV_NAMES:
        value = str(os.environ.get(name) or "").strip()
        if value:
            return value
    return ""


def smart_log_viewer_enabled() -> bool:
    """Return whether Smart Log Viewer should replace per-process tail shells."""
    value = smart_log_viewer_env_value()
    return value.lower() not in SMART_LOG_VIEWER_FALSE_VALUES


def smart_log_viewer_executable() -> str:
    """Return the Smart Log Viewer executable selected by environment."""
    value = smart_log_viewer_env_value()
    if value.lower() in TRUE_VALUES:
        return SMART_LOG_VIEWER_DEFAULT_COMMAND
    return value or SMART_LOG_VIEWER_DEFAULT_COMMAND


def smart_log_viewer_base_port() -> int:
    """Return the first port Smart Log Viewer will try."""
    raw_value = str(os.environ.get("PORT") or "").strip()
    if not raw_value:
        return SMART_LOG_VIEWER_DEFAULT_PORT
    try:
        port = int(raw_value)
    except ValueError:
        return SMART_LOG_VIEWER_DEFAULT_PORT
    if 1 <= port <= 65535:
        return port
    return SMART_LOG_VIEWER_DEFAULT_PORT


def smart_log_viewer_url_message() -> str:
    """Return a user-facing URL hint for Smart Log Viewer."""
    port = smart_log_viewer_base_port()
    url = f"http://localhost:{port}"
    final_retry_port = min(port + SMART_LOG_VIEWER_PORT_ATTEMPTS - 1, 65535)
    if final_retry_port == port:
        return url
    return (
        f"{url} "
        f"(if that port is busy, try ports {port + 1}-{final_retry_port})"
    )


def _dedupe_path_entries(entries: list[str]) -> str:
    """Return PATH text with duplicate entries removed while preserving order."""
    seen: set[str] = set()
    deduped: list[str] = []
    for raw_entry in entries:
        entry = str(raw_entry or "").strip()
        if not entry:
            continue
        key = entry.rstrip("\\/").lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return os.pathsep.join(deduped)


def _windows_persisted_path_entries() -> list[str]:
    """Return machine/user PATH entries from the Windows environment registry."""
    if sys.platform != "win32":
        return []
    try:
        import winreg
    except ImportError:
        return []

    locations = (
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
        (winreg.HKEY_CURRENT_USER, "Environment"),
    )
    entries: list[str] = []
    for root, subkey in locations:
        try:
            with winreg.OpenKey(root, subkey) as key:
                value, _value_type = winreg.QueryValueEx(key, "Path")
        except OSError:
            continue
        entries.extend(str(value or "").split(os.pathsep))
    return entries


def smart_log_viewer_process_env() -> dict[str, str]:
    """Return the launch environment for Smart Log Viewer."""
    env = dict(os.environ)
    current_path = env.get("PATH") or env.get("Path") or ""
    path_entries = [*current_path.split(os.pathsep), *_windows_persisted_path_entries()]
    env["PATH"] = _dedupe_path_entries(path_entries)
    return env


def write_smart_log_viewer_config(
    *,
    config_dir: Path,
    sources: list[dict[str, str]],
) -> Path:
    """Write Smart Log Viewer config.json with normalized source entries."""
    config_dir.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    normalized_sources: list[dict[str, str]] = []
    for source in sources:
        raw_path = str(source.get("path") or "").strip()
        if not raw_path:
            continue
        path = str(Path(raw_path).expanduser().resolve())
        key = path.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized_sources.append(
            {
                "path": path,
                "tagName": str(source.get("tagName") or Path(path).stem).strip(),
                "color": str(source.get("color") or "#58a6ff").strip(),
            }
        )

    config_path = (config_dir / SMART_LOG_VIEWER_CONFIG_FILENAME).resolve()
    config_path.write_text(
        json.dumps({"sources": normalized_sources}, indent=2) + "\n",
        encoding="utf-8",
    )
    return config_path


def launch_smart_log_viewer(
    *,
    config_dir: Path,
    repo_root: Path,
    logger: Any,
) -> bool:
    """Launch Smart Log Viewer using the generated config directory."""
    executable = smart_log_viewer_executable()
    executable_path = shutil.which(executable) if not Path(executable).is_absolute() else executable
    if executable_path is None:
        logger.warning("smart-log-viewer executable not found executable=%s", executable)
        print(
            "Warning: smart-log-viewer is enabled but the executable was not found. "
            "Install with `npm install -g smart-log-viewer`.",
            file=sys.stderr,
        )
        return False
    argv = [str(executable_path), "--config", str(config_dir.resolve())]
    try:
        subprocess.Popen(  # pylint: disable=consider-using-with
            argv,
            cwd=str(repo_root.resolve()),
            env=smart_log_viewer_process_env(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=(sys.platform != "win32"),
        )
    except Exception as exc:  # pragma: no cover - defensive launch guard
        logger.exception("failed to launch smart-log-viewer argv=%s", argv, exc_info=exc)
        print(f"Warning: failed to launch smart-log-viewer: {exc}", file=sys.stderr)
        return False
    logger.info("launched smart-log-viewer argv=%s", argv)
    print(
        "Opened Smart Log Viewer at "
        f"{smart_log_viewer_url_message()} "
        f"with config: {config_dir.resolve()}"
    )
    return True


def launch_process_tail_shell(
    *,
    label: str,
    log_file: Path,
    repo_root: Path,
    is_windows: bool,
    shell_quote: Callable[[str], str],
) -> bool:
    """Open a new shell window tailing the provided log file."""
    resolved_log = log_file.resolve()
    if resolved_log.exists() is not True:
        return False

    if is_windows:
        command = (
            f"Write-Host 'Tailing {label}'; "
            f"Get-Content -Path {powershell_single_quote(resolved_log)} "
            f"-Wait -Tail {PROCESS_TAIL_INITIAL_LINES}"
        )
        subprocess.Popen(  # pylint: disable=consider-using-with
            ["powershell.exe", "-NoExit", "-Command", command],
            cwd=str(repo_root.resolve()),
            creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
        )
        return True

    bash_path = shutil.which("bash") or "/bin/bash"
    tail_command = (
        f"printf 'Tailing {label}\\n'; "
        f"tail -n {PROCESS_TAIL_INITIAL_LINES} -f {shell_quote(str(resolved_log))}"
    )
    terminal_candidates = [
        ["x-terminal-emulator", "-e", bash_path, "-lc", tail_command],
        ["gnome-terminal", "--", bash_path, "-lc", tail_command],
        ["konsole", "-e", bash_path, "-lc", tail_command],
        ["xfce4-terminal", "--command", f"{bash_path} -lc {shlex.quote(tail_command)}"],
        ["mate-terminal", "--", bash_path, "-lc", tail_command],
        ["lxterminal", "-e", f"{bash_path} -lc {shlex.quote(tail_command)}"],
        ["xterm", "-e", bash_path, "-lc", tail_command],
    ]
    for candidate in terminal_candidates:
        executable = shutil.which(candidate[0])
        if not executable:
            continue
        subprocess.Popen(  # pylint: disable=consider-using-with
            [executable, *candidate[1:]],
            cwd=str(repo_root.resolve()),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    return False


def open_process_tail_if_enabled(
    *,
    label: str,
    log_file: Path,
    enabled: bool,
    logger: Any,
    repo_root: Path,
    is_windows: bool,
    shell_quote: Callable[[str], str],
) -> None:
    """Open a tail shell for a managed process log when the feature is enabled."""
    if enabled is not True:
        logger.info("process tailing skipped because feature is disabled label=%s", label)
        return
    print(f"Process tailing enabled for {label}; log file: {log_file}")
    try:
        opened = launch_process_tail_shell(
            label=label,
            log_file=log_file,
            repo_root=repo_root,
            is_windows=is_windows,
            shell_quote=shell_quote,
        )
    except Exception as exc:  # pragma: no cover - defensive shell-launch guard
        logger.exception(
            "failed to open process tail shell label=%s log_file=%s",
            label,
            log_file,
            exc_info=exc,
        )
        print(f"Warning: failed to open process tail for {label}: {exc}", file=sys.stderr)
        return
    if opened:
        logger.info("opened process tail shell label=%s log_file=%s", label, log_file)
        print(f"Opened tail shell for {label}: {log_file}")
        return
    logger.warning("no terminal launcher available for process tail label=%s", label)
    print(
        f"Warning: no terminal launcher was available for process tailing {label}",
        file=sys.stderr,
    )
