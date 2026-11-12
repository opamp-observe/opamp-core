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

"""Quart OpAMP server skeleton."""

from __future__ import annotations

import asyncio
import logging
import ssl
import tracemalloc
from datetime import datetime, timezone
from http import HTTPStatus

from google.protobuf import text_format
from quart import Quart, Response, jsonify, redirect, request, websocket
from quart.typing import ResponseReturnValue
from werkzeug.exceptions import HTTPException

from opamp_provider import auth as provider_auth
from opamp_provider import config as provider_config
from opamp_provider.app_client_filters import coerce_bool_setting
from opamp_provider.app_constants import GLOBAL_SETTINGS_HELP, MODEL_DUMP_MODE
from opamp_provider.app_persistence import (
    PersistenceTracker,
)
from opamp_provider.app_persistence import (
    request_process_shutdown as _request_process_shutdown,
)
from opamp_provider.app_response_builder import ServerToAgentResponseBuilder
from opamp_provider.app_routes_clients import register_client_routes
from opamp_provider.app_routes_settings import register_settings_routes
from opamp_provider.app_routes_ui import register_ui_routes
from opamp_provider.app_ui_assets import load_provider_ui_assets, render_help_html
from opamp_provider.command_record import CommandRecord
from opamp_provider.commands import (
    command_object_factory,
    get_custom_capabilities_list,
)
from opamp_provider.component_features import (
    UiFeatureMenuItem,
    register_provider_component_entries,
    ui_menu_items_from_component_entries,
)
from opamp_provider.component_version import component_version_text
from opamp_provider.exceptions import ServerToAgentException
from opamp_provider.mcptool import register_mcp_transport, register_tool_routes
from opamp_provider.metrics import PROVIDER_METRICS
from opamp_provider.metrics.routes import register_metrics_routes
from opamp_provider.opamp_protocol import (
    build_error_message as protocol_build_error_message,
)
from opamp_provider.opamp_protocol import (
    build_opamp_http_error_response as protocol_build_opamp_http_error_response,
)
from opamp_provider.opamp_protocol import (
    evaluate_non_opamp_http_auth as protocol_evaluate_non_opamp_http_auth,
)
from opamp_provider.opamp_protocol import (
    evaluate_opamp_transport_auth as protocol_evaluate_opamp_transport_auth,
)
from opamp_provider.opamp_protocol import (
    extract_client_id as protocol_extract_client_id,
)
from opamp_provider.opamp_protocol import (
    header_value as protocol_header_value,
)
from opamp_provider.opamp_protocol import (
    log_blocked_agent_attempt as protocol_log_blocked_agent_attempt,
)
from opamp_provider.opamp_protocol import (
    provider_authorization_mode_to_auth_mode as protocol_provider_authorization_mode_to_auth_mode,
)
from opamp_provider.proto import opamp_pb2
from opamp_provider.state import STORE, ClientRecord
from opamp_provider.state_persistence import (
    list_snapshot_files,
    prune_snapshot_files,
    save_state_snapshot,
)
from opamp_provider.transport import decode_message, encode_message
from shared.opamp_config import (
    OPAMP_HTTP_PATH,
    OPAMP_TRANSPORT_HEADER_NONE,
    PB_FIELD_CONNECTION_SETTINGS_REQUEST,
    PB_FIELD_PACKAGE_STATUSES,
    UTF8_ENCODING,
    ServerCapabilities,
)
from shared.security_headers import register_clickjacking_protection

app = Quart("opamp_server")
app.config.setdefault("DIAGNOSTIC_MODE", False)
register_clickjacking_protection(app)
register_tool_routes(app)
# Expose both SSE and streamable HTTP wiring; /mcp itself is still gated at
# request time by provider.allow-mcp so operators can disable direct streamable
# MCP access while keeping the bridge code loaded.
register_mcp_transport(app, transport="both")
logger = logging.getLogger(__name__)
tracemalloc.start()

_ACTIVE_CONFIG_PATH = provider_config.get_effective_config_path()
_REGISTERED_COMPONENT_ENTRY_POINTS, _CONFIGURED_COMPONENT_ENTRY_POINTS = register_provider_component_entries(
    app=app,
    config_path=_ACTIVE_CONFIG_PATH,
    logger=logger,
)
_UI_FEATURE_MENU_ITEMS: list[UiFeatureMenuItem] = ui_menu_items_from_component_entries(
    _CONFIGURED_COMPONENT_ENTRY_POINTS
)
LANDING_PAGE_REDIRECT_URL = (
    "https://htmlpreview.github.io/?https://raw.githubusercontent.com/"
    "opamp-observe/opamp-core/main/github-landingpage/index.html"
)

