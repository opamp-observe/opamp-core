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

from __future__ import annotations

import re
from typing import Any

from config_service.services.rule_engine_service import RuleEngineService

KEY_CONFIG = "config"
KEY_PIPELINE = "pipeline"
KEY_PARSERS = "parsers"
KEY_UPSTREAM_SERVERS = "upstream_servers"
KEY_PLUGINS = "plugins"
KEY_COMMON = "common"
KEY_INPUTS = "inputs"
KEY_FILTERS = "filters"
KEY_OUTPUTS = "outputs"
KEY_NAME = "name"
KEY_NODES = "nodes"
KEY_HOST = "host"
KEY_PORT = "port"
KEY_TLS = "tls"
KEY_TLS_VERIFY = "tls_verify"
KEY_SHARED_KEY = "shared_key"
KEY_FIELDS = "fields"
KEY_REQUIRED = "required"
KEY_CHILDREN = "children"
KEY_PROCESSORS = "processors"
KEY_ROUTE = "route"
KEY_META = "_meta"
KEY_LABELS = "labels"
KEY_WORKERS = "workers"
KEY_SIGNALS = "signals"
KEY_CONDITION = "condition"
KEY_DIRECTIVE_ARGUMENT = "directive_argument"
KEY_ENGINE = "engine"
KEY_BUILTIN_PARSER_NAMES = "builtin_parser_names"
KEY_PARSER_FORMATS = "parser_formats"
KEY_FORMAT = "format"
KEY_NESTED_SECTIONS = "nested_sections"
KEY_MATCH = "match"
KEY_MATCH_REGEX = "match_regex"
KEY_REFERENCES_PARSER = "references_parser"
KEY_ALLOW_FILTERS_AS_PROCESSORS = "allow_filters_as_processors"
KEY_SUPPORTS_CONDITION = "supports_condition"
KEY_TOP_LEVEL_FIELDS = "top_level_fields"
KEY_IMPLEMENTED = "implemented"
KEY_PER_RECORD_ROUTING = "per_record_routing"
KEY_TO = "to"
KEY_DEFAULT = "default"
KEY_OP = "op"
KEY_RULES = "rules"
KEY_CONTEXT = "context"
KEY_FIELD = "field"
KEY_ALIAS = "alias"
KEY_SECTION = "section"
KEY_ALLOWED_CHILDREN = "allowed_children"
KEY_CARDINALITY = "cardinality"
KEY_MAXIMUM = "maximum"
KEY_REUSES_OUTPUT_PLUGINS = "reuses_output_plugins"
KEY_VARIANTS = "variants"
KEY_PLUGIN_BACKED = "plugin_backed"
DIRECTIVE_ARGUMENT_ALIAS = "directive_arg"
ENGINE_FLUENTBIT = "fluentbit"
ENGINE_FLUENTD = "fluentd"
ISSUE_KEY_ORDER = "order"
ISSUE_KEY_CODE = "code"
ISSUE_KEY_PATH = "path"
ISSUE_KEY_MESSAGE = "message"
ISSUE_KEY_SEVERITY = "severity"
ISSUE_KEY_SOURCE = "source"


