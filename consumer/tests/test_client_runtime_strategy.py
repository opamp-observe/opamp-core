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

# ruff: noqa: S101

from __future__ import annotations

import asyncio
import threading
from types import SimpleNamespace
from typing import Any, cast

import pytest

from opamp_consumer.client_observer_mixin import ClientObserverMixin
from opamp_consumer.client_runtime_mixin import ClientRuntimeMixin
from opamp_consumer.client_supervisor_mixin import ClientSupervisorMixin
from opamp_consumer.config import ConsumerConfig
from opamp_consumer.proto import opamp_pb2

_EVENT_LOOP_CYCLE_SECONDS = 0


class _RuntimeStrategyHarness(ClientRuntimeMixin):
    """Minimal runtime harness for process lifecycle strategy tests."""

    def __init__(self, process_tracking: str | None = None) -> None:
        config_payload: dict[str, object] = {
            "heartbeat_frequency": 1,
            "process_detection_regex": r"agent",
        }
        if process_tracking is not None:
            config_payload["process_tracking"] = process_tracking
        self._config = cast(ConsumerConfig, SimpleNamespace(**config_payload))
        self.data = cast(
            Any,
            SimpleNamespace(
                allow_heartbeat=True,
                process_lock=threading.RLock(),
                uid_instance=b"1234567890123456",
            ),
        )

    @property
    def config(self) -> ConsumerConfig:
        return self._config

    async def send(
        self, msg=None, *, send_as_is: bool = False
    ) -> opamp_pb2.ServerToAgent | None:
        return opamp_pb2.ServerToAgent()


def test_runtime_lifecycle_defaults_to_supervisor_when_unset() -> None:
    """Unset process_tracking should use the Supervisor strategy."""
    harness = _RuntimeStrategyHarness()

    lifecycle = harness._runtime_lifecycle()

    assert isinstance(lifecycle, ClientSupervisorMixin)


def test_runtime_lifecycle_falls_back_to_supervisor_for_unknown_mode() -> None:
    """Unknown process_tracking values should normalize to Supervisor."""
    harness = _RuntimeStrategyHarness("not-a-real-mode")

    lifecycle = harness._runtime_lifecycle()

    assert isinstance(lifecycle, ClientSupervisorMixin)


def test_runtime_lifecycle_selects_observer_case_insensitively() -> None:
    """Observer mode selection should be case-insensitive."""
    harness = _RuntimeStrategyHarness("Observer")

    lifecycle = harness._runtime_lifecycle()

    assert isinstance(lifecycle, ClientObserverMixin)


def test_runtime_lifecycle_is_cached_after_first_resolution() -> None:
    """Lifecycle selection should happen once and then be reused."""
    harness = _RuntimeStrategyHarness("Observer")

    first = harness._runtime_lifecycle()
    harness._config.process_tracking = "supervisor"
    second = harness._runtime_lifecycle()

    assert first is second
    assert isinstance(second, ClientObserverMixin)


class _FakeLifecycle:
    """Simple fake lifecycle to verify delegation from ClientRuntimeMixin."""

    def __init__(self) -> None:
        self.launch_calls = 0
        self.terminate_calls = 0
        self.restart_calls = 0
        self.finalize_calls = 0
        self.disconnect_calls = 0

    def launch_agent_process(self) -> bool:
        self.launch_calls += 1
        return True

    def terminate_agent_process(self) -> None:
        self.terminate_calls += 1

    def restart_agent_process(self) -> bool:
        self.restart_calls += 1
        return True

    async def finalize_async(self) -> None:
        """Record awaited lifecycle finalization."""
        self.finalize_calls += 1

    async def send_disconnect(self) -> None:
        self.disconnect_calls += 1


