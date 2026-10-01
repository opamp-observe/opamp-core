#!/usr/bin/env python3
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

"""Quart application for the schema-driven client configuration generator."""

from __future__ import annotations

import argparse
import importlib.resources
import json
import logging
import os
from http import HTTPStatus
from pathlib import Path
from typing import Any

from quart import Quart, Response, jsonify, redirect, request, send_from_directory

from client_config_generator_service.auth_integration import evaluate_ui_http_auth
from client_config_generator_service.runtime_config import (
    APP_CONFIG_MODE,
    APP_EXTENSION_CONFIG_PATH,
    APP_EXTENSION_SERVICE,
    APP_MODE_STANDALONE,
    ENV_CONFIG_PATH,
    GeneratorSettings,
    component_root,
    load_settings,
)
from client_config_generator_service.service import (
    KEY_CONFIGURATION,
    KEY_ERRORS,
    KEY_VALID,
    ConfigurationFileService,
)

APP_MODE_EMBEDDED = "embedded"
DEFAULT_BIND_HOST = "0.0.0.0"  # noqa: S104 - standalone service must be container reachable.
EXTENSION_REGISTRATION_MARKER = "client_config_generator_service:registered"
EXTENSION_SETTINGS = "client_config_generator_service:settings"

API_PREFIX = "/client-config-generator-service/api/v1"
UI_PATH = "/client-config-generator-service/ui"
UI_HELP_PATH = "/client-config-generator-service/ui/help"
UI_ASSET_PATH = "/client-config-generator-service/ui/assets/<path:filename>"

HEADER_AUTHORIZATION = "Authorization"
HEADER_WWW_AUTHENTICATE = "WWW-Authenticate"
KEY_CONFIGURATIONS = "configurations"
KEY_ERROR = "error"
KEY_NAME = "name"
KEY_SAVED = "saved"
KEY_SCHEMA = "schema"
CONFIG_EDITOR_STYLESHEET_NAME = "config_ui.css"
CONFIG_EDITOR_STYLESHEET_PACKAGE = "config_service"
PLACEHOLDER_UI_ASSET_SUFFIX = "__CLIENT_CONFIG_GENERATOR_UI_ASSET_SUFFIX__"
PLACEHOLDER_PROVIDER_LINK_ATTRIBUTES = "__PROVIDER_LINK_ATTRIBUTES__"
PLACEHOLDER_SAVE_DISABLED_ATTRIBUTES = "__CLIENT_CONFIG_GENERATOR_SAVE_DISABLED_ATTRIBUTES__"
PROVIDER_CONFIG_EXTENSION_KEYS = (
    APP_EXTENSION_CONFIG_PATH,
    "config_service:config_path",
    "catalog_service:config_path",
)
LANDING_PAGE_REDIRECT_URL = (
    "https://htmlpreview.github.io/?https://raw.githubusercontent.com/"
    "opamp-observe/opamp-core/main/github-landingpage/index.html"
)


def _configure_logging(settings: GeneratorSettings) -> None:
    """Configure debug-oriented structured console logging.

    Args:
        settings: Effective runtime settings containing the selected log level.
    """
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.DEBUG),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )


def _embedded_config_path(app: Quart) -> str | None:
    """Find the host application's active runtime configuration path.

    Args:
        app: Host Quart application receiving plugin routes.
    """
    for extension_key in PROVIDER_CONFIG_EXTENSION_KEYS:
        configured_path = str(app.extensions.get(extension_key) or "").strip()
        if configured_path:
            return configured_path
    environment_path = os.environ.get("OPAMP_CONFIG_PATH", "").strip()
    return environment_path or None


def _provider_link_attributes(mode: str) -> str:
    """Hide provider navigation when the generator is running standalone.

    Args:
        mode: Runtime deployment mode name.
    """
    if mode == APP_MODE_STANDALONE:
        return 'class="hidden" aria-hidden="true" tabindex="-1"'
    return ""


def _asset_suffix() -> str:
    """Return a stable cache-busting suffix for packaged UI assets."""
    return "?v=" + str(int(Path(__file__).stat().st_mtime_ns))


def _save_disabled_attributes(settings: GeneratorSettings) -> str:
    """Return Save button attributes for read-only deployments.

    Args:
        settings: Effective runtime settings containing the read-only flag.
    """
    if not settings.read_only:
        return ""
    return 'disabled aria-disabled="true" title="Read-only deployment: saving is disabled."'


