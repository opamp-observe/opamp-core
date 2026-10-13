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

"""Tests for the Fluent Bit asset-generator reconciliation integration."""

# Test scripts repeat the same explicit dev-tools source-path bootstrap by design.
# pylint: disable=duplicate-code

# Ruff's security assertion rule does not apply to pytest test assertions.
# ruff: noqa: S101

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

CONFIG_SERVICE_ROOT = Path(__file__).resolve().parents[1]
DEV_TOOLS_ROOT = CONFIG_SERVICE_ROOT / "dev-tools"
SRC_ROOT = CONFIG_SERVICE_ROOT / "src"
for import_root in (DEV_TOOLS_ROOT, SRC_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

# Tests load the developer script after making its sibling tools importable.
# Generator integration tests intentionally exercise private orchestration helpers.
# pylint: disable=import-error,protected-access,wrong-import-position
import generate_fluentbit_assets as generator  # noqa: E402

KEY_CATALOGS_BY_TYPE = "catalogs_by_type"
KEY_FIELDS = "fields"
KEY_FILTERS = "filters"
KEY_FLUENTBIT = "fluentbit"
KEY_FLUENT_BIT_VERSION = "fluent_bit_version"
KEY_GENERATED_AT = "generated_at"
KEY_INPUTS = "inputs"
KEY_OUTPUTS = "outputs"
KEY_PLUGINS = "plugins"
TARGET_VERSION = "5.0.5"
PREVIOUS_VERSION = "5.0.4"
REPLACEMENT_VERSION = "4.2.4"


def _minimal_catalog(version: str) -> dict[str, Any]:
    """Build a minimal valid catalog payload for generator orchestration tests."""
    return {
        KEY_FLUENT_BIT_VERSION: version,
        KEY_GENERATED_AT: "2026-10-09T00:00:00Z",
        KEY_PLUGINS: {
            KEY_INPUTS: {},
            KEY_FILTERS: {},
            KEY_OUTPUTS: {},
        },
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write one temporary JSON fixture used by catalog resolution tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _configure_removal_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    default_version: str = PREVIOUS_VERSION,
) -> tuple[Path, tuple[Path, ...]]:
    """Create canonical registries and artifacts for removal tests.

    Parameters
    ----------
    tmp_path:
        Temporary test root receiving the canonical package fixture.
    monkeypatch:
        Pytest patch helper used to redirect generator constants.
    default_version:
        Fluent Bit version recorded as the current default in every registry.

    Returns
    -------
    tuple[Path, tuple[Path, ...]]
        Package root and all version-owned artifact paths.
    """
    package_root = tmp_path / "config_service"
    definitions_directory = package_root / "json-definitions"
    schemas_directory = package_root / "json-schemas"
    config_directory = package_root / "config"
    registry_definitions = (
        (
            config_directory / "catalog-registry.json",
            generator.KEY_CATALOGS_BY_TYPE,
            f"json-definitions/{generator._artifact_filename(TARGET_VERSION)}",
        ),
        (
            config_directory / "service-registry.json",
            generator.KEY_SERVICE_DEFINITIONS_BY_TYPE,
            f"json-definitions/fluent-bit-{TARGET_VERSION}-service-options.json",
        ),
        (
            config_directory / "parser-registry.json",
            generator.KEY_PARSER_DEFINITIONS_BY_TYPE,
            f"json-definitions/fluent-bit-{TARGET_VERSION}-parser-options.json",
        ),
    )
    for registry_path, mapping_key, target_reference in registry_definitions:
        _write_json(
            registry_path,
            {
                generator.KEY_DEFAULT_VERSIONS: {KEY_FLUENTBIT: default_version},
                mapping_key: {
                    KEY_FLUENTBIT: {
                        REPLACEMENT_VERSION: "replacement.json",
                        PREVIOUS_VERSION: "previous.json",
                        TARGET_VERSION: target_reference,
                    }
                },
            },
        )

    monkeypatch.setattr(generator, "PACKAGE_ROOT", package_root)
    monkeypatch.setattr(generator, "DEFINITIONS_DIR", definitions_directory)
    monkeypatch.setattr(generator, "SCHEMAS_DIR", schemas_directory)
    monkeypatch.setattr(generator, "CATALOG_REGISTRY_PATH", registry_definitions[0][0])
    monkeypatch.setattr(generator, "SERVICE_REGISTRY_PATH", registry_definitions[1][0])
    monkeypatch.setattr(generator, "PARSER_REGISTRY_PATH", registry_definitions[2][0])

    artifact_paths = generator._removal_artifact_paths(TARGET_VERSION)
    for artifact_path in artifact_paths:
        is_version_directory = (
            artifact_path.name == TARGET_VERSION
            and artifact_path.parent.name in {"fluent-bit", "fluentbit"}
        )
        if is_version_directory:
            artifact_path.mkdir(parents=True)
            _write_json(artifact_path / "part.json", {})
        else:
            _write_json(artifact_path, {})
    return package_root, artifact_paths


def test_load_previous_catalog_selects_and_loads_packaged_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Automatic selection should find the nearest earlier packaged catalog."""
    relative_reference = f"json-definitions/{generator._artifact_filename(PREVIOUS_VERSION)}"
    package_root = tmp_path / "src" / "config_service"
    registry_path = package_root / "config" / "catalog-registry.json"
    _write_json(
        registry_path,
        {
            KEY_CATALOGS_BY_TYPE: {
                KEY_FLUENTBIT: {PREVIOUS_VERSION: relative_reference},
            }
        },
    )
    packaged_path = package_root / relative_reference
    _write_json(packaged_path, _minimal_catalog(PREVIOUS_VERSION))
    monkeypatch.setattr(generator, "CATALOG_REGISTRY_PATH", registry_path)
    monkeypatch.setattr(generator, "PACKAGE_ROOT", package_root)

    resolved_version, payload = generator._load_previous_catalog(
        TARGET_VERSION,
        requested_version=None,
    )

    assert resolved_version == PREVIOUS_VERSION
    assert payload is not None
    assert payload[KEY_FLUENT_BIT_VERSION] == PREVIOUS_VERSION


def test_load_previous_catalog_rejects_missing_explicit_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicit baseline should fail rather than silently disabling inheritance."""
    registry_path = tmp_path / "catalog-registry.json"
    _write_json(registry_path, {KEY_CATALOGS_BY_TYPE: {KEY_FLUENTBIT: {}}})
    monkeypatch.setattr(generator, "CATALOG_REGISTRY_PATH", registry_path)
    monkeypatch.setattr(generator, "PACKAGE_ROOT", tmp_path / "src" / "config_service")

    with pytest.raises(FileNotFoundError, match=PREVIOUS_VERSION):
        generator._load_previous_catalog(
            TARGET_VERSION,
            requested_version=PREVIOUS_VERSION,
        )


def test_generate_version_writes_reports_and_runs_downstream_steps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One generation run should connect scrape, reconciliation, enrichment, and schemas."""
    definitions_directory = tmp_path / "json-definitions"
    summary_directory = tmp_path / "reports"
    update_paths: list[Path] = []
    registered_versions: list[str] = []
    schema_calls: list[tuple[list[str], list[str]]] = []

    def fake_build_catalog(
        version: str,
        **_options: Any,
    ) -> dict[str, Any]:
        """Return deterministic scraped content without network access."""
        return _minimal_catalog(version)

    def fake_load_previous_catalog(
        _target_version: str,
        *,
        requested_version: str | None,
    ) -> tuple[str, dict[str, Any]]:
        """Return a deterministic baseline and validate the explicit request flow."""
        assert requested_version == PREVIOUS_VERSION
        return PREVIOUS_VERSION, _minimal_catalog(PREVIOUS_VERSION)

    def fake_update_catalog(path: Path, **_options: Any) -> None:
        """Record the canonical packaged enrichment call."""
        update_paths.append(path)

    def fake_update_registry(version: str) -> None:
        """Record the requested registry update without changing repository files."""
        registered_versions.append(version)

    def fake_generate_schemas(
        *,
        config_types: list[str],
        versions: list[str],
    ) -> None:
        """Record runtime-schema compilation arguments."""
        schema_calls.append((config_types, versions))

    monkeypatch.setattr(generator, "DEFINITIONS_DIR", definitions_directory)
    monkeypatch.setattr(generator, "build_catalog_from_docs", fake_build_catalog)
    monkeypatch.setattr(generator, "_load_previous_catalog", fake_load_previous_catalog)
    monkeypatch.setattr(generator.add_fluentbit_processors, "update_catalog", fake_update_catalog)
    monkeypatch.setattr(generator, "_update_catalog_registry", fake_update_registry)
    monkeypatch.setattr(
        generator.generate_runtime_schemas,
        "generate_runtime_schemas",
        fake_generate_schemas,
    )

    generator.generate_version(
        TARGET_VERSION,
        source="auto",
        timeout=5,
        github_ref=None,
        register=True,
        generate_schemas_flag=True,
        inherit_previous=True,
        previous_version=PREVIOUS_VERSION,
        summary_dir=summary_directory,
    )

    artifact_name = generator._artifact_filename(TARGET_VERSION)
    assert (definitions_directory / artifact_name).is_file()
    assert update_paths == [definitions_directory / artifact_name]
    assert registered_versions == [TARGET_VERSION]
    assert schema_calls == [([KEY_FLUENTBIT], [TARGET_VERSION])]
    assert (summary_directory / "fluentbit_5_0_5_scrape_summary.json").is_file()
    assert (summary_directory / "fluentbit_5_0_5_scrape_summary.md").is_file()


def test_main_creates_backup_before_generating_versions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CLI must finish its snapshot before the first mutating generation call."""
    operation_order: list[str] = []
    arguments = SimpleNamespace(
        backup_dir=tmp_path / "backups",
        versions=[TARGET_VERSION],
        source="auto",
        timeout=5,
        github_ref=None,
        no_register=False,
        no_schemas=False,
        no_inherit=False,
        previous_version=None,
        summary_dir=tmp_path / "reports",
        remove_version=None,
        replacement_default=None,
    )

    def fake_backup(package_root: Path, backup_directory: Path) -> Path:
        """Record backup completion without creating a repository archive."""
        assert package_root == generator.PACKAGE_ROOT
        operation_order.append("backup")
        return backup_directory / "configuration.zip"

    def fake_generate_version(version: str, **_options: Any) -> None:
        """Record generation and verify the requested version reaches orchestration."""
        assert version == TARGET_VERSION
        operation_order.append("generate")

    monkeypatch.setattr(generator, "parse_args", lambda: arguments)
    monkeypatch.setattr(generator, "create_configuration_backup", fake_backup)
    monkeypatch.setattr(generator, "generate_version", fake_generate_version)

    generator.main()

    assert operation_order == ["backup", "generate"]


def test_main_resolves_latest_release_before_generating(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An omitted operation should generate the current stable Fluent Bit release."""
    operation_order: list[str] = []
    arguments = SimpleNamespace(
        backup_dir=tmp_path / "backups",
        versions=None,
        source="auto",
        timeout=19,
        github_ref=None,
        no_register=False,
        no_schemas=False,
        no_inherit=False,
        previous_version=None,
        summary_dir=tmp_path / "reports",
        remove_version=None,
        replacement_default=None,
    )

    def fake_resolve(*, timeout: int) -> str:
        """Return a deterministic current release before repository mutation."""
        assert timeout == 19
        operation_order.append("resolve")
        return TARGET_VERSION

    def fake_backup(_package_root: Path, backup_directory: Path) -> Path:
        """Record that the mandatory backup follows release resolution."""
        operation_order.append("backup")
        return backup_directory / "configuration.zip"

    def fake_generate(version: str, **_options: Any) -> None:
        """Record generation of the resolved current stable release."""
        assert version == TARGET_VERSION
        operation_order.append("generate")

    monkeypatch.setattr(generator, "parse_args", lambda: arguments)
    monkeypatch.setattr(generator, "resolve_current_stable_version", fake_resolve)
    monkeypatch.setattr(generator, "create_configuration_backup", fake_backup)
    monkeypatch.setattr(generator, "generate_version", fake_generate)

    generator.main()

    assert operation_order == ["resolve", "backup", "generate"]


def test_main_stops_when_backup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed snapshot must prevent every mutating generation operation."""
    arguments = SimpleNamespace(
        backup_dir=tmp_path / "backups",
        versions=[TARGET_VERSION],
        source="auto",
        timeout=5,
        github_ref=None,
        no_register=False,
        no_schemas=False,
        no_inherit=False,
        previous_version=None,
        summary_dir=tmp_path / "reports",
        remove_version=None,
        replacement_default=None,
    )

    def fail_backup(_package_root: Path, _backup_directory: Path) -> Path:
        """Simulate a destination failure before generation begins."""
        raise OSError("backup unavailable")

    def reject_generation(_version: str, **_options: Any) -> None:
        """Fail the test if generation is called after the backup error."""
        pytest.fail("generation must not start after backup failure")

    monkeypatch.setattr(generator, "parse_args", lambda: arguments)
    monkeypatch.setattr(generator, "create_configuration_backup", fail_backup)
    monkeypatch.setattr(generator, "generate_version", reject_generation)

    with pytest.raises(OSError, match="backup unavailable"):
        generator.main()


def test_remove_version_deletes_canonical_artifacts_and_registry_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Removal should delete every owned artifact and unregister the version."""
    package_root, artifact_paths = _configure_removal_fixture(tmp_path, monkeypatch)
    summary_directory = tmp_path / "reports"
    backup_path = tmp_path / "backups" / "configuration.zip"

    json_summary_path, markdown_summary_path = generator.remove_version(
        TARGET_VERSION,
        replacement_default=None,
        summary_dir=summary_directory,
        backup_path=backup_path,
    )

    assert all(not artifact_path.exists() for artifact_path in artifact_paths)
    for registry_path, mapping_key in generator._registry_specs():
        registry_payload = json.loads(registry_path.read_text(encoding="utf-8"))
        assert TARGET_VERSION not in registry_payload[mapping_key][KEY_FLUENTBIT]
        assert registry_payload[generator.KEY_DEFAULT_VERSIONS][KEY_FLUENTBIT] == PREVIOUS_VERSION
    summary_payload = json.loads(json_summary_path.read_text(encoding="utf-8"))
    assert summary_payload[generator.KEY_VERSION] == TARGET_VERSION
    assert len(summary_payload[generator.KEY_REMOVED_PATHS]) == len(artifact_paths)
    assert all(
        not Path(package_root / relative_path).exists()
        for relative_path in summary_payload[generator.KEY_REMOVED_PATHS]
    )
    assert markdown_summary_path.is_file()


def test_remove_default_requires_replacement_before_deleting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default-version removal must fail before mutation without a replacement."""
    _package_root, artifact_paths = _configure_removal_fixture(
        tmp_path,
        monkeypatch,
        default_version=TARGET_VERSION,
    )

    with pytest.raises(ValueError, match="replacement-default"):
        generator.remove_version(
            TARGET_VERSION,
            replacement_default=None,
            summary_dir=tmp_path / "reports",
            backup_path=tmp_path / "configuration.zip",
        )

    assert all(artifact_path.exists() for artifact_path in artifact_paths)
    for registry_path, mapping_key in generator._registry_specs():
        registry_payload = json.loads(registry_path.read_text(encoding="utf-8"))
        assert TARGET_VERSION in registry_payload[mapping_key][KEY_FLUENTBIT]
        assert registry_payload[generator.KEY_DEFAULT_VERSIONS][KEY_FLUENTBIT] == TARGET_VERSION


def test_remove_default_assigns_explicit_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicit registered replacement should become the new default everywhere."""
    _configure_removal_fixture(
        tmp_path,
        monkeypatch,
        default_version=TARGET_VERSION,
    )

    generator.remove_version(
        TARGET_VERSION,
        replacement_default=REPLACEMENT_VERSION,
        summary_dir=tmp_path / "reports",
        backup_path=tmp_path / "configuration.zip",
    )

    for registry_path, mapping_key in generator._registry_specs():
        registry_payload = json.loads(registry_path.read_text(encoding="utf-8"))
        assert TARGET_VERSION not in registry_payload[mapping_key][KEY_FLUENTBIT]
        assert (
            registry_payload[generator.KEY_DEFAULT_VERSIONS][KEY_FLUENTBIT]
            == REPLACEMENT_VERSION
        )


def test_main_creates_backup_before_removing_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Removal mode must complete its backup before invoking destructive work."""
    operation_order: list[str] = []
    backup_path = tmp_path / "backups" / "configuration.zip"
    arguments = SimpleNamespace(
        backup_dir=tmp_path / "backups",
        versions=None,
        remove_version=TARGET_VERSION,
        replacement_default=None,
        source="auto",
        timeout=5,
        github_ref=None,
        no_register=False,
        no_schemas=False,
        no_inherit=False,
        previous_version=None,
        summary_dir=tmp_path / "reports",
    )

    def fake_backup(package_root: Path, backup_directory: Path) -> Path:
        """Record completion of the mandatory pre-removal backup."""
        assert package_root == generator.PACKAGE_ROOT
        assert backup_directory == arguments.backup_dir
        operation_order.append("backup")
        return backup_path

    def fake_remove_version(version: str, **options: Any) -> tuple[Path, Path]:
        """Record removal arguments after backup completion."""
        assert version == TARGET_VERSION
        assert options["backup_path"] == backup_path
        operation_order.append("remove")
        return tmp_path / "summary.json", tmp_path / "summary.md"

    monkeypatch.setattr(generator, "parse_args", lambda: arguments)
    monkeypatch.setattr(generator, "create_configuration_backup", fake_backup)
    monkeypatch.setattr(generator, "remove_version", fake_remove_version)

    generator.main()

    assert operation_order == ["backup", "remove"]


def test_parse_args_accepts_removal_as_generation_alternative(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The command line should accept removal instead of generation."""
    monkeypatch.setattr(
        generator.sys,
        "argv",
        ["generate_fluentbit_assets.py", "--remove-version", TARGET_VERSION],
    )

    arguments = generator.parse_args()

    assert arguments.remove_version == TARGET_VERSION
    assert arguments.versions is None


def test_parse_args_allows_omitted_operation_for_latest_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No explicit operation should defer latest-version resolution to main."""
    monkeypatch.setattr(generator.sys, "argv", ["generate_fluentbit_assets.py"])

    arguments = generator.parse_args()

    assert arguments.remove_version is None
    assert arguments.versions is None
