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

"""Tests for Docker-backed OWASP ZAP developer workflows."""

from __future__ import annotations

from pathlib import Path

import pytest

from opamp_dev_tools import dast


class _RecordingRuntime:
    """Record ZAP runner interactions without starting a container.

    Attributes
    ----------
    repo_root:
        Temporary repository root used to resolve reports and rule files.
    commands:
        Process argument vectors requested by the runner.
    messages:
        Informational and debug messages emitted by the runner.

    """

    def __init__(self, repo_root: Path) -> None:
        """Initialize an empty runtime recording.

        Parameters
        ----------
        repo_root:
            Temporary repository root used by the scan under test.

        """
        self.repo_root = repo_root
        self.commands: list[list[str]] = []
        self.messages: list[str] = []

    def info(self, message: str) -> None:
        """Record one informational message.

        Parameters
        ----------
        message:
            Developer-facing message emitted by the DAST runner.

        """
        self.messages.append(message)

    def run(self, command: list[str], *, cwd: Path) -> None:
        """Record one container command and its expected working directory.

        Parameters
        ----------
        command:
            Shell-independent argument vector prepared for the container runtime.
        cwd:
            Repository working directory supplied to the process runner.

        """
        assert cwd == self.repo_root
        self.commands.append(command)


def test_baseline_scan_builds_portable_docker_command(monkeypatch, tmp_path: Path) -> None:
    """Baseline scans should mount reports and bridge the cross-platform host alias."""
    runtime = _RecordingRuntime(tmp_path)
    monkeypatch.setattr(dast, "resolve_container_runtime", lambda configured_runtime: "docker")

    result = dast.run_dast_scan(
        runtime,  # type: ignore[arg-type]
        options=dast.DastScanOptions(mode=dast.BASELINE_MODE, generate_rules=True),
    )

    assert result is False
    assert len(runtime.commands) == 1
    command = runtime.commands[0]
    assert command[:5] == [
        "docker",
        "run",
        "--rm",
        "--add-host",
        dast.DOCKER_HOST_GATEWAY_MAPPING,
    ]
    assert dast.DEFAULT_ZAP_IMAGE in command
    assert dast.BASELINE_SCAN_SCRIPT in command
    assert "-I" in command
    assert command[-2:] == ["-g", dast.RULES_GENERATED_FILE_NAME]
    volume_value = command[command.index("--volume") + 1]
    assert volume_value.endswith(":/zap/wrk:rw")
    assert "security-reports/zap/provider/baseline" in volume_value
    assert any(message.startswith("DEBUG:") for message in runtime.messages)


def test_baseline_scan_copies_relative_rules_file(monkeypatch, tmp_path: Path) -> None:
    """A repository-relative policy should be copied into the mounted workspace."""
    source_directory = tmp_path / "security" / "zap"
    source_directory.mkdir(parents=True)
    rules_path = source_directory / "provider_rules.conf"
    rules_path.write_text("10020\tWARN\t(X-Frame-Options Header Not Set)\n", encoding="utf-8")
    runtime = _RecordingRuntime(tmp_path)
    monkeypatch.setattr(dast, "resolve_container_runtime", lambda configured_runtime: "docker")

    dast.run_dast_scan(
        runtime,  # type: ignore[arg-type]
        options=dast.DastScanOptions(
            mode=dast.BASELINE_MODE,
            rules_file=Path("security/zap/provider_rules.conf"),
        ),
    )

    copied_path = (
        tmp_path
        / dast.ZAP_REPORT_DIRECTORY
        / dast.DEFAULT_DAST_SCOPE
        / dast.BASELINE_MODE
        / dast.RULES_COPY_FILE_NAME
    )
    assert copied_path.read_text(encoding="utf-8") == rules_path.read_text(encoding="utf-8")
    command = runtime.commands[0]
    assert command[command.index("-c") + 1] == dast.RULES_COPY_FILE_NAME


def test_baseline_scan_accepts_absolute_rules_file(monkeypatch, tmp_path: Path) -> None:
    """An absolute policy path should be copied without repository-root prefixing."""
    rules_path = tmp_path / "absolute_rules.conf"
    rules_path.write_text("10020\tWARN\t(X-Frame-Options Header Not Set)\n", encoding="utf-8")
    runtime = _RecordingRuntime(tmp_path)
    monkeypatch.setattr(dast, "resolve_container_runtime", lambda configured_runtime: "docker")

    dast.run_dast_scan(
        runtime,  # type: ignore[arg-type]
        options=dast.DastScanOptions(mode=dast.BASELINE_MODE, rules_file=rules_path.resolve()),
    )

    copied_path = (
        tmp_path
        / dast.ZAP_REPORT_DIRECTORY
        / dast.DEFAULT_DAST_SCOPE
        / dast.BASELINE_MODE
        / dast.RULES_COPY_FILE_NAME
    )
    assert copied_path.is_file()


