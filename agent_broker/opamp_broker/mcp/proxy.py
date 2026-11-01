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

"""Broker-hosted MCP proxy layer for local desktop clients.

This module exposes a small MCP-compatible HTTP surface so tools like Claude
Desktop can talk to the broker, while the broker continues to call the OpAMP
provider as the upstream MCP server.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from quart import Quart, Response, current_app, request

from opamp_broker.mcp.client import MCPClient

logger = logging.getLogger(__name__)

HEADER_MCP_SESSION_ID = "MCP-Session-Id"
HEADER_MCP_PROTOCOL_VERSION = "MCP-Protocol-Version"
JSONRPC_VERSION = "2.0"
JSONRPC_METHOD_INITIALIZE = "initialize"
JSONRPC_METHOD_TOOLS_LIST = "tools/list"
JSONRPC_METHOD_TOOLS_CALL = "tools/call"
JSONRPC_ERROR_PARSE = -32700
JSONRPC_ERROR_INVALID_REQUEST = -32600
JSONRPC_ERROR_METHOD_NOT_FOUND = -32601
JSONRPC_ERROR_INVALID_PARAMS = -32602
JSONRPC_ERROR_INTERNAL = -32603
JSONRPC_ERROR_SESSION_REQUIRED = -32001
JSONRPC_ERROR_UPSTREAM = -32002
APP_CONFIG_KEY_PROXY = "opamp_broker.mcp_proxy"


class MCPProxyClient(Protocol):
    """Client surface required by the stateful MCP proxy."""

    async def initialize(
        self,
        *,
        protocol_version: str | None = None,
        client_info: dict[str, Any] | None = None,
        capabilities: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    async def list_tools(self) -> dict[str, Any]: ...

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...

    async def close(self) -> None: ...


def _jsonrpc_result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    """Build a JSON-RPC success envelope."""
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}


def _jsonrpc_error(
    request_id: Any,
    *,
    code: int,
    message: str,
    data: Any | None = None,
) -> dict[str, Any]:
    """Build a JSON-RPC error envelope."""
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "error": error}


@dataclass(slots=True)
class MCPProxySession:
    """One broker-side MCP session bound to one upstream provider client."""

    broker_session_id: str
    client: MCPProxyClient


class MCPProxyService:
    """Stateful broker-side MCP proxy for local desktop integrations."""

    def __init__(
        self,
        *,
        mcp_url: str,
        timeout_seconds: int,
        connection_mode: str,
        protocol_version_attempts: tuple[str, ...],
        client_factory: Callable[..., MCPProxyClient] = MCPClient,
    ) -> None:
        self._mcp_url = mcp_url
        self._timeout_seconds = timeout_seconds
        self._connection_mode = connection_mode
        self._protocol_version_attempts = protocol_version_attempts
        self._client_factory = client_factory
        self._sessions: dict[str, MCPProxySession] = {}
        self._lock = asyncio.Lock()

    async def close(self) -> None:
        """Close all upstream MCP clients and clear proxy sessions."""
        async with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            await session.client.close()

    def _build_client(self) -> MCPProxyClient:
        """Create one upstream client using the proxy's configured transport."""
        return self._client_factory(
            self._mcp_url,
            timeout_seconds=self._timeout_seconds,
            connection_mode=self._connection_mode,
            protocol_version_attempts=self._protocol_version_attempts,
        )

    async def initialize(
        self,
        *,
        protocol_version: str | None,
        client_info: dict[str, Any] | None,
        capabilities: dict[str, Any] | None,
    ) -> tuple[str, dict[str, Any]]:
        """Create one broker-side session and initialize its upstream client."""
        client = self._build_client()
        try:
            result = await client.initialize(
                protocol_version=protocol_version,
                client_info=client_info,
                capabilities=capabilities,
            )
        except Exception:
            await client.close()
            raise

        broker_session_id = str(uuid.uuid4())
        session = MCPProxySession(
            broker_session_id=broker_session_id,
            client=client,
        )
        async with self._lock:
            self._sessions[broker_session_id] = session
        return broker_session_id, result

    async def _require_session(self, broker_session_id: str | None) -> MCPProxySession:
        """Return one active proxy session or raise ``KeyError``."""
        if not broker_session_id:
            raise KeyError("missing MCP session id")
        async with self._lock:
            session = self._sessions.get(broker_session_id)
        if session is None:
            raise KeyError(f"unknown MCP session id: {broker_session_id}")
        return session

    async def list_tools(self, broker_session_id: str | None) -> dict[str, Any]:
        """Proxy ``tools/list`` for one existing broker session."""
        session = await self._require_session(broker_session_id)
        return await session.client.list_tools()

    async def call_tool(
        self,
        broker_session_id: str | None,
        *,
        name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Proxy ``tools/call`` for one existing broker session."""
        session = await self._require_session(broker_session_id)
        return await session.client.call_tool(name, arguments)


def create_mcp_proxy_app(
    *,
    proxy_service: MCPProxyService,
    mcp_path: str = "/mcp",
) -> Quart:
    """Create a Quart app exposing a minimal MCP proxy HTTP surface."""
    normalized_path = str(mcp_path or "/mcp").strip() or "/mcp"
    if not normalized_path.startswith("/"):
        normalized_path = f"/{normalized_path}"

    app = Quart(__name__)
    app.config[APP_CONFIG_KEY_PROXY] = proxy_service

    @app.get("/")
    async def root() -> Response:
        """Return a lightweight health payload for local diagnostics."""
        payload = {"ok": True, "service": "opamp-broker-mcp-proxy", "mcp_path": normalized_path}
        return Response(
            response=json.dumps(payload),
            status=200,
            content_type="application/json",
        )

    @app.post(normalized_path)
    async def mcp() -> Response:
        """Proxy one MCP JSON-RPC request to the configured upstream server."""
        proxy = current_app.config[APP_CONFIG_KEY_PROXY]
        try:
            payload = await request.get_json(force=True)
        except Exception as exc:
            return _response(
                _jsonrpc_error(
                    None,
                    code=JSONRPC_ERROR_PARSE,
                    message="invalid JSON request body",
                    data=str(exc),
                ),
                status=400,
            )

        if not isinstance(payload, dict):
            return _response(
                _jsonrpc_error(
                    None,
                    code=JSONRPC_ERROR_INVALID_REQUEST,
                    message="JSON-RPC request must be an object",
                ),
                status=400,
            )

        request_id = payload.get("id")
        method = str(payload.get("method") or "").strip()
        params = payload.get("params")
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return _response(
                _jsonrpc_error(
                    request_id,
                    code=JSONRPC_ERROR_INVALID_PARAMS,
                    message="JSON-RPC params must be an object",
                )
            )

        request_session_id = (
            request.headers.get(HEADER_MCP_SESSION_ID)
            or request.headers.get(HEADER_MCP_SESSION_ID.lower())
        )
        response_headers: dict[str, str] = {}
        try:
            if method == JSONRPC_METHOD_INITIALIZE:
                broker_session_id, result = await proxy.initialize(
                    protocol_version=str(params.get("protocolVersion") or "").strip() or None,
                    client_info=_as_dict(params.get("clientInfo")),
                    capabilities=_as_dict(params.get("capabilities")),
                )
                response_headers[HEADER_MCP_SESSION_ID] = broker_session_id
                negotiated_protocol = str(
                    result.get("protocolVersion")
                    or params.get("protocolVersion")
                    or ""
                ).strip()
                if negotiated_protocol:
                    response_headers[HEADER_MCP_PROTOCOL_VERSION] = negotiated_protocol
                return _response(
                    _jsonrpc_result(request_id, result),
                    headers=response_headers,
                )

            if method == JSONRPC_METHOD_TOOLS_LIST:
                result = await proxy.list_tools(request_session_id)
                return _response(
                    _jsonrpc_result(request_id, result),
                    headers=response_headers,
                )

            if method == JSONRPC_METHOD_TOOLS_CALL:
                tool_name = str(params.get("name") or "").strip()
                if not tool_name:
                    return _response(
                        _jsonrpc_error(
                            request_id,
                            code=JSONRPC_ERROR_INVALID_PARAMS,
                            message="tools/call requires a non-empty tool name",
                        ),
                    )
                arguments = _as_dict(params.get("arguments")) or {}
                result = await proxy.call_tool(
                    request_session_id,
                    name=tool_name,
                    arguments=arguments,
                )
                return _response(
                    _jsonrpc_result(request_id, result),
                    headers=response_headers,
                )

            return _response(
                _jsonrpc_error(
                    request_id,
                    code=JSONRPC_ERROR_METHOD_NOT_FOUND,
                    message=f"unsupported MCP method: {method}",
                ),
            )
        except KeyError as exc:
            return _response(
                _jsonrpc_error(
                    request_id,
                    code=JSONRPC_ERROR_SESSION_REQUIRED,
                    message="an active MCP session is required",
                    data=str(exc),
                ),
            )
        except Exception as exc:
            logger.warning("broker MCP proxy request failed method=%s error=%s", method, exc)
            return _response(
                _jsonrpc_error(
                    request_id,
                    code=JSONRPC_ERROR_UPSTREAM,
                    message="upstream MCP request failed",
                    data=str(exc),
                ),
            )

    return app


def _as_dict(value: Any) -> dict[str, Any] | None:
    """Return ``value`` when it is a dictionary, else ``None``."""
    if isinstance(value, dict):
        return value
    return None


def _response(
    payload: dict[str, Any],
    *,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> Response:
    """Build a JSON response with optional MCP headers."""
    response = Response(
        response=json.dumps(payload),
        status=status,
        content_type="application/json",
    )
    for key, value in (headers or {}).items():
        response.headers[key] = value
    return response
