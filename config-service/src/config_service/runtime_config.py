#!/usr/bin/env python3
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

"""Resolve config-service runtime settings and environment overrides."""

# Repository checkout imports intentionally follow the shared-package path bootstrap below.
# ruff: noqa: E402

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from quart import current_app, has_app_context

ROOT_PATH = Path(__file__).resolve().parents[3]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from shared.observability import ObservabilityConfig, load_observability_config_from_payload
from shared.opamp_config import (
    CFG_COMPONENT_ENTRY_POINTS_QUART,
    load_json_config,
    resolve_component_entry_points_from_payload,
)

ENV_CONFIG_TOOL_CONFIG_PATH = "CONFIG_TOOL_CONFIG_PATH"
ENV_OPAMP_CONFIG_PATH = "OPAMP_CONFIG_PATH"
ENV_CONFIG_SERVICE_WEB_PORT = "CONFIG_SERVICE_WEB_PORT"
ENV_CONFIG_SERVICE_UI_BASE_CSS_PATH = "CONFIG_SERVICE_UI_BASE_CSS_PATH"
ENV_CONFIG_SERVICE_UI_SHOW_SAVE_AS = "CONFIG_SERVICE_UI_SHOW_SAVE_AS"
ENV_CONFIG_SERVICE_SAVE_IGNORE_VALIDATION = "CONFIG_SERVICE_SAVE_IGNORE_VALIDATION"
ENV_CONFIG_SERVICE_SAVE_INGORE_VALIDATION = "CONFIG_SERVICE_SAVE_INGORE_VALIDATION"
ENV_CONFIG_TOOL_LOG_LEVEL = "CONFIG_TOOL_LOG_LEVEL"
CFG_CONFIG_TOOL = "config-tool"
CFG_CONFIG_TOOL_WEB_PORT = "web_port"
CFG_CONFIG_TOOL_UI_BASE_CSS_PATH = "ui_base_css_path"
CFG_CONFIG_TOOL_UI_SHOW_SAVE_AS = "ui_show_save_as"
CFG_CONFIG_TOOL_SAVE_IGNORE_VALIDATION = "save_ignore_validation"
CFG_CONFIG_TOOL_SAVE_INGORE_VALIDATION = "save_ingore_validation"
CFG_CONFIG_TOOL_SAVE_IGNORE_VALIDATION_HYPHEN = "save-ignore-validation"
CFG_CONFIG_TOOL_SAVE_INGORE_VALIDATION_HYPHEN = "save-ingore-validation"
CFG_CONFIG_TOOL_LOG_LEVEL = "log_level"
CFG_CONFIG_TOOL_UI_CSS_OVERRIDES = "ui_css_overrides"
CFG_CONFIG_TOOL_UI_COLLAPSED_SECTIONS = "ui_collapsed_sections"
CFG_CONFIG_TOOL_READ_ONLY = "read_only"
CFG_CONFIG_TOOL_AGENT_VALIDATION = "agent_validation"
CFG_CONFIG_TOOL_AGENT_VALIDATION_ENTRIES = "entries"
CFG_CONFIG_SERVICE = "config_service"
CFG_CONFIG_SERVICE_WEB_PORT = "web_port"
CFG_CONFIG_SERVICE_UI_BASE_CSS_PATH = "ui_base_css_path"
CFG_PROVIDER = "provider"
CFG_PROVIDER_LOG_LEVEL = "log_level"
CFG_PROVIDER_WEBUI_PORT = "webui_port"
DEFAULT_CONFIG_SERVICE_WEB_PORT = 8080
DEFAULT_CONFIG_SERVICE_UI_BASE_CSS_PATH = "/config-service/ui/assets/config_ui.css"
DEFAULT_COMPONENT_ENTRY_POINTS = [
    "opamp_tools.config_app:register_api_component",
    "opamp_tools.config_app:register_ui_component",
]
DEFAULT_CONFIG_TOOL_CONFIG_PATH = "config-service.json"
DEFAULT_CONFIG_TOOL_LOG_LEVEL = "INFO"
APP_EXTENSION_CONFIG_PATH = "config_service:config_path"


def _config_service_root() -> Path:
    """Resolve packaged assets before considering a legacy repository-level tree."""
    module_dir = Path(__file__).resolve().parent
    source_root = module_dir.parents[1]
    for candidate in (module_dir, source_root, Path(sys.prefix) / "config_service"):
        if (candidate / "config").is_dir() and (candidate / "json-definitions").is_dir():
            return candidate
    return source_root


def _repo_root() -> Path:
    return _config_service_root().parent


