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

"""Exercise ST-007 against live provider and simulator processes."""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import signal
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_PREFIX = "/svr-credentials-manager-service/api/v1"
CLIENT_A_UID = "st007-live-client-a"
CLIENT_B_UID = "st007-live-client-b"
CONNECTION_PRIMARY = "primary"
CONNECTION_SECONDARY = "secondary"
CONNECTION_TEMPORARY = "temporary"
CONSUMER_LOG_NEEDLE = "secondary.collector.test"
CONSUMER_UNSUPPORTED_NEEDLE = "---- to be implemented ----"
CREDENTIALS_PORT = 18091
FALLBACK_PORT = 18092
HTTP_BAD_REQUEST = 400
HTTP_NO_CONTENT = 204
HTTP_OK = 200
HTTP_CREATED = 201
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_PROXY_TENANT = "X-Proxy-Tenant"
HEADER_ST007_ACCESS = "X-ST007-Access"
MEDIA_TYPE_JSON = "application/json"
POLL_INTERVAL_SECONDS = 0.5
PROCESS_TIMEOUT_SECONDS = 90
PROVIDER_PORT = 18080
UTF8_ENCODING = "utf-8"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

KEY_AGENT_ADDITIONAL_PARAMS = "agent_additional_params"
KEY_AGENT_CONFIG_PATH = "agent_config_path"
KEY_ALLOW_CONNECTION_SETTINGS = "allow-connection-settings"
KEY_ALLOW_CONNECTION_SETTINGS_REQUEST = "allow-connection-settings-request"
KEY_ALLOW_EFFECTIVE_CONFIG = "allow-effective-config"
KEY_ALLOW_REMOTE_CONFIG = "allow-remote-config"
KEY_APPLIED_AT_UTC = "applied_at_utc"
KEY_ARCHIVE = "archive"
KEY_CLIENT_ID = "client_id"
KEY_CLIENT_STATUS_PORT = "client_status_port"
KEY_CLIENT_VERSION = "client_version"
KEY_CLIENTS = "clients"
KEY_CONFIG_VERSION = "config_version"
KEY_CONNECTION_NAME = "connection_name"
KEY_CONNECTION_SETTINGS = "connection_settings"
KEY_CONNECT_HEADERS = "connect_headers"
KEY_CONSUMER = "consumer"
KEY_DEFINITION = "definition"
KEY_DELIVERY = "delivery"
KEY_DESTINATION_ENDPOINT = "destination_endpoint"
KEY_DISCONNECTED = "disconnected"
KEY_ENABLED = "enabled"
KEY_ERROR = "error"
KEY_FALLBACK_DELIVERY_COUNT = "fallback_delivery_count"
KEY_HEADERS = "headers"
KEY_HEARTBEAT_FREQUENCY = "heartbeat_frequency"
KEY_LOG_LEVEL = "log_level"
KEY_LIVE_CLIENTS = "live_clients"
KEY_MAPPINGS = "mappings"
KEY_NAME = "name"
KEY_NAMES = "names"
KEY_OPAMP_AUTH = "opamp-use-authorization"
KEY_OTHER_CONNECTIONS = "other_connections"
KEY_OTHER_SETTINGS = "other_settings"
KEY_OWN_LOGS = "own_logs"
KEY_OWN_METRICS = "own_metrics"
KEY_OWN_TRACES = "own_traces"
KEY_OPAMP = "opamp"
KEY_PASSED = "passed"
KEY_PROVIDER = "provider"
KEY_PROVIDER_DELIVERY_CLIENT = "provider_delivery_client"
KEY_PROXY = "proxy"
KEY_RECONCILIATION = "reconciliation"
KEY_RESPONSES = "responses"
KEY_RETRIES = "retries"
KEY_RATIO = "ratio"
KEY_RESULTS = "results"
KEY_SCENARIO = "scenario"
KEY_SERVER_AUTHORIZATION = "server-authorization"
KEY_SERVER_TO_AGENT = "server_to_agent"
KEY_SERVER_URL = "server_url"
KEY_SERVICE_INSTANCE_UID = "service_instance_uid"
KEY_SERVICE_NAME = "service_name"
KEY_SERVICE_NAMESPACE = "service_namespace"
KEY_SERVICE_TYPE = "service_type"
KEY_SIMULATOR_RESPONSES_PATH = "simulator_responses_path"
KEY_STATE_PERSISTENCE = "state_persistence"
KEY_STATUS = "status"
KEY_TENANT = "tenant"
KEY_TLS = "tls"
KEY_TRANSPORT = "transport"
KEY_UI_AUTH = "ui-use-authorization"
KEY_URL = "url"
KEY_VERIFY_SERVER = "verify_server"
KEY_WEBUI_PORT = "webui_port"

