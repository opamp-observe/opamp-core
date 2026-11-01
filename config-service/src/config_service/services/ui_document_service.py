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

KEY_CONFIG_TYPE = "config_type"
KEY_VERSION = "version"
KEY_HEADER_COMMENTS = "header_comments"
KEY_BODY = "body"
KEY_INCLUDE_PATH = "include_path"
KEY_YAML = "yaml"
KEY_TEXT = "text"
KEY_PATH = "path"
KEY_TYPE = "type"
KEY_SERVICE = "service"
KEY_ENV = "env"
KEY_PIPELINE = "pipeline"
KEY_PARSERS = "parsers"
KEY_INPUTS = "inputs"
KEY_FILTERS = "filters"
KEY_OUTPUTS = "outputs"
KEY_NAME = "name"
KEY_CONTAINER = "container"
KEY_NESTED = "nested"
KEY_SOURCE = "source"
KEY_FILTER = "filter"
KEY_MATCH = "match"
KEY_UNKNOWN = "unknown"
KEY_AT_TYPE = "@type"

PATH_ROOT = "$"
PATH_SERVICE = "$.service"
PATH_ENV = "$.env"
PATH_PIPELINE_PREFIX = "$.pipeline"
PATH_PARSERS_PREFIX = "$.parsers"
PATH_SERVICE_PREFIX = "$.service"
PATH_ENV_PREFIX = "$.env"
FILE_EXTENSION_YAML_RE = r"\.ya?ml$"
FILE_EXTENSION_CONF_RE = r"\.conf$"

SECTION_MAP = {
    KEY_SOURCE: KEY_INPUTS,
    KEY_FILTER: KEY_FILTERS,
    KEY_MATCH: KEY_OUTPUTS,
}
CONTAINER_SECTION_NAMES = ("label", "worker")
PIPELINE_SECTION_NAMES = (KEY_INPUTS, KEY_FILTERS, KEY_OUTPUTS)


