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

"""Slack event and command handlers that drive broker conversation flow.

This module adapts Slack payloads into graph state, updates session snapshots,
and emits thread responses with a consistent output contract.
"""

from __future__ import annotations

import json
import logging
import random
import re
import shlex
from contextlib import suppress
from datetime import datetime, timezone
from typing import Any

import httpx
from slack_bolt.async_app import AsyncApp

from opamp_broker.graph.state import (
    STATE_KEY_AI_ENABLED,
    STATE_KEY_API_COMMAND_MODE,
    STATE_KEY_CHANNEL_ID,
    STATE_KEY_CONVERSATION_HISTORY,
    STATE_KEY_DIRECT_TOOL_ARGS,
    STATE_KEY_DIRECT_TOOL_NAME,
    STATE_KEY_INTENT,
    STATE_KEY_TARGET,
    STATE_KEY_TEAM_ID,
    STATE_KEY_TEXT,
    STATE_KEY_THREAD_TS,
    STATE_KEY_USER_ID,
)
from opamp_broker.planner.openai_compatible_connection import (
    OpenAICompatibleConnection,
)
from opamp_broker.session.manager import (
    AI_MODE_DISABLED,
    AI_MODE_OFF,
    AI_MODE_ON,
    SessionManager,
)

logger = logging.getLogger(__name__)
CONFIG_KEY_MESSAGES = "messages"
CONFIG_KEY_SLACK = "slack"
CONFIG_KEY_COMMAND_NAME = "command_name"
MESSAGE_KEY_HELP = "help"
MESSAGE_KEY_IMMEDIATE_ACK_MESSAGES = "immediate_ack_messages"
MESSAGE_KEY_SLACK_ERROR_REPLY = "slack_error_reply"
MESSAGE_KEY_AI_MODE_OFF_ACK_TEXT = "ai_mode_off_ack_text"
SLACK_KEY_EVENT = "event"
SLACK_KEY_TEAM_ID = "team_id"
SLACK_KEY_TEAM = "team"
SLACK_KEY_ID = "id"
SLACK_KEY_AUTHORIZATIONS = "authorizations"
SLACK_KEY_CHANNEL = "channel"
SLACK_KEY_CHANNEL_ID = "channel_id"
SLACK_KEY_THREAD_TS = "thread_ts"
SLACK_KEY_TS = "ts"
SLACK_KEY_TRIGGER_ID = "trigger_id"
SLACK_KEY_USER = "user"
SLACK_KEY_USER_ID = "user_id"
SLACK_KEY_TEXT = "text"
SLACK_KEY_CHANNEL_TYPE = "channel_type"
SLACK_KEY_RESPONSE_TEXT = "response_text"
SLACK_KEY_ENVIRONMENT = "environment"
SLACK_KEY_UNKNOWN = "unknown"
SLACK_KEY_NO_THREAD = "no-thread"
SLACK_KEY_IN_CHANNEL = "in_channel"
SLACK_CHANNEL_TYPE_IM = "im"
AI_MODE_OFF_EXACT_COMMAND = "ai off"
AI_MODE_ON_EXACT_COMMAND = "ai on"
AI_MODE_OFF_ACK_TEXT = "Affirmative, Dave. I read you."
AI_MODE_DISABLED_LOCK_TEXT = (
    "AI is disabled and can't be changed."
)
AI_MODE_PREFIX_PATTERN = re.compile(r"^\s*ai\s+(on|off)\b[:\s,-]*(.*)$", re.IGNORECASE)
SLASH_PREFIX = "/"
API_ROOT_OPAMP = "/opamp"
API_ROOT_SHORT = "/api"
API_LEGACY_NAMESPACE = "api"
API_VERB_HELP = "help"
API_VERB_TOOLS = "tools"
API_VERB_CALL = "call"
API_VERB_OPSTATE = "opstate"
LOG_KEY_EVENT = "event"
LOG_KEY_CONTEXT = "context"
LOG_KEY_COMMAND = "command"
LOG_KEY_ROUTE = "route"
CONVERSATION_HISTORY_MAX_MESSAGES = 12
HISTORY_ROLE_USER = "user"
HISTORY_ROLE_ASSISTANT = "assistant"
HISTORY_ROLE_SYSTEM = "system"
PROVIDER_HTTP_PROBE_TIMEOUT_SECONDS = 5
DEFAULT_PROCESSING_ACK_MESSAGES = (
    "ok",
    "let me think",
    "hmmmm",
    "ack",
    "working on it",
)
API_COMMAND_UNHANDLED_MESSAGE = (
    "I couldn't complete that `/opamp` command. Run `/opamp help` for syntax."
)
USER_FACING_STUMBLE_REPLY = "sorry, I stumbled, you might want to try that again"
BROKER_STARTED_AT_UTC_ISO = datetime.now(timezone.utc).isoformat()
API_USAGE_TEXT = (
    "Usage:\n"
    "`/opamp help [syntax|tools|call|opstate|<tool_name>]`\n"
    "`/opamp tools [filter_text]`\n"
    "`/opamp opstate`\n"
    "`/opamp call <tool_name> [key=value ...]`\n"
    "`/opamp call <tool_name> --json '{\"key\":\"value\"}'`"
)


