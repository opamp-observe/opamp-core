# Copyright 2026 mp3monster.org
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

"""Client runtime lifecycle mixin extracted from the legacy client_mixins module."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
from typing import TYPE_CHECKING, cast

import httpx

from opamp_consumer.logging_utils import format_instance_uid_for_log
from opamp_consumer.proto import opamp_pb2
from opamp_consumer.reporting_flag import ReportingFlag

if TYPE_CHECKING:
    from opamp_consumer.abstract_client import OpAMPClientData
    from opamp_consumer.config import ConsumerConfig

PROCESS_TRACKING_SUPERVISOR = "supervisor"
PROCESS_TRACKING_OBSERVER = "observer"


def _normalize_process_tracking(value: str | None) -> str:
    """Return normalized process tracking mode with supervisor fallback."""
    normalized = str(value or PROCESS_TRACKING_SUPERVISOR).strip().lower()
    if normalized in {PROCESS_TRACKING_SUPERVISOR, PROCESS_TRACKING_OBSERVER}:
        return normalized
    return PROCESS_TRACKING_SUPERVISOR


class _BaseClientProcessLifecycle:
    """Shared lifecycle helper behavior used by process-tracking implementations."""

    def __init__(self, owner: ClientRuntimeMixin) -> None:
        self._owner = owner

    def launch_agent_process(self) -> bool:
        """Launch process for current lifecycle strategy."""
        raise NotImplementedError

    def terminate_agent_process(self) -> None:
        """Terminate process for current lifecycle strategy."""
        raise NotImplementedError

    def restart_agent_process(self) -> bool:
        """Restart process for current lifecycle strategy."""
        raise NotImplementedError

    async def send_disconnect(self) -> None:
        """Best-effort disconnect send shared by supervisor/observer modes."""
        msg = self._owner._populate_disconnect(opamp_pb2.AgentToServer())
        logging.getLogger(__name__).debug("Built disconnect message")
        try:
            await self._owner.send(msg, send_as_is=True)
            self._owner.data.allow_heartbeat = False
        except Exception as err:  # pragma: no cover - error path varies by env
            logging.getLogger(__name__).warning(
                "Failed to send disconnect message - %s", err
            )

    def finalize(self) -> None:
        """Finalize client lifecycle with async disconnect fallback."""
        if self._owner._finalize_started:
            return
        self._owner._finalize_started = True
        if getattr(self._owner, "data", None) is not None:
            self._owner.data.allow_heartbeat = False
        try:
            loop = asyncio.get_running_loop()
            logging.getLogger(__name__).debug("finalize - got loop")
        except RuntimeError:

            def _runner() -> None:
                """Run best-effort async disconnect send inside a dedicated thread."""
                try:
                    logging.getLogger(__name__).debug(
                        "About to send disconnect message"
                    )
                    asyncio.run(self._owner._send_disconnect_with_timeout())
                except Exception as err:
                    logging.getLogger(__name__).error(
                        "Failed to send disconnect message, error is:\n %s", err
                    )
                    return

            thread = threading.Thread(target=_runner, daemon=True)
            thread.start()
        else:
            if loop.is_closed():
                return
            loop.create_task(self._owner._send_disconnect_with_timeout())


class ClientRuntimeMixin:
    """Agent process lifecycle and heartbeat polling behavior."""

    data: OpAMPClientData

    @property
    def config(self) -> ConsumerConfig:
        """Return active consumer configuration for this client."""
        raise NotImplementedError

    async def send(self, msg=None, *, send_as_is: bool = False) -> opamp_pb2.ServerToAgent | None:
        """Send AgentToServer payloads and return the provider response."""
        raise NotImplementedError

    def _handle_server_to_agent(self, reply: opamp_pb2.ServerToAgent) -> bool:
        """Delegate reply handling to the next mixin in the MRO chain."""
        handler = getattr(super(), "_handle_server_to_agent", None)
        if handler is None:
            raise NotImplementedError("_handle_server_to_agent is not implemented")
        return cast(bool, handler(reply))

    _runtime_agent_command = "agent"
    _runtime_config_flag = "-c"
    _heartbeat_paths = ("/health",)
    _localhost_base = "http://127.0.0.1"
    _http_timeout_seconds = 5.0
    _error_prefix = "error: "
    _error_status = "error"
    _heartbeat_skew_seconds = 1
    _semaphore_filename = "OpAMPSupervisor.signal"
    _finalize_started = False
    _key_agent_version = "version"
    _key_agent_edition = "edition"
    _json_key_agent = "agent"
    _json_key_agent_fallback: str | None = None
    _json_key_version = "version"
    _json_key_edition = "edition"
    _value_agent_type = "Agent"

    _runtime_process_lifecycle: _BaseClientProcessLifecycle | None = None

    def _create_runtime_process_lifecycle(
        self,
    ) -> _BaseClientProcessLifecycle:
        """Create process lifecycle implementation based on config selection."""
        tracking_mode = _normalize_process_tracking(
            getattr(self.config, "process_tracking", PROCESS_TRACKING_SUPERVISOR)
        )
        from opamp_consumer.client_observer_mixin import ClientObserverMixin
        from opamp_consumer.client_supervisor_mixin import ClientSupervisorMixin

        if tracking_mode == PROCESS_TRACKING_OBSERVER:
            return ClientObserverMixin(self)
        return ClientSupervisorMixin(self)

    def _runtime_lifecycle(self) -> _BaseClientProcessLifecycle:
        """Return lazily initialized lifecycle strategy implementation."""
        if self._runtime_process_lifecycle is None:
            self._runtime_process_lifecycle = self._create_runtime_process_lifecycle()
        return self._runtime_process_lifecycle

    def launch_agent_process(self) -> bool:
        """Launch/attach process using configured supervisor or observer strategy."""
        return self._runtime_lifecycle().launch_agent_process()

    def terminate_agent_process(self) -> None:
        """Terminate process using configured supervisor or observer strategy."""
        self._runtime_lifecycle().terminate_agent_process()

    def restart_agent_process(self) -> bool:
        """Restart process using configured supervisor or observer strategy."""
        return self._runtime_lifecycle().restart_agent_process()

    def _populate_disconnect(
        self, msg: opamp_pb2.AgentToServer
    ) -> opamp_pb2.AgentToServer:
        """Populate disconnect data and ensure instance UID is set."""
        if self.data.uid_instance is not None:
            msg.instance_uid = self.data.uid_instance
            logging.getLogger(__name__).warning(
                "Set disconnect message instance UID to %s",
                format_instance_uid_for_log(self.data.uid_instance),
            )
        msg.agent_disconnect.SetInParent()
        return msg

    async def send_disconnect(self) -> None:
        """Implements `OpAMPClientInterface.send_disconnect` with best-effort send."""
        await self._runtime_lifecycle().send_disconnect()

    async def _send_disconnect_with_timeout(self, timeout_seconds: float = 1.0) -> None:
        """Best-effort disconnect send with a short timeout."""
        try:
            logging.getLogger(__name__).warning("_send_disconnect_with_timeout exiting")
            await asyncio.wait_for(self.send_disconnect(), timeout=timeout_seconds)
        except Exception as err:  # pragma: no cover - error path varies by env
            logging.getLogger(__name__).error("Disconnect send timed out-- %s", err)

        logging.getLogger(__name__).warning("_send_disconnect_with_timeout exiting")

    def finalize(self) -> None:
        """Implements `OpAMPClientInterface.finalize` with async-loop fallback."""
        self._runtime_lifecycle().finalize()

    def __del__(self) -> None:
        """Attempt graceful disconnect/finalize during object destruction."""
        try:
            if getattr(self, "data", None) is not None:
                self.data.allow_heartbeat = False
            if sys.is_finalizing():
                return
            self.finalize()
        except Exception:
            return

    def _heartbeat_key(self, path: str) -> str:
        """Return the last URL path component as the dictionary key."""
        return path.rstrip("/").split("/")[-1]

    def poll_local_status_with_codes(
        self, port: int
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Poll local health endpoints and collect response bodies and status codes.

        Args:
            port: Local agent HTTP status port to query.

        Returns:
            Tuple of `(results, codes)` maps keyed by heartbeat endpoint name.
        """
        results: dict[str, str] = {}
        codes: dict[str, str] = {}
        for path in self._heartbeat_paths:
            url = f"{self._localhost_base}:{port}{path}"
            key = self._heartbeat_key(path)
            try:
                response = httpx.get(url, timeout=self._http_timeout_seconds)
                results[key] = response.text
                codes[key] = str(response.status_code)
                response.raise_for_status()
                if (response.status_code < 200) or (response.status_code > 299):
                    self.data.reporting_flags[ReportingFlag.REPORT_HEALTH] = True
                    results[key] = f"{path}={response.status_code}"
                    logging.getLogger(__name__).warning(
                        "Err checking status using %s got code %s",
                        path,
                        response.status_code,
                    )
            except Exception as error:  # pragma: no cover - error path varies by env
                results[key] = f"{self._error_prefix}{error}"
                codes[key] = self._error_status
                self.data.reporting_flags[ReportingFlag.REPORT_HEALTH] = True
                logging.getLogger(__name__).warning(
                    "Err checking status using %s got error %s", path, error
                )
        return results, codes

    def add_agent_version(self, port: int) -> None:
        """Fetch Fluent Bit version endpoint and store in client runtime metadata.

        Args:
            port: Local agent HTTP status port used for version endpoint calls.
        """
        url = f"{self._localhost_base}:{port}"
        try:
            response = httpx.get(url, timeout=self._http_timeout_seconds)
            response.raise_for_status()
            value = response.text
            try:
                data = response.json()
                version = None
                edition = None
                if isinstance(data, dict):
                    version = data.get(self._key_agent_version)
                    edition = data.get(self._key_agent_edition)
                    agent_payload = data.get(self._json_key_agent)
                    if (
                        agent_payload is None
                        and self._json_key_agent_fallback is not None
                    ):
                        agent_payload = data.get(self._json_key_agent_fallback)
                    if isinstance(agent_payload, dict):
                        self.data.agent_type_name = self._value_agent_type
                        version = version or agent_payload.get(
                            self._json_key_version
                        )
                        edition = edition or agent_payload.get(
                            self._json_key_edition
                        )
                if version or edition:
                    if version and edition:
                        value = f"{version} ({edition})"
                    else:
                        value = version or edition
                if value is not None:
                    self.data.agent_version = str(value)
            except ValueError as parse_error:
                logging.getLogger(__name__).warning(
                    "failed to parse Agent version response: %s", parse_error
                )
        except Exception as error:  # pragma: no cover # pylint: disable=broad-exception-caught
            logging.getLogger(__name__).warning(
                "failed to parse Agent version response: %s", error
            )

    def check_semaphore(self) -> bool:
        """Return True when the supervisor semaphore file exists on local disk."""
        if os.path.isfile(self._semaphore_filename):
            logging.getLogger(__name__).warning("Spotted Semaphore file")
            return True
        return False

    async def _heartbeat_loop(self, port: int) -> None:
        """Run a periodic polling loop that updates last heartbeat results.

        Args:
            port: Local agent HTTP status port used for heartbeat polling.
        """
        logger = logging.getLogger(__name__)
        heartbeat_frequency = int(self.config.heartbeat_frequency or 0)
        interval = max(0, heartbeat_frequency - self._heartbeat_skew_seconds)
        logger.debug("Heartbeat cycle start - checking every %s", interval)
        while self.data.allow_heartbeat:
            try:
                await asyncio.sleep(interval)
                if self.check_semaphore():
                    await self._send_disconnect_with_timeout()
                    self.data.allow_heartbeat = False
                    continue
                try:
                    with self.data.process_lock:
                        results, codes = self.poll_local_status_with_codes(port)
                        self.data.last_heartbeat_results.clear()
                        self.data.last_heartbeat_results.update(results)
                        self.add_agent_version(port)
                        self.data.last_heartbeat_http_codes = codes
                    if self.config.log_agent_api_responses and self.data.logFLB:
                        logger.debug("Heartbeat outcome --> %s", results)

                    logger.info("Heartbeat response codes: %s", codes)

                except KeyboardInterrupt as keyboard_interrupt:
                    logger.error(
                        "Error - a disturbance in the force\n %s", keyboard_interrupt
                    )
                    self.data.allow_heartbeat = False
                    await self._send_disconnect_with_timeout()
                    break
                except Exception as error:  # pylint: disable=broad-exception-caught
                    logger.error(
                        "Something stumbled - we catch and carry on\n %s", error
                    )
                    self.data.last_heartbeat_results = {}
                    self.data.last_heartbeat_http_codes = {}

                self._handle_server_to_agent(await self.send())
            except asyncio.CancelledError:
                await self._send_disconnect_with_timeout()
                logger.info("Heartbeat loop cancelled; disconnect signal sent")
                raise
            except (KeyboardInterrupt, SystemExit):
                await self._send_disconnect_with_timeout()
                logger.error("Heartbeat loop interrupted by shutdown signal")
                raise
            except Exception as loop_error:  # pylint: disable=broad-exception-caught
                logger.exception(
                    "Heartbeat loop recovered from unexpected cycle error: %s",
                    loop_error,
                )
                self.data.last_heartbeat_results = {}
                self.data.last_heartbeat_http_codes = {}
