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

"""Reconcile scraped Fluent Bit catalogs with an earlier local catalog.

The documentation scraper can only describe values present in a consistently
formatted documentation table. This module preserves trustworthy scraped
values, fills genuinely undetermined metadata from an earlier catalog, and
builds a review report for every fallback or divergence.
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

CATALOG_SECTIONS = ("inputs", "filters", "outputs")
EXPECTED_TABLE_HEADERS = {"key", "description"}
FIELD_ATTRIBUTE_KEYS = (
    "required",
    "description",
    "data_type",
    "validation_rule",
    "default",
    "enum_options",
    "references_parser",
)
PLUGIN_ATTRIBUTE_KEYS = ("title", "description")
INCOMPLETE_EXTRACTION_STATUS = "no_configuration_parameters"
OK_EXTRACTION_STATUS = "ok"
REVIEW_COMMENT = (
    "REVIEW REQUIRED: The documentation page did not expose the expected configuration "
    "parameter table. Fields from the previous catalog were retained where available; "
    "verify the page reference and table section before accepting this catalog."
)
SUMMARY_FORMAT = "config-service.fluentbit-scrape-summary/v1"

KEY_ADDED_FIELDS = "added_fields"
KEY_ADDED_PLUGINS = "added_plugins"
KEY_ATTRIBUTE = "attribute"
KEY_CARRIED_FORWARD = "carried_forward"
KEY_COUNTS = "counts"
KEY_CURRENT = "current"
KEY_DATA_TYPE = "data_type"
KEY_DEFAULT = "default"
KEY_DESCRIPTION = "description"
KEY_DIVERGENCES = "divergences"
KEY_DOC_URL = "doc_url"
KEY_ENUM_OPTIONS = "enum_options"
KEY_EXTRACTION = "extraction"
KEY_FIELD = "field"
KEY_FIELDS = "fields"
KEY_FLUENT_BIT_VERSION = "fluent_bit_version"
KEY_FORMAT = "format"
KEY_GENERATED_AT = "generated_at"
KEY_INCOMPLETE_PAGES = "incomplete_pages"
KEY_KIND = "kind"
KEY_NAME = "name"
KEY_PLUGINS = "plugins"
KEY_PLUGIN = "plugin"
KEY_PREVIOUS = "previous"
KEY_PREVIOUS_VERSION = "previous_version"
KEY_REASON = "reason"
KEY_REFERENCE = "reference"
KEY_REFERENCES_PARSER = "references_parser"
KEY_REQUIRED = "required"
KEY_REVIEW_COMMENT = "review_comment"
KEY_REVIEW_REQUIRED = "review_required"
KEY_SECTION = "section"
KEY_STATUS = "status"
KEY_TABLE_HEADER = "table_header"
KEY_TARGET_VERSION = "target_version"
KEY_TITLE = "title"
KEY_VALIDATION_RULE = "validation_rule"
KEY_VALUE = "value"

KIND_FIELD_ADDED = "field_added"
KIND_FIELD_ATTRIBUTE_CHANGED = "field_attribute_changed"
KIND_FIELD_NOT_DOCUMENTED = "field_not_documented"
KIND_PLUGIN_ADDED = "plugin_added"
KIND_PLUGIN_ATTRIBUTE_CHANGED = "plugin_attribute_changed"
KIND_PLUGIN_NOT_DOCUMENTED = "plugin_not_documented"
REASON_INCOMPLETE_PAGE = "incomplete_page"
REASON_MISSING_ATTRIBUTE = "missing_attribute"
REASON_REQUIRED_COLUMN_MISSING = "required_column_missing"
REASON_WEAK_TYPE_INFERENCE = "weak_type_inference"

_MISSING = object()


def semantic_version_key(version: str) -> tuple[int, ...]:
    """Return a numeric comparison key for one dotted Fluent Bit version.

    Parameters
    ----------
    version:
        Version text such as ``5.0.4``. A leading ``v`` is accepted.

    Raises
    ------
    ValueError
        Raised when the version does not contain only numeric dotted segments.
    """
    normalized_version = str(version).strip().removeprefix("v")
    if not re.fullmatch(r"\d+(?:\.\d+)*", normalized_version):
        raise ValueError(f"Unsupported Fluent Bit version '{version}'")
    return tuple(int(version_part) for version_part in normalized_version.split("."))


def select_previous_version(target_version: str, available_versions: Iterable[str]) -> str | None:
    """Select the greatest available semantic version below the target.

    Parameters
    ----------
    target_version:
        Version being generated.
    available_versions:
        Locally available versions that might provide fallback metadata.

    Returns
    -------
    str or None
        The nearest earlier version, or ``None`` when none is suitable.
    """
    target_key = semantic_version_key(target_version)
    earlier_versions = [
        candidate_version
        for candidate_version in available_versions
        if semantic_version_key(candidate_version) < target_key
    ]
    if not earlier_versions:
        return None
    return max(earlier_versions, key=semantic_version_key)


def reconcile_catalogs(
    current_catalog: Mapping[str, Any],
    previous_catalog: Mapping[str, Any] | None,
    *,
    previous_version: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Merge undetermined scraped metadata and return a structured review summary.

    Parameters
    ----------
    current_catalog:
        Newly scraped Fluent Bit catalog. This mapping is not mutated.
    previous_catalog:
        Earlier assembled catalog used as a fallback, or ``None``.
    previous_version:
        Version label for the earlier catalog, or ``None``.

    Returns
    -------
    tuple[dict, dict]
        Reconciled catalog followed by its machine-readable summary.
    """
    reconciled_catalog = copy.deepcopy(dict(current_catalog))
    summary = _new_summary(reconciled_catalog, previous_version)
    current_plugins = reconciled_catalog.setdefault(KEY_PLUGINS, {})
    previous_plugins = (previous_catalog or {}).get(KEY_PLUGINS, {})
    baseline_available = previous_catalog is not None

    for section_name in CATALOG_SECTIONS:
        current_section = _mapping_value(current_plugins, section_name)
        previous_section = _mapping_value(previous_plugins, section_name)
        _reconcile_section(
            current_section,
            previous_section,
            section_name=section_name,
            previous_version=previous_version,
            baseline_available=baseline_available,
            summary=summary,
        )

    _finalize_counts(summary)
    return reconciled_catalog, summary


