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

"""Tests for the public consumer package layout."""

from __future__ import annotations

import importlib.util

CANONICAL_SIMULATOR_METADATA_MODULE = "opamp_consumer.simulator.config_metadata"
REMOVED_FLAT_SIMULATOR_METADATA_MODULE = "opamp_consumer.simulator_config_metadata"


def test_simulator_config_metadata_has_one_package_owner() -> None:
    """Keep simulator metadata in its plugin package without a flat duplicate."""
    assert (  # noqa: S101 - pytest uses assertions to report package-layout failures.
        importlib.util.find_spec(CANONICAL_SIMULATOR_METADATA_MODULE) is not None
    )
    assert (  # noqa: S101 - pytest uses assertions to report package-layout failures.
        importlib.util.find_spec(REMOVED_FLAT_SIMULATOR_METADATA_MODULE) is None
    )
