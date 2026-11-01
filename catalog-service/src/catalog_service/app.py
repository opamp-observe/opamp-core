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

from __future__ import annotations

import argparse
import logging
import os
import sys
from http import HTTPStatus
from pathlib import Path

from quart import Quart, Response, jsonify, redirect, request

ROOT_PATH = Path(__file__).resolve().parents[3]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from shared.observability import attach_observability
from shared.opamp_config import ComponentEntryPoint, register_component_entry_points

from catalog_service.auth_integration import evaluate_ui_http_auth
from catalog_service.config import load_catalog_service_config
from catalog_service.routes import register_catalog_routes
from catalog_service.runtime_config import (
    ENV_CATALOG_SERVICE_CONFIG_PATH,
    get_effective_config_path,
    resolve_component_entries,
    resolve_observability_config,
    resolve_web_port,
)
from catalog_service.service import CatalogFileIndexService

APP_CONFIG_KEY_MODE = "CATALOG_SERVICE_MODE"
APP_EXTENSION_MENU_ITEMS = "catalog_service:ui_menu_items"
APP_EXTENSION_REGISTERED_ENTRY_POINTS = "catalog_service:registered_entry_points"
APP_EXTENSION_CONFIG_PATH = "catalog_service:config_path"
APP_EXTENSION_INDEX_SERVICE = "catalog_service:index_service"
HEADER_AUTHORIZATION = "Authorization"
HEADER_WWW_AUTHENTICATE = "WWW-Authenticate"
MENU_ITEM_KEY_ENTRY_POINT = "entry_point"
MENU_ITEM_KEY_LABEL = "label"
MENU_ITEM_KEY_URL = "url"
MENU_ITEM_KEY_TARGET = "target"
MENU_ITEM_TARGET_SELF = "_self"
RESPONSE_KEY_ITEMS = "items"
RESPONSE_KEY_COMPONENT_ENTRY_POINTS_REGISTERED = "component_entry_points_registered"
RESPONSE_KEY_ERROR = "error"
LANDING_PAGE_REDIRECT_URL = (
    "https://htmlpreview.github.io/?https://raw.githubusercontent.com/"
    "mp3monster/fluent-opamp/main/github-landingpage/index.html"
)


def _component_root() -> Path:
    module_dir = Path(__file__).resolve().parent
    source_root = module_dir.parents[1]
    if (source_root / "config").is_dir():
        return source_root
    return module_dir


def _repo_root() -> Path:
    return _component_root().parent


def _ensure_optional_component_paths() -> None:
    """Ensure sibling component source roots are importable for entrypoint loading."""
    root = _repo_root()
    candidates = [
        root / "config-service" / "src",
        root / "provider" / "src",
    ]
    for candidate in candidates:
        if not candidate.exists():
            continue
        resolved = str(candidate.resolve())
        if resolved not in sys.path:
            sys.path.insert(0, resolved)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )


