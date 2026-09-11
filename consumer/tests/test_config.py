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

import importlib
import json
import sys
from pathlib import Path

import pytest

from opamp_consumer import config as consumer_config


def _base_consumer_config() -> dict:
    return {
        "consumer": {
            "server_url": "http://localhost:4320",
            "transport": "http",
            "log_agent_api_responses": False,
            "agent_config_path": "./fluent-bit.conf",
            "agent_additional_params": [],
            "heartbeat_frequency": 30,
            "log_level": "debug",
            "service_name": "Fluentbit",
            "service_namespace": "FluentBitNS",
        }
    }


def test_consumer_config_root_path_insertion_is_idempotent(monkeypatch) -> None:
    """Reloads should not duplicate ROOT_PATH entries in sys.path."""
    root_path = str(consumer_config.ROOT_PATH)
    sanitized_path = [entry for entry in sys.path if entry != root_path]
    monkeypatch.setattr(sys, "path", list(sanitized_path))

    importlib.reload(consumer_config)
    assert sys.path.count(root_path) == 1

    importlib.reload(consumer_config)
    assert sys.path.count(root_path) == 1


def test_allow_custom_capabilities_defaults_false_when_missing(
    tmp_path, monkeypatch
) -> None:
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(_base_consumer_config(), indent=2),
        encoding="utf-8",
    )
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.allow_custom_capabilities is False


def test_log_level_loads_from_config_file(tmp_path, monkeypatch) -> None:
    """Consumer log_level should be preserved when loading file config."""
    raw = _base_consumer_config()
    raw["consumer"]["log_level"] = "info"
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.log_level == "info"


def test_preserve_previous_config_defaults_false_when_missing(
    tmp_path, monkeypatch
) -> None:
    """Consumer preserve_previous_config should default to false when omitted."""
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(_base_consumer_config(), indent=2),
        encoding="utf-8",
    )
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.preserve_previous_config is False


def test_preserve_previous_config_loads_when_enabled(tmp_path, monkeypatch) -> None:
    """Consumer preserve_previous_config should load from config when supplied."""
    raw = _base_consumer_config()
    raw["consumer"]["preserve_previous_config"] = True
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.preserve_previous_config is True


def test_service_type_defaults_to_fluentbit_when_missing(tmp_path, monkeypatch) -> None:
    """Consumer service_type should default to fluentbit when omitted."""
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(_base_consumer_config(), indent=2),
        encoding="utf-8",
    )
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.service_type == consumer_config.SERVICE_TYPE_FLUENTBIT


def test_service_type_preserves_custom_plugin_key(tmp_path, monkeypatch) -> None:
    """Custom plugin service_type values should survive config loading."""
    raw = _base_consumer_config()
    raw["consumer"]["service_type"] = "custom_agent"
    raw["consumer"]["plugins"] = [
        {
            "service_type": "custom_agent",
            "entry_point": "example_plugin:main",
            "enabled": True,
        }
    ]
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.service_type == "custom_agent"
    assert loaded.consumer_plugins == raw["consumer"]["plugins"]


def test_elastic_agent_plugin_config_section_loads_fields(tmp_path) -> None:
    """Plugin-owned config blocks should enrich the shared ConsumerConfig."""
    agent_config_path = tmp_path / "elastic-agent.yml"
    agent_config_path.write_text("inputs: []\n", encoding="utf-8")
    home_path = tmp_path / "elastic-home"
    raw = _base_consumer_config()
    raw["consumer"]["service_type"] = "elastic_agent"
    raw["consumer"]["agent_config_path"] = str(agent_config_path)
    raw["consumer"]["elastic_agent"] = {
        "executable_path": "elastic-agent",
        "home_path": "elastic-home",
        "api_host": "127.0.0.1",
        "api_port": 6792,
        "api_failon": "failed",
        "status_timeout_seconds": 2,
    }
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    loaded = consumer_config.load_config_with_overrides(
        config_path=config_path,
        server_url=None,
        server_port=None,
        agent_config_path=None,
        agent_additional_params=None,
        heartbeat_frequency=None,
        log_level=None,
        full_update_controller=None,
    )

    assert loaded.elastic_agent_executable_path == "elastic-agent"
    assert loaded.elastic_agent_home_path == str(home_path)
    assert loaded.elastic_agent_api_host == "127.0.0.1"
    assert loaded.elastic_agent_api_port == 6792
    assert loaded.elastic_agent_api_failon == "failed"
    assert loaded.elastic_agent_status_timeout_seconds == 2


def test_vector_plugin_defaults_load_without_vector_config_section(tmp_path) -> None:
    """Vector-owned defaults should not live on the shared ConsumerConfig dataclass."""
    agent_config_path = tmp_path / "vector.yaml"
    agent_config_path.write_text("api:\n  enabled: true\n", encoding="utf-8")
    raw = _base_consumer_config()
    raw["consumer"]["service_type"] = "vector"
    raw["consumer"]["agent_config_path"] = str(agent_config_path)
    raw["consumer"].pop("vector", None)
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    loaded = consumer_config.load_config_with_overrides(
        config_path=config_path,
        server_url=None,
        server_port=None,
        agent_config_path=None,
        agent_additional_params=None,
        heartbeat_frequency=None,
        log_level=None,
        full_update_controller=None,
    )

    assert "vector_executable_path" not in consumer_config.ConsumerConfig.__dataclass_fields__
    assert loaded.vector_executable_path == "vector"
    assert loaded.vector_api_host == "127.0.0.1"
    assert loaded.vector_api_port == 8686
    assert loaded.vector_status_timeout_seconds == 5.0


