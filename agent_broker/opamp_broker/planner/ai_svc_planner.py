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

"""AI service-backed planner implementation."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from opamp_broker.planner.ai_connection import AIConnection
from opamp_broker.planner.ai_connection_factory import create_ai_connection
from opamp_broker.planner.constants import (
    BROKER_PLAN_JSON_SCHEMA,
    DEFAULT_AI_SVC_API_KEY_ENV,
    DEFAULT_AI_SVC_BASE_URL,
    DEFAULT_AI_SVC_PROVIDER,
    DEFAULT_SLACK_FORMAT_SYSTEM_PROMPT,
    REQUIRES_CONFIRMATION_KEY,
    RESPONSE_TEXT_KEY,
    SLACK_FORMAT_SYSTEM_PROMPT_KEY,
    TOOL_ARGS_KEY,
    TOOL_NAME_KEY,
)

logger = logging.getLogger(__name__)

SLACK_FORMATTED_TEXT_KEY = "formatted_text"
SLACK_FORMAT_RESULT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        SLACK_FORMATTED_TEXT_KEY: {"type": "string"},
    },
    "required": [SLACK_FORMATTED_TEXT_KEY],
}
SLACK_FORMAT_TOOL_RESULT_MAX_CHARS = 12000
COMPONENT_HEALTH_NORMALIZED_KEY = "componenthealth"
PLANNER_HISTORY_MAX_MESSAGES = 12
PLANNER_HISTORY_MAX_CONTENT_CHARS = 1000


class AISvcPlanner:
    """LLM planner that returns a strict JSON plan constrained to discovered tools."""

    def __init__(
        self,
        *,
        model: str,
        connection: AIConnection,
        system_prompt: str,
        temperature: float,
        slack_format_system_prompt: str = DEFAULT_SLACK_FORMAT_SYSTEM_PROMPT,
    ) -> None:
        """Initialize planner with runtime-selected provider connection and prompts.

        Why prompts are constructor parameters:
        they are loaded centrally from config so operations teams can tune planner
        behavior without changing code.
        """
        self.model = model
        self.connection = connection
        self.system_prompt = system_prompt
        self.slack_format_system_prompt = slack_format_system_prompt
        self.temperature = temperature

    async def plan(
        self,
        *,
        text: str,
        tools: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Generate a tool-constrained execution plan from natural-language input.

        Why this method is schema-constrained:
        planner output is machine-consumed by graph nodes, so strict schema
        output avoids brittle free-text parsing and unsupported tool calls.
        """
        allowed_tools = [
            {
                "name": tool.get("name"),
                "description": tool.get("description", ""),
                "inputSchema": tool.get("inputSchema", {}),
            }
            for tool in tools
            if tool.get("name")
        ]

        system_prompt = str(self.system_prompt).strip()
        if not system_prompt:
            raise RuntimeError(
                "missing required non-empty system_prompt in planner prompts config"
            )

        history = _sanitize_conversation_history(conversation_history)

        user_prompt: dict[str, Any] = {
            "request_text": text,
            "available_tools": allowed_tools,
            "output_requirements": {
                "must_use_only_listed_tool_names": True,
                "tool_args_must_match_selected_tool_schema": True,
            },
        }
        if history:
            user_prompt["conversation_history"] = history

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
            ],
            "temperature": self.temperature,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "broker_plan",
                    "schema": BROKER_PLAN_JSON_SCHEMA,
                    "strict": True,
                },
            },
        }

        logger.debug(
            "Sending planner request to AI service provider=%s model=%s base_url=%s tool_count=%d",
            self.connection.provider,
            self.model,
            self.connection.base_url,
            len(allowed_tools),
        )
        logger.debug("Planner request payload: %s", json.dumps(payload, ensure_ascii=False))

        raw_content = await self.connection.request_json_schema_completion(
            model=self.model,
            messages=payload["messages"],
            schema_name="broker_plan",
            schema=BROKER_PLAN_JSON_SCHEMA,
            temperature=self.temperature,
        )
        if raw_content is None:
            raise RuntimeError("AI service returned empty planner response")
        parsed = json.loads(raw_content)
        return sanitize_plan(parsed=parsed, tools=tools)

    async def format_tool_response_for_slack(
        self,
        *,
        user_text: str,
        tool_name: str,
        tool_args: dict[str, Any],
        tool_result: dict[str, Any],
        default_response_text: str,
    ) -> str | None:
        """Render tool output into concise Slack text using a prompt-configured style.

        Why this is a separate formatter call:
        tool payloads are often verbose JSON; a dedicated formatting pass keeps
        end-user Slack responses readable while preserving key facts.
        """
        if not isinstance(tool_result, dict) or not tool_result:
            return None

        formatter_system_prompt = str(self.slack_format_system_prompt).strip()
        if not formatter_system_prompt:
            raise RuntimeError(
                "missing required non-empty "
                f"{SLACK_FORMAT_SYSTEM_PROMPT_KEY} in planner prompts config"
            )

        filtered_tool_result = _strip_component_health_fields(tool_result)
        filtered_tool_result = _strip_null_fields(filtered_tool_result)

        try:
            serialized_tool_result = json.dumps(
                filtered_tool_result,
                ensure_ascii=False,
                default=str,
            )
        except TypeError:
            serialized_tool_result = str(filtered_tool_result)
        if len(serialized_tool_result) > SLACK_FORMAT_TOOL_RESULT_MAX_CHARS:
            omitted = len(serialized_tool_result) - SLACK_FORMAT_TOOL_RESULT_MAX_CHARS
            serialized_tool_result = (
                serialized_tool_result[:SLACK_FORMAT_TOOL_RESULT_MAX_CHARS]
                + f"... [truncated {omitted} chars]"
            )

        formatter_prompt = {
            "user_request_text": str(user_text or ""),
            "tool_name": str(tool_name or ""),
            "tool_args": tool_args if isinstance(tool_args, dict) else {},
            "default_response_text": str(default_response_text or ""),
            "tool_result_json": serialized_tool_result,
            "instructions": (
                "Produce a clear Slack-ready response. "
                "Use bullet points and short headings only when helpful. "
                "Do not include JSON blobs unless explicitly needed. "
                "Exclude component health details from status descriptions. "
                "Omit fields when the value is null, None, or empty."
            ),
        }

        raw_content = await self.connection.request_json_schema_completion(
            model=self.model,
            messages=[
                {"role": "system", "content": formatter_system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(formatter_prompt, ensure_ascii=False),
                },
            ],
            schema_name="broker_slack_tool_response",
            schema=SLACK_FORMAT_RESULT_JSON_SCHEMA,
            temperature=self.temperature,
        )
        if raw_content is None:
            return None
        parsed = json.loads(raw_content)
        formatted_text = parsed.get(SLACK_FORMATTED_TEXT_KEY)
        if isinstance(formatted_text, str):
            cleaned = formatted_text.strip()
            return cleaned or None
        return None


