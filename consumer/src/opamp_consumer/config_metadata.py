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

"""Shared config metadata model and helper utilities for consumer clients."""

from __future__ import annotations

import logging
import pathlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

TEXT_FILE_ENCODING = "utf-8"  # Encoding used when reading config text files.
CONFIG_METADATA_KEY_ADDITIONAL_METADATA = "additional_metadata"
CONFIG_METADATA_KEY_AGENT_DESCRIPTION = "agent_description"
CONFIG_METADATA_KEY_CONFIG_DATA = "config_data"
CONFIG_METADATA_KEY_CONFIG_TYPE = "config_type"
CONFIG_METADATA_KEY_CONFIG_VERSION = "config_version"
CONFIG_METADATA_KEY_CONFIGURATION_DATE = "configuration_date"
CONFIG_METADATA_KEY_SCM_CONFIG_VERSION = "SCM_config_version"
CONFIG_METADATA_KEY_SCM_SOURCE_NAME = "SCM_source_name"
CONFIG_METADATA_KEY_SERVICE_INSTANCE_ID = "service_instance_id"
CONFIG_METADATA_KEY_SERVICE_INSTANCE_UID = "service_instance_uid"
CONFIG_METADATA_KEY_VERSION = "version"
LEGACY_CONFIG_METADATA_KEY_CLIENT_VERSION_BASELINE = "client_version_baseline"
LEGACY_CONFIG_METADATA_KEY_SCM_NAME = "scm_name"


@dataclass
class ConfigMetadata:
    """Structured metadata extracted from a client-specific configuration source."""

    config_version: str = ""  # Parsed config version identifier when present.
    config_data: str = ""  # Raw config text or payload used to derive metadata.
    version: str = ""  # Config-service definition/catalog version associated with the config.
    config_type: str = ""  # Config-service type label such as Fluentbit or fluentd.
    configuration_date: str = ""  # Config-service metadata date value.
    SCM_config_version: str = ""  # Source-controlled configuration revision identifier.
    SCM_source_name: str = ""  # Source repository or other SCM source identifier.
    additional_metadata: dict[str, str] = field(
        default_factory=dict
    )  # Extra metadata not promoted into the top-level fields.

    @property
    def client_version_baseline(self) -> str:
        """Return the legacy consumer alias for config-service `version`."""
        return self.version

    @client_version_baseline.setter
    def client_version_baseline(self, value: str) -> None:
        """Set the legacy consumer alias by updating config-service `version`."""
        self.version = str(value or "").strip()

    @property
    def scm_name(self) -> str:
        """Return the legacy consumer alias for config-service `SCM_source_name`."""
        return self.SCM_source_name

    @scm_name.setter
    def scm_name(self, value: str) -> None:
        """Set the legacy consumer alias by updating `SCM_source_name`."""
        self.SCM_source_name = str(value or "").strip()


def read_config_text(
    config_path: str | pathlib.Path | None,
    *,
    logger: logging.Logger,
    config_type: str,
) -> str:
    """Read and return config text, logging a warning when the path is unusable.

    Args:
        config_path: Config file path to read.
        logger: Logger used for warning/error messages.
        config_type: Human-readable config type label used in warning messages.

    Returns:
        File contents as text, or an empty string when the file could not be read.
    """
    if not config_path:
        logger.warning(
            "config metadata extraction unsupported for %s because no config path was provided",
            config_type,
        )
        return ""

    path = pathlib.Path(config_path)
    try:
        return path.read_text(encoding=TEXT_FILE_ENCODING)
    except OSError as error:
        logger.warning(
            "config metadata extraction failed for %s config %s: %s",
            config_type,
            path,
            error,
        )
        return ""


def build_additional_metadata(
    metadata_values: Mapping[str, str],
    *,
    excluded_keys: Iterable[str],
) -> dict[str, str]:
    """Return metadata entries not mapped into top-level dataclass fields.

    Args:
        metadata_values: Full set of normalized metadata key/value pairs.
        excluded_keys: Keys already promoted into dedicated dataclass fields.

    Returns:
        Dictionary containing only non-empty metadata entries not in `excluded_keys`.
    """
    excluded_key_set = {
        str(value).strip().lower()
        for value in excluded_keys
        if str(value).strip()
    }
    return {
        str(key).strip(): str(value).strip()
        for key, value in metadata_values.items()
        if str(key).strip()
        and str(key).strip().lower() not in excluded_key_set
        and str(value).strip()
    }
