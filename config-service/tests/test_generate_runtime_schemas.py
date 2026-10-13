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

"""Tests for canonical runtime-schema generation orchestration."""

# Test scripts repeat the same explicit dev-tools source-path bootstrap by design.
# pylint: disable=duplicate-code

# Ruff's security assertion rule does not apply to pytest test assertions.
# ruff: noqa: S101

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

CONFIG_SERVICE_ROOT = Path(__file__).resolve().parents[1]
DEV_TOOLS_ROOT = CONFIG_SERVICE_ROOT / "dev-tools"
SRC_ROOT = CONFIG_SERVICE_ROOT / "src"
for import_root in (DEV_TOOLS_ROOT, SRC_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

# The developer script is intentionally loaded from its non-package source directory.
# pylint: disable=import-error,too-few-public-methods,wrong-import-position
import generate_runtime_schemas as generator  # noqa: E402

CONFIG_TYPE = "fluentbit"
TARGET_VERSION = "5.0.4"
KEY_VERSION = "version"


class FakeCatalogService:
    """Expose one catalog while recording the registry path used by generation."""

    # Registry paths records every location passed to a fake instance.
    registry_paths: list[Path] = []
    # Loaded records whether generation requested the complete registered catalog set.
    loaded: bool = False

    def __init__(self, registry_path: Path) -> None:
        """Record the registry selected by the generator.

        Parameters
        ----------
        registry_path:
            Catalog registry passed to the runtime catalog loader.
        """
        self.registry_paths.append(registry_path)

    def load_all_catalogs(self) -> None:
        """Record that all registry entries were loaded before filtering."""
        self.__class__.loaded = True

    def get_supported_config_types(self) -> list[str]:
        """Return the single configuration type represented by this fake."""
        return [CONFIG_TYPE]

    def get_versions(self, *, config_type: str) -> list[str]:
        """Return the target version for the expected configuration type."""
        assert config_type == CONFIG_TYPE
        return [TARGET_VERSION]

    def get_catalog(self, version: str, *, config_type: str) -> dict[str, Any]:
        """Return a minimal catalog token for schema compilation."""
        assert version == TARGET_VERSION
        assert config_type == CONFIG_TYPE
        return {KEY_VERSION: version}


class FakeSchemaService:
    """Compile a deterministic token so orchestration can be tested in isolation."""

    def compile_schema(
        self,
        catalog: dict[str, Any],
        *,
        strict_mode: bool,
    ) -> dict[str, Any]:
        """Return the input token after verifying strict compilation is requested."""
        assert strict_mode is True
        return catalog


def test_generate_runtime_schemas_uses_only_canonical_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compilation should read and write the one packaged configuration tree."""
    output_directory = tmp_path / "package" / "json-schemas"
    config_directory = tmp_path / "package" / "config"
    write_calls: list[tuple[Path, str, str, dict[str, Any]]] = []
    FakeCatalogService.registry_paths = []
    FakeCatalogService.loaded = False

    def record_schema_write(
        directory: Path,
        config_type: str,
        version: str,
        schema: dict[str, Any],
    ) -> None:
        """Record the single canonical output instead of writing generated fixtures."""
        write_calls.append((directory, config_type, version, schema))

    monkeypatch.setattr(generator, "OUTPUT_DIR", output_directory)
    monkeypatch.setattr(generator, "CONFIG_DIR", config_directory)
    monkeypatch.setattr(generator, "CatalogService", FakeCatalogService)
    monkeypatch.setattr(generator, "SchemaService", FakeSchemaService)
    monkeypatch.setattr(generator, "_write_schema_artifact", record_schema_write)

    generator.generate_runtime_schemas(
        config_types=[CONFIG_TYPE],
        versions=[TARGET_VERSION],
    )

    assert FakeCatalogService.registry_paths == [config_directory / "catalog-registry.json"]
    assert FakeCatalogService.loaded is True
    assert write_calls == [
        (
            output_directory,
            CONFIG_TYPE,
            TARGET_VERSION,
            {KEY_VERSION: TARGET_VERSION},
        )
    ]
