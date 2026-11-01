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

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config_service.rule_engine.adapters.builtin import DataTypeEnforcementAdapter
from config_service.rule_engine.base import RuleContext


def test_data_type_enforcement_accepts_integer_size_fields() -> None:
    """Fluent Bit size fields may be authored as raw integer values."""

    adapter = DataTypeEnforcementAdapter()
    context = RuleContext(
        version="5.0.4",
        config={
            "pipeline": {
                "inputs": [
                    {
                        "name": "forward",
                        "buffer_chunk_size": 1024,
                        "buffer_max_size": 2048,
                    }
                ],
                "filters": [],
                "outputs": [],
            }
        },
        catalog={
            "plugins": {
                "inputs": {
                    "forward": {
                        "fields": [
                            {"name": "buffer_chunk_size", "data_type": "size"},
                            {"name": "buffer_max_size", "data_type": "size"},
                        ]
                    }
                },
                "filters": {},
                "outputs": {},
            },
            "common": {"processors": {"signals": {}}},
        },
        params={},
    )

    assert adapter.evaluate(context) == []
