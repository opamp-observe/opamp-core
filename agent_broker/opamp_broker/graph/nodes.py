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

"""Node implementations for normalization, intent classification, and execution.

The graph keeps each stage as a focused function so intermediate state is easy
to inspect and behavior can be extended without rewriting the full pipeline.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Final, Protocol

try:
    import pandas as pd
except Exception:  # pragma: no cover - fallback for minimal runtime environments.
    pd = None  # type: ignore[assignment]

from opamp_broker.graph.slash_commands import apply_slash_command_overrides
from opamp_broker.graph.state import (
    STATE_KEY_API_COMMAND_MODE,
    STATE_KEY_COMMAND,
    STATE_KEY_CONVERSATION_HISTORY,
    STATE_KEY_INTENT,
    STATE_KEY_NORMALIZED_TEXT,
    STATE_KEY_REQUIRES_CONFIRMATION,
    STATE_KEY_RESPONSE_TEXT,
    STATE_KEY_TARGET,
    STATE_KEY_TEXT,
    STATE_KEY_TOOL_ARGS,
    STATE_KEY_TOOL_NAME,
    STATE_KEY_TOOL_RESULT,
    STATE_KEY_TOOLS_AVAILABLE,
    BrokerState,
)
from opamp_broker.graph.table_rendering import render_fixed_width_table
from opamp_broker.mcp.client import MCPServerUnavailableError
from opamp_broker.mcp.tools import MCPToolRegistry
from opamp_broker.planner.engine import (
    RESPONSE_TEXT_KEY,
    TOOL_ARGS_KEY,
    TOOL_NAME_KEY,
    Planner,
)
from opamp_broker.planner.rule_first_planner import RuleFirstPlanner

DEFAULT_MCP_SERVER_OFFLINE_MESSAGE = (
    "The OpAMP server is currently offline. Please try again shortly."
)

# Tool response payload keys.
PAYLOAD_KEY_ACTION: Final[str] = "action"
PAYLOAD_KEY_AGENT_ID: Final[str] = "agent_id"
PAYLOAD_KEY_AGENTS: Final[str] = "agents"
PAYLOAD_KEY_CLASSIFIER: Final[str] = "classifier"
PAYLOAD_KEY_CLIENT_ID: Final[str] = "client_id"
PAYLOAD_KEY_COMMANDS: Final[str] = "commands"
PAYLOAD_KEY_CONTENT: Final[str] = "content"
PAYLOAD_KEY_DISPLAY_NAME: Final[str] = "displayname"
PAYLOAD_KEY_ERROR: Final[str] = "error"
PAYLOAD_KEY_ID: Final[str] = "id"
PAYLOAD_KEY_INSTANCE_ID: Final[str] = "instance_id"
PAYLOAD_KEY_NAME: Final[str] = "name"
PAYLOAD_KEY_OPERATION: Final[str] = "operation"
PAYLOAD_KEY_OPENAPI_SPEC: Final[str] = "openapi_spec"
PAYLOAD_KEY_PATHS: Final[str] = "paths"
PAYLOAD_KEY_STATUS: Final[str] = "status"
PAYLOAD_KEY_TEXT: Final[str] = "text"
PAYLOAD_KEY_TOTAL: Final[str] = "total"

PAYLOAD_STATUS_QUEUED: Final[str] = "queued"
UNKNOWN_CLIENT_LABEL: Final[str] = "unknown-client"
RESPONSE_PREVIEW_ITEM_LIMIT: Final[int] = 10
AGENT_TABLE_MAX_ROWS: Final[int] = RESPONSE_PREVIEW_ITEM_LIMIT
AGENT_LONG_DETAILS_MAX_ITEMS: Final[int] = AGENT_TABLE_MAX_ROWS
AGENT_DESCRIPTION_KEY_PREFIX: Final[str] = "key:"
AGENT_DESCRIPTION_STRING_VALUE_PREFIX: Final[str] = "string_value:"
AGENT_DESCRIPTION_BOOL_VALUE_PREFIX: Final[str] = "bool_value:"
AGENT_DESCRIPTION_INT_VALUE_PREFIX: Final[str] = "int_value:"
AGENT_DESCRIPTION_DOUBLE_VALUE_PREFIX: Final[str] = "double_value:"
AGENT_DESCRIPTION_BYTES_VALUE_PREFIX: Final[str] = "bytes_value:"
AGENT_FALLBACK_IP_KEY: Final[str] = "ip"
AGENT_FALLBACK_HOSTNAME_KEY: Final[str] = "hostname"
AGENT_FALLBACK_MAC_KEY: Final[str] = "mac_address"
AGENT_SOURCE_REMOTE_ADDR_KEY: Final[str] = "remote_addr"
AGENT_SOURCE_CLIENT_ID_KEY: Final[str] = "client_id"
AGENT_SOURCE_AGENT_DESCRIPTION_KEY: Final[str] = "agent_description"
OPENAPI_COMPONENTS_KEY: Final[str] = "components"
OPENAPI_SCHEMAS_KEY: Final[str] = "schemas"
OPENAPI_PROPERTIES_KEY: Final[str] = "properties"
OPENAPI_DESCRIPTION_KEY: Final[str] = "description"
OPENAPI_OTEL_AGENT_SCHEMA_KEY: Final[str] = "OtelAgent"
OPENAPI_PATHS_KEY: Final[str] = "paths"
OPENAPI_TOOL_OTEL_AGENTS_PATH_KEY: Final[str] = "/tool/otelAgents"
OPENAPI_GET_KEY: Final[str] = "get"
OPENAPI_RESPONSES_KEY: Final[str] = "responses"
OPENAPI_RESPONSE_200_KEY: Final[str] = "200"
OPENAPI_CONTENT_KEY: Final[str] = "content"
OPENAPI_APPLICATION_JSON_KEY: Final[str] = "application/json"
OPENAPI_SCHEMA_KEY: Final[str] = "schema"
OPENAPI_SCHEMA_REF_KEY: Final[str] = "$ref"
OPENAPI_REF_PREFIX: Final[str] = "#/components/schemas/"
MARKDOWN_BULLET: Final[str] = "- "
COMPONENT_HEALTH_NORMALIZED_KEY: Final[str] = "componenthealth"
AGENT_TABLE_ATTRIBUTE_HEADER: Final[str] = "attribute"
AGENT_TABLE_MISSING_VALUE: Final[str] = "-"
AGENT_TABLE_MAX_ATTRIBUTE_COLUMN_WIDTH: Final[int] = 24
AGENT_TABLE_MAX_AGENT_COLUMN_WIDTH: Final[int] = 36
AGENT_TABLE_FALLBACK_LABEL_PREFIX: Final[str] = "agent-"
AGENT_LABEL_KEYS: Final[tuple[str, ...]] = (
    PAYLOAD_KEY_ID,
    PAYLOAD_KEY_NAME,
    PAYLOAD_KEY_AGENT_ID,
    PAYLOAD_KEY_INSTANCE_ID,
)
AGENT_TABLE_PRIORITY_COLUMNS: Final[tuple[str, ...]] = (
    PAYLOAD_KEY_ID,
    PAYLOAD_KEY_NAME,
    PAYLOAD_KEY_AGENT_ID,
    PAYLOAD_KEY_INSTANCE_ID,
    PAYLOAD_KEY_STATUS,
)
AGENT_SHORT_RICH_TEXT_FIELDS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("service.name", ("service.name",)),
    ("service.type", ("service.type",)),
    ("service.instance.id", ("service.instance.id",)),
    ("service.version", ("service.version",)),
    ("os_type", ("os.type", "os_type")),
    ("os_version", ("os.version", "os_version")),
    ("hostname", ("host.name", AGENT_FALLBACK_HOSTNAME_KEY)),
    ("ip", ("host.ip", "ip", "ip_address", AGENT_SOURCE_REMOTE_ADDR_KEY)),
    ("mac_address", ("host.mac", "host.mac_address", AGENT_FALLBACK_MAC_KEY)),
)
AGENT_FIELD_DESCRIPTION_DEFAULTS: Final[dict[str, str]] = {
    "service.name": "Service name reported by the OpenTelemetry agent.",
    "service.type": "Service type/category for the running workload.",
    "service.instance.id": "Stable instance identifier for the running service.",
    "service.version": "Service version reported in agent identifying attributes.",
    "os.type": "Operating system family/type for the host environment.",
    "os.version": "Operating system version for the host environment.",
    "host.name": "Hostname reported by the agent.",
    "host.ip": "Primary host IP address reported by the agent.",
    "host.mac": "Primary host MAC address reported by the agent.",
    AGENT_SOURCE_CLIENT_ID_KEY: "Unique client identifier tracked by the provider.",
    AGENT_SOURCE_REMOTE_ADDR_KEY: "Last known source IP address observed by the provider.",
}
AGENT_CORE_DETAIL_FIELDS: Final[tuple[str, ...]] = (
    AGENT_SOURCE_CLIENT_ID_KEY,
    "service.name",
    "service.type",
    "service.instance.id",
    "service.version",
    "os.type",
    "os.version",
    "host.name",
    "host.ip",
    "host.mac",
    AGENT_SOURCE_REMOTE_ADDR_KEY,
)
PLANNER_MAX_EXECUTION_STEPS_DEFAULT: Final[int] = 4
PLANNER_MAX_EXECUTION_STEPS_HARD_LIMIT: Final[int] = 8
PLANNER_FOLLOW_UP_SUMMARY_MAX_CHARS: Final[int] = 1200
PLANNER_FOLLOW_UP_ARGS_MAX_CHARS: Final[int] = 400

logger = logging.getLogger(__name__)

class ToolResponseFormatter(Protocol):
    """Callable protocol for keyword-only AI tool response formatting."""

    async def __call__(
        self,
        *,
        user_text: str,
        tool_name: str,
        tool_args: dict[str, Any],
        tool_result: dict[str, Any],
        default_response_text: str,
    ) -> str | None: ...


def _normalize_tool_args(raw_tool_args: Any) -> dict[str, Any]:
    """Return normalized tool args as a dictionary.

    Why this helper exists:
    planner output can contain malformed types; execution paths should always
    handle arguments as a dict to keep tool calls predictable.
    """
    if isinstance(raw_tool_args, dict):
        return raw_tool_args
    return {}


def _normalize_planner_step_limit(max_planning_steps: int) -> int:
    """Clamp configured planner step count to a safe bounded range."""
    try:
        normalized = int(max_planning_steps)
    except (TypeError, ValueError):
        return PLANNER_MAX_EXECUTION_STEPS_DEFAULT
    if normalized <= 0:
        return 1
    if normalized > PLANNER_MAX_EXECUTION_STEPS_HARD_LIMIT:
        return PLANNER_MAX_EXECUTION_STEPS_HARD_LIMIT
    return normalized


def _build_follow_up_planner_text(
    *,
    user_text: str,
    tool_name: str,
    tool_args: dict[str, Any],
    tool_summary: str,
) -> str:
    """Build follow-up planner prompt text after one tool execution.

    Why this helper exists:
    multi-step planning needs explicit context from the latest tool execution so
    the LLM can decide whether to stop or select the next tool call.
    """
    try:
        rendered_args = json.dumps(tool_args, ensure_ascii=False, default=str)
    except TypeError:
        rendered_args = str(tool_args)
    if len(rendered_args) > PLANNER_FOLLOW_UP_ARGS_MAX_CHARS:
        rendered_args = rendered_args[:PLANNER_FOLLOW_UP_ARGS_MAX_CHARS] + "..."

    summary = str(tool_summary).strip()
    if len(summary) > PLANNER_FOLLOW_UP_SUMMARY_MAX_CHARS:
        omitted = len(summary) - PLANNER_FOLLOW_UP_SUMMARY_MAX_CHARS
        summary = (
            summary[:PLANNER_FOLLOW_UP_SUMMARY_MAX_CHARS]
            + f"... [truncated {omitted} chars]"
        )

    return (
        "Continue this request if needed.\n"
        f"Original user request: {user_text}\n"
        f"Latest executed tool: {tool_name}\n"
        f"Latest tool args: {rendered_args}\n"
        f"Latest tool result summary: {summary}\n"
        "If the request is complete, set tool_name to null and provide final response_text. "
        "If another tool call is required, choose exactly one next tool."
    )


def _strip_bot_mention(text: str) -> str:
    """Remove Slack bot mention tokens from inbound text.

    Why this approach:
    mention tokens are transport noise that can degrade intent matching if not
    removed before normalization.

    Args:
        text: Raw message text from Slack events or slash commands.

    Returns:
        str: Text with ``<@...>`` mention fragments removed and stripped.
    """
    return re.sub(r"<@[^>]+>", "", text).strip()


def _format_tool_response_from_mapping(
    tool_name: str,
    parsed_content: dict[str, Any],
) -> str:
    """Render mapping payloads with domain-aware shortcuts before generic summary."""
    error = parsed_content.get(PAYLOAD_KEY_ERROR)
    if isinstance(error, str) and error.strip():
        return f"The tool `{tool_name}` returned an error: {error.strip()}"

    if PAYLOAD_KEY_AGENTS in parsed_content and isinstance(parsed_content[PAYLOAD_KEY_AGENTS], list):
        return _summarize_agents_payload(parsed_content)

    if PAYLOAD_KEY_COMMANDS in parsed_content and isinstance(parsed_content[PAYLOAD_KEY_COMMANDS], list):
        return _summarize_commands_payload(parsed_content)

    if PAYLOAD_KEY_PATHS in parsed_content and isinstance(parsed_content[PAYLOAD_KEY_PATHS], dict):
        return _summarize_openapi_payload(parsed_content)

    if str(parsed_content.get(PAYLOAD_KEY_STATUS, "")).strip().lower() == PAYLOAD_STATUS_QUEUED:
        return _summarize_queue_result(parsed_content)
    return _summarize_mapping(parsed_content)


def _format_tool_response_from_list(parsed_content: list[Any]) -> str:
    """Render list payloads with bounded previews for user-facing output."""
    if not parsed_content:
        return "The tool returned an empty result."
    preview = ", ".join(str(item) for item in parsed_content[:RESPONSE_PREVIEW_ITEM_LIMIT])
    suffix = "" if len(parsed_content) <= RESPONSE_PREVIEW_ITEM_LIMIT else ", ..."
    return f"The tool returned {len(parsed_content)} item(s): {preview}{suffix}"


def _format_tool_response(tool_name: str, result: dict[str, Any]) -> str:
    """Convert MCP tool output into a concise user-facing explanation."""
    content = result.get(PAYLOAD_KEY_CONTENT)
    parsed_content = _parse_content_payload(content)

    if isinstance(parsed_content, dict):
        return _format_tool_response_from_mapping(tool_name, parsed_content)

    if isinstance(parsed_content, list):
        return _format_tool_response_from_list(parsed_content)

    text = str(parsed_content).strip()
    if text:
        return text
    return "The tool completed, but did not return any output."


def _parse_content_payload(content: Any) -> Any:
    """Normalize MCP content payload without attempting JSON auto-parsing."""
    if isinstance(content, list):
        text_chunks: list[str] = []
        for item in content:
            if isinstance(item, dict) and PAYLOAD_KEY_TEXT in item:
                text_chunks.append(str(item.get(PAYLOAD_KEY_TEXT, "")))
            else:
                text_chunks.append(str(item))
        return " ".join(chunk for chunk in text_chunks if chunk.strip()).strip()
    if isinstance(content, str):
        return content
    if content is None:
        return {}
    return content


def _extract_agent_labels(agents: list[Any]) -> list[str]:
    """Extract stable human-readable labels from agent payload entries.

    Why this helper exists:
    summary responses need deterministic labels even when payloads vary across
    provider versions and tool implementations.
    """
    labels: list[str] = []
    for agent in agents:
        if isinstance(agent, dict):
            for key in AGENT_LABEL_KEYS:
                value = agent.get(key)
                if value is not None and str(value).strip():
                    labels.append(str(value).strip())
                    break
        elif str(agent).strip():
            labels.append(str(agent).strip())
    return labels


def _summarize_agents_payload(payload: dict[str, Any]) -> str:
    """Build a concise natural-language summary for an agents tool payload.

    Why this helper exists:
    agent list results can be large; we provide a compact summary/table preview
    for Slack-friendly responses.
    """
    agents_raw = payload.get(PAYLOAD_KEY_AGENTS, [])
    if not isinstance(agents_raw, list):
        return "I checked the agents list, but the payload was invalid."
    total_raw = payload.get(PAYLOAD_KEY_TOTAL)
    try:
        total = int(total_raw) if total_raw is not None else len(agents_raw)
    except (TypeError, ValueError):
        total = len(agents_raw)

    if total <= 0:
        return "I checked and found no OpenTelemetry agents."

    summary_table = _render_agents_summary_table(agents_raw)
    if summary_table:
        shown = min(len(agents_raw), AGENT_TABLE_MAX_ROWS)
        suffix = (
            f"\nShowing first {shown} agent(s)."
            if total > shown or len(agents_raw) > shown
            else ""
        )
        return (
            f"I found {total} OpenTelemetry agent(s).{suffix}\n\n"
            "Summary view (attributes x agents):\n"
            f"```\n{summary_table}\n```"
        )

    labels = _extract_agent_labels(agents_raw)
    if labels:
        preview = ", ".join(labels[:AGENT_TABLE_MAX_ROWS])
        extra = "" if len(labels) <= AGENT_TABLE_MAX_ROWS else ", ..."
        return f"I found {total} OpenTelemetry agent(s): {preview}{extra}"
    return f"I found {total} OpenTelemetry agent(s)."


def _render_agents_short_rich_text(agents: list[Any]) -> str:
    """Render a short bullet list view of agents and key identifying fields."""
    rendered: list[str] = []
    for agent in agents[:AGENT_TABLE_MAX_ROWS]:
        if not isinstance(agent, dict):
            continue
        line = _render_agent_short_rich_text(agent)
        if line:
            rendered.append(f"{MARKDOWN_BULLET}{line}")
    return "\n".join(rendered)


def _render_agents_summary_table(agents: list[Any]) -> str | None:
    """Render a fixed-width attribute-vs-agent summary table.

    Why this helper exists:
    tabular output makes cross-agent comparisons easier than paragraph text.
    """
    table_agents = [agent for agent in agents[:AGENT_TABLE_MAX_ROWS] if isinstance(agent, dict)]
    if not table_agents:
        return None

    headers = [AGENT_TABLE_ATTRIBUTE_HEADER]
    agent_values: list[dict[str, str]] = []
    for index, agent in enumerate(table_agents):
        labels = _extract_agent_labels([agent])
        fallback_label = f"{AGENT_TABLE_FALLBACK_LABEL_PREFIX}{index + 1}"
        headers.append(labels[0] if labels else fallback_label)
        agent_values.append(_extract_agent_attribute_values(agent))

    rows: list[list[str]] = []
    for label, candidates in AGENT_SHORT_RICH_TEXT_FIELDS:
        row = [label]
        for values in agent_values:
            row.append(
                _first_non_empty_attribute(values, candidates)
                or AGENT_TABLE_MISSING_VALUE
            )
        rows.append(row)
    return render_fixed_width_table(
        headers,
        rows,
        first_column_max_width=AGENT_TABLE_MAX_ATTRIBUTE_COLUMN_WIDTH,
        data_column_max_width=AGENT_TABLE_MAX_AGENT_COLUMN_WIDTH,
    )


def _render_agent_short_rich_text(agent: dict[str, Any]) -> str:
    """Render one agent as compact `key=value` text for quick previews."""
    values = _extract_agent_attribute_values(agent)
    parts: list[str] = []
    for label, candidates in AGENT_SHORT_RICH_TEXT_FIELDS:
        value = _first_non_empty_attribute(values, candidates)
        if value:
            parts.append(f"{label}={value}")
    if parts:
        return "; ".join(parts)
    fallback_label = _extract_agent_labels([agent])
    if fallback_label:
        return str(fallback_label[0])
    return ""


def _render_agent_short_rich_txt(agent: dict[str, Any]) -> str:
    """Compatibility alias using `rich_txt` naming for short agent rendering."""
    return _render_agent_short_rich_text(agent)


def _render_agents_detailed_rich_text(
    agents: list[Any],
    *,
    field_descriptions: dict[str, str],
) -> str:
    """Render detailed markdown bullets for multiple agents.

    Why this helper exists:
    detailed views are useful for diagnostics while still enforcing response
    size limits for chat surfaces.
    """
    rendered: list[str] = []
    count = 0
    for agent in agents:
        if count >= AGENT_LONG_DETAILS_MAX_ITEMS:
            break
        if not isinstance(agent, dict):
            continue
        count += 1
        rendered.append(f"Agent {count}:")
        details = _render_agent_long_rich_text(
            agent,
            field_descriptions=field_descriptions,
        )
        if details:
            rendered.append(details)
    return "\n".join(rendered).strip()


def _render_agent_long_rich_text(
    agent: dict[str, Any],
    *,
    field_descriptions: dict[str, str],
) -> str:
    """Render one agent with ordered attributes and optional field descriptions."""
    values = _extract_agent_attribute_values(agent)
    if not values:
        return f"{MARKDOWN_BULLET}No attributes reported."
    ordered_keys = _order_agent_attribute_keys(values)
    lines: list[str] = []
    for key in ordered_keys:
        raw_value = values.get(key)
        if raw_value is None:
            continue
        value = str(raw_value).strip()
        if not value:
            continue
        description = field_descriptions.get(key, "").strip()
        if description:
            lines.append(f"{MARKDOWN_BULLET}`{key}`: `{value}` ({description})")
        else:
            lines.append(f"{MARKDOWN_BULLET}`{key}`: `{value}`")
    return "\n".join(lines)


def _render_agent_long_rich_txt(
    agent: dict[str, Any],
    *,
    field_descriptions: dict[str, str],
) -> str:
    """Compatibility alias using `rich_txt` naming for detailed rendering."""
    return _render_agent_long_rich_text(
        agent,
        field_descriptions=field_descriptions,
    )


def _order_agent_attribute_keys(values: dict[str, str]) -> list[str]:
    """Order attributes with core diagnostic keys first, then alphabetical extras."""
    core_keys = [key for key in AGENT_CORE_DETAIL_FIELDS if key in values]
    remaining = sorted(
        key for key in values if key not in set(AGENT_CORE_DETAIL_FIELDS)
    )
    return core_keys + remaining


def _extract_agent_attribute_values(agent: dict[str, Any]) -> dict[str, str]:
    """Normalize a raw agent object into flattened, display-ready string attributes."""
    values: dict[str, str] = {}
    for key, value in agent.items():
        if str(key) == AGENT_SOURCE_AGENT_DESCRIPTION_KEY:
            continue
        if isinstance(value, (dict, list)):
            continue
        rendered = str(value).strip() if value is not None else ""
        if rendered:
            values[str(key)] = rendered

    description_attributes = _parse_agent_description_attributes(
        str(agent.get(AGENT_SOURCE_AGENT_DESCRIPTION_KEY, ""))
    )
    values.update(description_attributes)

    if AGENT_SOURCE_REMOTE_ADDR_KEY in values and AGENT_FALLBACK_IP_KEY not in values:
        values[AGENT_FALLBACK_IP_KEY] = values[AGENT_SOURCE_REMOTE_ADDR_KEY]
    if "host.name" in values and AGENT_FALLBACK_HOSTNAME_KEY not in values:
        values[AGENT_FALLBACK_HOSTNAME_KEY] = values["host.name"]
    if "host.mac" in values and AGENT_FALLBACK_MAC_KEY not in values:
        values[AGENT_FALLBACK_MAC_KEY] = values["host.mac"]
    return values


def _parse_agent_description_attributes(agent_description: str) -> dict[str, str]:
    """Extract key/value attributes from proto-like `agent_description` text blocks."""
    attributes: dict[str, str] = {}
    if not agent_description.strip():
        return attributes

    current_key: str | None = None
    for raw_line in agent_description.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        key_match = re.search(r'key:\s*"([^"]+)"', line)
        if key_match:
            current_key = key_match.group(1).strip()
            inline_value = _extract_inline_proto_value(line)
            if current_key and inline_value:
                attributes[current_key] = inline_value
                current_key = None
            continue
        if not current_key:
            continue
        inline_value = _extract_inline_proto_value(line)
        if inline_value:
            attributes[current_key] = inline_value
            current_key = None
    return attributes


def _parse_proto_scalar(line: str) -> str:
    """Parse a simple proto scalar line into a cleaned string value."""
    _, _, raw = line.partition(":")
    candidate = raw.strip()
    if candidate.startswith('"') and candidate.endswith('"') and len(candidate) >= 2:
        return candidate[1:-1]
    return candidate


def _extract_inline_proto_value(line: str) -> str:
    """Extract inline proto `*_value` tokens from a single text line."""
    for prefix in (
        AGENT_DESCRIPTION_STRING_VALUE_PREFIX,
        AGENT_DESCRIPTION_BOOL_VALUE_PREFIX,
        AGENT_DESCRIPTION_INT_VALUE_PREFIX,
        AGENT_DESCRIPTION_DOUBLE_VALUE_PREFIX,
        AGENT_DESCRIPTION_BYTES_VALUE_PREFIX,
    ):
        marker_index = line.find(prefix)
        if marker_index < 0:
            continue
        candidate = line[marker_index + len(prefix):].strip()
        if not candidate:
            continue
        candidate = candidate.split("}", 1)[0].strip()
        candidate = candidate.split("{", 1)[0].strip()
        if candidate.startswith('"') and candidate.endswith('"') and len(candidate) >= 2:
            candidate = candidate[1:-1]
        if candidate:
            return candidate
    return ""


def _first_non_empty_attribute(
    values: dict[str, str],
    keys: tuple[str, ...],
) -> str | None:
    """Return the first non-empty value for a prioritized set of attribute keys."""
    for key in keys:
        value = values.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _resolve_agent_field_descriptions(openapi_spec: Any) -> dict[str, str]:
    """Merge default field descriptions with OpenAPI-derived schema descriptions."""
    descriptions: dict[str, str] = dict(AGENT_FIELD_DESCRIPTION_DEFAULTS)
    schema_descriptions = _extract_agent_field_descriptions_from_spec(openapi_spec)
    descriptions.update(schema_descriptions)
    return descriptions


def _extract_agent_field_descriptions_from_spec(openapi_spec: Any) -> dict[str, str]:
    """Extract attribute descriptions for `OtelAgent` fields from OpenAPI spec."""
    if not isinstance(openapi_spec, dict):
        return {}

    schema = _resolve_otel_agent_schema_from_spec(openapi_spec)
    if not isinstance(schema, dict):
        return {}
    properties = schema.get(OPENAPI_PROPERTIES_KEY)
    if not isinstance(properties, dict):
        return {}

    descriptions: dict[str, str] = {}
    for key, property_spec in properties.items():
        if not isinstance(property_spec, dict):
            continue
        description = str(property_spec.get(OPENAPI_DESCRIPTION_KEY, "")).strip()
        if description:
            descriptions[str(key)] = description
    return descriptions


def _nested_dict_lookup(root: Any, *path: str) -> Any:
    """Resolve a nested dictionary path and return None when any hop is invalid."""
    current = root
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _resolve_schema_from_ref(
    schemas: dict[str, Any],
    schema_ref: Any,
) -> dict[str, Any] | None:
    """Resolve a `#/components/schemas/...` ref to a schema object."""
    ref = str(schema_ref or "").strip()
    if not ref.startswith(OPENAPI_REF_PREFIX):
        return None
    schema_name = ref[len(OPENAPI_REF_PREFIX) :]
    schema = schemas.get(schema_name)
    return schema if isinstance(schema, dict) else None


def _extract_otel_agents_response_schema_ref(openapi_spec: dict[str, Any]) -> Any:
    """Extract the `/tool/otelAgents` 200 JSON schema ref from OpenAPI payload."""
    schema = _nested_dict_lookup(
        openapi_spec,
        OPENAPI_PATHS_KEY,
        OPENAPI_TOOL_OTEL_AGENTS_PATH_KEY,
        OPENAPI_GET_KEY,
        OPENAPI_RESPONSES_KEY,
        OPENAPI_RESPONSE_200_KEY,
        OPENAPI_CONTENT_KEY,
        OPENAPI_APPLICATION_JSON_KEY,
        OPENAPI_SCHEMA_KEY,
    )
    return schema.get(OPENAPI_SCHEMA_REF_KEY) if isinstance(schema, dict) else None


def _resolve_otel_agent_schema_from_spec(openapi_spec: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve the effective `OtelAgent` schema from components or response refs."""
    components = openapi_spec.get(OPENAPI_COMPONENTS_KEY)
    schemas = components.get(OPENAPI_SCHEMAS_KEY) if isinstance(components, dict) else None
    if not isinstance(schemas, dict):
        return None

    direct_schema = schemas.get(OPENAPI_OTEL_AGENT_SCHEMA_KEY)
    if isinstance(direct_schema, dict):
        return direct_schema

    schema_ref = _extract_otel_agents_response_schema_ref(openapi_spec)
    response_schema = _resolve_schema_from_ref(schemas, schema_ref)
    if response_schema is None:
        return None
    response_properties = response_schema.get(OPENAPI_PROPERTIES_KEY)
    if not isinstance(response_properties, dict):
        return None
    agents_property = response_properties.get(PAYLOAD_KEY_AGENTS)
    if not isinstance(agents_property, dict):
        return None
    items = agents_property.get("items")
    if not isinstance(items, dict):
        return None
    return _resolve_schema_from_ref(schemas, items.get(OPENAPI_SCHEMA_REF_KEY))


