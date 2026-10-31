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

"""Configuration parsing for standalone and embedded catalog-service feature."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Any

from shared.opamp_config import ComponentEntryPoint, load_json_config

CFG_OPAMP = "opamp"
CFG_CONFIG_CATALOG = "config_catalog"
CFG_ENABLED = "enabled"
CFG_MENU_LABEL = "menu_label"
CFG_ROUTE_PATH = "route_path"
CFG_HELP_PATH = "help_path"
CFG_UI_BASE_CSS_PATH = "ui_base_css_path"
CFG_WEB_PORT = "web_port"
CFG_UI_REFRESH_SECONDS = "ui_refresh_seconds"
CFG_SOURCES = "sources"
CFG_FOLDER = "folder"
CFG_EXTENSIONS = "extensions"

CATALOG_COMPONENT_ENTRY_POINT = "catalog_service.opamp_integration:register_catalog_feature"
DEFAULT_MENU_LABEL = "Config Catalog"
DEFAULT_ROUTE_PATH = "/catalog"
DEFAULT_HELP_PATH = "/catalog/help"
DEFAULT_UI_BASE_CSS_PATH = "/config-service/ui/assets/config_ui.css"
DEFAULT_WEB_PORT = 8090
DEFAULT_UI_REFRESH_SECONDS = 120


@dataclass(frozen=True)
class CatalogSource:
    """One filesystem source directory and extension allow-list."""

    folder: str
    extensions: tuple[str, ...]


@dataclass(frozen=True)
class CatalogServiceConfig:
    """Resolved catalog UI, scanner, and standalone server configuration."""

    enabled: bool
    menu_label: str
    route_path: str
    help_path: str
    ui_base_css_path: str
    web_port: int
    sources: tuple[CatalogSource, ...]
    raw_payload: dict[str, Any]
    ui_refresh_seconds: int = DEFAULT_UI_REFRESH_SECONDS


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


def _normalized_path(value: str, fallback: str) -> str:
    path = str(value or "").strip() or fallback
    if not path.startswith("/"):
        path = "/" + path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return path


def _normalize_extensions(raw: Any) -> tuple[str, ...]:
    if isinstance(raw, str):
        raw = [item.strip() for item in raw.split(",") if item.strip()]
    if not isinstance(raw, list):
        return ()
    normalized: list[str] = []
    for item in raw:
        text = str(item or "").strip().lower()
        if not text:
            continue
        if not text.startswith("."):
            text = "." + text
        if text not in normalized:
            normalized.append(text)
    return tuple(normalized)


def _normalize_sources(raw: Any) -> tuple[CatalogSource, ...]:
    if not isinstance(raw, list):
        return ()
    normalized: list[CatalogSource] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        folder = str(item.get(CFG_FOLDER) or "").strip()
        if not folder:
            continue
        extensions = _normalize_extensions(item.get(CFG_EXTENSIONS, []))
        if not extensions:
            continue
        normalized.append(CatalogSource(folder=folder, extensions=extensions))
    return tuple(normalized)


def _coerce_positive_int(value: Any, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number > 0 else default


def _catalog_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    raw = payload if isinstance(payload, dict) else {}
    opamp_raw = raw.get(CFG_OPAMP, {}) if isinstance(raw, dict) else {}
    catalog_raw = opamp_raw.get(CFG_CONFIG_CATALOG, {}) if isinstance(opamp_raw, dict) else {}
    if not isinstance(catalog_raw, dict):
        catalog_raw = {}
    return catalog_raw


def load_catalog_service_config_from_payload(payload: dict[str, Any] | None) -> CatalogServiceConfig:
    """Normalize catalog-service config from an already loaded payload."""
    raw_payload = payload if isinstance(payload, dict) else {}
    catalog_raw = _catalog_payload(raw_payload)

    enabled = _coerce_bool(catalog_raw.get(CFG_ENABLED), False)
    menu_label = str(catalog_raw.get(CFG_MENU_LABEL) or DEFAULT_MENU_LABEL).strip() or DEFAULT_MENU_LABEL
    route_path = _normalized_path(str(catalog_raw.get(CFG_ROUTE_PATH) or ""), DEFAULT_ROUTE_PATH)
    help_path = _normalized_path(str(catalog_raw.get(CFG_HELP_PATH) or ""), DEFAULT_HELP_PATH)
    ui_base_css_path = str(catalog_raw.get(CFG_UI_BASE_CSS_PATH) or DEFAULT_UI_BASE_CSS_PATH).strip() or DEFAULT_UI_BASE_CSS_PATH
    web_port = _coerce_positive_int(catalog_raw.get(CFG_WEB_PORT), DEFAULT_WEB_PORT)
    ui_refresh_seconds = _coerce_positive_int(
        catalog_raw.get(CFG_UI_REFRESH_SECONDS),
        DEFAULT_UI_REFRESH_SECONDS,
    )
    sources = _normalize_sources(catalog_raw.get(CFG_SOURCES, []))

    if enabled and not sources:
        enabled = False

    return CatalogServiceConfig(
        enabled=enabled,
        menu_label=menu_label,
        route_path=route_path,
        help_path=help_path,
        ui_base_css_path=ui_base_css_path,
        web_port=web_port,
        ui_refresh_seconds=ui_refresh_seconds,
        sources=sources,
        raw_payload=raw_payload,
    )


def load_catalog_service_config(*, config_path: pathlib.Path) -> CatalogServiceConfig:
    """Load and normalize catalog-service config from a JSON config file."""
    return load_catalog_service_config_from_payload(load_json_config(config_path))


def catalog_component_entry_from_payload(
    payload: dict[str, Any] | None,
) -> ComponentEntryPoint | None:
    """Return the provider mount entrypoint when the catalog feature is enabled."""
    config = load_catalog_service_config_from_payload(payload)
    if config.enabled is not True:
        return None
    return ComponentEntryPoint(
        entry_point=CATALOG_COMPONENT_ENTRY_POINT,
        label=config.menu_label,
        url=config.route_path,
        enabled=True,
    )
