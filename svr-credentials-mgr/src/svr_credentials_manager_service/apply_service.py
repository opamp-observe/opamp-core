# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Build and dispatch connection-settings apply payloads."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib import error, parse, request

from connection_settings_builder import ConnectionSettingsBuilder
from connection_settings_builder.builder import FIELD_CONNECTIONS

ENV_PROVIDER_BASE_URL = "SVR_CREDENTIALS_PROVIDER_BASE_URL"
ENV_CONNECTION_APPLY_LOG_PATH = "SVR_CREDENTIALS_CONNECTION_APPLY_LOG_PATH"
DEFAULT_CONNECTION_APPLY_LOG_PATH = "connection-settings-apply-fallback.jsonl"
HTTP_TIMEOUT_SECONDS = 5


class ProviderApplyError(RuntimeError):
    """Raised when the provider responded but rejected the apply request."""


class ProviderUnavailableError(RuntimeError):
    """Raised when the provider endpoint cannot be reached reliably."""


class ApplyDependencyError(RuntimeError):
    """Raised when Apply-specific optional dependencies are unavailable."""


@dataclass(frozen=True)
class PreparedConnectionApply:
    """Serialized payload and JSON form ready to send or log."""

    connection_name: str
    payload_bytes: bytes | None
    server_to_agent: dict[str, Any]


@dataclass(frozen=True)
class ApplyDispatchResult:
    """Result returned after dispatching one apply request."""

    client_id: str
    connection_name: str
    delivery: str
    log_path: str | None = None
    provider_status_code: int | None = None


def _repo_root() -> Path:
    """Return the repository root path from the installed service package."""
    return Path(__file__).resolve().parents[3]


def _load_opamp_protobuf_module() -> ModuleType:
    """Load the repository OpAMP protobuf module used by the builder."""
    provider_source = _repo_root() / "provider" / "src"
    resolved_provider_source = str(provider_source.resolve())
    if resolved_provider_source not in sys.path:
        sys.path.insert(0, resolved_provider_source)
    try:
        from opamp_provider.proto import opamp_pb2  # noqa: WPS433
    except ModuleNotFoundError as error:
        raise ApplyDependencyError(
            "Apply requires the protobuf dependency. Install the service with its updated "
            "dependencies and retry."
        ) from error

    return opamp_pb2


def _message_to_dict(message: Any) -> dict[str, Any]:
    """Convert one protobuf message to a JSON-serializable dictionary."""
    try:
        from google.protobuf.json_format import MessageToDict  # noqa: WPS433
    except ModuleNotFoundError as error:
        raise ApplyDependencyError(
            "Apply requires the protobuf dependency. Install the service with its updated "
            "dependencies and retry."
        ) from error
    return MessageToDict(
        message,
        preserving_proto_field_name=True,
    )


def _read_reference_bytes(reference: str, *, file_root: Path) -> bytes:
    """Read one referenced file using the same relative-path rules as the builder."""
    reference_path = Path(reference).expanduser()
    selected_path = (
        reference_path
        if reference_path.is_absolute()
        else file_root / reference_path
    )
    return selected_path.resolve().read_bytes()


def _headers_payload(headers: dict[str, Any]) -> dict[str, Any] | None:
    """Return one protobuf-JSON compatible headers object when values exist."""
    if not headers:
        return None
    return {
        "headers": [
            {
                "key": str(header_key),
                "value": str(header_value),
            }
            for header_key, header_value in headers.items()
        ]
    }


def _certificate_payload(
    certificate: dict[str, Any],
    *,
    file_root: Path,
) -> dict[str, Any] | None:
    """Return one protobuf-JSON compatible certificate object."""
    payload: dict[str, Any] = {}
    if certificate.get("cert_file"):
        payload["cert"] = base64.b64encode(
            _read_reference_bytes(str(certificate["cert_file"]), file_root=file_root)
        ).decode("ascii")
    if certificate.get("private_key_file"):
        payload["private_key"] = base64.b64encode(
            _read_reference_bytes(str(certificate["private_key_file"]), file_root=file_root)
        ).decode("ascii")
    if certificate.get("ca_cert_file"):
        payload["ca_cert"] = base64.b64encode(
            _read_reference_bytes(str(certificate["ca_cert_file"]), file_root=file_root)
        ).decode("ascii")
    return payload or None


def _tls_payload(tls: dict[str, Any], *, file_root: Path) -> dict[str, Any] | None:
    """Return one protobuf-JSON compatible TLS object."""
    payload: dict[str, Any] = {}
    for field_name in (
        "include_system_ca_certs_pool",
        "insecure_skip_verify",
        "min_version",
        "max_version",
    ):
        if field_name in tls and tls[field_name] not in ("", None):
            payload[field_name] = tls[field_name]
    if tls.get("ca_pem_file"):
        payload["ca_pem_contents"] = _read_reference_bytes(
            str(tls["ca_pem_file"]),
            file_root=file_root,
        ).decode("utf-8")
    cipher_suites = list(tls.get("cipher_suites", []))
    if cipher_suites:
        payload["cipher_suites"] = cipher_suites
    return payload or None


