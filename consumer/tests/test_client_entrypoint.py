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

"""Tests for service-type aware consumer entrypoint routing."""

from __future__ import annotations

import argparse

import pytest

from opamp_consumer.client import main as entrypoint_main
from opamp_consumer.config import ConsumerConfig


def test_entrypoint_routes_to_simulator(monkeypatch) -> None:
    """Top-level consumer entrypoint should route simulator service type correctly."""
    import opamp_consumer.client as entry_module
    import opamp_consumer.simulator.client as simulator_module

    monkeypatch.setattr(
        entry_module,
        "_parse_args_for_routing",
        lambda: argparse.Namespace(),
    )
    monkeypatch.setattr(
        entry_module,
        "load_config_from_cli_args",
        lambda _args: ConsumerConfig(
            service_type="simulator",
            simulator_responses_path="tests/fixtures/simulator-responses.json",
        ),
    )

    calls: list[str] = []
    monkeypatch.setattr(simulator_module, "main", lambda: calls.append("simulator"))

    entrypoint_main()

    assert calls == ["simulator"]


def test_entrypoint_rejects_unknown_service_type(monkeypatch) -> None:
    """Top-level consumer entrypoint should fail fast for unknown service type."""
    import opamp_consumer.client as entry_module

    monkeypatch.setattr(
        entry_module,
        "_parse_args_for_routing",
        lambda: argparse.Namespace(),
    )
    monkeypatch.setattr(
        entry_module,
        "load_config_from_cli_args",
        lambda _args: ConsumerConfig(service_type="mystery"),
    )

    with pytest.raises(ValueError, match="unsupported consumer.service_type"):
        entrypoint_main()


def test_entrypoint_cli_config_exits_before_routing(monkeypatch) -> None:
    """Top-level entrypoint should honor cli-config before service routing."""
    import opamp_consumer.client as entry_module

    args = argparse.Namespace(cli_config=True, config_path="consumer/opamp.json")
    monkeypatch.setattr(
        entry_module,
        "_parse_args_for_routing",
        lambda: args,
    )
    monkeypatch.setattr(
        entry_module,
        "maybe_print_cli_config",
        lambda *, args: args is not None,
    )
    monkeypatch.setattr(
        entry_module,
        "load_config_from_cli_args",
        lambda _args: (_ for _ in ()).throw(
            AssertionError("config should not be loaded when --cli-config is used")
        ),
    )

    entrypoint_main()
