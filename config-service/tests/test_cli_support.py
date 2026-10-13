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

"""Unit tests for config-service CLI support helpers."""

# Ruff's security assertion rule does not apply to pytest test assertions.
# ruff: noqa: S101

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# Tests load the source package after making the repository source tree importable.
# Tests intentionally exercise private orchestration helpers as their focused unit boundary.
# pylint: disable=protected-access,wrong-import-position
from config_service.cli_support import (  # noqa: E402
    CONFIG_TYPE_FLUENTBIT,
    CONFIG_TYPE_FLUENTD,
    CliConfigBatchReport,
    CliConfigFileReport,
    CliConfigSupport,
)

CONFIG_FILENAME = "sample.yaml"
KEY_BODY = "body"
KEY_CATALOG = "catalog"
KEY_CODE = "code"
KEY_CONFIG = "config"
KEY_CONFIG_TYPE = "config_type"
KEY_ERRORS = "errors"
KEY_MESSAGE = "message"
KEY_PARSE_ISSUES = "parse_issues"
KEY_PARSER_DEFINITION = "parser_definition"
KEY_PATH = "path"
KEY_PARSERS = "parsers"
KEY_PIPELINE = "pipeline"
KEY_PLUGINS = "plugins"
KEY_SEVERITY = "severity"
KEY_VERSION = "version"
SAMPLE_VERSION = "5.0.4"


def _repo_root() -> Path:
    """Return the repository root used by integration-style service construction."""
    return Path(__file__).resolve().parents[2]


def _bare_support(repo_root: Path) -> CliConfigSupport:
    """Create a support instance without constructing its repository services."""
    support = object.__new__(CliConfigSupport)
    support.repo_root = repo_root.resolve()
    return support


def test_cli_metadata_injection_preserves_existing_header_comment_block(
    tmp_path: Path,
) -> None:
    """Missing metadata should be added ahead of preserved ownership comments."""
    support = CliConfigSupport(repo_root=_repo_root())
    config_path = tmp_path / CONFIG_FILENAME
    config_path.write_text(
        (
            "# owned by platform team\n"
            "# change-ticket: OPS-123\n"
            "\n"
            "service:\n"
            "  flush: 1\n"
            "pipeline:\n"
            "  inputs:\n"
            "    - name: dummy\n"
            "      tag: test\n"
            "  outputs:\n"
            "    - name: stdout\n"
            "      match: \"*\"\n"
        ),
        encoding="utf-8",
    )

    report = support.ensure_metadata_path(config_path)
    updated_text = config_path.read_text(encoding="utf-8")

    assert len(report.reports) == 1
    assert (
        "Metadata status: applied missing metadata fields config_type, version"
        in report.render()
    )
    assert updated_text.startswith(
        "# config-service: config_type=fluentbit\n"
        "# config-service: version=5.0.4\n"
        "# owned by platform team\n"
        "# change-ticket: OPS-123\n"
        "service:\n"
    )


def test_report_rendering_handles_empty_batches_and_issue_aggregation(tmp_path: Path) -> None:
    """File and batch reports should render deterministically and aggregate issue state."""
    clean_report = CliConfigFileReport(
        source_path=tmp_path / "clean.yaml",
        lines=("Validation result: no error",),
    )
    issue_report = CliConfigFileReport(
        source_path=tmp_path / "broken.conf",
        lines=("Validation result: issues found",),
        has_issues=True,
    )

    assert CliConfigBatchReport(reports=()).render() == ""
    batch_report = CliConfigBatchReport(reports=(clean_report, issue_report))
    rendered_report = batch_report.render()

    assert batch_report.has_issues is True
    assert f"File: {clean_report.source_path}" in rendered_report
    assert "\n\n\n\nFile:" in rendered_report
    assert rendered_report.endswith("\n")


def test_config_directory_resolution_uses_packaged_monorepo_and_fallback_paths(
    tmp_path: Path,
) -> None:
    """Configuration discovery should honor the three documented repository layouts."""
    support = _bare_support(tmp_path)
    fallback_path = tmp_path / "config"
    assert support._config_dir() == fallback_path

    monorepo_path = tmp_path / "config-service" / "config"
    monorepo_path.mkdir(parents=True)
    assert support._config_dir() == monorepo_path

    packaged_path = tmp_path / "config-service" / "src" / "config_service" / "config"
    packaged_path.mkdir(parents=True)
    assert support._config_dir() == packaged_path