def test_missing_rules_file_fails_before_container_start(monkeypatch, tmp_path: Path) -> None:
    """A missing policy should produce an actionable error without running Docker."""
    runtime = _RecordingRuntime(tmp_path)
    monkeypatch.setattr(dast, "resolve_container_runtime", lambda configured_runtime: "docker")

    with pytest.raises(FileNotFoundError, match="ZAP rules file was not found"):
        dast.run_dast_scan(
            runtime,  # type: ignore[arg-type]
            options=dast.DastScanOptions(
                mode=dast.BASELINE_MODE,
                rules_file=Path("security/zap/missing.conf"),
            ),
        )

    assert not runtime.commands


def test_rules_file_already_in_report_workspace_is_not_recopied(tmp_path: Path) -> None:
    """The policy copier should preserve a file already at its mounted destination."""
    runtime = _RecordingRuntime(tmp_path)
    report_directory = tmp_path / "reports"
    report_directory.mkdir()
    rules_path = report_directory / dast.RULES_COPY_FILE_NAME
    rules_path.write_text("10020\tWARN\t(X-Frame-Options Header Not Set)\n", encoding="utf-8")

    copied_path = dast._copy_rules_file(  # pylint: disable=protected-access
        runtime,  # type: ignore[arg-type]
        source_path=rules_path,
        report_directory=report_directory,
    )

    assert copied_path == rules_path


def test_full_scan_requires_explicit_active_scan_acknowledgement(tmp_path: Path) -> None:
    """Active attack payloads should never run without an explicit safety flag."""
    runtime = _RecordingRuntime(tmp_path)

    with pytest.raises(ValueError, match="--allow-active-scan"):
        dast.run_dast_scan(
            runtime,  # type: ignore[arg-type]
            options=dast.DastScanOptions(mode=dast.FULL_MODE),
        )

    assert not runtime.commands


def test_full_scan_can_fail_on_warnings(monkeypatch, tmp_path: Path) -> None:
    """Strict full scans should omit ZAP's warning-suppression argument."""
    runtime = _RecordingRuntime(tmp_path)
    monkeypatch.setattr(
        dast,
        "resolve_container_runtime",
        lambda configured_runtime: "/usr/bin/docker",
    )

    dast.run_dast_scan(
        runtime,  # type: ignore[arg-type]
        options=dast.DastScanOptions(
            mode=dast.FULL_MODE,
            allow_active_scan=True,
            fail_on_warning=True,
            target="http://provider:8080",
        ),
    )

    command = runtime.commands[0]
    assert dast.FULL_SCAN_SCRIPT in command
    assert "-I" not in command
    assert "--add-host" not in command


@pytest.mark.parametrize(
    ("options", "message"),
    [
        (dast.DastScanOptions(mode="unknown"), "Unsupported DAST mode"),
        (dast.DastScanOptions(mode=dast.BASELINE_MODE, target="localhost:8080"), "absolute"),
        (dast.DastScanOptions(mode=dast.BASELINE_MODE, scope="../escape"), "scope"),
        (dast.DastScanOptions(mode=dast.BASELINE_MODE, spider_minutes=0), "spider"),
        (
            dast.DastScanOptions(mode=dast.BASELINE_MODE, startup_timeout_minutes=0),
            "startup",
        ),
        (dast.DastScanOptions(mode=dast.BASELINE_MODE, image=""), "image"),
        (
            dast.DastScanOptions(
                mode=dast.BASELINE_MODE,
                rules_file=Path("rules.conf"),
                generate_rules=True,
            ),
            "either",
        ),
    ],
)
def test_invalid_scan_options_fail_before_runtime_discovery(
    options: dast.DastScanOptions,
    message: str,
    tmp_path: Path,
) -> None:
    """Invalid scan values should fail before filesystem or container side effects."""
    runtime = _RecordingRuntime(tmp_path)

    with pytest.raises((ValueError, FileNotFoundError), match=message):
        dast.run_dast_scan(runtime, options=options)  # type: ignore[arg-type]

    assert not runtime.commands
