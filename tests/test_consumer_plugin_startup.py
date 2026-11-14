# Copyright 2026 opamp.info
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

"""Contract tests for the clean consumer-plugin startup container."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "test-containers"
    / "consumer-plugin-startup"
    / "scripts"
    / "run_consumer_plugin_startup.py"
)
RUNNER_MODULE_NAME = "consumer_plugin_startup_runner"


def _load_runner_module() -> ModuleType:
    """Load the container runner without executing its command-line entry point."""
    module_spec = importlib.util.spec_from_file_location(RUNNER_MODULE_NAME, RUNNER_PATH)
    assert module_spec is not None
    assert module_spec.loader is not None
    runner_module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(runner_module)
    return runner_module


def test_install_supplies_shared_and_consumer_as_local_projects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Give pip both editable projects so it never resolves opamp-shared from PyPI.

    Args:
        monkeypatch: Pytest fixture used to capture the generated install command.
    """
    runner_module = _load_runner_module()
    captured_commands: list[tuple[list[str], Path]] = []

    def capture_command(command: list[str], *, cwd: Path) -> None:
        """Retain one generated command and working directory for assertions.

        Args:
            command: Generated pip command.
            cwd: Working directory selected for the install.
        """
        captured_commands.append((command, cwd))

    monkeypatch.setattr(runner_module, "_run", capture_command)
    runner_module._install_local_projects(REPOSITORY_ROOT)  # pylint: disable=protected-access

    install_command, install_directory = captured_commands[0]
    shared_path = str(REPOSITORY_ROOT / "shared")
    consumer_path = str(REPOSITORY_ROOT / "consumer")
    assert install_directory == REPOSITORY_ROOT
    assert install_command[:4] == [sys.executable, "-m", "pip", "install"]
    assert install_command.count("-e") == 2
    assert install_command.index(shared_path) < install_command.index(consumer_path)
