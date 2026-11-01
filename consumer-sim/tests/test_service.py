# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Contract tests for the public embeddable simulator lifecycle."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from opamp_consumer.config import ConsumerConfig

from opamp_consumer_sim.service import (
    SimulatorIdentity,
    SimulatorInstance,
    SimulatorInstanceConfig,
    SimulatorResponsePlan,
)


class FakeClient:
    """Record generic service lifecycle calls without an OpAMP server."""

    def __init__(self, base_url: str, config: ConsumerConfig) -> None:
        """Retain constructed settings and initialize call state."""

        self.base_url = base_url
        self.config = config
        self.launched = False
        self.finalized = False
        self.terminated = False
        self.sent = 0

    def launch_agent_process(self) -> bool:
        """Record logical launch."""

        self.launched = True
        return True

    def add_agent_version(self, port: int) -> None:
        """Retain the normalized status port."""

        self.config.client_status_port = port

    async def send(self) -> None:
        """Record the initial connection/send cycle."""

        self.sent += 1

    async def run_heartbeat_loop(self, port: int) -> None:
        """Remain cancellable until the service stops."""

        del port
        await asyncio.Event().wait()

    async def finalize_async(self) -> None:
        """Record awaited disconnect/finalization."""

        self.finalized = True

    def terminate_agent_process(self) -> None:
        """Record logical termination."""

        self.terminated = True


def _instance_config(tmp_path: Path, name: str = "one") -> SimulatorInstanceConfig:
    """Build one typed simulator configuration."""

    return SimulatorInstanceConfig(
        name,
        tmp_path / "consumer.json",
        SimulatorResponsePlan(tmp_path / "responses.json"),
        SimulatorIdentity(name, "1.0.0", "config-1"),
    )


def _loader(path: Path) -> ConsumerConfig:
    """Return a valid consumer config without reading disk."""

    del path
    return ConsumerConfig(server_url="http://provider", heartbeat_frequency=1)


@pytest.mark.asyncio
async def test_start_health_restart_and_stop(tmp_path: Path) -> None:
    """The public lifecycle is cancellable and reports passive immutable health."""

    clients: list[FakeClient] = []

    def factory(base_url: str, config: ConsumerConfig) -> FakeClient:
        client = FakeClient(base_url, config)
        clients.append(client)
        return client

    instance = SimulatorInstance(
        _instance_config(tmp_path),
        environ={"APP_ENABLE_DEV_FEATURES": "true"},
        config_loader=_loader,
        client_factory=factory,
    )
    await instance.start()
    assert instance.health().ready and clients[0].sent == 1
    assert clients[0].config.service_instance_id == "one"
    assert clients[0].config.agent_additional_params == [
        '{"client_version": "1.0.0", "config_version": "config-1", '
        '"service_instance_uid": "one"}'
    ]
    await instance.logical_restart()
    assert instance.health().restart_count == 1 and len(clients) == 2
    assert clients[0].finalized and clients[0].terminated
    await instance.stop()
    assert not instance.health().running and clients[1].finalized


@pytest.mark.asyncio
async def test_apply_config_rolls_back_and_dev_gate_blocks(tmp_path: Path) -> None:
    """A failed candidate restores the prior running instance and the dev gate is mandatory."""

    def loader(path: Path) -> ConsumerConfig:
        if path.name == "bad.json":
            return ConsumerConfig(server_url=None)
        return _loader(path)

    instance = SimulatorInstance(
        _instance_config(tmp_path),
        environ={"APP_ENABLE_DEV_FEATURES": "yes"},
        config_loader=loader,
        client_factory=FakeClient,
    )
    await instance.start()
    candidate = SimulatorInstanceConfig(
        "bad",
        tmp_path / "bad.json",
        SimulatorResponsePlan(tmp_path / "responses.json"),
        SimulatorIdentity("bad"),
    )
    with pytest.raises(ValueError, match="server_url"):
        await instance.apply_config(candidate)
    assert instance.config.name == "one" and instance.health().ready
    await instance.stop()
    blocked = SimulatorInstance(
        _instance_config(tmp_path),
        environ={},
        config_loader=_loader,
        client_factory=FakeClient,
    )
    with pytest.raises(RuntimeError, match="APP_ENABLE_DEV_FEATURES"):
        await blocked.start()
