"""Codex target handler for the MCP config utility."""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from typing import Any

from opamp_mcp_config.targets.base import ApplyResult

ARGUMENTS_KEY = "args"
CLIENTS_KEY = "clients"
CODEX_EXECUTABLE_NAME = "codex"
CODEX_UNAVAILABLE_ERROR = "codex CLI is not available on PATH"
COMMAND_KEY = "command"
COMMAND_SEPARATOR_ARGUMENT = "--"
DEFAULT_SERVER_NAME = "opamp-server"
ENVIRONMENT_KEY = "env"
ENVIRONMENT_ARGUMENT = "--env"
MCP_ADD_ARGUMENTS = ("mcp", "add")
MCP_REMOVE_ARGUMENTS = ("mcp", "remove")
NAME_KEY = "name"


class CodexTarget:  # pylint: disable=too-few-public-methods
    """Apply OpAMP MCP settings by invoking the Codex CLI.

    Attributes
    ----------
    key:
        Stable client key used to read the Codex settings object.
    _build_stdio_server_entry:
        Injected builder that returns the command and environment for the MCP server.

    """

    key = CODEX_EXECUTABLE_NAME

    def __init__(
        self,
        *,
        build_stdio_server_entry: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        """Store the builder used to translate shared settings into a Codex entry.

        Parameters
        ----------
        build_stdio_server_entry:
            Callable that creates a standard-input/output MCP server definition.

        """
        self._build_stdio_server_entry = build_stdio_server_entry

    def apply(self, settings: dict[str, Any], *, dry_run: bool) -> ApplyResult:
        """Build and optionally apply Codex MCP configuration.

        Parameters
        ----------
        settings:
            Shared MCP configuration containing the Codex client settings.
        dry_run:
            When true, return the command without invoking the Codex executable.

        Returns
        -------
        ApplyResult
            Command description and whether the settings were applied.

        """
        client_configuration = dict(settings[CLIENTS_KEY][self.key])
        name = str(client_configuration.get(NAME_KEY) or DEFAULT_SERVER_NAME)
        entry = self._build_stdio_server_entry(settings)
        command = [CODEX_EXECUTABLE_NAME, *MCP_ADD_ARGUMENTS, name]
        for environment_key, environment_value in entry.get(ENVIRONMENT_KEY, {}).items():
            command.extend([ENVIRONMENT_ARGUMENT, f"{environment_key}={environment_value}"])
        command.append(COMMAND_SEPARATOR_ARGUMENT)
        command.append(str(entry[COMMAND_KEY]))
        command.extend(str(item) for item in entry.get(ARGUMENTS_KEY, []))
        if not dry_run:
            codex_executable = shutil.which(CODEX_EXECUTABLE_NAME)
            if codex_executable is None:
                raise RuntimeError(CODEX_UNAVAILABLE_ERROR)
            remove_command = [codex_executable, *MCP_REMOVE_ARGUMENTS, name]
            apply_command = [codex_executable, *command[1:]]
            # The executable is resolved explicitly and arguments are passed without a shell.
            subprocess.run(remove_command, check=False)  # noqa: S603
            subprocess.run(apply_command, check=True)  # noqa: S603
        return ApplyResult(self.key, " ".join(command), not dry_run)
