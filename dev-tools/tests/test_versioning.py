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

from __future__ import annotations

import re

from opamp_dev_tools.versioning import VERSION_TARGETS


def test_version_targets_cover_primary_component_metadata_files() -> None:
    """Verify repository version updates cover shared and suite package metadata."""
    target_paths = {target.path for target in VERSION_TARGETS}
    assert "cli/pyproject.toml" in target_paths
    assert "provider/pyproject.toml" in target_paths
    assert "config-service/build_config.py" in target_paths
    assert "catalog-service/pyproject.toml" in target_paths
    assert "client-config-generator-service/pyproject.toml" in target_paths
    assert (
        "client-config-generator-service/src/client_config_generator_service/__init__.py"
        in target_paths
    )
    assert "shared/pyproject.toml" in target_paths
    assert "opamp-suite/pyproject.toml" in target_paths
    assert "opamp-suite/src/opamp_suite/__init__.py" in target_paths
    assert "catalog-service/setup.py" not in target_paths


def test_suite_dependency_pin_target_updates_all_core_versions() -> None:
    """Verify the suite profile dependency regex updates each core package pin."""
    suite_pin_target = next(
        target
        for target in VERSION_TARGETS
        if target.path == "opamp-suite/pyproject.toml" and "catalog-service|" in target.pattern
    )
    original = (
        '"catalog-service==0.6.0"\n'
        '"client-config-generator-service==0.6.0"\n'
        '"config-service==0.6.0"\n'
        '"opamp-consumer==0.6.0"\n'
        '"opamp-server==0.6.0"\n'
    )

    updated = re.sub(
        suite_pin_target.pattern,
        suite_pin_target.replacement.format(version="0.7.0"),
        original,
    )

    assert "0.6.0" not in updated
    assert updated.count("0.7.0") == 5
