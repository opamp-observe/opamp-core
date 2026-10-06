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

"""Unit tests for the containerized agent-shutdown regression verifier."""

from __future__ import annotations

import importlib.util
import json
import urllib.error
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[1]
VERIFIER_PATH = (
    REPO_ROOT
    / "tests"
    / "test-containers"
    / "agent-shutdown-e2e"
    / "scripts"
    / "verify_agent_shutdown.py"
)


def _load_verifier() -> ModuleType:
    """Load the standalone verifier script as a testable Python module."""
    spec = importlib.util.spec_from_file_location(
        "agent_shutdown_verifier", VERIFIER_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_find_client_matches_service_instance_description() -> None:
    """Select the intended provider record from a mixed client response."""
    verifier = _load_verifier()
    expected_client = {
        "client_id": "client-two",
        "agent_description": (
            'key: "service.instance.id"\n'
            'string_value: "shutdown-e2e-fluentbit"'
        ),
    }
    payload = {
        "clients": [
            {"client_id": "client-one", "agent_description": "another-agent"},
            expected_client,
        ]
    }

    assert verifier._find_client(payload, "shutdown-e2e-fluentbit") == expected_client


def test_http_json_treats_startup_connection_error_as_retryable(monkeypatch) -> None:
    """Return a non-HTTP status so readiness polling can retry provider startup."""
    verifier = _load_verifier()

    def raise_connection_error(*_args, **_kwargs):
        """Simulate a provider socket that is not ready to accept requests."""
        raise urllib.error.URLError("provider starting")

    monkeypatch.setattr(verifier.urllib.request, "urlopen", raise_connection_error)

    status_code, payload = verifier._http_json("http://provider:8080/api/clients")

    assert status_code == 0
    assert "provider starting" in payload["connection_error"]


def test_shutdown_command_requires_sent_timestamp() -> None:
    """Treat only a dispatched shutdown command as server-side success."""
    verifier = _load_verifier()
    queued_client = {"commands": [{"action": "shutdownagent", "sent_at": None}]}
    sent_client = {
        "commands": [{"action": "shutdownagent", "sent_at": "2026-09-24T12:00:00Z"}]
    }

    assert verifier._shutdown_command_was_sent(queued_client) is False
    assert verifier._shutdown_command_was_sent(sent_client) is True


def test_ui_evidence_requires_exact_ui_shutdown_payload() -> None:
    """Validate the browser request source, operation, and capability values."""
    verifier = _load_verifier()
    payload = {
        "result": "passed",
        "command_response_status": 201,
        "command_request_payload": {
            "pairs": [
                {"key": "classifier", "value": "custom"},
                {"key": "operation", "value": "shutdownagent"},
                {
                    "key": "capability",
                    "value": "org.mp3monster.opamp_provider.command_shutdown_agent",
                },
                {"key": "source", "value": "ui"},
            ]
        },
    }

    assert verifier._ui_evidence_is_valid(payload) is True
    payload["command_request_payload"]["pairs"][-1]["value"] = "api"
    assert verifier._ui_evidence_is_valid(payload) is False


def test_matching_processes_separates_supervisor_and_agent() -> None:
    """Keep process assertions specific to the consumer and managed executable."""
    verifier = _load_verifier()
    processes = [
        {"pid": 10, "command": "python /usr/local/bin/opamp-consumer --config-path x"},
        {"pid": 11, "command": "/usr/local/bin/fluent-bit -c fluent-bit.yaml"},
        {"pid": 12, "command": "sleep 1"},
    ]

    assert verifier._matching_processes(
        processes, verifier.SUPERVISOR_PROCESS_MARKERS
    ) == [processes[0]]
    assert verifier._matching_processes(
        processes, verifier.AGENT_PROCESS_MARKERS["fluentbit"]
    ) == [processes[1]]
    assert (
        verifier._matching_processes(
            processes, verifier.AGENT_PROCESS_MARKERS["simulator"]
        )
        == []
    )


def test_aggregate_phase_requires_every_supported_agent(tmp_path: Path) -> None:
    """Fail aggregation when any supported deployment is absent or unsuccessful."""
    verifier = _load_verifier()
    for agent_type in verifier.SUPPORTED_AGENT_TYPES:
        agent_dir = tmp_path / agent_type
        agent_dir.mkdir()
        (agent_dir / "summary.json").write_text(
            json.dumps({"result": "passed"}), encoding="utf-8"
        )

    args = type("Args", (), {"output_dir": tmp_path})()
    assert verifier._run_aggregate_phase(args) == 0

    (tmp_path / "fluentd" / "summary.json").unlink()
    assert verifier._run_aggregate_phase(args) == 1


def test_aggregate_phase_can_require_selected_agents(tmp_path: Path) -> None:
    """Allow focused container reruns to aggregate only selected agent types."""
    verifier = _load_verifier()
    fluentd_dir = tmp_path / "fluentd"
    fluentd_dir.mkdir()
    (fluentd_dir / "summary.json").write_text(
        json.dumps({"result": "passed"}), encoding="utf-8"
    )
    args = type(
        "Args",
        (),
        {"output_dir": tmp_path, "required_agent_type": ["fluentd"]},
    )()

    assert verifier._run_aggregate_phase(args) == 0
