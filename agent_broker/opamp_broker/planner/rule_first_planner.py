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

"""Deterministic rule-first planner implementation."""

from __future__ import annotations

import re
from typing import Any

from opamp_broker.planner.constants import (
    REQUIRES_CONFIRMATION_KEY,
    RESPONSE_TEXT_KEY,
    TOOL_ARGS_KEY,
    TOOL_NAME_KEY,
)

BOOLEAN_TRUE_VALUES = {"1", "true", "yes", "on"}
BOOLEAN_FALSE_VALUES = {"0", "false", "no", "off"}
ARGUMENT_KEY_VALUE_PATTERN = re.compile(
    r"(?P<key>(?:--)?[A-Za-z_][A-Za-z0-9_.-]*)\s*(?:=|:)\s*"
    r"(?P<value>\"[^\"]*\"|'[^']*'|\S+)"
)
ARGUMENT_TOKEN_PATTERN = re.compile(r"\"[^\"]*\"|'[^']*'|\S+")
AGENT_LIST_QUERY_PATTERN = re.compile(
    r"\b(?:list|show|find|get|query)\b.*\b(?:agents|collectors|clients)\b"
)
AGENT_NOUN_PATTERN = re.compile(r"\b(?:agent|agents|collector|collectors|client|clients)\b")