def _render_agents_table(agents: list[Any]) -> str | None:
    """Render a pandas-based normalized agent table when pandas is available.

    Why this helper exists:
    this path provides a broad dynamic table view for debugging environments,
    while fixed-width summary rendering is used for regular user responses.
    """
    if pd is None:
        return None
    pandas = pd

    rows: list[dict[str, Any]] = []
    for agent in agents[:AGENT_TABLE_MAX_ROWS]:
        if isinstance(agent, dict):
            row = {
                str(key): _stringify_table_value(value)
                for key, value in agent.items()
            }
            if row:
                rows.append(row)
            continue
        label = str(agent).strip()
        if label:
            rows.append({PAYLOAD_KEY_NAME: label})

    if not rows:
        return None

    try:
        frame = pandas.json_normalize(rows, sep=".").fillna("")
    except Exception:
        return None

    if frame.empty:
        return None
    ordered_columns = _ordered_agent_columns(list(frame.columns))
    return frame[ordered_columns].to_string(index=False)


def _ordered_agent_columns(columns: list[str]) -> list[str]:
    """Order table columns with priority identifiers first, then alphabetical."""
    preferred = [col for col in AGENT_TABLE_PRIORITY_COLUMNS if col in columns]
    remaining = sorted(col for col in columns if col not in preferred)
    return preferred + remaining