@pytest.mark.asyncio
async def test_runtime_methods_delegate_to_selected_lifecycle() -> None:
    """Runtime lifecycle entrypoints should delegate to the resolved strategy."""
    harness = _RuntimeStrategyHarness("supervisor")
    lifecycle = _FakeLifecycle()
    harness._runtime_process_lifecycle = cast(Any, lifecycle)

    assert harness.launch_agent_process() is True
    harness.terminate_agent_process()
    assert harness.restart_agent_process() is True
    await harness.finalize_async()
    await harness.send_disconnect()

    assert lifecycle.launch_calls == 1
    assert lifecycle.terminate_calls == 1
    assert lifecycle.restart_calls == 1
    assert lifecycle.finalize_calls == 1
    assert lifecycle.disconnect_calls == 1


def test_sync_finalize_completes_without_background_thread() -> None:
    """Synchronous finalization should finish its disconnect before returning."""
    harness = _RuntimeStrategyHarness("supervisor")
    lifecycle = _FakeLifecycle()
    harness._runtime_process_lifecycle = cast(Any, lifecycle)

    harness.finalize()

    assert lifecycle.finalize_calls == 1


@pytest.mark.asyncio
async def test_sync_finalize_schedules_cleanup_on_active_loop() -> None:
    """Compatibility finalization should use the caller's active event loop."""
    harness = _RuntimeStrategyHarness("supervisor")
    lifecycle = _FakeLifecycle()
    harness._runtime_process_lifecycle = cast(Any, lifecycle)

    harness.finalize()
    await asyncio.sleep(_EVENT_LOOP_CYCLE_SECONDS)

    assert lifecycle.finalize_calls == 1


@pytest.mark.asyncio
async def test_finalize_async_is_idempotent_and_stops_heartbeat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Awaited finalization should stop heartbeats and send disconnect once."""
    harness = _RuntimeStrategyHarness("supervisor")
    disconnect_calls = 0

    async def record_disconnect() -> None:
        """Record the lifecycle's final disconnect attempt."""
        nonlocal disconnect_calls
        disconnect_calls += 1

    monkeypatch.setattr(harness, "_send_disconnect_with_timeout", record_disconnect)

    await harness.finalize_async()
    await harness.finalize_async()

    assert harness.data.allow_heartbeat is False
    assert disconnect_calls == 1


class _HandlerProvider:
    """Provides the downstream handler used by ClientRuntimeMixin super() delegation."""

    _handled_reply: opamp_pb2.ServerToAgent | None = None

    def _handle_server_to_agent(self, reply: opamp_pb2.ServerToAgent) -> bool:
        self._handled_reply = reply
        return True


class _HandleDelegationHarness(ClientRuntimeMixin, _HandlerProvider):
    """Harness proving ClientRuntimeMixin delegates _handle_server_to_agent to super()."""

    def __del__(self) -> None:  # pragma: no cover - test harness guard
        return

    @property
    def config(self) -> ConsumerConfig:
        return cast(ConsumerConfig, SimpleNamespace(heartbeat_frequency=1))

    async def send(
        self, msg=None, *, send_as_is: bool = False
    ) -> opamp_pb2.ServerToAgent | None:
        return opamp_pb2.ServerToAgent()


class _NoHandlerHarness(ClientRuntimeMixin):
    """Harness with no downstream handler to exercise NotImplemented fallback."""

    def __del__(self) -> None:  # pragma: no cover - test harness guard
        return

    @property
    def config(self) -> ConsumerConfig:
        return cast(ConsumerConfig, SimpleNamespace(heartbeat_frequency=1))

    async def send(
        self, msg=None, *, send_as_is: bool = False
    ) -> opamp_pb2.ServerToAgent | None:
        return opamp_pb2.ServerToAgent()


def test_handle_server_to_agent_delegates_to_next_mixin_in_mro() -> None:
    """ClientRuntimeMixin should delegate handler logic to downstream mixins."""
    harness = _HandleDelegationHarness()
    reply = opamp_pb2.ServerToAgent()
    reply.instance_uid = b"uid"

    assert harness._handle_server_to_agent(reply) is True
    assert harness._handled_reply is reply


def test_handle_server_to_agent_raises_when_no_downstream_handler() -> None:
    """A missing downstream handler should raise NotImplementedError."""
    harness = _NoHandlerHarness()

    with pytest.raises(NotImplementedError):
        harness._handle_server_to_agent(opamp_pb2.ServerToAgent())
