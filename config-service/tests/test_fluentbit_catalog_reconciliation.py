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

"""Tests for Fluent Bit scrape reconciliation and review summaries."""

# Ruff's security assertion rule does not apply to pytest test assertions.
# ruff: noqa: S101

from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# Tests load the source package after making the repository source tree importable.
# pylint: disable=wrong-import-position
from config_service.fluentbit_catalog_reconciliation import (  # noqa: E402
    KEY_ATTRIBUTE,
    KEY_CARRIED_FORWARD,
    KEY_CURRENT,
    KEY_DATA_TYPE,
    KEY_DEFAULT,
    KEY_DIVERGENCES,
    KEY_EXTRACTION,
    KEY_FIELD,
    KEY_FIELDS,
    KEY_INCOMPLETE_PAGES,
    KEY_KIND,
    KEY_NAME,
    KEY_PLUGINS,
    KEY_PREVIOUS,
    KEY_REASON,
    KEY_REQUIRED,
    KEY_REVIEW_COMMENT,
    KEY_REVIEW_REQUIRED,
    KEY_STATUS,
    KEY_TABLE_HEADER,
    KEY_VALIDATION_RULE,
    KIND_FIELD_ADDED,
    KIND_FIELD_ATTRIBUTE_CHANGED,
    KIND_FIELD_NOT_DOCUMENTED,
    KIND_PLUGIN_ADDED,
    KIND_PLUGIN_NOT_DOCUMENTED,
    REASON_INCOMPLETE_PAGE,
    REASON_REQUIRED_COLUMN_MISSING,
    REVIEW_COMMENT,
    reconcile_catalogs,
    render_summary_markdown,
    select_previous_version,
    semantic_version_key,
    write_summary_files,
)

KEY_DESCRIPTION = "description"
KEY_DOC_URL = "doc_url"
KEY_FLUENT_BIT_VERSION = "fluent_bit_version"
KEY_GENERATED_AT = "generated_at"
KEY_INPUTS = "inputs"
KEY_KIND_VALUE = "kind"
KEY_MAXIMUM = "max"
KEY_MINIMUM = "min"
KEY_FILTERS = "filters"
KEY_OUTPUTS = "outputs"
KEY_REFERENCE = "reference"
KEY_TITLE = "title"
STATUS_OK = "ok"
STATUS_NO_PARAMETERS = "no_configuration_parameters"
PLUGIN_NEW = "new_plugin"
PLUGIN_INVALID = "invalid_plugin"
PLUGIN_RETIRED = "retired_plugin"
PLUGIN_SAMPLE = "sample"