def _build_non_thread_session_scope(user_id: str | None) -> str:
    """Build a deterministic session scope for non-thread channel exchanges."""
    normalized_user_id = str(user_id or "").strip() or SLACK_KEY_UNKNOWN
    return f"{SLACK_KEY_NO_THREAD}:{normalized_user_id}"


def _derive_session_thread_ts(
    *,
    reply_thread_ts: str | None,
    user_id: str | None,
) -> str:
    """Return session scope id, preserving real thread ts when present."""
    normalized_thread_ts = str(reply_thread_ts or "").strip()
    if normalized_thread_ts:
        return normalized_thread_ts
    return _build_non_thread_session_scope(user_id)

def _normalize_conversation_history(
    history_raw: Any,
) -> list[dict[str, str]]:
    """Return validated bounded conversation history entries for planner context."""
    if not isinstance(history_raw, list):
        return []

    history: list[dict[str, str]] = []
    for message in history_raw:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role", "")).strip().lower()
        if role not in {HISTORY_ROLE_USER, HISTORY_ROLE_ASSISTANT, HISTORY_ROLE_SYSTEM}:
            continue
        content = str(message.get("content", "")).strip()
        if not content:
            continue
        history.append({"role": role, "content": content})
    if len(history) > CONVERSATION_HISTORY_MAX_MESSAGES:
        return history[-CONVERSATION_HISTORY_MAX_MESSAGES:]
    return history


def _build_planner_history(session: Any) -> list[dict[str, str]]:
    """Extract normalized planner history payload from one session object."""
    return _normalize_conversation_history(
        getattr(session, "conversation_history", []),
    )


def _append_conversation_turn(
    history: list[dict[str, str]],
    *,
    user_text: str,
    assistant_text: str,
) -> list[dict[str, str]]:
    """Append a user/assistant turn pair and enforce max retained history length."""
    updated = list(history)
    normalized_user_text = str(user_text).strip()
    normalized_assistant_text = str(assistant_text).strip()
    if normalized_user_text:
        updated.append({"role": HISTORY_ROLE_USER, "content": normalized_user_text})
    if normalized_assistant_text:
        updated.append(
            {"role": HISTORY_ROLE_ASSISTANT, "content": normalized_assistant_text}
        )
    if len(updated) > CONVERSATION_HISTORY_MAX_MESSAGES:
        return updated[-CONVERSATION_HISTORY_MAX_MESSAGES:]
    return updated


def _log_selected_route(
    *,
    route: str,
    team_id: str,
    channel_id: str,
    thread_ts: str,
    user_id: str | None,
) -> None:
    """Log the selected Slack handling route for traceability."""
    logger.info(
        "==== Slack route selected: %s ====",
        route,
        extra={
            LOG_KEY_EVENT: "slack.handlers.route_selected",
            LOG_KEY_CONTEXT: {
                SLACK_KEY_TEAM_ID: team_id,
                SLACK_KEY_CHANNEL_ID: channel_id,
                SLACK_KEY_THREAD_TS: thread_ts,
                SLACK_KEY_USER_ID: user_id or SLACK_KEY_UNKNOWN,
                LOG_KEY_ROUTE: route,
            },
        },
    )


def _extract_ai_mode_directive(text: str) -> tuple[str | None, str]:
    """Parse optional `AI On`/`AI Off` prefix and return remaining text."""
    candidate = str(text).strip()
    if not candidate:
        return None, ""
    match = AI_MODE_PREFIX_PATTERN.match(candidate)
    if match is None:
        return None, candidate
    toggle = (
        AI_MODE_ON
        if str(match.group(1)).strip().lower() == AI_MODE_ON
        else AI_MODE_OFF
    )
    remainder = str(match.group(2)).strip()
    return toggle, remainder


def _normalize_mode_command_text(text: str) -> str:
    candidate = re.sub(r"<@[^>]+>", "", str(text or ""))
    return " ".join(candidate.split()).strip().lower()


