# Copyright 2026 opamp.info
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

"""Unit coverage for the optional developer CLI bridge."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace

from opamp_cli import developer_cli


def test_resolve_developer_cli_uses_first_available_alias(monkeypatch) -> None:
    """Executable discovery should preserve the documented alias preference."""

    resolved_names: list[str] = []

    def fake_which(executable_name: str) -> str | None:
        """Record each lookup and resolve only the legacy executable."""

        resolved_names.append(executable_name)
        return "resolved-opamp-dev-tools" if executable_name == "opamp-dev-tools" else None

    monkeypatch.setattr(developer_cli.shutil, "which", fake_which)

    executable_path = developer_cli.resolve_developer_cli()

    assert executable_path == "resolved-opamp-dev-tools"
    assert resolved_names == ["opamp-dev-cli", "opamp-dev-tools"]


def test_developer_cli_available_is_false_when_no_alias_is_installed(monkeypatch) -> None:
    """Operator-only installations should not advertise unavailable developer commands."""

    monkeypatch.setattr(developer_cli.shutil, "which", lambda _executable_name: None)

    assert developer_cli.resolve_developer_cli() is None
    assert developer_cli.developer_cli_available() is False


def test_execute_developer_cli_forwards_repository_and_arguments(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The bridge should preserve arguments and explicitly select the repository."""

    captured: dict[str, object] = {}
    monkeypatch.setattr(
        developer_cli,
        "resolve_developer_cli",
        lambda: "resolved-opamp-dev-cli",
    )

    def fake_run(command: list[str], **options: object) -> SimpleNamespace:
        """Capture the delegated command without starting another process."""

        captured["command"] = command
        captured["options"] = options
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(developer_cli.subprocess, "run", fake_run)

    exit_code = developer_cli.execute_developer_cli(
        ["test", "security"],
        repo_root=tmp_path,
        logger=logging.getLogger("test-developer-cli"),
    )

    assert exit_code == 7
    assert captured["command"] == [
        "resolved-opamp-dev-cli",
        "--repo-root",
        str(tmp_path.resolve()),
        "test",
        "security",
    ]
    assert captured["options"] == {"cwd": str(tmp_path.resolve()), "check": False}


def test_execute_developer_cli_reports_optional_package_absence(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    """An operator-only installation should fail clearly without importing dev-tools."""

    monkeypatch.setattr(developer_cli, "resolve_developer_cli", lambda: None)

    exit_code = developer_cli.execute_developer_cli(
        [],
        repo_root=tmp_path,
        logger=logging.getLogger("test-developer-cli"),
    )

    assert exit_code == developer_cli.DEVELOPER_CLI_UNAVAILABLE_EXIT_CODE
    assert "optional opamp-dev-cli package is not installed" in capsys.readouterr().out


def test_execute_developer_cli_reports_process_start_failure(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    """Executable startup failures should return a stable bridge error."""

    monkeypatch.setattr(
        developer_cli,
        "resolve_developer_cli",
        lambda: "resolved-opamp-dev-cli",
    )

    def fail_to_start(_command: list[str], **_options: object) -> None:
        """Simulate an installed executable that the operating system cannot start."""

        raise OSError("cannot start")

    monkeypatch.setattr(developer_cli.subprocess, "run", fail_to_start)

    exit_code = developer_cli.execute_developer_cli(
        ["help"],
        repo_root=tmp_path,
        logger=logging.getLogger("test-developer-cli"),
    )

    assert exit_code == developer_cli.DEVELOPER_CLI_UNAVAILABLE_EXIT_CODE
    assert "Unable to execute opamp-dev-cli" in capsys.readouterr().out
