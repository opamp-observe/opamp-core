# Copyright 2026 mp3monster.org
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Report plugin and attribute additions between local Fluent Bit catalogs."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .fluentbit_online import (
    DEFAULT_DOCUMENTATION_SOURCE,
    DEFAULT_ONLINE_TIMEOUT_SECONDS,
    load_online_catalog,
)

CATALOG_RELATIVE_PATH = Path("config-service/src/config_service/json-definitions/fluent-bit")
CATALOG_SECTIONS = ("inputs", "filters", "outputs")
DEFAULT_REPORT_RELATIVE_PATH = Path("config-service/reports/fluentbit")
REPORT_FORMAT = "opamp-dev-tools.fluentbit-additions/v1"
REPORT_SCOPE_NOTE = (
    "Candidate additions are derived from retained local catalogs. They can reflect catalog "
    "coverage or naming changes and are not independent proof of an upstream Fluent Bit change."
)
ONLINE_REPORT_SCOPE_NOTE = (
    "Candidate additions are derived from live upstream documentation compared with a retained "
    "local catalog. They can reflect documentation coverage, parsing, or naming changes and are "
    "not independent proof of an upstream Fluent Bit runtime change."
)
LOCAL_CATALOG_SOURCE = "retained local catalog"
ONLINE_CATALOG_SOURCE = "live upstream documentation"

KEY_ARTIFACT_MANIFEST = "artifact_manifest"
KEY_ATTRIBUTE = "attribute"
KEY_ATTRIBUTES = "attributes"
KEY_CATALOG_ROOT = "catalog_root"
KEY_COUNTS = "counts"
KEY_CURRENT_SOURCE = "current_source"
KEY_CURRENT_VERSION = "current_version"
KEY_DOCUMENTATION_SOURCE = "documentation_source"
KEY_FIELDS = "fields"
KEY_FILE = "file"
KEY_FORMAT = "format"
KEY_NAME = "name"
KEY_NEW_ATTRIBUTES = "new_attributes"
KEY_NEW_ATTRIBUTE_COUNT = "new_attribute_count"
KEY_NEW_PLUGIN_COUNT = "new_plugin_count"
KEY_NEW_PLUGINS = "new_plugins"
KEY_PARTS = "parts"
KEY_PLUGIN = "plugin"
KEY_PLUGINS = "plugins"
KEY_POINTER = "pointer"
KEY_PREVIOUS_VERSION = "previous_version"
KEY_PREVIOUS_SOURCE = "previous_source"
KEY_PREVIOUS_ATTRIBUTES = "previous_attributes"
KEY_REASON = "reason"
KEY_REPRESENTATION_CHANGE_COUNT = "representation_change_count"
KEY_REPRESENTATION_CHANGES = "representation_changes"
KEY_SCOPE_NOTE = "scope_note"
KEY_SECTION = "section"
KEY_TITLE = "title"

REASON_CURRENT_WILDCARD = "current_wildcard_covers_previous_attributes"
REASON_PREVIOUS_WILDCARD = "previous_wildcard_already_covered_attribute"


def report_fluentbit_changes(  # pylint: disable=too-many-arguments
    runtime: Any,
    *,
    current_version: str = "",
    previous_version: str = "",
    output_dir: str = "",
    online: bool = False,
    documentation_source: str = DEFAULT_DOCUMENTATION_SOURCE,
    github_ref: str = "",
    timeout: int = DEFAULT_ONLINE_TIMEOUT_SECONDS,
) -> bool:
    """Compare catalogs, write JSON/Markdown reports, and print additions.

    Parameters
    ----------
    runtime:
        Command runtime that provides the repository root and console logging.
    current_version:
        Optional target version; the newest retained version is used by default.
    previous_version:
        Optional baseline version; the nearest earlier version is used by default.
    output_dir:
        Optional report directory, resolved relative to the repository root.
    online:
        Whether the current catalog should be built from upstream documentation.
    documentation_source:
        Upstream source preference used for an online comparison.
    github_ref:
        Optional Git ref override for an online GitHub documentation scrape.
    timeout:
        Per-request timeout for online documentation retrieval.

    """
    if online:
        report = compare_online_fluentbit_catalog(
            runtime.repo_root,
            current_version=current_version,
            previous_version=previous_version,
            documentation_source=documentation_source,
            github_ref=github_ref,
            timeout=timeout,
        )
    else:
        report = compare_fluentbit_catalogs(
            runtime.repo_root,
            current_version=current_version,
            previous_version=previous_version,
        )
    resolved_output_dir = _resolve_output_directory(runtime.repo_root, output_dir)
    json_path, markdown_path = write_change_reports(report, resolved_output_dir)
    runtime.info(
        "DEBUG: compared Fluent Bit catalogs "
        f"previous={report[KEY_PREVIOUS_VERSION]} current={report[KEY_CURRENT_VERSION]}"
    )
    _print_report_summary(runtime, report)
    runtime.info(f"JSON report: {json_path}")
    runtime.info(f"Markdown report: {markdown_path}")
    return False


