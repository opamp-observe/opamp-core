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

"""Common configuration enums and helpers for OpAMP projects."""

from __future__ import annotations

import importlib
import json
import logging
import pathlib
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Callable, Iterable

LOGGER = logging.getLogger(__name__)

BOOL_TRUE_VALUES = {"1", "true", "yes", "on"}
BOOL_FALSE_VALUES = {"0", "false", "no", "off"}
JSON_EMPTY_OBJECT: dict[str, Any] = {}

NAME_UNSPECIFIED_AGENT_CAPABILITY = "UnspecifiedAgentCapability"

ANYVALUE_ONEOF_NAME = "value"
ANYVALUE_KIND_STRING = "string_value"
ANYVALUE_KIND_BYTES = "bytes_value"
ANYVALUE_KIND_INT = "int_value"
ANYVALUE_KIND_BOOL = "bool_value"
ANYVALUE_KIND_DOUBLE = "double_value"
BOOL_VALUE_TRUE = "true"
BOOL_VALUE_FALSE = "false"

COMPONENT_ENTRYPOINT_SEPARATOR_COLON = ":"
COMPONENT_ENTRYPOINT_SEPARATOR_DOT = "."
ERR_COMPONENT_ENTRY_POINT_EMPTY = "component entry point cannot be empty"
ERR_COMPONENT_ENTRY_POINT_INVALID_TEMPLATE = (
    "invalid component entry point '{entry_point}' (expected module:symbol)"
)
ERR_COMPONENT_ENTRY_POINT_NOT_CALLABLE_TEMPLATE = (
    "component entry point '{entry_point}' is not callable"
)

CFG_KEY_ENABLED = "enabled"
CFG_KEY_ENTRY_POINT = "entry_point"
CFG_KEY_ENTRYPOINT = "entrypoint"
CFG_KEY_PYTHON_ENTRYPOINT = "python_entrypoint"
CFG_KEY_PYTHON_ENTRY_POINT = "python-entry-point"
CFG_KEY_LABEL = "label"
CFG_KEY_URL = "url"
CFG_KEY_PATH = "path"
CFG_COMPONENT_ENTRY_POINTS = "component-entry-points"
CFG_COMPONENT_ENTRY_POINTS_QUART = "quart"

OPAMP_HTTP_PATH = "/v1/opamp"
UTF8_ENCODING = "utf-8"
OPAMP_TRANSPORT_HEADER_NONE = 0
PB_FIELD_INSTANCE_UID = "instance_uid"
PB_FIELD_ERROR_RESPONSE = "error_response"
PB_FIELD_REMOTE_CONFIG = "remote_config"
PB_FIELD_CONNECTION_SETTINGS = "connection_settings"
PB_FIELD_PACKAGES_AVAILABLE = "packages_available"
PB_FIELD_AGENT_IDENTIFICATION = "agent_identification"
PB_FIELD_COMMAND = "command"
PB_FIELD_CUSTOM_CAPABILITIES = "custom_capabilities"
PB_FIELD_CUSTOM_MESSAGE = "custom_message"
PB_FIELD_RETRY_INFO = "retry_info"
PB_FIELD_AGENT_DESCRIPTION = "agent_description"
PB_FIELD_AGENT_DISCONNECT = "agent_disconnect"
PB_FIELD_HEALTH = "health"
PB_FIELD_PACKAGE_STATUSES = "package_statuses"
PB_FIELD_CONNECTION_SETTINGS_REQUEST = "connection_settings_request"
PB_FLAG_REPORT_FULL_STATE = "ReportFullState"


class AgentCapabilities(IntEnum):
    """Agent capability bit flags from the OpAMP specification."""

    Unspecified = 0x00000000
    ReportsStatus = 0x00000001
    AcceptsRemoteConfig = 0x00000002
    ReportsEffectiveConfig = 0x00000004
    AcceptsPackages = 0x00000008
    ReportsPackageStatuses = 0x00000010
    ReportsOwnTraces = 0x00000020
    ReportsOwnMetrics = 0x00000040
    ReportsOwnLogs = 0x00000080
    AcceptsOpAMPConnectionSettings = 0x00000100
    AcceptsOtherConnectionSettings = 0x00000200
    AcceptsRestartCommand = 0x00000400
    ReportsHealth = 0x00000800
    ReportsRemoteConfig = 0x00001000
    ReportsHeartbeat = 0x00002000
    ReportsAvailableComponents = 0x00004000
    ReportsConnectionSettingsStatus = 0x00008000


AGENT_CAPABILITIES_MAP: dict[str, int] = {
    name: int(value) for name, value in AgentCapabilities.__members__.items()
}
AGENT_CAPABILITIES_MAP[NAME_UNSPECIFIED_AGENT_CAPABILITY] = int(AgentCapabilities.Unspecified)


class ServerCapabilities(IntEnum):
    """Server capability bit flags from the OpAMP specification."""

    Unspecified = 0x00000000
    AcceptsStatus = 0x00000001
    OffersRemoteConfig = 0x00000002
    AcceptsEffectiveConfig = 0x00000004
    OffersPackages = 0x00000008
    AcceptsPackagesStatus = 0x00000010
    OffersConnectionSettings = 0x00000020
    AcceptsConnectionSettingsRequest = 0x00000040


