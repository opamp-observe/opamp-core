"""Claude Desktop target handler for the MCP config utility."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from opamp_mcp_config.targets.base import ApplyResult


class ClaudeTarget:  # pylint: disable=too-few-public-methods
    """Apply OpAMP MCP settings to Claude Desktop configuration."""

    key = "claude"

    def __init__(
        self,
        *,
        path_or_default: Callable[[str, Path], Path],
        claude_config_path: Callable[[], Path],
        build_remote_server_entry: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
        merge_server_entry: Callable[..., None],
    ) -> None:
        self._path_or_default = path_or_default
        self._claude_config_path = claude_config_path
        self._build_remote_server_entry = build_remote_server_entry
        self._merge_server_entry = merge_server_entry

    def apply(self, settings: dict[str, Any], *, dry_run: bool) -> ApplyResult:
        """Write the configured Claude MCP server entry unless previewing."""
        cfg = dict(settings["clients"][self.key])
        config_path = self._path_or_default(
            str(cfg.get("config_path") or ""),
            self._claude_config_path(),
        )
        entry = self._build_remote_server_entry(settings, cfg)
        name = str(cfg.get("name") or "OpAMP Server")
        if not dry_run:
            self._merge_server_entry(
                config_path=config_path,
                section_name="mcpServers",
                server_name=name,
                server_entry=entry,
            )
        return ApplyResult(self.key, f"{config_path} -> mcpServers.{name}", not dry_run)
