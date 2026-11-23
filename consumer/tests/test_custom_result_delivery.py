# ruff: noqa: S101
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

"""Contract tests for completed custom results on normal OpAMP exchanges."""

from __future__ import annotations

import asyncio
import threading

import pytest

from opamp_consumer.custom_handlers.handler_interface import CustomMessageHandlerInterface
from opamp_consumer.custom_handlers.registry import build_factory_lookup
from opamp_consumer.custom_handlers.result_queue import CustomResultQueue
from opamp_consumer.exceptions import AgentException
from opamp_consumer.fluentbit import client
from opamp_consumer.proto import opamp_pb2

CAPABILITY = "org.example.scan"


class _ScanHandler(CustomMessageHandlerInterface):
    """Test handler whose blocking operation is controlled without sleeps."""

    started = threading.Event()
    release = threading.Event()

    def set_client_data(self, data) -> None:
        """Accept client data from the factory."""

    def get_fqdn(self) -> str:
        """Return the raw capability name."""
        return CAPABILITY

    def handle_message(self, message: str, message_type: str) -> None:
        """Accept the request envelope before executing its action."""

    def execute_action(self, action: str, opamp_client) -> opamp_pb2.CustomMessage:
        """Hold the worker until the test permits completion."""
        self.started.set()
        self.release.wait(timeout=2)
        return opamp_pb2.CustomMessage(capability=CAPABILITY, type="result", data=b"done")


def test_result_queue_copies_orders_and_bounds_results() -> None:
    """A handler cannot mutate a queued result and cannot overflow the backlog."""
    queue = CustomResultQueue(limit=1)
    original = opamp_pb2.CustomMessage(capability="org.example.scan", type="result", data=b"one")
    queue.enqueue(original)
    original.data = b"changed"
    assert queue.peek().data == b"one"
    try:
        queue.enqueue(original)
    except OverflowError:
        pass
    else:
        raise AssertionError("full queue accepted another result")
    queue.acknowledge()
    assert queue.peek() is None


def test_http_retry_keeps_result_and_uses_normal_message_builder() -> None:
    """The next scheduled send retries a failed result with UID and sequence number."""
    async def scenario() -> None:
        instance = client.OpAMPClient("http://localhost")
        instance._custom_result_queue.enqueue(
            opamp_pb2.CustomMessage(capability="org.example.scan", type="result", data=b"ok")
        )
        attempts: list[opamp_pb2.AgentToServer] = []

        async def send_http(message: opamp_pb2.AgentToServer) -> opamp_pb2.ServerToAgent:
            copy = opamp_pb2.AgentToServer()
            copy.CopyFrom(message)
            attempts.append(copy)
            if len(attempts) == 1:
                raise OSError("offline")
            return opamp_pb2.ServerToAgent(instance_uid=instance.data.uid_instance)

        instance.send_http = send_http
        assert await instance.send() is None
        assert instance._custom_result_queue.peek() is not None
        assert await instance.send() is not None
        assert instance._custom_result_queue.peek() is None
        assert [message.custom_message.data for message in attempts] == [b"ok", b"ok"]
        assert all(message.instance_uid == instance.data.uid_instance for message in attempts)
        assert attempts[1].sequence_num > attempts[0].sequence_num

    asyncio.run(scenario())


def test_async_mode_keeps_event_loop_responsive() -> None:
    """Trusted async configuration runs a blocking scan away from the event loop."""
    async def scenario() -> None:
        _ScanHandler.started.clear()
        _ScanHandler.release.clear()
        instance = client.OpAMPClient("http://localhost")
        instance.config.allow_custom_capabilities = True
        instance.config.custom_handler_execution_modes = {CAPABILITY: "async"}
        instance._custom_handler_lookup = {CAPABILITY: _ScanHandler}
        instance.handle_custom_capabilities(opamp_pb2.CustomCapabilities(capabilities=[CAPABILITY]))
        message = opamp_pb2.CustomMessage(capability=CAPABILITY, type="request", data=b"{}")
        instance.handle_custom_message(message)
        assert await asyncio.to_thread(_ScanHandler.started.wait, 1)
        assert instance._custom_result_queue.peek() is None
        _ScanHandler.release.set()
        await asyncio.gather(*instance._custom_handler_tasks)
        assert instance._custom_result_queue.peek().data == b"done"

    asyncio.run(scenario())


