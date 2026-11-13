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

"""Catalog service route and auth test coverage.

Test-case reference: catalog-service/docs/TEST_CASES.md
"""

from __future__ import annotations

import json
from http import HTTPStatus
from pathlib import Path

import pytest
from quart import Quart

from catalog_service.app import APP_EXTENSION_INDEX_SERVICE, create_app
from catalog_service.auth_integration import UIAuthResult
from catalog_service.config import CatalogServiceConfig, CatalogSource
from catalog_service.routes import register_catalog_routes
from catalog_service.service import CatalogFileIndexService
from shared.security_headers import (
    CONTENT_SECURITY_POLICY_HEADER,
    CONTENT_SECURITY_POLICY_REPORT_ONLY_HEADER,
    SHARED_CONTENT_SECURITY_POLICY,
    STRICT_REPORT_ONLY_CONTENT_SECURITY_POLICY,
    X_CONTENT_TYPE_OPTIONS_HEADER,
    X_CONTENT_TYPE_OPTIONS_NOSNIFF,
    X_FRAME_OPTIONS_DENY,
    X_FRAME_OPTIONS_HEADER,
)


@pytest.mark.asyncio
async def test_catalog_routes_render_ui_help_and_api(tmp_path: Path) -> None:
    source_dir = tmp_path / "catalog"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "sample.yaml").write_text(
        "# config-service: config_type=fluentbit\n# config-service: version=5.0.4\n",
        encoding="utf-8",
    )

    config = CatalogServiceConfig(
        enabled=True,
        menu_label="Config Catalog",
        route_path="/catalog",
        help_path="/catalog/help",
        ui_base_css_path="/config-service/ui/assets/config_ui.css",
        web_port=8090,
        ui_refresh_seconds=45,
        sources=(CatalogSource(folder="catalog", extensions=(".yaml",)),),
        raw_payload={},
    )
    service = CatalogFileIndexService(repo_root=tmp_path, config=config)

    app = Quart(__name__)
    register_catalog_routes(app=app, config=config, service=service)

    async with app.test_client() as client:
        ui_resp = await client.get("/catalog")
        assert ui_resp.status_code == 200
        ui_html = (await ui_resp.get_data()).decode("utf-8")
        javascript_resp = await client.get("/catalog/assets/catalog_ui.js")
        assert javascript_resp.status_code == 200
        assert javascript_resp.mimetype == "text/javascript"
        ui_javascript = (await javascript_resp.get_data()).decode("utf-8")
        assert "Config Catalog" in ui_html
        assert "/catalog/assets/catalog_ui_api.js" in ui_html
        assert "/catalog/assets/catalog_ui.js" in ui_html
        assert "/catalog/assets/catalog_ui.css" in ui_html
        assert "Selection checkbox state" in ui_javascript
        assert "Unselected" in ui_javascript
        assert "config type (metadata)" in ui_javascript
        assert "engine (inferred)" in ui_javascript
        assert 'id="catalogSelectionActions"' in ui_html
        assert 'id="catalogApplySelectionBtn"' in ui_html
        assert "selection_callback" in ui_javascript
        assert 'id="featureMenuGroup"' in ui_html
        assert "catalogReadonlyOverlay" in ui_html
        assert "CONFIG_SERVICE_ENTRY_POINT" not in ui_html
        assert "config_service.opamp_integration:register_config_service_feature" in ui_javascript
        assert 'data-history-back-button="true"' in ui_html
        assert 'hidden' in ui_html
        assert 'href="/ui" >Server Console</a>' in ui_html
        assert "const CONFIGURED_UI_REFRESH_SECONDS = parseInt(45, 10);" in ui_javascript

        help_resp = await client.get("/catalog/help")
        assert help_resp.status_code == 200
        help_html = (await help_resp.get_data()).decode("utf-8")
        assert "How Metadata Columns Are Built" in help_html
        assert "Selection Checkbox Direction" in help_html
        assert "File Change Refresh" in help_html
        assert "selected and unselected rows available for direct filtering" in help_html
        assert "Apply button appears when a callback URL is provided" in help_html

        data_resp = await client.get("/catalog/api/files")
        assert data_resp.status_code == 200
        payload = await data_resp.get_json()

        api_js_resp = await client.get("/catalog/assets/catalog_ui_api.js")
        assert api_js_resp.status_code == 200
        assert api_js_resp.content_type.startswith("text/javascript")
        api_js = (await api_js_resp.get_data()).decode("utf-8")
        assert "window.CatalogServiceUiApi" in api_js
        assert 'routePath + "/api/files"' in api_js
        assert 'routePath + "/api/file-content"' in api_js

        file_resp = await client.get(
            "/catalog/api/file-content",
            query_string={"path": str((source_dir / "sample.yaml").resolve())},
        )
        assert file_resp.status_code == 200
        file_payload = await file_resp.get_json()

    assert payload["total"] == 1
    assert payload["rows"][0]["filename"] == "sample.yaml"
    assert file_payload["filename"] == "sample.yaml"
    assert "config_type=fluentbit" in file_payload["text"]


