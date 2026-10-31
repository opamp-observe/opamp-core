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

"""Provider-specific async JSON-RPC client for OpAMP MCP connectivity."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import httpx

logger = logging.getLogger(__name__)
DEFAULT_MCP_PROTOCOL_VERSION = "2025-06-18"
DEFAULT_MCP_PROTOCOL_VERSION_ATTEMPTS = (
    DEFAULT_MCP_PROTOCOL_VERSION,
    "2025-03-26",
)
MAX_DEBUG_PAYLOAD_CHARS = 8000
MCP_CONNECTION_MODE_AUTO = "auto"
MCP_CONNECTION_MODE_JSON = "json"
MCP_CONNECTION_MODE_SSE = "sse"
MCP_CONNECTION_MODES = {
    MCP_CONNECTION_MODE_AUTO,
    MCP_CONNECTION_MODE_JSON,
    MCP_CONNECTION_MODE_SSE,
}


def _parse_sse_event_payload(event_payload: str) -> dict[str, Any] | None:
    """Parse one SSE event payload into a JSON object when possible."""
    payload = event_payload.strip()
    if not payload or payload == "[DONE]":
        return None
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


class MCPServerUnavailableError(RuntimeError):
    """Raised when the broker cannot reach the OpAMP MCP server."""


class MCPClient:
    """Async client for OpAMP provider MCP JSON-RPC operations."""

    def __init__(
        self,
        mcp_url: str,
        timeout_seconds: int = 30,
        *,
        connection_mode: str = MCP_CONNECTION_MODE_AUTO,
        protocol_version_attempts: tuple[str, ...] | list[str] | None = None,
    ) -> None:
        """Create an MCP HTTP client with a reusable async connection pool.

        Why this approach:
        a long-lived ``httpx.AsyncClient`` reduces connection overhead during
        repeated tool operations in active Slack conversations.

        Args:
            mcp_url: Full HTTP endpoint URL for MCP JSON-RPC requests.
            timeout_seconds: Per-request timeout applied by ``httpx``.
            connection_mode: Response handling strategy (`auto`, `json`, `sse`).
            protocol_version_attempts: Ordered protocol versions attempted for
                `initialize`. Defaults to known compatible versions.

        Returns:
            None: Stores client configuration for later RPC calls.
        """
        self.mcp_url = mcp_url
        self.timeout_seconds = timeout_seconds
        self._client = httpx.AsyncClient(timeout=timeout_seconds)
        self._mcp_session_id: str | None = None
        self._mcp_protocol_version: str = DEFAULT_MCP_PROTOCOL_VERSION
        normalized_mode = str(connection_mode or MCP_CONNECTION_MODE_AUTO).strip().lower()
        if normalized_mode not in MCP_CONNECTION_MODES:
            normalized_mode = MCP_CONNECTION_MODE_AUTO
        self._connection_mode = normalized_mode
        raw_protocol_versions = (
            tuple(protocol_version_attempts)
            if protocol_version_attempts
            else DEFAULT_MCP_PROTOCOL_VERSION_ATTEMPTS
        )
        normalized_protocol_versions = tuple(
            str(version).strip() for version in raw_protocol_versions if str(version).strip()
        )
        self._protocol_version_attempts = (
            normalized_protocol_versions
            if normalized_protocol_versions
            else DEFAULT_MCP_PROTOCOL_VERSION_ATTEMPTS
        )

    async def close(self) -> None:
        """Close the underlying HTTP client to release network resources.

        Returns:
            None: Closes sockets and connection-pool state.
        """
        await self._client.aclose()

    @staticmethod
    def _ascii_safe_text(value: str, *, limit: int | None = None) -> str:
        """Return ASCII-safe text suitable for cross-platform logging."""
        normalized = str(value or "").strip()
        if not normalized:
            return "<empty>"
        if limit is not None and limit >= 0:
            normalized = normalized[:limit]
        return normalized.encode("ascii", "backslashreplace").decode("ascii")

    @staticmethod
    def _debug_payload_preview(payload: Any) -> str:
        """Return a bounded text preview for debug logging."""
        try:
            rendered = json.dumps(payload, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            rendered = str(payload)
        truncated = len(rendered) > MAX_DEBUG_PAYLOAD_CHARS
        preview = MCPClient._ascii_safe_text(rendered, limit=MAX_DEBUG_PAYLOAD_CHARS)
        if truncated:
            return preview + "...<truncated>"
        return preview

    async def _rpc(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        include_session_header: bool = True,
        protocol_version: str | None = None,
    ) -> dict[str, Any]:
        """Send one JSON-RPC request and return the ``result`` payload."""
        request_id = str(uuid.uuid4())
        payload = self._build_rpc_payload(
            request_id=request_id,
            method=method,
            params=params,
        )
        resolved_protocol_version = protocol_version or self._mcp_protocol_version
        headers = self._build_rpc_headers(
            resolved_protocol_version=resolved_protocol_version,
            include_session_header=include_session_header,
        )
        try:
            async with self._client.stream(
                "POST",
                self.mcp_url,
                json=payload,
                headers=headers,
            ) as response:
                self._capture_session_header(response)
                await self._raise_for_status(method=method, response=response)
                data = await self._decode_rpc_response(
                    method=method,
                    request_id=request_id,
                    response=response,
                )
        except httpx.RequestError as exc:
            raise MCPServerUnavailableError(
                f"unable to reach MCP server at {self.mcp_url}: {exc}"
            ) from exc

        data = self._validate_response_envelope(method=method, data=data)
        logger.debug(
            "MCP response envelope method=%s payload=%s",
            method,
            self._debug_payload_preview(data),
        )
        if "error" in data:
            raise RuntimeError(f"MCP error calling {method}: {data['error']}")
        result = data.get("result", {})
        logger.debug(
            "MCP response result method=%s payload=%s",
            method,
            self._debug_payload_preview(result),
        )
        return result

    @staticmethod
    def _build_rpc_payload(
        *,
        request_id: str,
        method: str,
        params: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Build standard JSON-RPC request envelope."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }

    def _build_rpc_headers(
        self,
        *,
        resolved_protocol_version: str,
        include_session_header: bool,
    ) -> dict[str, str]:
        """Build MCP request headers for current connection mode."""
        headers = {
            "Accept": self._resolve_accept_header(),
            "MCP-Protocol-Version": resolved_protocol_version,
        }
        if include_session_header and self._mcp_session_id:
            headers["MCP-Session-Id"] = self._mcp_session_id
        return headers

    def _resolve_accept_header(self) -> str:
        """Return HTTP Accept header value based on connection mode."""
        if self._connection_mode == MCP_CONNECTION_MODE_AUTO:
            return "application/json, text/event-stream"
        if self._connection_mode == MCP_CONNECTION_MODE_JSON:
            return "application/json"
        return "text/event-stream"

    def _capture_session_header(self, response: httpx.Response) -> None:
        """Persist MCP session id header when present on response."""
        response_session_id = (
            response.headers.get("MCP-Session-Id")
            or response.headers.get("mcp-session-id")
        )
        if response_session_id:
            self._mcp_session_id = response_session_id

    async def _raise_for_status(self, *, method: str, response: httpx.Response) -> None:
        """Raise typed errors for unsuccessful HTTP status responses."""
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            response_body = (await response.aread()).decode(
                exc.response.encoding or "utf-8",
                errors="replace",
            ).strip()
            response_body_summary = self._ascii_safe_text(response_body, limit=500)
            if status_code >= 500:
                raise MCPServerUnavailableError(
                    f"MCP server returned {status_code} for {method}: "
                    f"{response_body_summary}"
                ) from exc
            raise

    async def _decode_rpc_response(
        self,
        *,
        method: str,
        request_id: str,
        response: httpx.Response,
    ) -> dict[str, Any]:
        """Decode JSON or SSE response envelope for one MCP RPC request."""
        content_type = str(response.headers.get("content-type", "")).lower()
        if self._should_decode_as_sse(content_type):
            return await self._decode_sse_response(
                method=method,
                request_id=request_id,
                content_type=content_type,
                response=response,
            )
        if self._should_decode_as_json():
            return await self._decode_json_response(
                method=method,
                content_type=content_type,
                response=response,
            )
        raise RuntimeError(
            "MCP response decode failed for "
            f"{method}: unsupported connection mode {self._connection_mode}"
        )

    def _should_decode_as_sse(self, content_type: str) -> bool:
        """Return whether response should be decoded as SSE event stream."""
        if self._connection_mode == MCP_CONNECTION_MODE_SSE:
            return True
        return self._connection_mode == MCP_CONNECTION_MODE_AUTO and "text/event-stream" in content_type

    def _should_decode_as_json(self) -> bool:
        """Return whether response should be decoded as JSON body."""
        return self._connection_mode in {MCP_CONNECTION_MODE_AUTO, MCP_CONNECTION_MODE_JSON}

    async def _decode_sse_response(
        self,
        *,
        method: str,
        request_id: str,
        content_type: str,
        response: httpx.Response,
    ) -> dict[str, Any]:
        """Decode SSE payload stream into a JSON-RPC response envelope."""
        data: dict[str, Any] | None = None
        latest_payload: dict[str, Any] | None = None
        data_lines: list[str] = []

        async for raw_line in response.aiter_lines():
            line = raw_line.rstrip("\r")
            if line == "":
                parsed = _parse_sse_event_payload("\n".join(data_lines)) if data_lines else None
                data_lines = []
                if parsed is None:
                    continue
                if str(parsed.get("id", "")) == request_id:
                    data = parsed
                    break
                latest_payload = parsed
                continue
            if line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
        else:
            trailing = _parse_sse_event_payload("\n".join(data_lines)) if data_lines else None
            if trailing is not None:
                if str(trailing.get("id", "")) == request_id:
                    data = trailing
                else:
                    latest_payload = trailing
            if data is None and latest_payload is not None:
                data = latest_payload

        if data is None:
            raise RuntimeError(
                "MCP response decode failed for "
                f"{method}: content_type={content_type} "
                "body=<no decodable SSE data payload>"
            )
        return data

    async def _decode_json_response(
        self,
        *,
        method: str,
        content_type: str,
        response: httpx.Response,
    ) -> dict[str, Any]:
        """Decode standard JSON response body into a response envelope."""
        raw_body = await response.aread()
        body_text = raw_body.decode(response.encoding or "utf-8", errors="replace")
        try:
            parsed_data = json.loads(body_text)
        except json.JSONDecodeError as exc:
            body_summary = self._ascii_safe_text(body_text, limit=500)
            raise RuntimeError(
                f"MCP response decode failed for {method}: "
                f"content_type={content_type or '<unknown>'} "
                f"body={body_summary}"
            ) from exc
        if not isinstance(parsed_data, dict):
            raise RuntimeError(
                f"MCP response is not a JSON object for {method}: "
                f"{type(parsed_data).__name__}"
            )
        return parsed_data

    @staticmethod
    def _validate_response_envelope(*, method: str, data: dict[str, Any] | None) -> dict[str, Any]:
        """Validate decoded response envelope shape."""
        if data is None:
            raise RuntimeError(f"MCP response is empty for {method}")
        if not isinstance(data, dict):
            raise RuntimeError(
                f"MCP response is not a JSON object for {method}: "
                f"{type(data).__name__}"
            )
        return data

    async def discover_tools(self) -> list[dict[str, Any]]:
        """Initialize provider MCP and return discovered tool definitions."""
        await self.initialize()
        result = await self.list_tools()
        raw_tools = result.get("tools", [])
        if not isinstance(raw_tools, list):
            return []
        return [
            tool for tool in raw_tools if isinstance(tool, dict) and "name" in tool
        ]

    async def initialize(
        self,
        *,
        protocol_version: str | None = None,
        client_info: dict[str, Any] | None = None,
        capabilities: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Initialize the upstream MCP session with version fallback."""
        requested_protocol_version = str(protocol_version or "").strip()
        attempts: list[str] = []
        if requested_protocol_version:
            attempts.append(requested_protocol_version)
        for fallback_version in self._protocol_version_attempts:
            if fallback_version not in attempts:
                attempts.append(fallback_version)

        self._mcp_session_id = None
        initialize_result: dict[str, Any] | None = None
        initialize_error: Exception | None = None
        for attempted_protocol_version in attempts:
            try:
                initialize_result = await self._rpc(
                    "initialize",
                    {
                        "protocolVersion": attempted_protocol_version,
                        "clientInfo": client_info
                        or {
                            "name": "opamp-conversation-broker",
                            "version": "0.1.0",
                        },
                        "capabilities": capabilities or {},
                    },
                    include_session_header=False,
                    protocol_version=attempted_protocol_version,
                )
                self._mcp_protocol_version = attempted_protocol_version
                break
            except Exception as exc:  # pragma: no cover - defensive compatibility.
                initialize_error = exc
                logger.warning(
                    "MCP initialize attempt failed for protocol version %s: %s",
                    attempted_protocol_version,
                    exc,
                )
        if initialize_result is None:
            if initialize_error is not None:
                raise initialize_error
            raise RuntimeError("MCP initialize failed without an explicit error")
        return initialize_result

    async def list_tools(self) -> dict[str, Any]:
        """Return the raw ``tools/list`` result from the provider."""
        return await self._rpc("tools/list", {})

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Invoke one provider MCP tool by name."""
        return await self._rpc(
            "tools/call",
            {"name": name, "arguments": arguments},
        )
