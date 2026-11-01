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

"""ASCII-safe helpers for logging runtime values."""

from __future__ import annotations


def format_instance_uid_for_log(instance_uid: bytes | None) -> str:
    """Return an ASCII-safe representation for instance UID log output."""
    if not instance_uid:
        return "<empty>"
    return instance_uid.hex()
