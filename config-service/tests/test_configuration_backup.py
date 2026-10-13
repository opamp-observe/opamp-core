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

"""Tests for atomic config-service configuration backups."""

# Ruff's security assertion rule does not apply to pytest test assertions.
# ruff: noqa: S101

from __future__ import annotations

import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from config_service.configuration_backup import create_configuration_backup

BACKUP_TIMESTAMP = datetime(2026, 10, 10, 12, 30, tzinfo=timezone.utc)


def _write_fixture(package_root: Path, relative_path: str, content: str) -> None:
    """Create one representative configuration file beneath the package root."""
    fixture_path = package_root / relative_path
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    fixture_path.write_text(content, encoding="utf-8")


def test_create_configuration_backup_archives_canonical_tree(tmp_path: Path) -> None:
    """A successful backup should contain all existing canonical configuration files."""
    package_root = tmp_path / "src" / "config_service"
    backup_directory = tmp_path / "backups"
    _write_fixture(package_root, "config/catalog-registry.json", "{}")
    _write_fixture(package_root, "json-definitions/catalog.json", '{"catalog": true}')
    _write_fixture(package_root, "json-schemas/schema.json", '{"schema": true}')
    _write_fixture(package_root, "ignored.txt", "not configuration")

    backup_path = create_configuration_backup(
        package_root,
        backup_directory,
        timestamp=BACKUP_TIMESTAMP,
    )

    assert backup_path.name == "config_service_configuration_20261010T123000_000000Z.zip"
    with zipfile.ZipFile(backup_path) as backup_archive:
        assert backup_archive.namelist() == [
            "config/catalog-registry.json",
            "json-definitions/catalog.json",
            "json-schemas/schema.json",
        ]
    assert not list(backup_directory.glob("*.partial"))


def test_create_configuration_backup_rejects_missing_configuration(tmp_path: Path) -> None:
    """An empty source root should stop generation instead of producing a useless archive."""
    with pytest.raises(FileNotFoundError, match="No configuration directories"):
        create_configuration_backup(tmp_path / "package", tmp_path / "backups")


def test_create_configuration_backup_rejects_nested_destination(tmp_path: Path) -> None:
    """A destination inside archived content should be rejected to prevent recursion."""
    package_root = tmp_path / "package"
    _write_fixture(package_root, "config/catalog-registry.json", "{}")

    with pytest.raises(ValueError, match="cannot be inside"):
        create_configuration_backup(package_root, package_root / "config" / "backups")


def test_create_configuration_backup_does_not_replace_existing_archive(tmp_path: Path) -> None:
    """A timestamp collision should preserve the first completed snapshot."""
    package_root = tmp_path / "package"
    backup_directory = tmp_path / "backups"
    _write_fixture(package_root, "config/catalog-registry.json", "{}")
    create_configuration_backup(package_root, backup_directory, timestamp=BACKUP_TIMESTAMP)

    with pytest.raises(FileExistsError, match="already exists"):
        create_configuration_backup(package_root, backup_directory, timestamp=BACKUP_TIMESTAMP)


def test_create_configuration_backup_removes_partial_file_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ZIP write failure should leave neither a completed nor partial snapshot."""
    package_root = tmp_path / "package"
    backup_directory = tmp_path / "backups"
    _write_fixture(package_root, "config/catalog-registry.json", "{}")

    def fail_write(
        _archive: zipfile.ZipFile,
        _filename: str | Path,
        arcname: str | None = None,
        _compress_type: int | None = None,
        _compresslevel: int | None = None,
    ) -> None:
        """Simulate an archive failure after the temporary file has been created."""
        del arcname
        raise OSError("simulated backup failure")

    monkeypatch.setattr(zipfile.ZipFile, "write", fail_write)

    with pytest.raises(OSError, match="simulated backup failure"):
        create_configuration_backup(package_root, backup_directory, timestamp=BACKUP_TIMESTAMP)

    assert not list(backup_directory.iterdir())
