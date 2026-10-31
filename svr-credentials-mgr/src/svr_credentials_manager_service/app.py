# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Serve the credential manager API and browser UI."""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from quart import Blueprint, Quart, Response, current_app, jsonify, request, send_from_directory

from . import apply_service
from . import auth as service_auth
from .mock_client_service import MockClientService
from .service_config import (
    resolve_file_directory_from_config,
    resolve_mapping_path_from_config,
    resolve_runtime_config_path,
    resolve_tls_versions_path_from_config,
)
from .storage import (
    ClientMappingStore,
    CredentialStore,
    MappingReconciliationResult,
    create_default_backend,
)

API_PREFIX = "/svr-credentials-manager-service/api/v1"
UI_PATH = "/svr-credentials-manager-service/ui"
HELP_PATH = UI_PATH + "/help"
ENV_MAPPING_PATH = "SVR_CREDENTIALS_MAPPING_PATH"
ENV_FILE_DIRECTORY = "SVR_CREDENTIALS_FILE_DIRECTORY"
ENV_TLS_VERSIONS_PATH = "SVR_CREDENTIALS_TLS_VERSIONS_PATH"
ENV_APP_ENABLE_DEV_FEATURES = "APP_ENABLE_DEV_FEATURES"
DEFAULT_MAPPING_PATH = "client-connection-mappings.json"
DEFAULT_FILE_DIRECTORY = "connection-files"
EXT_CREDENTIAL_STORE = "credential_store"
EXT_MAPPING_STORE = "mapping_store"
EXT_MOCK_CLIENT_SERVICE = "mock_client_service"
JSON_KEY_NAME = "name"
JSON_KEY_DEFINITION = "definition"
JSON_KEY_MAPPINGS = "mappings"
JSON_KEY_CLIENTS = "clients"
JSON_KEY_ERROR = "error"
JSON_KEY_MESSAGE = "message"
JSON_KEY_REFERENCE = "reference"
JSON_KEY_RECONCILIATION = "reconciliation"
JSON_KEY_REMOVED_ASSIGNMENTS = "removed_assignments"
JSON_KEY_VERSIONS = "versions"
JSON_KEY_RESULTS = "results"
JSON_KEY_DELIVERY = "delivery"
JSON_KEY_LOG_PATH = "log_path"
JSON_KEY_APP_ENABLE_DEV_FEATURES = "app_enable_dev_features"
JSON_KEY_HEADERS = "headers"
JSON_KEY_CERTIFICATE = "certificate"
JSON_KEY_TLS = "tls"
JSON_KEY_PROXY = "proxy"
JSON_KEY_OTHER_SETTINGS = "other_settings"
JSON_KEY_OTHER_CONNECTIONS = "other_connections"
JSON_KEY_DESTINATION_ENDPOINT = "destination_endpoint"
JSON_KEY_ENABLED = "enabled"
JSON_KEY_URL = "url"
JSON_KEY_CONNECT_HEADERS = "connect_headers"
JSON_KEY_CERT_FILE = "cert_file"
JSON_KEY_PRIVATE_KEY_FILE = "private_key_file"
JSON_KEY_CA_CERT_FILE = "ca_cert_file"
JSON_KEY_CA_PEM_FILE = "ca_pem_file"
JSON_KEY_INCLUDE_SYSTEM_CA_CERTS_POOL = "include_system_ca_certs_pool"
JSON_KEY_INSECURE_SKIP_VERIFY = "insecure_skip_verify"
JSON_KEY_MIN_VERSION = "min_version"
JSON_KEY_MAX_VERSION = "max_version"
JSON_KEY_CIPHER_SUITES = "cipher_suites"
JSON_KEY_CLIENT_ID = "client_id"
JSON_KEY_CONNECTION_NAME = "connection_name"
STANDARD_CONNECTION_KEYS = (
    "opamp",
    "own_metrics",
    "own_traces",
    "own_logs",
)
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_NO_CONTENT = 204
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
HEADER_CACHE_CONTROL = "Cache-Control"
NO_CACHE_VALUE = "no-store, no-cache, must-revalidate, max-age=0"
ASSET_VERSION_PLACEHOLDER = "__SVR_CREDENTIALS_ASSET_VERSION__"
INDEX_DOCUMENT_NAME = "index.html"
HELP_DOCUMENT_NAME = "help.html"
ENV_TRUE_VALUES = {"1", "true", "yes", "on"}


