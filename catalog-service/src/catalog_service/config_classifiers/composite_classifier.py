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

"""Composite classifier that fans out to concrete config classifiers.

Evaluation summary:
- Read file text once, then run concrete classifiers in deterministic order.
- Return the first non-`None` classification result (first-match-wins).
- Return `None` only when no classifier recognizes the payload.
"""

from __future__ import annotations

import io
from collections.abc import Sequence
from typing import TextIO

from catalog_service.config_classifiers.config_classifier import (
    ConfigClassification,
    ConfigClassifier,
    read_text_from_handle,
)
from catalog_service.config_classifiers.fluentbit_classic_classifier import (
    FluentBitClassicConfigClassifier,
)
from catalog_service.config_classifiers.fluentbit_yaml_classifier import (
    FluentBitYamlConfigClassifier,
)
from catalog_service.config_classifiers.fluentd_classifier import FluentdConfigClassifier
from catalog_service.config_classifiers.json_config_classifier import JsonConfigClassifier


class CompositeConfigClassifier:
    """Try classifiers in sequence and return first successful classification."""

    def __init__(self, classifiers: Sequence[ConfigClassifier] | None = None) -> None:
        self.classifiers: list[ConfigClassifier] = list(
            classifiers
            or (
                FluentBitClassicConfigClassifier(),
                FluentBitYamlConfigClassifier(),
                FluentdConfigClassifier(),
                JsonConfigClassifier(),
            )
        )

    def classify(self, file_handle: TextIO) -> ConfigClassification | None:
        """Return first matching classification result, or None when unknown."""
        text = read_text_from_handle(file_handle)
        for classifier in self.classifiers:
            result = classifier.classify(io.StringIO(text))
            if result is not None:
                return result
        return None
