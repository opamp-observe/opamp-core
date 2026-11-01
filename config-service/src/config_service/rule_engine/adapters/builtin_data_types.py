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

"""Built-in adapter that enforces catalog-declared runtime data types.

This adapter checks both top-level plugin fields and nested Fluent Bit
processor fields. Its job is to catch obvious shape/type mismatches before the
configuration reaches downstream rendering or runtime execution.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from config_service.rule_engine.base import RuleAdapter, RuleContext
from config_service.rule_engine.adapters.builtin_shared import (
    DATA_TYPE_ARRAY,
    DATA_TYPE_BOOLEAN,
    DATA_TYPE_DURATION,
    DATA_TYPE_FLOAT,
    DATA_TYPE_INTEGER,
    DATA_TYPE_LIST,
    DATA_TYPE_MAP,
    DATA_TYPE_NUMBER,
    DATA_TYPE_OBJECT,
    DATA_TYPE_SIZE,
    DATA_TYPE_STRING,
    DATA_TYPE_TIME,
    KEY_COMMON,
    KEY_DATA_TYPE,
    KEY_FIELDS,
    KEY_FILTERS,
    KEY_INPUTS,
    KEY_NAME,
    KEY_OUTPUTS,
    KEY_PLUGINS,
    KEY_PROCESSORS,
    KEY_SIGNALS,
    KEY_ALLOW_FILTERS_AS_PROCESSORS,
    PIPELINE_PATH_PREFIX,
    SIGNAL_LOGS,
    build_issue,
    catalog_plugin_definition,
    iter_pipeline_plugins,
)

LOGGER = logging.getLogger(__name__)


class DataTypeEnforcementAdapter(RuleAdapter):
    """Validate payload values against the Python types implied by catalog metadata.

    Use this adapter to catch invalid scalar/object/list values early, including
    nested Fluent Bit processor settings that inherit their own catalog field
    definitions from shared processor metadata.
    """

    _ENV_VAR_PATTERN = re.compile(r"^\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)\}$")
    _TIME_VALUE_PATTERN = re.compile(r"^\d+[smhdSMHD]?$")

    TYPE_MAP = {
        DATA_TYPE_STRING: str,
        "code": str,
        DATA_TYPE_INTEGER: int,
        DATA_TYPE_BOOLEAN: bool,
        DATA_TYPE_FLOAT: (int, float),
        DATA_TYPE_NUMBER: (int, float),
        DATA_TYPE_DURATION: str,
        # Fluent Bit size fields are commonly authored as either raw integers
        # or compact literals such as 64K / 10M in existing payloads/tests.
        DATA_TYPE_SIZE: (int, str),
        DATA_TYPE_ARRAY: list,
        DATA_TYPE_LIST: list,
        DATA_TYPE_OBJECT: dict,
        DATA_TYPE_MAP: dict,
    }

    @classmethod
    def _is_numeric_env_var(cls, value: Any) -> bool:
        """Return `True` for runtime-expanded numeric placeholders like `${PORT}`."""

        return isinstance(value, str) and bool(cls._ENV_VAR_PATTERN.fullmatch(value))

    @classmethod
    def _is_valid_time_value(cls, value: Any) -> bool:
        """Accept non-negative integers or compact time strings such as `10s`."""

        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return value >= 0
        if isinstance(value, str):
            return bool(cls._TIME_VALUE_PATTERN.fullmatch(value))
        return False

    def evaluate(self, context: RuleContext) -> list[dict[str, Any]]:
        """Validate plugin payloads and nested processors against catalog data types."""

        LOGGER.info("starting data type enforcement evaluation version=%s", context.version)
        issues: list[dict[str, Any]] = []
        common_processors = context.catalog.get(KEY_COMMON, {}).get(KEY_PROCESSORS, {})
        processor_signals = common_processors.get(KEY_SIGNALS, {})
        filter_plugins = context.catalog.get(KEY_PLUGINS, {}).get(KEY_FILTERS, {})

        for section, idx, plugin_instance in iter_pipeline_plugins(context.config):
            plugin_name = str(plugin_instance.get(KEY_NAME, ""))
            plugin_def = catalog_plugin_definition(context.catalog, section, plugin_name)
            if not plugin_def:
                continue

            issues.extend(
                self._validate_payload_types(
                    payload=plugin_instance,
                    field_defs=plugin_def.get(KEY_FIELDS, []),
                    path_prefix=f"{PIPELINE_PATH_PREFIX}.{section}[{idx}]",
                )
            )
            if section in {KEY_INPUTS, KEY_OUTPUTS}:
                issues.extend(
                    self._validate_processor_types(
                        plugin_instance=plugin_instance,
                        path_prefix=f"{PIPELINE_PATH_PREFIX}.{section}[{idx}]",
                        processor_signals=processor_signals,
                        filter_plugins=filter_plugins,
                    )
                )

        LOGGER.info(
            "completed data type enforcement evaluation version=%s issue_count=%s",
            context.version,
            len(issues),
        )
        return issues

    def _validate_payload_types(
        self,
        *,
        payload: dict[str, Any],
        field_defs: list[dict[str, Any]],
        path_prefix: str,
    ) -> list[dict[str, Any]]:
        """Validate one payload object's field values against catalog data types.

        High-complexity flow notes:
        - Skip unknown keys early to avoid duplicate unknown-field handling elsewhere.
        - Special-case `time` and numeric env placeholders before generic type checks.
        - Keep bool-vs-number guard explicit because `bool` is a Python `int` subtype.
        """

        issues: list[dict[str, Any]] = []
        fields_by_name = {field[KEY_NAME]: field for field in field_defs if isinstance(field, dict)}

        # Walk payload keys once and evaluate expected type per catalog field metadata.
        for key, value in payload.items():
            if key == KEY_NAME or key not in fields_by_name:
                continue

            data_type = str(fields_by_name[key].get(KEY_DATA_TYPE, DATA_TYPE_STRING)).lower()

            # Time fields intentionally support integer values and compact duration strings.
            if data_type == DATA_TYPE_TIME:
                if not self._is_valid_time_value(value):
                    LOGGER.warning(
                        "time field failed validation path=%s key=%s value_type=%s",
                        path_prefix,
                        key,
                        type(value).__name__,
                    )
                    issues.append(
                        build_issue(
                            "invalid_type",
                            f"{path_prefix}.{key}",
                            f"Field '{key}' expects a non-negative integer or a string with optional s/m/h/d suffix.",
                        )
                    )
                continue

            expected = self.TYPE_MAP.get(data_type)
            if expected is None:
                LOGGER.debug("skipping unknown catalog data type key=%s data_type=%s", key, data_type)
                continue

            # Numeric fields may safely defer value resolution to runtime env expansion.
            if data_type in {DATA_TYPE_INTEGER, DATA_TYPE_FLOAT, DATA_TYPE_NUMBER} and self._is_numeric_env_var(value):
                continue

            if data_type in {DATA_TYPE_INTEGER, DATA_TYPE_FLOAT, DATA_TYPE_NUMBER, DATA_TYPE_SIZE} and isinstance(value, bool):
                LOGGER.warning(
                    "numeric-like field received boolean path=%s key=%s data_type=%s",
                    path_prefix,
                    key,
                    data_type,
                )
                issues.append(
                    build_issue(
                        "invalid_type",
                        f"{path_prefix}.{key}",
                        f"Field '{key}' expects {data_type}, got boolean.",
                    )
                )
                continue

            if not isinstance(value, expected):
                LOGGER.warning(
                    "field type mismatch path=%s key=%s expected=%s actual_type=%s",
                    path_prefix,
                    key,
                    data_type,
                    type(value).__name__,
                )
                issues.append(
                    build_issue(
                        "invalid_type",
                        f"{path_prefix}.{key}",
                        f"Field '{key}' expects {data_type}.",
                    )
                )

        return issues

    def _validate_processor_types(
        self,
        *,
        plugin_instance: dict[str, Any],
        path_prefix: str,
        processor_signals: dict[str, Any],
        filter_plugins: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Validate nested processor field types for input/output plugin payloads.

        High-complexity flow notes:
        - Validate processor container shape before deep traversal.
        - Build per-signal processor allow-lists, optionally merging filter plugins.
        - Delegate each processor payload to `_validate_payload_types`.
        """

        issues: list[dict[str, Any]] = []
        processors = plugin_instance.get(KEY_PROCESSORS)
        if not isinstance(processors, dict):
            if processors is not None:
                LOGGER.warning(
                    "processor payload is not a dict path=%s type=%s",
                    path_prefix,
                    type(processors).__name__,
                )
            return issues

        # Traverse signal -> processor-entry hierarchy and validate known processors only.
        for signal_name, processor_items in processors.items():
            if not isinstance(processor_items, list):
                LOGGER.warning(
                    "processor signal entry is not a list path=%s signal=%s type=%s",
                    path_prefix,
                    signal_name,
                    type(processor_items).__name__,
                )
                continue

            signal_def = processor_signals.get(signal_name, {})
            available_processors = dict(signal_def.get(KEY_PROCESSORS, {}))
            if signal_name == SIGNAL_LOGS and signal_def.get(KEY_ALLOW_FILTERS_AS_PROCESSORS):
                available_processors.update(filter_plugins)

            for idx, processor_payload in enumerate(processor_items):
                if not isinstance(processor_payload, dict):
                    LOGGER.warning(
                        "processor entry is not a dict path=%s signal=%s index=%s type=%s",
                        path_prefix,
                        signal_name,
                        idx,
                        type(processor_payload).__name__,
                    )
                    continue

                processor_name = processor_payload.get(KEY_NAME)
                if not isinstance(processor_name, str) or not processor_name:
                    LOGGER.warning(
                        "processor entry missing name path=%s signal=%s index=%s",
                        path_prefix,
                        signal_name,
                        idx,
                    )
                    continue

                processor_def = available_processors.get(processor_name)
                if not isinstance(processor_def, dict):
                    LOGGER.debug(
                        "processor definition not found path=%s signal=%s processor=%s",
                        path_prefix,
                        signal_name,
                        processor_name,
                    )
                    continue

                issues.extend(
                    self._validate_payload_types(
                        payload=processor_payload,
                        field_defs=processor_def.get(KEY_FIELDS, []),
                        path_prefix=f"{path_prefix}.{KEY_PROCESSORS}.{signal_name}[{idx}]",
                    )
                )

        return issues
