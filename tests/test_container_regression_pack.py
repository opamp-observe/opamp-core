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

"""Unit coverage for container regression-pack scenario registration."""

# The registry helpers are intentionally private because only this focused test imports them.
# pylint: disable=protected-access

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_NAME = "opamp_container_regression_pack"
SCENARIO_IDS = ("st004b", "st007", "st009", "st010", "st011")


def _load_regression_pack_module():
    """Load the hyphenated-path regression module for direct registry inspection."""
    module_path = (
        Path(__file__).resolve().parent
        / "test-containers"
        / "run_regression_pack.py"
    )
    module_spec = importlib.util.spec_from_file_location(MODULE_NAME, module_path)
    assert module_spec is not None
    assert module_spec.loader is not None
    loaded_module = importlib.util.module_from_spec(module_spec)
    sys.modules[MODULE_NAME] = loaded_module
    module_spec.loader.exec_module(loaded_module)
    return loaded_module


def test_default_tests_register_new_system_scenarios() -> None:
    """The regression pack should expose each new container through `--only`."""
    regression_pack = _load_regression_pack_module()

    registered_ids = {
        regression_test.test_id
        for regression_test in regression_pack._default_tests(
            regression_pack._repo_root()
        )
    }

    assert set(SCENARIO_IDS).issubset(registered_ids)


def test_regression_directories_include_new_scenario_evidence(tmp_path: Path) -> None:
    """Evidence preparation should create host mount points for all new scenarios."""
    regression_pack = _load_regression_pack_module()

    regression_pack._ensure_regression_directories(tmp_path)

    for scenario_id in SCENARIO_IDS:
        assert (tmp_path / "dist" / "test-reports" / scenario_id).is_dir()