def _resolve_session_ai_mode(session: Any) -> str:
    """Return normalized session AI mode with compatibility fallback."""
    ai_mode = str(getattr(session, "ai_mode", "")).strip().lower()
    if ai_mode in {AI_MODE_ON, AI_MODE_OFF, AI_MODE_DISABLED}:
        return ai_mode
    return AI_MODE_ON if bool(getattr(session, "ai_enabled", True)) else AI_MODE_OFF


def _is_ai_mode_ui_switch_allowed(ai_mode: str) -> bool:
    """Return whether UI mode switches are allowed for the current mode."""
    return ai_mode != AI_MODE_DISABLED


def _build_ai_mode_changed_text(ai_mode: str) -> str:
    if ai_mode == AI_MODE_ON:
        return (
            "AI mode is now ON for this client. "
            "Subsequent messages will use the LLM path."
        )
    if ai_mode == AI_MODE_DISABLED:
        return AI_MODE_DISABLED_LOCK_TEXT
    return (
        "AI mode is now OFF for this client. "
        "Subsequent messages will use the non-AI path."
    )


def _resolve_processing_ack_messages(
    message_config: dict[str, Any],
) -> tuple[str, ...]:
    """Return configured immediate ack phrases with a safe default fallback."""
    configured_value = message_config.get(MESSAGE_KEY_IMMEDIATE_ACK_MESSAGES, [])
    if isinstance(configured_value, list):
        normalized = tuple(
            str(item).strip()
            for item in configured_value
            if str(item).strip()
        )
        if normalized:
            return normalized
    return DEFAULT_PROCESSING_ACK_MESSAGES


def _build_processing_ack_text(processing_ack_messages: tuple[str, ...]) -> str:
    """Return a short randomized acknowledgement for inbound requests."""
    return random.choice(processing_ack_messages)  # noqa: S311


def _resolve_ai_mode_off_ack_text(message_config: dict[str, Any]) -> str:
    """Return configured AI-off acknowledgement text with safe fallback."""
    configured_value = str(
        message_config.get(
            MESSAGE_KEY_AI_MODE_OFF_ACK_TEXT,
            AI_MODE_OFF_ACK_TEXT,
        )
    ).strip()
    return configured_value or AI_MODE_OFF_ACK_TEXT

def _build_api_help_text(topic: str | None = None) -> str:
    topic_normalized = str(topic or "").strip().lower()
    if topic_normalized in {"syntax", ""}:
        return (
            "Strict slash-command mode for OpAMP.\n"
            f"{API_USAGE_TEXT}\n"
            "Tip: run `/opamp tools` to discover callable tool names."
        )
    if topic_normalized == API_VERB_TOOLS:
        return (
            "`/opamp tools [filter_text]`\n"
            "Lists discovered tools. Optional filter narrows output."
        )
    if topic_normalized == API_VERB_CALL:
        return (
            "`/opamp call <tool_name> [key=value ...]`\n"
            "`/opamp call <tool_name> --json '{\"key\":\"value\"}'`\n"
            "Use either key/value tokens or --json, not both."
        )
    if topic_normalized == API_VERB_OPSTATE:
        return (
            "`/opamp opstate`\n"
            "Shows whether AI mode is ON/OFF/DISABLED for this client and checks "
            "server reachability using the returned HTTP status code."
        )
    return (
        f"Help for `{topic_normalized}`: run `/opamp tools {topic_normalized}` "
        "to locate the tool, then call it using `/opamp call ...`.\n"
        f"{API_USAGE_TEXT}"
    )


def _filter_tools_response(response_text: str, filter_text: str) -> str:
    query = str(filter_text).strip().lower()
    if not query:
        return response_text
    lines = [line for line in response_text.splitlines() if line.strip()]
    tool_lines = [line for line in lines if line.strip().startswith("- `")]
    if not tool_lines:
        return response_text
    matched = [line for line in tool_lines if query in line.lower()]
    if not matched:
        return (
            f"No tools matched filter `{filter_text}`.\n"
            "Tip: run `/opamp tools` to see all tools."
        )
    return "Available MCP tools (filtered):\n" + "\n".join(matched)


def _parse_api_call_args(raw_tokens: list[str]) -> tuple[dict[str, Any] | None, str | None]:
    if not raw_tokens:
        return {}, None

    if "--json" in raw_tokens:
        json_index = raw_tokens.index("--json")
        if len(raw_tokens) != 2 or json_index != 0:
            return None, "Use either key=value arguments or `--json`, not both."
        try:
            payload = json.loads(raw_tokens[1])
        except json.JSONDecodeError as exc:
            return None, f"Invalid JSON for `--json`: {exc.msg}."
        if not isinstance(payload, dict):
            return None, "`--json` payload must decode to a JSON object."
        return payload, None

    parsed: dict[str, Any] = {}
    for token in raw_tokens:
        if "=" not in token:
            return None, f"Invalid argument `{token}`. Expected `key=value`."
        key, value = token.split("=", 1)
        key_name = key.strip()
        if not key_name:
            return None, f"Invalid argument `{token}`. Key cannot be empty."
        parsed[key_name] = value
    return parsed, None


