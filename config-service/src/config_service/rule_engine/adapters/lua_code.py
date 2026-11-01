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

from __future__ import annotations

import logging
import re
from typing import Any

from config_service.rule_engine.base import RuleAdapter, RuleContext

KEY_PIPELINE = "pipeline"
KEY_PLUGINS = "plugins"
KEY_INPUTS = "inputs"
KEY_FILTERS = "filters"
KEY_OUTPUTS = "outputs"
KEY_NAME = "name"
KEY_FIELDS = "fields"
KEY_DATA_TYPE = "data_type"
KEY_VALIDATION_RULE = "validation_rule"
KEY_KIND = "kind"
KEY_LANGUAGE = "language"
KEY_CODE = "code"
KEY_PATH = "path"
KEY_MESSAGE = "message"
KEY_SEVERITY = "severity"
KEY_SOURCE = "source"

ISSUE_SEVERITY_ERROR = "error"
ISSUE_SOURCE_RULES = "rules"
DATA_TYPE_CODE = "code"
VALIDATION_KIND_CODE_SYNTAX = "code_syntax"
LANGUAGE_LUA = "lua"
PIPELINE_CONFIG_PATH_PREFIX = "$.config.pipeline"

LOGGER = logging.getLogger(__name__)

try:
    from luaparser import ast as lua_ast
except ImportError:  # pragma: no cover - exercised via runtime fallback
    # Mitigates optional dependency environments where luaparser is not installed.
    lua_ast = None


def _issue(
    code: str,
    path: str,
    message: str,
    severity: str = ISSUE_SEVERITY_ERROR,
    source: str = ISSUE_SOURCE_RULES,
) -> dict[str, Any]:
    """Create a consistently-shaped rule-engine issue payload."""
    return {
        KEY_CODE: code,
        KEY_PATH: path,
        KEY_MESSAGE: message,
        KEY_SEVERITY: severity,
        KEY_SOURCE: source,
    }


