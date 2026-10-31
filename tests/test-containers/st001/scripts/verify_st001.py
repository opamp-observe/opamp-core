#!/usr/bin/env python3
# Licensed under the Apache License, Version 2.0.
# Copyright 2026 opamp.info
"""Verify the ST-001 compose scenario and write reviewable evidence."""

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


SCENARIO_LABEL = "ST-001"
SCENARIO_SLUG = "st001"

SOCKET_SCENARIO = "socket"
HTTP_SCENARIO = "http"
WEBSOCKET_CHANNEL = "websocket"
HTTP_CHANNEL = "http"
EXPECTED_CHANNEL_BY_SCENARIO = {
    SOCKET_SCENARIO: WEBSOCKET_CHANNEL,
    HTTP_SCENARIO: HTTP_CHANNEL,
}

DEFAULT_BASE_URL = "http://127.0.0.1:18080"
DEFAULT_HTTP_TIMEOUT_SECONDS = 5.0
DEFAULT_VERIFY_TIMEOUT_SECONDS = 180.0
DISCONNECT_TIMEOUT_SECONDS = 45.0
POLL_INTERVAL_SECONDS = 1.0
HTTP_STATUS_OK = 200

API_CLIENTS_ENDPOINT = "/api/clients"
TOOL_OTEL_AGENTS_ENDPOINT = "/tool/otelAgents"
SUPERVISOR_SIGNAL_PATH = "/opt/opamp/source/OpAMPSupervisor.signal"
API_CLIENTS_LIVE_FILE_NAME = "api-clients-live.json"
DISCONNECT_SIGNAL_FILE_NAME = "disconnect-signal-result.json"
REPORT_FILE_NAME = "results.md"
SUMMARY_FILE_NAME = "summary.json"
TOOL_OTEL_AGENTS_LIVE_FILE_NAME = "tool-otelAgents-live.json"

ACCEPT_HEADER_KEY = "Accept"
AGENT_DESCRIPTION_KEY = "agent_description"
AGENTS_KEY = "agents"
API_CLIENTS_TIMEOUT_FILE_NAME = "api-clients-timeout.json"
CAPABILITIES_KEY = "capabilities"
CHECKS_KEY = "checks"
CHECK_NAME_KEY = "name"
CLIENT_ID_KEY = "client_id"
CLIENTS_KEY = "clients"
DISCONNECTED_AT_KEY = "disconnected_at"
DISCONNECTED_KEY = "disconnected"
EVIDENCE_PATHS_KEY = "evidence_paths"
GENERATED_AT_UTC_KEY = "generated_at_utc"
HEALTH_KEY = "health"
HTTP_STATUS_KEY = "http_status"
LAST_CHANNEL_KEY = "last_channel"
PASSED_KEY = "passed"
RESULT_KEY = "result"
RETURN_CODE_KEY = "returncode"
SCENARIO_KEY = "scenario"
SERVICE_INSTANCE_ID_KEY = "service_instance_id"
STDERR_KEY = "stderr"
STDOUT_KEY = "stdout"
TOTAL_KEY = "total"
VALUE_KEY = "value"

CHECK_AGENT_DESCRIPTION = "agent_description"
CHECK_CAPABILITIES = "capabilities"
CHECK_DISCONNECT_SIGNAL_WRITTEN = "disconnect_signal_written"
CHECK_DISCONNECT_VISIBLE = "disconnect_visible"
CHECK_HEALTH = "health"
CHECK_INSTANCE_UID = "instance_uid"
CHECK_LAST_CHANNEL = "last_channel"
CHECK_NOT_DISCONNECTED_WHILE_LIVE = "not_disconnected_while_live"
CHECK_TOOL_OTEL_AGENTS_LIVE_AGENT = "tool_otelAgents_live_agent"
CHECK_VERIFICATION_EXCEPTION = "verification_exception"

EVIDENCE_API_CLIENT_DISCONNECTED = "api_client_disconnected"
EVIDENCE_API_CLIENTS_LIVE = "api_clients_live"
EVIDENCE_DISCONNECT_SIGNAL = "disconnect_signal"
EVIDENCE_SUMMARY = "summary"
EVIDENCE_TOOL_OTEL_AGENTS_LIVE = "tool_otelAgents_live"

