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

import asyncio
import logging
import pathlib
from typing import cast

import pytest
from shared.opamp_config import AGENT_CAPABILITIES_MAP

import opamp_consumer.fluentbit.client as client
from opamp_consumer.config import ConsumerConfig
from opamp_consumer.exceptions import RemoteAgentConfigWriteError
from opamp_consumer.fluentbit.client import CONFIG_DOCS_URL
from opamp_consumer.proto import opamp_pb2
from opamp_consumer.remote_config_status import resolve_remote_config_hash


def _set_config(
    agent_capabilities,
    *,
    preserve_previous_config: bool = False,
) -> None:
    """Install a test config with the requested agent capabilities."""
    config = ConsumerConfig(
        server_url="http://localhost",
        agent_config_path="unused",
        agent_additional_params=[],
        heartbeat_frequency=30,
        agent_capabilities=agent_capabilities,
        preserve_previous_config=preserve_previous_config,
        log_level="debug",
        service_name="Fluentbit",
        service_namespace="FluentBitNS",
    )
    client.CONFIG = config


def test_get_agent_capabilities_from_names(caplog) -> None:
    """Configured capability names should merge with mandatory capabilities."""
    _set_config(["ReportsStatus", "ReportsHealth", "ReportsHeartbeat"])
    caplog.set_level(logging.INFO)
    instance = client.OpAMPClient("http://localhost")

    mask = instance.get_agent_capabilities()
    expected = (
        AGENT_CAPABILITIES_MAP["ReportsStatus"]
        | AGENT_CAPABILITIES_MAP["AcceptsRestartCommand"]
        | AGENT_CAPABILITIES_MAP["ReportsHealth"]
        | AGENT_CAPABILITIES_MAP["ReportsHeartbeat"]
    )
    assert mask == expected
    assert instance.config.enabled_agent_capabilities == [
        "ReportsStatus",
        "AcceptsRestartCommand",
        "ReportsHealth",
        "ReportsHeartbeat",
    ]
    assert "supported capability not enabled capability=AcceptsRemoteConfig" in caplog.text


def test_get_agent_capabilities_warns_unknown(caplog) -> None:
    """Configured unsupported capabilities should be warned and ignored."""
    _set_config(["ReportsStatus", "UnknownCapability"])
    caplog.set_level(logging.INFO)
    instance = client.OpAMPClient("http://localhost")

    mask = instance.get_agent_capabilities()
    assert mask == (
        AGENT_CAPABILITIES_MAP["ReportsStatus"]
        | AGENT_CAPABILITIES_MAP["AcceptsRestartCommand"]
        | AGENT_CAPABILITIES_MAP["ReportsHealth"]
    )
    assert (
        "configured capability cannot be supported capability=UnknownCapability; "
        "ignoring config"
    ) in caplog.text


def test_populate_agent_to_server_uses_configured_capability_override() -> None:
    """Configured optional capabilities should merge into the outbound mask."""
    _set_config(["AcceptsRestartCommand", "AcceptsRemoteConfig"])
    instance = client.OpAMPClient("http://localhost")
    message = opamp_pb2.AgentToServer()

    populated = instance._populate_agent_to_server(message)

    expected_mask = (
        AGENT_CAPABILITIES_MAP["ReportsStatus"]
        | AGENT_CAPABILITIES_MAP["AcceptsRestartCommand"]
        | AGENT_CAPABILITIES_MAP["ReportsHealth"]
        | AGENT_CAPABILITIES_MAP["AcceptsRemoteConfig"]
    )
    assert populated.capabilities == expected_mask
    assert instance.config.agent_capabilities == expected_mask
    assert "AcceptsRemoteConfig" in instance.config.enabled_agent_capabilities


