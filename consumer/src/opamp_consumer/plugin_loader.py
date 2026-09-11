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

"""Runtime discovery for OpAMP consumer client plugins."""

from __future__ import annotations

import importlib
import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from importlib import metadata, resources
from pathlib import Path
from typing import Any, cast

from opamp_consumer.config import (
    CFG_CONSUMER_PLUGIN_ENABLED,
    CFG_CONSUMER_PLUGIN_ENTRY_POINT,
    CFG_SERVICE_TYPE,
    ConsumerConfig,
)

CONSUMER_PLUGIN_ENTRY_POINT_GROUP = "opamp_consumer.plugins"
DEFAULT_PLUGIN_FUNCTION = "main"
BUILTIN_CONSUMER_PLUGIN_CONFIG_RESOURCE = "builtin_consumer_plugins.json"
BUILTIN_CONSUMER_PLUGIN_CONFIG_ENV = "OPAMP_CONSUMER_BUILTIN_PLUGINS_PATH"


@dataclass(frozen=True)
class ConsumerPlugin:
    """Resolved plugin entry for a consumer service type."""

    service_type: str
    entry_point: str
    load: Callable[[], Callable[[], None]]


def _normalize_service_type(value: object) -> str:
    """Return a normalized registry key for a service type."""
    return str(value or "").strip().lower()


def _callable_from_reference(reference: str) -> Callable[[], None]:
    """Load a callable from `module` or `module:callable` notation."""
    module_name, separator, attribute_name = reference.partition(":")
    module_name = module_name.strip()
    attribute_name = attribute_name.strip() if separator else DEFAULT_PLUGIN_FUNCTION
    if not module_name or not attribute_name:
        raise ValueError(f"invalid consumer plugin entry_point {reference!r}")
    module = importlib.import_module(module_name)
    target: Any = module
    for attribute_part in attribute_name.split("."):
        target = getattr(target, attribute_part)
    if not callable(target):
        raise TypeError(f"consumer plugin entry_point {reference!r} is not callable")
    return cast(Callable[[], None], target)


def _builtin_plugin_config_text(config_path: Path | None = None) -> str:
    """Read the built-in plugin registry config from disk or package resources."""
    if config_path is not None:
        return config_path.read_text(encoding="utf-8")
    override = os.getenv(BUILTIN_CONSUMER_PLUGIN_CONFIG_ENV)
    if override:
        return Path(override).read_text(encoding="utf-8")
    return (
        resources.files("opamp_consumer")
        .joinpath(BUILTIN_CONSUMER_PLUGIN_CONFIG_RESOURCE)
        .read_text(encoding="utf-8")
    )


def _load_builtin_consumer_plugins(
    config_path: Path | None = None,
) -> tuple[dict[str, str | bool], ...]:
    """Load built-in consumer plugin definitions from JSON configuration."""
    payload = json.loads(_builtin_plugin_config_text(config_path))
    raw_plugins = payload.get("plugins") if isinstance(payload, dict) else payload
    if not isinstance(raw_plugins, list):
        raise ValueError("built-in consumer plugin config must contain a plugins list")

    plugins: list[dict[str, str | bool]] = []
    for index, raw_plugin in enumerate(raw_plugins):
        if not isinstance(raw_plugin, dict):
            raise ValueError(f"built-in consumer plugin at index {index} must be an object")
        service_type = _normalize_service_type(raw_plugin.get(CFG_SERVICE_TYPE))
        entry_point = str(raw_plugin.get(CFG_CONSUMER_PLUGIN_ENTRY_POINT) or "").strip()
        enabled = bool(raw_plugin.get(CFG_CONSUMER_PLUGIN_ENABLED, True))
        if not service_type or not entry_point:
            raise ValueError(
                "built-in consumer plugin at index "
                f"{index} must define service_type and entry_point"
            )
        plugins.append(
            {
                CFG_SERVICE_TYPE: service_type,
                CFG_CONSUMER_PLUGIN_ENTRY_POINT: entry_point,
                CFG_CONSUMER_PLUGIN_ENABLED: enabled,
            }
        )
    return tuple(plugins)


BUILTIN_CONSUMER_PLUGINS: tuple[dict[str, str | bool], ...] = (
    _load_builtin_consumer_plugins()
)


