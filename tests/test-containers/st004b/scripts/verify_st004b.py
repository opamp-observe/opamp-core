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

"""Verify one ST-004B authorization or TLS profile and retain evidence."""

# One verifier keeps the seven profile reports structurally identical.
# pylint: disable=too-many-lines

from __future__ import annotations

import argparse
import json
import ssl
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path
from typing import Any

SCENARIO_LABEL = "ST-004B"
DEFAULT_BASE_URL = "http://127.0.0.1:18084"
DEFAULT_ISSUER_URL = "http://127.0.0.1:18085"
DEFAULT_HTTP_TIMEOUT_SECONDS = 5.0
DEFAULT_VERIFY_TIMEOUT_SECONDS = 120.0
POLL_INTERVAL_SECONDS = 1.0
ROUTE_BODY_EVIDENCE_LIMIT = 1000

PROFILE_NO_AUTH = "no-auth"
PROFILE_STATIC_OPAMP = "static-opamp"
PROFILE_STATIC_UI = "static-ui"
PROFILE_STATIC_BOTH = "static-both"
PROFILE_MCP_DISABLED = "mcp-disabled"
PROFILE_JWT_NEGATIVE = "jwt-negative"
PROFILE_TLS = "tls"
SUPPORTED_PROFILES = (
    PROFILE_NO_AUTH,
    PROFILE_STATIC_OPAMP,
    PROFILE_STATIC_UI,
    PROFILE_STATIC_BOTH,
    PROFILE_MCP_DISABLED,
    PROFILE_JWT_NEGATIVE,
    PROFILE_TLS,
)

API_CLIENTS_ENDPOINT = "/api/clients"
MCP_ENDPOINT = "/mcp"
MESSAGES_ENDPOINT = "/messages"
METRICS_ENDPOINT = "/metrics"
OPAMP_ENDPOINT = "/v1/opamp"
SSE_ENDPOINT = "/sse"
TOOL_ENDPOINT = "/tool/otelAgents"
UI_ENDPOINT = "/ui"
MINT_ENDPOINT = "/mint"

OPAMP_TOKEN = "st004b-opamp-token"
UI_TOKEN = "st004b-ui-token"
WRONG_TOKEN = "st004b-wrong-token"

CASE_VALID = "valid"
CASE_EXPIRED = "expired"
CASE_WRONG_ISSUER = "wrong-issuer"
CASE_WRONG_AUDIENCE = "wrong-audience"
CASE_UNSIGNED = "unsigned"
JWT_REJECTION_CASES = (
    CASE_EXPIRED,
    CASE_WRONG_ISSUER,
    CASE_WRONG_AUDIENCE,
    CASE_UNSIGNED,
)

VALID_INSTANCE_BY_PROFILE = {
    PROFILE_NO_AUTH: "st004b-no-auth-valid",
    PROFILE_STATIC_OPAMP: "st004b-static-opamp-valid",
    PROFILE_STATIC_UI: "st004b-static-ui-valid",
    PROFILE_STATIC_BOTH: "st004b-static-both-valid",
    PROFILE_TLS: "st004b-tls-valid",
}
INVALID_INSTANCE_BY_PROFILE = {
    PROFILE_STATIC_OPAMP: "st004b-static-opamp-invalid",
    PROFILE_TLS: "st004b-tls-invalid",
}

ACCEPT_HEADER = "Accept"
AUTHORIZATION_HEADER = "Authorization"
CONTENT_TYPE_HEADER = "Content-Type"
APPLICATION_JSON = "application/json"
APPLICATION_PROTOBUF = "application/x-protobuf"
MCP_ACCEPT = "application/json, text/event-stream"
UTF_8_ENCODING = "utf-8"
DECODE_ERROR_HANDLER = "replace"

KEY_BODY = "body"
KEY_CHECKS = "checks"
KEY_ERROR = "error"
KEY_EVIDENCE = "evidence"
KEY_EXPECTED = "expected"
KEY_GENERATED_AT = "generated_at_utc"
KEY_NAME = "name"
KEY_PASSED = "passed"  # pragma: allowlist secret -- report status key, not a password
KEY_PROFILE = "profile"
KEY_RESULT = "result"
KEY_STATUS = "status"
KEY_TOKEN = "token"
KEY_VALUE = "value"
KEY_CLIENTS = "clients"
KEY_AGENT_DESCRIPTION = "agent_description"
KEY_CAPABILITIES = "capabilities"
KEY_CASE = "case"
KEY_CLIENT_INFO = "clientInfo"
KEY_ID = "id"
KEY_JSONRPC = "jsonrpc"
KEY_METHOD = "method"
KEY_PARAMS = "params"
KEY_PROTOCOL_VERSION = "protocolVersion"
KEY_VERSION = "version"

