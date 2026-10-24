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

# ruff: noqa: S101, S108

"""Config-service YAML rendering API test coverage.

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


@pytest.mark.asyncio
async def test_render_yaml_includes_parsers_before_pipeline() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "service": {},
            "parsers": [
                {
                    "name": "custom_json",
                    "format": "json",
                    "time_key": "timestamp",
                }
            ],
            "pipeline": {
                "inputs": [],
                "filters": [],
                "outputs": [],
            },
        }
    }

    response = await client.post(
        "/config-service/api/v1/render/yaml/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert response.status_code == 200
    body = await response.get_json()
    rendered = body["yaml"]
    assert "parsers:" in rendered
    assert "pipeline:" not in rendered
    assert rendered.index("parsers:") < rendered.index("-\n    name: custom_json")

@pytest.mark.asyncio
async def test_render_yaml_quotes_yaml_indicator_scalar_values() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "pipeline": {
                "inputs": [{"name": "dummy", "tag": "dummy"}],
                "outputs": [{"name": "stdout", "match": "*"}],
            }
        }
    }

    response = await client.post(
        "/config-service/api/v1/render/yaml/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert response.status_code == 200
    body = await response.get_json()
    rendered = body["yaml"]
    assert 'match: "*"' in rendered
    assert yaml.safe_load(rendered)["pipeline"]["outputs"][0]["match"] == "*"

@pytest.mark.asyncio
async def test_render_yaml_translates_route_object_to_native_routes_block() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "pipeline": {
                "inputs": [
                    {
                        "name": "tail",
                        "path": "/var/log/app.log",
                        "tag": "app.logs",
                        "route": {
                            "per_record_routing": True,
                            "logs": [
                                {
                                    "name": "error_logs",
                                    "condition": {
                                        "op": "and",
                                        "rules": [
                                            {"context": "body", "field": "$level", "op": "eq", "value": "error"}
                                        ],
                                    },
                                    "to": {"outputs": ["error_destination"]},
                                }
                            ],
                        },
                    }
                ],
                "filters": [],
                "outputs": [
                    {"name": "stdout", "alias": "error_destination"}
                ],
            }
        }
    }

    response = await client.post(
        "/config-service/api/v1/render/yaml/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert response.status_code == 200
    body = await response.get_json()
    rendered = body["yaml"]
    assert "route:" not in rendered
    assert "routes:" in rendered
    assert "per_record_routing: true" in rendered
    assert "outputs:" in rendered
    assert "error_destination" in rendered

@pytest.mark.asyncio
async def test_render_yaml_omits_empty_processors_block() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "pipeline": {
                "inputs": [
                    {
                        "name": "tail",
                        "tag": "app.logs",
                        "processors": {
                            "logs": None,
                            "metrics": None,
                            "traces": None,
                        },
                    }
                ],
                "filters": [],
                "outputs": [{"name": "stdout"}],
            }
        }
    }

    response = await client.post(
        "/config-service/api/v1/render/yaml/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert response.status_code == 200
    body = await response.get_json()
    rendered = body["yaml"]
    assert "processors:" not in rendered
    assert "logs:" not in rendered
    assert "metrics:" not in rendered
    assert "traces:" not in rendered

@pytest.mark.asyncio
async def test_render_can_include_rendered_include_files_without_mutation() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    root_config = {
        "service": {},
        "parsers": [],
        "pipeline": {
            "inputs": [{"name": "tcp", "chunk_size": 32}],
            "filters": [],
            "outputs": [],
        },
        "labels": [],
        "workers": [],
        "includes": ["child.yaml"],
    }
    included_documents = [
        {
            "include_path": "child.yaml",
            "resolved_path": "/tmp/child.yaml",
            "ok": True,
            "errors": [],
            "config": {
                "service": {},
                "parsers": [
                    {
                        "name": "app_json",
                        "format": "json",
                    }
                ],
                "pipeline": {
                    "inputs": [],
                    "filters": [],
                    "outputs": [{"name": "null"}],
                },
                "labels": [],
                "workers": [],
                "includes": [],
            },
            "included_documents": [],
        }
    ]
    root_before = json.loads(json.dumps(root_config))
    includes_before = json.loads(json.dumps(included_documents))

    response = await client.post(
        "/config-service/api/v1/render/yaml/5.0.4?config_type=fluentbit",
        json={
            "config": root_config,
            "included_documents": included_documents,
            "render_included_files": True,
        },
    )
    assert response.status_code == 200
    body = await response.get_json()
    assert body["ok"] is True
    assert len(body["included_files"]) == 1
    include_render = body["included_files"][0]
    assert include_render["include_path"] == "child.yaml"
    assert "parsers:" in include_render["yaml"]
    assert 'name: "null"' in include_render["yaml"]

    assert root_config == root_before
    assert included_documents == includes_before

def test_include_document_service_does_not_mutate_inputs() -> None:
    app = create_app(mode="standalone")
    include_document_service = app.extensions["include_document_service"]
    yaml_render_service = app.extensions["yaml_render_service"]
    fluentd_config_service = app.extensions["fluentd_config_service"]

    root_config = {
        "service": {},
        "parsers": [],
        "pipeline": {"inputs": [{"name": "tcp", "parser": "app_json"}], "filters": [], "outputs": []},
        "labels": [],
        "workers": [],
        "includes": ["child.yaml"],
    }
    included_documents = [
        {
            "include_path": "child.yaml",
            "resolved_path": "/tmp/child.yaml",
            "ok": True,
            "errors": [],
            "config": {
                "service": {},
                "parsers": [{"name": "app_json", "format": "json"}],
                "pipeline": {"inputs": [], "filters": [], "outputs": [{"name": "null"}]},
                "labels": [],
                "workers": [],
                "includes": [],
            },
            "included_documents": [],
        }
    ]
    root_before = json.loads(json.dumps(root_config))
    includes_before = json.loads(json.dumps(included_documents))

    merged = include_document_service.merge_for_validation(
        config=root_config,
        included_documents=included_documents,
    )
    rendered = include_document_service.render_included_documents(
        config_type="fluentbit",
        included_documents=included_documents,
        include_comments=False,
        yaml_render_service=yaml_render_service,
        fluentd_config_service=fluentd_config_service,
    )

    assert merged["parsers"][0]["name"] == "app_json"
    assert rendered[0]["include_path"] == "child.yaml"
    assert root_config == root_before
    assert included_documents == includes_before

@pytest.mark.asyncio
async def test_render_yaml_omits_empty_optional_sections() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "service": {},
            "pipeline": {
                "inputs": [{"name": "forward", "port": 24224}],
                "filters": [],
                "outputs": [{"name": "stdout"}],
            },
            "labels": [],
            "workers": [],
            "includes": [],
        }
    }

    yaml_resp = await client.post(
        "/config-service/api/v1/render/yaml/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert yaml_resp.status_code == 200
    yaml_body = await yaml_resp.get_json()
    assert yaml_body["ok"] is True
    assert "filters:" not in yaml_body["yaml"]
    assert "labels:" not in yaml_body["yaml"]
    assert "workers:" not in yaml_body["yaml"]
    assert "includes:" not in yaml_body["yaml"]
    assert "service:" not in yaml_body["yaml"]

@pytest.mark.asyncio
async def test_render_yaml_omits_empty_inputs_outputs_and_pipeline() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "service": {},
            "pipeline": {
                "inputs": [],
                "filters": [],
                "outputs": [],
            },
            "labels": [],
            "workers": [],
            "includes": [],
        }
    }

    yaml_resp = await client.post(
        "/config-service/api/v1/render/yaml/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert yaml_resp.status_code == 200
    yaml_body = await yaml_resp.get_json()
    assert yaml_body["ok"] is True
    assert "service:" not in yaml_body["yaml"]
    assert "pipeline:" not in yaml_body["yaml"]
    assert "inputs:" not in yaml_body["yaml"]
    assert "filters:" not in yaml_body["yaml"]
    assert "outputs:" not in yaml_body["yaml"]
    assert yaml_body["yaml"].strip() == ""

@pytest.mark.asyncio
async def test_render_yaml_returns_backend_composed_rendered_output() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    response = await client.post(
        "/config-service/api/v1/render/yaml/5.0.4?config_type=fluentbit",
        json={
            "config": {
                "pipeline": {
                    "inputs": [{"name": "tail", "path": "/var/log/app.log"}],
                    "filters": [],
                    "outputs": [{"name": "stdout"}],
                },
            },
            "render_included_files": True,
            "included_documents": [
                {
                    "include_path": "child.yaml",
                    "ok": True,
                    "config": {
                        "pipeline": {
                            "inputs": [],
                            "filters": [],
                            "outputs": [{"name": "null"}],
                        },
                    },
                    "included_documents": [],
                }
            ],
        },
    )
    assert response.status_code == 200
    body = await response.get_json()
    assert body["ok"] is True
    assert not body["rendered_output"].startswith("# Owned by Team A")
    assert "# Included file: child.yaml" in body["rendered_output"]

@pytest.mark.asyncio
async def test_render_yaml_can_include_config_service_header_in_rendered_output() -> None:
    app = create_app(mode="standalone")
    client = app.test_client()

    response = await client.post(
        "/config-service/api/v1/render/yaml/5.0.4?config_type=fluentbit",
        json={
            "config": {
                "pipeline": {
                    "inputs": [{"name": "tail", "path": "/var/log/app.log"}],
                    "filters": [],
                    "outputs": [{"name": "stdout"}],
                },
            },
            "include_config_header": True,
        },
    )
    assert response.status_code == 200
    body = await response.get_json()
    assert body["ok"] is True
    assert body["rendered_output"].startswith(
        "# config-service: config_type=fluentbit\n# config-service: version=5.0.4\n"
    )
