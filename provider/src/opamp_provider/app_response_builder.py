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

"""Build ServerToAgent payloads for the provider transport handlers."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from google.protobuf import text_format

from opamp_provider.command_record import CommandRecord
from opamp_provider.proto import opamp_pb2
from opamp_provider.state import ClientRecord
from shared.opamp_config import PB_FIELD_COMMAND, PB_FIELD_CUSTOM_MESSAGE, UTF8_ENCODING


@dataclass(frozen=True)
class ServerToAgentResponseBuilder:
    """Assemble outbound ServerToAgent payloads from provider state and actions."""

    store: Any
    logger: logging.Logger
    server_capabilities_mask: Callable[[], int]
    get_custom_capabilities_list: Callable[[], tuple[str, ...]]
    command_object_factory: Callable[..., Any]
    channel_http: str
    action_apply_config: str
    action_change_connections: str
    action_package_available: str
    action_command_agent: str
    action_custom_agent_command: str
    classifier_command: str
    classifier_custom_command: str
    classifier_custom: str
    command_restart: str
    command_force_resync: str
    default_heartbeat_interval_seconds: int = 30

    def _build_apply_config(
        self,
        response: opamp_pb2.ServerToAgent,
        client: ClientRecord | None,
    ) -> opamp_pb2.ServerToAgent:
        """Attach a remote_config action to the ServerToAgent response."""
        self.logger.info("building next action payload: %s", self.action_apply_config)
        if client:
            pending_remote_config = self.store.pop_pending_remote_config(client.client_id)
            if pending_remote_config:
                response.remote_config.ParseFromString(pending_remote_config)
                return response
        response.remote_config.SetInParent()
        return response

    def _build_change_connections(
        self,
        response: opamp_pb2.ServerToAgent,
        client: ClientRecord | None,
    ) -> opamp_pb2.ServerToAgent:
        """Attach connection_settings updates to the ServerToAgent response."""
        self.logger.info(
            "building next action payload: %s",
            self.action_change_connections,
        )
        if client is not None:
            pending_connection_settings = self.store.pop_pending_connection_settings(
                client.client_id
            )
            if pending_connection_settings:
                response.connection_settings.ParseFromString(pending_connection_settings)
                self.logger.info(
                    "loaded queued connection_settings payload for client_id=%s",
                    client.client_id,
                )
                return response
        raw_interval = (
            getattr(client, "heartbeat_frequency", self.default_heartbeat_interval_seconds)
            if client is not None
            else self.default_heartbeat_interval_seconds
        )
        try:
            interval_seconds = max(1, int(raw_interval))
        except (TypeError, ValueError):
            interval_seconds = self.default_heartbeat_interval_seconds
        response.connection_settings.opamp.heartbeat_interval_seconds = interval_seconds
        self.logger.info(
            "set connection_settings.opamp.heartbeat_interval_seconds=%s for client_id=%s",
            interval_seconds,
            client.client_id if client else "unknown",
        )
        return response

    def _build_package_available(
        self,
        response: opamp_pb2.ServerToAgent,
    ) -> opamp_pb2.ServerToAgent:
        """Return a not-available error for package availability action."""
        self.logger.info(
            "building next action payload: %s",
            self.action_package_available,
        )
        response.error_response.type = (
            opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest
        )
        if not response.error_response.error_message:
            response.error_response.error_message = (
                "Package Availability feature not available"
            )
        self.logger.warning(
            "opamp error response channel=%s status_code=%s error_type=%s instance_uid=%s error_message=%s",
            self.channel_http,
            "-",
            "ServerErrorResponseType_BadRequest",
            response.instance_uid.hex() if response.instance_uid else "missing",
            response.error_response.error_message,
        )
        return response

    def _build_agent_remote_config(
        self,
        response: opamp_pb2.ServerToAgent,
        request_msg: opamp_pb2.AgentToServer,
    ) -> opamp_pb2.ServerToAgent:
        """Placeholder builder for AgentRemoteConfig server offers."""
        self.logger.info("remote config TBD")
        del request_msg
        return response

    def _build_connection_settings_offers(
        self,
        response: opamp_pb2.ServerToAgent,
        request_msg: opamp_pb2.AgentToServer,
    ) -> opamp_pb2.ServerToAgent:
        """Placeholder builder for ConnectionSettingsOffers server offers."""
        del request_msg
        self.logger.info("connection settings TBD")
        return response

    def _build_packages_available(
        self,
        response: opamp_pb2.ServerToAgent,
        request_msg: opamp_pb2.AgentToServer,
    ) -> opamp_pb2.ServerToAgent:
        """Placeholder builder for PackagesAvailable server offers."""
        del request_msg
        self.logger.info("packages available: TBD")
        return response

    def _build_offer_payloads(
        self,
        response: opamp_pb2.ServerToAgent,
        request_msg: opamp_pb2.AgentToServer,
    ) -> opamp_pb2.ServerToAgent:
        """Apply request-driven server-offer payload builders."""
        response = self._build_agent_remote_config(response, request_msg)
        response = self._build_connection_settings_offers(response, request_msg)
        response = self._build_packages_available(response, request_msg)
        return response

    def _build_restart_command(
        self,
        response: opamp_pb2.ServerToAgent,
        pending_command: CommandRecord,
    ) -> opamp_pb2.ServerToAgent:
        """Build a restart ServerToAgentCommand payload."""
        self.logger.info(
            "building command payload classifier=%s action=%s",
            pending_command.classifier,
            pending_command.action,
        )
        response.command.type = opamp_pb2.CommandType.CommandType_Restart
        self.logger.debug(
            "created ServerToAgent.command payload: %s",
            text_format.MessageToString(response.command).strip(),
        )
        return response

    def _build_force_resync_command(
        self,
        response: opamp_pb2.ServerToAgent,
        pending_command: CommandRecord,
    ) -> opamp_pb2.ServerToAgent:
        """Build a report-full-state ServerToAgent flags payload."""
        self.logger.info(
            "building command payload classifier=%s action=%s",
            pending_command.classifier,
            pending_command.action,
        )
        response.flags = response.flags | int(
            opamp_pb2.ServerToAgentFlags.ServerToAgentFlags_ReportFullState
        )
        self.logger.debug("created ServerToAgent.flags payload: %s", response.flags)
        return response

    @staticmethod
    def _kv_lookup(pairs: list[dict[str, str]], key: str) -> str:
        """Fetch a string value from a list of key/value dictionaries."""
        for pair in pairs:
            if pair.get("key", "").strip().lower() == key.lower():
                return str(pair.get("value", "")).strip()
        return ""

    def _build_custom_command_payload(
        self,
        response: opamp_pb2.ServerToAgent,
        pending_command: CommandRecord,
    ) -> opamp_pb2.ServerToAgent:
        """Build a ServerToAgent custom message payload from queued key/value pairs."""
        self.logger.info(
            "building custom command payload classifier=%s action=%s",
            pending_command.classifier,
            pending_command.action,
        )
        classifier = (pending_command.classifier or "").strip().lower()
        action = (pending_command.action or "").strip().lower()
        if classifier == self.classifier_custom:
            try:
                command_obj = self.command_object_factory(
                    classifier=classifier,
                    key_values={
                        pair["key"]: pair["value"]
                        for pair in pending_command.key_value_pairs
                    },
                )
                if hasattr(command_obj, "to_custom_message"):
                    response.custom_message.CopyFrom(command_obj.to_custom_message())
                    self.logger.debug(
                        "created ServerToAgent.custom_message payload from custom command object: %s",
                        text_format.MessageToString(response.custom_message).strip(),
                    )
                    return response
            except ValueError:
                self.logger.debug(
                    "no concrete custom command object for action=%s; using generic payload builder",
                    action,
                )

        capability = self._kv_lookup(pending_command.key_value_pairs, "capability")
        custom_type = self._kv_lookup(pending_command.key_value_pairs, "type")
        data_value = self._kv_lookup(pending_command.key_value_pairs, "data")

        response.custom_message.capability = capability or "custom_command"
        response.custom_message.type = custom_type or pending_command.action
        if data_value:
            response.custom_message.data = data_value.encode(UTF8_ENCODING)
        else:
            response.custom_message.data = b""
        self.logger.debug(
            "created ServerToAgent.custom_message payload: %s",
            text_format.MessageToString(response.custom_message).strip(),
        )
        return response

    def _apply_command_intent(
        self,
        response: opamp_pb2.ServerToAgent,
        pending_command: CommandRecord | None,
    ) -> opamp_pb2.ServerToAgent:
        """Map classifier/action to the matching outbound command payload builder."""
        if pending_command is None:
            return response
        classifier = pending_command.classifier.strip().lower()
        action = pending_command.action.strip().lower()

        if classifier == self.classifier_command and action == self.command_restart:
            updated_response = self._build_restart_command(response, pending_command)
        elif (
            classifier == self.classifier_command
            and action == self.command_force_resync
        ):
            updated_response = self._build_force_resync_command(
                response,
                pending_command,
            )
        elif classifier in {self.classifier_custom, self.classifier_custom_command}:
            updated_response = self._build_custom_command_payload(
                response,
                pending_command,
            )
        else:
            self.logger.warning(
                "No command builder for classifier=%s action=%s",
                classifier,
                action,
            )
            return response

        self.logger.debug(
            "created command intent payload summary client classifier=%s action=%s has_command=%s has_custom_message=%s",
            classifier,
            action,
            updated_response.HasField(PB_FIELD_COMMAND),
            updated_response.HasField(PB_FIELD_CUSTOM_MESSAGE),
        )
        return updated_response

    def _apply_next_action(
        self,
        response: opamp_pb2.ServerToAgent,
        *,
        action: str,
        pending_command: CommandRecord | None,
        client: ClientRecord | None = None,
    ) -> opamp_pb2.ServerToAgent:
        """Dispatch the next-action token to the correct outbound payload builder."""
        if action == self.action_apply_config:
            return self._build_apply_config(response, client)
        if action == self.action_change_connections:
            return self._build_change_connections(response, client)
        if action == self.action_package_available:
            return self._build_package_available(response)
        if action == self.action_command_agent:
            return self._apply_command_intent(response, pending_command)
        if action == self.action_custom_agent_command:
            return self._apply_command_intent(response, pending_command)
        self.logger.warning("unknown next action: %s", action)
        return response

    def build_response(
        self,
        request_msg: opamp_pb2.AgentToServer,
        pending_command: CommandRecord | None,
        *,
        client: ClientRecord | None = None,
        channel: str | None = None,
    ) -> opamp_pb2.ServerToAgent:
        """Build a ServerToAgent response for one AgentToServer request."""
        response = opamp_pb2.ServerToAgent()
        if request_msg.instance_uid:
            response.instance_uid = request_msg.instance_uid
            self.logger.info("set response to: %s", response.instance_uid)
        else:
            self.logger.warning("Cant set response instance_uid")

        response.capabilities = self.server_capabilities_mask()
        custom_capabilities = self.get_custom_capabilities_list()
        if custom_capabilities:
            response.custom_capabilities.capabilities.extend(custom_capabilities)
        if client:
            pending_identification = self.store.pop_agent_identification(client.client_id)
            if pending_identification:
                response.agent_identification.new_instance_uid = pending_identification
        response = self._build_offer_payloads(response, request_msg)
        if channel == self.channel_http and client:
            next_action = self.store.pop_next_action(client.client_id)
            if next_action:
                response = self._apply_next_action(
                    response,
                    action=next_action,
                    pending_command=pending_command,
                    client=client,
                )
        response = self._apply_command_intent(response, pending_command)
        return response

    @staticmethod
    def has_dispatched_command_payload(
        response_msg: opamp_pb2.ServerToAgent,
    ) -> bool:
        """Return whether the response encoded a queued command payload."""
        return (
            response_msg.HasField(PB_FIELD_COMMAND)
            or response_msg.HasField(PB_FIELD_CUSTOM_MESSAGE)
            or bool(response_msg.flags)
        )