def write_summary_files(
    summary: Mapping[str, Any],
    output_directory: Path,
    *,
    target_version: str,
) -> tuple[Path, Path]:
    """Write JSON and Markdown copies of one scrape reconciliation summary.

    Parameters
    ----------
    summary:
        Structured summary returned by :func:`reconcile_catalogs`.
    output_directory:
        Directory that receives the generated report files.
    target_version:
        Fluent Bit version used to make deterministic snake-case filenames.

    Returns
    -------
    tuple[Path, Path]
        JSON summary path followed by Markdown summary path.
    """
    output_directory.mkdir(parents=True, exist_ok=True)
    version_token = re.sub(r"[^a-z0-9]+", "_", target_version.lower()).strip("_")
    filename_stem = f"fluentbit_{version_token}_scrape_summary"
    json_path = output_directory / f"{filename_stem}.json"
    markdown_path = output_directory / f"{filename_stem}.md"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_summary_markdown(summary), encoding="utf-8")
    return json_path, markdown_path


def render_summary_markdown(summary: Mapping[str, Any]) -> str:
    """Render a structured scrape summary as a human-readable Markdown report.

    Parameters
    ----------
    summary:
        Structured summary returned by :func:`reconcile_catalogs`.

    Returns
    -------
    str
        Markdown report ending with a newline.
    """
    target_version = summary.get(KEY_TARGET_VERSION) or "unknown"
    previous_version = summary.get(KEY_PREVIOUS_VERSION) or "none"
    lines = [
        f"# Fluent Bit {target_version} scrape summary",
        "",
        f"Previous catalog: `{previous_version}`",
        "",
        "## Counts",
        "",
    ]
    counts = _mapping_value(summary, KEY_COUNTS)
    if counts:
        for count_name, count_value in sorted(counts.items()):
            lines.append(f"- {count_name.replace('_', ' ')}: {count_value}")
    else:
        lines.append("- No reportable changes.")

    lines.extend(["", "## Pages requiring review", ""])
    incomplete_pages = _list_value(summary, KEY_INCOMPLETE_PAGES)
    if incomplete_pages:
        for page in incomplete_pages:
            lines.append(
                f"- `{page.get(KEY_SECTION)}/{page.get(KEY_PLUGIN)}`: "
                f"{page.get(KEY_STATUS)} — {page.get(KEY_REFERENCE) or 'no reference'}"
            )
    else:
        lines.append("No incomplete or structurally unexpected pages were detected.")

    lines.extend(["", "## Values carried forward", ""])
    carried_forward = _list_value(summary, KEY_CARRIED_FORWARD)
    if carried_forward:
        lines.extend(_render_change_table(carried_forward, include_previous=False))
    else:
        lines.append("No values were carried forward.")

    lines.extend(["", "## Divergences", ""])
    divergences = _list_value(summary, KEY_DIVERGENCES)
    if divergences:
        lines.extend(_render_change_table(divergences, include_previous=True))
    else:
        lines.append("No divergences from the previous catalog were detected.")
    lines.append("")
    return "\n".join(lines)


