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

"""Tests for Elastic Agent observer consumer behavior."""

# ruff: noqa: S101

from __future__ import annotations

import json
import logging
import subprocess
import threading
from types import SimpleNamespace
from typing import Any, cast

from opamp_consumer.abstract_client import KEY_SERVICE_INSTANCE_ID
from opamp_consumer.config import ConsumerConfig
from opamp_consumer.elastic_agent import client as elastic_client_module
from opamp_consumer.elastic_agent.client import (
    ELASTIC_AGENT_CONFIG_FLAG,
    ELASTIC_AGENT_RUN_COMMAND,
    ElasticAgentCliLifecycle,
    ElasticAgentOpAMPClient,
    _logstash_hosts_from_agent_config,
    load_elastic_agent_config,
)
from opamp_consumer.proto import opamp_pb2


def _elastic_config(tmp_path) -> ConsumerConfig:
    """Build a minimal Elastic Agent config for unit tests.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        Consumer configuration populated with Elastic Agent settings.
    """
    agent_config_path = tmp_path / "elastic-agent.yml"
    agent_config_path.write_text("agent.monitoring:\n  enabled: true\n", encoding="utf-8")
    return ConsumerConfig(
        server_url="http://localhost:8080",
        service_type="elastic_agent",
        process_tracking="observer",
        process_detection_regex="elastic-agent",
        agent_config_path=str(agent_config_path),
        agent_additional_params=[],
        heartbeat_frequency=10,
        elastic_agent_executable_path="D:\\tools\\elastic-agent.exe",
        elastic_agent_home_path="D:\\tools",
        elastic_agent_api_host="localhost",
        elastic_agent_api_port=6791,
        elastic_agent_api_failon="degraded",
        elastic_agent_status_timeout_seconds=5.0,
        service_name="ElasticAgentObserver",
        service_namespace="ElasticAgent",
    )


def test_load_elastic_agent_config_populates_runtime_status_fields(
    tmp_path,
    caplog,
) -> None:
    """Elastic config loader should populate shared local status fields."""
    config = _elastic_config(tmp_path)
    caplog.set_level(logging.INFO, logger="opamp_consumer.elastic_agent.client")

    loaded = load_elastic_agent_config(config)

    assert loaded.client_status_port == 6791
    assert loaded.agent_http_port == 6791
    assert loaded.agent_http_listen == "localhost"
    assert loaded.agent_http_server == "on"
    assert "agent.monitoring" in str(loaded.agent_config_text)
    assert "Elastic Agent config step: loading agent config" in caplog.text
    assert "Elastic Agent config step: monitoring api host=localhost port=6791" in caplog.text


def test_elastic_lifecycle_launch_uses_run_command(
    monkeypatch,
    tmp_path,
    caplog,
) -> None:
    """Elastic lifecycle launch should use `elastic-agent run -c <config>`."""
    config = _elastic_config(tmp_path)
    config.process_tracking = "supervisor"
    client = ElasticAgentOpAMPClient(config.server_url or "", config)
    launched_commands: list[dict[str, Any]] = []
    caplog.set_level(logging.INFO, logger="opamp_consumer.elastic_agent.client")

    class FakeProcess:
        """Minimal process fake returned by `subprocess.Popen`."""

        pid = 4567

    def fake_popen(command, cwd=None, **_kwargs):
        """Capture launch command and return a fake process.

        Args:
            command: Command list supplied by the lifecycle.
            cwd: Working directory supplied by the lifecycle.
        """
        launched_commands.append({"command": command, "cwd": cwd})
        return FakeProcess()

    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.subprocess.Popen",
        fake_popen,
    )

    assert client.launch_agent_process() is True

    assert launched_commands == [
        {
            "command": [
                "D:\\tools\\elastic-agent.exe",
                ELASTIC_AGENT_RUN_COMMAND,
                ELASTIC_AGENT_CONFIG_FLAG,
                str(tmp_path / "elastic-agent.yml"),
            ],
            "cwd": "D:\\tools",
        }
    ]
    assert client.data.observed_process_pid == 4567
    assert "Elastic Agent lifecycle step: using supervisor CLI strategy" in caplog.text
    assert "Elastic Agent launch step: preparing supervisor launch" in caplog.text
    assert "Elastic Agent launch command:" in caplog.text
    assert "'D:\\tools\\elastic-agent.exe' run -c" in caplog.text
    assert "cwd=D:\\tools" in caplog.text


