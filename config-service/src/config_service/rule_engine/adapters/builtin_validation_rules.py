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

"""Built-in adapter that interprets inline catalog validation rules.

This adapter handles rule metadata that is richer than a plain runtime type,
such as numeric ranges, regex requirements, canonical duration strings, Fluent
Bit size values, and explicit boolean-only constraints.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from config_service.rule_engine.base import RuleAdapter, RuleContext
from config_service.rule_engine.adapters.builtin_shared import (
    DURATION_VALUE_PATTERN,
    KEY_FIELDS,
    KEY_KIND,
    KEY_MAX,
    KEY_MIN,
    KEY_NAME,
    KEY_PATTERN,
    KEY_VALIDATION_RULE,
    PIPELINE_PATH_PREFIX,
    RULE_KIND_BOOLEAN,
    RULE_KIND_DURATION,
    RULE_KIND_RANGE,
    RULE_KIND_REGEX,
    RULE_KIND_REGEX_STRING,
    RULE_KIND_SIZE,
    SIZE_VALUE_PATTERN,
    build_issue,
    catalog_plugin_definition,
    iter_pipeline_plugins,
)

LOGGER = logging.getLogger(__name__)


class ValidationRuleConstraintsAdapter(RuleAdapter):
    """Apply inline `validation_rule` metadata declared on catalog fields.

    Use this adapter when field definitions need semantic constraints beyond
    simple type checks, for example numeric bounds or a required regex pattern.
    """

    def evaluate(self, context: RuleContext) -> list[dict[str, Any]]:
        """Apply rule-level constraints declared in catalog field metadata.

        High-complexity flow notes:
        - Iterate only known plugin fields so unknown keys are handled elsewhere.
        - Dispatch by `validation_rule.kind` to targeted validation branches.
        - Each branch emits normalized, path-aware rule issues.

        Important enum note:
        - This adapter does not currently implement a dedicated `kind == "enum"`
          branch.
        - Enum-like constraints are typically enforced either by generated JSON
          Schema `enum` metadata from `enum_options`, or by catalog
          metadata that translates enum-like upstream docs into a
          `regex_string` validation rule.

        Type mismatch note:
        - When a rule-specific check receives an incompatible runtime type, this
          adapter logs the mismatch and skips that branch instead of raising.
        - The companion data-type adapter is responsible for emitting the
          user-facing `invalid_type` issues for those payloads.
        """

        LOGGER.info("starting validation rule constraints evaluation version=%s", context.version)
        issues: list[dict[str, Any]] = []
        for section, idx, plugin_instance in iter_pipeline_plugins(context.config):
            plugin_name = str(plugin_instance.get(KEY_NAME, ""))
            plugin_def = catalog_plugin_definition(context.catalog, section, plugin_name)
            if not plugin_def:
                continue

            fields_by_name = {
                field[KEY_NAME]: field
                for field in plugin_def.get(KEY_FIELDS, [])
                if isinstance(field, dict) and KEY_NAME in field
            }

            # Evaluate constraints only for declared fields present in payload.
            for key, value in plugin_instance.items():
                if key == KEY_NAME or key not in fields_by_name:
                    continue

                rule = fields_by_name[key].get(KEY_VALIDATION_RULE)
                if not isinstance(rule, dict):
                    continue

                kind = rule.get(KEY_KIND)
                path = f"{PIPELINE_PATH_PREFIX}.{section}[{idx}].{key}"

                # Numeric bounds check branch.
                if kind == RULE_KIND_RANGE and isinstance(value, (int, float)) and not isinstance(value, bool):
                    min_val = rule.get(KEY_MIN)
                    max_val = rule.get(KEY_MAX)
                    if min_val is not None and value < min_val:
                        LOGGER.warning("range minimum violation path=%s min=%s value=%s", path, min_val, value)
                        issues.append(build_issue("range_min", path, f"Value for '{key}' must be >= {min_val}."))
                    if max_val is not None and value > max_val:
                        LOGGER.warning("range maximum violation path=%s max=%s value=%s", path, max_val, value)
                        issues.append(build_issue("range_max", path, f"Value for '{key}' must be <= {max_val}."))
                elif kind == RULE_KIND_RANGE:
                    LOGGER.warning(
                        "range rule skipped incompatible value type path=%s actual_type=%s",
                        path,
                        type(value).__name__,
                    )

                # Regex pattern compliance branch.
                elif kind in {RULE_KIND_REGEX, RULE_KIND_REGEX_STRING}:
                    if isinstance(value, str):
                        pattern = rule.get(KEY_PATTERN)
                        if pattern and re.fullmatch(pattern, value) is None:
                            LOGGER.warning("regex mismatch path=%s pattern=%s", path, pattern)
                            issues.append(
                                build_issue("regex_mismatch", path, f"Value for '{key}' does not match required pattern.")
                            )
                    else:
                        LOGGER.warning(
                            "regex rule skipped incompatible value type path=%s actual_type=%s",
                            path,
                            type(value).__name__,
                        )

                # Canonical duration-value branch using compact time suffixes.
                elif kind == RULE_KIND_DURATION:
                    if isinstance(value, str):
                        if DURATION_VALUE_PATTERN.fullmatch(value) is None:
                            LOGGER.warning("duration mismatch path=%s value=%s", path, value)
                            issues.append(
                                build_issue(
                                    "regex_mismatch",
                                    path,
                                    f"Value for '{key}' must be a valid duration.",
                                )
                            )
                    else:
                        LOGGER.warning(
                            "duration rule skipped incompatible value type path=%s actual_type=%s",
                            path,
                            type(value).__name__,
                        )

                # Canonical size-value branch using Fluent Bit unit-size syntax:
                # https://docs.fluentbit.io/manual/administration/configuring-fluent-bit#unit-sizes
                elif kind == RULE_KIND_SIZE:
                    if isinstance(value, str):
                        if SIZE_VALUE_PATTERN.fullmatch(value) is None:
                            LOGGER.warning("size mismatch path=%s value=%s", path, value)
                            issues.append(build_issue("regex_mismatch", path, f"Value for '{key}' must be a valid size."))
                    elif not isinstance(value, int) or isinstance(value, bool):
                        LOGGER.warning(
                            "size rule skipped incompatible value type path=%s actual_type=%s",
                            path,
                            type(value).__name__,
                        )

                # Explicit boolean-only branch.
                elif kind == RULE_KIND_BOOLEAN and not isinstance(value, bool):
                    LOGGER.warning("boolean constraint violation path=%s actual_type=%s", path, type(value).__name__)
                    issues.append(build_issue("invalid_boolean", path, f"Value for '{key}' must be boolean."))

        LOGGER.info(
            "completed validation rule constraints evaluation version=%s issue_count=%s",
            context.version,
            len(issues),
        )
        return issues