def _config_path_from_app_context() -> Path | None:
    if has_app_context() is not True:
        return None
    configured = str(current_app.extensions.get(APP_EXTENSION_CONFIG_PATH) or "").strip()
    if configured:
        return Path(configured)
    return None


def get_effective_config_path(config_path: str | None = None) -> Path:
    configured = str(config_path or "").strip()
    if configured:
        return Path(configured)

    app_config_path = _config_path_from_app_context()
    if app_config_path is not None:
        return app_config_path

    configured = os.environ.get(ENV_CONFIG_TOOL_CONFIG_PATH, "").strip()
    if configured:
        return Path(configured)

    configured = os.environ.get(ENV_OPAMP_CONFIG_PATH, "").strip()
    if configured:
        return Path(configured)

    default_tool_path = _config_service_root() / "config" / DEFAULT_CONFIG_TOOL_CONFIG_PATH
    if default_tool_path.is_file():
        return default_tool_path

    return _repo_root() / "config" / "opamp.json"


def _coerce_port(value: Any, default: int) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError):
        return default
    return port if port > 0 else default


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


def resolve_component_entry_points(config_path: str | None = None) -> list[str]:
    raw = load_json_config(get_effective_config_path(config_path))
    entries = resolve_component_entry_points_from_payload(
        raw,
        runtime_key=CFG_COMPONENT_ENTRY_POINTS_QUART,
        default_entry_points=DEFAULT_COMPONENT_ENTRY_POINTS,
    )
    return [entry.entry_point for entry in entries]


def resolve_web_port(config_path: str | None = None) -> int:
    env_value = os.environ.get(ENV_CONFIG_SERVICE_WEB_PORT, "").strip()
    if env_value:
        return _coerce_port(env_value, DEFAULT_CONFIG_SERVICE_WEB_PORT)

    raw = load_json_config(get_effective_config_path(config_path))
    config_tool_raw = raw.get(CFG_CONFIG_TOOL, {})
    if isinstance(config_tool_raw, dict) and CFG_CONFIG_TOOL_WEB_PORT in config_tool_raw:
        return _coerce_port(
            config_tool_raw.get(CFG_CONFIG_TOOL_WEB_PORT),
            DEFAULT_CONFIG_SERVICE_WEB_PORT,
        )

    config_service_raw = raw.get(CFG_CONFIG_SERVICE, {})
    if isinstance(config_service_raw, dict) and CFG_CONFIG_SERVICE_WEB_PORT in config_service_raw:
        return _coerce_port(
            config_service_raw.get(CFG_CONFIG_SERVICE_WEB_PORT),
            DEFAULT_CONFIG_SERVICE_WEB_PORT,
        )

    provider_raw = raw.get(CFG_PROVIDER, {})
    if isinstance(provider_raw, dict):
        return _coerce_port(
            provider_raw.get(CFG_PROVIDER_WEBUI_PORT),
            DEFAULT_CONFIG_SERVICE_WEB_PORT,
        )

    return DEFAULT_CONFIG_SERVICE_WEB_PORT


def resolve_ui_base_css_path(config_path: str | None = None) -> str:
    env_value = os.environ.get(ENV_CONFIG_SERVICE_UI_BASE_CSS_PATH, "").strip()
    if env_value:
        return env_value

    raw = load_json_config(get_effective_config_path(config_path))
    config_tool_raw = raw.get(CFG_CONFIG_TOOL, {})
    if isinstance(config_tool_raw, dict):
        configured = str(config_tool_raw.get(CFG_CONFIG_TOOL_UI_BASE_CSS_PATH, "")).strip()
        if configured:
            return configured

    config_service_raw = raw.get(CFG_CONFIG_SERVICE, {})
    if isinstance(config_service_raw, dict):
        configured = str(config_service_raw.get(CFG_CONFIG_SERVICE_UI_BASE_CSS_PATH, "")).strip()
        if configured:
            return configured

    return DEFAULT_CONFIG_SERVICE_UI_BASE_CSS_PATH


def resolve_ui_show_save_as(config_path: str | None = None) -> bool:
    env_value = os.environ.get(ENV_CONFIG_SERVICE_UI_SHOW_SAVE_AS, "").strip()
    if env_value:
        return _coerce_bool(env_value, False)

    raw = load_json_config(get_effective_config_path(config_path))
    config_tool_raw = raw.get(CFG_CONFIG_TOOL, {})
    if isinstance(config_tool_raw, dict):
        return _coerce_bool(config_tool_raw.get(CFG_CONFIG_TOOL_UI_SHOW_SAVE_AS), False)
    return False