def test_elastic_observer_launch_attaches_without_spawning(
    monkeypatch,
    tmp_path,
    caplog,
) -> None:
    """Observer mode should attach to an existing Elastic Agent process."""
    config = _elastic_config(tmp_path)
    client = ElasticAgentOpAMPClient(config.server_url or "", config)

    def fake_popen(*_args, **_kwargs):
        raise AssertionError("observer mode should not spawn Elastic Agent")

    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.subprocess.Popen",
        fake_popen,
    )
    monkeypatch.setattr(
        "opamp_consumer.client_observer_mixin.ProcessUtils.find_pid_by_regex",
        lambda regex: 2468 if regex == "elastic-agent" else None,
    )
    caplog.set_level(logging.INFO)

    assert client.launch_agent_process() is True

    assert client.data.observed_process_pid == 2468
    assert client.data.agent_process is None
    assert "Elastic Agent lifecycle step: using observer attach strategy" in caplog.text
    assert "observer mode attached to process pid=2468" in caplog.text


def test_elastic_windows_no_console_kwargs_returns_create_no_window(monkeypatch) -> None:
    """Elastic Agent subprocess helpers should suppress Windows console popups."""
    monkeypatch.setattr(elastic_client_module.sys, "platform", "win32")
    monkeypatch.setattr(
        elastic_client_module.subprocess,
        "CREATE_NO_WINDOW",
        0x08000000,
        raising=False,
    )

    kwargs = elastic_client_module._windows_no_console_kwargs()  # type: ignore[attr-defined]

    assert kwargs == {"creationflags": 0x08000000}


def test_elastic_lifecycle_run_cli_logs_command(monkeypatch, caplog) -> None:
    """Elastic lifecycle should log short CLI commands before running them."""
    owner = SimpleNamespace(
        config=ConsumerConfig(
            elastic_agent_executable_path="elastic-agent",
            elastic_agent_home_path="/tmp/elastic home",
            elastic_agent_status_timeout_seconds=7.0,
        ),
        data=SimpleNamespace(
            observed_process_pid=None,
            process_lock=threading.RLock(),
        ),
    )
    lifecycle = ElasticAgentCliLifecycle(cast(Any, owner))
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.shutil.which",
        lambda *_args, **_kwargs: None,
    )

    def fake_run(
        command,
        cwd=None,
        text=False,
        capture_output=False,
        timeout=None,
        check=True,
        **_kwargs,
    ):
        calls.append(
            {
                "command": command,
                "cwd": cwd,
                "text": text,
                "capture_output": capture_output,
                "timeout": timeout,
                "check": check,
            }
        )
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="{}", stderr="")

    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.subprocess.run",
        fake_run,
    )
    caplog.set_level(logging.INFO, logger="opamp_consumer.elastic_agent.client")

    lifecycle._run_cli("status", "--output", "json")

    assert calls == [
        {
            "command": ["elastic-agent", "status", "--output", "json"],
            "cwd": "/tmp/elastic home",
            "text": True,
            "capture_output": True,
            "timeout": 7.0,
            "check": False,
        }
    ]
    assert "Elastic Agent CLI command: elastic-agent status --output json" in caplog.text
    assert "cwd=/tmp/elastic home" in caplog.text
    assert "timeout=7.0" in caplog.text


