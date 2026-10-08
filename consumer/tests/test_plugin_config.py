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

"""Tests for shared consumer plugin configuration helpers."""

# ruff: noqa: S101

from __future__ import annotations

from pathlib import Path

import pytest

from opamp_consumer import plugin_config
from opamp_consumer.plugin_config import (
    collect_consumer_plugin_config_updates,
    looks_like_executable_path,
    resolve_optional_executable_from_config,
)

BARE_COMMAND = "agent"
BARE_COMMAND_WITH_EXTENSION = "agent.exe"
EMPTY_COMMAND = ""
POSIX_RELATIVE_EXECUTABLE_PATH = "bin/agent"
DOT_RELATIVE_EXECUTABLE_PATH = "./agent"
USER_RELATIVE_EXECUTABLE_PATH = "~/bin/agent"
WINDOWS_DRIVE_RELATIVE_EXECUTABLE_PATH = "C:agent.exe"
WINDOWS_ABSOLUTE_EXECUTABLE_PATH = "C:\\tools\\agent.exe"
EXPECTED_RELATIVE_EXECUTABLE_PATH = "bin/agent"
EXPECTED_WINDOWS_ABSOLUTE_EXECUTABLE_PATH = "C:\\tools\\agent.exe"
PLUGIN_IMPORT_ERROR_MESSAGE = (
    "cannot import name 'KEY_HEALTH' from partially initialized module "
    "'opamp_consumer.abstract_client'"
)


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        (EMPTY_COMMAND, False),
        (BARE_COMMAND, False),
        (BARE_COMMAND_WITH_EXTENSION, False),
        (POSIX_RELATIVE_EXECUTABLE_PATH, True),
        (DOT_RELATIVE_EXECUTABLE_PATH, True),
        (USER_RELATIVE_EXECUTABLE_PATH, True),
        (WINDOWS_DRIVE_RELATIVE_EXECUTABLE_PATH, True),
        (WINDOWS_ABSOLUTE_EXECUTABLE_PATH, True),
    ],
)
def test_looks_like_executable_path_classifies_commands_and_paths(
    raw_value: str,
    expected: bool,
) -> None:
    """Executable helper should distinguish PATH commands from filesystem paths.

    Args:
        raw_value: Configured executable value supplied by a plugin.
        expected: Expected path-like classification result.
    """
    assert looks_like_executable_path(raw_value) is expected


def test_resolve_optional_executable_from_config_keeps_bare_commands(
    tmp_path: Path,
) -> None:
    """Bare executable commands should stay unchanged for PATH lookup.

    Args:
        tmp_path: Pytest temporary directory fixture for the owning config file.
    """
    config_path = tmp_path / "opamp.json"

    resolved = resolve_optional_executable_from_config(
        raw_value=BARE_COMMAND,
        config_path=config_path,
    )

    assert resolved == BARE_COMMAND


def test_resolve_optional_executable_from_config_resolves_relative_paths(
    tmp_path: Path,
) -> None:
    """Relative executable paths should resolve beside the owning config file.

    Args:
        tmp_path: Pytest temporary directory fixture for the owning config file.
    """
    config_path = tmp_path / "opamp.json"

    resolved = resolve_optional_executable_from_config(
        raw_value=POSIX_RELATIVE_EXECUTABLE_PATH,
        config_path=config_path,
    )

    assert resolved == str((tmp_path / EXPECTED_RELATIVE_EXECUTABLE_PATH).resolve())


def test_resolve_optional_executable_from_config_preserves_windows_absolute_paths(
    tmp_path: Path,
) -> None:
    """Windows absolute paths should be preserved even on non-Windows test hosts.

    Args:
        tmp_path: Pytest temporary directory fixture for the owning config file.
    """
    config_path = tmp_path / "opamp.json"

    resolved = resolve_optional_executable_from_config(
        raw_value=WINDOWS_ABSOLUTE_EXECUTABLE_PATH,
        config_path=config_path,
    )

    assert resolved == EXPECTED_WINDOWS_ABSOLUTE_EXECUTABLE_PATH


def test_resolve_optional_executable_from_config_omits_blank_values(
    tmp_path: Path,
) -> None:
    """Blank executable settings should remain absent from plugin updates.

    Args:
        tmp_path: Pytest temporary directory fixture for the owning config file.
    """
    config_path = tmp_path / "opamp.json"

    resolved = resolve_optional_executable_from_config(
        raw_value=EMPTY_COMMAND,
        config_path=config_path,
    )

    assert resolved is None


def test_collect_consumer_plugin_config_updates_skips_partial_import(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Plugin hook discovery should not fail while abstract_client is importing.

    Args:
        monkeypatch: Pytest fixture used to simulate the circular import window.
        tmp_path: Pytest temporary directory fixture for the owning config file.
    """

    def fake_import_module(module_name: str) -> object:
        """Raise the same partial-import error produced by plugin client imports."""
        raise ImportError(PLUGIN_IMPORT_ERROR_MESSAGE)

    monkeypatch.setattr(plugin_config.importlib, "import_module", fake_import_module)

    updates = collect_consumer_plugin_config_updates(
        service_type="fluentbit",
        consumer_plugins=[],
        consumer_raw={},
        config_path=tmp_path / "opamp.json",
    )

    assert updates == {}
