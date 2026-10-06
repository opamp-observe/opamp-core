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

"""Verify provider deployment config controls generator route accessibility."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

KEY_COMPONENT_ENTRY_POINTS = "component-entry-points"
KEY_CONFIGURATION_DIRECTORY = "configuration_directory"
KEY_ENABLED = "enabled"
KEY_ENTRY_POINT = "entry_point"
KEY_LABEL = "label"
KEY_OPAMP = "opamp"
KEY_QUART = "quart"
KEY_SERVICE = "client_config_generator"
KEY_STORAGE = "storage"
KEY_URL = "url"
ENTRY_POINT = (
    "client_config_generator_service.opamp_integration:"
    "register_client_config_generator_feature"
)
FEATURE_LABEL = "Client Config Generator"
FEATURE_URL = "/client-config-generator-service/ui"
ENV_OPAMP_CONFIG_PATH = "OPAMP_CONFIG_PATH"


def _configure_import_paths(repo_root: Path) -> None:
    """Add source roots needed for provider and plugin registration.

    Args:
        repo_root: Mounted repository root inside the container.
    """
    source_paths = (
        repo_root,
        repo_root / "provider" / "src",
        repo_root / "client-config-generator-service" / "src",
    )
    for source_path in source_paths:
        source_text = str(source_path.resolve())
        if source_text not in sys.path:
            sys.path.insert(0, source_text)


def _write_deployment_config(root_path: Path, *, enabled: bool) -> Path:
    """Write one enabled or disabled component deployment definition.

    Args:
        root_path: Temporary scenario directory.
        enabled: Whether the generator entry point should be registered.
    """
    scenario_name = "enabled" if enabled else "disabled"
    scenario_path = root_path / scenario_name
    scenario_path.mkdir(parents=True, exist_ok=True)
    config_path = scenario_path / "opamp.json"
    component_entry = {
        KEY_ENTRY_POINT: ENTRY_POINT,
        KEY_LABEL: FEATURE_LABEL,
        KEY_URL: FEATURE_URL,
        KEY_ENABLED: enabled,
    }
    payload = {
        KEY_COMPONENT_ENTRY_POINTS: {KEY_QUART: [component_entry]},
        KEY_OPAMP: {
            KEY_SERVICE: {
                KEY_STORAGE: {KEY_CONFIGURATION_DIRECTORY: "generated"},
            }
        },
    }
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return config_path


async def _verify_enabled_deployment(config_path: Path) -> None:
    """Assert enabled deployment registers menu metadata and reachable routes.

    Args:
        config_path: Enabled scenario runtime configuration.
    """
    from opamp_provider.component_features import (
        register_provider_component_entries,
        ui_menu_items_from_component_entries,
    )
    from quart import Quart

    os.environ[ENV_OPAMP_CONFIG_PATH] = str(config_path)
    application = Quart("enabled-deployment")
    registered_entries, configured_entries = register_provider_component_entries(
        app=application,
        config_path=config_path,
        logger=logging.getLogger("enabled-deployment"),
    )
    menu_items = ui_menu_items_from_component_entries(configured_entries)
    response = await application.test_client().get(FEATURE_URL)

    assert registered_entries == [ENTRY_POINT]
    assert [(item.label, item.url) for item in menu_items] == [(FEATURE_LABEL, FEATURE_URL)]
    assert response.status_code == 200


async def _verify_disabled_deployment(config_path: Path) -> None:
    """Assert disabled deployment omits menu metadata and generator routes.

    Args:
        config_path: Disabled scenario runtime configuration.
    """
    from opamp_provider.component_features import (
        register_provider_component_entries,
        ui_menu_items_from_component_entries,
    )
    from quart import Quart

    os.environ[ENV_OPAMP_CONFIG_PATH] = str(config_path)
    application = Quart("disabled-deployment")
    registered_entries, configured_entries = register_provider_component_entries(
        app=application,
        config_path=config_path,
        logger=logging.getLogger("disabled-deployment"),
    )
    menu_items = ui_menu_items_from_component_entries(configured_entries)
    response = await application.test_client().get(FEATURE_URL)

    assert registered_entries == []
    assert menu_items == []
    assert response.status_code == 404


def main() -> int:
    """Run both deployment variants and return a container-friendly exit code."""
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("--repo-root", type=Path, required=True)
    arguments = argument_parser.parse_args()
    repo_root = arguments.repo_root.resolve()
    _configure_import_paths(repo_root)
    with tempfile.TemporaryDirectory(prefix="client-config-generator-deployment-") as temp_name:
        scenario_root = Path(temp_name)
        enabled_config = _write_deployment_config(scenario_root, enabled=True)
        disabled_config = _write_deployment_config(scenario_root, enabled=False)
        asyncio.run(_verify_enabled_deployment(enabled_config))
        asyncio.run(_verify_disabled_deployment(disabled_config))
    print("client config generator enabled/disabled deployment checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
