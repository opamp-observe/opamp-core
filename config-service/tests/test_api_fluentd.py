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

"""Config-service Fluentd API test coverage.

Test-case reference: config-service/docs/TEST_CASES.md
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config_service.app import create_app
from config_service.runtime_config import (
    ENV_CONFIG_TOOL_CONFIG_PATH,
    resolve_log_level_name,
    resolve_read_only,
    resolve_ui_base_css_path,
    resolve_web_port,
)

@pytest.mark.asyncio
async def test_parse_and_render_fluentd_config() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    sample_conf = """
<system>
  log_level info
</system>

<source>
  @type tail
  tag app.logs
  path /var/log/app.log
  <parse>
    @type json
  </parse>
</source>

<filter app.**>
  @type grep
  <regexp>
    key message
    pattern error
  </regexp>
</filter>

<match app.**>
  @type copy
  <store>
    @type stdout
  </store>
</match>
""".strip()

    parsed_resp = await client.post(
        "/config-service/api/v1/parse/fluentd/1.19",
        json={"text": sample_conf},
    )
    assert parsed_resp.status_code == 200
    parsed_body = await parsed_resp.get_json()
    assert parsed_body["ok"] is True
    assert parsed_body["config"]["service"]["log_level"] == "info"
    assert parsed_body["config"]["pipeline"]["inputs"][0]["name"] == "tail"
    assert parsed_body["config"]["pipeline"]["filters"][0]["match"] == "app.**"
    assert parsed_body["config"]["pipeline"]["outputs"][0]["name"] == "copy"
    assert parsed_body["config"]["pipeline"]["outputs"][0]["match"] == "app.**"

    rendered_resp = await client.post(
        "/config-service/api/v1/render/fluentd/1.19",
        json={"config": parsed_body["config"]},
    )
    assert rendered_resp.status_code == 200
    rendered_body = await rendered_resp.get_json()
    assert rendered_body["ok"] is True
    assert "<source>" in rendered_body["text"]
    assert "<match app.**>" in rendered_body["text"]

@pytest.mark.asyncio
async def test_schema_endpoint_supports_fluentd() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    resp = await client.post("/config-service/api/v1/schema/1.19?config_type=fluentd", json={"strict": True})
    assert resp.status_code == 200
    body = await resp.get_json()
    assert body["ok"] is True
    assert "labels" in body["schema"]["properties"]["config"]["properties"]
    filter_plugins = body["schema"]["properties"]["config"]["properties"]["pipeline"]["properties"]["filters"]["items"]["oneOf"]
    grep_schema = next(
        item
        for item in filter_plugins
        if item.get("properties", {}).get("name", {}).get("const") == "grep"
    )
    assert "match" in grep_schema["properties"]
    assert "allOf" in grep_schema

@pytest.mark.asyncio
async def test_validate_fluentd_accepts_match_and_legacy_directive_arg() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    base_config = {
        "service": {"log_level": "info"},
        "pipeline": {
            "inputs": [{"name": "tail", "tag": "app.logs", "path": "/var/log/app.log"}],
            "filters": [],
            "outputs": [{"name": "stdout"}],
        },
    }

    canonical = json.loads(json.dumps(base_config))
    canonical["pipeline"]["outputs"][0]["match"] = "app.**"
    canonical_resp = await client.post(
        "/config-service/api/v1/validate/1.19?config_type=fluentd",
        json={"config": canonical},
    )
    assert canonical_resp.status_code == 200
    canonical_body = await canonical_resp.get_json()
    assert canonical_body["ok"] is True

    legacy = json.loads(json.dumps(base_config))
    legacy["pipeline"]["outputs"][0]["directive_arg"] = "app.**"
    legacy_resp = await client.post(
        "/config-service/api/v1/validate/1.19?config_type=fluentd",
        json={"config": legacy},
    )
    assert legacy_resp.status_code == 200
    legacy_body = await legacy_resp.get_json()
    assert legacy_body["ok"] is True

@pytest.mark.asyncio
async def test_parse_fluentd_returns_parser_errors_for_invalid_conf() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    resp = await client.post(
        "/config-service/api/v1/parse/fluentd/1.19",
        json={"text": "<source>\n  @type tail\n"},
    )
    assert resp.status_code == 400
    body = await resp.get_json()
    assert body["ok"] is False
    assert body["errors"][0]["code"] == "fluentd_parse_error"
    assert body["errors"][0]["source"] == "parser"

@pytest.mark.asyncio
async def test_parse_fluentd_rejects_empty_file() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    resp = await client.post(
        "/config-service/api/v1/parse/fluentd/1.19",
        json={"text": "   \n\t  "},
    )
    assert resp.status_code == 400
    body = await resp.get_json()
    assert body["ok"] is False
    assert body["errors"][0]["code"] == "empty_input_file"

@pytest.mark.asyncio
async def test_render_fluentd_rejects_invalid_request_payload() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    resp = await client.post("/config-service/api/v1/render/fluentd/1.19", json={})
    assert resp.status_code == 400
    body = await resp.get_json()
    assert body["ok"] is False
    assert body["errors"][0]["code"] == "pydantic_validation_error"

@pytest.mark.asyncio
async def test_render_fluentd_returns_backend_composed_rendered_output() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    response = await client.post(
        "/config-service/api/v1/render/fluentd/1.19",
        json={
            "config": {
                "service": {"log_level": "info"},
                "pipeline": {"inputs": [], "filters": [], "outputs": []},
            },
        },
    )
    assert response.status_code == 200
    body = await response.get_json()
    assert body["ok"] is True
    assert body["rendered_output"] == body["text"]

@pytest.mark.asyncio
async def test_render_fluentd_can_include_config_service_header_in_rendered_output() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    response = await client.post(
        "/config-service/api/v1/render/fluentd/1.19",
        json={
            "config": {
                "service": {"log_level": "info"},
                "pipeline": {"inputs": [], "filters": [], "outputs": []},
            },
            "include_config_header": True,
        },
    )
    assert response.status_code == 200
    body = await response.get_json()
    assert body["ok"] is True
    assert body["rendered_output"].startswith(
        "# config-service: config_type=fluentd\n# config-service: version=1.19\n"
    )
