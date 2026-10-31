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

"""Tests for repository security-check orchestration."""

from __future__ import annotations

import json
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
    module_checks:
        Python module and package requirements requested by tool bootstrap.

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
        self.module_checks: list[tuple[str, str, str]] = []

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

    def ensure_python_module(
        self,
        *,
        python_exe: str,
        module_name: str,
        pip_package: str,
    ) -> None:
        """Capture one interpreter-specific security dependency check.

        Parameters
        ----------
        python_exe:
            Python interpreter that should own the tool.
        module_name:
            Import name checked by the runtime.
        pip_package:
            Versioned requirement installed when the import is unavailable.

        """
        self.module_checks.append((python_exe, module_name, pip_package))


def test_security_tool_bootstrap_uses_the_selected_python(tmp_path: Path) -> None:
    """Tool discovery should not accept an unrelated or stale PATH executable."""
    runtime = _SecurityRuntime(tmp_path)

    security._ensure_cli_tool(  # pylint: disable=protected-access
        runtime,
        python_exe="python-selected",
        module_name=security.PIP_AUDIT_TOOL_MODULE,
        pip_package=security.PIP_AUDIT_PIP_REQUIREMENT,
    )

    assert runtime.module_checks == [
        (
            "python-selected",
            security.PIP_AUDIT_TOOL_MODULE,
            security.PIP_AUDIT_PIP_REQUIREMENT,
        )
    ]


def test_repository_security_targets_cover_packaged_source_trees() -> None:
    """The full static-analysis gate should include every packaged source tree."""
    required_targets = {
        "agent_broker/opamp_broker",
        "catalog-service/src",
        "cli/src",
        "client-config-generator-service/src",
        "config-service/src",
        "consumer-sim/src",
        "consumer/src",
        "dev-tools/src",
        "mcp/src",
        "provider/src",
        "svr-credentials-mgr/plaintext-keyring/src",
        "svr-credentials-mgr/src",
    }

    assert required_targets <= set(security.REPO_RUFF_SECURITY_TARGETS)


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
    assert runtime.commands[1][0:5] == [
        "python",
        "-m",
        security.RUFF_TOOL_MODULE,
        "check",
        "--select",
    ]
    ruff_output_index = runtime.commands[1].index("--output-file")
    assert runtime.commands[1][ruff_output_index + 1] == str(
        tmp_path
        / "dev-tools"
        / "runtime"
        / "security-reports"
        / "repository"
        / "ruff.sarif"
    )
    assert runtime.commands[2][0:4] == [
        "python",
        "-c",
        security.SEMGREP_ENTRYPOINT_CODE,
        "scan",
    ]
    assert runtime.commands[3][0:4] == [
        "python",
        "-m",
        security.BANDIT_TOOL_MODULE,
        "-r",
    ]


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
        python_exe="python",
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


def test_project_audit_writes_scoped_json_report(tmp_path: Path) -> None:
    """Dependency audits should resolve pyproject metadata into a stable report."""
    runtime = _SecurityRuntime(tmp_path)
    project_path = tmp_path / "provider"
    project_path.mkdir(parents=True)
    (project_path / "pyproject.toml").write_text(
        '[project]\nname = "provider"\nversion = "0.1.0"\ndependencies = ["quart>=0.19"]\n',
        encoding="utf-8",
    )

    security._audit_python_projects(  # pylint: disable=protected-access
        runtime,
        python_exe="python",
        project_paths=[project_path],
        env={},
        report_scope="provider",
    )

    assert runtime.commands == [
        [
            "python",
            "-m",
            security.PIP_AUDIT_TOOL_MODULE,
            "--strict",
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
            "--requirement",
            str(
                tmp_path
                / "dev-tools"
                / "runtime"
                / "security-reports"
                / "provider"
                / security.PIP_AUDIT_REQUIREMENTS_DIRECTORY_NAME
                / "provider.txt"
            ),
        ]
    ]
    requirements_path = Path(runtime.commands[0][-1])
    assert requirements_path.read_text(encoding="utf-8") == "quart>=0.19\n"


