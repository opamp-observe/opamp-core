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
from typing import Any

from config_service.rule_engine.base import RuleAdapter, RuleContext

KEY_PIPELINE = "pipeline"
KEY_PLUGINS = "plugins"
KEY_COMMON = "common"
KEY_PROCESSORS = "processors"
KEY_SIGNALS = "signals"
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
LANGUAGE_SQL = "sql"
PARSER_TYPE_LALR = "lalr"
LEXER_TYPE_CONTEXTUAL = "contextual"
PATH_PREFIX_PIPELINE_CONFIG = "$.config.pipeline"
SIGNAL_LOGS = "logs"

LOGGER = logging.getLogger(__name__)

try:
    from lark import Lark, Token, Tree, UnexpectedInput
except ImportError:  # pragma: no cover - runtime fallback only
    # Mitigates environments that intentionally omit heavy parser dependencies.
    Lark = None
    Token = None
    Tree = None
    UnexpectedInput = Exception


FLUENT_BIT_SQL_GRAMMAR = r"""
start: select_stmt

select_stmt: SELECT select_list FROM STREAM stream_name? where_clause? ";"

select_list: select_item ("," select_item)*
select_item: "*"                         -> wildcard_item
           | IDENTIFIER alias_clause?    -> identifier_item

alias_clause: AS IDENTIFIER
stream_name: IDENTIFIER
where_clause: WHERE condition

?condition: or_expr
?or_expr: and_expr (OR and_expr)*
?and_expr: unary_expr (AND unary_expr)*
?unary_expr: NOT unary_expr              -> not_expr
           | primary
?primary: "(" condition ")"             -> grouped_condition
        | comparison
        | value                          -> literal_condition

?comparison: operand IS NULL             -> is_null
           | operand IS NOT NULL         -> is_not_null
           | operand comparator value    -> binary_comparison
           | operand                     -> truthy_operand

?operand: IDENTIFIER                     -> key_operand
        | RECORD "." CONTAINS "(" IDENTIFIER ")" -> record_contains

comparator: "="
          | NEQ
          | LT
          | LTE
          | GT
          | GTE

?value: NUMBER                           -> number_value
      | STRING                           -> string_value
      | BOOLEAN                          -> boolean_value

SELECT.2: /SELECT/i
AS.2: /AS/i
FROM.2: /FROM/i
STREAM.2: /STREAM/i
WHERE.2: /WHERE/i
AND.2: /AND/i
OR.2: /OR/i
NOT.2: /NOT/i
IS.2: /IS/i
NULL.2: /NULL/i
RECORD.2: /RECORD/i
CONTAINS.2: /CONTAINS/i
BOOLEAN.2: /TRUE|FALSE/i
NEQ: "!=" | "<>"
LTE: "<="
GTE: ">="
LT: "<"
GT: ">"
IDENTIFIER.0: /[_A-Za-z][_A-Za-z0-9.]*/
STRING: /'(?:[^']|'')*'/
NUMBER: /-?(?:[1-9][0-9]*|0)(?:\.[0-9]+)?/

%import common.WS
%ignore WS
"""


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


