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

"""Run the ST-009 ten-client provider and simulator launcher integration check."""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

CLIENTS_KEY = "clients"
CLIENT_VERSION_KEY = "client_version"
CONFIG_PATH_KEY = "config_path"
CONFIG_VERSION_KEY = "config_version"
CONSUMER_KEY = "consumer"
DISCONNECTED_KEY = "disconnected"
ENTRYPOINT_KEY = "entrypoint"
ENV_APP_ENABLE_DEV_FEATURES = "APP_ENABLE_DEV_FEATURES"
ENV_CONSUMER_SIM_CONFIG = "CONSUMER_SIM_CONFIG"
ENV_OPAMP_CONFIG_PATH = "OPAMP_CONFIG_PATH"
ENV_KEY = "env"
AGENT_ADDITIONAL_PARAMS_KEY = "agent-additional-params"
AGENT_CONFIG_PATH_KEY = "agent_config_path"
AGENT_DESCRIPTION_KEY = "agent_description"
ALLOW_EFFECTIVE_CONFIG_KEY = "allow-effective-config"
ALLOW_REMOTE_CONFIG_KEY = "allow-remote-config"
CLIENT_ID_KEY = "client_id"
ENABLED_KEY = "enabled"
HEARTBEAT_FREQUENCY_KEY = "heartbeat_frequency"
HEARTBEAT_FREQUENCY_SECONDS = 5
LOG_LEVEL_KEY = "log_level"
HTTP_OK = 200
INSTANCES_KEY = "instances"
INSTANCE_PREFIX = "st009-simulator-"
NAME_KEY = "name"
OPAMP_USE_AUTHORIZATION_KEY = "opamp-use-authorization"
OVERRIDES_KEY = "overrides"
PROVIDER_KEY = "provider"
POLL_INTERVAL_SECONDS = 0.5
PROCESS_TIMEOUT_SECONDS = 120
RESPONSES_KEY = "responses"
STATE_FILE_KEY = "state_file"
SERVICE_INSTANCE_UID_KEY = "service_instance_uid"
SERVER_AUTHORIZATION_KEY = "server-authorization"
SERVER_URL_KEY = "server_url"
SERVICE_TYPE_KEY = "service_type"
SIMULATOR_RESPONSES_PATH_KEY = "simulator_responses_path"
STATE_PERSISTENCE_KEY = "state_persistence"
TLS_KEY = "tls"
TRANSPORT_KEY = "transport"
UI_USE_AUTHORIZATION_KEY = "ui-use-authorization"
UTF8_ENCODING = "utf-8"
VERIFY_SERVER_KEY = "verify_server"
WEBUI_PORT_KEY = "webui_port"
WORKING_DIR_KEY = "working_dir"


def _free_port() -> int:
    """Reserve and return a currently unused loopback TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _write_json(path: Path, payload: Any) -> None:
    """Write a JSON fixture or evidence payload to the requested path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding=UTF8_ENCODING)


def _read_clients(provider_url: str) -> dict[str, Any]:
    """Read the provider client catalog, returning an empty payload while unavailable."""
    try:
        with urllib.request.urlopen(f"{provider_url}/api/clients", timeout=3) as response:
            if int(response.status) != HTTP_OK:
                return {}
            payload = json.loads(response.read().decode(UTF8_ENCODING))
            return payload if isinstance(payload, dict) else {}
    except (OSError, urllib.error.URLError, ValueError):
        return {}


