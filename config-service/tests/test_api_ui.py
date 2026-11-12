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

"""Config-service UI and editor API test coverage.

Test-case reference: config-service/docs/TEST_CASES.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shared.security_headers import (
    CONTENT_SECURITY_POLICY_HEADER,
    FRAME_ANCESTORS_NONE_POLICY,
    X_FRAME_OPTIONS_DENY,
    X_FRAME_OPTIONS_HEADER,
)

from config_service.app import create_app
from config_service.runtime_config import (
    ENV_CONFIG_TOOL_CONFIG_PATH,
)


@pytest.mark.asyncio
async def test_client_error_endpoint_logs_ui_errors(capsys: pytest.CaptureFixture[str]) -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    response = await client.post(
        "/config-service/api/v1/client-errors",
        json={
            "kind": "window_error",
            "message": "Render button handler exploded",
            "source": "config_ui.js",
            "path": "http://localhost:8080/config-service/ui",
            "stack": "Error: Render button handler exploded\n    at onClick (config_ui.js:10:2)",
            "line": 10,
            "column": 2,
        },
    )
    assert response.status_code == 200
    body = await response.get_json()
    assert body["ok"] is True

    captured = capsys.readouterr()
    assert "UI ERROR" in captured.err
    assert "Render button handler exploded" in captured.err

@pytest.mark.asyncio
async def test_ui_css_override_injected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONFIG_SERVICE_UI_CSS_OVERRIDE_PATH", "/ui/assets/web_ui.css")
    monkeypatch.setenv("CONFIG_SERVICE_UI_BASE_CSS_PATH", "/ui/assets/base.css")
    app = create_app(mode="standalone")
    client = app.test_client()
    ui = await client.get("/config-service/ui")
    assert ui.status_code == 200
    html = (await ui.get_data()).decode("utf-8")
    assert 'href="/ui/assets/base.css"' in html
    assert "/ui/assets/web_ui.css" in html

@pytest.mark.asyncio
async def test_component_entry_points_can_disable_ui_routes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "component-entry-points": {
                    "quart": [
                        "opamp_tools.config_app:register_api_component",
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    app = create_app(mode="standalone")
    client = app.test_client()

    ui = await client.get("/config-service/ui")
    assert ui.status_code in {301, 302, 307, 308}
    assert ui.headers["Location"].startswith(
        "https://htmlpreview.github.io/?https://raw.githubusercontent.com/"
        "mp3monster/fluent-opamp/main/github-landingpage/index.html"
    )

    health = await client.get("/config-service/api/v1/health")
    assert health.status_code == 200

@pytest.mark.asyncio
async def test_ui_collapsed_sections_injected_from_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                    "config-tool": {
                        "ui_collapsed_sections": [
                            "environment_variables",
                            "upstream_servers",
                            "parsers",
                            "service",
                            "rendered_configuration",
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    app = create_app(mode="standalone")
    client = app.test_client()
    ui = await client.get("/config-service/ui")
    assert ui.status_code == 200
    html = (await ui.get_data()).decode("utf-8")
    assert "window.__CONFIG_SERVICE_UI_COLLAPSED_SECTIONS__" in html
    assert '"environment_variables"' in html
    assert '"upstream_servers"' in html
    assert '"rendered_configuration"' in html

@pytest.mark.asyncio
async def test_ui_save_as_toggle_injected_from_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "config-tool": {
                    "ui_show_save_as": True,
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    monkeypatch.delenv("CONFIG_SERVICE_UI_SHOW_SAVE_AS", raising=False)
    app = create_app(mode="standalone")
    client = app.test_client()
    ui = await client.get("/config-service/ui")
    assert ui.status_code == 200
    html = (await ui.get_data()).decode("utf-8")
    assert "window.__CONFIG_SERVICE_UI_SHOW_SAVE_AS__ = true;" in html

@pytest.mark.asyncio
async def test_ui_save_as_toggle_defaults_to_hidden(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "config-tool": {
                    "read_only": False,
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))
    monkeypatch.delenv("CONFIG_SERVICE_UI_SHOW_SAVE_AS", raising=False)
    app = create_app(mode="standalone")
    client = app.test_client()
    ui = await client.get("/config-service/ui")
    assert ui.status_code == 200
    html = (await ui.get_data()).decode("utf-8")
    assert "window.__CONFIG_SERVICE_UI_SHOW_SAVE_AS__ = false;" in html

@pytest.mark.asyncio
async def test_upstream_servers_section_is_present_in_ui() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()
    ui = await client.get("/config-service/ui")
    assert ui.status_code == 200
    html = (await ui.get_data()).decode("utf-8")
    assert 'id="upstream-servers-panel"' in html
    assert 'id="upstream-servers-list"' in html
    assert 'id="add-upstream-server-group"' in html

@pytest.mark.asyncio
async def test_raw_config_view_dialog_is_present_in_ui() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()
    ui = await client.get("/config-service/ui")
    assert ui.status_code == 200
    html = (await ui.get_data()).decode("utf-8")
    assert 'id="view-raw-config"' in html
    assert ">View Raw</button>" in html
    assert 'id="raw-config-dialog"' in html
    assert 'aria-modal="true"' in html
    assert 'id="raw-config-text"' in html
    assert "readonly" in html
    assert 'id="raw-config-close"' in html
    assert ">Close</button>" in html

@pytest.mark.asyncio
async def test_ui_save_script_defaults_fluentbit_saves_to_yaml() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()
    ui_script_response = await client.get("/config-service/ui/assets/config_ui.js")
    assert ui_script_response.status_code == 200
    ui_script = (await ui_script_response.get_data()).decode("utf-8")
    assert '.yaml' in ui_script
    assert 'description: "Fluent Bit configuration"' in ui_script
    assert '"text/yaml": [".yaml", ".yml"]' in ui_script

    api_script_response = await client.get("/config-service/ui/assets/config_ui_api.js")
    assert api_script_response.status_code == 200
    api_script = (await api_script_response.get_data()).decode("utf-8")
    assert 'apiBase + "/render/yaml/" + encodeURIComponent(version)' in api_script
    assert 'buildConfigTypeQuery(configType, "fluentbit")' in api_script

@pytest.mark.asyncio
async def test_validate_save_toggle_is_present_in_ui() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()
    ui = await client.get("/config-service/ui")
    assert ui.status_code == 200
    html = (await ui.get_data()).decode("utf-8")
    assert 'id="validation-save-toggle"' in html

@pytest.mark.asyncio
async def test_config_service_help_page_served() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()
    response = await client.get("/config-service/ui/docs/help")
    assert response.status_code == 200
    html = (await response.get_data()).decode("utf-8")
    assert "Config Service Help" in html
    assert "Main Building Blocks" in html
    assert "Icon Buttons" in html
    assert "Color Use" in html
    assert "Route" in html
    assert "Processors" in html
    assert "writes rendered YAML output" in html

@pytest.mark.asyncio
async def test_metadata_env_help_page_served() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()
    response = await client.get("/config-service/ui/docs/metadata-env")
    assert response.status_code == 200
    html = (await response.get_data()).decode("utf-8")
    assert "Additional Metadata" in html
    assert "Preset Metadata Options" in html
    assert "Header Comments" not in html

@pytest.mark.asyncio
async def test_top_level_help_link_is_rendered() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()
    response = await client.get("/config-service/ui")
    assert response.status_code == 200
    html = (await response.get_data()).decode("utf-8")
    assert 'href="/config-service/ui/docs/help"' in html
    assert 'aria-label="Open UI help in a new tab"' in html
    assert ">Help</a>" in html
    assert 'id="featureMenuGroup"' in html
    assert 'data-history-back-button="true"' in html
    assert 'aria-hidden="true"' in html
    assert 'tabindex="-1"' in html
    assert ">Back</button>" in html
    assert ">Server Console</a>" in html


@pytest.mark.asyncio
async def test_standalone_config_service_responses_deny_browser_framing() -> None:
    """Verify standalone UI and redirect responses inherit clickjacking protection."""
    app = create_app(mode="standalone")
    client = app.test_client()

    for route_path in ("/config-service/ui", "/does-not-exist"):
        response = await client.get(route_path)
        assert response.headers[CONTENT_SECURITY_POLICY_HEADER] == FRAME_ANCESTORS_NONE_POLICY
        assert response.headers[X_FRAME_OPTIONS_HEADER] == X_FRAME_OPTIONS_DENY


@pytest.mark.asyncio
async def test_server_console_link_is_visible_in_embedded_mode() -> None:
    app = create_app(mode="embedded")
    client = app.test_client()
    response = await client.get("/config-service/ui")
    assert response.status_code == 200
    html = (await response.get_data()).decode("utf-8")
    assert 'data-history-back-button="true"' in html
    assert 'hidden' in html
    assert 'href="/ui" >Server Console</a>' in html

@pytest.mark.asyncio
async def test_ui_routes_disable_cache_in_dev_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENABLE_DEV_FEATURES", "1")
    app = create_app(mode="standalone")
    client = app.test_client()

    ui = await client.get("/config-service/ui")
    assert ui.status_code == 200
    assert ui.headers["Cache-Control"] == "no-store, no-cache, must-revalidate, max-age=0"
    html = (await ui.get_data()).decode("utf-8")
    assert "/config-service/ui/assets/config_ui.css?v=" in html
    assert "/config-service/ui/assets/config_ui_plugins.js?v=" in html
    assert "/config-service/ui/assets/config_ui_sections.js?v=" in html
    assert "/config-service/ui/assets/config_ui_env.js?v=" in html
    assert "/config-service/ui/assets/config_ui_api.js?v=" in html
    assert "/config-service/ui/assets/config_ui.js?v=" in html

    asset = await client.get("/config-service/ui/assets/config_ui.js")
    assert asset.status_code == 200
    assert asset.headers["Cache-Control"] == "no-store, no-cache, must-revalidate, max-age=0"

    api_asset = await client.get("/config-service/ui/assets/config_ui_api.js")
    assert api_asset.status_code == 200
    assert api_asset.headers["Cache-Control"] == "no-store, no-cache, must-revalidate, max-age=0"

@pytest.mark.asyncio
async def test_ui_prepare_file_extracts_header_metadata_and_line_map() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    text = (
        "# config-service: config_type=fluentbit\n"
        "# config-service: version=5.0.4\n"
        "# Owned by Team A\n"
        "\n"
        "pipeline:\n"
        "  inputs:\n"
        "    - name: tail\n"
    )

    response = await client.post(
        "/config-service/api/v1/ui/prepare-file",
        json={
            "text": text,
            "file_name": "example.yaml",
            "config_type": "fluentbit",
        },
    )
    assert response.status_code == 200
    body = await response.get_json()
    assert body["ok"] is True
    assert body["config_type"] == "fluentbit"
    assert body["version"] == "5.0.4"
    assert body["header_comments"] == "Owned by Team A"
    assert body["body"].startswith("pipeline:")
    assert body["source_line_map"]["$.pipeline"] >= 1


@pytest.mark.asyncio
async def test_ui_load_source_file_reads_text_from_server_path(tmp_path: Path) -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    source_file = tmp_path / "sample.yaml"
    source_file.write_text(
        "# config-service: config_type=fluentbit\npipeline:\n  inputs: []\n",
        encoding="utf-8",
    )

    response = await client.post(
        "/config-service/api/v1/ui/load-source-file",
        json={"source_path": str(source_file)},
    )
    assert response.status_code == 200
    body = await response.get_json()
    assert body["ok"] is True
    assert body["file_name"] == "sample.yaml"
    assert body["source_path"] == str(source_file.resolve())
    assert "pipeline:" in body["text"]