def test_elastic_lifecycle_launch_resolves_bare_executable(
    monkeypatch,
    tmp_path,
    caplog,
) -> None:
    """Bare executable names should resolve before calling subprocess on Windows."""
    agent_config_path = tmp_path / "elastic-agent.yml"
    agent_config_path.write_text("agent.monitoring:\n  enabled: true\n", encoding="utf-8")
    config = ConsumerConfig(
        server_url="http://localhost:8080",
        process_tracking="supervisor",
        agent_config_path=str(agent_config_path),
        agent_additional_params=[],
        elastic_agent_executable_path="elastic-agent",
        elastic_agent_home_path=str(tmp_path),
    )
    client = ElasticAgentOpAMPClient(config.server_url or "", config)
    resolved_executable = str(tmp_path / "elastic-agent.exe")
    launched_commands: list[list[str]] = []

    def fake_which(executable, path=None):
        assert executable == "elastic-agent"
        assert str(tmp_path) in str(path)
        return resolved_executable

    class FakeProcess:
        """Minimal process fake returned by `subprocess.Popen`."""

        pid = 7654

    def fake_popen(command, cwd=None, **_kwargs):
        launched_commands.append(list(command))
        assert cwd == str(tmp_path)
        return FakeProcess()

    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.shutil.which",
        fake_which,
    )
    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.subprocess.Popen",
        fake_popen,
    )
    caplog.set_level(logging.INFO, logger="opamp_consumer.elastic_agent.client")

    assert client.launch_agent_process() is True

    assert launched_commands == [
        [
            resolved_executable,
            ELASTIC_AGENT_RUN_COMMAND,
            ELASTIC_AGENT_CONFIG_FLAG,
            str(agent_config_path),
        ]
    ]
    assert "Elastic Agent executable resolved: elastic-agent ->" in caplog.text


def test_elastic_lifecycle_launch_logs_reachable_logstash_endpoint(
    monkeypatch,
    tmp_path,
    caplog,
) -> None:
    """Launch should probe configured Logstash outputs before starting Agent."""
    config = _elastic_config(tmp_path)
    config.process_tracking = "supervisor"
    agent_config_path = tmp_path / "elastic-agent.yml"
    agent_config_path.write_text(
        'outputs:\n  default:\n    type: logstash\n    hosts: ["127.0.0.1:5044"]\n',
        encoding="utf-8",
    )
    config.agent_config_path = str(agent_config_path)
    client = ElasticAgentOpAMPClient(config.server_url or "", config)

    class FakeSocket:
        """Context-manager socket fake returned by create_connection."""

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    class FakeProcess:
        """Minimal process fake returned by `subprocess.Popen`."""

        pid = 8765

    calls: list[tuple[tuple[str, int], float]] = []

    def fake_create_connection(address, timeout=None):
        assert timeout is not None
        calls.append((address, float(timeout)))
        return FakeSocket()

    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.socket.create_connection",
        fake_create_connection,
    )
    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.subprocess.Popen",
        lambda *_args, **_kwargs: FakeProcess(),
    )
    caplog.set_level(logging.INFO, logger="opamp_consumer.elastic_agent.client")

    assert client.launch_agent_process() is True

    assert calls == [(("127.0.0.1", 5044), 1.0)]
    assert (
        "Elastic Agent Logstash output endpoint reachable: 127.0.0.1:5044"
        in caplog.text
    )


def test_elastic_lifecycle_launch_skips_unreachable_logstash_endpoint(
    monkeypatch,
    tmp_path,
    caplog,
) -> None:
    """Launch should fail early when configured Logstash output is unavailable."""
    config = _elastic_config(tmp_path)
    config.process_tracking = "supervisor"
    agent_config_path = tmp_path / "elastic-agent.yml"
    agent_config_path.write_text(
        'outputs:\n  default:\n    type: logstash\n    hosts: ["127.0.0.1:5044"]\n',
        encoding="utf-8",
    )
    config.agent_config_path = str(agent_config_path)
    client = ElasticAgentOpAMPClient(config.server_url or "", config)

    def fake_create_connection(_address, timeout=None):
        raise OSError("connection refused")

    def fake_popen(*_args, **_kwargs):
        raise AssertionError("Elastic Agent should not be launched")

    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.socket.create_connection",
        fake_create_connection,
    )
    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.subprocess.Popen",
        fake_popen,
    )
    caplog.set_level(logging.INFO, logger="opamp_consumer.elastic_agent.client")

    assert client.launch_agent_process() is False

    assert (
        "Elastic Agent Logstash output endpoint unreachable: 127.0.0.1:5044"
        in caplog.text
    )
    assert "Elastic Agent launch skipped" in caplog.text