def test_process_tracking_defaults_to_supervisor_when_missing(
    tmp_path, monkeypatch
) -> None:
    """Consumer process_tracking should default to supervisor when omitted."""
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(_base_consumer_config(), indent=2),
        encoding="utf-8",
    )
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.process_tracking == consumer_config.PROCESS_TRACKING_SUPERVISOR
    assert loaded.process_detection_regex is None


def test_process_tracking_observer_requires_detection_regex(
    tmp_path, monkeypatch
) -> None:
    """Observer process tracking mode must include processDetectionRegex."""
    raw = _base_consumer_config()
    raw["consumer"]["processTracking"] = "Observer"
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    with pytest.raises(
        ValueError,
        match=(
            "consumer.processDetectionRegex is required when "
            "consumer.processTracking=observer"
        ),
    ):
        consumer_config.load_config()


def test_process_tracking_observer_loads_detection_regex(
    tmp_path, monkeypatch
) -> None:
    """Observer process tracking should load regex when provided."""
    raw = _base_consumer_config()
    raw["consumer"]["processTracking"] = "observer"
    raw["consumer"]["processDetectionRegex"] = r"fluent-bit\\s+-c"
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.process_tracking == consumer_config.PROCESS_TRACKING_OBSERVER
    assert loaded.process_detection_regex == r"fluent-bit\\s+-c"


def test_service_type_simulator_requires_responses_path(tmp_path, monkeypatch) -> None:
    """Simulator mode must provide consumer.simulator_responses_path."""
    raw = _base_consumer_config()
    raw["consumer"]["service_type"] = consumer_config.SERVICE_TYPE_SIMULATOR
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    with pytest.raises(
        ValueError,
        match=(
            "consumer.simulator_responses_path is required when "
            "consumer.service_type=simulator"
        ),
    ):
        consumer_config.load_config()


def test_service_type_simulator_loads_responses_path(tmp_path, monkeypatch) -> None:
    """Simulator mode should accept a valid scripted responses file path."""
    raw = _base_consumer_config()
    responses_path = tmp_path / "simulator-responses.json"
    responses_path.write_text(
        json.dumps({"responses": {"remote_config": ["accept"]}}, indent=2),
        encoding="utf-8",
    )
    raw["consumer"]["service_type"] = consumer_config.SERVICE_TYPE_SIMULATOR
    raw["consumer"]["simulator_responses_path"] = str(responses_path)
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.service_type == consumer_config.SERVICE_TYPE_SIMULATOR
    assert loaded.simulator_responses_path == str(responses_path)


def test_consumer_tls_defaults_when_missing(tmp_path, monkeypatch) -> None:
    raw = _base_consumer_config()
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.tls_verify_server is True
    assert loaded.tls_ca_file is None


def test_consumer_tls_loads_verify_and_ca_file(tmp_path, monkeypatch) -> None:
    raw = _base_consumer_config()
    ca_file = tmp_path / "ca-root.pem"
    ca_file.write_text("dummy ca", encoding="utf-8")
    raw["consumer"]["tls"] = {
        "verify_server": False,
        "ca_file": str(ca_file),
    }
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.tls_verify_server is False
    assert loaded.tls_ca_file == str(ca_file)


def test_consumer_tls_ca_file_must_exist(tmp_path, monkeypatch) -> None:
    raw = _base_consumer_config()
    raw["consumer"]["tls"] = {
        "verify_server": True,
        "ca_file": str(tmp_path / "missing-ca.pem"),
    }
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    with pytest.raises(ValueError, match="consumer.tls.ca_file must reference an existing file"):
        consumer_config.load_config()


def test_server_authorization_defaults_none_when_missing(tmp_path, monkeypatch) -> None:
    raw = _base_consumer_config()
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.server_authorization == consumer_config.SERVER_AUTHORIZATION_NONE


def test_server_authorization_loads_from_canonical_key(tmp_path, monkeypatch) -> None:
    raw = _base_consumer_config()
    raw["consumer"]["server-authorization"] = "config-var"
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.server_authorization == consumer_config.SERVER_AUTHORIZATION_CONFIG_VAR


def test_server_authorization_ignores_removed_legacy_key(tmp_path, monkeypatch) -> None:
    raw = _base_consumer_config()
    raw["consumer"]["use_authorization"] = "true"
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.server_authorization == consumer_config.SERVER_AUTHORIZATION_NONE


