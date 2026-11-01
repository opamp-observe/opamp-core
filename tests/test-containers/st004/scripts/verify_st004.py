#!/usr/bin/env python3
# Licensed under the Apache License, Version 2.0.
# Copyright 2026 opamp.info
"""Verify the ST-004 Keycloak authentication scenario and write evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCENARIO_LABEL = "ST-004"
SCENARIO_NAME = "keycloak"
DEFAULT_BASE_URL = "http://127.0.0.1:18083"
DEFAULT_KEYCLOAK_URL = "http://127.0.0.1:18082"
DEFAULT_HTTP_TIMEOUT_SECONDS = 5.0
DEFAULT_VERIFY_TIMEOUT_SECONDS = 180.0
POLL_INTERVAL_SECONDS = 1.0
HTTP_STATUS_OK = 200
HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_ACCEPTED = 202

REALM = "opamp"
VALID_CONSUMER_ID = "st004-simulator-valid"
WRONG_AUDIENCE_CONSUMER_ID = "st004-simulator-wrong-audience"
TOKEN_ENDPOINT = f"/realms/{REALM}/protocol/openid-connect/token"
API_CLIENTS_ENDPOINT = "/api/clients"
TOOL_OTEL_AGENTS_ENDPOINT = "/tool/otelAgents"
UI_ENDPOINT = "/ui"
MCP_ENDPOINT = "/mcp"
OPAMP_ENDPOINT = "/v1/opamp"

OPAMP_CLIENT_ID = "opamp-consumer"
OPAMP_CLIENT_SECRET = "opamp-consumer-secret"  # noqa: S105 - local test fixture secret.
UI_CLIENT_ID = "opamp-ui"
UI_CLIENT_SECRET = "opamp-ui-secret"  # noqa: S105 - local test fixture secret.
WRONG_CLIENT_ID = "opamp-wrong-audience"
WRONG_CLIENT_SECRET = "opamp-wrong-audience-secret"  # noqa: S105 - local test fixture secret.

ACCEPT_HEADER_KEY = "Accept"
AUTH_HEADER_KEY = "Authorization"
CONTENT_TYPE_HEADER_KEY = "Content-Type"
APPLICATION_JSON_MEDIA_TYPE = "application/json"
APPLICATION_PROTOBUF_MEDIA_TYPE = "application/x-protobuf"
TEXT_HTML_MEDIA_TYPE = "text/html"
MCP_ACCEPT_HEADER = "application/json, text/event-stream"
UTF_8_ENCODING = "utf-8"
DECODE_ERROR_HANDLER = "replace"

REPORT_FILE_NAME = "results.md"
SUMMARY_FILE_NAME = "summary.json"
ROUTE_MATRIX_FILE_NAME = "route-matrix.json"
CLIENTS_LIVE_FILE_NAME = "api-clients-live.json"
TOOL_OTEL_AGENTS_FILE_NAME = "tool-otelAgents-live.json"
BAD_CONSUMER_LOG_FILE_NAME = "consumer-wrong-audience.log"

CHECKS_KEY = "checks"
CHECK_NAME_KEY = "name"
EVIDENCE_PATHS_KEY = "evidence_paths"
GENERATED_AT_UTC_KEY = "generated_at_utc"
PASSED_KEY = "passed"
RESULT_KEY = "result"
ROUTE_KEY = "route"
STATUS_KEY = "status"
VALUE_KEY = "value"

CHECK_API_VALID_TOKEN = "api_valid_ui_token"
CHECK_BAD_CONSUMER_NOT_REGISTERED = "consumer_wrong_audience_not_registered"
CHECK_BAD_CONSUMER_REJECTED = "consumer_wrong_audience_rejected"
CHECK_CONSUMER_REGISTERED = "consumer_valid_keycloak_token_registered"
CHECK_MCP_MISSING_TOKEN_REJECTED = "mcp_missing_token_rejected"
CHECK_MCP_VALID_TOKEN_REACHES_TRANSPORT = "mcp_valid_ui_token_reaches_transport"
CHECK_MCP_WRONG_TOKEN_REJECTED = "mcp_wrong_audience_token_rejected"
CHECK_OPAMP_MISSING_TOKEN_REJECTED = "opamp_missing_token_rejected"
CHECK_OPAMP_VALID_TOKEN_REACHES_PROTOCOL = "opamp_valid_token_reaches_protocol"
CHECK_OPAMP_WRONG_TOKEN_REJECTED = "opamp_wrong_audience_token_rejected"
CHECK_TOOL_VALID_TOKEN = "tool_valid_ui_token"
CHECK_UI_MISSING_TOKEN_REJECTED = "ui_missing_token_rejected"
CHECK_UI_VALID_TOKEN = "ui_valid_token"
CHECK_UI_WRONG_TOKEN_REJECTED = "ui_wrong_audience_token_rejected"
CHECK_VERIFICATION_EXCEPTION = "verification_exception"

PASSED_RESULT = "passed"
FAILED_RESULT = "failed"


def _utc_now() -> str:
    """Return a stable UTC timestamp string for evidence files."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _join_url(base_url: str, endpoint: str) -> str:
    """Combine a configured base URL with an absolute endpoint path."""
    return f"{base_url.rstrip('/')}{endpoint}"