CONTENT_TYPE_PROTO = "application/x-protobuf"  # Content-Type for protobuf payloads.
LOG_HTTP_MSG = "opamp http AgentToServer:\n%s"  # Log format for HTTP messages.
LOG_WS_MSG = "opamp ws AgentToServer:\n%s"  # Log format for WebSocket messages.
ERR_UNSUPPORTED_HEADER = "unsupported transport header"  # Transport header error text.
LOG_REST_COMMAND = "queued command for client %s classifier=%s action=%s at %s"  # Log format for queued REST-originated commands.
LOG_SEND_COMMAND = "sent command to client %s at %s"  # Log format for command dispatch completion.
OPAMP_HEADER_NONE = OPAMP_TRANSPORT_HEADER_NONE  # Expected transport header value.
# The next two constants are used to build the actual integer capability mask
# that the provider advertises on the wire in OpAMP ServerToAgent payloads.
SERVER_CAPABILITIES_REMOTE_CONFIG = int(
    ServerCapabilities.OffersRemoteConfig
)  # Optional protocol bit added only when provider remote-config support is enabled.
SERVER_CAPABILITIES_EFFECTIVE_CONFIG = int(
    ServerCapabilities.AcceptsEffectiveConfig
)  # Optional protocol bit added only when provider effective-config acceptance is enabled.
SERVER_CAPABILITIES_CONNECTION_SETTINGS = int(
    ServerCapabilities.OffersConnectionSettings
)  # Optional protocol bit added only when provider connection-settings offers are enabled.
SERVER_CAPABILITIES_CONNECTION_SETTINGS_REQUEST = int(
    ServerCapabilities.AcceptsConnectionSettingsRequest
)  # Optional protocol bit added only when provider connection-settings requests are enabled.
SERVER_CAPABILITIES_BASE = int(
    ServerCapabilities.AcceptsStatus
)  # Baseline protocol bitmask always advertised by this provider.
# This tuple is separate from the protocol-mask constants above. It exists for
# UI/presentation purposes so Global Settings can render a stable, ordered,
# human-readable capability list with labels and enabled/disabled state.
SERVER_CAPABILITY_DEFINITIONS = (
    ("accepts_status", "Accepts Status", int(ServerCapabilities.AcceptsStatus)),
    (
        "offers_remote_config",
        "Offers Remote Config",
        int(ServerCapabilities.OffersRemoteConfig),
    ),
    (
        "accepts_effective_config",
        "Accepts Effective Config",
        int(ServerCapabilities.AcceptsEffectiveConfig),
    ),
    ("offers_packages", "Offers Packages", int(ServerCapabilities.OffersPackages)),
    (
        "accepts_packages_status",
        "Accepts Packages Status",
        int(ServerCapabilities.AcceptsPackagesStatus),
    ),
    (
        "offers_connection_settings",
        "Offers Connection Settings",
        int(ServerCapabilities.OffersConnectionSettings),
    ),
    (
        "accepts_connection_settings_request",
        "Accepts Connection Settings Request",
        int(ServerCapabilities.AcceptsConnectionSettingsRequest),
    ),
)  # Ordered capability list shown in Global Settings for provider capability advertisement.
DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 30  # Fallback heartbeat interval for connection settings offers.
CERT_NOT_AFTER_SUFFIX_GMT = " GMT"  # Trailing timezone marker emitted by ssl certificate decoder.
CERT_NOT_AFTER_PARSE_FORMAT = "%b %d %H:%M:%S %Y"  # Datetime parse format for decoded certificate notAfter values.
TLS_EXPIRY_WARNING_DAYS = 30  # Number of days before expiry to highlight certificate warning state.
COMMAND_RESTART = "restart"  # Standard OpAMP restart command action name.
COMMAND_FORCE_RESYNC = "forceresync"  # Custom action name used to trigger full state resync.
COMMAND_CHATOP = "chatopcommand"  # Custom action name for ChatOps command dispatch.
COMMAND_SHUTDOWN_AGENT = "shutdownagent"  # Custom action name for remote shutdown requests.
COMMAND_NULLCOMMAND = "nullcommand"  # Custom no-op action used for testing command plumbing.
CLASSIFIER_COMMAND = "command"  # Classifier used for standard OpAMP commands.
CLASSIFIER_CUSTOM_COMMAND = "custom_command"  # Classifier used for provider custom command routing.
CLASSIFIER_CUSTOM = "custom"  # Alternate classifier value emitted by some custom command builders.
CHANNEL_HTTP = "HTTP"  # Client channel label for HTTP transport.
CHANNEL_WEBSOCKET = "websocket"  # Client channel label for WebSocket transport.
ACTION_APPLY_CONFIG = "apply_config"  # Next-action token to build remote_config payload.
ACTION_CHANGE_CONNECTIONS = "change_connections"  # Next-action token to build connection settings payload.
ACTION_PACKAGE_AVAILABLE = "package_availabe"  # Next-action token to build packages available payload.
ACTION_COMMAND_AGENT = "command_agent"  # Next-action token to send an OpAMP standard command.
ACTION_CUSTOM_AGENT_COMMAND = "custom_agent_command"  # Next-action token to send a custom capability command.
CLIENT_REMOTE_CONFIG_CAPABILITY = "Accepts Remote Config"  # Human-readable capability required for AgentRemoteConfig offers.
ERR_REMOTE_CONFIG_DISABLED = "remote config is disabled by provider configuration"
# Allowed next-action values accepted by /rest/nextAction.
ACTION_OPTIONS = {
    ACTION_APPLY_CONFIG,
    ACTION_CHANGE_CONNECTIONS,
    ACTION_PACKAGE_AVAILABLE,
    ACTION_COMMAND_AGENT,
    ACTION_CUSTOM_AGENT_COMMAND,
}
_WEBSOCKET_CLIENTS: dict[object, str | None] = {}  # Active websocket -> client_id mapping.
_PERSISTENCE_TRACKER = PersistenceTracker()
ERR_AGENT_PENDING_APPROVAL = "agent pending approval"
ERR_AGENT_BLOCKED = "agent is blocked"
ERR_AGENT_AUTH_FAILED = "agent authentication failed"
ERR_OPAMP_AUTH_CONFIG_INVALID = "invalid opamp-use-authorization configuration"
ERR_UI_AUTH_CONFIG_INVALID = "invalid ui-use-authorization configuration"


@app.errorhandler(HTTPStatus.NOT_FOUND)
async def redirect_unknown_provider_route(_: HTTPException) -> Response:
    """Redirect unknown provider routes to the shared project landing page."""
    logger.info(
        "provider 404 redirect path=%s remote_addr=%s target=%s",
        request.path,
        request.remote_addr,
        LANDING_PAGE_REDIRECT_URL,
    )
    return redirect(LANDING_PAGE_REDIRECT_URL)

