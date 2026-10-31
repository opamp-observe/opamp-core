"""LibreChat target handler for the MCP config utility."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from opamp_mcp_config.targets.base import ApplyResult


class LibreChatTarget:  # pylint: disable=too-few-public-methods
    """Apply OpAMP MCP settings to LibreChat YAML configuration."""

    key = "librechat"

    def __init__(
        self,
        *,
        resolve_path: Callable[[str], Path],
        server_urls: Callable[[dict[str, Any]], dict[str, str]],
        build_stdio_server_entry: Callable[[dict[str, Any]], dict[str, Any]],
        merge_librechat_yaml: Callable[[Path, str, dict[str, Any]], None],
    ) -> None:
        self._resolve_path = resolve_path
        self._server_urls = server_urls
        self._build_stdio_server_entry = build_stdio_server_entry
        self._merge_librechat_yaml = merge_librechat_yaml

    def apply(self, settings: dict[str, Any], *, dry_run: bool) -> ApplyResult:
        """Write the configured LibreChat MCP server entry unless previewing."""
        cfg = dict(settings["clients"][self.key])
        config_path = self._resolve_path(str(cfg.get("config_path") or "librechat.yaml"))
        name = str(cfg.get("name") or "opampServer")
        transport = str(cfg.get("transport") or "stdio").strip().lower()
        if transport == "sse":
            entry: dict[str, Any] = {
                "type": "sse",
                "url": self._server_urls(settings)["sse_url"],
            }
        else:
            stdio = self._build_stdio_server_entry(settings)
            entry = {
                "type": "stdio",
                "command": stdio["command"],
                "args": stdio.get("args", []),
                "env": stdio.get("env", {}),
            }
        if str(cfg.get("title") or "").strip():
            entry["title"] = str(cfg["title"])
        if str(cfg.get("description") or "").strip():
            entry["description"] = str(cfg["description"])
        if not dry_run:
            self._merge_librechat_yaml(config_path, name, entry)
        return ApplyResult(self.key, f"{config_path} -> mcpServers.{name}", not dry_run)