def _new_summary(
    current_catalog: Mapping[str, Any],
    previous_version: str | None,
) -> dict[str, Any]:
    """Create the stable top-level structure used by scrape summaries."""
    return {
        KEY_FORMAT: SUMMARY_FORMAT,
        KEY_TARGET_VERSION: current_catalog.get(KEY_FLUENT_BIT_VERSION),
        KEY_PREVIOUS_VERSION: previous_version,
        KEY_GENERATED_AT: current_catalog.get(KEY_GENERATED_AT),
        KEY_INCOMPLETE_PAGES: [],
        KEY_CARRIED_FORWARD: [],
        KEY_DIVERGENCES: [],
        KEY_COUNTS: {},
    }


# Section reconciliation passes explicit baseline state and report context.
# pylint: disable=too-many-arguments
def _reconcile_section(
    current_section: dict[str, Any],
    previous_section: Mapping[str, Any],
    *,
    section_name: str,
    previous_version: str | None,
    baseline_available: bool,
    summary: dict[str, Any],
) -> None:
    """Reconcile every plugin in one input, filter, or output section."""
    for plugin_name, current_plugin_value in sorted(current_section.items()):
        if not isinstance(current_plugin_value, dict):
            continue
        previous_plugin_value = previous_section.get(plugin_name)
        if not isinstance(previous_plugin_value, Mapping):
            _mark_incomplete_page(
                current_plugin_value,
                section_name=section_name,
                plugin_name=plugin_name,
                summary=summary,
            )
            if baseline_available:
                _append_divergence(
                    summary,
                    kind=KIND_PLUGIN_ADDED,
                    section_name=section_name,
                    plugin_name=plugin_name,
                    current_value=current_plugin_value.get(KEY_TITLE),
                )
            continue
        _reconcile_plugin(
            current_plugin_value,
            previous_plugin_value,
            section_name=section_name,
            plugin_name=plugin_name,
            previous_version=previous_version,
            summary=summary,
        )

    for plugin_name, previous_plugin_value in sorted(previous_section.items()):
        if plugin_name in current_section or not isinstance(previous_plugin_value, Mapping):
            continue
        _append_divergence(
            summary,
            kind=KIND_PLUGIN_NOT_DOCUMENTED,
            section_name=section_name,
            plugin_name=plugin_name,
            previous_value=previous_plugin_value.get(KEY_TITLE),
        )