def _menu_items_from_entries(entries: list[ComponentEntryPoint]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for entry in entries:
        label = str(entry.label or "").strip()
        url = str(entry.url or "").strip()
        if not label or not url:
            continue
        items.append(
            {
                MENU_ITEM_KEY_ENTRY_POINT: str(entry.entry_point or "").strip(),
                MENU_ITEM_KEY_LABEL: label,
                MENU_ITEM_KEY_URL: url,
                MENU_ITEM_KEY_TARGET: MENU_ITEM_TARGET_SELF,
            }
        )
    return items


def _catalog_repo_root(*, config_path: Path, sources: tuple[object, ...]) -> Path:
    """Resolve the most appropriate base folder for relative catalog source paths."""
    component_config_dir = (_component_root() / "config").resolve()
    repo_root = _repo_root().resolve()
    config_parent = config_path.parent.resolve()

    if config_parent == component_config_dir:
        return repo_root

    source_folders = [str(getattr(source, "folder", "") or "").strip() for source in sources]
    source_folders = [folder for folder in source_folders if folder]
    for candidate in (config_parent, repo_root):
        if any((candidate / folder).exists() for folder in source_folders):
            return candidate
    return config_parent


def register_catalog_component(app: Quart) -> None:
    """Register catalog UI/help/API routes into the provided Quart app."""
    config_path = Path(str(app.extensions.get(APP_EXTENSION_CONFIG_PATH) or get_effective_config_path())).resolve()
    app.logger.info("catalog component registration requested config_path=%s", config_path)
    config = load_catalog_service_config(config_path=config_path)
    if config.enabled is not True:
        app.logger.info("catalog component disabled; skipping route registration")
        return

    repo_root = _catalog_repo_root(config_path=config_path, sources=config.sources)
    service = CatalogFileIndexService(
        repo_root=repo_root,
        config=config,
    )
    app.extensions[APP_EXTENSION_INDEX_SERVICE] = service

    @app.before_serving
    async def start_catalog_background_refresh() -> None:
        """Start backend catalog refresh independent of UI polling state."""
        service.start_background_refresh(interval_seconds=float(config.ui_refresh_seconds))
        app.logger.info(
            "catalog background refresh enabled route_path=%s interval_seconds=%s",
            config.route_path,
            config.ui_refresh_seconds,
        )

    @app.after_serving
    async def stop_catalog_background_refresh() -> None:
        """Stop backend catalog refresh when the app shuts down."""
        service.stop_background_refresh()

    register_catalog_routes(app=app, config=config, service=service)
    app.logger.info(
        "catalog component registered mode=%s config_path=%s route_path=%s help_path=%s repo_root=%s source_count=%s",
        app.config.get(APP_CONFIG_KEY_MODE),
        config_path,
        config.route_path,
        config.help_path,
        repo_root,
        len(config.sources),
    )


def _register_component_entry_points(app: Quart, *, config_path: Path) -> tuple[list[str], list[ComponentEntryPoint]]:
    app.logger.info("resolving catalog component entry points config_path=%s", config_path)
    _ensure_optional_component_paths()
    entries = resolve_component_entries(str(config_path))
    try:
        registered = register_component_entry_points(app, entries=entries)
    except Exception as exc:
        app.logger.exception(
            "catalog component entry-point registration failed config_path=%s",
            config_path,
            exc_info=exc,
        )
        raise
    app.logger.info(
        "catalog component entry points registered config_path=%s configured=%s registered=%s",
        config_path,
        [entry.entry_point for entry in entries],
        registered,
    )
    return registered, entries


def create_app(*, mode: str = "standalone", config_path: str | None = None) -> Quart:
    """Create a standalone catalog Quart app."""
    _configure_logging()
    app = Quart(__name__)
    effective_config_path = get_effective_config_path(config_path).resolve()
    app.config[APP_CONFIG_KEY_MODE] = mode
    app.extensions[APP_EXTENSION_CONFIG_PATH] = str(effective_config_path)
    app.logger.info(
        "creating catalog app mode=%s config_path=%s",
        mode,
        effective_config_path,
    )

    registered_entry_points, configured_entries = _register_component_entry_points(
        app,
        config_path=effective_config_path,
    )
    app.extensions[APP_EXTENSION_REGISTERED_ENTRY_POINTS] = registered_entry_points
    app.extensions[APP_EXTENSION_MENU_ITEMS] = _menu_items_from_entries(configured_entries)
    if mode == "standalone":
        attach_observability(
            app,
            service_name="catalog-service",
            config=resolve_observability_config(str(effective_config_path)),
            log_level=logging.INFO,
        )

    @app.get("/api/ui/features")
    async def ui_features() -> Response:
        items = list(app.extensions.get(APP_EXTENSION_MENU_ITEMS, []))
        registered = list(app.extensions.get(APP_EXTENSION_REGISTERED_ENTRY_POINTS, []))
        return jsonify(
            {
                RESPONSE_KEY_ITEMS: items,
                RESPONSE_KEY_COMPONENT_ENTRY_POINTS_REGISTERED: registered,
            }
        )

    if mode == "standalone":
        @app.before_request
        async def enforce_ui_bearer_auth() -> tuple[object, int] | None:
            """Apply provider-compatible UI bearer auth for standalone catalog routes."""
            result = evaluate_ui_http_auth(
                path=request.path,
                method=request.method,
                authorization_header=request.headers.get(HEADER_AUTHORIZATION),
                remote_addr=request.remote_addr,
            )
            if result.allowed:
                return None
            app.logger.warning(
                "catalog request rejected by auth path=%s method=%s remote_addr=%s status_code=%s error=%s",
                request.path,
                request.method,
                request.remote_addr,
                int(result.status_code or HTTPStatus.UNAUTHORIZED),
                result.error,
            )
            response = jsonify({RESPONSE_KEY_ERROR: result.error})
            if result.www_authenticate:
                response.headers[HEADER_WWW_AUTHENTICATE] = result.www_authenticate
            return response, int(result.status_code or HTTPStatus.UNAUTHORIZED)

    @app.before_serving
    async def log_catalog_startup() -> None:
        """Log catalog app startup for lifecycle observability."""
        app.logger.info(
            "catalog app starting mode=%s config_path=%s registered_entry_points=%s",
            app.config.get(APP_CONFIG_KEY_MODE),
            app.extensions.get(APP_EXTENSION_CONFIG_PATH),
            app.extensions.get(APP_EXTENSION_REGISTERED_ENTRY_POINTS, []),
        )

    @app.after_serving
    async def log_catalog_shutdown() -> None:
        """Log catalog app shutdown for lifecycle observability."""
        app.logger.info(
            "catalog app stopping mode=%s config_path=%s",
            app.config.get(APP_CONFIG_KEY_MODE),
            app.extensions.get(APP_EXTENSION_CONFIG_PATH),
        )

    @app.errorhandler(404)
    async def redirect_unknown_catalog_route(_: object) -> Response:
        """Redirect unknown catalog routes to the shared landing page."""
        app.logger.info(
            "catalog 404 redirect path=%s remote_addr=%s target=%s",
            request.path,
            request.remote_addr,
            LANDING_PAGE_REDIRECT_URL,
        )
        return redirect(LANDING_PAGE_REDIRECT_URL)

    return app


def main() -> None:
    """Run the standalone catalog UI server."""
    parser = argparse.ArgumentParser(description="OpAMP catalog standalone server")
    parser.add_argument("--config-path", type=str, help="Path to catalog JSON configuration file")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind address")
    parser.add_argument("--port", type=int, help="Override listen port")
    args = parser.parse_args()

    if args.config_path:
        os.environ[ENV_CATALOG_SERVICE_CONFIG_PATH] = args.config_path

    app = create_app(mode="standalone", config_path=args.config_path)
    port = args.port or resolve_web_port(args.config_path)
    app.logger.info(
        "catalog standalone server run requested host=%s port=%s config_path=%s",
        args.host,
        port,
        get_effective_config_path(args.config_path).resolve(),
    )
    app.run(host=args.host, port=port, debug=True)
