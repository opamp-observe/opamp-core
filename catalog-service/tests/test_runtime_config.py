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

"""Catalog service runtime-config test coverage.

Test-case reference: catalog-service/docs/TEST_CASES.md
"""

from __future__ import annotations

import json
from pathlib import Path

from catalog_service.config import (
    catalog_component_entry_from_payload,
    load_catalog_service_config,
    load_catalog_service_config_from_payload,
)
from catalog_service.runtime_config import (
    ENV_CATALOG_SERVICE_CONFIG_PATH,
    resolve_component_entries,
    resolve_component_entry_points,
    resolve_observability_config,
    resolve_web_port,
)


def test_catalog_component_entry_is_generated_when_enabled() -> None:
    payload = {
        "opamp": {
            "config_catalog": {
                "enabled": True,
                "menu_label": "Catalog",
                "route_path": "/catalog",
                "help_path": "/catalog/help",
                "sources": [{"folder": "configs", "extensions": [".yaml"]}],
            }
        }
    }

    entry = catalog_component_entry_from_payload(payload)
    assert entry is not None
    assert entry.entry_point == "catalog_service.opamp_integration:register_catalog_feature"
    assert entry.label == "Catalog"
    assert entry.url == "/catalog"


def test_catalog_config_defaults_ui_refresh_to_120_seconds() -> None:
    config = load_catalog_service_config_from_payload(
        {
            "opamp": {
                "config_catalog": {
                    "enabled": True,
                    "sources": [{"folder": "configs", "extensions": [".yaml"]}],
                }
            }
        }
    )

    assert config.ui_refresh_seconds == 120


def test_catalog_config_uses_configured_ui_refresh_seconds() -> None:
    config = load_catalog_service_config_from_payload(
        {
            "opamp": {
                "config_catalog": {
                    "enabled": True,
                    "ui_refresh_seconds": 30,
                    "sources": [{"folder": "configs", "extensions": [".yaml"]}],
                }
            }
        }
    )

    assert config.ui_refresh_seconds == 30


def test_runtime_config_uses_component_defaults_when_component_entry_points_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "catalog-service.json"
    config_path.write_text(
        json.dumps(
            {
                "opamp": {
                    "config_catalog": {
                        "enabled": True,
                        "web_port": 8123,
                        "sources": [{"folder": "configs", "extensions": [".yaml"]}],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CATALOG_SERVICE_CONFIG_PATH, str(config_path))

    assert resolve_component_entry_points() == ["catalog_service.opamp_integration:register_catalog_feature"]
    assert resolve_web_port() == 8123

    config = load_catalog_service_config(config_path=config_path)
    assert config.enabled is True


def test_runtime_config_preserves_explicit_component_entries_for_freestanding_editor(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "catalog-service.json"
    config_path.write_text(
        json.dumps(
            {
                "component-entry-points": {
                    "quart": [
                        {
                            "entry_point": "catalog_service.app:register_catalog_component",
                            "label": "Config Catalog",
                            "url": "/catalog",
                            "enabled": True,
                        },
                        {
                            "entry_point": "config_service.opamp_integration:register_config_service_feature",
                            "label": "Config Editor",
                            "url": "/config-service/ui",
                            "enabled": True,
                        },
                    ]
                },
                "opamp": {
                    "config_catalog": {
                        "enabled": True,
                        "web_port": 8123,
                        "sources": [{"folder": "configs", "extensions": [".yaml"]}],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CATALOG_SERVICE_CONFIG_PATH, str(config_path))

    entries = resolve_component_entries()
    assert [entry.entry_point for entry in entries] == [
        "catalog_service.app:register_catalog_component",
        "config_service.opamp_integration:register_config_service_feature",
    ]
    assert [entry.label for entry in entries] == ["Config Catalog", "Config Editor"]


def test_runtime_config_omits_config_service_entry_when_not_configured(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "catalog-service.json"
    config_path.write_text(
        json.dumps(
            {
                "component-entry-points": {
                    "quart": [
                        {
                            "entry_point": "catalog_service.app:register_catalog_component",
                            "label": "Config Catalog",
                            "url": "/catalog",
                            "enabled": True,
                        }
                    ]
                },
                "opamp": {
                    "config_catalog": {
                        "enabled": True,
                        "web_port": 8123,
                        "sources": [{"folder": "configs", "extensions": [".yaml"]}],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CATALOG_SERVICE_CONFIG_PATH, str(config_path))

    entries = resolve_component_entries()
    assert [entry.entry_point for entry in entries] == [
        "catalog_service.app:register_catalog_component"
    ]


def test_runtime_config_loads_observability_from_root_payload(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "catalog-service.json"
    config_path.write_text(
        json.dumps(
            {
                "otlp-endpoints": {
                    "ALL": "http://collector:4317",
                    "traces": "http://traces:4320",
                    "export_interval": 90,
                },
                "opamp": {
                    "config_catalog": {
                        "enabled": True,
                        "sources": [{"folder": "configs", "extensions": [".yaml"]}],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CATALOG_SERVICE_CONFIG_PATH, str(config_path))

    config = resolve_observability_config()

    assert config.resolved_logs_endpoint == "http://collector:4317"
    assert config.resolved_metrics_endpoint == "http://collector:4317"
    assert config.resolved_traces_endpoint == "http://traces:4320"
    assert config.export_interval_seconds == 90