def test_elastic_lifecycle_launch_reports_interface_name_logstash_host(
    monkeypatch,
    tmp_path,
    caplog,
) -> None:
    """Preflight should call out interface names used accidentally as hosts."""
    config = _elastic_config(tmp_path)
    config.process_tracking = "supervisor"
    agent_config_path = tmp_path / "elastic-agent.yml"
    agent_config_path.write_text(
        'outputs:\n  default:\n    type: logstash\n    hosts: ["eth0:5044"]\n',
        encoding="utf-8",
    )
    config.agent_config_path = str(agent_config_path)
    client = ElasticAgentOpAMPClient(config.server_url or "", config)

    def fake_create_connection(_address, timeout=None):
        raise AssertionError("interface-name host should fail before socket connect")

    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.socket.create_connection",
        fake_create_connection,
    )
    caplog.set_level(logging.INFO, logger="opamp_consumer.elastic_agent.client")

    assert client.launch_agent_process() is False

    assert "eth0 looks like an interface name" in caplog.text


def test_elastic_lifecycle_launch_error_logs_command_context(
    monkeypatch,
    tmp_path,
    caplog,
) -> None:
    """Launch errors should include enough command context to diagnose PATH issues."""
    agent_config_path = tmp_path / "elastic-agent.yml"
    agent_config_path.write_text("agent.monitoring:\n  enabled: true\n", encoding="utf-8")
    config = ConsumerConfig(
        server_url="http://localhost:8080",
        process_tracking="supervisor",
        agent_config_path=str(agent_config_path),
        agent_additional_params=[],
        elastic_agent_executable_path="elastic-agent",
        elastic_agent_home_path=str(tmp_path),
    )
    client = ElasticAgentOpAMPClient(config.server_url or "", config)

    def fake_popen(_command, cwd=None, **_kwargs):
        raise FileNotFoundError("missing elastic-agent")

    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.shutil.which",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.subprocess.Popen",
        fake_popen,
    )
    caplog.set_level(logging.INFO, logger="opamp_consumer.elastic_agent.client")

    assert client.launch_agent_process() is False

    assert "Elastic Agent launch failed:" in caplog.text
    assert "commandline=elastic-agent run -c" in caplog.text
    assert "argv=['elastic-agent'" in caplog.text
    assert f"cwd={tmp_path}" in caplog.text
    assert "configured_executable=elastic-agent" in caplog.text
    assert "lookup_path=" in caplog.text
    assert "process_cwd=" in caplog.text
    assert "path=" in caplog.text
    assert "timeout=None" in caplog.text


def test_elastic_lifecycle_run_cli_error_logs_command_context(
    monkeypatch,
    tmp_path,
    caplog,
) -> None:
    """Short CLI command errors should include command, cwd, and timeout details."""
    owner = SimpleNamespace(
        config=ConsumerConfig(
            elastic_agent_executable_path="elastic-agent",
            elastic_agent_home_path=str(tmp_path),
            elastic_agent_status_timeout_seconds=7.0,
        ),
        data=SimpleNamespace(
            observed_process_pid=None,
            process_lock=threading.RLock(),
        ),
    )
    lifecycle = ElasticAgentCliLifecycle(cast(Any, owner))

    def fake_run(*_args, **_kwargs):
        raise FileNotFoundError("missing elastic-agent")

    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.shutil.which",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.subprocess.run",
        fake_run,
    )
    caplog.set_level(logging.INFO, logger="opamp_consumer.elastic_agent.client")

    try:
        lifecycle._run_cli("status", "--output", "json")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("expected FileNotFoundError")

    assert "Elastic Agent CLI command failed:" in caplog.text
    assert "commandline=elastic-agent status --output json" in caplog.text
    assert f"cwd={tmp_path}" in caplog.text
    assert "configured_executable=elastic-agent" in caplog.text
    assert "timeout=7.0" in caplog.text


