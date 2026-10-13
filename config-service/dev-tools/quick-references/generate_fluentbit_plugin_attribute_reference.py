#!/usr/bin/env python3
# Copyright 2026 mp3monster.org
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

"""Generate Fluent Bit plugin attribute reference markdown files.

What this script does:
1. Reads Fluent Bit plugin catalog JSON files from a source directory.
2. Produces markdown tables listing plugin attributes for `inputs`, `filters`,
   and `outputs`.
3. Writes markdown reference files into a target directory.

Dependencies:
1. Python 3.10+.
2. Python standard library plus local `config_service` helpers.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_SERVICE_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = CONFIG_SERVICE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config_service.json_artifacts import load_json_artifact  # noqa: E402

DEFAULT_SOURCE_DIR = CONFIG_SERVICE_ROOT / "src" / "config_service" / "json-definitions"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "quick-references"
DEFAULT_VERSIONS = ("3.2.10", "4.2.4", "5.0.4")
SECTION_TITLES = (
    ("inputs", "Inputs"),
    ("filters", "Filters"),
    ("outputs", "Outputs"),
)


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def _input_path(source_dir: Path, version: str) -> Path:
    return source_dir / f"fluent-bit-{version}-all-plugins-catalog.json"


def _output_path(output_dir: Path, version: str) -> Path:
    version_token = str(version).replace(".", "-")
    return output_dir / f"fluentbit-{version_token}-plugin-attribute-reference.md"


def _link(title: str, reference: str) -> str:
    if reference:
        return f"[{title}]({reference})"
    return title


def _section_rows(section_plugins: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for plugin_name in sorted(section_plugins):
        plugin_def = section_plugins.get(plugin_name)
        if not isinstance(plugin_def, dict):
            continue
        plugin_title = str(plugin_def.get("title") or plugin_name)
        fields = plugin_def.get("fields")
        if not isinstance(fields, list):
            continue
        for field_def in fields:
            if not isinstance(field_def, dict):
                continue
            field_name = str(field_def.get("name") or "").strip()
            if not field_name:
                continue
            reference = str(field_def.get("reference") or plugin_def.get("doc_url") or "").strip()
            rows.append(
                f"| `{plugin_name}` | `{field_name}` | {_link(plugin_title, reference)} |"
            )
    return rows


def _render_markdown(version: str, payload: dict[str, Any], source_file: Path) -> str:
    plugins = payload.get("plugins", {})
    lines: list[str] = [
        f"# Fluent Bit {version} Plugin Attribute Reference",
        "",
        "Generated from the local catalog JSON only.",
        f"- `{_display_path(source_file)}`",
        "",
        "Scope: this reference includes the field-based `inputs`, `filters`, and `outputs` plugin groups from the catalog JSON. The `custom_plugins` block is not tabulated because it does not provide per-attribute documentation links in the same structure.",
    ]
    for section_key, section_title in SECTION_TITLES:
        section_plugins = plugins.get(section_key, {})
        if not isinstance(section_plugins, dict):
            continue
        lines.extend(
            [
                "",
                f"## {section_title}",
                "",
                "| Plugin Name | Attribute Name | Fluent Bit Page |",
                "| --- | --- | --- |",
            ]
        )
        lines.extend(_section_rows(section_plugins))
    return "\n".join(lines) + "\n"


def generate_reference(version: str, source_dir: Path, output_dir: Path) -> None:
    input_path = _input_path(source_dir, version)
    output_path = _output_path(output_dir, version)
    payload = load_json_artifact(input_path)
    output_path.write_text(_render_markdown(version, payload, input_path), encoding="utf-8")
    print(f"Wrote {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Fluent Bit plugin attribute reference markdown from catalog JSON.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="append",
        dest="versions",
        help="Fluent Bit version to generate. Repeat for multiple versions.",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help="Directory containing fluent-bit-<version>-all-plugins-catalog.json files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where markdown reference files are written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    versions = tuple(args.versions) if args.versions else DEFAULT_VERSIONS
    source_dir = args.source_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    for version in versions:
        generate_reference(version, source_dir, output_dir)


if __name__ == "__main__":
    main()
