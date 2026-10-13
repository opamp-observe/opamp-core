# Copyright 2026 mp3monster.org
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Discover and remove generated cache and Python egg directories."""

from __future__ import annotations

import fnmatch
import os
import shutil
from pathlib import Path
from typing import Any

PURGE_DIRECTORY_PATTERNS = ("*.cache", "*.egg", "*.egg-info")
SKIPPED_DIRECTORY_NAMES = frozenset({".git", ".venv", "node_modules", "venv"})


def purge_cache_and_egg_folders(runtime: Any, *, dry_run: bool = False) -> bool:
    """Remove matching generated directories beneath the repository root.

    Parameters
    ----------
    runtime:
        Command runtime that supplies the repository root and console logging.
    dry_run:
        Whether to report matching directories without removing them.

    """
    matching_directories = discover_cache_and_egg_folders(runtime.repo_root)
    runtime.info(
        "DEBUG: discovered "
        f"{len(matching_directories)} cache or egg folder(s) beneath {runtime.repo_root}"
    )
    if not matching_directories:
        runtime.info("No .cache, .egg, or .egg-info folders were found.")
        return False

    action = "Would remove" if dry_run else "Removing"
    for directory_path in matching_directories:
        runtime.info(f"{action} generated folder {directory_path}")
        if not dry_run:
            shutil.rmtree(directory_path)
    return False


def discover_cache_and_egg_folders(repo_root: Path) -> list[Path]:
    """Return removable cache and egg directories within a repository.

    Parameters
    ----------
    repo_root:
        Repository boundary searched recursively without following links.

    """
    resolved_repo_root = repo_root.expanduser().resolve()
    matching_directories: list[Path] = []
    for current_root, directory_names, _file_names in os.walk(
        resolved_repo_root,
        topdown=True,
        followlinks=False,
    ):
        current_path = Path(current_root)
        traversable_names: list[str] = []
        for directory_name in directory_names:
            directory_path = current_path / directory_name
            if directory_name in SKIPPED_DIRECTORY_NAMES or directory_path.is_symlink():
                continue
            if _is_purge_directory_name(directory_name):
                matching_directories.append(directory_path)
                continue
            traversable_names.append(directory_name)
        directory_names[:] = traversable_names
    return sorted(matching_directories, key=lambda directory_path: str(directory_path).casefold())


def _is_purge_directory_name(directory_name: str) -> bool:
    """Return whether a directory name matches a generated-folder pattern.

    Parameters
    ----------
    directory_name:
        Leaf directory name encountered during repository traversal.

    """
    return any(
        fnmatch.fnmatchcase(directory_name, pattern)
        for pattern in PURGE_DIRECTORY_PATTERNS
    )
