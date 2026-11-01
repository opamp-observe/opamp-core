"""VS Code target handler for the MCP config utility."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from opamp_mcp_config.targets.base import ApplyResult


class VSCodeTarget:  # pylint: disable=too-few-public-methods
    """Apply OpAMP MCP settings to VS Code workspace configuration."""

    key = "vscode"

    def __init__(
        self,
        *,
        path_or_default: Callable[[str, Path], Path],
        repo_root: Callable[[], Path],
        build_client_entry: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
        merge_server_entry: Callable[..., None],
    ) -> None:
        self._path_or_default = path_or_default
        self._repo_root = repo_root
        self._build_client_entry = build_client_entry
        self._merge_server_entry = merge_server_entry

    def apply(self, settings: dict[str, Any], *, dry_run: bool) -> ApplyResult:
        """Write the configured VS Code MCP server entry unless previewing."""
        cfg = dict(settings["clients"][self.key])
        config_path = self._path_or_default(
            str(cfg.get("config_path") or ""),
            self._repo_root() / ".vscode/mcp.json",
        )
        entry = self._build_client_entry(settings, cfg)
        entry.setdefault("type", "stdio")
        name = str(cfg.get("name") or "opampServer")
        if not dry_run:
            self._merge_server_entry(
                config_path=config_path,
                section_name="servers",
                server_name=name,
                server_entry=entry,
            )
        return ApplyResult(self.key, f"{config_path} -> servers.{name}", not dry_run)
