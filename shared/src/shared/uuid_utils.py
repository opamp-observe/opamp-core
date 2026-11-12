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

"""UUID helper utilities shared by provider and consumer."""

from __future__ import annotations

import logging
import secrets
import time
import uuid

LOGGER = logging.getLogger(__name__)

NANOSECONDS_PER_MILLISECOND = 1_000_000
UUID7_TIMESTAMP_BITS = 48
UUID7_TIMESTAMP_SHIFT = 80
UUID7_VERSION_VALUE = 0x7
UUID7_VERSION_SHIFT = 76
UUID7_RANDOM_A_BITS = 12
UUID7_RANDOM_A_SHIFT = 64
UUID7_VARIANT_VALUE = 0x2
UUID7_VARIANT_SHIFT = 62
UUID7_RANDOM_B_BITS = 62
UUID7_TIMESTAMP_MASK = (1 << UUID7_TIMESTAMP_BITS) - 1


def generate_uuid7_bytes() -> bytes:
    """Generate UUIDv7 bytes without requiring third-party libraries."""
    LOGGER.info("generating UUIDv7 bytes")
    timestamp_ms = int(time.time_ns() / NANOSECONDS_PER_MILLISECOND)
    rand_a = secrets.randbits(UUID7_RANDOM_A_BITS)
    rand_b = secrets.randbits(UUID7_RANDOM_B_BITS)
    uuid_int = (
        (timestamp_ms & UUID7_TIMESTAMP_MASK) << UUID7_TIMESTAMP_SHIFT
        | (UUID7_VERSION_VALUE << UUID7_VERSION_SHIFT)
        | (rand_a << UUID7_RANDOM_A_SHIFT)
        | (UUID7_VARIANT_VALUE << UUID7_VARIANT_SHIFT)
        | rand_b
    )
    uuid_bytes = uuid.UUID(int=uuid_int).bytes
    LOGGER.info("generated UUIDv7 bytes length=%s", len(uuid_bytes))
    return uuid_bytes
