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

"""Run the standalone config-service application and register its HTTP routes."""

# Repository checkout imports intentionally follow the shared-package path bootstrap below.
# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from quart import Quart, Response, jsonify, redirect, request, send_from_directory

ROOT_PATH = Path(__file__).resolve().parents[3]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from shared.observability import attach_observability
from shared.opamp_config import ComponentEntryPoint
from shared.opamp_config import (
    register_component_entry_points as shared_register_component_entry_points,
)

from config_service.agent_validation.service import ExternalAgentValidationService
from config_service.auth_integration import evaluate_ui_http_auth
from config_service.routes.api import create_api_blueprint
from config_service.runtime_config import (
    APP_EXTENSION_CONFIG_PATH,
    ENV_CONFIG_TOOL_CONFIG_PATH,
    get_effective_config_path,
    resolve_component_entry_points,
    resolve_log_level_name,
    resolve_observability_config,
    resolve_read_only,
    resolve_ui_base_css_path,
    resolve_ui_collapsed_sections,
    resolve_ui_css_overrides,
    resolve_ui_show_save_as,
    resolve_web_port,
)
from config_service.services.catalog_service import CatalogService
from config_service.services.fluentbit_yaml_config_service import FluentBitYamlConfigService
from config_service.services.fluentd_config_service import FluentdConfigService
from config_service.services.include_document_service import IncludeDocumentService
from config_service.services.issue_code_service import IssueCodeService
from config_service.services.parser_definition_service import ParserDefinitionService
from config_service.services.rule_engine_service import RuleEngineService
from config_service.services.rules_registry_service import RulesRegistryService
from config_service.services.schema_service import SchemaService
from config_service.services.service_definition_service import ServiceDefinitionService
from config_service.services.ui_document_service import UiDocumentService
from config_service.services.validation_service import ValidationService
from config_service.services.yaml_render_service import YamlRenderService

APP_CONFIG_KEY_MODE = "CONFIG_SERVICE_MODE"
APP_CONFIG_KEY_READ_ONLY = "CONFIG_SERVICE_READ_ONLY"
APP_MODE_STANDALONE = "standalone"

EXT_CATALOG_SERVICE = "catalog_service"
EXT_RULES_REGISTRY_SERVICE = "rules_registry_service"
EXT_RULE_ENGINE_SERVICE = "rule_engine_service"
EXT_SERVICE_DEFINITION_SERVICE = "service_definition_service"
EXT_PARSER_DEFINITION_SERVICE = "parser_definition_service"
EXT_ISSUE_CODE_SERVICE = "issue_code_service"
EXT_SCHEMA_SERVICE = "schema_service"
EXT_VALIDATION_SERVICE = "validation_service"
EXT_YAML_RENDER_SERVICE = "yaml_render_service"
EXT_UI_DOCUMENT_SERVICE = "ui_document_service"
EXT_FLUENTBIT_YAML_CONFIG_SERVICE = "fluentbit_yaml_config_service"
EXT_FLUENTD_CONFIG_SERVICE = "fluentd_config_service"
EXT_INCLUDE_DOCUMENT_SERVICE = "include_document_service"
EXT_EXTERNAL_AGENT_VALIDATION_SERVICE = "external_agent_validation_service"

HEADER_AUTHORIZATION = "Authorization"
HEADER_WWW_AUTHENTICATE = "WWW-Authenticate"
HEADER_CACHE_CONTROL = "Cache-Control"
HEADER_PRAGMA = "Pragma"
HEADER_EXPIRES = "Expires"

ENV_APP_ENABLE_DEV_FEATURES = "APP_ENABLE_DEV_FEATURES"
CONFIG_SERVICE_DOCS_URL = "https://github.com/mp3monster/fluent-opamp/tree/main/config-service/docs"
CONFIG_SERVICE_UI_CSS_OVERRIDE_PATH_ENV = "CONFIG_SERVICE_UI_CSS_OVERRIDE_PATH"
CONFIG_SERVICE_UI_CSS_OVERRIDES_ENV = "CONFIG_SERVICE_UI_CSS_OVERRIDES"
CONFIG_SERVICE_UI_CSS_OVERRIDES_KEY = "CONFIG_SERVICE_UI_CSS_OVERRIDES"
_ENV_TRUE_VALUES = {"1", "true", "yes", "on"}
LANDING_PAGE_REDIRECT_URL = (
    "https://htmlpreview.github.io/?https://raw.githubusercontent.com/"
    "mp3monster/fluent-opamp/main/github-landingpage/index.html"
)
PLACEHOLDER_PROVIDER_UI_LINK_ATTRS = "__CONFIG_SERVICE_PROVIDER_UI_LINK_ATTRS__"


