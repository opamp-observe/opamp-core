# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Load runtime configuration for the credentials manager service."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ENV_CONFIG_PATH = "SVR_CREDENTIALS_CONFIG_PATH"
ENV_OPAMP_CONFIG_PATH = "OPAMP_CONFIG_PATH"
JSON_KEY_OPAMP = "opamp"
JSON_KEY_SERVICE = "svr_credentials_manager"
JSON_KEY_AUTHORIZATION = "authorization"
JSON_KEY_STORAGE = "storage"
JSON_KEY_UI_USE_AUTHORIZATION = "ui_use_authorization"
JSON_KEY_UI_AUTH_STATIC_TOKEN = "ui_auth_static_token"  # noqa: S105
JSON_KEY_UI_AUTH_JWT_ISSUER = "ui_auth_jwt_issuer"
JSON_KEY_UI_AUTH_JWT_AUDIENCE = "ui_auth_jwt_audience"
JSON_KEY_UI_AUTH_JWT_JWKS_URL = "ui_auth_jwt_jwks_url"
JSON_KEY_UI_AUTH_JWT_LEEWAY_SECONDS = "ui_auth_jwt_leeway_seconds"
JSON_KEY_MAPPING_PATH = "mapping_path"
JSON_KEY_KEYRING_BACKEND = "keyring_backend"
JSON_KEY_PLAINTEXT_PATH = "plaintext_path"
JSON_KEY_CRYPTFILE_PATH = "cryptfile_path"
JSON_KEY_CRYPTFILE_PASSWORD = "cryptfile_password"  # noqa: S105
JSON_KEY_FILE_DIRECTORY = "file_directory"
JSON_KEY_TLS_VERSIONS_PATH = "tls_versions_path"
UTF8_ENCODING = "utf-8"


def _load_json_object(config_path: Path) -> dict[str, Any]:
    """Load one JSON object from ``config_path``."""
    if not config_path.exists():
        raise RuntimeError(f"Service configuration file not found: {config_path}")
    try:
        payload = json.loads(config_path.read_text(encoding=UTF8_ENCODING))
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Invalid service configuration JSON at {config_path}: {error.msg}"
        ) from error
    except OSError as error:
        raise RuntimeError(
            f"Unable to read service configuration file {config_path}: {error}"
        ) from error
    if not isinstance(payload, dict):
        raise RuntimeError("Service configuration must be a JSON object")
    return payload


def _service_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the credentials-manager config object from common or legacy JSON."""
    opamp_payload = payload.get(JSON_KEY_OPAMP, {})
    if opamp_payload is None:
        opamp_payload = {}
    if not isinstance(opamp_payload, dict):
        raise RuntimeError("Service configuration field 'opamp' must be a JSON object")
    if JSON_KEY_SERVICE not in opamp_payload:
        return payload
    service_payload = opamp_payload.get(JSON_KEY_SERVICE, {})
    if service_payload is None:
        return {}
    if not isinstance(service_payload, dict):
        raise RuntimeError(
            "Service configuration field 'opamp.svr_credentials_manager' must be a JSON object"
        )
    return service_payload


def _section_payload(payload: dict[str, Any], section_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the resolved service payload and one validated nested section."""
    service_payload = _service_payload(payload)
    section_payload = service_payload.get(section_name, {})
    if section_payload is None:
        section_payload = {}
    if not isinstance(section_payload, dict):
        raise RuntimeError(
            f"Service configuration field '{section_name}' must be a JSON object"
        )
    return service_payload, section_payload


def _configured_string(
    payload: dict[str, Any],
    *,
    field_name: str,
    section_name: str | None = None,
) -> str:
    """Return one configured string from the common or legacy payload shape."""
    service_payload = _service_payload(payload)
    raw_value: Any
    if section_name is None:
        raw_value = service_payload.get(field_name)
    else:
        service_payload, section_payload = _section_payload(payload, section_name)
        raw_value = section_payload.get(field_name, service_payload.get(field_name))
    if raw_value is None:
        return ""
    if not isinstance(raw_value, str):
        raise RuntimeError(f"Service configuration field '{field_name}' must be a string")
    return raw_value.strip()


def _configured_int(
    payload: dict[str, Any],
    *,
    field_name: str,
    section_name: str | None = None,
) -> int | None:
    """Return one configured integer from the common or legacy payload shape."""
    service_payload = _service_payload(payload)
    raw_value: Any
    if section_name is None:
        raw_value = service_payload.get(field_name)
    else:
        service_payload, section_payload = _section_payload(payload, section_name)
        raw_value = section_payload.get(field_name, service_payload.get(field_name))
    if raw_value is None or raw_value == "":
        return None
    try:
        return int(raw_value)
    except (TypeError, ValueError) as error:
        raise RuntimeError(
            f"Service configuration field '{field_name}' must be an integer"
        ) from error


def resolve_runtime_config_path(config_path: Path | None = None) -> Path | None:
    """Return the optional runtime config path from argument or environment."""
    if config_path is not None:
        return config_path.expanduser().resolve()
    for env_name in (ENV_CONFIG_PATH, ENV_OPAMP_CONFIG_PATH):
        configured_path = os.environ.get(env_name, "").strip()
        if configured_path:
            return Path(configured_path).expanduser().resolve()
    return None


