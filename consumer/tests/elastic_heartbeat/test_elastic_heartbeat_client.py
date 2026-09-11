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

"""Tests for the Elastic Heartbeat consumer plugin."""

# ruff: noqa: S101

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from opamp_consumer.config import ConsumerConfig
from opamp_consumer.elastic_heartbeat import client as heartbeat_module
from opamp_consumer.elastic_heartbeat.client import (
    ELASTIC_HEARTBEAT_CONFIG_FLAG,
    ELASTIC_HEARTBEAT_FOREGROUND_FLAG,
    ElasticHeartbeatLifecycle,
    ElasticHeartbeatOpAMPClient,
    _logstash_hosts_from_beat_config,
    load_elastic_heartbeat_config,
    process_consumer_config,
)
from opamp_consumer.plugin_config import ConsumerPluginConfigContext
from opamp_consumer.proto import opamp_pb2


def _heartbeat_config(tmp_path: Path) -> ConsumerConfig:
    agent_config_path = tmp_path / "heartbeat.yml"
    agent_config_path.write_text(
        "http.enabled: true\n"
        "http.host: 127.0.0.1\n"
        "http.port: 5066\n"
        "output.logstash:\n"
        "  hosts: ['127.0.0.1:5044']\n",
        encoding="utf-8",
    )
    return ConsumerConfig(
        server_url="http://localhost:8080",
        service_type="elastic_heartbeat",
        process_tracking="supervisor",
        agent_config_path=str(agent_config_path),
        agent_additional_params=[],
        heartbeat_frequency=5,
        elastic_heartbeat_executable_path="heartbeat",
        elastic_heartbeat_home_path=str(tmp_path),
        elastic_heartbeat_api_host="127.0.0.1",
        elastic_heartbeat_api_port=5066,
        elastic_heartbeat_status_timeout_seconds=3.0,
        service_name="ElasticHeartbeat",
        service_namespace="ElasticBeat",
    )


def test_process_consumer_config_resolves_heartbeat_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "opamp.json"
    config_path.write_text("{}\n", encoding="utf-8")
    context = ConsumerPluginConfigContext(
        service_type="elastic_heartbeat",
        section_name="elastic_heartbeat",
        raw_section={
            "executable_path": "bin/heartbeat",
            "home_path": "heartbeat-home",
            "api_host": "127.0.0.1",
            "api_port": 5067,
            "status_timeout_seconds": 2,
        },
        consumer_raw={},
        config_path=config_path,
    )

    updates = process_consumer_config(context)

    assert updates["elastic_heartbeat_executable_path"] == str((tmp_path / "bin" / "heartbeat").resolve())
    assert updates["elastic_heartbeat_home_path"] == str((tmp_path / "heartbeat-home").resolve())
    assert updates["elastic_heartbeat_api_host"] == "127.0.0.1"
    assert updates["elastic_heartbeat_api_port"] == 5067
    assert updates["elastic_heartbeat_status_timeout_seconds"] == 2.0


def test_load_elastic_heartbeat_config_reads_beat_http_settings(tmp_path: Path) -> None:
    config = _heartbeat_config(tmp_path)

    loaded = load_elastic_heartbeat_config(config)

    assert loaded.client_status_port == 5066
    assert loaded.agent_http_port == 5066
    assert loaded.agent_http_listen == "127.0.0.1"
    assert loaded.agent_http_server == "on"
    assert "output.logstash" in str(loaded.agent_config_text)


def test_logstash_hosts_from_beat_config_resolves_env_provider_default(monkeypatch) -> None:
    monkeypatch.delenv("OPAMP_LOGSTASH_HOST", raising=False)

    hosts = _logstash_hosts_from_beat_config(
        "output.logstash:\n"
        "  hosts: [\"${env.OPAMP_LOGSTASH_HOST|'127.0.0.1'}:5044\"]\n"
    )

    assert hosts == ["127.0.0.1:5044"]


