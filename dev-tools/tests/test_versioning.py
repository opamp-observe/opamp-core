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

from __future__ import annotations

from opamp_dev_tools.versioning import VERSION_TARGETS


def test_version_targets_cover_primary_component_metadata_files() -> None:
    target_paths = {target.path for target in VERSION_TARGETS}
    assert "cli/pyproject.toml" in target_paths
    assert "provider/pyproject.toml" in target_paths
    assert "config-service/build_config.py" in target_paths
    assert "catalog-service/pyproject.toml" in target_paths
    assert "client-config-generator-service/pyproject.toml" in target_paths
    assert "client-config-generator-service/src/client_config_generator_service/__init__.py" in target_paths
    assert "catalog-service/setup.py" not in target_paths