def _parse_api_command(text: str) -> dict[str, Any] | None:
    """Parse strict slash command-mode operations.

    Primary syntax is `/opamp <verb> ...`; legacy `/opamp api <verb> ...` is
    still accepted for compatibility.
    """
    normalized = str(text or "").strip()
    if not normalized or not normalized.startswith(SLASH_PREFIX):
        return None

    tokens, parse_error = _parse_api_command_tokens(normalized)
    if parse_error:
        return {"api_mode": True, "error": parse_error}
    if not tokens:
        return {
            "api_mode": True,
            "error": API_USAGE_TEXT,
        }

    index = _resolve_api_command_index(tokens)
    if index is None:
        return {
            "api_mode": True,
            "error": "Unsupported slash syntax. Use `/opamp <help|tools|opstate|call> ...`.",
        }

    if len(tokens) <= index:
        return {
            "api_mode": True,
            "immediate_response": _build_api_help_text(),
        }

    verb = tokens[index].strip().lower()
    tail = tokens[index + 1 :]
    return _parse_api_command_verb(verb=verb, tail=tail)


def _parse_api_command_tokens(normalized: str) -> tuple[list[str], str | None]:
    """Split API command text into shell-like tokens with user-friendly errors."""
    try:
        return shlex.split(normalized), None
    except ValueError as exc:
        return [], f"Invalid command quoting: {exc}."


def _resolve_api_command_index(tokens: list[str]) -> int | None:
    """Resolve verb index for supported command roots, including legacy namespace."""
    first = tokens[0].strip().lower()
    if first == API_ROOT_SHORT:
        return 1
    if first != API_ROOT_OPAMP:
        return None
    if len(tokens) > 1 and tokens[1].strip().lower() == API_LEGACY_NAMESPACE:
        return 2
    return 1


def _parse_api_command_verb(*, verb: str, tail: list[str]) -> dict[str, Any]:
    """Parse a specific slash-command verb payload."""
    if verb == API_VERB_HELP:
        topic = tail[0] if tail else ""
        return {
            "api_mode": True,
            "immediate_response": _build_api_help_text(topic),
        }
    if verb == API_VERB_TOOLS:
        return _build_tools_api_request(tail)
    if verb == API_VERB_OPSTATE:
        return {"api_mode": True, "verb": API_VERB_OPSTATE}
    if verb == API_VERB_CALL:
        return _build_call_api_request(tail)
    return {
        "api_mode": True,
        "error": f"Unsupported verb `{verb}`.\n{API_USAGE_TEXT}",
    }


def _build_tools_api_request(tail: list[str]) -> dict[str, Any]:
    """Build parsed payload for `/opamp tools` command mode requests."""
    # Normalize bare `/opamp tools` to the same internal shape as a
    # trailing-space form (`/opamp tools `) so both inputs behave identically.
    tools_filter = " ".join(tail).strip() if tail else " "
    return {
        "api_mode": True,
        "verb": API_VERB_TOOLS,
        "planner_text": "tools",
        "tools_filter": tools_filter,
    }


def _build_call_api_request(tail: list[str]) -> dict[str, Any]:
    """Build parsed payload for `/opamp call <tool>` requests."""
    if not tail:
        return {
            "api_mode": True,
            "error": "Missing tool name.\n" + API_USAGE_TEXT,
        }
    tool_name = str(tail[0]).strip()
    if not tool_name:
        return {
            "api_mode": True,
            "error": "Missing tool name.\n" + API_USAGE_TEXT,
        }
    tool_args, parse_error = _parse_api_call_args(tail[1:])
    if parse_error:
        return {
            "api_mode": True,
            "error": f"{parse_error}\n{API_USAGE_TEXT}",
        }
    return {
        "api_mode": True,
        "verb": API_VERB_CALL,
        "planner_text": tool_name,
        "direct_tool_name": tool_name,
        "direct_tool_args": tool_args or {},
    }


