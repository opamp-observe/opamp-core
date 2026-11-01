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

"""Abstract contract and shared helpers for config-file classification.

Evaluation summary:
- Extract top-of-file `config-service:` metadata comments.
- Respect metadata `config_type` when provided and reject conflicting classifiers.
- Delegate format recognition to concrete `_recognizes(...)` implementations.
- Build final classification from resolved type plus extracted metadata attributes.
"""

from __future__ import annotations

import abc
import logging
import re
from dataclasses import dataclass
from typing import TextIO

HEADER_LINE_PATTERN = re.compile(r"^\s*(?:#|//|;)\s?(.*)$")
METADATA_PATTERN = re.compile(r"^config-service:\s*([A-Za-z0-9_.-]+)\s*=\s*(.*?)\s*$")
METADATA_CONFIG_TYPE = "config_type"
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConfigClassification:
    """Classification result for one config file."""

    config_type: str
    attributes: dict[str, str]


def read_text_from_handle(file_handle: TextIO) -> str:
    """Read full text from one file handle and restore offset when possible."""
    position: int | None = None
    try:
        position = file_handle.tell()
    except (AttributeError, OSError, ValueError):
        position = None

    content = file_handle.read()
    if isinstance(content, str):
        text = content
    else:
        text = str(content or "")

    if position is not None:
        try:
            file_handle.seek(position)
        except (AttributeError, OSError, ValueError):
            pass
    return text


def extract_header_metadata(text: str) -> dict[str, str]:
    """Extract `config-service:` metadata from the top comment block."""
    metadata: dict[str, str] = {}
    for raw_line in str(text or "").splitlines():
        stripped = raw_line.strip()
        if not stripped:
            if metadata:
                break
            continue
        header_match = HEADER_LINE_PATTERN.match(raw_line)
        if not header_match:
            break
        comment_text = str(header_match.group(1) or "").strip()
        meta_match = METADATA_PATTERN.match(comment_text)
        if not meta_match:
            continue
        key = str(meta_match.group(1) or "").strip()
        value = str(meta_match.group(2) or "").strip()
        if key:
            metadata[key] = value
    return metadata


class ConfigClassifier(abc.ABC):
    """Abstract base class for one config-type recognizer."""

    config_type: str = ""

    def classify(self, file_handle: TextIO) -> ConfigClassification | None:
        """Return classification when file matches this classifier, else None."""
        text = read_text_from_handle(file_handle)
        metadata = extract_header_metadata(text)
        if self._metadata_conflicts(metadata):
            return None
        if self._recognizes(text=text, metadata=metadata) is not True:
            return None
        resolved_type = str(metadata.get(METADATA_CONFIG_TYPE) or self.config_type).strip()
        attributes = {
            key: value
            for key, value in metadata.items()
            if key != METADATA_CONFIG_TYPE
        }
        classification = ConfigClassification(
            config_type=resolved_type or self.config_type,
            attributes=attributes,
        )
        LOGGER.debug(
            "classified config properties classifier=%s config_type=%s attributes=%s",
            self.__class__.__name__,
            classification.config_type,
            classification.attributes,
        )
        return classification

    def accepted_config_types(self) -> tuple[str, ...]:
        """Return metadata `config_type` values accepted by this classifier."""
        return (self.config_type,)

    def _metadata_conflicts(self, metadata: dict[str, str]) -> bool:
        configured = str(metadata.get(METADATA_CONFIG_TYPE) or "").strip().lower()
        if not configured:
            return False
        allowed = {item.lower() for item in self.accepted_config_types()}
        return configured not in allowed

    @abc.abstractmethod
    def _recognizes(self, *, text: str, metadata: dict[str, str]) -> bool:
        """Return whether this classifier recognizes the config payload."""