# These internal parameters keep report location and comparison state explicit at each call site.
# pylint: disable=too-many-arguments,too-many-locals
def _reconcile_plugin(
    current_plugin: dict[str, Any],
    previous_plugin: Mapping[str, Any],
    *,
    section_name: str,
    plugin_name: str,
    previous_version: str | None,
    summary: dict[str, Any],
) -> None:
    """Reconcile one plugin and record page, field, and metadata findings."""
    for attribute_name in PLUGIN_ATTRIBUTE_KEYS:
        current_value = current_plugin.get(attribute_name, _MISSING)
        previous_value = previous_plugin.get(attribute_name, _MISSING)
        if (
            _has_value(current_value)
            and _has_value(previous_value)
            and current_value != previous_value
        ):
            _append_divergence(
                summary,
                kind=KIND_PLUGIN_ATTRIBUTE_CHANGED,
                section_name=section_name,
                plugin_name=plugin_name,
                attribute_name=attribute_name,
                previous_value=previous_value,
                current_value=current_value,
            )

    page_is_incomplete = _mark_incomplete_page(
        current_plugin,
        section_name=section_name,
        plugin_name=plugin_name,
        summary=summary,
    )
    extraction = current_plugin[KEY_EXTRACTION]

    current_fields = _field_map(current_plugin.get(KEY_FIELDS))
    previous_fields = _field_map(previous_plugin.get(KEY_FIELDS))
    reconciled_fields: list[dict[str, Any]] = []
    for field_name, current_field in current_fields.items():
        previous_field = previous_fields.get(field_name)
        if previous_field is None:
            reconciled_fields.append(current_field)
            _append_divergence(
                summary,
                kind=KIND_FIELD_ADDED,
                section_name=section_name,
                plugin_name=plugin_name,
                field_name=field_name,
                current_value=current_field,
            )
            continue
        _reconcile_field(
            current_field,
            previous_field,
            extraction=extraction,
            section_name=section_name,
            plugin_name=plugin_name,
            field_name=field_name,
            previous_version=previous_version,
            summary=summary,
        )
        reconciled_fields.append(current_field)

    for field_name, previous_field in previous_fields.items():
        if field_name in current_fields:
            continue
        if page_is_incomplete:
            reconciled_fields.append(copy.deepcopy(previous_field))
            _append_carry_forward(
                summary,
                section_name=section_name,
                plugin_name=plugin_name,
                field_name=field_name,
                attribute_name=KEY_FIELDS,
                value=previous_field,
                previous_version=previous_version,
                reason=REASON_INCOMPLETE_PAGE,
            )
        else:
            _append_divergence(
                summary,
                kind=KIND_FIELD_NOT_DOCUMENTED,
                section_name=section_name,
                plugin_name=plugin_name,
                field_name=field_name,
                previous_value=previous_field,
            )
    current_plugin[KEY_FIELDS] = reconciled_fields


def _mark_incomplete_page(
    current_plugin: dict[str, Any],
    *,
    section_name: str,
    plugin_name: str,
    summary: dict[str, Any],
) -> bool:
    """Annotate and report one page when its extraction metadata is unreliable."""
    extraction = current_plugin.setdefault(KEY_EXTRACTION, {})
    if not isinstance(extraction, dict):
        extraction = {}
        current_plugin[KEY_EXTRACTION] = extraction
    if not _page_is_incomplete(extraction):
        return False
    extraction[KEY_REVIEW_REQUIRED] = True
    extraction[KEY_REVIEW_COMMENT] = REVIEW_COMMENT
    _list_value(summary, KEY_INCOMPLETE_PAGES).append(
        {
            KEY_SECTION: section_name,
            KEY_PLUGIN: plugin_name,
            KEY_STATUS: extraction.get(KEY_STATUS, INCOMPLETE_EXTRACTION_STATUS),
            KEY_REFERENCE: extraction.get(KEY_REFERENCE) or current_plugin.get(KEY_DOC_URL),
            KEY_REVIEW_COMMENT: REVIEW_COMMENT,
        }
    )
    return True


