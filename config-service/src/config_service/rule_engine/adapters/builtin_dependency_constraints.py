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

"""Built-in adapter placeholder for future dependency-based validation rules.

This module intentionally stays small. It preserves the adapter contract and
documents the future role for cross-field and cross-plugin dependency checks
without mixing placeholder behavior into the more active adapters.
"""

from __future__ import annotations

import logging
from typing import Any

from config_service.rule_engine.base import RuleAdapter, RuleContext

LOGGER = logging.getLogger(__name__)


class DependencyConstraintsAdapter(RuleAdapter):
    """Reserved adapter for future catalog dependency and implication rules.

    Use this adapter name in rule registries when you want a stable placeholder
    today and a natural expansion point later for dependency-aware validation.
    """

    def evaluate(self, context: RuleContext) -> list[dict[str, Any]]:
        """Return no issues until cross-field dependency validation is implemented."""

        LOGGER.info("dependency constraints evaluation not yet implemented version=%s", context.version)
        return []
