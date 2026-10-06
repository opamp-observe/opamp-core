#!/usr/bin/env python3
"""Verify the Vector plugin provider/consumer E2E scenario."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = "http://127.0.0.1:18180"
API_CLIENTS_ENDPOINT = "/api/clients"
SERVICE_INSTANCE_ID = "vector-plugin-e2e"
HTTP_STATUS_OK = 200


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _http_json(url: str) -> tuple[int, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8", errors="replace")
            return int(response.status), json.loads(body) if body.strip() else None
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        try:
            payload: Any = json.loads(body) if body.strip() else body
        except json.JSONDecodeError:
            payload = body
        return int(error.code), payload


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _find_client(payload: dict[str, Any]) -> dict[str, Any] | None:
    for client in payload.get("clients") or []:
        description = str(client.get("agent_description") or "")
        if SERVICE_INSTANCE_ID in description and "Vector" in description:
            return client
    return None


def _health_reports_ok(client: dict[str, Any]) -> bool:
    health = client.get("health")
    if not isinstance(health, dict):
        return False

    def truthy(value: Any) -> bool:
        return value is True or str(value).strip().lower() in {"1", "true", "yes"}

    if truthy(health.get("healthy")):
        return True
    if str(health.get("status") or "").strip().lower() in {"ok", "healthy"}:
        return True

    component_map = health.get("component_health_map")
    if isinstance(component_map, dict):
        for component in component_map.values():
            if not isinstance(component, dict):
                continue
            component_status = str(component.get("status") or "").strip().lower()
            if truthy(component.get("healthy")) and component_status in {"ok", "healthy"}:
                return True

    return False


def _wait_for_vector_client(
    *,
    base_url: str,
    timeout_seconds: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    deadline = time.monotonic() + timeout_seconds
    last_payload: dict[str, Any] = {}
    while time.monotonic() < deadline:
        status, payload = _http_json(f"{base_url.rstrip('/')}{API_CLIENTS_ENDPOINT}")
        if status == HTTP_STATUS_OK and isinstance(payload, dict):
            last_payload = payload
            client = _find_client(payload)
            if (
                client is not None
                and str(client.get("last_channel") or "").lower() == "http"
                and _health_reports_ok(client)
            ):
                return payload, client
        time.sleep(1)
    raise AssertionError(f"Vector client did not report ok in provider API: {last_payload}")


def _check_vector_output(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "missing"
    text = path.read_text(encoding="utf-8", errors="replace")
    if "vector_" not in text:
        return False, "no vector metric names found"
    return True, f"{path.stat().st_size} bytes"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--vector-output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=180)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []
    result = "failed"
    evidence: dict[str, str] = {}

    try:
        clients_payload, client = _wait_for_vector_client(
            base_url=args.base_url,
            timeout_seconds=args.timeout_seconds,
        )
        clients_path = args.output_dir / "api-clients-live.json"
        _write_json(clients_path, clients_payload)
        evidence["api_clients_live"] = str(clients_path)
        checks.extend(
            [
                {"name": "provider_sees_vector_plugin", "passed": True, "value": client.get("client_id")},
                {
                    "name": "vector_plugin_reports_ok",
                    "passed": _health_reports_ok(client),
                    "value": client.get("health"),
                },
                {
                    "name": "consumer_connected_over_http",
                    "passed": str(client.get("last_channel") or "").lower() == "http",
                    "value": client.get("last_channel"),
                },
            ]
        )
        output_ok, output_value = _check_vector_output(args.vector_output)
        checks.append(
            {
                "name": "vector_self_monitor_output_written",
                "passed": output_ok,
                "value": output_value,
            }
        )
        result = "passed" if all(check["passed"] for check in checks) else "failed"
    except Exception as error:
        checks.append({"name": "verification_exception", "passed": False, "value": repr(error)})
    finally:
        summary = {
            "generated_at_utc": _utc_now(),
            "result": result,
            "service_instance_id": SERVICE_INSTANCE_ID,
            "checks": checks,
            "evidence": evidence,
        }
        summary_path = args.output_dir / "summary.json"
        _write_json(summary_path, summary)
        report_lines = [
            "# Vector Plugin E2E Results",
            "",
            f"- Generated: {_utc_now()}",
            f"- Result: {result}",
            "",
            "| Check | Result | Evidence |",
            "|---|---:|---|",
        ]
        for check in checks:
            value = check.get("value", "")
            if isinstance(value, (dict, list)):
                value = json.dumps(value, sort_keys=True)
            report_lines.append(
                f"| {check['name']} | {'PASS' if check['passed'] else 'FAIL'} | `{value}` |"
            )
        (args.output_dir / "results.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
        print(f"Vector plugin E2E result: {result}")
    return 0 if result == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