# These internal parameters keep report location and comparison state explicit at each call site.
# pylint: disable=too-many-arguments
def _reconcile_field(
    current_field: dict[str, Any],
    previous_field: Mapping[str, Any],
    *,
    extraction: Mapping[str, Any],
    section_name: str,
    plugin_name: str,
    field_name: str,
    previous_version: str | None,
    summary: dict[str, Any],
) -> None:
    """Fill undetermined field metadata and report explicit value changes."""
    for attribute_name in FIELD_ATTRIBUTE_KEYS:
        current_value = current_field.get(attribute_name, _MISSING)
        previous_value = previous_field.get(attribute_name, _MISSING)
        fallback_reason = _fallback_reason(
            attribute_name,
            current_value,
            previous_value,
            current_field=current_field,
            extraction=extraction,
        )
        if fallback_reason and _has_value(previous_value):
            current_field[attribute_name] = copy.deepcopy(previous_value)
            _append_carry_forward(
                summary,
                section_name=section_name,
                plugin_name=plugin_name,
                field_name=field_name,
                attribute_name=attribute_name,
                value=previous_value,
                previous_version=previous_version,
                reason=fallback_reason,
            )
            continue
        if (
            _has_value(current_value)
            and _has_value(previous_value)
            and current_value != previous_value
        ):
            _append_divergence(
                summary,
                kind=KIND_FIELD_ATTRIBUTE_CHANGED,
                section_name=section_name,
                plugin_name=plugin_name,
                field_name=field_name,
                attribute_name=attribute_name,
                previous_value=previous_value,
                current_value=current_value,
            )


def _fallback_reason(
    attribute_name: str,
    current_value: Any,
    previous_value: Any,
    *,
    current_field: Mapping[str, Any],
    extraction: Mapping[str, Any],
) -> str | None:
    """Explain why a current attribute is too weak to replace an earlier value."""
    if not _has_value(current_value):
        return REASON_MISSING_ATTRIBUTE
    if attribute_name == KEY_REQUIRED and not _header_present(extraction, KEY_REQUIRED):
        return REASON_REQUIRED_COLUMN_MISSING
    if (
        attribute_name == KEY_DATA_TYPE
        and current_value == "string"
        and previous_value != "string"
        and not _has_value(current_field.get(KEY_DEFAULT, _MISSING))
        and not _has_value(current_field.get(KEY_VALIDATION_RULE, _MISSING))
    ):
        return REASON_WEAK_TYPE_INFERENCE
    return None


def _page_is_incomplete(extraction: Mapping[str, Any]) -> bool:
    """Return whether extraction metadata indicates an unexpected page shape."""
    if extraction.get(KEY_STATUS) != OK_EXTRACTION_STATUS:
        return True
    normalized_headers = {
        str(header_value).strip().lower()
        for header_value in extraction.get(KEY_TABLE_HEADER, [])
    }
    return not EXPECTED_TABLE_HEADERS.issubset(normalized_headers)


def _header_present(extraction: Mapping[str, Any], header_name: str) -> bool:
    """Return whether a normalized documentation table header is present."""
    return header_name.lower() in {
        str(header_value).strip().lower()
        for header_value in extraction.get(KEY_TABLE_HEADER, [])
    }


def _field_map(fields_value: Any) -> dict[str, dict[str, Any]]:
    """Convert a catalog field list into an ordered name-to-field mapping."""
    field_mapping: dict[str, dict[str, Any]] = {}
    if not isinstance(fields_value, list):
        return field_mapping
    for field_value in fields_value:
        if not isinstance(field_value, dict):
            continue
        field_name = str(field_value.get(KEY_NAME) or "").strip()
        if field_name:
            field_mapping[field_name] = copy.deepcopy(field_value)
    return field_mapping


def _mapping_value(payload: Any, key_name: str) -> dict[str, Any]:
    """Return a mutable mapping value, substituting an empty mapping when absent."""
    if not isinstance(payload, Mapping):
        return {}
    value = payload.get(key_name, {})
    if isinstance(value, dict):
        return value
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _list_value(payload: Mapping[str, Any], key_name: str) -> list[dict[str, Any]]:
    """Return a summary list while keeping type handling localized."""
    value = payload.get(key_name, [])
    return value if isinstance(value, list) else []


def _has_value(value: Any) -> bool:
    """Return whether a scraped value carries usable information."""
    return value is not _MISSING and value is not None and value != "" and value != []


# Report records deliberately receive fully named location fields for readable call sites.
# pylint: disable=too-many-arguments
def _append_carry_forward(
    summary: dict[str, Any],
    *,
    section_name: str,
    plugin_name: str,
    field_name: str,
    attribute_name: str,
    value: Any,
    previous_version: str | None,
    reason: str,
) -> None:
    """Append one inherited value to the structured summary."""
    _list_value(summary, KEY_CARRIED_FORWARD).append(
        {
            KEY_SECTION: section_name,
            KEY_PLUGIN: plugin_name,
            KEY_FIELD: field_name,
            KEY_ATTRIBUTE: attribute_name,
            KEY_VALUE: copy.deepcopy(value),
            KEY_PREVIOUS_VERSION: previous_version,
            KEY_REASON: reason,
        }
    )


