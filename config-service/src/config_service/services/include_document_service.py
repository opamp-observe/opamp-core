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

from copy import deepcopy
from pathlib import Path
from typing import Any

KEY_CONFIG = "config"
KEY_INCLUDES = "includes"
KEY_INCLUDE_PATH = "include_path"
KEY_RESOLVED_PATH = "resolved_path"
KEY_OK = "ok"
KEY_ERRORS = "errors"
KEY_TEXT = "text"
KEY_YAML = "yaml"
KEY_INCLUDED_DOCUMENTS = "included_documents"
KEY_ORDER = "order"
KEY_CODE = "code"
KEY_PATH = "path"
KEY_MESSAGE = "message"
KEY_SEVERITY = "severity"
KEY_SOURCE = "source"
KEY_META = "_meta"

CONFIG_TYPE_FLUENTBIT = "fluentbit"
CONFIG_TYPE_FLUENTD = "fluentd"
ENCODING_UTF8 = "utf-8"
PATH_INCLUDES = "$.includes"
SEVERITY_WARNING = "warning"
SOURCE_INCLUDE_LOADER = "include-loader"
CODE_INCLUDE_FILE_NOT_FOUND = "include_file_not_found"
CODE_INCLUDE_CYCLE_DETECTED = "include_cycle_detected"
CODE_INCLUDE_FILE_NOT_READABLE = "include_file_not_readable"
CODE_INCLUDE_PARSE_ERROR = "include_parse_error"
GLOB_TOKENS = ("*", "?", "[")


