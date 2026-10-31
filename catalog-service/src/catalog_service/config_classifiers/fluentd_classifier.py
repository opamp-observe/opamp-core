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

"""Classifier for Fluentd directive-style config files.

Evaluation summary:
- Accept when known Fluentd directives like `<source>`, `<match>`, `<filter>`, etc. are present.
- Accept when `@include ...` directives are present.
- Otherwise reject so other classifiers can continue.
"""

from __future__ import annotations

import re

from catalog_service.config_classifiers.config_classifier import ConfigClassifier

FLUENTD_DIRECTIVE_PATTERN = re.compile(
    r"^\s*<(?:"
    r"source|match|filter|system|label|worker|parse|format|buffer|transport|"
    r"storage|service_discovery|extract|inject|record|regexp|exclude|store|secondary"
    r")\b.*>\s*$",
    re.IGNORECASE | re.MULTILINE,
)
FLUENTD_INCLUDE_PATTERN = re.compile(r"^\s*@include\b", re.IGNORECASE | re.MULTILINE)


class FluentdConfigClassifier(ConfigClassifier):
    """Classify Fluentd configs by `<directive>` and `@include` usage."""

    config_type = "fluentd"

    def _recognizes(self, *, text: str, metadata: dict[str, str]) -> bool:
        """Return whether content contains Fluentd-style directives/includes."""
        del metadata
        if FLUENTD_DIRECTIVE_PATTERN.search(text):
            return True
        return bool(FLUENTD_INCLUDE_PATTERN.search(text))