def test_heartbeat_lifecycle_launch_uses_foreground_config_command(
    monkeypatch,
    tmp_path: Path,
    caplog,
) -> None:
    config = _heartbeat_config(tmp_path)
    client = ElasticHeartbeatOpAMPClient(config.server_url or "", config)
    launched_commands: list[dict[str, object]] = []

    class FakeProcess:
        pid = 2468

    def fake_popen(command, cwd=None, **_kwargs):
        launched_commands.append({"command": list(command), "cwd": cwd})
        return FakeProcess()

    monkeypatch.setattr(
        "opamp_consumer.elastic_heartbeat.client.shutil.which",
        lambda executable, path=None: "/usr/local/bin/heartbeat"
        if executable == "heartbeat"
        else None,
    )
    monkeypatch.setattr(
        "opamp_consumer.elastic_heartbeat.client.socket.create_connection",
        lambda *_args, **_kwargs: _SocketContext(),
    )
    monkeypatch.setattr(
        "opamp_consumer.elastic_heartbeat.client.subprocess.Popen",
        fake_popen,
    )
    caplog.set_level(logging.INFO, logger="opamp_consumer.elastic_heartbeat.client")

    assert client.launch_agent_process() is True

    assert launched_commands == [
        {
            "command": [
                "/usr/local/bin/heartbeat",
                ELASTIC_HEARTBEAT_FOREGROUND_FLAG,
                ELASTIC_HEARTBEAT_CONFIG_FLAG,
                str(tmp_path / "heartbeat.yml"),
            ],
            "cwd": str(tmp_path),
        }
    ]
    assert client.data.observed_process_pid == 2468
    assert "Elastic Heartbeat launch command:" in caplog.text


class _SocketContext:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


def test_heartbeat_lifecycle_launch_skips_unreachable_logstash(
    monkeypatch,
    tmp_path: Path,
    caplog,
) -> None:
    config = _heartbeat_config(tmp_path)
    client = ElasticHeartbeatOpAMPClient(config.server_url or "", config)

    monkeypatch.setattr(
        "opamp_consumer.elastic_heartbeat.client.socket.create_connection",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("refused")),
    )
    monkeypatch.setattr(
        "opamp_consumer.elastic_heartbeat.client.subprocess.Popen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not launch")),
    )
    caplog.set_level(logging.INFO, logger="opamp_consumer.elastic_heartbeat.client")

    assert client.launch_agent_process() is False

    assert "Elastic Heartbeat Logstash output endpoint unreachable: 127.0.0.1:5044" in caplog.text
    assert "Elastic Heartbeat launch skipped" in caplog.text


def test_heartbeat_observer_launch_attaches_without_spawning(
    monkeypatch,
    tmp_path: Path,
    caplog,
) -> None:
    config = _heartbeat_config(tmp_path)
    config.process_tracking = "observer"
    config.process_detection_regex = "heartbeat.*heartbeat.yml"
    client = ElasticHeartbeatOpAMPClient(config.server_url or "", config)

    monkeypatch.setattr(
        "opamp_consumer.elastic_heartbeat.client.subprocess.Popen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("observer should not spawn")),
    )
    monkeypatch.setattr(
        "opamp_consumer.client_observer_mixin.ProcessUtils.find_pid_by_regex",
        lambda regex: 1357 if regex == "heartbeat.*heartbeat.yml" else None,
    )
    caplog.set_level(logging.INFO)

    assert client.launch_agent_process() is True

    assert client.data.observed_process_pid == 1357
    assert client.data.agent_process is None
    assert "Elastic Heartbeat lifecycle step: using observer attach strategy" in caplog.text