def _field(
    name: str,
    *,
    default: Any = None,
    data_type: str = "string",
    required: bool = False,
    validation_rule: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a complete field fixture with optional typed metadata."""
    payload = {
        KEY_NAME: name,
        KEY_REQUIRED: required,
        KEY_DESCRIPTION: f"Description for {name}",
        KEY_REFERENCE: "https://example.test/plugin#configuration-parameters",
        KEY_DATA_TYPE: data_type,
        KEY_VALIDATION_RULE: validation_rule,
    }
    if default is not None:
        payload[KEY_DEFAULT] = default
    return payload


def _catalog(
    version: str,
    fields: list[dict[str, Any]],
    *,
    status: str = STATUS_OK,
    table_header: list[str] | None = None,
) -> dict[str, Any]:
    """Build a minimal catalog fixture containing one input plugin."""
    headers = table_header if table_header is not None else ["Key", "Description", "Default"]
    return {
        KEY_FLUENT_BIT_VERSION: version,
        KEY_GENERATED_AT: "2026-10-09T00:00:00Z",
        KEY_PLUGINS: {
            KEY_INPUTS: {
                PLUGIN_SAMPLE: {
                    KEY_TITLE: "Sample",
                    KEY_DESCRIPTION: "Fluent Bit input plugin: Sample.",
                    KEY_DOC_URL: "https://example.test/plugin",
                    KEY_FIELDS: fields,
                    KEY_EXTRACTION: {
                        KEY_STATUS: status,
                        KEY_REFERENCE: "https://example.test/plugin#configuration-parameters",
                        KEY_TABLE_HEADER: headers,
                    },
                }
            },
            KEY_FILTERS: {},
            KEY_OUTPUTS: {},
        },
    }


def test_select_previous_version_uses_nearest_lower_semantic_version() -> None:
    """Patch numbers must be compared numerically rather than lexicographically."""
    selected_version = select_previous_version("5.0.10", ["4.2.4", "5.0.4", "5.0.9", "5.1.0"])

    assert selected_version == "5.0.9"


def test_semantic_version_selection_rejects_invalid_and_handles_no_earlier_version() -> None:
    """Invalid versions should fail clearly and a first version should have no baseline."""
    with pytest.raises(ValueError, match="Unsupported Fluent Bit version"):
        semantic_version_key("release-five")

    assert select_previous_version("3.0.0", ["3.0.0", "4.0.0"]) is None


def test_reconcile_carries_undetermined_field_values_and_reports_divergence() -> None:
    """Missing metadata should inherit while explicit current values remain authoritative."""
    previous_catalog = _catalog(
        "5.0.4",
        [
            _field(
                "port",
                default=25826,
                data_type="integer",
                required=True,
                validation_rule={KEY_KIND_VALUE: "range", KEY_MINIMUM: 1, KEY_MAXIMUM: 65535},
            )
        ],
        table_header=["Key", "Description", "Default", "Required"],
    )
    current_field = _field("port", data_type="string", required=False)
    current_field[KEY_DESCRIPTION] = "Current port description"
    current_catalog = _catalog("5.0.5", [current_field])

    reconciled_catalog, summary = reconcile_catalogs(
        current_catalog,
        previous_catalog,
        previous_version="5.0.4",
    )

    reconciled_field = reconciled_catalog[KEY_PLUGINS][KEY_INPUTS][PLUGIN_SAMPLE][KEY_FIELDS][0]
    assert reconciled_field[KEY_DEFAULT] == 25826
    assert reconciled_field[KEY_DATA_TYPE] == "integer"
    assert reconciled_field[KEY_REQUIRED] is True
    assert reconciled_field[KEY_VALIDATION_RULE][KEY_KIND_VALUE] == "range"
    carry_reasons = {item[KEY_REASON] for item in summary[KEY_CARRIED_FORWARD]}
    assert REASON_REQUIRED_COLUMN_MISSING in carry_reasons
    assert any(
        item.get(KEY_KIND) == KIND_FIELD_ATTRIBUTE_CHANGED
        and item.get(KEY_ATTRIBUTE) == KEY_DESCRIPTION
        and item.get(KEY_PREVIOUS) != item.get(KEY_CURRENT)
        for item in summary[KEY_DIVERGENCES]
    )


def test_reconcile_incomplete_page_retains_prior_fields_and_marks_review() -> None:
    """An unparseable table should retain earlier fields and carry a prominent warning."""
    previous_catalog = _catalog("5.0.4", [_field("listen"), _field("port", default=25826)])
    current_catalog = _catalog(
        "5.0.5",
        [],
        status=STATUS_NO_PARAMETERS,
        table_header=[],
    )

    reconciled_catalog, summary = reconcile_catalogs(
        current_catalog,
        previous_catalog,
        previous_version="5.0.4",
    )

    plugin = reconciled_catalog[KEY_PLUGINS][KEY_INPUTS][PLUGIN_SAMPLE]
    assert [field[KEY_NAME] for field in plugin[KEY_FIELDS]] == ["listen", "port"]
    assert plugin[KEY_EXTRACTION][KEY_REVIEW_REQUIRED] is True
    assert plugin[KEY_EXTRACTION][KEY_REVIEW_COMMENT] == REVIEW_COMMENT
    assert len(summary[KEY_INCOMPLETE_PAGES]) == 1
    assert all(
        item[KEY_REASON] == REASON_INCOMPLETE_PAGE
        for item in summary[KEY_CARRIED_FORWARD]
    )


def test_reconcile_complete_page_reports_missing_field_without_restoring_it() -> None:
    """A prior-only field on a valid page may be an upstream removal and must stay absent."""
    previous_catalog = _catalog("5.0.4", [_field("listen"), _field("removed_option")])
    current_catalog = _catalog("5.0.5", [_field("listen")])

    reconciled_catalog, summary = reconcile_catalogs(
        current_catalog,
        previous_catalog,
        previous_version="5.0.4",
    )

    fields = reconciled_catalog[KEY_PLUGINS][KEY_INPUTS][PLUGIN_SAMPLE][KEY_FIELDS]
    assert [field[KEY_NAME] for field in fields] == ["listen"]
    assert any(
        item.get(KEY_KIND) == KIND_FIELD_NOT_DOCUMENTED
        and item.get(KEY_FIELD) == "removed_option"
        for item in summary[KEY_DIVERGENCES]
    )


def test_write_summary_files_uses_snake_case_names(tmp_path: Path) -> None:
    """Human and machine reports should be emitted with repository-safe filenames."""
    current_catalog = _catalog("5.0.5", [_field("listen")])
    _, summary = reconcile_catalogs(current_catalog, None, previous_version=None)

    json_path, markdown_path = write_summary_files(
        summary,
        tmp_path,
        target_version="5.0.5",
    )

    assert json_path.name == "fluentbit_5_0_5_scrape_summary.json"
    assert markdown_path.name == "fluentbit_5_0_5_scrape_summary.md"
    assert "# Fluent Bit 5.0.5 scrape summary" in markdown_path.read_text(encoding="utf-8")


def test_reconcile_without_baseline_still_marks_incomplete_pages() -> None:
    """Page confidence checks must run even when no earlier catalog can be loaded."""
    current_catalog = _catalog(
        "5.0.5",
        [],
        status=STATUS_NO_PARAMETERS,
        table_header=[],
    )

    reconciled_catalog, summary = reconcile_catalogs(
        current_catalog,
        None,
        previous_version=None,
    )

    plugin = reconciled_catalog[KEY_PLUGINS][KEY_INPUTS][PLUGIN_SAMPLE]
    assert plugin[KEY_EXTRACTION][KEY_REVIEW_REQUIRED] is True
    assert len(summary[KEY_INCOMPLETE_PAGES]) == 1
    assert not summary[KEY_DIVERGENCES]


def test_reconcile_reports_plugin_and_field_additions_and_plugin_removal() -> None:
    """Baseline comparison should expose structural catalog changes for review."""
    previous_catalog = _catalog("5.0.4", [_field("listen")])
    previous_sample = previous_catalog[KEY_PLUGINS][KEY_INPUTS][PLUGIN_SAMPLE]
    previous_catalog[KEY_PLUGINS][KEY_INPUTS][PLUGIN_RETIRED] = deepcopy(previous_sample)
    current_catalog = _catalog("5.0.5", [_field("listen"), _field("new_option")])
    current_sample = current_catalog[KEY_PLUGINS][KEY_INPUTS][PLUGIN_SAMPLE]
    current_catalog[KEY_PLUGINS][KEY_INPUTS][PLUGIN_NEW] = deepcopy(current_sample)

    _, summary = reconcile_catalogs(
        current_catalog,
        previous_catalog,
        previous_version="5.0.4",
    )

    divergence_kinds = {item[KEY_KIND] for item in summary[KEY_DIVERGENCES]}
    assert KIND_FIELD_ADDED in divergence_kinds
    assert KIND_PLUGIN_ADDED in divergence_kinds
    assert KIND_PLUGIN_NOT_DOCUMENTED in divergence_kinds


def test_reconcile_tolerates_malformed_plugin_containers_and_extraction_metadata() -> None:
    """Unexpected local payload shapes should be ignored or marked for review, not crash."""
    previous_catalog = _catalog("5.0.4", [])
    previous_catalog[KEY_PLUGINS][KEY_INPUTS][PLUGIN_SAMPLE][KEY_FIELDS] = "not-a-list"
    current_catalog = _catalog("5.0.5", [])
    current_plugin = current_catalog[KEY_PLUGINS][KEY_INPUTS][PLUGIN_SAMPLE]
    current_plugin[KEY_EXTRACTION] = "not-an-object"
    current_plugin[KEY_FIELDS] = ["not-an-object", {}, {KEY_NAME: ""}]
    current_catalog[KEY_PLUGINS][KEY_INPUTS][PLUGIN_INVALID] = "not-an-object"
    current_catalog[KEY_PLUGINS][KEY_FILTERS] = "not-an-object"

    reconciled_catalog, summary = reconcile_catalogs(
        current_catalog,
        previous_catalog,
        previous_version="5.0.4",
    )

    current_plugin = reconciled_catalog[KEY_PLUGINS][KEY_INPUTS][PLUGIN_SAMPLE]
    assert not current_plugin[KEY_FIELDS]
    assert current_plugin[KEY_EXTRACTION][KEY_REVIEW_REQUIRED] is True
    assert len(summary[KEY_INCOMPLETE_PAGES]) == 1


def test_render_summary_markdown_includes_review_and_change_tables() -> None:
    """A report with fallbacks and differences should render all review sections."""
    previous_catalog = _catalog("5.0.4", [_field("retained_option"), _field("removed_option")])
    current_catalog = _catalog(
        "5.0.5",
        [],
        status=STATUS_NO_PARAMETERS,
        table_header=[],
    )
    _, summary = reconcile_catalogs(
        current_catalog,
        previous_catalog,
        previous_version="5.0.4",
    )
    summary[KEY_DIVERGENCES].append(
        {
            KEY_KIND: KIND_FIELD_ATTRIBUTE_CHANGED,
            KEY_FIELD: "field|with-separator",
            KEY_PREVIOUS: "old\nvalue",
            KEY_CURRENT: "new|value",
        }
    )

    markdown = render_summary_markdown(summary)

    assert "## Pages requiring review" in markdown
    assert "| Location | Kind/reason | Attribute | Value |" in markdown
    assert "| Location | Kind/reason | Attribute | Previous | Current |" in markdown
    assert "field\\|with-separator" in markdown