ENV_APP_ENABLE_DEV_FEATURES = "APP_ENABLE_DEV_FEATURES"
ENV_OPAMP_CONFIG_PATH = "OPAMP_CONFIG_PATH"

VALUE_ACCEPT = "accept"
VALUE_FALLBACK_LOG = "fallback_log"
VALUE_PROVIDER_QUEUE = "provider_queue"
VALUE_WILDCARD = "*"


def _write_json(path: Path, payload: Any) -> None:
    """Write one formatted JSON fixture or evidence document.

    Args:
        path: Destination file path.
        payload: JSON-compatible content to serialize.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding=UTF8_ENCODING)


def _request_json(
    method: str,
    url: str,
    *,
    payload: Any | None = None,
) -> tuple[int, dict[str, Any]]:
    """Send one JSON request and return status plus decoded object payload.

    Args:
        method: HTTP request method.
        url: Absolute endpoint URL.
        payload: Optional JSON request body.

    Returns:
        HTTP status code followed by a decoded dictionary.
    """
    request_body = None
    headers: dict[str, str] = {}
    if payload is not None:
        request_body = json.dumps(payload).encode(UTF8_ENCODING)
        headers[HEADER_CONTENT_TYPE] = MEDIA_TYPE_JSON
    http_request = urllib.request.Request(
        url,
        data=request_body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(http_request, timeout=5) as response:
            response_text = response.read().decode(UTF8_ENCODING)
            decoded = json.loads(response_text) if response_text else {}
            return int(response.status), decoded if isinstance(decoded, dict) else {}
    except urllib.error.HTTPError as error:
        response_text = error.read().decode(UTF8_ENCODING)
        decoded = json.loads(response_text) if response_text else {}
        return int(error.code), decoded if isinstance(decoded, dict) else {}


def _wait_for_endpoint(url: str, process: subprocess.Popen[str]) -> dict[str, Any]:
    """Wait until an HTTP endpoint responds or its owning process exits.

    Args:
        url: Readiness endpoint URL.
        process: Child process expected to serve the endpoint.

    Returns:
        Last successful JSON response.
    """
    deadline = time.monotonic() + PROCESS_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"process exited before readiness with status {process.returncode}")
        try:
            status, payload = _request_json("GET", url)
            if status == HTTP_OK:
                return payload
        except (OSError, ValueError, urllib.error.URLError):
            pass
        time.sleep(POLL_INTERVAL_SECONDS)
    raise RuntimeError(f"endpoint did not become ready: {url}")


def _start_process(
    command: list[str],
    *,
    environment: dict[str, str],
    log_path: Path,
    working_directory: Path,
) -> subprocess.Popen[str]:
    """Start a child process with combined output retained as evidence.

    Args:
        command: Executable and argument list.
        environment: Complete environment passed to the process.
        log_path: File receiving stdout and stderr.
        working_directory: Process working directory.

    Returns:
        Running child process handle.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("w", encoding=UTF8_ENCODING)
    try:
        return subprocess.Popen(  # pylint: disable=consider-using-with
            command,
            cwd=working_directory,
            env=environment,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
        )
    finally:
        log_handle.close()