class SqlCodeSyntaxAdapter(RuleAdapter):
    """Validate Fluent Bit processor SQL using the project-specific Lark grammar."""

    _parser = None

    @classmethod
    def parser(cls):
        """Build and cache the Lark parser so each validation pass can reuse it."""
        if Lark is None:
            LOGGER.warning("SQL syntax parser unavailable because lark is not installed")
            return None
        if cls._parser is None:
            LOGGER.info("creating cached SQL syntax parser")
            cls._parser = Lark(
                FLUENT_BIT_SQL_GRAMMAR,
                parser=PARSER_TYPE_LALR,
                lexer=LEXER_TYPE_CONTEXTUAL,
                maybe_placeholders=False,
            )
        return cls._parser

    def evaluate(self, context: RuleContext) -> list[dict[str, Any]]:
        """Scan plugin fields and processor fields that declare SQL syntax rules."""
        LOGGER.info("starting SQL code syntax evaluation version=%s", context.version)
        issues: list[dict[str, Any]] = []
        pipeline = context.config.get(KEY_PIPELINE, {})
        if not isinstance(pipeline, dict):
            LOGGER.warning("SQL code syntax evaluation skipped because pipeline is not a dict")
            return issues

        plugin_groups = context.catalog.get(KEY_PLUGINS, {})
        common_processors = context.catalog.get(KEY_COMMON, {}).get(KEY_PROCESSORS, {})

        for section in (KEY_INPUTS, KEY_FILTERS, KEY_OUTPUTS):
            items = pipeline.get(section, [])
            if not isinstance(items, list):
                LOGGER.warning(
                    "SQL code syntax evaluation skipped non-list section section=%s type=%s",
                    section,
                    type(items).__name__,
                )
                continue
            section_defs = plugin_groups.get(section, {})
            for idx, plugin_instance in enumerate(items):
                if not isinstance(plugin_instance, dict):
                    LOGGER.warning(
                        "SQL code syntax evaluation skipped non-dict plugin instance section=%s index=%s type=%s",
                        section,
                        idx,
                        type(plugin_instance).__name__,
                    )
                    continue
                plugin_name = plugin_instance.get(KEY_NAME)
                if not isinstance(plugin_name, str) or not plugin_name:
                    LOGGER.warning(
                        "SQL code syntax evaluation skipped unnamed plugin section=%s index=%s",
                        section,
                        idx,
                    )
                    continue
                plugin_def = section_defs.get(plugin_name)
                if isinstance(plugin_def, dict):
                    issues.extend(
                        self._validate_named_code_fields(
                            payload=plugin_instance,
                            field_defs=plugin_def.get(KEY_FIELDS, []),
                            path_prefix=f"{PATH_PREFIX_PIPELINE_CONFIG}.{section}[{idx}]",
                            context_name=plugin_name,
                        )
                    )
                else:
                    LOGGER.debug(
                        "SQL code syntax evaluation found no catalog definition section=%s plugin=%s",
                        section,
                        plugin_name,
                    )
                if section in {KEY_INPUTS, KEY_OUTPUTS}:
                    issues.extend(
                        self._validate_processor_code_fields(
                            plugin_instance=plugin_instance,
                            processors_def=common_processors,
                            path_prefix=f"{PATH_PREFIX_PIPELINE_CONFIG}.{section}[{idx}]",
                        )
                    )
        LOGGER.info(
            "completed SQL code syntax evaluation version=%s issue_count=%s",
            context.version,
            len(issues),
        )
        return issues

    def _validate_named_code_fields(
        self,
        *,
        payload: dict[str, Any],
        field_defs: list[dict[str, Any]],
        path_prefix: str,
        context_name: str,
    ) -> list[dict[str, Any]]:
        """Validate SQL-bearing fields on a single plugin or processor payload."""
        issues: list[dict[str, Any]] = []
        for field in field_defs:
            if not isinstance(field, dict):
                LOGGER.warning("SQL code syntax skipped non-dict field definition path_prefix=%s", path_prefix)
                continue
            if not self._targets_sql(field=field, context_name=context_name):
                continue
            field_name = str(field.get(KEY_NAME, ""))
            if not field_name:
                LOGGER.warning("SQL code syntax skipped unnamed field definition path_prefix=%s", path_prefix)
                continue
            code_value = payload.get(field_name)
            if isinstance(code_value, str) and code_value.strip():
                issues.extend(self._validate_sql_source(code_value, f"{path_prefix}.{field_name}"))
            elif code_value is not None:
                LOGGER.warning(
                    "SQL code syntax skipped non-string or blank field path=%s.%s type=%s",
                    path_prefix,
                    field_name,
                    type(code_value).__name__,
                )
        return issues

    def _validate_processor_code_fields(
        self,
        *,
        plugin_instance: dict[str, Any],
        processors_def: dict[str, Any],
        path_prefix: str,
    ) -> list[dict[str, Any]]:
        """Walk nested processor blocks and validate any SQL query fields they carry."""
        issues: list[dict[str, Any]] = []
        processors = plugin_instance.get(KEY_PROCESSORS)
        if not isinstance(processors, dict):
            if processors is not None:
                LOGGER.warning(
                    "SQL code syntax skipped processors payload because it is not a dict path=%s type=%s",
                    path_prefix,
                    type(processors).__name__,
                )
            return issues
        signals = processors_def.get(KEY_SIGNALS, {})
        for signal_name, entries in processors.items():
            if not isinstance(entries, list):
                LOGGER.warning(
                    "SQL code syntax skipped processor signal because it is not a list path=%s signal=%s type=%s",
                    path_prefix,
                    signal_name,
                    type(entries).__name__,
                )
                continue
            signal_def = signals.get(signal_name, {})
            signal_processors = signal_def.get(KEY_PROCESSORS, {})
            for idx, processor_instance in enumerate(entries):
                if not isinstance(processor_instance, dict):
                    LOGGER.warning(
                        "SQL code syntax skipped non-dict processor instance path=%s signal=%s index=%s type=%s",
                        path_prefix,
                        signal_name,
                        idx,
                        type(processor_instance).__name__,
                    )
                    continue
                processor_name = processor_instance.get(KEY_NAME)
                if not isinstance(processor_name, str) or not processor_name:
                    LOGGER.warning(
                        "SQL code syntax skipped unnamed processor path=%s signal=%s index=%s",
                        path_prefix,
                        signal_name,
                        idx,
                    )
                    continue
                processor_def = signal_processors.get(processor_name)
                if not isinstance(processor_def, dict):
                    LOGGER.debug(
                        "SQL code syntax found no processor definition path=%s signal=%s processor=%s",
                        path_prefix,
                        signal_name,
                        processor_name,
                    )
                    continue
                issues.extend(
                    self._validate_named_code_fields(
                        payload=processor_instance,
                        field_defs=processor_def.get(KEY_FIELDS, []),
                        path_prefix=f"{path_prefix}.{KEY_PROCESSORS}.{signal_name}[{idx}]",
                        context_name=processor_name,
                    )
                )
        return issues

    def _validate_sql_source(self, source: str, path: str) -> list[dict[str, Any]]:
        """Parse Fluent Bit SQL and translate grammar failures into rule issues."""
        parser = self.parser()
        if parser is None:
            LOGGER.warning("SQL validation parser unavailable path=%s", path)
            return [
                _issue(
                    "sql_parser_unavailable",
                    path,
                    "SQL validation is unavailable because the 'lark' dependency is not installed.",
                )
            ]

        try:
            tree = parser.parse(source)
            wildcard_count = self._count_wildcards(tree)
            select_items = self._count_select_items(tree)
            if wildcard_count > 0 and select_items > 1:
                LOGGER.warning(
                    "SQL validation rejected wildcard and explicit field mix path=%s wildcard_count=%s select_items=%s",
                    path,
                    wildcard_count,
                    select_items,
                )
                return [
                    _issue(
                        "sql_syntax_error",
                        path,
                        "SQL syntax error: wildcard selection '*' cannot be combined with additional selected fields.",
                    )
                ]
        except UnexpectedInput as exc:
            # Mitigates raw parser traces by translating token failures into user-facing diagnostics.
            expected = ", ".join(sorted(exc.expected)) if getattr(exc, "expected", None) else "valid SQL tokens"
            message = (
                f"SQL syntax error at line {getattr(exc, 'line', '?')}, "
                f"column {getattr(exc, 'column', '?')}: unexpected input; expected {expected}."
            )
            LOGGER.warning("SQL syntax validation failed path=%s message=%s", path, message)
            return [_issue("sql_syntax_error", path, message)]
        except Exception as exc:
            # Mitigates unexpected parser/runtime errors and keeps API output normalized.
            LOGGER.exception("unexpected SQL syntax validation failure path=%s", path)
            return [_issue("sql_syntax_error", path, f"SQL syntax error: {str(exc).strip() or 'invalid SQL query.'}")]
        LOGGER.debug("SQL syntax validation succeeded path=%s", path)
        return []

    @staticmethod
    def _is_sql_rule(validation_rule: Any) -> bool:
        """Return true only for validation rules that explicitly target SQL syntax."""
        return (
            isinstance(validation_rule, dict)
            and str(validation_rule.get(KEY_KIND, "")).lower() == VALIDATION_KIND_CODE_SYNTAX
            and str(validation_rule.get(KEY_LANGUAGE, "")).lower() == LANGUAGE_SQL
        )

    @classmethod
    def _targets_sql(cls, *, field: dict[str, Any], context_name: str) -> bool:
        """Route fields to SQL validation when explicitly or contextually SQL code."""
        validation_rule = field.get(KEY_VALIDATION_RULE)
        if cls._is_sql_rule(validation_rule):
            return True
        if str(field.get(KEY_DATA_TYPE, "")).lower() != DATA_TYPE_CODE:
            return False
        return str(context_name or "").strip().lower() == LANGUAGE_SQL

    @staticmethod
    def _count_wildcards(tree: Any) -> int:
        """Count wildcard selections so we can enforce Fluent Bit SQL quirks."""
        if Tree is None or not isinstance(tree, Tree):
            return 0
        return sum(1 for sub in tree.iter_subtrees_topdown() if sub.data == "wildcard_item")

    @staticmethod
    def _count_select_items(tree: Any) -> int:
        """Count selected items to detect invalid `*` plus explicit field mixes."""
        if Tree is None or not isinstance(tree, Tree):
            return 0
        return sum(1 for sub in tree.iter_subtrees_topdown() if sub.data in {"wildcard_item", "identifier_item"})


CUSTOM_ADAPTERS: dict[str, type[RuleAdapter]] = {
    "custom.sql_code_syntax": SqlCodeSyntaxAdapter,
}