def _stringify_table_value(value: Any) -> Any:
    """Convert nested values into compact JSON strings for tabular rendering."""
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, sort_keys=True)
        except TypeError:
            return str(value)
    return value


def _summarize_commands_payload(payload: dict[str, Any]) -> str:
    """Summarize command-catalog payloads into concise user-facing text."""
    commands_raw = payload.get(PAYLOAD_KEY_COMMANDS, [])
    if not isinstance(commands_raw, list):
        return "I checked the command catalog, but the payload was invalid."
    total_raw = payload.get(PAYLOAD_KEY_TOTAL)
    try:
        total = int(total_raw) if total_raw is not None else len(commands_raw)
    except (TypeError, ValueError):
        total = len(commands_raw)

    if total <= 0:
        return "I checked and found no available commands."

    labels = _extract_command_labels(commands_raw)
    if labels:
        preview = ", ".join(labels[:RESPONSE_PREVIEW_ITEM_LIMIT])
        suffix = "" if len(labels) <= RESPONSE_PREVIEW_ITEM_LIMIT else ", ..."
        return f"I found {total} available command(s): {preview}{suffix}."
    return f"I found {total} available command(s)."


def _extract_command_labels(commands: list[Any]) -> list[str]:
    """Extract display labels for command definitions with graceful fallbacks."""
    labels: list[str] = []
    for command in commands:
        if not isinstance(command, dict):
            raw = str(command).strip()
            if raw:
                labels.append(raw)
            continue
        display_name = str(command.get(PAYLOAD_KEY_DISPLAY_NAME, "")).strip()
        operation = str(command.get(PAYLOAD_KEY_OPERATION, "")).strip()
        classifier = str(command.get(PAYLOAD_KEY_CLASSIFIER, "")).strip()
        if display_name:
            labels.append(display_name)
        elif classifier and operation:
            labels.append(f"{classifier}/{operation}")
        elif operation:
            labels.append(operation)
    return labels


