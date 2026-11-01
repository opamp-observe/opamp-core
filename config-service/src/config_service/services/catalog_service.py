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

from config_service.json_artifacts import load_json_artifact
from config_service.json_utils import load_json_file

KEY_CATALOGS_BY_TYPE = "catalogs_by_type"
KEY_DEFAULT_VERSIONS = "default_versions"
KEY_ENGINE = "engine"
KEY_PLUGINS = "plugins"
KEY_CUSTOM_PLUGINS = "custom_plugins"
KEY_FLUENT_BIT_VERSION = "fluent_bit_version"
KEY_FLUENTD_VERSION = "fluentd_version"
KEY_NESTED_SECTIONS = "nested_sections"
KEY_ROOT_SECTIONS = "root_sections"
KEY_FIELDS = "fields"
KEY_DIRECTIVE_ARGUMENT = "directive_argument"
KEY_PLUGIN_BACKED = "plugin_backed"
KEY_VARIANTS = "variants"
KEY_REUSES_OUTPUT_PLUGINS = "reuses_output_plugins"
KEY_NAME = "name"
KEY_REQUIRED = "required"
KEY_DESCRIPTION = "description"
KEY_REFERENCE = "reference"
KEY_DATA_TYPE = "data_type"

ENGINE_FLUENTBIT = "fluentbit"
ENGINE_FLUENTD = "fluentd"
DEFAULT_CONFIG_TYPE = ENGINE_FLUENTBIT
IN_MEMORY_SOURCE = "<in-memory>"

SECTION_INPUTS = "inputs"
SECTION_FILTERS = "filters"
SECTION_OUTPUTS = "outputs"
PLUGIN_SECTIONS = (SECTION_INPUTS, SECTION_FILTERS, SECTION_OUTPUTS)
FIELD_REQUIRED_KEYS = (
    KEY_NAME,
    KEY_REQUIRED,
    KEY_DESCRIPTION,
    KEY_REFERENCE,
    KEY_DATA_TYPE,
)