def _disable_browser_cache(response: Response) -> Response:
    """Mark a UI response as non-cacheable so reloads fetch current assets."""
    response.headers[HEADER_CACHE_CONTROL] = NO_CACHE_VALUE
    return response


def _app_enable_dev_features_enabled() -> bool:
    """Return whether development-only UI features are enabled."""
    raw_value = os.environ.get(ENV_APP_ENABLE_DEV_FEATURES, "")
    normalized = str(raw_value or "").strip().lower()
    return normalized in ENV_TRUE_VALUES


def _is_service_api_path(path: str) -> bool:
    """Return whether ``path`` targets this service's API surface."""
    normalized_path = str(path or "").rstrip("/") or "/"
    normalized_prefix = API_PREFIX.rstrip("/")
    return normalized_path == normalized_prefix or normalized_path.startswith(
        f"{normalized_prefix}/"
    )


def _ui_asset_version(html_directory: Path) -> str:
    """Return a cache-busting version derived from the newest UI asset timestamp."""
    asset_timestamps = [
        asset_path.stat().st_mtime_ns
        for asset_path in html_directory.iterdir()
        if asset_path.is_file()
    ]
    return str(max(asset_timestamps, default=0))


def _load_ui_document(html_directory: Path, document_name: str) -> str:
    """Load one UI HTML document and replace any asset-version placeholders."""
    document = (html_directory / document_name).read_text(encoding="utf-8")
    return document.replace(
        ASSET_VERSION_PLACEHOLDER,
        _ui_asset_version(html_directory),
    )


def _validate_name(name: Any) -> str:
    """Normalize a required connection name or raise a client-safe validation error."""
    normalized = str(name or "").strip()
    if not normalized:
        raise ValueError("Connection name is required")
    return normalized


def _validate_optional_http_address(field_name: str, value: Any) -> None:
    """Ensure optional endpoint fields use an absolute HTTP or HTTPS address."""
    normalized_value = str(value or "").strip()
    if not normalized_value:
        return
    parsed_value = urlparse(normalized_value)
    if parsed_value.scheme not in {"http", "https"} or not parsed_value.netloc:
        raise ValueError(f"{field_name} must be a valid http or https address")


def _validate_optional_json_object(field_name: str, value: Any) -> None:
    """Ensure optional JSON-backed fields remain JSON objects after parsing."""
    if value is None:
        return
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")


def _validate_optional_string(field_name: str, value: Any) -> None:
    """Ensure optional simple text fields remain strings when provided."""
    if value is None:
        return
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")


def _validate_optional_boolean(field_name: str, value: Any) -> None:
    """Ensure optional toggle fields remain booleans when provided."""
    if value is None:
        return
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")


def _validate_optional_string_list(field_name: str, value: Any) -> None:
    """Ensure optional list fields contain only non-empty strings."""
    if value is None:
        return
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{field_name} must be a list of non-empty strings")


def _validate_certificate_settings(section_name: str, certificate_settings: Any) -> None:
    """Validate optional certificate file references for one connection section."""
    if certificate_settings is None:
        return
    if not isinstance(certificate_settings, dict):
        raise ValueError(f"{section_name}.certificate must be a JSON object")
    _validate_optional_string(
        f"{section_name}.{JSON_KEY_CERTIFICATE}.{JSON_KEY_CERT_FILE}",
        certificate_settings.get(JSON_KEY_CERT_FILE),
    )
    _validate_optional_string(
        f"{section_name}.{JSON_KEY_CERTIFICATE}.{JSON_KEY_PRIVATE_KEY_FILE}",
        certificate_settings.get(JSON_KEY_PRIVATE_KEY_FILE),
    )
    _validate_optional_string(
        f"{section_name}.{JSON_KEY_CERTIFICATE}.{JSON_KEY_CA_CERT_FILE}",
        certificate_settings.get(JSON_KEY_CA_CERT_FILE),
    )


