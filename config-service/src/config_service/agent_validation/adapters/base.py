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

from __future__ import annotations

import logging
import platform
import shlex
from abc import ABC, abstractmethod
from pathlib import Path
from string import Template
from typing import Any

from config_service.agent_validation.exceptions import AgentCommandBuildError
from config_service.agent_validation.models import ValidationAgentEntry

PLACEHOLDER_CONFIG_PATH = "{config_path}"
PLACEHOLDER_CONFIG_TEXT = "{config_text}"
REPLACEMENT_KEY_CONFIG_PATH = "config_path"
REPLACEMENT_KEY_CONFIG_TEXT = "config_text"
ERR_COMMAND_PATH_REQUIRED = "Validation agent command_path is empty."
ERR_CONFIG_PATH_REQUIRED = (
    "Command entry requires {config_path}, but no file path was provided."
)
ERR_CONFIG_TEXT_REQUIRED = (
    "Command entry requires {config_text}, but no config text was provided."
)
RESULT_KEY_MESSAGES = "messages"
LOGGER = logging.getLogger(__name__)


class AgentValidationAdapter(ABC):
    """Adapter abstraction for different agent-specific command/result behaviors."""

    @abstractmethod
    def create_command(
        self,
        *,
        config_text: str | None,
        config_path: Path | None,
        entry: ValidationAgentEntry,
    ) -> str:
        """
        Build an executable command string from config input and entry metadata.

        Implementations should raise AgentCommandBuildError for unsupported inputs.
        """

    @abstractmethod
    def interpret_result(self, result_text: str) -> dict[str, Any]:
        """Convert raw process text output into a JSON-serializable structure."""


class TemplateCommandAdapter(AgentValidationAdapter):
    """
    Default adapter for command-line validators.

    Supports placeholders in command args:
    - `{config_path}`: absolute path to rendered temporary or explicit config file
    - `{config_text}`: full config content (quoted for shell safety)
    """

    def _argument_uses_config_path(self, arg: str) -> bool:
        return PLACEHOLDER_CONFIG_PATH in str(arg)

    def _argument_uses_config_text(self, arg: str) -> bool:
        return PLACEHOLDER_CONFIG_TEXT in str(arg)

    def _quote(self, value: str) -> str:
        if platform.system().lower() == "windows":
            # Keep quoting behavior consistent with subprocess on Windows shells.
            return '"' + str(value).replace('"', '\\"') + '"'
        return shlex.quote(str(value))

    def _expand_argument(self, arg: str, *, config_text: str | None, config_path: Path | None) -> str:
        if PLACEHOLDER_CONFIG_PATH in arg and config_path is None:
            LOGGER.error(
                "command argument expansion failed because config_path placeholder was present without a file path arg=%s",
                arg,
            )
            raise AgentCommandBuildError(ERR_CONFIG_PATH_REQUIRED)
        if PLACEHOLDER_CONFIG_TEXT in arg and config_text is None:
            LOGGER.error(
                "command argument expansion failed because config_text placeholder was present without config text arg=%s",
                arg,
            )
            raise AgentCommandBuildError(ERR_CONFIG_TEXT_REQUIRED)
        replacements = {
            REPLACEMENT_KEY_CONFIG_PATH: str(config_path) if config_path is not None else "",
            REPLACEMENT_KEY_CONFIG_TEXT: str(config_text or ""),
        }
        expanded = Template(arg.replace("{", "${")).safe_substitute(replacements)
        LOGGER.debug(
            "expanded validation command argument uses_config_path=%s uses_config_text=%s",
            self._argument_uses_config_path(arg),
            self._argument_uses_config_text(arg),
        )
        return expanded

    def create_command(
        self,
        *,
        config_text: str | None,
        config_path: Path | None,
        entry: ValidationAgentEntry,
    ) -> str:
        command_path = str(entry.command_path or "").strip()
        raw_args = [str(arg) for arg in entry.command_args]
        LOGGER.info(
            "building validation command adapter=%s agent_type=%s agent_version=%s command_path=%s arg_count=%s has_config_text=%s has_config_path=%s uses_config_text_placeholder=%s uses_config_path_placeholder=%s",
            self.__class__.__name__,
            entry.agent_type,
            entry.agent_version,
            command_path,
            len(raw_args),
            config_text is not None,
            config_path is not None,
            any(self._argument_uses_config_text(arg) for arg in raw_args),
            any(self._argument_uses_config_path(arg) for arg in raw_args),
        )
        if not command_path:
            LOGGER.error(
                "validation command build failed because command_path is empty adapter=%s agent_type=%s",
                self.__class__.__name__,
                entry.agent_type,
            )
            raise AgentCommandBuildError(ERR_COMMAND_PATH_REQUIRED)

        parts: list[str] = [self._quote(command_path)]
        for arg in raw_args:
            expanded = self._expand_argument(
                arg,
                config_text=config_text,
                config_path=config_path,
            )
            parts.append(self._quote(expanded))
        command = " ".join(parts)
        LOGGER.info(
            "validation command built adapter=%s agent_type=%s arg_count=%s",
            self.__class__.__name__,
            entry.agent_type,
            len(raw_args),
        )
        return command

    def interpret_result(self, result_text: str) -> dict[str, Any]:
        raw_text = str(result_text or "")
        LOGGER.info(
            "interpreting validation result adapter=%s raw_length=%s",
            self.__class__.__name__,
            len(raw_text),
        )
        messages = [
            line.strip()
            for line in raw_text.replace("\r\n", "\n").split("\n")
            if line.strip()
        ]
        if not raw_text.strip():
            LOGGER.warning(
                "validation result was empty adapter=%s",
                self.__class__.__name__,
            )
        elif not messages:
            LOGGER.warning(
                "validation result contained only blank lines adapter=%s",
                self.__class__.__name__,
            )
        LOGGER.info(
            "interpreted validation result adapter=%s message_count=%s",
            self.__class__.__name__,
            len(messages),
        )
        return {
            RESULT_KEY_MESSAGES: messages,
        }