MCP_JSONRPC_VERSION = "2.0"
MCP_INITIALIZE_ID = "st004b-init"
MCP_INITIALIZE_METHOD = "initialize"
MCP_PROTOCOL_VERSION = "2025-06-18"
MCP_CLIENT_NAME = "st004b-verifier"
MCP_CLIENT_VERSION = "1.0.0"

PASSED_RESULT = "passed"
FAILED_RESULT = "failed"
REPORT_FILE_NAME = "results.md"
ROUTE_MATRIX_FILE_NAME = "route-matrix.json"
SUMMARY_FILE_NAME = "summary.json"
PROVIDER_LOG_FILE_NAME = "provider.log"
INVALID_CONSUMER_LOG_FILE_NAME = "consumer-invalid.log"


def _utc_now() -> str:
    """Return the current UTC timestamp for generated evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _join_url(base_url: str, endpoint: str) -> str:
    """Join a configured provider base URL to an absolute route.

    Args:
        base_url: Provider or issuer scheme and authority.
        endpoint: Absolute HTTP path to append.
    """
    return f"{base_url.rstrip('/')}{endpoint}"


def _write_json(path: Path, payload: Any) -> None:
    """Write deterministic JSON evidence.

    Args:
        path: Destination file whose parent is created when required.
        payload: JSON-compatible evidence value.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"{json.dumps(payload, indent=2, sort_keys=True)}\n",
        encoding=UTF_8_ENCODING,
    )


