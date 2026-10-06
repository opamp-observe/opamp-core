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

"""Tests for generator runtime configuration precedence and path handling."""

from __future__ import annotations

import json
from pathlib import Path

from client_config_generator_service.runtime_config import (
    DEFAULT_WEB_PORT,
    ENV_CONFIG_PATH,
    ENV_CONFIGURATION_DIRECTORY,
    ENV_LOG_LEVEL,
    ENV_READ_ONLY,
    ENV_WEB_PORT,
    load_config_payload,
    load_settings,
    resolve_config_path,
)


def test_load_settings_resolves_shared_config_and_relative_storage(tmp_path: Path) -> None:
    """Shared component settings should resolve relative paths from the config file."""
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(
            {
                "opamp": {
                    "client_config_generator": {
                        "web_port": 9123,
                        "log_level": "debug",
                        "read_only": True,
                        "storage": {"configuration_directory": "saved"},
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    settings = load_settings(config_path)

    assert settings.config_path == config_path.resolve()
    assert settings.configuration_directory == (tmp_path / "saved").resolve()
    assert settings.read_only is True
    assert settings.web_port == 9123
    assert settings.log_level == "DEBUG"


def test_load_settings_gives_environment_values_precedence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Environment values should override the shared JSON component object."""
    config_path = tmp_path / "opamp.json"
    config_path.write_text("{}", encoding="utf-8")
    override_directory = tmp_path / "environment-configs"
    monkeypatch.setenv(ENV_CONFIGURATION_DIRECTORY, str(override_directory))
    monkeypatch.setenv(ENV_LOG_LEVEL, "warning")
    monkeypatch.setenv(ENV_READ_ONLY, "yes")
    monkeypatch.setenv(ENV_WEB_PORT, "9011")

    settings = load_settings(config_path)

    assert settings.configuration_directory == override_directory.resolve()
    assert settings.log_level == "WARNING"
    assert settings.read_only is True
    assert settings.web_port == 9011


def test_load_config_payload_handles_missing_file_and_rejects_non_object(tmp_path: Path) -> None:
    """Missing config may use defaults, while a present non-object JSON file is invalid."""
    assert load_config_payload(tmp_path / "missing.json") == {}
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("[]", encoding="utf-8")

    try:
        load_config_payload(invalid_path)
    except ValueError as error:
        assert "JSON object" in str(error)
    else:
        raise AssertionError("non-object configuration should fail")


def test_config_path_and_invalid_values_fall_back_safely(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Config-path environment and malformed component values should use safe defaults."""
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(
            {
                "opamp": {
                    "client_config_generator": {
                        "web_port": "not-a-port",
                        "storage": "invalid",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(ENV_CONFIG_PATH, str(config_path))

    settings = load_settings()

    assert resolve_config_path() == config_path.resolve()
    assert settings.web_port == DEFAULT_WEB_PORT
    assert settings.read_only is False
    assert settings.configuration_directory == (
        tmp_path / "generated-client-configs"
    ).resolve()
