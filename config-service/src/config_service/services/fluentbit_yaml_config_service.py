#!/usr/bin/env python3
# Copyright 2026 mp3monster.org
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

"""Parse Fluent Bit YAML while preserving its string-oriented scalar values."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import yaml

KEY_ENV = "env"
KEY_SERVICE = "service"
KEY_PIPELINE = "pipeline"
KEY_PARSERS = "parsers"
KEY_UPSTREAM_SERVERS = "upstream_servers"
KEY_LABELS = "labels"
KEY_WORKERS = "workers"
KEY_INCLUDES = "includes"
KEY_INPUTS = "inputs"
KEY_FILTERS = "filters"
KEY_OUTPUTS = "outputs"
KEY_NAME = "name"
KEY_ROUTE = "route"
KEY_ROUTES = "routes"
KEY_NODES = "nodes"
KEY_HOST = "host"
KEY_PORT = "port"

CODE_INVALID_SECTION = "fluentbit_yaml_invalid_section"
CODE_IGNORED_SECTION = "fluentbit_yaml_ignored_section"
CODE_INVALID_PLUGIN = "fluentbit_yaml_invalid_plugin"
CODE_MISSING_PLUGIN_NAME = "missing_plugin_name"

PATH_ENV = "$.env"
PATH_SERVICE = "$.service"
PATH_PIPELINE = "$.pipeline"
PATH_PARSERS = "$.parsers"
PATH_UPSTREAM_SERVERS = "$.upstream_servers"
PATH_INCLUDES = "$.includes"

_PIPELINE_SECTIONS = (KEY_INPUTS, KEY_FILTERS, KEY_OUTPUTS)


class _FluentBitYamlLoader(yaml.SafeLoader):
    """YAML loader that keeps Fluent Bit string-ish scalars as strings.

    Fluent Bit YAML examples commonly use unquoted values like:
    - name: null
    - daemon: on
    - http_server: off

    In generic YAML these can be coerced into null/booleans, but for
    Fluent Bit they are often intended as literal strings.
    """


_FluentBitYamlLoader.yaml_implicit_resolvers = deepcopy(
    yaml.SafeLoader.yaml_implicit_resolvers
)
# Keep Fluent Bit's string-oriented scalar rules local to this loader subclass.
for _first_char, _resolver_mappings in list(_FluentBitYamlLoader.yaml_implicit_resolvers.items()):
    _FluentBitYamlLoader.yaml_implicit_resolvers[_first_char] = [
        (tag, regexp)
        for tag, regexp in _resolver_mappings
        if tag not in {"tag:yaml.org,2002:bool", "tag:yaml.org,2002:null"}
    ]


def _issue(
    order: int,
    code: str,
    path: str,
    message: str,
    *,
    severity: str = "error",
    source: str = "parser",
) -> dict[str, Any]:
    """Build a normalized parser issue object used by API/UI consumers."""
    return {
        "order": order,
        "code": code,
        "path": path,
        "message": message,
        "severity": severity,
        "source": source,
    }


class FluentBitYamlConfigService:
    """Parse Fluent Bit YAML config into the internal document model."""

    def parse(self, text: str) -> dict[str, Any]:
        """Parse Fluent Bit YAML and normalize known sections into config model.

        High-complexity flow notes:
        - The root loop dispatches each top-level section (`env`, `service`,
          `pipeline`, `parsers`, `upstream_servers`, `includes`) to section-specific parsing.
        - Each branch validates the incoming shape first, then either stores a
          normalized payload or emits an issue and continues parsing other sections.
        """
        if not str(text or "").strip():
            raise ValueError("The Fluent Bit YAML file is empty.")

        try:
            loaded = yaml.load(text, Loader=_FluentBitYamlLoader)  # noqa: S506
        except yaml.YAMLError as exc:
            # Convert low-level YAML parser errors into a stable domain error so
            # callers can consistently report malformed config text.
            raise ValueError(f"Fluent Bit YAML could not be parsed: {exc}") from exc

        if loaded is None:
            raise ValueError("The Fluent Bit YAML file is empty.")
        if not isinstance(loaded, dict):
            raise ValueError("The Fluent Bit YAML root must be a mapping/object.")

        config: dict[str, Any] = {
            KEY_ENV: {},
            KEY_SERVICE: {},
            KEY_PARSERS: [],
            KEY_UPSTREAM_SERVERS: [],
            KEY_PIPELINE: {KEY_INPUTS: [], KEY_FILTERS: [], KEY_OUTPUTS: []},
            KEY_LABELS: [],
            KEY_WORKERS: [],
            KEY_INCLUDES: [],
        }
        errors: list[dict[str, Any]] = []
        order = 1

        for key, value in loaded.items():
            if key == KEY_ENV:
                if isinstance(value, dict):
                    env_map: dict[str, Any] = {}
                    for env_key, env_value in value.items():
                        env_name = str(env_key).strip()
                        if not env_name:
                            continue
                        env_map[env_name] = deepcopy(env_value)
                    config[KEY_ENV] = env_map
                else:
                    errors.append(
                        _issue(
                            order,
                            CODE_INVALID_SECTION,
                            PATH_ENV,
                            "Ignored env section because it is not a mapping/object.",
                        )
                    )
                    order += 1
                continue

            if key == KEY_SERVICE:
                if isinstance(value, dict):
                    config[KEY_SERVICE] = deepcopy(value)
                else:
                    errors.append(
                        _issue(
                            order,
                            CODE_INVALID_SECTION,
                            PATH_SERVICE,
                            "Ignored service section because it is not a mapping/object.",
                        )
                    )
                    order += 1
                continue

            if key == KEY_PIPELINE:
                pipeline_payload, pipeline_errors = self._parse_pipeline(value, order)
                config[KEY_PIPELINE] = pipeline_payload
                errors.extend(pipeline_errors)
                order += len(pipeline_errors)
                continue

            if key == KEY_PARSERS:
                parsers_payload, parser_errors = self._parse_parsers(value, order)
                config[KEY_PARSERS] = parsers_payload
                errors.extend(parser_errors)
                order += len(parser_errors)
                continue

            if key == KEY_UPSTREAM_SERVERS:
                upstream_payload, upstream_errors = self._parse_upstream_servers(value, order)
                config[KEY_UPSTREAM_SERVERS] = upstream_payload
                errors.extend(upstream_errors)
                order += len(upstream_errors)
                continue

            if key == KEY_INCLUDES:
                if isinstance(value, list):
                    config[KEY_INCLUDES] = [str(item).strip() for item in value if str(item).strip()]
                else:
                    errors.append(
                        _issue(
                            order,
                            CODE_INVALID_SECTION,
                            PATH_INCLUDES,
                            "Ignored includes section because it is not a list.",
                        )
                    )
                    order += 1
                continue

            errors.append(
                _issue(
                    order,
                    CODE_IGNORED_SECTION,
                    f"$.{key}",
                    f"Ignored unsupported Fluent Bit YAML section '{key}'.",
                )
            )
            order += 1

        return {
            "config": config,
            "errors": errors,
            "ok": len(errors) == 0,
        }

    def _parse_pipeline(self, payload: Any, start_order: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Parse/validate the `pipeline` map and keep only valid plugin entries.

        High-complexity flow notes:
        - The first branch rejects non-object `pipeline` values immediately.
        - For each pipeline section, we validate section support and item shape.
        - Nested conditions enforce plugin identity (`name`) and alias normalization
          (`routes` -> `route`) before appending accepted plugin objects.
        """
        pipeline = {KEY_INPUTS: [], KEY_FILTERS: [], KEY_OUTPUTS: []}
        errors: list[dict[str, Any]] = []
        order = start_order

        if not isinstance(payload, dict):
            errors.append(
                _issue(
                    order,
                    CODE_INVALID_SECTION,
                    PATH_PIPELINE,
                    "Ignored pipeline section because it is not a mapping/object.",
                )
            )
            return pipeline, errors

        for section_name, section_value in payload.items():
            if section_name not in _PIPELINE_SECTIONS:
                errors.append(
                    _issue(
                        order,
                        CODE_IGNORED_SECTION,
                        f"{PATH_PIPELINE}.{section_name}",
                        f"Ignored unsupported pipeline section '{section_name}'.",
                    )
                )
                order += 1
                continue

            if not isinstance(section_value, list):
                errors.append(
                    _issue(
                        order,
                        CODE_INVALID_SECTION,
                        f"{PATH_PIPELINE}.{section_name}",
                        f"Ignored pipeline section '{section_name}' because it is not a list.",
                    )
                )
                order += 1
                continue

            for index, item in enumerate(section_value):
                item_path = f"{PATH_PIPELINE}.{section_name}[{index}]"
                if not isinstance(item, dict):
                    errors.append(
                        _issue(
                            order,
                            CODE_INVALID_PLUGIN,
                            item_path,
                            f"Ignored {section_name[:-1]} entry at index {index} because it is not an object.",
                        )
                    )
                    order += 1
                    continue
                if not str(item.get(KEY_NAME) or "").strip():
                    errors.append(
                        _issue(
                            order,
                            CODE_MISSING_PLUGIN_NAME,
                            item_path,
                            f"Ignored {section_name[:-1]} entry at index {index} because it does not define a plugin name.",
                        )
                    )
                    order += 1
                    continue
                plugin_item = deepcopy(item)
                if KEY_ROUTES in plugin_item and KEY_ROUTE not in plugin_item:
                    plugin_item[KEY_ROUTE] = plugin_item.pop(KEY_ROUTES)
                pipeline[section_name].append(plugin_item)

        return pipeline, errors

    def _parse_parsers(self, payload: Any, start_order: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Parse/validate the `parsers` list while preserving parser payloads."""
        parsers: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        order = start_order
        if not isinstance(payload, list):
            errors.append(
                _issue(
                    order,
                    CODE_INVALID_SECTION,
                    PATH_PARSERS,
                    "Ignored parsers section because it is not a list.",
                )
            )
            return parsers, errors
        for index, item in enumerate(payload):
            item_path = f"{PATH_PARSERS}[{index}]"
            if not isinstance(item, dict):
                errors.append(
                    _issue(
                        order,
                        CODE_INVALID_PLUGIN,
                        item_path,
                        f"Ignored parser entry at index {index} because it is not an object.",
                    )
                )
                order += 1
                continue
            parsers.append(deepcopy(item))
        return parsers, errors

    def _parse_upstream_servers(
        self,
        payload: Any,
        start_order: int,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Parse/validate root-level `upstream_servers` groups and node lists."""
        upstream_groups: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        order = start_order

        if not isinstance(payload, list):
            errors.append(
                _issue(
                    order,
                    CODE_INVALID_SECTION,
                    PATH_UPSTREAM_SERVERS,
                    "Ignored upstream_servers section because it is not a list.",
                )
            )
            return upstream_groups, errors

        for group_index, group_item in enumerate(payload):
            group_path = f"{PATH_UPSTREAM_SERVERS}[{group_index}]"
            if not isinstance(group_item, dict):
                errors.append(
                    _issue(
                        order,
                        CODE_INVALID_PLUGIN,
                        group_path,
                        f"Ignored upstream group at index {group_index} because it is not an object.",
                    )
                )
                order += 1
                continue

            group_name = str(group_item.get(KEY_NAME) or "").strip()
            nodes = group_item.get(KEY_NODES)
            if not group_name:
                errors.append(
                    _issue(
                        order,
                        CODE_MISSING_PLUGIN_NAME,
                        group_path,
                        f"Ignored upstream group at index {group_index} because it does not define a group name.",
                    )
                )
                order += 1
                continue
            if not isinstance(nodes, list):
                errors.append(
                    _issue(
                        order,
                        CODE_INVALID_SECTION,
                        f"{group_path}.nodes",
                        f"Ignored upstream group '{group_name}' because `nodes` is not a list.",
                    )
                )
                order += 1
                continue

            parsed_nodes: list[dict[str, Any]] = []
            for node_index, node_item in enumerate(nodes):
                node_path = f"{group_path}.nodes[{node_index}]"
                if not isinstance(node_item, dict):
                    errors.append(
                        _issue(
                            order,
                            CODE_INVALID_PLUGIN,
                            node_path,
                            f"Ignored node at index {node_index} because it is not an object.",
                        )
                    )
                    order += 1
                    continue
                node_name = str(node_item.get(KEY_NAME) or "").strip()
                node_host = str(node_item.get(KEY_HOST) or "").strip()
                node_port = node_item.get(KEY_PORT)
                if not node_name or not node_host or node_port is None:
                    errors.append(
                        _issue(
                            order,
                            CODE_INVALID_SECTION,
                            node_path,
                            "Ignored upstream node because required fields `name`, `host`, and `port` are not all present.",
                        )
                    )
                    order += 1
                    continue
                parsed_nodes.append(deepcopy(node_item))

            if parsed_nodes:
                upstream_groups.append(
                    {
                        KEY_NAME: group_name,
                        "nodes": parsed_nodes,
                    }
                )
            else:
                errors.append(
                    _issue(
                        order,
                        CODE_INVALID_SECTION,
                        f"{group_path}.nodes",
                        f"Ignored upstream group '{group_name}' because it has no valid nodes.",
                    )
                )
                order += 1

        return upstream_groups, errors
