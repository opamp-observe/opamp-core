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

from config_service.services.schema_service import SchemaService


def test_field_schema_uses_enum_options_when_enum_rule_omits_values() -> None:
    """Enum rules may inherit allowed values from the parent field metadata."""

    service = SchemaService()

    schema = service._field_schema(
        {
            "name": "log_level",
            "data_type": "enum",
            "description": "Allowed log level.",
            "reference": "https://example.invalid/log-level",
            "enum_options": ["off", "info", "debug"],
            "validation_rule": {"kind": "enum"},
        }
    )

    assert schema["enum"] == ["off", "info", "debug"]


def test_field_schema_prefers_validation_rule_enum_values_when_present() -> None:
    """Explicit enum rule values should override the parent enum option list."""

    service = SchemaService()

    schema = service._field_schema(
        {
            "name": "log_level",
            "data_type": "enum",
            "description": "Allowed log level.",
            "reference": "https://example.invalid/log-level",
            "enum_options": ["off", "info", "debug"],
            "validation_rule": {"kind": "enum", "values": ["warn", "error"]},
        }
    )

    assert schema["enum"] == ["warn", "error"]
