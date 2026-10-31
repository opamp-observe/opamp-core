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

"""Server message handling mixin extracted from the legacy client_mixins module."""

from __future__ import annotations

import asyncio
import logging
import sys
from enum import IntEnum
from typing import TYPE_CHECKING, cast

from google.protobuf import text_format
from shared.opamp_config import (
    AgentCapabilities,
    PB_FIELD_AGENT_IDENTIFICATION,
    PB_FIELD_COMMAND,
    PB_FIELD_CONNECTION_SETTINGS,
    PB_FIELD_CUSTOM_CAPABILITIES,
    PB_FIELD_CUSTOM_MESSAGE,
    PB_FIELD_ERROR_RESPONSE,
    PB_FIELD_PACKAGES_AVAILABLE,
    PB_FIELD_REMOTE_CONFIG,
    PB_FIELD_RETRY_INFO,
    PB_FLAG_REPORT_FULL_STATE,
    ServerCapabilities,
)

from opamp_consumer.common_config_handler import CommonConfigHandler
from opamp_consumer.client_message_builder import (
    EFFECTIVE_CONFIG_CAPABILITY_NAME,
    populate_agent_to_server_effective_config,
)
from opamp_consumer.custom_handlers import build_factory_lookup, create_handler
from opamp_consumer.exceptions import AgentException
from opamp_consumer.logging_utils import format_instance_uid_for_log
from opamp_consumer.proto import opamp_pb2

if TYPE_CHECKING:
    from pathlib import Path

    from opamp_consumer.abstract_client import OpAMPClientData
    from opamp_consumer.config import ConsumerConfig
    from opamp_consumer.custom_handlers.handler_interface import (
        CustomMessageHandlerInterface,
    )
    from opamp_consumer.opamp_client_interface import OpAMPClientInterface


