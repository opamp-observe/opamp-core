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

"""Tests for consumer startup banner logging."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import pytest

import opamp_consumer.client_bootstrap as client_bootstrap
import opamp_consumer.elastic_agent.client as elastic_agent_client
import opamp_consumer.elastic_heartbeat.client as elastic_heartbeat_client
import opamp_consumer.fluentd.client as fluentd_client
import opamp_consumer.simulator.client as simulator_client
from opamp_consumer.config import ConsumerConfig
from opamp_consumer.startup_banner import (
    build_consumer_startup_banner_lines,
    log_consumer_startup_banner,
)


def _banner_config(service_type: str) -> ConsumerConfig:
    """Return a startup banner test config for one service type."""
    return ConsumerConfig(
        server_url="http://localhost:8080",
        transport="http",
        service_type=service_type,
        process_tracking="observer",
        process_detection_regex=f"{service_type}-process",
        agent_config_path="agent.conf",
        agent_additional_params=[],
        heartbeat_frequency=10,
        consumer_plugins=[
            {
                "service_type": service_type,
                "entry_point": f"opamp_consumer.{service_type}.client:main",
            }
        ],
    )


def test_startup_banner_includes_mode_paths_and_plugin(caplog) -> None:
    """Banner should summarize mode, config locations, and selected plugin."""
    config = _banner_config("fluentbit")
    logger = logging.getLogger("startup-banner-test")
    caplog.set_level(logging.INFO, logger="startup-banner-test")

    log_consumer_startup_banner(
        logger=logger,
        config=config,
        runtime_name="consumer",
        consumer_config_path="/tmp/opamp/consumer.json",
    )

    assert "OpAMP consumer startup" in caplog.text
    assert "mode: observer" in caplog.text
    assert "service_type: fluentbit" in caplog.text
    assert "plugin_entry_point: opamp_consumer.fluentbit.client:main" in caplog.text
    assert "consumer_config_path: /tmp/opamp/consumer.json" in caplog.text
    expected_agent_path = (
        Path("/tmp/opamp/consumer.json").resolve().parent / "agent.conf"
    ).resolve()
    assert f"agent_config_path: {expected_agent_path}" in caplog.text
    assert "server_url: http://localhost:8080" in caplog.text
    assert "transport: http" in caplog.text


def test_startup_banner_resolves_windows_relative_agent_config() -> None:
    """Windows config paths should keep Windows path formatting."""
    lines = build_consumer_startup_banner_lines(
        config=_banner_config("elastic_agent"),
        runtime_name="consumer-elastic-agent",
        consumer_config_path=r"D:\dev\opamp\tests\logstash\consumer.json",
    )

    assert (
        r"agent_config_path: D:\dev\opamp\tests\logstash\agent.conf"
        in lines
    )


def _exercise_main_until_help(
    monkeypatch: pytest.MonkeyPatch,
    *,
    module: Any,
    service_type: str,
    runtime_name: str,
) -> dict[str, object]:
    """Run a plugin main flow until config-help exit and capture banner details."""
    args = argparse.Namespace(config_path="consumer/opamp.json", help=True)
    config = _banner_config(service_type)
    captured: dict[str, object] = {}

    class _Parser:
        def parse_args(self) -> argparse.Namespace:
            return args

    monkeypatch.setattr(module, "build_common_cli_parser", lambda: _Parser())
    monkeypatch.setattr(module, "maybe_print_cli_config", lambda *, args: False)
    monkeypatch.setattr(module, "load_config_from_cli_args", lambda _args: config)
    monkeypatch.setattr(
        module,
        "configure_logging_for_config",
        lambda _config: logging.getLogger(f"{service_type}-test"),
    )
    monkeypatch.setattr(
        module,
        "log_runtime_config_path",
        lambda **_kwargs: Path("/tmp/opamp/consumer.json"),
    )

    def _capture_banner(**kwargs) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(module, "log_consumer_startup_banner", _capture_banner)
    monkeypatch.setattr(module, "maybe_print_config_help", lambda **_kwargs: True)

    module.main()

    assert captured["config"] is config
    assert captured["runtime_name"] == runtime_name
    assert captured["consumer_config_path"] == Path("/tmp/opamp/consumer.json")
    return captured


def test_fluentd_startup_logs_banner(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fluentd startup should emit the common banner."""
    _exercise_main_until_help(
        monkeypatch,
        module=fluentd_client,
        service_type="fluentd",
        runtime_name="consumer",
    )


def test_simulator_startup_logs_banner(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulator startup should emit the common banner."""
    _exercise_main_until_help(
        monkeypatch,
        module=simulator_client,
        service_type="simulator",
        runtime_name="simulator",
    )


def test_elastic_agent_startup_logs_banner(monkeypatch: pytest.MonkeyPatch) -> None:
    """Elastic Agent startup should emit the common banner."""
    _exercise_main_until_help(
        monkeypatch,
        module=elastic_agent_client,
        service_type="elastic_agent",
        runtime_name="consumer-elastic-agent",
    )


def test_elastic_heartbeat_startup_logs_banner(monkeypatch: pytest.MonkeyPatch) -> None:
    """Elastic Heartbeat startup should emit the common banner."""
    _exercise_main_until_help(
        monkeypatch,
        module=elastic_heartbeat_client,
        service_type="elastic_heartbeat",
        runtime_name="consumer-elastic-heartbeat",
    )


def test_default_fluentbit_startup_logs_banner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The shared default bootstrap used by Fluent Bit should emit the banner."""
    args = argparse.Namespace(config_path="consumer/opamp.json", help=True)
    config = _banner_config("fluentbit")
    captured: dict[str, object] = {}

    class _Parser:
        def parse_args(self) -> argparse.Namespace:
            return args

    monkeypatch.setattr(
        client_bootstrap,
        "build_common_cli_parser",
        lambda: _Parser(),
    )
    monkeypatch.setattr(client_bootstrap, "maybe_print_cli_config", lambda *, args: False)
    monkeypatch.setattr(
        client_bootstrap,
        "load_config_from_cli_args",
        lambda _args: config,
    )
    monkeypatch.setattr(
        client_bootstrap,
        "configure_logging_for_config",
        lambda _config: logging.getLogger("fluentbit-test"),
    )
    monkeypatch.setattr(
        client_bootstrap,
        "log_runtime_config_path",
        lambda **_kwargs: Path("/tmp/opamp/consumer.json"),
    )

    def _capture_banner(**kwargs) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(
        client_bootstrap,
        "log_consumer_startup_banner",
        _capture_banner,
    )
    monkeypatch.setattr(
        client_bootstrap,
        "maybe_print_config_help",
        lambda **_kwargs: True,
    )

    client_bootstrap.run_default_client_main(
        client_class=object,
        config_parameters_payload_builder=lambda _config: {},
        load_agent_config_fn=lambda runtime_config: runtime_config,
        localhost_base="http://localhost",
    )

    assert captured["config"] is config
    assert captured["runtime_name"] == "consumer"
    assert captured["consumer_config_path"] == Path("/tmp/opamp/consumer.json")
