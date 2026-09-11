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

"""Tests for dynamic OpAMP consumer plugin loading."""

# ruff: noqa: S101

from __future__ import annotations

import json
import logging
import sys
import types
from pathlib import Path

import pytest

from opamp_consumer.config import ConsumerConfig
from opamp_consumer.plugin_loader import (
    _load_builtin_consumer_plugins,
    build_consumer_plugin_registry,
    load_consumer_plugin,
)


def test_unknown_service_type_reports_supported_plugins(monkeypatch, caplog) -> None:
    """Unknown services should fail with the built-in plugin registry listed."""
    monkeypatch.setattr(
        "opamp_consumer.plugin_loader._entry_points_for_group",
        lambda: [],
    )
    config = ConsumerConfig(service_type="custom_agent")
    caplog.set_level(logging.ERROR, logger="opamp_consumer.plugin_loader")

    registry = build_consumer_plugin_registry(config)

    assert sorted(registry) == [
        "elastic_agent",
        "elastic_heartbeat",
        "fluentbit",
        "fluentd",
        "simulator",
        "vector",
    ]
    with pytest.raises(
        ValueError,
        match=(
            "unsupported consumer.service_type 'custom_agent'; "
            "configured/installed plugins: elastic_agent, elastic_heartbeat, "
            "fluentbit, fluentd, simulator, vector"
        ),
    ):
        load_consumer_plugin(config)
    assert (
        "failed to load consumer plugin service_type=custom_agent; "
        "configured/installed plugins: elastic_agent, elastic_heartbeat, "
        "fluentbit, fluentd, simulator, vector"
    ) in caplog.text


def test_one_configured_plugin_builds_single_plugin_registry(monkeypatch) -> None:
    """One configured plugin should be the only available registry entry."""
    monkeypatch.setattr(
        "opamp_consumer.plugin_loader._entry_points_for_group",
        lambda: [],
    )
    config = ConsumerConfig(
        service_type="custom_agent",
        consumer_plugins=[
            {
                "service_type": "custom_agent",
                "entry_point": "tests_fake_consumer_plugin:main",
            }
        ],
    )

    registry = build_consumer_plugin_registry(config)

    assert sorted(registry) == [
        "custom_agent",
        "elastic_agent",
        "elastic_heartbeat",
        "fluentbit",
        "fluentd",
        "simulator",
        "vector",
    ]
    assert registry["custom_agent"].entry_point == "tests_fake_consumer_plugin:main"


def test_all_builtin_plugin_config_builds_full_registry(monkeypatch) -> None:
    """All consumer plugin definitions should coexist in the registry."""
    monkeypatch.setattr(
        "opamp_consumer.plugin_loader._entry_points_for_group",
        lambda: [],
    )
    config = ConsumerConfig(
        service_type="fluentbit",
        consumer_plugins=[
            {
                "service_type": "fluentbit",
                "entry_point": "opamp_consumer.fluentbit.client:main",
            },
            {
                "service_type": "fluentd",
                "entry_point": "opamp_consumer.fluentd.client:main",
            },
            {
                "service_type": "elastic_agent",
                "entry_point": "opamp_consumer.elastic_agent.client:main",
            },
            {
                "service_type": "elastic_heartbeat",
                "entry_point": "opamp_consumer.elastic_heartbeat.client:main",
            },
            {
                "service_type": "simulator",
                "entry_point": "opamp_consumer.simulator.client:main",
            },
            {
                "service_type": "vector",
                "entry_point": "opamp_consumer.vector.client:main",
            },
        ],
    )

    registry = build_consumer_plugin_registry(config)

    assert sorted(registry) == [
        "elastic_agent",
        "elastic_heartbeat",
        "fluentbit",
        "fluentd",
        "simulator",
        "vector",
    ]
    assert registry["fluentbit"].entry_point == "opamp_consumer.fluentbit.client:main"
    assert registry["fluentd"].entry_point == "opamp_consumer.fluentd.client:main"
    assert (
        registry["elastic_agent"].entry_point
        == "opamp_consumer.elastic_agent.client:main"
    )
    assert (
        registry["elastic_heartbeat"].entry_point
        == "opamp_consumer.elastic_heartbeat.client:main"
    )
    assert registry["simulator"].entry_point == "opamp_consumer.simulator.client:main"
    assert registry["vector"].entry_point == "opamp_consumer.vector.client:main"


