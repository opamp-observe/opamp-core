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

"""Tests for the consumer deployment bootstrap installer behavior."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest


def _load_bootstrap_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = (
        repo_root
        / "tests"
        / "test-containers"
        / "opamp-consumer-deployment"
        / "scripts"
        / "bootstrap.py"
    )
    spec = importlib.util.spec_from_file_location(
        "opamp_consumer_deployment_bootstrap",
        module_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_consumer_config_includes_builtin_plugins() -> None:
    """Generated installer config should be usable without wheel metadata fallback."""
    bootstrap = _load_bootstrap_module()

    config = bootstrap._build_default_consumer_config(  # type: ignore[attr-defined]
        deployment="fluentbit",
        agent_config_path=Path("/tmp/fluent-bit.yaml"),
        transport="http",
        http_url="http://provider:8080",
        websocket_url="ws://provider:4320",
    )

    plugins = config["consumer"]["plugins"]
    assert plugins == [
        {
            "service_type": "fluentbit",
            "entry_point": "opamp_consumer.fluentbit.client:main",
            "enabled": True,
        },
        {
            "service_type": "fluentd",
            "entry_point": "opamp_consumer.fluentd.client:main",
            "enabled": True,
        },
        {
            "service_type": "elastic_agent",
            "entry_point": "opamp_consumer.elastic_agent.client:main",
            "enabled": True,
        },
        {
            "service_type": "elastic_heartbeat",
            "entry_point": "opamp_consumer.elastic_heartbeat.client:main",
            "enabled": True,
        },
        {
            "service_type": "simulator",
            "entry_point": "opamp_consumer.simulator.client:main",
            "enabled": True,
        },
        {
            "service_type": "vector",
            "entry_point": "opamp_consumer.vector.client:main",
            "enabled": True,
        },
    ]


def test_verify_installed_consumer_plugins_rejects_missing_builtin() -> None:
    """Fail verification before launch when plugin entry points are missing."""
    bootstrap = _load_bootstrap_module()

    bootstrap._installed_consumer_plugin_entry_points = lambda: {  # type: ignore[attr-defined]
        "fluentbit": "opamp_consumer.fluentbit.client:main",
    }

    with pytest.raises(
        bootstrap.ConfigError,
        match="missing expected plugin entry points",
    ):
        bootstrap._verify_installed_consumer_plugins(  # type: ignore[attr-defined]
            deployment="fluentbit"
        )


def test_resolve_wheel_path_selects_latest_wheel_from_directory(tmp_path: Path) -> None:
    """Regression env files can point WHEEL_PATH at a generated wheel directory."""
    bootstrap = _load_bootstrap_module()
    older = tmp_path / "opamp_consumer-0.4.0-py3-none-any.whl"
    newer = tmp_path / "opamp_consumer-0.4.1-py3-none-any.whl"
    older.write_bytes(b"older")
    newer.write_bytes(b"newer")
    os.utime(older, (1, 1))
    os.utime(newer, (2, 2))

    assert bootstrap._resolve_wheel_path(str(tmp_path)) == newer  # type: ignore[attr-defined]


def test_stage_consumer_config_applies_identity_and_simulator_responses(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Runtime staging should apply stable identity and simulator response paths."""
    bootstrap = _load_bootstrap_module()
    source_path = tmp_path / "source.json"
    source_path.write_text(
        json.dumps({"consumer": {"server_url": "http://old-provider:8080"}}),
        encoding="utf-8",
    )
    staged_dir = tmp_path / "staged"
    staged_dir.mkdir()
    monkeypatch.setattr(bootstrap, "STAGED_CONFIG_DIR", staged_dir)

    staged_path = bootstrap._stage_consumer_config(  # type: ignore[attr-defined]
        deployment="simulator",
        cfg={
            "CONSUMER_CONFIG_PATH": str(source_path),
            "SERVER_URL": "http://provider:8080",
            "SERVICE_INSTANCE_ID_OVERRIDE": "shutdown-e2e-simulator",
            "SIMULATOR_RESPONSES_PATH": "/config/simulator-responses.json",
        },
        agent_config_path=tmp_path / "simulator-agent.yaml",
        transport="http",
        http_url="http://fallback:8080",
        websocket_url="ws://fallback:4320",
    )

    consumer = json.loads(staged_path.read_text(encoding="utf-8"))["consumer"]
    assert consumer["service_instance_id"] == "shutdown-e2e-simulator"
    assert consumer["simulator_responses_path"] == "/config/simulator-responses.json"
    assert consumer["server_url"] == "http://provider:8080"


