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

"""Abstract interface for OpAMP client implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod

from opamp_consumer.config_metadata import ConfigMetadata
from opamp_consumer.proto import opamp_pb2


class OpAMPClientInterface(ABC):  # pylint: disable=too-many-public-methods
    """Defines the core contract for an OpAMP client implementation."""

    @abstractmethod
    async def send(self) -> opamp_pb2.ServerToAgent:
        """Send a status update to the server and return the server reply."""

    @abstractmethod
    async def send_disconnect(self) -> None:
        """Send an agent_disconnect message to the server."""

    @abstractmethod
    def launch_agent_process(self) -> bool:
        """Launch the managed agent process."""

    @abstractmethod
    def terminate_agent_process(self) -> None:
        """Terminate the managed agent process."""

    @abstractmethod
    def restart_agent_process(self) -> bool:
        """Restart the managed Fluent Bit process."""

    @abstractmethod
    def handle_custom_message(self, custom_message: opamp_pb2.CustomMessage) -> None:
        """Handle a custom message received from the server."""

    @abstractmethod
    def handle_custom_capabilities(
        self, custom_capabilities: opamp_pb2.CustomCapabilities
    ) -> None:
        """Handle custom capability declarations received from the server."""

    @abstractmethod
    def handle_connection_settings(
        self, connection_settings: opamp_pb2.ConnectionSettingsOffers
    ) -> None:
        """Handle connection settings sent by the server."""

    @abstractmethod
    def handle_packages_available(
        self, packages_available: opamp_pb2.PackagesAvailable
    ) -> None:
        """Handle package availability payloads sent by the server."""

    @abstractmethod
    def handle_remote_config(self, remote_config: opamp_pb2.AgentRemoteConfig) -> None:
        """Handle remote configuration payloads sent by the server."""

    @abstractmethod
    def write_config_file(self, filename: str, body: bytes) -> None:
        """Persist one remote config file to local disk."""

    @abstractmethod
    def set_remote_config_status(
        self,
        remote_config: opamp_pb2.AgentRemoteConfig,
        status: int,
        error_message: str = "",
    ) -> None:
        """Store the latest remote-config status for future AgentToServer sends."""

    @abstractmethod
    def poll_local_status_with_codes(
        self, port: int
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Poll local agent endpoints and return response text and status code maps."""

    @abstractmethod
    def add_agent_version(self, port: int) -> None:
        """Fetch and cache agent version details from the local status endpoint."""

    @abstractmethod
    def get_agent_description(
        self, instance_uid: bytes | str | None = None
    ) -> opamp_pb2.AgentDescription:
        """Build and return AgentDescription metadata for outbound OpAMP payloads."""

    @abstractmethod
    def get_config_metadata(self) -> ConfigMetadata:
        """Build and return structured config metadata for the active client config."""

    @abstractmethod
    def get_configuration_files(self) -> list[str]:
        """Return the local configuration file paths managed by this client."""

    @abstractmethod
    def get_agent_capabilities(self) -> int:
        """Build and return agent capability bitmask for outbound OpAMP payloads."""

    @abstractmethod
    def check_hot_deploy(self) -> str:
        """Return any extra launch flag needed to enable hot deploy support."""

    @abstractmethod
    def hot_reload(self) -> bool:
        """Trigger a hot reload on the managed agent when supported."""

    @abstractmethod
    def is_capability_allowed(self, capability_name: str) -> bool:
        """Return whether the named capability is enabled for this client."""

    async def finalize_async(self) -> None:
        """Await cleanup, falling back to the synchronous hook for legacy clients."""
        self.finalize()

    @abstractmethod
    def finalize(self) -> None:
        """Start or run client cleanup from synchronous compatibility callers."""