def _proxy_payload(proxy: dict[str, Any]) -> dict[str, Any] | None:
    """Return one protobuf-JSON compatible proxy object."""
    payload: dict[str, Any] = {}
    url = str(proxy.get("url") or "").strip()
    if url:
        payload["url"] = url
    connect_headers = _headers_payload(proxy.get("connect_headers", {}))
    if connect_headers:
        payload["connect_headers"] = connect_headers
    return payload or None


def _any_value_payload(value: Any) -> dict[str, Any]:
    """Return one protobuf-JSON compatible AnyValue object."""
    if isinstance(value, bool):
        return {"bool_value": value}
    if isinstance(value, int):
        return {"int_value": str(value)}
    if isinstance(value, float):
        return {"double_value": value}
    return {"string_value": str(value)}


def _connection_payload(
    definition: dict[str, Any],
    *,
    file_root: Path,
    include_other_settings: bool = False,
) -> dict[str, Any]:
    """Return one protobuf-JSON compatible connection-settings section."""
    payload: dict[str, Any] = {}
    destination_endpoint = str(definition.get("destination_endpoint") or "").strip()
    if destination_endpoint:
        payload["destination_endpoint"] = destination_endpoint
    headers = _headers_payload(definition.get("headers", {}))
    if headers:
        payload["headers"] = headers
    certificate = _certificate_payload(
        definition.get("certificate", {}),
        file_root=file_root,
    )
    if certificate:
        payload["certificate"] = certificate
    tls = _tls_payload(definition.get("tls", {}), file_root=file_root)
    if tls:
        payload["tls"] = tls
    proxy = _proxy_payload(definition.get("proxy", {}))
    if proxy:
        payload["proxy"] = proxy
    if include_other_settings:
        other_settings = definition.get("other_settings", {})
        if other_settings:
            payload["other_settings"] = {
                str(setting_key): _any_value_payload(setting_value)
                for setting_key, setting_value in other_settings.items()
            }
    return payload