def _resolve_optional_path_from_config(
    config_path: Path | None,
    *,
    field_name: str,
    section_name: str | None = None,
) -> Path | None:
    """Resolve one configured path relative to the config file when needed."""
    resolved_config_path = resolve_runtime_config_path(config_path)
    if resolved_config_path is None:
        return None
    configured_path = _configured_string(
        _load_json_object(resolved_config_path),
        field_name=field_name,
        section_name=section_name,
    )
    if not configured_path:
        return None
    path = Path(configured_path).expanduser()
    if not path.is_absolute():
        path = resolved_config_path.parent / path
    return path.resolve()


def resolve_mapping_path_from_config(config_path: Path | None) -> Path | None:
    """Resolve the mapping-file path from the runtime config when configured."""
    return _resolve_optional_path_from_config(
        config_path,
        field_name=JSON_KEY_MAPPING_PATH,
        section_name=JSON_KEY_STORAGE,
    )


def resolve_plaintext_path_from_config(config_path: Path | None) -> Path | None:
    """Resolve the plaintext credential-store path from the runtime config."""
    return _resolve_optional_path_from_config(
        config_path,
        field_name=JSON_KEY_PLAINTEXT_PATH,
        section_name=JSON_KEY_STORAGE,
    )


def resolve_cryptfile_path_from_config(config_path: Path | None) -> Path | None:
    """Resolve the cryptfile credential-store path from the runtime config."""
    return _resolve_optional_path_from_config(
        config_path,
        field_name=JSON_KEY_CRYPTFILE_PATH,
        section_name=JSON_KEY_STORAGE,
    )


def resolve_file_directory_from_config(config_path: Path | None) -> Path | None:
    """Resolve the managed connection-file directory from the runtime config."""
    return _resolve_optional_path_from_config(
        config_path,
        field_name=JSON_KEY_FILE_DIRECTORY,
        section_name=JSON_KEY_STORAGE,
    )


def resolve_tls_versions_path_from_config(config_path: Path | None) -> Path | None:
    """Resolve the TLS-versions JSON path from the runtime config."""
    return _resolve_optional_path_from_config(
        config_path,
        field_name=JSON_KEY_TLS_VERSIONS_PATH,
        section_name=JSON_KEY_STORAGE,
    )


def _resolve_optional_string_from_config(
    config_path: Path | None,
    *,
    field_name: str,
    section_name: str | None = None,
) -> str | None:
    """Resolve one optional string value from the runtime config."""
    resolved_config_path = resolve_runtime_config_path(config_path)
    if resolved_config_path is None:
        return None
    configured_value = _configured_string(
        _load_json_object(resolved_config_path),
        field_name=field_name,
        section_name=section_name,
    )
    return configured_value or None


def resolve_keyring_backend_from_config(config_path: Path | None = None) -> str | None:
    """Resolve the optional keyring backend name from the runtime config."""
    return _resolve_optional_string_from_config(
        config_path,
        field_name=JSON_KEY_KEYRING_BACKEND,
        section_name=JSON_KEY_STORAGE,
    )


def resolve_cryptfile_password_from_config(config_path: Path | None = None) -> str | None:
    """Resolve the optional cryptfile password from the runtime config."""
    return _resolve_optional_string_from_config(
        config_path,
        field_name=JSON_KEY_CRYPTFILE_PASSWORD,
        section_name=JSON_KEY_STORAGE,
    )


def resolve_ui_authorization_mode_from_config(config_path: Path | None = None) -> str | None:
    """Resolve the optional UI authorization mode from the runtime config."""
    configured_mode = _resolve_optional_string_from_config(
        config_path,
        field_name=JSON_KEY_UI_USE_AUTHORIZATION,
        section_name=JSON_KEY_AUTHORIZATION,
    )
    return configured_mode.lower() if configured_mode else None


def resolve_ui_auth_static_token_from_config(config_path: Path | None = None) -> str | None:
    """Resolve the optional static bearer token from the runtime config."""
    return _resolve_optional_string_from_config(
        config_path,
        field_name=JSON_KEY_UI_AUTH_STATIC_TOKEN,
        section_name=JSON_KEY_AUTHORIZATION,
    )


def resolve_ui_auth_jwt_issuer_from_config(config_path: Path | None = None) -> str | None:
    """Resolve the optional JWT issuer from the runtime config."""
    return _resolve_optional_string_from_config(
        config_path,
        field_name=JSON_KEY_UI_AUTH_JWT_ISSUER,
        section_name=JSON_KEY_AUTHORIZATION,
    )


def resolve_ui_auth_jwt_audience_from_config(config_path: Path | None = None) -> str | None:
    """Resolve the optional JWT audience from the runtime config."""
    return _resolve_optional_string_from_config(
        config_path,
        field_name=JSON_KEY_UI_AUTH_JWT_AUDIENCE,
        section_name=JSON_KEY_AUTHORIZATION,
    )


def resolve_ui_auth_jwt_jwks_url_from_config(config_path: Path | None = None) -> str | None:
    """Resolve the optional JWT JWKS URL from the runtime config."""
    return _resolve_optional_string_from_config(
        config_path,
        field_name=JSON_KEY_UI_AUTH_JWT_JWKS_URL,
        section_name=JSON_KEY_AUTHORIZATION,
    )


def resolve_ui_auth_jwt_leeway_seconds_from_config(
    config_path: Path | None = None,
) -> int | None:
    """Resolve the optional JWT clock-skew leeway from the runtime config."""
    resolved_config_path = resolve_runtime_config_path(config_path)
    if resolved_config_path is None:
        return None
    return _configured_int(
        _load_json_object(resolved_config_path),
        field_name=JSON_KEY_UI_AUTH_JWT_LEEWAY_SECONDS,
        section_name=JSON_KEY_AUTHORIZATION,
    )
