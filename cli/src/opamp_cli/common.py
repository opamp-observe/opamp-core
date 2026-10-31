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

"""Cross-cutting small helpers for the OpAMP CLI."""

from __future__ import annotations

import os
import shlex
from datetime import datetime, timezone
from pathlib import Path


def _is_windows() -> bool:
    """Return whether the current OS is Windows."""
    return os.name == "nt"


def _target_extension() -> str:
    """Return script extension for the current OS."""
    return ".cmd" if _is_windows() else ".sh"


def _first_token(command_text: str) -> str:
    """Return first shell token or empty string when tokenization fails."""
    text = str(command_text or "").strip()
    if not text:
        return ""
    try:
        tokens = shlex.split(text, posix=not _is_windows())
    except ValueError:
        tokens = text.split()
    if not tokens:
        return ""
    return str(tokens[0] or "").strip().strip("\"'")


def _is_python_launcher(token: str) -> bool:
    """Return whether token is a Python interpreter command."""
    normalized = Path(str(token or "").strip().strip("\"'")).name.lower()
    return normalized in {"python", "python3", "py", "python.exe", "py.exe"}


def _is_python_script_target(token: str) -> bool:
    """Return whether token points to a Python source script."""
    cleaned = str(token or "").strip().strip("\"'")
    return Path(cleaned).suffix.lower() in {".py", ".pyw"}


def _normalize_python_script_command(command_text: str, *, launcher: str) -> str:
    """Prefix direct .py/.pyw invocations with a Python launcher."""
    first = _first_token(command_text)
    if not first:
        return command_text
    if _is_python_launcher(first):
        return command_text
    if not _is_python_script_target(first):
        return command_text
    return f"\"{launcher}\" {command_text}"


def _shell_quote(value: str) -> str:
    """Return shell-safe quoting for one argument fragment."""
    if _is_windows():
        escaped = str(value).replace('"', '""')
        return f'"{escaped}"'
    return shlex.quote(str(value))


def _utc_timestamp() -> str:
    """Return UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slugify(label: str) -> str:
    """Convert a human label into a stable lowercase slug."""
    cleaned = "".join(
        char.lower() if char.isalnum() else "-"
        for char in str(label or "").strip()
    )
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "process"


def _normalized_label(label: str) -> str:
    """Return a stable comparison key for guided action labels."""
    return _slugify(label).replace("-", "")
