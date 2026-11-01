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

"""Simulator metadata extraction helpers."""

from __future__ import annotations

import json
import logging
from typing import Any

from opamp_consumer.config_metadata import (
    CONFIG_METADATA_KEY_ADDITIONAL_METADATA,
    CONFIG_METADATA_KEY_AGENT_DESCRIPTION,
    CONFIG_METADATA_KEY_CONFIG_DATA,
    CONFIG_METADATA_KEY_CONFIG_TYPE,
    CONFIG_METADATA_KEY_CONFIG_VERSION,
    CONFIG_METADATA_KEY_CONFIGURATION_DATE,
    CONFIG_METADATA_KEY_SCM_CONFIG_VERSION,
    CONFIG_METADATA_KEY_SCM_SOURCE_NAME,
    CONFIG_METADATA_KEY_SERVICE_INSTANCE_ID,
    CONFIG_METADATA_KEY_SERVICE_INSTANCE_UID,
    CONFIG_METADATA_KEY_VERSION,
    LEGACY_CONFIG_METADATA_KEY_CLIENT_VERSION_BASELINE,
    LEGACY_CONFIG_METADATA_KEY_SCM_NAME,
    ConfigMetadata,
    build_additional_metadata,
)

SIMULATOR_METADATA_CLIENT_VERSION = "client_version"
# Legacy simulator payload key used as the version baseline source.


def extract_simulator_config_metadata(
    additional_params: list[str] | None,
) -> ConfigMetadata:
    """Extract simulator metadata from JSON payloads passed via additional params.

    Args:
        additional_params: Extra CLI tokens provided for the simulated agent process.

    Returns:
        Normalized `ConfigMetadata` populated from the simulator JSON payload.
    """
    payload_dict = _parse_simulator_metadata_payload(additional_params)
    if payload_dict is None:
        return ConfigMetadata()

    metadata_values = _normalize_simulator_metadata_values(payload_dict)
    version = metadata_values.get(
        CONFIG_METADATA_KEY_VERSION,
        "",
    ) or metadata_values.get(SIMULATOR_METADATA_CLIENT_VERSION, "")

    nested_additional_metadata = _normalize_nested_additional_metadata(
        payload_dict.get(CONFIG_METADATA_KEY_ADDITIONAL_METADATA),
    )
    additional_metadata = build_additional_metadata(
        metadata_values,
        excluded_keys=(
            CONFIG_METADATA_KEY_CONFIG_VERSION,
            CONFIG_METADATA_KEY_CONFIG_TYPE,
            CONFIG_METADATA_KEY_CONFIGURATION_DATE,
            CONFIG_METADATA_KEY_SCM_CONFIG_VERSION,
            CONFIG_METADATA_KEY_SCM_SOURCE_NAME,
            CONFIG_METADATA_KEY_VERSION,
            SIMULATOR_METADATA_CLIENT_VERSION,
            CONFIG_METADATA_KEY_CONFIG_DATA,
            CONFIG_METADATA_KEY_ADDITIONAL_METADATA,
        ),
    )
    additional_metadata.update(nested_additional_metadata)

    return ConfigMetadata(
        config_version=metadata_values.get(CONFIG_METADATA_KEY_CONFIG_VERSION, ""),
        config_data=metadata_values.get(CONFIG_METADATA_KEY_CONFIG_DATA, ""),
        version=version,
        config_type=metadata_values.get(CONFIG_METADATA_KEY_CONFIG_TYPE, "simulator"),
        configuration_date=metadata_values.get(CONFIG_METADATA_KEY_CONFIGURATION_DATE, ""),
        SCM_config_version=metadata_values.get(CONFIG_METADATA_KEY_SCM_CONFIG_VERSION, ""),
        SCM_source_name=metadata_values.get(CONFIG_METADATA_KEY_SCM_SOURCE_NAME, ""),
        additional_metadata=additional_metadata,
    )


def _parse_simulator_metadata_payload(
    additional_params: list[str] | None,
) -> dict[str, Any] | None:
    """Parse the first valid simulator metadata JSON object from CLI tokens.

    Args:
        additional_params: Extra CLI tokens provided for the simulated agent process.

    Returns:
        Parsed JSON object, or `None` when no valid metadata payload is available.
    """
    if not additional_params:
        return None
    raw_tokens = [str(value).strip() for value in additional_params if str(value).strip()]
    if not raw_tokens:
        return None

    payload_candidates: list[str] = []
    if len(raw_tokens) == 1:
        payload_candidates.append(raw_tokens[0])
    else:
        payload_candidates.append(" ".join(raw_tokens))
        payload_candidates.extend(raw_tokens)

    for payload_text in payload_candidates:
        try:
            parsed_payload = json.loads(payload_text)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed_payload, dict):
            return parsed_payload

    logging.getLogger(__name__).warning(
        "simulator expected JSON object in --agent-additional-params but got: %s",
        raw_tokens,
    )
    return None


def _normalize_simulator_metadata_values(
    payload_dict: dict[str, Any],
) -> dict[str, str]:
    """Normalize supported top-level simulator metadata values into strings.

    Args:
        payload_dict: Parsed simulator metadata JSON object.

    Returns:
        Dictionary containing non-empty string metadata values.
    """
    normalized: dict[str, str] = {}
    supported_keys = (
        CONFIG_METADATA_KEY_AGENT_DESCRIPTION,
        CONFIG_METADATA_KEY_CONFIG_DATA,
        CONFIG_METADATA_KEY_CONFIG_TYPE,
        CONFIG_METADATA_KEY_CONFIG_VERSION,
        CONFIG_METADATA_KEY_CONFIGURATION_DATE,
        CONFIG_METADATA_KEY_SCM_CONFIG_VERSION,
        CONFIG_METADATA_KEY_SCM_SOURCE_NAME,
        CONFIG_METADATA_KEY_SERVICE_INSTANCE_ID,
        CONFIG_METADATA_KEY_SERVICE_INSTANCE_UID,
        CONFIG_METADATA_KEY_VERSION,
        LEGACY_CONFIG_METADATA_KEY_CLIENT_VERSION_BASELINE,
        LEGACY_CONFIG_METADATA_KEY_SCM_NAME,
        SIMULATOR_METADATA_CLIENT_VERSION,
    )
    for key in supported_keys:
        value = payload_dict.get(key)
        if value is None:
            continue
        normalized_value = str(value).strip()
        if normalized_value:
            if key == LEGACY_CONFIG_METADATA_KEY_CLIENT_VERSION_BASELINE:
                normalized[CONFIG_METADATA_KEY_VERSION] = normalized_value
                continue
            if key == LEGACY_CONFIG_METADATA_KEY_SCM_NAME:
                normalized[CONFIG_METADATA_KEY_SCM_SOURCE_NAME] = normalized_value
                continue
            normalized[key] = normalized_value
    return normalized


def _normalize_nested_additional_metadata(payload: Any) -> dict[str, str]:
    """Normalize nested `additional_metadata` payload values into strings.

    Args:
        payload: Nested JSON object value stored under `additional_metadata`.

    Returns:
        Dictionary of non-empty string key/value pairs.
    """
    if not isinstance(payload, dict):
        return {}
    normalized: dict[str, str] = {}
    for key, value in payload.items():
        normalized_key = str(key).strip()
        normalized_value = str(value).strip()
        if normalized_key and normalized_value:
            normalized[normalized_key] = normalized_value
    return normalized