class LuaCodeSyntaxAdapter(RuleAdapter):
    """Validate inline Lua snippets declared in catalog fields of type `code`."""

    _LINE_COL_RE = re.compile(r"line\\s+(?P<line>\\d+):(?P<column>\\d+):\\s*(?P<detail>.+)$", re.IGNORECASE)

    def evaluate(self, context: RuleContext) -> list[dict[str, Any]]:
        """Scan pipeline plugins and validate only Lua-targeted `code` fields."""
        LOGGER.info("starting Lua code syntax evaluation version=%s", context.version)
        issues: list[dict[str, Any]] = []
        pipeline = context.config.get(KEY_PIPELINE, {})
        if not isinstance(pipeline, dict):
            LOGGER.warning("Lua code syntax evaluation skipped because pipeline is not a dict")
            return issues

        plugin_groups = context.catalog.get(KEY_PLUGINS, {})
        for section in (KEY_INPUTS, KEY_FILTERS, KEY_OUTPUTS):
            items = pipeline.get(section, [])
            if not isinstance(items, list):
                LOGGER.warning(
                    "Lua code syntax evaluation skipped non-list section section=%s type=%s",
                    section,
                    type(items).__name__,
                )
                continue
            section_defs = plugin_groups.get(section, {})
            for idx, plugin_instance in enumerate(items):
                if not isinstance(plugin_instance, dict):
                    LOGGER.warning(
                        "Lua code syntax evaluation skipped non-dict plugin instance section=%s index=%s type=%s",
                        section,
                        idx,
                        type(plugin_instance).__name__,
                    )
                    continue
                plugin_name = plugin_instance.get(KEY_NAME)
                if not isinstance(plugin_name, str) or not plugin_name:
                    LOGGER.warning(
                        "Lua code syntax evaluation skipped unnamed plugin section=%s index=%s",
                        section,
                        idx,
                    )
                    continue
                plugin_def = section_defs.get(plugin_name)
                if not isinstance(plugin_def, dict):
                    LOGGER.debug(
                        "Lua code syntax evaluation found no catalog definition section=%s plugin=%s",
                        section,
                        plugin_name,
                    )
                    continue
                issues.extend(
                    self._validate_plugin_code_fields(
                        plugin_instance=plugin_instance,
                        plugin_def=plugin_def,
                        path_prefix=f"{PIPELINE_CONFIG_PATH_PREFIX}.{section}[{idx}]",
                    )
                )
        LOGGER.info(
            "completed Lua code syntax evaluation version=%s issue_count=%s",
            context.version,
            len(issues),
        )
        return issues

    def _validate_plugin_code_fields(
        self,
        *,
        plugin_instance: dict[str, Any],
        plugin_def: dict[str, Any],
        path_prefix: str,
    ) -> list[dict[str, Any]]:
        """Find Lua code fields on a plugin instance and validate their source."""
        issues: list[dict[str, Any]] = []
        plugin_name = str(plugin_instance.get(KEY_NAME, "")).strip().lower()
        for field in plugin_def.get(KEY_FIELDS, []):
            if not isinstance(field, dict):
                LOGGER.warning("Lua code syntax skipped non-dict field definition path_prefix=%s", path_prefix)
                continue
            if str(field.get(KEY_DATA_TYPE, "")).lower() != DATA_TYPE_CODE:
                continue
            if not self._targets_lua(field=field, plugin_name=plugin_name):
                continue

            field_name = str(field.get(KEY_NAME, ""))
            if not field_name:
                LOGGER.warning("Lua code syntax skipped unnamed field definition path_prefix=%s", path_prefix)
                continue
            code_value = plugin_instance.get(field_name)
            if code_value is None:
                continue
            if not isinstance(code_value, str):
                LOGGER.warning(
                    "Lua code syntax skipped non-string code field path=%s.%s type=%s",
                    path_prefix,
                    field_name,
                    type(code_value).__name__,
                )
                continue
            if not code_value.strip():
                LOGGER.warning("Lua code syntax skipped blank code field path=%s.%s", path_prefix, field_name)
                continue

            issues.extend(
                self._validate_lua_source(
                    source=code_value,
                    path=f"{path_prefix}.{field_name}",
                )
            )
        return issues

    @staticmethod
    def _targets_lua(*, field: dict[str, Any], plugin_name: str) -> bool:
        """Route `code` fields to Lua validation when explicitly or contextually Lua."""
        validation_rule = field.get(KEY_VALIDATION_RULE)
        if isinstance(validation_rule, dict):
            kind = str(validation_rule.get(KEY_KIND, "")).lower()
            language = str(validation_rule.get(KEY_LANGUAGE, "")).lower()
            if kind == VALIDATION_KIND_CODE_SYNTAX and language:
                return language == LANGUAGE_LUA
        return plugin_name == LANGUAGE_LUA

    def _validate_lua_source(self, *, source: str, path: str) -> list[dict[str, Any]]:
        """Run luaparser and normalize syntax failures into UI-friendly issues."""
        if lua_ast is None:
            LOGGER.warning("Lua validation parser unavailable path=%s", path)
            return [
                _issue(
                    "lua_parser_unavailable",
                    path,
                    "Lua validation is unavailable because the 'luaparser' dependency is not installed.",
                )
            ]

        try:
            lua_ast.parse(source)
            LOGGER.debug("Lua syntax validation succeeded path=%s", path)
        except Exception as exc:  # luaparser raises SyntaxException with formatted text
            # Mitigates parser crashes/format variance by converting to stable API errors.
            message = str(exc).strip() or "Lua syntax validation failed."
            match = self._LINE_COL_RE.search(message)
            if match:
                line = match.group("line")
                column = match.group("column")
                detail = match.group("detail").strip()
                message = f"Lua syntax error at line {line}, column {column}: {detail}"
            elif message.lower() in {"none", "syntax errors: none", "syntax errors"}:
                message = "Lua syntax error: the source is incomplete or invalid."
            elif not message.lower().startswith("lua syntax error"):
                message = f"Lua syntax error: {message}"
            LOGGER.warning("Lua syntax validation failed path=%s message=%s", path, message)
            return [_issue("lua_syntax_error", path, message)]
        return []


CUSTOM_ADAPTERS: dict[str, type[RuleAdapter]] = {
    "custom.lua_code_syntax": LuaCodeSyntaxAdapter,
}
