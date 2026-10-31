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

"""Config-service agent dry-run API test coverage.

Test-case reference: config-service/docs/TEST_CASES.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from quart import Quart

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import config_service.opamp_integration as opamp_integration
from config_service.app import create_app
from config_service.opamp_integration import register_config_service_feature
from config_service.runtime_config import ENV_CONFIG_TOOL_CONFIG_PATH


def _minimal_fluentbit_config() -> dict[str, object]:
    return {
        "env": {},
        "service": {},
        "parsers": [],
        "upstream_servers": [],
        "pipeline": {"inputs": [], "filters": [], "outputs": []},
        "labels": [],
        "workers": [],
        "includes": [],
    }


def _runtime_config_with_entry(*, dry_run_validation_enabled: bool) -> dict[str, object]:
    return {
        "config-tool": {
            "agent_validation": {
                "entries": [
                    {
                        "agent_type": "fluentbit",
                        "agent_version": "5.0.4",
                        "command_path": sys.executable,
                        "command_args": [
                            "-c",
                            (
                                "import sys; _ = sys.stdin.read(); "
                                "print('DRY_RUN_OK'); "
                                "sys.exit(0)"
                            ),
                        ],
                        "adapter": "generic",
                        "send_config_via_stdin": True,
                        "dry_run_validation_enabled": dry_run_validation_enabled,
                    }
                ]
            }
        }
    }


@pytest.mark.asyncio
async def test_agent_validation_availability_hides_disabled_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(_runtime_config_with_entry(dry_run_validation_enabled=False)),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))

    app = create_app(mode="standalone")
    client = app.test_client()

    resp = await client.get("/config-service/api/v1/agent-validation/availability/5.0.4?config_type=fluentbit")
    assert resp.status_code == 200
    body = await resp.get_json()
    assert body["ok"] is True
    assert body["available"] is False


@pytest.mark.asyncio
async def test_embedded_agent_validation_availability_registers_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(_runtime_config_with_entry(dry_run_validation_enabled=False)),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))

    app = Quart(__name__)
    register_config_service_feature(app)
    client = app.test_client()

    resp = await client.get("/config-service/api/v1/agent-validation/availability/5.0.4?config_type=fluentbit")
    assert resp.status_code == 200
    body = await resp.get_json()
    assert body["ok"] is True
    assert body["available"] is False


def test_register_config_service_feature_wraps_bootstrap_errors_with_stage_and_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = Quart(__name__)

    def _raise_catalog_error(self: object) -> None:
        raise ValueError("broken catalog payload")

    monkeypatch.setattr(opamp_integration.CatalogService, "load_all_catalogs", _raise_catalog_error)

    with pytest.raises(RuntimeError) as exc_info:
        opamp_integration.register_config_service_feature(app)

    message = str(exc_info.value)
    assert "catalog definitions" in message
    assert "catalog-registry.json" in message
    assert "broken catalog payload" in message


@pytest.mark.asyncio
async def test_agent_validation_dry_run_rejects_when_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(_runtime_config_with_entry(dry_run_validation_enabled=False)),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))

    app = create_app(mode="standalone")
    client = app.test_client()

    resp = await client.post(
        "/config-service/api/v1/agent-validation/dry-run/5.0.4?config_type=fluentbit",
        json={"config": _minimal_fluentbit_config()},
    )
    assert resp.status_code == 404
    body = await resp.get_json()
    assert body["ok"] is False
    assert "dry-run enabled" in body["error"]


@pytest.mark.asyncio
async def test_agent_validation_dry_run_executes_when_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "config-service.json"
    config_path.write_text(
        json.dumps(_runtime_config_with_entry(dry_run_validation_enabled=True)),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))

    app = create_app(mode="standalone")
    client = app.test_client()

    resp = await client.post(
        "/config-service/api/v1/agent-validation/dry-run/5.0.4?config_type=fluentbit",
        json={"config": _minimal_fluentbit_config()},
    )
    assert resp.status_code == 200
    body = await resp.get_json()
    assert body["ok"] is True
    assert body["agent_type"] == "fluentbit"
    assert any("DRY_RUN_OK" in message for message in body["messages"])
