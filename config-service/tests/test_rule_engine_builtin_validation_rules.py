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

import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config_service.rule_engine.adapters.builtin import ValidationRuleConstraintsAdapter
from config_service.rule_engine.base import RuleContext


def test_validation_rule_adapter_logs_incompatible_runtime_types(caplog: pytest.LogCaptureFixture) -> None:
    """Rule checks should skip incompatible value types cleanly and log why."""

    adapter = ValidationRuleConstraintsAdapter()
    caplog.set_level(logging.INFO)

    issues = adapter.evaluate(
        RuleContext(
            version="5.0.4",
            config={
                "pipeline": {
                    "inputs": [
                        {
                            "name": "demo",
                            "retry_limit": "not-a-number",
                            "selector": ["not-a-string"],
                            "scrape_interval": 5,
                            "buffer_size": {"unexpected": "object"},
                        }
                    ],
                    "filters": [],
                    "outputs": [],
                }
            },
            catalog={
                "plugins": {
                    "inputs": {
                        "demo": {
                            "fields": [
                                {
                                    "name": "retry_limit",
                                    "data_type": "integer",
                                    "validation_rule": {"kind": "range", "min": 0, "max": 10},
                                },
                                {
                                    "name": "selector",
                                    "data_type": "string",
                                    "validation_rule": {"kind": "regex_string", "pattern": "^ok$"},
                                },
                                {
                                    "name": "scrape_interval",
                                    "data_type": "duration",
                                    "validation_rule": {"kind": "duration"},
                                },
                                {
                                    "name": "buffer_size",
                                    "data_type": "size",
                                    "validation_rule": {"kind": "size"},
                                },
                            ]
                        }
                    },
                    "filters": {},
                    "outputs": {},
                }
            },
            params={},
        )
    )

    assert issues == []
    assert "range rule skipped incompatible value type" in caplog.text
    assert "regex rule skipped incompatible value type" in caplog.text
    assert "duration rule skipped incompatible value type" in caplog.text
    assert "size rule skipped incompatible value type" in caplog.text


def test_validation_rule_adapter_logs_and_reports_invalid_boolean_constraint(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Boolean validation should emit an issue and log the incorrect runtime type."""

    adapter = ValidationRuleConstraintsAdapter()
    caplog.set_level(logging.INFO)

    issues = adapter.evaluate(
        RuleContext(
            version="5.0.4",
            config={
                "pipeline": {
                    "inputs": [{"name": "demo", "enabled": "yes"}],
                    "filters": [],
                    "outputs": [],
                }
            },
            catalog={
                "plugins": {
                    "inputs": {
                        "demo": {
                            "fields": [
                                {
                                    "name": "enabled",
                                    "data_type": "boolean",
                                    "validation_rule": {"kind": "boolean"},
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
    )

    assert issues == [
        {
            "code": "invalid_boolean",
            "path": "$.pipeline.inputs[0].enabled",
            "message": "Value for 'enabled' must be boolean.",
            "severity": "error",
            "source": "rules",
        }
    ]
    assert "boolean constraint violation" in caplog.text