def resolve_save_ignore_validation(config_path: str | None = None) -> bool:
    for env_name in (
        ENV_CONFIG_SERVICE_SAVE_IGNORE_VALIDATION,
        ENV_CONFIG_SERVICE_SAVE_INGORE_VALIDATION,
    ):
        env_value = os.environ.get(env_name, "").strip()
        if env_value:
            return _coerce_bool(env_value, False)

    raw = load_json_config(get_effective_config_path(config_path))
    config_tool_raw = raw.get(CFG_CONFIG_TOOL, {})
    if not isinstance(config_tool_raw, dict):
        return False
    for key in (
        CFG_CONFIG_TOOL_SAVE_INGORE_VALIDATION_HYPHEN,
        CFG_CONFIG_TOOL_SAVE_INGORE_VALIDATION,
        CFG_CONFIG_TOOL_SAVE_IGNORE_VALIDATION_HYPHEN,
        CFG_CONFIG_TOOL_SAVE_IGNORE_VALIDATION,
    ):
        if key in config_tool_raw:
            return _coerce_bool(config_tool_raw.get(key), False)
    return False


def resolve_ui_css_overrides(config_path: str | None = None) -> list[str]:
    raw = load_json_config(get_effective_config_path(config_path))
    config_tool_raw = raw.get(CFG_CONFIG_TOOL, {})
    if isinstance(config_tool_raw, dict):
        configured = config_tool_raw.get(CFG_CONFIG_TOOL_UI_CSS_OVERRIDES, [])
        if isinstance(configured, str):
            return [value.strip() for value in configured.split(",") if value.strip()]
        if isinstance(configured, list):
            return [str(value).strip() for value in configured if str(value).strip()]
    return []


def resolve_ui_collapsed_sections(config_path: str | None = None) -> list[str]:
    """Return configured UI section keys that should render collapsed by default."""
    raw = load_json_config(get_effective_config_path(config_path))
    config_tool_raw = raw.get(CFG_CONFIG_TOOL, {})
    if isinstance(config_tool_raw, dict):
        configured = config_tool_raw.get(CFG_CONFIG_TOOL_UI_COLLAPSED_SECTIONS, [])
        if isinstance(configured, str):
            return [value.strip() for value in configured.split(",") if value.strip()]
        if isinstance(configured, list):
            return [str(value).strip() for value in configured if str(value).strip()]
    return []


def resolve_read_only(config_path: str | None = None) -> bool:
    raw = load_json_config(get_effective_config_path(config_path))
    config_tool_raw = raw.get(CFG_CONFIG_TOOL, {})
    if isinstance(config_tool_raw, dict):
        return _coerce_bool(config_tool_raw.get(CFG_CONFIG_TOOL_READ_ONLY), False)
    return False


def resolve_validation_agent_entries(config_path: str | None = None) -> list[dict[str, Any]]:
    """
    Return configured external validation agent entries.

    Expected path:
    - `config-tool.agent_validation.entries`
    """
    raw = load_json_config(get_effective_config_path(config_path))
    config_tool_raw = raw.get(CFG_CONFIG_TOOL, {})
    if not isinstance(config_tool_raw, dict):
        return []
    section_raw = config_tool_raw.get(CFG_CONFIG_TOOL_AGENT_VALIDATION, {})
    if not isinstance(section_raw, dict):
        return []
    entries_raw = section_raw.get(CFG_CONFIG_TOOL_AGENT_VALIDATION_ENTRIES, [])
    if not isinstance(entries_raw, list):
        return []
    return [entry for entry in entries_raw if isinstance(entry, dict)]


def resolve_log_level_name(config_path: str | None = None) -> str:
    env_value = os.environ.get(ENV_CONFIG_TOOL_LOG_LEVEL, "").strip()
    if env_value:
        return str(env_value).strip().upper()

    raw = load_json_config(get_effective_config_path(config_path))
    config_tool_raw = raw.get(CFG_CONFIG_TOOL, {})
    if isinstance(config_tool_raw, dict):
        configured = str(config_tool_raw.get(CFG_CONFIG_TOOL_LOG_LEVEL, "")).strip()
        if configured:
            return configured.upper()

    provider_raw = raw.get(CFG_PROVIDER, {})
    if isinstance(provider_raw, dict):
        configured = str(provider_raw.get(CFG_PROVIDER_LOG_LEVEL, "")).strip()
        if configured:
            return configured.upper()

    return DEFAULT_CONFIG_TOOL_LOG_LEVEL


def resolve_observability_config(config_path: str | None = None) -> ObservabilityConfig:
    """Return normalized OTLP endpoint settings for config-service."""
    raw = load_json_config(get_effective_config_path(config_path))
    return load_observability_config_from_payload(raw)
