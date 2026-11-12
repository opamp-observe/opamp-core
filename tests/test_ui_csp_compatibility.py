#!/usr/bin/env python3
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

"""Regression tests for browser assets compatible with the strict CSP trial."""

from __future__ import annotations

import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
UI_HTML_ROOTS = (
    REPOSITORY_ROOT / "catalog-service" / "src" / "catalog_service" / "html",
    REPOSITORY_ROOT
    / "client-config-generator-service"
    / "src"
    / "client_config_generator_service"
    / "html",
    REPOSITORY_ROOT / "config-service" / "src" / "config_service" / "html",
    REPOSITORY_ROOT / "provider" / "src" / "opamp_provider" / "html",
    REPOSITORY_ROOT
    / "svr-credentials-mgr"
    / "src"
    / "svr_credentials_manager_service"
    / "html",
)
EXTERNAL_FONT_HOST_PATTERN = re.compile(
    r"fonts\.(?:googleapis|gstatic)\.com",
    re.IGNORECASE,
)
INLINE_EVENT_HANDLER_PATTERN = re.compile(r"\son[a-z]+\s*=", re.IGNORECASE)
INLINE_SCRIPT_PATTERN = re.compile(r"<script(?![^>]*\bsrc\s*=)[^>]*>", re.IGNORECASE)
INLINE_STYLE_ATTRIBUTE_PATTERN = re.compile(r"\sstyle\s*=", re.IGNORECASE)
INLINE_STYLE_BLOCK_PATTERN = re.compile(r"<style\b", re.IGNORECASE)


def test_ui_html_uses_only_external_scripts_styles_and_local_fonts() -> None:
    """Ensure strict-CSP preparation does not regress in packaged HTML assets."""
    html_paths = tuple(
        html_path
        for html_root in UI_HTML_ROOTS
        for html_path in html_root.rglob("*.html")
    )
    assert html_paths

    violations: list[str] = []
    checks = (
        ("external font host", EXTERNAL_FONT_HOST_PATTERN),
        ("inline event handler", INLINE_EVENT_HANDLER_PATTERN),
        ("inline script", INLINE_SCRIPT_PATTERN),
        ("inline style attribute", INLINE_STYLE_ATTRIBUTE_PATTERN),
        ("inline style block", INLINE_STYLE_BLOCK_PATTERN),
    )
    for html_path in html_paths:
        html_text = html_path.read_text(encoding="utf-8")
        for description, prohibited_pattern in checks:
            if prohibited_pattern.search(html_text):
                relative_path = html_path.relative_to(REPOSITORY_ROOT)
                violations.append(f"{relative_path}: {description}")

    assert not violations, "\n".join(violations)
