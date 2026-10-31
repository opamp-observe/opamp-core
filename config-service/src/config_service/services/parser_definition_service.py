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

from __future__ import annotations

from pathlib import Path
from typing import Any

from config_service.json_utils import load_json_file

UTF8_ENCODING = "utf-8"
KEY_PARSER_DEFINITIONS_BY_TYPE = "parser_definitions_by_type"
KEY_ENGINE = "engine"
KEY_FLUENT_BIT_VERSION = "fluent_bit_version"
KEY_SECTION = "section"
KEY_CARDINALITY = "cardinality"
KEY_PARSER_FORMATS = "parser_formats"
KEY_FIELDS = "fields"
KEY_TITLE = "title"
KEY_DESCRIPTION = "description"
KEY_DOC_URL = "doc_url"
KEY_NAME = "name"
KEY_REQUIRED = "required"
KEY_REFERENCE = "reference"
KEY_DATA_TYPE = "data_type"
ENGINE_FLUENTBIT = "fluentbit"
SECTION_PARSERS = "parsers"


class ParserDefinitionService:
    """Load versioned Fluent Bit parser definitions for UI and runtime use."""

    def __init__(self, registry_path: Path) -> None:
        """Initialize the parser definition service from its registry path."""
        self.registry_path = registry_path
        self._registry: dict[str, Any] = {}
        self._definitions_by_type: dict[str, dict[str, dict[str, Any]]] = {}
        self._load_registry()

    def _resolve_path(self, ref: str) -> Path:
        """Resolve a definition reference path relative to the registry root when needed."""
        candidate = Path(ref)
        if candidate.is_absolute():
            return candidate
        return self.registry_path.parent.parent / ref

    def _load_registry(self) -> None:
        """Load the parser registry and validate that it contains grouped definitions."""
        self._registry = load_json_file(self.registry_path, purpose="parser registry")
        grouped = self._registry_definitions_by_type()
        if not grouped:
            raise ValueError("parser-registry.json must include non-empty parser definitions")

    def _registry_definitions_by_type(self) -> dict[str, dict[str, str]]:
        """Return normalized parser-definition paths grouped by config type and version."""
        grouped = self._registry.get(KEY_PARSER_DEFINITIONS_BY_TYPE)
        if isinstance(grouped, dict) and grouped:
            normalized: dict[str, dict[str, str]] = {}
            for config_type, versions in grouped.items():
                if isinstance(versions, dict) and versions:
                    normalized[str(config_type)] = {
                        str(version): str(path) for version, path in versions.items()
                    }
            return normalized
        return {}

    def load_all(self) -> None:
        """Load and validate all parser definitions referenced by the registry."""
        loaded: dict[str, dict[str, dict[str, Any]]] = {}
        for config_type, version_map in self._registry_definitions_by_type().items():
            loaded[config_type] = {}
            for version, ref in version_map.items():
                path = self._resolve_path(str(ref))
                payload = load_json_file(path, purpose="parser definition")
                self.validate_definition(version, payload, source=str(path))
                loaded[config_type][version] = payload
        self._definitions_by_type = loaded

    def validate_definition(self, version: str, payload: dict[str, Any], source: str = "<in-memory>") -> None:
        """Validate one parser definition payload before it is exposed to callers."""
        required_top = {KEY_ENGINE, KEY_FLUENT_BIT_VERSION, KEY_SECTION, KEY_CARDINALITY, KEY_PARSER_FORMATS}
        missing = [key for key in required_top if key not in payload]
        if missing:
            raise ValueError(f"Parser definition {version} missing keys {missing} ({source})")

        if str(payload.get(KEY_ENGINE) or "").lower() != ENGINE_FLUENTBIT:
            raise ValueError(f"Parser definition {version} engine must be '{ENGINE_FLUENTBIT}' ({source})")
        if payload.get(KEY_SECTION) != SECTION_PARSERS:
            raise ValueError(f"Parser definition {version} section must be '{SECTION_PARSERS}' ({source})")

        cardinality = payload.get(KEY_CARDINALITY, {})
        if not isinstance(cardinality, dict):
            raise ValueError(f"Parser definition {version} cardinality must be object ({source})")

        parser_formats = payload.get(KEY_PARSER_FORMATS)
        if not isinstance(parser_formats, dict) or not parser_formats:
            raise ValueError(f"Parser definition {version} parser_formats must be non-empty object ({source})")

        for format_name, format_payload in parser_formats.items():
            if not isinstance(format_payload, dict):
                raise ValueError(
                    f"Parser definition {version} parser format {format_name} must be object ({source})"
                )
            for req in (KEY_TITLE, KEY_DESCRIPTION, KEY_DOC_URL, KEY_FIELDS):
                if req not in format_payload:
                    raise ValueError(
                        f"Parser definition {version} parser format {format_name} missing {req} ({source})"
                    )
            fields = format_payload.get(KEY_FIELDS)
            if not isinstance(fields, list):
                raise ValueError(
                    f"Parser definition {version} parser format {format_name} fields must be array ({source})"
                )
            for idx, item in enumerate(fields):
                if not isinstance(item, dict):
                    raise ValueError(
                        f"Parser definition {version} parser format {format_name} field[{idx}] must be object ({source})"
                    )
                for req in (KEY_NAME, KEY_REQUIRED, KEY_DESCRIPTION, KEY_REFERENCE, KEY_DATA_TYPE):
                    if req not in item:
                        raise ValueError(
                            f"Parser definition {version} parser format {format_name} field[{idx}] missing {req} ({source})"
                        )

    def get_definition(self, version: str, config_type: str | None = None) -> dict[str, Any]:
        """Return one parser definition by version, optionally constrained by config type."""
        if config_type:
            mapping = self._definitions_by_type.get(str(config_type), {})
            if version not in mapping:
                raise KeyError(f"Unsupported parser-definition version for {config_type}: {version}")
            return mapping[version]
        matches = [
            payload
            for version_map in self._definitions_by_type.values()
            for candidate_version, payload in version_map.items()
            if candidate_version == version
        ]
        if not matches:
            raise KeyError(f"Unsupported parser-definition version: {version}")
        if len(matches) > 1:
            raise KeyError(f"Ambiguous parser-definition version without config type: {version}")
        return matches[0]