FAILED_RESULT = "failed"
PASSED_RESULT = "passed"
APPLICATION_JSON_MEDIA_TYPE = "application/json"
DECODE_ERROR_HANDLER = "replace"
DISCONNECT_SIGNAL_ERROR = "failed to write disconnect signal"
UTF_8_ENCODING = "utf-8"


def _utc_now() -> str:
    """Return the current UTC timestamp used in evidence files.

    No parameters are required because all verifier evidence should be stamped
    with the current execution time, not a caller-provided clock value.
    """
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _join_url(base_url: str, endpoint: str) -> str:
    """Combine a configured provider base URL with a provider endpoint.

    Parameters:
    - base_url: Host URL supplied by the runner, such as http://127.0.0.1:18080.
    - endpoint: Absolute provider path, such as /api/clients.
    """
    return f"{base_url.rstrip('/')}{endpoint}"


def _http_json(url: str, *, timeout: float = DEFAULT_HTTP_TIMEOUT_SECONDS) -> tuple[int, Any]:
    """Fetch JSON from a provider endpoint and return status plus payload.

    Parameters:
    - url: Full URL to request.
    - timeout: Per-request timeout in seconds so polling cannot hang forever.
    """
    request = urllib.request.Request(url, headers={ACCEPT_HEADER_KEY: APPLICATION_JSON_MEDIA_TYPE})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode(UTF_8_ENCODING, errors=DECODE_ERROR_HANDLER)
            return int(response.status), json.loads(body) if body.strip() else None
    except urllib.error.HTTPError as http_error:
        body = http_error.read().decode(UTF_8_ENCODING, errors=DECODE_ERROR_HANDLER)
        try:
            payload: Any = json.loads(body) if body.strip() else None
        except json.JSONDecodeError:
            payload = body
        return int(http_error.code), payload


def _write_json(path: Path, payload: Any) -> None:
    """Write a deterministic JSON evidence file.

    Parameters:
    - path: Destination evidence path; parent directories are created.
    - payload: JSON-serializable payload captured from checks or endpoints.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"{json.dumps(payload, indent=2, sort_keys=True)}\n",
        encoding=UTF_8_ENCODING,
    )


def _find_client(
    clients_payload: dict[str, Any],
    service_instance_id: str,
) -> dict[str, Any] | None:
    """Find the ST simulator client inside the provider clients response.

    Parameters:
    - clients_payload: Parsed response from GET /api/clients.
    - service_instance_id: Scenario-specific simulator identifier to match.
    """
    for client_payload in clients_payload.get(CLIENTS_KEY) or []:
        agent_description = str(client_payload.get(AGENT_DESCRIPTION_KEY) or "")
        if service_instance_id in agent_description:
            return client_payload
    return None


def _find_tool_agent(
    agents_payload: dict[str, Any],
    service_instance_id: str,
) -> dict[str, Any] | None:
    """Find the ST simulator agent inside the tool endpoint response.

    Parameters:
    - agents_payload: Parsed response from GET /tool/otelAgents.
    - service_instance_id: Scenario-specific simulator identifier to match.
    """
    for agent_payload in agents_payload.get(AGENTS_KEY) or []:
        agent_description = str(agent_payload.get(AGENT_DESCRIPTION_KEY) or "")
        if service_instance_id in agent_description:
            return agent_payload
    return None


def _wait_for_client(
    *,
    base_url: str,
    service_instance_id: str,
    expected_channel: str,
    timeout_seconds: float,
    evidence_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Poll until the provider shows the live simulator on the expected channel.

    Parameters:
    - base_url: Provider base URL to query.
    - service_instance_id: Simulator identifier expected in the agent metadata.
    - expected_channel: Transport channel that proves the requested profile ran.
    - timeout_seconds: Maximum polling duration before failing the scenario.
    - evidence_dir: Directory for timeout diagnostics if the client never appears.
    """
    deadline = time.monotonic() + timeout_seconds
    last_payload: dict[str, Any] = {}
    while time.monotonic() < deadline:
        status, payload = _http_json(_join_url(base_url, API_CLIENTS_ENDPOINT))
        if status == HTTP_STATUS_OK and isinstance(payload, dict):
            last_payload = payload
            client_payload = _find_client(payload, service_instance_id)
            last_channel = (
                str(client_payload.get(LAST_CHANNEL_KEY) or "").lower()
                if client_payload
                else ""
            )
            if client_payload and last_channel == expected_channel:
                return payload, client_payload
        time.sleep(POLL_INTERVAL_SECONDS)
    _write_json(evidence_dir / API_CLIENTS_TIMEOUT_FILE_NAME, last_payload)
    raise AssertionError(
        f"client {service_instance_id!r} was not visible on channel {expected_channel!r}"
    )


