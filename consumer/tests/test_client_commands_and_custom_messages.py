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

import logging
from io import BytesIO, TextIOWrapper
from typing import cast

import pytest

import opamp_consumer.fluentbit.client as client
from opamp_consumer.config import ConsumerConfig
from opamp_consumer.custom_handlers.handler_interface import (
    CustomMessageHandlerInterface,
)
from opamp_consumer.exceptions import AgentException
from opamp_consumer.proto import opamp_pb2


class _RaisingStreamHandler(logging.StreamHandler):
    """StreamHandler variant that fails tests on emit/encoding errors."""

    def handleError(self, record) -> None:  # noqa: N802
        raise AssertionError("logging handler failed to emit record")


def test_handle_error_response_logs(caplog) -> None:
    """Log server error response details including message and retry info."""
    instance = client.OpAMPClient("http://localhost")
    caplog.set_level(logging.WARNING)

    error = opamp_pb2.ServerErrorResponse(
        type=opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest,
        error_message="boom",
        retry_info=opamp_pb2.RetryInfo(retry_after_nanoseconds=123),
    )
    instance.handle_error_response(error)

    assert "error_response" in caplog.text
    assert "boom" in caplog.text


def test_server_to_agent_to_log_string_decodes_capability_labels() -> None:
    """ServerToAgent log formatting should include human-readable capability labels."""
    instance = client.OpAMPClient("http://localhost")
    reply = opamp_pb2.ServerToAgent()
    reply.capabilities = (
        opamp_pb2.ServerCapabilities.ServerCapabilities_AcceptsStatus
        | opamp_pb2.ServerCapabilities.ServerCapabilities_OffersRemoteConfig
    )

    rendered = instance.server_to_agent_to_log_string(reply)

    assert (
        "capabilities: 3  # labels: AcceptsStatus, OffersRemoteConfig" in rendered
    )


def test_agent_to_server_to_log_string_includes_unknown_capability_bits() -> None:
    """AgentToServer log formatting should preserve unknown capability bits."""
    instance = client.OpAMPClient("http://localhost")
    msg = opamp_pb2.AgentToServer()
    msg.capabilities = (
        opamp_pb2.AgentCapabilities.AgentCapabilities_ReportsStatus
        | opamp_pb2.AgentCapabilities.AgentCapabilities_ReportsHealth
        | 0x20000000
    )

    rendered = instance.agent_to_server_to_log_string(msg)

    assert "ReportsStatus" in rendered
    assert "ReportsHealth" in rendered
    assert "UNKNOWN(0x20000000)" in rendered


def test_handle_command_restart_invokes_restart(monkeypatch) -> None:
    """Restart command should invoke restart_agent_process."""
    instance = client.OpAMPClient("http://localhost")
    calls = {"restart": 0}

    def _restart() -> bool:
        calls["restart"] += 1
        return True

    monkeypatch.setattr(instance, "restart_agent_process", _restart)
    command = opamp_pb2.ServerToAgentCommand(
        type=opamp_pb2.CommandType.CommandType_Restart
    )

    instance.handle_command(command)
    assert calls["restart"] == 1


def test_handle_command_unknown_raises_agent_exception() -> None:
    """Unknown command type should raise AgentException."""
    instance = client.OpAMPClient("http://localhost")
    command = opamp_pb2.ServerToAgentCommand()
    command.type = 999

    with pytest.raises(AgentException):
        instance.handle_command(command)


def test_handle_custom_message_missing_capability_raises_agent_exception() -> None:
    """Missing capability on CustomMessage should raise AgentException."""
    instance = client.OpAMPClient("http://localhost")
    custom_message = opamp_pb2.CustomMessage()
    custom_message.type = "test"
    custom_message.data = b'{"action":"run"}'

    with pytest.raises(AgentException):
        instance.handle_custom_message(custom_message)


def test_handle_custom_message_execute_error_raises_agent_exception(monkeypatch) -> None:
    """A handler execute error should be converted to AgentException."""
    instance = client.OpAMPClient("http://localhost")

    class _FakeHandler:
        def set_custom_message_handler(self, _custom_message):
            return None

        def execute(self, _opamp_client):
            from opamp_consumer.exceptions import CommandException

            return CommandException("bad execute")

    monkeypatch.setattr(
        client, "create_handler", lambda *_args, **_kwargs: _FakeHandler()
    )

    custom_message = opamp_pb2.CustomMessage()
    custom_message.capability = "org.mp3monster.opamp_provider.chatopcommand"
    custom_message.type = "test"
    custom_message.data = b'{"action":"run"}'

    with pytest.raises(AgentException):
        instance.handle_custom_message(custom_message)


def test_get_custom_capabilities_payload_from_registry() -> None:
    """Build custom capability payload from registered custom handlers."""
    instance = client.OpAMPClient("http://localhost")
    instance._custom_handler_lookup = {
        "org.mp3monster.opamp_provider.command_shutdown_agent": cast(
            type[CustomMessageHandlerInterface], object
        ),
        "org.mp3monster.opamp_provider.chatopcommand": cast(
            type[CustomMessageHandlerInterface], object
        ),
        "": cast(type[CustomMessageHandlerInterface], object),
    }

    payload = instance.get_custom_capabilities_payload()

    assert payload.capabilities == [
        "request:org.mp3monster.opamp_provider.chatopcommand",
        "request:org.mp3monster.opamp_provider.command_shutdown_agent",
    ]


