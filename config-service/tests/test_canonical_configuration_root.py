#!/usr/bin/env python3
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

"""Tests that runtime code selects the canonical packaged configuration tree."""

# Ruff's security assertion rule does not apply to pytest test assertions.
# ruff: noqa: S101

from pathlib import Path

from config_service import app, runtime_config


def test_runtime_components_prefer_packaged_configuration() -> None:
    """Both runtime entry points should ignore a duplicate repository artifact tree."""
    packaged_root = Path(app.__file__).resolve().parent

    assert app._config_service_root() == packaged_root  # pylint: disable=protected-access
    assert (
        runtime_config._config_service_root() == packaged_root  # pylint: disable=protected-access
    )
