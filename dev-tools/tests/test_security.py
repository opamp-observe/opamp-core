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

"""Tests for repository security-check orchestration."""

from __future__ import annotations

import subprocess
from pathlib import Path

from opamp_dev_tools import security


class _SecurityRuntime:
    """Capture repository security commands without running external tools.

    Attributes
    ----------
    repo_root:
        Temporary repository root used by the security workflow.
    commands:
        External commands captured during orchestration.
    messages:
        Informational messages emitted by the workflow.

    """

    def __init__(self, repo_root: Path) -> None:
        """Initialize captures for one temporary repository.

        Parameters
        ----------
        repo_root:
            Temporary root used for command working directories.

        """
        self.repo_root = repo_root
        self.commands: list[list[str]] = []
        self.messages: list[str] = []

    def run(self, command: list[str], **_options: object) -> subprocess.CompletedProcess[str]:
        """Capture one external command and report successful completion.

        Parameters
        ----------
        command:
            Complete command line requested by the security workflow.
        _options:
            Working directory and environment options ignored by the fake.

        """
        self.commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    def info(self, message: str) -> None:
        """Capture one informational message.

        Parameters
        ----------
        message:
            Console message emitted by the security workflow.

        """
        self.messages.append(message)


def test_repo_security_pytest_uses_importlib_mode(monkeypatch, tmp_path: Path) -> None:
    """The full suite should isolate duplicate test module filenames."""
    monkeypatch.setattr(security, "_ensure_cli_tool", lambda *_args, **_options: None)
    monkeypatch.setattr(
        security,
        "ensure_pytest_dependencies",
        lambda *_args, **_options: None,
    )
    monkeypatch.setattr(
        security,
        "compact_provider_ui_assets",
        lambda *_args, **_options: False,
    )
    monkeypatch.setattr(security, "_scan_for_secrets", lambda *_args, **_options: None)
    runtime = _SecurityRuntime(tmp_path)

    issues_found = security.run_repo_security_checks(runtime, python_exe="python")

    assert issues_found is False
    assert runtime.commands[0] == [
        "python",
        "-m",
        "pytest",
        "-s",
        security.PYTEST_IMPORT_MODE_ARGUMENT,
    ]
