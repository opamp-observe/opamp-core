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

"""Plugin-owned consumer configuration processing."""

from __future__ import annotations

import importlib
import logging
import pathlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib import metadata
from typing import Any, cast

CONSUMER_PLUGIN_ENTRY_POINT_GROUP = "opamp_consumer.plugins"
PLUGIN_CONFIG_HOOK_NAME = "process_consumer_config"
CFG_SERVICE_TYPE = "service_type"
CFG_CONSUMER_PLUGIN_ENTRY_POINT = "entry_point"
CFG_CONSUMER_PLUGIN_ENABLED = "enabled"


@dataclass(frozen=True)
class ConsumerPluginConfigContext:
    """Context supplied to plugin-owned config processors."""

    service_type: str
    section_name: str
    raw_section: Mapping[str, Any]
    consumer_raw: Mapping[str, Any]
    config_path: pathlib.Path


ConsumerPluginConfigHook = Callable[
    [ConsumerPluginConfigContext],
    Mapping[str, Any] | None,
]


def resolve_optional_path_from_config(
    *,
    raw_value: Any,
    config_path: pathlib.Path,
) -> str | None:
    """Resolve optional plugin paths relative to the containing config file."""
    normalized_path = str(raw_value).strip() if raw_value is not None else ""
    if not normalized_path:
        return None
    if pathlib.PureWindowsPath(normalized_path).is_absolute():
        return normalized_path
    path = pathlib.Path(normalized_path).expanduser()
    if path.is_absolute():
        return str(path)
    return str((config_path.parent / path).resolve())


def _normalize_service_type(value: object) -> str:
    """Return a normalized plugin/service key."""
    return str(value or "").strip().lower()


def _module_name_from_reference(reference: str) -> str | None:
    """Return module name from `module` or `module:callable` notation."""
    module_name = reference.partition(":")[0].strip()
    return module_name or None


def _configured_plugin_module(
    *,
    consumer_plugins: list[dict[str, Any]],
    service_type: str,
) -> str | None:
    """Return configured plugin module for a service type, if present."""
    for plugin_config in consumer_plugins:
        plugin_service_type = _normalize_service_type(
            plugin_config.get(CFG_SERVICE_TYPE)
        )
        if plugin_service_type != service_type:
            continue
        if not bool(plugin_config.get(CFG_CONSUMER_PLUGIN_ENABLED, True)):
            return None
        entry_point = str(
            plugin_config.get(CFG_CONSUMER_PLUGIN_ENTRY_POINT) or ""
        ).strip()
        return _module_name_from_reference(entry_point)
    return None


def _installed_plugin_module(*, service_type: str) -> str | None:
    """Return installed entry-point module for a service type, if discoverable."""
    entry_points = metadata.entry_points()
    if hasattr(entry_points, "select"):
        candidates = list(entry_points.select(group=CONSUMER_PLUGIN_ENTRY_POINT_GROUP))
    else:
        candidates = list(entry_points.get(CONSUMER_PLUGIN_ENTRY_POINT_GROUP, []))
    for entry_point in candidates:
        if _normalize_service_type(entry_point.name) != service_type:
            continue
        return _module_name_from_reference(entry_point.value)
    return None


def _candidate_plugin_modules(
    *,
    service_type: str,
    consumer_plugins: list[dict[str, Any]],
) -> list[str]:
    """Return ordered module candidates for plugin config hook discovery."""
    candidates: list[str] = []
    configured_module = _configured_plugin_module(
        consumer_plugins=consumer_plugins,
        service_type=service_type,
    )
    installed_module = _installed_plugin_module(service_type=service_type)
    conventional_module = f"opamp_consumer.{service_type.replace('-', '_')}.client"
    for module_name in (configured_module, installed_module, conventional_module):
        if module_name and module_name not in candidates:
            candidates.append(module_name)
    return candidates


def _load_plugin_config_hook(
    *,
    service_type: str,
    consumer_plugins: list[dict[str, Any]],
) -> ConsumerPluginConfigHook | None:
    """Load a plugin config hook from the selected plugin module, when present."""
    logger = logging.getLogger(__name__)
    for module_name in _candidate_plugin_modules(
        service_type=service_type,
        consumer_plugins=consumer_plugins,
    ):
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            logger.debug(
                "plugin config module not found service_type=%s module=%s",
                service_type,
                module_name,
            )
            continue
        except AttributeError as error:
            if "partially initialized module" not in str(error):
                raise
            logger.debug(
                "plugin config module skipped during partial import "
                "service_type=%s module=%s error=%s",
                service_type,
                module_name,
                error,
            )
            continue
        hook = getattr(module, PLUGIN_CONFIG_HOOK_NAME, None)
        if hook is None:
            logger.debug(
                "plugin config hook missing service_type=%s module=%s hook=%s",
                service_type,
                module_name,
                PLUGIN_CONFIG_HOOK_NAME,
            )
            continue
        if not callable(hook):
            raise TypeError(
                f"plugin config hook {module_name}.{PLUGIN_CONFIG_HOOK_NAME} "
                "is not callable"
            )
        return cast(ConsumerPluginConfigHook, hook)
    return None


def collect_consumer_plugin_config_updates(
    *,
    service_type: str,
    consumer_plugins: list[dict[str, Any]],
    consumer_raw: Mapping[str, Any],
    config_path: pathlib.Path,
) -> dict[str, Any]:
    """Return ConsumerConfig attribute updates from a plugin config block."""
    normalized_service_type = _normalize_service_type(service_type)
    raw_section = consumer_raw.get(normalized_service_type)
    if not isinstance(raw_section, Mapping):
        raw_section = {}

    hook = _load_plugin_config_hook(
        service_type=normalized_service_type,
        consumer_plugins=consumer_plugins,
    )
    if hook is None:
        logging.getLogger(__name__).debug(
            "plugin config block ignored; no hook service_type=%s",
            normalized_service_type,
        )
        return {}

    context = ConsumerPluginConfigContext(
        service_type=normalized_service_type,
        section_name=normalized_service_type,
        raw_section=raw_section,
        consumer_raw=consumer_raw,
        config_path=config_path,
    )
    updates = hook(context)
    if updates is None:
        return {}
    return dict(updates)