def _summarize_openapi_payload(payload: dict[str, Any]) -> str:
    """Summarize OpenAPI path metadata with bounded preview output."""
    paths_raw = payload.get(PAYLOAD_KEY_PATHS)
    if not isinstance(paths_raw, dict):
        return "I checked the OpenAPI spec, but no paths were available."
    routes = sorted(str(path).strip() for path in paths_raw if str(path).strip())
    total = len(routes)
    if total <= 0:
        return "I checked the OpenAPI spec, but it contains no routes."
    preview = ", ".join(routes[:RESPONSE_PREVIEW_ITEM_LIMIT])
    suffix = "" if len(routes) <= RESPONSE_PREVIEW_ITEM_LIMIT else ", ..."
    return f"I found {total} API route(s) in the OpenAPI spec: {preview}{suffix}."


def _summarize_queue_result(payload: dict[str, Any]) -> str:
    """Summarize queued-operation acknowledgements for command dispatch tools."""
    client_id = str(payload.get(PAYLOAD_KEY_CLIENT_ID, "")).strip() or UNKNOWN_CLIENT_LABEL
    classifier = str(payload.get(PAYLOAD_KEY_CLASSIFIER, "")).strip()
    action = str(payload.get(PAYLOAD_KEY_ACTION, "")).strip()
    if classifier and action:
        return (
            f"Queued command `{classifier}/{action}` for client `{client_id}`."
        )
    return f"Queued command for client `{client_id}`."


