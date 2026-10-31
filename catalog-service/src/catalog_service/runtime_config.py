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

import os
import sys
from pathlib import Path
from typing import Any

ROOT_PATH = Path(__file__).resolve().parents[3]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from shared.opamp_config import CFG_COMPONENT_ENTRY_POINTS_QUART, ComponentEntryPoint, resolve_component_entry_points_from_payload
from shared.observability import ObservabilityConfig, load_observability_config_from_payload

from catalog_service.config import (
    catalog_component_entry_from_payload,
    load_catalog_service_config,
)

ENV_CATALOG_SERVICE_CONFIG_PATH = "CATALOG_SERVICE_CONFIG_PATH"
ENV_OPAMP_CONFIG_PATH = "OPAMP_CONFIG_PATH"
ENV_CATALOG_SERVICE_WEB_PORT = "CATALOG_SERVICE_WEB_PORT"
DEFAULT_CATALOG_SERVICE_CONFIG_PATH = "catalog-service.json"
DEFAULT_CATALOG_SERVICE_WEB_PORT = 8090


def _component_root() -> Path:
    """Return the deployed or source-root folder for the catalog component."""
    module_dir = Path(__file__).resolve().parent
    source_root = module_dir.parents[1]
    if (source_root / "config").is_dir():
        return source_root
    for candidate in (module_dir, Path(sys.prefix) / "catalog_service"):
        if (candidate / "config").is_dir():
            return candidate
    return source_root


def _repo_root() -> Path:
    return _component_root().parent


def get_effective_config_path(config_path: str | None = None) -> Path:
    """Return the active runtime config path for standalone catalog launches."""
    configured = str(config_path or "").strip()
    if configured:
        return Path(configured)

    for env_name in (ENV_CATALOG_SERVICE_CONFIG_PATH, ENV_OPAMP_CONFIG_PATH):
        configured = os.environ.get(env_name, "").strip()
        if configured:
            return Path(configured)

    default_component_path = _component_root() / "config" / DEFAULT_CATALOG_SERVICE_CONFIG_PATH
    if default_component_path.is_file():
        return default_component_path

    return _repo_root() / "config" / "opamp.json"


def _coerce_port(value: Any, default: int) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError):
        return default
    return port if port > 0 else default


def resolve_component_entry_points(config_path: str | None = None) -> list[str]:
    """Return Quart component entrypoints to register for the catalog app."""
    entries = resolve_component_entries(config_path)
    return [entry.entry_point for entry in entries]


def resolve_component_entries(config_path: str | None = None) -> list[ComponentEntryPoint]:
    """Return structured Quart component entries for the catalog app."""
    config = load_catalog_service_config(config_path=get_effective_config_path(config_path))
    payload = config.raw_payload
    entries = resolve_component_entry_points_from_payload(
        payload,
        runtime_key=CFG_COMPONENT_ENTRY_POINTS_QUART,
        default_entry_points=(),
    )
    if entries:
        return entries
    default_entry = catalog_component_entry_from_payload(payload)
    if default_entry is not None:
        return [default_entry]
    return []


def resolve_web_port(config_path: str | None = None) -> int:
    """Return the standalone catalog web port from environment or config."""
    env_value = os.environ.get(ENV_CATALOG_SERVICE_WEB_PORT, "").strip()
    if env_value:
        return _coerce_port(env_value, DEFAULT_CATALOG_SERVICE_WEB_PORT)

    config = load_catalog_service_config(config_path=get_effective_config_path(config_path))
    if config.web_port:
        return _coerce_port(config.web_port, DEFAULT_CATALOG_SERVICE_WEB_PORT)
    return DEFAULT_CATALOG_SERVICE_WEB_PORT


def resolve_observability_config(config_path: str | None = None) -> ObservabilityConfig:
    """Return normalized OTLP endpoint settings for catalog-service."""
    config = load_catalog_service_config(config_path=get_effective_config_path(config_path))
    return load_observability_config_from_payload(config.raw_payload)
