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

from pathlib import Path

from opamp_dev_tools.release_assets import (
    DEFAULT_RELEASE_COMPONENT_KEYS,
    parse_release_component_keys,
    resolve_release_sbom_paths,
)


def test_default_release_component_selection_includes_independent_deployables() -> None:
    component_keys = parse_release_component_keys(",".join(DEFAULT_RELEASE_COMPONENT_KEYS))

    assert component_keys == [
        "provider",
        "consumer",
        "catalog-service",
        "client-config-generator-service",
        "cli",
        "consumer-sim",
    ]


def test_release_component_parsing_accepts_legacy_catalog_alias() -> None:
    component_keys = parse_release_component_keys("catalog,cli")

    assert component_keys == ["catalog-service", "cli"]


def test_release_component_sbom_overrides_support_new_targets(tmp_path: Path) -> None:
    resolved = resolve_release_sbom_paths(
        repo_root=tmp_path,
        component_keys=["catalog-service", "cli"],
        provider_sbom_path="dist/sbom/provider.cdx.json",
        consumer_sbom_path="dist/sbom/consumer.cdx.json",
        component_sbom_path_overrides=["catalog=dist/sbom/custom-catalog.cdx.json"],
    )

    assert resolved["catalog-service"].name == "custom-catalog.cdx.json"
    assert resolved["cli"].name == "opamp_cli_deployable_artifacts.cyclonedx.json"