def _render_ui_html(
    html_directory: Path,
    filename: str,
    mode: str,
    settings: GeneratorSettings,
) -> str:
    """Render shared placeholders in a packaged UI HTML file.

    Args:
        html_directory: Directory containing the packaged HTML asset.
        filename: HTML file name to render.
        mode: Runtime deployment mode used to show or hide provider links.
        settings: Effective runtime settings used to render deployment-specific controls.
    """
    html_template = (html_directory / filename).read_text(encoding="utf-8")
    return (
        html_template.replace(PLACEHOLDER_UI_ASSET_SUFFIX, _asset_suffix()).replace(
            PLACEHOLDER_PROVIDER_LINK_ATTRIBUTES,
            _provider_link_attributes(mode),
        ).replace(
            PLACEHOLDER_SAVE_DISABLED_ATTRIBUTES,
            _save_disabled_attributes(settings),
        )
    )


def _json_error(message: str, status_code: int) -> tuple[Response, int]:
    """Build a stable JSON error response.

    Args:
        message: Safe response detail.
        status_code: HTTP failure status.
    """
    return jsonify({KEY_ERROR: message}), status_code


def _configuration_from_request(payload: Any) -> Any:
    """Extract the named configuration object from an API payload.

    Args:
        payload: Decoded request JSON.
    """
    if not isinstance(payload, dict) or KEY_CONFIGURATION not in payload:
        raise ValueError("request body must contain a configuration value")
    return payload[KEY_CONFIGURATION]


def _load_config_editor_stylesheet() -> str:
    """Load the config editor stylesheet used as the shared UI baseline."""
    try:
        stylesheet = (
            importlib.resources.files(CONFIG_EDITOR_STYLESHEET_PACKAGE)
            / "html"
            / CONFIG_EDITOR_STYLESHEET_NAME
        )
        return stylesheet.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError):
        source_stylesheet = (
            component_root().parents[2]
            / "config-service"
            / "src"
            / "config_service"
            / "html"
            / CONFIG_EDITOR_STYLESHEET_NAME
        )
        return source_stylesheet.read_text(encoding="utf-8")


def _register_auth_guard(app: Quart) -> None:
    """Register provider-compatible authentication for generator routes.

    Args:
        app: Quart application receiving the request guard.
    """
    @app.before_request
    async def enforce_generator_auth() -> tuple[Response, int] | None:
        """Reject protected requests using the host-managed auth policy."""
        if not request.path.startswith("/client-config-generator-service/"):
            return None
        auth_result = evaluate_ui_http_auth(
            path=request.path,
            method=request.method,
            authorization_header=request.headers.get(HEADER_AUTHORIZATION),
            remote_addr=request.remote_addr,
        )
        if auth_result.allowed:
            return None
        response = jsonify({KEY_ERROR: auth_result.error})
        if auth_result.www_authenticate:
            response.headers[HEADER_WWW_AUTHENTICATE] = auth_result.www_authenticate
        return response, auth_result.status_code


