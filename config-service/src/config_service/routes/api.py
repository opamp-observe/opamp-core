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

import json
import logging
import os
import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from quart import Blueprint, current_app, jsonify, request
from shared.opamp_config import load_json_config

from config_service.agent_validation.exceptions import AgentNotSupportedError
from config_service.models.contracts import (
    ParseTextRequest,
    RenderTextRequest,
    RenderYamlRequest,
    SchemaOptions,
    UiLoadSourceFileRequest,
    UiPrepareFileRequest,
    ValidateRequest,
)
from config_service.runtime_config import get_effective_config_path, resolve_save_ignore_validation

APP_ENABLE_DEV_FEATURES_ENV = "APP_ENABLE_DEV_FEATURES"
LOGGER = logging.getLogger(__name__)

ENV_TRUE_VALUES = {"1", "true", "yes", "on"}
ROOT_PATH = "$"
ROOT_PATH_WITH_SEPARATOR = "$."
BODY_LOC_TOKEN = "body"

DEFAULT_CONFIG_TYPE_FLUENTBIT = "fluentbit"
CONFIG_TYPE_FLUENTD = "fluentd"
CONFIG_TYPE_FLUENT_BIT_ALIAS = "fluent-bit"

BLUEPRINT_NAME = "config_service_api"

EXT_CATALOG_SERVICE = "catalog_service"
EXT_SERVICE_DEFINITION_SERVICE = "service_definition_service"
EXT_PARSER_DEFINITION_SERVICE = "parser_definition_service"
EXT_ISSUE_CODE_SERVICE = "issue_code_service"
EXT_UI_DOCUMENT_SERVICE = "ui_document_service"
EXT_SCHEMA_SERVICE = "schema_service"
EXT_INCLUDE_DOCUMENT_SERVICE = "include_document_service"
EXT_VALIDATION_SERVICE = "validation_service"
EXT_EXTERNAL_AGENT_VALIDATION_SERVICE = "external_agent_validation_service"
EXT_YAML_RENDER_SERVICE = "yaml_render_service"
EXT_FLUENTD_CONFIG_SERVICE = "fluentd_config_service"
EXT_FLUENTBIT_YAML_CONFIG_SERVICE = "fluentbit_yaml_config_service"

CONFIG_KEY_MODE = "CONFIG_SERVICE_MODE"
CONFIG_KEY_READ_ONLY = "CONFIG_SERVICE_READ_ONLY"
CONFIG_MODE_STANDALONE = "standalone"

KEY_OK = "ok"
KEY_MODE = "mode"
KEY_ERROR = "error"
KEY_ERRORS = "errors"
KEY_MESSAGE = "message"
KEY_KIND = "kind"
KEY_SOURCE = "source"
KEY_PATH = "path"
KEY_STACK = "stack"
KEY_LINE = "line"
KEY_COLUMN = "column"
KEY_CONFIG_TYPE = "config_type"
KEY_VERSION = "version"
KEY_VERSIONS = "versions"
KEY_DEFAULT = "default"
KEY_SUPPORTED_CONFIG_TYPES = "supported_config_types"
KEY_HEADER_COMMENTS = "header_comments"
KEY_BODY = "body"
KEY_SOURCE_LINE_MAP = "source_line_map"
KEY_SOURCE_PATH = "source_path"
KEY_FILE_NAME = "file_name"
KEY_TEXT = "text"
KEY_SCHEMA = "schema"
KEY_CONFIG = "config"
KEY_ANNOTATIONS = "annotations"
KEY_INCLUDED_DOCUMENTS = "included_documents"
KEY_INCLUDED_FILES = "included_files"
KEY_RENDERED_OUTPUT = "rendered_output"
KEY_YAML = "yaml"
KEY_READ_ONLY = "read_only"
KEY_APP_ENABLE_DEV_FEATURES = "app_enable_dev_features"
KEY_ORDER = "order"
KEY_CODE = "code"
KEY_SEVERITY = "severity"
KEY_DETAIL_TYPE = "detail_type"
KEY_PYDANTIC_LOC = "loc"
KEY_PYDANTIC_MSG = "msg"
KEY_PYDANTIC_TYPE = "type"
KEY_SAVE_DECLINED = "save_declined"
KEY_SAVE_MESSAGE = "save_message"
KEY_SAVE_PATH = "save_path"
KEY_SAVED = "saved"

VALUE_ERROR = "error"
VALUE_SCHEMA = "schema"
VALUE_PARSER = "parser"
VALUE_BROWSER = "browser"
VALUE_RUNTIME_ERROR = "runtime_error"
VALUE_UNKNOWN_UI_ERROR = "Unknown UI error"
VALUE_PYDANTIC_VALIDATION_ERROR = "pydantic_validation_error"
VALUE_REQUEST_VALIDATION_ERROR = "Request validation error"
VALUE_VALIDATION_ERROR = "validation_error"
VALUE_EMPTY_INPUT_FILE = "empty_input_file"
VALUE_FLUENTD_PARSE_ERROR = "fluentd_parse_error"
VALUE_FLUENTBIT_YAML_PARSE_ERROR = "fluentbit_yaml_parse_error"
VALUE_SERVER_SAVE_NOT_ALLOWED = "server_save_not_allowed"
VALUE_SERVER_SAVE_FAILED = "server_save_failed"

HEADER_REFERER = "Referer"
HEADER_USER_AGENT = "User-Agent"
ENCODING_UTF8 = "utf-8"
COMMENT_PREFIX_HASH = "#"
COMMENT_PREFIX_SLASH = "//"