def set_state_restore_status(status: str, detail: str = "") -> None:
    """Record persisted-state restore status for diagnostics and logs."""
    _PERSISTENCE_TRACKER.set_state_restore_status(status, detail)


def _record_snapshot_status(
    *,
    status: str,
    path: str | None,
    reason: str,
    at: datetime | None = None,
) -> None:
    """Record latest snapshot save status for diagnostics."""
    _PERSISTENCE_TRACKER.record_snapshot_status(
        status=status,
        path=path,
        reason=reason,
        at=at,
    )


def _is_heartbeat_only_message(agent_msg: opamp_pb2.AgentToServer) -> bool:
    """Return whether AgentToServer payload only contains instance_uid/sequence_num."""
    return _PERSISTENCE_TRACKER.is_heartbeat_only_message(agent_msg)


def _save_state_snapshot(reason: str) -> None:
    """Save one persisted-state snapshot if persistence is enabled."""
    _PERSISTENCE_TRACKER.save_state_snapshot(
        reason=reason,
        store=STORE,
        persistence=provider_config.CONFIG.state_persistence,
        logger=logger,
    )


def _note_non_heartbeat_state_change_and_maybe_autosave() -> None:
    """Track non-heartbeat state change timing and run autosave checks."""
    _PERSISTENCE_TRACKER.note_non_heartbeat_state_change_and_maybe_autosave(
        store=STORE,
        persistence=provider_config.CONFIG.state_persistence,
        logger=logger,
    )


def _state_snapshot_file_count() -> int:
    """Return count of snapshot files currently present for configured prefix."""
    try:
        prefix = provider_config.CONFIG.state_persistence.state_file_prefix
        return len(list_snapshot_files(prefix))
    except Exception as exc:
        logger.warning("failed counting state snapshot files", exc_info=exc)
        return 0


async def _shutdown_after_response() -> None:
    """Delay briefly to flush responses before shutting down."""
    await asyncio.sleep(0.2)
    _request_process_shutdown()


