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

"""Quart route registration for OpAMP config-catalog UI."""

from __future__ import annotations

import html
import json
import logging
from functools import lru_cache
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from quart import Quart, Response, jsonify, request

from catalog_service.config import CatalogServiceConfig
from catalog_service.service import CatalogFileIndexService

CONFIG_EDITOR_ENTRY_POINT = "config_service.opamp_integration:register_config_service_feature"
HTML_DIR = Path(__file__).resolve().parent / "html"
CATALOG_HTML_PATH = HTML_DIR / "catalog.html"
CATALOG_HELP_HTML_PATH = HTML_DIR / "catalog_help.html"
CATALOG_UI_CSS_PATH = HTML_DIR / "catalog_ui.css"
CATALOG_UI_API_JS_PATH = HTML_DIR / "catalog_ui_api.js"
CATALOG_UI_JS_PATH = HTML_DIR / "catalog_ui.js"
CATALOG_UI_LOGO_PATH = HTML_DIR / "opamp_logo.png"
CATALOG_UI_ICON_PATH = HTML_DIR / "config_editor_icon.png"
PLACEHOLDER_TITLE = "__CATALOG_TITLE__"
PLACEHOLDER_ROUTE_PATH = "__CATALOG_ROUTE_PATH__"
PLACEHOLDER_HELP_PATH = "__CATALOG_HELP_PATH__"
PLACEHOLDER_CSS_PATH = "__CATALOG_CSS_PATH__"
PLACEHOLDER_COMPONENT_CSS_LINK = "__CATALOG_COMPONENT_CSS_LINK__"
PLACEHOLDER_API_JS_PATH = "__CATALOG_API_JS_PATH__"
PLACEHOLDER_JS_PATH = "__CATALOG_JS_PATH__"
PLACEHOLDER_LOGO_PATH = "__CATALOG_LOGO_PATH__"
PLACEHOLDER_ICON_PATH = "__CATALOG_ICON_PATH__"
PLACEHOLDER_UI_REFRESH_SECONDS = "__CATALOG_UI_REFRESH_SECONDS__"
PLACEHOLDER_CONFIG_EDITOR_ENTRY_POINT = "__CATALOG_CONFIG_EDITOR_ENTRY_POINT__"
PLACEHOLDER_PROVIDER_UI_LINK_ATTRS = "__CATALOG_PROVIDER_UI_LINK_ATTRS__"
PLACEHOLDER_CLIENT_ERRORS_ENDPOINT = "__CATALOG_CLIENT_ERRORS_ENDPOINT__"
REQUEST_ARG_PATH = "path"
RESPONSE_KEY_ERROR = "error"
RESPONSE_KEY_OK = "ok"
HEADER_REFERER = "Referer"
HEADER_USER_AGENT = "User-Agent"
KEY_MESSAGE = "message"
KEY_KIND = "kind"
KEY_SOURCE = "source"
KEY_PATH = "path"
KEY_STACK = "stack"
KEY_LINE = "line"
KEY_COLUMN = "column"
VALUE_UNKNOWN_UI_ERROR = "Unknown UI error"
VALUE_RUNTIME_ERROR = "runtime_error"
VALUE_BROWSER = "browser"
STYLESHEET_LINK_TEMPLATE = '<link rel="stylesheet" href="{stylesheet_path}" />'
ERR_PATH_REQUIRED = "path is required"
ERR_FILE_NOT_FOUND = "catalog file not found: {file_path}"
ERR_FILE_NOT_ALLOWED = "catalog file is not part of configured sources: {file_path}"
APP_CONFIG_KEY_MODE = "CATALOG_SERVICE_MODE"
APP_MODE_STANDALONE = "standalone"
EMBEDDED_LOGO_PATH = "/config-service/ui/assets/opamp_logo.png"
EMBEDDED_ICON_PATH = "/config-service/ui/assets/config_editor_icon.png"
LOGGER = logging.getLogger(__name__)

@lru_cache(maxsize=4)
def _load_html_asset(template_path: str, modified_time_ns: int) -> str:
    """Return cached HTML/CSS asset text keyed by file modification time."""
    _ = modified_time_ns
    return Path(template_path).read_text(encoding="utf-8")


def _read_text_asset(template_path: Path) -> str:
    """Read an HTML/CSS asset using a cache key that updates on file changes."""
    modified_time_ns = int(template_path.stat().st_mtime_ns)
    return _load_html_asset(str(template_path), modified_time_ns)


def _append_cache_bust_query(url: str, *, source_path: Path) -> str:
    """Append/update a cache-busting query value derived from an asset mtime."""
    try:
        version = str(int(source_path.stat().st_mtime_ns))
    except OSError:
        return url
    parts = urlsplit(str(url or ""))
    query_pairs = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "v"]
    query_pairs.append(("v", version))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query_pairs), parts.fragment))