def _entry_points_for_group() -> list[metadata.EntryPoint]:
    """Return installed package entry points for consumer plugins."""
    entry_points = metadata.entry_points()
    if hasattr(entry_points, "select"):
        return list(entry_points.select(group=CONSUMER_PLUGIN_ENTRY_POINT_GROUP))
    return list(entry_points.get(CONSUMER_PLUGIN_ENTRY_POINT_GROUP, []))


def _discover_installed_plugins() -> dict[str, ConsumerPlugin]:
    """Build a registry from package metadata entry points."""
    plugins: dict[str, ConsumerPlugin] = {}
    for entry_point in _entry_points_for_group():
        service_type = _normalize_service_type(entry_point.name)
        if not service_type:
            continue
        plugins[service_type] = ConsumerPlugin(
            service_type=service_type,
            entry_point=entry_point.value,
            load=entry_point.load,
        )
    return plugins


def _builtin_plugins() -> dict[str, ConsumerPlugin]:
    """Return built-in consumer plugins available from the source package."""
    plugins: dict[str, ConsumerPlugin] = {}
    for plugin_config in BUILTIN_CONSUMER_PLUGINS:
        if not bool(plugin_config.get(CFG_CONSUMER_PLUGIN_ENABLED, True)):
            continue
        plugin = _configured_plugin(dict(plugin_config))
        if plugin is not None:
            plugins[plugin.service_type] = plugin
    return plugins


def _configured_plugin(plugin_config: dict[str, Any]) -> ConsumerPlugin | None:
    """Build a registry entry from one `consumer.plugins` definition."""
    service_type = _normalize_service_type(plugin_config.get(CFG_SERVICE_TYPE))
    entry_point = str(plugin_config.get(CFG_CONSUMER_PLUGIN_ENTRY_POINT) or "").strip()
    if not service_type or not entry_point:
        return None
    return ConsumerPlugin(
        service_type=service_type,
        entry_point=entry_point,
        load=lambda: _callable_from_reference(entry_point),
    )


def build_consumer_plugin_registry(config: ConsumerConfig) -> dict[str, ConsumerPlugin]:
    """Return installed plugins overlaid with config-defined plugins."""
    plugins = _builtin_plugins()
    plugins.update(_discover_installed_plugins())
    for plugin_config in config.consumer_plugins:
        service_type = _normalize_service_type(plugin_config.get(CFG_SERVICE_TYPE))
        if not service_type:
            continue
        if not bool(plugin_config.get(CFG_CONSUMER_PLUGIN_ENABLED, True)):
            plugins.pop(service_type, None)
            continue
        plugin = _configured_plugin(plugin_config)
        if plugin is not None:
            plugins[service_type] = plugin
    return plugins


def load_consumer_plugin(config: ConsumerConfig) -> Callable[[], None]:
    """Resolve and load the configured consumer client plugin entrypoint."""
    logger = logging.getLogger(__name__)
    service_type = _normalize_service_type(config.service_type)
    registry = build_consumer_plugin_registry(config)
    plugin = registry.get(service_type)
    if plugin is None:
        supported = ", ".join(sorted(registry)) or "none"
        logger.error(
            "failed to load consumer plugin service_type=%s; configured/installed plugins: %s",
            service_type,
            supported,
        )
        raise ValueError(
            "unsupported consumer.service_type "
            f"{service_type!r}; configured/installed plugins: {supported}"
        )
    logger.info(
        "loading consumer plugin service_type=%s entry_point=%s",
        plugin.service_type,
        plugin.entry_point,
    )
    try:
        target = plugin.load()
        if not callable(target):
            raise TypeError(
                "consumer plugin entry_point "
                f"{plugin.entry_point!r} for service_type={service_type!r} is not callable"
            )
    except Exception:
        logger.error(
            "failed to load consumer plugin service_type=%s entry_point=%s",
            plugin.service_type,
            plugin.entry_point,
            exc_info=True,
        )
        raise
    logger.info(
        "loaded consumer plugin service_type=%s entry_point=%s callable=%s.%s",
        plugin.service_type,
        plugin.entry_point,
        getattr(target, "__module__", "<unknown>"),
        getattr(target, "__qualname__", getattr(target, "__name__", "<callable>")),
    )
    return target