def _write_json(path: Path, payload: Any) -> None:
    """Write deterministic JSON evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"{json.dumps(payload, indent=2, sort_keys=True)}\n",
        encoding=UTF_8_ENCODING,
    )


def _write_text(path: Path, payload: str) -> None:
    """Write text evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding=UTF_8_ENCODING)


def _http_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    timeout: float = DEFAULT_HTTP_TIMEOUT_SECONDS,
) -> tuple[int, dict[str, str], str]:
    """Issue one HTTP request and return status, headers, and response body."""
    request = urllib.request.Request(
        url,
        data=data,
        headers=headers or {},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode(UTF_8_ENCODING, errors=DECODE_ERROR_HANDLER)
            return int(response.status), dict(response.headers.items()), body
    except urllib.error.HTTPError as http_error:
        body = http_error.read().decode(UTF_8_ENCODING, errors=DECODE_ERROR_HANDLER)
        return int(http_error.code), dict(http_error.headers.items()), body


def _json_from_body(body: str) -> Any:
    """Parse JSON when possible, otherwise keep the original text body."""
    try:
        return json.loads(body) if body.strip() else None
    except json.JSONDecodeError:
        return body


def _bearer(token: str) -> str:
    """Return Authorization header value for a bearer token."""
    return f"Bearer {token}"


def _request_token(
    *,
    keycloak_url: str,
    client_id: str,
    client_secret: str,
) -> str:
    """Request a client-credentials access token from the local Keycloak realm."""
    form = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode(UTF_8_ENCODING)
    status, _headers, body = _http_request(
        _join_url(keycloak_url, TOKEN_ENDPOINT),
        method="POST",
        headers={CONTENT_TYPE_HEADER_KEY: "application/x-www-form-urlencoded"},
        data=form,
    )
    payload = _json_from_body(body)
    if status != HTTP_STATUS_OK or not isinstance(payload, dict):
        raise AssertionError(f"token request failed for {client_id}: {status} {payload}")
    token = str(payload.get("access_token") or "").strip()
    if not token:
        raise AssertionError(f"token response missing access_token for {client_id}")
    return token


def _route_check(
    *,
    name: str,
    url: str,
    expected_status: int | None = None,
    allowed_statuses: set[int] | None = None,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
) -> dict[str, Any]:
    """Execute one route check for the auth matrix."""
    status, response_headers, body = _http_request(
        url,
        method=method,
        headers=headers,
        data=data,
    )
    passed = (
        status == expected_status
        if expected_status is not None
        else status in (allowed_statuses or set())
    )
    return {
        CHECK_NAME_KEY: name,
        PASSED_KEY: passed,
        ROUTE_KEY: url,
        STATUS_KEY: status,
        "headers": response_headers,
        "body": _json_from_body(body),
    }


def _find_client(
    clients_payload: dict[str, Any],
    service_instance_id: str,
) -> dict[str, Any] | None:
    """Find a simulator client by service instance id in the provider API payload."""
    for client_payload in clients_payload.get("clients") or []:
        agent_description = str(client_payload.get("agent_description") or "")
        if service_instance_id in agent_description:
            return client_payload
    return None


def _wait_for_valid_consumer(
    *,
    base_url: str,
    ui_token: str,
    timeout_seconds: float,
    evidence_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Poll authenticated `/api/clients` until the valid consumer appears."""
    deadline = time.monotonic() + timeout_seconds
    last_payload: dict[str, Any] = {}
    while time.monotonic() < deadline:
        status, _headers, body = _http_request(
            _join_url(base_url, API_CLIENTS_ENDPOINT),
            headers={
                ACCEPT_HEADER_KEY: APPLICATION_JSON_MEDIA_TYPE,
                AUTH_HEADER_KEY: _bearer(ui_token),
            },
        )
        payload = _json_from_body(body)
        if status == HTTP_STATUS_OK and isinstance(payload, dict):
            last_payload = payload
            client_payload = _find_client(payload, VALID_CONSUMER_ID)
            if client_payload is not None:
                return payload, client_payload
        time.sleep(POLL_INTERVAL_SECONDS)
    _write_json(evidence_dir / "api-clients-timeout.json", last_payload)
    raise AssertionError(f"valid consumer {VALID_CONSUMER_ID!r} was not visible")


def _compose_logs(
    *,
    compose_file: Path,
    compose_project: str,
    service_name: str,
) -> subprocess.CompletedProcess[str]:
    """Capture logs for one compose service."""
    return subprocess.run(
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


def _check_payload(name: str, passed: bool, value: Any = "") -> dict[str, Any]:
    """Create one check row for JSON and Markdown output."""
    return {
        CHECK_NAME_KEY: name,
        PASSED_KEY: passed,
        VALUE_KEY: value,
    }


def _mcp_initialize_payload() -> bytes:
    """Return a minimal Streamable HTTP MCP initialize request."""
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": "st004-init",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "clientInfo": {"name": "st004-auth-verifier", "version": "1.0.0"},
                "capabilities": {},
            },
        }
    ).encode(UTF_8_ENCODING)


def _minimal_opamp_payload() -> bytes:
    """Return a tiny valid AgentToServer protobuf with only instance_uid set."""
    instance_uid = b"st004-auth-check"
    return b"\x0a\x10" + instance_uid


def _write_report(
    *,
    path: Path,
    checks: list[dict[str, Any]],
    route_matrix: list[dict[str, Any]],
    evidence_paths: dict[str, str],
    result: str,
) -> None:
    """Write the human-readable ST-004 report."""
    lines = [
        f"# {SCENARIO_LABEL} Results - {SCENARIO_NAME}",
        "",
        f"- Generated: {_utc_now()}",
        f"- Result: {result}",
        "- IdP: local Keycloak compose service",
        "- OpAMP audience: `opamp-consumer`",
        "- UI/API/MCP audience: `opamp-ui`",
        "",
        "## Verification Checks",
        "",
        "| Check | Result | Evidence |",
        "|---|---:|---|",
    ]
    for check in checks:
        evidence = check.get(VALUE_KEY, "")
        if isinstance(evidence, (dict, list)):
            evidence = json.dumps(evidence, sort_keys=True)
        check_result = "PASS" if check.get(PASSED_KEY) else "FAIL"
        lines.append(f"| {check[CHECK_NAME_KEY]} | {check_result} | `{evidence}` |")

    lines.extend(["", "## Route Matrix", "", "| Check | Status | Result |", "|---|---:|---:|"])
    for route in route_matrix:
        route_result = "PASS" if route.get(PASSED_KEY) else "FAIL"
        lines.append(f"| {route[CHECK_NAME_KEY]} | {route[STATUS_KEY]} | {route_result} |")

    lines.extend(["", "## Evidence Files", ""])
    for label, value in evidence_paths.items():
        lines.append(f"- {label}: `{value}`")

    lines.extend(
        [
            "",
            "## ST-004 Reconciliation",
            "",
            "| ST-004 expectation | Covered by this artefact |",
            "|---|---|",
            "| Provider validates OpAMP JWTs with Keycloak JWKS | valid consumer registration and wrong-audience rejection |",
            "| UI routes require bearer auth | `/ui` missing, wrong-audience, and valid-token route checks |",
            "| API/tool routes require UI-scope auth | `/api/clients` and `/tool/otelAgents` valid-token checks |",
            "| MCP routes require UI-scope auth | `/mcp` missing, wrong-audience, and valid-token route checks |",
            "| Negative consumer auth is exercised | `consumer-wrong-audience` attempts to run and is not registered |",
            "| Evidence is retained for review | JSON captures, service logs, compose logs, and this report |",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding=UTF_8_ENCODING)


def main() -> int:
    """Run ST-004 verification from command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--keycloak-url", default=DEFAULT_KEYCLOAK_URL)
    parser.add_argument("--compose-file", type=Path, required=True)
    parser.add_argument("--compose-project", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_VERIFY_TIMEOUT_SECONDS)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []
    route_matrix: list[dict[str, Any]] = []
    evidence_paths: dict[str, str] = {}
    result = FAILED_RESULT

    try:
        opamp_token = _request_token(
            keycloak_url=args.keycloak_url,
            client_id=OPAMP_CLIENT_ID,
            client_secret=OPAMP_CLIENT_SECRET,
        )
        ui_token = _request_token(
            keycloak_url=args.keycloak_url,
            client_id=UI_CLIENT_ID,
            client_secret=UI_CLIENT_SECRET,
        )
        wrong_token = _request_token(
            keycloak_url=args.keycloak_url,
            client_id=WRONG_CLIENT_ID,
            client_secret=WRONG_CLIENT_SECRET,
        )

        clients_payload, valid_client = _wait_for_valid_consumer(
            base_url=args.base_url,
            ui_token=ui_token,
            timeout_seconds=args.timeout_seconds,
            evidence_dir=args.output_dir,
        )
        clients_path = args.output_dir / CLIENTS_LIVE_FILE_NAME
        _write_json(clients_path, clients_payload)
        evidence_paths["api_clients_live"] = str(clients_path)
        wrong_client = _find_client(clients_payload, WRONG_AUDIENCE_CONSUMER_ID)
        checks.append(
            _check_payload(
                CHECK_CONSUMER_REGISTERED,
                valid_client is not None,
                valid_client.get("client_id") if valid_client else "",
            )
        )
        checks.append(
            _check_payload(
                CHECK_BAD_CONSUMER_NOT_REGISTERED,
                wrong_client is None,
                "absent" if wrong_client is None else wrong_client.get("client_id"),
            )
        )

        route_matrix.extend(
            [
                _route_check(
                    name=CHECK_UI_MISSING_TOKEN_REJECTED,
                    url=_join_url(args.base_url, UI_ENDPOINT),
                    expected_status=HTTP_STATUS_UNAUTHORIZED,
                    headers={ACCEPT_HEADER_KEY: TEXT_HTML_MEDIA_TYPE},
                ),
                _route_check(
                    name=CHECK_UI_WRONG_TOKEN_REJECTED,
                    url=_join_url(args.base_url, UI_ENDPOINT),
                    expected_status=HTTP_STATUS_UNAUTHORIZED,
                    headers={
                        ACCEPT_HEADER_KEY: TEXT_HTML_MEDIA_TYPE,
                        AUTH_HEADER_KEY: _bearer(wrong_token),
                    },
                ),
                _route_check(
                    name=CHECK_UI_VALID_TOKEN,
                    url=_join_url(args.base_url, UI_ENDPOINT),
                    expected_status=HTTP_STATUS_OK,
                    headers={
                        ACCEPT_HEADER_KEY: TEXT_HTML_MEDIA_TYPE,
                        AUTH_HEADER_KEY: _bearer(ui_token),
                    },
                ),
                _route_check(
                    name=CHECK_API_VALID_TOKEN,
                    url=_join_url(args.base_url, API_CLIENTS_ENDPOINT),
                    expected_status=HTTP_STATUS_OK,
                    headers={
                        ACCEPT_HEADER_KEY: APPLICATION_JSON_MEDIA_TYPE,
                        AUTH_HEADER_KEY: _bearer(ui_token),
                    },
                ),
            ]
        )

        query_string = urllib.parse.urlencode({"service_instance_id": VALID_CONSUMER_ID})
        tool_check = _route_check(
            name=CHECK_TOOL_VALID_TOKEN,
            url=f"{_join_url(args.base_url, TOOL_OTEL_AGENTS_ENDPOINT)}?{query_string}",
            expected_status=HTTP_STATUS_OK,
            headers={
                ACCEPT_HEADER_KEY: APPLICATION_JSON_MEDIA_TYPE,
                AUTH_HEADER_KEY: _bearer(ui_token),
            },
        )
        route_matrix.append(tool_check)
        tool_path = args.output_dir / TOOL_OTEL_AGENTS_FILE_NAME
        _write_json(tool_path, tool_check.get("body"))
        evidence_paths["tool_otelAgents_live"] = str(tool_path)

        route_matrix.extend(
            [
                _route_check(
                    name=CHECK_OPAMP_MISSING_TOKEN_REJECTED,
                    url=_join_url(args.base_url, OPAMP_ENDPOINT),
                    method="POST",
                    expected_status=HTTP_STATUS_UNAUTHORIZED,
                    headers={CONTENT_TYPE_HEADER_KEY: APPLICATION_PROTOBUF_MEDIA_TYPE},
                    data=_minimal_opamp_payload(),
                ),
                _route_check(
                    name=CHECK_OPAMP_WRONG_TOKEN_REJECTED,
                    url=_join_url(args.base_url, OPAMP_ENDPOINT),
                    method="POST",
                    expected_status=HTTP_STATUS_UNAUTHORIZED,
                    headers={
                        CONTENT_TYPE_HEADER_KEY: APPLICATION_PROTOBUF_MEDIA_TYPE,
                        AUTH_HEADER_KEY: _bearer(wrong_token),
                    },
                    data=_minimal_opamp_payload(),
                ),
                _route_check(
                    name=CHECK_OPAMP_VALID_TOKEN_REACHES_PROTOCOL,
                    url=_join_url(args.base_url, OPAMP_ENDPOINT),
                    method="POST",
                    expected_status=HTTP_STATUS_OK,
                    headers={
                        CONTENT_TYPE_HEADER_KEY: APPLICATION_PROTOBUF_MEDIA_TYPE,
                        AUTH_HEADER_KEY: _bearer(opamp_token),
                    },
                    data=_minimal_opamp_payload(),
                ),
                _route_check(
                    name=CHECK_MCP_MISSING_TOKEN_REJECTED,
                    url=_join_url(args.base_url, MCP_ENDPOINT),
                    method="POST",
                    expected_status=HTTP_STATUS_UNAUTHORIZED,
                    headers={
                        CONTENT_TYPE_HEADER_KEY: APPLICATION_JSON_MEDIA_TYPE,
                        ACCEPT_HEADER_KEY: MCP_ACCEPT_HEADER,
                    },
                    data=_mcp_initialize_payload(),
                ),
                _route_check(
                    name=CHECK_MCP_WRONG_TOKEN_REJECTED,
                    url=_join_url(args.base_url, MCP_ENDPOINT),
                    method="POST",
                    expected_status=HTTP_STATUS_UNAUTHORIZED,
                    headers={
                        CONTENT_TYPE_HEADER_KEY: APPLICATION_JSON_MEDIA_TYPE,
                        ACCEPT_HEADER_KEY: MCP_ACCEPT_HEADER,
                        AUTH_HEADER_KEY: _bearer(wrong_token),
                    },
                    data=_mcp_initialize_payload(),
                ),
                _route_check(
                    name=CHECK_MCP_VALID_TOKEN_REACHES_TRANSPORT,
                    url=_join_url(args.base_url, MCP_ENDPOINT),
                    method="POST",
                    allowed_statuses={
                        HTTP_STATUS_OK,
                        HTTP_STATUS_ACCEPTED,
                        HTTP_STATUS_BAD_REQUEST,
                    },
                    headers={
                        CONTENT_TYPE_HEADER_KEY: APPLICATION_JSON_MEDIA_TYPE,
                        ACCEPT_HEADER_KEY: MCP_ACCEPT_HEADER,
                        AUTH_HEADER_KEY: _bearer(ui_token),
                    },
                    data=_mcp_initialize_payload(),
                ),
            ]
        )

        bad_logs = _compose_logs(
            compose_file=args.compose_file,
            compose_project=args.compose_project,
            service_name="consumer-wrong-audience",
        )
        bad_log_text = (bad_logs.stdout or "") + (bad_logs.stderr or "")
        bad_log_path = args.output_dir / BAD_CONSUMER_LOG_FILE_NAME
        _write_text(bad_log_path, bad_log_text)
        evidence_paths["consumer_wrong_audience_log"] = str(bad_log_path)
        lower_bad_log = bad_log_text.lower()
        checks.append(
            _check_payload(
                CHECK_BAD_CONSUMER_REJECTED,
                (
                    "401" in lower_bad_log
                    or "invalid bearer token" in lower_bad_log
                    or "audience" in lower_bad_log
                    or "unauthorized" in lower_bad_log
                ),
                "auth rejection evidence found in consumer-wrong-audience logs",
            )
        )

        for route_check in route_matrix:
            checks.append(
                _check_payload(
                    str(route_check[CHECK_NAME_KEY]),
                    bool(route_check[PASSED_KEY]),
                    route_check[STATUS_KEY],
                )
            )

        route_matrix_path = args.output_dir / ROUTE_MATRIX_FILE_NAME
        _write_json(route_matrix_path, route_matrix)
        evidence_paths["route_matrix"] = str(route_matrix_path)
        result = PASSED_RESULT if all(check.get(PASSED_KEY) for check in checks) else FAILED_RESULT
    except Exception as verification_error:
        checks.append(
            _check_payload(CHECK_VERIFICATION_EXCEPTION, False, repr(verification_error))
        )
    finally:
        summary_path = args.output_dir / SUMMARY_FILE_NAME
        _write_json(
            summary_path,
            {
                RESULT_KEY: result,
                GENERATED_AT_UTC_KEY: _utc_now(),
                CHECKS_KEY: checks,
                EVIDENCE_PATHS_KEY: evidence_paths,
            },
        )
        evidence_paths["summary"] = str(summary_path)
        report_path = args.output_dir / REPORT_FILE_NAME
        _write_report(
            path=report_path,
            checks=checks,
            route_matrix=route_matrix,
            evidence_paths=evidence_paths,
            result=result,
        )
        print(f"{SCENARIO_LABEL} {SCENARIO_NAME} result: {result}")
        print(f"Report: {report_path}")

    return 0 if result == PASSED_RESULT else 1


if __name__ == "__main__":
    raise SystemExit(main())