class RuleFirstPlanner:
    """Deterministic fallback planner when LLM planning is unavailable."""

    async def plan(
        self,
        *,
        text: str,
        tools: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Create a tool-constrained plan using deterministic keyword rules.

        Why this planner exists:
        broker operations must continue even when LLM mode is disabled or not
        available, so we provide predictable command routing as a safe fallback.
        """
        del conversation_history
        tool_names, tool_lookup = _build_tool_index(tools)
        normalized = text.strip().lower()
        target = _extract_default_target(text)

        direct_plan = _plan_for_direct_tool(
            text=text,
            tool_names=tool_names,
            tool_lookup=tool_lookup,
        )
        if direct_plan is not None:
            return direct_plan

        if _is_tool_catalog_request(normalized):
            return _build_response_only_plan(_format_tool_catalog(tools))
        if _is_help_request(normalized):
            return _build_response_only_plan(_default_help_text())

        prefix_plan = _plan_for_prefixed_action(
            normalized=normalized,
            tool_names=tool_names,
            target=target,
        )
        if prefix_plan is not None:
            return prefix_plan

        otel_plan = _plan_for_otel_agent_listing(
            text=text,
            tool_names=tool_names,
            tool_lookup=tool_lookup,
        )
        if otel_plan is not None:
            return otel_plan

        return _build_default_status_plan(tool_names=tool_names, target=target)


def _build_tool_index(tools: list[dict[str, Any]]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Build ordered tool names plus lookup map for normalized planner access."""
    tool_names = [str(tool.get("name", "")).strip() for tool in tools]
    tool_lookup = {
        str(tool.get("name", "")).strip(): tool
        for tool in tools
        if str(tool.get("name", "")).strip()
    }
    return tool_names, tool_lookup


def _extract_default_target(text: str) -> str | None:
    """Extract fallback target as final token when present."""
    parts = text.split()
    return parts[-1] if len(parts) > 1 else None


def _plan_for_direct_tool(
    *,
    text: str,
    tool_names: list[str],
    tool_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Plan explicit direct tool invocation when user references tool name."""
    direct_tool = _find_direct_tool_request(text=text, tool_names=tool_names)
    if direct_tool is None:
        return None
    direct_args = _extract_tool_arguments(
        text=text,
        tool_name=direct_tool,
        tool=tool_lookup.get(direct_tool),
        scoped_to_direct_invocation=True,
    )
    if not direct_args:
        direct_target = _extract_direct_target(text=text, tool_name=direct_tool)
        if direct_target:
            direct_args = {"target": direct_target}
    return _build_tool_plan(tool_name=direct_tool, tool_args=direct_args)


def _is_tool_catalog_request(normalized: str) -> bool:
    """Return True when user asks for available tools/capabilities."""
    return any(
        phrase in normalized
        for phrase in (
            "tools",
            "available tools",
            "what can you do",
            "capabilities",
            "commands",
        )
    )


def _is_help_request(normalized: str) -> bool:
    """Return True for help or blank requests."""
    return "help" in normalized or not normalized


def _default_help_text() -> str:
    """Return static help guidance for fallback planner responses."""
    return (
        "Try `/opamp help`, `/opamp tools`, `/opamp opstate`, or use "
        "`/opamp call <tool_name> [key=value ...]` to run a specific tool."
    )


def _plan_for_prefixed_action(
    *,
    normalized: str,
    tool_names: list[str],
    target: str | None,
) -> dict[str, Any] | None:
    """Resolve prefix-led requests like `status ...` or `restart ...`."""
    for prefix, tool_hint in [
        ("status", "status"),
        ("health", "health"),
        ("config", "config"),
        ("diff", "diff"),
        ("restart", "restart"),
    ]:
        if not normalized.startswith(prefix):
            continue
        chosen = next((name for name in tool_names if tool_hint in name.lower()), None)
        return _build_tool_plan(
            tool_name=chosen,
            tool_args={"target": target} if (chosen and target) else {},
        )
    return None


def _plan_for_otel_agent_listing(
    *,
    text: str,
    tool_names: list[str],
    tool_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Resolve natural-language list/find agent requests to otel agents tool."""
    otel_agents_tool = _find_otel_agents_tool_name(tool_names)
    if not otel_agents_tool or not _looks_like_agent_list_query(text):
        return None
    tool_args = _extract_tool_arguments(
        text=text,
        tool_name=otel_agents_tool,
        tool=tool_lookup.get(otel_agents_tool),
        scoped_to_direct_invocation=False,
    )
    return _build_tool_plan(tool_name=otel_agents_tool, tool_args=tool_args)


def _build_default_status_plan(*, tool_names: list[str], target: str | None) -> dict[str, Any]:
    """Build fallback plan preferring health then status tools."""
    chosen = next((name for name in tool_names if "health" in name.lower()), None) or next(
        (name for name in tool_names if "status" in name.lower()),
        None,
    )
    return _build_tool_plan(
        tool_name=chosen,
        tool_args={"target": target} if (chosen and target) else {},
    )


def _build_response_only_plan(response_text: str) -> dict[str, Any]:
    """Build a planner result that only returns text (no tool execution)."""
    return {
        RESPONSE_TEXT_KEY: response_text,
        TOOL_NAME_KEY: None,
        TOOL_ARGS_KEY: {},
        REQUIRES_CONFIRMATION_KEY: False,
    }


def _build_tool_plan(*, tool_name: str | None, tool_args: dict[str, Any]) -> dict[str, Any]:
    """Build a planner result that executes a tool."""
    return {
        RESPONSE_TEXT_KEY: "",
        TOOL_NAME_KEY: tool_name,
        TOOL_ARGS_KEY: tool_args,
        REQUIRES_CONFIRMATION_KEY: False,
    }


def _format_tool_catalog(tools: list[dict[str, Any]]) -> str:
    """Render a human-readable summary of discovered tools.

    Why: users often ask capability questions before issuing commands.
    """
    usable_tools = [tool for tool in tools if str(tool.get("name", "")).strip()]
    if not usable_tools:
        return (
            "I can use MCP tools to help, but I haven't discovered any yet. "
            "Please check that the OpAMP provider is online."
        )

    lines = ["Available MCP tools:"]
    for tool in sorted(usable_tools, key=lambda item: str(item.get("name", ""))):
        lines.append(_format_tool_line(tool))
    lines.append(
        "Tell me what you want to do and the target, for example: "
        "`status collector-a` or `health collector-a`."
    )
    return "\n".join(lines)


def _format_tool_line(tool: dict[str, Any]) -> str:
    """Render one tool with purpose and argument hints.

    Why: concise per-tool hints reduce trial-and-error in chat interactions.
    """
    name = str(tool.get("name", "")).strip()
    description = str(tool.get("description", "")).strip() or "No description provided."
    args_hint = _format_args_hint(tool.get("inputSchema", {}))
    if args_hint:
        return f"- `{name}`: {description}. Args: {args_hint}"
    return f"- `{name}`: {description}. Args: none."


def _format_args_hint(input_schema: Any) -> str:
    """Build concise argument guidance from a JSON Schema-like object.

    Why: rule-first help text should reflect live tool schemas, not hardcoded args.
    """
    if not isinstance(input_schema, dict):
        return ""
    properties = input_schema.get("properties")
    if not isinstance(properties, dict) or not properties:
        return ""

    required_values = input_schema.get("required", [])
    required = {
        str(value).strip()
        for value in required_values
        if isinstance(value, str) and value.strip()
    }
    rendered: list[str] = []
    for name, schema in properties.items():
        field_name = str(name).strip()
        if not field_name:
            continue
        field_type = ""
        if isinstance(schema, dict):
            raw_type = schema.get("type")
            if isinstance(raw_type, str) and raw_type.strip():
                field_type = raw_type.strip()
        suffix = "required" if field_name in required else "optional"
        if field_type:
            rendered.append(f"{field_name} ({field_type}, {suffix})")
        else:
            rendered.append(f"{field_name} ({suffix})")
    return ", ".join(rendered)


def _find_direct_tool_request(text: str, tool_names: list[str]) -> str | None:
    """Return explicitly requested tool name when user types a tool identifier.

    Why: explicit tool invocations should bypass heuristic intent matching.
    """
    normalized = text.strip().lower()
    if not normalized:
        return None

    for name in tool_names:
        stripped_name = name.strip()
        if not stripped_name:
            continue
        lowered_name = stripped_name.lower()
        if normalized == lowered_name:
            return stripped_name
        if normalized.startswith(f"{lowered_name} "):
            return stripped_name
        if re.search(rf"\b{re.escape(lowered_name)}\b", normalized):
            return stripped_name
    return None


def _extract_direct_target(text: str, tool_name: str) -> str | None:
    """Extract a simple trailing target token from direct tool invocation text.

    Why: many operational commands follow `tool_name target` shorthand patterns.
    """
    pattern = re.compile(rf"^\s*{re.escape(tool_name)}\s+(?P<target>\S+)")
    match = pattern.search(text)
    if not match:
        return None
    target = match.group("target").strip()
    return target if target else None


def _find_otel_agents_tool_name(tool_names: list[str]) -> str | None:
    """Return the best discovered tool name for listing/filtering agents.

    Why: deployments may expose different agent-list tool names.
    """
    for name in tool_names:
        if "otel_agents" in name.lower():
            return name
    for name in tool_names:
        lowered = name.lower()
        if "agent" in lowered and "tool" in lowered:
            return name
    return None


def _looks_like_agent_list_query(text: str) -> bool:
    """Determine whether free text likely intends an agent listing/filter request.

    Why: filtering/listing requests are common and should auto-route correctly.
    """
    normalized = text.strip().lower()
    if not normalized:
        return False
    if normalized in {"agents", "collectors", "clients"}:
        return True
    if AGENT_LIST_QUERY_PATTERN.search(normalized):
        return True
    return bool(AGENT_NOUN_PATTERN.search(normalized) and ARGUMENT_KEY_VALUE_PATTERN.search(text))


def _extract_tool_arguments(
    *,
    text: str,
    tool_name: str,
    tool: dict[str, Any] | None,
    scoped_to_direct_invocation: bool,
) -> dict[str, Any]:
    """Extract schema-aware tool arguments from user text.

    Arguments are accepted as ``key=value`` (or ``key:value``) tokens and only
    mapped when they match the discovered tool schema. This keeps rule-first
    behavior aligned with the currently available tool options.
    """
    scope_text = text
    if scoped_to_direct_invocation:
        invocation_pattern = re.compile(rf"^\s*{re.escape(tool_name)}\b", re.IGNORECASE)
        match = invocation_pattern.search(scope_text)
        if not match:
            return {}
        scope_text = scope_text[match.end():]
    scope_text = scope_text.strip()
    if not scope_text:
        return {}

    properties = _extract_input_schema_properties(tool)
    parsed = _extract_key_value_arguments(scope_text, properties)

    if "invert_filter" in properties and "invert_filter" not in parsed:
        lowered_scope = scope_text.lower()
        if re.search(r"\bexclude\b", lowered_scope):
            parsed["invert_filter"] = True
        elif parsed and re.search(r"\bshow\b", lowered_scope):
            parsed["invert_filter"] = False

    if not parsed and "target" in properties:
        positional_target = _extract_first_positional_token(scope_text)
        if positional_target:
            parsed["target"] = positional_target
    return parsed


def _extract_input_schema_properties(tool: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Return normalized ``inputSchema.properties`` mapping for a tool.

    Why: schema-aware parsing avoids sending unsupported tool arguments.
    """
    if not isinstance(tool, dict):
        return {}
    input_schema = tool.get("inputSchema")
    if not isinstance(input_schema, dict):
        return {}
    raw_properties = input_schema.get("properties")
    if not isinstance(raw_properties, dict):
        return {}
    properties: dict[str, dict[str, Any]] = {}
    for key, value in raw_properties.items():
        key_text = str(key).strip()
        if not key_text:
            continue
        properties[key_text] = value if isinstance(value, dict) else {}
    return properties


def _extract_key_value_arguments(
    text: str,
    properties: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Extract ``key=value`` tokens and coerce values using schema metadata.

    Why: users naturally type CLI-like args in Slack commands and free text.
    """
    parsed: dict[str, Any] = {}
    for match in ARGUMENT_KEY_VALUE_PATTERN.finditer(text):
        raw_key = str(match.group("key") or "").strip().lstrip("-")
        raw_value = _strip_wrapping_quotes(str(match.group("value") or "").strip())
        if not raw_key or not raw_value:
            continue
        resolved_key = _resolve_argument_key(raw_key, properties)
        if resolved_key is None:
            if properties:
                continue
            resolved_key = raw_key
        parsed[resolved_key] = _coerce_argument_value(
            raw_value,
            properties.get(resolved_key, {}),
        )
    return parsed


def _resolve_argument_key(raw_key: str, properties: dict[str, dict[str, Any]]) -> str | None:
    """Resolve a user-provided argument name to one schema property key.

    Why: forgiving key matching (hyphen/underscore/case) improves UX.
    """
    if not properties:
        return raw_key

    normalized_lookup = {
        _normalize_argument_name(name): name
        for name in properties
        if _normalize_argument_name(name)
    }
    normalized_key = _normalize_argument_name(raw_key)
    if not normalized_key:
        return None
    if normalized_key in normalized_lookup:
        return normalized_lookup[normalized_key]

    suffix_matches = {
        name
        for normalized_name, name in normalized_lookup.items()
        if normalized_name.endswith(normalized_key)
        or normalized_key.endswith(normalized_name)
    }
    if len(suffix_matches) == 1:
        return next(iter(suffix_matches))
    return None


def _normalize_argument_name(value: str) -> str:
    """Normalize argument names for forgiving matching across separators/casing.

    Why: argument names from users and schemas may differ in punctuation/case.
    """
    return re.sub(r"[^a-z0-9]", "", str(value).strip().lower())


def _strip_wrapping_quotes(value: str) -> str:
    """Remove one pair of matching leading/trailing quotes.

    Why: quoted values are common in chat commands with spaces/special chars.
    """
    stripped = value.strip()
    if len(stripped) < 2:
        return stripped
    if (
        (stripped.startswith('"') and stripped.endswith('"'))
        or (stripped.startswith("'") and stripped.endswith("'"))
    ):
        return stripped[1:-1]
    return stripped


def _coerce_argument_value(raw_value: str, schema: dict[str, Any]) -> Any:
    """Coerce user text to primitive schema type when safe.

    Why: tool inputs should preserve intended types (bool/int/float) when possible.
    """
    arg_type = str(schema.get("type", "")).strip().lower() if schema else ""
    if arg_type == "boolean":
        normalized = raw_value.strip().lower()
        if normalized in BOOLEAN_TRUE_VALUES:
            return True
        if normalized in BOOLEAN_FALSE_VALUES:
            return False
        return raw_value
    if arg_type == "integer":
        try:
            return int(raw_value, 10)
        except ValueError:
            return raw_value
    if arg_type == "number":
        try:
            return float(raw_value)
        except ValueError:
            return raw_value
    return raw_value


def _extract_first_positional_token(text: str) -> str | None:
    """Return first non-key=value token from a command tail.

    Why: many tools accept a primary positional `target` in addition to flags.
    """
    for token in ARGUMENT_TOKEN_PATTERN.findall(text):
        candidate = _strip_wrapping_quotes(token.strip())
        if not candidate:
            continue
        if ARGUMENT_KEY_VALUE_PATTERN.fullmatch(candidate):
            continue
        if "=" in candidate or ":" in candidate:
            continue
        return candidate
    return None
