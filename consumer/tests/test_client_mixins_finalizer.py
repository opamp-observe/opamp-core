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

from types import SimpleNamespace
from typing import cast

from opamp_consumer.client_runtime_mixin import ClientRuntimeMixin


class _FakeFinalizerTarget:
    """Lightweight object exposing fields/methods used by ClientRuntimeMixin.__del__."""

    def __init__(self) -> None:
        self.data = SimpleNamespace(allow_heartbeat=True)
        self.finalize_calls = 0

    def finalize(self) -> None:
        """Record any unsafe attempt to start cleanup during destruction."""
        self.finalize_calls += 1


def test_del_stops_heartbeat_without_starting_finalize() -> None:
    """Object destruction should perform local cleanup without network-capable work."""
    target = _FakeFinalizerTarget()

    ClientRuntimeMixin.__del__(cast(ClientRuntimeMixin, target))

    assert target.data.allow_heartbeat is False
    assert target.finalize_calls == 0