class CatalogService:
    """Loads and validates versioned plugin catalogs by configuration type."""

    def __init__(self, registry_path: Path) -> None:
        """Initialize service state and eagerly load the catalog registry."""
        self.registry_path = registry_path
        self._registry: dict[str, Any] = {}
        self._catalogs_by_type: dict[str, dict[str, dict[str, Any]]] = {}
        self._load_registry()

    def _resolve_catalog_path(self, catalog_ref: str) -> Path:
        """Resolve one catalog path, supporting absolute and repo-relative refs."""
        candidate = Path(catalog_ref)
        if candidate.is_absolute():
            return candidate
        return self.registry_path.parent.parent / catalog_ref

    def _load_registry(self) -> None:
        """Load registry JSON and enforce that at least one catalog group exists."""
        self._registry = load_json_file(self.registry_path, purpose="catalog registry")
        catalogs_by_type = self._registry_catalogs_by_type()
        if not catalogs_by_type:
            raise ValueError("catalog-registry.json must define at least one catalog group")

    def _registry_catalogs_by_type(self) -> dict[str, dict[str, str]]:
        """Return normalized `config_type -> version -> catalog_path` mapping."""
        grouped = self._registry.get(KEY_CATALOGS_BY_TYPE)
        if isinstance(grouped, dict) and grouped:
            normalized: dict[str, dict[str, str]] = {}
            for config_type, catalogs in grouped.items():
                if isinstance(catalogs, dict) and catalogs:
                    normalized[str(config_type)] = {str(version): str(path) for version, path in catalogs.items()}
            return normalized
        return {}

    def load_all_catalogs(self) -> None:
        """Load and validate every catalog declared in the registry."""
        loaded: dict[str, dict[str, dict[str, Any]]] = {}
        for config_type, version_map in self._registry_catalogs_by_type().items():
            loaded[config_type] = {}
            for version, catalog_ref in version_map.items():
                path = self._resolve_catalog_path(catalog_ref)
                try:
                    payload = load_json_artifact(path)
                except Exception as exc:
                    raise ValueError(
                        f"Failed loading catalog for config_type={config_type} version={version} from {path}: {exc}"
                    ) from exc
                self.validate_catalog_payload(version, payload, source=str(path))
                loaded[config_type][version] = payload
        self._catalogs_by_type = loaded

    def validate_catalog_payload(
        self,
        version: str,
        payload: dict[str, Any],
        source: str = IN_MEMORY_SOURCE,
    ) -> None:
        """Validate one catalog payload against engine-specific structure rules."""
        # Engine-specific required top-level keys.
        engine = str(payload.get(KEY_ENGINE) or ENGINE_FLUENTBIT).lower()
        top_required = {KEY_ENGINE, KEY_PLUGINS, KEY_CUSTOM_PLUGINS}
        if engine == ENGINE_FLUENTBIT:
            top_required.add(KEY_FLUENT_BIT_VERSION)
        elif engine == ENGINE_FLUENTD:
            top_required.update({KEY_FLUENTD_VERSION, KEY_NESTED_SECTIONS, KEY_ROOT_SECTIONS})
        missing = [key for key in top_required if key not in payload]
        if missing:
            raise ValueError(f"Catalog {version} missing required keys {missing} ({source})")

        plugins = payload.get(KEY_PLUGINS)
        if not isinstance(plugins, dict):
            raise ValueError(f"Catalog {version} must include plugins object ({source})")

        engine_plugins = plugins
        # Validate all plugin sections and each plugin's declared fields.
        for section in PLUGIN_SECTIONS:
            section_map = engine_plugins.get(section)
            if not isinstance(section_map, dict):
                raise ValueError(f"Catalog {version} section {section} must be an object ({source})")
            for plugin_name, plugin_def in section_map.items():
                if KEY_FIELDS not in plugin_def or not isinstance(plugin_def[KEY_FIELDS], list):
                    raise ValueError(
                        f"Catalog {version} plugin {section}.{plugin_name} must define list 'fields' ({source})"
                    )
                for idx, field in enumerate(plugin_def[KEY_FIELDS]):
                    for req in FIELD_REQUIRED_KEYS:
                        if req not in field:
                            raise ValueError(
                                f"Catalog {version} plugin {section}.{plugin_name} field[{idx}] missing {req} ({source})"
                            )
                directive_argument = plugin_def.get(KEY_DIRECTIVE_ARGUMENT)
                if directive_argument is not None:
                    self._validate_field_like(
                        version=version,
                        field=directive_argument,
                        source=source,
                        context=f"plugin {section}.{plugin_name} directive_argument",
                    )

        if engine == ENGINE_FLUENTD:
            # Fluentd adds nested section definitions with plugin-backed and
            # non-plugin-backed variants that each have different constraints.
            nested_sections = payload.get(KEY_NESTED_SECTIONS)
            if not isinstance(nested_sections, dict):
                raise ValueError(f"Catalog {version} nested_sections must be an object ({source})")
            for nested_name, nested_def in nested_sections.items():
                if not isinstance(nested_def, dict):
                    raise ValueError(
                        f"Catalog {version} nested section {nested_name} must be an object ({source})"
                    )
                if nested_def.get(KEY_PLUGIN_BACKED) is True:
                    variants = nested_def.get(KEY_VARIANTS)
                    if nested_def.get(KEY_REUSES_OUTPUT_PLUGINS) is True:
                        continue
                    if not isinstance(variants, dict) or not variants:
                        raise ValueError(
                            f"Catalog {version} nested section {nested_name} must define variants ({source})"
                        )
                    # Plugin-backed nested sections validate each variant's field list.
                    for variant_name, variant_def in variants.items():
                        if not isinstance(variant_def, dict) or not isinstance(
                            variant_def.get(KEY_FIELDS), list
                        ):
                            raise ValueError(
                                f"Catalog {version} nested section {nested_name}.{variant_name} "
                                f"must define list 'fields' ({source})"
                            )
                        for idx, field in enumerate(variant_def[KEY_FIELDS]):
                            self._validate_field_like(
                                version=version,
                                field=field,
                                source=source,
                                context=f"nested section {nested_name}.{variant_name} field[{idx}]",
                            )
                else:
                    # Non plugin-backed nested sections validate one shared field list.
                    fields = nested_def.get(KEY_FIELDS)
                    if not isinstance(fields, list):
                        raise ValueError(
                            f"Catalog {version} nested section {nested_name} must define list 'fields' ({source})"
                        )
                    for idx, field in enumerate(fields):
                        self._validate_field_like(
                            version=version,
                            field=field,
                            source=source,
                            context=f"nested section {nested_name} field[{idx}]",
                        )

    def _validate_field_like(
        self,
        *,
        version: str,
        field: dict[str, Any],
        source: str,
        context: str,
    ) -> None:
        """Validate one field-like object has all required descriptor keys."""
        for req in FIELD_REQUIRED_KEYS:
            if req not in field:
                raise ValueError(
                    f"Catalog {version} {context} missing {req} ({source})"
                )

    def get_supported_config_types(self) -> list[str]:
        """Return loaded configuration types (for example fluentbit/fluentd)."""
        return list(self._catalogs_by_type.keys())

    def get_versions(self, config_type: str | None = None) -> list[str]:
        """Return loaded catalog versions for one config type."""
        resolved_type = str(config_type or DEFAULT_CONFIG_TYPE)
        return list(self._catalogs_by_type.get(resolved_type, {}).keys())

    def get_default_version(self, config_type: str | None = None) -> str:
        """Return default version from registry, falling back to first loaded version."""
        defaults = self._registry.get(KEY_DEFAULT_VERSIONS)
        resolved_type = str(config_type or DEFAULT_CONFIG_TYPE)
        if isinstance(defaults, dict) and defaults.get(resolved_type):
            return str(defaults[resolved_type])
        versions = self.get_versions(resolved_type)
        if versions:
            return str(versions[0])
        raise ValueError(f"No default version configured for {resolved_type}")

    def get_catalog(self, version: str, config_type: str | None = None) -> dict[str, Any]:
        """Return one catalog by version, optionally scoped by config type."""
        if config_type:
            version_map = self._catalogs_by_type.get(str(config_type), {})
            if version not in version_map:
                raise KeyError(f"Unsupported version for {config_type}: {version}")
            return version_map[version]

        matches = [
            payload
            for version_map in self._catalogs_by_type.values()
            for candidate_version, payload in version_map.items()
            if candidate_version == version
        ]
        if not matches:
            raise KeyError(f"Unsupported version: {version}")
        if len(matches) > 1:
            raise KeyError(f"Ambiguous version without config type: {version}")
        return matches[0]

    def validate_catalog_for_version(self, version: str) -> dict[str, Any]:
        """Re-validate one loaded catalog and return success payload."""
        payload = self.get_catalog(version)
        self.validate_catalog_payload(version, payload)
        return {"ok": True, "version": version}
