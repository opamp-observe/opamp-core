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

"""Runtime configuration resolution for the client config generator service."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ENV_CONFIG_PATH = "CLIENT_CONFIG_GENERATOR_CONFIG_PATH"
ENV_OPAMP_CONFIG_PATH = "OPAMP_CONFIG_PATH"
ENV_CONFIGURATION_DIRECTORY = "CLIENT_CONFIG_GENERATOR_CONFIG_DIR"
ENV_LOG_LEVEL = "CLIENT_CONFIG_GENERATOR_LOG_LEVEL"
ENV_READ_ONLY = "CLIENT_CONFIG_GENERATOR_READ_ONLY"
ENV_WEB_PORT = "CLIENT_CONFIG_GENERATOR_WEB_PORT"

KEY_OPAMP = "opamp"
KEY_COMPONENT = "client_config_generator"
KEY_STORAGE = "storage"
KEY_CONFIGURATION_DIRECTORY = "configuration_directory"
KEY_READ_ONLY = "read_only"
KEY_WEB_PORT = "web_port"
KEY_LOG_LEVEL = "log_level"

DEFAULT_CONFIG_FILENAME = "client-config-generator-service.json"
DEFAULT_CONFIGURATION_DIRECTORY = "generated-client-configs"
DEFAULT_LOG_LEVEL = "DEBUG"
DEFAULT_WEB_PORT = 8095
TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}

APP_EXTENSION_CONFIG_PATH = "client_config_generator_service:config_path"
APP_EXTENSION_SERVICE = "client_config_generator_service:file_service"
APP_CONFIG_MODE = "CLIENT_CONFIG_GENERATOR_MODE"
APP_MODE_STANDALONE = "standalone"


@dataclass(frozen=True)
class GeneratorSettings:
    """Effective settings used to host and persist generated client configurations."""

    config_path: Path  # Source JSON file used to resolve relative settings.
    configuration_directory: Path  # Allowed directory for generated JSON files.
    read_only: bool  # Whether API mutations are disabled.
    web_port: int  # Standalone HTTP listen port.
    log_level: str  # Python logging level name.


def component_root() -> Path:
    """Return the installed package root containing bundled assets."""
    return Path(__file__).resolve().parent


def default_config_path() -> Path:
    """Return the packaged standalone configuration path."""
    return component_root() / "config" / DEFAULT_CONFIG_FILENAME


def resolve_config_path(config_path: str | Path | None = None) -> Path:
    """Resolve the runtime config path from an argument, environment, or package default.

    Args:
        config_path: Optional explicit configuration path supplied by the caller.
    """
    explicit_value = str(config_path or "").strip()
    if explicit_value:
        return Path(explicit_value).expanduser().resolve()
    for environment_name in (ENV_CONFIG_PATH, ENV_OPAMP_CONFIG_PATH):
        environment_value = os.environ.get(environment_name, "").strip()
        if environment_value:
            return Path(environment_value).expanduser().resolve()
    return default_config_path().resolve()


def load_config_payload(config_path: Path) -> dict[str, Any]:
    """Load one JSON object, returning an empty object for missing standalone config.

    Args:
        config_path: JSON file to read.
    """
    if not config_path.is_file():
        return {}
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("client config generator configuration must be a JSON object")
    return payload


def _component_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the shared ``opamp.client_config_generator`` settings object.

    Args:
        payload: Loaded root OpAMP configuration object.
    """
    opamp_payload = payload.get(KEY_OPAMP, {})
    if not isinstance(opamp_payload, dict):
        return {}
    component_payload = opamp_payload.get(KEY_COMPONENT, {})
    return component_payload if isinstance(component_payload, dict) else {}


def _coerce_bool(value: Any, default: bool = False) -> bool:
    """Normalize common JSON and environment boolean forms.

    Args:
        value: Candidate boolean value.
        default: Fallback used for absent or unrecognized values.
    """
    if isinstance(value, bool):
        return value
    normalized_value = str(value or "").strip().lower()
    if normalized_value in TRUE_VALUES:
        return True
    if normalized_value in FALSE_VALUES:
        return False
    return default


def _coerce_port(value: Any) -> int:
    """Return a positive port or the component default.

    Args:
        value: Candidate port value from JSON or the environment.
    """
    try:
        parsed_port = int(value)
    except (TypeError, ValueError):
        return DEFAULT_WEB_PORT
    return parsed_port if parsed_port > 0 else DEFAULT_WEB_PORT


def load_settings(config_path: str | Path | None = None) -> GeneratorSettings:
    """Resolve settings with environment variables taking highest precedence.

    Args:
        config_path: Optional explicit runtime JSON path.
    """
    effective_path = resolve_config_path(config_path)
    payload = load_config_payload(effective_path)
    component_payload = _component_payload(payload)
    storage_payload = component_payload.get(KEY_STORAGE, {})
    if not isinstance(storage_payload, dict):
        storage_payload = {}

    configured_directory = os.environ.get(ENV_CONFIGURATION_DIRECTORY, "").strip()
    if not configured_directory:
        configured_directory = str(
            storage_payload.get(KEY_CONFIGURATION_DIRECTORY, DEFAULT_CONFIGURATION_DIRECTORY)
        ).strip()
    directory_path = Path(configured_directory or DEFAULT_CONFIGURATION_DIRECTORY).expanduser()
    if not directory_path.is_absolute():
        directory_path = effective_path.parent / directory_path

    read_only_value: Any = component_payload.get(KEY_READ_ONLY, False)
    if ENV_READ_ONLY in os.environ:
        read_only_value = os.environ[ENV_READ_ONLY]
    web_port_value: Any = component_payload.get(KEY_WEB_PORT, DEFAULT_WEB_PORT)
    if ENV_WEB_PORT in os.environ:
        web_port_value = os.environ[ENV_WEB_PORT]
    log_level_value = os.environ.get(
        ENV_LOG_LEVEL,
        str(component_payload.get(KEY_LOG_LEVEL, DEFAULT_LOG_LEVEL)),
    )

    return GeneratorSettings(
        config_path=effective_path,
        configuration_directory=directory_path.resolve(),
        read_only=_coerce_bool(read_only_value),
        web_port=_coerce_port(web_port_value),
        log_level=str(log_level_value or DEFAULT_LOG_LEVEL).strip().upper(),
    )
