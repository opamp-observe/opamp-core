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

# ruff: noqa: S101

"""Focused tests for remote-config command metadata and shared payload helpers."""

from __future__ import annotations

from opamp_provider.proto import opamp_pb2
from opamp_provider.remote_config_offer import RemoteConfigOfferCommand
from shared.agent_remote_config import (
    AgentConfigMapFileEntry,
    build_agent_remote_config,
    calculate_agent_config_map_hash,
)


def test_remote_config_offer_command_exposes_expected_defaults() -> None:
    """RemoteConfigOfferCommand should retain the command metadata contract."""
    command = RemoteConfigOfferCommand(
        key_values={
            "client_id": "abc123",
            "file_count": "2",
        }
    )

    assert command.get_command_classifier() == "remote_config"
    assert command.get_command_description() == "Queue AgentRemoteConfig offer"
    assert command.getdisplayname() == "Remote Config Offer"
    assert command.get_capability_fqdn() is None
    assert command.isOpAMPStandard() is False
    assert command.get_key_value_dictionary() == {
        "classifier": "remote_config",
        "action": "apply_config",
        "client_id": "abc123",
        "file_count": "2",
    }


def test_shared_agent_remote_config_helpers_build_payload_and_hash() -> None:
    """Shared helper should populate config files and compute deterministic hashes."""
    remote_config = build_agent_remote_config(
        opamp_pb2.AgentRemoteConfig(),
        [
            AgentConfigMapFileEntry(
                target_name="configs/agent.yaml",
                body=b"enabled: true\n",
                content_type="application/x-yaml",
            ),
            AgentConfigMapFileEntry(
                target_name="notes.txt",
                body=b"hello\n",
                content_type="text/plain",
            ),
        ],
        include_hash=True,
    )

    assert remote_config.config.config_map["configs/agent.yaml"].body == b"enabled: true\n"
    assert (
        remote_config.config.config_map["configs/agent.yaml"].content_type
        == "application/x-yaml"
    )
    assert remote_config.config.config_map["notes.txt"].body == b"hello\n"
    assert remote_config.config.config_map["notes.txt"].content_type == "text/plain"
    assert remote_config.config_hash == calculate_agent_config_map_hash(remote_config.config)