def _config_service_root() -> Path:
    """Resolve packaged assets before considering a legacy repository-level tree."""
    module_dir = Path(__file__).resolve().parent
    source_root = module_dir.parents[1]
    for candidate in (module_dir, source_root, Path(sys.prefix) / "config_service"):
        if (candidate / "config").is_dir() and (candidate / "json-definitions").is_dir():
            return candidate
    return source_root


def _resolve_css_overrides(app: Quart) -> list[str]:
    configured_runtime = resolve_ui_css_overrides()
    if configured_runtime:
        return configured_runtime

    configured = app.config.get(CONFIG_SERVICE_UI_CSS_OVERRIDES_KEY)
    if isinstance(configured, str):
        return [value.strip() for value in configured.split(",") if value.strip()]
    if isinstance(configured, (list, tuple)):
        return [str(value).strip() for value in configured if str(value).strip()]

    plural_env = os.environ.get(CONFIG_SERVICE_UI_CSS_OVERRIDES_ENV, "")
    if plural_env.strip():
        return [value.strip() for value in plural_env.split(",") if value.strip()]

    single_env = os.environ.get(CONFIG_SERVICE_UI_CSS_OVERRIDE_PATH_ENV, "").strip()
    if single_env:
        return [single_env]
    return []


def _app_enable_dev_features_enabled() -> bool:
    raw_value = os.environ.get(ENV_APP_ENABLE_DEV_FEATURES, "")
    normalized = str(raw_value or "").strip().lower()
    return normalized in _ENV_TRUE_VALUES


def _apply_no_cache_headers(response: Response) -> Response:
    response.headers[HEADER_CACHE_CONTROL] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers[HEADER_PRAGMA] = "no-cache"
    response.headers[HEADER_EXPIRES] = "0"
    return response


def _asset_suffix() -> str:
    if not _app_enable_dev_features_enabled():
        return ""
    return "?v=" + str(int(Path(__file__).stat().st_mtime_ns))


def _append_suffix(url: str, suffix: str) -> str:
    if not suffix:
        return url
    joiner = "&" if "?" in url else "?"
    return url + joiner + suffix.lstrip("?")


def _standalone_mode(app: Quart) -> bool:
    return str(app.config.get(APP_CONFIG_KEY_MODE) or "").strip().lower() == APP_MODE_STANDALONE


def _provider_ui_link_attrs(app: Quart) -> str:
    if _standalone_mode(app):
        return 'style="display:none" aria-hidden="true" tabindex="-1"'
    return ""


def _configure_logging() -> None:
    level_name = resolve_log_level_name()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )


def register_component_entry_points(app: Quart) -> None:
    """Register config-service Quart components declared in runtime config."""
    configured = resolve_component_entry_points()
    entries = [ComponentEntryPoint(entry_point=item) for item in configured]
    shared_register_component_entry_points(app, entries=entries)


def register_api_component(app: Quart) -> None:
    app.register_blueprint(create_api_blueprint(), url_prefix="/config-service/api/v1")