@dataclass(frozen=True)
class ComponentEntryPoint:
    """Normalized component entrypoint record from configuration."""

    entry_point: str
    label: str = ""
    url: str = ""
    enabled: bool = True


def parse_capabilities(names: Iterable[str], enum_cls: type[IntEnum]) -> int:
    """Convert capability names into a bitmask for the given enum class."""
    LOGGER.info("parsing capability names enum=%s", enum_cls.__name__)
    mask = 0
    if not isinstance(names, Iterable):
        LOGGER.warning("capability payload is not iterable payload=%r", names)
        return mask

    for name in names:
        try:
            mask |= int(enum_cls[name])
            LOGGER.debug("parse_capabilities add to mask (%s) for %s", enum_cls[name], name)
        except KeyError:
            LOGGER.warning("unknown capability ignored capability=%s enum=%s", name, enum_cls.__name__)
    LOGGER.info("completed capability parsing enum=%s mask=%s", enum_cls.__name__, mask)
    return mask


def anyvalue_to_string(value: Any) -> str | None:
    """Convert a protobuf AnyValue-like object into a string representation."""
    if value is None:
        LOGGER.warning("cannot convert AnyValue-like payload because value is None")
        return None
    try:
        kind = value.WhichOneof(ANYVALUE_ONEOF_NAME)
    except AttributeError:
        LOGGER.warning("AnyValue-like payload is missing WhichOneof; type=%s", type(value).__name__)
        return None

    LOGGER.debug("converting AnyValue-like payload kind=%s", kind)
    if kind == ANYVALUE_KIND_STRING:
        return value.string_value
    if kind == ANYVALUE_KIND_BYTES:
        return value.bytes_value.hex()
    if kind == ANYVALUE_KIND_INT:
        return str(value.int_value)
    if kind == ANYVALUE_KIND_BOOL:
        return BOOL_VALUE_TRUE if value.bool_value else BOOL_VALUE_FALSE
    if kind == ANYVALUE_KIND_DOUBLE:
        return str(value.double_value)

    LOGGER.warning("unsupported AnyValue-like payload kind=%s", kind)
    return None


def _coerce_bool(value: Any, default: bool = False) -> bool:
    """Return boolean coercion for common config and environment value forms."""
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in BOOL_TRUE_VALUES:
        return True
    if normalized in BOOL_FALSE_VALUES:
        return False
    LOGGER.warning("failed to coerce bool value=%r default=%s", value, default)
    return default


def normalize_component_entry_points(configured: Any) -> list[ComponentEntryPoint]:
    """Normalize raw component entrypoint payload into structured records."""
    LOGGER.info("normalizing component entry points payload_type=%s", type(configured).__name__)
    if isinstance(configured, str):
        configured = [item.strip() for item in configured.split(",") if item.strip()]
    if not isinstance(configured, list):
        LOGGER.warning(
            "component entry point payload is not a list after normalization payload_type=%s",
            type(configured).__name__,
        )
        return []

    normalized: list[ComponentEntryPoint] = []
    for item in configured:
        if isinstance(item, str):
            entry = item.strip()
            if entry:
                normalized.append(ComponentEntryPoint(entry_point=entry))
            else:
                LOGGER.warning("skipping blank string component entry point")
            continue
        if not isinstance(item, dict):
            LOGGER.warning(
                "skipping component entry point item because it is not a dict type=%s",
                type(item).__name__,
            )
            continue
        enabled = _coerce_bool(item.get(CFG_KEY_ENABLED), True)
        if enabled is not True:
            LOGGER.info("skipping disabled component entry point item=%s", item)
            continue
        candidate = str(
            item.get(CFG_KEY_ENTRY_POINT)
            or item.get(CFG_KEY_ENTRYPOINT)
            or item.get(CFG_KEY_PYTHON_ENTRYPOINT)
            or item.get(CFG_KEY_PYTHON_ENTRY_POINT)
            or ""
        ).strip()
        if not candidate:
            LOGGER.warning("skipping component entry point item without entry point keys item=%s", item)
            continue
        label = str(item.get(CFG_KEY_LABEL) or "").strip()
        url = str(item.get(CFG_KEY_URL) or item.get(CFG_KEY_PATH) or "").strip()
        normalized.append(
            ComponentEntryPoint(
                entry_point=candidate,
                label=label,
                url=url,
                enabled=True,
            )
        )
    LOGGER.info("completed component entry point normalization count=%s", len(normalized))
    return normalized