def _terminate_process(process: subprocess.Popen[str] | None) -> None:
    """Stop one child process and avoid leaking it from the test container.

    Args:
        process: Optional process to terminate.
    """
    if process is None or process.poll() is not None:
        return
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def _complete_definition(private_value: str, *, endpoint_prefix: str) -> dict[str, Any]:
    """Build a definition containing every ST-007 connection section.

    Args:
        private_value: Runtime-only marker used to test storage separation.
        endpoint_prefix: Host label used to distinguish definition revisions.

    Returns:
        Complete credentials-manager definition payload.
    """
    return {
        KEY_OPAMP: {
            KEY_ENABLED: True,
            KEY_DESTINATION_ENDPOINT: f"https://{endpoint_prefix}.collector.test/opamp",
            KEY_HEADERS: {HEADER_ST007_ACCESS: private_value},
            KEY_PROXY: {
                KEY_URL: "https://proxy.collector.test",
                KEY_CONNECT_HEADERS: {HEADER_PROXY_TENANT: "st007"},
            },
        },
        KEY_OWN_METRICS: {
            KEY_ENABLED: True,
            KEY_DESTINATION_ENDPOINT: f"https://{endpoint_prefix}.collector.test/metrics",
        },
        KEY_OWN_TRACES: {
            KEY_ENABLED: True,
            KEY_DESTINATION_ENDPOINT: f"https://{endpoint_prefix}.collector.test/traces",
        },
        KEY_OWN_LOGS: {
            KEY_ENABLED: True,
            KEY_DESTINATION_ENDPOINT: f"https://{endpoint_prefix}.collector.test/logs",
        },
        KEY_OTHER_CONNECTIONS: {
            KEY_ARCHIVE: {
                KEY_ENABLED: True,
                KEY_DESTINATION_ENDPOINT: f"https://{endpoint_prefix}.collector.test/archive",
                KEY_OTHER_SETTINGS: {
                    KEY_ENABLED: True,
                    KEY_RETRIES: 3,
                    KEY_RATIO: 1.5,
                    KEY_TENANT: "st007",
                },
            }
        },
    }


def _invalid_definitions() -> tuple[tuple[str, dict[str, Any], str], ...]:
    """Return malformed definitions and their expected validation details."""
    return (
        (
            "invalid-destination",
            {KEY_OPAMP: {KEY_DESTINATION_ENDPOINT: "grpc://collector.test:4317"}},
            "destination_endpoint",
        ),
        (
            "invalid-proxy",
            {KEY_OPAMP: {KEY_PROXY: {KEY_URL: "socks5://proxy.test:1080"}}},
            "proxy.url",
        ),
        (
            "invalid-headers",
            {KEY_OPAMP: {KEY_HEADERS: []}},
            "headers must be a JSON object",
        ),
        (
            "invalid-proxy-object",
            {KEY_OPAMP: {KEY_PROXY: []}},
            "proxy must be a JSON object",
        ),
        (
            "invalid-other-settings",
            {KEY_OTHER_CONNECTIONS: {KEY_ARCHIVE: {KEY_OTHER_SETTINGS: []}}},
            "other_settings must be a JSON object",
        ),
    )


def _consumer_config(
    *,
    provider_url: str,
    client_uid: str,
    status_port: int,
    agent_path: Path,
    responses_path: Path,
) -> dict[str, Any]:
    """Build one simulator consumer configuration with a stable identity.

    Args:
        provider_url: Provider base URL.
        client_uid: Stable identity placed in agent metadata.
        status_port: Unique local status port for this consumer.
        agent_path: Simulator agent configuration path.
        responses_path: Scripted response configuration path.

    Returns:
        Consumer configuration payload.
    """
    return {
        KEY_CONSUMER: {
            KEY_SERVER_URL: provider_url,
            KEY_CLIENT_STATUS_PORT: status_port,
            KEY_TRANSPORT: "http",
            KEY_TLS: {KEY_VERIFY_SERVER: False},
            KEY_SERVER_AUTHORIZATION: "none",
            KEY_AGENT_CONFIG_PATH: str(agent_path),
            KEY_AGENT_ADDITIONAL_PARAMS: [
                json.dumps(
                    {
                        KEY_SERVICE_INSTANCE_UID: client_uid,
                        KEY_CLIENT_VERSION: "ST007 simulator",
                        KEY_CONFIG_VERSION: "st007-live",
                    }
                )
            ],
            KEY_HEARTBEAT_FREQUENCY: 2,
            KEY_SERVICE_TYPE: "simulator",
            KEY_SIMULATOR_RESPONSES_PATH: str(responses_path),
            KEY_LOG_LEVEL: "debug",
            KEY_SERVICE_NAME: f"ST007 {client_uid}",
            KEY_SERVICE_NAMESPACE: "ST007",
        }
    }


