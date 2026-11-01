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
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from config_service.agent_validation.adapters import (
    AgentValidationAdapter,
    FluentBitValidationAdapter,
    FluentdValidationAdapter,
    TemplateCommandAdapter,
)
from config_service.agent_validation.exceptions import (
    AgentAdapterNotSupportedError,
    AgentConfigError,
    AgentNotSupportedError,
)
from config_service.agent_validation.models import ValidationAgentEntry
from config_service.runtime_config import resolve_validation_agent_entries

CFG_KEY_AGENT_TYPE = "agent_type"
CFG_KEY_AGENT_VERSION = "agent_version"
CFG_KEY_COMMAND_PATH = "command_path"
CFG_KEY_COMMAND_ARGS = "command_args"
CFG_KEY_SUCCESS_EXIT_CODES = "success_exit_codes"
CFG_KEY_ENVIRONMENT = "environment"
CFG_KEY_ADAPTER = "adapter"
CFG_KEY_SEND_CONFIG_VIA_STDIN = "send_config_via_stdin"
CFG_KEY_WORKING_DIRECTORY = "working_directory"
CFG_KEY_DRY_RUN_VALIDATION_ENABLED = "dry_run_validation_enabled"

KEY_MESSAGES = "messages"
KEY_OK = "ok"
KEY_AVAILABLE = "available"
KEY_REASON = "reason"
KEY_AGENT_TYPE = "agent_type"
KEY_REQUESTED_AGENT_VERSION = "requested_agent_version"
KEY_USED_AGENT_VERSION = "used_agent_version"
KEY_VERSION_MISMATCH = "version_mismatch"
KEY_COMMAND = "command"
KEY_EXIT_CODE = "exit_code"
KEY_STDOUT = "stdout"
KEY_STDERR = "stderr"
KEY_INTERPRETER_PAYLOAD = "interpreter_payload"

AGENT_TYPE_FLUENTBIT = "fluentbit"
AGENT_TYPE_FLUENTD = "fluentd"
ADAPTER_KEY_GENERIC = "generic"

LOGGER = logging.getLogger(__name__)


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


