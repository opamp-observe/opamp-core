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
