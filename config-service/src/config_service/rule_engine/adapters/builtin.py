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

"""Compatibility exports for the built-in rule-engine adapters.

The built-in adapter set used to live in one larger module. The concrete
implementations now live in smaller single-purpose modules, while this module
keeps the established import path and adapter registry stable.
"""

from __future__ import annotations

from config_service.rule_engine.base import RuleAdapter
from config_service.rule_engine.adapters.builtin_data_types import DataTypeEnforcementAdapter
from config_service.rule_engine.adapters.builtin_dependency_constraints import DependencyConstraintsAdapter
from config_service.rule_engine.adapters.builtin_required_fields import CatalogRequiredFieldsAdapter
from config_service.rule_engine.adapters.builtin_validation_rules import ValidationRuleConstraintsAdapter

BUILTIN_ADAPTERS: dict[str, type[RuleAdapter]] = {
    "builtin.catalog_required_fields": CatalogRequiredFieldsAdapter,
    "builtin.data_type_enforcement": DataTypeEnforcementAdapter,
    "builtin.dependency_constraints": DependencyConstraintsAdapter,
    "builtin.validation_rule_constraints": ValidationRuleConstraintsAdapter,
}

__all__ = [
    "BUILTIN_ADAPTERS",
    "CatalogRequiredFieldsAdapter",
    "DataTypeEnforcementAdapter",
    "DependencyConstraintsAdapter",
    "ValidationRuleConstraintsAdapter",
]
