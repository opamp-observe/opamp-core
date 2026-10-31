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

"""Classifier for JSON-based Fluent Bit and Fluentd config/catalog payloads.

Evaluation summary:
- Parse the file as JSON and require a top-level object.
- Resolve config type using, in order:
  1) declared header metadata `config_type`
  2) payload `configType`
  3) payload `engine`
  4) presence of `fluent_bit_version` / `fluentd_version`
- Reject when no Fluent Bit/Fluentd type can be resolved.
- Populate attributes from metadata plus normalized `engine` and `version` fields.
"""

from __future__ import annotations

import json
from typing import TextIO

from catalog_service.config_classifiers.config_classifier import (
    METADATA_CONFIG_TYPE,
    ConfigClassification,
    ConfigClassifier,
    extract_header_metadata,
    read_text_from_handle,
)

KEY_CONFIG_TYPE_CAMEL = "configType"
KEY_ENGINE = "engine"
KEY_VERSION = "version"
KEY_FLUENT_BIT_VERSION = "fluent_bit_version"
KEY_FLUENTD_VERSION = "fluentd_version"
VALUE_FLUENT_BIT = "fluentbit"
VALUE_FLUENTD = "fluentd"
ENGINE_ALIASES = {
    "fluentbit": VALUE_FLUENT_BIT,
    "fluent-bit": VALUE_FLUENT_BIT,
    "fluentd": VALUE_FLUENTD,
}


class JsonConfigClassifier(ConfigClassifier):
    """Classify JSON payloads and derive table metadata attributes."""

    config_type = ""

    def accepted_config_types(self) -> tuple[str, ...]:
        return tuple(ENGINE_ALIASES.keys())

    def classify(self, file_handle: TextIO) -> ConfigClassification | None:
        """Return JSON-derived classification when engine/type resolution succeeds."""
        text = read_text_from_handle(file_handle)
        metadata = extract_header_metadata(text)
        declared = str(metadata.get(METADATA_CONFIG_TYPE) or "").strip().lower()
        if declared and declared not in self.accepted_config_types():
            return None

        try:
            payload = json.loads(text)
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None

        resolved_type = self._resolved_type(payload=payload, declared=declared)
        if not resolved_type:
            return None

        attributes: dict[str, str] = {
            key: value for key, value in metadata.items() if key != METADATA_CONFIG_TYPE
        }
        attributes.setdefault(KEY_ENGINE, resolved_type)
        version = self._resolved_version(payload)
        if version:
            attributes.setdefault(KEY_VERSION, version)
        return ConfigClassification(config_type=resolved_type, attributes=attributes)

    @staticmethod
    def _resolved_type(*, payload: dict[str, object], declared: str) -> str:
        if declared:
            normalized = ENGINE_ALIASES.get(declared)
            if normalized:
                return normalized
        payload_type = str(payload.get(KEY_CONFIG_TYPE_CAMEL) or "").strip().lower()
        if payload_type in ENGINE_ALIASES:
            return ENGINE_ALIASES[payload_type]
        engine = str(payload.get(KEY_ENGINE) or "").strip().lower()
        if engine in ENGINE_ALIASES:
            return ENGINE_ALIASES[engine]
        if KEY_FLUENT_BIT_VERSION in payload:
            return VALUE_FLUENT_BIT
        if KEY_FLUENTD_VERSION in payload:
            return VALUE_FLUENTD
        return ""

    @staticmethod
    def _resolved_version(payload: dict[str, object]) -> str:
        for key in (KEY_VERSION, KEY_FLUENT_BIT_VERSION, KEY_FLUENTD_VERSION):
            value = payload.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return ""

    def _recognizes(self, *, text: str, metadata: dict[str, str]) -> bool:
        del text, metadata
        return False