def _client_ids_by_uid(provider_url: str) -> dict[str, str]:
    """Return provider client IDs indexed by the two stable ST-007 identities.

    Args:
        provider_url: Provider base URL.

    Returns:
        Mapping from service-instance UID to provider client ID.
    """
    status, payload = _request_json("GET", f"{provider_url}/api/clients")
    if status != HTTP_OK:
        return {}
    clients = payload.get(KEY_CLIENTS, [])
    indexed: dict[str, str] = {}
    for client in clients if isinstance(clients, list) else []:
        if not isinstance(client, dict) or bool(client.get(KEY_DISCONNECTED)):
            continue
        serialized = json.dumps(client)
        for client_uid in (CLIENT_A_UID, CLIENT_B_UID):
            if client_uid in serialized:
                indexed[client_uid] = str(client.get(KEY_CLIENT_ID) or "")
    return indexed


def _wait_for_live_clients(provider_url: str) -> dict[str, str]:
    """Poll until both simulator identities are visible and connected.

    Args:
        provider_url: Provider base URL.

    Returns:
        Stable UID to client-ID mapping.
    """
    deadline = time.monotonic() + PROCESS_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        indexed = _client_ids_by_uid(provider_url)
        if set(indexed) == {CLIENT_A_UID, CLIENT_B_UID} and all(indexed.values()):
            return indexed
        time.sleep(POLL_INTERVAL_SECONDS)
    raise RuntimeError("provider did not report both ST-007 simulator clients")


def _wait_for_log_text(path: Path, expected_text: str) -> None:
    """Wait for one diagnostic string to appear in a retained process log.

    Args:
        path: Log file to poll.
        expected_text: Text proving connection-settings delivery.
    """
    deadline = time.monotonic() + PROCESS_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if path.exists() and expected_text in path.read_text(
            encoding=UTF8_ENCODING, errors="replace"
        ):
            return
        time.sleep(POLL_INTERVAL_SECONDS)
    raise RuntimeError(f"expected log text was not observed: {expected_text}")


def _credentials_url(port: int, suffix: str) -> str:
    """Build one credentials-manager API URL.

    Args:
        port: Local credentials-manager port.
        suffix: API-relative route beginning with a slash.

    Returns:
        Absolute API URL.
    """
    return f"http://127.0.0.1:{port}{API_PREFIX}{suffix}"


def _start_credentials_service(  # pylint: disable=too-many-arguments
    *,
    repo_root: Path,
    service_script: Path,
    runtime_dir: Path,
    port: int,
    provider_base_url: str,
    log_path: Path,
) -> subprocess.Popen[str]:
    """Start an isolated credentials manager and wait for health.

    Args:
        repo_root: Staged source-tree root.
        service_script: Service launcher helper path.
        runtime_dir: Mutable state directory.
        port: Local listen port.
        provider_base_url: Provider target used by Apply.
        log_path: Service diagnostic log path.

    Returns:
        Ready service process.
    """
    process = _start_process(
        [
            "python",
            str(service_script),
            "--runtime-dir",
            str(runtime_dir),
            "--port",
            str(port),
            "--provider-base-url",
            provider_base_url,
        ],
        environment=os.environ.copy(),
        log_path=log_path,
        working_directory=repo_root,
    )
    _wait_for_endpoint(_credentials_url(port, "/health"), process)
    return process


def _assert_status(actual_status: int, expected_status: int, payload: dict[str, Any]) -> None:
    """Raise a reviewable assertion when an API status differs.

    Args:
        actual_status: Observed HTTP status.
        expected_status: Required HTTP status.
        payload: Decoded response included in assertion diagnostics.
    """
    assert actual_status == expected_status, payload