def test_server_authorization_loads_idp_settings(tmp_path, monkeypatch) -> None:
    raw = _base_consumer_config()
    raw["consumer"]["server-authorization"] = "idp"
    raw["consumer"]["idp-token-url"] = "http://idp.example.com/token"
    raw["consumer"]["idp-client-id"] = "client-id"
    raw["consumer"]["idp-client-secret"] = "client-secret"
    raw["consumer"]["idp-scope"] = "opamp.read"
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.server_authorization == consumer_config.SERVER_AUTHORIZATION_IDP
    assert loaded.idp_token_url == "http://idp.example.com/token"
    assert loaded.idp_client_id == "client-id"
    assert loaded.idp_client_secret == "client-secret"
    assert loaded.idp_scope == "opamp.read"


def test_allow_custom_capabilities_true_when_configured(
    tmp_path, monkeypatch
) -> None:
    raw = _base_consumer_config()
    raw["consumer"]["allow_custom_capabilities"] = True
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.allow_custom_capabilities is True


def test_chat_ops_port_defaults_none_when_missing(tmp_path, monkeypatch) -> None:
    raw = _base_consumer_config()
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.chat_ops_port is None


def test_chat_ops_port_and_client_status_port_load_when_configured(
    tmp_path, monkeypatch
) -> None:
    raw = _base_consumer_config()
    raw["consumer"]["chat_ops_port"] = 8888
    raw["consumer"]["client_status_port"] = 2020
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.chat_ops_port == 8888
    assert loaded.client_status_port == 2020


def test_agent_capabilities_override_loads_from_config(tmp_path, monkeypatch) -> None:
    """Configured agent capability names should load as the raw override list."""
    raw = _base_consumer_config()
    raw["consumer"]["agent_capabilities"] = ["ReportsHeartbeat"]
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.agent_capabilities == ["ReportsHeartbeat"]


def test_full_update_controller_loads_from_config_object(tmp_path, monkeypatch) -> None:
    """Load full_update_controller object from config file."""
    raw = _base_consumer_config()
    raw["consumer"]["full_update_controller"] = {"fullResendAfter": 3}
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.full_update_controller == {"fullResendAfter": 3}


def test_full_update_controller_cli_override_uses_string(tmp_path) -> None:
    """Apply full_update_controller CLI override as a JSON string."""
    raw = _base_consumer_config()
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    loaded = consumer_config.load_config_with_overrides(
        config_path=config_path,
        server_url=None,
        server_port=None,
        agent_config_path=None,
        agent_additional_params=None,
        heartbeat_frequency=None,
        log_level=None,
        full_update_controller='{"fullResendAfter":2}',
    )

    assert loaded.full_update_controller == '{"fullResendAfter":2}'


def test_full_update_controller_type_loads_from_config(tmp_path, monkeypatch) -> None:
    """Load full_update_controller_type from config file."""
    raw = _base_consumer_config()
    raw["consumer"]["full_update_controller_type"] = "TimeSend"
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.full_update_controller_type == "TimeSend"


def test_fluentd_test_config_loads_successfully() -> None:
    """Ensure the Fluentd test config file is valid for consumer config loading."""
    repo_root = Path(__file__).resolve().parents[2]
    config_path = repo_root / "consumer" / "opamp-fluentd.json"

    loaded = consumer_config.load_config_with_overrides(
        config_path=config_path,
        server_url=None,
        server_port=None,
        agent_config_path=None,
        agent_additional_params=None,
        heartbeat_frequency=None,
        log_level=None,
        full_update_controller=None,
    )

    assert loaded.service_name == "Fluentd"
    assert loaded.agent_config_path == "./consumer/fluentd.conf"
    assert loaded.service_type == consumer_config.SERVICE_TYPE_FLUENTD


def test_simulator_test_config_loads_successfully(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure simulator example config file is valid for consumer config loading."""
    repo_root = Path(__file__).resolve().parents[2]
    config_path = repo_root / "consumer" / "opamp-simulator.json"
    monkeypatch.chdir(repo_root)

    loaded = consumer_config.load_config_with_overrides(
        config_path=config_path,
        server_url=None,
        server_port=None,
        agent_config_path=None,
        agent_additional_params=None,
        heartbeat_frequency=None,
        log_level=None,
        full_update_controller=None,
    )

    assert loaded.service_name == "Simulator"
    assert loaded.service_type == consumer_config.SERVICE_TYPE_SIMULATOR
    assert loaded.simulator_responses_path == "./consumer/simulator-responses.example.json"


def test_consumer_observability_loads_signal_specific_endpoint(
    tmp_path,
    monkeypatch,
) -> None:
    """Consumer should load top-level OTLP settings alongside consumer config."""
    raw = _base_consumer_config()
    raw["otlp-endpoints"] = {
        "ALL": "http://collector:4317",
        "metrics": "http://metrics:4318",
        "export_interval": 42,
    }
    config_path = tmp_path / "opamp.json"
    config_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    monkeypatch.setenv(consumer_config.ENV_OPAMP_CONFIG_PATH, str(config_path))

    loaded = consumer_config.load_config()

    assert loaded.observability.resolved_logs_endpoint == "http://collector:4317"
    assert loaded.observability.resolved_metrics_endpoint == "http://metrics:4318"
    assert loaded.observability.resolved_traces_endpoint == "http://collector:4317"
    assert loaded.observability.export_interval_seconds == 42