def _wait_for_disconnect(
    *,
    base_url: str,
    service_instance_id: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Poll until the provider records the simulator as disconnected.

    Parameters:
    - base_url: Provider base URL to query.
    - service_instance_id: Simulator identifier expected in the agent metadata.
    - timeout_seconds: Maximum polling duration after the supervisor signal.
    """
    deadline = time.monotonic() + timeout_seconds
    last_client_payload: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        status, payload = _http_json(_join_url(base_url, API_CLIENTS_ENDPOINT))
        if status == HTTP_STATUS_OK and isinstance(payload, dict):
            client_payload = _find_client(payload, service_instance_id)
            if client_payload is not None:
                last_client_payload = client_payload
                if client_payload.get(DISCONNECTED_KEY) is True:
                    return client_payload
        time.sleep(POLL_INTERVAL_SECONDS)
    raise AssertionError(f"client did not report disconnected state: {last_client_payload}")


def _compose_exec_touch_signal(
    *,
    compose_file: Path,
    project_name: str,
    service_name: str,
) -> subprocess.CompletedProcess[str]:
    """Ask Docker Compose to create the supervisor signal inside the consumer.

    Parameters:
    - compose_file: Compose file used for the active scenario.
    - project_name: Compose project name created by the runner.
    - service_name: Consumer service that should receive the stop signal.
    """
    command = [
        "docker",
        "compose",
        "-p",
        project_name,
        "-f",
        str(compose_file),
        "exec",
        "-T",
        service_name,
        "sh",
        "-lc",
        f"touch {SUPERVISOR_SIGNAL_PATH}",
    ]
    return subprocess.run(command, text=True, capture_output=True, check=False)


def _check_payload(name: str, passed: bool, value: Any = "") -> dict[str, Any]:
    """Create a consistently shaped check row for JSON and Markdown output.

    Parameters:
    - name: Stable check identifier.
    - passed: Boolean outcome for the check.
    - value: Evidence value displayed in the Markdown report.
    """
    return {
        CHECK_NAME_KEY: name,
        PASSED_KEY: passed,
        VALUE_KEY: value,
    }


def _required_client_checks(
    client_payload: dict[str, Any],
    expected_channel: str,
) -> list[dict[str, Any]]:
    """Build the field-level checks required for a live client registration.

    Parameters:
    - client_payload: Provider client entry returned by /api/clients.
    - expected_channel: Channel that must match the requested socket/http profile.
    """
    return [
        _check_payload(
            CHECK_INSTANCE_UID,
            bool(str(client_payload.get(CLIENT_ID_KEY) or "").strip()),
            client_payload.get(CLIENT_ID_KEY),
        ),
        _check_payload(
            CHECK_AGENT_DESCRIPTION,
            bool(str(client_payload.get(AGENT_DESCRIPTION_KEY) or "").strip()),
        ),
        _check_payload(
            CHECK_CAPABILITIES,
            bool(client_payload.get(CAPABILITIES_KEY)),
            client_payload.get(CAPABILITIES_KEY),
        ),
        _check_payload(
            CHECK_HEALTH,
            isinstance(client_payload.get(HEALTH_KEY), dict),
            client_payload.get(HEALTH_KEY),
        ),
        _check_payload(
            CHECK_LAST_CHANNEL,
            str(client_payload.get(LAST_CHANNEL_KEY) or "").lower() == expected_channel,
            client_payload.get(LAST_CHANNEL_KEY),
        ),
        _check_payload(
            CHECK_NOT_DISCONNECTED_WHILE_LIVE,
            client_payload.get(DISCONNECTED_KEY) is False,
            client_payload.get(DISCONNECTED_KEY),
        ),
    ]


def _write_report(
    *,
    path: Path,
    scenario: str,
    expected_channel: str,
    service_instance_id: str,
    checks: list[dict[str, Any]],
    evidence_paths: dict[str, str],
    result: str,
) -> None:
    """Write the human-readable Markdown report for the scenario run.

    Parameters:
    - path: Destination Markdown report path.
    - scenario: Profile name, either socket or http.
    - expected_channel: Provider channel expected for the profile.
    - service_instance_id: Simulator identifier used during verification.
    - checks: Ordered check payloads produced by this verifier.
    - evidence_paths: Labels and paths for captured JSON files.
    - result: Final scenario result string.
    """
    lines = [
        f"# {SCENARIO_LABEL} Results - {scenario}",
        "",
        f"- Generated: {_utc_now()}",
        f"- Result: {result}",
        f"- Expected channel: `{expected_channel}`",
        f"- Service instance id: `{service_instance_id}`",
        "",
        "## Verification Checks",
        "",
        "| Check | Result | Evidence |",
        "|---|---:|---|",
    ]
    for check_payload in checks:
        evidence = check_payload.get(VALUE_KEY, "")
        if isinstance(evidence, (dict, list)):
            evidence = json.dumps(evidence, sort_keys=True)
        check_result = "PASS" if check_payload.get(PASSED_KEY) else "FAIL"
        lines.append(f"| {check_payload[CHECK_NAME_KEY]} | {check_result} | `{evidence}` |")

    lines.extend(["", "## Evidence Files", ""])
    for label, value in evidence_paths.items():
        lines.append(f"- {label}: `{value}`")

    lines.extend(
        [
            "",
            f"## {SCENARIO_LABEL} Reconciliation",
            "",
            f"| {SCENARIO_LABEL} expectation | Covered by this artefact |",
            "|---|---|",
            "| Provider starts and serves OpAMP/API traffic | `provider` compose service plus "
            "readiness check on `/api/clients` |",
            "| Consumer connects and sends valid `AgentToServer` messages | `consumer-socket` / "
            "`consumer-http` simulator service and client registration check |",
            "| WebSocket/socket connectivity is prioritized | `socket` profile and "
            "`last_channel=websocket` assertion |",
            "| HTTP connectivity is supported | `http` profile and `last_channel=http` assertion |",
            "| Provider records instance UID, metadata, capabilities, and health | API client "
            "field assertions in this report |",
            "| `/tool/otelAgents` lists the live agent | Tool endpoint assertion and "
            "captured JSON evidence |",
            "| Clean disconnect is visible | Supervisor signal touch plus "
            "`disconnected=true` assertion |",
            "| Evidence is retained for later review | JSON payloads and this Markdown "
            "report under the output directory |",
            "| Real Fluent Bit/Fluentd variants | Documented as optional follow-up profiles; "
            "not required for mandatory simulator pass |",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding=UTF_8_ENCODING)


def main() -> int:
    """Parse arguments, run the scenario checks, and write final evidence.

    No parameters are accepted directly; this entry point reads command-line
    arguments so it can be called from run_st001.sh and from manual debugging.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, choices=(SOCKET_SCENARIO, HTTP_SCENARIO))
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--compose-file", type=Path, required=True)
    parser.add_argument("--compose-project", required=True)
    parser.add_argument("--consumer-service", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_VERIFY_TIMEOUT_SECONDS)
    args = parser.parse_args()

    expected_channel = EXPECTED_CHANNEL_BY_SCENARIO[args.scenario]
    service_instance_id = f"{SCENARIO_SLUG}-simulator-{args.scenario}"
    args.output_dir.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = []
    result = FAILED_RESULT
    evidence_paths: dict[str, str] = {}

    try:
        # First prove the provider sees a live simulator on the expected
        # transport; all later checks are only meaningful after this registration.
        clients_payload, client_payload = _wait_for_client(
            base_url=args.base_url,
            service_instance_id=service_instance_id,
            expected_channel=expected_channel,
            timeout_seconds=args.timeout_seconds,
            evidence_dir=args.output_dir,
        )
        clients_path = args.output_dir / API_CLIENTS_LIVE_FILE_NAME
        _write_json(clients_path, clients_payload)
        evidence_paths[EVIDENCE_API_CLIENTS_LIVE] = str(clients_path)
        checks.extend(_required_client_checks(client_payload, expected_channel))

        query_string = urllib.parse.urlencode({SERVICE_INSTANCE_ID_KEY: service_instance_id})
        tool_status, tool_payload = _http_json(
            f"{_join_url(args.base_url, TOOL_OTEL_AGENTS_ENDPOINT)}?{query_string}"
        )
        tool_path = args.output_dir / TOOL_OTEL_AGENTS_LIVE_FILE_NAME
        _write_json(tool_path, tool_payload)
        evidence_paths[EVIDENCE_TOOL_OTEL_AGENTS_LIVE] = str(tool_path)
        tool_agent = (
            _find_tool_agent(tool_payload, service_instance_id)
            if tool_status == HTTP_STATUS_OK and isinstance(tool_payload, dict)
            else None
        )
        checks.append(
            _check_payload(
                CHECK_TOOL_OTEL_AGENTS_LIVE_AGENT,
                tool_agent is not None,
                {
                    HTTP_STATUS_KEY: tool_status,
                    TOTAL_KEY: (tool_payload or {}).get(TOTAL_KEY),
                },
            )
        )

        # The consumer watches OpAMPSupervisor.signal. Touching it exercises the
        # harness shutdown path and lets the provider prove disconnect tracking.
        signal_result = _compose_exec_touch_signal(
            compose_file=args.compose_file,
            project_name=args.compose_project,
            service_name=args.consumer_service,
        )
        signal_path = args.output_dir / DISCONNECT_SIGNAL_FILE_NAME
        _write_json(
            signal_path,
            {
                RETURN_CODE_KEY: signal_result.returncode,
                STDOUT_KEY: signal_result.stdout,
                STDERR_KEY: signal_result.stderr,
            },
        )
        evidence_paths[EVIDENCE_DISCONNECT_SIGNAL] = str(signal_path)
        checks.append(
            _check_payload(
                CHECK_DISCONNECT_SIGNAL_WRITTEN,
                signal_result.returncode == 0,
                signal_result.returncode,
            )
        )
        if signal_result.returncode != 0:
            raise AssertionError(signal_result.stderr.strip() or DISCONNECT_SIGNAL_ERROR)

        disconnected_client = _wait_for_disconnect(
            base_url=args.base_url,
            service_instance_id=service_instance_id,
            timeout_seconds=DISCONNECT_TIMEOUT_SECONDS,
        )
        disconnected_path = args.output_dir / "api-client-disconnected.json"
        _write_json(disconnected_path, disconnected_client)
        evidence_paths[EVIDENCE_API_CLIENT_DISCONNECTED] = str(disconnected_path)
        checks.append(
            _check_payload(
                CHECK_DISCONNECT_VISIBLE,
                disconnected_client.get(DISCONNECTED_KEY) is True,
                disconnected_client.get(DISCONNECTED_AT_KEY),
            )
        )

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
                SCENARIO_KEY: args.scenario,
                RESULT_KEY: result,
                GENERATED_AT_UTC_KEY: _utc_now(),
                CHECKS_KEY: checks,
                EVIDENCE_PATHS_KEY: evidence_paths,
            },
        )
        evidence_paths[EVIDENCE_SUMMARY] = str(summary_path)
        report_path = args.output_dir / REPORT_FILE_NAME
        _write_report(
            path=report_path,
            scenario=args.scenario,
            expected_channel=expected_channel,
            service_instance_id=service_instance_id,
            checks=checks,
            evidence_paths=evidence_paths,
            result=result,
        )
        print(f"{SCENARIO_LABEL} {args.scenario} result: {result}")
        print(f"Report: {report_path}")

    return 0 if result == PASSED_RESULT else 1


if __name__ == "__main__":
    raise SystemExit(main())