def test_populate_agent_to_server_includes_custom_capabilities() -> None:
    """Populate AgentToServer with custom capabilities from handler registry."""
    instance = client.OpAMPClient("http://localhost")
    instance._custom_handler_lookup = {
        "org.mp3monster.opamp_provider.command_shutdown_agent": cast(
            type[CustomMessageHandlerInterface], object
        ),
        "org.mp3monster.opamp_provider.chatopcommand": cast(
            type[CustomMessageHandlerInterface], object
        ),
    }
    message = opamp_pb2.AgentToServer()

    populated = instance._populate_agent_to_server(message)

    assert populated.HasField("custom_capabilities")
    assert populated.custom_capabilities.capabilities == [
        "request:org.mp3monster.opamp_provider.chatopcommand",
        "request:org.mp3monster.opamp_provider.command_shutdown_agent",
    ]


def test_handle_remote_config_logs_filenames_when_capability_not_enabled(
    tmp_path,
    caplog,
) -> None:
    """Remote config should be rejected when the capability is not enabled."""
    config = ConsumerConfig(
        server_url="http://localhost",
        agent_config_path="unused",
        agent_additional_params=[],
        heartbeat_frequency=30,
        agent_capabilities=None,
        log_level="debug",
        service_name="Fluentbit",
        service_namespace="FluentBitNS",
    )
    instance = client.OpAMPClient("http://localhost", config)
    caplog.set_level(logging.ERROR)
    target_path = tmp_path / "remote-disabled.conf"
    remote_config = opamp_pb2.AgentRemoteConfig()
    remote_config.config.config_map[str(target_path)].body = b"super-secret-body\n"

    instance.handle_remote_config(remote_config)

    assert str(target_path) in caplog.text
    assert "super-secret-body" not in caplog.text
    assert "remote config is not allowed for this client" in caplog.text
    assert not target_path.exists()


def test_validate_reply_instance_uid_logs_cp1252_safe_hex() -> None:
    """Binary instance UIDs should log as ASCII-safe hex text."""
    instance = client.OpAMPClient("http://localhost")
    reply = opamp_pb2.ServerToAgent()
    reply.instance_uid = b"\x01\xff\xfej\x81\xfdy\x80\xfe\xff8\x81\x82\x01\xff\xfe"

    stream = TextIOWrapper(BytesIO(), encoding="cp1252")
    handler = _RaisingStreamHandler(stream)
    logger = logging.getLogger("opamp_consumer.client_server_message_mixin")
    previous_level = logger.level
    previous_propagate = logger.propagate
    logger.handlers = [handler]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    try:
        assert instance._validate_reply_instance_uid(reply) is False
        handler.flush()
        stream.flush()
        output = stream.buffer.getvalue().decode("cp1252")
    finally:
        logger.handlers = []
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate
        stream.close()

    assert "reply target is 01fffe6a81fd7980feff38818201fffe" in output


def test_handle_server_to_agent_logs_human_readable_payload(caplog) -> None:
    """Inbound server payload logging should use the decoded capability formatter."""
    instance = client.OpAMPClient("http://localhost")
    reply = opamp_pb2.ServerToAgent()
    reply.instance_uid = instance.data.uid_instance
    reply.capabilities = (
        opamp_pb2.ServerCapabilities.ServerCapabilities_AcceptsStatus
        | opamp_pb2.ServerCapabilities.ServerCapabilities_AcceptsEffectiveConfig
    )
    caplog.set_level(logging.DEBUG)

    assert instance._handle_server_to_agent(reply) is True
    assert (
        "capabilities: 5  # labels: AcceptsStatus, AcceptsEffectiveConfig"
        in caplog.text
    )


def test_populate_disconnect_logs_cp1252_safe_hex() -> None:
    """Disconnect logging should also avoid raw non-text bytes."""
    instance = client.OpAMPClient("http://localhost")
    instance.data.uid_instance = b"\xff\xfe\x81\x82"
    stream = TextIOWrapper(BytesIO(), encoding="cp1252")
    handler = _RaisingStreamHandler(stream)
    logger = logging.getLogger("opamp_consumer.client_runtime_mixin")
    previous_level = logger.level
    previous_propagate = logger.propagate
    logger.handlers = [handler]
    logger.setLevel(logging.WARNING)
    logger.propagate = False

    try:
        message = instance._populate_disconnect(opamp_pb2.AgentToServer())
        handler.flush()
        stream.flush()
        output = stream.buffer.getvalue().decode("cp1252")
    finally:
        logger.handlers = []
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate
        stream.close()

    assert message.instance_uid == b"\xff\xfe\x81\x82"
    assert "Set disconnect message instance UID to fffe8182" in output
