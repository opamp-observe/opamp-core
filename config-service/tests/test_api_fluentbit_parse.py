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

"""Config-service Fluent Bit parsing API test coverage.

Test-case reference: config-service/docs/TEST_CASES.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config_service.app import create_app


def test_fluentbit_yaml_loader_does_not_change_safe_loader_scalar_types() -> None:
    """The Fluent Bit loader should not modify PyYAML's process-wide safe loader."""
    loaded = yaml.safe_load("enabled: true\nmissing: null\n")

    assert loaded == {"enabled": True, "missing": None}


@pytest.mark.asyncio
async def test_parse_fluentbit_yaml_maps_native_routes_to_internal_route() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    yaml_text = """
pipeline:
  inputs:
    - name: tail
      path: /var/log/app.log
      tag: app.logs
      routes:
        logs:
          - name: error_logs
            condition:
              op: and
              rules:
                - field: "$level"
                  op: eq
                  value: error
            to:
              outputs:
                - error_destination
  outputs:
    - name: stdout
      alias: error_destination
""".strip()

    response = await client.post(
        "/config-service/api/v1/parse/fluentbit/5.0.4",
        json={"text": yaml_text},
    )
    assert response.status_code == 200
    body = await response.get_json()
    route = body["config"]["pipeline"]["inputs"][0]["route"]
    assert "logs" in route
    assert route["logs"][0]["name"] == "error_logs"
    assert route["logs"][0]["to"]["outputs"] == ["error_destination"]

@pytest.mark.asyncio
async def test_parse_fluentbit_yaml_loads_parsers() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    yaml_text = """
parsers:
  - name: app_json
    format: json
    time_key: timestamp
pipeline:
  inputs:
    - name: tcp
      chunk_size: 32
      parser: app_json
  outputs:
    - name: null
""".strip()

    response = await client.post(
        "/config-service/api/v1/parse/fluentbit/5.0.4",
        json={"text": yaml_text},
    )
    assert response.status_code == 200
    body = await response.get_json()
    assert body["config"]["parsers"][0]["name"] == "app_json"
    assert body["config"]["parsers"][0]["format"] == "json"
    assert body["config"]["pipeline"]["inputs"][0]["parser"] == "app_json"

@pytest.mark.asyncio
async def test_parse_fluentbit_yaml_recursively_loads_includes(tmp_path: Path) -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    grandchild = tmp_path / "grandchild.yaml"
    grandchild.write_text(
        """
parsers:
  - name: app_json
    format: json
""".strip(),
        encoding="utf-8",
    )
    child = tmp_path / "child.yaml"
    child.write_text(
        """
includes:
  - grandchild.yaml
pipeline:
  outputs:
    - name: null
      match: '*'
""".strip(),
        encoding="utf-8",
    )
    root = tmp_path / "root.yaml"
    root.write_text(
        """
includes:
  - child.yaml
pipeline:
  inputs:
    - name: tcp
      chunk_size: 32
      parser: app_json
""".strip(),
        encoding="utf-8",
    )

    response = await client.post(
        "/config-service/api/v1/parse/fluentbit/5.0.4",
        json={
            "text": root.read_text(encoding="utf-8"),
            "source_path": str(root),
            "resolve_includes": True,
        },
    )
    assert response.status_code == 200
    body = await response.get_json()
    assert body["config"]["includes"] == ["child.yaml"]
    assert len(body["included_documents"]) == 1
    child_doc = body["included_documents"][0]
    assert child_doc["resolved_path"].endswith("child.yaml")
    assert child_doc["config"]["pipeline"]["outputs"][0]["name"] == "null"
    assert len(child_doc["included_documents"]) == 1
    grandchild_doc = child_doc["included_documents"][0]
    assert grandchild_doc["resolved_path"].endswith("grandchild.yaml")
    assert grandchild_doc["config"]["parsers"][0]["name"] == "app_json"

@pytest.mark.asyncio
async def test_validate_can_merge_recursive_includes_without_mutation(tmp_path: Path) -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    grandchild = tmp_path / "grandchild.yaml"
    grandchild.write_text(
        """
parsers:
  - name: app_json
    format: json
""".strip(),
        encoding="utf-8",
    )
    child = tmp_path / "child.yaml"
    child.write_text(
        """
includes:
  - grandchild.yaml
pipeline:
  outputs:
    - name: null
      match: '*'
""".strip(),
        encoding="utf-8",
    )
    root = tmp_path / "root.yaml"
    root.write_text(
        """
includes:
  - child.yaml
pipeline:
  inputs:
    - name: tcp
      chunk_size: 32
      parser: app_json
""".strip(),
        encoding="utf-8",
    )

    parse_response = await client.post(
        "/config-service/api/v1/parse/fluentbit/5.0.4",
        json={
            "text": root.read_text(encoding="utf-8"),
            "source_path": str(root),
            "resolve_includes": True,
        },
    )
    assert parse_response.status_code == 200
    parse_body = await parse_response.get_json()
    root_config = parse_body["config"]
    included_documents = parse_body["included_documents"]
    root_before = json.loads(json.dumps(root_config))
    includes_before = json.loads(json.dumps(included_documents))

    plain_validate = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json={"config": root_config, "included_documents": included_documents},
    )
    assert plain_validate.status_code == 200
    plain_body = await plain_validate.get_json()
    assert any(item["code"] == "unknown_parser_reference" for item in plain_body["errors"])

    merged_validate = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json={
            "config": root_config,
            "included_documents": included_documents,
            "merge_includes_for_validation": True,
        },
    )
    assert merged_validate.status_code == 200
    merged_body = await merged_validate.get_json()
    assert not any(item["code"] == "unknown_parser_reference" for item in merged_body["errors"])

    assert root_config == root_before
    assert included_documents == includes_before

