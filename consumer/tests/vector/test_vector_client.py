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

"""Tests for the Vector consumer plugin."""

# ruff: noqa: S101

from __future__ import annotations

import subprocess
from pathlib import Path

from opamp_consumer.client_observer_mixin import ClientObserverMixin
from opamp_consumer.config import ConsumerConfig
from opamp_consumer.config_metadata import (
    CONFIG_METADATA_KEY_AGENT_DESCRIPTION,
    CONFIG_METADATA_KEY_SERVICE_INSTANCE_ID,
)
from opamp_consumer.plugin_config import ConsumerPluginConfigContext
from opamp_consumer.proto import opamp_pb2
from opamp_consumer.vector import client as vector_module
from opamp_consumer.vector.client import (
    VALUE_AGENT_TYPE_VECTOR,
    VectorLifecycle,
    VectorOpAMPClient,
    load_vector_config,
    process_consumer_config,
)


def _write_vector_config(path: Path) -> None:
    path.write_text(
        "# agent_description: vector self monitor\n"
        "# config_version: 2026.09.10\n"
        "# service_instance_id: vector-demo-01\n"
        "# SCM_source_name: docs/vector-self-monitor\n"
        "api:\n"
        "  enabled: true\n"
        "  address: 0.0.0.0:8686\n"
        "sources:\n"
        "  vector_internal_metrics:\n"
        "    type: internal_metrics\n"
        "transforms:\n"
        "  as_logs:\n"
        "    type: metric_to_log\n"
        "    inputs: [vector_internal_metrics]\n"
        "sinks:\n"
        "  out:\n"
        "    type: console\n"
        "    inputs: [as_logs]\n"
        "    encoding:\n"
        "      codec: json\n",
        encoding="utf-8",
    )


def test_process_consumer_config_resolves_vector_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "opamp.json"
    config_path.write_text("{}\n", encoding="utf-8")
    context = ConsumerPluginConfigContext(
        service_type="vector",
        section_name="vector",
        raw_section={
            "executable_path": "bin/vector",
            "api_host": "127.0.0.1",
            "api_port": 8687,
            "status_timeout_seconds": 2,
        },
        consumer_raw={},
        config_path=config_path,
    )

    updates = process_consumer_config(context)

    assert updates["vector_executable_path"] == str((tmp_path / "bin" / "vector").resolve())
    assert updates["vector_api_host"] == "127.0.0.1"
    assert updates["vector_api_port"] == 8687
    assert updates["vector_status_timeout_seconds"] == 2.0


def test_process_consumer_config_supplies_vector_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "opamp.json"
    config_path.write_text("{}\n", encoding="utf-8")
    context = ConsumerPluginConfigContext(
        service_type="vector",
        section_name="vector",
        raw_section={},
        consumer_raw={},
        config_path=config_path,
    )

    updates = process_consumer_config(context)

    assert updates["vector_executable_path"] == "vector"
    assert updates["vector_api_host"] == "127.0.0.1"
    assert updates["vector_api_port"] == 8686
    assert updates["vector_status_timeout_seconds"] == 5.0


def test_load_vector_config_reads_api_and_metadata(tmp_path: Path) -> None:
    config_path = tmp_path / "vector.yaml"
    _write_vector_config(config_path)
    config = ConsumerConfig(
        server_url="http://localhost:8080",
        service_type="vector",
        agent_config_path=str(config_path),
        agent_additional_params=[],
        heartbeat_frequency=5,
        service_name="Vector",
        service_namespace="VectorNS",
    )

    loaded = load_vector_config(config)

    assert loaded.client_status_port == 8686
    assert loaded.agent_http_port == 8686
    assert loaded.agent_http_listen == "0.0.0.0"
    assert loaded.agent_http_server == "on"
    assert loaded.agent_description == "vector self monitor"
    assert loaded.config_version == "2026.09.10"
    assert loaded.service_instance_id == "vector-demo-01"
    assert "internal_metrics" in str(loaded.agent_config_text)