def _validate_tls_settings(section_name: str, tls_settings: Any) -> None:
    """Validate optional TLS settings for one connection section."""
    if tls_settings is None:
        return
    if not isinstance(tls_settings, dict):
        raise ValueError(f"{section_name}.tls must be a JSON object")
    _validate_optional_string(
        f"{section_name}.{JSON_KEY_TLS}.{JSON_KEY_CA_PEM_FILE}",
        tls_settings.get(JSON_KEY_CA_PEM_FILE),
    )
    _validate_optional_boolean(
        f"{section_name}.{JSON_KEY_TLS}.{JSON_KEY_INCLUDE_SYSTEM_CA_CERTS_POOL}",
        tls_settings.get(JSON_KEY_INCLUDE_SYSTEM_CA_CERTS_POOL),
    )
    _validate_optional_boolean(
        f"{section_name}.{JSON_KEY_TLS}.{JSON_KEY_INSECURE_SKIP_VERIFY}",
        tls_settings.get(JSON_KEY_INSECURE_SKIP_VERIFY),
    )
    _validate_optional_string(
        f"{section_name}.{JSON_KEY_TLS}.{JSON_KEY_MIN_VERSION}",
        tls_settings.get(JSON_KEY_MIN_VERSION),
    )
    _validate_optional_string(
        f"{section_name}.{JSON_KEY_TLS}.{JSON_KEY_MAX_VERSION}",
        tls_settings.get(JSON_KEY_MAX_VERSION),
    )
    _validate_optional_string_list(
        f"{section_name}.{JSON_KEY_TLS}.{JSON_KEY_CIPHER_SUITES}",
        tls_settings.get(JSON_KEY_CIPHER_SUITES),
    )


def _validate_proxy_settings(section_name: str, proxy_settings: Any) -> None:
    """Validate optional proxy settings for one connection section."""
    if proxy_settings is None:
        return
    if not isinstance(proxy_settings, dict):
        raise ValueError(f"{section_name}.proxy must be a JSON object")
    _validate_optional_http_address(
        f"{section_name}.{JSON_KEY_PROXY}.{JSON_KEY_URL}",
        proxy_settings.get(JSON_KEY_URL),
    )
    _validate_optional_json_object(
        f"{section_name}.{JSON_KEY_PROXY}.{JSON_KEY_CONNECT_HEADERS}",
        proxy_settings.get(JSON_KEY_CONNECT_HEADERS),
    )


def _validate_connection_section(section_name: str, section_definition: Any) -> None:
    """Validate one ConnectionSettings section against the supported UI payload shape."""
    if section_definition is None:
        return
    if not isinstance(section_definition, dict):
        raise ValueError(f"{section_name} must be a JSON object")
    _validate_optional_boolean(
        f"{section_name}.{JSON_KEY_ENABLED}",
        section_definition.get(JSON_KEY_ENABLED),
    )
    _validate_optional_http_address(
        f"{section_name}.{JSON_KEY_DESTINATION_ENDPOINT}",
        section_definition.get(JSON_KEY_DESTINATION_ENDPOINT),
    )
    _validate_optional_json_object(
        f"{section_name}.{JSON_KEY_HEADERS}",
        section_definition.get(JSON_KEY_HEADERS),
    )
    _validate_optional_json_object(
        f"{section_name}.{JSON_KEY_OTHER_SETTINGS}",
        section_definition.get(JSON_KEY_OTHER_SETTINGS),
    )
    _validate_certificate_settings(
        section_name,
        section_definition.get(JSON_KEY_CERTIFICATE),
    )
    _validate_tls_settings(
        section_name,
        section_definition.get(JSON_KEY_TLS),
    )
    _validate_proxy_settings(
        section_name,
        section_definition.get(JSON_KEY_PROXY),
    )