def _summarize_mapping_list_field(key_name: str, value: list[Any]) -> str:
    """Render summary text for list-valued mapping fields."""
    if not value:
        return f"{key_name} is empty"
    if all(not isinstance(item, (dict, list)) for item in value):
        preview = ", ".join(str(item) for item in value[:5])
        suffix = "" if len(value) <= 5 else ", ..."
        return f"{key_name} has {len(value)} item(s): {preview}{suffix}"
    return f"{key_name} contains {len(value)} structured item(s)"


def _summarize_mapping_dict_field(key_name: str, value: dict[str, Any]) -> str:
    """Render summary text for dict-valued mapping fields."""
    nested_keys = [
        str(nested).strip()
        for nested in value.keys()
        if not _is_component_health_field_name(str(nested).strip())
    ]
    preview = ", ".join(item for item in nested_keys[:5] if item)
    suffix = "" if len(nested_keys) <= 5 else ", ..."
    if preview:
        return f"{key_name} includes {len(nested_keys)} field(s): {preview}{suffix}"
    return f"{key_name} contains structured data"


def _summarize_mapping_field(key: Any, value: Any) -> str | None:
    """Summarize one generic mapping field while omitting null/health noise."""
    key_name = str(key).strip() or "value"
    if _is_component_health_field_name(key_name):
        return None
    if _is_null_like_scalar(value):
        return None
    if isinstance(value, list):
        return _summarize_mapping_list_field(key_name, value)
    if isinstance(value, dict):
        return _summarize_mapping_dict_field(key_name, value)
    return f"{key_name} is {value}"


