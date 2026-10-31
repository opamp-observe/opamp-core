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

"""End-to-end socket integration test for provider OpAMP websocket transport."""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PROVIDER_SRC = REPO_ROOT / "provider" / "src"
for _path in (REPO_ROOT, PROVIDER_SRC):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from opamp_provider.proto import opamp_pb2  # noqa: E402 - path setup required above.
from opamp_provider.transport import decode_message, encode_message  # noqa: E402 - path setup required above.

websockets = pytest.importorskip("websockets")

SUMMARY_PATH_ENV = "OPAMP_SOCKET_E2E_SUMMARY_PATH"
DEFAULT_SUMMARY_PATH = REPO_ROOT / "dist" / "test-reports" / "socket_e2e_summary.json"


def _utc_now() -> str:
    """Return current UTC timestamp in ISO-8601."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _pick_free_port() -> int:
    """Return one available local TCP port for transient test server startup."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _provider_subprocess_env() -> dict[str, str]:
    """Build subprocess environment with PYTHONPATH for provider module startup."""
    env = os.environ.copy()
    # The provider app is launched as a subprocess via `python -m opamp_provider.server`.
    # Ensure that process resolves local repo modules from this checkout.
    py_paths = [str(PROVIDER_SRC), str(REPO_ROOT)]
    existing = str(env.get("PYTHONPATH", "")).strip()
    if existing:
        py_paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(py_paths)
    return env


def _tail_text(path: pathlib.Path, *, max_lines: int = 80) -> str:
    """Return trailing lines from one text file for failure/summary context."""
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[-max_lines:])


def _http_json(
    *,
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout_seconds: float = 3.0,
) -> tuple[int, Any]:
    """Perform one HTTP request and return status code plus decoded JSON when possible."""
    data: bytes | None = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8", errors="replace").strip()
            if not body:
                return response.status, None
            try:
                return response.status, json.loads(body)
            except json.JSONDecodeError:
                return response.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace").strip()
        if not body:
            return int(exc.code), None
        try:
            return int(exc.code), json.loads(body)
        except json.JSONDecodeError:
            return int(exc.code), body


def _wait_for_provider_ready(
    *,
    base_url: str,
    process: subprocess.Popen[str],
    log_path: pathlib.Path,
    timeout_seconds: float = 25.0,
) -> None:
    """Poll `/api/clients` until provider is serving traffic or fail with context."""
    # Readiness signal: API responds with 200.
    # This keeps the websocket step deterministic instead of racing provider startup.
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                "provider exited before readiness check completed; "
                f"returncode={process.returncode}\n{_tail_text(log_path)}"
            )
        try:
            status_code, _ = _http_json(url=f"{base_url}/api/clients")
            if status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.25)
    raise TimeoutError(
        f"provider did not become ready within {timeout_seconds:.1f}s\n{_tail_text(log_path)}"
    )


async def _ws_round_trip(
    *,
    ws_url: str,
    agent_message: opamp_pb2.AgentToServer,
) -> tuple[int, opamp_pb2.ServerToAgent]:
    """Send one websocket AgentToServer message and return decoded ServerToAgent."""
    # Use the same transport framing helpers as the provider (varint header + payload)
    # so this is a real protocol-level round-trip, not a mocked exchange.
    async with websockets.connect(ws_url, open_timeout=5, close_timeout=2) as ws:
        await ws.send(encode_message(agent_message.SerializeToString()))
        raw_response = await asyncio.wait_for(ws.recv(), timeout=7)
    if isinstance(raw_response, str):
        raw_response = raw_response.encode("utf-8")
    header, payload = decode_message(raw_response)
    server_message = opamp_pb2.ServerToAgent()
    server_message.ParseFromString(payload)
    return header, server_message


def _summary_path() -> pathlib.Path:
    """Return filesystem path where E2E summary should be written."""
    configured = str(os.environ.get(SUMMARY_PATH_ENV, "")).strip()
    if configured:
        return pathlib.Path(configured).expanduser().resolve()
    return DEFAULT_SUMMARY_PATH.resolve()


def _write_summary(summary: dict[str, Any]) -> pathlib.Path:
    """Persist JSON summary and return written path."""
    path = _summary_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(summary, indent=2)}\n", encoding="utf-8")
    return path


