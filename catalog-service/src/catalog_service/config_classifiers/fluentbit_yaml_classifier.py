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

"""Classifier for Fluent Bit YAML style config files.

Evaluation summary:
- Accept when non-comment lines follow YAML key/value mapping form.
- Reject when JSON-like leading tokens (`{` or `[`) are detected.
- Reject when classic `[SECTION]` directives are detected.
- Reject when Fluentd directive syntax (`<source>`, `</match>`, `@...`) is detected.
"""

from __future__ import annotations

import re

from catalog_service.config_classifiers.config_classifier import ConfigClassifier

YAML_KEY_PATTERN = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_-]*\s*:\s*.*$")
CLASSIC_SECTION_PATTERN = re.compile(r"^\s*\[[A-Za-z][A-Za-z0-9_\- ]*\]\s*$")
FLUENTD_DIRECTIVE_PATTERN = re.compile(r"^\s*<[/@A-Za-z_]")
COMMENT_PREFIXES = ("#", ";", "//")


class FluentBitYamlConfigClassifier(ConfigClassifier):
    """Classify Fluent Bit YAML content by key/value mapping structure."""

    config_type = "fluentbit"

    def accepted_config_types(self) -> tuple[str, ...]:
        return ("fluentbit", "fluent-bit")

    def _recognizes(self, *, text: str, metadata: dict[str, str]) -> bool:
        """Return whether content looks YAML-like and not classic/Fluentd/JSON."""
        del metadata
        yaml_like_lines = 0
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            if stripped.startswith(COMMENT_PREFIXES):
                continue
            if stripped.startswith("{") or stripped.startswith("["):
                return False
            if CLASSIC_SECTION_PATTERN.match(raw_line):
                return False
            if FLUENTD_DIRECTIVE_PATTERN.match(raw_line):
                return False
            if YAML_KEY_PATTERN.match(raw_line):
                yaml_like_lines += 1
                continue
            if yaml_like_lines > 0:
                continue
            return False
        return yaml_like_lines > 0