class ValidationAgentRegistry:
    """Loaded external validation entries with type/version matching rules."""

    def __init__(self, entries: list[ValidationAgentEntry]) -> None:
        self._entries = entries

    @property
    def entries(self) -> list[ValidationAgentEntry]:
        return list(self._entries)

    @classmethod
    def from_config_payload(cls, payload: list[dict[str, Any]]) -> ValidationAgentRegistry:
        entries: list[ValidationAgentEntry] = []
        for index, item in enumerate(payload):
            if not isinstance(item, dict):
                raise AgentConfigError(f"validation_agents[{index}] must be an object.")

            agent_type = _normalize_text(item.get(CFG_KEY_AGENT_TYPE))
            command_path = _normalize_text(item.get(CFG_KEY_COMMAND_PATH))
            if not agent_type:
                raise AgentConfigError(f"validation_agents[{index}].{CFG_KEY_AGENT_TYPE} is required.")
            if not command_path:
                raise AgentConfigError(f"validation_agents[{index}].{CFG_KEY_COMMAND_PATH} is required.")

            raw_args = item.get(CFG_KEY_COMMAND_ARGS, [])
            if isinstance(raw_args, str):
                command_args = [_normalize_text(raw_args)] if _normalize_text(raw_args) else []
            elif isinstance(raw_args, list):
                command_args = [_normalize_text(arg) for arg in raw_args if _normalize_text(arg)]
            else:
                raise AgentConfigError(
                    f"validation_agents[{index}].{CFG_KEY_COMMAND_ARGS} must be a string or array of strings."
                )

            raw_codes = item.get(CFG_KEY_SUCCESS_EXIT_CODES, [0])
            if isinstance(raw_codes, list):
                success_exit_codes: list[int] = []
                for code in raw_codes:
                    try:
                        success_exit_codes.append(int(code))
                    except (TypeError, ValueError) as exc:
                        raise AgentConfigError(
                            f"validation_agents[{index}].{CFG_KEY_SUCCESS_EXIT_CODES} has invalid value: {code!r}"
                        ) from exc
                if not success_exit_codes:
                    success_exit_codes = [0]
            else:
                raise AgentConfigError(
                    f"validation_agents[{index}].{CFG_KEY_SUCCESS_EXIT_CODES} must be an array of integers."
                )

            raw_env = item.get(CFG_KEY_ENVIRONMENT, {})
            if raw_env is None:
                raw_env = {}
            if not isinstance(raw_env, dict):
                raise AgentConfigError(
                    f"validation_agents[{index}].{CFG_KEY_ENVIRONMENT} must be an object map."
                )
            environment = {_normalize_text(key): _normalize_text(value) for key, value in raw_env.items()}
            environment = {key: value for key, value in environment.items() if key}

            entry = ValidationAgentEntry(
                agent_type=agent_type,
                agent_version=_normalize_text(item.get(CFG_KEY_AGENT_VERSION)) or None,
                command_path=command_path,
                command_args=command_args,
                adapter=_normalize_text(item.get(CFG_KEY_ADAPTER)) or None,
                send_config_via_stdin=_coerce_bool(item.get(CFG_KEY_SEND_CONFIG_VIA_STDIN), False),
                environment=environment,
                working_directory=_normalize_text(item.get(CFG_KEY_WORKING_DIRECTORY)) or None,
                success_exit_codes=success_exit_codes,
                dry_run_validation_enabled=_coerce_bool(
                    item.get(CFG_KEY_DRY_RUN_VALIDATION_ENABLED),
                    True,
                ),
            )
            entries.append(entry)
        return cls(entries)

    @classmethod
    def from_runtime_config(cls, config_path: str | None = None) -> ValidationAgentRegistry:
        return cls.from_config_payload(resolve_validation_agent_entries(config_path))

    def resolve(
        self,
        agent_type: str,
        agent_version: str | None,
        *,
        require_dry_run_enabled: bool = False,
    ) -> tuple[ValidationAgentEntry, bool]:
        normalized_type = _normalize_text(agent_type).lower()
        normalized_requested_version = _normalize_text(agent_version) or None
        if not normalized_type:
            raise AgentNotSupportedError("Agent type is required.")

        by_type = [item for item in self._entries if item.normalized_agent_type == normalized_type]
        if not by_type:
            raise AgentNotSupportedError(
                f"No validation agent entries configured for agent_type '{agent_type}'."
            )
        if require_dry_run_enabled:
            by_type = [item for item in by_type if item.dry_run_validation_enabled]
            if not by_type:
                raise AgentNotSupportedError(
                    f"No dry-run enabled validation agent entries configured for agent_type '{agent_type}'."
                )

        if normalized_requested_version:
            exact_matches = [
                item for item in by_type if item.normalized_agent_version == normalized_requested_version
            ]
            if exact_matches:
                return exact_matches[0], True

        fallback_matches = [item for item in by_type if item.normalized_agent_version is None]
        if fallback_matches:
            return fallback_matches[0], False

        available_versions = sorted(
            {item.normalized_agent_version for item in by_type if item.normalized_agent_version}
        )
        raise AgentNotSupportedError(
            "No compatible validation agent entry found for "
            f"agent_type '{agent_type}' and agent_version '{normalized_requested_version}'. "
            f"Available configured versions: {available_versions}"
        )