def _assert_fallback_records(
    records: list[dict[str, Any]],
    *,
    expected_client_ids: set[str],
) -> None:
    """Validate one fallback record per intended client.

    Args:
        records: Decoded JSONL fallback records.
        expected_client_ids: Exact clients that should receive fallback records.
    """
    assert len(records) == len(expected_client_ids)
    assert {str(record.get(KEY_CLIENT_ID)) for record in records} == expected_client_ids
    for record in records:
        assert record.get(KEY_CONNECTION_NAME) == CONNECTION_SECONDARY
        assert record.get(KEY_DELIVERY) == VALUE_FALLBACK_LOG
        assert record.get(KEY_APPLIED_AT_UTC)
        server_to_agent = record.get(KEY_SERVER_TO_AGENT)
        assert isinstance(server_to_agent, dict)
        connection_settings = server_to_agent.get(KEY_CONNECTION_SETTINGS)
        assert isinstance(connection_settings, dict)
        assert KEY_OPAMP in connection_settings
        assert KEY_OWN_METRICS in connection_settings
        assert KEY_OWN_TRACES in connection_settings
        assert KEY_OWN_LOGS in connection_settings
        assert KEY_ARCHIVE in connection_settings.get(KEY_OTHER_CONNECTIONS, {})


def _exercise_credentials_api(  # pylint: disable=too-many-locals,too-many-statements
    *,
    credentials_port: int,
    runtime_dir: Path,
    output_dir: Path,
    client_ids: dict[str, str],
) -> dict[str, Any]:
    """Run definition, validation, assignment, reconciliation, and apply checks.

    Args:
        credentials_port: Ready credentials-manager port.
        runtime_dir: Directory containing mutable storage files.
        output_dir: Evidence destination.
        client_ids: Stable UID to provider client-ID mapping.

    Returns:
        Provider-queue Apply response.
    """
    private_value = "-".join(("st007", "runtime", "private", str(time.time_ns())))
    primary_definition = _complete_definition(private_value, endpoint_prefix="primary")
    secondary_definition = _complete_definition(private_value, endpoint_prefix="secondary")

    status, payload = _request_json(
        "PUT",
        _credentials_url(credentials_port, f"/connections/{CONNECTION_PRIMARY}"),
        payload={KEY_DEFINITION: primary_definition},
    )
    _assert_status(status, HTTP_OK, payload)
    status, loaded = _request_json(
        "GET", _credentials_url(credentials_port, f"/connections/{CONNECTION_PRIMARY}")
    )
    _assert_status(status, HTTP_OK, loaded)
    assert loaded[KEY_DEFINITION] == primary_definition
    _write_json(output_dir / "connection-api.json", loaded)

    status, listed = _request_json("GET", _credentials_url(credentials_port, "/connections"))
    _assert_status(status, HTTP_OK, listed)
    assert listed == {KEY_NAMES: [CONNECTION_PRIMARY]}
    assert private_value not in json.dumps(listed)

    mapping_path = runtime_dir / "client-mappings.json"
    credentials_path = runtime_dir / "credentials.json"
    assert private_value not in mapping_path.read_text(encoding=UTF8_ENCODING)
    assert private_value in credentials_path.read_text(encoding=UTF8_ENCODING)

    status, payload = _request_json(
        "PUT",
        _credentials_url(credentials_port, f"/connections/{CONNECTION_PRIMARY}"),
        payload={KEY_DEFINITION: _complete_definition(private_value, endpoint_prefix="updated")},
    )
    _assert_status(status, HTTP_OK, payload)

    status, payload = _request_json(
        "PUT",
        _credentials_url(credentials_port, f"/connections/{CONNECTION_TEMPORARY}"),
        payload={KEY_DEFINITION: primary_definition},
    )
    _assert_status(status, HTTP_OK, payload)
    status, payload = _request_json(
        "DELETE",
        _credentials_url(credentials_port, f"/connections/{CONNECTION_TEMPORARY}"),
    )
    _assert_status(status, HTTP_NO_CONTENT, payload)

    validation_results: list[dict[str, Any]] = []
    for name, invalid_definition, error_fragment in _invalid_definitions():
        status, invalid_payload = _request_json(
            "PUT",
            _credentials_url(credentials_port, f"/connections/{name}"),
            payload={KEY_DEFINITION: invalid_definition},
        )
        _assert_status(status, HTTP_BAD_REQUEST, invalid_payload)
        assert error_fragment in str(invalid_payload.get(KEY_ERROR) or "")
        validation_results.append(
            {KEY_NAME: name, KEY_STATUS: status, KEY_ERROR: invalid_payload}
        )
    _write_json(output_dir / "validation-errors.json", {KEY_RESULTS: validation_results})

    status, payload = _request_json(
        "PUT",
        _credentials_url(credentials_port, f"/connections/{CONNECTION_SECONDARY}"),
        payload={KEY_DEFINITION: secondary_definition},
    )
    _assert_status(status, HTTP_OK, payload)

    client_a_id = client_ids[CLIENT_A_UID]
    client_b_id = client_ids[CLIENT_B_UID]
    status, mappings = _request_json(
        "PUT",
        _credentials_url(credentials_port, "/mappings"),
        payload={KEY_MAPPINGS: {client_a_id: CONNECTION_PRIMARY, client_b_id: CONNECTION_PRIMARY}},
    )
    _assert_status(status, HTTP_OK, mappings)
    _write_json(output_dir / "mappings-before-reassignment.json", mappings)

    status, mappings = _request_json(
        "PUT",
        _credentials_url(credentials_port, "/mappings"),
        payload={
            KEY_MAPPINGS: {
                client_a_id: CONNECTION_PRIMARY,
                client_b_id: CONNECTION_SECONDARY,
            }
        },
    )
    _assert_status(status, HTTP_OK, mappings)
    assert mappings[KEY_MAPPINGS][client_b_id] == CONNECTION_SECONDARY
    assert sum(1 for value in mappings[KEY_MAPPINGS].values() if value == CONNECTION_SECONDARY) == 1

    status, rejected_delete = _request_json(
        "DELETE",
        _credentials_url(credentials_port, f"/connections/{CONNECTION_PRIMARY}"),
    )
    _assert_status(status, HTTP_BAD_REQUEST, rejected_delete)

    stale_mappings = dict(mappings[KEY_MAPPINGS])
    stale_mappings["stale-client"] = "missing-definition"
    _write_json(mapping_path, {KEY_CLIENTS: stale_mappings})
    shutil.copy2(mapping_path, output_dir / "mapping-before-reconciliation.json")
    status, reconciled = _request_json("GET", _credentials_url(credentials_port, "/mappings"))
    _assert_status(status, HTTP_OK, reconciled)
    assert "stale-client" not in reconciled[KEY_MAPPINGS]
    assert "stale-client" in json.dumps(reconciled.get(KEY_RECONCILIATION, {}))
    _write_json(output_dir / "mapping-after-reconciliation.json", reconciled)
    shutil.copy2(mapping_path, output_dir / "mapping-storage.json")
    shutil.copy2(credentials_path, output_dir / "plaintext-test-backend.json")

    status, apply_payload = _request_json(
        "POST",
        _credentials_url(credentials_port, f"/connections/{CONNECTION_SECONDARY}/apply"),
    )
    _assert_status(status, HTTP_OK, apply_payload)
    assert apply_payload[KEY_CLIENTS] == [client_b_id]
    assert apply_payload[KEY_RESULTS][0][KEY_DELIVERY] == VALUE_PROVIDER_QUEUE
    _write_json(output_dir / "provider-request-capture.json", apply_payload)
    return apply_payload


