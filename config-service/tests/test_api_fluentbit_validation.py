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

"""Config-service Fluent Bit validation API test coverage.

Test-case reference: config-service/docs/TEST_CASES.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config_service.app import create_app
from config_service.runtime_config import ENV_CONFIG_TOOL_CONFIG_PATH


def _valid_fluentbit_payload() -> dict[str, object]:
    return {
        "config": {
            "pipeline": {
                "inputs": [
                    {
                        "name": "forward",
                        "buffer_chunk_size": 1024,
                        "buffer_max_size": 2048,
                        "port": 24224,
                    }
                ],
                "filters": [],
                "outputs": [{"name": "null", "match": "*"}],
            }
        },
        "profile": "strict",
    }


def _write_catalog_config(
    config_path: Path,
    source_folder: str = "catalog",
    *,
    save_ignore_validation: bool = False,
) -> None:
    config_path.write_text(
        json.dumps(
            {
                "config-tool": {
                    "save-ingore-validation": save_ignore_validation,
                },
                "opamp": {
                    "config_catalog": {
                        "enabled": True,
                        "sources": [
                            {
                                "folder": source_folder,
                                "extensions": [".json", ".yaml", ".yml", ".conf"],
                            }
                        ],
                    }
                }
            }
        ),
        encoding="utf-8",
    )


@pytest.mark.asyncio
async def test_validate_can_save_valid_catalog_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Valid catalog saves should write the rendered Fluent Bit config to disk."""
    config_path = tmp_path / "config-service.json"
    _write_catalog_config(config_path)
    source_dir = tmp_path / "catalog"
    source_dir.mkdir()
    target_path = source_dir / "sample.yaml"
    target_path.write_text("pipeline:\n  inputs: []\n", encoding="utf-8")
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))

    app = create_app(mode="standalone")
    client = app.test_client()
    payload = {
        **_valid_fluentbit_payload(),
        "save_on_success": True,
        "save_source_path": str(target_path),
        "header_comments": "Managed by tests",
        "include_config_header": True,
    }

    response = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )

    assert response.status_code == 200
    body = await response.get_json()
    assert body["ok"] is True
    assert body["saved"] is True
    assert body["save_path"] == str(target_path.resolve())
    saved_text = target_path.read_text(encoding="utf-8")
    assert "# Managed by tests" in saved_text
    assert "# config-service: config_type=fluentbit" in saved_text
    assert "pipeline:" in saved_text
    assert "outputs:" in saved_text


@pytest.mark.asyncio
async def test_validate_declines_save_when_validation_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Validation errors should block save requests when override is disabled."""
    config_path = tmp_path / "config-service.json"
    _write_catalog_config(config_path)
    source_dir = tmp_path / "catalog"
    source_dir.mkdir()
    target_path = source_dir / "broken.yaml"
    original_text = "unchanged: true\n"
    target_path.write_text(original_text, encoding="utf-8")
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))

    app = create_app(mode="standalone")
    client = app.test_client()
    payload = {
        "config": {
            "pipeline": {
                "inputs": [
                    {
                        "name": "forward",
                        "buffer_chunk_size": 1024,
                        "buffer_max_size": 2048,
                        "port": "${BAD PORT}",
                    }
                ],
                "filters": [],
                "outputs": [{"name": "null", "match": "*"}],
            }
        },
        "profile": "strict",
        "save_on_success": True,
        "save_source_path": str(target_path),
    }

    response = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )

    assert response.status_code == 400
    body = await response.get_json()
    assert body["ok"] is False
    assert body["save_declined"] is True
    assert body["save_message"] == "Validation failed; file was not saved."
    assert target_path.read_text(encoding="utf-8") == original_text


@pytest.mark.asyncio
async def test_validate_saves_when_override_enabled_even_if_validation_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Save override should persist files even when validation reports errors."""
    config_path = tmp_path / "config-service.json"
    _write_catalog_config(config_path, save_ignore_validation=True)
    source_dir = tmp_path / "catalog"
    source_dir.mkdir()
    target_path = source_dir / "broken-but-saved.yaml"
    original_text = "unchanged: true\n"
    target_path.write_text(original_text, encoding="utf-8")
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))

    app = create_app(mode="standalone")
    client = app.test_client()
    payload = {
        "config": {
            "pipeline": {
                "inputs": [
                    {
                        "name": "forward",
                        "buffer_chunk_size": 1024,
                        "buffer_max_size": 2048,
                        "port": "${BAD PORT}",
                    }
                ],
                "filters": [],
                "outputs": [{"name": "null", "match": "*"}],
            }
        },
        "profile": "strict",
        "save_on_success": True,
        "save_source_path": str(target_path),
    }

    response = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )

    assert response.status_code == 200
    body = await response.get_json()
    assert body["ok"] is False
    assert body["saved"] is True
    assert body["save_path"] == str(target_path.resolve())
    assert body.get("save_declined") is not True
    assert body["save_message"] == f"Saved configuration with validation errors to {target_path.name}."
    saved_text = target_path.read_text(encoding="utf-8")
    assert saved_text != original_text
    assert '"${BAD PORT}"' in saved_text


