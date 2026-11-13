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

"""Shared helpers for populating OpAMP AgentConfigMap and AgentRemoteConfig payloads."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentConfigMapFileEntry:
    """Normalized file entry used to populate an OpAMP AgentConfigMap payload."""

    target_name: str  # Remote-config target filename used inside the protobuf map.
    body: bytes  # UTF-8 or other raw file body bytes sent to the agent.
    content_type: str = ""  # Optional MIME type advertised for the file body.

    @property
    def size_bytes(self) -> int:
        """Return the file-body length in bytes."""
        return len(self.body)


def populate_agent_config_map(
    agent_config_map: Any,
    file_entries: Iterable[AgentConfigMapFileEntry],
) -> Any:
    """Populate an AgentConfigMap-like protobuf object from shared file entries.

    Args:
        agent_config_map: Protobuf object exposing `config_map[...]`.
        file_entries: Iterable of normalized config file entries to copy in.

    Returns:
        The populated `agent_config_map` object for call chaining.
    """
    for file_entry in file_entries:
        config_file = agent_config_map.config_map[file_entry.target_name]
        config_file.body = bytes(file_entry.body)
        normalized_content_type = str(file_entry.content_type or "").strip()
        if normalized_content_type:
            config_file.content_type = normalized_content_type
    return agent_config_map


def calculate_agent_config_map_hash(agent_config_map: Any) -> bytes:
    """Return a SHA-256 digest for a deterministic AgentConfigMap serialization.

    Args:
        agent_config_map: Protobuf object exposing `SerializeToString`.

    Returns:
        SHA-256 digest bytes for the deterministic serialized config map.
    """
    serialized = agent_config_map.SerializeToString(deterministic=True)
    return hashlib.sha256(serialized).digest()


def build_agent_remote_config(
    remote_config: Any,
    file_entries: Iterable[AgentConfigMapFileEntry],
    *,
    include_hash: bool,
) -> Any:
    """Populate an AgentRemoteConfig-like protobuf object from shared file entries.

    Args:
        remote_config: Protobuf object exposing `.config` and `.config_hash`.
        file_entries: Iterable of normalized config file entries to copy in.
        include_hash: Whether to calculate and set `config_hash`.

    Returns:
        The populated `remote_config` object for call chaining.
    """
    populate_agent_config_map(remote_config.config, file_entries)
    if include_hash:
        remote_config.config_hash = calculate_agent_config_map_hash(
            remote_config.config,
        )
    return remote_config
