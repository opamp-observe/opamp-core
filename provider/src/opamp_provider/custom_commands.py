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

"""Installed custom command contract, registration, and result dispatch."""

from __future__ import annotations

import base64
import importlib.metadata
import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any

from opamp_provider.command_interface import CommandObjectInterface
from opamp_provider.proto import opamp_pb2

ENTRY_POINT_GROUP = "opamp_provider.custom_commands"
WIRE_CAPABILITY_KEY = "_custom_capability"
WIRE_TYPE_KEY = "_custom_type"
WIRE_DATA_KEY = "_custom_data_b64"
COMMAND_ID_KEY = "command_id"


class CustomCommandABC(ABC):
    """Own one installed command's validation, request payload, and optional results."""

    @property
    @abstractmethod
    def command_id(self) -> str:
        """Return the stable identifier selected by the UI/API."""

    @property
    @abstractmethod
    def capability(self) -> str:
        """Return the raw reverse-FQDN carried by CustomMessage."""

    @abstractmethod
    def validate(self, parameters: dict[str, Any]) -> Any:
        """Validate typed user parameters and return an implementation-owned request."""

    @abstractmethod
    def build_message(self, agent_id: str, request: Any) -> opamp_pb2.CustomMessage:
        """Build a request and record pending history if this command tracks results."""

    def handle_result(self, agent_id: str, message: opamp_pb2.CustomMessage) -> None:
        """Accept a result from an authenticated agent; tracking is optional."""

    @property
    def display_name(self) -> str:
        """Return a short UI label for the command."""
        return self.command_id

    @property
    def description(self) -> str:
        """Return a human-readable explanation of the command."""
        return self.display_name

    @property
    def parameter_schema(self) -> list[dict[str, object]]:
        """Return parameter metadata displayed by the provider UI."""
        return []


class LegacyCustomCommandAdapter(CustomCommandABC):
    """Expose an existing CommandObjectInterface through the new command contract."""

    def __init__(self, command_type: type[CommandObjectInterface]) -> None:
        """Keep the legacy type so each request receives a fresh command object."""
        self._command_type = command_type

    @property
    def command_id(self) -> str:
        """Use the existing action/operation as its stable identifier."""
        return self._command_type().get_key_value_dictionary()["action"]

    @property
    def capability(self) -> str:
        """Preserve the existing reverse-FQDN."""
        return self._command_type().get_capability_fqdn() or ""

    @property
    def display_name(self) -> str:
        """Preserve the legacy display label."""
        return self._command_type().getdisplayname()

    @property
    def description(self) -> str:
        """Preserve the legacy command description."""
        return self._command_type().get_command_description()

    @property
    def parameter_schema(self) -> list[dict[str, object]]:
        """Expose user parameters declared by the legacy command, when available."""
        schema_provider = getattr(self._command_type(), "get_user_parameter_schema", None)
        if not callable(schema_provider):
            return []
        return [dict(parameter) for parameter in schema_provider()]

    def validate(self, parameters: dict[str, Any]) -> dict[str, str]:
        """Keep legacy key/value semantics while rejecting structured raw data."""
        if set(parameters) & {
            "capability", "type", "data", "action", "classifier", "operation"
        }:
            raise ValueError("legacy command parameters cannot override routing or wire data")
        if any(not isinstance(value, (str, int, float, bool)) for value in parameters.values()):
            raise ValueError("legacy command parameters must be primitive values")
        return {key: str(value) for key, value in parameters.items()}

    def build_message(
        self, agent_id: str, request: dict[str, str]
    ) -> opamp_pb2.CustomMessage:
        """Delegate payload construction to the existing command object."""
        instance = self._command_type()
        instance.set_key_value_dictionary(request)
        builder = getattr(instance, "to_custom_message", None)
        if not callable(builder):
            raise TypeError("legacy custom command has no to_custom_message method")
        return builder()


@lru_cache(maxsize=1)
def installed_commands() -> dict[str, CustomCommandABC]:
    """Load and validate installed implementations once before routing requests."""
    registry: dict[str, CustomCommandABC] = {}
    capabilities: set[str] = set()
    entry_points = importlib.metadata.entry_points().select(group=ENTRY_POINT_GROUP)
    for entry_point in sorted(entry_points, key=lambda item: (item.name, item.value)):
        candidate = entry_point.load()
        if not callable(candidate):
            raise TypeError(f"Invalid custom command entry point: {entry_point.name}")
        command = candidate()
        if not isinstance(command, CustomCommandABC):
            raise TypeError(f"Invalid custom command entry point: {entry_point.name}")
        identifier = command.command_id.strip()
        capability = command.capability.strip()
        if not identifier or not capability:
            raise ValueError(f"Empty custom command identifier/capability: {entry_point.name}")
        if identifier in registry or capability in capabilities:
            raise ValueError(f"Duplicate custom command identifier/capability: {identifier}")
        registry[identifier] = command
        capabilities.add(capability)
    return registry


def prepare_command(
    command_id: str, agent_id: str, parameters: dict[str, Any]
) -> tuple[str, dict[str, str]]:
    """Resolve a registered command and serialize its trusted wire message for queueing."""
    command = installed_commands().get(command_id)
    if command is None:
        raise ValueError(f"Unsupported custom command identifier: {command_id}")
    if not isinstance(parameters, dict):
        raise ValueError("custom command parameters must be an object")
    request = command.validate(parameters)
    message = command.build_message(agent_id, request)
    if not isinstance(message, opamp_pb2.CustomMessage):
        raise TypeError("custom command builder must return CustomMessage")
    if message.capability != command.capability:
        raise ValueError("custom command builder returned a different capability")
    if not message.type:
        raise ValueError("custom command builder returned an empty message type")
    return command_id, {
        COMMAND_ID_KEY: command_id,
        WIRE_CAPABILITY_KEY: message.capability,
        WIRE_TYPE_KEY: message.type,
        WIRE_DATA_KEY: base64.b64encode(message.data).decode("ascii"),
    }


def queued_message(values: dict[str, str]) -> opamp_pb2.CustomMessage:
    """Rebuild a provider-generated message from a queued command record."""
    identifier = values[COMMAND_ID_KEY]
    command = installed_commands().get(identifier)
    if command is None or values[WIRE_CAPABILITY_KEY] != command.capability:
        raise ValueError("queued custom command is no longer registered")
    return opamp_pb2.CustomMessage(
        capability=command.capability,
        type=values[WIRE_TYPE_KEY],
        data=base64.b64decode(values[WIRE_DATA_KEY], validate=True),
    )


def dispatch_result(agent_id: str, message: opamp_pb2.CustomMessage) -> None:
    """Route an authenticated result to its owner and isolate callback failures."""
    for command in installed_commands().values():
        if command.capability == message.capability:
            try:
                command.handle_result(agent_id, message)
            except Exception:  # pylint: disable=broad-exception-caught
                logging.getLogger(__name__).exception(
                    "Custom command result callback failed capability=%s agent_id=%s",
                    message.capability,
                    agent_id,
                )
            return


__all__ = [
    "CustomCommandABC",
    "LegacyCustomCommandAdapter",
    "installed_commands",
    "prepare_command",
    "queued_message",
    "dispatch_result",
]