def _write_text(path: Path, payload: str) -> None:
    """Write textual log evidence.

    Args:
        path: Destination file whose parent is created when required.
        payload: Text captured from the running Compose profile.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding=UTF_8_ENCODING)


# This transport helper intentionally exposes all request controls used by the matrix.
# pylint: disable-next=too-many-arguments
def _request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    ca_file: Path | None = None,
    timeout: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> tuple[int, str]:
    """Issue one request and normalize HTTP and connection failures.

    Args:
        url: Fully qualified request URL.
        method: HTTP method sent to the route.
        headers: Optional request headers.
        data: Optional request body bytes.
        ca_file: Optional CA file trusted for HTTPS verification.
        timeout: Maximum request duration in seconds.

    Returns:
        Status and decoded body; status zero represents a transport/TLS failure.
    """
    request = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    context = None
    if urlsplit_scheme(url) == "https":
        context = ssl.create_default_context(cafile=str(ca_file) if ca_file else None)
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            body = response.read().decode(UTF_8_ENCODING, errors=DECODE_ERROR_HANDLER)
            return int(response.status), body
    except urllib.error.HTTPError as http_error:
        body = http_error.read().decode(UTF_8_ENCODING, errors=DECODE_ERROR_HANDLER)
        return int(http_error.code), body
    except (OSError, ssl.SSLError, urllib.error.URLError) as transport_error:
        return 0, repr(transport_error)


def urlsplit_scheme(url: str) -> str:
    """Return the lower-case scheme used by a request URL.

    Args:
        url: Fully qualified URL whose scheme is required.
    """
    return urllib.parse.urlsplit(url).scheme.lower()


def _bearer_headers(token: str, *, protobuf: bool = False) -> dict[str, str]:
    """Build bearer headers for JSON/MCP or protobuf requests.

    Args:
        token: Bearer credential sent to the provider.
        protobuf: Select the OpAMP protobuf content type when true.
    """
    return {
        AUTHORIZATION_HEADER: f"Bearer {token}",
        CONTENT_TYPE_HEADER: APPLICATION_PROTOBUF if protobuf else APPLICATION_JSON,
    }


def _minimal_opamp_payload() -> bytes:
    """Return a minimal AgentToServer protobuf accepted by the provider."""
    instance_uid = b"st004b-auth"
    return bytes((0x0A, len(instance_uid))) + instance_uid


def _mcp_payload() -> bytes:
    """Return a minimal MCP initialize payload for auth-boundary checks."""
    return json.dumps(
        {
            KEY_JSONRPC: MCP_JSONRPC_VERSION,
            KEY_ID: MCP_INITIALIZE_ID,
            KEY_METHOD: MCP_INITIALIZE_METHOD,
            KEY_PARAMS: {
                KEY_PROTOCOL_VERSION: MCP_PROTOCOL_VERSION,
                KEY_CLIENT_INFO: {
                    KEY_NAME: MCP_CLIENT_NAME,
                    KEY_VERSION: MCP_CLIENT_VERSION,
                },
                KEY_CAPABILITIES: {},
            },
        }
    ).encode(UTF_8_ENCODING)


def _check(name: str, passed: bool, value: Any, expected: Any) -> dict[str, Any]:
    """Build one consistently shaped verification result.

    Args:
        name: Stable check identifier.
        passed: Whether the observed value satisfies the requirement.
        value: Observed status or evidence detail.
        expected: Human-readable expected value.
    """
    return {
        KEY_NAME: name,
        KEY_PASSED: passed,
        KEY_VALUE: value,
        KEY_EXPECTED: expected,
    }


# Each route row carries request controls plus its expected statuses.
# pylint: disable-next=too-many-arguments
def _route_check(
    *,
    name: str,
    url: str,
    expected_statuses: set[int],
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    ca_file: Path | None = None,
) -> dict[str, Any]:
    """Execute and record one route-matrix assertion.

    Args:
        name: Stable check identifier.
        url: Fully qualified route URL.
        expected_statuses: Status values accepted by the scenario.
        method: HTTP method sent to the route.
        headers: Optional request headers.
        data: Optional request body.
        ca_file: Optional custom HTTPS trust anchor.
    """
    status, body = _request(
        url,
        method=method,
        headers=headers,
        data=data,
        ca_file=ca_file,
    )
    return {
        KEY_NAME: name,
        KEY_PASSED: status in expected_statuses,
        KEY_STATUS: status,
        KEY_EXPECTED: sorted(expected_statuses),
        KEY_BODY: body[:ROUTE_BODY_EVIDENCE_LIMIT],
    }


def _find_client(payload: dict[str, Any], instance_id: str) -> dict[str, Any] | None:
    """Find a provider client containing a service instance identifier.

    Args:
        payload: Parsed `/api/clients` response.
        instance_id: Simulator identifier expected in agent metadata.
    """
    for client_payload in payload.get(KEY_CLIENTS) or []:
        description = str(client_payload.get(KEY_AGENT_DESCRIPTION) or "")
        if instance_id in description:
            return client_payload
    return None


def _wait_for_client(
    *,
    base_url: str,
    instance_id: str,
    headers: dict[str, str],
    timeout_seconds: float,
    ca_file: Path | None = None,
) -> dict[str, Any]:
    """Poll until one expected consumer appears in provider state.

    Args:
        base_url: Provider URL used for API polling.
        instance_id: Expected simulator service instance identifier.
        headers: UI/API authorization headers for the profile.
        timeout_seconds: Maximum wait before failing.
        ca_file: Optional provider CA for TLS profiles.
    """
    deadline = time.monotonic() + timeout_seconds
    last_payload: dict[str, Any] = {}
    while time.monotonic() < deadline:
        status, body = _request(
            _join_url(base_url, API_CLIENTS_ENDPOINT),
            headers=headers,
            ca_file=ca_file,
        )
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            payload = {}
        if status == HTTPStatus.OK and isinstance(payload, dict):
            last_payload = payload
            if _find_client(payload, instance_id) is not None:
                return payload
        time.sleep(POLL_INTERVAL_SECONDS)
    raise AssertionError(f"consumer {instance_id!r} not registered: {last_payload}")


def _mint_token(issuer_url: str, token_case: str) -> str:
    """Retrieve one JWT variant from the local issuer.

    Args:
        issuer_url: Host-accessible URL for the issuer container.
        token_case: Named JWT variant requested by the verifier.
    """
    query = urllib.parse.urlencode({KEY_CASE: token_case})
    status, body = _request(f"{_join_url(issuer_url, MINT_ENDPOINT)}?{query}")
    payload = json.loads(body) if body else {}
    if status != HTTPStatus.OK or not isinstance(payload, dict):
        raise AssertionError(f"JWT mint failed case={token_case}: {status} {payload}")
    token = str(payload.get(KEY_TOKEN) or "")
    if not token:
        raise AssertionError(f"JWT mint returned no token for case={token_case}")
    return token


def _compose_logs(compose_file: Path, compose_project: str, service_name: str) -> str:
    """Capture logs for one service in the active Compose project.

    Args:
        compose_file: Compose definition used by the profile runner.
        compose_project: Active Compose project name.
        service_name: Service whose logs should be retained.
    """
    completed = subprocess.run(
        [
            "docker",
            "compose",
            "-p",
            compose_project,
            "-f",
            str(compose_file),
            "logs",
            "--no-color",
            service_name,
        ],
        text=True,
        encoding=UTF_8_ENCODING,
        errors=DECODE_ERROR_HANDLER,
        capture_output=True,
        check=False,
    )
    return (completed.stdout or "") + (completed.stderr or "")


def _append_route(checks: list[dict[str, Any]], route: dict[str, Any]) -> None:
    """Append a route result to the shared profile checks.

    Args:
        checks: Mutable check list for the active profile.
        route: Route-matrix result produced by `_route_check`.
    """
    checks.append(route)


def _verify_no_auth(
    base_url: str,
    timeout_seconds: float,
    _issuer_url: str,
    _ca_file: Path | None,
) -> list[dict[str, Any]]:
    """Verify unprotected routes and a token-free consumer.

    Args:
        base_url: Provider URL.
        timeout_seconds: Consumer registration timeout.
        _issuer_url: Unused issuer URL retained for a common verifier signature.
        _ca_file: Unused CA path retained for a common verifier signature.
    """
    checks: list[dict[str, Any]] = []
    for name, endpoint in (
        ("no_auth_api", API_CLIENTS_ENDPOINT),
        ("no_auth_tool", TOOL_ENDPOINT),
        ("no_auth_metrics", METRICS_ENDPOINT),
        ("no_auth_ui", UI_ENDPOINT),
    ):
        _append_route(
            checks,
            _route_check(
                name=name,
                url=_join_url(base_url, endpoint),
                expected_statuses={HTTPStatus.OK},
            ),
        )
    _append_route(
        checks,
        _route_check(
            name="no_auth_opamp",
            url=_join_url(base_url, OPAMP_ENDPOINT),
            expected_statuses={HTTPStatus.OK},
            method="POST",
            headers={CONTENT_TYPE_HEADER: APPLICATION_PROTOBUF},
            data=_minimal_opamp_payload(),
        ),
    )
    clients = _wait_for_client(
        base_url=base_url,
        instance_id=VALID_INSTANCE_BY_PROFILE[PROFILE_NO_AUTH],
        headers={ACCEPT_HEADER: APPLICATION_JSON},
        timeout_seconds=timeout_seconds,
    )
    checks.append(
        _check(
            "no_auth_consumer_registered",
            True,
            len(clients.get(KEY_CLIENTS) or []),
            ">=1",
        )
    )
    return checks


def _verify_static_opamp(
    base_url: str,
    timeout_seconds: float,
    _issuer_url: str,
    _ca_file: Path | None,
) -> list[dict[str, Any]]:
    """Verify OpAMP-only static authorization and consumer rejection.

    Args:
        base_url: Provider URL.
        timeout_seconds: Consumer registration timeout.
        _issuer_url: Unused issuer URL retained for a common verifier signature.
        _ca_file: Unused CA path retained for a common verifier signature.
    """
    checks = [
        _route_check(
            name="static_opamp_ui_unprotected",
            url=_join_url(base_url, API_CLIENTS_ENDPOINT),
            expected_statuses={HTTPStatus.OK},
        )
    ]
    for name, headers in (
        ("static_opamp_missing", {CONTENT_TYPE_HEADER: APPLICATION_PROTOBUF}),
        (
            "static_opamp_malformed",
            {
                AUTHORIZATION_HEADER: "Basic invalid",
                CONTENT_TYPE_HEADER: APPLICATION_PROTOBUF,
            },
        ),
        ("static_opamp_wrong", _bearer_headers(WRONG_TOKEN, protobuf=True)),
    ):
        checks.append(
            _route_check(
                name=name,
                url=_join_url(base_url, OPAMP_ENDPOINT),
                expected_statuses={HTTPStatus.UNAUTHORIZED},
                method="POST",
                headers=headers,
                data=_minimal_opamp_payload(),
            )
        )
    checks.append(
        _route_check(
            name="static_opamp_valid",
            url=_join_url(base_url, OPAMP_ENDPOINT),
            expected_statuses={HTTPStatus.OK},
            method="POST",
            headers=_bearer_headers(OPAMP_TOKEN, protobuf=True),
            data=_minimal_opamp_payload(),
        )
    )
    clients = _wait_for_client(
        base_url=base_url,
        instance_id=VALID_INSTANCE_BY_PROFILE[PROFILE_STATIC_OPAMP],
        headers={ACCEPT_HEADER: APPLICATION_JSON},
        timeout_seconds=timeout_seconds,
    )
    invalid_id = INVALID_INSTANCE_BY_PROFILE[PROFILE_STATIC_OPAMP]
    checks.append(_check("static_opamp_valid_consumer_registered", True, "present", "present"))
    checks.append(
        _check(
            "static_opamp_invalid_consumer_absent",
            _find_client(clients, invalid_id) is None,
            "absent" if _find_client(clients, invalid_id) is None else "present",
            "absent",
        )
    )
    return checks


def _verify_static_ui(
    base_url: str,
    timeout_seconds: float,
    _issuer_url: str,
    _ca_file: Path | None,
) -> list[dict[str, Any]]:
    """Verify UI static auth while OpAMP remains unprotected.

    Args:
        base_url: Provider URL.
        timeout_seconds: Consumer registration timeout.
        _issuer_url: Unused issuer URL retained for a common verifier signature.
        _ca_file: Unused CA path retained for a common verifier signature.
    """
    checks: list[dict[str, Any]] = []
    protected_routes = (
        ("static_ui_api_missing", API_CLIENTS_ENDPOINT, "GET"),
        ("static_ui_tool_missing", TOOL_ENDPOINT, "GET"),
        ("static_ui_metrics_missing", METRICS_ENDPOINT, "GET"),
        ("static_ui_sse_missing", SSE_ENDPOINT, "GET"),
        ("static_ui_messages_missing", MESSAGES_ENDPOINT, "POST"),
        ("static_ui_mcp_missing", MCP_ENDPOINT, "POST"),
    )
    for name, endpoint, method in protected_routes:
        checks.append(
            _route_check(
                name=name,
                url=_join_url(base_url, endpoint),
                expected_statuses={HTTPStatus.UNAUTHORIZED},
                method=method,
                headers={CONTENT_TYPE_HEADER: APPLICATION_JSON},
                data=_mcp_payload() if method == "POST" else None,
            )
        )
    for name, headers in (
        ("static_ui_api_malformed", {AUTHORIZATION_HEADER: "Token invalid"}),
        ("static_ui_api_wrong", _bearer_headers(WRONG_TOKEN)),
    ):
        checks.append(
            _route_check(
                name=name,
                url=_join_url(base_url, API_CLIENTS_ENDPOINT),
                expected_statuses={HTTPStatus.UNAUTHORIZED},
                headers=headers,
            )
        )
    checks.extend(
        [
            _route_check(
                name="static_ui_api_valid",
                url=_join_url(base_url, API_CLIENTS_ENDPOINT),
                expected_statuses={HTTPStatus.OK},
                headers=_bearer_headers(UI_TOKEN),
            ),
            _route_check(
                name="static_ui_metrics_valid",
                url=_join_url(base_url, METRICS_ENDPOINT),
                expected_statuses={HTTPStatus.OK},
                headers=_bearer_headers(UI_TOKEN),
            ),
            _route_check(
                name="static_ui_tool_valid",
                url=_join_url(base_url, TOOL_ENDPOINT),
                expected_statuses={HTTPStatus.OK},
                headers=_bearer_headers(UI_TOKEN),
            ),
            _route_check(
                name="static_ui_mcp_valid",
                url=_join_url(base_url, MCP_ENDPOINT),
                expected_statuses={HTTPStatus.OK, HTTPStatus.ACCEPTED, HTTPStatus.BAD_REQUEST},
                method="POST",
                headers={
                    **_bearer_headers(UI_TOKEN),
                    ACCEPT_HEADER: MCP_ACCEPT,
                },
                data=_mcp_payload(),
            ),
            _route_check(
                name="static_ui_opamp_unprotected",
                url=_join_url(base_url, OPAMP_ENDPOINT),
                expected_statuses={HTTPStatus.OK},
                method="POST",
                headers={CONTENT_TYPE_HEADER: APPLICATION_PROTOBUF},
                data=_minimal_opamp_payload(),
            ),
        ]
    )
    _wait_for_client(
        base_url=base_url,
        instance_id=VALID_INSTANCE_BY_PROFILE[PROFILE_STATIC_UI],
        headers=_bearer_headers(UI_TOKEN),
        timeout_seconds=timeout_seconds,
    )
    checks.append(
        _check(
            "static_ui_unauthenticated_consumer_registered",
            True,
            "present",
            "present",
        )
    )
    return checks


def _verify_static_both(
    base_url: str,
    timeout_seconds: float,
    _issuer_url: str,
    _ca_file: Path | None,
) -> list[dict[str, Any]]:
    """Verify static tokens remain isolated to their intended route scopes.

    Args:
        base_url: Provider URL.
        timeout_seconds: Consumer registration timeout.
        _issuer_url: Unused issuer URL retained for a common verifier signature.
        _ca_file: Unused CA path retained for a common verifier signature.
    """
    checks = [
        _route_check(
            name="static_both_ui_rejects_opamp_token",
            url=_join_url(base_url, API_CLIENTS_ENDPOINT),
            expected_statuses={HTTPStatus.UNAUTHORIZED},
            headers=_bearer_headers(OPAMP_TOKEN),
        ),
        _route_check(
            name="static_both_opamp_rejects_ui_token",
            url=_join_url(base_url, OPAMP_ENDPOINT),
            expected_statuses={HTTPStatus.UNAUTHORIZED},
            method="POST",
            headers=_bearer_headers(UI_TOKEN, protobuf=True),
            data=_minimal_opamp_payload(),
        ),
        _route_check(
            name="static_both_ui_accepts_ui_token",
            url=_join_url(base_url, API_CLIENTS_ENDPOINT),
            expected_statuses={HTTPStatus.OK},
            headers=_bearer_headers(UI_TOKEN),
        ),
        _route_check(
            name="static_both_opamp_accepts_opamp_token",
            url=_join_url(base_url, OPAMP_ENDPOINT),
            expected_statuses={HTTPStatus.OK},
            method="POST",
            headers=_bearer_headers(OPAMP_TOKEN, protobuf=True),
            data=_minimal_opamp_payload(),
        ),
    ]
    _wait_for_client(
        base_url=base_url,
        instance_id=VALID_INSTANCE_BY_PROFILE[PROFILE_STATIC_BOTH],
        headers=_bearer_headers(UI_TOKEN),
        timeout_seconds=timeout_seconds,
    )
    checks.append(_check("static_both_consumer_registered", True, "present", "present"))
    return checks


def _verify_mcp_disabled(
    base_url: str,
    _timeout_seconds: float,
    _issuer_url: str,
    _ca_file: Path | None,
) -> list[dict[str, Any]]:
    """Verify `allow-mcp=false` rejects even a valid UI token.

    Args:
        base_url: Provider URL.
        _timeout_seconds: Unused timeout retained for a common verifier signature.
        _issuer_url: Unused issuer URL retained for a common verifier signature.
        _ca_file: Unused CA path retained for a common verifier signature.
    """
    return [
        _route_check(
            name="mcp_disabled_valid_token_rejected",
            url=_join_url(base_url, MCP_ENDPOINT),
            expected_statuses={HTTPStatus.FORBIDDEN, HTTPStatus.NOT_FOUND},
            method="POST",
            headers={**_bearer_headers(UI_TOKEN), ACCEPT_HEADER: MCP_ACCEPT},
            data=_mcp_payload(),
        )
    ]


def _verify_jwt_negative(
    base_url: str,
    _timeout_seconds: float,
    issuer_url: str,
    _ca_file: Path | None,
) -> list[dict[str, Any]]:
    """Verify valid JWTs and isolated malformed/claim/signature failures.

    Args:
        base_url: Provider URL.
        _timeout_seconds: Unused timeout retained for a common verifier signature.
        issuer_url: Host URL for the local JWKS issuer.
        _ca_file: Unused CA path retained for a common verifier signature.
    """
    valid_token = _mint_token(issuer_url, CASE_VALID)
    rejected_tokens = {"malformed": "not-a-jwt"}
    for token_case in JWT_REJECTION_CASES:
        rejected_tokens[token_case] = _mint_token(issuer_url, token_case)
    checks: list[dict[str, Any]] = []
    for token_case, token in rejected_tokens.items():
        checks.extend(
            [
                _route_check(
                    name=f"jwt_ui_{token_case}_rejected",
                    url=_join_url(base_url, API_CLIENTS_ENDPOINT),
                    expected_statuses={HTTPStatus.UNAUTHORIZED},
                    headers=_bearer_headers(token),
                ),
                _route_check(
                    name=f"jwt_opamp_{token_case}_rejected",
                    url=_join_url(base_url, OPAMP_ENDPOINT),
                    expected_statuses={HTTPStatus.UNAUTHORIZED},
                    method="POST",
                    headers=_bearer_headers(token, protobuf=True),
                    data=_minimal_opamp_payload(),
                ),
            ]
        )
    checks.extend(
        [
            _route_check(
                name="jwt_ui_valid",
                url=_join_url(base_url, API_CLIENTS_ENDPOINT),
                expected_statuses={HTTPStatus.OK},
                headers=_bearer_headers(valid_token),
            ),
            _route_check(
                name="jwt_opamp_valid",
                url=_join_url(base_url, OPAMP_ENDPOINT),
                expected_statuses={HTTPStatus.OK},
                method="POST",
                headers=_bearer_headers(valid_token, protobuf=True),
                data=_minimal_opamp_payload(),
            ),
        ]
    )
    return checks


def _verify_tls(
    base_url: str,
    timeout_seconds: float,
    _issuer_url: str,
    ca_file: Path | None,
) -> list[dict[str, Any]]:
    """Verify HTTPS enforcement, CA trust, and untrusted-consumer rejection.

    Args:
        base_url: HTTPS provider URL.
        timeout_seconds: Trusted-consumer registration timeout.
        _issuer_url: Unused issuer URL retained for a common verifier signature.
        ca_file: Generated self-signed certificate trusted as the test CA.
    """
    if ca_file is None or not ca_file.is_file():
        raise AssertionError(f"TLS CA file is unavailable: {ca_file}")
    plain_url = base_url.replace("https://", "http://", 1)
    checks = [
        _route_check(
            name="tls_plain_http_refused",
            url=_join_url(plain_url, API_CLIENTS_ENDPOINT),
            expected_statuses={0},
        ),
        _route_check(
            name="tls_system_trust_rejects_self_signed",
            url=_join_url(base_url, API_CLIENTS_ENDPOINT),
            expected_statuses={0},
        ),
        _route_check(
            name="tls_ca_bundle_accepts_provider",
            url=_join_url(base_url, API_CLIENTS_ENDPOINT),
            expected_statuses={HTTPStatus.OK},
            ca_file=ca_file,
        ),
    ]
    clients = _wait_for_client(
        base_url=base_url,
        instance_id=VALID_INSTANCE_BY_PROFILE[PROFILE_TLS],
        headers={ACCEPT_HEADER: APPLICATION_JSON},
        timeout_seconds=timeout_seconds,
        ca_file=ca_file,
    )
    invalid_id = INVALID_INSTANCE_BY_PROFILE[PROFILE_TLS]
    checks.append(_check("tls_trusted_consumer_registered", True, "present", "present"))
    checks.append(
        _check(
            "tls_untrusted_consumer_absent",
            _find_client(clients, invalid_id) is None,
            "absent" if _find_client(clients, invalid_id) is None else "present",
            "absent",
        )
    )
    return checks


PROFILE_VERIFIERS: dict[
    str,
    Callable[[str, float, str, Path | None], list[dict[str, Any]]],
] = {
    PROFILE_NO_AUTH: _verify_no_auth,
    PROFILE_STATIC_OPAMP: _verify_static_opamp,
    PROFILE_STATIC_UI: _verify_static_ui,
    PROFILE_STATIC_BOTH: _verify_static_both,
    PROFILE_MCP_DISABLED: _verify_mcp_disabled,
    PROFILE_JWT_NEGATIVE: _verify_jwt_negative,
    PROFILE_TLS: _verify_tls,
}


def _write_report(
    path: Path,
    *,
    profile: str,
    checks: list[dict[str, Any]],
    evidence: dict[str, str],
    result: str,
) -> None:
    """Write a human-readable profile result.

    Args:
        path: Markdown report destination.
        profile: Active ST-004B profile.
        checks: Ordered verification results.
        evidence: Generated evidence files by label.
        result: Aggregate profile result.
    """
    lines = [
        f"# {SCENARIO_LABEL} Results - {profile}",
        "",
        f"- Generated: {_utc_now()}",
        f"- Result: {result}",
        "",
        "## Checks",
        "",
        "| Check | Expected | Observed | Result |",
        "|---|---|---|---:|",
    ]
    for check in checks:
        observed = check.get(KEY_STATUS, check.get(KEY_VALUE, ""))
        check_result = "PASS" if check.get(KEY_PASSED) else "FAIL"
        lines.append(
            f"| {check.get(KEY_NAME)} | `{check.get(KEY_EXPECTED)}` | "
            f"`{observed}` | {check_result} |"
        )
    lines.extend(["", "## Evidence", ""])
    for label, evidence_path in evidence.items():
        lines.append(f"- {label}: `{evidence_path}`")
    path.write_text("\n".join(lines) + "\n", encoding=UTF_8_ENCODING)


# The entry point owns CLI, evidence, log, and aggregate-result state.
# pylint: disable-next=too-many-locals
def main() -> int:
    """Parse arguments, verify one profile, and write retained evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, choices=SUPPORTED_PROFILES)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--issuer-url", default=DEFAULT_ISSUER_URL)
    parser.add_argument("--ca-file", type=Path)
    parser.add_argument("--compose-file", type=Path, required=True)
    parser.add_argument("--compose-project", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_VERIFY_TIMEOUT_SECONDS)
    arguments = parser.parse_args()

    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []
    evidence: dict[str, str] = {}
    result = FAILED_RESULT
    try:
        verifier = PROFILE_VERIFIERS[arguments.profile]
        checks = verifier(
            arguments.base_url,
            arguments.timeout_seconds,
            arguments.issuer_url,
            arguments.ca_file,
        )
        provider_logs = _compose_logs(
            arguments.compose_file,
            arguments.compose_project,
            "provider",
        )
        provider_log_path = arguments.output_dir / PROVIDER_LOG_FILE_NAME
        _write_text(provider_log_path, provider_logs)
        evidence[PROVIDER_LOG_FILE_NAME] = str(provider_log_path)
        if arguments.profile in {
            PROFILE_STATIC_OPAMP,
            PROFILE_STATIC_UI,
            PROFILE_STATIC_BOTH,
            PROFILE_JWT_NEGATIVE,
        }:
            lower_logs = provider_logs.lower()
            checks.append(
                _check(
                    "authorization_rejection_logged",
                    all(
                        marker in lower_logs
                        for marker in ("authorization rejected", "method=", "path=", "reason=")
                    ),
                    "structured rejection fields present",
                    "mode/method/path/reason warning",
                )
            )
        if arguments.profile in {PROFILE_STATIC_OPAMP, PROFILE_TLS}:
            invalid_logs = _compose_logs(
                arguments.compose_file,
                arguments.compose_project,
                "consumer-invalid",
            )
            invalid_log_path = arguments.output_dir / INVALID_CONSUMER_LOG_FILE_NAME
            _write_text(invalid_log_path, invalid_logs)
            evidence[INVALID_CONSUMER_LOG_FILE_NAME] = str(invalid_log_path)
            expected_markers = (
                ("401", "unauthorized")
                if arguments.profile == PROFILE_STATIC_OPAMP
                else ("certificate verify failed", "self-signed certificate")
            )
            lower_invalid_logs = invalid_logs.lower()
            checks.append(
                _check(
                    "invalid_consumer_has_actionable_log",
                    any(marker in lower_invalid_logs for marker in expected_markers),
                    "matching diagnostic present",
                    expected_markers,
                )
            )
        all_checks_passed = checks and all(check.get(KEY_PASSED) for check in checks)
        result = PASSED_RESULT if all_checks_passed else FAILED_RESULT
    except Exception as verification_error:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        checks.append(
            _check(
                "verification_exception",
                False,
                repr(verification_error),
                "no exception",
            )
        )

    route_matrix_path = arguments.output_dir / ROUTE_MATRIX_FILE_NAME
    _write_json(route_matrix_path, checks)
    evidence[ROUTE_MATRIX_FILE_NAME] = str(route_matrix_path)
    summary_path = arguments.output_dir / SUMMARY_FILE_NAME
    _write_json(
        summary_path,
        {
            KEY_PROFILE: arguments.profile,
            KEY_RESULT: result,
            KEY_GENERATED_AT: _utc_now(),
            KEY_CHECKS: checks,
            KEY_EVIDENCE: evidence,
        },
    )
    evidence[SUMMARY_FILE_NAME] = str(summary_path)
    report_path = arguments.output_dir / REPORT_FILE_NAME
    _write_report(
        report_path,
        profile=arguments.profile,
        checks=checks,
        evidence=evidence,
        result=result,
    )
    print(f"{SCENARIO_LABEL} profile={arguments.profile} result={result}")
    print(f"Report: {report_path}")
    return 0 if result == PASSED_RESULT else 1


if __name__ == "__main__":
    raise SystemExit(main())
