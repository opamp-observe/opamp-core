#!/usr/bin/env python3
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
# 
from __future__ import annotations

from pathlib import Path
from typing import Any

from config_service.json_utils import load_json_file

UTF8_ENCODING = "utf-8"
KEY_REGISTRY_VERSION = "registry_version"
KEY_CODES = "codes"
DEFAULT_REGISTRY_VERSION = "1.0.0"


class IssueCodeService:
    """Load and expose configured issue-code registry payloads."""

    def __init__(self, config_path: Path) -> None:
        """Initialize the issue-code service with the supplied registry path."""
        self.config_path = config_path
        self._payload: dict[str, Any] = {KEY_REGISTRY_VERSION: DEFAULT_REGISTRY_VERSION, KEY_CODES: {}}

    def load(self) -> None:
        """Load the issue-code registry from disk when the registry file exists."""
        if not self.config_path.exists():
            return
        self._payload = load_json_file(self.config_path, purpose="issue-code registry")

    def get_all(self) -> dict[str, Any]:
        """Return the full loaded issue-code registry payload."""
        return self._payload

    def get_codes(self) -> dict[str, Any]:
        """Return the code-definition map from the loaded registry payload."""
        codes = self._payload.get(KEY_CODES, {})
        return codes if isinstance(codes, dict) else {}
