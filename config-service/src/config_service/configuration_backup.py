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

"""Create recoverable snapshots of config-service's generated configuration tree."""

from __future__ import annotations

import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

CONFIGURATION_DIRECTORY_NAMES = ("config", "json-definitions", "json-schemas")
BACKUP_FILENAME_PREFIX = "config_service_configuration"
BACKUP_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%S_%fZ"
ZIP_FILE_SUFFIX = ".zip"
TEMPORARY_FILE_SUFFIX = ".partial"


def _configuration_directories(package_root: Path) -> tuple[Path, ...]:
    """Return existing configuration directories beneath ``package_root``.

    Parameters
    ----------
    package_root:
        Canonical ``src/config_service`` directory containing packaged assets.
    """
    return tuple(
        package_root / directory_name
        for directory_name in CONFIGURATION_DIRECTORY_NAMES
        if (package_root / directory_name).is_dir()
    )


def _validate_backup_directory(
    configuration_directories: tuple[Path, ...],
    backup_directory: Path,
) -> None:
    """Reject a backup destination nested inside content being archived.

    Parameters
    ----------
    configuration_directories:
        Existing canonical directories that will be placed in the archive.
    backup_directory:
        Requested location for completed and temporary ZIP files.
    """
    resolved_backup_directory = backup_directory.resolve()
    for configuration_directory in configuration_directories:
        if resolved_backup_directory.is_relative_to(configuration_directory.resolve()):
            raise ValueError(
                "Backup directory cannot be inside a configuration directory: "
                f"{backup_directory}"
            )


def create_configuration_backup(
    package_root: Path,
    backup_directory: Path,
    *,
    timestamp: datetime | None = None,
) -> Path:
    """Atomically archive the current canonical configuration before mutation.

    Parameters
    ----------
    package_root:
        Canonical ``src/config_service`` directory containing packaged assets.
    backup_directory:
        Directory in which the compressed snapshot should be created.
    timestamp:
        Optional UTC timestamp used to make a deterministic filename in tests.

    Returns
    -------
    pathlib.Path
        Path to the completed ZIP archive.

    Raises
    ------
    FileNotFoundError
        Raised when none of the expected configuration directories exists.
    FileExistsError
        Raised rather than replacing a backup with the same timestamp.
    ValueError
        Raised when the backup destination is within archived content.
    """
    configuration_directories = _configuration_directories(package_root)
    if not configuration_directories:
        expected_names = ", ".join(CONFIGURATION_DIRECTORY_NAMES)
        raise FileNotFoundError(
            f"No configuration directories found beneath {package_root}; expected {expected_names}."
        )
    _validate_backup_directory(configuration_directories, backup_directory)
    backup_directory.mkdir(parents=True, exist_ok=True)

    backup_timestamp = timestamp or datetime.now(timezone.utc)
    normalized_timestamp = backup_timestamp.astimezone(timezone.utc)
    timestamp_token = normalized_timestamp.strftime(BACKUP_TIMESTAMP_FORMAT)
    backup_path = backup_directory / (
        f"{BACKUP_FILENAME_PREFIX}_{timestamp_token}{ZIP_FILE_SUFFIX}"
    )
    if backup_path.exists():
        raise FileExistsError(f"Configuration backup already exists: {backup_path}")

    with tempfile.NamedTemporaryFile(
        dir=backup_directory,
        prefix=f"{BACKUP_FILENAME_PREFIX}_",
        suffix=TEMPORARY_FILE_SUFFIX,
        delete=False,
    ) as temporary_handle:
        temporary_path = Path(temporary_handle.name)
    try:
        with zipfile.ZipFile(
            temporary_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as backup_archive:
            for configuration_directory in configuration_directories:
                for source_path in sorted(configuration_directory.rglob("*")):
                    if source_path.is_file():
                        archive_path = source_path.relative_to(package_root)
                        backup_archive.write(source_path, arcname=archive_path.as_posix())
        temporary_path.replace(backup_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return backup_path
