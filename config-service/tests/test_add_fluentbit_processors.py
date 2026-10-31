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

import importlib.util
import json
import logging
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config_service.fluentbit_docs_support import PluginNameResolution
from config_service.json_artifacts import load_json_artifact


def _load_module():
    path = Path(__file__).resolve().parents[1] / "dev-tools" / "add_fluentbit_processors.py"
    spec = importlib.util.spec_from_file_location("add_fluentbit_processors", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _logger() -> logging.Logger:
    logger = logging.getLogger("test_add_fluentbit_processors")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.INFO)
    return logger


def test_update_catalog_normalizes_unique_plugin_names(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    catalog_path = tmp_path / "fluent-bit-5.0.4-all-plugins-catalog.json"
    payload = {
        "engine": "fluentbit",
        "fluent_bit_version": "5.0.4",
        "custom_plugins": [],
        "plugins": {
            "inputs": {
                "standard-input": {
                    "title": "Standard Input",
                    "doc_url": "https://example.test/stdin",
                    "fields": [],
                }
            },
            "filters": {},
            "outputs": {},
        },
    }
    _write_json(catalog_path, payload)

    def _normalize(section_plugins, section, **kwargs):
        if section == "inputs":
            return (
                {
                    "stdin": {
                        "title": "Standard Input",
                        "doc_url": "https://example.test/stdin",
                        "fields": [],
                    }
                },
                [
                    PluginNameResolution(
                        current_name="standard-input",
                        expected_name="stdin",
                        evidence="[INPUT] Name",
                        doc_url="https://example.test/stdin",
                    )
                ],
                {},
            )
        return dict(section_plugins), [], {}

    monkeypatch.setattr(module, "normalize_plugin_map", _normalize)

    module.update_catalog(catalog_path, logger=_logger(), page_cache={}, timeout=1)

    assembled = load_json_artifact(catalog_path)
    assert "stdin" in assembled["plugins"]["inputs"]
    assert "standard-input" not in assembled["plugins"]["inputs"]
    manifest = json.loads(catalog_path.read_text(encoding="utf-8"))
    section_parts = manifest["artifact_manifest"]["parts"]
    assert any(part["file"] == "fluent-bit/5.0.4/inputs.json" for part in section_parts)
    nested_manifest = json.loads((catalog_path.parent / "fluent-bit" / "5.0.4" / "inputs.json").read_text(encoding="utf-8"))
    assert nested_manifest["artifact_manifest"]["parts"][0]["pointer"] == "/stdin"
    assert nested_manifest["artifact_manifest"]["parts"][0]["file"] == "inputs/stdin.json"