def _is_component_health_field_name(field_name: str) -> bool:
    """Identify component-health keys with forgiving normalization.

    Why normalization is needed:
    upstream payloads may vary by naming style (snake, camel, spaced), but we
    always want component health excluded from generated summaries.
    """
    normalized = re.sub(r"[^a-z0-9]", "", str(field_name).strip().lower())
    return normalized == COMPONENT_HEALTH_NORMALIZED_KEY


def _strip_component_health_fields(value: Any) -> Any:
    """Recursively remove component-health fields from nested tool payloads."""
    if isinstance(value, dict):
        filtered: dict[Any, Any] = {}
        for key, nested in value.items():
            if _is_component_health_field_name(str(key)):
                continue
            filtered[key] = _strip_component_health_fields(nested)
        return filtered
    if isinstance(value, list):
        return [_strip_component_health_fields(item) for item in value]
    return value


def _strip_null_fields(value: Any) -> Any:
    """Recursively remove null-like values from nested tool payloads.

    Why this helper exists:
    Slack responses are easier to read when missing values are omitted instead
    of rendered as `null`/empty placeholder lines.
    """
    if isinstance(value, dict):
        filtered: dict[Any, Any] = {}
        for key, nested in value.items():
            cleaned = _strip_null_fields(nested)
            if _is_null_like_value(cleaned):
                continue
            filtered[key] = cleaned
        return filtered
    if isinstance(value, list):
        cleaned_items = [_strip_null_fields(item) for item in value]
        return [item for item in cleaned_items if not _is_null_like_value(item)]
    return value


