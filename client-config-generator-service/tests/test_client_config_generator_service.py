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

"""Tests for safe storage and schema validation behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from client_config_generator_service.runtime_config import component_root
from client_config_generator_service.service import ConfigurationFileService


def _valid_configuration(mode: str = "Supervisor") -> dict[str, object]:
    """Build the smallest valid configuration for a selected process mode.

    Args:
        mode: Supervisor or Observer schema selection.
    """
    consumer = {
        "server_url": "http://localhost:8080",
        "transport": "http",
        "processTracking": mode,
        "service_type": "fluentbit",
        "heartbeat_frequency": 30,
        "log_level": "debug",
    }
    if mode == "Observer":
        consumer["processDetectionRegex"] = "fluent-bit"
    return {"consumer": consumer}


def _service(tmp_path: Path, *, read_only: bool = False) -> ConfigurationFileService:
    """Create a file service backed by the packaged schema.

    Args:
        tmp_path: Isolated storage directory supplied by pytest.
        read_only: Whether save operations should be rejected.
    """
    return ConfigurationFileService(
        root_directory=tmp_path / "configs",
        schema_path=component_root() / "schemas" / "consumer_config_schema.json",
        read_only=read_only,
    )


def test_service_saves_lists_and_loads_valid_supervisor_configuration(tmp_path: Path) -> None:
    """A valid payload should round trip through atomic JSON persistence."""
    service = _service(tmp_path)
    configuration = _valid_configuration()

    saved_path = service.save_configuration("team/consumer.json", configuration)

    assert saved_path.is_file()
    assert service.list_configurations() == ["team/consumer.json"]
    assert service.load_configuration("team/consumer.json") == configuration
    assert json.loads(saved_path.read_text(encoding="utf-8")) == configuration


def test_service_requires_observer_detection_regex(tmp_path: Path) -> None:
    """Observer mode should fail schema validation without its discovery regex."""
    service = _service(tmp_path)
    configuration = _valid_configuration("Observer")
    del configuration["consumer"]["processDetectionRegex"]

    result = service.validate_configuration(configuration)

    assert result["valid"] is False
    assert any("processDetectionRegex" in item["message"] for item in result["errors"])


@pytest.mark.parametrize("name", ["../outside.json", "consumer.yaml", ""])
def test_service_rejects_unsafe_or_non_json_names(tmp_path: Path, name: str) -> None:
    """File access should be constrained to JSON files beneath configured storage."""
    service = _service(tmp_path)

    with pytest.raises(ValueError):
        service.resolve_configuration_path(name)


def test_service_rejects_writes_in_read_only_mode(tmp_path: Path) -> None:
    """Read-only deployments should retain load APIs but reject mutations."""
    service = _service(tmp_path, read_only=True)

    with pytest.raises(PermissionError):
        service.save_configuration("consumer.json", _valid_configuration())


def test_service_rejects_invalid_save_and_non_object_load(tmp_path: Path) -> None:
    """Schema-invalid saves and non-object JSON documents should fail explicitly."""
    service = _service(tmp_path)
    with pytest.raises(ValueError):
        service.save_configuration("invalid.json", {"consumer": {}})

    invalid_path = service.root_directory / "array.json"
    invalid_path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        service.load_configuration("array.json")
