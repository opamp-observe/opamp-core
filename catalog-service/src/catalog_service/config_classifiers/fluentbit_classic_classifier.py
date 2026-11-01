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

"""Classifier for Fluent Bit classic (`.conf`) style files.

Evaluation summary:
- Accept when classic section headers like `[SERVICE]` are present.
- Accept when classic include directives like `@include ...` are present.
- Otherwise reject so later classifiers can attempt classification.
"""

from __future__ import annotations

import re

from catalog_service.config_classifiers.config_classifier import ConfigClassifier

SECTION_HEADER_PATTERN = re.compile(r"^\s*\[[A-Za-z][A-Za-z0-9_\- ]*\]\s*$", re.MULTILINE)
INCLUDE_PATTERN = re.compile(r"^\s*@include\b", re.IGNORECASE | re.MULTILINE)


class FluentBitClassicConfigClassifier(ConfigClassifier):
    """Classify Fluent Bit classic format driven by `[SECTION]` and `@include`."""

    config_type = "fluentbit"

    def accepted_config_types(self) -> tuple[str, ...]:
        return ("fluentbit", "fluent-bit")

    def _recognizes(self, *, text: str, metadata: dict[str, str]) -> bool:
        """Return whether classic Fluent Bit structural markers are present."""
        del metadata
        if SECTION_HEADER_PATTERN.search(text):
            return True
        return bool(INCLUDE_PATTERN.search(text))