def _validate_connection_definition(definition: dict[str, Any]) -> None:
    """Validate all supported connection sections before storage."""
    for section_name in STANDARD_CONNECTION_KEYS:
        _validate_connection_section(section_name, definition.get(section_name))
    other_connections = definition.get(JSON_KEY_OTHER_CONNECTIONS)
    if other_connections is None:
        return
    if not isinstance(other_connections, dict):
        raise ValueError("other_connections must be a JSON object")
    for other_connection_name, other_definition in other_connections.items():
        normalized_name = str(other_connection_name or "").strip()
        if not normalized_name:
            raise ValueError("other_connections keys must be non-empty strings")
        _validate_connection_section(
            f"{JSON_KEY_OTHER_CONNECTIONS}.{normalized_name}",
            other_definition,
        )


def _resolve_mapping_store_path(config_path: Path | None) -> Path:
    """Return the configured mapping document path with env-var precedence."""
    configured_mapping_path = os.environ.get(ENV_MAPPING_PATH, "").strip()
    if configured_mapping_path:
        return Path(configured_mapping_path).expanduser().resolve()
    resolved_config_path = resolve_runtime_config_path(config_path)
    config_mapping_path = resolve_mapping_path_from_config(resolved_config_path)
    if config_mapping_path is not None:
        return config_mapping_path
    return Path(DEFAULT_MAPPING_PATH).expanduser().resolve()


def _resolve_file_directory(
    file_directory: Path | None,
    config_path: Path | None,
) -> Path:
    """Return the managed upload directory with explicit/env/config precedence."""
    if file_directory is not None:
        return file_directory.expanduser().resolve()
    configured_directory = os.environ.get(ENV_FILE_DIRECTORY, "").strip()
    if configured_directory:
        return Path(configured_directory).expanduser().resolve()
    resolved_config_path = resolve_runtime_config_path(config_path)
    config_directory = resolve_file_directory_from_config(resolved_config_path)
    if config_directory is not None:
        return config_directory
    return Path(DEFAULT_FILE_DIRECTORY).expanduser().resolve()


def _resolve_tls_versions_file(
    tls_versions_path: Path | None,
    config_path: Path | None,
) -> Path:
    """Return the TLS-versions JSON file with explicit/env/config precedence."""
    if tls_versions_path is not None:
        return tls_versions_path.expanduser().resolve()
    configured_path = os.environ.get(ENV_TLS_VERSIONS_PATH, "").strip()
    if configured_path:
        return Path(configured_path).expanduser().resolve()
    resolved_config_path = resolve_runtime_config_path(config_path)
    config_tls_versions_path = resolve_tls_versions_path_from_config(resolved_config_path)
    if config_tls_versions_path is not None:
        return config_tls_versions_path
    return (Path(__file__).resolve().with_name("config") / "tls_versions.json").resolve()


def _normalize_mappings_payload(payload: Any) -> dict[str, str]:
    """Validate and normalize a mapping payload from the API."""
    mappings = payload.get(JSON_KEY_MAPPINGS) if isinstance(payload, dict) else None
    if not isinstance(mappings, dict):
        raise ValueError("mappings must be a JSON object")
    normalized_mappings = {
        str(client).strip(): str(connection).strip()
        for client, connection in mappings.items()
    }
    if any(not client or not connection for client, connection in normalized_mappings.items()):
        raise ValueError("Client and connection names are required")
    return normalized_mappings


def _mappings_with_known_connections(
    mappings: dict[str, str],
    connection_names: list[str],
) -> dict[str, str]:
    """Validate that each mapping targets a stored connection definition."""
    missing_connections = sorted(set(mappings.values()) - set(connection_names))
    if missing_connections:
        raise ValueError(f"Unknown connections: {', '.join(missing_connections)}")
    return mappings


def _reconcile_mappings(
    credential_store: CredentialStore,
    mapping_store: ClientMappingStore,
) -> MappingReconciliationResult:
    """Load the mapping file and remove assignments to missing connections."""
    return mapping_store.load_and_reconcile(credential_store.list_names())


