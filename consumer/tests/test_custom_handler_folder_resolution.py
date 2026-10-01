# ruff: noqa: S101
# Copyright 2026 mp3monster.org
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0

"""Tests for resolving built-in and agent-specific custom handler folders."""

from __future__ import annotations

from pathlib import Path

from opamp_consumer.custom_handlers.registry import resolve_handler_folder


def test_missing_agent_handler_folder_uses_shared_builtin_handlers(
    tmp_path: Path,
) -> None:
    """Use package handlers when a concrete agent has no override directory."""
    shared_folder = tmp_path / "shared-custom-handlers"
    shared_folder.mkdir()
    resolved = resolve_handler_folder(
        tmp_path / "missing-custom-handlers", shared_folder
    )

    assert resolved == shared_folder


def test_existing_agent_handler_folder_is_preserved(tmp_path: Path) -> None:
    """Keep a plugin-specific handler directory when the plugin supplies one."""
    custom_folder = tmp_path / "custom_handlers"
    custom_folder.mkdir()

    assert resolve_handler_folder(custom_folder, tmp_path / "fallback") == custom_folder