@pytest.mark.asyncio
async def test_parse_fluentbit_yaml_loads_supported_sections_and_reports_ignored_ones() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    sample_yaml = """
service:
  flush_interval: 5
pipeline:
  inputs:
    - name: dummy
      tag: sample
  outputs:
    - name: stdout
  processors:
    - name: ignored
plugins:
  custom:
    - path: ./custom.so
""".strip()

    resp = await client.post(
        "/config-service/api/v1/parse/fluentbit/5.0.4",
        json={"text": sample_yaml},
    )
    assert resp.status_code == 200
    body = await resp.get_json()
    assert body["ok"] is False
    assert body["config"]["service"]["flush_interval"] == 5
    assert body["config"]["pipeline"]["inputs"][0]["name"] == "dummy"
    assert body["config"]["pipeline"]["outputs"][0]["name"] == "stdout"
    assert body["config"]["pipeline"]["filters"] == []

    codes = [item["code"] for item in body["errors"]]
    assert "fluentbit_yaml_ignored_section" in codes
    assert any(item["path"] == "$.pipeline.processors" for item in body["errors"])
    assert any(item["path"] == "$.plugins" for item in body["errors"])

@pytest.mark.asyncio
async def test_parse_fluentbit_yaml_preserves_null_plugin_name_and_string_enums() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    sample_yaml = """
service:
  daemon: on
  http_server: off
pipeline:
  outputs:
    - name: null
      match: '*'
""".strip()

    resp = await client.post(
        "/config-service/api/v1/parse/fluentbit/5.0.4",
        json={"text": sample_yaml},
    )
    assert resp.status_code == 200
    body = await resp.get_json()
    assert body["config"]["service"]["daemon"] == "on"
    assert body["config"]["service"]["http_server"] == "off"
    assert body["config"]["pipeline"]["outputs"][0]["name"] == "null"
    assert not body["errors"]

@pytest.mark.asyncio
async def test_parse_and_render_fluentbit_yaml_env_section_round_trips() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    sample_yaml = """
env:
  FLUSH_INTERVAL: 1
  STDOUT_FMT: json_lines
service:
  flush: ${FLUSH_INTERVAL}
pipeline:
  inputs:
    - name: random
  outputs:
    - name: stdout
      match: '*'
      format: ${STDOUT_FMT}
""".strip()

    parse_resp = await client.post(
        "/config-service/api/v1/parse/fluentbit/5.0.4",
        json={"text": sample_yaml},
    )
    assert parse_resp.status_code == 200
    parse_body = await parse_resp.get_json()
    assert parse_body["config"]["env"]["FLUSH_INTERVAL"] == 1
    assert parse_body["config"]["env"]["STDOUT_FMT"] == "json_lines"
    assert parse_body["config"]["service"]["flush"] == "${FLUSH_INTERVAL}"
    assert parse_body["config"]["pipeline"]["outputs"][0]["format"] == "${STDOUT_FMT}"

    render_resp = await client.post(
        "/config-service/api/v1/render/yaml/5.0.4?config_type=fluentbit",
        json={"config": parse_body["config"], "include_comments": False},
    )
    assert render_resp.status_code == 200
    render_body = await render_resp.get_json()
    rendered_yaml = render_body["yaml"]
    assert "env:" in rendered_yaml
    assert "FLUSH_INTERVAL: 1" in rendered_yaml
    assert "STDOUT_FMT: json_lines" in rendered_yaml
    assert "flush: ${FLUSH_INTERVAL}" in rendered_yaml
    assert "format: ${STDOUT_FMT}" in rendered_yaml