def _reconciliation_message(result: MappingReconciliationResult) -> str:
    """Return a user-facing reconciliation message when stale mappings were removed."""
    if not result.removed_assignments:
        return ""
    removed_pairs = ", ".join(
        f"{assignment.client_id} -> {assignment.connection_name}"
        for assignment in result.removed_assignments
    )
    return (
        "Removed assignments for missing connections: "
        f"{removed_pairs}"
    )


def _mappings_response_payload(result: MappingReconciliationResult) -> dict[str, Any]:
    """Serialize a mapping reconciliation result for API responses."""
    payload: dict[str, Any] = {JSON_KEY_MAPPINGS: result.mappings}
    if not result.removed_assignments:
        return payload
    payload[JSON_KEY_RECONCILIATION] = {
        JSON_KEY_MESSAGE: _reconciliation_message(result),
        JSON_KEY_REMOVED_ASSIGNMENTS: [
            {
                JSON_KEY_CLIENT_ID: assignment.client_id,
                JSON_KEY_CONNECTION_NAME: assignment.connection_name,
            }
            for assignment in result.removed_assignments
        ],
    }
    return payload


def _assigned_client_ids_for_connection(
    mappings: dict[str, str],
    connection_name: str,
) -> list[str]:
    """Return sorted client IDs assigned to one connection definition."""
    return sorted(
        client_id
        for client_id, mapped_connection_name in mappings.items()
        if mapped_connection_name == connection_name
    )


def _apply_response_message(
    connection_name: str,
    results: list[apply_service.ApplyDispatchResult],
) -> str:
    """Build a short user-facing summary for one apply operation."""
    provider_queue_count = sum(
        1 for result in results if result.delivery == "provider_queue"
    )
    fallback_results = [
        result for result in results if result.delivery == "fallback_log"
    ]
    client_label = "client" if len(results) == 1 else "clients"
    if fallback_results and not provider_queue_count:
        return (
            f"Applied {connection_name} to {len(results)} {client_label} using fallback JSON log "
            f"at {fallback_results[0].log_path}."
        )
    if provider_queue_count and not fallback_results:
        return f"Applied {connection_name} to {provider_queue_count} {client_label} via provider queue."
    return (
        f"Applied {connection_name} to {len(results)} {client_label}: "
        f"{provider_queue_count} queued via provider, {len(fallback_results)} logged to fallback JSON."
    )