def resolve_component_entry_points_from_payload(
    payload: dict[str, Any] | None,
    *,
    runtime_key: str = CFG_COMPONENT_ENTRY_POINTS_QUART,
    default_entry_points: Iterable[str] = (),
) -> list[ComponentEntryPoint]:
    """Resolve component entrypoints for one runtime from loaded config payload."""
    LOGGER.info("resolving component entry points runtime_key=%s", runtime_key)
    raw = payload if isinstance(payload, dict) else {}
    if payload is not None and not isinstance(payload, dict):
        LOGGER.warning(
            "component entry point payload root is not a dict payload_type=%s",
            type(payload).__name__,
        )
    configured = raw.get(CFG_COMPONENT_ENTRY_POINTS)
    if isinstance(configured, dict):
        configured = configured.get(runtime_key, [])
    normalized = normalize_component_entry_points(configured)
    if normalized:
        LOGGER.info(
            "resolved configured component entry points runtime_key=%s count=%s",
            runtime_key,
            len(normalized),
        )
        return normalized

    default_items = [
        ComponentEntryPoint(entry_point=str(item).strip())
        for item in default_entry_points
        if str(item).strip()
    ]
    LOGGER.info(
        "using default component entry points runtime_key=%s count=%s",
        runtime_key,
        len(default_items),
    )
    return default_items


def load_json_config(path: pathlib.Path) -> dict[str, Any]:
    """Load JSON configuration from disk, returning empty payload on read errors."""
    LOGGER.info("loading JSON config path=%s", path)
    if not path.exists():
        LOGGER.warning("JSON config path does not exist path=%s", path)
        return dict(JSON_EMPTY_OBJECT)
    try:
        payload = json.loads(path.read_text(encoding=UTF8_ENCODING))
    except json.JSONDecodeError as exc:
        LOGGER.exception(
            "failed to parse JSON config path=%s line=%s column=%s message=%s",
            path,
            exc.lineno,
            exc.colno,
            exc.msg,
        )
        return dict(JSON_EMPTY_OBJECT)
    except (OSError, ValueError, TypeError) as exc:
        LOGGER.exception("failed to load JSON config path=%s message=%s", path, exc)
        return dict(JSON_EMPTY_OBJECT)
    if not isinstance(payload, dict):
        LOGGER.warning(
            "JSON config payload is not an object path=%s payload_type=%s",
            path,
            type(payload).__name__,
        )
        return dict(JSON_EMPTY_OBJECT)
    LOGGER.info("loaded JSON config path=%s", path)
    return payload


def resolve_component_callable(component_entry_point: str) -> Callable[[Any], None]:
    """Resolve one `module:symbol` entrypoint string to a callable."""
    entry_point = str(component_entry_point or "").strip()
    LOGGER.info("resolving component callable entry_point=%s", entry_point)
    if not entry_point:
        LOGGER.error("component callable resolution failed because entry point was empty")
        raise ValueError(ERR_COMPONENT_ENTRY_POINT_EMPTY)

    module_name: str
    symbol_path: str
    if COMPONENT_ENTRYPOINT_SEPARATOR_COLON in entry_point:
        module_name, symbol_path = entry_point.split(COMPONENT_ENTRYPOINT_SEPARATOR_COLON, 1)
    elif COMPONENT_ENTRYPOINT_SEPARATOR_DOT in entry_point:
        module_name, symbol_path = entry_point.rsplit(COMPONENT_ENTRYPOINT_SEPARATOR_DOT, 1)
    else:
        LOGGER.error("component callable resolution failed because format was invalid entry_point=%s", entry_point)
        raise ValueError(ERR_COMPONENT_ENTRY_POINT_INVALID_TEMPLATE.format(entry_point=entry_point))

    try:
        module = importlib.import_module(module_name.strip())
    except ImportError:
        LOGGER.exception("failed to import component entry point module entry_point=%s", entry_point)
        raise
    target: object = module
    try:
        for part in symbol_path.split(COMPONENT_ENTRYPOINT_SEPARATOR_DOT):
            target = getattr(target, part)
    except AttributeError:
        LOGGER.exception("failed to resolve component entry point symbol entry_point=%s", entry_point)
        raise
    if not callable(target):
        LOGGER.error("component entry point resolved to non-callable entry_point=%s target_type=%s", entry_point, type(target).__name__)
        raise TypeError(ERR_COMPONENT_ENTRY_POINT_NOT_CALLABLE_TEMPLATE.format(entry_point=entry_point))
    LOGGER.info("resolved component callable entry_point=%s", entry_point)
    return target


def register_component_entry_points(
    app: Any,
    *,
    entries: Iterable[ComponentEntryPoint],
) -> list[str]:
    """Register deduplicated component entrypoints against the provided app."""
    LOGGER.info("registering component entry points")
    registered: list[str] = []
    seen: set[str] = set()
    for item in entries:
        entry_point = str(item.entry_point or "").strip()
        if not entry_point:
            LOGGER.warning("skipping blank component entry point during registration")
            continue
        if entry_point in seen:
            LOGGER.info("skipping duplicate component entry point entry_point=%s", entry_point)
            continue
        seen.add(entry_point)
        callback = resolve_component_callable(entry_point)
        callback(app)
        registered.append(entry_point)
        LOGGER.info("registered component entry point entry_point=%s", entry_point)
    LOGGER.info("completed component entry point registration count=%s", len(registered))
    return registered