def _app_enable_dev_features_enabled() -> bool:
    """Return whether development-only features are enabled for this process."""
    raw_value = os.environ.get(APP_ENABLE_DEV_FEATURES_ENV, "")
    normalized = str(raw_value or "").strip().lower()
    return normalized in ENV_TRUE_VALUES


def _normalize_pydantic_issues(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Pydantic validation details into the API's stable error structure."""
    normalized: list[dict[str, Any]] = []
    for index, error in enumerate(errors, start=1):
        loc = error.get(KEY_PYDANTIC_LOC, ())
        if isinstance(loc, (list, tuple)):
            path = ROOT_PATH_WITH_SEPARATOR + ".".join(
                str(part) for part in loc if part != BODY_LOC_TOKEN
            )
        else:
            path = ROOT_PATH
        path = path if path != ROOT_PATH_WITH_SEPARATOR else ROOT_PATH
        normalized.append(
            {
                KEY_ORDER: index,
                KEY_CODE: VALUE_PYDANTIC_VALIDATION_ERROR,
                KEY_PATH: path,
                KEY_MESSAGE: str(error.get(KEY_PYDANTIC_MSG) or VALUE_REQUEST_VALIDATION_ERROR),
                KEY_SEVERITY: VALUE_ERROR,
                KEY_SOURCE: VALUE_SCHEMA,
                KEY_DETAIL_TYPE: str(error.get(KEY_PYDANTIC_TYPE) or VALUE_VALIDATION_ERROR),
            }
        )
    return normalized


async def _get_request_body() -> dict[str, Any]:
    """Read the current JSON request body, defaulting to an empty object."""
    return await request.get_json(silent=True) or {}


def _json_error_response(message: str, status: HTTPStatus) -> tuple[Any, HTTPStatus]:
    """Build a standard single-error JSON response."""
    return jsonify({KEY_OK: False, KEY_ERROR: message}), status


def _json_validation_errors_response(exc: ValidationError) -> tuple[Any, HTTPStatus]:
    """Build the standard validation error response from a Pydantic exception."""
    return (
        jsonify({KEY_OK: False, KEY_ERRORS: _normalize_pydantic_issues(exc.errors())}),
        HTTPStatus.BAD_REQUEST,
    )


def _request_config_type(default: str | None = None) -> str | None:
    """Return the normalized config type query parameter, or the supplied default."""
    raw_value = request.args.get(KEY_CONFIG_TYPE, default)
    if raw_value is None:
        return None
    return str(raw_value or default or "").strip().lower()


def _repo_root() -> Path:
    """Return the repository root used by component-relative catalog sources."""
    return Path(__file__).resolve().parents[4]


def _config_service_root() -> Path:
    """Return the config-service package root for bundled component config."""
    return Path(__file__).resolve().parents[3]


def _normalize_source_extensions(raw: Any) -> set[str]:
    """Normalize one catalog source extension list for path allow-listing."""
    if isinstance(raw, str):
        raw = [item.strip() for item in raw.split(",") if item.strip()]
    if not isinstance(raw, list):
        return set()
    normalized: set[str] = set()
    for item in raw:
        text = str(item or "").strip().lower()
        if not text:
            continue
        if not text.startswith("."):
            text = "." + text
        normalized.add(text)
    return normalized


def _catalog_sources_from_runtime_config() -> list[tuple[str, set[str]]]:
    """Return configured catalog source folders and extensions from runtime config."""
    try:
        payload = load_json_config(get_effective_config_path())
    except (OSError, ValueError, TypeError):
        return []
    opamp_raw = payload.get("opamp", {}) if isinstance(payload, dict) else {}
    catalog_raw = opamp_raw.get("config_catalog", {}) if isinstance(opamp_raw, dict) else {}
    sources_raw = catalog_raw.get("sources", []) if isinstance(catalog_raw, dict) else []
    if not isinstance(sources_raw, list):
        return []
    sources: list[tuple[str, set[str]]] = []
    for item in sources_raw:
        if not isinstance(item, dict):
            continue
        folder = str(item.get("folder") or "").strip()
        extensions = _normalize_source_extensions(item.get("extensions", []))
        if folder and extensions:
            sources.append((folder, extensions))
    return sources


def _catalog_base_path(config_path: Path, source_folders: list[str]) -> Path:
    """Resolve the base directory for catalog source folders."""
    component_config_dir = (_config_service_root() / "config").resolve()
    repo_root = _repo_root().resolve()
    config_parent = config_path.parent.resolve()
    if config_parent == component_config_dir:
        return repo_root
    for candidate in (config_parent, repo_root):
        if any((candidate / folder).exists() for folder in source_folders):
            return candidate
    return config_parent


def _allowed_catalog_save_target(raw_path: str | None) -> Path | None:
    """Resolve a requested save path only when it belongs to a configured catalog source."""
    target_text = str(raw_path or "").strip()
    if not target_text:
        return None
    try:
        target = Path(target_text).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if target.is_file() is not True:
        return None

    sources = _catalog_sources_from_runtime_config()
    if not sources:
        return None
    config_path = get_effective_config_path().resolve()
    base_path = _catalog_base_path(config_path, [folder for folder, _extensions in sources])
    for folder, extensions in sources:
        if target.suffix.lower() not in extensions:
            continue
        source_root = (base_path / folder).resolve()
        if source_root.exists() is not True or source_root.is_dir() is not True:
            continue
        try:
            target.relative_to(source_root)
        except ValueError:
            continue
        return target
    return None


def _validation_save_error(message: str, status: HTTPStatus) -> tuple[Any, HTTPStatus]:
    """Build a response for a declined validate-and-save request."""
    return (
        jsonify(
            {
                KEY_OK: False,
                KEY_SAVE_DECLINED: True,
                KEY_SAVE_MESSAGE: message,
                KEY_ERRORS: [
                    {
                        KEY_ORDER: 1,
                        KEY_CODE: VALUE_SERVER_SAVE_NOT_ALLOWED,
                        KEY_PATH: ROOT_PATH,
                        KEY_MESSAGE: message,
                        KEY_SEVERITY: VALUE_ERROR,
                        KEY_SOURCE: VALUE_SCHEMA,
                        KEY_DETAIL_TYPE: VALUE_SERVER_SAVE_NOT_ALLOWED,
                    }
                ],
            }
        ),
        status,
    )


def _render_validated_save_text(
    *,
    req: ValidateRequest,
    version: str,
    config_type: str,
    target_path: Path,
) -> str:
    """Render a validated config payload to the target file's native text format."""
    ui_document_service = current_app.extensions[EXT_UI_DOCUMENT_SERVICE]
    suffix = target_path.suffix.lower()
    if suffix == ".json":
        document = {
            KEY_VERSION: version,
            "configType": config_type,
            KEY_CONFIG: req.config,
            KEY_ANNOTATIONS: req.annotations,
        }
        if req.included_documents:
            document[KEY_INCLUDED_DOCUMENTS] = req.included_documents
        rendered = json.dumps(document, indent=2) + "\n"
        return ui_document_service.compose_render_output(
            main_rendered=rendered,
            include_loaded_files=False,
            included_files=[],
            header_comments=req.header_comments,
            include_config_header=req.include_config_header,
            config_type=config_type,
            version=version,
            comment_prefix=COMMENT_PREFIX_SLASH,
        )

    if _is_fluentd_config_type(config_type) or suffix == ".conf":
        fluentd_config_service = current_app.extensions[EXT_FLUENTD_CONFIG_SERVICE]
        rendered = fluentd_config_service.render(req.config)
        return ui_document_service.compose_render_output(
            main_rendered=rendered,
            include_loaded_files=False,
            included_files=[],
            header_comments=req.header_comments,
            include_config_header=req.include_config_header,
            config_type=CONFIG_TYPE_FLUENTD,
            version=version,
            comment_prefix=COMMENT_PREFIX_HASH,
        )

    yaml_render_service = current_app.extensions[EXT_YAML_RENDER_SERVICE]
    rendered = yaml_render_service.render(
        payload={KEY_CONFIG: req.config, KEY_ANNOTATIONS: req.annotations},
        include_comments=True,
    )
    return ui_document_service.compose_render_output(
        main_rendered=rendered,
        include_loaded_files=False,
        included_files=[],
        header_comments=req.header_comments,
        include_config_header=req.include_config_header,
        config_type=DEFAULT_CONFIG_TYPE_FLUENTBIT,
        version=version,
        comment_prefix=COMMENT_PREFIX_HASH,
    )


def _is_fluentbit_config_type(config_type: str | None) -> bool:
    """Return whether the supplied config type should use Fluent Bit handling."""
    normalized = str(config_type or DEFAULT_CONFIG_TYPE_FLUENTBIT).strip().lower()
    return normalized in {DEFAULT_CONFIG_TYPE_FLUENTBIT, CONFIG_TYPE_FLUENT_BIT_ALIAS}


def _is_fluentd_config_type(config_type: str | None) -> bool:
    """Return whether the supplied config type should use Fluentd handling."""
    return str(config_type or "").strip().lower() == CONFIG_TYPE_FLUENTD


def create_api_blueprint() -> Blueprint:
    """Create the Quart blueprint that serves the config-service HTTP API."""
    bp = Blueprint(BLUEPRINT_NAME, __name__)

    @bp.post("/client-errors")
    async def client_errors() -> Any:
        """Record a client-side UI error reported by browser JavaScript."""
        body = await _get_request_body()
        message = str(body.get(KEY_MESSAGE) or VALUE_UNKNOWN_UI_ERROR).strip()
        kind = str(body.get(KEY_KIND) or VALUE_RUNTIME_ERROR).strip()
        source = str(body.get(KEY_SOURCE) or VALUE_BROWSER).strip()
        path = str(body.get(KEY_PATH) or request.headers.get(HEADER_REFERER) or "").strip()
        stack = str(body.get(KEY_STACK) or "").strip()
        line = body.get(KEY_LINE)
        column = body.get(KEY_COLUMN)
        user_agent = request.headers.get(HEADER_USER_AGENT, "")

        log_message = (
            f"UI ERROR | kind={kind} | source={source} | path={path or '-'} | "
            f"line={line if line is not None else '-'} | column={column if column is not None else '-'} | "
            f"message={message}"
        )
        if user_agent:
            log_message += f" | user_agent={user_agent}"
        if stack:
            log_message += f"\n{stack}"

        current_app.logger.error(log_message)
        print(log_message, file=sys.stderr, flush=True)
        return jsonify({KEY_OK: True})

    @bp.get("/health")
    async def health() -> Any:
        """Return a small process-health payload for operational checks."""
        current_app.logger.debug("health endpoint requested")
        return jsonify(
            {
                KEY_OK: True,
                KEY_MODE: current_app.config.get(CONFIG_KEY_MODE, CONFIG_MODE_STANDALONE),
                KEY_APP_ENABLE_DEV_FEATURES: _app_enable_dev_features_enabled(),
                KEY_READ_ONLY: bool(current_app.config.get(CONFIG_KEY_READ_ONLY, False)),
            }
        )

    @bp.get("/versions")
    async def versions() -> Any:
        """Return supported versions and defaults for a configuration type."""
        catalog_service = current_app.extensions[EXT_CATALOG_SERVICE]
        config_type = _request_config_type(DEFAULT_CONFIG_TYPE_FLUENTBIT) or DEFAULT_CONFIG_TYPE_FLUENTBIT
        current_app.logger.info("versions requested config_type=%s", config_type)
        try:
            default_version = catalog_service.get_default_version(config_type=config_type)
        except ValueError:
            current_app.logger.warning(
                "no default version available for config_type=%s; returning empty default",
                config_type,
            )
            default_version = ""
        return jsonify(
            {
                KEY_CONFIG_TYPE: config_type,
                KEY_VERSIONS: catalog_service.get_versions(config_type=config_type),
                KEY_DEFAULT: default_version,
                KEY_SUPPORTED_CONFIG_TYPES: catalog_service.get_supported_config_types(),
            }
        )

    @bp.get("/catalog/<version>")
    async def catalog(version: str) -> Any:
        """Return the catalog payload for a version and optional config type."""
        catalog_service = current_app.extensions[EXT_CATALOG_SERVICE]
        config_type = _request_config_type()
        current_app.logger.info("catalog requested version=%s config_type=%s", version, config_type)
        try:
            payload = catalog_service.get_catalog(version, config_type=config_type)
        except KeyError as exc:
            current_app.logger.warning(
                "catalog lookup failed version=%s config_type=%s error=%s",
                version,
                config_type,
                exc,
            )
            return _json_error_response(str(exc), HTTPStatus.NOT_FOUND)
        return jsonify(payload)

    @bp.get("/service-options/<version>")
    async def service_options(version: str) -> Any:
        """Return the service-definition options for a version and config type."""
        service_definition_service = current_app.extensions[EXT_SERVICE_DEFINITION_SERVICE]
        config_type = _request_config_type()
        current_app.logger.info(
            "service options requested version=%s config_type=%s",
            version,
            config_type,
        )
        try:
            payload = service_definition_service.get_definition(version, config_type=config_type)
        except KeyError as exc:
            current_app.logger.warning(
                "service options lookup failed version=%s config_type=%s error=%s",
                version,
                config_type,
                exc,
            )
            return _json_error_response(str(exc), HTTPStatus.NOT_FOUND)
        return jsonify(payload)

    @bp.get("/parser-options/<version>")
    async def parser_options(version: str) -> Any:
        """Return the parser-definition options for a version and config type."""
        parser_definition_service = current_app.extensions[EXT_PARSER_DEFINITION_SERVICE]
        config_type = _request_config_type(DEFAULT_CONFIG_TYPE_FLUENTBIT) or DEFAULT_CONFIG_TYPE_FLUENTBIT
        current_app.logger.info(
            "parser options requested version=%s config_type=%s",
            version,
            config_type,
        )
        try:
            payload = parser_definition_service.get_definition(version, config_type=config_type)
        except KeyError as exc:
            current_app.logger.warning(
                "parser options lookup failed version=%s config_type=%s error=%s",
                version,
                config_type,
                exc,
            )
            return _json_error_response(str(exc), HTTPStatus.NOT_FOUND)
        return jsonify(payload)

    @bp.get("/issue-codes")
    async def issue_codes() -> Any:
        """Return all configured validation and issue codes."""
        issue_code_service = current_app.extensions[EXT_ISSUE_CODE_SERVICE]
        current_app.logger.debug("issue codes requested")
        return jsonify(issue_code_service.get_all())

    @bp.post("/ui/prepare-file")
    async def ui_prepare_file() -> Any:
        """Parse UI header metadata and build editor support data for a source file."""
        ui_document_service = current_app.extensions[EXT_UI_DOCUMENT_SERVICE]
        body = await _get_request_body()
        try:
            req = UiPrepareFileRequest.model_validate(body)
        except ValidationError as exc:
            current_app.logger.warning("ui prepare file validation failed errors=%s", exc.errors())
            return _json_validation_errors_response(exc)

        parsed = ui_document_service.parse_config_header(req.text)
        effective_config_type = str(req.config_type or parsed.get(KEY_CONFIG_TYPE) or "").strip().lower()
        source_line_map = ui_document_service.build_source_line_map(
            parsed.get(KEY_BODY, ""),
            effective_config_type,
            req.file_name,
        )
        current_app.logger.info(
            "ui prepare file completed file_name=%s effective_config_type=%s",
            req.file_name,
            effective_config_type,
        )
        return jsonify(
            {
                KEY_OK: True,
                KEY_CONFIG_TYPE: parsed.get(KEY_CONFIG_TYPE, ""),
                KEY_VERSION: parsed.get(KEY_VERSION, ""),
                KEY_HEADER_COMMENTS: parsed.get(KEY_HEADER_COMMENTS, ""),
                KEY_BODY: parsed.get(KEY_BODY, ""),
                KEY_SOURCE_LINE_MAP: source_line_map,
            }
        )

    @bp.post("/ui/load-source-file")
    async def ui_load_source_file() -> Any:
        """Load a source file from disk so the editor UI can inspect its contents."""
        body = await _get_request_body()
        try:
            req = UiLoadSourceFileRequest.model_validate(body)
        except ValidationError as exc:
            current_app.logger.warning("ui load source file validation failed errors=%s", exc.errors())
            return _json_validation_errors_response(exc)

        source_path = str(req.source_path or "").strip()
        if not source_path:
            current_app.logger.warning("ui load source file rejected because source_path was empty")
            return _json_error_response("source_path is required", HTTPStatus.BAD_REQUEST)

        try:
            resolved = Path(source_path).expanduser().resolve(strict=True)
        except OSError:
            current_app.logger.warning("ui load source file path not found source_path=%s", source_path)
            return _json_error_response(
                f"source_path not found: {source_path}",
                HTTPStatus.NOT_FOUND,
            )

        if resolved.is_file() is not True:
            current_app.logger.warning(
                "ui load source file rejected because path is not a file source_path=%s resolved=%s",
                source_path,
                resolved,
            )
            return _json_error_response(
                f"source_path is not a file: {source_path}",
                HTTPStatus.BAD_REQUEST,
            )

        try:
            text = resolved.read_text(encoding=ENCODING_UTF8)
        except OSError as exc:
            current_app.logger.exception(
                "ui load source file failed to read source_path=%s resolved=%s",
                source_path,
                resolved,
            )
            return _json_error_response(
                f"failed to read source file: {exc}",
                HTTPStatus.BAD_REQUEST,
            )

        current_app.logger.info("ui load source file completed source_path=%s", resolved)
        return jsonify(
            {
                KEY_OK: True,
                KEY_SOURCE_PATH: str(resolved),
                KEY_FILE_NAME: resolved.name,
                KEY_TEXT: text,
                KEY_CONFIG_TYPE: str(req.config_type or ""),
            }
        )

    @bp.post("/catalog/<version>/validate")
    async def validate_catalog(version: str) -> Any:
        """Validate the catalog registry and rules for a specific version."""
        catalog_service = current_app.extensions[EXT_CATALOG_SERVICE]
        current_app.logger.info("catalog validation requested version=%s", version)
        try:
            result = catalog_service.validate_catalog_for_version(version)
        except (KeyError, ValueError) as exc:
            current_app.logger.warning(
                "catalog validation failed version=%s error=%s",
                version,
                exc,
            )
            return _json_error_response(str(exc), HTTPStatus.BAD_REQUEST)
        return jsonify(result)

    @bp.post("/schema/<version>")
    async def schema(version: str) -> Any:
        """Compile and return a schema for the requested catalog version."""
        catalog_service = current_app.extensions[EXT_CATALOG_SERVICE]
        schema_service = current_app.extensions[EXT_SCHEMA_SERVICE]
        parser_definition_service = current_app.extensions[EXT_PARSER_DEFINITION_SERVICE]
        body = await _get_request_body()
        config_type = _request_config_type()
        current_app.logger.info("schema requested version=%s config_type=%s", version, config_type)
        try:
            options = SchemaOptions.model_validate(body)
            catalog_payload = catalog_service.get_catalog(version, config_type=config_type)
        except ValidationError as exc:
            current_app.logger.warning(
                "schema request validation failed version=%s config_type=%s errors=%s",
                version,
                config_type,
                exc.errors(),
            )
            return jsonify({KEY_OK: False, KEY_ERROR: exc.errors()}), HTTPStatus.BAD_REQUEST
        except KeyError as exc:
            current_app.logger.warning(
                "schema catalog lookup failed version=%s config_type=%s error=%s",
                version,
                config_type,
                exc,
            )
            return _json_error_response(str(exc), HTTPStatus.NOT_FOUND)
        parser_definition = None
        if _is_fluentbit_config_type(config_type):
            parser_definition = parser_definition_service.get_definition(
                version,
                config_type=DEFAULT_CONFIG_TYPE_FLUENTBIT,
            )
        schema_payload = schema_service.compile_schema(
            catalog_payload,
            strict_mode=options.strict,
            parser_definition=parser_definition,
        )
        current_app.logger.info("schema compiled version=%s config_type=%s", version, config_type)
        return jsonify({KEY_OK: True, KEY_SCHEMA: schema_payload})

    @bp.post("/validate/<version>")
    async def validate(version: str) -> Any:
        """Validate a config payload against the selected catalog and rules."""
        catalog_service = current_app.extensions[EXT_CATALOG_SERVICE]
        include_document_service = current_app.extensions[EXT_INCLUDE_DOCUMENT_SERVICE]
        parser_definition_service = current_app.extensions[EXT_PARSER_DEFINITION_SERVICE]
        validation_service = current_app.extensions[EXT_VALIDATION_SERVICE]
        body = await _get_request_body()
        config_type = _request_config_type()
        current_app.logger.info("config validation requested version=%s config_type=%s", version, config_type)
        try:
            req = ValidateRequest.model_validate(body)
            catalog_payload = catalog_service.get_catalog(version, config_type=config_type)
        except ValidationError as exc:
            current_app.logger.warning(
                "config validation request invalid version=%s config_type=%s errors=%s",
                version,
                config_type,
                exc.errors(),
            )
            return _json_validation_errors_response(exc)
        except KeyError as exc:
            current_app.logger.warning(
                "config validation catalog lookup failed version=%s config_type=%s error=%s",
                version,
                config_type,
                exc,
            )
            return _json_error_response(str(exc), HTTPStatus.NOT_FOUND)

        parser_definition = None
        if _is_fluentbit_config_type(config_type):
            parser_definition = parser_definition_service.get_definition(
                version,
                config_type=DEFAULT_CONFIG_TYPE_FLUENTBIT,
            )
        payload = {
            KEY_CONFIG: req.config,
            KEY_ANNOTATIONS: req.annotations,
            KEY_INCLUDED_DOCUMENTS: req.included_documents,
        }
        if req.merge_includes_for_validation:
            current_app.logger.info(
                "config validation merging include documents version=%s config_type=%s include_count=%s",
                version,
                config_type,
                len(req.included_documents),
            )
            payload[KEY_CONFIG] = include_document_service.merge_for_validation(
                config=req.config,
                included_documents=req.included_documents,
            )
        result = validation_service.validate(
            version=version,
            payload=payload,
            catalog=catalog_payload,
            profile=req.profile,
            parser_definition=parser_definition,
        )
        save_ignore_validation = req.save_on_success and resolve_save_ignore_validation()
        should_save = req.save_on_success and (result.get(KEY_OK) is True or save_ignore_validation)
        if req.save_on_success and result.get(KEY_OK) is not True and not save_ignore_validation:
            result[KEY_SAVE_DECLINED] = True
            result[KEY_SAVE_MESSAGE] = "Validation failed; file was not saved."
        if should_save:
            target_path = _allowed_catalog_save_target(req.save_source_path)
            if target_path is None:
                return _validation_save_error(
                    "Save target is not a configured catalog file.",
                    HTTPStatus.FORBIDDEN,
                )
            try:
                rendered_text = _render_validated_save_text(
                    req=req,
                    version=version,
                    config_type=config_type or DEFAULT_CONFIG_TYPE_FLUENTBIT,
                    target_path=target_path,
                )
                target_path.write_text(rendered_text, encoding=ENCODING_UTF8)
            except OSError as exc:
                current_app.logger.warning(
                    "validated config save failed version=%s config_type=%s path=%s error=%s",
                    version,
                    config_type,
                    target_path,
                    exc,
                )
                return _validation_save_error(
                    "Validated configuration could not be saved by the server.",
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                )
            result[KEY_SAVED] = True
            result[KEY_SAVE_PATH] = str(target_path)
            if result.get(KEY_OK) is True:
                result[KEY_SAVE_MESSAGE] = f"Saved validated configuration to {target_path.name}."
            else:
                result[KEY_SAVE_MESSAGE] = (
                    f"Saved configuration with validation errors to {target_path.name}."
                )
        current_app.logger.info(
            "config validation completed version=%s config_type=%s ok=%s",
            version,
            config_type,
            result.get(KEY_OK),
        )
        return jsonify(result), HTTPStatus.OK if result.get(KEY_OK) or result.get(KEY_SAVED) else HTTPStatus.BAD_REQUEST

    @bp.get("/agent-validation/availability/<version>")
    async def agent_validation_availability(version: str) -> Any:
        """Report whether dry-run external validation is available for a config type."""
        external_agent_validation_service = current_app.extensions[
            EXT_EXTERNAL_AGENT_VALIDATION_SERVICE
        ]
        config_type = _request_config_type(DEFAULT_CONFIG_TYPE_FLUENTBIT) or DEFAULT_CONFIG_TYPE_FLUENTBIT
        current_app.logger.info(
            "agent validation availability requested version=%s config_type=%s",
            version,
            config_type,
        )
        result = external_agent_validation_service.dry_run_capability(
            agent_type=config_type,
            agent_version=version,
        )
        return jsonify({KEY_OK: True, **result})

    @bp.post("/agent-validation/dry-run/<version>")
    async def dry_run_validate(version: str) -> Any:
        """Render config text and execute external agent dry-run validation."""
        catalog_service = current_app.extensions[EXT_CATALOG_SERVICE]
        include_document_service = current_app.extensions[EXT_INCLUDE_DOCUMENT_SERVICE]
        yaml_render_service = current_app.extensions[EXT_YAML_RENDER_SERVICE]
        fluentd_config_service = current_app.extensions[EXT_FLUENTD_CONFIG_SERVICE]
        external_agent_validation_service = current_app.extensions[
            EXT_EXTERNAL_AGENT_VALIDATION_SERVICE
        ]

        body = await _get_request_body()
        config_type = _request_config_type(DEFAULT_CONFIG_TYPE_FLUENTBIT) or DEFAULT_CONFIG_TYPE_FLUENTBIT
        current_app.logger.info(
            "agent dry-run validation requested version=%s config_type=%s",
            version,
            config_type,
        )
        try:
            req = ValidateRequest.model_validate(body)
            catalog_service.get_catalog(version, config_type=config_type)
        except ValidationError as exc:
            current_app.logger.warning(
                "agent dry-run request invalid version=%s config_type=%s errors=%s",
                version,
                config_type,
                exc.errors(),
            )
            return _json_validation_errors_response(exc)
        except KeyError as exc:
            current_app.logger.warning(
                "agent dry-run catalog lookup failed version=%s config_type=%s error=%s",
                version,
                config_type,
                exc,
            )
            return _json_error_response(str(exc), HTTPStatus.NOT_FOUND)

        dry_run_config = req.config
        if req.merge_includes_for_validation:
            current_app.logger.info(
                "agent dry-run merging include documents version=%s config_type=%s include_count=%s",
                version,
                config_type,
                len(req.included_documents),
            )
            dry_run_config = include_document_service.merge_for_validation(
                config=req.config,
                included_documents=req.included_documents,
            )

        if config_type == CONFIG_TYPE_FLUENTD:
            rendered_text = fluentd_config_service.render(dry_run_config)
        else:
            rendered_text = yaml_render_service.render(
                payload={KEY_CONFIG: dry_run_config, KEY_ANNOTATIONS: req.annotations},
                include_comments=True,
            )

        try:
            result = external_agent_validation_service.validate(
                config_text=rendered_text,
                agent_type=config_type,
                agent_version=version,
                require_dry_run_enabled=True,
            )
        except AgentNotSupportedError as exc:
            current_app.logger.warning(
                "agent dry-run validation unavailable version=%s config_type=%s error=%s",
                version,
                config_type,
                exc,
            )
            return _json_error_response(str(exc), HTTPStatus.NOT_FOUND)
        current_app.logger.info(
            "agent dry-run validation completed version=%s config_type=%s ok=%s",
            version,
            config_type,
            result.get(KEY_OK),
        )
        return jsonify(result), HTTPStatus.OK

    @bp.post("/render/yaml/<version>")
    async def render_yaml(version: str) -> Any:
        """Render a config payload into YAML plus optional include outputs."""
        catalog_service = current_app.extensions[EXT_CATALOG_SERVICE]
        include_document_service = current_app.extensions[EXT_INCLUDE_DOCUMENT_SERVICE]
        ui_document_service = current_app.extensions[EXT_UI_DOCUMENT_SERVICE]
        yaml_render_service = current_app.extensions[EXT_YAML_RENDER_SERVICE]
        fluentd_config_service = current_app.extensions[EXT_FLUENTD_CONFIG_SERVICE]
        body = await _get_request_body()
        config_type = _request_config_type(DEFAULT_CONFIG_TYPE_FLUENTBIT) or DEFAULT_CONFIG_TYPE_FLUENTBIT
        current_app.logger.info("yaml render requested version=%s config_type=%s", version, config_type)
        try:
            req = RenderYamlRequest.model_validate(body)
            catalog_service.get_catalog(version, config_type=config_type)
        except ValidationError as exc:
            current_app.logger.warning(
                "yaml render request invalid version=%s config_type=%s errors=%s",
                version,
                config_type,
                exc.errors(),
            )
            return jsonify({KEY_OK: False, KEY_ERROR: exc.errors()}), HTTPStatus.BAD_REQUEST
        except KeyError as exc:
            current_app.logger.warning(
                "yaml render catalog lookup failed version=%s config_type=%s error=%s",
                version,
                config_type,
                exc,
            )
            return _json_error_response(str(exc), HTTPStatus.NOT_FOUND)

        yaml_text = yaml_render_service.render(
            payload=req.model_dump(),
            include_comments=req.include_comments,
        )
        included_files: list[dict[str, Any]] = []
        response: dict[str, Any] = {KEY_OK: True, KEY_YAML: yaml_text}
        if req.render_included_files:
            current_app.logger.info(
                "yaml render includes requested version=%s config_type=%s include_count=%s",
                version,
                config_type,
                len(req.included_documents),
            )
            included_files = include_document_service.render_included_documents(
                config_type=config_type,
                included_documents=req.included_documents,
                include_comments=req.include_comments,
                yaml_render_service=yaml_render_service,
                fluentd_config_service=fluentd_config_service,
            )
            response[KEY_INCLUDED_FILES] = included_files
        response[KEY_RENDERED_OUTPUT] = ui_document_service.compose_render_output(
            main_rendered=yaml_text,
            include_loaded_files=req.render_included_files,
            included_files=included_files,
            header_comments=req.header_comments,
            include_config_header=req.include_config_header,
            config_type=config_type,
            version=version,
            comment_prefix=COMMENT_PREFIX_HASH,
        )
        current_app.logger.info("yaml render completed version=%s config_type=%s", version, config_type)
        return jsonify(response)

    @bp.post("/parse/fluentd/<version>")
    async def parse_fluentd(version: str) -> Any:
        """Parse Fluentd text into the structured config payload shape."""
        catalog_service = current_app.extensions[EXT_CATALOG_SERVICE]
        fluentd_config_service = current_app.extensions[EXT_FLUENTD_CONFIG_SERVICE]
        include_document_service = current_app.extensions[EXT_INCLUDE_DOCUMENT_SERVICE]
        body = await _get_request_body()
        current_app.logger.info("fluentd parse requested version=%s", version)
        try:
            req = ParseTextRequest.model_validate(body)
            catalog_service.get_catalog(version, config_type=CONFIG_TYPE_FLUENTD)
        except ValidationError as exc:
            current_app.logger.warning(
                "fluentd parse request invalid version=%s errors=%s",
                version,
                exc.errors(),
            )
            return _json_validation_errors_response(exc)
        except KeyError as exc:
            current_app.logger.warning("fluentd parse catalog lookup failed version=%s error=%s", version, exc)
            return _json_error_response(str(exc), HTTPStatus.NOT_FOUND)
        if not req.text.strip():
            current_app.logger.warning("fluentd parse rejected empty input version=%s", version)
            return (
                jsonify(
                    {
                        KEY_OK: False,
                        KEY_ERRORS: [
                            {
                                KEY_ORDER: 1,
                                KEY_CODE: VALUE_EMPTY_INPUT_FILE,
                                KEY_PATH: ROOT_PATH,
                                KEY_MESSAGE: "The configuration file is empty.",
                                KEY_SEVERITY: VALUE_ERROR,
                                KEY_SOURCE: VALUE_PARSER,
                            }
                        ],
                    }
                ),
                HTTPStatus.BAD_REQUEST,
            )
        try:
            config_payload = fluentd_config_service.parse(req.text)
        except ValueError as exc:
            current_app.logger.warning("fluentd parse failed version=%s error=%s", version, exc)
            return (
                jsonify(
                    {
                        KEY_OK: False,
                        KEY_ERRORS: [
                            {
                                KEY_ORDER: 1,
                                KEY_CODE: VALUE_FLUENTD_PARSE_ERROR,
                                KEY_PATH: ROOT_PATH,
                                KEY_MESSAGE: str(exc),
                                KEY_SEVERITY: VALUE_ERROR,
                                KEY_SOURCE: VALUE_PARSER,
                            }
                        ],
                    }
                ),
                HTTPStatus.BAD_REQUEST,
            )
        response: dict[str, Any] = {KEY_OK: True, KEY_CONFIG: config_payload}
        if req.resolve_includes and req.source_path:
            current_app.logger.info(
                "fluentd parse resolving includes version=%s source_path=%s",
                version,
                req.source_path,
            )
            response[KEY_INCLUDED_DOCUMENTS] = include_document_service.resolve_include_documents(
                config_type=CONFIG_TYPE_FLUENTD,
                source_path=req.source_path,
                config=config_payload,
            )
        current_app.logger.info("fluentd parse completed version=%s", version)
        return jsonify(response)

    @bp.post("/parse/fluentbit/<version>")
    async def parse_fluentbit(version: str) -> Any:
        """Parse Fluent Bit YAML text into the structured config payload shape."""
        catalog_service = current_app.extensions[EXT_CATALOG_SERVICE]
        fluentbit_yaml_config_service = current_app.extensions[EXT_FLUENTBIT_YAML_CONFIG_SERVICE]
        include_document_service = current_app.extensions[EXT_INCLUDE_DOCUMENT_SERVICE]
        body = await _get_request_body()
        current_app.logger.info("fluentbit parse requested version=%s", version)
        try:
            req = ParseTextRequest.model_validate(body)
            catalog_service.get_catalog(version, config_type=DEFAULT_CONFIG_TYPE_FLUENTBIT)
        except ValidationError as exc:
            current_app.logger.warning(
                "fluentbit parse request invalid version=%s errors=%s",
                version,
                exc.errors(),
            )
            return _json_validation_errors_response(exc)
        except KeyError as exc:
            current_app.logger.warning("fluentbit parse catalog lookup failed version=%s error=%s", version, exc)
            return _json_error_response(str(exc), HTTPStatus.NOT_FOUND)

        try:
            result = fluentbit_yaml_config_service.parse(req.text)
        except ValueError as exc:
            message = str(exc)
            code = (
                VALUE_EMPTY_INPUT_FILE
                if "empty" in message.lower()
                else VALUE_FLUENTBIT_YAML_PARSE_ERROR
            )
            current_app.logger.warning(
                "fluentbit parse failed version=%s code=%s error=%s",
                version,
                code,
                exc,
            )
            return (
                jsonify(
                    {
                        KEY_OK: False,
                        KEY_ERRORS: [
                            {
                                KEY_ORDER: 1,
                                KEY_CODE: code,
                                KEY_PATH: ROOT_PATH,
                                KEY_MESSAGE: message,
                                KEY_SEVERITY: VALUE_ERROR,
                                KEY_SOURCE: VALUE_PARSER,
                            }
                        ],
                    }
                ),
                HTTPStatus.BAD_REQUEST,
            )
        if req.resolve_includes and req.source_path:
            current_app.logger.info(
                "fluentbit parse resolving includes version=%s source_path=%s",
                version,
                req.source_path,
            )
            result[KEY_INCLUDED_DOCUMENTS] = include_document_service.resolve_include_documents(
                config_type=DEFAULT_CONFIG_TYPE_FLUENTBIT,
                source_path=req.source_path,
                config=result.get(KEY_CONFIG, {}),
            )
        current_app.logger.info("fluentbit parse completed version=%s", version)
        return jsonify(result)

    @bp.post("/render/fluentd/<version>")
    async def render_fluentd(version: str) -> Any:
        """Render structured Fluentd config data back into Fluentd text."""
        catalog_service = current_app.extensions[EXT_CATALOG_SERVICE]
        fluentd_config_service = current_app.extensions[EXT_FLUENTD_CONFIG_SERVICE]
        include_document_service = current_app.extensions[EXT_INCLUDE_DOCUMENT_SERVICE]
        ui_document_service = current_app.extensions[EXT_UI_DOCUMENT_SERVICE]
        yaml_render_service = current_app.extensions[EXT_YAML_RENDER_SERVICE]
        body = await _get_request_body()
        current_app.logger.info("fluentd render requested version=%s", version)
        try:
            req = RenderTextRequest.model_validate(body)
            catalog_service.get_catalog(version, config_type=CONFIG_TYPE_FLUENTD)
        except ValidationError as exc:
            current_app.logger.warning(
                "fluentd render request invalid version=%s errors=%s",
                version,
                exc.errors(),
            )
            return _json_validation_errors_response(exc)
        except KeyError as exc:
            current_app.logger.warning("fluentd render catalog lookup failed version=%s error=%s", version, exc)
            return _json_error_response(str(exc), HTTPStatus.NOT_FOUND)
        rendered = fluentd_config_service.render(req.config)
        included_files: list[dict[str, Any]] = []
        response: dict[str, Any] = {KEY_OK: True, KEY_TEXT: rendered}
        if req.render_included_files:
            current_app.logger.info(
                "fluentd render includes requested version=%s include_count=%s",
                version,
                len(req.included_documents),
            )
            included_files = include_document_service.render_included_documents(
                config_type=CONFIG_TYPE_FLUENTD,
                included_documents=req.included_documents,
                include_comments=False,
                yaml_render_service=yaml_render_service,
                fluentd_config_service=fluentd_config_service,
            )
            response[KEY_INCLUDED_FILES] = included_files
        response[KEY_RENDERED_OUTPUT] = ui_document_service.compose_render_output(
            main_rendered=rendered,
            include_loaded_files=req.render_included_files,
            included_files=included_files,
            header_comments=req.header_comments,
            include_config_header=req.include_config_header,
            config_type=CONFIG_TYPE_FLUENTD,
            version=version,
            comment_prefix=COMMENT_PREFIX_HASH,
        )
        current_app.logger.info("fluentd render completed version=%s", version)
        return jsonify(response)

    return bp
