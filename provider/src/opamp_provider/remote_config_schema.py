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

"""Provider request-schema helpers for queued AgentRemoteConfig offers."""

from __future__ import annotations

import json
import logging
import pathlib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import yaml
from defusedxml import ElementTree as xml_etree

from shared.agent_remote_config import AgentConfigMapFileEntry

LOGGER = logging.getLogger(__name__)
TEXT_PLAIN_CONTENT_TYPE = "text/plain"
YAML_CONTENT_TYPE = "application/x-yaml"
XML_CONTENT_TYPE = "application/xml"
JSON_CONTENT_TYPE = "application/json"
FLUENTBIT_CONFIG_TYPE = "fluentbit"
FLUENTD_CONFIG_TYPE = "fluentd"
CONFIG_EDITOR_VALIDATION_MODE = "config_editor"
BASIC_VALIDATION_MODE = "basic"
YAML_SUFFIXES = {".yaml", ".yml"}
XML_SUFFIXES = {".xml"}
JSON_SUFFIXES = {".json"}
FLUENTD_SUFFIXES = {".conf"}
JSON_CONTENT_TYPES = {"application/json", "text/json"}
YAML_CONTENT_TYPES = {
    "application/yaml",
    "application/x-yaml",
    "text/yaml",
    "text/x-yaml",
}
XML_CONTENT_TYPES = {"application/xml", "text/xml"}
VALIDATION_PAYLOAD_KEY_CONFIG = "config"
VALIDATION_RESULT_KEY_ERRORS = "errors"
VALIDATION_RESULT_KEY_OK = "ok"


@dataclass(frozen=True)
class RemoteConfigValidationSettings:
    """Optional richer validation hints supplied by the request caller."""

    config_type: str | None = None
    version: str | None = None
    profile: str | None = None

    @classmethod
    def from_payload(cls, payload: object) -> RemoteConfigValidationSettings:
        """Normalize optional validation settings from request payload data."""
        if payload is None:
            return cls()
        if not isinstance(payload, dict):
            raise ValueError("validation must be an object when provided")
        config_type = str(payload.get("config_type", "")).strip().lower() or None
        version = str(payload.get("version", "")).strip() or None
        profile = str(payload.get("profile", "")).strip() or None
        return cls(config_type=config_type, version=version, profile=profile)


@dataclass(frozen=True)
class RemoteConfigSelectionSpec:
    """Ordered remote-config selection item returned from API payload normalization."""

    source_path: pathlib.Path
    target_name: str

    @property
    def filename(self) -> str:
        """Return the basename displayed in provider responses."""
        return self.source_path.name


@dataclass(frozen=True)
class RemoteConfigFileSpec:
    """Normalized file descriptor used during remote-config validation/build."""

    source_path: pathlib.Path
    target_name: str
    content_type: str
    body: bytes
    validation_kind: str

    @property
    def size_bytes(self) -> int:
        """Return the file-body length in bytes."""
        return len(self.body)

    def to_agent_config_map_entry(self) -> AgentConfigMapFileEntry:
        """Convert provider file-spec state into a shared AgentConfigMap entry."""
        return AgentConfigMapFileEntry(
            target_name=self.target_name,
            body=self.body,
            content_type=self.content_type,
        )


def normalize_remote_config_file_specs(files_payload: object) -> list[RemoteConfigFileSpec]:
    """Normalize request file descriptors into concrete remote-config file specs."""
    selection_specs = normalize_remote_config_selection_specs(files_payload)
    file_specs: list[RemoteConfigFileSpec] = []
    for index, selection_spec in enumerate(selection_specs):
        item = files_payload[index]
        explicit_content_type = _extract_explicit_content_type(item)
        file_specs.append(
            RemoteConfigFileSpec(
                source_path=selection_spec.source_path,
                target_name=selection_spec.target_name,
                content_type=_resolve_remote_config_content_type(
                    source_path=selection_spec.source_path,
                    explicit_content_type=explicit_content_type,
                ),
                body=selection_spec.source_path.read_bytes(),
                validation_kind=_detect_validation_kind(
                    source_path=selection_spec.source_path,
                    explicit_content_type=explicit_content_type,
                ),
            )
        )
    return file_specs