def register_handlers(
    app: AsyncApp,
    session_manager: SessionManager,
    compiled_graph: Any,
    config: dict[str, Any],
) -> None:
    """Register slash-command, mention, and DM handlers on the Slack app.

    Why this approach:
    colocating registration keeps shared helpers (session updates and graph
    invocation) close to the handlers that use them.

    Args:
        app: Slack Bolt async application receiving events.
        session_manager: Session storage used to persist thread context.
        compiled_graph: LangGraph runnable used to process user requests.
        config: Runtime broker configuration including message templates.

    Returns:
        None: Handlers are registered by side effect on ``app``.
    """
    message_config = (
        config.get(CONFIG_KEY_MESSAGES, {})
        if isinstance(config, dict)
        else {}
    )
    help_text = str(
        message_config.get(
            MESSAGE_KEY_HELP,
            "Try `/opamp help`, `/opamp tools`, `/opamp opstate`, "
            "or mention me with a question.",
        )
    )
    slack_error_reply = str(
        message_config.get(
            MESSAGE_KEY_SLACK_ERROR_REPLY,
            USER_FACING_STUMBLE_REPLY,
        )
    ).strip() or USER_FACING_STUMBLE_REPLY
    processing_ack_messages = _resolve_processing_ack_messages(message_config)
    ai_mode_off_ack_text = _resolve_ai_mode_off_ack_text(message_config)
    # Always return one consistent fallback sentence for unhandled exceptions.
    # Keep `slack_error_reply` loaded for config compatibility, but don't expose
    # exception details or variable wording to end users.
    del slack_error_reply
    provider_routes = (
        config.get("derived", {}).get("provider_routes", {})
        if isinstance(config.get("derived", {}), dict)
        else {}
    )
    provider_base_url = (
        str(provider_routes.get("base_url", "")).strip().rstrip("/")
        if isinstance(provider_routes, dict)
        else ""
    )
    provider_probe_url = f"{provider_base_url}/tool" if provider_base_url else ""

    async def _probe_provider_http_status() -> tuple[int | None, str | None]:
        """Return provider HTTP status code to validate broker-to-server reachability."""
        if not provider_probe_url:
            return None, "provider base URL is not configured"
        try:
            async with httpx.AsyncClient(
                timeout=PROVIDER_HTTP_PROBE_TIMEOUT_SECONDS,
                follow_redirects=True,
            ) as client:
                response = await client.get(provider_probe_url)
            return int(response.status_code), None
        except httpx.RequestError as exc:
            logger.exception(
                "provider connectivity probe failed for url=%s",
                provider_probe_url,
                exc_info=exc,
            )
            return None, None

    def _build_opstate_status_response_text(
        *,
        ai_mode: str,
        http_status_code: int | None,
        http_error: str | None,
    ) -> str:
        """Build strict command-mode status output for `/opamp opstate`."""
        lines = [
            "Broker opstate status:",
            f"- AI mode (per client): {str(ai_mode or AI_MODE_OFF).upper()}",
            f"- Broker started at (UTC): {BROKER_STARTED_AT_UTC_ISO}",
        ]
        if ai_mode == AI_MODE_DISABLED:
            lines.append("- AI mode controls via UI: locked while DISABLED")
        if ai_mode == AI_MODE_ON:
            cumulative_tokens = (
                OpenAICompatibleConnection.get_cumulative_tokens_since_startup()
            )
            lines.append(
                "- AI cumulative tokens since startup: "
                f"input={cumulative_tokens['input_tokens']}, "
                f"output={cumulative_tokens['output_tokens']}"
            )
        if http_status_code is not None:
            lines.append(
                f"- Server connectivity: reachable (HTTP {http_status_code})"
            )
        else:
            lines.append("- Server connectivity: unreachable")
            if http_error:
                lines.append(f"- Connectivity error: {http_error}")
        return "\n".join(lines)

    async def _invoke_graph_and_update_session(
        *,
        team_id: str,
        channel_id: str,
        thread_ts: str,
        user_id: str | None,
        user_text: str,
    ) -> str:
        """Invoke the graph and persist the resulting session state."""
        session = await session_manager.upsert(team_id, channel_id, thread_ts, user_id)
        session_ai_mode = _resolve_session_ai_mode(session)
        simple_mode_command = _normalize_mode_command_text(user_text)
        if simple_mode_command in {AI_MODE_OFF_EXACT_COMMAND, AI_MODE_ON_EXACT_COMMAND}:
            _log_selected_route(
                route="control.ai_mode_exact_command",
                team_id=team_id,
                channel_id=channel_id,
                thread_ts=thread_ts,
                user_id=user_id,
            )
            requested_ai_mode = (
                AI_MODE_ON
                if simple_mode_command == AI_MODE_ON_EXACT_COMMAND
                else AI_MODE_OFF
            )
            if _is_ai_mode_ui_switch_allowed(session_ai_mode):
                await session_manager.update(
                    session.key,
                    ai_mode=requested_ai_mode,
                )
                session = await session_manager.upsert(
                    team_id, channel_id, thread_ts, user_id
                )
                session_ai_mode = _resolve_session_ai_mode(session)
            response_text = (
                ai_mode_off_ack_text
                if requested_ai_mode == AI_MODE_OFF
                and _is_ai_mode_ui_switch_allowed(session_ai_mode)
                else _build_ai_mode_changed_text(session_ai_mode)
            )
            session_history = _normalize_conversation_history(session.conversation_history)
            updated_history = _append_conversation_turn(
                session_history,
                user_text=user_text,
                assistant_text=response_text,
            )
            await session_manager.update(
                session.key,
                current_target=None,
                environment=None,
                intent="control",
                last_summary=response_text,
                conversation_history=updated_history,
            )
            return response_text

        api_request = _parse_api_command(user_text)
        if api_request is None:
            normalized_user_text = str(user_text).strip()
            if normalized_user_text and not normalized_user_text.startswith(SLASH_PREFIX):
                first_token = normalized_user_text.split()[0].strip().lower()
                if first_token in {
                    API_VERB_HELP,
                    API_VERB_TOOLS,
                    API_VERB_OPSTATE,
                    API_VERB_CALL,
                }:
                    api_request = _parse_api_command(
                        f"{API_ROOT_OPAMP} {normalized_user_text}"
                    )
        if api_request is not None:
            _log_selected_route(
                route="api.slash_command_mode",
                team_id=team_id,
                channel_id=channel_id,
                thread_ts=thread_ts,
                user_id=user_id,
            )
            session_history = _normalize_conversation_history(session.conversation_history)
            verb = str(api_request.get("verb", "")).strip().lower()
            if verb == API_VERB_OPSTATE:
                status_code, status_error = await _probe_provider_http_status()
                response_text = _build_opstate_status_response_text(
                    ai_mode=_resolve_session_ai_mode(session),
                    http_status_code=status_code,
                    http_error=status_error,
                )
            elif isinstance(api_request.get("error"), str) and api_request.get("error"):
                response_text = str(api_request["error"]).strip()
            elif isinstance(
                api_request.get("immediate_response"),
                str,
            ) and api_request.get("immediate_response"):
                response_text = str(api_request["immediate_response"]).strip()
            else:
                planner_history = _build_planner_history(session)
                result = await compiled_graph.ainvoke(
                    {
                        STATE_KEY_TEAM_ID: team_id,
                        STATE_KEY_CHANNEL_ID: channel_id,
                        STATE_KEY_THREAD_TS: thread_ts,
                        STATE_KEY_USER_ID: user_id or "",
                        STATE_KEY_TEXT: str(api_request.get("planner_text", "")).strip(),
                        STATE_KEY_CONVERSATION_HISTORY: planner_history,
                        STATE_KEY_AI_ENABLED: False,
                        STATE_KEY_API_COMMAND_MODE: True,
                        STATE_KEY_DIRECT_TOOL_NAME: api_request.get("direct_tool_name"),
                        STATE_KEY_DIRECT_TOOL_ARGS: api_request.get("direct_tool_args", {}),
                    }
                )
                response_text = str(result.get(SLACK_KEY_RESPONSE_TEXT, "")).strip()
                if not response_text:
                    response_text = API_COMMAND_UNHANDLED_MESSAGE
                if verb == API_VERB_TOOLS:
                    response_text = _filter_tools_response(
                        response_text,
                        str(api_request.get("tools_filter", "")).strip(),
                    )

            updated_history = _append_conversation_turn(
                session_history,
                user_text=user_text,
                assistant_text=response_text,
            )
            await session_manager.update(
                session.key,
                current_target=None,
                environment=None,
                intent="api",
                last_summary=response_text,
                conversation_history=updated_history,
            )
            return response_text

        ai_mode_override, planner_text = _extract_ai_mode_directive(user_text)
        ai_mode = _resolve_session_ai_mode(session)
        if ai_mode_override is not None:
            if not _is_ai_mode_ui_switch_allowed(ai_mode):
                _log_selected_route(
                    route="control.ai_mode_change_blocked_disabled",
                    team_id=team_id,
                    channel_id=channel_id,
                    thread_ts=thread_ts,
                    user_id=user_id,
                )
                response_text = _build_ai_mode_changed_text(ai_mode)
                session_history = _normalize_conversation_history(
                    session.conversation_history
                )
                updated_history = _append_conversation_turn(
                    session_history,
                    user_text=user_text,
                    assistant_text=response_text,
                )
                await session_manager.update(
                    session.key,
                    current_target=None,
                    environment=None,
                    intent="control",
                    last_summary=response_text,
                    conversation_history=updated_history,
                )
                return response_text
            if _is_ai_mode_ui_switch_allowed(ai_mode):
                ai_mode = ai_mode_override
                await session_manager.update(
                    session.key,
                    ai_mode=ai_mode,
                )
                session = await session_manager.upsert(
                    team_id, channel_id, thread_ts, user_id
                )
                ai_mode = _resolve_session_ai_mode(session)
        if not planner_text and ai_mode_override is not None:
            _log_selected_route(
                route="control.ai_mode_directive_only",
                team_id=team_id,
                channel_id=channel_id,
                thread_ts=thread_ts,
                user_id=user_id,
            )
            response_text = _build_ai_mode_changed_text(ai_mode)
            session_history = _normalize_conversation_history(session.conversation_history)
            updated_history = _append_conversation_turn(
                session_history,
                user_text=user_text,
                assistant_text=response_text,
            )
            await session_manager.update(
                session.key,
                current_target=None,
                environment=None,
                intent="control",
                last_summary=response_text,
                conversation_history=updated_history,
            )
            return response_text

        ai_enabled = ai_mode == AI_MODE_ON
        session_history = _normalize_conversation_history(session.conversation_history)
        planner_history = _build_planner_history(session)
        _log_selected_route(
            route=(
                "graph.standard_ai_enabled"
                if ai_enabled
                else "graph.standard_ai_disabled"
            ),
            team_id=team_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            user_id=user_id,
        )
        result = await compiled_graph.ainvoke(
            {
                STATE_KEY_TEAM_ID: team_id,
                STATE_KEY_CHANNEL_ID: channel_id,
                STATE_KEY_THREAD_TS: thread_ts,
                STATE_KEY_USER_ID: user_id or "",
                STATE_KEY_TEXT: planner_text,
                STATE_KEY_CONVERSATION_HISTORY: planner_history,
                STATE_KEY_AI_ENABLED: ai_enabled,
            }
        )
        response_text = str(result.get(SLACK_KEY_RESPONSE_TEXT, help_text))
        updated_history = _append_conversation_turn(
            session_history,
            user_text=user_text,
            assistant_text=response_text,
        )
        await session_manager.update(
            session.key,
            current_target=result.get(STATE_KEY_TARGET),
            environment=result.get(SLACK_KEY_ENVIRONMENT),
            intent=result.get(STATE_KEY_INTENT),
            last_summary=response_text,
            conversation_history=updated_history,
        )
        return response_text

    async def _reply(
        responder: Any,
        *,
        response_text: str,
        thread_ts: str | None = None,
        response_type: str | None = None,
    ) -> None:
        """Send a Slack response."""
        payload: dict[str, Any] = {
            SLACK_KEY_TEXT: response_text,
            # Disable unfurling so route-like text (for example `/api/...`) does
            # not become auto-expanded links that can render as confusing 404s.
            "unfurl_links": False,
            "unfurl_media": False,
        }
        if thread_ts:
            payload[SLACK_KEY_THREAD_TS] = thread_ts
        if response_type:
            payload["response_type"] = response_type
        await responder(**payload)

    async def _process_message(body: dict[str, Any], text: str, say: Any) -> None:
        """Process a conversational message event and post graph output."""
        event = body.get(SLACK_KEY_EVENT, {})
        team_id = body.get(SLACK_KEY_TEAM_ID) or body.get(
            SLACK_KEY_AUTHORIZATIONS,
            [{}],
        )[0].get(SLACK_KEY_TEAM_ID, SLACK_KEY_UNKNOWN)
        channel_id = event.get(SLACK_KEY_CHANNEL) or body.get(SLACK_KEY_CHANNEL_ID)
        if not isinstance(channel_id, str) or not channel_id.strip():
            channel_id = SLACK_KEY_UNKNOWN
        reply_thread_ts = (
            str(event.get(SLACK_KEY_THREAD_TS, "")).strip()
            or None
        )
        session_thread_ts = _derive_session_thread_ts(
            reply_thread_ts=reply_thread_ts,
            user_id=event.get(SLACK_KEY_USER) or body.get(SLACK_KEY_USER_ID),
        )
        user_id = event.get(SLACK_KEY_USER) or body.get(SLACK_KEY_USER_ID)
        with suppress(Exception):
            await _reply(
                say,
                response_text=_build_processing_ack_text(processing_ack_messages),
                thread_ts=reply_thread_ts,
            )
        try:
            response_text = await _invoke_graph_and_update_session(
                team_id=team_id,
                channel_id=channel_id,
                thread_ts=session_thread_ts,
                user_id=user_id,
                user_text=text,
            )
            await _reply(
                say,
                response_text=response_text,
                thread_ts=reply_thread_ts,
            )
        except Exception:
            logger.exception(
                "failed processing Slack message event",
                extra={
                    LOG_KEY_EVENT: "slack.handlers.message_processing_failed",
                    LOG_KEY_CONTEXT: {
                        SLACK_KEY_TEAM_ID: team_id,
                        SLACK_KEY_CHANNEL_ID: channel_id,
                        SLACK_KEY_THREAD_TS: session_thread_ts,
                    },
                },
            )
            with suppress(Exception):
                if reply_thread_ts:
                    await _reply(
                        say,
                        response_text=USER_FACING_STUMBLE_REPLY,
                        thread_ts=reply_thread_ts,
                    )
                else:
                    await _reply(
                        say,
                        response_text=USER_FACING_STUMBLE_REPLY,
                    )

    @app.command(config[CONFIG_KEY_SLACK][CONFIG_KEY_COMMAND_NAME])
    async def handle_command(ack: Any, body: dict[str, Any], respond: Any) -> None:
        """Handle `/opamp` commands and return a channel-visible response.

        Why this flow:
        slash commands should acknowledge quickly and reply in-channel so the
        exchange remains visible to collaborators.

        Args:
            ack: Slack acknowledgment callable for command receipt.
            body: Slash command payload from Slack.
            respond: Slack response callable for command replies.

        Returns:
            None: Acknowledges, updates session state, and sends a response.
        """
        await ack()
        text = body.get(SLACK_KEY_TEXT, "").strip()
        if not text:
            await respond(help_text)
            return

        team_id = body.get(SLACK_KEY_TEAM_ID, SLACK_KEY_UNKNOWN)
        channel_id = body.get(SLACK_KEY_CHANNEL_ID, SLACK_KEY_UNKNOWN)
        raw_thread_ts = str(body.get(SLACK_KEY_THREAD_TS, "")).strip() or None
        user_id = body.get(SLACK_KEY_USER_ID)
        session_thread_ts = _derive_session_thread_ts(
            reply_thread_ts=raw_thread_ts,
            user_id=user_id,
        )
        with suppress(Exception):
            await _reply(
                respond,
                response_text=_build_processing_ack_text(processing_ack_messages),
                response_type=SLACK_KEY_IN_CHANNEL,
            )
        try:
            response_text = await _invoke_graph_and_update_session(
                team_id=team_id,
                channel_id=channel_id,
                thread_ts=session_thread_ts,
                user_id=user_id,
                user_text=text,
            )
            await _reply(
                respond,
                response_text=response_text,
                response_type=SLACK_KEY_IN_CHANNEL,
            )
        except Exception:
            logger.exception(
                "failed handling Slack slash command",
                extra={
                    LOG_KEY_EVENT: "slack.handlers.command_failed",
                    LOG_KEY_CONTEXT: {
                        SLACK_KEY_TEAM_ID: team_id,
                        SLACK_KEY_CHANNEL_ID: channel_id,
                        SLACK_KEY_THREAD_TS: session_thread_ts,
                        LOG_KEY_COMMAND: config[CONFIG_KEY_SLACK][CONFIG_KEY_COMMAND_NAME],
                    },
                },
            )
            with suppress(Exception):
                await _reply(
                    respond,
                    response_text=USER_FACING_STUMBLE_REPLY,
                    response_type=SLACK_KEY_IN_CHANNEL,
                )

    @app.event("app_mention")
    async def handle_mention(body: dict[str, Any], say: Any) -> None:
        """Handle app mentions in channels by delegating to message processing.

        Args:
            body: Slack event envelope for the mention.
            say: Slack Bolt responder bound to the source channel/thread.

        Returns:
            None: Posts graph output back to the mention thread.
        """
        text = body.get(SLACK_KEY_EVENT, {}).get(SLACK_KEY_TEXT, "")
        await _process_message(body, text, say)

    @app.event("message")
    async def handle_message(
        body: dict[str, Any], say: Any, event: dict[str, Any]
    ) -> None:
        """Handle direct-message events while ignoring non-DM traffic.

        Why this guard:
        channel message events are noisy; restricting this path to DM traffic
        prevents duplicate responses when app mentions already handle channels.

        Args:
            body: Slack event envelope.
            say: Slack Bolt responder bound to the event context.
            event: Flattened event payload supplied by Bolt.

        Returns:
            None: Processes DM text through the conversation graph when eligible.
        """
        channel_type = event.get(SLACK_KEY_CHANNEL_TYPE)
        if channel_type != SLACK_CHANNEL_TYPE_IM:
            return
        text = event.get(SLACK_KEY_TEXT, "")
        await _process_message(body, text, say)