def register_ui_component(app: Quart) -> None:
    html_dir = Path(__file__).resolve().with_name("html")

    @app.get("/config-service/ui")
    async def config_service_ui() -> Response:
        css_overrides = _resolve_css_overrides(app)
        base_css_path = resolve_ui_base_css_path()
        asset_suffix = _asset_suffix()
        html_template = (html_dir / "config_ui.html").read_text(encoding="utf-8")
        rendered = html_template.replace(
            "__CONFIG_SERVICE_UI_CSS_OVERRIDES_VALUE__",
            json.dumps(css_overrides),
        )
        rendered = rendered.replace(
            "__CONFIG_SERVICE_UI_COLLAPSED_SECTIONS_VALUE__",
            json.dumps(resolve_ui_collapsed_sections()),
        )
        rendered = rendered.replace(
            "__CONFIG_SERVICE_UI_SHOW_SAVE_AS_VALUE__",
            "true" if resolve_ui_show_save_as() else "false",
        )
        rendered = rendered.replace(
            "__CONFIG_SERVICE_UI_BASE_CSS_PATH__",
            _append_suffix(base_css_path, asset_suffix),
        )
        rendered = rendered.replace(
            "__CONFIG_SERVICE_UI_ASSET_SUFFIX__",
            asset_suffix,
        )
        rendered = rendered.replace(
            PLACEHOLDER_PROVIDER_UI_LINK_ATTRS,
            _provider_ui_link_attrs(app),
        )
        response = Response(rendered, mimetype="text/html")
        if _app_enable_dev_features_enabled():
            return _apply_no_cache_headers(response)
        return response

    @app.get("/config-service/ui/docs/help")
    async def config_service_ui_help() -> Response:
        base_css_path = resolve_ui_base_css_path()
        asset_suffix = _asset_suffix()
        html_template = (html_dir / "config_ui_help.html").read_text(encoding="utf-8")
        rendered = html_template.replace(
            "__CONFIG_SERVICE_UI_BASE_CSS_PATH__",
            _append_suffix(base_css_path, asset_suffix),
        )
        rendered = rendered.replace(
            "__CONFIG_SERVICE_UI_ASSET_SUFFIX__",
            asset_suffix,
        )
        response = Response(rendered, mimetype="text/html")
        if _app_enable_dev_features_enabled():
            return _apply_no_cache_headers(response)
        return response

    @app.get("/config-service/ui/docs/metadata-env")
    async def config_service_ui_metadata_env_help() -> Response:
        base_css_path = resolve_ui_base_css_path()
        asset_suffix = _asset_suffix()
        html_template = (html_dir / "metadata_env_help.html").read_text(encoding="utf-8")
        rendered = html_template.replace(
            "__CONFIG_SERVICE_UI_BASE_CSS_PATH__",
            _append_suffix(base_css_path, asset_suffix),
        )
        rendered = rendered.replace(
            "__CONFIG_SERVICE_UI_ASSET_SUFFIX__",
            asset_suffix,
        )
        response = Response(rendered, mimetype="text/html")
        if _app_enable_dev_features_enabled():
            return _apply_no_cache_headers(response)
        return response

    @app.get("/config-service/ui/assets/<path:filename>")
    async def config_service_ui_assets(filename: str) -> Response:
        response = await send_from_directory(html_dir, filename)
        if _app_enable_dev_features_enabled():
            return _apply_no_cache_headers(response)
        return response


