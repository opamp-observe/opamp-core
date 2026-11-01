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

from config_service.rule_engine.adapters.builtin import (
    BUILTIN_ADAPTERS,
    CatalogRequiredFieldsAdapter,
    DataTypeEnforcementAdapter,
    DependencyConstraintsAdapter,
    ValidationRuleConstraintsAdapter,
)
from config_service.rule_engine.registry import RuleAdapterRegistry


def test_builtin_registry_resolves_split_adapter_modules() -> None:
    """Keep the public built-in adapter registry stable across internal splits."""

    registry = RuleAdapterRegistry()

    assert registry.resolve("builtin.catalog_required_fields") is CatalogRequiredFieldsAdapter
    assert registry.resolve("builtin.data_type_enforcement") is DataTypeEnforcementAdapter
    assert registry.resolve("builtin.dependency_constraints") is DependencyConstraintsAdapter
    assert registry.resolve("builtin.validation_rule_constraints") is ValidationRuleConstraintsAdapter
    assert BUILTIN_ADAPTERS == {
        "builtin.catalog_required_fields": CatalogRequiredFieldsAdapter,
        "builtin.data_type_enforcement": DataTypeEnforcementAdapter,
        "builtin.dependency_constraints": DependencyConstraintsAdapter,
        "builtin.validation_rule_constraints": ValidationRuleConstraintsAdapter,
    }
