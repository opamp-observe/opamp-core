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

from __future__ import annotations

import json
from pathlib import Path

from opamp_provider.component_features import (
    resolve_provider_component_entries,
    ui_menu_items_from_component_entries,
)

CLIENT_CONFIG_GENERATOR_ENTRY_POINT = (
    "client_config_generator_service.opamp_integration:register_client_config_generator_feature"
)
CLIENT_CONFIG_GENERATOR_LABEL = "Client Config Generator"
CLIENT_CONFIG_GENERATOR_URL = "/client-config-generator-service/ui"
COMPONENT_ENTRY_POINTS_KEY = "component-entry-points"
OPAMP_KEY = "opamp"
QUART_KEY = "quart"


def test_provider_component_entries_and_menu_items_support_labels_and_urls(tmp_path: Path) -> None:
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(
            {
                "component-entry-points": {
                    "quart": [
                        {
                            "entry_point": "pkg.alpha:register",
                            "label": "Alpha UI",
                            "url": "/alpha/ui",
                            "enabled": True,
                        },
                        {
                            "entry_point": "pkg.disabled:register",
                            "label": "Disabled",
                            "url": "/disabled",
                            "enabled": False,
                        },
                        "pkg.legacy:register",
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    entries = resolve_provider_component_entries(config_path=config_path)
    assert [entry.entry_point for entry in entries] == [
        "pkg.alpha:register",
        "pkg.legacy:register",
    ]

    menu_items = ui_menu_items_from_component_entries(entries)
    assert len(menu_items) == 1
    assert menu_items[0].entry_point == "pkg.alpha:register"
    assert menu_items[0].label == "Alpha UI"
    assert menu_items[0].url == "/alpha/ui"
    assert menu_items[0].target == "_self"


def test_provider_component_entries_include_catalog_entry_when_enabled(tmp_path: Path) -> None:
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(
            {
                "opamp": {
                    "config_catalog": {
                        "enabled": True,
                        "menu_label": "Config Catalog",
                        "route_path": "/catalog",
                        "help_path": "/catalog/help",
                        "sources": [
                            {
                                "folder": "configs",
                                "extensions": [".yaml"],
                            }
                        ],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    entries = resolve_provider_component_entries(config_path=config_path)
    assert any(entry.entry_point == "catalog_service.opamp_integration:register_catalog_feature" for entry in entries)

    menu_items = ui_menu_items_from_component_entries(entries)
    catalog_item = next(item for item in menu_items if item.label == "Config Catalog")
    assert catalog_item.url == "/catalog"


def test_default_provider_config_includes_client_config_generator() -> None:
    """Verify default opamp-server configuration exposes the generator plugin."""
    repo_root = Path(__file__).resolve().parents[2]
    config_path = repo_root / "config" / "opamp.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))

    entries = resolve_provider_component_entries(config_path=config_path)
    entry_points = [entry.entry_point for entry in entries]
    assert CLIENT_CONFIG_GENERATOR_ENTRY_POINT in entry_points

    menu_items = ui_menu_items_from_component_entries(entries)
    generator_item = next(
        item for item in menu_items if item.entry_point == CLIENT_CONFIG_GENERATOR_ENTRY_POINT
    )
    assert generator_item.label == CLIENT_CONFIG_GENERATOR_LABEL
    assert generator_item.url == CLIENT_CONFIG_GENERATOR_URL

    configured_entries = payload[COMPONENT_ENTRY_POINTS_KEY][QUART_KEY]
    assert any(
        item.get("entry_point") == CLIENT_CONFIG_GENERATOR_ENTRY_POINT
        and item.get("enabled") is True
        for item in configured_entries
    )
    assert "client_config_generator" in payload[OPAMP_KEY]