@pytest.mark.asyncio
async def test_validate_rejects_save_outside_catalog_source(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Server-side save requests should be rejected outside approved catalog roots."""
    config_path = tmp_path / "config-service.json"
    _write_catalog_config(config_path)
    (tmp_path / "catalog").mkdir()
    target_path = tmp_path / "outside.yaml"
    target_path.write_text("unchanged: true\n", encoding="utf-8")
    monkeypatch.setenv(ENV_CONFIG_TOOL_CONFIG_PATH, str(config_path))

    app = create_app(mode="standalone")
    client = app.test_client()
    payload = {
        **_valid_fluentbit_payload(),
        "save_on_success": True,
        "save_source_path": str(target_path),
    }

    response = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )

    assert response.status_code == 403
    body = await response.get_json()
    assert body["ok"] is False
    assert body["save_declined"] is True
    assert body["errors"][0]["code"] == "server_save_not_allowed"
    assert target_path.read_text(encoding="utf-8") == "unchanged: true\n"

@pytest.mark.asyncio
async def test_validate_accepts_builtin_and_custom_parser_references() -> None:
    """Parser validation should allow both built-in and locally declared parser names."""
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "parsers": [
                {
                    "name": "app_json",
                    "format": "json",
                    "time_key": "timestamp",
                }
            ],
            "pipeline": {
                "inputs": [
                    {
                        "name": "tcp",
                        "chunk_size": 32,
                        "parser": "app_json",
                    },
                    {
                        "name": "tcp",
                        "chunk_size": 32,
                        "parser": "docker",
                    },
                ],
                "filters": [],
                "outputs": [{"name": "null", "match": "*"}],
            },
        },
        "profile": "strict",
    }

    response = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert response.status_code in (200, 400)
    body = await response.get_json()
    assert body["ok"] is True
    assert body["errors"] == []

@pytest.mark.asyncio
async def test_validate_accepts_env_placeholders_for_integer_and_number_fields() -> None:
    """Numeric fields should accept well-formed environment placeholder values."""
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "pipeline": {
                "inputs": [
                    {
                        "name": "forward",
                        "buffer_chunk_size": 1024,
                        "buffer_max_size": 2048,
                        "port": "${FORWARD_PORT}",
                    }
                ],
                "filters": [],
                "outputs": [
                    {
                        "name": "null",
                        "match": "*",
                        "processors": {
                            "metrics": [
                                {
                                    "name": "tda",
                                    "threshold": "${METRICS_THRESHOLD}",
                                }
                            ]
                        },
                    }
                ],
            }
        },
        "profile": "strict",
    }

    response = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert response.status_code in (200, 400)
    body = await response.get_json()
    invalid_type_errors = [item for item in body["errors"] if item["code"] == "invalid_type"]
    assert invalid_type_errors == []

@pytest.mark.asyncio
async def test_validate_rejects_invalid_env_placeholders_for_integer_and_number_fields() -> None:
    """Malformed environment placeholders should fail numeric field validation."""
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "pipeline": {
                "inputs": [
                    {
                        "name": "forward",
                        "buffer_chunk_size": 1024,
                        "buffer_max_size": 2048,
                        "port": "${BAD PORT}",
                    }
                ],
                "filters": [],
                "outputs": [
                    {
                        "name": "null",
                        "match": "*",
                        "processors": {
                            "metrics": [
                                {
                                    "name": "tda",
                                    "threshold": "${BAD!THRESHOLD}",
                                }
                            ]
                        },
                    }
                ],
            }
        },
        "profile": "strict",
    }

    response = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert response.status_code in (200, 400)
    body = await response.get_json()
    invalid_type_paths = {item["path"] for item in body["errors"] if item["code"] == "invalid_type"}
    assert "$.pipeline.inputs[0].port" in invalid_type_paths
    assert "$.pipeline.outputs[0].processors.metrics[0].threshold" in invalid_type_paths

@pytest.mark.asyncio
async def test_validate_accepts_time_values_as_integer_or_smhd_suffix() -> None:
    """Time fields should accept integers and Fluent Bit style unit suffixes."""
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "pipeline": {
                "inputs": [{"name": "dummy"}],
                "filters": [],
                "outputs": [
                    {
                        "name": "null",
                        "match": "*",
                        "processors": {
                            "metrics": [
                                {"name": "cumulative_to_delta", "max_staleness": 10},
                                {"name": "cumulative_to_delta", "max_staleness": "15H"},
                            ]
                        },
                    }
                ],
            }
        },
        "profile": "strict",
    }

    response = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert response.status_code in (200, 400)
    body = await response.get_json()
    invalid_type_errors = [item for item in body["errors"] if item["code"] == "invalid_type"]
    assert invalid_type_errors == []

@pytest.mark.asyncio
async def test_validate_rejects_invalid_time_value_format() -> None:
    """Unsupported time formats should be reported as invalid type errors."""
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "pipeline": {
                "inputs": [{"name": "dummy"}],
                "filters": [],
                "outputs": [
                    {
                        "name": "null",
                        "match": "*",
                        "processors": {
                            "metrics": [
                                {"name": "cumulative_to_delta", "max_staleness": "10ms"},
                            ]
                        },
                    }
                ],
            }
        },
        "profile": "strict",
    }

    response = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert response.status_code in (200, 400)
    body = await response.get_json()
    invalid_type_paths = {item["path"] for item in body["errors"] if item["code"] == "invalid_type"}
    assert "$.pipeline.outputs[0].processors.metrics[0].max_staleness" in invalid_type_paths

@pytest.mark.asyncio
async def test_validate_rejects_invalid_size_value_format() -> None:
    """Size-typed fields should reject values that do not match the size pattern."""
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "pipeline": {
                "inputs": [
                    {
                        "name": "tail",
                        "path": "/var/log/test.log",
                        "buffer_chunk_size": "not-a-size",
                        "buffer_max_size": "64K",
                    }
                ],
                "filters": [],
                "outputs": [{"name": "null", "match": "*"}],
            }
        },
        "profile": "strict",
    }

    response = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert response.status_code in (200, 400)
    body = await response.get_json()
    mismatch_paths = {item["path"] for item in body["errors"] if item["code"] == "regex_mismatch"}
    assert "$.pipeline.inputs[0].buffer_chunk_size" in mismatch_paths


def test_duration_rule_rejects_invalid_duration_value_format() -> None:
    """Duration rules should reject values that do not match the compact duration pattern."""
    from config_service.rule_engine.adapters.builtin import ValidationRuleConstraintsAdapter
    from config_service.rule_engine.base import RuleContext

    adapter = ValidationRuleConstraintsAdapter()
    context = RuleContext(
        version="5.0.4",
        config={
            "pipeline": {
                "inputs": [{"name": "nginx_metrics", "scrape_interval": "five-seconds"}],
                "filters": [],
                "outputs": [],
            }
        },
        catalog={
            "plugins": {
                "inputs": {
                    "nginx_metrics": {
                        "fields": [
                            {
                                "name": "scrape_interval",
                                "data_type": "duration",
                                "validation_rule": {"kind": "duration"},
                            }
                        ]
                    }
                },
                "filters": {},
                "outputs": {},
            }
        },
        params={},
    )

    issues = adapter.evaluate(context)

    assert issues
    assert issues[0]["code"] == "regex_mismatch"
    assert issues[0]["path"] == "$.pipeline.inputs[0].scrape_interval"

@pytest.mark.asyncio
async def test_validate_route_output_reference_and_enablement() -> None:
    """Route validation should warn on unknown destinations and disabled routing."""
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "pipeline": {
                "inputs": [
                    {
                        "name": "tcp",
                        "chunk_size": 32,
                        "route": {
                            "per_record_routing": False,
                            "logs": [
                                {
                                    "name": "error_logs",
                                    "condition": {
                                        "op": "and",
                                        "rules": [
                                            {"field": "$level", "op": "eq", "value": "error"}
                                        ],
                                    },
                                    "to": {"outputs": ["missing_destination"]},
                                }
                            ],
                        },
                    }
                ],
                "filters": [],
                "outputs": [{"name": "null", "match": "*", "alias": "known_destination"}],
            }
        },
        "profile": "strict",
    }

    response = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert response.status_code in (200, 400)
    body = await response.get_json()
    assert body["ok"] is True
    codes = {issue["code"] for issue in body["errors"]}
    severities = {issue["code"]: issue["severity"] for issue in body["errors"]}
    assert "unknown_route_output_reference" in codes
    assert "route_not_enabled" in codes
    assert severities["unknown_route_output_reference"] == "warning"
    assert severities["route_not_enabled"] == "warning"

@pytest.mark.asyncio
async def test_validate_rejects_unknown_parser_reference_and_duplicate_parser_name() -> None:
    """Parser validation should warn on missing references and duplicate parser names."""
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "parsers": [
                {
                    "name": "dup_parser",
                    "format": "json",
                },
                {
                    "name": "dup_parser",
                    "format": "regex",
                    "regex": "^(?<msg>.*)$",
                },
            ],
            "pipeline": {
                "inputs": [
                    {
                        "name": "tcp",
                        "chunk_size": 32,
                        "parser": "missing_parser",
                    }
                ],
                "filters": [],
                "outputs": [{"name": "null", "match": "*"}],
            },
        },
        "profile": "strict",
    }

    response = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert response.status_code in (200, 400)
    body = await response.get_json()
    assert body["ok"] is True
    codes = {issue["code"] for issue in body["errors"]}
    assert "duplicate_parser_name" in codes
    assert "unknown_parser_reference" in codes
    severities = {issue["severity"] for issue in body["errors"]}
    assert severities == {"warning"}

@pytest.mark.asyncio
async def test_fluentbit_processors_validate_and_render() -> None:
    """Processor blocks should validate cleanly and appear in rendered YAML/schema output."""
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "pipeline": {
                "inputs": [
                    {
                        "name": "tail",
                        "path": "/var/log/example.log",
                        "processors": {
                            "logs": [
                                {
                                    "name": "content_modifier",
                                    "action": "upsert",
                                    "context": "body",
                                    "key": "environment",
                                    "value": "dev",
                                }
                            ]
                        },
                    }
                ],
                "filters": [],
                "outputs": [
                    {
                        "name": "stdout",
                        "match": "*",
                        "processors": {
                            "logs": [
                                {
                                    "name": "sql",
                                    "query": "SELECT * FROM STREAM;",
                                }
                            ]
                        },
                    }
                ],
            }
        }
    }

    validate_resp = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert validate_resp.status_code in (200, 400)
    validate_body = await validate_resp.get_json()
    assert "errors" in validate_body

    schema_resp = await client.post(
        "/config-service/api/v1/schema/5.0.4?config_type=fluentbit",
        json={"strict": True},
    )
    assert schema_resp.status_code == 200
    schema_body = await schema_resp.get_json()
    config_props = schema_body["schema"]["properties"]["config"]["properties"]
    assert "upstream_servers" in config_props
    upstream_items = config_props["upstream_servers"]["items"]
    assert set(upstream_items["required"]) == {"name", "nodes"}
    upstream_node_items = upstream_items["properties"]["nodes"]["items"]
    assert set(upstream_node_items["required"]) == {"name", "host", "port"}
    input_schema = config_props["pipeline"]["properties"]["inputs"]["items"]
    assert "oneOf" in input_schema

    yaml_resp = await client.post(
        "/config-service/api/v1/render/yaml/5.0.4?config_type=fluentbit",
        json={**payload, "include_comments": False},
    )
    assert yaml_resp.status_code == 200
    yaml_body = await yaml_resp.get_json()
    assert "processors:" in yaml_body["yaml"]
    assert "content_modifier" in yaml_body["yaml"]

@pytest.mark.asyncio
async def test_validate_accepts_valid_upstream_servers() -> None:
    """Well-formed upstream server groups should not produce upstream validation errors."""
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "upstream_servers": [
                {
                    "name": "primary_cluster",
                    "nodes": [
                        {
                            "name": "node_a",
                            "host": "127.0.0.1",
                            "port": 24224,
                            "tls": True,
                            "tls_verify": False,
                            "shared_key": "secret-token",
                        },
                        {
                            "name": "node_b",
                            "host": "127.0.0.2",
                            "port": "${UPSTREAM_PORT}",
                        },
                    ],
                }
            ],
            "pipeline": {
                "inputs": [{"name": "dummy"}],
                "filters": [],
                "outputs": [{"name": "null", "match": "*"}],
            },
        }
    }

    response = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert response.status_code == 200
    body = await response.get_json()
    upstream_errors = [item for item in body["errors"] if "upstream_servers" in item.get("path", "")]
    assert upstream_errors == []

@pytest.mark.asyncio
async def test_validate_reports_invalid_upstream_servers() -> None:
    """Invalid upstream server groups should report duplicate, type, and field issues."""
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "upstream_servers": [
                {
                    "name": "duplicate_group",
                    "nodes": [
                        {
                            "name": "dup_node",
                            "host": "",
                            "port": True,
                            "tls": "yes",
                            "unexpected_node_field": "x",
                        },
                        {
                            "name": "dup_node",
                            "host": "127.0.0.3",
                            "port": 24224,
                        }
                    ],
                    "unexpected_group_field": "x",
                },
                {
                    "name": "duplicate_group",
                    "nodes": [
                        {
                            "name": "dup_node",
                            "host": "127.0.0.1",
                            "port": "${BAD PORT}",
                        }
                    ],
                },
            ],
            "pipeline": {
                "inputs": [{"name": "dummy"}],
                "filters": [],
                "outputs": [{"name": "null", "match": "*"}],
            },
        }
    }

    response = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert response.status_code in (200, 400)
    body = await response.get_json()
    codes = {item["code"] for item in body["errors"] if "upstream_servers" in item.get("path", "")}
    assert "duplicate_upstream_group_name" in codes
    assert "duplicate_upstream_node_name" in codes
    assert "missing_required_field" in codes
    assert "invalid_type" in codes
    assert "unknown_field" in codes

@pytest.mark.asyncio
async def test_validate_requires_match_or_match_regex_when_both_fields_exist() -> None:
    """Outputs should require at least one selector when match fields are supported."""
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "pipeline": {
                "inputs": [{"name": "dummy"}],
                "filters": [],
                "outputs": [{"name": "null"}],
            }
        }
    }

    resp = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert resp.status_code in (200, 400)
    body = await resp.get_json()
    assert "errors" in body
    selector_errors = [item for item in body["errors"] if item["code"] == "missing_match_selector"]
    assert selector_errors
    assert selector_errors[0]["path"] == "$.config.pipeline.outputs[0]"

@pytest.mark.asyncio
async def test_validate_accepts_match_or_match_regex_when_either_is_present() -> None:
    """Providing either `match` or `match_regex` should satisfy selector validation."""
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "pipeline": {
                "inputs": [{"name": "dummy"}],
                "filters": [{"name": "grep", "regex": "message error", "match_regex": "^app\\."}],
                "outputs": [{"name": "null", "match": "*"}],
            }
        }
    }

    resp = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert resp.status_code in (200, 400)
    body = await resp.get_json()
    assert "errors" in body
    assert not [item for item in body["errors"] if item["code"] == "missing_match_selector"]

@pytest.mark.asyncio
async def test_lua_code_validation_returns_normalized_errors() -> None:
    """Lua syntax failures should be normalized into API-friendly validation errors."""
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "pipeline": {
                "inputs": [{"name": "forward", "port": 24224}],
                "filters": [
                    {
                        "name": "lua",
                        "call": "cb_filter",
                        "code": "function cb_filter(tag, timestamp, record) return 0, timestamp, record",
                    }
                ],
                "outputs": [{"name": "stdout"}],
            }
        }
    }

    resp = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert resp.status_code in (200, 400)
    body = await resp.get_json()
    assert "errors" in body
    lua_errors = [
        item
        for item in body["errors"]
        if item["code"] in {"lua_syntax_error", "lua_parser_unavailable"}
    ]
    assert lua_errors
    assert lua_errors[0]["path"] == "$.config.pipeline.filters[0].code"
    assert "Lua" in lua_errors[0]["message"]

@pytest.mark.asyncio
async def test_sql_code_validation_returns_normalized_errors() -> None:
    """SQL syntax failures should be normalized into API-friendly validation errors."""
    app = create_app(mode="standalone")
    client = app.test_client()

    payload = {
        "config": {
            "pipeline": {
                "inputs": [
                    {
                        "name": "dummy",
                        "dummy": '{"http.url": "https://fluentbit.io"}',
                        "processors": {
                            "logs": [
                                {
                                    "name": "sql",
                                    "query": "SELECT FROM STREAM;",
                                }
                            ]
                        },
                    }
                ],
                "filters": [],
                "outputs": [{"name": "stdout"}],
            }
        }
    }

    resp = await client.post(
        "/config-service/api/v1/validate/5.0.4?config_type=fluentbit",
        json=payload,
    )
    assert resp.status_code in (200, 400)
    body = await resp.get_json()
    assert "errors" in body
    sql_errors = [item for item in body["errors"] if item["code"] == "sql_syntax_error"]
    assert sql_errors
    assert sql_errors[0]["path"] == "$.config.pipeline.inputs[0].processors.logs[0].query"
    assert "SQL syntax error" in sql_errors[0]["message"]

def test_lua_code_adapter_uses_context_for_code_type_without_language_rule() -> None:
    """Lua adapter should infer code validation from field data type when rules omit language."""
    from config_service.rule_engine.adapters.lua_code import LuaCodeSyntaxAdapter
    from config_service.rule_engine.base import RuleContext

    adapter = LuaCodeSyntaxAdapter()
    context = RuleContext(
        version="5.0.4",
        config={
            "pipeline": {
                "inputs": [],
                "filters": [
                    {
                        "name": "lua",
                        "code": "function cb_filter(",
                    }
                ],
                "outputs": [],
            }
        },
        catalog={
            "plugins": {
                "inputs": {},
                "filters": {
                    "lua": {
                        "fields": [
                            {
                                "name": "code",
                                "data_type": "code",
                                "required": False,
                            }
                        ]
                    }
                },
                "outputs": {},
            }
        },
        params={},
    )

    issues = adapter.evaluate(context)
    assert issues
    assert issues[0]["path"] == "$.config.pipeline.filters[0].code"
    assert issues[0]["code"] in {"lua_syntax_error", "lua_parser_unavailable"}

def test_sql_code_adapter_uses_context_for_code_type_without_language_rule() -> None:
    """SQL adapter should infer code validation from processor field data type metadata."""
    from config_service.rule_engine.adapters.sql_code import SqlCodeSyntaxAdapter
    from config_service.rule_engine.base import RuleContext

    adapter = SqlCodeSyntaxAdapter()
    context = RuleContext(
        version="5.0.4",
        config={
            "pipeline": {
                "inputs": [],
                "filters": [],
                "outputs": [
                    {
                        "name": "null",
                        "processors": {
                            "logs": [
                                {
                                    "name": "sql",
                                    "query": "SELECT FROM STREAM;",
                                }
                            ]
                        },
                    }
                ],
            }
        },
        catalog={
            "plugins": {
                "inputs": {},
                "filters": {},
                "outputs": {"null": {"fields": []}},
            },
            "common": {
                "processors": {
                    "signals": {
                        "logs": {
                            "processors": {
                                "sql": {
                                    "fields": [
                                        {
                                            "name": "query",
                                            "data_type": "code",
                                            "required": False,
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            },
        },
        params={},
    )

    issues = adapter.evaluate(context)
    assert issues
    assert issues[0]["path"] == "$.config.pipeline.outputs[0].processors.logs[0].query"
    assert issues[0]["code"] in {"sql_syntax_error", "sql_parser_unavailable"}


def test_builtin_data_type_adapter_logs_unhappy_path(caplog: pytest.LogCaptureFixture) -> None:
    """Builtin adapter should log and exit cleanly when pipeline structure is invalid."""
    from config_service.rule_engine.adapters.builtin import DataTypeEnforcementAdapter
    from config_service.rule_engine.base import RuleContext

    adapter = DataTypeEnforcementAdapter()
    caplog.set_level("INFO")

    issues = adapter.evaluate(
        RuleContext(
            version="5.0.4",
            config={"pipeline": []},
            catalog={"plugins": {}, "common": {"processors": {"signals": {}}}},
            params={},
        )
    )

    assert issues == []
    assert "starting data type enforcement evaluation" in caplog.text
    assert "pipeline payload is not a dict" in caplog.text


def test_lua_code_adapter_logs_unhappy_path(caplog: pytest.LogCaptureFixture) -> None:
    """Lua adapter should log parser failures along its unhappy validation path."""
    from config_service.rule_engine.adapters.lua_code import LuaCodeSyntaxAdapter
    from config_service.rule_engine.base import RuleContext

    adapter = LuaCodeSyntaxAdapter()
    caplog.set_level("INFO")

    issues = adapter.evaluate(
        RuleContext(
            version="5.0.4",
            config={
                "pipeline": {
                    "inputs": [],
                    "filters": [{"name": "lua", "code": "function cb_filter("}],
                    "outputs": [],
                }
            },
            catalog={
                "plugins": {
                    "inputs": {},
                    "filters": {
                        "lua": {
                            "fields": [{"name": "code", "data_type": "code"}],
                        }
                    },
                    "outputs": {},
                }
            },
            params={},
        )
    )

    assert issues
    assert "starting Lua code syntax evaluation" in caplog.text
    assert (
        "Lua syntax validation failed" in caplog.text
        or "Lua validation parser unavailable" in caplog.text
    )


def test_sql_code_adapter_logs_unhappy_path(caplog: pytest.LogCaptureFixture) -> None:
    """SQL adapter should log parser failures along its unhappy validation path."""
    from config_service.rule_engine.adapters.sql_code import SqlCodeSyntaxAdapter
    from config_service.rule_engine.base import RuleContext

    adapter = SqlCodeSyntaxAdapter()
    caplog.set_level("INFO")

    issues = adapter.evaluate(
        RuleContext(
            version="5.0.4",
            config={
                "pipeline": {
                    "inputs": [],
                    "filters": [],
                    "outputs": [
                        {
                            "name": "null",
                            "processors": {
                                "logs": [{"name": "sql", "query": "SELECT FROM STREAM;"}]
                            },
                        }
                    ],
                }
            },
            catalog={
                "plugins": {"inputs": {}, "filters": {}, "outputs": {"null": {"fields": []}}},
                "common": {
                    "processors": {
                        "signals": {
                            "logs": {
                                "processors": {
                                    "sql": {
                                        "fields": [{"name": "query", "data_type": "code"}]
                                    }
                                }
                            }
                        }
                    }
                },
            },
            params={},
        )
    )

    assert issues
    assert "starting SQL code syntax evaluation" in caplog.text
    assert (
        "SQL syntax validation failed" in caplog.text
        or "SQL validation parser unavailable" in caplog.text
    )
