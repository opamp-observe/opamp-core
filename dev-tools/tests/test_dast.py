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

from opamp_dev_tools import dast, dast_scan_hooks

UNRELATED_ZAP_RULE_ID = "10020"


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


class _RecordingAlertApi:
    """Record alert identifiers deleted through the simulated ZAP API.

    Attributes:
        deleted_alert_ids: Alert identifiers removed by the scan hook.
    """

    def __init__(self) -> None:
        """Initialize an empty alert-deletion record."""
        self.deleted_alert_ids: list[str] = []

    def delete_alert(self, alert_id: str) -> None:
        """Record one alert deletion requested by the scan hook.

        Parameters:
            alert_id: ZAP alert identifier selected for removal.
        """
        self.deleted_alert_ids.append(alert_id)


class _RecordingZapClient:
    """Provide the alert API surface used by the packaged-scan hook.

    Attributes:
        alert: Recording alert API exposed using the ZAP client attribute name.
    """

    def __init__(self) -> None:
        """Initialize the recording alert API."""
        self.alert = _RecordingAlertApi()


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
    assert f"--hook={dast.SCAN_HOOK_COPY_FILE_NAME}" in command
    volume_value = command[command.index("--volume") + 1]
    assert volume_value.endswith(":/zap/wrk:rw")
    assert "security-reports/zap/provider/baseline" in volume_value
    copied_hook = (
        tmp_path
        / dast.ZAP_REPORT_DIRECTORY
        / dast.DEFAULT_DAST_SCOPE
        / dast.BASELINE_MODE
        / dast.SCAN_HOOK_COPY_FILE_NAME
    )
    assert copied_hook.read_text(encoding="utf-8") == dast.SCAN_HOOK_SOURCE_PATH.read_text(
        encoding="utf-8"
    )
    assert any(message.startswith("DEBUG:") for message in runtime.messages)


def test_scan_hook_removes_only_htmlpreview_big_redirect_alerts() -> None:
    """The hook should remove reviewed redirects while retaining unrelated rule findings."""
    zap_client = _RecordingZapClient()
    dast_scan_hooks.zap_started(zap_client, "http://target.example")
    reviewed_alert = {
        dast_scan_hooks.ALERT_ID_KEY: "7",
        dast_scan_hooks.ALERT_OTHER_INFO_KEY: (
            "Location header URI length: 120 "
            "[https://htmlpreview.github.io/?https://raw.githubusercontent.com/example/docs]."
        ),
    }
    unrelated_redirect = {
        dast_scan_hooks.ALERT_ID_KEY: "8",
        dast_scan_hooks.ALERT_OTHER_INFO_KEY: (
            "Location header URI length: 40 [https://example.org/docs]."
        ),
    }
    unrelated_rule_alert = {
        dast_scan_hooks.ALERT_ID_KEY: "9",
        dast_scan_hooks.ALERT_OTHER_INFO_KEY: "unrelated",
    }
    alert_dict = {
        dast_scan_hooks.BIG_REDIRECT_RULE_ID: [reviewed_alert, unrelated_redirect],
        UNRELATED_ZAP_RULE_ID: [unrelated_rule_alert],
    }

    dast_scan_hooks.zap_get_alerts_wrap(alert_dict)

    assert alert_dict == {
        dast_scan_hooks.BIG_REDIRECT_RULE_ID: [unrelated_redirect],
        UNRELATED_ZAP_RULE_ID: [unrelated_rule_alert],
    }
    assert zap_client.alert.deleted_alert_ids == ["7"]


def test_scan_hook_removes_empty_big_redirect_rule_group() -> None:
    """Removing the final reviewed redirect should remove its empty rule group."""
    zap_client = _RecordingZapClient()
    dast_scan_hooks.zap_started(zap_client, "http://target.example")
    alert_dict = {
        dast_scan_hooks.BIG_REDIRECT_RULE_ID: [
            {
                dast_scan_hooks.ALERT_ID_KEY: "11",
                dast_scan_hooks.ALERT_OTHER_INFO_CAMEL_KEY: (
                    "Redirected to https://htmlpreview.github.io/?example"
                ),
            }
        ]
    }

    dast_scan_hooks.zap_get_alerts_wrap(alert_dict)

    assert alert_dict == {}
    assert zap_client.alert.deleted_alert_ids == ["11"]


def test_scan_hook_leaves_unrelated_alert_groups_unchanged() -> None:
    """The hook should be a no-op when rule 10044 has no alerts."""
    unrelated_rule_alert = {
        dast_scan_hooks.ALERT_ID_KEY: "13",
        dast_scan_hooks.ALERT_OTHER_INFO_LOWER_KEY: "unrelated",
    }
    alert_dict = {UNRELATED_ZAP_RULE_ID: [unrelated_rule_alert]}

    dast_scan_hooks.zap_get_alerts_wrap(alert_dict)

    assert alert_dict == {UNRELATED_ZAP_RULE_ID: [unrelated_rule_alert]}
    assert dast_scan_hooks._alert_other_info({}) == ""  # pylint: disable=protected-access


@pytest.mark.parametrize(
    ("zap_client", "alert_id"),
    [
        (None, "15"),
        (_RecordingZapClient(), None),
    ],
)
def test_scan_hook_can_filter_alert_without_deletion_api_call(
    zap_client: _RecordingZapClient | None,
    alert_id: str | None,
) -> None:
    """Filtering should remain safe when the client or alert identifier is unavailable.

    Parameters:
        zap_client: Optional recording client retained by the packaged-scan startup hook.
        alert_id: Optional alert identifier supplied by ZAP.
    """
    dast_scan_hooks.zap_started(zap_client, "http://target.example")
    reviewed_alert = {
        dast_scan_hooks.ALERT_ID_KEY: alert_id,
        dast_scan_hooks.ALERT_OTHER_INFO_LOWER_KEY: (
            "Redirected to https://htmlpreview.github.io/?example"
        ),
    }
    alert_dict = {dast_scan_hooks.BIG_REDIRECT_RULE_ID: [reviewed_alert]}

    dast_scan_hooks.zap_get_alerts_wrap(alert_dict)

    assert alert_dict == {}
    if zap_client is not None:
        assert zap_client.alert.deleted_alert_ids == []


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


def test_missing_packaged_scan_hook_fails_before_container_start(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A packaging error should fail clearly before ZAP starts.

    Parameters:
        monkeypatch: Pytest fixture used to simulate an omitted packaged hook module.
        tmp_path: Pytest-provided directory used as the report workspace.
    """
    missing_hook_path = tmp_path / "missing_scan_hook.py"
    monkeypatch.setattr(dast, "SCAN_HOOK_SOURCE_PATH", missing_hook_path)

    with pytest.raises(FileNotFoundError, match="Packaged ZAP scan hook was not found"):
        dast._copy_scan_hook(report_directory=tmp_path)  # pylint: disable=protected-access


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