def test_elastic_lifecycle_status_json_parses_cli_output() -> None:
    """Elastic lifecycle should parse CLI JSON status output."""
    owner = SimpleNamespace(
        config=ConsumerConfig(
            elastic_agent_executable_path="elastic-agent",
            elastic_agent_home_path=None,
            elastic_agent_status_timeout_seconds=5.0,
        ),
        data=SimpleNamespace(
            observed_process_pid=None,
            process_lock=threading.RLock(),
        ),
    )
    lifecycle = ElasticAgentCliLifecycle(cast(Any, owner))
    lifecycle._run_cli = lambda *args: subprocess.CompletedProcess(
        args=list(args),
        returncode=0,
        stdout='{"status":"HEALTHY","version":"9.5.0"}',
        stderr="",
    )

    payload = lifecycle.status_json()

    assert payload["status"] == "HEALTHY"
    assert payload["version"] == "9.5.0"


def test_elastic_lifecycle_status_json_uses_json_payload_from_nonzero_status(
    caplog,
) -> None:
    """Elastic degraded status returns rc=1 while still writing useful JSON."""
    owner = SimpleNamespace(
        config=ConsumerConfig(
            elastic_agent_executable_path="elastic-agent",
            elastic_agent_home_path=None,
            elastic_agent_status_timeout_seconds=5.0,
        ),
        data=SimpleNamespace(
            observed_process_pid=None,
            process_lock=threading.RLock(),
        ),
    )
    lifecycle = ElasticAgentCliLifecycle(cast(Any, owner))
    lifecycle._run_cli = lambda *args: subprocess.CompletedProcess(
        args=list(args),
        returncode=1,
        stdout=json.dumps(
            {
                "info": {"version": "9.5.0"},
                "state": 3,
                "message": "1 or more components/units in a degraded state",
            }
        ),
        stderr="",
    )
    caplog.set_level(logging.WARNING, logger="opamp_consumer.elastic_agent.client")

    payload = lifecycle.status_json()

    assert payload["info"]["version"] == "9.5.0"
    assert payload["state"] == 3
    assert "Elastic Agent status returned rc=1 with JSON payload" in caplog.text


def test_elastic_lifecycle_status_json_error_includes_stdout() -> None:
    """Status failures should preserve stdout when stderr is empty."""
    owner = SimpleNamespace(
        config=ConsumerConfig(
            elastic_agent_executable_path="elastic-agent",
            elastic_agent_home_path=None,
            elastic_agent_status_timeout_seconds=5.0,
        ),
        data=SimpleNamespace(
            observed_process_pid=None,
            process_lock=threading.RLock(),
        ),
    )
    lifecycle = ElasticAgentCliLifecycle(cast(Any, owner))
    lifecycle._run_cli = lambda *args: subprocess.CompletedProcess(
        args=list(args),
        returncode=1,
        stdout="not json\nwith detail",
        stderr="",
    )

    try:
        lifecycle.status_json()
    except Exception as status_error:
        error_text = str(status_error)
    else:
        raise AssertionError("expected status failure")

    assert "rc=1" in error_text
    assert "stderr=" in error_text
    assert "stdout=not json with detail" in error_text


def test_logstash_hosts_from_agent_config_resolves_env_provider_default(
    monkeypatch,
) -> None:
    """Logstash host parsing should match Elastic Agent env-provider fallbacks."""
    monkeypatch.delenv("OPAMP_LOGSTASH_HOST", raising=False)

    hosts = _logstash_hosts_from_agent_config(
        "outputs:\n"
        "  default:\n"
        "    type: logstash\n"
        "    hosts: [\"${env.OPAMP_LOGSTASH_HOST|'127.0.0.1'}:5044\"]\n"
    )

    assert hosts == ["127.0.0.1:5044"]


