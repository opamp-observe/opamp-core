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

"""Provider component-entry-point loading and UI feature metadata helpers."""

from __future__ import annotations

import logging
import pathlib
import sys
from dataclasses import dataclass
from typing import Any

from shared.opamp_config import (
    CFG_COMPONENT_ENTRY_POINTS_QUART,
    ComponentEntryPoint,
    load_json_config,
    register_component_entry_points,
    resolve_component_entry_points_from_payload,
)


@dataclass(frozen=True)
class UiFeatureMenuItem:
    """One UI feature menu entry displayed in the provider console."""

    entry_point: str
    label: str
    url: str
    target: str = "_self"


def _repo_root() -> pathlib.Path:
    """Return repository root from provider source package path."""
    return pathlib.Path(__file__).resolve().parents[3]


def _ensure_optional_component_paths() -> None:
    """Ensure optional embedded component source paths are importable."""
    root = _repo_root()
    candidates = [
        root / "client-config-generator-service" / "src",
        root / "config-service" / "src",
        root / "consumer" / "src",
        root / "svr-credentials-mgr" / "src",
        root / "svr-credentials-mgr" / "plaintext-keyring" / "src",
    ]
    for candidate in candidates:
        if not candidate.exists():
            continue
        resolved = str(candidate.resolve())
        if resolved not in sys.path:
            sys.path.insert(0, resolved)
    catalog_src = root / "catalog-service" / "src"
    if catalog_src.exists():
        resolved = str(catalog_src.resolve())
        if resolved not in sys.path:
            sys.path.insert(0, resolved)


def resolve_provider_component_entries(
    *,
    config_path: pathlib.Path,
) -> list[ComponentEntryPoint]:
    """Return configured Quart component entrypoints for provider runtime."""
    _ensure_optional_component_paths()
    payload = load_json_config(config_path)
    entries = resolve_component_entry_points_from_payload(
        payload,
        runtime_key=CFG_COMPONENT_ENTRY_POINTS_QUART,
        default_entry_points=(),
    )
    try:
        from catalog_service.config import catalog_component_entry_from_payload
    except ImportError:
        return entries

    catalog_entry = catalog_component_entry_from_payload(payload)
    if catalog_entry is None:
        return entries

    configured = {entry.entry_point for entry in entries}
    if catalog_entry.entry_point not in configured:
        entries.append(catalog_entry)
    return entries


def register_provider_component_entries(
    *,
    app: Any,
    config_path: pathlib.Path,
    logger: logging.Logger,
) -> tuple[list[str], list[ComponentEntryPoint]]:
    """Register configured provider component entrypoints and return loaded entries."""
    _ensure_optional_component_paths()
    entries = resolve_provider_component_entries(config_path=config_path)
    if not entries:
        return [], []
    try:
        registered = register_component_entry_points(app, entries=entries)
    except Exception as exc:
        logger.exception("failed registering provider component entrypoints", exc_info=exc)
        return [], entries
    return registered, entries


def ui_menu_items_from_component_entries(
    entries: list[ComponentEntryPoint],
) -> list[UiFeatureMenuItem]:
    """Build provider UI feature-menu entries from configured component payload."""
    items: list[UiFeatureMenuItem] = []
    for entry in entries:
        label = str(entry.label or "").strip()
        url = str(entry.url or "").strip()
        if not label or not url:
            continue
        items.append(
            UiFeatureMenuItem(
                entry_point=str(entry.entry_point or "").strip(),
                label=label,
                url=url,
                target="_self",
            )
        )
    return items
