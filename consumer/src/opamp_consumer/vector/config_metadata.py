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

"""Vector config metadata extraction helpers."""

from __future__ import annotations

import logging
import pathlib
import re
from collections.abc import Callable

from opamp_consumer.config_metadata import (
    CONFIG_METADATA_KEY_AGENT_DESCRIPTION,
    CONFIG_METADATA_KEY_CONFIG_TYPE,
    CONFIG_METADATA_KEY_CONFIG_VERSION,
    CONFIG_METADATA_KEY_CONFIGURATION_DATE,
    CONFIG_METADATA_KEY_SCM_CONFIG_VERSION,
    CONFIG_METADATA_KEY_SCM_SOURCE_NAME,
    CONFIG_METADATA_KEY_SERVICE_INSTANCE_ID,
    CONFIG_METADATA_KEY_VERSION,
    LEGACY_CONFIG_METADATA_KEY_CLIENT_VERSION_BASELINE,
    LEGACY_CONFIG_METADATA_KEY_SCM_NAME,
    ConfigMetadata,
    build_additional_metadata,
    read_config_text,
)

MATCH_GROUP_KEY = "key"
MATCH_GROUP_VALUE = "value"
SUPPORTED_COMMENT_KEYS = (
    CONFIG_METADATA_KEY_AGENT_DESCRIPTION,
    CONFIG_METADATA_KEY_CONFIG_VERSION,
    CONFIG_METADATA_KEY_CONFIG_TYPE,
    CONFIG_METADATA_KEY_CONFIGURATION_DATE,
    CONFIG_METADATA_KEY_SCM_CONFIG_VERSION,
    CONFIG_METADATA_KEY_SCM_SOURCE_NAME,
    CONFIG_METADATA_KEY_SERVICE_INSTANCE_ID,
    CONFIG_METADATA_KEY_VERSION,
    LEGACY_CONFIG_METADATA_KEY_SCM_NAME,
    LEGACY_CONFIG_METADATA_KEY_CLIENT_VERSION_BASELINE,
)
COMMENT_METADATA_PATTERN = re.compile(
    rf"^\s*#\s*(?:config-service:\s*)?(?P<{MATCH_GROUP_KEY}>{'|'.join(SUPPORTED_COMMENT_KEYS)})\s*[:=]\s*"
    rf"(?P<{MATCH_GROUP_VALUE}>.+?)\s*$",
    re.IGNORECASE,
)
METADATA_KEY_ALIASES = {
    LEGACY_CONFIG_METADATA_KEY_CLIENT_VERSION_BASELINE.lower(): CONFIG_METADATA_KEY_VERSION,
    LEGACY_CONFIG_METADATA_KEY_SCM_NAME.lower(): CONFIG_METADATA_KEY_SCM_SOURCE_NAME,
    CONFIG_METADATA_KEY_AGENT_DESCRIPTION.lower(): CONFIG_METADATA_KEY_AGENT_DESCRIPTION,
    CONFIG_METADATA_KEY_CONFIG_TYPE.lower(): CONFIG_METADATA_KEY_CONFIG_TYPE,
    CONFIG_METADATA_KEY_CONFIG_VERSION.lower(): CONFIG_METADATA_KEY_CONFIG_VERSION,
    CONFIG_METADATA_KEY_CONFIGURATION_DATE.lower(): CONFIG_METADATA_KEY_CONFIGURATION_DATE,
    CONFIG_METADATA_KEY_SCM_CONFIG_VERSION.lower(): CONFIG_METADATA_KEY_SCM_CONFIG_VERSION,
    CONFIG_METADATA_KEY_SCM_SOURCE_NAME.lower(): CONFIG_METADATA_KEY_SCM_SOURCE_NAME,
    CONFIG_METADATA_KEY_SERVICE_INSTANCE_ID.lower(): CONFIG_METADATA_KEY_SERVICE_INSTANCE_ID,
    CONFIG_METADATA_KEY_VERSION.lower(): CONFIG_METADATA_KEY_VERSION,
}


def extract_vector_config_metadata(
    config_path: str | pathlib.Path | None,
    *,
    resolve_service_instance_id_template_fn: Callable[[str | None], str | None],
) -> ConfigMetadata:
    """Extract Vector metadata comments and raw config text."""
    logger = logging.getLogger(__name__)
    config_text = read_config_text(
        config_path,
        logger=logger,
        config_type="Vector",
    )
    if not config_text:
        return ConfigMetadata()

    metadata_values: dict[str, str] = {}
    for raw_line in config_text.splitlines():
        metadata_match = COMMENT_METADATA_PATTERN.match(raw_line)
        if metadata_match is None:
            continue
        key = METADATA_KEY_ALIASES.get(
            metadata_match.group(MATCH_GROUP_KEY).strip().lower(),
            metadata_match.group(MATCH_GROUP_KEY).strip(),
        )
        value = metadata_match.group(MATCH_GROUP_VALUE).strip()
        if key == CONFIG_METADATA_KEY_SERVICE_INSTANCE_ID:
            value = str(resolve_service_instance_id_template_fn(value) or "").strip()
        if value:
            metadata_values[key] = value

    return ConfigMetadata(
        config_version=metadata_values.get(CONFIG_METADATA_KEY_CONFIG_VERSION, ""),
        config_data=config_text,
        version=metadata_values.get(CONFIG_METADATA_KEY_VERSION, ""),
        config_type=metadata_values.get(CONFIG_METADATA_KEY_CONFIG_TYPE, "Vector"),
        configuration_date=metadata_values.get(CONFIG_METADATA_KEY_CONFIGURATION_DATE, ""),
        SCM_config_version=metadata_values.get(CONFIG_METADATA_KEY_SCM_CONFIG_VERSION, ""),
        SCM_source_name=metadata_values.get(CONFIG_METADATA_KEY_SCM_SOURCE_NAME, ""),
        additional_metadata=build_additional_metadata(
            metadata_values,
            excluded_keys=(
                CONFIG_METADATA_KEY_CONFIG_VERSION,
                CONFIG_METADATA_KEY_CONFIG_TYPE,
                CONFIG_METADATA_KEY_CONFIGURATION_DATE,
                CONFIG_METADATA_KEY_SCM_CONFIG_VERSION,
                CONFIG_METADATA_KEY_SCM_SOURCE_NAME,
                CONFIG_METADATA_KEY_VERSION,
            ),
        ),
    )