class UiDocumentService:
    """Backend-owned document preparation/render composition helpers for the UI."""

    _CONFIG_HEADER_RE = re.compile(r"^config-service:\s*(config_type|version)\s*=\s*(.+?)\s*$")
    _COMMENT_RE = re.compile(r"^(//|#)\s?(.*)$")

    @staticmethod
    def prepend_config_header(text: str, config_type: str, version: str, comment_prefix: str = "#") -> str:
        """Prepend the standard config-service metadata header to rendered text."""
        prefix = comment_prefix or "#"
        header_block = "\n".join(
            [
                f"{prefix} config-service: config_type={str(config_type or '')}",
                f"{prefix} config-service: version={str(version or '')}",
            ]
        )
        return f"{header_block}\n{str(text or '')}"

    def parse_config_header(self, text: str) -> dict[str, str]:
        """Parse config-service metadata header comments from a text document."""
        meta = {
            KEY_CONFIG_TYPE: "",
            KEY_VERSION: "",
            KEY_HEADER_COMMENTS: "",
            KEY_BODY: str(text or ""),
        }
        lines = meta[KEY_BODY].replace("\r\n", "\n").split("\n")
        body_start = 0
        header_comment_lines: list[str] = []
        saw_config_service_header = False

        for index, line in enumerate(lines):
            trimmed = str(line or "").strip()
            if not trimmed:
                body_start = index + 1
                if saw_config_service_header or header_comment_lines:
                    header_comment_lines.append("")
                continue

            comment_match = self._COMMENT_RE.match(str(line or ""))
            if not comment_match:
                break

            content = str(comment_match.group(2) or "").strip()
            config_header_match = self._CONFIG_HEADER_RE.match(content)
            if config_header_match:
                saw_config_service_header = True
                key_name = config_header_match.group(1)
                value = config_header_match.group(2).strip()
                if key_name == KEY_CONFIG_TYPE:
                    meta[KEY_CONFIG_TYPE] = value
                else:
                    meta[KEY_VERSION] = value
                body_start = index + 1
                continue

            header_comment_lines.append(str(comment_match.group(2) or "").rstrip())
            body_start = index + 1

        while header_comment_lines and header_comment_lines[0].strip() == "":
            header_comment_lines.pop(0)
        while header_comment_lines and header_comment_lines[-1].strip() == "":
            header_comment_lines.pop()

        meta[KEY_HEADER_COMMENTS] = "\n".join(header_comment_lines)
        meta[KEY_BODY] = "\n".join(lines[body_start:])
        return meta

    @staticmethod
    def normalize_header_comment_lines(text: str) -> list[str]:
        """Normalize line endings for UI header comment editing."""
        normalized_text = (
            str(text or "")
            .replace("\r\n", "\n")
            .replace("\\r\\n", "\n")
            .replace("\\n", "\n")
        )
        lines = normalized_text.split("\n")
        while lines and lines[0].strip() == "":
            lines.pop(0)
        while lines and lines[-1].strip() == "":
            lines.pop()
        return lines

    def prepend_header_comments(self, text: str, header_comments: str, comment_prefix: str = "#") -> str:
        """Prepend free-form header comments to a rendered configuration."""
        lines = self.normalize_header_comment_lines(header_comments or "")
        if not lines:
            return str(text or "")
        prefix = comment_prefix or "#"
        header_block = "\n".join(prefix if line.strip() == "" else f"{prefix} {line}" for line in lines)
        return f"{header_block}\n{str(text or '')}"

    def compose_render_output(
        self,
        *,
        main_rendered: str,
        include_loaded_files: bool,
        included_files: list[dict[str, Any]] | None,
        header_comments: str,
        include_config_header: bool = False,
        config_type: str = "",
        version: str = "",
        comment_prefix: str = "#",
    ) -> str:
        """Compose final UI output including config metadata and included-file blocks."""
        rendered_output = str(main_rendered or "")
        if include_loaded_files:
            include_items = included_files if isinstance(included_files, list) else []
            if include_items:
                sections = [rendered_output]
                for item in include_items:
                    include_path = str((item or {}).get(KEY_INCLUDE_PATH) or KEY_UNKNOWN)
                    include_text = str((item or {}).get(KEY_YAML) or (item or {}).get(KEY_TEXT) or "")
                    sections.append("\n# Included file: " + include_path + "\n" + include_text)
                rendered_output = "\n".join(sections)
        if include_config_header:
            rendered_output = self.prepend_config_header(
                rendered_output,
                config_type=config_type,
                version=version,
                comment_prefix=comment_prefix,
            )
        rendered_output = self.prepend_header_comments(
            rendered_output,
            header_comments,
            comment_prefix=comment_prefix,
        )
        return rendered_output

    def build_source_line_map(self, text: str, config_type: str, file_name: str) -> dict[str, int]:
        """Build a best-effort source-path to line-number lookup for editor UX."""
        if not text:
            return {}
        config_type_text = str(config_type or "").strip().lower()
        file_name_text = str(file_name or "")
        if config_type_text == "fluentbit" or re.search(FILE_EXTENSION_YAML_RE, file_name_text, re.IGNORECASE):
            return self._build_fluentbit_yaml_line_map(text)
        if config_type_text == "fluentd" or re.search(FILE_EXTENSION_CONF_RE, file_name_text, re.IGNORECASE):
            return self._build_fluentd_line_map(text)
        return {}

    def _build_fluentbit_yaml_line_map(self, text: str) -> dict[str, int]:
        """Map Fluent Bit YAML object paths to source line numbers."""
        source_line_map: dict[str, int] = {}
        lines = str(text or "").replace("\r\n", "\n").split("\n")
        root_section = ""
        pipeline_section = ""
        indices = {KEY_INPUTS: -1, KEY_FILTERS: -1, KEY_OUTPUTS: -1}
        current_plugin_index = -1

        for index, raw_line in enumerate(lines):
            line_number = index + 1
            trimmed = raw_line.strip()
            if not trimmed or trimmed.startswith("#"):
                continue
            indent = len(raw_line) - len(raw_line.lstrip())

            if indent == 0:
                root_section = ""
                pipeline_section = ""
                current_plugin_index = -1
                root_match = re.match(r"^([A-Za-z0-9_.-]+):(?:\s|$)", trimmed)
                if root_match:
                    root_section = root_match.group(1)
                    source_line_map[f"$.{root_section}"] = line_number
                continue

            if root_section == KEY_SERVICE:
                service_match = re.match(r"^([A-Za-z0-9_.-]+):(?:\s|$)", trimmed)
                if service_match:
                    source_line_map[f"{PATH_SERVICE_PREFIX}.{service_match.group(1)}"] = line_number
                continue

            if root_section == KEY_ENV:
                env_match = re.match(r"^([A-Za-z0-9_.-]+):(?:\s|$)", trimmed)
                if env_match:
                    source_line_map[f"{PATH_ENV_PREFIX}.{env_match.group(1)}"] = line_number
                continue

            if root_section == KEY_PARSERS:
                if indent >= 2 and re.match(r"^-\s*", trimmed):
                    current_plugin_index += 1
                    parser_base_path = f"{PATH_PARSERS_PREFIX}[{current_plugin_index}]"
                    source_line_map[parser_base_path] = line_number
                    inline_parser = re.sub(r"^-\s*", "", trimmed)
                    inline_parser_match = re.match(r"^([A-Za-z0-9_.-]+):(?:\s|$)", inline_parser)
                    if inline_parser_match:
                        source_line_map[f"{parser_base_path}.{inline_parser_match.group(1)}"] = line_number
                    continue

                if current_plugin_index >= 0:
                    parser_field_match = re.match(r"^([A-Za-z0-9_.-]+):(?:\s|$)", trimmed)
                    if parser_field_match:
                        source_line_map[f"{PATH_PARSERS_PREFIX}[{current_plugin_index}].{parser_field_match.group(1)}"] = line_number
                continue

            if root_section != KEY_PIPELINE:
                continue

            if indent == 2:
                section_match = re.match(r"^(inputs|filters|outputs):(?:\s|$)", trimmed)
                if section_match:
                    pipeline_section = section_match.group(1)
                    current_plugin_index = -1
                    indices[pipeline_section] = -1
                    source_line_map[f"{PATH_PIPELINE_PREFIX}.{pipeline_section}"] = line_number
                else:
                    pipeline_section = ""
                continue

            if not pipeline_section:
                continue

            if indent >= 4 and re.match(r"^-\s*", trimmed):
                indices[pipeline_section] += 1
                current_plugin_index = indices[pipeline_section]
                base_path = f"{PATH_PIPELINE_PREFIX}.{pipeline_section}[{current_plugin_index}]"
                source_line_map[base_path] = line_number
                inline = re.sub(r"^-\s*", "", trimmed)
                inline_match = re.match(r"^([A-Za-z0-9_.-]+):(?:\s|$)", inline)
                if inline_match:
                    source_line_map[f"{base_path}.{inline_match.group(1)}"] = line_number
                continue

            if current_plugin_index >= 0:
                field_match = re.match(r"^([A-Za-z0-9_.-]+):(?:\s|$)", trimmed)
                if field_match:
                    source_line_map[f"{PATH_PIPELINE_PREFIX}.{pipeline_section}[{current_plugin_index}].{field_match.group(1)}"] = line_number

        return source_line_map

    def _build_fluentd_line_map(self, text: str) -> dict[str, int]:
        """Map Fluentd directive paths to source line numbers."""
        source_line_map: dict[str, int] = {}
        lines = str(text or "").replace("\r\n", "\n").split("\n")
        stack: list[dict[str, str]] = []
        indices = {KEY_INPUTS: -1, KEY_FILTERS: -1, KEY_OUTPUTS: -1}

        for index, raw_line in enumerate(lines):
            line_number = index + 1
            trimmed = raw_line.strip()
            if not trimmed or trimmed.startswith("#"):
                continue

            end_match = re.match(r"^</([@A-Za-z_][\w@-]*)>$", trimmed)
            if end_match:
                if stack:
                    stack.pop()
                continue

            if re.match(r"^<system>$", trimmed):
                stack = [{KEY_TYPE: KEY_SERVICE, KEY_PATH: PATH_SERVICE}]
                source_line_map[PATH_SERVICE] = line_number
                continue

            source_match = re.match(r"^<(source|filter|match)(?:\s+.*)?>$", trimmed)
            if source_match:
                section_name = SECTION_MAP[source_match.group(1)]
                indices[section_name] += 1
                path = f"{PATH_PIPELINE_PREFIX}.{section_name}[{indices[section_name]}]"
                stack = [{KEY_TYPE: source_match.group(1), KEY_PATH: path}]
                source_line_map[path] = line_number
                continue

            if re.match(r"^<(label|worker)(?:\s+.*)?>$", trimmed):
                stack = [{KEY_TYPE: KEY_CONTAINER, KEY_PATH: ""}]
                continue

            if trimmed.startswith("<"):
                stack.append({KEY_TYPE: KEY_NESTED, KEY_PATH: ""})
                continue

            if not stack:
                continue

            current = stack[-1]
            current_path = current.get(KEY_PATH, "")
            if not current_path:
                continue

            parts = re.split(r"\s+", trimmed, maxsplit=1)
            key_name = parts[0] if parts else ""
            if not key_name:
                continue
            if key_name == KEY_AT_TYPE:
                source_line_map[f"{current_path}.{KEY_NAME}"] = line_number
                continue
            source_line_map[f"{current_path}.{key_name}"] = line_number

        return source_line_map
