#!/usr/bin/env python3
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

"""Provider command object for queued AgentRemoteConfig offers."""

from __future__ import annotations

from datetime import datetime, timezone

from opamp_provider.command_interface import (
    CommandObjectInterface,
    CommandParameterSchemaInterface,
)


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class RemoteConfigOfferCommand(CommandObjectInterface, CommandParameterSchemaInterface):
    """Concrete command-style helper that describes queued remote-config offers."""

    def __init__(
        self,
        *,
        command_time: datetime | None = None,
        key_values: dict[str, str] | None = None,
    ) -> None:
        """Initialize default routing metadata and optional key/value context."""
        self._command_time = command_time or _utc_now()
        merged = self._default_key_values()
        if key_values:
            merged.update(key_values)
        self._key_values = merged

    def _default_key_values(self) -> dict[str, str]:
        """Return default metadata describing this remote-config offer."""
        return {
            "classifier": "remote_config",
            "action": "apply_config",
        }

    def get_command_classifier(self) -> str:
        """Return provider routing classifier metadata."""
        return "remote_config"

    def get_command_time(self) -> datetime:
        """Return command creation time."""
        return self._command_time

    def get_command_description(self) -> str:
        """Return a human-readable command description."""
        return "Queue AgentRemoteConfig offer"

    def getdisplayname(self) -> str:
        """Return a provider-facing command display name."""
        return "Remote Config Offer"

    def set_key_value_dictionary(self, key_values: dict[str, str]) -> None:
        """Replace metadata values while preserving defaults."""
        merged = self._default_key_values()
        merged.update(key_values)
        self._key_values = merged

    def get_key_value_dictionary(self) -> dict[str, str]:
        """Return a copy of stored metadata values."""
        return dict(self._key_values)

    def get_capability_fqdn(self) -> str | None:
        """Return no custom capability because this is not a custom command."""
        return None

    def isOpAMPStandard(self) -> bool:
        """Return whether this is an OpAMP-standard command."""
        return False

    def get_user_parameter_schema(self) -> list[dict[str, str | bool]]:
        """Return minimal parameter metadata for request discovery."""
        return [
            {
                "parametername": "files",
                "type": "array",
                "description": "List of source config files to include in the remote offer.",
                "isrequired": True,
            },
            {
                "parametername": "validation",
                "type": "object",
                "description": "Optional config-editor validation hints.",
                "isrequired": False,
            },
        ]