def _exercise_fallback(
    *,
    credentials_port: int,
    runtime_dir: Path,
    output_dir: Path,
    client_ids: set[str],
) -> None:
    """Apply one definition to two clients through unavailable-provider fallback.

    Args:
        credentials_port: Ready fallback credentials-manager port.
        runtime_dir: Directory containing service state and JSONL output.
        output_dir: Evidence destination.
        client_ids: Intended delivery client IDs.
    """
    status, mappings = _request_json(
        "PUT",
        _credentials_url(credentials_port, "/mappings"),
        payload={KEY_MAPPINGS: {client_id: CONNECTION_SECONDARY for client_id in client_ids}},
    )
    _assert_status(status, HTTP_OK, mappings)
    status, apply_payload = _request_json(
        "POST",
        _credentials_url(credentials_port, f"/connections/{CONNECTION_SECONDARY}/apply"),
    )
    _assert_status(status, HTTP_OK, apply_payload)
    assert {result[KEY_DELIVERY] for result in apply_payload[KEY_RESULTS]} == {
        VALUE_FALLBACK_LOG
    }
    fallback_path = runtime_dir / "fallback-deliveries.jsonl"
    records = [
        json.loads(line)
        for line in fallback_path.read_text(encoding=UTF8_ENCODING).splitlines()
        if line.strip()
    ]
    _assert_fallback_records(records, expected_client_ids=client_ids)
    shutil.copy2(fallback_path, output_dir / "fallback-deliveries.jsonl")
    _write_json(output_dir / "fallback-apply-response.json", apply_payload)