def test_main_smoke_only_stops_after_staging(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Smoke-only regression mode should not launch long-running processes."""
    bootstrap = _load_bootstrap_module()
    wheel_path = tmp_path / "opamp_consumer-0.4.1-py3-none-any.whl"
    wheel_path.write_bytes(b"fake wheel")
    output_dir = tmp_path / "output"
    config_path = tmp_path / "test-container.env"
    config_path.write_text(
        "\n".join(
            [
                "DEPLOYMENT_TYPE=fluentbit",
                "AGENT_VERSION=5.0.3",
                f"WHEEL_PATH={wheel_path}",
                f"OUTPUT_HOST_DIR={output_dir}",
                "SMOKE_ONLY=true",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("TEST_CONTAINER_CONFIG", str(config_path))
    monkeypatch.setattr(bootstrap, "RUNTIME_ROOT", tmp_path / "runtime")
    monkeypatch.setattr(bootstrap, "STAGED_CONFIG_DIR", tmp_path / "runtime" / "config")
    monkeypatch.setattr(bootstrap, "DOWNLOADS_DIR", tmp_path / "runtime" / "downloads")
    monkeypatch.setattr(
        bootstrap,
        "ELK_DOWNLOADS_DIR",
        tmp_path / "runtime" / "downloads" / "elk",
    )
    monkeypatch.setattr(
        bootstrap,
        "LOG_GENERATOR_DOWNLOADS_DIR",
        tmp_path / "runtime" / "downloads" / "log-generator",
    )

    events: list[str] = []
    monkeypatch.setattr(
        bootstrap,
        "_install_consumer_wheel",
        lambda _wheel_path: events.append("install-consumer-wheel"),
    )
    monkeypatch.setattr(
        bootstrap,
        "_install_consumer_plugin_packages",
        lambda _cfg: events.append("install-consumer-plugins"),
    )
    monkeypatch.setattr(
        bootstrap,
        "_verify_installed_consumer_plugins",
        lambda *, deployment: events.append(f"verify-plugins:{deployment}"),
    )
    monkeypatch.setattr(
        bootstrap,
        "_download_elk_stack_components",
        lambda _cfg, _agent_version: events.append("download-elk"),
    )
    monkeypatch.setattr(
        bootstrap,
        "_download_log_generator",
        lambda _cfg: events.append("download-log-generator"),
    )
    monkeypatch.setattr(
        bootstrap,
        "_install_fluentbit",
        lambda _agent_version, _cfg: events.append("install-agent"),
    )
    monkeypatch.setattr(
        bootstrap,
        "_stage_agent_config",
        lambda **_kwargs: events.append("stage-agent") or tmp_path / "fluent-bit.yaml",
    )
    monkeypatch.setattr(
        bootstrap,
        "_stage_consumer_config",
        lambda **_kwargs: events.append("stage-consumer") or tmp_path / "opamp.json",
    )
    monkeypatch.setattr(
        bootstrap,
        "_launch_consumer",
        lambda *_args: events.append("launch-consumer"),
    )
    monkeypatch.setattr(
        bootstrap,
        "_launch_agent_only",
        lambda *_args: events.append("launch-agent-only"),
    )

    assert bootstrap.main() == 0
    assert events == [
        "install-consumer-wheel",
        "install-consumer-plugins",
        "verify-plugins:fluentbit",
        "download-elk",
        "download-log-generator",
        "install-agent",
        "stage-agent",
        "stage-consumer",
    ]


def test_main_installs_base_then_external_plugins_then_verifies(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Bootstrap install order should make external plugins see the base consumer."""
    bootstrap = _load_bootstrap_module()
    wheel_path = tmp_path / "opamp_consumer-0.4.1-py3-none-any.whl"
    wheel_path.write_bytes(b"fake wheel")
    output_dir = tmp_path / "output"
    config_path = tmp_path / "test-container.env"
    config_path.write_text(
        "\n".join(
            [
                "DEPLOYMENT_TYPE=fluentbit",
                "AGENT_VERSION=5.0.3",
                f"WHEEL_PATH={wheel_path}",
                "CONSUMER_PLUGIN_INSTALLS=/host-assets/dist/custom_plugin.whl",
                f"OUTPUT_HOST_DIR={output_dir}",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("TEST_CONTAINER_CONFIG", str(config_path))
    monkeypatch.setattr(bootstrap, "RUNTIME_ROOT", tmp_path / "runtime")
    monkeypatch.setattr(bootstrap, "STAGED_CONFIG_DIR", tmp_path / "runtime" / "config")
    monkeypatch.setattr(bootstrap, "DOWNLOADS_DIR", tmp_path / "runtime" / "downloads")
    monkeypatch.setattr(
        bootstrap,
        "ELK_DOWNLOADS_DIR",
        tmp_path / "runtime" / "downloads" / "elk",
    )
    monkeypatch.setattr(
        bootstrap,
        "LOG_GENERATOR_DOWNLOADS_DIR",
        tmp_path / "runtime" / "downloads" / "log-generator",
    )

    events: list[str] = []
    monkeypatch.setattr(
        bootstrap,
        "_install_consumer_wheel",
        lambda _wheel_path: events.append("install-consumer-wheel"),
    )
    monkeypatch.setattr(
        bootstrap,
        "_install_consumer_plugin_packages",
        lambda _cfg: events.append("install-consumer-plugins"),
    )
    monkeypatch.setattr(
        bootstrap,
        "_verify_installed_consumer_plugins",
        lambda *, deployment: events.append(f"verify-plugins:{deployment}"),
    )
    monkeypatch.setattr(
        bootstrap,
        "_download_elk_stack_components",
        lambda _cfg, _agent_version: events.append("download-elk"),
    )
    monkeypatch.setattr(
        bootstrap,
        "_download_log_generator",
        lambda _cfg: events.append("download-log-generator"),
    )
    monkeypatch.setattr(
        bootstrap,
        "_install_fluentbit",
        lambda _agent_version, _cfg: events.append("install-agent"),
    )
    monkeypatch.setattr(
        bootstrap,
        "_stage_agent_config",
        lambda **_kwargs: events.append("stage-agent") or tmp_path / "fluent-bit.yaml",
    )
    monkeypatch.setattr(
        bootstrap,
        "_stage_consumer_config",
        lambda **_kwargs: events.append("stage-consumer") or tmp_path / "opamp.json",
    )
    monkeypatch.setattr(
        bootstrap,
        "_launch_consumer",
        lambda *_args: events.append("launch-consumer"),
    )

    assert bootstrap.main() == 0
    assert events == [
        "install-consumer-wheel",
        "install-consumer-plugins",
        "verify-plugins:fluentbit",
        "download-elk",
        "download-log-generator",
        "install-agent",
        "stage-agent",
        "stage-consumer",
        "launch-consumer",
    ]