def compare_fluentbit_catalogs(
    repo_root: Path,
    *,
    current_version: str = "",
    previous_version: str = "",
) -> dict[str, Any]:
    """Return plugin and field additions between two retained local catalogs.

    Parameters
    ----------
    repo_root:
        Repository containing the canonical Config Service catalog tree.
    current_version:
        Optional target version, defaulting to the newest retained version.
    previous_version:
        Optional baseline version, defaulting to the nearest earlier version.

    """
    catalog_root = (repo_root / CATALOG_RELATIVE_PATH).resolve()
    available_versions = discover_fluentbit_versions(catalog_root)
    resolved_current, resolved_previous = resolve_version_pair(
        available_versions,
        current_version=current_version,
        previous_version=previous_version,
    )
    current_plugins = load_catalog_plugins(catalog_root, resolved_current)
    previous_plugins = load_catalog_plugins(catalog_root, resolved_previous)
    return _build_report(
        current_version=resolved_current,
        previous_version=resolved_previous,
        current_plugins=current_plugins,
        previous_plugins=previous_plugins,
        scope_note=REPORT_SCOPE_NOTE,
        current_source=LOCAL_CATALOG_SOURCE,
        previous_source=LOCAL_CATALOG_SOURCE,
    )


def compare_online_fluentbit_catalog(  # pylint: disable=too-many-arguments
    repo_root: Path,
    *,
    current_version: str = "",
    previous_version: str = "",
    documentation_source: str = DEFAULT_DOCUMENTATION_SOURCE,
    github_ref: str = "",
    timeout: int = DEFAULT_ONLINE_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Compare an online documentation catalog with a retained local baseline.

    Parameters
    ----------
    repo_root:
        Repository containing local catalogs and the Config Service scraper.
    current_version:
        Optional upstream version, defaulting to the current stable release.
    previous_version:
        Optional retained local baseline, defaulting to the nearest earlier version.
    documentation_source:
        Upstream source preference: auto, GitHub, or published website.
    github_ref:
        Optional Git ref override used by the GitHub documentation scraper.
    timeout:
        Per-request timeout for upstream retrieval.

    """
    catalog_root = (repo_root / CATALOG_RELATIVE_PATH).resolve()
    available_versions = discover_fluentbit_versions(catalog_root)
    resolved_current, online_catalog = load_online_catalog(
        repo_root,
        version=current_version,
        source=documentation_source,
        github_ref=github_ref,
        timeout=timeout,
    )
    resolved_previous = resolve_online_previous_version(
        available_versions,
        current_version=resolved_current,
        previous_version=previous_version,
    )
    current_plugins = load_documentation_catalog_plugins(online_catalog)
    previous_plugins = load_catalog_plugins(catalog_root, resolved_previous)
    return _build_report(
        current_version=resolved_current,
        previous_version=resolved_previous,
        current_plugins=current_plugins,
        previous_plugins=previous_plugins,
        scope_note=ONLINE_REPORT_SCOPE_NOTE,
        current_source=ONLINE_CATALOG_SOURCE,
        previous_source=LOCAL_CATALOG_SOURCE,
        documentation_source=documentation_source,
    )


def _build_report(  # pylint: disable=too-many-arguments
    *,
    current_version: str,
    previous_version: str,
    current_plugins: Mapping[tuple[str, str], Mapping[str, Any]],
    previous_plugins: Mapping[tuple[str, str], Mapping[str, Any]],
    scope_note: str,
    current_source: str,
    previous_source: str,
    documentation_source: str = "",
) -> dict[str, Any]:
    """Build the common report structure for local and online comparisons.

    Parameters
    ----------
    current_version:
        Target Fluent Bit version label.
    previous_version:
        Baseline Fluent Bit version label.
    current_plugins:
        Target plugins keyed by section and plugin name.
    previous_plugins:
        Baseline plugins keyed by section and plugin name.
    scope_note:
        Accuracy and interpretation guidance included in the report.
    current_source:
        Human-readable target catalog source.
    previous_source:
        Human-readable baseline catalog source.
    documentation_source:
        Optional upstream source selection used for an online scrape.

    """
    new_plugins, new_attributes, representation_changes = _collect_additions(
        current_plugins,
        previous_plugins,
    )
    report = {
        KEY_FORMAT: REPORT_FORMAT,
        KEY_CURRENT_VERSION: current_version,
        KEY_PREVIOUS_VERSION: previous_version,
        KEY_CATALOG_ROOT: CATALOG_RELATIVE_PATH.as_posix(),
        KEY_SCOPE_NOTE: scope_note,
        KEY_CURRENT_SOURCE: current_source,
        KEY_PREVIOUS_SOURCE: previous_source,
        KEY_COUNTS: {
            KEY_NEW_PLUGIN_COUNT: len(new_plugins),
            KEY_NEW_ATTRIBUTE_COUNT: len(new_attributes),
            KEY_REPRESENTATION_CHANGE_COUNT: len(representation_changes),
        },
        KEY_NEW_PLUGINS: new_plugins,
        KEY_NEW_ATTRIBUTES: new_attributes,
        KEY_REPRESENTATION_CHANGES: representation_changes,
    }
    if documentation_source:
        report[KEY_DOCUMENTATION_SOURCE] = documentation_source
    return report


def discover_fluentbit_versions(catalog_root: Path) -> list[str]:
    """Return semantically sorted versions with all required section manifests.

    Parameters
    ----------
    catalog_root:
        Canonical directory containing one subdirectory per Fluent Bit version.

    """
    if not catalog_root.is_dir():
        raise FileNotFoundError(f"Fluent Bit catalog directory not found: {catalog_root}")
    versions = [
        candidate.name
        for candidate in catalog_root.iterdir()
        if candidate.is_dir()
        and all((candidate / f"{section_name}.json").is_file() for section_name in CATALOG_SECTIONS)
        and _is_semantic_version(candidate.name)
    ]
    return sorted(versions, key=semantic_version_key)


def resolve_version_pair(
    available_versions: list[str],
    *,
    current_version: str = "",
    previous_version: str = "",
) -> tuple[str, str]:
    """Resolve explicit or automatic current and previous catalog versions.

    Parameters
    ----------
    available_versions:
        Semantically sortable versions available in the local catalog tree.
    current_version:
        Optional requested current version.
    previous_version:
        Optional requested previous version.

    """
    if len(available_versions) < 2:
        raise ValueError("At least two local Fluent Bit catalog versions are required")
    normalized_current = current_version.strip().removeprefix("v")
    normalized_previous = previous_version.strip().removeprefix("v")
    resolved_current = normalized_current or available_versions[-1]
    if resolved_current not in available_versions:
        raise ValueError(f"Fluent Bit catalog version '{resolved_current}' is not available")

    earlier_versions = [
        version
        for version in available_versions
        if semantic_version_key(version) < semantic_version_key(resolved_current)
    ]
    resolved_previous = normalized_previous or (earlier_versions[-1] if earlier_versions else "")
    if resolved_previous not in available_versions:
        raise ValueError(
            f"Previous Fluent Bit catalog version '{resolved_previous or 'none'}' is not available"
        )
    if semantic_version_key(resolved_previous) >= semantic_version_key(resolved_current):
        raise ValueError("Previous Fluent Bit version must be earlier than the current version")
    return resolved_current, resolved_previous


def resolve_online_previous_version(
    available_versions: list[str],
    *,
    current_version: str,
    previous_version: str = "",
) -> str:
    """Resolve the retained local baseline for an online target version.

    Parameters
    ----------
    available_versions:
        Semantically sortable versions available in the local catalog tree.
    current_version:
        Resolved upstream documentation version.
    previous_version:
        Optional explicitly requested local baseline.

    """
    normalized_previous = previous_version.strip().removeprefix("v")
    if normalized_previous:
        if normalized_previous not in available_versions:
            raise ValueError(
                f"Previous Fluent Bit catalog version '{normalized_previous}' is not available"
            )
        if semantic_version_key(normalized_previous) >= semantic_version_key(current_version):
            raise ValueError("Previous Fluent Bit version must be earlier than the online version")
        return normalized_previous

    earlier_versions = [
        version
        for version in available_versions
        if semantic_version_key(version) < semantic_version_key(current_version)
    ]
    if not earlier_versions:
        raise ValueError(
            f"No retained local Fluent Bit catalog predates online version '{current_version}'"
        )
    return earlier_versions[-1]


def semantic_version_key(version: str) -> tuple[int, ...]:
    """Return a numeric sorting key for a dotted Fluent Bit version.

    Parameters
    ----------
    version:
        Dotted numeric version string, optionally prefixed with ``v``.

    """
    normalized_version = version.strip().removeprefix("v")
    if not _is_semantic_version(normalized_version):
        raise ValueError(f"Unsupported Fluent Bit version '{version}'")
    return tuple(int(version_part) for version_part in normalized_version.split("."))


def load_catalog_plugins(catalog_root: Path, version: str) -> dict[tuple[str, str], dict[str, Any]]:
    """Load plugin identities and field names from one composite catalog version.

    Parameters
    ----------
    catalog_root:
        Canonical directory containing versioned Fluent Bit catalogs.
    version:
        Version directory to assemble from its composite manifests.

    """
    version_root = catalog_root / version
    plugins: dict[tuple[str, str], dict[str, Any]] = {}
    for section_name in CATALOG_SECTIONS:
        plugins.update(_load_section_plugins(version_root, section_name))
    return plugins


def load_documentation_catalog_plugins(
    catalog: Mapping[str, Any],
) -> dict[tuple[str, str], dict[str, Any]]:
    """Load comparable plugin records from an in-memory documentation catalog.

    Parameters
    ----------
    catalog:
        Catalog structure returned by the Config Service documentation scraper.

    """
    catalog_plugins = _require_mapping(catalog, KEY_PLUGINS, Path("online catalog"))
    plugins: dict[tuple[str, str], dict[str, Any]] = {}
    for section_name in CATALOG_SECTIONS:
        section_plugins = _require_mapping(
            catalog_plugins,
            section_name,
            Path("online catalog/plugins"),
        )
        for plugin_name, plugin_value in section_plugins.items():
            if not isinstance(plugin_value, Mapping):
                raise ValueError(f"Online plugin must be an object: {section_name}/{plugin_name}")
            fields = plugin_value.get(KEY_FIELDS)
            if not isinstance(fields, list):
                raise ValueError(
                    f"Online plugin fields must be a list: {section_name}/{plugin_name}"
                )
            plugin_key = (section_name, str(plugin_name))
            plugin_path = Path(f"online catalog/{section_name}/{plugin_name}")
            plugins[plugin_key] = {
                KEY_SECTION: section_name,
                KEY_PLUGIN: str(plugin_name),
                KEY_TITLE: str(plugin_value.get(KEY_TITLE, plugin_name)),
                KEY_ATTRIBUTES: [_field_name(field, plugin_path) for field in fields],
            }
    return plugins


def _load_section_plugins(
    version_root: Path,
    section_name: str,
) -> dict[tuple[str, str], dict[str, Any]]:
    """Load every plugin referenced by one section manifest.

    Parameters
    ----------
    version_root:
        Catalog version directory containing the section manifest and shards.
    section_name:
        Input, filter, or output section name being assembled.

    """
    manifest_path = version_root / f"{section_name}.json"
    manifest = _load_json_object(manifest_path)
    artifact_manifest = _require_mapping(manifest, KEY_ARTIFACT_MANIFEST, manifest_path)
    parts = artifact_manifest.get(KEY_PARTS)
    if not isinstance(parts, list):
        raise ValueError(f"Catalog manifest has no parts list: {manifest_path}")
    plugins: dict[tuple[str, str], dict[str, Any]] = {}
    for part in parts:
        if not isinstance(part, Mapping):
            raise ValueError(f"Catalog manifest contains an invalid part: {manifest_path}")
        plugin_name = _decode_json_pointer(str(part.get(KEY_POINTER, "")))
        relative_file = str(part.get(KEY_FILE, ""))
        if not plugin_name or not relative_file:
            raise ValueError(f"Catalog manifest part is incomplete: {manifest_path}")
        plugin_path = version_root / relative_file
        plugin_payload = _load_json_object(plugin_path)
        fields = plugin_payload.get(KEY_FIELDS)
        if not isinstance(fields, list):
            raise ValueError(f"Plugin fields must be a list: {plugin_path}")
        plugin_key = (section_name, plugin_name)
        plugins[plugin_key] = {
            KEY_SECTION: section_name,
            KEY_PLUGIN: plugin_name,
            KEY_TITLE: str(plugin_payload.get(KEY_TITLE, plugin_name)),
            KEY_ATTRIBUTES: [_field_name(field, plugin_path) for field in fields],
        }
    return plugins


def _collect_additions(
    current_plugins: Mapping[tuple[str, str], Mapping[str, Any]],
    previous_plugins: Mapping[tuple[str, str], Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, Any]]]:
    """Separate new plugins from new fields on retained plugins.

    Parameters
    ----------
    current_plugins:
        Plugin records loaded from the current catalog.
    previous_plugins:
        Plugin records loaded from the baseline catalog.

    """
    new_plugins: list[dict[str, Any]] = []
    new_attributes: list[dict[str, str]] = []
    representation_changes: list[dict[str, Any]] = []
    for plugin_key in sorted(current_plugins):
        current_plugin = current_plugins[plugin_key]
        previous_plugin = previous_plugins.get(plugin_key)
        if previous_plugin is None:
            new_plugins.append(
                {
                    KEY_SECTION: current_plugin[KEY_SECTION],
                    KEY_PLUGIN: current_plugin[KEY_PLUGIN],
                    KEY_TITLE: current_plugin[KEY_TITLE],
                    KEY_ATTRIBUTES: sorted(current_plugin[KEY_ATTRIBUTES]),
                }
            )
            continue
        previous_attributes = set(previous_plugin[KEY_ATTRIBUTES])
        added_attributes = sorted(set(current_plugin[KEY_ATTRIBUTES]) - previous_attributes)
        for attribute_name in added_attributes:
            representation_change = _find_representation_change(
                attribute_name,
                previous_attributes,
            )
            if representation_change is not None:
                representation_changes.append(
                    {
                        KEY_SECTION: str(current_plugin[KEY_SECTION]),
                        KEY_PLUGIN: str(current_plugin[KEY_PLUGIN]),
                        KEY_TITLE: str(current_plugin[KEY_TITLE]),
                        KEY_ATTRIBUTE: attribute_name,
                        **representation_change,
                    }
                )
                continue
            new_attributes.append(
                {
                    KEY_SECTION: str(current_plugin[KEY_SECTION]),
                    KEY_PLUGIN: str(current_plugin[KEY_PLUGIN]),
                    KEY_TITLE: str(current_plugin[KEY_TITLE]),
                    KEY_ATTRIBUTE: attribute_name,
                }
            )
    return new_plugins, new_attributes, representation_changes


def _find_representation_change(
    current_attribute: str,
    previous_attributes: set[str],
) -> dict[str, Any] | None:
    """Describe placeholder/concrete field changes that are not safe additions.

    Parameters
    ----------
    current_attribute:
        Field name present only in the current local plugin record.
    previous_attributes:
        Field names retained for the corresponding previous plugin record.

    """
    if _contains_placeholder(current_attribute):
        covered_attributes = sorted(
            attribute
            for attribute in previous_attributes
            if _placeholder_matches(current_attribute, attribute)
        )
        if covered_attributes:
            return {
                KEY_REASON: REASON_CURRENT_WILDCARD,
                KEY_PREVIOUS_ATTRIBUTES: covered_attributes,
            }
    covering_attributes = sorted(
        attribute
        for attribute in previous_attributes
        if _contains_placeholder(attribute) and _placeholder_matches(attribute, current_attribute)
    )
    if covering_attributes:
        return {
            KEY_REASON: REASON_PREVIOUS_WILDCARD,
            KEY_PREVIOUS_ATTRIBUTES: covering_attributes,
        }
    return None


def _contains_placeholder(attribute_name: str) -> bool:
    """Return whether an attribute contains a brace-delimited placeholder.

    Parameters
    ----------
    attribute_name:
        Catalog field name that might represent a family of concrete fields.

    """
    return re.search(r"\{[^{}]+\}", attribute_name) is not None


def _placeholder_matches(pattern: str, attribute_name: str) -> bool:
    """Return whether a placeholder field pattern covers a concrete field name.

    Parameters
    ----------
    pattern:
        Field name containing one or more brace-delimited placeholders.
    attribute_name:
        Concrete or alternative catalog field name tested against the pattern.

    """
    escaped_pattern = re.escape(pattern)
    wildcard_pattern = re.sub(r"\\\{[^{}]+\\\}", ".+", escaped_pattern)
    return re.fullmatch(wildcard_pattern, attribute_name) is not None


def write_change_reports(report: Mapping[str, Any], output_directory: Path) -> tuple[Path, Path]:
    """Write JSON and Markdown versions of one catalog additions report.

    Parameters
    ----------
    report:
        Structured report returned by :func:`compare_fluentbit_catalogs`.
    output_directory:
        Directory that receives deterministic report filenames.

    """
    output_directory.mkdir(parents=True, exist_ok=True)
    current_token = str(report[KEY_CURRENT_VERSION]).replace(".", "_")
    previous_token = str(report[KEY_PREVIOUS_VERSION]).replace(".", "_")
    report_stem = f"fluentbit_{current_token}_vs_{previous_token}_additions"
    json_path = output_directory / f"{report_stem}.json"
    markdown_path = output_directory / f"{report_stem}.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_change_report_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def render_change_report_markdown(report: Mapping[str, Any]) -> str:
    """Render one structured catalog additions report as Markdown.

    Parameters
    ----------
    report:
        Structured report returned by :func:`compare_fluentbit_catalogs`.

    """
    counts = _require_mapping(report, KEY_COUNTS, Path("report"))
    lines = [
        (
            f"# Fluent Bit {report[KEY_CURRENT_VERSION]} additions since "
            f"{report[KEY_PREVIOUS_VERSION]}"
        ),
        "",
        str(report[KEY_SCOPE_NOTE]),
        "",
        "## Comparison sources",
        "",
        f"- Current catalog: {report[KEY_CURRENT_SOURCE]}",
        f"- Previous catalog: {report[KEY_PREVIOUS_SOURCE]}",
    ]
    if report.get(KEY_DOCUMENTATION_SOURCE):
        lines.append(f"- Documentation source selection: `{report[KEY_DOCUMENTATION_SOURCE]}`")
    lines.extend(
        [
            "",
            "## Counts",
            "",
            f"- New plugins: {counts[KEY_NEW_PLUGIN_COUNT]}",
            f"- New attributes on existing plugins: {counts[KEY_NEW_ATTRIBUTE_COUNT]}",
            f"- Catalog representation changes: {counts[KEY_REPRESENTATION_CHANGE_COUNT]}",
            "",
            "## New plugins",
            "",
        ]
    )
    new_plugins = report[KEY_NEW_PLUGINS]
    if new_plugins:
        lines.extend(["| Section | Plugin | Title | Attributes |", "| --- | --- | --- | ---: |"])
        for plugin in new_plugins:
            lines.append(
                f"| `{plugin[KEY_SECTION]}` | `{plugin[KEY_PLUGIN]}` | "
                f"{plugin[KEY_TITLE]} | {len(plugin[KEY_ATTRIBUTES])} |"
            )
    else:
        lines.append("No new plugins were identified.")
    lines.extend(["", "## New attributes on existing plugins", ""])
    new_attributes = report[KEY_NEW_ATTRIBUTES]
    if new_attributes:
        lines.extend(["| Section | Plugin | Title | Attribute |", "| --- | --- | --- | --- |"])
        for attribute in new_attributes:
            lines.append(
                f"| `{attribute[KEY_SECTION]}` | `{attribute[KEY_PLUGIN]}` | "
                f"{attribute[KEY_TITLE]} | `{attribute[KEY_ATTRIBUTE]}` |"
            )
    else:
        lines.append("No new attributes on existing plugins were identified.")
    lines.extend(["", "## Catalog representation changes", ""])
    representation_changes = report[KEY_REPRESENTATION_CHANGES]
    if representation_changes:
        lines.extend(
            [
                "| Section | Plugin | Current attribute | Reason | Previous matches |",
                "| --- | --- | --- | --- | ---: |",
            ]
        )
        for change in representation_changes:
            lines.append(
                f"| `{change[KEY_SECTION]}` | `{change[KEY_PLUGIN]}` | "
                f"`{change[KEY_ATTRIBUTE]}` | `{change[KEY_REASON]}` | "
                f"{len(change[KEY_PREVIOUS_ATTRIBUTES])} |"
            )
    else:
        lines.append("No wildcard/concrete representation changes were identified.")
    return "\n".join(lines) + "\n"


def _print_report_summary(runtime: Any, report: Mapping[str, Any]) -> None:
    """Print report counts and every identified addition.

    Parameters
    ----------
    runtime:
        Command runtime used for console output.
    report:
        Structured catalog additions report.

    """
    counts = report[KEY_COUNTS]
    runtime.info(
        f"Fluent Bit additions {report[KEY_PREVIOUS_VERSION]} -> {report[KEY_CURRENT_VERSION]}: "
        f"{counts[KEY_NEW_PLUGIN_COUNT]} new plugin(s), "
        f"{counts[KEY_NEW_ATTRIBUTE_COUNT]} new attribute(s) on existing plugins, "
        f"{counts[KEY_REPRESENTATION_CHANGE_COUNT]} representation change(s)"
    )
    for plugin in report[KEY_NEW_PLUGINS]:
        runtime.info(
            f"NEW PLUGIN {plugin[KEY_SECTION]}/{plugin[KEY_PLUGIN]} "
            f"({len(plugin[KEY_ATTRIBUTES])} attributes)"
        )
    for attribute in report[KEY_NEW_ATTRIBUTES]:
        runtime.info(
            f"NEW ATTRIBUTE {attribute[KEY_SECTION]}/{attribute[KEY_PLUGIN]}/"
            f"{attribute[KEY_ATTRIBUTE]}"
        )
    for change in report[KEY_REPRESENTATION_CHANGES]:
        runtime.info(
            f"REPRESENTATION CHANGE {change[KEY_SECTION]}/{change[KEY_PLUGIN]}/"
            f"{change[KEY_ATTRIBUTE]} ({change[KEY_REASON]})"
        )


def _resolve_output_directory(repo_root: Path, output_dir: str) -> Path:
    """Resolve a configured report directory against the repository root.

    Parameters
    ----------
    repo_root:
        Repository root used for the default and relative paths.
    output_dir:
        Optional absolute or repository-relative report directory.

    """
    configured_path = (
        Path(output_dir).expanduser() if output_dir.strip() else DEFAULT_REPORT_RELATIVE_PATH
    )
    if not configured_path.is_absolute():
        configured_path = repo_root / configured_path
    return configured_path.resolve()


def _load_json_object(path: Path) -> dict[str, Any]:
    """Load a JSON object from a catalog file.

    Parameters
    ----------
    path:
        JSON file expected to contain an object at its root.

    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Catalog JSON root must be an object: {path}")
    return payload


def _require_mapping(payload: Mapping[str, Any], key: str, path: Path) -> Mapping[str, Any]:
    """Return a required mapping value from a structured payload.

    Parameters
    ----------
    payload:
        Object containing the required key.
    key:
        Named key whose value must be a mapping.
    path:
        Source path included in validation errors.

    """
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"Expected object '{key}' in {path}")
    return value


def _field_name(field: Any, plugin_path: Path) -> str:
    """Return a validated field name from one plugin field record.

    Parameters
    ----------
    field:
        Field record loaded from a plugin catalog shard.
    plugin_path:
        Plugin file included in validation errors.

    """
    if not isinstance(field, Mapping) or not str(field.get(KEY_NAME, "")).strip():
        raise ValueError(f"Plugin contains an unnamed field: {plugin_path}")
    return str(field[KEY_NAME]).strip()


def _decode_json_pointer(pointer: str) -> str:
    """Decode a single-token JSON pointer used as the plugin identity.

    Parameters
    ----------
    pointer:
        Manifest pointer such as ``/kafka``.

    """
    return pointer.removeprefix("/").replace("~1", "/").replace("~0", "~")


def _is_semantic_version(version: str) -> bool:
    """Return whether text contains only dotted numeric version segments.

    Parameters
    ----------
    version:
        Candidate Fluent Bit version directory name.

    """
    return re.fullmatch(r"\d+(?:\.\d+)*", version) is not None
