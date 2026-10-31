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

"""Tests for MCP client error reporting and console-safe diagnostics."""

import asyncio
import importlib
import sys
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_BROKER_ROOT = REPO_ROOT / "agent_broker"
if str(AGENT_BROKER_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_BROKER_ROOT))

mcp_client_module = importlib.import_module("opamp_broker.mcp.client")
MCPClient = mcp_client_module.MCPClient
MCPServerUnavailableError = mcp_client_module.MCPServerUnavailableError


def test_debug_payload_preview_is_ascii_safe() -> None:
    """Debug payload previews should stay printable on cp1252 consoles."""
    preview = MCPClient._debug_payload_preview(
        {"emoji": "😀", "replacement": "\ufffd", "plain": "ok"}
    )

    assert "\\U0001f600" in preview
    assert "\\ufffd" in preview
    preview.encode("cp1252")


def test_raise_for_status_uses_ascii_safe_body_summary() -> None:
    """5xx errors should render ASCII-safe body summaries in exception text."""
    client = MCPClient("http://localhost/mcp")
    response = httpx.Response(
        500,
        content=b"\xff\xfeoops",
        request=httpx.Request("POST", "http://localhost/mcp"),
    )

    try:
        with pytest.raises(MCPServerUnavailableError) as exc_info:
            asyncio.run(client._raise_for_status(method="tools/list", response=response))
    finally:
        asyncio.run(client.close())

    message = str(exc_info.value)
    assert "MCP server returned 500 for tools/list:" in message
    assert "\\ufffd\\ufffdoops" in message
    message.encode("cp1252")


def test_decode_json_response_uses_ascii_safe_body_summary() -> None:
    """JSON decode failures should keep exception text Windows-console safe."""
    client = MCPClient("http://localhost/mcp")
    response = httpx.Response(
        200,
        content=b'{"x":\xff}',
        headers={"content-type": "application/json"},
        request=httpx.Request("POST", "http://localhost/mcp"),
    )

    try:
        with pytest.raises(RuntimeError) as exc_info:
            asyncio.run(
                client._decode_json_response(
                    method="tools/list",
                    content_type="application/json",
                    response=response,
                )
            )
    finally:
        asyncio.run(client.close())

    message = str(exc_info.value)
    assert "MCP response decode failed for tools/list:" in message
    assert 'body={"x":\\ufffd}' in message
    message.encode("cp1252")
