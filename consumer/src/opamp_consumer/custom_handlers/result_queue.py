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

"""Bounded, ordered outbound custom results awaiting transport acknowledgement."""

from __future__ import annotations

from collections import deque

from opamp_consumer.proto import opamp_pb2

DEFAULT_RESULT_QUEUE_LIMIT = 128


class CustomResultQueue:
    """Retain result payloads until a normal AgentToServer exchange succeeds."""

    def __init__(self, limit: int = DEFAULT_RESULT_QUEUE_LIMIT) -> None:
        """Create a queue with a strict maximum number of pending results."""
        if limit < 1:
            raise ValueError("custom result queue limit must be positive")
        self._limit = limit
        self._pending: deque[opamp_pb2.CustomMessage] = deque()

    def enqueue(self, result: opamp_pb2.CustomMessage) -> None:
        """Copy one completed result, rejecting a full queue."""
        if len(self._pending) >= self._limit:
            raise OverflowError("custom result queue is full")
        copy = opamp_pb2.CustomMessage()
        copy.CopyFrom(result)
        self._pending.append(copy)

    def peek(self) -> opamp_pb2.CustomMessage | None:
        """Return the oldest pending result without consuming it."""
        return self._pending[0] if self._pending else None

    def acknowledge(self) -> None:
        """Remove the oldest result after a successful transport exchange."""
        if not self._pending:
            raise ValueError("no pending custom result")
        self._pending.popleft()