def test_installed_entry_point_is_discovered_without_source_folder(monkeypatch, tmp_path) -> None:
    """An installed wheel handler is available even if the source folder is absent."""
    class EntryPoint:
        name = "scan"
        value = "scan:handler"

        @staticmethod
        def load():
            return _ScanHandler

    class EntryPoints:
        @staticmethod
        def select(*, group):
            assert group == "opamp_consumer.custom_handlers"
            return [EntryPoint()]

    monkeypatch.setattr(
        "opamp_consumer.custom_handlers.registry.importlib.metadata.entry_points",
        lambda: EntryPoints(),
    )
    lookup = build_factory_lookup(tmp_path / "absent", allow_custom_capabilities=True)
    assert lookup[CAPABILITY] is _ScanHandler


def test_duplicate_installed_handler_capability_is_rejected(monkeypatch, tmp_path) -> None:
    """Two installed registrations cannot claim the same reverse-FQDN."""
    class EntryPoint:
        value = "scan:handler"

        def __init__(self, name: str) -> None:
            self.name = name

        @staticmethod
        def load():
            return _ScanHandler

    class EntryPoints:
        @staticmethod
        def select(*, group):
            assert group == "opamp_consumer.custom_handlers"
            return [EntryPoint("one"), EntryPoint("two")]

    monkeypatch.setattr(
        "opamp_consumer.custom_handlers.registry.importlib.metadata.entry_points",
        lambda: EntryPoints(),
    )
    with pytest.raises(ValueError, match="Duplicate or empty"):
        build_factory_lookup(tmp_path / "absent", allow_custom_capabilities=True)


def test_chatops_failure_is_queued_without_direct_transport_send(monkeypatch) -> None:
    """A legacy handler's failure takes the normal result queue path."""
    from opamp_consumer.custom_handlers.chatops_command import ChatOpsCommand

    monkeypatch.setattr(
        "opamp_consumer.custom_handlers.chatops_command.httpx.post",
        lambda *_args, **_kwargs: type("Response", (), {"status_code": 500, "text": "failed"})(),
    )
    instance = client.OpAMPClient("http://localhost")
    instance.config.allow_custom_capabilities = True
    capability = ChatOpsCommand().get_fqdn()
    instance._custom_handler_lookup = {capability: ChatOpsCommand}
    instance.handle_custom_capabilities(opamp_pb2.CustomCapabilities(capabilities=[capability]))
    message = opamp_pb2.CustomMessage(
        capability=capability, type="request", data=b'{"action":"run","tag":"events"}'
    )
    instance.handle_custom_message(message)
    result = instance._custom_result_queue.peek()
    assert result is not None
    assert result.capability == capability
    assert result.type == "failure"


def test_server_capability_agreement_blocks_unadvertised_requests() -> None:
    """A provider cannot request a capability it has not declared."""
    instance = client.OpAMPClient("http://localhost")
    instance.config.allow_custom_capabilities = True
    instance._custom_handler_lookup = {CAPABILITY: _ScanHandler}
    instance.handle_custom_capabilities(opamp_pb2.CustomCapabilities())
    with pytest.raises(AgentException, match="did not advertise"):
        instance.handle_custom_message(opamp_pb2.CustomMessage(
            capability=CAPABILITY, type="request", data=b"{}"
        ))


def test_websocket_completion_sends_ready_results_in_order() -> None:
    """Completed results wake an immediate exchange and drain in queue order."""
    async def scenario() -> None:
        instance = client.OpAMPClient("http://localhost")
        instance.config.transport = "websocket"
        observed: list[bytes] = []

        async def send_websocket(message: opamp_pb2.AgentToServer) -> opamp_pb2.ServerToAgent:
            observed.append(message.custom_message.data)
            return opamp_pb2.ServerToAgent(instance_uid=instance.data.uid_instance)

        instance.send_websocket = send_websocket
        instance._accept_custom_handler_result(opamp_pb2.CustomMessage(
            capability=CAPABILITY, type="result", data=b"first"
        ))
        instance._accept_custom_handler_result(opamp_pb2.CustomMessage(
            capability=CAPABILITY, type="result", data=b"second"
        ))
        await instance._custom_result_send_task
        assert observed == [b"first", b"second"]
        assert instance._custom_result_queue.peek() is None

    asyncio.run(scenario())
