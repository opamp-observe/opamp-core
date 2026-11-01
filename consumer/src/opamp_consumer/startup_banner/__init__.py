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

"""Startup banner logging for consumer runtimes."""

from __future__ import annotations

import logging
import pathlib
from typing import Any

from opamp_consumer.config import (
    CFG_CONSUMER_PLUGIN_ENABLED,
    CFG_CONSUMER_PLUGIN_ENTRY_POINT,
    CFG_SERVICE_TYPE,
    ConsumerConfig,
)

BANNER_BORDER = "=" * 68
NOT_CONFIGURED = "<not configured>"


def _looks_like_windows_path(value: str) -> bool:
    """Return whether path text should be handled with Windows path rules."""
    return bool(pathlib.PureWindowsPath(value).drive) or "\\" in value


def _is_absolute_path(value: str) -> bool:
    """Return whether path text is absolute on Windows or POSIX."""
    if _looks_like_windows_path(value):
        return pathlib.PureWindowsPath(value).is_absolute()
    return pathlib.Path(value).is_absolute()


def _resolve_display_path(
    value: str | pathlib.Path | None,
    *,
    consumer_config_path: str | pathlib.Path | None,
) -> str:
    """Return path text, resolving agent-relative paths from the consumer config."""
    if value is None:
        return NOT_CONFIGURED
    path_text = str(value).strip()
    if not path_text:
        return NOT_CONFIGURED
    if _is_absolute_path(path_text) or consumer_config_path is None:
        return path_text

    config_path_text = str(consumer_config_path).strip()
    if not config_path_text:
        return path_text
    if _looks_like_windows_path(config_path_text):
        return str(pathlib.PureWindowsPath(config_path_text).parent / path_text)
    return str((pathlib.Path(config_path_text).expanduser().resolve().parent / path_text).resolve())


def _matching_plugin(config: ConsumerConfig) -> dict[str, Any] | None:
    """Return the configured plugin block for the selected service type."""
    service_type = str(config.service_type or "").strip().lower()
    for plugin_config in config.consumer_plugins:
        plugin_service_type = str(
            plugin_config.get(CFG_SERVICE_TYPE) or ""
        ).strip().lower()
        if plugin_service_type != service_type:
            continue
        if not bool(plugin_config.get(CFG_CONSUMER_PLUGIN_ENABLED, True)):
            continue
        return plugin_config
    return None


def _plugin_entry_point(config: ConsumerConfig) -> str:
    """Return the configured entry point for the selected plugin, when known."""
    plugin_config = _matching_plugin(config)
    if plugin_config is None:
        return NOT_CONFIGURED
    entry_point = str(plugin_config.get(CFG_CONSUMER_PLUGIN_ENTRY_POINT) or "").strip()
    return entry_point or NOT_CONFIGURED


def build_consumer_startup_banner_lines(
    *,
    config: ConsumerConfig,
    runtime_name: str,
    consumer_config_path: str | pathlib.Path | None,
) -> list[str]:
    """Build human-readable startup banner lines for a consumer runtime."""
    consumer_path = _resolve_display_path(
        consumer_config_path,
        consumer_config_path=None,
    )
    agent_path = _resolve_display_path(
        config.agent_config_path,
        consumer_config_path=consumer_config_path,
    )
    service_type = str(config.service_type or NOT_CONFIGURED).strip() or NOT_CONFIGURED
    process_tracking = (
        str(config.process_tracking or NOT_CONFIGURED).strip().lower()
        or NOT_CONFIGURED
    )
    # Add future startup-wide banner messages to this list so every consumer
    # entry point logs them consistently.
    banner_lines = [
        BANNER_BORDER,
        "OpAMP consumer startup",
        f"runtime: {runtime_name}",
        f"mode: {process_tracking}",
        f"service_type: {service_type}",
        f"plugin_entry_point: {_plugin_entry_point(config)}",
        f"consumer_config_path: {consumer_path}",
        f"agent_config_path: {agent_path}",
        f"server_url: {config.server_url or NOT_CONFIGURED}",
        f"transport: {config.transport or NOT_CONFIGURED}",
        BANNER_BORDER,
    ]
    return banner_lines


def log_consumer_startup_banner(
    *,
    logger: logging.Logger,
    config: ConsumerConfig,
    runtime_name: str,
    consumer_config_path: str | pathlib.Path | None,
) -> None:
    """Log the consumer startup banner at info level."""
    for line in build_consumer_startup_banner_lines(
        config=config,
        runtime_name=runtime_name,
        consumer_config_path=consumer_config_path,
    ):
        logger.info(line)