def test_get_agent_capabilities_derives_default_mask_when_unset() -> None:
    """Missing override should derive and cache the mandatory capability mask."""
    _set_config(None)
    instance = client.OpAMPClient("http://localhost")

    mask = instance.get_agent_capabilities()

    assert mask == (
        AGENT_CAPABILITIES_MAP["ReportsStatus"]
        | AGENT_CAPABILITIES_MAP["AcceptsRestartCommand"]
        | AGENT_CAPABILITIES_MAP["ReportsHealth"]
    )
    assert instance.config.agent_capabilities == mask
    assert instance.config.enabled_agent_capabilities == [
        "ReportsStatus",
        "AcceptsRestartCommand",
        "ReportsHealth",
    ]


def test_populate_agent_to_server_includes_mandatory_capabilities_when_unset() -> None:
    """Outbound payload should advertise the built-in three capabilities by default."""
    _set_config(None)
    instance = client.OpAMPClient("http://localhost")
    message = opamp_pb2.AgentToServer()

    populated = instance._populate_agent_to_server(message)

    assert populated.capabilities & AGENT_CAPABILITIES_MAP["ReportsStatus"]
    assert populated.capabilities & AGENT_CAPABILITIES_MAP["AcceptsRestartCommand"]
    assert populated.capabilities & AGENT_CAPABILITIES_MAP["ReportsHealth"]


def test_get_agent_capabilities_enables_remote_config_when_configured() -> None:
    """Configured optional remote config should be enabled when supported."""
    _set_config(["AcceptsRemoteConfig"])
    instance = client.OpAMPClient("http://localhost")

    mask = instance.get_agent_capabilities()

    assert mask == (
        AGENT_CAPABILITIES_MAP["ReportsStatus"]
        | AGENT_CAPABILITIES_MAP["AcceptsRestartCommand"]
        | AGENT_CAPABILITIES_MAP["ReportsHealth"]
        | AGENT_CAPABILITIES_MAP["AcceptsRemoteConfig"]
    )
    assert instance.is_capability_allowed("AcceptsRemoteConfig") is True
    assert instance.is_capability_allowed("AcceptsPackages") is False


def test_get_agent_capabilities_enables_effective_config_when_configured() -> None:
    """Configured effective-config reporting should be enabled when supported."""
    _set_config(["ReportsEffectiveConfig"])
    instance = client.OpAMPClient("http://localhost")

    mask = instance.get_agent_capabilities()

    assert mask == (
        AGENT_CAPABILITIES_MAP["ReportsStatus"]
        | AGENT_CAPABILITIES_MAP["AcceptsRestartCommand"]
        | AGENT_CAPABILITIES_MAP["ReportsHealth"]
        | AGENT_CAPABILITIES_MAP["ReportsEffectiveConfig"]
    )
    assert instance.is_capability_allowed("ReportsEffectiveConfig") is True


def test_populate_agent_to_server_includes_effective_config_when_enabled(
    tmp_path,
    caplog,
) -> None:
    """Effective config should be attached when enabled and accepted by the server."""
    config_path = tmp_path / "effective.yaml"
    config_path.write_bytes(b"service:\n  flush: 1\n")
    config = ConsumerConfig(
        server_url="http://localhost",
        agent_config_path=str(config_path),
        agent_additional_params=[],
        heartbeat_frequency=30,
        agent_capabilities=["ReportsEffectiveConfig"],
        log_level="debug",
        service_name="Fluentbit",
        service_namespace="FluentBitNS",
    )
    instance = client.OpAMPClient("http://localhost", config)
    instance._server_accepts_effective_config = True
    message = opamp_pb2.AgentToServer()
    caplog.set_level(logging.INFO)

    populated = instance._populate_agent_to_server(message)

    config_map = populated.effective_config.config_map.config_map
    assert str(config_path) in config_map
    assert config_map[str(config_path)].body == b"service:\n  flush: 1\n"
    assert config_map[str(config_path)].content_type == "application/x-yaml"
    assert "generated effective_config payload" in caplog.text


