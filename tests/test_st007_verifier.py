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

"""Unit coverage for the ST-007 container verification helpers."""

# The container helpers intentionally expose private functions only to this focused test.
# pylint: disable=protected-access

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

SERVE_MODULE_NAME = "opamp_st007_serve_credentials_manager"
VERIFY_MODULE_NAME = "opamp_st007_verify"


def _load_script(module_name: str, script_name: str) -> ModuleType:
    """Load one ST-007 executable script as a testable Python module.

    Args:
        module_name: Unique import name assigned to the loaded module.
        script_name: File name under the ST-007 scripts directory.

    Returns:
        Imported script module.
    """
    module_path = (
        Path(__file__).resolve().parent
        / "test-containers"
        / "st007"
        / "scripts"
        / script_name
    )
    module_spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert module_spec is not None
    assert module_spec.loader is not None
    loaded_module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_name] = loaded_module
    module_spec.loader.exec_module(loaded_module)
    return loaded_module


def test_complete_definition_includes_every_supported_connection_section() -> None:
    """The integration fixture should exercise every standard and custom section."""
    verifier = _load_script(VERIFY_MODULE_NAME, "verify_st007.py")

    definition = verifier._complete_definition(
        "synthetic-private-marker",
        endpoint_prefix="unit",
    )

    assert set(definition) == {
        verifier.KEY_OPAMP,
        verifier.KEY_OWN_METRICS,
        verifier.KEY_OWN_TRACES,
        verifier.KEY_OWN_LOGS,
        verifier.KEY_OTHER_CONNECTIONS,
    }
    assert verifier.KEY_ARCHIVE in definition[verifier.KEY_OTHER_CONNECTIONS]
    assert (
        definition[verifier.KEY_OPAMP][verifier.KEY_HEADERS][verifier.HEADER_ST007_ACCESS]
        == "synthetic-private-marker"
    )


def test_fallback_record_validation_enforces_assigned_client_set() -> None:
    """Fallback evidence validation should reject missing or extra intended clients."""
    verifier = _load_script(VERIFY_MODULE_NAME, "verify_st007.py")
    connection_settings = {
        verifier.KEY_OPAMP: {},
        verifier.KEY_OWN_METRICS: {},
        verifier.KEY_OWN_TRACES: {},
        verifier.KEY_OWN_LOGS: {},
        verifier.KEY_OTHER_CONNECTIONS: {verifier.KEY_ARCHIVE: {}},
    }
    record = {
        verifier.KEY_CLIENT_ID: "client-a",
        verifier.KEY_CONNECTION_NAME: verifier.CONNECTION_SECONDARY,
        verifier.KEY_DELIVERY: verifier.VALUE_FALLBACK_LOG,
        verifier.KEY_APPLIED_AT_UTC: "2026-10-12T10:00:00Z",
        verifier.KEY_SERVER_TO_AGENT: {
            verifier.KEY_CONNECTION_SETTINGS: connection_settings
        },
    }

    verifier._assert_fallback_records([record], expected_client_ids={"client-a"})
    with pytest.raises(AssertionError):
        verifier._assert_fallback_records([record], expected_client_ids={"client-b"})


@pytest.mark.parametrize("seed_stale_mapping", [False, True])
def test_service_runtime_files_are_isolated_and_optionally_seed_stale_mapping(
    tmp_path: Path,
    seed_stale_mapping: bool,
) -> None:
    """The browser service fixture should create local config and controlled mappings."""
    service_helper = _load_script(
        SERVE_MODULE_NAME,
        "serve_credentials_manager.py",
    )

    config_path = service_helper._write_runtime_files(
        tmp_path,
        seed_stale_mapping=seed_stale_mapping,
    )
    config_payload = service_helper.json.loads(config_path.read_text(encoding="utf-8"))
    mapping_path = Path(
        config_payload[service_helper.KEY_STORAGE][service_helper.KEY_MAPPING_PATH]
    )
    mapping_payload = service_helper.json.loads(mapping_path.read_text(encoding="utf-8"))

    expected_mappings = (
        {
            service_helper.STALE_UI_CLIENT_ID: service_helper.STALE_CONNECTION_NAME,
        }
        if seed_stale_mapping
        else {}
    )
    assert mapping_payload == {service_helper.KEY_CLIENTS: expected_mappings}
    assert (
        config_payload[service_helper.KEY_AUTHORIZATION][
            service_helper.KEY_UI_USE_AUTHORIZATION
        ]
        == "none"
    )