def test_vector_client_metadata_and_description(tmp_path: Path) -> None:
    config_path = tmp_path / "vector.yaml"
    _write_vector_config(config_path)
    config = ConsumerConfig(
        server_url="http://localhost:8080",
        service_type="vector",
        agent_config_path=str(config_path),
        agent_additional_params=[],
        heartbeat_frequency=5,
        service_name="Vector",
        service_namespace="VectorNS",
    )
    loaded = load_vector_config(config)
    instance = VectorOpAMPClient("http://localhost:8080", loaded)

    metadata = instance.get_config_metadata()
    description = instance.get_agent_description(b"\x01\x02")
    identifying = {
        item.key: item.value.string_value
        if item.value.WhichOneof("value") == "string_value"
        else ""
        for item in description.identifying_attributes
    }

    assert metadata.config_type == "Vector"
    assert metadata.SCM_source_name == "docs/vector-self-monitor"
    assert metadata.additional_metadata == {
        CONFIG_METADATA_KEY_AGENT_DESCRIPTION: "vector self monitor",
        CONFIG_METADATA_KEY_SERVICE_INSTANCE_ID: "vector-demo-01",
    }
    assert identifying["service.type"] == VALUE_AGENT_TYPE_VECTOR


def test_vector_health_from_ok_payload_marks_component_healthy(tmp_path: Path) -> None:
    config_path = tmp_path / "vector.yaml"
    _write_vector_config(config_path)
    config = load_vector_config(
        ConsumerConfig(
            server_url="http://localhost:8080",
            service_type="vector",
            agent_config_path=str(config_path),
            agent_additional_params=[],
            heartbeat_frequency=5,
        )
    )
    instance = VectorOpAMPClient("http://localhost:8080", config)
    message = opamp_pb2.AgentToServer()

    populated = instance._health_from_metrics(message, "ok")

    assert populated.health.component_health_map["health"].healthy is True
    assert populated.health.component_health_map["health"].status == "ok"


def test_vector_lifecycle_uses_configured_executable(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "vector.yaml"
    _write_vector_config(config_path)
    config = ConsumerConfig(
        server_url="http://localhost:8080",
        service_type="vector",
        agent_config_path=str(config_path),
        agent_additional_params=["--quiet"],
        heartbeat_frequency=5,
    )
    config.vector_executable_path = "/opt/vector/bin/vector"
    config = load_vector_config(config)
    instance = VectorOpAMPClient("http://localhost:8080", config)
    lifecycle = VectorLifecycle(instance)
    launched: list[list[str]] = []

    class FakeProcess:
        def terminate(self) -> None:
            return None

        def wait(self, timeout=None) -> int:
            return 0

    def fake_popen(command):
        launched.append(list(command))
        return FakeProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    assert lifecycle.launch_agent_process() is True

    assert launched == [["/opt/vector/bin/vector", "--quiet", "--config", str(config_path)]]


def test_vector_lifecycle_honors_observer_mode(tmp_path: Path) -> None:
    config_path = tmp_path / "vector.yaml"
    _write_vector_config(config_path)
    config = load_vector_config(
        ConsumerConfig(
            server_url="http://localhost:8080",
            service_type="vector",
            agent_config_path=str(config_path),
            agent_additional_params=[],
            heartbeat_frequency=5,
            process_tracking="observer",
            process_detection_regex="vector",
        )
    )
    instance = VectorOpAMPClient("http://localhost:8080", config)

    assert isinstance(instance._create_runtime_process_lifecycle(), ClientObserverMixin)


def test_vector_add_agent_version_reads_binary_output(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "vector.yaml"
    _write_vector_config(config_path)
    config = ConsumerConfig(
        server_url="http://localhost:8080",
        service_type="vector",
        agent_config_path=str(config_path),
        agent_additional_params=[],
        heartbeat_frequency=5,
    )
    config.vector_executable_path = "vector"
    config = load_vector_config(config)
    instance = VectorOpAMPClient("http://localhost:8080", config)

    def fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(["vector", "--version"], 0, stdout="vector 0.58.0\n")

    monkeypatch.setattr(vector_module.shutil, "which", lambda _name: "/usr/bin/vector")
    monkeypatch.setattr(subprocess, "run", fake_run)

    instance.add_agent_version(8686)

    assert instance.data.agent_version == "vector 0.58.0"