def create_api_blueprint(file_directory: Path, tls_versions_path: Path) -> Blueprint:
    """Create routes independently so a larger Quart application can register them."""
    blueprint = Blueprint("svr_credentials_manager_api", __name__)

    @blueprint.get("/options/tls-versions")
    async def get_tls_versions() -> tuple[Response, int] | Response:
        """Return supported TLS versions from the configured JSON document."""
        try:
            payload = json.loads(tls_versions_path.read_text(encoding="utf-8"))
            versions = payload.get(JSON_KEY_VERSIONS)
            if not isinstance(versions, list) or not all(
                isinstance(version, str) and version for version in versions
            ):
                raise ValueError("versions must be a list of non-empty strings")
        except (OSError, ValueError, json.JSONDecodeError) as error:
            return jsonify({JSON_KEY_ERROR: f"Invalid TLS versions configuration: {error}"}), 500
        return jsonify({JSON_KEY_VERSIONS: versions})

    @blueprint.post("/files")
    async def upload_connection_file() -> tuple[Response, int] | Response:
        """Store one selected certificate/key file and return its backend reference."""
        uploaded_files = await request.files
        uploaded_file = uploaded_files.get("file")
        if uploaded_file is None or not uploaded_file.filename:
            return jsonify({JSON_KEY_ERROR: "A file is required"}), HTTP_BAD_REQUEST
        safe_name = Path(uploaded_file.filename).name
        if not safe_name:
            return jsonify({JSON_KEY_ERROR: "A valid filename is required"}), HTTP_BAD_REQUEST
        file_directory.mkdir(parents=True, exist_ok=True)
        destination = (file_directory / safe_name).resolve()
        destination.write_bytes(uploaded_file.read())
        return jsonify({JSON_KEY_REFERENCE: str(destination)})

    @blueprint.get("/connections")
    async def list_connections() -> Response:
        """List named definitions without returning their credential values."""
        store: CredentialStore = blueprint.extensions[EXT_CREDENTIAL_STORE]
        return jsonify({"names": store.list_names()})

    @blueprint.get("/connections/<name>")
    async def get_connection(name: str) -> tuple[Response, int] | Response:
        """Return one named definition for editing."""
        store: CredentialStore = blueprint.extensions[EXT_CREDENTIAL_STORE]
        definition = store.get(name)
        if definition is None:
            return jsonify({JSON_KEY_ERROR: "Connection not found"}), HTTP_NOT_FOUND
        return jsonify({JSON_KEY_NAME: name, JSON_KEY_DEFINITION: definition})

    @blueprint.put("/connections/<name>")
    async def save_connection(name: str) -> tuple[Response, int] | Response:
        """Create or replace a named connection definition."""
        try:
            normalized_name = _validate_name(name)
            payload = await request.get_json()
            definition = payload.get(JSON_KEY_DEFINITION) if isinstance(payload, dict) else None
            if not isinstance(definition, dict):
                raise ValueError("definition must be a JSON object")
            _validate_connection_definition(definition)
        except ValueError as error:
            return jsonify({JSON_KEY_ERROR: str(error)}), HTTP_BAD_REQUEST
        store: CredentialStore = blueprint.extensions[EXT_CREDENTIAL_STORE]
        store.save(normalized_name, definition)
        return jsonify({JSON_KEY_NAME: normalized_name})

    @blueprint.delete("/connections/<name>")
    async def delete_connection(name: str) -> tuple[Response, int] | Response:
        """Delete a definition unless a client mapping still references it."""
        store: CredentialStore = blueprint.extensions[EXT_CREDENTIAL_STORE]
        mapping_store: ClientMappingStore = blueprint.extensions[EXT_MAPPING_STORE]
        reconciled_mappings = _reconcile_mappings(store, mapping_store).mappings
        if name in reconciled_mappings.values():
            return (
                jsonify({JSON_KEY_ERROR: "Connection is referenced by a client"}),
                HTTP_BAD_REQUEST,
            )
        if not store.delete(name):
            return jsonify({JSON_KEY_ERROR: "Connection not found"}), HTTP_NOT_FOUND
        return Response(status=HTTP_NO_CONTENT)

    @blueprint.get("/mappings")
    async def get_mappings() -> Response:
        """Return the separate client-to-connection mapping document."""
        store: CredentialStore = blueprint.extensions[EXT_CREDENTIAL_STORE]
        mapping_store: ClientMappingStore = blueprint.extensions[EXT_MAPPING_STORE]
        return jsonify(_mappings_response_payload(_reconcile_mappings(store, mapping_store)))

    @blueprint.get("/mock-clients")
    async def get_mock_clients() -> Response:
        """Return the current list of mock client identifiers for standalone use."""
        mock_client_service: MockClientService = blueprint.extensions[EXT_MOCK_CLIENT_SERVICE]
        return jsonify({JSON_KEY_CLIENTS: mock_client_service.list_client_ids()})

    @blueprint.get("/health")
    async def get_health() -> Response:
        """Return a small runtime payload for UI capability toggles."""
        return jsonify(
            {
                JSON_KEY_APP_ENABLE_DEV_FEATURES: _app_enable_dev_features_enabled(),
            }
        )

    @blueprint.post("/mock-clients")
    async def seed_mock_clients() -> Response:
        """Populate the default set of mock client identifiers and return them."""
        mock_client_service: MockClientService = blueprint.extensions[EXT_MOCK_CLIENT_SERVICE]
        return jsonify({JSON_KEY_CLIENTS: mock_client_service.seed_default_clients()})

    @blueprint.put("/mappings")
    async def save_mappings() -> tuple[Response, int] | Response:
        """Validate and replace all client-to-connection mappings."""
        try:
            normalized_mappings = _normalize_mappings_payload(await request.get_json())
        except ValueError as error:
            return jsonify({JSON_KEY_ERROR: str(error)}), HTTP_BAD_REQUEST
        store: CredentialStore = blueprint.extensions[EXT_CREDENTIAL_STORE]
        try:
            validated_mappings = _mappings_with_known_connections(
                normalized_mappings,
                store.list_names(),
            )
        except ValueError as error:
            return jsonify({JSON_KEY_ERROR: str(error)}), HTTP_BAD_REQUEST
        mapping_store: ClientMappingStore = blueprint.extensions[EXT_MAPPING_STORE]
        mapping_store.save(validated_mappings)
        return jsonify({JSON_KEY_MAPPINGS: validated_mappings})

    @blueprint.post("/connections/<name>/apply")
    async def apply_connection(name: str) -> tuple[Response, int] | Response:
        """Build and dispatch one connection definition to every assigned client."""
        normalized_name = _validate_name(name)
        store: CredentialStore = blueprint.extensions[EXT_CREDENTIAL_STORE]
        definition = store.get(normalized_name)
        if definition is None:
            return jsonify({JSON_KEY_ERROR: "Connection not found"}), HTTP_NOT_FOUND
        mapping_store: ClientMappingStore = blueprint.extensions[EXT_MAPPING_STORE]
        reconciliation_result = _reconcile_mappings(store, mapping_store)
        assigned_client_ids = _assigned_client_ids_for_connection(
            reconciliation_result.mappings,
            normalized_name,
        )
        if not assigned_client_ids:
            return (
                jsonify(
                    {
                        JSON_KEY_ERROR: (
                            "Connection is not assigned to any client nodes"
                        )
                    }
                ),
                HTTP_BAD_REQUEST,
            )
        allow_fallback_without_transport_payload = (
            current_app.config.get("SVR_CREDENTIALS_MANAGER_MODE") == "standalone"
            and not os.environ.get(apply_service.ENV_PROVIDER_BASE_URL, "").strip()
        )
        try:
            prepared_payload = apply_service.build_apply_payload(
                normalized_name,
                definition,
                require_transport_payload=not allow_fallback_without_transport_payload,
            )
        except apply_service.ApplyDependencyError as error:
            return jsonify({JSON_KEY_ERROR: str(error)}), 503
        provider_base_url = apply_service.resolve_provider_base_url(request.host_url)
        dispatch_results: list[apply_service.ApplyDispatchResult] = []
        for client_id in assigned_client_ids:
            dispatch_results.append(
                await apply_service.dispatch_apply(
                    provider_base_url=provider_base_url,
                    prepared_payload=prepared_payload,
                    client_id=client_id,
                    authorization_header=request.headers.get("Authorization"),
                    allow_fallback_without_transport_payload=(
                        allow_fallback_without_transport_payload
                    ),
                )
            )
        payload: dict[str, Any] = {
            JSON_KEY_NAME: normalized_name,
            JSON_KEY_CLIENTS: assigned_client_ids,
            JSON_KEY_MESSAGE: _apply_response_message(
                normalized_name,
                dispatch_results,
            ),
            JSON_KEY_RESULTS: [
                {
                    JSON_KEY_CLIENT_ID: result.client_id,
                    JSON_KEY_CONNECTION_NAME: result.connection_name,
                    JSON_KEY_DELIVERY: result.delivery,
                    JSON_KEY_LOG_PATH: result.log_path,
                }
                for result in dispatch_results
            ],
        }
        if reconciliation_result.removed_assignments:
            payload[JSON_KEY_RECONCILIATION] = _mappings_response_payload(
                reconciliation_result
            )[JSON_KEY_RECONCILIATION]
        return jsonify(payload)

    return blueprint