@app.errorhandler(Exception)
async def handle_unexpected_error(error: Exception) -> ResponseReturnValue:
    """Return JSON for unexpected errors while preserving HTTPException behavior."""
    if isinstance(error, HTTPException):
        return error
    logger.exception("Unhandled app error", exc_info=error)
    return jsonify({"error": "internal server error"}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.before_request
async def enforce_bearer_auth() -> ResponseReturnValue | None:
    """Apply non-OpAMP bearer-token auth using provider.ui-use-authorization."""
    if request.path == OPAMP_HTTP_PATH:
        return None
    decision = _evaluate_non_opamp_http_auth(
        path=request.path,
        method=request.method,
        authorization_header=request.headers.get("Authorization"),
        remote_addr=request.remote_addr,
    )
    if decision.allowed:
        return None
    response = jsonify({"error": decision.error})
    if decision.status_code == HTTPStatus.UNAUTHORIZED:
        response.headers["WWW-Authenticate"] = provider_auth.WWW_AUTHENTICATE_BEARER
    return response, decision.status_code


def _extract_client_id(agent_msg: opamp_pb2.AgentToServer) -> str:
    """Return hex-encoded instance UID when present; otherwise an empty string."""
    return protocol_extract_client_id(agent_msg)


def _request_header_map() -> dict[str, str]:
    """Return request headers as a plain dictionary for audit logging/auth checks."""
    return {str(key): str(value) for key, value in request.headers.items()}


def _websocket_header_map() -> dict[str, str]:
    """Return websocket handshake headers as a plain dictionary."""
    return {str(key): str(value) for key, value in websocket.headers.items()}


def _websocket_remote_addr() -> str | None:
    """Return websocket remote address when available."""
    client_info = getattr(websocket, "client", None)
    if isinstance(client_info, tuple) and client_info:
        return str(client_info[0])
    return None


def _diagnostic_mode_enabled() -> bool:
    """Return whether server diagnostic mode is enabled."""
    return bool(app.config.get("DIAGNOSTIC_MODE", False))


def _provider_allows_remote_config() -> bool:
    """Return whether provider configuration enables remote-config UI and queueing support."""
    return provider_config.CONFIG.allow_remote_config is True


def _provider_allows_effective_config() -> bool:
    """Return whether provider configuration advertises effective-config support."""
    return provider_config.CONFIG.allow_effective_config is True


def _provider_allows_connection_settings() -> bool:
    """Return whether provider configuration advertises connection-settings offers."""
    return provider_config.CONFIG.allow_connection_settings is True


def _provider_allows_connection_settings_request() -> bool:
    """Return whether provider configuration advertises connection-settings requests."""
    return provider_config.CONFIG.allow_connection_settings_request is True


def _server_capabilities_mask() -> int:
    """Return the effective protocol bitmask advertised to OpAMP agents."""
    mask = SERVER_CAPABILITIES_BASE
    if _provider_allows_remote_config():
        mask |= SERVER_CAPABILITIES_REMOTE_CONFIG
    if _provider_allows_effective_config():
        mask |= SERVER_CAPABILITIES_EFFECTIVE_CONFIG
    if _provider_allows_connection_settings():
        mask |= SERVER_CAPABILITIES_CONNECTION_SETTINGS
    if _provider_allows_connection_settings_request():
        mask |= SERVER_CAPABILITIES_CONNECTION_SETTINGS_REQUEST
    return mask


def _advertised_server_capabilities() -> list[dict[str, object]]:
    """Return UI-ready capability rows derived from the protocol bitmask."""
    mask = _server_capabilities_mask()
    return [
        {
            "key": key,
            "label": label,
            "enabled": bool(mask & bitmask),
        }
        for key, label, bitmask in SERVER_CAPABILITY_DEFINITIONS
    ]


_SERVER_TO_AGENT_RESPONSE_BUILDER = ServerToAgentResponseBuilder(
    store=STORE,
    logger=logger,
    server_capabilities_mask=_server_capabilities_mask,
    get_custom_capabilities_list=get_custom_capabilities_list,
    command_object_factory=command_object_factory,
    channel_http=CHANNEL_HTTP,
    action_apply_config=ACTION_APPLY_CONFIG,
    action_change_connections=ACTION_CHANGE_CONNECTIONS,
    action_package_available=ACTION_PACKAGE_AVAILABLE,
    action_command_agent=ACTION_COMMAND_AGENT,
    action_custom_agent_command=ACTION_CUSTOM_AGENT_COMMAND,
    classifier_command=CLASSIFIER_COMMAND,
    classifier_custom_command=CLASSIFIER_CUSTOM_COMMAND,
    classifier_custom=CLASSIFIER_CUSTOM,
    command_restart=COMMAND_RESTART,
    command_force_resync=COMMAND_FORCE_RESYNC,
    default_heartbeat_interval_seconds=DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
)
COMMAND_BUILDERS = {
    (CLASSIFIER_COMMAND, COMMAND_RESTART): (
        _SERVER_TO_AGENT_RESPONSE_BUILDER._build_restart_command
    ),
    (CLASSIFIER_COMMAND, COMMAND_FORCE_RESYNC): (
        _SERVER_TO_AGENT_RESPONSE_BUILDER._build_force_resync_command
    ),
    (CLASSIFIER_CUSTOM, "*"): (
        _SERVER_TO_AGENT_RESPONSE_BUILDER._build_custom_command_payload
    ),
    (CLASSIFIER_CUSTOM_COMMAND, "*"): (
        _SERVER_TO_AGENT_RESPONSE_BUILDER._build_custom_command_payload
    ),
}  # Routing map retained for queue-command validation and dispatch compatibility.


def _coerce_bool_setting(value: object, *, key: str) -> bool:
    """Coerce UI/API boolean payload values for settings endpoints."""
    return coerce_bool_setting(value, key=key)


def _load_tls_certificate_expiry_utc(cert_file: str) -> datetime | None:
    """Load certificate expiry timestamp in UTC from a PEM certificate file."""
    try:
        cert_data = ssl._ssl._test_decode_cert(cert_file)
    except Exception as exc:
        logger.warning(
            "failed to decode provider tls cert file %s", cert_file, exc_info=exc
        )
        return None
    not_after_raw = cert_data.get("notAfter")
    if not isinstance(not_after_raw, str) or not not_after_raw.strip():
        return None
    normalized_not_after = not_after_raw.strip()
    if normalized_not_after.endswith(CERT_NOT_AFTER_SUFFIX_GMT):
        normalized_not_after = normalized_not_after[: -len(CERT_NOT_AFTER_SUFFIX_GMT)]
    normalized_not_after = " ".join(normalized_not_after.split())
    try:
        parsed = datetime.strptime(normalized_not_after, CERT_NOT_AFTER_PARSE_FORMAT)
    except ValueError:
        logger.warning(
            "failed to parse provider tls cert notAfter value %r",
            not_after_raw,
        )
        return None
    return parsed.replace(tzinfo=timezone.utc)


def _tls_certificate_expiry_metadata(
    *,
    now_utc: datetime | None = None,
) -> dict[str, object]:
    """Build TLS certificate-expiry metadata for global settings responses."""
    tls_config = provider_config.CONFIG.tls
    if tls_config is None:
        return {
            "tls_enabled": False,
            "https_certificate_expiry_date": None,
            "https_certificate_days_remaining": None,
            "https_certificate_expiring_soon": False,
        }
    expiry_utc = _load_tls_certificate_expiry_utc(tls_config.cert_file)
    if expiry_utc is None:
        return {
            "tls_enabled": True,
            "https_certificate_expiry_date": None,
            "https_certificate_days_remaining": None,
            "https_certificate_expiring_soon": False,
        }
    now = now_utc or datetime.now(timezone.utc)
    days_remaining = (expiry_utc.date() - now.date()).days
    return {
        "tls_enabled": True,
        "https_certificate_expiry_date": expiry_utc.date().isoformat(),
        "https_certificate_days_remaining": days_remaining,
        "https_certificate_expiring_soon": days_remaining <= TLS_EXPIRY_WARNING_DAYS,
    }


def _header_value(
    *,
    headers: dict[str, str],
    name: str,
) -> str | None:
    """Return a case-insensitive header value from a plain header dictionary."""
    return protocol_header_value(headers=headers, name=name)


def _provider_authorization_mode_to_auth_mode(
    provider_mode: str,
) -> str | None:
    """Map provider config authorization values to auth module mode."""
    return protocol_provider_authorization_mode_to_auth_mode(provider_mode)


def _evaluate_opamp_transport_auth(
    *,
    headers: dict[str, str],
    remote_addr: str | None,
    channel: str,
) -> provider_auth.AuthDecision:
    """Authorize OpAMP transport requests using provider config mode."""
    return protocol_evaluate_opamp_transport_auth(
        headers=headers,
        remote_addr=remote_addr,
        channel=channel,
        opamp_http_path=OPAMP_HTTP_PATH,
        invalid_config_error=ERR_OPAMP_AUTH_CONFIG_INVALID,
    )


def _evaluate_non_opamp_http_auth(
    *,
    path: str,
    method: str,
    authorization_header: str | None,
    remote_addr: str | None,
) -> provider_auth.AuthDecision:
    """Authorize non-OpAMP HTTP requests using provider.ui-use-authorization."""
    return protocol_evaluate_non_opamp_http_auth(
        path=path,
        method=method,
        authorization_header=authorization_header,
        remote_addr=remote_addr,
        invalid_config_error=ERR_UI_AUTH_CONFIG_INVALID,
    )


def _build_error_message(
    *,
    instance_uid: bytes | None,
    error_message: str,
    error_type: opamp_pb2.ServerErrorResponseType = (
        opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest
    ),
) -> opamp_pb2.ServerToAgent:
    """Build a ServerToAgent error payload without requiring prior response state."""
    _log_opamp_error_message(
        instance_uid=instance_uid,
        error_message=error_message,
        error_type=error_type,
    )
    return protocol_build_error_message(
        instance_uid=instance_uid,
        error_message=error_message,
        error_type=error_type,
    )


def _build_opamp_http_error_response(
    *,
    instance_uid: bytes | None,
    status_code: int,
    error_message: str,
    headers: dict[str, str] | None = None,
    error_type: opamp_pb2.ServerErrorResponseType = (
        opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest
    ),
) -> Response:
    """Build a protobuf HTTP response carrying a ServerToAgent error payload."""
    _log_opamp_error_message(
        instance_uid=instance_uid,
        error_message=error_message,
        error_type=error_type,
        status_code=status_code,
        channel=CHANNEL_HTTP,
    )
    return protocol_build_opamp_http_error_response(
        instance_uid=instance_uid,
        status_code=status_code,
        error_message=error_message,
        headers=headers,
        error_type=error_type,
    )


def _opamp_error_type_name(
    error_type: opamp_pb2.ServerErrorResponseType,
) -> str:
    """Return a readable enum label for one OpAMP ServerErrorResponseType value."""
    try:
        return opamp_pb2.ServerErrorResponseType.Name(int(error_type))
    except ValueError:
        return str(int(error_type))


def _log_opamp_error_message(
    *,
    instance_uid: bytes | None,
    error_message: str,
    error_type: opamp_pb2.ServerErrorResponseType,
    status_code: int | None = None,
    channel: str | None = None,
) -> None:
    """Log one OpAMP error payload with enough context to diagnose the failure."""
    log_level = (
        logging.ERROR
        if (
            int(error_type)
            == opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_Unavailable
            or (status_code is not None and status_code >= HTTPStatus.INTERNAL_SERVER_ERROR)
        )
        else logging.WARNING
    )
    logger.log(
        log_level,
        (
            "opamp error response channel=%s status_code=%s error_type=%s "
            "instance_uid=%s error_message=%s"
        ),
        channel or "unspecified",
        int(status_code) if status_code is not None else "-",
        _opamp_error_type_name(error_type),
        instance_uid.hex() if instance_uid else "missing",
        error_message,
    )


def _log_blocked_agent_attempt(
    *,
    client_id: str,
    channel: str,
    headers: dict[str, str],
    remote_addr: str | None,
) -> None:
    """Log one blocked-agent request with headers for audit visibility."""
    protocol_log_blocked_agent_attempt(
        client_id=client_id,
        channel=channel,
        headers=headers,
        remote_addr=remote_addr,
        logger=logger,
    )


def _build_error(
    msg: opamp_pb2.ServerToAgent,
    error_type: opamp_pb2.ServerErrorResponseType = (
        opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest
    ),
    error_message: str = "Bad Request",
) -> opamp_pb2.ServerToAgent:
    """Build an error response and append error details to the message."""
    response = msg
    if not response.instance_uid:
        raise ServerToAgentException("no instance UID set")

    if not response.error_response:
        response.error_response = opamp_pb2.ErrorResponseType

    response.error_response.type = error_type

    if not response.error_response.error_message:
        response.error_response.error_message = error_message
    else:
        response.error_response.error_message = (
            response.error_response.error_message + "\n" + error_message
        )

    if (
        error_type
        == opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_Unavailable
    ):
        retry_ns = int(provider_config.CONFIG.retry_after_seconds) * 1_000_000_000
        response.error_response.retry_info.retry_after_nanoseconds = retry_ns

    _log_opamp_error_message(
        instance_uid=response.instance_uid if response.instance_uid else None,
        error_message=response.error_response.error_message,
        error_type=error_type,
    )
    return response


def _unsupported_agent_fields(agent_msg: opamp_pb2.AgentToServer) -> list[str]:
    """Return unsupported top-level AgentToServer fields currently rejected by server."""
    unsupported: list[str] = []
    if agent_msg.HasField(PB_FIELD_PACKAGE_STATUSES):
        unsupported.append(PB_FIELD_PACKAGE_STATUSES)
    if agent_msg.HasField(PB_FIELD_CONNECTION_SETTINGS_REQUEST):
        unsupported.append(PB_FIELD_CONNECTION_SETTINGS_REQUEST)
    return unsupported


def _build_http_auth_error_response(
    *,
    agent_msg: opamp_pb2.AgentToServer,
    auth_decision: provider_auth.AuthDecision,
) -> Response:
    """Build an OpAMP HTTP auth error response with expected headers and type."""
    response_headers: dict[str, str] = {}
    if auth_decision.status_code == HTTPStatus.UNAUTHORIZED:
        response_headers["WWW-Authenticate"] = (
            provider_auth.WWW_AUTHENTICATE_BEARER
        )
    error_type = (
        opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_Unavailable
        if auth_decision.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR
        else opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest
    )
    return _build_opamp_http_error_response(
        instance_uid=agent_msg.instance_uid if agent_msg.instance_uid else None,
        status_code=auth_decision.status_code,
        error_message=auth_decision.error or ERR_AGENT_AUTH_FAILED,
        headers=response_headers,
        error_type=error_type,
    )


def _build_http_unsupported_fields_response(
    *,
    agent_msg: opamp_pb2.AgentToServer,
    unsupported_fields: list[str],
) -> Response:
    """Build a protobuf HTTP bad-request response for unsupported AgentToServer fields."""
    response_msg = opamp_pb2.ServerToAgent()
    response_msg.instance_uid = agent_msg.instance_uid
    response_msg = _build_error(
        error_type=opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest,
        error_message=(f"unsupported fields: {', '.join(unsupported_fields)}"),
        msg=response_msg,
    )
    return Response(
        response_msg.SerializeToString(),
        content_type=CONTENT_TYPE_PROTO,
        status=HTTPStatus.BAD_REQUEST,
    )


def _http_human_in_loop_gate_response(
    *,
    agent_msg: opamp_pb2.AgentToServer,
    client_id: str | None,
    known_client: ClientRecord | None,
    request_headers: dict[str, str],
    remote_addr: str | None,
) -> Response | None:
    """Return an approval-gate response when the agent is not yet approved."""
    if not provider_config.CONFIG.human_in_loop_approval:
        return None
    if not client_id:
        return _build_opamp_http_error_response(
            instance_uid=None,
            status_code=HTTPStatus.BAD_REQUEST,
            error_message="instance_uid is required when human_in_loop_approval is enabled",
        )
    if known_client is not None:
        return None
    if STORE.get_pending_approval(client_id) is None:
        try:
            STORE.add_pending_approval_from_agent_msg(
                agent_msg,
                channel=CHANNEL_HTTP,
                remote_addr=remote_addr,
            )
            logger.info(
                "agent moved to pending approval client_id=%s remote_addr=%s",
                client_id,
                remote_addr or "unknown",
            )
        except Exception as approval_error:
            STORE.block_agent(
                client_id,
                reason=f"failed pending approval payload transformation: {approval_error}",
                headers=request_headers,
                ip=remote_addr,
            )
            logger.exception(
                "failed to transform pending approval payload; client blocked client_id=%s",
                client_id,
                exc_info=approval_error,
            )
            return _build_opamp_http_error_response(
                instance_uid=agent_msg.instance_uid if agent_msg.instance_uid else None,
                status_code=HTTPStatus.FORBIDDEN,
                error_message=ERR_AGENT_BLOCKED,
                error_type=opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest,
            )
    return _build_opamp_http_error_response(
        instance_uid=agent_msg.instance_uid if agent_msg.instance_uid else None,
        status_code=HTTPStatus.FORBIDDEN,
        error_message=ERR_AGENT_PENDING_APPROVAL,
        error_type=opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest,
    )


def _build_http_success_response(
    *,
    agent_msg: opamp_pb2.AgentToServer,
    remote_addr: str | None,
) -> Response:
    """Persist one HTTP agent message, build response, and mark commands sent."""
    client = STORE.upsert_from_agent_msg(
        agent_msg,
        channel=CHANNEL_HTTP,
        remote_addr=remote_addr,
    )
    if not _is_heartbeat_only_message(agent_msg):
        _note_non_heartbeat_state_change_and_maybe_autosave()
    pending_command = STORE.next_pending_command(client.client_id)
    response_msg = _SERVER_TO_AGENT_RESPONSE_BUILDER.build_response(
        agent_msg,
        pending_command,
        client=client,
        channel=CHANNEL_HTTP,
    )
    if pending_command is not None and _SERVER_TO_AGENT_RESPONSE_BUILDER.has_dispatched_command_payload(
        response_msg
    ):
        STORE.mark_command_sent(client.client_id, pending_command)
        logger.info(LOG_SEND_COMMAND, client.client_id, datetime.now(timezone.utc))
    return Response(response_msg.SerializeToString(), content_type=CONTENT_TYPE_PROTO)


def _build_websocket_auth_error_message(
    auth_decision: provider_auth.AuthDecision,
) -> opamp_pb2.ServerToAgent:
    """Build an auth error ServerToAgent message for websocket handshakes."""
    error_type = (
        opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_Unavailable
        if auth_decision.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR
        else opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest
    )
    return _build_error_message(
        instance_uid=None,
        error_type=error_type,
        error_message=auth_decision.error or ERR_AGENT_AUTH_FAILED,
    )


async def _send_websocket_error_and_close(
    response_msg: opamp_pb2.ServerToAgent,
) -> None:
    """Send one websocket error response and close with policy-violation code."""
    await websocket.send(encode_message(response_msg.SerializeToString()))
    await websocket.close(code=1008)


def _websocket_human_in_loop_gate(
    *,
    agent_msg: opamp_pb2.AgentToServer,
    client_id: str | None,
    known_client: ClientRecord | None,
    ws_headers: dict[str, str],
    remote_addr: str | None,
) -> tuple[opamp_pb2.ServerToAgent | None, bool]:
    """Evaluate websocket approval gate and return response + close flag when blocked."""
    if not provider_config.CONFIG.human_in_loop_approval:
        return None, False
    if not client_id:
        return (
            _build_error_message(
                instance_uid=None,
                error_type=opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest,
                error_message="instance_uid is required when human_in_loop_approval is enabled",
            ),
            True,
        )
    if known_client is not None:
        return None, False
    if STORE.get_pending_approval(client_id) is None:
        try:
            STORE.add_pending_approval_from_agent_msg(
                agent_msg,
                channel=CHANNEL_WEBSOCKET,
                remote_addr=remote_addr,
            )
            logger.info(
                "agent moved to pending approval client_id=%s remote_addr=%s",
                client_id,
                remote_addr or "unknown",
            )
        except Exception as approval_error:
            STORE.block_agent(
                client_id,
                reason=(
                    "failed pending approval payload "
                    f"transformation: {approval_error}"
                ),
                headers=ws_headers,
                ip=remote_addr,
            )
            logger.exception(
                (
                    "failed to transform pending approval payload; "
                    "client blocked client_id=%s"
                ),
                client_id,
                exc_info=approval_error,
            )
            return (
                _build_error_message(
                    instance_uid=agent_msg.instance_uid if agent_msg.instance_uid else None,
                    error_type=opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest,
                    error_message=ERR_AGENT_BLOCKED,
                ),
                True,
            )
    return (
        _build_error_message(
            instance_uid=agent_msg.instance_uid if agent_msg.instance_uid else None,
            error_type=opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest,
            error_message=ERR_AGENT_PENDING_APPROVAL,
        ),
        True,
    )


def _process_websocket_agent_message(
    *,
    agent_msg: opamp_pb2.AgentToServer,
    ws_headers: dict[str, str],
    remote_addr: str | None,
) -> tuple[opamp_pb2.ServerToAgent, CommandRecord | None, ClientRecord | None, bool]:
    """Process one decoded websocket AgentToServer message and return response context."""
    pending_command = None
    client = None
    close_after_send = False
    client_id = _extract_client_id(agent_msg)

    if client_id and STORE.is_blocked_agent(client_id):
        _log_blocked_agent_attempt(
            client_id=client_id,
            channel=CHANNEL_WEBSOCKET,
            headers=ws_headers,
            remote_addr=remote_addr,
        )
        return (
            _build_error_message(
                instance_uid=agent_msg.instance_uid if agent_msg.instance_uid else None,
                error_type=opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest,
                error_message=ERR_AGENT_BLOCKED,
            ),
            pending_command,
            client,
            True,
        )

    known_client = STORE.get(client_id) if client_id else None
    approval_response, close_after_send = _websocket_human_in_loop_gate(
        agent_msg=agent_msg,
        client_id=client_id,
        known_client=known_client,
        ws_headers=ws_headers,
        remote_addr=remote_addr,
    )
    if approval_response is not None:
        return approval_response, pending_command, client, close_after_send

    client = STORE.upsert_from_agent_msg(
        agent_msg,
        channel=CHANNEL_WEBSOCKET,
        remote_addr=remote_addr,
    )
    if not _is_heartbeat_only_message(agent_msg):
        _note_non_heartbeat_state_change_and_maybe_autosave()
    _WEBSOCKET_CLIENTS[websocket] = client.client_id
    pending_command = STORE.next_pending_command(client.client_id)
    response_msg = _SERVER_TO_AGENT_RESPONSE_BUILDER.build_response(
        agent_msg,
        pending_command,
        client=client,
        channel=CHANNEL_WEBSOCKET,
    )
    return response_msg, pending_command, client, False


@app.post(OPAMP_HTTP_PATH)
async def opamp_http() -> Response:
    """Handle OpAMP HTTP POST requests."""
    try:
        data = await request.get_data()
        agent_msg = opamp_pb2.AgentToServer()
        if data:
            agent_msg.ParseFromString(data)

        logger.info(LOG_HTTP_MSG, text_format.MessageToString(agent_msg))
        client_id = _extract_client_id(agent_msg)
        request_headers = _request_header_map()
        remote_addr = request.remote_addr

        if client_id and STORE.is_blocked_agent(client_id):
            _log_blocked_agent_attempt(
                client_id=client_id,
                channel=CHANNEL_HTTP,
                headers=request_headers,
                remote_addr=remote_addr,
            )
            return _build_opamp_http_error_response(
                instance_uid=agent_msg.instance_uid if agent_msg.instance_uid else None,
                status_code=HTTPStatus.FORBIDDEN,
                error_message=ERR_AGENT_BLOCKED,
                error_type=opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest,
            )

        opamp_auth_decision = _evaluate_opamp_transport_auth(
            headers=request_headers,
            remote_addr=remote_addr,
            channel=CHANNEL_HTTP,
        )
        if not opamp_auth_decision.allowed:
            return _build_http_auth_error_response(
                agent_msg=agent_msg,
                auth_decision=opamp_auth_decision,
            )

        known_client = STORE.get(client_id) if client_id else None
        approval_response = _http_human_in_loop_gate_response(
            agent_msg=agent_msg,
            client_id=client_id,
            known_client=known_client,
            request_headers=request_headers,
            remote_addr=remote_addr,
        )
        if approval_response is not None:
            return approval_response

        unsupported = _unsupported_agent_fields(agent_msg)
        if unsupported:
            return _build_http_unsupported_fields_response(
                agent_msg=agent_msg,
                unsupported_fields=unsupported,
            )
        return _build_http_success_response(
            agent_msg=agent_msg,
            remote_addr=remote_addr,
        )
    except Exception as exc:
        logger.exception("Unhandled HTTP error - %s", exc_info=exc)
        response_msg = _build_error_message(
            instance_uid=None,
            error_type=opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_Unavailable,
            error_message="internal server error",
        )
        payload = response_msg.SerializeToString()
        return Response(
            payload,
            content_type=CONTENT_TYPE_PROTO,
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@app.websocket(OPAMP_HTTP_PATH)
async def opamp_websocket() -> None:
    """Handle OpAMP WebSocket connections."""
    _WEBSOCKET_CLIENTS[websocket] = None
    ws_headers = _websocket_header_map()
    remote_addr = _websocket_remote_addr()
    try:
        opamp_auth_decision = _evaluate_opamp_transport_auth(
            headers=ws_headers,
            remote_addr=remote_addr,
            channel=CHANNEL_WEBSOCKET,
        )
        if not opamp_auth_decision.allowed:
            await _send_websocket_error_and_close(
                _build_websocket_auth_error_message(opamp_auth_decision)
            )
            return

        while True:
            pending_command = None
            client = None
            close_after_send = False
            agent_msg = opamp_pb2.AgentToServer()
            data = await websocket.receive()
            if isinstance(data, str):
                data = data.encode(UTF8_ENCODING)
            try:
                header, payload = decode_message(data)
                if header != OPAMP_HEADER_NONE:
                    response_msg = _build_error_message(
                        instance_uid=None,
                        error_type=opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest,
                        error_message=ERR_UNSUPPORTED_HEADER,
                    )
                else:
                    if payload:
                        agent_msg.ParseFromString(payload)
                    logger.info(LOG_WS_MSG, text_format.MessageToString(agent_msg))
                    (
                        response_msg,
                        pending_command,
                        client,
                        close_after_send,
                    ) = _process_websocket_agent_message(
                        agent_msg=agent_msg,
                        ws_headers=ws_headers,
                        remote_addr=remote_addr,
                    )
            except ValueError as exc:
                logger.warning("OpAMP websocket value error: %s", exc)
                response_msg = _build_error_message(
                    instance_uid=(
                        agent_msg.instance_uid if agent_msg.instance_uid else None
                    ),
                    error_type=opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_BadRequest,
                    error_message=str(exc),
                )
            except Exception as exc:
                logger.exception("Unhandled websocket error", exc_info=exc)
                response_msg = _build_error_message(
                    instance_uid=(
                        agent_msg.instance_uid if agent_msg.instance_uid else None
                    ),
                    error_type=opamp_pb2.ServerErrorResponseType.ServerErrorResponseType_Unavailable,
                    error_message="internal server error",
                )

            out_payload = response_msg.SerializeToString()
            await websocket.send(encode_message(out_payload))
            if pending_command is not None and _SERVER_TO_AGENT_RESPONSE_BUILDER.has_dispatched_command_payload(
                response_msg
            ):
                if client is not None:
                    STORE.mark_command_sent(client.client_id, pending_command)
                    logger.info(
                        LOG_SEND_COMMAND, client.client_id, datetime.now(timezone.utc)
                    )
            if close_after_send:
                await websocket.close(code=1008)
                break
    finally:
        _WEBSOCKET_CLIENTS.pop(websocket, None)


async def _close_websockets() -> None:
    """Close all active WebSocket connections."""
    if not _WEBSOCKET_CLIENTS:
        return

    async def _close_one(web_socket: object, client_id: str | None) -> None:
        try:
            await web_socket.close(code=1001)
            if client_id:
                logger.info("closed websocket for client %s", client_id)
            else:
                logger.info("closed websocket for unknown client")
        except Exception as err:
            logger.warning(
                "failed to close websocket for client %s - %s", client_id, err
            )

    await asyncio.gather(
        *[
            _close_one(web_socket, client_id)
            for web_socket, client_id in list(_WEBSOCKET_CLIENTS.items())
            if web_socket is not None
        ],
        return_exceptions=True,
    )


@app.after_serving
async def _finalize_server() -> None:
    """Finalizer to cleanly close WebSocket connections on shutdown."""
    await _close_websockets()
    _save_state_snapshot("graceful_shutdown")


_UI_ASSETS = load_provider_ui_assets(logger=logger)
register_ui_routes(
    app,
    ui_assets=_UI_ASSETS,
    provider_config=provider_config,
    global_settings_help=GLOBAL_SETTINGS_HELP,
    render_help_html=render_help_html,
    component_version_text=component_version_text,
    ui_feature_menu_items=_UI_FEATURE_MENU_ITEMS,
    registered_component_entry_points=_REGISTERED_COMPONENT_ENTRY_POINTS,
)
register_settings_routes(
    app,
    provider_config=provider_config,
    store=STORE,
    logger=logger,
    persistence_tracker=_PERSISTENCE_TRACKER,
    diagnostic_mode_enabled=_diagnostic_mode_enabled,
    state_snapshot_file_count=_state_snapshot_file_count,
    tls_certificate_expiry_metadata=_tls_certificate_expiry_metadata,
    record_snapshot_status=_record_snapshot_status,
    coerce_bool_setting=_coerce_bool_setting,
    advertised_server_capabilities=_advertised_server_capabilities,
    save_state_snapshot_func=lambda **kwargs: save_state_snapshot(**kwargs),
    prune_snapshot_files_func=lambda **kwargs: prune_snapshot_files(**kwargs),
)
register_metrics_routes(
    app,
    provider_config=provider_config,
    metrics_registry=PROVIDER_METRICS,
    store=STORE,
)
register_client_routes(
    app,
    provider_config=provider_config,
    store=STORE,
    logger=logger,
    model_dump_mode=MODEL_DUMP_MODE,
    command_builders=COMMAND_BUILDERS,
    action_options=ACTION_OPTIONS,
    action_apply_config=ACTION_APPLY_CONFIG,
    action_change_connections=ACTION_CHANGE_CONNECTIONS,
    client_remote_config_capability=CLIENT_REMOTE_CONFIG_CAPABILITY,
    remote_config_disabled_error=ERR_REMOTE_CONFIG_DISABLED,
    diagnostic_mode_enabled=_diagnostic_mode_enabled,
    close_websockets=_close_websockets,
    shutdown_after_response=_shutdown_after_response,
    coerce_bool_setting=_coerce_bool_setting,
)