class ServerMessageHandlingMixin:
    """ServerToAgent message dispatch and handler implementations."""

    data: OpAMPClientData
    _custom_handler_folder: Path
    _custom_handler_lookup: dict[str, type[CustomMessageHandlerInterface]]
    _server_accepts_effective_config: bool = False

    @property
    def config(self) -> ConsumerConfig:
        """Return active consumer configuration for this client."""
        raise NotImplementedError

    def restart_agent_process(self) -> bool:
        """Restart the managed agent process.

        Concrete implementations are expected to provide this behavior.
        """
        raise NotImplementedError

    def is_capability_allowed(self, capability_name: str) -> bool:
        """Return whether the named capability is enabled for this client.

        Concrete AbstractOpAMPClient implementations provide the actual logic.
        The mixin defines the method shape so server-message handling can gate
        capability-specific processing consistently.
        """
        raise NotImplementedError

    def get_configuration_files(self) -> list[str]:
        """Return local configuration file paths available for effective config."""
        raise NotImplementedError

    @staticmethod
    def _capability_mask_to_labels(mask: int, enum_cls: type[IntEnum]) -> str:
        """Convert an OpAMP capability bitmask into a compact label list."""
        if mask == 0:
            return "none"

        labels: list[str] = []
        known_mask = 0
        for capability in enum_cls:
            capability_value = int(capability)
            if capability_value == 0:
                continue
            known_mask |= capability_value
            if mask & capability_value:
                labels.append(capability.name)

        unknown_mask = mask & ~known_mask
        if unknown_mask:
            labels.append(f"UNKNOWN(0x{unknown_mask:x})")
        return ", ".join(labels) if labels else "none"

    @staticmethod
    def _format_opamp_message_with_capabilities(
        message: opamp_pb2.ServerToAgent | opamp_pb2.AgentToServer | None,
        capability_enum: type[IntEnum],
    ) -> str:
        """Render an OpAMP protobuf message with decoded top-level capabilities."""
        if message is None:
            return "None"

        rendered = text_format.MessageToString(message).rstrip()
        capability_mask = int(getattr(message, "capabilities", 0) or 0)
        capability_line = f"capabilities: {capability_mask}"
        capability_labels = ServerMessageHandlingMixin._capability_mask_to_labels(
            capability_mask,
            capability_enum,
        )
        replacement_line = f"{capability_line}  # labels: {capability_labels}"

        lines = rendered.splitlines()
        for index, line in enumerate(lines):
            if line == capability_line:
                lines[index] = replacement_line
                return "\n".join(lines)

        return rendered

    @staticmethod
    def server_to_agent_to_log_string(message: opamp_pb2.ServerToAgent | None) -> str:
        """Render ServerToAgent payloads for logs with decoded capabilities."""
        return ServerMessageHandlingMixin._format_opamp_message_with_capabilities(
            message,
            ServerCapabilities,
        )

    @staticmethod
    def agent_to_server_to_log_string(message: opamp_pb2.AgentToServer | None) -> str:
        """Render AgentToServer payloads for logs with decoded capabilities."""
        return ServerMessageHandlingMixin._format_opamp_message_with_capabilities(
            message,
            AgentCapabilities,
        )

    def _handle_server_to_agent(self, reply: opamp_pb2.ServerToAgent) -> bool:
        """Process ServerToAgent fields and dispatch each populated payload section.

        Args:
            reply: ServerToAgent payload received from the provider.

        Returns:
            True when message processing completed without critical handling errors.
        """
        logger = logging.getLogger(__name__)
        logger.debug("_handle_server_to_agent called **************************************")
        successful_message = True

        logger.debug(
            "Handling Server to agent payload:\n%s",
            self.server_to_agent_to_log_string(reply),
        )
        if reply is None:
            logger.error("Been given None response")
            return False

        try:
            if not self._validate_reply_instance_uid(reply):
                successful_message = False
        except ValueError as val_err:
            logger.error("Error processing svr instance uid %s", val_err)
            successful_message = False

        try:
            if reply.HasField(PB_FIELD_ERROR_RESPONSE):
                self.data.set_all_reporting_flags()
                self.handle_error_response(error_response=reply.error_response)
            if reply.HasField(PB_FIELD_REMOTE_CONFIG):
                self.handle_remote_config(reply.remote_config)
            if reply.HasField(PB_FIELD_CONNECTION_SETTINGS):
                self.handle_connection_settings(reply.connection_settings)
            if reply.HasField(PB_FIELD_PACKAGES_AVAILABLE):
                self.handle_packages_available(reply.packages_available)
            if reply.flags:
                self.handle_flags(reply.flags)
            if reply.capabilities:
                self.handle_capabilities(reply.capabilities)
            if reply.HasField(PB_FIELD_AGENT_IDENTIFICATION):
                self.handle_agent_identification(reply.agent_identification)
            if reply.HasField(PB_FIELD_COMMAND):
                self.handle_command(reply.command)
            if reply.HasField(PB_FIELD_CUSTOM_CAPABILITIES):
                self.handle_custom_capabilities(reply.custom_capabilities)
            if reply.HasField(PB_FIELD_CUSTOM_MESSAGE):
                self.handle_custom_message(reply.custom_message)

        except AgentException as agent_err:
            logger.error("Agent Error received - %s", agent_err)
            successful_message = False
        return successful_message

    def _validate_reply_instance_uid(self, reply: opamp_pb2.ServerToAgent) -> bool:
        """Validate that a reply contains and matches the expected instance UID.

        Args:
            reply: Incoming ServerToAgent payload.

        Returns:
            True if the payload instance UID is present and matches this client.
        """
        logger = logging.getLogger(__name__)
        # `instance_uid` is a proto3 scalar bytes field and does not support HasField().
        if reply.instance_uid:
            logger.debug(
                "reply target is %s",
                format_instance_uid_for_log(reply.instance_uid),
            )
            if reply.instance_uid == self.data.uid_instance:
                return True
            logger.error(
                "Message doesn't have an instance uid or doesn't match our "
                "service instance id %s",
                format_instance_uid_for_log(reply.instance_uid),
            )
            return False
        logger.error(
            "Server didn't share instance_uid, my instance uid is %s",
            format_instance_uid_for_log(self.data.uid_instance),
        )
        return False

    def handle_error_response(
        self, error_response: opamp_pb2.ServerErrorResponse
    ) -> None:
        """Log details from a ServerErrorResponse.

        Args:
            error_response: Server error payload to inspect and log.
        """
        logger = logging.getLogger(__name__)
        logger.warning("server error_response type=%s", error_response.type)
        if error_response.error_message:
            logger.warning(
                "*******/n server error_response message=%s/n*******",
                error_response.error_message,
            )
        if error_response.HasField(PB_FIELD_RETRY_INFO):
            logger.warning(
                "server error_response retry_after_nanoseconds=%s",
                error_response.retry_info.retry_after_nanoseconds,
            )

    def handle_remote_config(self, remote_config: opamp_pb2.AgentRemoteConfig) -> None:
        """Validate and apply the remote-config payload received from the provider.

        Args:
            remote_config: Remote configuration payload from ServerToAgent.
        """
        logger = logging.getLogger(__name__)
        logger.debug("handle_remote_config triggered")
        if not self.is_capability_allowed("AcceptsRemoteConfig"):
            filenames = sorted(str(filename).strip() for filename in remote_config.config.config_map)
            logger.error(
                "remote config payload received but remote config is not allowed for "
                "this client; filenames=%s",
                ", ".join(filenames),
            )
            return
        CommonConfigHandler.apply_remote_config(remote_config, cast("OpAMPClientInterface", self))

    def handle_connection_settings(
        self, connection_settings: opamp_pb2.ConnectionSettingsOffers
    ) -> None:
        """Log provider connection-settings offers for diagnostics and visibility.

        Args:
            connection_settings: Connection settings offered by the provider.
        """
        logging.getLogger(__name__).info(
            "server connection_settings:\n%s \n ---- to be implemented ----",
            text_format.MessageToString(connection_settings),
        )

    def handle_packages_available(
        self, packages_available: opamp_pb2.PackagesAvailable
    ) -> None:
        """Log package offers sent by the provider.

        Args:
            packages_available: Package availability payload from ServerToAgent.
        """
        logging.getLogger(__name__).info(
            "server packages_available:\n%s\n ---- to be implemented ----",
            text_format.MessageToString(packages_available),
        )

    def handle_flags(self, flags: int) -> None:
        """Log raw server flag bitmask values from ServerToAgent.

        Args:
            flags: Integer bitmask from `ServerToAgent.flags`.
        """
        logger = logging.getLogger(__name__)
        flag_names: list[str] = []
        for enum_value in opamp_pb2.ServerToAgentFlags.DESCRIPTOR.values:
            if enum_value.number == 0:
                continue
            if flags & enum_value.number:
                name = enum_value.name
                if name.startswith("ServerToAgentFlags_"):
                    name = name[len("ServerToAgentFlags_"):]
                flag_names.append(name)

        if PB_FLAG_REPORT_FULL_STATE in flag_names:
            self.data.set_all_reporting_flags(True)
            logger.info(
                "server flags include ReportFullState; set all reporting flags true"
            )
            if (
                self._server_accepts_effective_config
                and self.is_capability_allowed(EFFECTIVE_CONFIG_CAPABILITY_NAME)
            ):
                self.data.config_changed = True
                logger.info(
                    "server flags include ReportFullState; queued effective_config for next outbound message"
                )

        if flag_names:
            logger.info("server flags: %s (%s)", flags, ", ".join(flag_names))
        else:
            logger.info("server flags: %s", flags)

    def handle_capabilities(self, capabilities: int) -> None:
        """Log raw server capability bitmask values from ServerToAgent.

        Args:
            capabilities: Integer bitmask from `ServerToAgent.capabilities`.
        """
        logger = logging.getLogger(__name__)
        logger.info("handle_capabilities given server capabilities: %s", capabilities)

        accepts_effective_config = bool(
            capabilities
            & opamp_pb2.ServerCapabilities.ServerCapabilities_AcceptsEffectiveConfig
        )
        logger.debug("handle_capabilities - accepts_effective_config %s", capabilities)

        if accepts_effective_config and not self._server_accepts_effective_config:
            self._server_accepts_effective_config = True
            self._schedule_effective_config_report()
            logger.debug("handle_capabilities - _schedule_effective_config_report")         
        else:
            self._server_accepts_effective_config = accepts_effective_config
            logger.debug(
                "handle_capabilities - set accepts_effective_config to %s", accepts_effective_config
            )   

    def _schedule_effective_config_report(self) -> None:
        """Schedule a one-off EffectiveConfig report when the server accepts it."""
        logger = logging.getLogger(__name__)
        logger.debug("_schedule_effective_config_report called")
        if not self.is_capability_allowed(EFFECTIVE_CONFIG_CAPABILITY_NAME):
            logger.info(
                "server accepts effective config but agent capability %s is disabled",
                EFFECTIVE_CONFIG_CAPABILITY_NAME,
            )
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            self.data.config_changed = True
            logger.debug(
                "server accepts effective config; it will be included on the next outbound message - RuntimeTrap"
            )
            return
        if loop.is_closed():
            self.data.config_changed = True
            logger.debug(
                "server accepts effective config; it will be included on the next outbound message - loop closed")        
            return
        
        logger.debug(
            "server accepts effective config; it will be included on the next outbound message - loop.create task call")
        loop.create_task(self._send_effective_config_report())

    async def _send_effective_config_report(self) -> None:
        """Build and send an EffectiveConfig-only AgentToServer message."""
        logger = logging.getLogger(__name__)
        logger.debug("_send_effective_config_report triggered")
        msg = opamp_pb2.AgentToServer()
        if self.data.uid_instance is not None:
            msg.instance_uid = self.data.uid_instance
        msg.sequence_num = self.data.msg_sequence_number
        self.data.msg_sequence_number = self.data.msg_sequence_number + 1
        populate_agent_to_server_effective_config(
            msg=msg,
            configuration_files=self.get_configuration_files(),
        )
        if not msg.HasField("effective_config"):
            return
        try:
            await self.send(msg=msg, send_as_is=True)
            self.data.config_changed = False
        except Exception:
            logger.exception("failed to send effective_config report")

    def handle_command(self, command: opamp_pb2.ServerToAgentCommand) -> None:
        """Handle ServerToAgent command payloads.

        Args:
            command: Command payload from the provider.
        """
        logger = logging.getLogger(__name__)
        if command is None:
            return
        logger.info("server command:\n%s", text_format.MessageToString(command))
        match command.type:
            case opamp_pb2.CommandType.CommandType_Restart:
                logger.info("server command to restart recognized")
                self.restart_agent_process()
            case _:
                raise AgentException(f"Unknown command type: {command.type}")

    def handle_agent_identification(
        self, agent_identification: opamp_pb2.AgentIdentification
    ) -> None:
        """Update local instance UID when the server sends AgentIdentification.

        Args:
            agent_identification: AgentIdentification payload with replacement UID.
        """
        logging.getLogger(__name__).info(
            "server agent_identification:\n%s",
            text_format.MessageToString(agent_identification),
        )
        self.data.uid_instance = agent_identification.new_instance_uid

    def handle_custom_capabilities(
        self, custom_capabilities: opamp_pb2.CustomCapabilities
    ) -> None:
        """Log custom capability declarations received from the provider.

        Args:
            custom_capabilities: Custom capability list reported by the provider.
        """
        logging.getLogger(__name__).info(
            "notified of server custom_capabilities: %s",
            text_format.MessageToString(custom_capabilities),
        )

    def handle_custom_message(self, custom_message: opamp_pb2.CustomMessage) -> None:
        """Route a custom message to its handler and execute it against this client.

        Args:
            custom_message: Custom message payload containing capability and data.
        """
        logger = logging.getLogger(__name__)
        logger.info(
            "server custom_message: %s", text_format.MessageToString(custom_message)
        )
        if custom_message is None:
            return

        # Resolve handler factories from the concrete client module for test patch points.
        client_module = sys.modules.get(self.__class__.__module__)

        create_handler_fn = create_handler
        build_factory_lookup_fn = build_factory_lookup
        if client_module is not None:
            create_handler_fn = getattr(client_module, "create_handler", create_handler)
            build_factory_lookup_fn = getattr(
                client_module, "build_factory_lookup", build_factory_lookup
            )

        capability = str(custom_message.capability or "").strip()
        if not capability:
            raise AgentException("CustomMessage capability is missing")
        logger.debug(
            "handling custom message capability=%s type=%s data_len=%s",
            capability,
            str(custom_message.type or ""),
            len(bytes(custom_message.data or b"")),
        )

        handler = create_handler_fn(
            capability,
            self._custom_handler_folder,
            client_data=self.data,
            factory_lookup=self._custom_handler_lookup,
            allow_custom_capabilities=bool(self.config.allow_custom_capabilities),
        )
        logger.debug(
            "custom handler lookup initial capability=%s found=%s",
            capability,
            handler.__class__.__name__ if handler is not None else None,
        )
        if handler is None:
            self._custom_handler_lookup = build_factory_lookup_fn(
                self._custom_handler_folder,
                client_data=self.data,
            )
            handler = create_handler_fn(
                capability,
                self._custom_handler_folder,
                client_data=self.data,
                factory_lookup=self._custom_handler_lookup,
                allow_custom_capabilities=bool(self.config.allow_custom_capabilities),
            )
            logger.debug(
                "custom handler lookup after refresh capability=%s found=%s",
                capability,
                handler.__class__.__name__ if handler is not None else None,
            )
        if handler is None:
            raise AgentException(
                f"No command handler registered for capability: {capability}"
            )

        handler.set_custom_message_handler(custom_message)
        logger.debug(
            "executing custom handler capability=%s handler=%s",
            capability,
            handler.__class__.__name__,
        )
        command_error = handler.execute(cast("OpAMPClientInterface", self))
        if command_error is not None:
            raise AgentException(str(command_error))