class ValidationService:
    """Validate config payloads against catalog metadata and semantic constraints.

    This service coordinates two layers of validation:
    1. Semantic/schema-shape checks implemented in this class.
    2. Rule-engine checks delegated to `RuleEngineService`.
    """

    def __init__(self, rule_engine_service: RuleEngineService) -> None:
        """Store the rule engine dependency used for profile-based validation."""
        self.rule_engine_service = rule_engine_service
        self._numeric_env_var_pattern = re.compile(r"^\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)\}$")

    def validate(
        self,
        *,
        version: str,
        payload: dict[str, Any],
        catalog: dict[str, Any],
        profile: str | None,
        parser_definition: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run semantic + rule-engine validation and return normalized issues.

        The method first validates payload shape, then dispatches to Fluent Bit or
        Fluentd semantic validation based on catalog engine metadata, and finally
        executes ruleset adapters selected by profile.
        """
        config = payload.get(KEY_CONFIG)
        if not isinstance(config, dict):
            return {
                "ok": False,
                "errors": self._normalize_errors(
                    [
                        {
                            ISSUE_KEY_CODE: "invalid_payload",
                            ISSUE_KEY_PATH: "$.config",
                            ISSUE_KEY_MESSAGE: "Payload must include object 'config'.",
                            ISSUE_KEY_SEVERITY: "error",
                            ISSUE_KEY_SOURCE: "schema",
                        }
                    ]
                ),
            }

        engine = str(catalog.get(KEY_ENGINE) or ENGINE_FLUENTBIT).lower()
        if engine == ENGINE_FLUENTD:
            semantic_issues = self._validate_fluentd_config(config, catalog)
        else:
            semantic_issues = self._validate_fluentbit_pipeline(
                config,
                catalog,
                parser_definition=parser_definition,
            )
        rule_issues = self.rule_engine_service.evaluate(
            version=version,
            config=config,
            catalog=catalog,
            profile=profile,
        )
        errors = self._normalize_errors(semantic_issues + rule_issues)
        has_error = any(str(item.get(ISSUE_KEY_SEVERITY) or "error").lower() == "error" for item in errors)
        return {"ok": not has_error, "errors": errors}

    def _normalize_errors(self, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize issue shape and add stable ordering for UI/API consumers."""
        normalized: list[dict[str, Any]] = []
        for index, issue in enumerate(issues, start=1):
            item = dict(issue)
            item[ISSUE_KEY_ORDER] = index
            item[ISSUE_KEY_CODE] = str(item.get(ISSUE_KEY_CODE) or "unknown_issue")
            item[ISSUE_KEY_MESSAGE] = str(item.get(ISSUE_KEY_MESSAGE) or "Validation issue")
            item[ISSUE_KEY_PATH] = str(item.get(ISSUE_KEY_PATH) or "$")
            item[ISSUE_KEY_SEVERITY] = str(item.get(ISSUE_KEY_SEVERITY) or "error")
            item[ISSUE_KEY_SOURCE] = str(item.get(ISSUE_KEY_SOURCE) or "validation")
            normalized.append(item)
        return normalized

    def _validate_fluentbit_pipeline(
        self,
        config: dict[str, Any],
        catalog: dict[str, Any],
        *,
        parser_definition: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Validate Fluent Bit pipeline sections and parser definitions."""
        issues: list[dict[str, Any]] = []
        parser_issues, custom_parser_names, builtin_parser_names = self._validate_fluentbit_parsers(
            config.get(KEY_PARSERS),
            parser_definition,
        )
        issues.extend(parser_issues)
        issues.extend(
            self._validate_fluentbit_upstream_servers(
                config.get(KEY_UPSTREAM_SERVERS),
            )
        )
        pipeline = config.get(KEY_PIPELINE)
        if not isinstance(pipeline, dict):
            issues.append(
                {
                    ISSUE_KEY_CODE: "missing_pipeline",
                    ISSUE_KEY_PATH: "$.config.pipeline",
                    ISSUE_KEY_MESSAGE: "config.pipeline must be an object.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "schema",
                }
            )
            return issues

        plugins = catalog.get(KEY_PLUGINS, {})
        processors_def = catalog.get(KEY_COMMON, {}).get(KEY_PROCESSORS, {})
        route_def = catalog.get(KEY_COMMON, {}).get(KEY_ROUTE, {})
        for section in (KEY_INPUTS, KEY_FILTERS, KEY_OUTPUTS):
            issues.extend(
                self._validate_plugin_list(
                    section_items=pipeline.get(section),
                    path_prefix=f"$.config.pipeline.{section}",
                    section=section,
                    plugins=plugins,
                    nested_sections={},
                    allow_children=False,
                    fluentbit_processors=processors_def,
                    fluentbit_filter_plugins=plugins.get(KEY_FILTERS, {}),
                    known_parser_names=custom_parser_names | builtin_parser_names,
                    fluentbit_route=route_def,
                    pipeline=pipeline,
                )
            )
        return issues

    def _is_numeric_env_var(self, value: Any) -> bool:
        """Return true when value is a Fluent Bit env placeholder like `${MY_VAR}`."""
        return isinstance(value, str) and bool(self._numeric_env_var_pattern.fullmatch(value))

    def _validate_fluentbit_upstream_servers(self, upstream_payload: Any) -> list[dict[str, Any]]:
        """Validate Fluent Bit root-level `upstream_servers` groups and nodes.

        High-complexity flow notes:
        - First branch validates top-level container shape (`list` expected).
        - Group-level branches enforce object shape, required keys, and known fields.
        - Node-level branches validate required fields and key type constraints.
        """
        issues: list[dict[str, Any]] = []
        if upstream_payload is None:
            return issues
        if not isinstance(upstream_payload, list):
            return [
                {
                    ISSUE_KEY_CODE: "invalid_section_type",
                    ISSUE_KEY_PATH: "$.config.upstream_servers",
                    ISSUE_KEY_MESSAGE: "upstream_servers must be an array.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "schema",
                }
            ]

        seen_group_names: set[str] = set()
        for group_index, group_item in enumerate(upstream_payload):
            group_path = f"$.config.upstream_servers[{group_index}]"
            if not isinstance(group_item, dict):
                issues.append(
                    {
                        ISSUE_KEY_CODE: "invalid_plugin_item",
                        ISSUE_KEY_PATH: group_path,
                        ISSUE_KEY_MESSAGE: "Upstream server group must be an object.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "schema",
                    }
                )
                continue

            group_name = group_item.get(KEY_NAME)
            if not isinstance(group_name, str) or not group_name.strip():
                issues.append(
                    {
                        ISSUE_KEY_CODE: "missing_required_field",
                        ISSUE_KEY_PATH: f"{group_path}.name",
                        ISSUE_KEY_MESSAGE: "Upstream server group requires a non-empty name.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
            else:
                normalized_group_name = group_name.strip()
                if normalized_group_name in seen_group_names:
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "duplicate_upstream_group_name",
                            ISSUE_KEY_PATH: f"{group_path}.name",
                            ISSUE_KEY_MESSAGE: f"Upstream server group '{normalized_group_name}' is defined more than once.",
                            ISSUE_KEY_SEVERITY: "warning",
                            ISSUE_KEY_SOURCE: "semantic",
                        }
                    )
                else:
                    seen_group_names.add(normalized_group_name)

            nodes = group_item.get(KEY_NODES)
            if not isinstance(nodes, list):
                issues.append(
                    {
                        ISSUE_KEY_CODE: "invalid_section_type",
                        ISSUE_KEY_PATH: f"{group_path}.nodes",
                        ISSUE_KEY_MESSAGE: "Upstream server group nodes must be an array.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "schema",
                    }
                )
                nodes = []

            for key in group_item:
                if key in {KEY_NAME, KEY_NODES, KEY_META}:
                    continue
                issues.append(
                    {
                        ISSUE_KEY_CODE: "unknown_field",
                        ISSUE_KEY_PATH: f"{group_path}.{key}",
                        ISSUE_KEY_MESSAGE: f"Unknown field '{key}' for upstream server group.",
                        ISSUE_KEY_SEVERITY: "warning",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )

            seen_node_names: set[str] = set()
            for node_index, node_item in enumerate(nodes):
                node_path = f"{group_path}.nodes[{node_index}]"
                if not isinstance(node_item, dict):
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "invalid_plugin_item",
                            ISSUE_KEY_PATH: node_path,
                            ISSUE_KEY_MESSAGE: "Upstream server node must be an object.",
                            ISSUE_KEY_SEVERITY: "error",
                            ISSUE_KEY_SOURCE: "schema",
                        }
                    )
                    continue

                node_name = node_item.get(KEY_NAME)
                if not isinstance(node_name, str) or not node_name.strip():
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "missing_required_field",
                            ISSUE_KEY_PATH: f"{node_path}.name",
                            ISSUE_KEY_MESSAGE: "Upstream server node requires a non-empty name.",
                            ISSUE_KEY_SEVERITY: "error",
                            ISSUE_KEY_SOURCE: "semantic",
                        }
                    )
                else:
                    normalized_node_name = node_name.strip()
                    if normalized_node_name in seen_node_names:
                        issues.append(
                            {
                                ISSUE_KEY_CODE: "duplicate_upstream_node_name",
                                ISSUE_KEY_PATH: f"{node_path}.name",
                                ISSUE_KEY_MESSAGE: f"Upstream server node '{normalized_node_name}' is defined more than once in this group.",
                                ISSUE_KEY_SEVERITY: "warning",
                                ISSUE_KEY_SOURCE: "semantic",
                            }
                        )
                    else:
                        seen_node_names.add(normalized_node_name)

                host_value = node_item.get(KEY_HOST)
                if not isinstance(host_value, str) or not host_value.strip():
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "missing_required_field",
                            ISSUE_KEY_PATH: f"{node_path}.host",
                            ISSUE_KEY_MESSAGE: "Upstream server node requires a non-empty host.",
                            ISSUE_KEY_SEVERITY: "error",
                            ISSUE_KEY_SOURCE: "semantic",
                        }
                    )

                port_value = node_item.get(KEY_PORT)
                if KEY_PORT not in node_item:
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "missing_required_field",
                            ISSUE_KEY_PATH: f"{node_path}.port",
                            ISSUE_KEY_MESSAGE: "Upstream server node requires a port.",
                            ISSUE_KEY_SEVERITY: "error",
                            ISSUE_KEY_SOURCE: "semantic",
                        }
                    )
                elif isinstance(port_value, bool) or (
                    not isinstance(port_value, int) and not self._is_numeric_env_var(port_value)
                ):
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "invalid_type",
                            ISSUE_KEY_PATH: f"{node_path}.port",
                            ISSUE_KEY_MESSAGE: "Upstream server node port must be an integer or an environment variable placeholder.",
                            ISSUE_KEY_SEVERITY: "error",
                            ISSUE_KEY_SOURCE: "schema",
                        }
                    )

                tls_value = node_item.get(KEY_TLS)
                if tls_value is not None and not isinstance(tls_value, bool):
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "invalid_type",
                            ISSUE_KEY_PATH: f"{node_path}.tls",
                            ISSUE_KEY_MESSAGE: "Upstream server node tls must be true or false.",
                            ISSUE_KEY_SEVERITY: "error",
                            ISSUE_KEY_SOURCE: "schema",
                        }
                    )

                tls_verify_value = node_item.get(KEY_TLS_VERIFY)
                if tls_verify_value is not None and not isinstance(tls_verify_value, bool):
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "invalid_type",
                            ISSUE_KEY_PATH: f"{node_path}.tls_verify",
                            ISSUE_KEY_MESSAGE: "Upstream server node tls_verify must be true or false.",
                            ISSUE_KEY_SEVERITY: "error",
                            ISSUE_KEY_SOURCE: "schema",
                        }
                    )

                shared_key_value = node_item.get(KEY_SHARED_KEY)
                if shared_key_value is not None and not isinstance(shared_key_value, str):
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "invalid_type",
                            ISSUE_KEY_PATH: f"{node_path}.shared_key",
                            ISSUE_KEY_MESSAGE: "Upstream server node shared_key must be a string.",
                            ISSUE_KEY_SEVERITY: "error",
                            ISSUE_KEY_SOURCE: "schema",
                        }
                    )

                for key in node_item:
                    if key in {KEY_NAME, KEY_HOST, KEY_PORT, KEY_TLS, KEY_TLS_VERIFY, KEY_SHARED_KEY, KEY_META}:
                        continue
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "unknown_field",
                            ISSUE_KEY_PATH: f"{node_path}.{key}",
                            ISSUE_KEY_MESSAGE: f"Unknown field '{key}' for upstream server node.",
                            ISSUE_KEY_SEVERITY: "warning",
                            ISSUE_KEY_SOURCE: "semantic",
                        }
                    )
        return issues

    def _validate_fluentbit_parsers(
        self,
        parsers_payload: Any,
        parser_definition: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], set[str], set[str]]:
        """Validate Fluent Bit `parsers` blocks and collect known parser names.

        High-complexity flow notes:
        - First branch validates container shape (`list` expected).
        - Per-parser branches enforce identity (`name`), format support, required
          format fields, and unknown key detection.
        """
        issues: list[dict[str, Any]] = []
        custom_parser_names: set[str] = set()
        builtin_parser_names = (
            set(parser_definition.get(KEY_BUILTIN_PARSER_NAMES, []))
            if parser_definition
            else set()
        )
        if parsers_payload is None:
            return issues, custom_parser_names, builtin_parser_names
        if not isinstance(parsers_payload, list):
            return [
                {
                    ISSUE_KEY_CODE: "invalid_section_type",
                    ISSUE_KEY_PATH: "$.config.parsers",
                    ISSUE_KEY_MESSAGE: "parsers must be an array.",
                    ISSUE_KEY_SEVERITY: "warning",
                    ISSUE_KEY_SOURCE: "schema",
                }
            ], custom_parser_names, builtin_parser_names

        parser_formats = (
            parser_definition.get(KEY_PARSER_FORMATS, {})
            if isinstance(parser_definition, dict)
            else {}
        )
        # Iterate each parser definition and validate shape before semantic checks.
        for idx, parser_instance in enumerate(parsers_payload):
            path = f"$.config.parsers[{idx}]"
            if not isinstance(parser_instance, dict):
                issues.append(
                    {
                        ISSUE_KEY_CODE: "invalid_plugin_item",
                        ISSUE_KEY_PATH: path,
                        ISSUE_KEY_MESSAGE: "Parser definition must be an object.",
                        ISSUE_KEY_SEVERITY: "warning",
                        ISSUE_KEY_SOURCE: "schema",
                    }
                )
                continue

            parser_name = parser_instance.get(KEY_NAME)
            # Enforce parser uniqueness so parser references resolve deterministically.
            if not isinstance(parser_name, str) or not parser_name:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "missing_required_field",
                        ISSUE_KEY_PATH: f"{path}.name",
                        ISSUE_KEY_MESSAGE: "Parser definition requires a non-empty name.",
                        ISSUE_KEY_SEVERITY: "warning",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
            elif parser_name in custom_parser_names:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "duplicate_parser_name",
                        ISSUE_KEY_PATH: f"{path}.name",
                        ISSUE_KEY_MESSAGE: f"Parser name '{parser_name}' is defined more than once.",
                        ISSUE_KEY_SEVERITY: "warning",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
            else:
                custom_parser_names.add(parser_name)

            parser_format = parser_instance.get(KEY_FORMAT)
            if not isinstance(parser_format, str) or not parser_format:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "missing_required_field",
                        ISSUE_KEY_PATH: f"{path}.format",
                        ISSUE_KEY_MESSAGE: "Parser definition requires a non-empty format.",
                        ISSUE_KEY_SEVERITY: "warning",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
                continue
            format_def = parser_formats.get(parser_format)
            if not isinstance(format_def, dict):
                issues.append(
                    {
                        ISSUE_KEY_CODE: "unknown_parser_format",
                        ISSUE_KEY_PATH: f"{path}.format",
                        ISSUE_KEY_MESSAGE: f"Unknown parser format '{parser_format}'.",
                        ISSUE_KEY_SEVERITY: "warning",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
                continue
            fields = {field[KEY_NAME]: field for field in format_def.get(KEY_FIELDS, [])}
            # Validate required parser-format-specific keys.
            for required in [
                name
                for name, field in fields.items()
                if field.get(KEY_REQUIRED) is True
            ]:
                value = parser_instance.get(required)
                if value is None or (isinstance(value, str) and not value):
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "missing_required_field",
                            ISSUE_KEY_PATH: f"{path}.{required}",
                            ISSUE_KEY_MESSAGE: f"Required field '{required}' is missing.",
                            ISSUE_KEY_SEVERITY: "warning",
                            ISSUE_KEY_SOURCE: "semantic",
                        }
                    )
            # Warn on unknown keys to surface typos without blocking hard.
            for key in parser_instance:
                if key in {KEY_NAME, "format", KEY_META}:
                    continue
                if key not in fields:
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "unknown_field",
                            ISSUE_KEY_PATH: f"{path}.{key}",
                            ISSUE_KEY_MESSAGE: f"Unknown field '{key}' for parser format '{parser_format}'.",
                            ISSUE_KEY_SEVERITY: "warning",
                            ISSUE_KEY_SOURCE: "semantic",
                        }
                    )
        return issues, custom_parser_names, builtin_parser_names

    def _validate_fluentd_config(self, config: dict[str, Any], catalog: dict[str, Any]) -> list[dict[str, Any]]:
        """Validate Fluentd pipeline plus optional labels/workers trees.

        High-complexity flow notes:
        - Validates top-level pipeline sections first.
        - Then validates optional `labels` and `workers` containers, each of which
          recursively reuse plugin-list checks.
        """
        issues: list[dict[str, Any]] = []
        pipeline = config.get(KEY_PIPELINE)
        if not isinstance(pipeline, dict):
            return [
                {
                    ISSUE_KEY_CODE: "missing_pipeline",
                    ISSUE_KEY_PATH: "$.config.pipeline",
                    ISSUE_KEY_MESSAGE: "config.pipeline must be an object.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "schema",
                }
            ]

        plugin_groups = catalog.get(KEY_PLUGINS, {})
        nested_sections = catalog.get(KEY_NESTED_SECTIONS, {})
        for section in (KEY_INPUTS, KEY_FILTERS, KEY_OUTPUTS):
            issues.extend(
                self._validate_plugin_list(
                    section_items=pipeline.get(section),
                    path_prefix=f"$.config.pipeline.{section}",
                    section=section,
                    plugins=plugin_groups,
                    nested_sections=nested_sections,
                    allow_children=True,
                    fluentbit_processors=None,
                    fluentbit_filter_plugins=None,
                    known_parser_names=set(),
                    fluentbit_route=None,
                    pipeline=pipeline,
                )
            )

        labels = config.get(KEY_LABELS, [])
        if labels is not None and not isinstance(labels, list):
            issues.append(
                {
                    ISSUE_KEY_CODE: "invalid_section_type",
                    ISSUE_KEY_PATH: "$.config.labels",
                    ISSUE_KEY_MESSAGE: "labels must be an array.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "schema",
                }
            )
        elif isinstance(labels, list):
            for idx, label in enumerate(labels):
                issues.extend(
                    self._validate_label_like(
                        label,
                        path_prefix=f"$.config.labels[{idx}]",
                        plugin_groups=plugin_groups,
                        nested_sections=nested_sections,
                    )
                )

        workers = config.get(KEY_WORKERS, [])
        if workers is not None and not isinstance(workers, list):
            issues.append(
                {
                    ISSUE_KEY_CODE: "invalid_section_type",
                    ISSUE_KEY_PATH: "$.config.workers",
                    ISSUE_KEY_MESSAGE: "workers must be an array.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "schema",
                }
            )
        elif isinstance(workers, list):
            for idx, worker in enumerate(workers):
                issues.extend(
                    self._validate_worker(
                        worker,
                        path_prefix=f"$.config.workers[{idx}]",
                        plugin_groups=plugin_groups,
                        nested_sections=nested_sections,
                    )
                )
        return issues

    def _validate_label_like(
        self,
        payload: Any,
        *,
        path_prefix: str,
        plugin_groups: dict[str, Any],
        nested_sections: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Validate a Fluentd label object and its nested pipeline sections."""
        issues: list[dict[str, Any]] = []
        if not isinstance(payload, dict):
            return [
                {
                    ISSUE_KEY_CODE: "invalid_plugin_item",
                    ISSUE_KEY_PATH: path_prefix,
                    ISSUE_KEY_MESSAGE: "Label definition must be an object.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "schema",
                }
            ]
        if not isinstance(payload.get(KEY_NAME), str) or not payload.get(KEY_NAME):
            issues.append(
                {
                    ISSUE_KEY_CODE: "missing_required_field",
                    ISSUE_KEY_PATH: f"{path_prefix}.name",
                    ISSUE_KEY_MESSAGE: "Label definition requires a non-empty name.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "semantic",
                }
            )
        pipeline = payload.get(KEY_PIPELINE, {})
        if not isinstance(pipeline, dict):
            issues.append(
                {
                    ISSUE_KEY_CODE: "missing_pipeline",
                    ISSUE_KEY_PATH: f"{path_prefix}.pipeline",
                    ISSUE_KEY_MESSAGE: "Label definition requires a pipeline object.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "schema",
                }
            )
            return issues
        for section in (KEY_INPUTS, KEY_FILTERS, KEY_OUTPUTS):
            issues.extend(
                self._validate_plugin_list(
                    section_items=pipeline.get(section),
                    path_prefix=f"{path_prefix}.pipeline.{section}",
                    section=section,
                    plugins=plugin_groups,
                    nested_sections=nested_sections,
                    allow_children=True,
                    fluentbit_processors=None,
                    fluentbit_filter_plugins=None,
                    known_parser_names=set(),
                    fluentbit_route=None,
                    pipeline=pipeline,
                )
            )
        return issues

    def _validate_worker(
        self,
        payload: Any,
        *,
        path_prefix: str,
        plugin_groups: dict[str, Any],
        nested_sections: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Validate Fluentd worker block and any nested worker-specific labels."""
        issues = self._validate_label_like(
            payload,
            path_prefix=path_prefix,
            plugin_groups=plugin_groups,
            nested_sections=nested_sections,
        )
        if isinstance(payload, dict):
            labels = payload.get(KEY_LABELS, [])
            if labels is not None and not isinstance(labels, list):
                issues.append(
                    {
                        ISSUE_KEY_CODE: "invalid_section_type",
                        ISSUE_KEY_PATH: f"{path_prefix}.labels",
                        ISSUE_KEY_MESSAGE: "Worker labels must be an array.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "schema",
                    }
                )
            elif isinstance(labels, list):
                for idx, label in enumerate(labels):
                    issues.extend(
                        self._validate_label_like(
                            label,
                            path_prefix=f"{path_prefix}.labels[{idx}]",
                            plugin_groups=plugin_groups,
                            nested_sections=nested_sections,
                        )
                    )
        return issues

    def _validate_plugin_list(
        self,
        *,
        section_items: Any,
        path_prefix: str,
        section: str,
        plugins: dict[str, Any],
        nested_sections: dict[str, Any],
        allow_children: bool,
        fluentbit_processors: dict[str, Any] | None,
        fluentbit_filter_plugins: dict[str, Any] | None,
        known_parser_names: set[str],
        fluentbit_route: dict[str, Any] | None,
        pipeline: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Validate a section list (`inputs`/`filters`/`outputs`) of plugin items."""
        issues: list[dict[str, Any]] = []
        if section_items is None:
            return issues
        if not isinstance(section_items, list):
            return [
                {
                    ISSUE_KEY_CODE: "invalid_section_type",
                    ISSUE_KEY_PATH: path_prefix,
                    ISSUE_KEY_MESSAGE: f"{section} must be an array.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "schema",
                }
            ]
        # Loop each plugin instance so we can report path-specific issues.
        for idx, plugin_instance in enumerate(section_items):
            path = f"{path_prefix}[{idx}]"
            if not isinstance(plugin_instance, dict):
                issues.append(
                    {
                        ISSUE_KEY_CODE: "invalid_plugin_item",
                        ISSUE_KEY_PATH: path,
                        ISSUE_KEY_MESSAGE: "Plugin instance must be an object.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "schema",
                    }
                )
                continue
            plugin_name = plugin_instance.get(KEY_NAME)
            if not isinstance(plugin_name, str) or not plugin_name:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "missing_plugin_name",
                        ISSUE_KEY_PATH: f"{path}.name",
                        ISSUE_KEY_MESSAGE: "Plugin instance requires a non-empty 'name'.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "schema",
                    }
                )
                continue
            plugin_def = plugins.get(section, {}).get(plugin_name)
            if plugin_def is None:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "unknown_plugin",
                        ISSUE_KEY_PATH: f"{path}.name",
                        ISSUE_KEY_MESSAGE: f"Unknown plugin '{plugin_name}' in section '{section}'.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
                continue
            issues.extend(
                self._validate_plugin_instance(
                    path,
                    plugin_instance,
                    plugin_def,
                    nested_sections,
                    allow_children,
                    fluentbit_processors=fluentbit_processors,
                    fluentbit_filter_plugins=fluentbit_filter_plugins,
                    section=section,
                    known_parser_names=known_parser_names,
                    fluentbit_route=fluentbit_route,
                    pipeline=pipeline,
                )
            )
        return issues

    def _validate_plugin_instance(
        self,
        path: str,
        plugin_instance: dict[str, Any],
        plugin_def: dict[str, Any],
        nested_sections: dict[str, Any],
        allow_children: bool,
        fluentbit_processors: dict[str, Any] | None,
        fluentbit_filter_plugins: dict[str, Any] | None,
        section: str,
        known_parser_names: set[str],
        fluentbit_route: dict[str, Any] | None,
        pipeline: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Validate one plugin payload against catalog fields and nested semantics.

        High-complexity flow notes:
        - Required-field checks run before unknown-field checks so users see missing
          essentials even when extra keys are present.
        - Optional feature blocks (`children`, `processors`, `route`) are delegated
          to specialized validators to keep issue paths accurate.
        """
        issues: list[dict[str, Any]] = []
        fields = {field[KEY_NAME]: field for field in plugin_def.get(KEY_FIELDS, [])}
        directive_arg = plugin_def.get(KEY_DIRECTIVE_ARGUMENT)
        directive_arg_keys = self._directive_argument_keys(directive_arg)
        # Directive arguments are pseudo-fields (e.g. Fluentd <match ARG>), so they
        # are validated separately from regular plugin fields.
        if isinstance(directive_arg, dict) and directive_arg.get(KEY_REQUIRED) is True:
            if not any(key in plugin_instance for key in directive_arg_keys):
                issues.append(
                    {
                        ISSUE_KEY_CODE: "missing_required_field",
                        ISSUE_KEY_PATH: f"{path}.{directive_arg_keys[0]}",
                        ISSUE_KEY_MESSAGE: "Required directive argument is missing.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
        for required in [name for name, field in fields.items() if field.get(KEY_REQUIRED) is True]:
            if required not in plugin_instance:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "missing_required_field",
                        ISSUE_KEY_PATH: f"{path}.{required}",
                        ISSUE_KEY_MESSAGE: f"Required field '{required}' is missing.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
        for key in plugin_instance:
            if key in {KEY_NAME, KEY_CHILDREN, KEY_PROCESSORS, KEY_ROUTE, KEY_META}:
                continue
            if key in directive_arg_keys:
                continue
            if key not in fields:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "unknown_field",
                        ISSUE_KEY_PATH: f"{path}.{key}",
                        ISSUE_KEY_MESSAGE: f"Unknown field '{key}' for plugin '{plugin_instance.get(KEY_NAME)}'.",
                        ISSUE_KEY_SEVERITY: "warning",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
        issues.extend(
            self._validate_match_selector_presence(
                path=path,
                plugin_instance=plugin_instance,
                fields=fields,
            )
        )
        issues.extend(
            self._validate_parser_references(
                path=path,
                plugin_instance=plugin_instance,
                fields=fields,
                known_parser_names=known_parser_names,
            )
        )
        # Delegate nested children/processors/routes so each subsystem can enforce
        # its own schema and semantic constraints.
        if allow_children:
            issues.extend(self._validate_children(path, plugin_instance, plugin_def, nested_sections))
        if fluentbit_processors and section in {KEY_INPUTS, KEY_OUTPUTS}:
            issues.extend(
                self._validate_fluentbit_processors(
                    path=path,
                    plugin_instance=plugin_instance,
                    processors_def=fluentbit_processors,
                    filter_plugins=fluentbit_filter_plugins or {},
                )
            )
        if fluentbit_route and section == KEY_INPUTS:
            issues.extend(
                self._validate_fluentbit_route(
                    path=path,
                    plugin_instance=plugin_instance,
                    route_def=fluentbit_route,
                    outputs=pipeline.get(KEY_OUTPUTS) if isinstance(pipeline, dict) else [],
                )
            )
        return issues

    @staticmethod
    def _directive_argument_keys(directive_arg: dict[str, Any] | Any) -> list[str]:
        """Return accepted directive-argument keys, including legacy alias support."""
        if not isinstance(directive_arg, dict):
            return [DIRECTIVE_ARGUMENT_ALIAS]
        configured_name = str(directive_arg.get(KEY_NAME) or "").strip()
        if not configured_name or configured_name == "directive_arg":
            return [DIRECTIVE_ARGUMENT_ALIAS]
        return [configured_name, "directive_arg"]

    def _validate_match_selector_presence(
        self,
        *,
        path: str,
        plugin_instance: dict[str, Any],
        fields: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Require at least one routing selector when both selector fields exist."""
        if "match" not in fields or "match_regex" not in fields:
            return []

        match_value = plugin_instance.get(KEY_MATCH)
        regex_value = plugin_instance.get(KEY_MATCH_REGEX)

        has_match = isinstance(match_value, str) and bool(match_value.strip())
        has_match_regex = isinstance(regex_value, str) and bool(regex_value.strip())
        if has_match or has_match_regex:
            return []

        return [
            {
                ISSUE_KEY_CODE: "missing_match_selector",
                ISSUE_KEY_PATH: path,
                ISSUE_KEY_MESSAGE: "At least one of 'match' or 'match_regex' must be provided.",
                ISSUE_KEY_SEVERITY: "error",
                ISSUE_KEY_SOURCE: "semantic",
            }
        ]

    def _validate_parser_references(
        self,
        *,
        path: str,
        plugin_instance: dict[str, Any],
        fields: dict[str, dict[str, Any]],
        known_parser_names: set[str],
    ) -> list[dict[str, Any]]:
        """Validate parser-reference fields against known custom and built-in names."""
        issues: list[dict[str, Any]] = []
        if not known_parser_names:
            return issues
        for field_name, field_def in fields.items():
            if field_def.get(KEY_REFERENCES_PARSER) is not True:
                continue
            value = plugin_instance.get(field_name)
            if not isinstance(value, str) or not value:
                continue
            if value not in known_parser_names:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "unknown_parser_reference",
                        ISSUE_KEY_PATH: f"{path}.{field_name}",
                        ISSUE_KEY_MESSAGE: f"Parser '{value}' was not found in the defined parsers or known built-in parser names.",
                        ISSUE_KEY_SEVERITY: "warning",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
        return issues

    def _validate_fluentbit_processors(
        self,
        *,
        path: str,
        plugin_instance: dict[str, Any],
        processors_def: dict[str, Any],
        filter_plugins: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Validate Fluent Bit processor graph for one plugin instance.

        High-complexity flow notes:
        - Validate processors container shape first.
        - Per signal: verify signal is known and list-shaped.
        - Per processor: verify existence, required fields, unknown fields, and
          optional condition semantics.
        """
        issues: list[dict[str, Any]] = []
        processors = plugin_instance.get(KEY_PROCESSORS)
        if processors is None:
            return issues
        if not isinstance(processors, dict):
            return [
                {
                    ISSUE_KEY_CODE: "invalid_section_type",
                    ISSUE_KEY_PATH: f"{path}.processors",
                    ISSUE_KEY_MESSAGE: "processors must be an object.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "schema",
                }
            ]
        signals = processors_def.get(KEY_SIGNALS, {})
        # Process signal by signal to preserve precise JSON paths in errors.
        for signal_name, items in processors.items():
            signal_path = f"{path}.{KEY_PROCESSORS}.{signal_name}"
            signal_def = signals.get(signal_name)
            if signal_def is None:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "unknown_nested_section",
                        ISSUE_KEY_PATH: signal_path,
                        ISSUE_KEY_MESSAGE: f"Unknown processors signal '{signal_name}'.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
                continue
            if not isinstance(items, list):
                issues.append(
                    {
                        ISSUE_KEY_CODE: "invalid_section_type",
                        ISSUE_KEY_PATH: signal_path,
                        ISSUE_KEY_MESSAGE: "Signal processors must be an array.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "schema",
                    }
                )
                continue
            available = dict(signal_def.get(KEY_PROCESSORS, {}))
            if signal_name == "logs" and signal_def.get(KEY_ALLOW_FILTERS_AS_PROCESSORS):
                available.update(filter_plugins)
            # Validate each processor instance within this signal stream.
            for idx, processor in enumerate(items):
                proc_path = f"{signal_path}[{idx}]"
                if not isinstance(processor, dict):
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "invalid_plugin_item",
                            ISSUE_KEY_PATH: proc_path,
                            ISSUE_KEY_MESSAGE: "Processor entry must be an object.",
                            ISSUE_KEY_SEVERITY: "error",
                            ISSUE_KEY_SOURCE: "schema",
                        }
                    )
                    continue
                proc_name = processor.get(KEY_NAME)
                if not isinstance(proc_name, str) or not proc_name:
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "missing_plugin_name",
                            ISSUE_KEY_PATH: f"{proc_path}.name",
                            ISSUE_KEY_MESSAGE: "Processor requires a non-empty 'name'.",
                            ISSUE_KEY_SEVERITY: "error",
                            ISSUE_KEY_SOURCE: "schema",
                        }
                    )
                    continue
                proc_def = available.get(proc_name)
                if proc_def is None:
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "unknown_plugin",
                            ISSUE_KEY_PATH: f"{proc_path}.name",
                            ISSUE_KEY_MESSAGE: f"Unknown processor '{proc_name}' for signal '{signal_name}'.",
                            ISSUE_KEY_SEVERITY: "error",
                            ISSUE_KEY_SOURCE: "semantic",
                        }
                    )
                    continue
                fields = {field[KEY_NAME]: field for field in proc_def.get(KEY_FIELDS, [])}
                for required in [name for name, field in fields.items() if field.get(KEY_REQUIRED) is True]:
                    if required not in processor:
                        issues.append(
                            {
                                ISSUE_KEY_CODE: "missing_required_field",
                                ISSUE_KEY_PATH: f"{proc_path}.{required}",
                                ISSUE_KEY_MESSAGE: f"Required field '{required}' is missing.",
                                ISSUE_KEY_SEVERITY: "error",
                                ISSUE_KEY_SOURCE: "semantic",
                            }
                        )
                for key in processor:
                    if key in {KEY_NAME, KEY_CONDITION, KEY_META}:
                        continue
                    if key not in fields:
                        issues.append(
                            {
                                ISSUE_KEY_CODE: "unknown_field",
                                ISSUE_KEY_PATH: f"{proc_path}.{key}",
                                ISSUE_KEY_MESSAGE: f"Unknown field '{key}' for processor '{proc_name}'.",
                                ISSUE_KEY_SEVERITY: "warning",
                                ISSUE_KEY_SOURCE: "semantic",
                            }
                        )
                if KEY_CONDITION in processor:
                    if not proc_def.get(KEY_SUPPORTS_CONDITION):
                        issues.append(
                            {
                                ISSUE_KEY_CODE: "unknown_field",
                                ISSUE_KEY_PATH: f"{proc_path}.{KEY_CONDITION}",
                                ISSUE_KEY_MESSAGE: f"Processor '{proc_name}' does not support conditional processing.",
                                ISSUE_KEY_SEVERITY: "warning",
                                ISSUE_KEY_SOURCE: "semantic",
                            }
                        )
                    elif not isinstance(processor[KEY_CONDITION], dict):
                        issues.append(
                            {
                                ISSUE_KEY_CODE: "invalid_section_type",
                                ISSUE_KEY_PATH: f"{proc_path}.{KEY_CONDITION}",
                                ISSUE_KEY_MESSAGE: "condition must be an object.",
                                ISSUE_KEY_SEVERITY: "error",
                                ISSUE_KEY_SOURCE: "schema",
                            }
                        )
        return issues

    def _validate_fluentbit_route(
        self,
        *,
        path: str,
        plugin_instance: dict[str, Any],
        route_def: dict[str, Any],
        outputs: Any,
    ) -> list[dict[str, Any]]:
        """Validate Fluent Bit route rules attached to an input plugin.

        High-complexity flow notes:
        - Top-level route keys are split into known scalar flags and signal blocks.
        - Each signal block is validated as a list of route items.
        - Cross-check ensures `per_record_routing=true` when conditional routes exist.
        """
        issues: list[dict[str, Any]] = []
        route_payload = plugin_instance.get(KEY_ROUTE)
        if route_payload is None:
            return issues
        if not isinstance(route_payload, dict):
            return [
                {
                    ISSUE_KEY_CODE: "invalid_section_type",
                    ISSUE_KEY_PATH: f"{path}.route",
                    ISSUE_KEY_MESSAGE: "route must be an object.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "schema",
                }
            ]

        # Build allow-lists from catalog metadata to validate unknown keys/signals.
        top_level_fields = {
            field[KEY_NAME]: field
            for field in route_def.get(KEY_TOP_LEVEL_FIELDS, [])
            if isinstance(field, dict) and isinstance(field.get(KEY_NAME), str)
        }
        allowed_signals = {
            str(signal.get(KEY_NAME)): signal
            for signal in route_def.get(KEY_SIGNALS, [])
            if isinstance(signal, dict) and isinstance(signal.get(KEY_NAME), str)
        }
        seen_route_names: set[str] = set()
        available_output_refs = self._route_output_reference_names(outputs)
        has_any_routes = False

        # Evaluate each route key: top-level flags vs signal-specific rule arrays.
        for key, value in route_payload.items():
            if key == KEY_META:
                continue
            if key in top_level_fields:
                if key == "per_record_routing" and not isinstance(value, bool):
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "invalid_route_field_type",
                            ISSUE_KEY_PATH: f"{path}.route.per_record_routing",
                            ISSUE_KEY_MESSAGE: "per_record_routing must be true or false.",
                            ISSUE_KEY_SEVERITY: "error",
                            ISSUE_KEY_SOURCE: "schema",
                        }
                    )
                continue

            signal_meta = allowed_signals.get(key)
            if signal_meta is None:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "unknown_route_signal",
                        ISSUE_KEY_PATH: f"{path}.route.{key}",
                        ISSUE_KEY_MESSAGE: f"Unknown route signal '{key}'.",
                        ISSUE_KEY_SEVERITY: "warning",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
                continue

            if not isinstance(value, list):
                issues.append(
                    {
                        ISSUE_KEY_CODE: "invalid_section_type",
                        ISSUE_KEY_PATH: f"{path}.route.{key}",
                        ISSUE_KEY_MESSAGE: f"Route signal '{key}' must be an array.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "schema",
                    }
                )
                continue

            if value:
                has_any_routes = True
            if signal_meta.get(KEY_IMPLEMENTED) is False:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "route_signal_not_fully_supported",
                        ISSUE_KEY_PATH: f"{path}.route.{key}",
                        ISSUE_KEY_MESSAGE: f"Signal '{key}' is parsed by Fluent Bit but is not fully evaluated yet.",
                        ISSUE_KEY_SEVERITY: "warning",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )

            # Validate route entries one by one so errors retain stable indices.
            for idx, route_item in enumerate(value):
                issues.extend(
                    self._validate_route_item(
                        route_item,
                        path_prefix=f"{path}.route.{key}[{idx}]",
                        seen_route_names=seen_route_names,
                        available_output_refs=available_output_refs,
                    )
                )

        if has_any_routes and route_payload.get(KEY_PER_RECORD_ROUTING) is not True:
            issues.append(
                {
                    ISSUE_KEY_CODE: "route_not_enabled",
                    ISSUE_KEY_PATH: f"{path}.route.per_record_routing",
                    ISSUE_KEY_MESSAGE: "Conditional routing rules are defined but per_record_routing is not enabled.",
                    ISSUE_KEY_SEVERITY: "warning",
                    ISSUE_KEY_SOURCE: "semantic",
                }
            )
        return issues

    def _validate_route_item(
        self,
        route_item: Any,
        *,
        path_prefix: str,
        seen_route_names: set[str],
        available_output_refs: set[str],
    ) -> list[dict[str, Any]]:
        """Validate one route item: identity, condition, and destinations.

        High-complexity flow notes:
        - Validate object shape and unique route name.
        - Validate condition subtree (delegated).
        - Validate destination outputs and optionally cross-check references.
        """
        issues: list[dict[str, Any]] = []
        if not isinstance(route_item, dict):
            return [
                {
                    ISSUE_KEY_CODE: "invalid_plugin_item",
                    ISSUE_KEY_PATH: path_prefix,
                    ISSUE_KEY_MESSAGE: "Route entry must be an object.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "schema",
                }
            ]

        route_name = route_item.get(KEY_NAME)
        if not isinstance(route_name, str) or not route_name:
            issues.append(
                {
                    ISSUE_KEY_CODE: "missing_required_field",
                    ISSUE_KEY_PATH: f"{path_prefix}.name",
                    ISSUE_KEY_MESSAGE: "Route entry requires a non-empty name.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "semantic",
                }
            )
        elif route_name in seen_route_names:
            issues.append(
                {
                    ISSUE_KEY_CODE: "duplicate_route_name",
                    ISSUE_KEY_PATH: f"{path_prefix}.name",
                    ISSUE_KEY_MESSAGE: f"Route name '{route_name}' is defined more than once.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "semantic",
                }
            )
        else:
            seen_route_names.add(route_name)

        condition = route_item.get(KEY_CONDITION)
        if not isinstance(condition, dict):
            issues.append(
                {
                    ISSUE_KEY_CODE: "missing_required_field",
                    ISSUE_KEY_PATH: f"{path_prefix}.{KEY_CONDITION}",
                    ISSUE_KEY_MESSAGE: "Route entry requires a condition object.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "semantic",
                }
            )
        else:
            issues.extend(
                    self._validate_route_condition(
                        condition,
                        path_prefix=f"{path_prefix}.{KEY_CONDITION}",
                    )
                )

        destination = route_item.get(KEY_TO)
        if not isinstance(destination, dict):
            issues.append(
                {
                    ISSUE_KEY_CODE: "missing_required_field",
                    ISSUE_KEY_PATH: f"{path_prefix}.to",
                    ISSUE_KEY_MESSAGE: "Route entry requires a to object.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "semantic",
                }
            )
        else:
            route_outputs = destination.get(KEY_OUTPUTS)
            if not isinstance(route_outputs, list) or not route_outputs:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "missing_required_field",
                        ISSUE_KEY_PATH: f"{path_prefix}.to.{KEY_OUTPUTS}",
                        ISSUE_KEY_MESSAGE: "Route entry requires at least one output destination.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
            else:
                for idx, output_name in enumerate(route_outputs):
                    output_path = f"{path_prefix}.to.{KEY_OUTPUTS}[{idx}]"
                    if not isinstance(output_name, str) or not output_name:
                        issues.append(
                            {
                                ISSUE_KEY_CODE: "invalid_route_output_reference",
                                ISSUE_KEY_PATH: output_path,
                                ISSUE_KEY_MESSAGE: "Route output reference must be a non-empty string.",
                                ISSUE_KEY_SEVERITY: "error",
                                ISSUE_KEY_SOURCE: "schema",
                            }
                        )
                        continue
                    if available_output_refs and output_name not in available_output_refs:
                        issues.append(
                            {
                                ISSUE_KEY_CODE: "unknown_route_output_reference",
                                ISSUE_KEY_PATH: output_path,
                                ISSUE_KEY_MESSAGE: f"Route output '{output_name}' was not found in the configured outputs by name or alias.",
                                ISSUE_KEY_SEVERITY: "warning",
                                ISSUE_KEY_SOURCE: "semantic",
                            }
                        )
        return issues

    def _validate_route_condition(
        self,
        condition: dict[str, Any],
        *,
        path_prefix: str,
    ) -> list[dict[str, Any]]:
        """Validate route condition operator and rule-list semantics.

        High-complexity flow notes:
        - Early-return on `default: true` because no rule list is required.
        - Enforces allowed condition operator and non-empty rules.
        - Iterates each rule validating context, operator, and required operands.
        """
        issues: list[dict[str, Any]] = []
        if condition.get(KEY_DEFAULT) is True:
            return issues

        op = condition.get(KEY_OP)
        if op not in {"and", "or"}:
            issues.append(
                {
                    ISSUE_KEY_CODE: "invalid_route_condition_operator",
                    ISSUE_KEY_PATH: f"{path_prefix}.op",
                    ISSUE_KEY_MESSAGE: "Route condition operator must be 'and' or 'or'.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "semantic",
                }
            )

        rules = condition.get(KEY_RULES)
        if not isinstance(rules, list) or not rules:
            issues.append(
                {
                    ISSUE_KEY_CODE: "missing_required_field",
                    ISSUE_KEY_PATH: f"{path_prefix}.rules",
                    ISSUE_KEY_MESSAGE: "Route condition requires at least one rule unless it is marked as default.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "semantic",
                }
            )
            return issues

        valid_contexts = {
            "body",
            "group_attributes",
            "group_metadata",
            "metadata",
            "otel_resource_attributes",
            "otel_scope_attributes",
            "otel_scope_metadata",
        }
        valid_ops = {
            "eq",
            "gt",
            "gte",
            "in",
            "lt",
            "lte",
            "neq",
            "not_in",
            "not_regex",
            "regex",
        }
        # Validate each rule in-place to preserve detailed index paths.
        for idx, rule in enumerate(rules):
            rule_path = f"{path_prefix}.rules[{idx}]"
            if not isinstance(rule, dict):
                issues.append(
                    {
                        ISSUE_KEY_CODE: "invalid_plugin_item",
                        ISSUE_KEY_PATH: rule_path,
                        ISSUE_KEY_MESSAGE: "Route condition rule must be an object.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "schema",
                    }
                )
                continue
            if KEY_CONTEXT in rule and rule.get(KEY_CONTEXT) not in valid_contexts:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "invalid_route_context",
                        ISSUE_KEY_PATH: f"{rule_path}.context",
                        ISSUE_KEY_MESSAGE: f"Unknown route rule context '{rule.get('context')}'.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
            if not isinstance(rule.get(KEY_FIELD), str) or not rule.get(KEY_FIELD):
                issues.append(
                    {
                        ISSUE_KEY_CODE: "missing_required_field",
                        ISSUE_KEY_PATH: f"{rule_path}.field",
                        ISSUE_KEY_MESSAGE: "Route rule requires a non-empty field.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
            if rule.get(KEY_OP) not in valid_ops:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "invalid_route_rule_operator",
                        ISSUE_KEY_PATH: f"{rule_path}.op",
                        ISSUE_KEY_MESSAGE: f"Unknown route rule operator '{rule.get('op')}'.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
            if "value" not in rule:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "missing_required_field",
                        ISSUE_KEY_PATH: f"{rule_path}.value",
                        ISSUE_KEY_MESSAGE: "Route rule requires a comparison value.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
        return issues

    def _route_output_reference_names(self, outputs: Any) -> set[str]:
        """Compute accepted route output references from configured outputs.

        Supports:
        - direct plugin name (e.g. `null`)
        - indexed duplicate name alias (`null.0`, `null.1`, ...)
        - explicit configured `alias`
        """
        names: set[str] = set()
        if not isinstance(outputs, list):
            return names
        counters: dict[str, int] = {}
        for output in outputs:
            if not isinstance(output, dict):
                continue
            plugin_name = output.get(KEY_NAME)
            if isinstance(plugin_name, str) and plugin_name:
                names.add(plugin_name)
                sequence = counters.get(plugin_name, 0)
                names.add(f"{plugin_name}.{sequence}")
                counters[plugin_name] = sequence + 1
            alias = output.get(KEY_ALIAS)
            if isinstance(alias, str) and alias:
                names.add(alias)
        return names

    def _validate_children(
        self,
        path: str,
        plugin_instance: dict[str, Any],
        plugin_def: dict[str, Any],
        nested_sections: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Validate Fluentd nested child sections for a plugin instance.

        High-complexity flow notes:
        - Validate children container type and section allow-list first.
        - Apply nested cardinality constraints before deep item validation.
        - For plugin-backed sections, validate nested plugin `name` and required
          fields against either variant schema or flat field schema.
        """
        issues: list[dict[str, Any]] = []
        children = plugin_instance.get(KEY_CHILDREN)
        if children is None:
            return issues
        if not isinstance(children, dict):
            return [
                {
                    ISSUE_KEY_CODE: "invalid_section_type",
                    ISSUE_KEY_PATH: f"{path}.children",
                    ISSUE_KEY_MESSAGE: "children must be an object.",
                    ISSUE_KEY_SEVERITY: "error",
                    ISSUE_KEY_SOURCE: "schema",
                }
            ]
        allowed = {
            item[KEY_SECTION]: item
            for item in plugin_def.get(KEY_ALLOWED_CHILDREN, [])
            if isinstance(item, dict) and isinstance(item.get(KEY_SECTION), str)
        }
        # Validate each nested child section against the plugin's allow-list.
        for child_name, child_items in children.items():
            if child_name == "includes":
                continue
            if child_name not in allowed:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "unknown_nested_section",
                        ISSUE_KEY_PATH: f"{path}.children.{child_name}",
                        ISSUE_KEY_MESSAGE: f"Nested section '{child_name}' is not allowed for plugin '{plugin_instance.get(KEY_NAME)}'.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
                continue
            if not isinstance(child_items, list):
                issues.append(
                    {
                        ISSUE_KEY_CODE: "invalid_section_type",
                        ISSUE_KEY_PATH: f"{path}.children.{child_name}",
                        ISSUE_KEY_MESSAGE: f"Nested section '{child_name}' must be an array.",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "schema",
                    }
                )
                continue
            nested_def = nested_sections.get(child_name, {})
            card = allowed[child_name].get(KEY_CARDINALITY, {})
            maximum = card.get(KEY_MAXIMUM)
            if isinstance(maximum, int) and len(child_items) > maximum:
                issues.append(
                    {
                        ISSUE_KEY_CODE: "nested_cardinality_exceeded",
                        ISSUE_KEY_PATH: f"{path}.children.{child_name}",
                        ISSUE_KEY_MESSAGE: f"Nested section '{child_name}' allows at most {maximum} item(s).",
                        ISSUE_KEY_SEVERITY: "error",
                        ISSUE_KEY_SOURCE: "semantic",
                    }
                )
            if nested_def.get(KEY_REUSES_OUTPUT_PLUGINS) is True:
                continue
            fields = {
                field[KEY_NAME]: field
                for field in nested_def.get(KEY_FIELDS, [])
                if isinstance(field, dict)
            }
            variants = nested_def.get(KEY_VARIANTS, {})
            # Deep-validate each child item according to plugin-backed vs flat mode.
            for idx, child_item in enumerate(child_items):
                if not isinstance(child_item, dict):
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "invalid_plugin_item",
                            ISSUE_KEY_PATH: f"{path}.children.{child_name}[{idx}]",
                            ISSUE_KEY_MESSAGE: "Nested section item must be an object.",
                            ISSUE_KEY_SEVERITY: "error",
                            ISSUE_KEY_SOURCE: "schema",
                        }
                    )
                    continue
                if nested_def.get(KEY_PLUGIN_BACKED) is True and variants and KEY_NAME not in child_item:
                    issues.append(
                        {
                            ISSUE_KEY_CODE: "missing_plugin_name",
                            ISSUE_KEY_PATH: f"{path}.children.{child_name}[{idx}].name",
                            ISSUE_KEY_MESSAGE: "Nested plugin section requires a non-empty 'name'.",
                            ISSUE_KEY_SEVERITY: "error",
                            ISSUE_KEY_SOURCE: "semantic",
                        }
                    )
                    continue
                if nested_def.get(KEY_PLUGIN_BACKED) is True and variants:
                    variant = variants.get(child_item.get(KEY_NAME))
                    if variant is None:
                        issues.append(
                            {
                                ISSUE_KEY_CODE: "unknown_plugin",
                                ISSUE_KEY_PATH: f"{path}.children.{child_name}[{idx}].name",
                                ISSUE_KEY_MESSAGE: f"Unknown nested plugin '{child_item.get(KEY_NAME)}' in section '{child_name}'.",
                                ISSUE_KEY_SEVERITY: "error",
                                ISSUE_KEY_SOURCE: "semantic",
                            }
                        )
                        continue
                    required_fields = [f[KEY_NAME] for f in variant.get(KEY_FIELDS, []) if f.get(KEY_REQUIRED) is True]
                else:
                    required_fields = [name for name, field in fields.items() if field.get(KEY_REQUIRED) is True]
                for required in required_fields:
                    if required not in child_item:
                        issues.append(
                            {
                                ISSUE_KEY_CODE: "missing_required_field",
                                ISSUE_KEY_PATH: f"{path}.children.{child_name}[{idx}].{required}",
                                ISSUE_KEY_MESSAGE: f"Required field '{required}' is missing.",
                                ISSUE_KEY_SEVERITY: "error",
                                ISSUE_KEY_SOURCE: "semantic",
                            }
                        )
        return issues
