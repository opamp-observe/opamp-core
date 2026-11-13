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

import json
import subprocess
from pathlib import Path

import pytest

from opamp_dev_tools import dast, dast_scan_hooks

UNRELATED_ZAP_RULE_ID = "10020"
EXTERNAL_TARGET_URL = "http://host.docker.internal:8080"
CONFIG_KEY_PROVIDER = "provider"
CONFIG_KEY_TLS = "tls"
CONFIG_KEY_TLS_CERT_FILE = "cert_file"
CONFIG_KEY_TLS_ENABLED = "enabled"
CONFIG_KEY_TLS_KEY_FILE = "key_file"


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

    def run(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
        capture_output: bool = False,
        text: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Record one container command and its expected working directory.

        Parameters
        ----------
        command:
            Shell-independent argument vector prepared for the container runtime.
        cwd:
            Repository working directory supplied to the process runner.
        check:
            Whether the production runtime would raise for a non-zero exit.
        capture_output:
            Whether the production runtime would retain command output.
        text:
            Whether the production runtime would decode process streams as text.

        """
        del check, capture_output, text
        assert cwd is None or cwd == self.repo_root
        self.commands.append(command)
        stdout = dast.MANAGED_TARGET_STATUS_HEALTHY if "inspect" in command else ""
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")


class _FailingHttpZapRuntime(_RecordingRuntime):
    """Fail the HTTP ZAP command while retaining every attempted command."""

    def run(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
        capture_output: bool = False,
        text: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Record commands and raise when ZAP reaches the managed HTTP target.

        Parameters
        ----------
        command:
            Shell-independent process argument vector.
        cwd:
            Optional process working directory.
        check:
            Whether the production runtime would raise on failure.
        capture_output:
            Whether the production runtime would capture process output.
        text:
            Whether process output would be decoded as text.

        """
        completed = super().run(
            command,
            cwd=cwd,
            check=check,
            capture_output=capture_output,
            text=text,
        )
        if dast.DEFAULT_ZAP_IMAGE in command and dast.DEFAULT_DAST_TARGET in command:
            raise subprocess.CalledProcessError(returncode=1, cmd=command)
        return completed


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
        opened_urls: URLs added to the managed full-app scan tree.
    """

    def __init__(self) -> None:
        """Initialize the recording alert API."""
        self.alert = _RecordingAlertApi()
        self.opened_urls: list[str] = []

    def urlopen(self, url: str) -> bytes:
        """Record one URL opened to seed the traditional ZAP spider.

        Parameters:
            url: Absolute managed application URL added to the ZAP site tree.

        Returns:
            Empty response body used by the recording client.
        """
        self.opened_urls.append(url)
        return b""


class _FailingSeedZapClient(_RecordingZapClient):
    """Simulate a ZAP client that cannot access managed route seeds."""

    def urlopen(self, url: str) -> bytes:
        """Raise the generic API failure shape handled by the packaged scan hook.

        Parameters:
            url: Managed route URL whose access is being simulated.
        """
        raise RuntimeError(f"unavailable: {url}")


class _UnhealthyRecordingRuntime(_RecordingRuntime):
    """Simulate a target container whose health check fails with retained logs."""

    def run(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
        capture_output: bool = False,
        text: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Return terminal health status and diagnostic logs for managed-target inspection.

        Parameters:
            command: Container command requested by the DAST runner.
            cwd: Optional repository working directory.
            check: Whether command failure should raise in the production runtime.
            capture_output: Whether command output is requested by the caller.
            text: Whether streams should be decoded as text.
        """
        completed = super().run(
            command,
            cwd=cwd,
            check=check,
            capture_output=capture_output,
            text=text,
        )
        if "inspect" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=dast.MANAGED_TARGET_STATUS_UNHEALTHY,
                stderr="",
            )
        if "logs" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="application bootstrap failed",
                stderr="",
            )
        return completed


