"""Gemini target handler for the MCP config utility."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from opamp_mcp_config.targets.base import ApplyResult


class GeminiTarget:  # pylint: disable=too-few-public-methods
    """Apply OpAMP MCP settings to Gemini CLI configuration."""

    key = "gemini"

    def __init__(
        self,
        *,
        path_or_default: Callable[[str, Path], Path],
        gemini_config_path: Callable[[], Path],
        build_client_entry: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
        merge_server_entry: Callable[..., None],
    ) -> None:
        self._path_or_default = path_or_default
        self._gemini_config_path = gemini_config_path
        self._build_client_entry = build_client_entry
        self._merge_server_entry = merge_server_entry

    def apply(self, settings: dict[str, Any], *, dry_run: bool) -> ApplyResult:
        """Write the configured Gemini MCP server entry unless previewing."""
        cfg = dict(settings["clients"][self.key])
        config_path = self._path_or_default(
            str(cfg.get("config_path") or ""),
            self._gemini_config_path(),
        )
        entry = self._build_client_entry(settings, cfg)
        if "trust" in cfg:
            entry["trust"] = bool(cfg.get("trust"))
        name = str(cfg.get("name") or "opampServer")
        if not dry_run:
            self._merge_server_entry(
                config_path=config_path,
                section_name="mcpServers",
                server_name=name,
                server_entry=entry,
            )
        return ApplyResult(self.key, f"{config_path} -> mcpServers.{name}", not dry_run)
