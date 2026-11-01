# Copyright 2026 opamp.info
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

"""Process discovery and control helpers used by observer lifecycle mode."""

from __future__ import annotations

import logging
import os
import re
import signal
from typing import Any

try:
    import psutil
except ImportError:  # pragma: no cover - exercised only when dependency missing
    psutil = None  # type: ignore[assignment]


class ProcessUtils:
    """Static helpers for regex-based process discovery and control."""

    @staticmethod
    def _psutil_available() -> bool:
        """Return whether psutil is importable in this runtime."""
        if psutil is not None:
            return True
        logging.getLogger(__name__).error(
            "psutil is not installed; observer process tracking is unavailable"
        )
        return False

    @staticmethod
    def _psutil_module():
        """Return imported psutil module when available."""
        if not ProcessUtils._psutil_available() or psutil is None:
            return None
        return psutil

    @staticmethod
    def find_pid_by_regex(pattern: str) -> int | None:
        """Return the first process pid whose command line/name matches regex."""
        psutil_module = ProcessUtils._psutil_module()
        if psutil_module is None:
            return None

        try:
            regex = re.compile(pattern)
        except re.error as err:
            logging.getLogger(__name__).error(
                "invalid process detection regex %r: %s",
                pattern,
                err,
            )
            return None

        for process in psutil_module.process_iter(attrs=["pid", "name", "cmdline"]):
            try:
                info: dict[str, Any] = process.info
                # Keep this match text aligned with the dev-only `opamp-cli`
                # PID lookup workflow so the CLI preview reflects observer-mode
                # process detection.
                cmdline = info.get("cmdline") or []
                if isinstance(cmdline, list):
                    text = " ".join(str(item) for item in cmdline)
                else:
                    text = str(cmdline)
                if not text.strip():
                    text = str(info.get("name") or "")
                if text and regex.search(text):
                    pid_value = info.get("pid")
                    if isinstance(pid_value, int):
                        return pid_value
            except (
                psutil_module.NoSuchProcess,
                psutil_module.AccessDenied,
                psutil_module.ZombieProcess,
            ):
                continue
        return None

    @staticmethod
    def is_process_running(pid: int | None) -> bool:
        """Return whether pid currently exists and is not a zombie process."""
        if pid is None:
            return False
        psutil_module = ProcessUtils._psutil_module()
        if psutil_module is None:
            return False
        if not psutil_module.pid_exists(pid):
            return False
        try:
            process = psutil_module.Process(pid)
            return process.is_running() and process.status() != psutil_module.STATUS_ZOMBIE
        except (
            psutil_module.NoSuchProcess,
            psutil_module.AccessDenied,
            psutil_module.ZombieProcess,
        ):
            return False

    @staticmethod
    def can_send_signal() -> bool:
        """Return whether current runtime supports os.kill based signaling."""
        return hasattr(os, "kill")

    @staticmethod
    def send_termination_signal(pid: int, sig: int = signal.SIGTERM) -> bool:
        """Attempt to send termination signal to pid."""
        if not ProcessUtils.can_send_signal():
            return False
        try:
            os.kill(pid, sig)
            return True
        except OSError as err:
            logging.getLogger(__name__).warning(
                "failed sending signal %s to pid=%s: %s",
                sig,
                pid,
                err,
            )
            return False

    @staticmethod
    def terminate_process(pid: int, timeout_seconds: float = 5.0) -> bool:
        """Request graceful process termination via psutil Process.terminate()."""
        psutil_module = ProcessUtils._psutil_module()
        if psutil_module is None:
            return False
        try:
            process = psutil_module.Process(pid)
            process.terminate()
            process.wait(timeout=timeout_seconds)
            return True
        except (psutil_module.NoSuchProcess, psutil_module.ZombieProcess):
            return True
        except (psutil_module.TimeoutExpired, psutil_module.AccessDenied) as err:
            logging.getLogger(__name__).warning(
                "terminate_process failed for pid=%s: %s",
                pid,
                err,
            )
            return False

    @staticmethod
    def kill_process(pid: int, timeout_seconds: float = 5.0) -> bool:
        """Force kill a process via psutil Process.kill()."""
        psutil_module = ProcessUtils._psutil_module()
        if psutil_module is None:
            return False
        try:
            process = psutil_module.Process(pid)
            process.kill()
            process.wait(timeout=timeout_seconds)
            return True
        except (psutil_module.NoSuchProcess, psutil_module.ZombieProcess):
            return True
        except (psutil_module.TimeoutExpired, psutil_module.AccessDenied) as err:
            logging.getLogger(__name__).warning(
                "kill_process failed for pid=%s: %s",
                pid,
                err,
            )
            return False