def normalize_remote_config_selection_specs(
    files_payload: object,
) -> list[RemoteConfigSelectionSpec]:
    """Normalize request file descriptors into ordered callback-safe selection items."""
    if not isinstance(files_payload, list) or not files_payload:
        raise ValueError("files must be a non-empty list")

    selection_specs: list[RemoteConfigSelectionSpec] = []
    seen_target_names: set[str] = set()
    for item in files_payload:
        source_path, target_name, _ = _normalize_file_item(item)
        resolved_source_path = source_path.resolve()
        if not resolved_source_path.is_file():
            raise ValueError(f"source file does not exist: {source_path}")
        lowered_target_name = target_name.casefold()
        if lowered_target_name in seen_target_names:
            raise ValueError(
                f"duplicate remote config target name is not allowed: {target_name}"
            )
        seen_target_names.add(lowered_target_name)
        selection_specs.append(
            RemoteConfigSelectionSpec(
                source_path=resolved_source_path,
                target_name=target_name,
            )
        )
    return selection_specs


def validate_remote_config_files(
    file_specs: list[RemoteConfigFileSpec],
    *,
    app_extensions: Mapping[str, Any],
    validation_payload: object = None,
) -> list[dict[str, str]]:
    """Validate all files before they are queued into one remote-config payload."""
    settings = RemoteConfigValidationSettings.from_payload(validation_payload)
    results: list[dict[str, str]] = []
    for file_spec in file_specs:
        validation_mode = _validate_one_file(
            file_spec=file_spec,
            app_extensions=app_extensions,
            settings=settings,
        )
        results.append(
            {
                "target_name": file_spec.target_name,
                "validation_mode": validation_mode,
            }
        )
    return results


def config_editor_validation_available(app_extensions: Mapping[str, Any]) -> bool:
    """Return whether embedded config-service validation helpers are mounted."""
    return "validation_service" in app_extensions and "catalog_service" in app_extensions


def _normalize_file_item(
    item: object,
) -> tuple[pathlib.Path, str, str | None]:
    """Normalize one incoming file descriptor into path/name/type primitives."""
    if isinstance(item, str):
        source_path = pathlib.Path(item).expanduser()
        target_name = source_path.name
        explicit_content_type = None
    elif isinstance(item, dict):
        raw_source_path = item.get("source_path") or item.get("path")
        if not raw_source_path:
            raise ValueError("each file item requires source_path")
        source_path = pathlib.Path(str(raw_source_path)).expanduser()
        target_name = str(
            item.get("target_name")
            or item.get("target_path")
            or item.get("filename")
            or source_path.name
        ).strip()
        explicit_content_type = str(item.get("content_type", "")).strip() or None
    else:
        raise ValueError("each file item must be a string path or object")

    if not target_name:
        raise ValueError("target file name cannot be blank")
    return source_path, target_name, explicit_content_type


def _extract_explicit_content_type(item: object) -> str | None:
    """Return one explicit content type from an incoming request file descriptor."""
    if not isinstance(item, dict):
        return None
    return str(item.get("content_type", "")).strip() or None


def _resolve_remote_config_content_type(
    *,
    source_path: pathlib.Path,
    explicit_content_type: str | None,
) -> str:
    """Return the inferred content type for one remote-config file."""
    if explicit_content_type:
        return explicit_content_type
    suffix = source_path.suffix.lower()
    if suffix in YAML_SUFFIXES:
        return YAML_CONTENT_TYPE
    if suffix in JSON_SUFFIXES:
        return JSON_CONTENT_TYPE
    if suffix in XML_SUFFIXES:
        return XML_CONTENT_TYPE
    return TEXT_PLAIN_CONTENT_TYPE