def test_logstash_hosts_from_agent_config_resolves_env_provider_override(
    monkeypatch,
) -> None:
    """Logstash host parsing should use OPAMP_LOGSTASH_HOST when set."""
    monkeypatch.setenv("OPAMP_LOGSTASH_HOST", "172.29.112.1")

    hosts = _logstash_hosts_from_agent_config(
        "outputs:\n"
        "  default:\n"
        "    type: logstash\n"
        "    hosts: [\"${env.OPAMP_LOGSTASH_HOST|'127.0.0.1'}:5044\"]\n"
    )

    assert hosts == ["172.29.112.1:5044"]


def test_elastic_poll_status_combines_api_and_cli_payload(monkeypatch, tmp_path) -> None:
    """Status polling should combine liveness API and CLI status data."""
    config = _elastic_config(tmp_path)
    client = ElasticAgentOpAMPClient(config.server_url or "", config)

    class FakeResponse:
        """HTTP response fake for Elastic liveness API."""

        status_code = 200
        text = "HEALTHY"

    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.httpx.get",
        lambda url, timeout: FakeResponse(),
    )
    monkeypatch.setattr(
        ElasticAgentCliLifecycle,
        "status_json",
        lambda _self: {
            "status": "HEALTHY",
            "version": "9.5.0",
            "components": [
                {"name": "system/metrics", "status": "HEALTHY"},
                {
                    "name": "logstash-output",
                    "status": "DEGRADED",
                    "message": "backpressure",
                },
            ],
        },
    )

    results, codes = client.poll_local_status_with_codes(6791)

    assert codes == {"health": "200"}
    payload = json.loads(results["health"])
    assert payload["api"]["liveness"]["status"] == "HEALTHY"
    assert payload["cli_status"]["version"] == "9.5.0"


def test_elastic_poll_status_keeps_liveness_when_cli_status_fails(
    monkeypatch,
    tmp_path,
    caplog,
) -> None:
    """A transient CLI control-socket failure should not hide API liveness."""
    config = _elastic_config(tmp_path)
    client = ElasticAgentOpAMPClient(config.server_url or "", config)

    class FakeResponse:
        """HTTP response fake for Elastic liveness API."""

        status_code = 200
        text = "HEALTHY"

    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.httpx.get",
        lambda url, timeout: FakeResponse(),
    )

    def fake_status_json(_self):
        raise RuntimeError("control socket missing")

    monkeypatch.setattr(ElasticAgentCliLifecycle, "status_json", fake_status_json)
    caplog.set_level(logging.WARNING, logger="opamp_consumer.elastic_agent.client")

    results, codes = client.poll_local_status_with_codes(6791)

    assert codes == {"health": "200"}
    payload = json.loads(results["health"])
    assert payload["api"]["liveness"]["status"] == "HEALTHY"
    assert payload["cli_status_error"] == "control socket missing"
    assert (
        "Elastic Agent status step: CLI status unavailable; "
        "using liveness-only health payload"
    ) in caplog.text


def test_elastic_add_agent_version_retries_until_cli_status_ready(
    monkeypatch,
    tmp_path,
    caplog,
) -> None:
    """Bootstrap version discovery should tolerate early CLI socket readiness."""
    config = _elastic_config(tmp_path)
    client = ElasticAgentOpAMPClient(config.server_url or "", config)
    calls = 0

    def fake_status_json(_self):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("control socket missing")
        return {"version": "9.5.0"}

    monkeypatch.setattr(ElasticAgentCliLifecycle, "status_json", fake_status_json)
    monkeypatch.setattr(
        "opamp_consumer.elastic_agent.client.time.sleep",
        lambda _seconds: None,
    )
    caplog.set_level(logging.INFO, logger="opamp_consumer.elastic_agent.client")

    client.add_agent_version(6791)

    assert calls == 2
    assert client.data.agent_version == "9.5.0"
    assert "Elastic Agent version step: CLI status not ready attempt=1/3" in caplog.text