@pytest.mark.asyncio
async def test_parse_and_render_fluentbit_yaml_metadata_env_round_trips() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    sample_yaml = """
env:
  LOG_LEVEL: info
  _metadata.config_version: 5.0.4
  _metadata.SCM_config_version: cfg-123
  _metadata.configuration_date: 2026-05-09
  _metadata.config_type: Fluentbit
  _metadata.SCM_source_name: parse-test
pipeline:
  inputs:
    - name: random
  outputs:
    - name: stdout
      match: '*'
""".strip()

    parse_resp = await client.post(
        "/config-service/api/v1/parse/fluentbit/5.0.4",
        json={"text": sample_yaml},
    )
    assert parse_resp.status_code == 200
    parse_body = await parse_resp.get_json()
    assert parse_body["config"]["env"]["LOG_LEVEL"] == "info"
    assert str(parse_body["config"]["env"]["_metadata.config_version"]) == "5.0.4"
    assert parse_body["config"]["env"]["_metadata.SCM_config_version"] == "cfg-123"
    parsed_date_value = str(parse_body["config"]["env"]["_metadata.configuration_date"])
    assert "2026" in parsed_date_value
    assert "09" in parsed_date_value
    assert parse_body["config"]["env"]["_metadata.config_type"] == "Fluentbit"
    assert parse_body["config"]["env"]["_metadata.SCM_source_name"] == "parse-test"

    render_resp = await client.post(
        "/config-service/api/v1/render/yaml/5.0.4?config_type=fluentbit",
        json={"config": parse_body["config"], "include_comments": False},
    )
    assert render_resp.status_code == 200
    render_body = await render_resp.get_json()
    rendered_yaml = render_body["yaml"]
    assert "_metadata.config_version: 5.0.4" in rendered_yaml
    assert "_metadata.SCM_config_version: cfg-123" in rendered_yaml
    assert "_metadata.configuration_date:" in rendered_yaml
    assert "_metadata.config_type: Fluentbit" in rendered_yaml
    assert "_metadata.SCM_source_name: parse-test" in rendered_yaml

@pytest.mark.asyncio
async def test_parse_fluentbit_yaml_reports_invalid_env_section_type() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    sample_yaml = """
env:
  - FLUSH_INTERVAL=1
pipeline:
  inputs:
    - name: random
""".strip()

    resp = await client.post(
        "/config-service/api/v1/parse/fluentbit/5.0.4",
        json={"text": sample_yaml},
    )
    assert resp.status_code == 200
    body = await resp.get_json()
    assert body["ok"] is False
    assert any(item["path"] == "$.env" for item in body["errors"])
    assert body["config"]["env"] == {}

@pytest.mark.asyncio
async def test_parse_and_render_fluentbit_yaml_upstream_servers_round_trips() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    sample_yaml = """
upstream_servers:
  - name: forward-balancing
    nodes:
      - name: node-1
        host: 127.0.0.1
        port: 43000
      - name: node-2
        host: 127.0.0.1
        port: 44000
        tls: true
        tls_verify: false
        shared_key: secret
pipeline:
  inputs:
    - name: random
  outputs:
    - name: stdout
      match: '*'
""".strip()

    parse_resp = await client.post(
        "/config-service/api/v1/parse/fluentbit/5.0.4",
        json={"text": sample_yaml},
    )
    assert parse_resp.status_code == 200
    parse_body = await parse_resp.get_json()
    assert parse_body["ok"] is True
    assert parse_body["config"]["upstream_servers"][0]["name"] == "forward-balancing"
    assert parse_body["config"]["upstream_servers"][0]["nodes"][0]["name"] == "node-1"
    assert parse_body["config"]["upstream_servers"][0]["nodes"][1]["tls"] == "true"
    assert parse_body["config"]["upstream_servers"][0]["nodes"][1]["tls_verify"] == "false"
    assert parse_body["config"]["upstream_servers"][0]["nodes"][1]["shared_key"] == "secret"

    render_resp = await client.post(
        "/config-service/api/v1/render/yaml/5.0.4?config_type=fluentbit",
        json={"config": parse_body["config"], "include_comments": False},
    )
    assert render_resp.status_code == 200
    render_body = await render_resp.get_json()
    rendered_yaml = render_body["yaml"]
    assert "upstream_servers:" in rendered_yaml
    assert "nodes:" in rendered_yaml
    assert "shared_key: secret" in rendered_yaml

@pytest.mark.asyncio
async def test_parse_fluentbit_yaml_reports_invalid_upstream_servers_section_type() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    sample_yaml = """
upstream_servers:
  name: invalid
pipeline:
  inputs:
    - name: random
""".strip()

    resp = await client.post(
        "/config-service/api/v1/parse/fluentbit/5.0.4",
        json={"text": sample_yaml},
    )
    assert resp.status_code == 200
    body = await resp.get_json()
    assert body["ok"] is False
    assert any(item["path"] == "$.upstream_servers" for item in body["errors"])
    assert body["config"]["upstream_servers"] == []

@pytest.mark.asyncio
async def test_parse_fluentbit_yaml_rejects_empty_file() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    resp = await client.post(
        "/config-service/api/v1/parse/fluentbit/5.0.4",
        json={"text": " \n  "},
    )
    assert resp.status_code == 400
    body = await resp.get_json()
    assert body["ok"] is False
    assert body["errors"][0]["code"] == "empty_input_file"
