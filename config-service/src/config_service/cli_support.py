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

"""CLI-oriented helpers that reuse config-service parsing and validation logic."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config_service.services.catalog_service import CatalogService
from config_service.services.fluentbit_yaml_config_service import FluentBitYamlConfigService
from config_service.services.fluentd_config_service import FluentdConfigService
from config_service.services.parser_definition_service import ParserDefinitionService
from config_service.services.rule_engine_service import RuleEngineService
from config_service.services.rules_registry_service import RulesRegistryService
from config_service.services.ui_document_service import UiDocumentService
from config_service.services.validation_service import ValidationService

UTF8_ENCODING = "utf-8"
CONFIG_TYPE_FLUENTBIT = "fluentbit"
CONFIG_TYPE_FLUENTD = "fluentd"
SUPPORTED_SUFFIX_TO_CONFIG_TYPE = {
    ".yaml": CONFIG_TYPE_FLUENTBIT,
    ".yml": CONFIG_TYPE_FLUENTBIT,
    ".conf": CONFIG_TYPE_FLUENTD,
}
ENTRY_SEPARATOR = "\n\n\n\n"


@dataclass(frozen=True)
class CliConfigFileReport:
    """One human-readable report block for a processed config file.

    Attributes
    ----------
    source_path:
        Resolved configuration file represented by the report.
    lines:
        Ordered human-readable result lines excluding the file heading.
    has_issues:
        Whether parsing or validation produced at least one issue.
    """

    source_path: Path
    lines: tuple[str, ...]
    has_issues: bool = False

    def render(self) -> str:
        """Render the report block as plain text."""
        block_lines = [f"File: {self.source_path}", *self.lines]
        return "\n".join(block_lines).rstrip() + "\n"


@dataclass(frozen=True)
class CliConfigBatchReport:
    """Collection of file reports rendered with wide spacing between entries.

    Attributes
    ----------
    reports:
        Ordered immutable reports for every configuration file processed.
    """

    reports: tuple[CliConfigFileReport, ...]

    @property
    def has_issues(self) -> bool:
        """Return whether any processed file reported parse or validation issues."""
        return any(report.has_issues for report in self.reports)

    def render(self) -> str:
        """Render all reports using three blank lines between files."""
        if not self.reports:
            return ""
        return ENTRY_SEPARATOR.join(report.render().rstrip() for report in self.reports) + "\n"


# The orchestrator intentionally owns one focused service for each config-processing concern.
# pylint: disable=too-many-instance-attributes
class CliConfigSupport:
    """Thin orchestrator around config-service services for local CLI use.

    Attributes
    ----------
    repo_root:
        Resolved repository root used to locate configuration registries.
    catalog_service:
        Catalog registry loader and version lookup service.
    parser_definition_service:
        Fluent Bit parser-definition registry service.
    rules_registry_service:
        Validation-rule registry used to construct the rule engine.
    validation_service:
        Semantic configuration validation service.
    ui_document_service:
        Header metadata parser and renderer shared with the browser UI.
    fluentbit_yaml_config_service:
        Fluent Bit YAML parser.
    fluentd_config_service:
        Fluentd configuration parser.
    """

    def __init__(self, *, repo_root: Path) -> None:
        """Construct config-processing services from one repository root.

        Parameters
        ----------
        repo_root:
            Repository or package root containing config-service registries.
        """
        self.repo_root = repo_root.resolve()
        config_dir = self._config_dir()
        self.catalog_service = CatalogService(config_dir / "catalog-registry.json")
        self.catalog_service.load_all_catalogs()
        self.parser_definition_service = ParserDefinitionService(
            config_dir / "parser-registry.json"
        )
        self.parser_definition_service.load_all()
        self.rules_registry_service = RulesRegistryService(
            config_dir / "validation-rules-registry.json"
        )
        self.validation_service = ValidationService(
            RuleEngineService(self.rules_registry_service)
        )
        self.ui_document_service = UiDocumentService()
        self.fluentbit_yaml_config_service = FluentBitYamlConfigService()
        self.fluentd_config_service = FluentdConfigService()

    def _config_dir(self) -> Path:
        """Resolve packaged, monorepo, or standalone configuration directories."""
        packaged_config_dir = (
            self.repo_root / "config-service" / "src" / "config_service" / "config"
        )
        if packaged_config_dir.is_dir():
            return packaged_config_dir
        monorepo_config_dir = self.repo_root / "config-service" / "config"
        if monorepo_config_dir.is_dir():
            return monorepo_config_dir
        return self.repo_root / "config"

    def validate_path(self, target_path: Path) -> CliConfigBatchReport:
        """Validate one config file or every supported file beneath one directory."""
        reports = tuple(
            self._validate_file(path)
            for path in self._resolve_supported_files(target_path)
        )
        return CliConfigBatchReport(reports=reports)

    def ensure_metadata_path(self, target_path: Path) -> CliConfigBatchReport:
        """Add missing config-service header metadata to one file or directory tree."""
        reports = tuple(
            self._ensure_metadata_for_file(path)
            for path in self._resolve_supported_files(target_path)
        )
        return CliConfigBatchReport(reports=reports)

    def _resolve_supported_files(self, target_path: Path) -> list[Path]:
        resolved = target_path.expanduser().resolve()
        if resolved.exists() is not True:
            raise FileNotFoundError(f"path not found: {resolved}")
        if resolved.is_file():
            config_type = self._config_type_for_path(resolved)
            if not config_type:
                raise ValueError(f"unsupported config file extension: {resolved.name}")
            return [resolved]

        files = sorted(
            path.resolve()
            for path in resolved.rglob("*")
            if path.is_file() and self._config_type_for_path(path)
        )
        if not files:
            raise ValueError(f"no supported config files found under: {resolved}")
        return files

    def _validate_file(self, source_path: Path) -> CliConfigFileReport:
        prepared = self._prepare_source_file(source_path)
        lines = [
            f"Config type: {prepared['config_type']}",
            f"Version: {prepared['version']}",
        ]
        parse_issues = list(prepared["parse_issues"])
        validation_result = self.validation_service.validate(
            version=prepared["version"],
            payload={"config": prepared["config"]},
            catalog=prepared["catalog"],
            profile=None,
            parser_definition=prepared["parser_definition"],
        )
        validation_issues = list(validation_result.get("errors", []))
        if not parse_issues and not validation_issues:
            lines.append("Validation result: no error")
        else:
            lines.append("Validation result: issues found")
            if parse_issues:
                lines.append("Parser issues:")
                lines.extend(self._format_issue_lines(parse_issues))
            if validation_issues:
                lines.append("Validation issues:")
                lines.extend(self._format_issue_lines(validation_issues))
        return CliConfigFileReport(
            source_path=source_path,
            lines=tuple(lines),
            has_issues=bool(parse_issues or validation_issues),
        )

    def _ensure_metadata_for_file(self, source_path: Path) -> CliConfigFileReport:
        raw_text = source_path.read_text(encoding=UTF8_ENCODING)
        parsed_header = self.ui_document_service.parse_config_header(raw_text)
        existing_config_type = str(parsed_header.get("config_type") or "").strip()
        existing_version = str(parsed_header.get("version") or "").strip()
        detected_config_type = existing_config_type or self._require_config_type_for_path(
            source_path
        )
        detected_version = existing_version or self.catalog_service.get_default_version(
            detected_config_type
        )
        lines = [
            f"Config type: {detected_config_type}",
            f"Version: {detected_version}",
        ]
        if existing_config_type and existing_version:
            lines.append(
                "Metadata status: existing metadata preserved; no values were overwritten"
            )
            return CliConfigFileReport(source_path=source_path, lines=tuple(lines))

        body_text = str(parsed_header.get("body") or "")
        header_comments = str(parsed_header.get("header_comments") or "")
        updated_text = body_text
        if header_comments:
            updated_text = self.ui_document_service.prepend_header_comments(
                updated_text,
                header_comments,
                comment_prefix="#",
            )
        updated_text = self.ui_document_service.prepend_config_header(
            updated_text,
            config_type=detected_config_type,
            version=detected_version,
            comment_prefix="#",
        )
        source_path.write_text(updated_text, encoding=UTF8_ENCODING)
        applied_fields: list[str] = []
        if not existing_config_type:
            applied_fields.append("config_type")
        if not existing_version:
            applied_fields.append("version")
        lines.append(
            "Metadata status: applied missing metadata fields "
            + ", ".join(applied_fields)
        )
        return CliConfigFileReport(source_path=source_path, lines=tuple(lines))

    def _prepare_source_file(self, source_path: Path) -> dict[str, Any]:
        raw_text = source_path.read_text(encoding=UTF8_ENCODING)
        parsed_header = self.ui_document_service.parse_config_header(raw_text)
        config_type = str(parsed_header.get("config_type") or "").strip().lower()
        if not config_type:
            config_type = self._require_config_type_for_path(source_path)
        version = str(parsed_header.get("version") or "").strip()
        if not version:
            version = self.catalog_service.get_default_version(config_type)
        body_text = str(parsed_header.get("body") or "")
        catalog = self.catalog_service.get_catalog(version, config_type=config_type)
        parser_definition = None
        parse_issues: list[dict[str, Any]] = []
        if config_type == CONFIG_TYPE_FLUENTD:
            parsed_config = self.fluentd_config_service.parse(body_text)
        else:
            parser_definition = self.parser_definition_service.get_definition(
                version,
                config_type=CONFIG_TYPE_FLUENTBIT,
            )
            parse_result = self.fluentbit_yaml_config_service.parse(body_text)
            parse_issues = [
                issue
                for issue in parse_result.get("errors", [])
                if isinstance(issue, dict)
            ]
            parsed_config = parse_result.get("config")
        if not isinstance(parsed_config, dict):
            raise ValueError(f"config parser did not produce a config object: {source_path}")
        return {
            "config": parsed_config,
            "config_type": config_type,
            "version": version,
            "catalog": catalog,
            "parser_definition": parser_definition,
            "parse_issues": parse_issues,
        }

    @staticmethod
    def _format_issue_lines(issues: list[dict[str, Any]]) -> list[str]:
        lines: list[str] = []
        for issue in issues:
            severity = str(issue.get("severity") or "error")
            code = str(issue.get("code") or "unknown_issue")
            path = str(issue.get("path") or "$")
            message = str(issue.get("message") or "Validation issue")
            lines.append(f"- [{severity}] {code} at {path}: {message}")
        return lines

    @staticmethod
    def _config_type_for_path(source_path: Path) -> str:
        return SUPPORTED_SUFFIX_TO_CONFIG_TYPE.get(source_path.suffix.lower(), "")

    def _require_config_type_for_path(self, source_path: Path) -> str:
        config_type = self._config_type_for_path(source_path)
        if not config_type:
            raise ValueError(f"unable to detect config type from file extension: {source_path}")
        return config_type