def _render_html_asset(*, template_path: Path, replacements: dict[str, str]) -> str:
    """Apply placeholder substitutions to one external HTML asset."""
    rendered = _read_text_asset(template_path)
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def _catalog_html(
    config: CatalogServiceConfig,
    *,
    css_path: str,
    component_css_path: str | None,
    api_js_path: str,
    ui_js_path: str,
    logo_path: str,
    icon_path: str,
    show_provider_ui_link: bool,
    client_errors_endpoint: str,
) -> str:
    """Render catalog UI HTML with same-origin asset references.

    Parameters
    ----------
    config:
        Effective catalog settings used for labels and routes.
    css_path:
        Base stylesheet path for the current standalone or embedded host.
    component_css_path:
        Optional catalog-specific stylesheet added when the host supplies the base stylesheet.
    api_js_path:
        Same-origin catalog API helper JavaScript path.
    ui_js_path:
        Same-origin catalog behavior JavaScript path.
    logo_path:
        Logo asset path for the current host mode.
    icon_path:
        Browser and page icon asset path for the current host mode.
    show_provider_ui_link:
        Whether navigation back to the provider UI is available.
    client_errors_endpoint:
        Endpoint receiving browser runtime error reports.

    Returns
    -------
    str
        Rendered catalog HTML without inline executable code or styles.
    """
    provider_link_attrs = (
        "" if show_provider_ui_link else 'hidden aria-hidden="true" tabindex="-1"'
    )
    component_css_link = ""
    if component_css_path:
        component_css_link = STYLESHEET_LINK_TEMPLATE.format(
            stylesheet_path=html.escape(component_css_path, quote=True),
        )
    return _render_html_asset(
        template_path=CATALOG_HTML_PATH,
        replacements={
            PLACEHOLDER_TITLE: html.escape(config.menu_label),
            PLACEHOLDER_ROUTE_PATH: html.escape(config.route_path),
            PLACEHOLDER_HELP_PATH: html.escape(config.help_path),
            PLACEHOLDER_CSS_PATH: html.escape(css_path),
            PLACEHOLDER_COMPONENT_CSS_LINK: component_css_link,
            PLACEHOLDER_API_JS_PATH: html.escape(api_js_path),
            PLACEHOLDER_JS_PATH: html.escape(ui_js_path),
            PLACEHOLDER_LOGO_PATH: html.escape(logo_path),
            PLACEHOLDER_ICON_PATH: html.escape(icon_path),
            PLACEHOLDER_UI_REFRESH_SECONDS: html.escape(str(config.ui_refresh_seconds)),
            PLACEHOLDER_CONFIG_EDITOR_ENTRY_POINT: CONFIG_EDITOR_ENTRY_POINT,
            PLACEHOLDER_PROVIDER_UI_LINK_ATTRS: provider_link_attrs,
            PLACEHOLDER_CLIENT_ERRORS_ENDPOINT: html.escape(client_errors_endpoint),
        },
    )


def _catalog_javascript(
    config: CatalogServiceConfig,
    *,
    client_errors_endpoint: str,
) -> str:
    """Render the external catalog behavior asset with runtime route settings.

    Parameters
    ----------
    config:
        Effective catalog configuration supplying route and refresh values.
    client_errors_endpoint:
        Deployment-specific endpoint used for browser error reporting.

    Returns
    -------
    str
        JavaScript with JSON-encoded runtime values and no inline HTML script.
    """
    return _render_html_asset(
        template_path=CATALOG_UI_JS_PATH,
        replacements={
            PLACEHOLDER_ROUTE_PATH: json.dumps(config.route_path),
            PLACEHOLDER_UI_REFRESH_SECONDS: json.dumps(config.ui_refresh_seconds),
            PLACEHOLDER_CONFIG_EDITOR_ENTRY_POINT: json.dumps(CONFIG_EDITOR_ENTRY_POINT),
            PLACEHOLDER_CLIENT_ERRORS_ENDPOINT: json.dumps(client_errors_endpoint),
        },
    )


def _help_html(config: CatalogServiceConfig, *, css_path: str) -> str:
    """Render catalog help HTML from external asset markup."""
    return _render_html_asset(
        template_path=CATALOG_HELP_HTML_PATH,
        replacements={
            PLACEHOLDER_TITLE: html.escape(config.menu_label),
            PLACEHOLDER_ROUTE_PATH: html.escape(config.route_path),
            PLACEHOLDER_CSS_PATH: html.escape(css_path),
        },
    )