def test_socket_e2e_websocket_roundtrip_publishes_summary(
    tmp_path: pathlib.Path,
    record_property: pytest.RecordProperty,
) -> None:
    """Run provider + websocket client round-trip over real sockets and publish a summary."""
    # Build isolated, per-test provider config on a random local port to avoid conflicts.
    provider_port = _pick_free_port()
    base_url = f"http://127.0.0.1:{provider_port}"
    ws_url = f"ws://127.0.0.1:{provider_port}/v1/opamp"
    client_id = "11111111222222223333333344444444"
    provider_log_path = tmp_path / "provider_socket_e2e.log"
    provider_config_path = tmp_path / "provider_socket_e2e.json"
    provider_config_path.write_text(
        json.dumps(
            {
                "provider": {
                    "webui_port": provider_port,
                    "log_level": "INFO",
                    "opamp-use-authorization": "none",
                    "ui-use-authorization": "none",
                    "state_persistence": {"enabled": False},
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    started_at = time.monotonic()
    summary: dict[str, Any] = {
        "name": "socket_e2e_websocket_roundtrip",
        "started_at_utc": _utc_now(),
        "result": "running",
        "provider": {
            "base_url": base_url,
            "ws_url": ws_url,
            "config_path": str(provider_config_path),
            "log_path": str(provider_log_path),
        },
        "checks": [],
    }

    log_handle = provider_log_path.open("w", encoding="utf-8")
    # Launch provider in a real subprocess so we exercise network sockets end-to-end.
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "opamp_provider.server",
            "--config-path",
            str(provider_config_path),
            "--host",
            "127.0.0.1",
            "--port",
            str(provider_port),
        ],
        cwd=str(REPO_ROOT),
        env=_provider_subprocess_env(),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    summary["provider"]["pid"] = process.pid

    raised_error: Exception | None = None
    try:
        # 1) Wait until provider is actually ready.
        _wait_for_provider_ready(
            base_url=base_url,
            process=process,
            log_path=provider_log_path,
        )
        summary["checks"].append({"step": "provider_ready", "status": "ok"})

        # 2) Capture initial client state.
        pre_status, pre_payload = _http_json(url=f"{base_url}/api/clients")
        assert pre_status == 200
        pre_total = int((pre_payload or {}).get("total", -1))
        summary["checks"].append(
            {
                "step": "initial_clients",
                "status": "ok",
                "http_status": pre_status,
                "total": pre_total,
            }
        )

        # 3) Send one websocket AgentToServer payload and validate transport response.
        outgoing = opamp_pb2.AgentToServer(instance_uid=bytes.fromhex(client_id))
        outgoing.sequence_num = 1
        outgoing.capabilities = opamp_pb2.AgentCapabilities.AgentCapabilities_ReportsStatus
        header, incoming = asyncio.run(_ws_round_trip(ws_url=ws_url, agent_message=outgoing))
        assert header == 0
        assert incoming.instance_uid == outgoing.instance_uid
        summary["checks"].append(
            {
                "step": "websocket_roundtrip",
                "status": "ok",
                "header": header,
                "response_instance_uid": incoming.instance_uid.hex(),
            }
        )

        # 4) Verify provider has persisted the client and recorded websocket channel.
        # Give provider a short window to persist/update in-memory client listing.
        time.sleep(0.5)
        list_status, list_payload = _http_json(url=f"{base_url}/api/clients")
        assert list_status == 200
        payload = list_payload or {}
        clients = payload.get("clients") or []
        matched = [item for item in clients if item.get("client_id") == client_id]
        assert matched, f"expected client {client_id} in /api/clients response"
        last_channel = str(matched[0].get("last_channel") or "")
        assert last_channel.lower() == "websocket"
        summary["checks"].append(
            {
                "step": "client_list_after_ws",
                "status": "ok",
                "http_status": list_status,
                "total": int(payload.get("total", 0)),
                "matched_client_id": client_id,
                "last_channel": last_channel,
            }
        )

        summary["result"] = "passed"
    except Exception as exc:  # pragma: no cover - explicit summary capture path.
        # Preserve failure detail in summary artifact before re-raising.
        raised_error = exc
        summary["result"] = "failed"
        summary["error"] = repr(exc)
    finally:
        shutdown_result: dict[str, Any] = {"attempted": False}
        if process.poll() is None:
            # Ask provider to shutdown gracefully first; fall back to terminate/kill below.
            shutdown_result["attempted"] = True
            try:
                status, payload = _http_json(
                    url=f"{base_url}/api/shutdown",
                    method="POST",
                    payload={"confirm": True},
                    timeout_seconds=5.0,
                )
                shutdown_result["http_status"] = status
                shutdown_result["response"] = payload
            except Exception as exc:  # pragma: no cover - defensive logging path.
                shutdown_result["error"] = repr(exc)

        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        finally:
            log_handle.close()

        # Always publish a machine-readable summary (pass or fail) for CI/debug visibility.
        summary["provider"]["shutdown"] = shutdown_result
        summary["provider"]["return_code"] = process.returncode
        summary["provider"]["log_tail"] = _tail_text(provider_log_path)
        summary["finished_at_utc"] = _utc_now()
        summary["duration_seconds"] = round(time.monotonic() - started_at, 3)
        summary_path = _write_summary(summary)
        record_property("socket_e2e_summary_path", str(summary_path))
        record_property("socket_e2e_result", summary.get("result", "unknown"))
        print("socket e2e summary:")
        print(json.dumps(summary, indent=2))
        print(f"socket e2e summary file: {summary_path}")

    if raised_error is not None:
        raise raised_error
