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

"""Shared constants and helpers for built-in rule-engine adapters.

These helpers keep the built-in adapter modules small and focused. Each adapter
validates a different aspect of the same catalog-backed pipeline payload, so the
catalog keys, issue shape, traversal logic, and common regexes live here.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from typing import Any

KEY_PIPELINE = "pipeline"
KEY_INPUTS = "inputs"
KEY_FILTERS = "filters"
KEY_OUTPUTS = "outputs"
KEY_NAME = "name"
KEY_PLUGINS = "plugins"
KEY_FIELDS = "fields"
KEY_REQUIRED = "required"
KEY_COMMON = "common"
KEY_PROCESSORS = "processors"
KEY_SIGNALS = "signals"
KEY_CONDITION = "condition"
KEY_VALIDATION_RULE = "validation_rule"
KEY_DATA_TYPE = "data_type"
KEY_KIND = "kind"
KEY_MIN = "min"
KEY_MAX = "max"
KEY_PATTERN = "pattern"
KEY_ALLOW_FILTERS_AS_PROCESSORS = "allow_filters_as_processors"

ISSUE_KEY_CODE = "code"
ISSUE_KEY_PATH = "path"
ISSUE_KEY_MESSAGE = "message"
ISSUE_KEY_SEVERITY = "severity"
ISSUE_KEY_SOURCE = "source"
ISSUE_SEVERITY_ERROR = "error"
ISSUE_SOURCE_RULES = "rules"

RULE_KIND_RANGE = "range"
RULE_KIND_REGEX = "regex"
RULE_KIND_REGEX_STRING = "regex_string"
RULE_KIND_BOOLEAN = "boolean"
RULE_KIND_DURATION = "duration"
RULE_KIND_SIZE = "size"

DATA_TYPE_STRING = "string"
DATA_TYPE_TIME = "time"
DATA_TYPE_INTEGER = "integer"
DATA_TYPE_BOOLEAN = "boolean"
DATA_TYPE_FLOAT = "float"
DATA_TYPE_NUMBER = "number"
DATA_TYPE_DURATION = "duration"
DATA_TYPE_SIZE = "size"
DATA_TYPE_ARRAY = "array"
DATA_TYPE_LIST = "list"
DATA_TYPE_OBJECT = "object"
DATA_TYPE_MAP = "map"

SIGNAL_LOGS = "logs"
PIPELINE_PATH_PREFIX = "$.pipeline"

LOGGER = logging.getLogger(__name__)

# Fluent Bit size literals follow the upstream unit-size rules:
# https://docs.fluentbit.io/manual/administration/configuring-fluent-bit#unit-sizes
SIZE_VALUE_PATTERN = re.compile(r"^\d+([KMGTP]i?[Bb]?|[KMGTP])?$")
DURATION_VALUE_PATTERN = re.compile(r"^\d+(ns|us|ms|s|m|h|d)?$")


def iter_pipeline_plugins(config: dict[str, Any]) -> Iterator[tuple[str, int, dict[str, Any]]]:
    """Yield concrete plugin payloads from the main pipeline sections.

    Built-in adapters all validate plugin instances under `pipeline.inputs`,
    `pipeline.filters`, and `pipeline.outputs`. This helper centralizes the
    traversal and defensive logging for malformed payload shapes.
    """

    pipeline = config.get(KEY_PIPELINE, {})
    if not isinstance(pipeline, dict):
        LOGGER.warning("rule adapter pipeline payload is not a dict; skipping plugin traversal")
        return

    for section in (KEY_INPUTS, KEY_FILTERS, KEY_OUTPUTS):
        items = pipeline.get(section, [])
        if not isinstance(items, list):
            LOGGER.warning(
                "rule adapter pipeline section is not a list; skipping section=%s type=%s",
                section,
                type(items).__name__,
            )
            continue

        for idx, item in enumerate(items):
            if isinstance(item, dict):
                yield section, idx, item
            else:
                LOGGER.warning(
                    "rule adapter plugin entry is not a dict; skipping section=%s index=%s type=%s",
                    section,
                    idx,
                    type(item).__name__,
                )


def catalog_plugin_definition(catalog: dict[str, Any], section: str, name: str) -> dict[str, Any] | None:
    """Return the catalog definition for one plugin instance, if available."""

    plugin = catalog.get(KEY_PLUGINS, {}).get(section, {}).get(name)
    if plugin is None:
        LOGGER.debug("catalog plugin definition not found section=%s name=%s", section, name)
    return plugin


def build_issue(
    code: str,
    path: str,
    message: str,
    severity: str = ISSUE_SEVERITY_ERROR,
    source: str = ISSUE_SOURCE_RULES,
) -> dict[str, Any]:
    """Create a consistently-shaped issue payload for rule-engine responses."""

    return {
        ISSUE_KEY_CODE: code,
        ISSUE_KEY_PATH: path,
        ISSUE_KEY_MESSAGE: message,
        ISSUE_KEY_SEVERITY: severity,
        ISSUE_KEY_SOURCE: source,
    }
