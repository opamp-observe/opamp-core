#!/usr/bin/env python3
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
#
# Copyright 2026 mp3monster.org

"""Verify provider state and container processes around a UI shutdown command."""

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

API_CLIENTS_ENDPOINT = "/api/clients"
CAPABILITY_FQDN = "org.mp3monster.opamp_provider.command_shutdown_agent"
COMMAND_ACTION = "shutdownagent"
COMMAND_SOURCE = "ui"
DEFAULT_BASE_URL = "http://127.0.0.1:18190"
DEFAULT_TIMEOUT_SECONDS = 180.0
HTTP_STATUS_OK = 200
PROCESS_SUPERVISOR = "supervisor"
PROCESS_AGENT = "agent"
SUPPORTED_AGENT_TYPES = (
    "fluentbit",
    "fluentd",
    "elastic_agent",
    "elastic_heartbeat",
    "vector",
    "simulator",
)
AGENT_PROCESS_MARKERS = {
    "fluentbit": ("/usr/local/bin/fluent-bit",),
    "fluentd": ("/usr/local/bin/fluentd",),
    "elastic_heartbeat": ("/usr/local/bin/heartbeat",),
    "elastic_agent": ("elastic-agent",),
    "vector": ("/usr/local/bin/vector",),
    "simulator": (),
}
AGENT_TYPES_WITH_MANAGED_PROCESS = frozenset(
    agent_type for agent_type, markers in AGENT_PROCESS_MARKERS.items() if markers
)
SUPERVISOR_PROCESS_MARKERS = ("/usr/local/bin/opamp-consumer",)


def _utc_now() -> str:
    """Return a stable UTC timestamp for generated evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: Any) -> None:
    """Write a JSON evidence artifact and create its parent directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _http_json(url: str) -> tuple[int, Any]:
    """GET one provider JSON endpoint and preserve HTTP error payloads."""
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            response_text = response.read().decode("utf-8", errors="replace")
            payload = json.loads(response_text) if response_text.strip() else None
            return int(response.status), payload
    except urllib.error.HTTPError as error:
        response_text = error.read().decode("utf-8", errors="replace")
        try:
            payload = (
                json.loads(response_text) if response_text.strip() else response_text
            )
        except json.JSONDecodeError:
            payload = response_text
        return int(error.code), payload
    except (urllib.error.URLError, ConnectionError, OSError) as error:
        return 0, {"connection_error": repr(error)}


def _find_client(payload: Any, service_instance_id: str) -> dict[str, Any] | None:
    """Find a provider client by its service instance identifier."""
    if not isinstance(payload, dict):
        return None
    for client in payload.get("clients") or []:
        if not isinstance(client, dict):
            continue
        description = str(client.get("agent_description") or "")
        if service_instance_id in description:
            return client
    return None


def _shutdown_command_was_sent(client: dict[str, Any]) -> bool:
    """Return whether the provider recorded a sent shutdown command."""
    for command in client.get("commands") or []:
        if not isinstance(command, dict):
            continue
        if str(command.get("action") or "").strip().lower() == COMMAND_ACTION and bool(
            command.get("sent_at")
        ):
            return True
    return False


def _ui_evidence_is_valid(payload: Any) -> bool:
    """Validate that browser evidence contains the UI-originated shutdown payload."""
    if not isinstance(payload, dict) or payload.get("result") != "passed":
        return False
    if int(payload.get("command_response_status") or 0) != 201:
        return False
    request_payload = payload.get("command_request_payload")
    if not isinstance(request_payload, dict):
        return False
    pairs = request_payload.get("pairs")
    if not isinstance(pairs, list):
        return False
    values = {
        str(pair.get("key") or "").strip().lower(): str(pair.get("value") or "").strip()
        for pair in pairs
        if isinstance(pair, dict)
    }
    return (
        values.get("classifier") == "custom"
        and values.get("operation") == COMMAND_ACTION
        and values.get("capability") == CAPABILITY_FQDN
        and values.get("source") == COMMAND_SOURCE
    )