# Report records deliberately receive fully named location fields for readable call sites.
# pylint: disable=too-many-arguments
def _append_divergence(
    summary: dict[str, Any],
    *,
    kind: str,
    section_name: str,
    plugin_name: str,
    field_name: str | None = None,
    attribute_name: str | None = None,
    previous_value: Any = _MISSING,
    current_value: Any = _MISSING,
) -> None:
    """Append one difference between current documentation and prior metadata."""
    divergence: dict[str, Any] = {
        KEY_KIND: kind,
        KEY_SECTION: section_name,
        KEY_PLUGIN: plugin_name,
    }
    if field_name is not None:
        divergence[KEY_FIELD] = field_name
    if attribute_name is not None:
        divergence[KEY_ATTRIBUTE] = attribute_name
    if previous_value is not _MISSING:
        divergence[KEY_PREVIOUS] = copy.deepcopy(previous_value)
    if current_value is not _MISSING:
        divergence[KEY_CURRENT] = copy.deepcopy(current_value)
    _list_value(summary, KEY_DIVERGENCES).append(divergence)


def _finalize_counts(summary: dict[str, Any]) -> None:
    """Populate compact totals after all report entries have been collected."""
    divergences = _list_value(summary, KEY_DIVERGENCES)
    summary[KEY_COUNTS] = {
        KEY_INCOMPLETE_PAGES: len(_list_value(summary, KEY_INCOMPLETE_PAGES)),
        KEY_CARRIED_FORWARD: len(_list_value(summary, KEY_CARRIED_FORWARD)),
        KEY_DIVERGENCES: len(divergences),
        KEY_ADDED_PLUGINS: sum(
            1 for item in divergences if item.get(KEY_KIND) == KIND_PLUGIN_ADDED
        ),
        KEY_ADDED_FIELDS: sum(1 for item in divergences if item.get(KEY_KIND) == KIND_FIELD_ADDED),
    }


def _render_change_table(items: list[dict[str, Any]], *, include_previous: bool) -> list[str]:
    """Render carry-forward or divergence entries as a compact Markdown table."""
    if include_previous:
        lines = [
            "| Location | Kind/reason | Attribute | Previous | Current |",
            "| --- | --- | --- | --- | --- |",
        ]
    else:
        lines = [
            "| Location | Kind/reason | Attribute | Value |",
            "| --- | --- | --- | --- |",
        ]
    for item in items:
        location_parts = [str(item.get(KEY_SECTION) or ""), str(item.get(KEY_PLUGIN) or "")]
        if item.get(KEY_FIELD):
            location_parts.append(str(item[KEY_FIELD]))
        location = "/".join(location_parts)
        change_label = item.get(KEY_KIND) or item.get(KEY_REASON) or ""
        attribute_name = item.get(KEY_ATTRIBUTE) or ""
        if include_previous:
            lines.append(
                f"| `{_escape_markdown(location)}` | {_escape_markdown(change_label)} | "
                f"`{_escape_markdown(attribute_name)}` | "
                f"{_format_markdown_value(item.get(KEY_PREVIOUS))} | "
                f"{_format_markdown_value(item.get(KEY_CURRENT))} |"
            )
        else:
            lines.append(
                f"| `{_escape_markdown(location)}` | {_escape_markdown(change_label)} | "
                f"`{_escape_markdown(attribute_name)}` | "
                f"{_format_markdown_value(item.get(KEY_VALUE))} |"
            )
    return lines


def _format_markdown_value(value: Any) -> str:
    """Serialize and escape one report value for a Markdown table cell."""
    if value is None:
        return ""
    serialized_value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return f"`{_escape_markdown(serialized_value)}`"


def _escape_markdown(value: Any) -> str:
    """Escape table separators and line breaks in generated Markdown text."""
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")
