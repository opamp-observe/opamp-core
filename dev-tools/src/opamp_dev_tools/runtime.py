# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Shared runtime helpers for the OpAMP developer CLI."""

from __future__ import annotations

import importlib.util
import json
import os
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]


DEFAULT_ISSUES_EXIT_CODE = 1
DEFAULT_ERROR_EXIT_CODE = 2


class CommandRuntimeError(RuntimeError):
    """Raised when the CLI hits an execution-time failure."""


@dataclass
class LogRecord:
    """One structured issue or error record.

    Attributes
    ----------
    category:
        Classification used to group similar issues or runtime failures.
    message:
        Human-readable description of the issue or error.
    path:
        Optional file or directory path associated with the record.
    command:
        Command line that triggered the record, when applicable.
    details:
        Structured payload with extra debugging context for the record.
    timestamp_utc:
        UTC timestamp captured when the record was created.

    """

    category: str
    message: str
    path: str = ""
    command: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    timestamp_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )


class CommandRuntime:
    """Holds shared paths, logging, and subprocess helpers for one CLI run.

    Attributes
    ----------
    repo_root:
        Absolute repository root used for command execution defaults.
    tool_root:
        Absolute dev-tools root used to place runtime artefacts and logs.
    command_slug:
        Filesystem-safe command identifier used in log filenames.
    log_dir:
        Directory where JSON issue and error logs are written.
    issues_log_path:
        JSON log path for command issues found during execution.
    errors_log_path:
        JSON log path for runtime or subprocess failures.
    issue_records:
        In-memory issue records captured during the current run.
    error_records:
        In-memory error records captured during the current run.

    """

    def __init__(self, *, repo_root: Path, tool_root: Path, command_slug: str) -> None:
        """Resolve runtime paths and prepare per-command log destinations.

        Parameters
        ----------
        repo_root:
            Repository root used as the default working directory.
        tool_root:
            Dev-tools root that owns runtime log output directories.
        command_slug:
            Parsed command identifier used when naming the JSON log files.

        """
        self.repo_root = repo_root.resolve()
        self.tool_root = tool_root.resolve()
        self.command_slug = _slugify(command_slug)
        self.log_dir = (self.tool_root / "runtime" / "logs").resolve()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.issues_log_path = self.log_dir / f"{timestamp}-{self.command_slug}-issues.json"
        self.errors_log_path = self.log_dir / f"{timestamp}-{self.command_slug}-errors.json"
        self.issue_records: list[LogRecord] = []
        self.error_records: list[LogRecord] = []

    def info(self, message: str) -> None:
        """Print one informational console line."""
        print(message)

    def record_issue(
        self,
        message: str,
        *,
        category: str = "issue",
        path: Path | str | None = None,
        command: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record a tool issue and echo it to the console."""
        record = LogRecord(
            category=category,
            message=message,
            path=str(path or ""),
            command=list(command or []),
            details=dict(details or {}),
        )
        self.issue_records.append(record)
        location = f" [{record.path}]" if record.path else ""
        print(f"[ISSUE]{location} {message}")

    def record_error(
        self,
        message: str,
        *,
        category: str = "cli-error",
        path: Path | str | None = None,
        command: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record one CLI/runtime failure and echo it to stderr."""
        record = LogRecord(
            category=category,
            message=message,
            path=str(path or ""),
            command=list(command or []),
            details=dict(details or {}),
        )
        self.error_records.append(record)
        location = f" [{record.path}]" if record.path else ""
        print(f"[ERROR]{location} {message}", file=sys.stderr)

    def run(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        check: bool = True,
        capture_output: bool = False,
        text: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Run one subprocess command, logging failures as CLI errors."""
        resolved_cwd = (cwd or self.repo_root).resolve()
        self.info(f"+ {_shell_join(command)}")
        try:
            completed = subprocess.run(
                command,
                cwd=str(resolved_cwd),
                env=env,
                check=check,
                capture_output=capture_output,
                text=text,
            )
        except FileNotFoundError as exc:
            self.record_error(
                f"required command not found: {command[0]}",
                command=command,
                details={"exception": repr(exc)},
            )
            raise CommandRuntimeError(str(exc)) from exc
        except subprocess.CalledProcessError as exc:
            self.record_error(
                f"command failed with exit code {exc.returncode}",
                command=command,
                details={
                    "returncode": exc.returncode,
                    "stdout": _coerce_text(exc.stdout),
                    "stderr": _coerce_text(exc.stderr),
                },
            )
            raise CommandRuntimeError(str(exc)) from exc
        return completed

    def ensure_python_module(
        self,
        *,
        python_exe: str,
        module_name: str,
        pip_package: str | None = None,
    ) -> None:
        """Ensure a Python module is importable, installing it when needed."""
        probe = subprocess.run(
            [python_exe, "-c", f"import {module_name}"],
            cwd=str(self.repo_root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            text=True,
        )
        if probe.returncode == 0:
            return
        package_name = pip_package or module_name
        self.info(f"Python package `{package_name}` not found; installing it now...")
        self.run([python_exe, "-m", "pip", "install", package_name], cwd=self.repo_root)

    def write_logs(self) -> None:
        """Persist issue and error logs for the current CLI run."""
        self.issues_log_path.write_text(
            json.dumps([asdict(record) for record in self.issue_records], indent=2) + "\n",
            encoding="utf-8",
        )
        self.errors_log_path.write_text(
            json.dumps([asdict(record) for record in self.error_records], indent=2) + "\n",
            encoding="utf-8",
        )

    def print_log_summary(self) -> None:
        """Print where the current run wrote its JSON logs."""
        print(f"Issue log: {self.issues_log_path}")
        print(f"Error log: {self.errors_log_path}")


def prompt_text(prompt: str, *, default: str = "") -> str:
    """Prompt the user for one text value with an optional default."""
    prompt_suffix = f" [{default}]" if default else ""
    response = input(f"{prompt}{prompt_suffix}: ").strip()
    return response or default


def prompt_int(prompt: str, *, default: int) -> int:
    """Prompt the user for one integer value."""
    while True:
        raw = prompt_text(prompt, default=str(default))
        try:
            return int(raw)
        except ValueError:
            print("Please enter a valid integer.")


def prompt_bool(prompt: str, *, default: bool) -> bool:
    """Prompt the user for one yes/no answer."""
    default_token = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{prompt} [{default_token}]: ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def read_project_metadata(pyproject_path: Path) -> dict[str, str]:
    """Read a component's project name/version from pyproject.toml."""
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = payload.get("project", {})
    if not isinstance(project, dict):
        return {}
    metadata: dict[str, str] = {}
    for key in ("name", "version", "description"):
        value = project.get(key)
        if isinstance(value, str):
            metadata[key] = value.strip()
    return metadata


def repo_root_from(start_path: Path) -> Path:
    """Resolve the repository root from a module or wrapper path."""
    current = start_path.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() or (candidate / "scripts").exists():
            return candidate
    return start_path.resolve()


def _shell_join(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _slugify(value: str) -> str:
    tokens = [token for token in "".join(ch if ch.isalnum() else "-" for ch in value).split("-") if token]
    return "-".join(tokens) or "run"


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)
