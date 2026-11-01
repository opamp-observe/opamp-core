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

"""Script-generation helpers for `opamp-cli script ...` mode."""

from __future__ import annotations

from pathlib import Path

try:
    from .common import _is_windows, _normalize_python_script_command, _target_extension
    from .constants import DEFAULT_OUTPUT_DIR
except ImportError:
    # Support direct module loading when `main.py` is executed as a script.
    from common import _is_windows, _normalize_python_script_command, _target_extension  # type: ignore[no-redef]
    from constants import DEFAULT_OUTPUT_DIR  # type: ignore[no-redef]

SCRIPT_DIRECTIVE_MIN_PARTS = 3


def _resolve_script_path(raw_name: str) -> Path:
    """Resolve output script path for current OS.

    Plain names are written under `scripts/`.
    """
    base = Path(raw_name.strip()).expanduser()
    if not base.name:
        raise ValueError("script name cannot be empty")

    target_ext = _target_extension()
    resolved = base.with_suffix(target_ext)
    if resolved.parent == Path("."):
        resolved = DEFAULT_OUTPUT_DIR / resolved.name
    return resolved.resolve()


def _render_script(command_text: str) -> str:
    """Render platform-specific script content."""
    launcher = "python" if _is_windows() else "python3"
    rendered_command = _normalize_python_script_command(
        command_text,
        launcher=launcher,
    )
    if _is_windows():
        return "\n".join([
            "@echo off",
            "setlocal",
            "",
            rendered_command,
            "",
        ])

    return "\n".join([
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        rendered_command,
        "",
    ])


def _write_script(output_path: Path, command_text: str) -> Path:
    """Write the generated script file to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_render_script(command_text), encoding="utf-8")
    if not _is_windows():
        output_path.chmod(output_path.stat().st_mode | 0o111)
    return output_path


def _split_script_directive(raw: str) -> tuple[str, str]:
    """Parse `script <name> <command...>` directive without command validation."""
    parts = raw.strip().split(maxsplit=2)
    if len(parts) < SCRIPT_DIRECTIVE_MIN_PARTS:
        raise ValueError("script mode requires: script <output_name> <command...>")
    _, output_name, command_text = parts
    return output_name, command_text.strip()
