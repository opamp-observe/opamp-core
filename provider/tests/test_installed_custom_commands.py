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

"""External command registration, queueing, and authenticated result routing."""

from __future__ import annotations

import logging

import pytest

from opamp_provider import custom_commands
from opamp_provider.command_implementations.command_nullcommand import CommandNullCommand
from opamp_provider.command_queue import QueueCommandRequestError, queue_command_from_payload
from opamp_provider.custom_commands import (
    CustomCommandABC,
    LegacyCustomCommandAdapter,
    dispatch_result,
    queued_message,
)
from opamp_provider.proto import opamp_pb2
from opamp_provider.state import ClientStore

CAPABILITY = "org.example.scan"
COMMAND_ID = "network-security-verifier"


def test_legacy_adapter_preserves_user_parameter_schema() -> None:
    """Show a legacy command's editable parameters in installed-command metadata."""
    adapter = LegacyCustomCommandAdapter(CommandNullCommand)
    expected_schema = CommandNullCommand().get_user_parameter_schema()

    assert adapter.parameter_schema == expected_schema
    assert adapter.parameter_schema is not expected_schema
    assert adapter.parameter_schema[0] is not expected_schema[0]


def test_legacy_adapter_without_schema_returns_empty_list(monkeypatch) -> None:
    """Keep old command types that lack optional schema metadata usable."""
    monkeypatch.setattr(CommandNullCommand, "get_user_parameter_schema", None)

    assert LegacyCustomCommandAdapter(CommandNullCommand).parameter_schema == []


class ScanCommand(CustomCommandABC):
    """Test extension that records which authenticated agent returned a result."""

    received: list[tuple[str, bytes]] = []

    @property
    def command_id(self) -> str:
        """Select the test implementation by stable identifier."""
        return COMMAND_ID

    @property
    def capability(self) -> str:
        """Use one raw reverse-FQDN for request and result."""
        return CAPABILITY

    def validate(self, parameters: dict[str, object]) -> str:
        """Require a typed target and reject opaque wire fields."""
        if set(parameters) != {"target"} or not isinstance(parameters["target"], str):
            raise ValueError("target string is required")
        return parameters["target"]

    def build_message(self, agent_id: str, request: str) -> opamp_pb2.CustomMessage:
        """Build a request containing the validated target."""
        return opamp_pb2.CustomMessage(
            capability=CAPABILITY, type="request", data=request.encode("utf-8")
        )

    def handle_result(self, agent_id: str, message: opamp_pb2.CustomMessage) -> None:
        """Record result attribution from the provider's authenticated client record."""
        self.received.append((agent_id, message.data))


def test_registered_command_requires_agent_capability_and_routes_result(monkeypatch) -> None:
    """Only a reported capability can be queued and its result reaches its owner."""
    command = ScanCommand()
    command.received.clear()
    monkeypatch.setattr(custom_commands, "installed_commands", lambda: {COMMAND_ID: command})
    store = ClientStore()
    agent = opamp_pb2.AgentToServer(instance_uid=b"agent-id")
    agent.custom_capabilities.capabilities.append(CAPABILITY)
    store.upsert_from_agent_msg(agent)
    payload = {"command_id": COMMAND_ID, "parameters": {"target": "127.0.0.1"}}
    record = queue_command_from_payload(
        client_id=b"agent-id".hex(), payload=payload, store=store, max_events=10,
        command_builders={}, logger=logging.getLogger(__name__),
    )
    values = {pair["key"]: pair["value"] for pair in record.key_value_pairs}
    request = queued_message(values)
    assert (request.capability, request.type, request.data) == (
        CAPABILITY, "request", b"127.0.0.1"
    )
    dispatch_result(b"agent-id".hex(), opamp_pb2.CustomMessage(
        capability=CAPABILITY, type="result", data=b"complete"
    ))
    assert command.received == [(b"agent-id".hex(), b"complete")]


def test_identifier_request_rejects_unadvertised_and_raw_payload(monkeypatch) -> None:
    """A UI cannot choose an unregistered capability or submit wire data."""
    monkeypatch.setattr(custom_commands, "installed_commands", lambda: {COMMAND_ID: ScanCommand()})
    store = ClientStore()
    with pytest.raises(QueueCommandRequestError, match="not advertised"):
        queue_command_from_payload(
            client_id="missing", payload={"command_id": COMMAND_ID, "parameters": {"target": "x"}},
            store=store, max_events=10, command_builders={}, logger=logging.getLogger(__name__),
        )
    agent = opamp_pb2.AgentToServer(instance_uid=b"agent-id")
    agent.custom_capabilities.capabilities.append(CAPABILITY)
    store.upsert_from_agent_msg(agent)
    with pytest.raises(QueueCommandRequestError, match="target string"):
        queue_command_from_payload(
            client_id=b"agent-id".hex(),
            payload={"command_id": COMMAND_ID, "parameters": {"capability": CAPABILITY, "data": "raw"}},
            store=store, max_events=10, command_builders={}, logger=logging.getLogger(__name__),
        )


def test_entry_point_discovery_rejects_duplicate_command_ids(monkeypatch) -> None:
    """Installed registration refuses ambiguous identifiers before routing."""
    class EntryPoint:
        value = "scan:command"

        def __init__(self, name: str) -> None:
            self.name = name

        @staticmethod
        def load():
            return ScanCommand

    class EntryPoints:
        @staticmethod
        def select(*, group):
            assert group == "opamp_provider.custom_commands"
            return [EntryPoint("one"), EntryPoint("two")]

    monkeypatch.setattr(custom_commands.importlib.metadata, "entry_points", lambda: EntryPoints())
    custom_commands.installed_commands.cache_clear()
    try:
        with pytest.raises(ValueError, match="Duplicate custom command"):
            custom_commands.installed_commands()
    finally:
        custom_commands.installed_commands.cache_clear()


def test_result_callback_failure_is_isolated(monkeypatch, caplog) -> None:
    """A broken extension callback cannot interrupt provider transport handling."""
    command = ScanCommand()

    def fail(_agent_id: str, _message: opamp_pb2.CustomMessage) -> None:
        raise RuntimeError("callback failed")

    monkeypatch.setattr(command, "handle_result", fail)
    monkeypatch.setattr(custom_commands, "installed_commands", lambda: {COMMAND_ID: command})
    dispatch_result("authenticated-agent", opamp_pb2.CustomMessage(
        capability=CAPABILITY, type="result", data=b"result"
    ))
    assert "Custom command result callback failed" in caplog.text