def test_heartbeat_poll_status_normalizes_root_to_health(monkeypatch, tmp_path: Path) -> None:
    config = _heartbeat_config(tmp_path)
    client = ElasticHeartbeatOpAMPClient(config.server_url or "", config)
    calls: list[str] = []

    class FakeResponse:
        def __init__(self, text: str, status_code: int = 200) -> None:
            self.text = text
            self.status_code = status_code

        def raise_for_status(self) -> None:
            return None

    def fake_get(url, timeout):
        calls.append(url)
        if url.endswith("/stats"):
            return FakeResponse('{"beat":{"cpu":{"total":{"ticks":1}}}}')
        return FakeResponse('{"beat":"heartbeat","version":"9.5.0","status":"ok"}')

    monkeypatch.setattr("opamp_consumer.client_runtime_mixin.httpx.get", fake_get)

    results, codes = client.poll_local_status_with_codes(5066)

    assert calls == ["http://127.0.0.1:5066/", "http://127.0.0.1:5066/stats"]
    assert "health" in results
    assert codes["health"] == "200"
    assert json.loads(results["health"])["beat"] == "heartbeat"


def test_heartbeat_add_agent_version_reads_beat_root(monkeypatch, tmp_path: Path) -> None:
    config = _heartbeat_config(tmp_path)
    client = ElasticHeartbeatOpAMPClient(config.server_url or "", config)

    class FakeResponse:
        text = '{"beat":"heartbeat","version":"9.5.0"}'
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {"beat": "heartbeat", "version": "9.5.0"}

    monkeypatch.setattr("opamp_consumer.client_runtime_mixin.httpx.get", lambda *_args, **_kwargs: FakeResponse())

    client.add_agent_version(5066)

    assert client.data.agent_version == "9.5.0"
    assert client.data.agent_type_name == "Elastic Heartbeat"


def test_heartbeat_health_transform_populates_component(tmp_path: Path) -> None:
    config = _heartbeat_config(tmp_path)
    client = ElasticHeartbeatOpAMPClient(config.server_url or "", config)
    message = opamp_pb2.AgentToServer()

    client._health_from_metrics(message, '{"status":"ok"}')

    assert message.health.component_health_map["Elastic Heartbeat"].healthy is True
    assert message.health.component_health_map["Elastic Heartbeat"].status == "ok"


def test_heartbeat_supports_remote_config_capabilities(tmp_path: Path) -> None:
    config = _heartbeat_config(tmp_path)
    client = ElasticHeartbeatOpAMPClient(config.server_url or "", config)

    supported = client.get_supported_capabilities()

    assert "AcceptsRemoteConfig" in supported
    assert "ReportsEffectiveConfig" in supported


def test_heartbeat_config_test_uses_beat_test_config_command(monkeypatch, tmp_path: Path) -> None:
    config = _heartbeat_config(tmp_path)
    client = ElasticHeartbeatOpAMPClient(config.server_url or "", config)
    lifecycle = ElasticHeartbeatLifecycle(client)
    calls: list[dict[str, object]] = []

    def fake_run(command, cwd=None, text=False, capture_output=False, timeout=None, check=True, **_kwargs):
        calls.append(
            {
                "command": list(command),
                "cwd": cwd,
                "text": text,
                "capture_output": capture_output,
                "timeout": timeout,
                "check": check,
            }
        )
        return subprocess.CompletedProcess(command, 0, stdout="Config OK", stderr="")

    monkeypatch.setattr(
        "opamp_consumer.elastic_heartbeat.client.shutil.which",
        lambda executable, path=None: "/usr/local/bin/heartbeat"
        if executable == "heartbeat"
        else None,
    )
    monkeypatch.setattr("opamp_consumer.elastic_heartbeat.client.subprocess.run", fake_run)

    result = lifecycle.test_config()

    assert result.returncode == 0
    assert calls == [
        {
            "command": [
                "/usr/local/bin/heartbeat",
                "test",
                "config",
                "-c",
                str(tmp_path / "heartbeat.yml"),
            ],
            "cwd": str(tmp_path),
            "text": True,
            "capture_output": True,
            "timeout": 3.0,
            "check": False,
        }
    ]