def _detect_validation_kind(
    *,
    source_path: pathlib.Path,
    explicit_content_type: str | None,
) -> str:
    """Infer which validation routine should be used for one file."""
    normalized_content_type = str(explicit_content_type or "").split(";", 1)[0].strip().lower()
    if normalized_content_type in JSON_CONTENT_TYPES:
        return "json"
    if normalized_content_type in YAML_CONTENT_TYPES:
        return "yaml"
    if normalized_content_type in XML_CONTENT_TYPES:
        return "xml"
    suffix = source_path.suffix.lower()
    if suffix in JSON_SUFFIXES:
        return "json"
    if suffix in YAML_SUFFIXES:
        return "yaml"
    if suffix in XML_SUFFIXES:
        return "xml"
    return "text"


def _validate_one_file(
    *,
    file_spec: RemoteConfigFileSpec,
    app_extensions: Mapping[str, Any],
    settings: RemoteConfigValidationSettings,
) -> str:
    """Validate one file using config-service when possible, otherwise basic parsing."""
    body_text = _decode_utf8_text(file_spec=file_spec)
    editor_config_type = _infer_editor_config_type(file_spec=file_spec, settings=settings)
    if editor_config_type and config_editor_validation_available(app_extensions):
        _validate_with_config_editor(
            file_spec=file_spec,
            body_text=body_text,
            app_extensions=app_extensions,
            settings=settings,
            config_type=editor_config_type,
        )
        return CONFIG_EDITOR_VALIDATION_MODE
    _validate_with_basic_parser(
        file_spec=file_spec,
        body_text=body_text,
    )
    return BASIC_VALIDATION_MODE


def _decode_utf8_text(*, file_spec: RemoteConfigFileSpec) -> str:
    """Decode a queued file as UTF-8 text, rejecting binary/invalid data."""
    try:
        return file_spec.body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"remote config file '{file_spec.target_name}' is not valid UTF-8 text"
        ) from exc


def _infer_editor_config_type(
    *,
    file_spec: RemoteConfigFileSpec,
    settings: RemoteConfigValidationSettings,
) -> str | None:
    """Infer the config-service config type for the provided file when possible."""
    if settings.config_type:
        return settings.config_type
    suffix = file_spec.source_path.suffix.lower()
    if suffix in FLUENTD_SUFFIXES:
        return FLUENTD_CONFIG_TYPE
    if file_spec.validation_kind in {"json", "yaml"}:
        return FLUENTBIT_CONFIG_TYPE
    return None


def _validate_with_config_editor(
    *,
    file_spec: RemoteConfigFileSpec,
    body_text: str,
    app_extensions: Mapping[str, Any],
    settings: RemoteConfigValidationSettings,
    config_type: str,
) -> None:
    """Validate one text file using embedded config-service validation helpers."""
    validation_service = app_extensions["validation_service"]
    catalog_service = app_extensions["catalog_service"]
    version = settings.version or catalog_service.get_default_version(config_type=config_type)
    catalog_payload = catalog_service.get_catalog(version, config_type=config_type)
    parser_definition = _load_parser_definition(
        app_extensions=app_extensions,
        version=version,
        config_type=config_type,
    )
    payload = _build_config_editor_validation_payload(
        file_spec=file_spec,
        body_text=body_text,
        app_extensions=app_extensions,
        config_type=config_type,
    )
    result = validation_service.validate(
        version=version,
        payload=payload,
        catalog=catalog_payload,
        profile=settings.profile,
        parser_definition=parser_definition,
    )
    if result.get(VALIDATION_RESULT_KEY_OK):
        return
    error_messages = _join_validation_messages(result.get(VALIDATION_RESULT_KEY_ERRORS))
    raise ValueError(
        f"config editor validation failed for '{file_spec.target_name}': {error_messages}"
    )


def _load_parser_definition(
    *,
    app_extensions: Mapping[str, Any],
    version: str,
    config_type: str,
) -> dict[str, object] | None:
    """Return parser-definition metadata for Fluent Bit validation when available."""
    if config_type != FLUENTBIT_CONFIG_TYPE:
        return None
    parser_definition_service = app_extensions.get("parser_definition_service")
    if parser_definition_service is None:
        return None
    return parser_definition_service.get_definition(
        version,
        config_type=FLUENTBIT_CONFIG_TYPE,
    )