def _summarize_mapping(payload: dict[str, Any]) -> str:
    """Summarize generic mapping payloads while skipping component health noise."""
    if not payload:
        return "The tool returned an empty result."
    pairs: list[str] = []
    for key, value in payload.items():
        summary = _summarize_mapping_field(key, value)
        if summary:
            pairs.append(summary)
    if not pairs:
        return "The tool returned details, but no reportable status fields."
    return "Tool result: " + "; ".join(pairs) + "."


def _is_component_health_field_name(field_name: str) -> bool:
    """Identify component-health fields across naming variations."""
    normalized = re.sub(r"[^a-z0-9]", "", str(field_name).strip().lower())
    return normalized == COMPONENT_HEALTH_NORMALIZED_KEY


def _is_null_like_scalar(value: Any) -> bool:
    """Return True when scalar payload values should be omitted from summaries."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in {"", "none", "null"}:
        return True
    return False


def normalize_input(state: BrokerState) -> BrokerState:
    """Normalize user text into a canonical state field.

    Why this approach:
    collapsing whitespace and stripping mentions gives downstream nodes a stable
    representation for keyword matching.

    Args:
        state: Mutable broker state carrying inbound message text.

    Returns:
        BrokerState: Updated state containing normalized text.
    """
    text = _strip_bot_mention(state.get(STATE_KEY_TEXT, ""))
    normalized = " ".join(text.split()).strip()
    state[STATE_KEY_NORMALIZED_TEXT] = normalized
    return state


def classify_intent(state: BrokerState) -> BrokerState:
    """Classify message intent and whether explicit confirmation is required.

    Why this approach:
    lightweight intent labels remain useful for diagnostics and session context
    without imposing execution control decisions at this stage.

    Args:
        state: Mutable broker state containing normalized user text.

    Returns:
        BrokerState: Updated state with command, intent, and confirmation flags.
    """
    text = state.get(STATE_KEY_NORMALIZED_TEXT, "").lower()
    parts = text.split()
    state[STATE_KEY_REQUIRES_CONFIRMATION] = False
    state[STATE_KEY_COMMAND] = parts[0] if parts else "help"

    if not text:
        state[STATE_KEY_INTENT] = "help"
    elif any(word in text for word in ["restart", "delete"]):
        state[STATE_KEY_INTENT] = "action"
    elif any(word in text for word in ["status", "health", "config", "tools", "help", "diff"]):
        state[STATE_KEY_INTENT] = "query"
    else:
        state[STATE_KEY_INTENT] = "diagnostic"
    return state


async def _refresh_tool_registry_names(
    *,
    state: BrokerState,
    tool_registry: MCPToolRegistry,
    offline_message: str,
) -> list[str] | None:
    """Return available tool names, handling registry refresh and offline fallbacks."""
    tool_names = tool_registry.list_names()
    if tool_names:
        return tool_names
    try:
        await tool_registry.refresh()
    except MCPServerUnavailableError as exc:
        logger.error(
            "MCP server unavailable during tool discovery: %s",
            exc,
            exc_info=True,
        )
        state[STATE_KEY_TOOLS_AVAILABLE] = []
        state[STATE_KEY_TOOL_NAME] = None
        state[STATE_KEY_TOOL_ARGS] = {}
        state[STATE_KEY_RESPONSE_TEXT] = offline_message
        return None
    except Exception:
        logger.exception("Unexpected error during MCP tool discovery refresh.")
    return tool_registry.list_names()


def _planner_tools(
    tool_registry: MCPToolRegistry,
    tool_names: list[str],
) -> list[dict[str, Any]]:
    """Build planner-visible tool metadata from the registry and discovered names."""
    return [
        tool_registry.get(name) or {PAYLOAD_KEY_NAME: name}
        for name in tool_names
    ]


def _conversation_history(state: BrokerState) -> list[Any]:
    """Normalize conversation history payload from broker state."""
    history = state.get(STATE_KEY_CONVERSATION_HISTORY, [])
    return history if isinstance(history, list) else []


async def _plan_with_rule_fallback(
    *,
    planner: Planner,
    text: str,
    tools: list[dict[str, Any]],
    conversation_history: list[Any],
) -> dict[str, Any] | None:
    """Run the configured planner and fall back to rule-first planning on failures."""
    try:
        return await planner.plan(
            text=text,
            tools=tools,
            conversation_history=conversation_history,
        )
    except Exception as exc:
        logger.exception(
            "Planner failed; falling back to rule-first planning. error=%s",
            exc,
        )
    try:
        return await RuleFirstPlanner().plan(
            text=text,
            tools=tools,
            conversation_history=conversation_history,
        )
    except Exception:
        logger.exception("Fallback planner failed unexpectedly.")
        return None


def _normalize_plan_selection(
    *,
    plan: dict[str, Any],
    tool_names: list[str],
    text: str,
) -> tuple[str | None, dict[str, Any], str | None, str | None]:
    """Normalize planner output into validated tool, args, and optional response text."""
    chosen_tool_raw = plan.get(TOOL_NAME_KEY)
    chosen_tool = str(chosen_tool_raw).strip() if isinstance(chosen_tool_raw, str) else ""
    if chosen_tool and chosen_tool not in tool_names:
        chosen_tool = ""
    chosen_args = _normalize_tool_args(plan.get(TOOL_ARGS_KEY, {}))
    if not chosen_tool:
        chosen_args = {}
    response_text_raw = plan.get(RESPONSE_TEXT_KEY, "")
    response_text = str(response_text_raw).strip() if isinstance(response_text_raw, str) else ""
    target = chosen_args.get(STATE_KEY_TARGET)
    if target is None:
        parts = text.split()
        target = parts[-1] if len(parts) > 1 else None
    normalized_target = str(target) if target is not None else None
    return (chosen_tool or None), chosen_args, (response_text or None), normalized_target


async def plan_action(
    state: BrokerState,
    tool_registry: MCPToolRegistry,
    planner: Planner,
    offline_message: str = DEFAULT_MCP_SERVER_OFFLINE_MESSAGE,
) -> BrokerState:
    """Use the runtime planner to map user text to a tool-constrained plan.

    Why this approach:
    planning is delegated to the LLM planner, but tool selection is validated
    against discovered MCP tools so execution remains strictly constrained.

    Args:
        state: Mutable broker state holding normalized user text.
        tool_registry: MCP registry providing discovered tool metadata.
        planner: Planner implementation (LLM or deterministic fallback).

    Returns:
        BrokerState: Updated state with response text and/or planned tool call.
    """
    text = state.get(STATE_KEY_NORMALIZED_TEXT, "")
    tool_names = await _refresh_tool_registry_names(
        state=state,
        tool_registry=tool_registry,
        offline_message=offline_message,
    )
    if tool_names is None:
        return state
    tools = _planner_tools(tool_registry, tool_names)

    state[STATE_KEY_TOOLS_AVAILABLE] = tool_names
    state[STATE_KEY_TOOL_NAME] = None
    state[STATE_KEY_TOOL_ARGS] = {}
    if apply_slash_command_overrides(state, tool_names):
        return state

    plan = await _plan_with_rule_fallback(
        planner=planner,
        text=text,
        tools=tools,
        conversation_history=_conversation_history(state),
    )
    if plan is None:
        state[STATE_KEY_TOOL_NAME] = None
        state[STATE_KEY_TOOL_ARGS] = {}
        state[STATE_KEY_RESPONSE_TEXT] = (
            "I hit an internal planning issue. Please try again in a moment."
        )
        return state

    chosen_tool, chosen_args, response_text, target = _normalize_plan_selection(
        plan=plan,
        tool_names=tool_names,
        text=text,
    )
    state[STATE_KEY_TOOL_NAME] = chosen_tool
    state[STATE_KEY_TOOL_ARGS] = chosen_args
    state[STATE_KEY_REQUIRES_CONFIRMATION] = False

    if response_text:
        state[STATE_KEY_RESPONSE_TEXT] = response_text
    elif not chosen_tool:
        state[STATE_KEY_RESPONSE_TEXT] = (
            "I couldn't map that to a known MCP tool yet. "
            "Ask for `tools` to see what I discovered."
        )
    state[STATE_KEY_TARGET] = target
    return state


def _ensure_initial_tool_name(state: BrokerState) -> str:
    """Extract and normalize the current selected tool name from state."""
    raw_value = state.get(STATE_KEY_TOOL_NAME)
    return str(raw_value).strip() if isinstance(raw_value, str) else ""


def _seed_unknown_tool_response(state: BrokerState) -> None:
    """Populate default unknown-tool response text when planner did not provide one."""
    if STATE_KEY_RESPONSE_TEXT not in state:
        state[STATE_KEY_RESPONSE_TEXT] = (
            "I couldn't map that to a known MCP tool yet. "
            "Ask for `tools` to see what I discovered."
        )


def _resolve_known_tool_names(
    *,
    state: BrokerState,
    tool_registry: MCPToolRegistry,
    current_tool_name: str,
) -> set[str]:
    """Resolve known tool names for follow-up planning with safe fallbacks."""
    available_tool_names = state.get(STATE_KEY_TOOLS_AVAILABLE, [])
    if not isinstance(available_tool_names, list):
        available_tool_names = []
    known_tool_names = {
        str(name).strip()
        for name in available_tool_names
        if str(name).strip()
    }
    if known_tool_names:
        return known_tool_names
    if not hasattr(tool_registry, "list_names"):
        return {current_tool_name}
    try:
        return {
            str(name).strip()
            for name in tool_registry.list_names()
            if str(name).strip()
        } or {current_tool_name}
    except Exception:
        logger.exception("Failed listing tools for follow-up planning.")
        return {current_tool_name}


async def _execute_tool_step(
    *,
    state: BrokerState,
    tool_registry: MCPToolRegistry,
    tool_name: str,
    tool_args: dict[str, Any],
    offline_message: str,
) -> tuple[bool, dict[str, Any], str]:
    """Execute one tool call and write default state updates for the returned result."""
    try:
        result = await tool_registry.call_tool(tool_name, tool_args)
    except MCPServerUnavailableError as exc:
        logger.error(
            "MCP server unavailable while calling tool %s: %s",
            tool_name,
            exc,
            exc_info=True,
        )
        state[STATE_KEY_TOOL_RESULT] = {PAYLOAD_KEY_ERROR: str(exc)}
        state[STATE_KEY_RESPONSE_TEXT] = offline_message
        return False, {}, ""
    default_response_text = _format_tool_response(tool_name, result)
    state[STATE_KEY_TOOL_NAME] = tool_name
    state[STATE_KEY_TOOL_ARGS] = tool_args
    state[STATE_KEY_TOOL_RESULT] = result
    state[STATE_KEY_RESPONSE_TEXT] = default_response_text
    return True, result, default_response_text


def _normalize_optional_text(value: Any) -> str:
    """Normalize optional planner values into trimmed text."""
    return str(value).strip() if isinstance(value, str) else str(value or "").strip()


def _apply_follow_up_plan(
    *,
    state: BrokerState,
    follow_up_plan: dict[str, Any],
    known_tool_names: set[str],
    current_tool_name: str,
    current_tool_args: dict[str, Any],
) -> tuple[bool, str, dict[str, Any]]:
    """Apply a follow-up plan and return whether execution should continue."""
    next_tool_name = _normalize_optional_text(follow_up_plan.get(TOOL_NAME_KEY))
    next_response_text = _normalize_optional_text(follow_up_plan.get(RESPONSE_TEXT_KEY, ""))
    if not next_tool_name:
        if next_response_text:
            state[STATE_KEY_RESPONSE_TEXT] = next_response_text
        return False, current_tool_name, current_tool_args
    if next_tool_name not in known_tool_names:
        state[STATE_KEY_RESPONSE_TEXT] = (
            next_response_text
            or f"I couldn't execute follow-up tool `{next_tool_name}` because it is not currently available."
        )
        return False, current_tool_name, current_tool_args
    next_tool_args = _normalize_tool_args(follow_up_plan.get(TOOL_ARGS_KEY, {}))
    if next_tool_name == current_tool_name and next_tool_args == current_tool_args:
        if next_response_text:
            state[STATE_KEY_RESPONSE_TEXT] = next_response_text
        return False, current_tool_name, current_tool_args
    next_target = next_tool_args.get(STATE_KEY_TARGET)
    if next_target is not None:
        state[STATE_KEY_TARGET] = str(next_target)
    return True, next_tool_name, next_tool_args


async def execute_or_summarize(
    state: BrokerState,
    tool_registry: MCPToolRegistry,
    offline_message: str = DEFAULT_MCP_SERVER_OFFLINE_MESSAGE,
    tool_response_formatter: ToolResponseFormatter | None = None,
    planner: Planner | None = None,
    max_planning_steps: int = PLANNER_MAX_EXECUTION_STEPS_DEFAULT,
) -> BrokerState:
    """Execute the selected tool call or produce a user-facing fallback message.

    Why this approach:
    this node centralizes final response rendering so all branches return a
    consistent ``response_text`` contract for Slack handlers.

    Args:
        state: Mutable broker state with planning outputs.
        tool_registry: MCP registry used to execute the selected tool.

    Returns:
        BrokerState: Updated state containing tool results and response text.
    """
    current_tool_name = _ensure_initial_tool_name(state)
    if not current_tool_name:
        _seed_unknown_tool_response(state)
        return state

    current_tool_args = _normalize_tool_args(state.get(STATE_KEY_TOOL_ARGS, {}))
    state[STATE_KEY_TOOL_ARGS] = current_tool_args

    normalized_user_text = str(state.get(STATE_KEY_NORMALIZED_TEXT, "")).strip()
    replanning_enabled = (
        planner is not None
        and not bool(state.get(STATE_KEY_API_COMMAND_MODE, False))
    )
    known_tool_names = (
        _resolve_known_tool_names(
            state=state,
            tool_registry=tool_registry,
            current_tool_name=current_tool_name,
        )
        if replanning_enabled
        else set()
    )

    max_steps = _normalize_planner_step_limit(max_planning_steps)
    step_count = 0
    final_result: dict[str, Any] = {}
    final_default_response_text = ""
    while True:
        step_count += 1
        executed, result, default_response_text = await _execute_tool_step(
            state=state,
            tool_registry=tool_registry,
            tool_name=current_tool_name,
            tool_args=current_tool_args,
            offline_message=offline_message,
        )
        if not executed:
            return state
        final_result = result
        final_default_response_text = default_response_text

        if not replanning_enabled or planner is None or step_count >= max_steps:
            break

        tools_for_replanning = _planner_tools(tool_registry, sorted(known_tool_names))
        follow_up_text = _build_follow_up_planner_text(
            user_text=normalized_user_text,
            tool_name=current_tool_name,
            tool_args=current_tool_args,
            tool_summary=final_default_response_text,
        )
        try:
            follow_up_plan = await planner.plan(
                text=follow_up_text,
                tools=tools_for_replanning,
                conversation_history=_conversation_history(state),
            )
        except Exception:
            logger.exception(
                "Planner follow-up step failed after tool execution; "
                "returning latest tool response."
            )
            break

        should_continue, next_tool_name, next_tool_args = _apply_follow_up_plan(
            state=state,
            follow_up_plan=follow_up_plan,
            known_tool_names=known_tool_names,
            current_tool_name=current_tool_name,
            current_tool_args=current_tool_args,
        )
        if not should_continue:
            break
        current_tool_name = next_tool_name
        current_tool_args = next_tool_args

    if tool_response_formatter is not None and final_result:
        try:
            formatted_response = await tool_response_formatter(
                user_text=normalized_user_text,
                tool_name=current_tool_name,
                tool_args=current_tool_args,
                tool_result=final_result,
                default_response_text=final_default_response_text,
            )
            if isinstance(formatted_response, str) and formatted_response.strip():
                state[STATE_KEY_RESPONSE_TEXT] = formatted_response.strip()
        except Exception:
            logger.exception(
                "AI formatter failed; returning default tool response text."
            )
    return state
