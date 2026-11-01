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

import json
import logging
from pathlib import Path

import opamp_consumer.client_bootstrap as client_bootstrap
import opamp_consumer.fluentbit.client as client
from opamp_consumer.config import ConsumerConfig
from opamp_consumer.fluentbit.client import CONFIG_DOCS_URL


def test_main_help_prints_config_parameters_and_skips_client(
    monkeypatch, capsys
) -> None:
    """`--help` should print config parameters and skip creating OpAMPClient."""
    config = ConsumerConfig(
        server_url="http://localhost",
        agent_config_path="unused",
        agent_additional_params=[],
        heartbeat_frequency=30,
        agent_capabilities=0,
        log_level="debug",
    )
    monkeypatch.setattr(
        client.consumer_config, "load_config_with_overrides", lambda **_: config
    )
    monkeypatch.setattr(
        client,
        "OpAMPClient",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("OpAMPClient should not be created for --help")
        ),
    )
    monkeypatch.setattr(client.sys, "argv", ["opamp-consumer", "--help"])

    client.main()

    out = capsys.readouterr().out
    json_start = out.find("{")
    assert json_start >= 0
    payload = json.loads(out[json_start:])
    assert payload["server_url"] == "http://localhost"
    assert payload["documentation_url"] == CONFIG_DOCS_URL
    assert isinstance(payload["component_version"], str)


def test_common_parser_accepts_canonical_agent_args() -> None:
    """Shared parser should accept canonical agent argument names."""
    parser = client_bootstrap.build_common_cli_parser()

    parsed = parser.parse_args(
        [
            "--config-path",
            "consumer/opamp-fluentd.json",
            "--agent-config-path",
            "consumer/fluentd.conf",
            "--agent-additional-params",
            "quiet-mode",
        ]
    )

    assert parsed.config_path == "consumer/opamp-fluentd.json"
    assert parsed.agent_config_path == "consumer/fluentd.conf"
    assert parsed.agent_additional_params == ["quiet-mode"]


def test_common_parser_accepts_cli_config_flag() -> None:
    """Shared parser should recognize the cli-config early-exit flag."""
    parser = client_bootstrap.build_common_cli_parser()

    parsed = parser.parse_args(["--cli-config"])

    assert parsed.cli_config is True


def test_main_cli_config_prints_config_file_and_skips_client(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    """`--cli-config` should pretty-print the resolved config file and exit early."""
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(
            {
                "consumer": {
                    "server_url": "http://localhost",
                    "agent_config_path": "consumer/fluent-bit.yaml",
                    "agent_additional_params": [],
                    "heartbeat_frequency": 30,
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        client,
        "OpAMPClient",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("OpAMPClient should not be created for --cli-config")
        ),
    )
    monkeypatch.setattr(
        client.sys,
        "argv",
        ["opamp-consumer", "--cli-config", "--config-path", str(config_path)],
    )

    client.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "consumer": {
            "agent_additional_params": [],
            "agent_config_path": "consumer/fluent-bit.yaml",
            "heartbeat_frequency": 30,
            "server_url": "http://localhost",
        }
    }


def test_load_config_from_cli_args_maps_overrides(monkeypatch) -> None:
    """Config loader should map parsed CLI args into override keyword arguments."""
    parser = client_bootstrap.build_common_cli_parser()
    args = parser.parse_args(
        [
            "--config-path",
            "tests/opamp.json",
            "--server-url",
            "http://127.0.0.1",
            "--server-port",
            "8080",
            "--agent-config-path",
            "consumer/fluent-bit.yaml",
            "--agent-additional-params",
            "dry-run",
            "--heartbeat-frequency",
            "15",
            "--log-level",
            "info",
            "--full-update-controller",
            '{"fullResendAfter":10}',
        ]
    )
    captured: dict[str, object] = {}
    expected = ConsumerConfig(
        server_url="http://127.0.0.1",
        agent_config_path="consumer/fluent-bit.yaml",
        agent_additional_params=["--dry-run"],
        heartbeat_frequency=15,
        agent_capabilities=0,
        log_level="info",
    )

    monkeypatch.setattr(
        client_bootstrap.consumer_config,
        "get_effective_config_path",
        lambda raw_path: f"/effective/{raw_path}",
    )

    def _fake_load_config_with_overrides(**kwargs) -> ConsumerConfig:
        captured.update(kwargs)
        return expected

    monkeypatch.setattr(
        client_bootstrap.consumer_config,
        "load_config_with_overrides",
        _fake_load_config_with_overrides,
    )

    loaded = client_bootstrap.load_config_from_cli_args(args)

    assert loaded is expected
    assert captured == {
        "config_path": "/effective/tests/opamp.json",
        "server_url": "http://127.0.0.1",
        "server_port": 8080,
        "agent_config_path": "consumer/fluent-bit.yaml",
        "agent_additional_params": ["dry-run"],
        "heartbeat_frequency": 15,
        "log_level": "info",
        "full_update_controller": '{"fullResendAfter":10}',
    }


def test_log_runtime_config_path_logs_absolute_path(
    monkeypatch, caplog
) -> None:
    """Runtime config-path helper should log the resolved absolute path."""
    resolved_path = Path("/tmp/consumer-config.json")
    monkeypatch.setattr(
        client_bootstrap.consumer_config,
        "get_effective_config_path",
        lambda raw_path: resolved_path,
    )
    logger = logging.getLogger("consumer-test")
    caplog.set_level(logging.INFO, logger="consumer-test")

    logged_path = client_bootstrap.log_runtime_config_path(
        logger=logger,
        runtime_name="consumer",
        config_path="consumer/opamp.json",
    )

    assert logged_path == resolved_path
    assert f"using consumer config path: {resolved_path}" in caplog.text


def test_validate_runtime_server_config_applies_server_port_when_url_has_no_port() -> None:
    """Runtime normalization should apply server_port to host-only server_url values."""
    config = ConsumerConfig(
        server_url="http://127.0.0.1",
        server_port=4320,
        client_status_port=2020,
    )

    loaded = client_bootstrap.validate_runtime_server_config(
        config=config,
        localhost_base="http://localhost",
        missing_status_port_error="missing status",
    )

    assert loaded.server_url == "http://127.0.0.1:4320"


def test_validate_runtime_server_config_keeps_existing_server_url_port() -> None:
    """Runtime normalization should preserve explicit port already present in server_url."""
    config = ConsumerConfig(
        server_url="http://127.0.0.1:8080/path?x=1",
        server_port=4320,
        client_status_port=2020,
    )

    loaded = client_bootstrap.validate_runtime_server_config(
        config=config,
        localhost_base="http://localhost",
        missing_status_port_error="missing status",
    )

    assert loaded.server_url == "http://127.0.0.1:8080/path?x=1"