class _StartingThenHealthyRuntime(_RecordingRuntime):
    """Simulate one pending health poll before the target becomes healthy.

    Attributes:
        inspect_count: Number of container health inspections requested by the runner.
    """

    def __init__(self, repo_root: Path) -> None:
        """Initialize the recording runtime with no completed health inspections.

        Parameters:
            repo_root: Temporary repository root used by the scan under test.
        """
        super().__init__(repo_root)
        self.inspect_count = 0

    def run(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
        capture_output: bool = False,
        text: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Return a starting status for the first health inspection.

        Parameters:
            command: Container command requested by the DAST runner.
            cwd: Optional repository working directory.
            check: Whether command failure should raise in the production runtime.
            capture_output: Whether command output is requested by the caller.
            text: Whether streams should be decoded as text.
        """
        completed = super().run(
            command,
            cwd=cwd,
            check=check,
            capture_output=capture_output,
            text=text,
        )
        if "inspect" not in command:
            return completed
        self.inspect_count += 1
        if self.inspect_count == 1:
            return subprocess.CompletedProcess(command, 0, stdout="starting", stderr="")
        return completed


def test_baseline_scan_builds_portable_docker_command(monkeypatch, tmp_path: Path) -> None:
    """Baseline scans should mount reports and bridge the cross-platform host alias."""
    runtime = _RecordingRuntime(tmp_path)
    monkeypatch.setattr(dast, "resolve_container_runtime", lambda configured_runtime: "docker")

    result = dast.run_dast_scan(
        runtime,  # type: ignore[arg-type]
        options=dast.DastScanOptions(
            mode=dast.BASELINE_MODE,
            target=EXTERNAL_TARGET_URL,
            generate_rules=True,
            external_target=True,
        ),
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


def test_managed_scan_builds_private_full_app_and_cleans_resources(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Default scans should isolate ZAP and the installed full app from host development tools.

    Parameters:
        monkeypatch: Pytest fixture used to select the recording container runtime.
        tmp_path: Temporary repository root used by the recording runtime.
    """
    dockerfile_path = tmp_path / dast.MANAGED_TARGET_DOCKERFILE
    dockerfile_path.parent.mkdir(parents=True)
    dockerfile_path.write_text("FROM scratch\n", encoding="utf-8")
    runtime = _RecordingRuntime(tmp_path)
    monkeypatch.setattr(dast, "resolve_container_runtime", lambda configured_runtime: "docker")

    dast.run_dast_scan(
        runtime,  # type: ignore[arg-type]
        options=dast.DastScanOptions(mode=dast.BASELINE_MODE),
    )

    build_commands = [command for command in runtime.commands if "build" in command]
    http_target_command = next(
        command
        for command in runtime.commands
        if command[:2] == ["docker", "run"] and dast.MANAGED_TARGET_IMAGE in command
    )
    https_target_command = next(
        command
        for command in runtime.commands
        if command[:2] == ["docker", "run"] and dast.MANAGED_HTTPS_TARGET_IMAGE in command
    )
    zap_commands = [
        command for command in runtime.commands if dast.DEFAULT_ZAP_IMAGE in command
    ]
    assert len(build_commands) == 2
    assert len(zap_commands) == 2
    assert str(dockerfile_path.resolve()) in build_commands[0]
    assert dast.MANAGED_HTTP_BUILD_TARGET in build_commands[0]
    assert dast.MANAGED_HTTPS_BUILD_TARGET in build_commands[1]
    assert "--publish" not in http_target_command
    assert "-p" not in http_target_command
    assert dast.MANAGED_TARGET_NETWORK_ALIAS in http_target_command
    assert "--publish" not in https_target_command
    assert "-p" not in https_target_command
    assert dast.MANAGED_TARGET_NETWORK_ALIAS in https_target_command
    assert "--network" in zap_commands[0]
    assert "--network" in zap_commands[1]
    assert dast.DEFAULT_DAST_TARGET in zap_commands[0]
    assert dast.MANAGED_HTTPS_DAST_TARGET in zap_commands[1]
    https_volume = zap_commands[1][zap_commands[1].index("--volume") + 1]
    assert f"/{dast.HTTPS_REPORT_SUBDIRECTORY}:/zap/wrk:rw" in https_volume
    assert runtime.commands.index(zap_commands[0]) < runtime.commands.index(https_target_command)
    cleanup_commands = [
        command
        for command in runtime.commands
        if command[1:4] == ["container", "rm", "--force"]
    ]
    network_cleanup_commands = [
        command for command in runtime.commands if command[1:3] == ["network", "rm"]
    ]
    assert len(cleanup_commands) == 2
    assert len(network_cleanup_commands) == 2


def test_https_target_definition_uses_generated_certificate_configuration() -> None:
    """The HTTPS image should generate TLS material and reference it from provider config."""
    repository_root = Path(__file__).resolve().parents[2]
    dockerfile_text = (repository_root / dast.MANAGED_TARGET_DOCKERFILE).read_text(
        encoding="utf-8"
    )
    https_config_path = repository_root / "dev-tools" / "docker" / "dast" / "opamp-https.json"
    https_config = json.loads(https_config_path.read_text(encoding="utf-8"))
    provider_config = https_config[CONFIG_KEY_PROVIDER]
    tls_config = provider_config[CONFIG_KEY_TLS]

    assert f"AS {dast.MANAGED_HTTPS_BUILD_TARGET}" in dockerfile_text
    assert "openssl req" in dockerfile_text
    assert "DNS:opamp-dast-target" in dockerfile_text
    assert tls_config[CONFIG_KEY_TLS_ENABLED] is True
    assert tls_config[CONFIG_KEY_TLS_CERT_FILE] == "/app/tls/server.crt"
    assert tls_config[CONFIG_KEY_TLS_KEY_FILE] == "/app/tls/server.key"


def test_managed_https_scan_does_not_start_when_http_scan_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The HTTPS target must start only after the HTTP ZAP process completes successfully.

    Parameters
    ----------
    monkeypatch:
        Pytest fixture used to select the recording container runtime.
    tmp_path:
        Temporary repository root containing a placeholder Dockerfile.

    """
    dockerfile_path = tmp_path / dast.MANAGED_TARGET_DOCKERFILE
    dockerfile_path.parent.mkdir(parents=True)
    dockerfile_path.write_text("FROM scratch\n", encoding="utf-8")
    runtime = _FailingHttpZapRuntime(tmp_path)
    monkeypatch.setattr(dast, "resolve_container_runtime", lambda configured_runtime: "docker")

    with pytest.raises(subprocess.CalledProcessError):
        dast.run_dast_scan(
            runtime,  # type: ignore[arg-type]
            options=dast.DastScanOptions(mode=dast.BASELINE_MODE),
        )

    assert any(
        dast.MANAGED_TARGET_IMAGE in command for command in runtime.commands
    )
    assert not any(
        dast.MANAGED_HTTPS_TARGET_IMAGE in command for command in runtime.commands
    )
    assert any(
        command[1:4] == ["container", "rm", "--force"]
        for command in runtime.commands
    )


def test_managed_target_requires_packaged_dockerfile(tmp_path: Path) -> None:
    """A missing target definition should fail before creating container resources.

    Parameters:
        tmp_path: Temporary repository root without a DAST Dockerfile.
    """
    runtime = _RecordingRuntime(tmp_path)

    with pytest.raises(FileNotFoundError, match="DAST target Dockerfile"):
        dast._start_managed_target(  # pylint: disable=protected-access
            runtime,  # type: ignore[arg-type]
            runtime_executable="docker",
            options=dast.DastScanOptions(mode=dast.BASELINE_MODE),
        )

    assert not runtime.commands


def test_managed_target_start_failure_removes_created_resources(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A failed readiness check should remove both the app container and private network.

    Parameters:
        monkeypatch: Pytest fixture used to force readiness failure.
        tmp_path: Temporary repository root containing a placeholder Dockerfile.
    """
    dockerfile_path = tmp_path / dast.MANAGED_TARGET_DOCKERFILE
    dockerfile_path.parent.mkdir(parents=True)
    dockerfile_path.write_text("FROM scratch\n", encoding="utf-8")
    runtime = _RecordingRuntime(tmp_path)

    def fail_readiness(*args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """Simulate an application that cannot complete its readiness check."""
        del args, kwargs
        raise RuntimeError("not ready")

    monkeypatch.setattr(dast, "_wait_for_managed_target", fail_readiness)

    with pytest.raises(RuntimeError, match="not ready"):
        dast._start_managed_target(  # pylint: disable=protected-access
            runtime,  # type: ignore[arg-type]
            runtime_executable="docker",
            options=dast.DastScanOptions(mode=dast.BASELINE_MODE),
        )

    assert any(command[1:4] == ["container", "rm", "--force"] for command in runtime.commands)
    assert any(command[1:3] == ["network", "rm"] for command in runtime.commands)


def test_managed_target_health_failure_includes_container_logs(tmp_path: Path) -> None:
    """Terminal health failure should report application logs for diagnosis.

    Parameters:
        tmp_path: Temporary repository root used by the unhealthy recording runtime.
    """
    runtime = _UnhealthyRecordingRuntime(tmp_path)
    deployment = dast.ManagedDastDeployment("private-network", "full-app")

    with pytest.raises(RuntimeError, match="application bootstrap failed"):
        dast._wait_for_managed_target(  # pylint: disable=protected-access
            runtime,  # type: ignore[arg-type]
            runtime_executable="docker",
            deployment=deployment,
        )


def test_managed_target_waits_while_health_check_is_starting(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A pending health status should be polled again after the configured interval.

    Parameters:
        monkeypatch: Pytest fixture used to bypass the real polling delay.
        tmp_path: Temporary repository root used by the recording runtime.
    """
    runtime = _StartingThenHealthyRuntime(tmp_path)
    deployment = dast.ManagedDastDeployment("private-network", "full-app")
    sleep_intervals: list[int] = []
    monkeypatch.setattr(dast.time, "sleep", sleep_intervals.append)

    dast._wait_for_managed_target(  # pylint: disable=protected-access
        runtime,  # type: ignore[arg-type]
        runtime_executable="docker",
        deployment=deployment,
    )

    assert runtime.inspect_count == 2
    assert sleep_intervals == [dast.MANAGED_TARGET_STATUS_POLL_SECONDS]


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


def test_scan_hook_seeds_all_managed_full_app_routes() -> None:
    """Managed scans should explicitly add JavaScript-discovered plugin routes to ZAP."""
    zap_client = _RecordingZapClient()

    dast_scan_hooks.zap_started(zap_client, dast.DEFAULT_DAST_TARGET)

    assert zap_client.opened_urls == [
        f"{dast.DEFAULT_DAST_TARGET}{seed_path}"
        for seed_path in dast_scan_hooks.MANAGED_TARGET_SEED_PATHS
    ]


def test_scan_hook_seed_failures_do_not_abort_scan(caplog: pytest.LogCaptureFixture) -> None:
    """A failed optional route seed should be logged without stopping packaged ZAP startup.

    Parameters:
        caplog: Pytest fixture used to verify the route-specific warning.
    """
    zap_client = _FailingSeedZapClient()

    dast_scan_hooks.zap_started(zap_client, dast.DEFAULT_DAST_TARGET)

    assert "Unable to seed managed DAST route" in caplog.text


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
            target=EXTERNAL_TARGET_URL,
            rules_file=Path("security/zap/provider_rules.conf"),
            external_target=True,
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
        options=dast.DastScanOptions(
            mode=dast.BASELINE_MODE,
            target=EXTERNAL_TARGET_URL,
            rules_file=rules_path.resolve(),
            external_target=True,
        ),
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
                target=EXTERNAL_TARGET_URL,
                rules_file=Path("security/zap/missing.conf"),
                external_target=True,
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
            external_target=True,
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
        (
            dast.DastScanOptions(mode=dast.BASELINE_MODE, target=EXTERNAL_TARGET_URL),
            "external-target",
        ),
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