def test_elastic_add_agent_version_reads_nested_info_version(
    monkeypatch,
    tmp_path,
) -> None:
    """Elastic status often reports version below the info object."""
    config = _elastic_config(tmp_path)
    client = ElasticAgentOpAMPClient(config.server_url or "", config)

    monkeypatch.setattr(
        ElasticAgentCliLifecycle,
        "status_json",
        lambda _self: {"info": {"version": "9.5.0"}},
    )

    client.add_agent_version(6791)

    assert client.data.agent_version == "9.5.0"


def test_elastic_health_transform_populates_component_health(tmp_path) -> None:
    """Elastic status payload should become OpAMP component health entries."""
    config = _elastic_config(tmp_path)
    client = ElasticAgentOpAMPClient(config.server_url or "", config)
    message = opamp_pb2.AgentToServer()
    status_payload = {
        "cli_status": {
            "status": "HEALTHY",
            "components": [
                {"name": "system/metrics", "status": "HEALTHY"},
                {
                    "name": "logstash-output",
                    "status": "DEGRADED",
                    "message": "backpressure",
                },
            ],
        }
    }

    client._health_from_metrics(message, json.dumps(status_payload))

    assert message.health.component_health_map["Elastic Agent"].healthy is True
    assert message.health.component_health_map["system/metrics"].healthy is True
    assert message.health.component_health_map["logstash-output"].healthy is False
    assert (
        message.health.component_health_map["logstash-output"].status
        == "DEGRADED: backpressure"
    )


def test_elastic_health_transform_handles_numeric_state_payload(tmp_path) -> None:
    """Elastic status can use numeric state fields instead of status strings."""
    config = _elastic_config(tmp_path)
    client = ElasticAgentOpAMPClient(config.server_url or "", config)
    message = opamp_pb2.AgentToServer()
    status_payload = {
        "cli_status": {
            "state": 3,
            "message": "1 or more components/units in a degraded state",
            "components": [
                {
                    "name": "filestream",
                    "state": 3,
                    "message": "Recoverable: logstash request failed",
                },
                {"name": "http/metrics-monitoring", "state": 2},
            ],
        }
    }

    client._health_from_metrics(message, json.dumps(status_payload))

    assert message.health.component_health_map["Elastic Agent"].healthy is False
    assert (
        message.health.component_health_map["Elastic Agent"].status
        == "degraded: 1 or more components/units in a degraded state"
    )
    assert message.health.component_health_map["filestream"].healthy is False
    assert (
        message.health.component_health_map["filestream"].status
        == "degraded: Recoverable: logstash request failed"
    )
    assert message.health.component_health_map["http/metrics-monitoring"].healthy is True


def test_elastic_agent_supports_remote_config_capabilities(tmp_path) -> None:
    config = _elastic_config(tmp_path)
    client = ElasticAgentOpAMPClient(config.server_url or "", config)

    supported = client.get_supported_capabilities()

    assert "AcceptsRemoteConfig" in supported
    assert "ReportsEffectiveConfig" in supported


def test_elastic_agent_description_defaults_instance_id_to_service_name(
    tmp_path,
) -> None:
    """Elastic Agent should report a friendly instance id when config omits one."""
    config = _elastic_config(tmp_path)
    config.service_instance_id = None
    config.service_name = "FullDemoElasticAgent"
    client = ElasticAgentOpAMPClient(config.server_url or "", config)

    description = client.get_agent_description()
    identifying = {
        item.key: item.value.string_value
        for item in description.identifying_attributes
        if item.value.WhichOneof("value") == "string_value"
    }

    assert identifying[KEY_SERVICE_INSTANCE_ID] == "FullDemoElasticAgent"
