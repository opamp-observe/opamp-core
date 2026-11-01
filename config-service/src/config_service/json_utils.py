#!/usr/bin/env python3
# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

UTF8_ENCODING = "utf-8"


class JsonConfigLoadError(ValueError):
    """Raised when a JSON-backed config file cannot be read or parsed."""


def load_json_file(path: Path, *, purpose: str = "JSON file") -> Any:
    """Load one JSON file and attach path and parse-location context on failure."""
    try:
        raw = path.read_text(encoding=UTF8_ENCODING)
    except OSError as exc:
        raise JsonConfigLoadError(f"Failed reading {purpose} '{path}': {exc}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise JsonConfigLoadError(
            f"Failed parsing {purpose} '{path}' at line {exc.lineno} column {exc.colno}: {exc.msg}"
        ) from exc
    except (TypeError, ValueError) as exc:
        raise JsonConfigLoadError(f"Failed parsing {purpose} '{path}': {exc}") from exc
