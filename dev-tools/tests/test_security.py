# Copyright 2026 mp3monster.org
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

"""Tests for repository security-check orchestration."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from opamp_dev_tools import security
from opamp_dev_tools.components import BuildComponent


class _SecurityRuntime:
    """Capture repository security commands without running external tools.

    Attributes
    ----------
    repo_root:
        Temporary repository root used by the security workflow.
    commands:
        External commands captured during orchestration.
    messages:
        Informational messages emitted by the workflow.

    """

    def __init__(self, repo_root: Path) -> None:
        """Initialize captures for one temporary repository.

        Parameters
        ----------
        repo_root:
            Temporary root used for command working directories.

        """
        self.repo_root = repo_root
        self.commands: list[list[str]] = []
        self.messages: list[str] = []

    def run(self, command: list[str], **_options: object) -> subprocess.CompletedProcess[str]:
        """Capture one external command and report successful completion.

        Parameters
        ----------
        command:
            Complete command line requested by the security workflow.
        _options:
            Working directory and environment options ignored by the fake.

        """
        self.commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    def info(self, message: str) -> None:
        """Capture one informational message.

        Parameters
        ----------
        message:
            Console message emitted by the security workflow.

        """
        self.messages.append(message)


def test_repo_security_pytest_uses_importlib_mode(monkeypatch, tmp_path: Path) -> None:
    """The full suite should isolate duplicate test module filenames."""
    monkeypatch.setattr(security, "_ensure_cli_tool", lambda *_args, **_options: None)
    monkeypatch.setattr(
        security,
        "ensure_pytest_dependencies",
        lambda *_args, **_options: None,
    )
    monkeypatch.setattr(
        security,
        "compact_provider_ui_assets",
        lambda *_args, **_options: False,
    )
    monkeypatch.setattr(security, "_scan_for_secrets", lambda *_args, **_options: None)
    runtime = _SecurityRuntime(tmp_path)

    issues_found = security.run_repo_security_checks(runtime, python_exe="python")

    assert issues_found is False
    pytest_report_path = (
        tmp_path
        / "dev-tools"
        / "runtime"
        / "security-reports"
        / "repository"
        / "pytest.xml"
    )
    assert runtime.commands[0] == [
        "python",
        "-m",
        "pytest",
        "-s",
        security.PYTEST_IMPORT_MODE_ARGUMENT,
        f"--junitxml={pytest_report_path}",
    ]
    assert runtime.commands[1][0:3] == ["ruff", "check", "--select"]
    ruff_output_index = runtime.commands[1].index("--output-file")
    assert runtime.commands[1][ruff_output_index + 1] == str(
        tmp_path
        / "dev-tools"
        / "runtime"
        / "security-reports"
        / "repository"
        / "ruff.sarif"
    )
    assert runtime.commands[2][0:2] == [security.SEMGREP_TOOL_NAME, "scan"]
    assert runtime.commands[3][0:2] == [security.BANDIT_TOOL_NAME, "-r"]


def test_detect_secrets_retains_native_json_report(monkeypatch, tmp_path: Path) -> None:
    """Secret scans should preserve their native JSON for later review."""
    runtime = _SecurityRuntime(tmp_path)
    scan_payload = '{"results": {}}'

    def run_with_scan_output(
        command: list[str],
        **_options: object,
    ) -> subprocess.CompletedProcess[str]:
        """Return a deterministic detect-secrets payload for the test command.

        Parameters
        ----------
        command:
            Complete command captured from the secret-scan helper.
        _options:
            Runtime options accepted for compatibility with the production API.

        """
        runtime.commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout=scan_payload, stderr="")

    monkeypatch.setattr(runtime, "run", run_with_scan_output)

    security._scan_for_secrets(  # pylint: disable=protected-access
        runtime,
        repo_root=tmp_path,
        env={},
        path_prefix="provider",
        report_scope="provider",
    )

    report_path = (
        tmp_path
        / "dev-tools"
        / "runtime"
        / "security-reports"
        / "provider"
        / security.DETECT_SECRETS_REPORT_FILE_NAME
    )
    assert report_path.read_text(encoding="utf-8") == scan_payload + "\n"
    assert runtime.commands[0][-1] == "provider"


def test_requirement_audit_writes_scoped_json_report(tmp_path: Path) -> None:
    """Dependency audits should target a stable component report path."""
    runtime = _SecurityRuntime(tmp_path)
    requirement_path = tmp_path / "provider" / "requirements.txt"
    requirement_path.parent.mkdir(parents=True)
    requirement_path.write_text("quart>=0.19\n", encoding="utf-8")

    security._audit_requirement_files(  # pylint: disable=protected-access
        runtime,
        requirement_paths=[requirement_path],
        env={},
        report_scope="provider",
    )

    assert runtime.commands == [
        [
            "pip-audit",
            "--format",
            "json",
            "--output",
            str(
                tmp_path
                / "dev-tools"
                / "runtime"
                / "security-reports"
                / "provider"
                / security.PIP_AUDIT_REPORT_FILE_NAME
            ),
            "-r",
            str(Path("provider") / "requirements.txt"),
        ]
    ]


def test_component_security_retains_component_scoped_reports(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Focused security runs should keep every report under the component scope."""
    component_path = tmp_path / "provider"
    component_path.mkdir()
    (component_path / "requirements.txt").write_text("quart>=0.19\n", encoding="utf-8")
    component = BuildComponent(
        key="provider",
        path=component_path,
        project_name="opamp-server",
        version="0.6.0",
    )
    runtime = _SecurityRuntime(tmp_path)
    monkeypatch.setattr(security, "_ensure_cli_tool", lambda *_args, **_options: None)
    monkeypatch.setattr(
        security,
        "ensure_pytest_dependencies",
        lambda *_args, **_options: None,
    )
    monkeypatch.setattr(security, "_scan_for_secrets", lambda *_args, **_options: None)

    issues_found = security.run_component_security_checks(
        runtime,
        component=component,
        python_exe="python",
    )

    report_directory = (
        tmp_path / "dev-tools" / "runtime" / "security-reports" / "provider"
    )
    assert issues_found is False
    assert runtime.commands[0][-1] == f"--junitxml={report_directory / 'pytest.xml'}"
    assert str(report_directory / "ruff.sarif") in runtime.commands[1]
    assert str(report_directory / "pip-audit.json") in runtime.commands[2]
    assert str(report_directory / "semgrep.sarif") in runtime.commands[3]
    assert str(report_directory / "bandit.json") in runtime.commands[4]


