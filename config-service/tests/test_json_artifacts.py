#!/usr/bin/env python3
# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config_service.json_artifacts import (
    JsonArtifactError,
    load_json_artifact,
    load_json_schema_artifact,
    write_manifest_json_artifact,
    write_split_json_artifact,
)


def test_write_split_json_artifact_round_trips_payload(tmp_path: Path) -> None:
    payload = {
        "plugins": {
            "inputs": {"tail": {"title": "Tail"}},
            "filters": {"grep": {"title": "Grep"}},
            "outputs": {"stdout": {"title": "Stdout"}},
        },
        "engine": "fluentbit",
    }
    artifact_path = tmp_path / "catalog.json"

    write_split_json_artifact(
        artifact_path,
        payload,
        split_parts=[
            ("/plugins/inputs", "inputs"),
            ("/plugins/outputs", "outputs"),
        ],
    )

    manifest_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert "artifact_manifest" in manifest_payload
    assert (tmp_path / "catalog.base.json").exists()
    assert (tmp_path / "catalog.inputs.json").exists()
    assert (tmp_path / "catalog.outputs.json").exists()
    assert load_json_artifact(artifact_path) == payload


def test_load_json_artifact_rejects_unknown_manifest_format(tmp_path: Path) -> None:
    artifact_path = tmp_path / "schema.json"
    artifact_path.write_text(
        json.dumps(
            {
                "artifact_manifest": {
                    "format": "unknown",
                    "base": "schema.base.json",
                    "parts": [],
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "schema.base.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(JsonArtifactError):
        load_json_artifact(artifact_path)


def test_load_json_artifact_reports_path_and_parse_location_for_invalid_json(tmp_path: Path) -> None:
    artifact_path = tmp_path / "broken.json"
    artifact_path.write_text('{"title": "broken",\n', encoding="utf-8")

    with pytest.raises(JsonArtifactError) as exc_info:
        load_json_artifact(artifact_path)

    message = str(exc_info.value)
    assert str(artifact_path) in message
    assert "line 2 column 1" in message


def test_write_manifest_json_artifact_supports_nested_files_and_array_appends(tmp_path: Path) -> None:
    artifact_path = tmp_path / "schema.json"

    write_manifest_json_artifact(
        artifact_path,
        base_file="fluentbit/3.2.10/schema.base.json",
        base_payload={
            "properties": {
                "inputs": {
                    "items": {
                        "oneOf": [],
                    }
                }
            }
        },
        parts=[
            {
                "pointer": "/properties/inputs",
                "file": "fluentbit/3.2.10/inputs.json",
                "payload": {
                    "artifact_manifest": {
                        "format": "config-service.composite-json/v1",
                        "base": "inputs.base.json",
                        "parts": [
                            {
                                "pointer": "/items/oneOf",
                                "operation": "append",
                                "file": "inputs/tail.json",
                            },
                            {
                                "pointer": "/items/oneOf",
                                "operation": "append",
                                "file": "inputs/cpu.json",
                            },
                        ],
                    }
                },
            }
        ],
    )
    (tmp_path / "fluentbit" / "3.2.10" / "inputs.base.json").write_text(
        json.dumps({"items": {"oneOf": []}}) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "fluentbit" / "3.2.10" / "inputs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "fluentbit" / "3.2.10" / "inputs" / "tail.json").write_text(
        json.dumps({"properties": {"name": {"const": "tail"}}}) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "fluentbit" / "3.2.10" / "inputs" / "cpu.json").write_text(
        json.dumps({"properties": {"name": {"const": "cpu"}}}) + "\n",
        encoding="utf-8",
    )

    payload = load_json_artifact(artifact_path)
    variants = payload["properties"]["inputs"]["items"]["oneOf"]
    assert [variant["properties"]["name"]["const"] for variant in variants] == ["tail", "cpu"]


def test_load_json_schema_artifact_resolves_file_refs_relative_to_plugin_shard(tmp_path: Path) -> None:
    plugin_path = tmp_path / "fluentbit" / "3.2.10" / "inputs" / "tail.json"
    plugin_path.parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "fluentbit" / "3.2.10" / "processors.json").write_text(
        json.dumps({"type": "object", "properties": {"logs": {"type": "array"}}}) + "\n",
        encoding="utf-8",
    )
    plugin_path.write_text(
        json.dumps(
            {
                "type": "object",
                "properties": {
                    "name": {"const": "tail"},
                    "processors": {"$ref": "../processors.json"},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = load_json_schema_artifact(plugin_path)
    assert payload["properties"]["processors"]["type"] == "object"
    assert "logs" in payload["properties"]["processors"]["properties"]