def _run_scenario(  # pylint: disable=too-many-locals
    repo_root: Path,
    service_script: Path,
    output_dir: Path,
) -> None:
    """Run the complete live-provider and fallback integration scenario.

    Args:
        repo_root: Writable staged repository root.
        service_script: Credentials-manager launcher helper.
        output_dir: Evidence directory mounted from the host.
    """
    runtime_dir = Path(
        tempfile.mkdtemp(prefix="integration-runtime-", dir=output_dir)
    )
    provider_url = f"http://127.0.0.1:{PROVIDER_PORT}"
    provider_config_path = runtime_dir / "provider.json"
    responses_path = runtime_dir / "simulator-responses.json"
    agent_path = runtime_dir / "simulator-agent.yaml"
    consumer_a_config_path = runtime_dir / "consumer-a.json"
    consumer_b_config_path = runtime_dir / "consumer-b.json"
    _write_json(
        provider_config_path,
        {
            KEY_PROVIDER: {
                KEY_WEBUI_PORT: PROVIDER_PORT,
                KEY_LOG_LEVEL: "DEBUG",
                KEY_ALLOW_REMOTE_CONFIG: True,
                KEY_ALLOW_EFFECTIVE_CONFIG: True,
                KEY_ALLOW_CONNECTION_SETTINGS: True,
                KEY_ALLOW_CONNECTION_SETTINGS_REQUEST: True,
                KEY_OPAMP_AUTH: "none",
                KEY_UI_AUTH: "none",
                KEY_STATE_PERSISTENCE: {KEY_ENABLED: False},
                KEY_TLS: {KEY_ENABLED: False},
            }
        },
    )
    _write_json(responses_path, {KEY_RESPONSES: {VALUE_WILDCARD: [VALUE_ACCEPT]}})
    agent_path.write_text("service:\n  flush: 1\n", encoding=UTF8_ENCODING)
    _write_json(
        consumer_a_config_path,
        _consumer_config(
            provider_url=provider_url,
            client_uid=CLIENT_A_UID,
            status_port=18201,
            agent_path=agent_path,
            responses_path=responses_path,
        ),
    )
    _write_json(
        consumer_b_config_path,
        _consumer_config(
            provider_url=provider_url,
            client_uid=CLIENT_B_UID,
            status_port=18202,
            agent_path=agent_path,
            responses_path=responses_path,
        ),
    )

    provider_process: subprocess.Popen[str] | None = None
    consumer_a_process: subprocess.Popen[str] | None = None
    consumer_b_process: subprocess.Popen[str] | None = None
    credentials_process: subprocess.Popen[str] | None = None
    fallback_process: subprocess.Popen[str] | None = None
    consumer_environment = os.environ.copy()
    consumer_environment[ENV_APP_ENABLE_DEV_FEATURES] = "true"
    try:
        provider_environment = os.environ.copy()
        provider_environment[ENV_OPAMP_CONFIG_PATH] = str(provider_config_path)
        provider_process = _start_process(
            [
                "opamp-provider",
                "--config-path",
                str(provider_config_path),
                "--host",
                "127.0.0.1",
                "--port",
                str(PROVIDER_PORT),
                "--log-level",
                "DEBUG",
            ],
            environment=provider_environment,
            log_path=output_dir / "provider.log",
            working_directory=repo_root,
        )
        _wait_for_endpoint(f"{provider_url}/api/clients", provider_process)
        consumer_a_process = _start_process(
            ["opamp-consumer", "--config-path", str(consumer_a_config_path)],
            environment=consumer_environment,
            log_path=output_dir / "consumer-a.log",
            working_directory=repo_root,
        )
        consumer_b_process = _start_process(
            ["opamp-consumer", "--config-path", str(consumer_b_config_path)],
            environment=consumer_environment,
            log_path=output_dir / "consumer-b.log",
            working_directory=repo_root,
        )
        client_ids = _wait_for_live_clients(provider_url)
        status, connected_clients = _request_json("GET", f"{provider_url}/api/clients")
        _assert_status(status, HTTP_OK, connected_clients)
        _write_json(output_dir / "provider-clients-before-apply.json", connected_clients)

        credentials_process = _start_credentials_service(
            repo_root=repo_root,
            service_script=service_script,
            runtime_dir=runtime_dir / "credentials",
            port=CREDENTIALS_PORT,
            provider_base_url=provider_url,
            log_path=output_dir / "credentials-manager.log",
        )
        _exercise_credentials_api(
            credentials_port=CREDENTIALS_PORT,
            runtime_dir=runtime_dir / "credentials",
            output_dir=output_dir,
            client_ids=client_ids,
        )
        _wait_for_log_text(output_dir / "consumer-b.log", CONSUMER_LOG_NEEDLE)
        _wait_for_log_text(
            output_dir / "consumer-b.log",
            CONSUMER_UNSUPPORTED_NEEDLE,
        )
        consumer_a_log = (output_dir / "consumer-a.log").read_text(
            encoding=UTF8_ENCODING, errors="replace"
        )
        assert CONSUMER_LOG_NEEDLE not in consumer_a_log
        status, applied_clients = _request_json("GET", f"{provider_url}/api/clients")
        _assert_status(status, HTTP_OK, applied_clients)
        serialized_clients = json.dumps(applied_clients)
        assert "Queued connection settings for secondary." in serialized_clients
        _write_json(output_dir / "provider-clients-after-apply.json", applied_clients)

        _terminate_process(credentials_process)
        credentials_process = None
        fallback_process = _start_credentials_service(
            repo_root=repo_root,
            service_script=service_script,
            runtime_dir=runtime_dir / "credentials",
            port=FALLBACK_PORT,
            provider_base_url="http://127.0.0.1:1",
            log_path=output_dir / "credentials-manager-fallback.log",
        )
        _exercise_fallback(
            credentials_port=FALLBACK_PORT,
            runtime_dir=runtime_dir / "credentials",
            output_dir=output_dir,
            client_ids=set(client_ids.values()),
        )
        _write_json(
            output_dir / "integration-summary.json",
            {
                KEY_SCENARIO: "ST-007",
                KEY_PASSED: True,
                KEY_LIVE_CLIENTS: client_ids,
                KEY_PROVIDER_DELIVERY_CLIENT: client_ids[CLIENT_B_UID],
                KEY_FALLBACK_DELIVERY_COUNT: len(client_ids),
            },
        )
    finally:
        for process in (
            fallback_process,
            credentials_process,
            consumer_b_process,
            consumer_a_process,
            provider_process,
        ):
            _terminate_process(process)


def main() -> int:
    """Parse container paths and execute ST-007 integration verification."""
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--service-script", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    _run_scenario(
        arguments.repo_root,
        arguments.service_script,
        arguments.output_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