def _is_null_like_value(value: Any) -> bool:
    """Return True when a value should be omitted from user-facing formatting."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in {"", "none", "null"}:
        return True
    if isinstance(value, (dict, list)) and not value:
        return True
    return False


def _sanitize_conversation_history(
    conversation_history: list[dict[str, str]] | None,
) -> list[dict[str, str]]:
    """Trim and validate chat history before sending it to the planner model.

    Why this sanitization exists:
    keeping history bounded protects token budget and prevents malformed entries
    from causing planner request failures.
    """
    if not isinstance(conversation_history, list):
        return []

    sanitized: list[dict[str, str]] = []
    for message in conversation_history:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role", "")).strip().lower()
        if role not in {"user", "assistant", "system"}:
            continue
        content = str(message.get("content", "")).strip()
        if not content:
            continue
        if len(content) > PLANNER_HISTORY_MAX_CONTENT_CHARS:
            content = content[:PLANNER_HISTORY_MAX_CONTENT_CHARS]
        sanitized.append({"role": role, "content": content})
    if len(sanitized) > PLANNER_HISTORY_MAX_MESSAGES:
        return sanitized[-PLANNER_HISTORY_MAX_MESSAGES:]
    return sanitized


async def verify_ai_svc_connection(
    *,
    model: str,
    provider: str = DEFAULT_AI_SVC_PROVIDER,
    timeout_seconds: int = 30,
    temperature: float = 0.0,
    api_key_env_var: str = DEFAULT_AI_SVC_API_KEY_ENV,
    base_url: str = DEFAULT_AI_SVC_BASE_URL,
    max_completion_tokens: int | None = 1024,
    verify_max_completion_tokens_attempts: tuple[int, ...] | None = (64, 512),
    verification_prompt: str = "",
) -> dict[str, Any]:
    """Verify provider auth/reachability independently of the planner graph.

    Why this helper exists:
    startup checks and tests need a lightweight way to validate AI credentials
    and endpoint access before the broker starts handling traffic.
    """
    try:
        connection = create_ai_connection(
            provider=provider,
            api_key_env_var=api_key_env_var,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            temperature=temperature,
            max_completion_tokens=max_completion_tokens,
            verify_max_completion_tokens_attempts=(
                verify_max_completion_tokens_attempts
            ),
            verification_prompt=verification_prompt,
        )
    except Exception as exc:
        return {
            "ok": False,
            "error": f"failed to create AI provider connection: {exc}",
        }
    return await connection.verify_connection(model=model)


def sanitize_plan(
    *,
    parsed: dict[str, Any],
    tools: list[dict[str, Any]],
) -> dict[str, Any]:
    """Normalize and constrain planner output to discovered tool metadata.

    Why sanitization is mandatory:
    model output can drift (wrong tool names, malformed args), so we gate the
    final plan to discovered tools and schema-safe argument structures.
    """
    allowed_names = {str(tool.get("name")) for tool in tools if tool.get("name")}

    raw_tool_name = parsed.get(TOOL_NAME_KEY)
    tool_name = str(raw_tool_name).strip() if raw_tool_name else None
    if tool_name not in allowed_names:
        tool_name = None

    # See planner/constants.py note: tool_args is emitted as a JSON string to stay
    # compatible with OpenAI strict response_format schema requirements.
    raw_tool_args = parsed.get(TOOL_ARGS_KEY, "{}")
    tool_args: dict[str, Any] = {}
    if isinstance(raw_tool_args, dict):
        tool_args = raw_tool_args
    elif isinstance(raw_tool_args, str):
        candidate = raw_tool_args.strip() or "{}"
        try:
            decoded = json.loads(candidate)
        except ValueError:
            # Keep planning resilient if the model emits non-JSON tool_args text.
            decoded = {}
        if isinstance(decoded, dict):
            tool_args = decoded
    if not tool_name:
        tool_args = {}

    response_text = parsed.get(RESPONSE_TEXT_KEY, "")
    if not isinstance(response_text, str):
        response_text = str(response_text)

    requires_confirmation = bool(parsed.get(REQUIRES_CONFIRMATION_KEY, False))

    return {
        RESPONSE_TEXT_KEY: response_text.strip(),
        TOOL_NAME_KEY: tool_name,
        TOOL_ARGS_KEY: tool_args,
        REQUIRES_CONFIRMATION_KEY: requires_confirmation,
    }