def create_app(*, mode: str = "standalone") -> Quart:
    _configure_logging()
    app = Quart(__name__)
    effective_config_path = get_effective_config_path().resolve()
    app.config[APP_CONFIG_KEY_MODE] = mode
    app.config[APP_CONFIG_KEY_READ_ONLY] = resolve_read_only(str(effective_config_path))
    app.extensions[APP_EXTENSION_CONFIG_PATH] = str(effective_config_path)
    app.logger.setLevel(getattr(logging, resolve_log_level_name(str(effective_config_path)), logging.INFO))

    repo_root = _config_service_root()
    provider_src = repo_root.parent / "provider" / "src"
    if provider_src.exists() and str(provider_src) not in sys.path:
        sys.path.insert(0, str(provider_src))

    catalog_registry_path = repo_root / "config" / "catalog-registry.json"
    service_registry_path = repo_root / "config" / "service-registry.json"
    parser_registry_path = repo_root / "config" / "parser-registry.json"
    issue_codes_path = repo_root / "config" / "issue-code-messages.json"
    rules_registry_path = repo_root / "config" / "validation-rules-registry.json"

    catalog_service = CatalogService(catalog_registry_path)
    catalog_service.load_all_catalogs()
    service_definition_service = ServiceDefinitionService(service_registry_path)
    service_definition_service.load_all()
    parser_definition_service = ParserDefinitionService(parser_registry_path)
    parser_definition_service.load_all()
    issue_code_service = IssueCodeService(issue_codes_path)
    issue_code_service.load()

    rules_registry_service = RulesRegistryService(rules_registry_path)
    rule_engine_service = RuleEngineService(rules_registry_service)
    validation_service = ValidationService(rule_engine_service)

    fluentbit_yaml_config_service = FluentBitYamlConfigService()
    fluentd_config_service = FluentdConfigService()
    include_document_service = IncludeDocumentService(
        fluentbit_yaml_config_service=fluentbit_yaml_config_service,
        fluentd_config_service=fluentd_config_service,
    )
    external_agent_validation_service = ExternalAgentValidationService.from_runtime_config(
        str(effective_config_path)
    )

    app.extensions[EXT_CATALOG_SERVICE] = catalog_service
    app.extensions[EXT_RULES_REGISTRY_SERVICE] = rules_registry_service
    app.extensions[EXT_RULE_ENGINE_SERVICE] = rule_engine_service
    app.extensions[EXT_SERVICE_DEFINITION_SERVICE] = service_definition_service
    app.extensions[EXT_PARSER_DEFINITION_SERVICE] = parser_definition_service
    app.extensions[EXT_ISSUE_CODE_SERVICE] = issue_code_service
    app.extensions[EXT_SCHEMA_SERVICE] = SchemaService()
    app.extensions[EXT_VALIDATION_SERVICE] = validation_service
    app.extensions[EXT_YAML_RENDER_SERVICE] = YamlRenderService()
    app.extensions[EXT_UI_DOCUMENT_SERVICE] = UiDocumentService()
    app.extensions[EXT_FLUENTBIT_YAML_CONFIG_SERVICE] = fluentbit_yaml_config_service
    app.extensions[EXT_FLUENTD_CONFIG_SERVICE] = fluentd_config_service
    app.extensions[EXT_INCLUDE_DOCUMENT_SERVICE] = include_document_service
    app.extensions[EXT_EXTERNAL_AGENT_VALIDATION_SERVICE] = external_agent_validation_service

    if mode == "standalone":
        attach_observability(
            app,
            service_name="config-service",
            config=resolve_observability_config(str(effective_config_path)),
            log_level=getattr(
                logging,
                resolve_log_level_name(str(effective_config_path)),
                logging.INFO,
            ),
        )

    if mode == "standalone":
        @app.before_request
        async def enforce_ui_bearer_auth() -> tuple[object, int] | None:
            result = evaluate_ui_http_auth(
                path=request.path,
                method=request.method,
                authorization_header=request.headers.get(HEADER_AUTHORIZATION),
                remote_addr=request.remote_addr,
            )
            if result.allowed:
                return None
            response = jsonify({"error": result.error})
            if result.www_authenticate:
                response.headers[HEADER_WWW_AUTHENTICATE] = result.www_authenticate
            return response, result.status_code

    @app.errorhandler(404)
    async def redirect_unknown_config_service_route(_: object) -> Response:
        """Redirect unknown config-service routes to the shared landing page."""
        app.logger.info(
            "config-service 404 redirect path=%s remote_addr=%s target=%s",
            request.path,
            request.remote_addr,
            LANDING_PAGE_REDIRECT_URL,
        )
        return redirect(LANDING_PAGE_REDIRECT_URL)

    register_component_entry_points(app)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Config Service standalone server",
        epilog=f"Documentation: {CONFIG_SERVICE_DOCS_URL}",
    )
    parser.add_argument("--config-path", type=str, help="Path to config-service JSON configuration file")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",  # noqa: S104 - standalone service intentionally accepts remote UI clients
        help="Bind address",
    )
    parser.add_argument("--port", type=int, help="Override listen port")
    args = parser.parse_args()

    if args.config_path:
        os.environ[ENV_CONFIG_TOOL_CONFIG_PATH] = args.config_path

    app = create_app(mode="standalone")
    app.run(host=args.host, port=args.port or resolve_web_port(), debug=True)


if __name__ == "__main__":
    main()