def test_supported_file_resolution_covers_files_directories_and_errors(tmp_path: Path) -> None:
    """File discovery should filter extensions, sort results, and reject invalid targets."""
    support = _bare_support(tmp_path)
    missing_path = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError, match="path not found"):
        support._resolve_supported_files(missing_path)

    unsupported_path = tmp_path / "notes.txt"
    unsupported_path.write_text("notes", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported config file extension"):
        support._resolve_supported_files(unsupported_path)

    config_directory = tmp_path / "configs"
    nested_directory = config_directory / "nested"
    nested_directory.mkdir(parents=True)
    yaml_path = config_directory / "b.YAML"
    fluentd_path = nested_directory / "a.conf"
    ignored_path = config_directory / "ignored.json"
    for config_path in (yaml_path, fluentd_path, ignored_path):
        config_path.write_text("content", encoding="utf-8")

    discovered_paths = support._resolve_supported_files(config_directory)
    assert discovered_paths == sorted([yaml_path.resolve(), fluentd_path.resolve()])

    empty_directory = tmp_path / "empty"
    empty_directory.mkdir()
    with pytest.raises(ValueError, match="no supported config files found"):
        support._resolve_supported_files(empty_directory)


def test_ensure_metadata_preserves_complete_existing_header(tmp_path: Path) -> None:
    """A complete header must remain byte-for-byte unchanged."""
    support = CliConfigSupport(repo_root=_repo_root())
    config_path = tmp_path / CONFIG_FILENAME
    original_text = (
        "# config-service: config_type=fluentbit\n"
        "# config-service: version=5.0.4\n"
        "pipeline:\n"
        "  inputs: []\n"
    )
    config_path.write_text(original_text, encoding="utf-8")

    report = support.ensure_metadata_path(config_path)

    assert config_path.read_text(encoding="utf-8") == original_text
    assert "existing metadata preserved" in report.render()


def test_validate_file_reports_clean_and_combined_issues(tmp_path: Path) -> None:
    """Validation output should distinguish clean files and grouped parser/validation issues."""
    support = _bare_support(tmp_path)
    source_path = tmp_path / CONFIG_FILENAME
    prepared_payload = {
        KEY_CONFIG: {},
        KEY_CONFIG_TYPE: CONFIG_TYPE_FLUENTBIT,
        KEY_VERSION: SAMPLE_VERSION,
        KEY_CATALOG: {},
        KEY_PARSER_DEFINITION: {},
        KEY_PARSE_ISSUES: [],
    }
    support._prepare_source_file = Mock(  # type: ignore[method-assign]
        return_value=prepared_payload
    )
    support.validation_service = Mock()
    support.validation_service.validate.return_value = {KEY_ERRORS: []}

    clean_report = support._validate_file(source_path)
    assert clean_report.has_issues is False
    assert "Validation result: no error" in clean_report.render()

    prepared_payload[KEY_PARSE_ISSUES] = [
        {
            KEY_SEVERITY: "warning",
            KEY_CODE: "parse_warning",
            KEY_PATH: "$.pipeline",
            KEY_MESSAGE: "Parser warning",
        }
    ]
    support.validation_service.validate.return_value = {
        KEY_ERRORS: [{}],
    }
    issue_report = support._validate_file(source_path)

    assert issue_report.has_issues is True
    assert "Parser issues:" in issue_report.render()
    assert "Validation issues:" in issue_report.render()
    assert "[warning] parse_warning at $.pipeline: Parser warning" in issue_report.render()
    assert "[error] unknown_issue at $: Validation issue" in issue_report.render()


def test_validate_path_aggregates_resolved_file_reports(tmp_path: Path) -> None:
    """The public validation entry point should preserve discovered file ordering."""
    support = _bare_support(tmp_path)
    first_path = tmp_path / "first.yaml"
    second_path = tmp_path / "second.conf"
    first_report = CliConfigFileReport(source_path=first_path, lines=("first",))
    second_report = CliConfigFileReport(source_path=second_path, lines=("second",))
    support._resolve_supported_files = Mock(  # type: ignore[method-assign]
        return_value=[first_path, second_path]
    )
    support._validate_file = Mock(  # type: ignore[method-assign]
        side_effect=[first_report, second_report]
    )

    batch_report = support.validate_path(tmp_path)

    assert batch_report.reports == (first_report, second_report)


def test_prepare_source_file_handles_fluentbit_and_fluentd_parsers(tmp_path: Path) -> None:
    """Preparation should route YAML and conf bodies to their engine-specific parsers."""
    support = _bare_support(tmp_path)
    source_path = tmp_path / CONFIG_FILENAME
    source_path.write_text("ignored", encoding="utf-8")
    support.ui_document_service = Mock()
    support.catalog_service = Mock()
    support.catalog_service.get_default_version.return_value = SAMPLE_VERSION
    support.catalog_service.get_catalog.return_value = {KEY_PLUGINS: {}}
    support.parser_definition_service = Mock()
    support.parser_definition_service.get_definition.return_value = {KEY_PARSERS: []}
    support.fluentbit_yaml_config_service = Mock()
    support.fluentbit_yaml_config_service.parse.return_value = {
        KEY_CONFIG: {KEY_PIPELINE: {}},
        KEY_ERRORS: [{KEY_CODE: "kept"}, "ignored"],
    }
    support.fluentd_config_service = Mock()
    support.ui_document_service.parse_config_header.return_value = {
        KEY_CONFIG_TYPE: "",
        KEY_VERSION: "",
        KEY_BODY: "pipeline: {}",
    }

    fluentbit_result = support._prepare_source_file(source_path)
    assert fluentbit_result[KEY_CONFIG_TYPE] == CONFIG_TYPE_FLUENTBIT
    assert fluentbit_result[KEY_PARSE_ISSUES] == [{KEY_CODE: "kept"}]
    assert fluentbit_result[KEY_PARSER_DEFINITION] == {KEY_PARSERS: []}

    fluentd_path = tmp_path / "sample.conf"
    fluentd_path.write_text("ignored", encoding="utf-8")
    support.ui_document_service.parse_config_header.return_value = {
        KEY_CONFIG_TYPE: CONFIG_TYPE_FLUENTD,
        KEY_VERSION: "1.19",
        KEY_BODY: "<source></source>",
    }
    support.fluentd_config_service.parse.return_value = {KEY_PIPELINE: {}}

    fluentd_result = support._prepare_source_file(fluentd_path)
    assert fluentd_result[KEY_CONFIG_TYPE] == CONFIG_TYPE_FLUENTD
    assert fluentd_result[KEY_PARSER_DEFINITION] is None
    support.fluentd_config_service.parse.assert_called_once_with("<source></source>")


def test_prepare_source_file_rejects_non_object_parser_result(tmp_path: Path) -> None:
    """A parser result that is not a configuration object should fail with file context."""
    support = _bare_support(tmp_path)
    source_path = tmp_path / CONFIG_FILENAME
    source_path.write_text("ignored", encoding="utf-8")
    support.ui_document_service = Mock()
    support.ui_document_service.parse_config_header.return_value = {
        KEY_CONFIG_TYPE: CONFIG_TYPE_FLUENTBIT,
        KEY_VERSION: SAMPLE_VERSION,
        KEY_BODY: "pipeline: []",
    }
    support.catalog_service = Mock()
    support.catalog_service.get_catalog.return_value = {}
    support.parser_definition_service = Mock()
    support.parser_definition_service.get_definition.return_value = {}
    support.fluentbit_yaml_config_service = Mock()
    support.fluentbit_yaml_config_service.parse.return_value = {
        KEY_CONFIG: [],
        KEY_ERRORS: [],
    }

    with pytest.raises(ValueError, match="config parser did not produce a config object"):
        support._prepare_source_file(source_path)


def test_config_type_helpers_support_known_suffixes_and_reject_unknown_paths(
    tmp_path: Path,
) -> None:
    """Suffix detection should be case-insensitive and reject unknown extensions."""
    support = _bare_support(tmp_path)
    assert support._config_type_for_path(Path("config.YML")) == CONFIG_TYPE_FLUENTBIT
    assert support._config_type_for_path(Path("config.conf")) == CONFIG_TYPE_FLUENTD
    assert support._config_type_for_path(Path("config.json")) == ""

    with pytest.raises(ValueError, match="unable to detect config type"):
        support._require_config_type_for_path(Path("config.json"))