def _build_config_editor_validation_payload(
    *,
    file_spec: RemoteConfigFileSpec,
    body_text: str,
    app_extensions: Mapping[str, Any],
    config_type: str,
) -> dict[str, object]:
    """Parse source text into the config-service validation payload shape."""
    if config_type == FLUENTD_CONFIG_TYPE:
        fluentd_config_service = app_extensions["fluentd_config_service"]
        parsed_payload = fluentd_config_service.parse(body_text)
        return _config_only_payload(
            parsed_payload=parsed_payload,
            target_name=file_spec.target_name,
        )
    if file_spec.validation_kind == "yaml":
        fluentbit_yaml_config_service = app_extensions["fluentbit_yaml_config_service"]
        parsed_payload = fluentbit_yaml_config_service.parse(body_text)
        return _config_only_payload(
            parsed_payload=parsed_payload,
            target_name=file_spec.target_name,
        )
    if file_spec.validation_kind == "json":
        return {
            VALIDATION_PAYLOAD_KEY_CONFIG: json.loads(body_text),
        }
    raise ValueError(
        f"config editor validation does not support '{file_spec.target_name}' as {file_spec.validation_kind}"
    )


def _config_only_payload(
    *,
    parsed_payload: object,
    target_name: str,
) -> dict[str, object]:
    """Return a config-only validation payload from one parser service result."""
    if not isinstance(parsed_payload, dict):
        raise ValueError(
            f"config editor parser returned an invalid payload for '{target_name}'"
        )
    parse_errors = parsed_payload.get(VALIDATION_RESULT_KEY_ERRORS)
    if isinstance(parse_errors, list) and parse_errors:
        raise ValueError(
            f"config editor parser rejected '{target_name}': { _join_validation_messages(parse_errors) }"
        )
    parsed_config = parsed_payload.get(VALIDATION_PAYLOAD_KEY_CONFIG)
    return {
        VALIDATION_PAYLOAD_KEY_CONFIG: parsed_config,
    }


def _join_validation_messages(messages_payload: object) -> str:
    """Join config-editor validation messages into one stable error string."""
    if not isinstance(messages_payload, list) or not messages_payload:
        return "unknown validation error"
    joined_messages = [
        str(message).strip()
        for message in messages_payload
        if str(message).strip()
    ]
    return "; ".join(joined_messages) or "unknown validation error"


def _validate_with_basic_parser(
    *,
    file_spec: RemoteConfigFileSpec,
    body_text: str,
) -> None:
    """Validate one text file with builtin JSON/YAML/XML parser checks."""
    if file_spec.validation_kind == "json":
        _validate_json_text(file_spec=file_spec, body_text=body_text)
        return
    if file_spec.validation_kind == "yaml":
        _validate_yaml_text(file_spec=file_spec, body_text=body_text)
        return
    if file_spec.validation_kind == "xml":
        _validate_xml_text(file_spec=file_spec, body_text=body_text)


def _validate_json_text(*, file_spec: RemoteConfigFileSpec, body_text: str) -> None:
    """Validate JSON text and surface one request-friendly error message."""
    try:
        json.loads(body_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid JSON in '{file_spec.target_name}': {exc.msg} "
            f"(line {exc.lineno}, column {exc.colno})"
        ) from exc


def _validate_yaml_text(*, file_spec: RemoteConfigFileSpec, body_text: str) -> None:
    """Validate YAML text and surface one request-friendly error message."""
    try:
        yaml.safe_load(body_text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML in '{file_spec.target_name}': {exc}") from exc


def _validate_xml_text(*, file_spec: RemoteConfigFileSpec, body_text: str) -> None:
    """Validate XML text and surface one request-friendly error message."""
    try:
        xml_etree.fromstring(body_text)
    except xml_etree.ParseError as exc:
        raise ValueError(f"invalid XML in '{file_spec.target_name}': {exc}") from exc
