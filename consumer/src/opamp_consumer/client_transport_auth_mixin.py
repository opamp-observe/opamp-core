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

"""Transport + authorization mixin extracted from the abstract client module."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, TypeVar, cast

import httpx

from opamp_consumer import config as consumer_config
from opamp_consumer.client_transport import send_http_message, send_websocket_message
from opamp_consumer.proto import opamp_pb2
from opamp_consumer.remote_config_status import mark_remote_config_status_sent
from shared.opamp_config import OPAMP_HTTP_PATH

TRANSPORT_HTTP = "http"  # Transport selector for HTTP polling mode.
TRANSPORT_WEBSOCKET = "websocket"  # Transport selector for WebSocket mode.
ENV_OPAMP_TOKEN = "OpAMP-token"  # Requested env var name for outbound OpAMP token.
HEADER_AUTHORIZATION = "Authorization"  # HTTP/WebSocket header key for provider auth token.
AUTH_RETRY_STATUS_CODES = {401, 403}  # Status codes that trigger IDP credential renegotiation.

if TYPE_CHECKING:
    from opamp_consumer.abstract_client import OpAMPClientData
    from opamp_consumer.config import ConsumerConfig


_T = TypeVar("_T")


def _legacy_transport_symbol(name: str, default: _T) -> _T:
    """Resolve transport symbols from legacy abstract_client module when present."""
    try:
        from opamp_consumer import abstract_client as legacy_abstract_client  # noqa: PLC0415
    except Exception:
        return default
    value = getattr(legacy_abstract_client, name, default)
    return cast(_T, value)


class ClientTransportAuthorizationMixin:
    """Shared transport send logic and authorization-header resolution."""
    data: OpAMPClientData

    @property
    def config(self) -> ConsumerConfig:
        """Return active consumer configuration for this client."""
        raise NotImplementedError

    def _populate_agent_to_server(
        self, msg: opamp_pb2.AgentToServer
    ) -> opamp_pb2.AgentToServer:
        """Populate outbound AgentToServer payload with local state."""
        raise NotImplementedError

    def _handle_server_to_agent(self, reply: opamp_pb2.ServerToAgent) -> bool:
        """Delegate reply handling to the next mixin in the MRO chain."""
        handler = getattr(super(), "_handle_server_to_agent", None)
        if handler is None:
            raise NotImplementedError("_handle_server_to_agent is not implemented")
        return cast(bool, handler(reply))

    async def send_http(self, msg: opamp_pb2.AgentToServer) -> opamp_pb2.ServerToAgent:
        """Send an AgentToServer message via HTTP and return the response.

        Args:
            msg: Populated AgentToServer payload to send.

        Returns:
            Parsed ServerToAgent reply from the provider.
        """
        send_http_fn = _legacy_transport_symbol("send_http_message", send_http_message)
        authorization_header = await self._resolve_authorization_header_value()
        try:
            return await send_http_fn(
                msg=msg,
                base_url=self.data.base_url,
                opamp_http_path=OPAMP_HTTP_PATH,
                handle_reply=self._handle_server_to_agent,
                authorization_header=authorization_header,
                tls_verify=self.config.tls_verify_server,
                tls_ca_file=self.config.tls_ca_file,
            )
        except Exception as err:
            if not self._should_retry_idp_authorization(err):
                raise
            logging.getLogger(__name__).info(
                "HTTP auth failure detected; renegotiating IDP token and retrying request"
            )
            authorization_header = await self._resolve_authorization_header_value(
                force_refresh=True
            )
            return await send_http_fn(
                msg=msg,
                base_url=self.data.base_url,
                opamp_http_path=OPAMP_HTTP_PATH,
                handle_reply=self._handle_server_to_agent,
                authorization_header=authorization_header,
                tls_verify=self.config.tls_verify_server,
                tls_ca_file=self.config.tls_ca_file,
            )

    async def send(
        self,
        msg: opamp_pb2.AgentToServer | None = None,
        *,
        send_as_is: bool = False,
    ) -> opamp_pb2.ServerToAgent | None:
        """Send an AgentToServer message using the configured transport.

        Args:
            msg: Optional outbound payload. A new payload is built when omitted.
            send_as_is: When True, skip automatic payload population.

        Returns:
            ServerToAgent reply when send succeeds; otherwise None.
        """
        if not send_as_is:
            if msg is None:
                msg = opamp_pb2.AgentToServer()
            msg = self._populate_agent_to_server(msg)
        response: opamp_pb2.ServerToAgent | None = None
        transport = (self.config.transport or TRANSPORT_HTTP).strip().lower()
        if transport == TRANSPORT_WEBSOCKET:
            try:
                response = await self.send_websocket(msg)
            except Exception as err:
                logging.getLogger(__name__).warning(
                    "Error sending websocket client-to-server message\n %s",
                    self._transport_error_details(
                        transport=TRANSPORT_WEBSOCKET,
                        err=err,
                    ),
                )
        if response is not None:
            mark_remote_config_status_sent(data=self.data, msg=msg)
            if not send_as_is and self.data.full_update_controller is not None:
                self.data.full_update_controller.update_sent()
            return response

        try:
            response = await self.send_http(msg)
            mark_remote_config_status_sent(data=self.data, msg=msg)
            if not send_as_is and self.data.full_update_controller is not None:
                self.data.full_update_controller.update_sent()
            return response
        except Exception as err:
            logging.getLogger(__name__).warning(
                "Error sending HTTP client-to-server message\n %s",
                self._transport_error_details(
                    transport=TRANSPORT_HTTP,
                    err=err,
                ),
            )
        return None

    async def send_websocket(
        self, msg: opamp_pb2.AgentToServer
    ) -> opamp_pb2.ServerToAgent:
        """Send an AgentToServer message via WebSocket and return the response.

        Args:
            msg: Populated AgentToServer payload to send.

        Returns:
            Parsed ServerToAgent reply from the provider.
        """
        send_websocket_fn = _legacy_transport_symbol(
            "send_websocket_message",
            send_websocket_message,
        )
        authorization_header = await self._resolve_authorization_header_value()
        try:
            return await send_websocket_fn(
                msg=msg,
                base_url=self.data.base_url,
                opamp_http_path=OPAMP_HTTP_PATH,
                handle_reply=self._handle_server_to_agent,
                authorization_header=authorization_header,
                tls_verify=self.config.tls_verify_server,
                tls_ca_file=self.config.tls_ca_file,
            )
        except Exception as err:
            if not self._should_retry_idp_authorization(err):
                raise
            logging.getLogger(__name__).info(
                "WebSocket auth failure detected; renegotiating IDP token and retrying request"
            )
            authorization_header = await self._resolve_authorization_header_value(
                force_refresh=True
            )
            return await send_websocket_fn(
                msg=msg,
                base_url=self.data.base_url,
                opamp_http_path=OPAMP_HTTP_PATH,
                handle_reply=self._handle_server_to_agent,
                authorization_header=authorization_header,
                tls_verify=self.config.tls_verify_server,
                tls_ca_file=self.config.tls_ca_file,
            )

    def _server_authorization_mode(self) -> str:
        """Return normalized configured server authorization mode."""
        raw_mode = str(
            self.config.server_authorization or consumer_config.DEFAULT_SERVER_AUTHORIZATION
        ).strip().lower()
        if raw_mode in (
            consumer_config.SERVER_AUTHORIZATION_NONE,
            consumer_config.SERVER_AUTHORIZATION_ENV_VAR,
            consumer_config.SERVER_AUTHORIZATION_CONFIG_VAR,
            consumer_config.SERVER_AUTHORIZATION_IDP,
        ):
            return raw_mode
        return consumer_config.DEFAULT_SERVER_AUTHORIZATION

    def _record_authorization_header(
        self,
        *,
        header_name: str,
        header_value: str | None,
    ) -> None:
        """Persist active outbound authorization header details onto client config."""
        self.config.server_authorization_header_name = str(header_name or HEADER_AUTHORIZATION)
        self.config.server_authorization_header_value = (
            str(header_value).strip() if header_value else None
        )

    def _status_code_from_exception(self, err: Exception) -> int | None:
        """Extract HTTP status code from transport-layer exceptions when available."""
        direct_status = getattr(err, "status_code", None)
        if isinstance(direct_status, int):
            return direct_status
        response = getattr(err, "response", None)
        response_status = getattr(response, "status_code", None)
        if isinstance(response_status, int):
            return response_status
        return None

    def _transport_error_details(self, *, transport: str, err: Exception) -> str:
        """Build enriched diagnostics for transport send failures."""
        endpoint = f"{self.data.base_url}{OPAMP_HTTP_PATH}"
        tls_ca_file = (
            str(self.config.tls_ca_file).strip()
            if self.config.tls_ca_file
            else "system-default"
        )
        chain_entries: list[str] = []
        seen_entries: set[str] = set()

        def _append_exception(exc: Exception) -> None:
            text = str(exc).strip()
            entry = f"{type(exc).__name__}: {text}" if text else type(exc).__name__
            if entry in seen_entries:
                return
            seen_entries.add(entry)
            chain_entries.append(entry)

        current: Exception | None = err
        depth = 0
        while current is not None and depth < 8:
            _append_exception(current)
            nested = getattr(current, "exceptions", None)
            if isinstance(nested, (list, tuple)):
                for nested_err in nested[:3]:
                    if isinstance(nested_err, Exception):
                        _append_exception(nested_err)
            next_exc = (
                current.__cause__
                if isinstance(current.__cause__, Exception)
                else None
            )
            if next_exc is None and isinstance(current.__context__, Exception):
                next_exc = current.__context__
            current = next_exc
            depth += 1
        if not chain_entries:
            chain_entries.append(repr(err))
        return (
            f"transport={transport} endpoint={endpoint} "
            f"tls_verify={bool(self.config.tls_verify_server)} "
            f"tls_ca_file={tls_ca_file} "
            f"error_details={' | '.join(chain_entries)}"
        )

    def _should_retry_idp_authorization(self, err: Exception) -> bool:
        """Return True when IDP mode should renegotiate credentials and retry once."""
        if self._server_authorization_mode() != consumer_config.SERVER_AUTHORIZATION_IDP:
            return False
        status_code = self._status_code_from_exception(err)
        return status_code in AUTH_RETRY_STATUS_CODES

    def _normalize_header_value(self, raw_value: str) -> str:
        """Normalize raw token/header value into a bearer Authorization header value."""
        value = str(raw_value or "").strip()
        if not value:
            raise ValueError("authorization token value is empty")
        if value.lower().startswith("bearer "):
            return value
        return f"Bearer {value}"

    def _token_from_env(self) -> str:
        """Resolve outbound OpAMP token from environment."""
        token = os.environ.get(ENV_OPAMP_TOKEN) or ""
        token = str(token).strip()
        if not token:
            raise ValueError(
                "consumer.server-authorization=env-var but no token is set in OpAMP-token"
            )
        return token

    async def _refresh_idp_authorization_header(self) -> str:
        """Obtain fresh bearer credentials from the configured IdP token endpoint."""
        token_url = str(self.config.idp_token_url or "").strip()
        if not token_url:
            raise ValueError(
                "consumer.server-authorization=idp requires consumer.idp-token-url"
            )
        client_id = str(self.config.idp_client_id or "").strip()
        client_secret = str(self.config.idp_client_secret or "").strip()
        if not client_id or not client_secret:
            raise ValueError(
                "consumer.server-authorization=idp requires consumer.idp-client-id and "
                "consumer.idp-client-secret"
            )
        grant_type = str(
            self.config.idp_grant_type or consumer_config.DEFAULT_IDP_GRANT_TYPE
        ).strip()
        scope = str(self.config.idp_scope or "").strip()
        form_payload = {
            "grant_type": grant_type or consumer_config.DEFAULT_IDP_GRANT_TYPE,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        if scope:
            form_payload["scope"] = scope
        httpx_module = _legacy_transport_symbol("httpx", httpx)
        async with httpx_module.AsyncClient() as http_client:
            response = await http_client.post(token_url, data=form_payload)
            response.raise_for_status()
            payload = response.json()
        access_token = str(payload.get("access_token", "")).strip()
        if not access_token:
            raise ValueError("idp token response missing access_token")
        token_type = str(payload.get("token_type", "Bearer")).strip() or "Bearer"
        header_value = (
            f"{token_type} {access_token}"
            if not access_token.lower().startswith("bearer ")
            else access_token
        )
        self._record_authorization_header(
            header_name=HEADER_AUTHORIZATION,
            header_value=header_value,
        )
        return header_value

    async def _resolve_authorization_header_value(
        self,
        *,
        force_refresh: bool = False,
    ) -> str | None:
        """Return outbound Authorization header value for configured mode."""
        mode = self._server_authorization_mode()
        if mode == consumer_config.SERVER_AUTHORIZATION_NONE:
            self._record_authorization_header(
                header_name=HEADER_AUTHORIZATION,
                header_value=None,
            )
            return None

        if mode == consumer_config.SERVER_AUTHORIZATION_ENV_VAR:
            header_value = self._normalize_header_value(self._token_from_env())
            self._record_authorization_header(
                header_name=HEADER_AUTHORIZATION,
                header_value=header_value,
            )
            return header_value

        if mode == consumer_config.SERVER_AUTHORIZATION_CONFIG_VAR:
            token = str(self.config.opamp_token or "").strip()
            if not token:
                raise ValueError(
                    "consumer.server-authorization=config-var requires consumer.OpAMP-token"
                )
            header_value = self._normalize_header_value(token)
            self._record_authorization_header(
                header_name=HEADER_AUTHORIZATION,
                header_value=header_value,
            )
            return header_value

        if mode == consumer_config.SERVER_AUTHORIZATION_IDP:
            cached_value = str(self.config.server_authorization_header_value or "").strip()
            if cached_value and not force_refresh:
                self._record_authorization_header(
                    header_name=HEADER_AUTHORIZATION,
                    header_value=cached_value,
                )
                return cached_value
            return await self._refresh_idp_authorization_header()

        self._record_authorization_header(
            header_name=HEADER_AUTHORIZATION,
            header_value=None,
        )
        return None