def test_repository_project_audit_records_each_pyproject_report(tmp_path: Path) -> None:
    """Repository audits should retain one native result per packaged project."""
    runtime = _SecurityRuntime(tmp_path)
    provider_path = tmp_path / "provider"
    consumer_path = tmp_path / "consumer"
    provider_path.mkdir()
    consumer_path.mkdir()
    (provider_path / "pyproject.toml").write_text(
        '[project]\nname = "provider"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (consumer_path / "pyproject.toml").write_text(
        '[project]\nname = "consumer"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )

    security._audit_python_projects(  # pylint: disable=protected-access
        runtime,
        python_exe="python",
        project_paths=[provider_path, consumer_path],
        env={},
        report_scope="repository",
    )

    assert len(runtime.commands) == 2
    assert runtime.commands[0][-1].endswith("provider.txt")
    assert runtime.commands[1][-1].endswith("consumer.txt")
    manifest_path = (
        tmp_path
        / "dev-tools"
        / "runtime"
        / "security-reports"
        / "repository"
        / security.PIP_AUDIT_REPORT_FILE_NAME
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    project_names = [
        entry[security.AUDIT_MANIFEST_PROJECT_KEY]
        for entry in manifest[security.AUDIT_MANIFEST_PROJECTS_KEY]
    ]
    assert project_names == ["provider", "consumer"]


def test_project_audit_excludes_dependencies_owned_by_the_workspace(tmp_path: Path) -> None:
    """Workspace packages should not be resolved through the public package index."""
    runtime = _SecurityRuntime(tmp_path)
    consumer_path = tmp_path / "consumer"
    simulator_path = tmp_path / "consumer-sim"
    consumer_path.mkdir()
    simulator_path.mkdir()
    (consumer_path / "pyproject.toml").write_text(
        '[project]\nname = "opamp-consumer"\nversion = "0.4.0"\n',
        encoding="utf-8",
    )
    (simulator_path / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "opamp-consumer-sim"',
                'version = "0.6.0"',
                'dependencies = ["jsonschema>=4.0", "opamp-consumer>=0.4.0"]',
                "",
            ]
        ),
        encoding="utf-8",
    )

    security._audit_python_projects(  # pylint: disable=protected-access
        runtime,
        python_exe="python",
        project_paths=[consumer_path, simulator_path],
        env={},
        report_scope="repository",
    )

    simulator_requirements = Path(runtime.commands[1][-1]).read_text(encoding="utf-8")
    assert simulator_requirements == "jsonschema>=4.0\n"


def test_repository_project_audit_continues_after_one_project_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """A failed project resolution should not suppress later dependency reports."""
    runtime = _SecurityRuntime(tmp_path)
    provider_path = tmp_path / "provider"
    consumer_path = tmp_path / "consumer"
    provider_path.mkdir()
    consumer_path.mkdir()
    (provider_path / "pyproject.toml").write_text(
        '[project]\nname = "provider"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (consumer_path / "pyproject.toml").write_text(
        '[project]\nname = "consumer"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )

    def fail_provider_audit(
        command: list[str],
        **_options: object,
    ) -> subprocess.CompletedProcess[str]:
        """Fail only the provider audit while recording every attempted command.

        Parameters
        ----------
        command:
            Complete pip-audit command requested by the helper.
        _options:
            Runtime options accepted for compatibility with the production API.

        """
        runtime.commands.append(command)
        if command[-1].endswith("provider.txt"):
            raise RuntimeError("provider dependency resolution failed")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(runtime, "run", fail_provider_audit)

    with pytest.raises(RuntimeError, match="provider dependency resolution failed"):
        security._audit_python_projects(  # pylint: disable=protected-access
            runtime,
            python_exe="python",
            project_paths=[provider_path, consumer_path],
            env={},
            report_scope="repository",
        )

    assert runtime.commands[0][-1].endswith("provider.txt")
    assert runtime.commands[1][-1].endswith("consumer.txt")
    manifest_path = (
        tmp_path
        / "dev-tools"
        / "runtime"
        / "security-reports"
        / "repository"
        / security.PIP_AUDIT_REPORT_FILE_NAME
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    statuses = [
        entry[security.AUDIT_MANIFEST_STATUS_KEY]
        for entry in manifest[security.AUDIT_MANIFEST_PROJECTS_KEY]
    ]
    assert statuses == [security.AUDIT_STATUS_FAILED, security.AUDIT_STATUS_PASSED]


def test_component_security_retains_component_scoped_reports(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Focused security runs should keep every report under the component scope."""
    component_path = tmp_path / "provider"
    component_path.mkdir()
    (component_path / "pyproject.toml").write_text(
        '[project]\nname = "provider"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
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

    assert any(
        command[0:4] == ["python", "-c", security.SEMGREP_ENTRYPOINT_CODE, "scan"]
        for command in runtime.commands
    )
    assert any(
        command[0:4] == ["python", "-m", security.BANDIT_TOOL_MODULE, "-r"]
        for command in runtime.commands
    )
