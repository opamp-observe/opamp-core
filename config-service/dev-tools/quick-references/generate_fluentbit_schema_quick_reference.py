#!/usr/bin/env python3
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

"""Generate Fluent Bit schema quick-reference markdown files.

What this script does:
1. Reads Fluent Bit JSON schema files from a source directory.
2. Builds human-readable markdown quick references for `env`, `upstream_servers`,
   and pipeline plugin sections (`inputs`, `filters`, `outputs`).
3. Writes output markdown files into a target directory.

Dependencies:
1. Python 3.10+.
2. Python standard library plus local `config_service` helpers.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_SERVICE_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = CONFIG_SERVICE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config_service.json_artifacts import load_json_schema_artifact  # noqa: E402

DEFAULT_SOURCE_DIR = CONFIG_SERVICE_ROOT / "src" / "config_service" / "json-schemas"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "quick-references"

SECTION_TITLES = {
    "inputs": "Inputs",
    "filters": "Filters",
    "outputs": "Outputs",
}
DEFAULT_VERSIONS = ("3.2.10", "4.2.4", "5.0.4")
ENV_ANCHOR = "environment-env"
UPSTREAM_SERVERS_ANCHOR = "upstream-servers-upstream-servers"
INTERNAL_COMMENT_META_FIELD = "_meta"


def schema_path(source_dir: Path, version: str) -> Path:
    return source_dir / f"fluentbit-{version}-config-schema.json"


def output_path(output_dir: Path, version: str) -> Path:
    version_token = str(version).replace(".", "-")
    return output_dir / f"fluentbit-{version_token}-schema-quick-reference.md"


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def load_schema(source_dir: Path, version: str) -> dict[str, Any]:
    return load_json_schema_artifact(schema_path(source_dir, version))


def plugin_variants(schema: dict[str, Any], section: str) -> list[dict[str, Any]]:
    return (
        schema["properties"]["config"]["properties"]["pipeline"]["properties"][section]["items"]["oneOf"]
    )


def plugin_name(variant: dict[str, Any]) -> str:
    return str(variant["properties"]["name"]["const"])


def plugin_doc_url(variant: dict[str, Any]) -> str:
    for field_name, field_schema in variant.get("properties", {}).items():
        if field_name in {"name", INTERNAL_COMMENT_META_FIELD}:
            continue
        ref = field_schema.get("x-doc-reference")
        if ref:
            return str(ref)
    return ""


def fluentbit_doc_series(version: str) -> str:
    parts = str(version).split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return str(version)


def env_doc_url(version: str) -> str:
    return (
        "https://docs.fluentbit.io/manual/"
        f"{fluentbit_doc_series(version)}"
        "/administration/configuring-fluent-bit/yaml/environment-variables-section"
    )


def upstream_servers_doc_url(version: str) -> str:
    return (
        "https://docs.fluentbit.io/manual/"
        f"{fluentbit_doc_series(version)}"
        "/administration/configuring-fluent-bit/yaml/upstream-servers-section"
    )


def anchor_for(section: str, name: str) -> str:
    return f"{section}-{name.lower().replace('_', '-').replace('.', '-')}"


def format_default(field_schema: dict[str, Any], *, fallback: str = "") -> str:
    if "const" in field_schema:
        return str(field_schema["const"])
    if "default" not in field_schema:
        return fallback
    value = field_schema["default"]
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    if isinstance(value, str):
        return re.sub(r",\s*", ", ", value)
    return str(value)


def mandatory_label(field_name: str, variant: dict[str, Any], field_schema: dict[str, Any]) -> str:
    required = set(variant.get("required", []))
    if field_name in required:
        return "Yes"
    if field_schema.get("x-doc-required") is True:
        return "Yes"
    return "No"


def attribute_description(field_name: str, field_schema: dict[str, Any]) -> str:
    if field_name == "name":
        return "Plugin identifier."
    return re.sub(r",\s*", ", ", str(field_schema.get("description", "")).strip())


def escape_pipes(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def sort_field_names(variant: dict[str, Any]) -> list[str]:
    properties = variant.get("properties", {})
    required = set(variant.get("required", []))
    # `_meta` is an internal, optional comment carrier used by config-service.
    # It is intentionally omitted from quick-reference output because it is not
    # part of the Fluent Bit configuration specification.
    candidate_fields = [
        field_name
        for field_name in properties.keys()
        if field_name != INTERNAL_COMMENT_META_FIELD
    ]

    def sort_key(field_name: str) -> tuple[int, int, str]:
        is_required = field_name in required or properties[field_name].get("x-doc-required") is True
        is_name = field_name == "name"
        return (0 if is_required else 1, 0 if is_name else 1, field_name.lower())

    return sorted(candidate_fields, key=sort_key)


def build_plugin_table(section: str, variant: dict[str, Any]) -> list[str]:
    name = plugin_name(variant)
    title = str(variant.get("title", name))
    doc_url = plugin_doc_url(variant)
    anchor = anchor_for(section, name)

    lines = [
        f'<a id="{anchor}"></a>',
        f"### `{name}`: {title}",
    ]
    if doc_url:
        lines.append(f"Fluent Bit page: [{title}]({doc_url})")
    lines.extend(
        [
            "",
            "| Attribute | Mandatory | Default | Description |",
            "| --- | --- | --- | --- |",
        ]
    )

    properties = variant.get("properties", {})
    for field_name in sort_field_names(variant):
        field_schema = properties[field_name]
        default_value = format_default(
            field_schema,
            fallback=name if field_name == "name" else "",
        )
        description = attribute_description(field_name, field_schema)
        attribute = f"`{escape_pipes(field_name)}`"
        if doc_url:
            attribute = f"[{attribute}]({doc_url})"
        lines.append(
            "| {attribute} | {mandatory} | {default_value} | {description} |".format(
                attribute=attribute,
                mandatory=mandatory_label(field_name, variant, field_schema),
                default_value=(
                    f"`{escape_pipes(default_value)}`" if default_value else ""
                ),
                description=escape_pipes(description),
            )
        )
    lines.append("")
    return lines


def build_section(section: str, variants: list[dict[str, Any]]) -> list[str]:
    sorted_variants = sorted(variants, key=lambda item: plugin_name(item).lower())
    links = [
        f"[`{plugin_name(variant)}`](#{anchor_for(section, plugin_name(variant))})"
        for variant in sorted_variants
    ]
    lines = [
        f"## {SECTION_TITLES[section]}",
        "",
        ", ".join(links),
        "",
    ]
    for variant in sorted_variants:
        lines.extend(build_plugin_table(section, variant))
    return lines


def build_env_section(version: str) -> list[str]:
    doc_url = env_doc_url(version)
    return [
        f'<a id="{ENV_ANCHOR}"></a>',
        "## Environment Variables",
        "",
        "Quick reference for the optional Fluent Bit YAML `env` section.",
        f"Fluent Bit page: [Environment variables]({doc_url})",
        "",
        "| Attribute | Mandatory | Default | Description |",
        "| --- | --- | --- | --- |",
        f"| [`env`]({doc_url}) | No | `{{}}` | Object map of local environment variables available to this configuration file. |",
        f"| [`<ENV_VAR_NAME>`]({doc_url}) | No |  | Variable key name. Use uppercase letters, digits, and `_`, and avoid spaces or punctuation. |",
        f"| [`<ENV_VAR_NAME>` value]({doc_url}) | No |  | Variable value consumed with `${{ENV_VAR_NAME}}` in Fluent Bit configuration fields. |",
        "",
    ]


def build_upstream_servers_section(version: str) -> list[str]:
    doc_url = upstream_servers_doc_url(version)
    return [
        f'<a id="{UPSTREAM_SERVERS_ANCHOR}"></a>',
        "## Upstream Servers",
        "",
        "Quick reference for optional Fluent Bit YAML `upstream_servers` groups.",
        f"Fluent Bit page: [Upstream servers]({doc_url})",
        "",
        "| Attribute | Mandatory | Default | Description |",
        "| --- | --- | --- | --- |",
        f"| [`upstream_servers`]({doc_url}) | No | `[]` | List of upstream groups used by supporting output plugins for round-robin endpoint selection. |",
        f"| [`upstream_servers[].name`]({doc_url}) | Yes |  | Upstream group name. |",
        f"| [`upstream_servers[].nodes`]({doc_url}) | Yes |  | List of node endpoints in the group. |",
        f"| [`upstream_servers[].nodes[].name`]({doc_url}) | Yes |  | Node name. |",
        f"| [`upstream_servers[].nodes[].host`]({doc_url}) | Yes |  | Node host/IP endpoint. |",
        f"| [`upstream_servers[].nodes[].port`]({doc_url}) | Yes |  | Node TCP port. |",
        f"| [`upstream_servers[].nodes[].tls`]({doc_url}) | No |  | Enable TLS for this node connection. |",
        f"| [`upstream_servers[].nodes[].tls_verify`]({doc_url}) | No |  | Verify TLS certificate for this node. |",
        f"| [`upstream_servers[].nodes[].shared_key`]({doc_url}) | No |  | Shared key for secure node communication. |",
        "",
    ]


def generate_markdown(schema: dict[str, Any], version: str, source_file: Path) -> str:
    lines = [
        f"# Fluent Bit {version} Schema Quick Reference",
        "",
        f"Generated from the local Fluent Bit {version} JSON schema only:",
        f"- `{_display_path(source_file)}`",
        "",
        "Scope:",
        "1. Environment variable map definition for `env`",
        "2. Upstream server groups for `upstream_servers`",
        "3. Pipeline plugin definitions",
        "4. Grouped by `inputs`, `filters`, and `outputs`",
        "5. Includes mandatory flags, defaults, descriptions, and Fluent Bit documentation links",
        "6. Excludes internal optional `_meta` comment metadata fields because they are not part of the Fluent Bit specification",
        "",
        "## Jump Lists",
        "",
        f"- **Environment**: [`env`](#{ENV_ANCHOR})",
        f"- **Upstream Servers**: [`upstream_servers`](#{UPSTREAM_SERVERS_ANCHOR})",
    ]
    for section in ("inputs", "filters", "outputs"):
        variants = plugin_variants(schema, section)
        links = [
            f"[`{plugin_name(variant)}`](#{anchor_for(section, plugin_name(variant))})"
            for variant in sorted(variants, key=lambda item: plugin_name(item).lower())
        ]
        lines.append(f"- **{SECTION_TITLES[section]}**: {', '.join(links)}")
    lines.append("")
    lines.extend(build_env_section(version))
    lines.extend(build_upstream_servers_section(version))

    for section in ("inputs", "filters", "outputs"):
        lines.extend(build_section(section, plugin_variants(schema, section)))

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Fluent Bit schema quick-reference markdown files.",
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
        help="Directory containing fluentbit-<version>-config-schema.json files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where markdown quick-reference files are written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    versions = tuple(args.versions) if args.versions else DEFAULT_VERSIONS
    source_dir = args.source_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for version in versions:
        source_file = schema_path(source_dir, version)
        schema = load_schema(source_dir, version)
        target_file = output_path(output_dir, version)
        target_file.write_text(
            generate_markdown(schema, version, source_file),
            encoding="utf-8",
        )
        print(f"Wrote {target_file}")


if __name__ == "__main__":
    main()