def test_builtin_plugins_load_from_config_file(tmp_path: Path) -> None:
    config_path = tmp_path / "builtin_plugins.json"
    config_path.write_text(
        json.dumps(
            {
                "plugins": [
                    {
                        "service_type": "Example_Agent",
                        "entry_point": "example_agent.client:main",
                    },
                    {
                        "service_type": "disabled_agent",
                        "entry_point": "disabled_agent.client:main",
                        "enabled": False,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    plugins = _load_builtin_consumer_plugins(config_path)

    assert plugins == (
        {
            "service_type": "example_agent",
            "entry_point": "example_agent.client:main",
            "enabled": True,
        },
        {
            "service_type": "disabled_agent",
            "entry_point": "disabled_agent.client:main",
            "enabled": False,
        },
    )


def test_disabled_builtin_plugin_is_not_added_to_registry(monkeypatch) -> None:
    monkeypatch.setattr(
        "opamp_consumer.plugin_loader._entry_points_for_group",
        lambda: [],
    )
    monkeypatch.setattr(
        "opamp_consumer.plugin_loader.BUILTIN_CONSUMER_PLUGINS",
        (
            {
                "service_type": "enabled_agent",
                "entry_point": "enabled_agent.client:main",
                "enabled": True,
            },
            {
                "service_type": "disabled_agent",
                "entry_point": "disabled_agent.client:main",
                "enabled": False,
            },
        ),
    )

    registry = build_consumer_plugin_registry(ConsumerConfig(service_type="enabled_agent"))

    assert sorted(registry) == ["enabled_agent"]


def test_load_consumer_plugin_uses_configured_entry_point(monkeypatch, caplog) -> None:
    """Configured plugins should route without hard-coded imports."""
    module = types.ModuleType("tests_fake_consumer_plugin")
    calls: list[str] = []

    def _main() -> None:
        calls.append("called")

    setattr(module, "main", _main)
    monkeypatch.setitem(sys.modules, module.__name__, module)

    config = ConsumerConfig(
        service_type="custom_agent",
        consumer_plugins=[
            {
                "service_type": "custom_agent",
                "entry_point": "tests_fake_consumer_plugin:main",
            }
        ],
    )
    caplog.set_level(logging.INFO, logger="opamp_consumer.plugin_loader")

    plugin_main = load_consumer_plugin(config)
    plugin_main()

    assert calls == ["called"]
    assert (
        "loaded consumer plugin service_type=custom_agent "
        "entry_point=tests_fake_consumer_plugin:main"
    ) in caplog.text


def test_failed_configured_plugin_load_is_logged_as_error(monkeypatch, caplog) -> None:
    """Import/load failures should be logged as errors with plugin identity."""
    monkeypatch.setattr(
        "opamp_consumer.plugin_loader._entry_points_for_group",
        lambda: [],
    )
    config = ConsumerConfig(
        service_type="broken_agent",
        consumer_plugins=[
            {
                "service_type": "broken_agent",
                "entry_point": "missing_consumer_plugin:main",
            }
        ],
    )
    caplog.set_level(logging.ERROR, logger="opamp_consumer.plugin_loader")

    with pytest.raises(ModuleNotFoundError):
        load_consumer_plugin(config)

    assert (
        "failed to load consumer plugin service_type=broken_agent "
        "entry_point=missing_consumer_plugin:main"
    ) in caplog.text


def test_disabled_config_plugin_removes_installed_entry_point(monkeypatch) -> None:
    """Disabled config definitions should suppress matching discovered plugins."""
    module = types.ModuleType("tests_disabled_consumer_plugin")

    def _main() -> None:
        raise AssertionError("disabled plugin should not load")

    setattr(module, "main", _main)
    monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setattr(
        "opamp_consumer.plugin_loader._entry_points_for_group",
        lambda: [],
    )

    config = ConsumerConfig(
        service_type="disabled_agent",
        consumer_plugins=[
            {
                "service_type": "disabled_agent",
                "entry_point": "tests_disabled_consumer_plugin:main",
                "enabled": False,
            }
        ],
    )

    registry = build_consumer_plugin_registry(config)

    assert "disabled_agent" not in registry
    with pytest.raises(ValueError, match="unsupported consumer.service_type"):
        load_consumer_plugin(config)
