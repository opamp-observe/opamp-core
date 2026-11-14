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

"""Unit coverage for locked Python dependency auditing."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace

from opamp_cli import dependency_audit


def test_audit_locked_project_exports_and_audits_complete_graph(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The helper should export all locked extras before invoking strict pip-audit."""

    project_path = tmp_path / "component"
    project_path.mkdir()
    commands: list[list[str]] = []
    monkeypatch.setattr(
        dependency_audit.shutil,
        "which",
        lambda _executable: "resolved-uv",
    )

    def record_command(command: list[str], *, check: bool) -> SimpleNamespace:
        """Capture subprocess arguments and return a successful process result."""

        assert check is False
        commands.append(command)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(dependency_audit.subprocess, "run", record_command)

    exit_code = dependency_audit.audit_locked_project(
        project_path,
        logger=logging.getLogger("test-dependency-audit"),
    )

    assert exit_code == 0
    assert commands[0][:6] == [
        "resolved-uv",
        "--quiet",
        "export",
        "--project",
        str(project_path.resolve()),
        "--locked",
    ]
    assert "--all-extras" in commands[0]
    assert "--no-emit-local" in commands[0]
    assert commands[1][:4] == [
        dependency_audit.sys.executable,
        "-m",
        "pip_audit",
        "--strict",
    ]


def test_audit_locked_project_reports_missing_uv(tmp_path: Path, monkeypatch) -> None:
    """The helper should fail clearly when uv is unavailable."""

    monkeypatch.setattr(dependency_audit.shutil, "which", lambda _executable: None)

    exit_code = dependency_audit.audit_locked_project(
        tmp_path,
        logger=logging.getLogger("test-dependency-audit"),
    )

    assert exit_code == 2


def test_export_failure_prevents_pip_audit(tmp_path: Path, monkeypatch) -> None:
    """A failed lock export should stop before pip-audit receives incomplete input."""

    commands: list[list[str]] = []
    monkeypatch.setattr(dependency_audit.shutil, "which", lambda _executable: "resolved-uv")

    def fail_export(command: list[str], *, check: bool) -> SimpleNamespace:
        """Return an export failure while retaining the attempted command."""

        assert check is False
        commands.append(command)
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(dependency_audit.subprocess, "run", fail_export)

    exit_code = dependency_audit.audit_locked_project(tmp_path)

    assert exit_code == 7
    assert len(commands) == 1


def test_command_start_failure_returns_command_error(tmp_path: Path, monkeypatch) -> None:
    """An operating-system startup failure should produce a stable command error code."""

    monkeypatch.setattr(dependency_audit.shutil, "which", lambda _executable: "resolved-uv")

    def fail_to_start(_command: list[str], *, check: bool) -> SimpleNamespace:
        """Simulate an executable that cannot be started by the operating system."""

        assert check is False
        raise OSError("unavailable executable")

    monkeypatch.setattr(dependency_audit.subprocess, "run", fail_to_start)

    exit_code = dependency_audit.audit_locked_project(tmp_path)

    assert exit_code == 2


def test_main_parses_project_and_returns_audit_status(tmp_path: Path, monkeypatch) -> None:
    """The module entry point should pass the selected project to the audit helper."""

    selected_projects: list[Path] = []

    def record_project(project_path: Path) -> int:
        """Capture the parsed project path and return a recognizable status."""

        selected_projects.append(project_path)
        return 9

    monkeypatch.setattr(dependency_audit, "audit_locked_project", record_project)

    exit_code = dependency_audit.main(["--project", str(tmp_path)])

    assert exit_code == 9
    assert selected_projects == [tmp_path]
