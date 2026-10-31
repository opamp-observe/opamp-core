"""Shared target result and protocol definitions for MCP client targets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ApplyResult:
    """Summarize one client-target apply operation."""

    client: str
    detail: str
    changed: bool


class ClientTarget(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol implemented by each MCP client target handler."""

    key: str

    def apply(self, settings: dict[str, Any], *, dry_run: bool) -> ApplyResult:
        """Apply client-specific configuration changes."""
        ...
