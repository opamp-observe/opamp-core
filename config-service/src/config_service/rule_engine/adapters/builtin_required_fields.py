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

"""Built-in adapter that enforces catalog-declared required fields.

This adapter is the simplest catalog mirror. It walks configured pipeline
plugins, looks up their catalog definitions, and emits rule-engine issues for
any field the catalog marks as required but the plugin payload omits.
"""

from __future__ import annotations

import logging
from typing import Any

from config_service.rule_engine.base import RuleAdapter, RuleContext
from config_service.rule_engine.adapters.builtin_shared import (
    KEY_FIELDS,
    KEY_NAME,
    KEY_REQUIRED,
    PIPELINE_PATH_PREFIX,
    build_issue,
    catalog_plugin_definition,
    iter_pipeline_plugins,
)

LOGGER = logging.getLogger(__name__)


class CatalogRequiredFieldsAdapter(RuleAdapter):
    """Report plugin instances that omit catalog-mandated fields.

    Use this adapter when a ruleset should treat the plugin catalog as the
    source of truth for which fields must be present in a saved configuration.
    """

    def evaluate(self, context: RuleContext) -> list[dict[str, Any]]:
        """Mirror required-field metadata from the catalog into validation issues."""

        LOGGER.info("starting catalog required fields evaluation version=%s", context.version)
        issues: list[dict[str, Any]] = []
        for section, idx, plugin_instance in iter_pipeline_plugins(context.config):
            plugin_name = str(plugin_instance.get(KEY_NAME, ""))
            plugin_def = catalog_plugin_definition(context.catalog, section, plugin_name)
            if not plugin_def:
                continue

            required_fields = [
                field[KEY_NAME]
                for field in plugin_def.get(KEY_FIELDS, [])
                if isinstance(field, dict) and field.get(KEY_REQUIRED) is True and KEY_NAME in field
            ]
            for field_name in required_fields:
                if field_name not in plugin_instance:
                    LOGGER.warning(
                        "required field missing section=%s index=%s plugin=%s field=%s",
                        section,
                        idx,
                        plugin_name,
                        field_name,
                    )
                    issues.append(
                        build_issue(
                            "missing_required_field",
                            f"{PIPELINE_PATH_PREFIX}.{section}[{idx}].{field_name}",
                            f"Required field '{field_name}' is missing for plugin '{plugin_name}'.",
                        )
                    )

        LOGGER.info(
            "completed catalog required fields evaluation version=%s issue_count=%s",
            context.version,
            len(issues),
        )
        return issues
