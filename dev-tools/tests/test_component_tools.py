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

"""Unit coverage for component-owned developer CLI capability discovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pytest

from opamp_dev_tools import component_tools

REPO_ROOT = Path(__file__).resolve().parents[2]
FLUENT_RESOURCES_GROUP = "fluent-resources"
GENERATE_ASSETS_COMMAND = "generate-fluentbit-assets"
GENERATE_MARKDOWN_COMMAND = "generate-fluentbit-markdown"


class _RuntimeDouble:
    """Capture component subprocess execution without starting a child process.

    Attributes
    ----------
    repo_root:
        Repository root expected as the child process working directory.
    commands:
        Commands received through the shared runtime interface.
    working_directories:
        Working directories supplied for each captured command.
    """

    def __init__(self, repo_root: Path) -> None:
        """Initialize captured runtime state for one test repository.

        Parameters
        ----------
        repo_root:
            Repository root that should own component tool execution.
        """
        self.repo_root = repo_root
        self.commands: list[list[str]] = []
        self.working_directories: list[Path | None] = []

    def run(self, command: list[str], *, cwd: Path | None = None) -> None:
        """Record a requested subprocess command and working directory.

        Parameters
        ----------
        command:
            Child-process arguments assembled by the component tool runner.
        cwd:
            Requested child-process working directory.
        """
        self.commands.append(command)
        self.working_directories.append(cwd)


def test_discovery_loads_config_service_tool_manifest() -> None:
    """The real Config Service manifest should publish both Fluent Bit commands."""
    tools = component_tools.discover_component_tools(REPO_ROOT)
    fluent_tools = component_tools.tools_for_group(tools, FLUENT_RESOURCES_GROUP)

    assert [tool.command for tool in fluent_tools] == [
        GENERATE_ASSETS_COMMAND,
        GENERATE_MARKDOWN_COMMAND,
    ]
    assert all(tool.component_name == "config-service" for tool in fluent_tools)
    assert all(tool.script_path.is_file() for tool in fluent_tools)


def test_discovery_returns_empty_for_missing_or_unreadable_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing manifests and unreadable roots must not break the core CLI."""
    assert component_tools.discover_component_tools(tmp_path) == []

    def fail_iteration(_path: Path) -> Any:
        """Raise the filesystem error handled by optional discovery."""
        raise OSError("unreadable")

    monkeypatch.setattr(Path, "iterdir", fail_iteration)

    assert component_tools.discover_component_tools(tmp_path) == []


@pytest.mark.parametrize(
    "manifest_text",
    [
        "not-json",
        json.dumps({"schema_version": 999, "tools": []}),
        json.dumps({"schema_version": 1, "tools": "invalid"}),
        json.dumps(
            {
                "schema_version": 1,
                "tools": [
                    {
                        "id": "unsafe_tool",
                        "command_group": FLUENT_RESOURCES_GROUP,
                        "command": "unsafe-tool",
                        "description": "Unsafe path",
                        "script": "../outside.py",
                    }
                ],
            }
        ),
    ],
)
def test_discovery_ignores_invalid_optional_manifests(
    tmp_path: Path,
    manifest_text: str,
) -> None:
    """Malformed optional component metadata should be ignored as one unit."""
    manifest_directory = tmp_path / "component" / "dev-tools"
    manifest_directory.mkdir(parents=True)
    (manifest_directory / component_tools.MANIFEST_FILENAME).write_text(
        manifest_text,
        encoding="utf-8",
    )

    assert component_tools.discover_component_tools(tmp_path) == []


def test_registered_component_parser_accepts_and_rejects_declared_options() -> None:
    """Manifest arguments should become typed argparse options and exclusions."""
    tools = component_tools.discover_component_tools(REPO_ROOT)
    tool = next(item for item in tools if item.command == GENERATE_ASSETS_COMMAND)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    component_tools.register_component_tool_parser(subparsers, tool)

    args = parser.parse_args(
        [
            GENERATE_ASSETS_COMMAND,
            "--version",
            "5.1.3",
            "--version",
            "5.1.4",
            "--timeout",
            "31",
            "--source",
            "github",
            "--no-schemas",
        ]
    )

    assert args.versions == ["5.1.3", "5.1.4"]
    assert args.timeout == 31
    assert args.source == "github"
    assert args.no_schemas is True
    assert not hasattr(args, "no_register")
    assert component_tools.component_tool_from_args(args) == tool
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                GENERATE_ASSETS_COMMAND,
                "--version",
                "5.1.3",
                "--remove-version",
                "5.0.4",
            ]
        )


def test_component_tool_from_args_returns_none_without_discovered_metadata() -> None:
    """Core command namespaces should not be mistaken for component tools."""
    assert component_tools.component_tool_from_args(argparse.Namespace()) is None


def test_component_tool_runner_reconstructs_only_supplied_arguments() -> None:
    """Execution should preserve repeated and boolean options without adding defaults."""
    tool = next(
        item
        for item in component_tools.discover_component_tools(REPO_ROOT)
        if item.command == GENERATE_ASSETS_COMMAND
    )
    args = argparse.Namespace(
        versions=["5.1.3", "5.1.4"],
        timeout=45,
        no_schemas=True,
    )
    runtime = _RuntimeDouble(REPO_ROOT)

    issues_found = component_tools.run_component_tool(
        runtime,  # type: ignore[arg-type]
        python_exe="python-test",
        args=args,
        tool=tool,
    )

    assert issues_found is False
    assert runtime.commands == [
        [
            "python-test",
            str(tool.script_path),
            "--version",
            "5.1.3",
            "--version",
            "5.1.4",
            "--timeout",
            "45",
            "--no-schemas",
        ]
    ]
    assert runtime.working_directories == [REPO_ROOT]