def test_repo_security_continues_after_a_failed_step(monkeypatch, tmp_path: Path) -> None:
    """A failed test step should not prevent later security evidence from being produced."""
    runtime = _SecurityRuntime(tmp_path)
    original_run = runtime.run

    def fail_pytest_only(
        command: list[str],
        **options: object,
    ) -> subprocess.CompletedProcess[str]:
        """Fail pytest while allowing every later fake tool command to succeed.

        Parameters
        ----------
        command:
            Complete command requested by the security workflow.
        options:
            Working directory and environment forwarded to the runtime double.

        """
        if command[0:3] == ["python", "-m", "pytest"]:
            runtime.commands.append(command)
            raise RuntimeError("pytest failed")
        return original_run(command, **options)

    monkeypatch.setattr(runtime, "run", fail_pytest_only)
    monkeypatch.setattr(security, "_ensure_cli_tool", lambda *_args, **_options: None)
    monkeypatch.setattr(
        security,
        "ensure_pytest_dependencies",
        lambda *_args, **_options: None,
    )
    monkeypatch.setattr(
        security,
        "compact_provider_ui_assets",
        lambda *_args, **_options: False,
    )
    monkeypatch.setattr(security, "_scan_for_secrets", lambda *_args, **_options: None)

    with pytest.raises(RuntimeError, match="pytest failed"):
        security.run_repo_security_checks(runtime, python_exe="python")

    assert any(command[0:2] == [security.SEMGREP_TOOL_NAME, "scan"] for command in runtime.commands)
    assert any(command[0:2] == [security.BANDIT_TOOL_NAME, "-r"] for command in runtime.commands)