def _local_catalog_css_route_path(route_path: str) -> str:
    normalized = str(route_path or "").rstrip("/")
    if not normalized:
        normalized = "/catalog"
    return f"{normalized}/assets/catalog_ui.css"


def _local_catalog_logo_route_path(route_path: str) -> str:
    normalized = str(route_path or "").rstrip("/")
    if not normalized:
        normalized = "/catalog"
    return f"{normalized}/assets/opamp_logo.png"


def _local_catalog_api_js_route_path(route_path: str) -> str:
    normalized = str(route_path or "").rstrip("/")
    if not normalized:
        normalized = "/catalog"
    return f"{normalized}/assets/catalog_ui_api.js"


def _local_catalog_js_route_path(route_path: str) -> str:
    """Return the same-origin route for the external catalog behavior asset.

    Parameters
    ----------
    route_path:
        Configured root route for the catalog UI.

    Returns
    -------
    str
        Route beneath the catalog asset namespace.
    """
    normalized = str(route_path or "").rstrip("/")
    if not normalized:
        normalized = "/catalog"
    return f"{normalized}/assets/catalog_ui.js"


def _local_catalog_icon_route_path(route_path: str) -> str:
    normalized = str(route_path or "").rstrip("/")
    if not normalized:
        normalized = "/catalog"
    return f"{normalized}/assets/config_editor_icon.png"


def _css_path_for_mode(*, config: CatalogServiceConfig, standalone_mode: bool) -> str:
    if standalone_mode:
        return _append_cache_bust_query(
            _local_catalog_css_route_path(config.route_path),
            source_path=CATALOG_UI_CSS_PATH,
        )
    return config.ui_base_css_path


def _logo_path_for_mode(*, config: CatalogServiceConfig, standalone_mode: bool) -> str:
    if standalone_mode:
        return _append_cache_bust_query(
            _local_catalog_logo_route_path(config.route_path),
            source_path=CATALOG_UI_LOGO_PATH,
        )
    return EMBEDDED_LOGO_PATH


def _icon_path_for_mode(*, config: CatalogServiceConfig, standalone_mode: bool) -> str:
    if standalone_mode:
        return _append_cache_bust_query(
            _local_catalog_icon_route_path(config.route_path),
            source_path=CATALOG_UI_ICON_PATH,
        )
    return EMBEDDED_ICON_PATH


def _client_errors_endpoint_for_mode(*, config: CatalogServiceConfig, standalone_mode: bool) -> str:
    if standalone_mode:
        normalized = str(config.route_path or "").rstrip("/")
        if not normalized:
            normalized = "/catalog"
        return f"{normalized}/api/client-errors"
    return "/api/client-errors"


