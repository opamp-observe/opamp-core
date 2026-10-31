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

"""Catalog-facing metadata keys extracted from config files."""

from __future__ import annotations

import json
import re

KEY_CONFIG_TYPE = "config_type"
KEY_CONFIG_VERSION = "config_version"
KEY_CONFIGURATION_DATE = "configuration_date"
KEY_SCM_CONFIG_VERSION = "SCM_config_version"
KEY_SCM_SOURCE_NAME = "SCM_source_name"

INLINE_METADATA_PREFIX = "_metadata."
INLINE_METADATA_KEYS = (
    KEY_CONFIG_VERSION,
    KEY_CONFIGURATION_DATE,
    KEY_SCM_CONFIG_VERSION,
    KEY_CONFIG_TYPE,
    KEY_SCM_SOURCE_NAME,
)
INLINE_METADATA_LINE_PATTERN = re.compile(
    r"""(?P<quote>["']?)_metadata\.(?P<key>[A-Za-z0-9_.-]+)(?P=quote)(?:\s*[:=]\s*|\s+)(?P<value>.+?)\s*$"""
)

_CONFIG_TYPE_ALIASES = {
    "fluentbit": "fluentbit",
    "fluent-bit": "fluentbit",
    "fluentd": "fluentd",
}


def extract_inline_metadata(text: str) -> dict[str, str]:
    """Extract supported `_metadata.*` entries from YAML, JSON, and classic text."""
    metadata: dict[str, str] = {}
    for raw_line in str(text or "").splitlines():
        if INLINE_METADATA_PREFIX not in raw_line:
            continue
        match = INLINE_METADATA_LINE_PATTERN.search(raw_line)
        if not match:
            continue
        key = str(match.group("key") or "").strip()
        if key not in INLINE_METADATA_KEYS:
            continue
        value = _normalize_metadata_value(key, str(match.group("value") or ""))
        if value:
            metadata[key] = value
    return metadata


def _normalize_metadata_value(key: str, raw_value: str) -> str:
    value = str(raw_value or "").strip()
    if not value:
        return ""
    value = re.sub(r",\s*$", "", value)
    if value.startswith('"') and value.endswith('"'):
        try:
            value = str(json.loads(value))
        except json.JSONDecodeError:
            value = value[1:-1]
    elif value.startswith("'") and value.endswith("'"):
        value = value[1:-1]
    else:
        value = re.sub(r"\s+#.*$", "", value).strip()
    if key == KEY_CONFIG_TYPE:
        return _CONFIG_TYPE_ALIASES.get(value.strip().lower(), value.strip())
    return value.strip()
