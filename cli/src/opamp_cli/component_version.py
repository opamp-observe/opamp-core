# Copyright 2026 mp3monster.org
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

"""Load the OpAMP CLI version from its packaged metadata resource."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

COMPONENT_NAME = "opamp-cli"
VERSION_RESOURCE_NAME = "version.json"
KEY_VERSION = "version"
UNKNOWN_VERSION = "unknown"
UTF8_ENCODING = "utf-8"


def component_version_text() -> str:
    """Return the packaged CLI version, falling back safely for damaged installations."""
    try:
        payload_text = resources.files("opamp_cli").joinpath(VERSION_RESOURCE_NAME).read_text(
            encoding=UTF8_ENCODING
        )
        payload: Any = json.loads(payload_text)
    except (OSError, TypeError, ValueError):
        return UNKNOWN_VERSION
    if not isinstance(payload, dict):
        return UNKNOWN_VERSION
    version_value = str(payload.get(KEY_VERSION, "") or "").strip()
    return version_value or UNKNOWN_VERSION