class IncludeDocumentService:
    """Resolve, merge, and render include graphs without mutating source payloads."""

    def __init__(self, *, fluentbit_yaml_config_service: Any, fluentd_config_service: Any) -> None:
        """Store the parser services used for recursively included documents."""
        self._fluentbit_yaml_config_service = fluentbit_yaml_config_service
        self._fluentd_config_service = fluentd_config_service

    def resolve_include_documents(
        self,
        *,
        config_type: str,
        source_path: str,
        config: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Resolve include declarations beneath one source configuration document."""
        root_path = Path(source_path).expanduser()
        base_dir = root_path.parent if root_path.name else root_path
        return self._resolve_include_list(
            config_type=str(config_type or CONFIG_TYPE_FLUENTBIT).lower(),
            base_dir=base_dir,
            include_items=config.get(KEY_INCLUDES),
            seen_stack=[root_path.resolve(strict=False)],
        )

    def merge_for_validation(
        self,
        *,
        config: dict[str, Any],
        included_documents: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        """Merge included documents into the root config for validation-only use."""
        merged = self._empty_like(config)
        for document in included_documents or []:
            child_config = self._merged_config_from_document(document)
            if child_config is not None:
                merged = self._merge_configs(merged, child_config)
        merged = self._merge_configs(merged, deepcopy(config))
        return merged

    def render_included_documents(
        self,
        *,
        config_type: str,
        included_documents: list[dict[str, Any]] | None,
        include_comments: bool,
        yaml_render_service: Any,
        fluentd_config_service: Any,
    ) -> list[dict[str, Any]]:
        """Render resolved include documents into YAML or Fluentd text payloads."""
        rendered: list[dict[str, Any]] = []
        normalized_config_type = str(config_type or CONFIG_TYPE_FLUENTBIT).lower()
        for document in included_documents or []:
            child_config = document.get(KEY_CONFIG)
            node: dict[str, Any] = {
                KEY_INCLUDE_PATH: document.get(KEY_INCLUDE_PATH, ""),
                KEY_RESOLVED_PATH: document.get(KEY_RESOLVED_PATH, ""),
                KEY_OK: bool(document.get(KEY_OK, False)),
                KEY_ERRORS: deepcopy(document.get(KEY_ERRORS, [])),
            }
            if isinstance(child_config, dict):
                if normalized_config_type == CONFIG_TYPE_FLUENTD:
                    node[KEY_TEXT] = fluentd_config_service.render(deepcopy(child_config))
                else:
                    node[KEY_YAML] = yaml_render_service.render(
                        payload={KEY_CONFIG: deepcopy(child_config)},
                        include_comments=include_comments,
                    )
            child_includes = document.get(KEY_INCLUDED_DOCUMENTS)
            if isinstance(child_includes, list):
                node[KEY_INCLUDED_DOCUMENTS] = self.render_included_documents(
                    config_type=config_type,
                    included_documents=child_includes,
                    include_comments=include_comments,
                    yaml_render_service=yaml_render_service,
                    fluentd_config_service=fluentd_config_service,
                )
            else:
                node[KEY_INCLUDED_DOCUMENTS] = []
            rendered.append(node)
        return rendered

    def _resolve_include_list(
        self,
        *,
        config_type: str,
        base_dir: Path,
        include_items: Any,
        seen_stack: list[Path],
    ) -> list[dict[str, Any]]:
        """Resolve one include list into a recursive document graph."""
        if not isinstance(include_items, list):
            return []

        resolved: list[dict[str, Any]] = []
        for item in include_items:
            if not isinstance(item, str) or not item.strip():
                continue
            include_path = item.strip()
            candidates = self._expand_include_candidates(base_dir=base_dir, include_path=include_path)
            if not candidates:
                resolved.append(
                    self._error_node(
                        include_path=include_path,
                        resolved_path=str((base_dir / include_path).resolve(strict=False)),
                        code=CODE_INCLUDE_FILE_NOT_FOUND,
                        message=f"Included file '{include_path}' could not be found.",
                    )
                )
                continue

            for candidate in candidates:
                candidate_resolved = candidate.resolve(strict=False)
                if candidate_resolved in seen_stack:
                    resolved.append(
                        self._error_node(
                            include_path=include_path,
                            resolved_path=str(candidate_resolved),
                            code=CODE_INCLUDE_CYCLE_DETECTED,
                            message=f"Include cycle detected for '{candidate_resolved}'.",
                        )
                    )
                    continue

                try:
                    text = candidate.read_text(encoding=ENCODING_UTF8)
                except OSError as exc:
                    resolved.append(
                        self._error_node(
                            include_path=include_path,
                            resolved_path=str(candidate_resolved),
                            code=CODE_INCLUDE_FILE_NOT_READABLE,
                            message=f"Included file '{candidate_resolved}' could not be read: {exc}",
                        )
                    )
                    continue

                try:
                    parsed = self._parse_child_text(config_type=config_type, text=text)
                except ValueError as exc:
                    resolved.append(
                        self._error_node(
                            include_path=include_path,
                            resolved_path=str(candidate_resolved),
                            code=CODE_INCLUDE_PARSE_ERROR,
                            message=str(exc),
                        )
                    )
                    continue

                child_config = parsed.get(KEY_CONFIG)
                if not isinstance(child_config, dict):
                    resolved.append(
                        self._error_node(
                            include_path=include_path,
                            resolved_path=str(candidate_resolved),
                            code=CODE_INCLUDE_PARSE_ERROR,
                            message=f"Included file '{candidate_resolved}' did not produce a valid config object.",
                        )
                    )
                    continue

                resolved.append(
                    {
                        KEY_INCLUDE_PATH: include_path,
                        KEY_RESOLVED_PATH: str(candidate_resolved),
                        KEY_OK: bool(parsed.get(KEY_OK, True)),
                        KEY_ERRORS: deepcopy(parsed.get(KEY_ERRORS, [])),
                        KEY_CONFIG: deepcopy(child_config),
                        KEY_INCLUDED_DOCUMENTS: self._resolve_include_list(
                            config_type=config_type,
                            base_dir=candidate.parent,
                            include_items=child_config.get(KEY_INCLUDES),
                            seen_stack=seen_stack + [candidate_resolved],
                        ),
                    }
                )
        return resolved

    @staticmethod
    def _error_node(*, include_path: str, resolved_path: str, code: str, message: str) -> dict[str, Any]:
        """Build a normalized warning node for a failed include resolution."""
        return {
            KEY_INCLUDE_PATH: include_path,
            KEY_RESOLVED_PATH: resolved_path,
            KEY_OK: False,
            KEY_ERRORS: [
                {
                    KEY_ORDER: 1,
                    KEY_CODE: code,
                    KEY_PATH: PATH_INCLUDES,
                    KEY_MESSAGE: message,
                    KEY_SEVERITY: SEVERITY_WARNING,
                    KEY_SOURCE: SOURCE_INCLUDE_LOADER,
                }
            ],
            KEY_INCLUDED_DOCUMENTS: [],
        }

    @staticmethod
    def _expand_include_candidates(*, base_dir: Path, include_path: str) -> list[Path]:
        """Expand one include declaration into existing file candidates."""
        candidate = Path(include_path).expanduser()
        if not candidate.is_absolute():
            candidate = (base_dir / candidate).resolve(strict=False)
        if any(token in include_path for token in GLOB_TOKENS):
            return sorted(Path(path) for path in candidate.parent.glob(candidate.name))
        if candidate.exists():
            return [candidate]
        return []

    def _parse_child_text(self, *, config_type: str, text: str) -> dict[str, Any]:
        """Parse one included document according to the current config type."""
        if str(config_type or CONFIG_TYPE_FLUENTBIT).lower() == CONFIG_TYPE_FLUENTD:
            config = self._fluentd_config_service.parse(text)
            return {KEY_OK: True, KEY_CONFIG: config, KEY_ERRORS: []}
        return self._fluentbit_yaml_config_service.parse(text)

    def _merged_config_from_document(self, document: dict[str, Any]) -> dict[str, Any] | None:
        """Build one recursively merged config subtree from a resolved include node."""
        config = document.get(KEY_CONFIG)
        if not isinstance(config, dict):
            return None
        return self.merge_for_validation(
            config=deepcopy(config),
            included_documents=document.get(KEY_INCLUDED_DOCUMENTS, []),
        )

    @staticmethod
    def _empty_like(config: dict[str, Any]) -> dict[str, Any]:
        """Return an empty structure mirroring the root config shape."""
        empty: dict[str, Any] = {}
        for key, value in config.items():
            if isinstance(value, dict):
                empty[key] = {}
            elif isinstance(value, list):
                empty[key] = []
            else:
                empty[key] = deepcopy(value)
        return empty

    def _merge_configs(self, base: Any, extra: Any) -> Any:
        """Merge two config trees, preserving structure and include ordering."""
        if isinstance(base, dict) and isinstance(extra, dict):
            merged = deepcopy(base)
            for key, value in extra.items():
                if key == KEY_META:
                    if isinstance(value, dict):
                        merged[key] = deepcopy(value)
                    continue
                if key not in merged:
                    merged[key] = deepcopy(value)
                    continue
                merged[key] = self._merge_configs(merged[key], value)
            return merged
        if isinstance(base, list) and isinstance(extra, list):
            return deepcopy(base) + deepcopy(extra)
        return deepcopy(base if base not in (None, "") else extra)
