#!/usr/bin/env python3
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

"""Config-service agent validation test coverage.

Test-case reference: config-service/docs/TEST_CASES.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config_service.agent_validation import validate
from config_service.agent_validation.adapters.base import TemplateCommandAdapter
from config_service.agent_validation.adapters.fluentbit import FluentBitValidationAdapter
from config_service.agent_validation.adapters.fluentd import FluentdValidationAdapter
from config_service.agent_validation.exceptions import AgentCommandBuildError
from config_service.agent_validation.exceptions import AgentNotSupportedError
from config_service.agent_validation.service import (
    ExternalAgentValidationService,
    ValidationAgentRegistry,
)


def _python_entry_payload(
    *,
    version: str | None = None,
    send_via_stdin: bool = True,
    dry_run_enabled: bool | None = None,
) -> dict[str, object]:
    if send_via_stdin:
        command_args = [
            "-c",
            (
                "import sys; data = sys.stdin.read(); "
                "print('CONFIG_OK' if data.strip() else 'CONFIG_EMPTY'); "
                "sys.exit(0 if data.strip() else 2)"
            ),
        ]
    else:
        command_args = [
            "-c",
            (
                "import pathlib, sys; "
                "path = pathlib.Path(sys.argv[1]); "
                "print('PATH_OK' if path.exists() else 'PATH_MISSING'); "
                "sys.exit(0 if path.exists() else 3)"
            ),
            "{config_path}",
        ]

    payload: dict[str, object] = {
        "agent_type": "fluentbit",
        "agent_version": version,
        "command_path": sys.executable,
        "command_args": command_args,
        "send_config_via_stdin": send_via_stdin,
        "adapter": "generic",
        "success_exit_codes": [0],
    }
    if dry_run_enabled is not None:
        payload["dry_run_validation_enabled"] = dry_run_enabled
    return payload


def test_validate_exact_version_match_uses_requested_entry() -> None:
    registry = ValidationAgentRegistry.from_config_payload(
        [
            _python_entry_payload(version="5.0.4", send_via_stdin=True),
            _python_entry_payload(version=None, send_via_stdin=True),
        ]
    )
    service = ExternalAgentValidationService(registry)

    result = service.validate(
        "service:\n  flush: 1\n",
        agent_type="fluentbit",
        agent_version="5.0.4",
    )

    assert result["ok"] is True
    assert result["used_agent_version"] == "5.0.4"
    assert result["version_mismatch"] is False
    assert any("CONFIG_OK" in message for message in result["messages"])


def test_validate_version_fallback_uses_unversioned_entry() -> None:
    registry = ValidationAgentRegistry.from_config_payload(
        [
            _python_entry_payload(version="4.2.4", send_via_stdin=True),
            _python_entry_payload(version=None, send_via_stdin=True),
        ]
    )
    service = ExternalAgentValidationService(registry)

    result = service.validate(
        "service:\n  flush: 1\n",
        agent_type="fluentbit",
        agent_version="9.9.9",
    )

    assert result["ok"] is True
    assert result["used_agent_version"] is None
    assert result["version_mismatch"] is True
    assert any("CONFIG_OK" in message for message in result["messages"])


def test_validate_supports_temporary_file_path_mode() -> None:
    registry = ValidationAgentRegistry.from_config_payload(
        [_python_entry_payload(version=None, send_via_stdin=False)]
    )
    service = ExternalAgentValidationService(registry)

    result = service.validate(
        "service:\n  flush: 1\n",
        agent_type="fluentbit",
    )

    assert result["ok"] is True
    assert any("PATH_OK" in message for message in result["messages"])


def test_validate_raises_for_unknown_agent_type() -> None:
    registry = ValidationAgentRegistry.from_config_payload(
        [_python_entry_payload(version=None, send_via_stdin=True)]
    )
    service = ExternalAgentValidationService(registry)
    with pytest.raises(AgentNotSupportedError):
        service.validate("service:\n  flush: 1\n", agent_type="fluentd")


def test_public_validate_function_reads_runtime_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(
            {
                "config-tool": {
                    "agent_validation": {
                        "entries": [
                            _python_entry_payload(version="5.0.4", send_via_stdin=True),
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("CONFIG_TOOL_CONFIG_PATH", str(config_path))

    result = validate(
        "service:\n  flush: 1\n",
        agent_type="fluentbit",
        agent_version="5.0.4",
    )
    assert result["ok"] is True
    assert result["used_agent_version"] == "5.0.4"


def test_validate_require_dry_run_enabled_uses_eligible_fallback() -> None:
    registry = ValidationAgentRegistry.from_config_payload(
        [
            _python_entry_payload(version="5.0.4", send_via_stdin=True, dry_run_enabled=False),
            _python_entry_payload(version=None, send_via_stdin=True, dry_run_enabled=True),
        ]
    )
    service = ExternalAgentValidationService(registry)

    result = service.validate(
        "service:\n  flush: 1\n",
        agent_type="fluentbit",
        agent_version="5.0.4",
        require_dry_run_enabled=True,
    )

    assert result["ok"] is True
    assert result["used_agent_version"] is None
    assert result["version_mismatch"] is True


def test_validate_require_dry_run_enabled_raises_when_disabled() -> None:
    registry = ValidationAgentRegistry.from_config_payload(
        [_python_entry_payload(version=None, send_via_stdin=True, dry_run_enabled=False)]
    )
    service = ExternalAgentValidationService(registry)

    with pytest.raises(AgentNotSupportedError):
        service.validate(
            "service:\n  flush: 1\n",
            agent_type="fluentbit",
            require_dry_run_enabled=True,
        )


def test_fluentbit_adapter_filters_banner_lines_from_messages() -> None:
    adapter = FluentBitValidationAdapter()
    result = adapter.interpret_result(
        "___\n"
        " | ___\n"
        "| ___\n"
        "[ info] dry run started\n"
        "[error] parse failed\n"
    )

    assert result["messages"] == ["[ info] dry run started", "[error] parse failed"]
    assert result["ok"] is False


def test_template_command_adapter_logs_placeholder_rejection(caplog: pytest.LogCaptureFixture) -> None:
    adapter = TemplateCommandAdapter()
    caplog.set_level("ERROR")

    with pytest.raises(AgentCommandBuildError):
        adapter.create_command(
            config_text="service:\n  flush: 1\n",
            config_path=None,
            entry=ValidationAgentRegistry.from_config_payload(
                [_python_entry_payload(version=None, send_via_stdin=False)]
            ).entries[0],
        )

    assert "config_path placeholder was present without a file path" in caplog.text


def test_template_command_adapter_logs_lifecycle_without_config_text_leakage(
    caplog: pytest.LogCaptureFixture,
) -> None:
    adapter = TemplateCommandAdapter()
    caplog.set_level("INFO")
    config_text = "service:\n  token: super-secret-value\n"
    entry = ValidationAgentRegistry.from_config_payload(
        [
            {
                "agent_type": "fluentbit",
                "command_path": sys.executable,
                "command_args": ["-c", "{config_text}"],
                "adapter": "generic",
                "success_exit_codes": [0],
            }
        ]
    ).entries[0]

    command = adapter.create_command(
        config_text=config_text,
        config_path=None,
        entry=entry,
    )

    assert "super-secret-value" in command
    assert "building validation command" in caplog.text
    assert "validation command built" in caplog.text
    assert "super-secret-value" not in caplog.text


def test_fluentbit_adapter_logs_unhappy_path(caplog: pytest.LogCaptureFixture) -> None:
    adapter = FluentBitValidationAdapter()
    caplog.set_level("INFO")

    result = adapter.interpret_result(
        "[ info] dry run started\n"
        "[error] parse failed\n"
    )

    assert result["ok"] is False
    assert "starting Fluent Bit result interpretation" in caplog.text
    assert "Fluent Bit validation output contains error lines" in caplog.text
    assert "completed Fluent Bit result interpretation" in caplog.text


def test_fluentbit_adapter_logs_empty_actionable_output(caplog: pytest.LogCaptureFixture) -> None:
    adapter = FluentBitValidationAdapter()
    caplog.set_level("WARNING")

    result = adapter.interpret_result("___\n| banner only\n")

    assert result["ok"] is True
    assert result["messages"] == []
    assert "Fluent Bit validation output contained no actionable lines" in caplog.text


def test_fluentd_adapter_logs_unhappy_path(caplog: pytest.LogCaptureFixture) -> None:
    adapter = FluentdValidationAdapter()
    caplog.set_level("INFO")

    result = adapter.interpret_result("config error near match block\n")

    assert result["ok"] is False
    assert "starting Fluentd result interpretation" in caplog.text
    assert "Fluentd validation output contains error lines" in caplog.text
    assert "completed Fluentd result interpretation" in caplog.text


def test_fluentd_adapter_logs_empty_output(caplog: pytest.LogCaptureFixture) -> None:
    adapter = FluentdValidationAdapter()
    caplog.set_level("WARNING")

    result = adapter.interpret_result("")

    assert result["ok"] is True
    assert result["messages"] == []
    assert "validation result was empty" in caplog.text
    assert "Fluentd validation output contained no actionable lines" in caplog.text
