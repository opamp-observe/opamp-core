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

# ruff: noqa: S101

"""Tests for remote config application and recovery behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from opamp_consumer.common_config_handler import CommonConfigHandler
from opamp_consumer.config_metadata import ConfigMetadata
from opamp_consumer.exceptions import (
    RemoteAgentConfigContentTypeError,
    RemoteAgentConfigHashMismatchError,
    RemoteAgentConfigValidationError,
    RemoteAgentConfigWriteError,
)
from opamp_consumer.opamp_client_interface import OpAMPClientInterface
from opamp_consumer.proto import opamp_pb2
from opamp_consumer.remote_config_status import resolve_remote_config_hash


class _FakeOpAMPClient(OpAMPClientInterface):
    def __init__(
        self,
        *,
        fail_write: bool = False,
        partial_write_text: str | None = None,
        hot_reload_result: bool = True,
        hot_reload_error: Exception | None = None,
    ) -> None:
        self.fail_write = fail_write
        self.partial_write_text = partial_write_text
        self.hot_reload_result = hot_reload_result
        self.hot_reload_error = hot_reload_error
        self.write_calls: list[tuple[str, bytes]] = []
        self.hot_reload_calls = 0
        self.remote_config_status_calls: list[tuple[bytes, int, str]] = []

    async def send(self) -> opamp_pb2.ServerToAgent:
        return opamp_pb2.ServerToAgent()

    async def send_disconnect(self) -> None:
        return None

    def launch_agent_process(self) -> bool:
        return True

    def terminate_agent_process(self) -> None:
        return None

    def restart_agent_process(self) -> bool:
        return True

    def handle_custom_message(self, custom_message: opamp_pb2.CustomMessage) -> None:
        return None

    def handle_custom_capabilities(
        self, custom_capabilities: opamp_pb2.CustomCapabilities
    ) -> None:
        return None

    def handle_connection_settings(
        self, connection_settings: opamp_pb2.ConnectionSettingsOffers
    ) -> None:
        return None

    def handle_packages_available(
        self, packages_available: opamp_pb2.PackagesAvailable
    ) -> None:
        return None

    def handle_remote_config(self, remote_config: opamp_pb2.AgentRemoteConfig) -> None:
        return None

    def write_config_file(self, filename: str, body: bytes) -> None:
        self.write_calls.append((filename, body))
        target_path = Path(filename)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if self.partial_write_text is not None:
            target_path.write_text(self.partial_write_text, encoding="utf-8")
        if self.fail_write:
            raise RuntimeError("simulated write failure")
        target_path.write_text(body.decode("utf-8"), encoding="utf-8")

    def set_remote_config_status(
        self,
        remote_config: opamp_pb2.AgentRemoteConfig,
        status: int,
        error_message: str = "",
    ) -> None:
        self.remote_config_status_calls.append(
            (resolve_remote_config_hash(remote_config), int(status), str(error_message or ""))
        )

    def poll_local_status_with_codes(
        self, port: int
    ) -> tuple[dict[str, str], dict[str, str]]:
        return {}, {}

    def add_agent_version(self, port: int) -> None:
        return None

    def get_agent_description(
        self, instance_uid: bytes | str | None = None
    ) -> opamp_pb2.AgentDescription:
        return opamp_pb2.AgentDescription()

    def get_config_metadata(self) -> ConfigMetadata:
        """Return empty config metadata for remote-config handler tests."""
        return ConfigMetadata()

    def get_configuration_files(self) -> list[str]:
        return []

    def get_agent_capabilities(self) -> int:
        return 0

    def check_hot_deploy(self) -> str:
        return ""

    def hot_reload(self) -> bool:
        self.hot_reload_calls += 1
        if self.hot_reload_error is not None:
            raise self.hot_reload_error
        return self.hot_reload_result

    def is_capability_allowed(self, capability_name: str) -> bool:
        return False

    async def finalize_async(self) -> None:
        """Complete the fake client's no-op asynchronous cleanup."""
        return None

    def finalize(self) -> None:
        return None


def _build_remote_config(
    *,
    entries: dict[str, tuple[bytes, str | None]],
    include_hash: bool = False,
) -> opamp_pb2.AgentRemoteConfig:
    remote_config = opamp_pb2.AgentRemoteConfig()
    for filename, (body, content_type) in entries.items():
        config_file = remote_config.config.config_map[filename]
        config_file.body = body
        if content_type:
            config_file.content_type = content_type
    if include_hash:
        remote_config.config_hash = CommonConfigHandler.calculate_config_hash(
            remote_config.config
        )
    return remote_config


def test_apply_remote_config_writes_text_file_without_content_type(tmp_path: Path) -> None:
    """Plain text payloads without metadata should still be written."""
    target_path = tmp_path / "config.conf"
    remote_config = _build_remote_config(
        entries={str(target_path): (b"hello=world\n", None)},
    )
    client = _FakeOpAMPClient()

    CommonConfigHandler.apply_remote_config(remote_config, client)

    assert target_path.read_text(encoding="utf-8") == "hello=world\n"
    assert client.write_calls == [(str(target_path), b"hello=world\n")]
    assert client.hot_reload_calls == 1
    assert client.remote_config_status_calls == [
        (
            resolve_remote_config_hash(remote_config),
            opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_APPLYING,
            "",
        ),
        (
            resolve_remote_config_hash(remote_config),
            opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_APPLIED,
            "",
        ),
    ]