def _fallback_server_to_agent_payload(
    definition: dict[str, Any],
    *,
    file_root: Path,
) -> dict[str, Any]:
    """Return a standalone JSON form of the intended ServerToAgent payload."""
    canonical = json.dumps(
        definition,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    connection_settings: dict[str, Any] = {
        "hash": base64.b64encode(hashlib.sha256(canonical).digest()).decode("ascii"),
    }
    for field_name in FIELD_CONNECTIONS:
        section_definition = definition.get(field_name)
        if section_definition and section_definition.get("enabled", True):
            connection_settings[field_name] = _connection_payload(
                section_definition,
                file_root=file_root,
            )
    other_connections = definition.get("other_connections", {})
    if other_connections:
        included_other_connections = {
            str(connection_name): _connection_payload(
                section_definition,
                file_root=file_root,
                include_other_settings=True,
            )
            for connection_name, section_definition in other_connections.items()
            if section_definition.get("enabled", True)
        }
        if included_other_connections:
            connection_settings["other_connections"] = included_other_connections
    return {"connection_settings": connection_settings}


def build_apply_payload(
    connection_name: str,
    definition: dict[str, Any],
    *,
    require_transport_payload: bool = True,
    file_root: Path | None = None,
) -> PreparedConnectionApply:
    """Build apply payload state for provider delivery and/or fallback logging."""
    selected_file_root = file_root or Path.cwd()
    fallback_server_to_agent = _fallback_server_to_agent_payload(
        definition,
        file_root=selected_file_root,
    )
    try:
        protobuf_module = _load_opamp_protobuf_module()
    except ApplyDependencyError:
        if require_transport_payload:
            raise
        return PreparedConnectionApply(
            connection_name=connection_name,
            payload_bytes=None,
            server_to_agent=fallback_server_to_agent,
        )
    message = ConnectionSettingsBuilder(
        protobuf_module,
        file_root=selected_file_root,
    ).build(definition)
    return PreparedConnectionApply(
        connection_name=connection_name,
        payload_bytes=message.connection_settings.SerializeToString(),
        server_to_agent=_message_to_dict(message)
        if require_transport_payload
        else fallback_server_to_agent,
    )


def resolve_provider_base_url(request_host_url: str) -> str:
    """Resolve the provider base URL from environment or the current request origin."""
    configured_base_url = str(os.environ.get(ENV_PROVIDER_BASE_URL, "")).strip()
    if configured_base_url:
        return configured_base_url.rstrip("/")
    return str(request_host_url or "").rstrip("/")


def resolve_fallback_log_path() -> Path:
    """Resolve the JSONL fallback log path for unavailable-provider applies."""
    configured_path = str(
        os.environ.get(
            ENV_CONNECTION_APPLY_LOG_PATH,
            DEFAULT_CONNECTION_APPLY_LOG_PATH,
        )
    ).strip()
    return Path(configured_path).expanduser().resolve()


def _request_body(prepared_payload: PreparedConnectionApply) -> bytes:
    """Serialize the provider API request body."""
    return json.dumps(
        {
            "connection_name": prepared_payload.connection_name,
            "payload_base64": base64.b64encode(prepared_payload.payload_bytes).decode(
                "ascii"
            ),
        }
    ).encode("utf-8")


def _validated_provider_endpoint(provider_base_url: str, client_id: str) -> str:
    """Build one provider endpoint URL after enforcing an HTTP(S) scheme."""
    target_url = (
        provider_base_url.rstrip("/")
        + "/api/clients/"
        + parse.quote(client_id, safe="")
        + "/connection-settings"
    )
    parsed_target_url = parse.urlsplit(target_url)
    if parsed_target_url.scheme not in {"http", "https"} or not parsed_target_url.netloc:
        raise ProviderApplyError("provider base URL must use http or https")
    return target_url


def _provider_request(
    *,
    provider_base_url: str,
    prepared_payload: PreparedConnectionApply,
    client_id: str,
    authorization_header: str | None,
) -> dict[str, Any]:
    """Perform the synchronous provider API request."""
    target_url = _validated_provider_endpoint(provider_base_url, client_id)
    headers = {"Content-Type": "application/json"}
    if authorization_header:
        headers["Authorization"] = authorization_header
    req = request.Request(  # noqa: S310 - target_url is validated to http(s) above.
        target_url,
        data=_request_body(prepared_payload),
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310
            response_payload = json.loads(response.read().decode("utf-8"))
            return {
                "status_code": response.getcode(),
                "payload": response_payload,
            }
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError as decode_error:
            raise ProviderUnavailableError(
                f"provider returned HTTP {exc.code}"
            ) from decode_error
        if exc.code >= 500:
            raise ProviderUnavailableError(f"provider returned HTTP {exc.code}") from exc
        raise ProviderApplyError(
            str(payload.get("error") or f"provider returned HTTP {exc.code}")
        ) from exc
    except (error.URLError, TimeoutError) as exc:
        raise ProviderUnavailableError("provider endpoint is unavailable") from exc


def _append_fallback_log(
    *,
    prepared_payload: PreparedConnectionApply,
    client_id: str,
    provider_base_url: str,
    fallback_log_path: Path,
) -> None:
    """Append one JSONL fallback record for an unavailable provider."""
    fallback_log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "applied_at_utc": datetime.now(timezone.utc).isoformat(),
        "delivery": "fallback_log",
        "provider_base_url": provider_base_url,
        "client_id": client_id,
        "connection_name": prepared_payload.connection_name,
        "server_to_agent": prepared_payload.server_to_agent,
    }
    with fallback_log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(payload, sort_keys=True) + "\n")


async def dispatch_apply(
    *,
    provider_base_url: str,
    prepared_payload: PreparedConnectionApply,
    client_id: str,
    authorization_header: str | None,
    fallback_log_path: Path | None = None,
    allow_fallback_without_transport_payload: bool = False,
) -> ApplyDispatchResult:
    """Queue one apply request with the provider or write a fallback JSON log."""
    selected_fallback_log_path = fallback_log_path or resolve_fallback_log_path()
    if prepared_payload.payload_bytes is None:
        if not allow_fallback_without_transport_payload:
            raise ApplyDependencyError(
                "Apply requires the protobuf dependency. Install the service with its updated "
                "dependencies and retry."
            )
        await asyncio.to_thread(
            _append_fallback_log,
            prepared_payload=prepared_payload,
            client_id=client_id,
            provider_base_url=provider_base_url,
            fallback_log_path=selected_fallback_log_path,
        )
        return ApplyDispatchResult(
            client_id=client_id,
            connection_name=prepared_payload.connection_name,
            delivery="fallback_log",
            log_path=str(selected_fallback_log_path),
        )
    try:
        provider_result = await asyncio.to_thread(
            _provider_request,
            provider_base_url=provider_base_url,
            prepared_payload=prepared_payload,
            client_id=client_id,
            authorization_header=authorization_header,
        )
    except ProviderUnavailableError:
        await asyncio.to_thread(
            _append_fallback_log,
            prepared_payload=prepared_payload,
            client_id=client_id,
            provider_base_url=provider_base_url,
            fallback_log_path=selected_fallback_log_path,
        )
        return ApplyDispatchResult(
            client_id=client_id,
            connection_name=prepared_payload.connection_name,
            delivery="fallback_log",
            log_path=str(selected_fallback_log_path),
        )
    return ApplyDispatchResult(
        client_id=client_id,
        connection_name=prepared_payload.connection_name,
        delivery="provider_queue",
        provider_status_code=int(provider_result["status_code"]),
    )