# Route registration intentionally keeps shared route state in one closure.
# pylint: disable=too-many-locals
def register_client_config_generator_component(
    app: Quart,
    *,
    config_path: str | Path | None = None,
    mode: str = APP_MODE_EMBEDDED,
) -> None:
    """Register the generator UI, help page, and API on a Quart application.

    Args:
        app: Quart host application.
        config_path: Optional explicit shared OpAMP configuration path.
        mode: ``embedded`` or ``standalone`` deployment mode.
    """
    if app.extensions.get(EXTENSION_REGISTRATION_MARKER) is True:
        app.logger.debug("client config generator routes already registered")
        return

    effective_config_path = config_path
    if effective_config_path is None and mode != APP_MODE_STANDALONE:
        effective_config_path = _embedded_config_path(app)
    settings = load_settings(effective_config_path)
    schema_path = component_root() / "schemas" / "consumer_config_schema.json"
    html_directory = component_root() / "html"
    file_service = ConfigurationFileService(
        root_directory=settings.configuration_directory,
        schema_path=schema_path,
        read_only=settings.read_only,
    )
    app.config[APP_CONFIG_MODE] = mode
    app.extensions[APP_EXTENSION_CONFIG_PATH] = str(settings.config_path)
    app.extensions[APP_EXTENSION_SERVICE] = file_service
    app.extensions[EXTENSION_SETTINGS] = settings
    app.extensions[EXTENSION_REGISTRATION_MARKER] = True
    _register_auth_guard(app)

    @app.get(UI_PATH)
    async def client_config_generator_ui() -> Response:
        """Serve the schema-driven configuration generator page."""
        return Response(
            _render_ui_html(html_directory, "index.html", mode, settings),
            content_type="text/html; charset=utf-8",
        )

    @app.get(UI_HELP_PATH)
    async def client_config_generator_help() -> Response:
        """Serve the static generator help page."""
        return Response(
            _render_ui_html(html_directory, "help.html", mode, settings),
            content_type="text/html; charset=utf-8",
        )

    @app.get(UI_ASSET_PATH)
    async def client_config_generator_asset(filename: str) -> Response:
        """Serve one packaged UI asset.

        Args:
            filename: Relative static asset name selected by the route.
        """
        if filename == CONFIG_EDITOR_STYLESHEET_NAME:
            return Response(
                _load_config_editor_stylesheet(),
                content_type="text/css; charset=utf-8",
            )
        return await send_from_directory(html_directory, filename)

    @app.get(f"{API_PREFIX}/schema")
    async def client_config_generator_schema() -> Response:
        """Return the consumer schema that drives the UI and validation."""
        return Response(
            json.dumps({KEY_SCHEMA: file_service.schema}),
            content_type="application/json; charset=utf-8",
        )

    @app.get(f"{API_PREFIX}/configurations")
    async def list_client_configurations() -> Response:
        """List saved consumer JSON files available for selection."""
        return jsonify({KEY_CONFIGURATIONS: file_service.list_configurations()})

    @app.get(f"{API_PREFIX}/configurations/<path:configuration_name>")
    async def load_client_configuration(configuration_name: str) -> Response | tuple[Response, int]:
        """Load one selected consumer configuration.

        Args:
            configuration_name: Relative JSON file name within configured storage.
        """
        try:
            configuration = file_service.load_configuration(configuration_name)
        except FileNotFoundError:
            return _json_error("configuration not found", HTTPStatus.NOT_FOUND)
        except (OSError, ValueError) as error:
            return _json_error(str(error), HTTPStatus.BAD_REQUEST)
        return jsonify({KEY_NAME: configuration_name, KEY_CONFIGURATION: configuration})

    @app.post(f"{API_PREFIX}/validate")
    async def validate_client_configuration() -> Response | tuple[Response, int]:
        """Validate an unsaved consumer configuration against the UI schema."""
        try:
            configuration = _configuration_from_request(await request.get_json())
        except (TypeError, ValueError) as error:
            return _json_error(str(error), HTTPStatus.BAD_REQUEST)
        return jsonify(file_service.validate_configuration(configuration))

    @app.put(f"{API_PREFIX}/configurations/<path:configuration_name>")
    async def save_client_configuration(configuration_name: str) -> Response | tuple[Response, int]:
        """Validate and save one selected consumer configuration.

        Args:
            configuration_name: Relative target JSON file name within configured storage.
        """
        try:
            configuration = _configuration_from_request(await request.get_json())
            saved_path = file_service.save_configuration(configuration_name, configuration)
        except PermissionError as error:
            return _json_error(str(error), HTTPStatus.FORBIDDEN)
        except (OSError, TypeError, ValueError) as error:
            return _json_error(str(error), HTTPStatus.BAD_REQUEST)
        return jsonify(
            {
                KEY_NAME: saved_path.relative_to(file_service.root_directory).as_posix(),
                KEY_SAVED: True,
                KEY_VALID: True,
                KEY_ERRORS: [],
            }
        )

    app.logger.info(
        "client config generator registered mode=%s config_path=%s storage=%s read_only=%s",
        mode,
        settings.config_path,
        settings.configuration_directory,
        settings.read_only,
    )


# pylint: enable=too-many-locals


def create_app(
    *,
    mode: str = APP_MODE_STANDALONE,
    config_path: str | Path | None = None,
) -> Quart:
    """Create a standalone Quart application.

    Args:
        mode: Runtime deployment mode used by navigation rendering.
        config_path: Optional explicit shared OpAMP configuration path.
    """
    settings = load_settings(config_path)
    _configure_logging(settings)
    app = Quart(__name__)
    app.logger.setLevel(getattr(logging, settings.log_level, logging.DEBUG))
    register_client_config_generator_component(app, config_path=config_path, mode=mode)

    @app.get("/")
    async def root() -> Response:
        """Redirect standalone root requests to the generator UI."""
        return redirect(UI_PATH)

    @app.errorhandler(404)
    async def redirect_unknown_route(_: object) -> Response:
        """Redirect unknown standalone routes to the project documentation."""
        return redirect(LANDING_PAGE_REDIRECT_URL)

    return app


def main() -> None:
    """Parse standalone options and run the Quart development server."""
    argument_parser = argparse.ArgumentParser(
        description="OpAMP client configuration generator service"
    )
    argument_parser.add_argument("--config-path", help="Shared OpAMP JSON configuration path")
    argument_parser.add_argument("--host", default=DEFAULT_BIND_HOST, help="Bind address")
    argument_parser.add_argument("--port", type=int, help="Override configured listen port")
    arguments = argument_parser.parse_args()
    if arguments.config_path:
        os.environ[ENV_CONFIG_PATH] = arguments.config_path
    settings = load_settings(arguments.config_path)
    application = create_app(config_path=arguments.config_path)
    application.run(
        host=arguments.host,
        port=arguments.port or settings.web_port,
        debug=True,
    )