def test_apply_remote_config_validates_hash_and_logs_match(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A matching `config_hash` should be logged and the write should proceed."""
    caplog.set_level("INFO")
    target_path = tmp_path / "config.json"
    remote_config = _build_remote_config(
        entries={str(target_path): (b'{"enabled": true}\n', "application/json")},
        include_hash=True,
    )
    client = _FakeOpAMPClient()

    CommonConfigHandler.apply_remote_config(remote_config, client)

    assert "remote config hash matched provided config_hash" in caplog.text
    assert target_path.read_text(encoding="utf-8") == '{"enabled": true}\n'


def test_apply_remote_config_raises_on_hash_mismatch(tmp_path: Path) -> None:
    """A mismatched `config_hash` should abort before any writes occur."""
    target_path = tmp_path / "config.json"
    remote_config = _build_remote_config(
        entries={str(target_path): (b'{"enabled": true}\n', "application/json")},
        include_hash=True,
    )
    remote_config.config_hash = b"\x00" * 32
    client = _FakeOpAMPClient()

    with pytest.raises(RemoteAgentConfigHashMismatchError):
        CommonConfigHandler.apply_remote_config(remote_config, client)

    assert not target_path.exists()
    assert client.write_calls == []


@pytest.mark.parametrize(
    ("content_type", "body"),
    [
        ("application/json", b'{"enabled": true}\n'),
        ("application/x-yaml", b"enabled: true\n"),
        ("application/xml", b"<config><enabled>true</enabled></config>\n"),
    ],
)
def test_apply_remote_config_validates_supported_structured_content_types(
    tmp_path: Path,
    content_type: str,
    body: bytes,
) -> None:
    """Known structured text content types should pass basic validation."""
    target_path = tmp_path / "validated.cfg"
    remote_config = _build_remote_config(
        entries={str(target_path): (body, content_type)},
    )
    client = _FakeOpAMPClient()

    CommonConfigHandler.apply_remote_config(remote_config, client)

    assert target_path.read_text(encoding="utf-8") == body.decode("utf-8")


def test_apply_remote_config_rejects_invalid_json(tmp_path: Path) -> None:
    """Malformed structured content should raise a validation error."""
    target_path = tmp_path / "broken.json"
    remote_config = _build_remote_config(
        entries={str(target_path): (b'{"enabled": }\n', "application/json")},
    )
    client = _FakeOpAMPClient()

    with pytest.raises(RemoteAgentConfigValidationError):
        CommonConfigHandler.apply_remote_config(remote_config, client)

    assert not target_path.exists()
    assert client.write_calls == []


def test_apply_remote_config_rejects_binary_content_type(tmp_path: Path) -> None:
    """Recognized binary content types should be rejected before any write occurs."""
    target_path = tmp_path / "config.bin"
    remote_config = _build_remote_config(
        entries={str(target_path): (b"\x00\x01\x02", "application/octet-stream")},
    )
    client = _FakeOpAMPClient()

    with pytest.raises(RemoteAgentConfigContentTypeError):
        CommonConfigHandler.apply_remote_config(remote_config, client)

    assert not target_path.exists()
    assert client.write_calls == []


def test_apply_remote_config_restores_backup_after_write_failure(tmp_path: Path) -> None:
    """Failed writes should remove partial output and restore the original file."""
    target_path = tmp_path / "config.yaml"
    target_path.write_text("original: true\n", encoding="utf-8")
    remote_config = _build_remote_config(
        entries={str(target_path): (b"updated: true\n", "application/x-yaml")},
    )
    client = _FakeOpAMPClient(
        fail_write=True,
        partial_write_text="partial write\n",
    )

    with pytest.raises(RemoteAgentConfigWriteError):
        CommonConfigHandler.apply_remote_config(remote_config, client)

    assert target_path.read_text(encoding="utf-8") == "original: true\n"
    assert list(tmp_path.glob("config.yaml.*")) == []
    assert client.remote_config_status_calls[-1] == (
        resolve_remote_config_hash(remote_config),
        opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_FAILED,
        "failed to write remote config file "
        f"'{str(target_path)}': simulated write failure",
    )


def test_apply_remote_config_marks_applied_when_hot_reload_returns_false(
    tmp_path: Path,
) -> None:
    """A non-raising hot-reload failure should still report the config as applied."""
    target_path = tmp_path / "config.yaml"
    remote_config = _build_remote_config(
        entries={str(target_path): (b"updated: true\n", "application/x-yaml")},
    )
    client = _FakeOpAMPClient(hot_reload_result=False)

    CommonConfigHandler.apply_remote_config(remote_config, client)

    assert client.remote_config_status_calls[-1] == (
        resolve_remote_config_hash(remote_config),
        opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_APPLIED,
        "",
    )


def test_apply_remote_config_marks_failed_when_hot_reload_raises(tmp_path: Path) -> None:
    """A trapped hot-reload exception should be reported as a failed deployment."""
    target_path = tmp_path / "config.yaml"
    remote_config = _build_remote_config(
        entries={str(target_path): (b"updated: true\n", "application/x-yaml")},
    )
    client = _FakeOpAMPClient(hot_reload_error=RuntimeError("reload exploded"))

    CommonConfigHandler.apply_remote_config(remote_config, client)

    assert client.remote_config_status_calls[-1] == (
        resolve_remote_config_hash(remote_config),
        opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_FAILED,
        "reload exploded",
    )