def test_populate_agent_to_server_omits_effective_config_when_not_enabled(
    tmp_path,
) -> None:
    """Effective config should be omitted when the reporting capability is disabled."""
    config_path = tmp_path / "effective.yaml"
    config_path.write_bytes(b"service:\n  flush: 1\n")
    config = ConsumerConfig(
        server_url="http://localhost",
        agent_config_path=str(config_path),
        agent_additional_params=[],
        heartbeat_frequency=30,
        agent_capabilities=None,
        log_level="debug",
        service_name="Fluentbit",
        service_namespace="FluentBitNS",
    )
    instance = client.OpAMPClient("http://localhost", config)
    message = opamp_pb2.AgentToServer()

    populated = instance._populate_agent_to_server(message)

    assert not populated.HasField("effective_config")


def test_handle_server_to_agent_sends_effective_config_when_server_accepts_it(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A server capability advertisement should trigger an effective-config send."""
    config_path = tmp_path / "effective.yaml"
    config_path.write_bytes(b"service:\n  flush: 1\n")
    config = ConsumerConfig(
        server_url="http://localhost",
        agent_config_path=str(config_path),
        agent_additional_params=[],
        heartbeat_frequency=30,
        agent_capabilities=["ReportsEffectiveConfig"],
        log_level="debug",
        service_name="Fluentbit",
        service_namespace="FluentBitNS",
    )
    instance = client.OpAMPClient("http://localhost", config)
    sent: dict[str, object] = {}

    async def _fake_send(
        msg: opamp_pb2.AgentToServer | None = None,
        *,
        send_as_is: bool = False,
    ) -> opamp_pb2.ServerToAgent:
        sent["msg"] = msg
        sent["send_as_is"] = send_as_is
        reply = opamp_pb2.ServerToAgent()
        reply.instance_uid = instance.data.uid_instance
        return reply

    monkeypatch.setattr(instance, "send", _fake_send)

    async def _exercise() -> None:
        reply = opamp_pb2.ServerToAgent()
        reply.instance_uid = instance.data.uid_instance
        reply.capabilities = (
            opamp_pb2.ServerCapabilities.ServerCapabilities_AcceptsEffectiveConfig
        )
        assert instance._handle_server_to_agent(reply) is True
        await asyncio.sleep(0)

    asyncio.run(_exercise())

    assert sent["send_as_is"] is True
    sent_msg = cast(opamp_pb2.AgentToServer, sent["msg"])
    assert isinstance(sent_msg, opamp_pb2.AgentToServer)
    assert sent_msg.instance_uid == instance.data.uid_instance
    assert sent_msg.sequence_num == 0
    assert instance.data.msg_sequence_number == 1
    config_map = sent_msg.effective_config.config_map.config_map
    assert str(config_path) in config_map
    assert config_map[str(config_path)].body == b"service:\n  flush: 1\n"
    assert config_map[str(config_path)].content_type == "application/x-yaml"


def test_handle_server_to_agent_only_sends_effective_config_once_per_advertisement(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repeated AcceptsEffectiveConfig replies should not trigger duplicate sends."""
    config_path = tmp_path / "effective.yaml"
    config_path.write_bytes(b"service:\n  flush: 1\n")
    config = ConsumerConfig(
        server_url="http://localhost",
        agent_config_path=str(config_path),
        agent_additional_params=[],
        heartbeat_frequency=30,
        agent_capabilities=["ReportsEffectiveConfig"],
        log_level="debug",
        service_name="Fluentbit",
        service_namespace="FluentBitNS",
    )
    instance = client.OpAMPClient("http://localhost", config)
    calls: list[opamp_pb2.AgentToServer] = []

    async def _fake_send(
        msg: opamp_pb2.AgentToServer | None = None,
        *,
        send_as_is: bool = False,
    ) -> opamp_pb2.ServerToAgent:
        assert send_as_is is True
        assert isinstance(msg, opamp_pb2.AgentToServer)
        calls.append(msg)
        reply = opamp_pb2.ServerToAgent()
        reply.instance_uid = instance.data.uid_instance
        return reply

    monkeypatch.setattr(instance, "send", _fake_send)

    async def _exercise() -> None:
        reply = opamp_pb2.ServerToAgent()
        reply.instance_uid = instance.data.uid_instance
        reply.capabilities = (
            opamp_pb2.ServerCapabilities.ServerCapabilities_AcceptsEffectiveConfig
        )
        assert instance._handle_server_to_agent(reply) is True
        assert instance._handle_server_to_agent(reply) is True
        await asyncio.sleep(0)

    asyncio.run(_exercise())

    assert len(calls) == 1


def test_handle_capabilities_marks_effective_config_for_next_outbound_message(
    tmp_path,
) -> None:
    """Without a running loop, effective config should be queued for the next send."""
    config_path = tmp_path / "effective.yaml"
    config_path.write_bytes(b"service:\n  flush: 1\n")
    config = ConsumerConfig(
        server_url="http://localhost",
        agent_config_path=str(config_path),
        agent_additional_params=[],
        heartbeat_frequency=30,
        agent_capabilities=["ReportsEffectiveConfig"],
        log_level="debug",
        service_name="Fluentbit",
        service_namespace="FluentBitNS",
    )
    instance = client.OpAMPClient("http://localhost", config)

    instance.handle_capabilities(
        opamp_pb2.ServerCapabilities.ServerCapabilities_AcceptsEffectiveConfig
    )

    assert instance.data.config_changed is True

    first_message = instance._populate_agent_to_server(opamp_pb2.AgentToServer())

    config_map = first_message.effective_config.config_map.config_map
    assert str(config_path) in config_map
    assert config_map[str(config_path)].body == b"service:\n  flush: 1\n"
    assert instance.data.config_changed is False

    second_message = instance._populate_agent_to_server(opamp_pb2.AgentToServer())

    assert not second_message.HasField("effective_config")


def test_send_includes_remote_config_status_only_after_it_changes(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RemoteConfigStatus should be sent once per changed snapshot."""
    config = ConsumerConfig(
        server_url="http://localhost",
        agent_config_path=str(tmp_path / "effective.yaml"),
        agent_additional_params=[],
        heartbeat_frequency=30,
        agent_capabilities=["AcceptsRemoteConfig"],
        log_level="debug",
        service_name="Fluentbit",
        service_namespace="FluentBitNS",
    )
    instance = client.OpAMPClient("http://localhost", config)
    remote_config = opamp_pb2.AgentRemoteConfig()
    remote_config.config.config_map[str(tmp_path / "remote.yaml")].body = b"updated: true\n"
    instance.set_remote_config_status(
        remote_config,
        opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_APPLIED,
    )
    sent_messages: list[opamp_pb2.AgentToServer] = []

    async def _fake_send_http(msg: opamp_pb2.AgentToServer) -> opamp_pb2.ServerToAgent:
        sent_messages.append(msg)
        reply = opamp_pb2.ServerToAgent()
        reply.instance_uid = instance.data.uid_instance
        return reply

    monkeypatch.setattr(instance, "send_http", _fake_send_http)

    asyncio.run(instance.send())
    asyncio.run(instance.send())

    assert len(sent_messages) == 2
    assert sent_messages[0].HasField("remote_config_status")
    assert sent_messages[0].remote_config_status.last_remote_config_hash == resolve_remote_config_hash(
        remote_config
    )
    assert (
        sent_messages[0].remote_config_status.status
        == opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_APPLIED
    )
    assert not sent_messages[1].HasField("remote_config_status")


def test_send_retries_remote_config_status_until_a_send_succeeds(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed transport send should not mark the status as already reported."""
    config = ConsumerConfig(
        server_url="http://localhost",
        agent_config_path=str(tmp_path / "effective.yaml"),
        agent_additional_params=[],
        heartbeat_frequency=30,
        agent_capabilities=["AcceptsRemoteConfig"],
        log_level="debug",
        service_name="Fluentbit",
        service_namespace="FluentBitNS",
    )
    instance = client.OpAMPClient("http://localhost", config)
    remote_config = opamp_pb2.AgentRemoteConfig()
    remote_config.config.config_map[str(tmp_path / "remote.yaml")].body = b"updated: true\n"
    instance.set_remote_config_status(
        remote_config,
        opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_FAILED,
        "disk full",
    )
    sent_messages: list[opamp_pb2.AgentToServer] = []
    attempts = {"count": 0}

    async def _fake_send_http(msg: opamp_pb2.AgentToServer) -> opamp_pb2.ServerToAgent:
        attempts["count"] += 1
        sent_messages.append(msg)
        if attempts["count"] == 1:
            raise RuntimeError("transport down")
        reply = opamp_pb2.ServerToAgent()
        reply.instance_uid = instance.data.uid_instance
        return reply

    monkeypatch.setattr(instance, "send_http", _fake_send_http)

    asyncio.run(instance.send())
    asyncio.run(instance.send())

    assert len(sent_messages) == 2
    assert sent_messages[0].HasField("remote_config_status")
    assert sent_messages[1].HasField("remote_config_status")
    assert instance.data.last_sent_remote_config_status is not None


def test_handle_capabilities_skips_effective_config_send_when_agent_capability_disabled(
    monkeypatch: pytest.MonkeyPatch,
    caplog,
) -> None:
    """No follow-up send should happen when ReportsEffectiveConfig is disabled."""
    _set_config(None)
    instance = client.OpAMPClient("http://localhost")
    called = {"count": 0}
    caplog.set_level(logging.INFO)

    async def _fake_send(
        msg: opamp_pb2.AgentToServer | None = None,
        *,
        send_as_is: bool = False,
    ) -> opamp_pb2.ServerToAgent:
        called["count"] += 1
        reply = opamp_pb2.ServerToAgent()
        reply.instance_uid = instance.data.uid_instance
        return reply

    monkeypatch.setattr(instance, "send", _fake_send)

    instance.handle_capabilities(
        opamp_pb2.ServerCapabilities.ServerCapabilities_AcceptsEffectiveConfig
    )

    assert called["count"] == 0
    assert (
        "server accepts effective config but agent capability ReportsEffectiveConfig is disabled"
        in caplog.text
    )


def test_write_config_file_preserves_previous_file_when_enabled(tmp_path) -> None:
    """A replaced config should be renamed with the required preserved postfix."""
    _set_config(None, preserve_previous_config=True)
    instance = client.OpAMPClient("http://localhost")
    target_path = tmp_path / "agent.conf"
    target_path.write_text("before=true\n", encoding="utf-8")

    instance.write_config_file(str(target_path), b"after=true\n")

    preserved_paths = list(tmp_path.glob("agent.conf.replaced_*"))
    assert target_path.read_text(encoding="utf-8") == "after=true\n"
    assert len(preserved_paths) == 1
    assert preserved_paths[0].read_text(encoding="utf-8") == "before=true\n"


def test_write_config_file_restores_original_when_write_fails(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An I/O failure after preservation should raise a controlled write error."""
    _set_config(None, preserve_previous_config=True)
    instance = client.OpAMPClient("http://localhost")
    target_path = tmp_path / "agent.conf"
    target_path.write_text("before=true\n", encoding="utf-8")
    original_write_text = pathlib.Path.write_text

    def _failing_write_text(
        self: pathlib.Path,
        data: str,
        *args,
        **kwargs,
    ) -> int:
        if self == target_path:
            raise OSError("disk full")
        return original_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "write_text", _failing_write_text)

    with pytest.raises(RemoteAgentConfigWriteError, match="disk full"):
        instance.write_config_file(str(target_path), b"after=true\n")

    assert target_path.read_text(encoding="utf-8") == "before=true\n"
    assert list(tmp_path.glob("agent.conf.replaced_*")) == []


def test_get_config_parameters_includes_docs_url() -> None:
    """Return config parameters plus documentation URL reference."""
    _set_config(["ReportsStatus"])
    instance = client.OpAMPClient("http://localhost")
    config_params = instance.get_config_parameters()
    assert config_params["server_url"] == "http://localhost"
    assert config_params["documentation_url"] == CONFIG_DOCS_URL
    assert isinstance(config_params["component_version"], str)


def test_reporting_flags_default_to_true() -> None:
    """OpAMPClientData should default all ReportingFlag values to True."""
    _set_config(["ReportsStatus"])
    instance = client.OpAMPClient("http://localhost")
    assert instance.data.reporting_flags
    assert set(instance.data.reporting_flags.keys()) == set(client.ReportingFlag)
    assert all(instance.data.reporting_flags.values())


def test_reporting_flags_setall_updates_all_values() -> None:
    """set_all_reporting_flags should apply the given value to all reporting flags."""
    _set_config(["ReportsStatus"])
    instance = client.OpAMPClient("http://localhost")

    instance.data.set_all_reporting_flags(False)
    assert all(value is False for value in instance.data.reporting_flags.values())

    instance.data.set_all_reporting_flags()
    assert all(value is True for value in instance.data.reporting_flags.values())


def test_reportingflag_setall_updates_all_values() -> None:
    """ReportingFlag.set_all_reporting_flags should update every flag entry in-place."""
    flags = {flag: True for flag in client.ReportingFlag}
    client.ReportingFlag.set_all_reporting_flags(flags, False)
    assert all(value is False for value in flags.values())


def test_handle_flags_logs_names_and_sets_all_for_report_full_state(caplog) -> None:
    """handle_flags should decode names and set all flags when ReportFullState is present."""
    _set_config(["ReportsStatus"])
    instance = client.OpAMPClient("http://localhost")
    instance.data.set_all_reporting_flags(False)
    caplog.set_level(logging.INFO)

    instance.handle_flags(
        opamp_pb2.ServerToAgentFlags.ServerToAgentFlags_ReportFullState
        | opamp_pb2.ServerToAgentFlags.ServerToAgentFlags_ReportAvailableComponents
    )

    assert all(instance.data.reporting_flags.values())
    assert "ReportFullState" in caplog.text
    assert "ReportAvailableComponents" in caplog.text


def test_handle_flags_report_full_state_marks_effective_config_when_supported() -> None:
    """ReportFullState should queue effective config when both sides support it."""
    _set_config(["ReportsEffectiveConfig"])
    instance = client.OpAMPClient("http://localhost")
    instance._server_accepts_effective_config = True
    instance.data.config_changed = False

    instance.handle_flags(
        opamp_pb2.ServerToAgentFlags.ServerToAgentFlags_ReportFullState
    )

    assert instance.data.config_changed is True


def test_handle_flags_report_full_state_skips_effective_config_when_disabled() -> None:
    """ReportFullState should not queue effective config when the agent capability is disabled."""
    _set_config(None)
    instance = client.OpAMPClient("http://localhost")
    instance._server_accepts_effective_config = True
    instance.data.config_changed = False

    instance.handle_flags(
        opamp_pb2.ServerToAgentFlags.ServerToAgentFlags_ReportFullState
    )

    assert instance.data.config_changed is False


def test_handle_flags_without_report_full_state_does_not_set_all() -> None:
    """handle_flags should not force-enable reporting flags without ReportFullState."""
    _set_config(["ReportsStatus"])
    instance = client.OpAMPClient("http://localhost")
    instance.data.set_all_reporting_flags(False)

    instance.handle_flags(
        opamp_pb2.ServerToAgentFlags.ServerToAgentFlags_ReportAvailableComponents
    )

    assert not any(instance.data.reporting_flags.values())