def register_components(
    app: Quart,
    credential_store: CredentialStore,
    mapping_store: ClientMappingStore,
    file_directory: Path | None = None,
    tls_versions_path: Path | None = None,
    config_path: Path | None = None,
) -> None:
    """Register API and UI components into ``app`` for embedded operation."""
    selected_file_directory = _resolve_file_directory(file_directory, config_path)
    selected_tls_versions_path = _resolve_tls_versions_file(
        tls_versions_path,
        config_path,
    )
    api_blueprint = create_api_blueprint(
        selected_file_directory,
        selected_tls_versions_path,
    )
    mock_client_service = MockClientService()
    api_blueprint.extensions = {
        EXT_CREDENTIAL_STORE: credential_store,
        EXT_MAPPING_STORE: mapping_store,
        EXT_MOCK_CLIENT_SERVICE: mock_client_service,
    }
    app.register_blueprint(api_blueprint, url_prefix=API_PREFIX)
    html_directory = Path(__file__).resolve().with_name("html")

    @app.before_request
    async def enforce_service_api_bearer_auth() -> tuple[Response, int] | None:
        """Apply provider-style bearer auth to the credentials-manager API routes."""
        if not _is_service_api_path(request.path):
            return None
        auth_decision = service_auth.evaluate_api_auth(
            path=request.path,
            method=request.method,
            authorization_header=request.headers.get("Authorization"),
            remote_addr=request.remote_addr,
            config_path=config_path,
        )
        if auth_decision.allowed:
            return None
        response = jsonify({JSON_KEY_ERROR: auth_decision.error})
        if auth_decision.status_code == 401:
            response.headers["WWW-Authenticate"] = service_auth.WWW_AUTHENTICATE_BEARER
        return response, auth_decision.status_code

    @app.get(UI_PATH)
    async def credential_manager_ui() -> Response:
        """Return the external HTML asset used by the credential editor."""
        document = _load_ui_document(html_directory, INDEX_DOCUMENT_NAME)
        return _disable_browser_cache(Response(document, mimetype="text/html"))

    @app.get(HELP_PATH)
    async def credential_manager_help() -> Response:
        """Return the standalone help page for the credential manager UI."""
        document = _load_ui_document(html_directory, HELP_DOCUMENT_NAME)
        return _disable_browser_cache(Response(document, mimetype="text/html"))

    @app.get(UI_PATH + "/assets/<path:filename>")
    async def credential_manager_assets(filename: str) -> Response:
        """Serve the modular JavaScript and CSS assets."""
        response = await send_from_directory(html_directory, filename)
        return _disable_browser_cache(response)


