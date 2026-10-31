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

"""Tests for simulator OpAMP consumer behavior."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from opamp_consumer.config import ConsumerConfig
from opamp_consumer.config_metadata import CONFIG_METADATA_KEY_SERVICE_INSTANCE_UID
from opamp_consumer.exceptions import AgentException
from opamp_consumer.fluentbit.client import (
    KEY_SERVICE_INSTANCE_ID,
    KEY_SERVICE_TYPE,
    KEY_SERVICE_VERSION,
)
from opamp_consumer.proto import opamp_pb2
from opamp_consumer.simulator import client as simulator_client
from opamp_consumer.simulator.client import SimulatorOpAMPClient


def _write_simulator_responses(
    *,
    tmp_path: Path,
    payload: dict,
) -> Path:
    path = tmp_path / "simulator-responses.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _build_simulator_config(
    *,
    responses_path: Path,
    additional_params: list[str] | None = None,
) -> ConsumerConfig:
    return ConsumerConfig(
        server_url="http://localhost:8080",
        agent_config_path="./consumer/fluent-bit.yaml",
        agent_additional_params=additional_params or [],
        heartbeat_frequency=5,
        client_status_port=1,
        service_name="Simulator",
        service_namespace="SimulatorNS",
        service_type="simulator",
        simulator_responses_path=str(responses_path),
    )


def test_simulator_cycles_command_response_actions(tmp_path: Path, monkeypatch) -> None:
    """Command handling should cycle through scripted actions and wrap to start."""
    responses_path = _write_simulator_responses(
        tmp_path=tmp_path,
        payload={
            "responses": {
                "command": ["ignore", "accept"],
            }
        },
    )
    instance = SimulatorOpAMPClient(
        "http://localhost:8080",
        _build_simulator_config(responses_path=responses_path),
    )

    calls = {"restart": 0}

    def _restart() -> bool:
        calls["restart"] += 1
        return True

    monkeypatch.setattr(instance, "restart_agent_process", _restart)
    command = opamp_pb2.ServerToAgentCommand(
        type=opamp_pb2.CommandType.CommandType_Restart
    )

    instance.handle_command(command)  # ignore
    instance.handle_command(command)  # accept
    instance.handle_command(command)  # wraps to ignore

    assert calls["restart"] == 1


def test_simulator_cycles_error_action_and_wraps(tmp_path: Path) -> None:
    """Error scripted action should raise, then wrap back to first action."""
    responses_path = _write_simulator_responses(
        tmp_path=tmp_path,
        payload={
            "responses": {
                "remote_config": [
                    "ignore",
                    {"action": "error", "message": "simulated remote config rejection"},
                ]
            }
        },
    )
    instance = SimulatorOpAMPClient(
        "http://localhost:8080",
        _build_simulator_config(responses_path=responses_path),
    )
    remote_config = opamp_pb2.AgentRemoteConfig()

    instance.handle_remote_config(remote_config)  # ignore
    with pytest.raises(AgentException, match="simulated remote config rejection"):
        instance.handle_remote_config(remote_config)  # error
    instance.handle_remote_config(remote_config)  # wraps to ignore


def test_simulator_agent_description_uses_simulator_service_type(tmp_path: Path) -> None:
    """Simulator should advertise service.type as simulator."""
    responses_path = _write_simulator_responses(
        tmp_path=tmp_path,
        payload={"responses": {"command": ["accept"]}},
    )
    instance = SimulatorOpAMPClient(
        "http://localhost:8080",
        _build_simulator_config(responses_path=responses_path),
    )

    description = instance.get_agent_description()
    identifying = {item.key: item.value.string_value for item in description.identifying_attributes}

    assert identifying[KEY_SERVICE_TYPE] == "simulator"


def test_simulator_metadata_json_from_agent_additional_params(tmp_path: Path) -> None:
    """Simulator should accept metadata JSON via --agent-additional-params."""
    responses_path = _write_simulator_responses(
        tmp_path=tmp_path,
        payload={"responses": {"command": ["accept"]}},
    )
    metadata_payload = json.dumps(
        {
            "service_instance_uid": "sim-uid-01",
            "client_version": "4.2.0",
            "config_version": "cfg-v7",
        }
    )
    instance = SimulatorOpAMPClient(
        "http://localhost:8080",
        _build_simulator_config(
            responses_path=responses_path,
            additional_params=[metadata_payload],
        ),
    )

    description = instance.get_agent_description()
    identifying = {item.key: item.value.string_value for item in description.identifying_attributes}
    non_identifying = {
        item.key: item.value.string_value for item in description.non_identifying_attributes
    }

    assert identifying[KEY_SERVICE_TYPE] == "simulator"
    assert identifying[KEY_SERVICE_INSTANCE_ID] == "sim-uid-01"
    assert identifying[KEY_SERVICE_VERSION] == "4.2.0"
    assert non_identifying["config.version"] == "cfg-v7"
    assert instance.config.config_version == "cfg-v7"


def test_simulator_metadata_json_supports_split_tokens(tmp_path: Path) -> None:
    """Simulator should parse metadata JSON when CLI tokenization splits braces."""
    responses_path = _write_simulator_responses(
        tmp_path=tmp_path,
        payload={"responses": {"command": ["accept"]}},
    )
    instance = SimulatorOpAMPClient(
        "http://localhost:8080",
        _build_simulator_config(
            responses_path=responses_path,
            additional_params=[
                '{"service_instance_uid":"sim-uid-02",',
                '"client_version":"6.1.0",',
                '"config_version":"cfg-v8"}',
            ],
        ),
    )

    description = instance.get_agent_description()
    identifying = {item.key: item.value.string_value for item in description.identifying_attributes}

    assert identifying[KEY_SERVICE_INSTANCE_ID] == "sim-uid-02"
    assert identifying[KEY_SERVICE_VERSION] == "6.1.0"


def test_simulator_get_config_metadata_maps_payload_fields(tmp_path: Path) -> None:
    """Simulator metadata should map JSON fields into the shared dataclass."""
    responses_path = _write_simulator_responses(
        tmp_path=tmp_path,
        payload={"responses": {"command": ["accept"]}},
    )
    metadata_payload = json.dumps(
        {
            "service_instance_uid": "sim-uid-03",
            "version": "7.2.0",
            "config_version": "cfg-v9",
            "config_data": "simulated=true",
            "SCM_source_name": "git",
            "SCM_config_version": "commit-123",
            "additional_metadata": {"environment": "dev"},
        }
    )
    instance = SimulatorOpAMPClient(
        "http://localhost:8080",
        _build_simulator_config(
            responses_path=responses_path,
            additional_params=[metadata_payload],
        ),
    )

    metadata = instance.get_config_metadata()

    assert metadata.config_version == "cfg-v9"
    assert metadata.config_data == "simulated=true"
    assert metadata.SCM_source_name == "git"
    assert metadata.SCM_config_version == "commit-123"
    assert metadata.version == "7.2.0"
    assert metadata.config_type == "simulator"
    assert metadata.additional_metadata == {
        CONFIG_METADATA_KEY_SERVICE_INSTANCE_UID: "sim-uid-03",
        "environment": "dev",
    }


def test_simulator_get_config_metadata_logs_warning_for_invalid_payload(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Invalid simulator metadata payloads should warn and return an empty dataclass."""
    caplog.set_level("WARNING")
    responses_path = _write_simulator_responses(
        tmp_path=tmp_path,
        payload={"responses": {"command": ["accept"]}},
    )
    instance = SimulatorOpAMPClient(
        "http://localhost:8080",
        _build_simulator_config(
            responses_path=responses_path,
            additional_params=["not-json"],
        ),
    )

    metadata = instance.get_config_metadata()

    assert metadata.config_version == ""
    assert metadata.config_data == ""
    assert metadata.SCM_source_name == ""
    assert metadata.version == ""
    assert metadata.additional_metadata == {}
    assert "simulator expected JSON object in --agent-additional-params" in caplog.text


