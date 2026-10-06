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

"""HTTP contract tests for standalone and embedded generator deployments."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from quart import Quart

from client_config_generator_service import app as app_module
from client_config_generator_service.app import (
    API_PREFIX,
    UI_HELP_PATH,
    UI_PATH,
    create_app,
    register_client_config_generator_component,
)
from client_config_generator_service.auth_integration import UIAuthResult
from client_config_generator_service.opamp_integration import (
    register_client_config_generator_feature,
)


def _write_runtime_config(tmp_path: Path, *, read_only: bool = False) -> Path:
    """Write an isolated shared OpAMP configuration for HTTP tests.

    Args:
        tmp_path: Temporary directory used for config and generated files.
        read_only: Whether mutations should be disabled.
    """
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(
            {
                "opamp": {
                    "client_config_generator": {
                        "read_only": read_only,
                        "storage": {"configuration_directory": "generated"},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return config_path


def _valid_configuration() -> dict[str, object]:
    """Return a compact valid supervisor-mode API payload."""
    return {
        "consumer": {
            "server_url": "http://provider:8080",
            "transport": "http",
            "processTracking": "Supervisor",
            "service_type": "fluentbit",
            "heartbeat_frequency": 30,
            "log_level": "debug",
        }
    }


@pytest.mark.asyncio
async def test_standalone_ui_schema_help_and_assets_are_available(tmp_path: Path) -> None:
    """Standalone mode should expose its schema-driven UI and static help page."""
    app = create_app(config_path=_write_runtime_config(tmp_path))
    client = app.test_client()

    ui_response = await client.get(UI_PATH)
    help_response = await client.get(UI_HELP_PATH)
    schema_response = await client.get(f"{API_PREFIX}/schema")
    script_response = await client.get(f"{UI_PATH}/assets/functions.js")
    shared_css_response = await client.get(f"{UI_PATH}/assets/config_ui.css")
    generator_css_response = await client.get(f"{UI_PATH}/assets/styles.css")

    assert ui_response.status_code == 200
    ui_text = await ui_response.get_data(as_text=True)
    assert 'class="hidden"' in ui_text
    assert f'{UI_PATH}/assets/config_ui.css' in ui_text
    assert "config_ui.css?v=" in ui_text
    assert "functions.js?v=" in ui_text
    assert 'id="selectedConfigurationDisplay"' in ui_text
    assert 'id="browseConfigurationButton"' in ui_text
    script_text = await script_response.get_data(as_text=True)
    generator_css_text = await generator_css_response.get_data(as_text=True)
    assert f"{API_PREFIX}/status" not in script_text
    assert "Ready." not in script_text
    assert "No saved configuration files were found" in script_text
    assert "generated-field" in generator_css_text
    assert ".hidden" in generator_css_text
    assert ".page-shell" in generator_css_text
    assert "#configurationForm fieldset fieldset" in generator_css_text
    assert "border: 0" in generator_css_text
    assert help_response.status_code == 200
    help_text = await help_response.get_data(as_text=True)
    assert "Supervisor" in help_text
    assert 'class="page-shell client-config-generator-shell"' in help_text
    assert f'{UI_PATH}/assets/config_ui.css' in help_text
    assert "https://opamp.info" in help_text
    schema_payload = await schema_response.get_json()
    assert schema_payload["schema"]["title"] == "OpAMP Consumer Configuration"
    consumer_properties = schema_payload["schema"]["properties"]["consumer"]["properties"]
    assert consumer_properties["transport"]["enum"] == ["http", "https", "websocket"]
    assert [item["label"] for item in consumer_properties["transport"]["x-options"]] == [
        "HTTP",
        "HTTPS",
        "websocket",
    ]
    property_names = list(consumer_properties)
    assert property_names.index("transport") < property_names.index("tls")
    assert property_names.index("tls") < property_names.index("processTracking")
    assert consumer_properties["transport"]["x-refresh-form"] is True
    assert consumer_properties["tls"]["x-visible-when"] == {
        "path": "consumer.transport",
        "values": ["https", "websocket"],
    }
    assert "x-ui-section" not in consumer_properties["tls"]
    assert consumer_properties["agent_capabilities"]["x-control"] == "multi-select"
    assert consumer_properties["agent_capabilities"]["x-options"][0]["value"] == "AcceptsRemoteConfig"
    custom_section_fields = [
        property_name
        for property_name, property_schema in consumer_properties.items()
        if property_schema.get("x-ui-section") == "Custom Config Values"
    ]
    assert custom_section_fields == ["chat_ops_port", "allow_custom_capabilities"]
    assert script_response.status_code == 200
    assert shared_css_response.status_code == 200
    assert ".page-shell" in await shared_css_response.get_data(as_text=True)


@pytest.mark.asyncio
async def test_api_validates_saves_lists_and_loads_configuration(tmp_path: Path) -> None:
    """Versioned API controls should round trip a selected configuration file."""
    app = create_app(config_path=_write_runtime_config(tmp_path))
    client = app.test_client()
    request_payload = {"configuration": _valid_configuration()}

    validation_response = await client.post(f"{API_PREFIX}/validate", json=request_payload)
    save_response = await client.put(
        f"{API_PREFIX}/configurations/team/consumer.json",
        json=request_payload,
    )
    list_response = await client.get(f"{API_PREFIX}/configurations")
    load_response = await client.get(f"{API_PREFIX}/configurations/team/consumer.json")

    assert (await validation_response.get_json())["valid"] is True
    assert (await save_response.get_json())["saved"] is True
    assert (await list_response.get_json())["configurations"] == ["team/consumer.json"]
    assert (await load_response.get_json())["configuration"] == _valid_configuration()


@pytest.mark.asyncio
async def test_read_only_api_rejects_save(tmp_path: Path) -> None:
    """Read-only runtime config should disable the save control and API mutation."""
    app = create_app(config_path=_write_runtime_config(tmp_path, read_only=True))
    client = app.test_client()

    ui_response = await client.get(UI_PATH)
    save_response = await client.put(
        f"{API_PREFIX}/configurations/consumer.json",
        json={"configuration": _valid_configuration()},
    )

    assert 'id="saveButton" type="button" disabled aria-disabled="true"' in (
        await ui_response.get_data(as_text=True)
    )
    assert save_response.status_code == 403


@pytest.mark.asyncio
async def test_embedded_registration_exposes_provider_navigation(tmp_path: Path) -> None:
    """Embedded mode should mount routes and retain a Server Console navigation link."""
    app = Quart(__name__)
    register_client_config_generator_component(
        app,
        config_path=_write_runtime_config(tmp_path),
    )

    response = await app.test_client().get(UI_PATH)
    response_text = await response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'href="/ui"' in response_text
    assert 'class="hidden"' not in response_text


@pytest.mark.asyncio
async def test_api_reports_bad_payloads_missing_files_and_validation_errors(
    tmp_path: Path,
) -> None:
    """API failure controls should return stable client errors without writing files."""
    app = create_app(config_path=_write_runtime_config(tmp_path))
    client = app.test_client()

    missing_body_response = await client.post(f"{API_PREFIX}/validate", json={})
    missing_file_response = await client.get(
        f"{API_PREFIX}/configurations/missing.json"
    )
    invalid_save_response = await client.put(
        f"{API_PREFIX}/configurations/invalid.json",
        json={"configuration": {"consumer": {}}},
    )
    invalid_name_response = await client.put(
        f"{API_PREFIX}/configurations/consumer.yaml",
        json={"configuration": _valid_configuration()},
    )

    assert missing_body_response.status_code == 400
    assert missing_file_response.status_code == 404
    assert invalid_save_response.status_code == 400
    assert invalid_name_response.status_code == 400


@pytest.mark.asyncio
async def test_root_unknown_route_and_duplicate_registration_are_safe(tmp_path: Path) -> None:
    """Standalone navigation and idempotent plugin registration should remain stable."""
    config_path = _write_runtime_config(tmp_path)
    app = create_app(config_path=config_path)
    register_client_config_generator_component(app, config_path=config_path)
    client = app.test_client()

    root_response = await client.get("/")
    unknown_response = await client.get("/unknown")

    assert root_response.status_code == 302
    assert root_response.location.endswith(UI_PATH)
    assert unknown_response.status_code == 302


@pytest.mark.asyncio
async def test_auth_guard_returns_host_managed_rejection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Provider-auth rejection should protect plugin paths and include its challenge."""
    monkeypatch.setattr(
        app_module,
        "evaluate_ui_http_auth",
        lambda **_: UIAuthResult(
            allowed=False,
            status_code=401,
            error="missing bearer token",
            www_authenticate='Bearer realm="test"',
        ),
    )
    app = create_app(config_path=_write_runtime_config(tmp_path))

    response = await app.test_client().get(f"{API_PREFIX}/schema")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == 'Bearer realm="test"'


def test_opamp_integration_delegates_registration(tmp_path: Path) -> None:
    """The published provider entry point should mount component routes."""
    app = Quart("integration-entry-point")
    app.extensions["client_config_generator_service:config_path"] = str(
        _write_runtime_config(tmp_path)
    )

    register_client_config_generator_feature(app)

    assert any(rule.rule == UI_PATH for rule in app.url_map.iter_rules())


def test_main_runs_with_configured_standalone_port(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Console entry point should pass parsed host and configured port to Quart."""
    config_path = _write_runtime_config(tmp_path)
    captured = {}

    def fake_run(self, **run_options) -> None:
        """Capture Quart run arguments without opening a listening socket."""
        del self
        captured.update(run_options)

    monkeypatch.setattr("sys.argv", ["client-config-generator-service", "--config-path", str(config_path)])
    monkeypatch.setattr(Quart, "run", fake_run)

    app_module.main()

    assert captured["host"] == app_module.DEFAULT_BIND_HOST
    assert captured["port"] == 8095
    assert captured["debug"] is True
