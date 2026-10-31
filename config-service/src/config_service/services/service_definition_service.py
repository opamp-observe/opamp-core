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
KEY_SERVICE_DEFINITIONS_BY_TYPE = "service_definitions_by_type"
KEY_ENGINE = "engine"
KEY_FLUENT_BIT_VERSION = "fluent_bit_version"
KEY_FLUENTD_VERSION = "fluentd_version"
KEY_SECTION = "section"
KEY_CARDINALITY = "cardinality"
KEY_OPTIONS = "options"
KEY_MAXIMUM = "maximum"
KEY_NAME = "name"
KEY_REQUIRED = "required"
KEY_DESCRIPTION = "description"
KEY_REFERENCE = "reference"
KEY_DATA_TYPE = "data_type"
ENGINE_FLUENTBIT = "fluentbit"
ENGINE_FLUENTD = "fluentd"
SECTION_SERVICE = "service"


class ServiceDefinitionService:
    """Load versioned service-section definitions for UI and runtime use."""

    def __init__(self, registry_path: Path) -> None:
        """Initialize the service definition service from its registry path."""
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
        """Load the service registry and validate that it contains grouped definitions."""
        self._registry = load_json_file(self.registry_path, purpose="service registry")
        grouped = self._registry_definitions_by_type()
        if not grouped:
            raise ValueError("service-registry.json must include non-empty service definitions")

    def _registry_definitions_by_type(self) -> dict[str, dict[str, str]]:
        """Return normalized service-definition paths grouped by config type and version."""
        grouped = self._registry.get(KEY_SERVICE_DEFINITIONS_BY_TYPE)
        if isinstance(grouped, dict) and grouped:
            normalized: dict[str, dict[str, str]] = {}
            for config_type, versions in grouped.items():
                if isinstance(versions, dict) and versions:
                    normalized[str(config_type)] = {
                        str(version): str(path) for version, path in versions.items()
                    }
            return normalized
        return {}

    @staticmethod
    def _normalize_config_type(config_type: str) -> str:
        """Normalize user-provided config type aliases into canonical service keys."""
        normalized = str(config_type or "").strip().lower().replace("-", "").replace("_", "").replace(" ", "")
        if normalized == ENGINE_FLUENTBIT:
            return ENGINE_FLUENTBIT
        if normalized == ENGINE_FLUENTD:
            return ENGINE_FLUENTD
        return str(config_type or "").strip()

    def load_all(self) -> None:
        """Load and validate all service definitions referenced by the registry."""
        loaded: dict[str, dict[str, dict[str, Any]]] = {}
        for config_type, version_map in self._registry_definitions_by_type().items():
            loaded[config_type] = {}
            for version, ref in version_map.items():
                path = self._resolve_path(str(ref))
                payload = load_json_file(path, purpose="service definition")
                self.validate_definition(version, payload, source=str(path))
                loaded[config_type][version] = payload
        self._definitions_by_type = loaded

    def validate_definition(self, version: str, payload: dict[str, Any], source: str = "<in-memory>") -> None:
        """Validate one service definition payload before it is exposed to callers."""
        engine = str(payload.get(KEY_ENGINE) or ENGINE_FLUENTBIT).lower()
        required_top = {KEY_ENGINE, KEY_SECTION, KEY_CARDINALITY, KEY_OPTIONS}
        if engine == ENGINE_FLUENTBIT:
            required_top.add(KEY_FLUENT_BIT_VERSION)
        elif engine == ENGINE_FLUENTD:
            required_top.add(KEY_FLUENTD_VERSION)
        missing = [key for key in required_top if key not in payload]
        if missing:
            raise ValueError(f"Service definition {version} missing keys {missing} ({source})")

        if payload.get(KEY_SECTION) != SECTION_SERVICE:
            raise ValueError(f"Service definition {version} section must be '{SECTION_SERVICE}' ({source})")

        cardinality = payload.get(KEY_CARDINALITY, {})
        if not isinstance(cardinality, dict):
            raise ValueError(f"Service definition {version} cardinality must be object ({source})")
        if cardinality.get(KEY_MAXIMUM) != 1:
            raise ValueError(f"Service definition {version} cardinality.maximum must be 1 ({source})")

        options = payload.get(KEY_OPTIONS)
        if not isinstance(options, list):
            raise ValueError(f"Service definition {version} options must be array ({source})")

        for idx, item in enumerate(options):
            if not isinstance(item, dict):
                raise ValueError(f"Service definition {version} option[{idx}] must be object ({source})")
            for req in (KEY_NAME, KEY_REQUIRED, KEY_DESCRIPTION, KEY_REFERENCE, KEY_DATA_TYPE):
                if req not in item:
                    raise ValueError(
                        f"Service definition {version} option[{idx}] missing {req} ({source})"
                    )

    def get_definition(self, version: str, config_type: str | None = None) -> dict[str, Any]:
        """Return one service definition by version, optionally constrained by config type."""
        if config_type:
            normalized_type = self._normalize_config_type(str(config_type))
            mapping = self._definitions_by_type.get(normalized_type, {})
            if version in mapping:
                return mapping[version]
            matches = [
                payload
                for version_map in self._definitions_by_type.values()
                for candidate_version, payload in version_map.items()
                if candidate_version == version
            ]
            if len(matches) == 1:
                return matches[0]
            raise KeyError(f"Unsupported service-definition version for {config_type}: {version}")
        matches = [
            payload
            for version_map in self._definitions_by_type.values()
            for candidate_version, payload in version_map.items()
            if candidate_version == version
        ]
        if not matches:
            raise KeyError(f"Unsupported service-definition version: {version}")
        if len(matches) > 1:
            raise KeyError(f"Ambiguous service-definition version without config type: {version}")
        return matches[0]
