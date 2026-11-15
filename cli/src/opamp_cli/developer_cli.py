#!/usr/bin/env python3
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

"""Optional bridge from the operator CLI to an installed developer CLI."""

from __future__ import annotations

import logging
import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path

DEVELOPER_CLI_EXECUTABLES = (
    "opamp-dev-cli",
    "opamp-dev-tools",
    "opamp-cli-dev",
)
DEVELOPER_CLI_UNAVAILABLE_EXIT_CODE = 1


def resolve_developer_cli(
    executable_names: Iterable[str] = DEVELOPER_CLI_EXECUTABLES,
) -> str | None:
    """Return the first installed developer CLI executable.

    Parameters:
        executable_names: Ordered executable names accepted for compatibility.
    """

    for executable_name in executable_names:
        executable_path = shutil.which(executable_name)
        if executable_path:
            return executable_path
    return None


def developer_cli_available() -> bool:
    """Return whether an independently installed developer CLI is available."""

    return resolve_developer_cli() is not None


def execute_developer_cli(
    arguments: list[str],
    *,
    repo_root: Path,
    logger: logging.Logger,
) -> int:
    """Run the installed developer CLI against the operator CLI repository.

    Parameters:
        arguments: Developer CLI command tokens supplied after the bridge command.
        repo_root: Repository root forwarded through the developer CLI global option.
        logger: Operator CLI logger receiving resolution and execution diagnostics.

    Returns:
        The developer CLI exit code, or a stable unavailable-command exit code.
    """

    executable_path = resolve_developer_cli()
    if executable_path is None:
        print(
            "The optional opamp-dev-cli package is not installed. "
            "Install opamp-dev-tools to enable developer commands."
        )
        return DEVELOPER_CLI_UNAVAILABLE_EXIT_CODE

    command = [
        executable_path,
        "--repo-root",
        str(repo_root.resolve()),
        *arguments,
    ]
    logger.debug("executing optional developer CLI command=%s", command)
    try:
        completed_process = subprocess.run(  # noqa: S603
            command,
            cwd=str(repo_root.resolve()),
            check=False,
        )
    except OSError as error:
        logger.error("unable to execute developer CLI: %s", error)
        print(f"Unable to execute opamp-dev-cli: {error}")
        return DEVELOPER_CLI_UNAVAILABLE_EXIT_CODE
    return int(completed_process.returncode)