@pytest.mark.asyncio
async def test_catalog_app_starts_and_stops_background_refresh_with_lifecycle(tmp_path: Path) -> None:
    source_dir = tmp_path / "catalog"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "sample.yaml").write_text("service:\n  flush: 1\n", encoding="utf-8")

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
                        "sources": [{"folder": "catalog", "extensions": [".yaml"]}],
                        "ui_refresh_seconds": 1,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    app = create_app(mode="standalone", config_path=str(config_path))
    service = app.extensions[APP_EXTENSION_INDEX_SERVICE]
    assert service._background_refresh_thread is None

    async with app.test_app():
        assert service._background_refresh_thread is not None
        assert service._background_refresh_thread.is_alive() is True

    assert service._background_refresh_thread is None


@pytest.mark.asyncio
async def test_standalone_catalog_app_exposes_feature_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "catalog-service.json"
    config_path.write_text(
        """
        {
          "component-entry-points": {
            "quart": [
              {
                "entry_point": "catalog_service.app:register_catalog_component",
                "label": "Config Catalog",
                "url": "/catalog",
                "enabled": true
              }
            ]
          },
          "opamp": {
            "config_catalog": {
              "enabled": true,
              "menu_label": "Config Catalog",
              "route_path": "/catalog",
              "help_path": "/catalog/help",
              "ui_base_css_path": "/config-service/ui/assets/config_ui.css",
              "web_port": 8090,
              "sources": [
                {
                  "folder": "catalog",
                  "extensions": [".yaml"]
                }
              ]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )
    source_dir = tmp_path / "catalog"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "sample.yaml").write_text("# config-service: version=5.0.4\n", encoding="utf-8")

    monkeypatch.setenv("CATALOG_SERVICE_CONFIG_PATH", str(config_path))

    from catalog_service.app import create_app

    app = create_app(mode="standalone", config_path=str(config_path))
    async with app.test_client() as client:
        feature_resp = await client.get("/api/ui/features")
        assert feature_resp.status_code == 200
        feature_payload = await feature_resp.get_json()
        assert feature_payload["items"][0]["label"] == "Config Catalog"
        assert feature_payload["items"][0]["entry_point"] == "catalog_service.app:register_catalog_component"

        ui_resp = await client.get("/catalog")
        assert ui_resp.status_code == 200
        ui_html = (await ui_resp.get_data()).decode("utf-8")
        assert '/catalog/assets/catalog_ui.css' in ui_html
        assert '/catalog/assets/catalog_ui_api.js?v=' in ui_html
        assert '/catalog/assets/opamp_logo.png' in ui_html
        assert '/catalog/assets/config_editor_icon.png' in ui_html
        assert 'data-history-back-button="true"' in ui_html
        assert 'aria-hidden="true"' in ui_html
        assert 'tabindex="-1"' in ui_html
        assert ">Back</button>" in ui_html
        assert ">Server Console</a>" in ui_html
        css_resp = await client.get("/catalog/assets/catalog_ui.css")
        assert css_resp.status_code == 200
        assert css_resp.content_type.startswith("text/css")
        api_js_resp = await client.get("/catalog/assets/catalog_ui_api.js")
        assert api_js_resp.status_code == 200
        assert api_js_resp.content_type.startswith("text/javascript")
        logo_resp = await client.get("/catalog/assets/opamp_logo.png")
        assert logo_resp.status_code == 200
        assert logo_resp.content_type.startswith("image/png")
        icon_resp = await client.get("/catalog/assets/config_editor_icon.png")
        assert icon_resp.status_code == 200
        assert icon_resp.content_type.startswith("image/png")
        data_resp = await client.get("/catalog/api/files")
        assert data_resp.status_code == 200
        data_payload = await data_resp.get_json()
        assert data_payload["total"] == 1


@pytest.mark.asyncio
async def test_standalone_catalog_unknown_route_redirects_to_landing_page(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "catalog-service.json"
    config_path.write_text(
        """
        {
          "component-entry-points": {
            "quart": [
              {
                "entry_point": "catalog_service.app:register_catalog_component",
                "label": "Config Catalog",
                "url": "/catalog",
                "enabled": true
              }
            ]
          },
          "opamp": {
            "config_catalog": {
              "enabled": true,
              "menu_label": "Config Catalog",
              "route_path": "/catalog",
              "help_path": "/catalog/help",
              "ui_base_css_path": "/config-service/ui/assets/config_ui.css",
              "web_port": 8090,
              "sources": [
                {
                  "folder": "catalog",
                  "extensions": [".yaml"]
                }
              ]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )
    source_dir = tmp_path / "catalog"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "sample.yaml").write_text("service:\n  flush: 1\n", encoding="utf-8")
    monkeypatch.setenv("CATALOG_SERVICE_CONFIG_PATH", str(config_path))

    from catalog_service.app import create_app

    app = create_app(mode="standalone", config_path=str(config_path))
    async with app.test_client() as client:
        response = await client.get("/does-not-exist")
        assert response.status_code in {301, 302, 307, 308}
        assert response.headers["Location"].startswith(
            "https://htmlpreview.github.io/?https://raw.githubusercontent.com/"
            "opamp-observe/opamp-core/main/github-landingpage/index.html"
        )
        assert (
            response.headers[CONTENT_SECURITY_POLICY_HEADER]
            == SHARED_CONTENT_SECURITY_POLICY
        )
        assert (
            response.headers[CONTENT_SECURITY_POLICY_REPORT_ONLY_HEADER]
            == STRICT_REPORT_ONLY_CONTENT_SECURITY_POLICY
        )
        assert response.headers[X_FRAME_OPTIONS_HEADER] == X_FRAME_OPTIONS_DENY
        assert response.headers[X_CONTENT_TYPE_OPTIONS_HEADER] == X_CONTENT_TYPE_OPTIONS_NOSNIFF


@pytest.mark.asyncio
async def test_standalone_catalog_app_exposes_config_service_feature_when_configured(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "catalog-service.json"
    config_path.write_text(
        """
        {
          "component-entry-points": {
            "quart": [
              {
                "entry_point": "catalog_service.app:register_catalog_component",
                "label": "Config Catalog",
                "url": "/catalog",
                "enabled": true
              },
              {
                "entry_point": "config_service.opamp_integration:register_config_service_feature",
                "label": "Config Editor",
                "url": "/config-service/ui",
                "enabled": true
              }
            ]
          },
          "opamp": {
            "config_catalog": {
              "enabled": true,
              "menu_label": "Config Catalog",
              "route_path": "/catalog",
              "help_path": "/catalog/help",
              "ui_base_css_path": "/config-service/ui/assets/config_ui.css",
              "web_port": 8090,
              "sources": [
                {
                  "folder": "catalog",
                  "extensions": [".yaml"]
                }
              ]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )
    source_dir = tmp_path / "catalog"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "sample.yaml").write_text("service:\n  flush: 1\n", encoding="utf-8")

    monkeypatch.setenv("CATALOG_SERVICE_CONFIG_PATH", str(config_path))

    from catalog_service.app import create_app

    app = create_app(mode="standalone", config_path=str(config_path))
    async with app.test_client() as client:
        feature_resp = await client.get("/api/ui/features")
        assert feature_resp.status_code == 200
        feature_payload = await feature_resp.get_json()

        ui_resp = await client.get("/catalog")
        assert ui_resp.status_code == 200
        ui_html = (await ui_resp.get_data()).decode("utf-8")
        javascript_resp = await client.get("/catalog/assets/catalog_ui.js")
        assert javascript_resp.status_code == 200
        ui_javascript = (await javascript_resp.get_data()).decode("utf-8")

    assert [item["label"] for item in feature_payload["items"]] == [
        "Config Catalog",
        "Config Editor",
    ]
    assert "/catalog/assets/catalog_ui.js" in ui_html
    assert "config_service.opamp_integration:register_config_service_feature" in ui_javascript


@pytest.mark.asyncio
async def test_embedded_config_service_validate_save_uses_catalog_runtime_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
                        "menu_label": "Config Catalog",
                        "route_path": "/catalog",
                        "help_path": "/catalog/help",
                        "ui_base_css_path": "/config-service/ui/assets/config_ui.css",
                        "web_port": 8090,
                        "sources": [
                            {
                                "folder": "catalog",
                                "extensions": [".yaml"],
                            }
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    source_dir = tmp_path / "catalog"
    source_dir.mkdir(parents=True, exist_ok=True)
    target_path = source_dir / "sample.yaml"
    target_path.write_text("pipeline:\n  inputs: []\n", encoding="utf-8")

    monkeypatch.setenv("CATALOG_SERVICE_CONFIG_PATH", str(config_path))
    monkeypatch.delenv("CONFIG_TOOL_CONFIG_PATH", raising=False)
    monkeypatch.delenv("OPAMP_CONFIG_PATH", raising=False)

    from catalog_service.app import create_app

    app = create_app(mode="standalone", config_path=str(config_path))
    async with app.test_client() as client:
        response = await client.post(
            "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
            json={
                "config": {
                    "service": {"flush": 1},
                    "pipeline": {
                        "inputs": [
                            {
                                "name": "forward",
                                "buffer_chunk_size": 1024,
                                "buffer_max_size": 2048,
                                "port": 24224,
                            }
                        ],
                        "outputs": [{"name": "null", "match": "*"}],
                    },
                },
                "annotations": {},
                "save_on_success": True,
                "save_source_path": str(target_path),
                "include_config_header": True,
            },
        )
        assert response.status_code == 200
        body = await response.get_json()

    assert body["ok"] is True
    assert body["saved"] is True
    assert body["save_path"] == str(target_path.resolve())
    saved_text = target_path.read_text(encoding="utf-8")
    assert "# config-service: config_type=fluentbit" in saved_text
    assert "pipeline:" in saved_text


@pytest.mark.asyncio
async def test_standalone_catalog_app_enforces_ui_auth(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "catalog-service.json"
    config_path.write_text(
        """
        {
          "component-entry-points": {
            "quart": [
              {
                "entry_point": "catalog_service.app:register_catalog_component",
                "label": "Config Catalog",
                "url": "/catalog",
                "enabled": true
              }
            ]
          },
          "opamp": {
            "config_catalog": {
              "enabled": true,
              "menu_label": "Config Catalog",
              "route_path": "/catalog",
              "help_path": "/catalog/help",
              "ui_base_css_path": "/config-service/ui/assets/config_ui.css",
              "web_port": 8090,
              "sources": [
                {
                  "folder": "catalog",
                  "extensions": [".yaml"]
                }
              ]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )
    source_dir = tmp_path / "catalog"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "sample.yaml").write_text("# config-service: version=5.0.4\n", encoding="utf-8")
    monkeypatch.setenv("CATALOG_SERVICE_CONFIG_PATH", str(config_path))

    from catalog_service import app as catalog_app_module

    def deny_auth(**_kwargs: object) -> UIAuthResult:
        return UIAuthResult(
            allowed=False,
            status_code=HTTPStatus.UNAUTHORIZED,
            error="authorization failed",
            www_authenticate='Bearer realm="opamp-provider"',
        )

    monkeypatch.setattr(catalog_app_module, "evaluate_ui_http_auth", deny_auth)
    app = catalog_app_module.create_app(mode="standalone", config_path=str(config_path))

    async with app.test_client() as client:
        response = await client.get("/catalog")
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.headers["WWW-Authenticate"] == 'Bearer realm="opamp-provider"'
        payload = await response.get_json()

    assert payload["error"] == "authorization failed"


@pytest.mark.asyncio
async def test_standalone_catalog_auth_rejection_is_logged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "catalog-service.json"
    config_path.write_text(
        """
        {
          "component-entry-points": {
            "quart": [
              {
                "entry_point": "catalog_service.app:register_catalog_component",
                "label": "Config Catalog",
                "url": "/catalog",
                "enabled": true
              }
            ]
          },
          "opamp": {
            "config_catalog": {
              "enabled": true,
              "menu_label": "Config Catalog",
              "route_path": "/catalog",
              "help_path": "/catalog/help",
              "ui_base_css_path": "/config-service/ui/assets/config_ui.css",
              "web_port": 8090,
              "sources": [
                {
                  "folder": "catalog",
                  "extensions": [".yaml"]
                }
              ]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )
    source_dir = tmp_path / "catalog"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "sample.yaml").write_text("# config-service: version=5.0.4\n", encoding="utf-8")
    monkeypatch.setenv("CATALOG_SERVICE_CONFIG_PATH", str(config_path))

    from catalog_service import app as catalog_app_module

    def deny_auth(**_kwargs: object) -> UIAuthResult:
        return UIAuthResult(
            allowed=False,
            status_code=HTTPStatus.UNAUTHORIZED,
            error="authorization failed",
            www_authenticate='Bearer realm="opamp-provider"',
        )

    monkeypatch.setattr(catalog_app_module, "evaluate_ui_http_auth", deny_auth)
    app = catalog_app_module.create_app(mode="standalone", config_path=str(config_path))
    warning_calls: list[tuple[object, ...]] = []

    def record_warning(message: object, *args: object, **_kwargs: object) -> None:
        warning_calls.append((message, *args))

    monkeypatch.setattr(app.logger, "warning", record_warning)

    async with app.test_client() as client:
        response = await client.get("/catalog")
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    assert warning_calls
    rendered = str(warning_calls[0][0]) % tuple(warning_calls[0][1:])
    assert "catalog request rejected by auth" in rendered
    assert "authorization failed" in rendered


@pytest.mark.asyncio
async def test_embedded_catalog_app_relies_on_outer_auth_layer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "catalog-service.json"
    config_path.write_text(
        """
        {
          "component-entry-points": {
            "quart": [
              {
                "entry_point": "catalog_service.app:register_catalog_component",
                "label": "Config Catalog",
                "url": "/catalog",
                "enabled": true
              }
            ]
          },
          "opamp": {
            "config_catalog": {
              "enabled": true,
              "menu_label": "Config Catalog",
              "route_path": "/catalog",
              "help_path": "/catalog/help",
              "ui_base_css_path": "/config-service/ui/assets/config_ui.css",
              "web_port": 8090,
              "sources": [
                {
                  "folder": "catalog",
                  "extensions": [".yaml"]
                }
              ]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )
    source_dir = tmp_path / "catalog"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "sample.yaml").write_text("# config-service: version=5.0.4\n", encoding="utf-8")
    monkeypatch.setenv("CATALOG_SERVICE_CONFIG_PATH", str(config_path))

    from catalog_service import app as catalog_app_module

    def deny_auth(**_kwargs: object) -> UIAuthResult:
        return UIAuthResult(
            allowed=False,
            status_code=HTTPStatus.UNAUTHORIZED,
            error="authorization failed",
            www_authenticate='Bearer realm="opamp-provider"',
        )

    monkeypatch.setattr(catalog_app_module, "evaluate_ui_http_auth", deny_auth)
    app = catalog_app_module.create_app(mode="embedded", config_path=str(config_path))

    async with app.test_client() as client:
        response = await client.get("/catalog")
        assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_catalog_file_content_rejections_are_logged(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    source_dir = tmp_path / "catalog"
    source_dir.mkdir(parents=True, exist_ok=True)
    allowed = source_dir / "sample.yaml"
    allowed.write_text("# config-service: version=5.0.4\n", encoding="utf-8")
    outside = tmp_path / "outside.yaml"
    outside.write_text("service:\n  flush: 1\n", encoding="utf-8")

    config = CatalogServiceConfig(
        enabled=True,
        menu_label="Config Catalog",
        route_path="/catalog",
        help_path="/catalog/help",
        ui_base_css_path="/config-service/ui/assets/config_ui.css",
        web_port=8090,
        sources=(CatalogSource(folder="catalog", extensions=(".yaml",)),),
        raw_payload={},
    )
    service = CatalogFileIndexService(repo_root=tmp_path, config=config)

    app = Quart(__name__)
    register_catalog_routes(app=app, config=config, service=service)
    caplog.set_level("WARNING")

    async with app.test_client() as client:
        missing_path_response = await client.get("/catalog/api/file-content")
        assert missing_path_response.status_code == HTTPStatus.BAD_REQUEST

        forbidden_response = await client.get(
            "/catalog/api/file-content",
            query_string={"path": str(outside.resolve())},
        )
        assert forbidden_response.status_code == HTTPStatus.FORBIDDEN

    assert "path argument is missing" in caplog.text
    assert "outside configured sources" in caplog.text