class ExternalAgentValidationService:
    """Validate config text by delegating execution to configured external agents."""

    def __init__(
        self,
        registry: ValidationAgentRegistry,
        adapters: dict[str, AgentValidationAdapter] | None = None,
    ) -> None:
        self._registry = registry
        self._adapters = adapters or {
            AGENT_TYPE_FLUENTBIT: FluentBitValidationAdapter(),
            AGENT_TYPE_FLUENTD: FluentdValidationAdapter(),
            ADAPTER_KEY_GENERIC: TemplateCommandAdapter(),
        }

    @classmethod
    def from_runtime_config(cls, config_path: str | None = None) -> ExternalAgentValidationService:
        return cls(ValidationAgentRegistry.from_runtime_config(config_path))

    def _adapter_for_entry(self, entry: ValidationAgentEntry) -> AgentValidationAdapter:
        adapter_key = _normalize_text(entry.adapter_key).lower()
        if adapter_key in self._adapters:
            return self._adapters[adapter_key]
        if entry.normalized_agent_type in self._adapters:
            return self._adapters[entry.normalized_agent_type]
        if ADAPTER_KEY_GENERIC in self._adapters:
            return self._adapters[ADAPTER_KEY_GENERIC]
        raise AgentAdapterNotSupportedError(
            f"No adapter registered for '{entry.adapter_key}' / '{entry.normalized_agent_type}'."
        )

    def _default_suffix_for_type(self, agent_type: str) -> str:
        normalized = _normalize_text(agent_type).lower()
        if normalized == AGENT_TYPE_FLUENTBIT:
            return ".yaml"
        if normalized == AGENT_TYPE_FLUENTD:
            return ".conf"
        return ".txt"

    def validate(
        self,
        config_text: str,
        agent_type: str,
        agent_version: str | None = None,
        *,
        config_path: str | Path | None = None,
        require_dry_run_enabled: bool = False,
    ) -> dict[str, Any]:
        entry, version_match = self._registry.resolve(
            agent_type,
            agent_version,
            require_dry_run_enabled=require_dry_run_enabled,
        )
        adapter = self._adapter_for_entry(entry)

        normalized_config_text = str(config_text or "")
        explicit_path = Path(config_path).resolve() if config_path else None
        temp_path: Path | None = None
        selected_path: Path | None = explicit_path
        if selected_path is None and not entry.send_config_via_stdin:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=self._default_suffix_for_type(entry.agent_type),
                delete=False,
            ) as temp_file:
                temp_file.write(normalized_config_text)
                temp_path = Path(temp_file.name)
            selected_path = temp_path

        try:
            command = adapter.create_command(
                config_text=normalized_config_text,
                config_path=selected_path,
                entry=entry,
            )
            if require_dry_run_enabled:
                LOGGER.info(
                    "Dry-run validation command prepared: agent_type=%s requested_version=%s used_version=%s command=%s",
                    entry.agent_type,
                    agent_version,
                    entry.agent_version,
                    command,
                )
            process = subprocess.run(
                command,
                shell=True,
                check=False,
                capture_output=True,
                text=True,
                input=(normalized_config_text if entry.send_config_via_stdin else None),
                cwd=entry.working_directory or None,
                env={**os.environ, **entry.environment},
            )
            result_text = "\n".join(
                value for value in [process.stdout.strip(), process.stderr.strip()] if value
            )
            interpreted = adapter.interpret_result(result_text)
            messages = interpreted.get(KEY_MESSAGES, [])
            if not isinstance(messages, list):
                messages = [str(messages)]
            interpreted_ok = interpreted.get(KEY_OK)
            success = process.returncode in entry.success_exit_codes
            if isinstance(interpreted_ok, bool):
                success = success and interpreted_ok
            if require_dry_run_enabled:
                LOGGER.info(
                    "Dry-run validation result: ok=%s exit_code=%s agent_type=%s requested_version=%s used_version=%s messages=%s",
                    success,
                    process.returncode,
                    entry.agent_type,
                    agent_version,
                    entry.agent_version,
                    messages,
                )

            return {
                KEY_OK: success,
                KEY_MESSAGES: [str(message) for message in messages],
                KEY_AGENT_TYPE: entry.agent_type,
                KEY_REQUESTED_AGENT_VERSION: agent_version,
                KEY_USED_AGENT_VERSION: entry.agent_version,
                KEY_VERSION_MISMATCH: bool(agent_version) and not version_match,
                KEY_COMMAND: command,
                KEY_EXIT_CODE: process.returncode,
                KEY_STDOUT: process.stdout,
                KEY_STDERR: process.stderr,
                KEY_INTERPRETER_PAYLOAD: {
                    key: value for key, value in interpreted.items() if key not in {KEY_MESSAGES, KEY_OK}
                },
            }
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink(missing_ok=True)

    def dry_run_capability(self, *, agent_type: str, agent_version: str | None = None) -> dict[str, Any]:
        try:
            entry, version_match = self._registry.resolve(
                agent_type=agent_type,
                agent_version=agent_version,
                require_dry_run_enabled=True,
            )
        except AgentNotSupportedError as exc:
            return {
                KEY_AVAILABLE: False,
                KEY_REASON: str(exc),
            }
        return {
            KEY_AVAILABLE: True,
            KEY_AGENT_TYPE: entry.agent_type,
            KEY_REQUESTED_AGENT_VERSION: agent_version,
            KEY_USED_AGENT_VERSION: entry.agent_version,
            KEY_VERSION_MISMATCH: bool(agent_version) and not version_match,
        }
