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

"""Config-service runtime-config test coverage.

Test-case reference: config-service/docs/TEST_CASES.md
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config_service.app import create_app
from config_service.runtime_config import (
    ENV_CONFIG_TOOL_CONFIG_PATH,
    resolve_component_entry_points,
    resolve_log_level_name,
    resolve_observability_config,
    resolve_read_only,
    resolve_save_ignore_validation,
    resolve_ui_base_css_path,
    resolve_ui_collapsed_sections,
    resolve_ui_show_save_as,
    resolve_validation_agent_entries,
    resolve_web_port,
)


def test_resolve_web_port_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(
            {
                "provider": {"webui_port": 8123},
                "config_service": {"web_port": 8124},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPAMP_CONFIG_PATH", str(config_path))
    monkeypatch.delenv("CONFIG_SERVICE_WEB_PORT", raising=False)
    assert resolve_web_port() == 8124

    monkeypatch.setenv("CONFIG_SERVICE_WEB_PORT", "8125")
    assert resolve_web_port() == 8125

def test_resolve_component_entry_points_from_root_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "component-entry-points": {
                    "quart": [
                        "pkg.alpha:register",
                        {"entry_point": "pkg.beta:register", "enabled": True},
                        {"entry_point": "pkg.disabled:register", "enabled": False},
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    assert resolve_component_entry_points() == [
        "pkg.alpha:register",
        "pkg.beta:register",
    ]

def test_resolve_component_entry_points_defaults_when_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps({"config-tool": {"read_only": False}}),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    assert resolve_component_entry_points() == [
        "opamp_tools.config_app:register_api_component",
        "opamp_tools.config_app:register_ui_component",
    ]

def test_resolve_ui_base_css_path_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(
            {
                "config_service": {"ui_base_css_path": "/ui/assets/base.css"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPAMP_CONFIG_PATH", str(config_path))
    monkeypatch.delenv("CONFIG_SERVICE_UI_BASE_CSS_PATH", raising=False)
    assert resolve_ui_base_css_path() == "/ui/assets/base.css"

    monkeypatch.setenv("CONFIG_SERVICE_UI_BASE_CSS_PATH", "/env/base.css")
    assert resolve_ui_base_css_path() == "/env/base.css"

def test_resolve_read_only_from_config_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "config-tool": {"read_only": True},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    assert resolve_read_only() is True

def test_resolve_log_level_name_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "config-tool": {"log_level": "warning"},
                "provider": {"log_level": "error"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    monkeypatch.delenv("CONFIG_TOOL_LOG_LEVEL", raising=False)
    assert resolve_log_level_name() == "WARNING"

    monkeypatch.setenv("CONFIG_TOOL_LOG_LEVEL", "debug")
    assert resolve_log_level_name() == "DEBUG"

def test_resolve_ui_collapsed_sections_from_config_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "config-tool": {"ui_collapsed_sections": ["service", "parsers"]},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    assert resolve_ui_collapsed_sections() == ["service", "parsers"]

def test_resolve_ui_collapsed_sections_defaults_to_empty_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "config-tool": {"read_only": False},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    assert resolve_ui_collapsed_sections() == []

def test_resolve_ui_show_save_as_from_config_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "config-tool": {"ui_show_save_as": True},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    monkeypatch.delenv("CONFIG_SERVICE_UI_SHOW_SAVE_AS", raising=False)
    assert resolve_ui_show_save_as() is True

def test_resolve_ui_show_save_as_env_overrides_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "config-tool": {"ui_show_save_as": False},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    monkeypatch.setenv("CONFIG_SERVICE_UI_SHOW_SAVE_AS", "true")
    assert resolve_ui_show_save_as() is True

def test_resolve_save_ignore_validation_supports_requested_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "config-tool": {"save-ingore-validation": True},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    monkeypatch.delenv("CONFIG_SERVICE_SAVE_IGNORE_VALIDATION", raising=False)
    monkeypatch.delenv("CONFIG_SERVICE_SAVE_INGORE_VALIDATION", raising=False)
    assert resolve_save_ignore_validation() is True

def test_resolve_save_ignore_validation_env_overrides_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "config-tool": {"save-ingore-validation": False},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    monkeypatch.setenv("CONFIG_SERVICE_SAVE_IGNORE_VALIDATION", "true")
    assert resolve_save_ignore_validation() is True

def test_resolve_validation_agent_entries_from_config_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "config-tool": {
                    "agent_validation": {
                        "entries": [
                            {
                                "agent_type": "fluentbit",
                                "agent_version": "5.0.4",
                                "command_path": "fluent-bit",
                                "command_args": ["--dry-run", "-c", "{config_path}"],
                            }
                        ]
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    entries = resolve_validation_agent_entries()
    assert len(entries) == 1
    assert entries[0]["agent_type"] == "fluentbit"
    assert entries[0]["agent_version"] == "5.0.4"


def test_resolve_validation_agent_entries_defaults_to_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "config-tool": {"read_only": False},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    assert resolve_validation_agent_entries() == []

def test_create_app_applies_resolved_log_level(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "config-tool": {"log_level": "debug"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    monkeypatch.delenv("CONFIG_TOOL_LOG_LEVEL", raising=False)

    app = create_app(mode="standalone")

    assert app.logger.level == logging.DEBUG


def test_resolve_observability_config_from_root_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "otlp-endpoints": {
                    "ALL": "http://collector:4317",
                    "logs": "http://logs:4319",
                    "export_interval": 75,
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))

    config = resolve_observability_config()

    assert config.resolved_logs_endpoint == "http://logs:4319"
    assert config.resolved_metrics_endpoint == "http://collector:4317"
    assert config.resolved_traces_endpoint == "http://collector:4317"
    assert config.export_interval_seconds == 75