def create_app(
    *,
    mode: str = "standalone",
    credential_store: CredentialStore | None = None,
    mapping_store: ClientMappingStore | None = None,
    config_path: Path | None = None,
    file_directory: Path | None = None,
    tls_versions_path: Path | None = None,
) -> Quart:
    """Create the service for standalone or larger-application registration."""
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    app = Quart(__name__)
    resolved_config_path = resolve_runtime_config_path(config_path)
    selected_credential_store = credential_store or CredentialStore(
        create_default_backend(resolved_config_path)
    )
    selected_mapping_store = mapping_store or ClientMappingStore(
        _resolve_mapping_store_path(resolved_config_path)
    )
    app.config["SVR_CREDENTIALS_MANAGER_MODE"] = mode
    app.logger.setLevel(logging.DEBUG)
    register_components(
        app,
        selected_credential_store,
        selected_mapping_store,
        file_directory,
        tls_versions_path,
        resolved_config_path,
    )
    return app


def main() -> None:
    """Parse standalone network options and run the Quart development server."""
    parser = argparse.ArgumentParser(description="OpAMP server credential manager service")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address")
    parser.add_argument("--port", default=8091, type=int, help="Listen port")
    parser.add_argument("--config-path", help="Optional JSON file with runtime storage settings")
    arguments = parser.parse_args()
    resolved_config_path = Path(arguments.config_path) if arguments.config_path else None
    create_app(config_path=resolved_config_path).run(
        host=arguments.host,
        port=arguments.port,
        debug=True,
    )


if __name__ == "__main__":
    main()
