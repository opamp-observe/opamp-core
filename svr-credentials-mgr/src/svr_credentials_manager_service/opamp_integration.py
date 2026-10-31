# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Provider embedding entrypoint for the credentials manager service."""

from __future__ import annotations

import os
from pathlib import Path

from quart import Quart

from .app import DEFAULT_MAPPING_PATH, ENV_MAPPING_PATH, register_components
from .service_config import resolve_mapping_path_from_config, resolve_runtime_config_path
from .storage import ClientMappingStore, CredentialStore, create_default_backend


def _resolve_mapping_store_path(config_path: Path | None) -> Path:
    """Return the configured mapping-file path for embedded startup."""
    configured_mapping_path = os.environ.get(ENV_MAPPING_PATH, "").strip()
    if configured_mapping_path:
        return Path(configured_mapping_path).expanduser().resolve()
    resolved_config_path = resolve_runtime_config_path(config_path)
    config_mapping_path = resolve_mapping_path_from_config(resolved_config_path)
    if config_mapping_path is not None:
        return config_mapping_path
    return Path(DEFAULT_MAPPING_PATH).expanduser().resolve()


def register_credentials_manager_feature(opamp_app: Quart) -> None:
    """Mount credentials-manager routes into an existing provider Quart app."""
    resolved_config_path = resolve_runtime_config_path()
    credential_store = CredentialStore(create_default_backend(resolved_config_path))
    mapping_store = ClientMappingStore(_resolve_mapping_store_path(resolved_config_path))
    register_components(
        opamp_app,
        credential_store,
        mapping_store,
        config_path=resolved_config_path,
    )
    opamp_app.config["SVR_CREDENTIALS_MANAGER_MODE"] = "embedded"
