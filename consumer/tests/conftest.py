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

"""Shared pytest setup and state-isolation fixtures for consumer tests."""

import os
import pathlib
import sys
from copy import deepcopy

import pytest

_CONFIG_NOT_CAPTURED = object()
_BASELINE_CONSUMER_CONFIG: object = _CONFIG_NOT_CAPTURED


def pytest_configure() -> None:
    """Configure import paths and capture the unmodified consumer configuration."""
    global _BASELINE_CONSUMER_CONFIG

    root = pathlib.Path(__file__).resolve().parents[2]
    src = root / "consumer" / "src"
    for path in (root, src):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    os.environ.setdefault("OPAMP_CONFIG_PATH", str(root / "tests" / "opamp.json"))

    from opamp_consumer import config as consumer_config

    _BASELINE_CONSUMER_CONFIG = deepcopy(consumer_config.CONFIG)


@pytest.fixture(autouse=True)
def isolate_consumer_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Give every test an independent copy of the module-level consumer config."""
    if _BASELINE_CONSUMER_CONFIG is _CONFIG_NOT_CAPTURED:
        raise RuntimeError("Consumer test configuration was not captured")

    from opamp_consumer import config as consumer_config
    from opamp_consumer.fluentbit import client as fluentbit_client

    isolated_config = deepcopy(_BASELINE_CONSUMER_CONFIG)
    monkeypatch.setattr(consumer_config, "CONFIG", isolated_config)
    monkeypatch.setattr(fluentbit_client, "CONFIG", isolated_config)