def _scenario_clients(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return provider client records carrying the ST-009 identity prefix."""
    clients = payload.get(CLIENTS_KEY)
    if not isinstance(clients, list):
        return []
    return [
        client
        for client in clients
        if isinstance(client, dict) and INSTANCE_PREFIX in json.dumps(client)
    ]


def _wait_for_client_state(
    provider_url: str,
    *,
    expected_count: int,
    disconnected: bool,
) -> dict[str, Any]:
    """Poll until all expected scenario clients reach the requested connection state."""
    deadline = time.monotonic() + PROCESS_TIMEOUT_SECONDS
    latest_payload: dict[str, Any] = {}
    while time.monotonic() < deadline:
        latest_payload = _read_clients(provider_url)
        clients = _scenario_clients(latest_payload)
        client_ids = {str(client.get(CLIENT_ID_KEY, "")) for client in clients}
        descriptions = "\n".join(str(client.get(AGENT_DESCRIPTION_KEY, "")) for client in clients)
        expected_identities = {
            f"{INSTANCE_PREFIX}{instance_number:02d}"
            for instance_number in range(1, expected_count + 1)
        }
        if (
            len(clients) == expected_count
            and len(client_ids) == expected_count
            and all(identity in descriptions for identity in expected_identities)
            and all(bool(client.get(DISCONNECTED_KEY)) is disconnected for client in clients)
        ):
            return latest_payload
        time.sleep(POLL_INTERVAL_SECONDS)
    raise RuntimeError(
        "provider did not report "
        f"{expected_count} ST-009 clients with disconnected={disconnected}; "
        f"last payload={latest_payload}"
    )


def _terminate_process(process: subprocess.Popen[str]) -> None:
    """Stop a child process without leaving the container test harness blocked."""
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def _run_scenario(  # pylint: disable=too-many-locals
    output_dir: Path,
    scale_count: int,
) -> None:
    """Generate isolated config, connect a simulator batch, and verify clean shutdown."""
    with tempfile.TemporaryDirectory(prefix="opamp-st009-") as temp_name:
        temp_root = Path(temp_name)
        provider_port = _free_port()
        provider_url = f"http://127.0.0.1:{provider_port}"
        provider_config_path = temp_root / "provider.json"
        consumer_config_path = temp_root / "consumer.json"
        launcher_config_path = temp_root / "launcher.json"
        response_path = temp_root / "responses.json"
        agent_config_path = temp_root / "agent.yaml"
        state_path = temp_root / "launcher-state.json"
        provider_log_path = output_dir / "provider.log"

        _write_json(
            provider_config_path,
            {
                PROVIDER_KEY: {
                    WEBUI_PORT_KEY: provider_port,
                    LOG_LEVEL_KEY: "DEBUG",
                    ALLOW_REMOTE_CONFIG_KEY: True,
                    ALLOW_EFFECTIVE_CONFIG_KEY: True,
                    OPAMP_USE_AUTHORIZATION_KEY: "none",
                    UI_USE_AUTHORIZATION_KEY: "none",
                    STATE_PERSISTENCE_KEY: {ENABLED_KEY: False},
                    TLS_KEY: {ENABLED_KEY: False},
                }
            },
        )
        _write_json(response_path, {RESPONSES_KEY: {"*": ["accept"]}})
        agent_config_path.write_text("service:\n  flush: 1\n", encoding=UTF8_ENCODING)
        _write_json(
            consumer_config_path,
            {
                CONSUMER_KEY: {
                    SERVER_URL_KEY: provider_url,
                    TRANSPORT_KEY: "http",
                    TLS_KEY: {VERIFY_SERVER_KEY: False},
                    SERVER_AUTHORIZATION_KEY: "none",
                    AGENT_CONFIG_PATH_KEY: str(agent_config_path),
                    HEARTBEAT_FREQUENCY_KEY: HEARTBEAT_FREQUENCY_SECONDS,
                    SERVICE_TYPE_KEY: "simulator",
                    SIMULATOR_RESPONSES_PATH_KEY: str(response_path),
                    LOG_LEVEL_KEY: "debug",
                }
            },
        )
        instances = []
        for instance_number in range(1, scale_count + 1):
            instance_id = f"{INSTANCE_PREFIX}{instance_number:02d}"
            instances.append(
                {
                    NAME_KEY: instance_id,
                    ENTRYPOINT_KEY: "simulator",
                    CONFIG_PATH_KEY: str(consumer_config_path),
                    WORKING_DIR_KEY: str(temp_root),
                    ENV_KEY: {ENV_OPAMP_CONFIG_PATH: str(consumer_config_path)},
                    OVERRIDES_KEY: {
                        AGENT_ADDITIONAL_PARAMS_KEY: [
                            json.dumps(
                                {
                                    SERVICE_INSTANCE_UID_KEY: instance_id,
                                    CLIENT_VERSION_KEY: "ST009 simulator",
                                    CONFIG_VERSION_KEY: "st009-config",
                                }
                            )
                        ],
                    },
                }
            )
        _write_json(
            launcher_config_path,
            {STATE_FILE_KEY: str(state_path), INSTANCES_KEY: instances},
        )

        provider_environment = os.environ.copy()
        provider_environment[ENV_OPAMP_CONFIG_PATH] = str(provider_config_path)
        with provider_log_path.open("w", encoding=UTF8_ENCODING) as provider_log:
            provider_process = subprocess.Popen(  # pylint: disable=consider-using-with
                ["opamp-provider", "--host", "127.0.0.1", "--port", str(provider_port)],
                env=provider_environment,
                stdout=provider_log,
                stderr=subprocess.STDOUT,
                text=True,
            )
        launcher_environment = os.environ.copy()
        launcher_environment[ENV_APP_ENABLE_DEV_FEATURES] = "true"
        launcher_environment[ENV_CONSUMER_SIM_CONFIG] = str(launcher_config_path)
        try:
            deadline = time.monotonic() + PROCESS_TIMEOUT_SECONDS
            while time.monotonic() < deadline and not _read_clients(provider_url):
                if provider_process.poll() is not None:
                    raise RuntimeError(f"provider exited early with {provider_process.returncode}")
                time.sleep(POLL_INTERVAL_SECONDS)
            subprocess.run(
                ["opamp-consumer-sim", "start"],
                env=launcher_environment,
                check=True,
                timeout=PROCESS_TIMEOUT_SECONDS,
            )
            state_payload = json.loads(state_path.read_text(encoding=UTF8_ENCODING))
            assert len(state_payload[INSTANCES_KEY]) == scale_count
            connected_payload = _wait_for_client_state(
                provider_url,
                expected_count=scale_count,
                disconnected=False,
            )
            _write_json(output_dir / "clients-connected.json", connected_payload)
            subprocess.run(
                ["opamp-consumer-sim", "stop"],
                env=launcher_environment,
                check=True,
                timeout=PROCESS_TIMEOUT_SECONDS,
            )
            assert not state_path.exists()
            disconnected_payload = _wait_for_client_state(
                provider_url,
                expected_count=scale_count,
                disconnected=True,
            )
            _write_json(output_dir / "clients-disconnected.json", disconnected_payload)
        finally:
            _terminate_process(provider_process)


def main() -> int:
    """Parse container arguments and execute the ST-009 integration scenario."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--scale-count", type=int, default=10)
    arguments = parser.parse_args()
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    _run_scenario(arguments.output_dir, arguments.scale_count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