def test_simulator_checks_process_record_status_and_marks_shuttingdown(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Simulator should poll status file, mark shuttingdown, then request shutdown."""
    responses_path = _write_simulator_responses(
        tmp_path=tmp_path,
        payload={"responses": {"command": ["accept"]}},
    )
    state_file = tmp_path / "launcher_state.json"
    state_file.write_text(
        json.dumps(
            {
                "instances": [
                    {"name": "sim-status-01", "pid": 7777, "status": "shutdown"},
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(
        simulator_client.SIMULATOR_PROCESS_RECORD_FILE_ENV,
        str(state_file),
    )
    monkeypatch.setenv(
        simulator_client.SIMULATOR_PROCESS_RECORD_NAME_ENV,
        "sim-status-01",
    )
    monkeypatch.setattr(simulator_client.time, "monotonic", lambda: 1000.0)
    instance = SimulatorOpAMPClient(
        "http://localhost:8080",
        _build_simulator_config(responses_path=responses_path),
    )

    should_shutdown = instance.check_semaphore()

    assert should_shutdown is True
    payload = json.loads(state_file.read_text(encoding="utf-8"))
    assert payload["instances"][0]["status"] == "shuttingdown"


def test_simulator_main_logs_runtime_config_path(monkeypatch) -> None:
    """Simulator startup should log the resolved config path after logging setup."""
    config = ConsumerConfig(
        server_url="http://localhost:8080",
        client_status_port=1,
        service_type="simulator",
    )
    args = type("Args", (), {"config_path": "consumer/opamp-simulator.json", "help": True})()
    captured: dict[str, object] = {}

    class _Parser:
        def parse_args(self):
            return args

    monkeypatch.setattr(simulator_client, "build_common_cli_parser", lambda: _Parser())
    monkeypatch.setattr(simulator_client, "load_config_from_cli_args", lambda _args: config)
    monkeypatch.setattr(
        simulator_client,
        "configure_logging_for_config",
        lambda _config: logging.getLogger("simulator-test"),
    )

    def _capture_log_runtime_config_path(*, logger, runtime_name, config_path):
        captured["logger_name"] = logger.name
        captured["runtime_name"] = runtime_name
        captured["config_path"] = config_path
        return Path("/tmp/opamp-simulator.json")

    monkeypatch.setattr(
        simulator_client,
        "log_runtime_config_path",
        _capture_log_runtime_config_path,
    )
    monkeypatch.setattr(
        simulator_client,
        "maybe_print_config_help",
        lambda **_kwargs: True,
    )

    simulator_client.main()

    assert captured == {
        "logger_name": "simulator-test",
        "runtime_name": "simulator",
        "config_path": "consumer/opamp-simulator.json",
    }


def test_validate_simulator_dev_features_flag_missing_env_logs_and_blocks(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.delenv(simulator_client.ENV_APP_ENABLE_DEV_FEATURES, raising=False)
    caplog.set_level(logging.ERROR)

    allowed = simulator_client._validate_simulator_dev_features_flag(
        logging.getLogger("test.simulator")
    )

    assert allowed is False
    assert (
        f"required environment flag {simulator_client.ENV_APP_ENABLE_DEV_FEATURES} is not set"
        in caplog.text
    )
    assert "shutting down gracefully before sending any details to the server" in caplog.text


def test_validate_simulator_dev_features_flag_false_logs_and_blocks(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv(simulator_client.ENV_APP_ENABLE_DEV_FEATURES, "false")
    caplog.set_level(logging.ERROR)

    allowed = simulator_client._validate_simulator_dev_features_flag(
        logging.getLogger("test.simulator")
    )

    assert allowed is False
    assert (
        f"required environment flag {simulator_client.ENV_APP_ENABLE_DEV_FEATURES} must be true"
        in caplog.text
    )


def test_validate_simulator_dev_features_flag_true_allows_startup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(simulator_client.ENV_APP_ENABLE_DEV_FEATURES, "true")
    allowed = simulator_client._validate_simulator_dev_features_flag(
        logging.getLogger("test.simulator")
    )
    assert allowed is True