def _docker_processes(container_name: str) -> list[dict[str, Any]]:
    """Return the Linux process table reported by Docker for one container."""
    completed = subprocess.run(
        ["docker", "top", container_name, "-eo", "pid,args"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"docker top failed for {container_name}: {completed.stderr.strip()}"
        )
    processes: list[dict[str, Any]] = []
    for line in completed.stdout.splitlines()[1:]:
        normalized_line = line.strip()
        if not normalized_line:
            continue
        columns = normalized_line.split(maxsplit=1)
        if len(columns) != 2 or not columns[0].isdigit():
            continue
        processes.append({"pid": int(columns[0]), "command": columns[1]})
    return processes


def _matching_processes(
    processes: list[dict[str, Any]], markers: tuple[str, ...]
) -> list[dict[str, Any]]:
    """Select processes whose command contains one of the expected markers."""
    normalized_markers = tuple(marker.lower() for marker in markers)
    return [
        process
        for process in processes
        if any(
            marker in str(process.get("command") or "").lower()
            for marker in normalized_markers
        )
    ]


def _client_url(base_url: str, service_instance_id: str) -> str:
    """Build the filtered provider clients URL used by both verification phases."""
    encoded_id = urllib.parse.quote(service_instance_id, safe="")
    return (
        f"{base_url.rstrip('/')}{API_CLIENTS_ENDPOINT}?service_instance_id={encoded_id}"
    )


def _wait_for_ready(
    *,
    base_url: str,
    container_name: str,
    service_instance_id: str,
    agent_type: str,
    output_dir: Path,
    timeout_seconds: float,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Wait until provider registration and both expected processes are visible."""
    deadline = time.monotonic() + timeout_seconds
    last_client: dict[str, Any] | None = None
    last_processes: list[dict[str, Any]] = []
    finished_path = output_dir / "consumer-finished"
    exit_code_path = output_dir / "consumer-exit-code.txt"
    while time.monotonic() < deadline:
        if finished_path.exists():
            exit_code = (
                exit_code_path.read_text(encoding="utf-8").strip()
                if exit_code_path.exists()
                else "unknown"
            )
            raise AssertionError(
                f"consumer exited before readiness with exit code {exit_code}"
            )
        status_code, payload = _http_json(_client_url(base_url, service_instance_id))
        if status_code == HTTP_STATUS_OK:
            last_client = _find_client(payload, service_instance_id)
        last_processes = _docker_processes(container_name)
        supervisor_processes = _matching_processes(
            last_processes, SUPERVISOR_PROCESS_MARKERS
        )
        agent_processes = _matching_processes(
            last_processes, AGENT_PROCESS_MARKERS[agent_type]
        )
        managed_agent_ready = (
            bool(agent_processes)
            if agent_type in AGENT_TYPES_WITH_MANAGED_PROCESS
            else True
        )
        capabilities = (
            set(last_client.get("custom_capabilities_reported") or [])
            if last_client is not None
            else set()
        )
        if (
            last_client is not None
            and last_client.get("disconnected") is not True
            and CAPABILITY_FQDN in capabilities
            and supervisor_processes
            and managed_agent_ready
        ):
            return last_client, supervisor_processes, agent_processes
        time.sleep(1)
    raise AssertionError(
        "agent did not become ready before timeout: "
        f"client={last_client!r} processes={last_processes!r}"
    )


def _wait_for_shutdown(
    *,
    base_url: str,
    container_name: str,
    service_instance_id: str,
    agent_type: str,
    output_dir: Path,
    timeout_seconds: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Wait for provider disconnect state and disappearance of both process groups."""
    deadline = time.monotonic() + timeout_seconds
    last_client: dict[str, Any] | None = None
    last_processes: list[dict[str, Any]] = []
    finished_path = output_dir / "consumer-finished"
    while time.monotonic() < deadline:
        status_code, payload = _http_json(_client_url(base_url, service_instance_id))
        if status_code == HTTP_STATUS_OK:
            last_client = _find_client(payload, service_instance_id)
        last_processes = _docker_processes(container_name)
        supervisor_processes = _matching_processes(
            last_processes, SUPERVISOR_PROCESS_MARKERS
        )
        agent_processes = _matching_processes(
            last_processes, AGENT_PROCESS_MARKERS[agent_type]
        )
        if (
            last_client is not None
            and last_client.get("disconnected") is True
            and _shutdown_command_was_sent(last_client)
            and finished_path.exists()
            and not supervisor_processes
            and not agent_processes
        ):
            return last_client, last_processes
        time.sleep(1)
    raise AssertionError(
        "shutdown did not complete before timeout: "
        f"client={last_client!r} processes={last_processes!r} "
        f"consumer_finished={finished_path.exists()}"
    )


def _run_ready_phase(args: argparse.Namespace) -> int:
    """Capture provider and process evidence immediately before UI shutdown."""
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    client, supervisor_processes, agent_processes = _wait_for_ready(
        base_url=args.base_url,
        container_name=args.container_name,
        service_instance_id=args.service_instance_id,
        agent_type=args.agent_type,
        output_dir=output_dir,
        timeout_seconds=args.timeout_seconds,
    )
    _write_json(output_dir / "api-client-live.json", client)
    _write_json(
        output_dir / "processes-before.json",
        {
            PROCESS_SUPERVISOR: supervisor_processes,
            PROCESS_AGENT: agent_processes,
        },
    )
    print(f"{args.agent_type}: provider registration and expected processes are ready")
    return 0


def _write_result_report(
    *, output_dir: Path, agent_type: str, result: str, checks: list[dict[str, Any]]
) -> None:
    """Write machine-readable and Markdown evidence for one agent iteration."""
    summary = {
        "agent_type": agent_type,
        "generated_at_utc": _utc_now(),
        "result": result,
        "checks": checks,
    }
    _write_json(output_dir / "summary.json", summary)
    report_lines = [
        f"# {agent_type} Agent Shutdown Results",
        "",
        f"- Generated: {summary['generated_at_utc']}",
        f"- Result: {result}",
        "",
        "| Check | Result | Evidence |",
        "|---|---:|---|",
    ]
    for check in checks:
        evidence = json.dumps(check.get("value"), sort_keys=True)
        check_result = "PASS" if check["passed"] else "FAIL"
        report_lines.append(
            f"| {check['name']} | {check_result} | `{evidence}` |"
        )
    (output_dir / "results.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )


def _run_confirm_phase(args: argparse.Namespace) -> int:
    """Confirm browser dispatch, clean process exit, and provider disconnect state."""
    output_dir = args.output_dir.resolve()
    checks: list[dict[str, Any]] = []
    try:
        client, remaining_processes = _wait_for_shutdown(
            base_url=args.base_url,
            container_name=args.container_name,
            service_instance_id=args.service_instance_id,
            agent_type=args.agent_type,
            output_dir=output_dir,
            timeout_seconds=args.timeout_seconds,
        )
        ui_evidence = json.loads(
            (output_dir / "ui-shutdown.json").read_text(encoding="utf-8")
        )
        exit_code = int(
            (output_dir / "consumer-exit-code.txt").read_text(encoding="utf-8").strip()
        )
        checks.extend(
            [
                {
                    "name": "shutdown_issued_from_provider_ui",
                    "passed": _ui_evidence_is_valid(ui_evidence),
                    "value": ui_evidence,
                },
                {
                    "name": "provider_marked_shutdown_command_sent",
                    "passed": _shutdown_command_was_sent(client),
                    "value": client.get("commands"),
                },
                {
                    "name": "provider_marked_agent_disconnected",
                    "passed": client.get("disconnected") is True,
                    "value": client.get("disconnected_at"),
                },
                {
                    "name": "consumer_supervisor_exited_cleanly",
                    "passed": exit_code == 0,
                    "value": exit_code,
                },
                {
                    "name": "supervisor_process_absent",
                    "passed": not _matching_processes(
                        remaining_processes, SUPERVISOR_PROCESS_MARKERS
                    ),
                    "value": remaining_processes,
                },
                {
                    "name": "managed_agent_process_absent",
                    "passed": not _matching_processes(
                        remaining_processes, AGENT_PROCESS_MARKERS[args.agent_type]
                    ),
                    "value": remaining_processes,
                },
            ]
        )
        _write_json(output_dir / "api-client-shutdown.json", client)
        _write_json(output_dir / "processes-after.json", remaining_processes)
    except Exception as error:  # pylint: disable=broad-exception-caught
        checks.append(
            {"name": "verification_completed", "passed": False, "value": repr(error)}
        )
    result = (
        "passed" if checks and all(check["passed"] for check in checks) else "failed"
    )
    _write_result_report(
        output_dir=output_dir,
        agent_type=args.agent_type,
        result=result,
        checks=checks,
    )
    print(f"{args.agent_type}: shutdown verification {result}")
    return 0 if result == "passed" else 1


def _run_aggregate_phase(args: argparse.Namespace) -> int:
    """Combine all supported-agent summaries into one scenario report."""
    output_dir = args.output_dir.resolve()
    agent_results: list[dict[str, Any]] = []
    required_agent_types = (
        getattr(args, "required_agent_type", None) or SUPPORTED_AGENT_TYPES
    )
    for agent_type in required_agent_types:
        summary_path = output_dir / agent_type / "summary.json"
        if not summary_path.exists():
            agent_results.append(
                {
                    "agent_type": agent_type,
                    "result": "missing",
                    "summary": str(summary_path),
                }
            )
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        agent_results.append(
            {
                "agent_type": agent_type,
                "result": summary.get("result"),
                "summary": str(summary_path),
            }
        )
    passed = all(item["result"] == "passed" for item in agent_results)
    aggregate = {
        "generated_at_utc": _utc_now(),
        "result": "passed" if passed else "failed",
        "agents": agent_results,
    }
    _write_json(output_dir / "summary.json", aggregate)
    report_lines = [
        "# Agent Shutdown E2E Results",
        "",
        f"- Generated: {aggregate['generated_at_utc']}",
        f"- Result: {aggregate['result']}",
        "",
        "| Agent | Result | Summary |",
        "|---|---:|---|",
    ]
    for agent_result in agent_results:
        report_lines.append(
            f"| {agent_result['agent_type']} | {agent_result['result']} | "
            f"`{agent_result['summary']}` |"
        )
    (output_dir / "results.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )
    return 0 if passed else 1


def _build_parser() -> argparse.ArgumentParser:
    """Build command-line arguments for ready, confirm, and aggregate phases."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase", choices=("ready", "confirm", "aggregate"), required=True
    )
    parser.add_argument("--agent-type", choices=SUPPORTED_AGENT_TYPES)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--container-name")
    parser.add_argument("--service-instance-id")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS
    )
    parser.add_argument(
        "--required-agent-type",
        action="append",
        choices=SUPPORTED_AGENT_TYPES,
        help="Agent type required by aggregate phase; repeat for multiple types.",
    )
    return parser


def main() -> int:
    """Execute the requested verification phase and return a process exit code."""
    parser = _build_parser()
    args = parser.parse_args()
    if args.phase == "aggregate":
        return _run_aggregate_phase(args)
    required_values = {
        "agent_type": args.agent_type,
        "container_name": args.container_name,
        "service_instance_id": args.service_instance_id,
    }
    missing = [key for key, value in required_values.items() if not value]
    if missing:
        parser.error(f"phase {args.phase} requires: {', '.join(missing)}")
    if args.phase == "ready":
        return _run_ready_phase(args)
    return _run_confirm_phase(args)


if __name__ == "__main__":
    raise SystemExit(main())