def register_catalog_routes(
    *,
    app: Quart,
    config: CatalogServiceConfig,
    service: CatalogFileIndexService,
) -> None:
    """Register provider catalog UI/help/API routes for the configured path."""

    if config.enabled is not True:
        LOGGER.info("catalog routes not registered because catalog feature is disabled")
        return
    LOGGER.info(
        "registering catalog routes route_path=%s help_path=%s source_count=%s",
        config.route_path,
        config.help_path,
        len(config.sources),
    )
    standalone_mode = str(app.config.get(APP_CONFIG_KEY_MODE) or "").strip().lower() == APP_MODE_STANDALONE
    css_path = _css_path_for_mode(config=config, standalone_mode=standalone_mode)
    local_css_route_path = _local_catalog_css_route_path(config.route_path)
    component_css_path = None
    if not standalone_mode:
        component_css_path = _append_cache_bust_query(
            local_css_route_path,
            source_path=CATALOG_UI_CSS_PATH,
        )
    api_js_path = _append_cache_bust_query(
        _local_catalog_api_js_route_path(config.route_path),
        source_path=CATALOG_UI_API_JS_PATH,
    )
    ui_js_path = _append_cache_bust_query(
        _local_catalog_js_route_path(config.route_path),
        source_path=CATALOG_UI_JS_PATH,
    )
    logo_path = _logo_path_for_mode(config=config, standalone_mode=standalone_mode)
    icon_path = _icon_path_for_mode(config=config, standalone_mode=standalone_mode)
    client_errors_endpoint = _client_errors_endpoint_for_mode(
        config=config,
        standalone_mode=standalone_mode,
    )

    @app.get(config.route_path)
    async def catalog_ui() -> Response:
        return Response(
            _catalog_html(
                config,
                css_path=css_path,
                component_css_path=component_css_path,
                api_js_path=api_js_path,
                ui_js_path=ui_js_path,
                logo_path=logo_path,
                icon_path=icon_path,
                show_provider_ui_link=not standalone_mode,
                client_errors_endpoint=client_errors_endpoint,
            ),
            content_type="text/html; charset=utf-8",
        )

    @app.get(config.help_path)
    async def catalog_help() -> Response:
        return Response(_help_html(config, css_path=css_path), content_type="text/html; charset=utf-8")

    local_api_js_route_path = _local_catalog_api_js_route_path(config.route_path)

    @app.get(local_api_js_route_path)
    async def catalog_ui_api_js() -> Response:
        return Response(_read_text_asset(CATALOG_UI_API_JS_PATH), content_type="text/javascript; charset=utf-8")

    local_js_route_path = _local_catalog_js_route_path(config.route_path)

    @app.get(local_js_route_path)
    async def catalog_ui_js() -> Response:
        """Serve external catalog behavior with effective runtime values."""
        return Response(
            _catalog_javascript(config, client_errors_endpoint=client_errors_endpoint),
            content_type="text/javascript; charset=utf-8",
        )

    @app.get(local_css_route_path)
    async def catalog_ui_css() -> Response:
        """Serve catalog-specific styles in standalone and embedded modes."""
        return Response(
            _read_text_asset(CATALOG_UI_CSS_PATH),
            content_type="text/css; charset=utf-8",
        )

    if standalone_mode:
        local_logo_route_path = _local_catalog_logo_route_path(config.route_path)
        local_icon_route_path = _local_catalog_icon_route_path(config.route_path)

        @app.get(local_logo_route_path)
        async def catalog_ui_logo() -> Response:
            return Response(CATALOG_UI_LOGO_PATH.read_bytes(), content_type="image/png")

        @app.get(local_icon_route_path)
        async def catalog_ui_icon() -> Response:
            return Response(CATALOG_UI_ICON_PATH.read_bytes(), content_type="image/png")

        @app.post(f"{config.route_path}/api/client-errors")
        async def catalog_client_errors() -> Response:
            """Record one client-side catalog UI error in standalone mode."""
            body = await request.get_json(silent=True) or {}
            message = str(body.get(KEY_MESSAGE) or VALUE_UNKNOWN_UI_ERROR).strip()
            kind = str(body.get(KEY_KIND) or VALUE_RUNTIME_ERROR).strip()
            source = str(body.get(KEY_SOURCE) or VALUE_BROWSER).strip()
            path = str(body.get(KEY_PATH) or request.headers.get(HEADER_REFERER) or "").strip()
            stack = str(body.get(KEY_STACK) or "").strip()
            line = body.get(KEY_LINE)
            column = body.get(KEY_COLUMN)
            user_agent = request.headers.get(HEADER_USER_AGENT, "")

            log_message = (
                f"CATALOG UI ERROR | kind={kind} | source={source} | path={path or '-'} | "
                f"line={line if line is not None else '-'} | column={column if column is not None else '-'} | "
                f"message={message}"
            )
            if user_agent:
                log_message += f" | user_agent={user_agent}"
            if stack:
                log_message += f"\n{stack}"
            app.logger.error(log_message)
            return jsonify({RESPONSE_KEY_OK: True}), HTTPStatus.OK

    @app.get(f"{config.route_path}/api/files")
    async def catalog_files() -> Response:
        return jsonify(service.scan()), HTTPStatus.OK

    @app.get(f"{config.route_path}/api/file-content")
    async def catalog_file_content() -> Response:
        file_path = str(request.args.get(REQUEST_ARG_PATH) or "").strip()
        if not file_path:
            LOGGER.warning(
                "catalog file-content request rejected because path argument is missing route_path=%s remote_addr=%s",
                config.route_path,
                request.remote_addr,
            )
            return jsonify({RESPONSE_KEY_ERROR: ERR_PATH_REQUIRED}), HTTPStatus.BAD_REQUEST
        try:
            payload = service.read_file_text(file_path)
        except FileNotFoundError:
            LOGGER.warning(
                "catalog file-content request failed because file was not found path=%s remote_addr=%s",
                file_path,
                request.remote_addr,
            )
            return jsonify({RESPONSE_KEY_ERROR: ERR_FILE_NOT_FOUND.format(file_path=file_path)}), HTTPStatus.NOT_FOUND
        except PermissionError:
            LOGGER.warning(
                "catalog file-content request rejected because file is outside configured sources path=%s remote_addr=%s",
                file_path,
                request.remote_addr,
            )
            return jsonify({RESPONSE_KEY_ERROR: ERR_FILE_NOT_ALLOWED.format(file_path=file_path)}), HTTPStatus.FORBIDDEN
        except OSError as exc:
            LOGGER.exception(
                "catalog file-content request failed due to filesystem error path=%s remote_addr=%s",
                file_path,
                request.remote_addr,
                exc_info=exc,
            )
            return jsonify({RESPONSE_KEY_ERROR: str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR
        return jsonify(payload), HTTPStatus.OK
