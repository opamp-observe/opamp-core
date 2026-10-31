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

"""Consumer-sim component version metadata loader."""

from __future__ import annotations

import json
from typing import Any

from opamp_consumer_sim.resources import (
    VERSION_FILENAME,
    read_packaged_text,
    source_resource_path,
)

COMPONENT_NAME = "consumer-sim"
_UNKNOWN_VALUE = "unknown"


def _fallback_payload() -> dict[str, str]:
    return {
        "component": COMPONENT_NAME,
        "git_label": _UNKNOWN_VALUE,
        "git_commit": _UNKNOWN_VALUE,
        "git_commit_date": _UNKNOWN_VALUE,
        "git_commit_date_friendly": _UNKNOWN_VALUE,
        "version": _UNKNOWN_VALUE,
        "generated_at_utc": _UNKNOWN_VALUE,
    }


def load_component_version_info() -> dict[str, str]:
    """Load version metadata from component JSON file with safe fallback."""
    fallback = _fallback_payload()
    try:
        version_path = source_resource_path(VERSION_FILENAME)
        if version_path is not None:
            payload_text = version_path.read_text(encoding="utf-8")
        else:
            payload_text = read_packaged_text(VERSION_FILENAME)
        payload: Any = json.loads(payload_text)
    except (OSError, ValueError, TypeError):
        return fallback
    if not isinstance(payload, dict):
        return fallback
    merged = dict(fallback)
    for key in merged:
        value = payload.get(key)
        if value is not None:
            merged[key] = str(value)
    return merged


def component_version_text() -> str:
    """Return formatted component version value for CLI help output."""
    return str(load_component_version_info().get("version", _UNKNOWN_VALUE))
