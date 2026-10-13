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

"""Start an isolated credentials-manager service for ST-007."""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

ENV_APP_ENABLE_DEV_FEATURES = "APP_ENABLE_DEV_FEATURES"
ENV_APPLY_LOG_PATH = "SVR_CREDENTIALS_CONNECTION_APPLY_LOG_PATH"
ENV_CONFIG_PATH = "SVR_CREDENTIALS_CONFIG_PATH"
ENV_FILE_DIRECTORY = "SVR_CREDENTIALS_FILE_DIRECTORY"
ENV_KEYRING_BACKEND = "SVR_CREDENTIALS_KEYRING_BACKEND"
ENV_MAPPING_PATH = "SVR_CREDENTIALS_MAPPING_PATH"
ENV_PLAINTEXT_PATH = "SVR_CREDENTIALS_PLAINTEXT_PATH"
ENV_PROVIDER_BASE_URL = "SVR_CREDENTIALS_PROVIDER_BASE_URL"
ENV_UI_AUTHORIZATION = "SVR_CREDENTIALS_UI_USE_AUTHORIZATION"
KEY_AUTHORIZATION = "authorization"
KEY_CLIENTS = "clients"
KEY_MAPPING_PATH = "mapping_path"
KEY_STORAGE = "storage"
KEY_UI_USE_AUTHORIZATION = "ui_use_authorization"
STALE_CONNECTION_NAME = "missing-ui-definition"
STALE_UI_CLIENT_ID = "stale-ui-client"
UTF8_ENCODING = "utf-8"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def _write_runtime_files(runtime_dir: Path, *, seed_stale_mapping: bool) -> Path:
    """Create isolated config and optional stale mapping fixtures.

    Args:
        runtime_dir: Directory that owns all mutable service state.
        seed_stale_mapping: Whether to seed one mapping to an absent definition.

    Returns:
        Path to the generated service configuration.
    """
    runtime_dir.mkdir(parents=True, exist_ok=True)
    mapping_path = runtime_dir / "client-mappings.json"
    mappings = (
        {STALE_UI_CLIENT_ID: STALE_CONNECTION_NAME} if seed_stale_mapping else {}
    )
    mapping_path.write_text(
        json.dumps({KEY_CLIENTS: mappings}, indent=2) + "\n",
        encoding=UTF8_ENCODING,
    )
    config_path = runtime_dir / "service-config.json"
    config_path.write_text(
        json.dumps(
            {
                KEY_STORAGE: {KEY_MAPPING_PATH: str(mapping_path)},
                KEY_AUTHORIZATION: {KEY_UI_USE_AUTHORIZATION: "none"},
            },
            indent=2,
        )
        + "\n",
        encoding=UTF8_ENCODING,
    )
    return config_path


def main() -> None:
    """Configure environment-backed storage and run the Quart service."""
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--provider-base-url", required=True)
    parser.add_argument("--seed-stale-mapping", action="store_true")
    arguments = parser.parse_args()

    config_path = _write_runtime_files(
        arguments.runtime_dir,
        seed_stale_mapping=arguments.seed_stale_mapping,
    )
    os.environ[ENV_APP_ENABLE_DEV_FEATURES] = "true"
    os.environ[ENV_APPLY_LOG_PATH] = str(arguments.runtime_dir / "fallback-deliveries.jsonl")
    os.environ[ENV_CONFIG_PATH] = str(config_path)
    os.environ[ENV_FILE_DIRECTORY] = str(arguments.runtime_dir / "connection-files")
    os.environ[ENV_KEYRING_BACKEND] = "plaintext"
    os.environ[ENV_MAPPING_PATH] = str(arguments.runtime_dir / "client-mappings.json")
    os.environ[ENV_PLAINTEXT_PATH] = str(arguments.runtime_dir / "credentials.json")
    os.environ[ENV_PROVIDER_BASE_URL] = arguments.provider_base_url
    os.environ[ENV_UI_AUTHORIZATION] = "none"

    # Import after setting environment values because the application resolves storage on import.
    from svr_credentials_manager_service.app import (  # pylint: disable=import-outside-toplevel
        create_app,
    )

    create_app(config_path=config_path).run(
        host="127.0.0.1",
        port=arguments.port,
        debug=False,
    )


if __name__ == "__main__":
    main()
