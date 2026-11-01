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

from __future__ import annotations

import asyncio
import threading
from types import SimpleNamespace
from typing import Any, cast

import pytest

from opamp_consumer.client_mixins import ClientRuntimeMixin
from opamp_consumer.config import ConsumerConfig
from opamp_consumer.proto import opamp_pb2


class _HeartbeatLoopHarness(ClientRuntimeMixin):
    """Minimal harness exposing `ClientRuntimeMixin._heartbeat_loop` for tests."""

    def __init__(
        self,
        *,
        send_outcomes: list[object],
        poll_outcomes: list[object] | None = None,
    ) -> None:
        self._config = cast(
            ConsumerConfig,
            SimpleNamespace(
            heartbeat_frequency=1,
            log_agent_api_responses=False,
            ),
        )
        self.data = cast(
            Any,
            SimpleNamespace(
            allow_heartbeat=True,
            process_lock=threading.RLock(),
            last_heartbeat_results={},
            last_heartbeat_http_codes={},
            logFLB=False,
            ),
        )
        self._send_outcomes = list(send_outcomes)
        self._poll_outcomes = list(poll_outcomes or [])
        self.disconnect_calls = 0
        self.send_calls = 0
        self.poll_calls = 0
        self.handle_calls = 0
        self.version_calls = 0

    @property
    def config(self) -> ConsumerConfig:
        return self._config

    async def _send_disconnect_with_timeout(self, timeout_seconds: float = 1.0) -> None:
        self.disconnect_calls += 1

    def check_semaphore(self) -> bool:
        return False

    def poll_local_status_with_codes(
        self, port: int
    ) -> tuple[dict[str, str], dict[str, str]]:
        self.poll_calls += 1
        if self._poll_outcomes:
            outcome = self._poll_outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            if (
                isinstance(outcome, tuple)
                and len(outcome) == 2
                and isinstance(outcome[0], dict)
                and isinstance(outcome[1], dict)
            ):
                return outcome
        return {"health": "ok"}, {"health": "200"}

    def add_agent_version(self, port: int) -> None:
        self.version_calls += 1

    async def send(self, msg=None, *, send_as_is: bool = False) -> opamp_pb2.ServerToAgent:
        self.send_calls += 1
        if self._send_outcomes:
            outcome = self._send_outcomes.pop(0)
            if outcome == "cancel":
                raise asyncio.CancelledError
            if isinstance(outcome, BaseException):
                raise outcome
        if not self._send_outcomes:
            self.data.allow_heartbeat = False
        return opamp_pb2.ServerToAgent()

    def _handle_server_to_agent(self, reply: opamp_pb2.ServerToAgent) -> bool:
        self.handle_calls += 1
        return True


def test_heartbeat_loop_recovers_after_unexpected_send_error() -> None:
    """Unexpected send exceptions should be caught and the next cycle should recover."""
    harness = _HeartbeatLoopHarness(
        send_outcomes=[RuntimeError("send exploded"), "ok"],
    )

    asyncio.run(harness._heartbeat_loop(port=2020))

    assert harness.send_calls == 2
    assert harness.handle_calls == 1
    assert harness.disconnect_calls == 0
    assert harness.data.last_heartbeat_results == {"health": "ok"}
    assert harness.data.last_heartbeat_http_codes == {"health": "200"}


def test_heartbeat_loop_recovers_after_unexpected_poll_error() -> None:
    """Unexpected poll exceptions should not kill the heartbeat loop."""
    harness = _HeartbeatLoopHarness(
        send_outcomes=["ok", "ok"],
        poll_outcomes=[RuntimeError("poll exploded"), ({"health": "ok"}, {"health": "200"})],
    )

    asyncio.run(harness._heartbeat_loop(port=2020))

    assert harness.send_calls == 2
    assert harness.handle_calls == 2
    assert harness.disconnect_calls == 0
    assert harness.data.last_heartbeat_results == {"health": "ok"}
    assert harness.data.last_heartbeat_http_codes == {"health": "200"}


def test_heartbeat_loop_recovers_after_unexpected_handler_error() -> None:
    """Unexpected reply-handler failures should log/reset state and continue polling."""
    harness = _HeartbeatLoopHarness(
        send_outcomes=["ok", "ok"],
    )
    original_handler = harness._handle_server_to_agent
    handler_outcomes = [RuntimeError("handler exploded"), True]

    def _handle(reply: opamp_pb2.ServerToAgent) -> bool:
        outcome = handler_outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return original_handler(reply)

    harness._handle_server_to_agent = _handle

    asyncio.run(harness._heartbeat_loop(port=2020))

    assert harness.send_calls == 2
    assert harness.handle_calls == 1
    assert harness.disconnect_calls == 0
    assert harness.data.last_heartbeat_results == {"health": "ok"}
    assert harness.data.last_heartbeat_http_codes == {"health": "200"}


def test_heartbeat_loop_reraises_cancelled_error() -> None:
    """Cancellation should not be swallowed by the outer heartbeat error handling."""
    harness = _HeartbeatLoopHarness(send_outcomes=["cancel"])

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(harness._heartbeat_loop(port=2020))

    assert harness.disconnect_calls == 1


def test_public_heartbeat_loop_delegates_to_cancellable_runtime() -> None:
    """Embedding hosts can use the public wrapper without accessing private methods."""

    harness = _HeartbeatLoopHarness(send_outcomes=[])
    observed_ports: list[int] = []

    async def replacement(port: int) -> None:
        observed_ports.append(port)

    harness._heartbeat_loop = replacement
    asyncio.run(harness.run_heartbeat_loop(port=2020))
    assert observed_ports == [2020]
