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

"""Tests for generated cache and Python egg directory cleanup."""

from __future__ import annotations

from pathlib import Path

from opamp_dev_tools import generated_folders


class _FakeRuntime:
    """Provide repository paths and capture cleanup status messages.

    Attributes
    ----------
    repo_root:
        Temporary repository boundary used by the cleanup operation.
    messages:
        Informational messages emitted during cleanup.

    """

    def __init__(self, repo_root: Path) -> None:
        """Initialize the runtime double for a temporary repository.

        Parameters
        ----------
        repo_root:
            Temporary repository root searched by the cleanup operation.

        """
        self.repo_root = repo_root
        self.messages: list[str] = []

    def info(self, message: str) -> None:
        """Capture one informational message.

        Parameters
        ----------
        message:
            Cleanup status text emitted for the command-line user.

        """
        self.messages.append(message)


def test_discover_cache_and_egg_folders_matches_supported_patterns(tmp_path: Path) -> None:
    """Discovery should find all supported patterns but ignore unrelated caches."""
    expected_paths = [
        tmp_path / "tools" / ".cache",
        tmp_path / "build" / "package.egg",
        tmp_path / "src" / "package.egg-info",
    ]
    for expected_path in expected_paths:
        expected_path.mkdir(parents=True)
    (tmp_path / ".pytest_cache").mkdir()
    ignored_git_cache = tmp_path / ".git" / "internal.cache"
    ignored_git_cache.mkdir(parents=True)
    ignored_virtual_environment_egg = tmp_path / ".venv" / "package.egg-info"
    ignored_virtual_environment_egg.mkdir(parents=True)

    discovered_paths = generated_folders.discover_cache_and_egg_folders(tmp_path)

    assert discovered_paths == sorted(expected_paths, key=lambda path: str(path).casefold())


def test_purge_cache_and_egg_folders_dry_run_preserves_matches(tmp_path: Path) -> None:
    """Dry-run mode should report every match without changing the filesystem."""
    cache_path = tmp_path / "tools" / "download.cache"
    egg_info_path = tmp_path / "src" / "project.egg-info"
    cache_path.mkdir(parents=True)
    egg_info_path.mkdir(parents=True)
    runtime = _FakeRuntime(tmp_path)

    issues_found = generated_folders.purge_cache_and_egg_folders(runtime, dry_run=True)

    assert issues_found is False
    assert cache_path.is_dir()
    assert egg_info_path.is_dir()
    assert any("Would remove generated folder" in message for message in runtime.messages)


def test_purge_cache_and_egg_folders_removes_matches(tmp_path: Path) -> None:
    """Normal mode should remove matches while retaining unrelated directories."""
    cache_path = tmp_path / ".cache"
    egg_path = tmp_path / "dist" / "project.egg"
    egg_info_path = tmp_path / "src" / "project.egg-info"
    retained_path = tmp_path / ".ruff_cache"
    for directory_path in (cache_path, egg_path, egg_info_path, retained_path):
        directory_path.mkdir(parents=True)
        (directory_path / "content.txt").write_text("generated\n", encoding="utf-8")
    runtime = _FakeRuntime(tmp_path)

    issues_found = generated_folders.purge_cache_and_egg_folders(runtime)

    assert issues_found is False
    assert not cache_path.exists()
    assert not egg_path.exists()
    assert not egg_info_path.exists()
    assert retained_path.is_dir()
    assert any("Removing generated folder" in message for message in runtime.messages)


def test_purge_cache_and_egg_folders_reports_no_matches(tmp_path: Path) -> None:
    """An empty scan should complete successfully with a clear status message."""
    runtime = _FakeRuntime(tmp_path)

    issues_found = generated_folders.purge_cache_and_egg_folders(runtime)

    assert issues_found is False
    assert "No .cache, .egg, or .egg-info folders were found." in runtime.messages
