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

"""Tests for broker planning, graph-node execution, and AI integration helpers."""

from __future__ import annotations

import asyncio
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_BROKER_ROOT = REPO_ROOT / "agent_broker"
if str(AGENT_BROKER_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_BROKER_ROOT))

nodes = importlib.import_module("opamp_broker.graph.nodes")
planner_engine = importlib.import_module("opamp_broker.planner.engine")
ai_svc_planner = importlib.import_module("opamp_broker.planner.ai_svc_planner")
ai_connection_factory = importlib.import_module(
    "opamp_broker.planner.ai_connection_factory"
)
openai_compatible_connection = importlib.import_module(
    "opamp_broker.planner.openai_compatible_connection"
)
config_loader = importlib.import_module("opamp_broker.config.loader")
state_module = importlib.import_module("opamp_broker.graph.state")
mcp_client_module = importlib.import_module("opamp_broker.mcp.client")


class _FakeToolRegistry:
    def __init__(self, tools: dict[str, dict[str, Any]]) -> None:
        self._tools = tools

    def list_names(self) -> list[str]:
        return sorted(self._tools.keys())

    def get(self, name: str) -> dict[str, Any] | None:
        return self._tools.get(name)


class _FakePlanner:
    def __init__(self, plan: dict[str, Any]) -> None:
        self._plan = plan

    async def plan(
        self,
        *,
        text: str,
        tools: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        del text, tools, conversation_history
        return self._plan


class _RaisingPlanner:
    async def plan(
        self,
        *,
        text: str,
        tools: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        del text, tools, conversation_history
        raise RuntimeError("planner unavailable")


def _looks_like_json_blob(value: str) -> bool:
    stripped = value.strip()
    return (
        (stripped.startswith("{") and stripped.endswith("}"))
        or (stripped.startswith("[") and stripped.endswith("]"))
    )


def test_create_planner_returns_rule_first_without_api_key() -> None:
    """Verifies planner creation falls back to rule-first mode when no API key is set."""
    api_key_env_var = planner_engine.DEFAULT_AI_SVC_API_KEY_ENV
    os.environ.pop(api_key_env_var, None)
    planner = planner_engine.create_planner(
        {"planner": {"llm_enabled": True, "model": "gpt-5.4"}}
    )
    assert isinstance(planner, planner_engine.RuleFirstPlanner)


def test_create_planner_returns_ai_svc_planner_with_api_key() -> None:
    """Verifies planner creation uses the AI service planner when an API key is available."""
    api_key_env_var = planner_engine.DEFAULT_AI_SVC_API_KEY_ENV
    os.environ[api_key_env_var] = "test-key"
    planner = planner_engine.create_planner(
        {
            "planner": {
                "llm_enabled": True,
                "model": "gpt-5.4",
                "prompts": {
                    "system_prompt": "system prompt",
                    "verification_prompt": "verification prompt",
                },
            }
        }
    )
    assert isinstance(planner, planner_engine.AISvcPlanner)
    os.environ.pop(api_key_env_var, None)


def test_create_planner_applies_configured_max_completion_tokens() -> None:
    """Verifies planner creation applies the configured max completion token limit."""
    api_key_env_var = planner_engine.DEFAULT_AI_SVC_API_KEY_ENV
    os.environ[api_key_env_var] = "test-key"
    planner = planner_engine.create_planner(
        {
            "planner": {
                "llm_enabled": True,
                "model": "gpt-5.4",
                "max_completion_tokens": 2048,
                "prompts": {
                    "system_prompt": "system prompt",
                    "verification_prompt": "verification prompt",
                },
            }
        }
    )
    assert isinstance(planner, planner_engine.AISvcPlanner)
    assert planner.connection.max_completion_tokens == 2048
    os.environ.pop(api_key_env_var, None)


def test_create_planner_returns_rule_first_for_unsupported_provider() -> None:
    """Verifies unsupported AI providers fall back to the rule-first planner."""
    api_key_env_var = planner_engine.DEFAULT_AI_SVC_API_KEY_ENV
    os.environ[api_key_env_var] = "test-key"
    planner = planner_engine.create_planner(
        {
            "planner": {
                "llm_enabled": True,
                "provider": "unsupported-provider",
                "model": "gpt-5.4",
                "prompts": {
                    "system_prompt": "system prompt",
                    "verification_prompt": "verification prompt",
                },
            }
        }
    )
    assert isinstance(planner, planner_engine.RuleFirstPlanner)
    os.environ.pop(api_key_env_var, None)


def test_create_planner_accepts_openai_compatible_provider_alias() -> None:
    """Verifies the openai-compatible provider alias resolves to the AI service planner."""
    api_key_env_var = planner_engine.DEFAULT_AI_SVC_API_KEY_ENV
    os.environ[api_key_env_var] = "test-key"
    planner = planner_engine.create_planner(
        {
            "planner": {
                "llm_enabled": True,
                "provider": "openai-compatible",
                "model": "gpt-5.4",
                "prompts": {
                    "system_prompt": "system prompt",
                    "verification_prompt": "verification prompt",
                },
            }
        }
    )
    assert isinstance(planner, planner_engine.AISvcPlanner)
    os.environ.pop(api_key_env_var, None)


def test_create_planner_returns_rule_first_for_template_provider() -> None:
    """Verifies the template provider stays on the rule-first fallback path."""
    api_key_env_var = planner_engine.DEFAULT_AI_SVC_API_KEY_ENV
    os.environ[api_key_env_var] = "test-key"
    planner = planner_engine.create_planner(
        {
            "planner": {
                "llm_enabled": True,
                "provider": "template",
                "model": "gpt-5.4",
                "prompts": {
                    "system_prompt": "system prompt",
                    "verification_prompt": "verification prompt",
                },
            }
        }
    )
    assert isinstance(planner, planner_engine.RuleFirstPlanner)
    os.environ.pop(api_key_env_var, None)


def test_resolve_ai_runtime_settings_supports_structured_prompt_entries() -> None:
    """Verifies structured prompt entries are flattened into runtime prompt settings."""
    settings = ai_connection_factory.resolve_ai_runtime_settings(
        {
            "planner": {
                "prompts": {
                    "system_prompt": {
                        "description": "used for planning",
                        "text": "planner system prompt",
                    },
                    "verification_prompt": {
                        "description": "used for startup verification",
                        "text": "connection check",
                    },
                    "slack_format_system_prompt": {
                        "description": "used for slack formatting",
                        "text": "format this for slack",
                    },
                }
            }
        }
    )

    assert settings["system_prompt"] == "planner system prompt"
    assert settings["verification_prompt"] == "connection check"
    assert settings["slack_format_system_prompt"] == "format this for slack"
    assert settings["prompt_descriptions"]["system_prompt"] == "used for planning"
    assert (
        settings["prompt_descriptions"]["verification_prompt"]
        == "used for startup verification"
    )
    assert (
        settings["prompt_descriptions"]["slack_format_system_prompt"]
        == "used for slack formatting"
    )


def test_load_runtime_config_loads_prompt_text_and_descriptions(
    tmp_path: Path,
) -> None:
    """Verifies runtime config loading imports prompt text and prompt descriptions."""
    prompts_path = tmp_path / "planner_prompts.json"
    prompts_path.write_text(
        json.dumps(
            {
                "system_prompt": {
                    "description": "Used for AI planning requests.",
                    "text": "planner prompt",
                },
                "verification_prompt": {
                    "description": "Used during startup verification checks.",
                    "text": "verify prompt",
                },
                "slack_format_system_prompt": {
                    "description": "Used to format tool responses for Slack.",
                    "text": "slack formatter prompt",
                },
            }
        ),
        encoding="utf-8",
    )

    opamp_config_path = tmp_path / "opamp.json"
    opamp_config_path.write_text("{}", encoding="utf-8")
    broker_config_path = tmp_path / "broker.json"
    broker_config_path.write_text(
        json.dumps(
            {
                "paths": {"opamp_config_path": str(opamp_config_path)},
                "planner": {"prompts_config_path": str(prompts_path)},
            }
        ),
        encoding="utf-8",
    )

    config = config_loader.load_runtime_config(str(broker_config_path))

    assert config["planner"]["prompts"]["system_prompt"] == "planner prompt"
    assert config["planner"]["prompts"]["verification_prompt"] == "verify prompt"
    assert (
        config["planner"]["prompts"]["slack_format_system_prompt"]
        == "slack formatter prompt"
    )
    assert (
        config["planner"]["prompt_descriptions"]["system_prompt"]
        == "Used for AI planning requests."
    )
    assert (
        config["planner"]["prompt_descriptions"]["verification_prompt"]
        == "Used during startup verification checks."
    )
    assert (
        config["planner"]["prompt_descriptions"]["slack_format_system_prompt"]
        == "Used to format tool responses for Slack."
    )


def test_sanitize_plan_rejects_unknown_tool() -> None:
    """Verifies plan sanitization removes tool selections that were not discovered."""
    sanitized = planner_engine._sanitize_plan(
        parsed={
            planner_engine.TOOL_NAME_KEY: "tool.not.allowed",
            planner_engine.TOOL_ARGS_KEY: {"target": "collector-a"},
            planner_engine.RESPONSE_TEXT_KEY: "",
            planner_engine.REQUIRES_CONFIRMATION_KEY: False,
        },
        tools=[{"name": "tool.status"}],
    )
    assert sanitized[planner_engine.TOOL_NAME_KEY] is None
    assert sanitized[planner_engine.TOOL_ARGS_KEY] == {}


def test_broker_plan_schema_uses_openai_strict_safe_tool_arg_value_types() -> None:
    """Verifies the planner schema keeps tool arguments in an OpenAI strict-safe string field."""
    tool_args = planner_engine.BROKER_PLAN_JSON_SCHEMA["properties"][
        planner_engine.TOOL_ARGS_KEY
    ]
    assert tool_args["type"] == "string"


def test_sanitize_plan_parses_tool_args_json_string() -> None:
    """Verifies plan sanitization converts JSON-encoded tool arguments into a mapping."""
    sanitized = planner_engine._sanitize_plan(
        parsed={
            planner_engine.RESPONSE_TEXT_KEY: "Running status",
            planner_engine.TOOL_NAME_KEY: "tool.status",
            planner_engine.TOOL_ARGS_KEY: '{"target":"collector-a"}',
            planner_engine.REQUIRES_CONFIRMATION_KEY: False,
        },
        tools=[{"name": "tool.status"}],
    )
    assert sanitized[planner_engine.TOOL_ARGS_KEY] == {"target": "collector-a"}


def test_rule_first_planner_lists_tools() -> None:
    """Verifies the rule-first planner can answer simple tool-list requests."""
    planner = planner_engine.RuleFirstPlanner()
    plan = asyncio.run(
        planner.plan(
            text="tools",
            tools=[{"name": "tool.status"}, {"name": "tool.health"}],
        )
    )
    assert "Available MCP tools" in plan[planner_engine.RESPONSE_TEXT_KEY]
    assert plan[planner_engine.TOOL_NAME_KEY] is None


def test_rule_first_planner_describes_tools_with_argument_hints() -> None:
    """Verifies tool descriptions include argument names, types, and required markers."""
    planner = planner_engine.RuleFirstPlanner()
    plan = asyncio.run(
        planner.plan(
            text="what can you do?",
            tools=[
                {
                    "name": "tool.status",
                    "description": "Check agent status",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "target": {"type": "string"},
                            "verbose": {"type": "boolean"},
                        },
                        "required": ["target"],
                    },
                }
            ],
        )
    )
    response = plan[planner_engine.RESPONSE_TEXT_KEY]
    assert "tool.status" in response
    assert "Check agent status" in response
    assert "target (string, required)" in response
    assert "verbose (boolean, optional)" in response
    assert plan[planner_engine.TOOL_NAME_KEY] is None


def test_rule_first_planner_allows_direct_tool_name_invocation() -> None:
    """Verifies the rule-first planner accepts a direct tool name with no arguments."""
    planner = planner_engine.RuleFirstPlanner()
    plan = asyncio.run(
        planner.plan(
            text="tool_otel_agents",
            tools=[
                {
                    "name": "tool_otel_agents",
                    "description": "List OpenTelemetry agents",
                }
            ],
        )
    )
    assert plan[planner_engine.TOOL_NAME_KEY] == "tool_otel_agents"
    assert plan[planner_engine.TOOL_ARGS_KEY] == {}
    assert plan[planner_engine.REQUIRES_CONFIRMATION_KEY] is False


def test_rule_first_planner_allows_direct_tool_name_with_target() -> None:
    """Verifies the rule-first planner maps a trailing target value into tool arguments."""
    planner = planner_engine.RuleFirstPlanner()
    plan = asyncio.run(
        planner.plan(
            text="tool.status collector-a",
            tools=[
                {
                    "name": "tool.status",
                    "description": "Get status",
                }
            ],
        )
    )
    assert plan[planner_engine.TOOL_NAME_KEY] == "tool.status"
    assert plan[planner_engine.TOOL_ARGS_KEY] == {"target": "collector-a"}
    assert plan[planner_engine.REQUIRES_CONFIRMATION_KEY] is False


def test_rule_first_planner_parses_direct_tool_key_value_arguments() -> None:
    """Verifies direct tool calls parse key=value arguments into typed tool inputs."""
    planner = planner_engine.RuleFirstPlanner()
    plan = asyncio.run(
        planner.plan(
            text=(
                "tool_otel_agents "
                "service_instance_id=checkout "
                "host_name=alpha-node "
                "invert_filter=true"
            ),
            tools=[
                {
                    "name": "tool_otel_agents",
                    "description": "List OpenTelemetry agents",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "service_instance_id": {"type": "string"},
                            "host_name": {"type": "string"},
                            "invert_filter": {"type": "boolean"},
                        },
                    },
                }
            ],
        )
    )
    assert plan[planner_engine.TOOL_NAME_KEY] == "tool_otel_agents"
    assert plan[planner_engine.TOOL_ARGS_KEY] == {
        "service_instance_id": "checkout",
        "host_name": "alpha-node",
        "invert_filter": True,
    }
    assert plan[planner_engine.REQUIRES_CONFIRMATION_KEY] is False


def test_rule_first_planner_routes_agent_list_queries_with_filters() -> None:
    """Verifies agent list requests are routed to the agent tool with parsed filters."""
    planner = planner_engine.RuleFirstPlanner()
    plan = asyncio.run(
        planner.plan(
            text="show agents host-ip=10.0.0.5 version=1.2 exclude",
            tools=[
                {
                    "name": "tool_otel_agents",
                    "description": "List OpenTelemetry agents",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "host_ip": {"type": "string"},
                            "client_version": {"type": "string"},
                            "invert_filter": {"type": "boolean"},
                        },
                    },
                }
            ],
        )
    )
    assert plan[planner_engine.TOOL_NAME_KEY] == "tool_otel_agents"
    assert plan[planner_engine.TOOL_ARGS_KEY] == {
        "host_ip": "10.0.0.5",
        "client_version": "1.2",
        "invert_filter": True,
    }
    assert plan[planner_engine.REQUIRES_CONFIRMATION_KEY] is False


def test_rule_first_planner_supports_direct_tool_camel_case_argument_names() -> None:
    """Verifies direct tool calls accept camelCase aliases for snake_case arguments."""
    planner = planner_engine.RuleFirstPlanner()
    plan = asyncio.run(
        planner.plan(
            text="tool_otel_agents invertFilter=true hostName=alpha",
            tools=[
                {
                    "name": "tool_otel_agents",
                    "description": "List OpenTelemetry agents",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "invert_filter": {"type": "boolean"},
                            "host_name": {"type": "string"},
                        },
                    },
                }
            ],
        )
    )
    assert plan[planner_engine.TOOL_NAME_KEY] == "tool_otel_agents"
    assert plan[planner_engine.TOOL_ARGS_KEY] == {
        "invert_filter": True,
        "host_name": "alpha",
    }


def test_plan_action_uses_only_discovered_tool_names() -> None:
    """Verifies plan_action rejects planner-selected tools that are not in the registry."""
    tool_registry = _FakeToolRegistry(
        {
            "tool.status": {"name": "tool.status", "description": "status"},
        }
    )
    planner = _FakePlanner(
        {
            planner_engine.RESPONSE_TEXT_KEY: "",
            planner_engine.TOOL_NAME_KEY: "tool.unknown",
            planner_engine.TOOL_ARGS_KEY: {"target": "collector-a"},
            planner_engine.REQUIRES_CONFIRMATION_KEY: False,
        }
    )
    state = {
        state_module.STATE_KEY_TEXT: "status collector-a",
        state_module.STATE_KEY_NORMALIZED_TEXT: "status collector-a",
    }

    updated = asyncio.run(nodes.plan_action(state, tool_registry, planner))

    assert updated[state_module.STATE_KEY_TOOL_NAME] is None
    assert updated[state_module.STATE_KEY_TOOL_ARGS] == {}
    assert "couldn't map" in updated[state_module.STATE_KEY_RESPONSE_TEXT]


def test_plan_action_accepts_discovered_tool_name() -> None:
    """Verifies plan_action preserves discovered tool selections and extracted targets."""
    tool_registry = _FakeToolRegistry(
        {
            "tool.status": {"name": "tool.status", "description": "status"},
        }
    )
    planner = _FakePlanner(
        {
            planner_engine.RESPONSE_TEXT_KEY: "",
            planner_engine.TOOL_NAME_KEY: "tool.status",
            planner_engine.TOOL_ARGS_KEY: {"target": "collector-a"},
            planner_engine.REQUIRES_CONFIRMATION_KEY: False,
        }
    )
    state = {
        state_module.STATE_KEY_TEXT: "status collector-a",
        state_module.STATE_KEY_NORMALIZED_TEXT: "status collector-a",
    }

    updated = asyncio.run(nodes.plan_action(state, tool_registry, planner))

    assert updated[state_module.STATE_KEY_TOOL_NAME] == "tool.status"
    assert updated[state_module.STATE_KEY_TOOL_ARGS] == {"target": "collector-a"}
    assert updated[state_module.STATE_KEY_TARGET] == "collector-a"


def test_plan_action_passes_conversation_history_to_planner() -> None:
    """Verifies plan_action forwards conversation history to the planner."""
    tool_registry = _FakeToolRegistry(
        {
            "tool.status": {"name": "tool.status", "description": "status"},
        }
    )
    captured: dict[str, Any] = {}

    class _CapturingPlanner:
        async def plan(
            self,
            *,
            text: str,
            tools: list[dict[str, Any]],
            conversation_history: list[dict[str, str]] | None = None,
        ) -> dict[str, Any]:
            captured["text"] = text
            captured["tools"] = tools
            captured["conversation_history"] = conversation_history
            return {
                planner_engine.RESPONSE_TEXT_KEY: "",
                planner_engine.TOOL_NAME_KEY: "tool.status",
                planner_engine.TOOL_ARGS_KEY: {"target": "collector-a"},
                planner_engine.REQUIRES_CONFIRMATION_KEY: False,
            }

    state = {
        state_module.STATE_KEY_TEXT: "confirm",
        state_module.STATE_KEY_NORMALIZED_TEXT: "confirm",
        state_module.STATE_KEY_CONVERSATION_HISTORY: [
            {"role": "assistant", "content": "I can run restart for collector-a."},
            {"role": "user", "content": "confirm"},
        ],
    }

    updated = asyncio.run(
        nodes.plan_action(
            state,
            tool_registry,
            _CapturingPlanner(),
        )
    )

    assert updated[state_module.STATE_KEY_TOOL_NAME] == "tool.status"
    assert captured["text"] == "confirm"
    assert isinstance(captured["tools"], list)
    assert captured["conversation_history"] == [
        {"role": "assistant", "content": "I can run restart for collector-a."},
        {"role": "user", "content": "confirm"},
    ]


def test_plan_action_confirm_text_uses_planner_result() -> None:
    """Verifies confirmation requests return the planner-provided confirmation text."""
    tool_registry = _FakeToolRegistry(
        {
            "tool.status": {
                "name": "tool.status",
                "description": "status",
            },
        }
    )
    planner = _FakePlanner(
        {
            planner_engine.RESPONSE_TEXT_KEY: "",
            planner_engine.TOOL_NAME_KEY: "tool.status",
            planner_engine.TOOL_ARGS_KEY: {"target": "collector-a"},
            planner_engine.REQUIRES_CONFIRMATION_KEY: False,
        }
    )

    state = {
        state_module.STATE_KEY_TEXT: "confirm",
        state_module.STATE_KEY_NORMALIZED_TEXT: "confirm",
        state_module.STATE_KEY_PENDING_ACTION: {
            "tool": "tool_invoke_custom_command",
            "args": {"client_id": "collector-a", "operation": "restart"},
        },
    }

    updated = asyncio.run(
        nodes.plan_action(
            state,
            tool_registry,
            planner,
        )
    )

    assert updated[state_module.STATE_KEY_TOOL_NAME] == "tool.status"
    assert updated[state_module.STATE_KEY_TOOL_ARGS] == {"target": "collector-a"}
    assert updated[state_module.STATE_KEY_REQUIRES_CONFIRMATION] is False


def test_plan_action_cancel_text_uses_planner_result() -> None:
    """Verifies cancellation requests return the planner-provided cancellation text."""
    tool_registry = _FakeToolRegistry(
        {
            "tool.status": {
                "name": "tool.status",
                "description": "status",
            },
        }
    )
    planner = _FakePlanner(
        {
            planner_engine.RESPONSE_TEXT_KEY: "",
            planner_engine.TOOL_NAME_KEY: "tool.status",
            planner_engine.TOOL_ARGS_KEY: {"target": "collector-b"},
            planner_engine.REQUIRES_CONFIRMATION_KEY: False,
        }
    )

    state = {
        state_module.STATE_KEY_TEXT: "cancel",
        state_module.STATE_KEY_NORMALIZED_TEXT: "cancel",
        state_module.STATE_KEY_PENDING_ACTION: {
            "tool": "tool_invoke_custom_command",
            "args": {"client_id": "collector-a", "operation": "restart"},
        },
    }

    updated = asyncio.run(
        nodes.plan_action(
            state,
            tool_registry,
            planner,
        )
    )

    assert updated[state_module.STATE_KEY_TOOL_NAME] == "tool.status"
    assert updated[state_module.STATE_KEY_TOOL_ARGS] == {"target": "collector-b"}
    assert updated[state_module.STATE_KEY_REQUIRES_CONFIRMATION] is False


def test_plan_action_uses_direct_tool_when_api_command_mode_is_enabled() -> None:
    """Verifies API command mode uses the explicitly parsed tool instead of replanning."""
    tool_registry = _FakeToolRegistry(
        {
            "tool.status": {"name": "tool.status", "description": "status"},
        }
    )
    state = {
        state_module.STATE_KEY_TEXT: "/opamp call tool.status target=collector-a",
        state_module.STATE_KEY_NORMALIZED_TEXT: "tool.status target=collector-a",
        state_module.STATE_KEY_API_COMMAND_MODE: True,
        state_module.STATE_KEY_DIRECT_TOOL_NAME: "tool.status",
        state_module.STATE_KEY_DIRECT_TOOL_ARGS: {"target": "collector-a"},
    }
    updated = asyncio.run(
        nodes.plan_action(
            state,
            tool_registry,
            _RaisingPlanner(),
        )
    )

    assert updated[state_module.STATE_KEY_TOOL_NAME] == "tool.status"
    assert updated[state_module.STATE_KEY_TOOL_ARGS] == {"target": "collector-a"}
    assert updated[state_module.STATE_KEY_REQUIRES_CONFIRMATION] is False


def test_plan_action_rejects_unknown_direct_tool_in_api_command_mode() -> None:
    """Verifies API command mode rejects direct tool names that are not available."""
    tool_registry = _FakeToolRegistry(
        {
            "tool.status": {"name": "tool.status", "description": "status"},
        }
    )
    state = {
        state_module.STATE_KEY_TEXT: "/opamp call tool.unknown",
        state_module.STATE_KEY_NORMALIZED_TEXT: "tool.unknown",
        state_module.STATE_KEY_API_COMMAND_MODE: True,
        state_module.STATE_KEY_DIRECT_TOOL_NAME: "tool.unknown",
        state_module.STATE_KEY_DIRECT_TOOL_ARGS: {},
    }
    updated = asyncio.run(
        nodes.plan_action(
            state,
            tool_registry,
            _RaisingPlanner(),
        )
    )

    assert updated[state_module.STATE_KEY_TOOL_NAME] is None
    assert "Unknown tool `tool.unknown`." in str(updated[state_module.STATE_KEY_RESPONSE_TEXT])


def test_plan_action_preserves_planner_selected_tool_for_stop_request() -> None:
    """Verifies stop-style requests can preserve a planner-selected tool when one was supplied."""
    tool_registry = _FakeToolRegistry(
        {
            "tool_otel_agents": {"name": "tool_otel_agents", "description": "list"},
            "tool_invoke_custom_command": {
                "name": "tool_invoke_custom_command",
                "description": "invoke",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "client_id": {"type": "string"},
                        "operation": {"type": "string"},
                    },
                },
            },
        }
    )
    planner = _FakePlanner(
        {
            planner_engine.RESPONSE_TEXT_KEY: "Stop agent request: fluentd-Watts",
            planner_engine.TOOL_NAME_KEY: "tool_otel_agents",
            planner_engine.TOOL_ARGS_KEY: {"host_name": "fluentd-Watts"},
            planner_engine.REQUIRES_CONFIRMATION_KEY: False,
        }
    )
    state = {
        state_module.STATE_KEY_TEXT: "Stop agent request: fluentd-Watts",
        state_module.STATE_KEY_NORMALIZED_TEXT: "stop agent request: fluentd-watts",
    }

    updated = asyncio.run(nodes.plan_action(state, tool_registry, planner))

    assert updated[state_module.STATE_KEY_TOOL_NAME] == "tool_otel_agents"
    assert updated[state_module.STATE_KEY_TOOL_ARGS] == {"host_name": "fluentd-Watts"}
    assert updated[state_module.STATE_KEY_REQUIRES_CONFIRMATION] is False


def test_plan_action_stop_request_without_command_tool_keeps_planner_result() -> None:
    """Verifies stop requests without a command tool keep the planner response text intact."""
    tool_registry = _FakeToolRegistry(
        {
            "tool_otel_agents": {"name": "tool_otel_agents", "description": "list"},
        }
    )
    planner = _FakePlanner(
        {
            planner_engine.RESPONSE_TEXT_KEY: "",
            planner_engine.TOOL_NAME_KEY: "tool_otel_agents",
            planner_engine.TOOL_ARGS_KEY: {},
            planner_engine.REQUIRES_CONFIRMATION_KEY: False,
        }
    )
    state = {
        state_module.STATE_KEY_TEXT: "shutdown fluentd-Watts",
        state_module.STATE_KEY_NORMALIZED_TEXT: "shutdown fluentd-watts",
    }

    updated = asyncio.run(nodes.plan_action(state, tool_registry, planner))

    assert updated[state_module.STATE_KEY_TOOL_NAME] == "tool_otel_agents"
    assert updated[state_module.STATE_KEY_TOOL_ARGS] == {}
    assert updated[state_module.STATE_KEY_REQUIRES_CONFIRMATION] is False
    assert "couldn't find a command execution tool" not in str(
        updated.get(state_module.STATE_KEY_RESPONSE_TEXT, "")
    )


def test_plan_action_returns_offline_message_when_mcp_unavailable() -> None:
    """Verifies plan_action returns the offline message when MCP is unavailable."""
    class _UnavailableToolRegistry:
        def list_names(self) -> list[str]:
            return []

        async def refresh(self) -> None:
            raise mcp_client_module.MCPServerUnavailableError("offline")

        def get(self, name: str) -> dict[str, Any] | None:
            return None

    planner = _FakePlanner(
        {
            planner_engine.RESPONSE_TEXT_KEY: "",
            planner_engine.TOOL_NAME_KEY: None,
            planner_engine.TOOL_ARGS_KEY: {},
            planner_engine.REQUIRES_CONFIRMATION_KEY: False,
        }
    )
    state = {
        state_module.STATE_KEY_TEXT: "status collector-a",
        state_module.STATE_KEY_NORMALIZED_TEXT: "status collector-a",
    }

    updated = asyncio.run(
        nodes.plan_action(
            state,
            _UnavailableToolRegistry(),
            planner,
            "The OpAMP server is currently offline.",
        )
    )

    assert updated[state_module.STATE_KEY_TOOL_NAME] is None
    assert updated[state_module.STATE_KEY_TOOL_ARGS] == {}
    assert updated[state_module.STATE_KEY_TOOLS_AVAILABLE] == []
    assert updated[state_module.STATE_KEY_RESPONSE_TEXT] == (
        "The OpAMP server is currently offline."
    )


def test_plan_action_falls_back_to_rule_first_when_planner_raises() -> None:
    """Verifies plan_action falls back to rule-first planning when the main planner fails."""
    tool_registry = _FakeToolRegistry(
        {
            "tool.status": {"name": "tool.status", "description": "status"},
        }
    )
    state = {
        state_module.STATE_KEY_TEXT: "status collector-a",
        state_module.STATE_KEY_NORMALIZED_TEXT: "status collector-a",
    }

    updated = asyncio.run(nodes.plan_action(state, tool_registry, _RaisingPlanner()))

    assert updated[state_module.STATE_KEY_TOOL_NAME] == "tool.status"
    assert updated[state_module.STATE_KEY_TOOL_ARGS] == {"target": "collector-a"}
    assert updated[state_module.STATE_KEY_TARGET] == "collector-a"


def test_execute_or_summarize_returns_offline_message_when_mcp_unavailable() -> None:
    """Verifies execute_or_summarize returns an offline message when MCP calls cannot run."""
    class _UnavailableToolRegistry:
        async def call_tool(
            self,
            name: str,
            arguments: dict[str, Any],
        ) -> dict[str, Any]:
            raise mcp_client_module.MCPServerUnavailableError(
                f"offline while calling {name}"
            )

    state = {
        state_module.STATE_KEY_TOOL_NAME: "tool.status",
        state_module.STATE_KEY_TOOL_ARGS: {"target": "collector-a"},
    }

    updated = asyncio.run(
        nodes.execute_or_summarize(
            state,
            _UnavailableToolRegistry(),
            "The OpAMP server is currently offline.",
        )
    )

    assert updated[state_module.STATE_KEY_RESPONSE_TEXT] == (
        "The OpAMP server is currently offline."
    )
    assert "offline while calling tool.status" in str(
        updated[state_module.STATE_KEY_TOOL_RESULT]
    )


def test_execute_or_summarize_preserves_plain_text_for_otel_agents() -> None:
    """Verifies agent-list tool results keep their plain-text summary formatting."""
    class _FakeToolRegistry:
        async def call_tool(
            self,
            name: str,
            arguments: dict[str, Any],
        ) -> dict[str, Any]:
            del name, arguments
            plain_text = "I checked and found no OpenTelemetry agents."
            return {
                "content": [
                    {
                        "type": "text",
                        "text": plain_text,
                    }
                ]
            }

    state = {
        state_module.STATE_KEY_TOOL_NAME: "tool_otel_agents",
        state_module.STATE_KEY_TOOL_ARGS: {},
    }
    updated = asyncio.run(nodes.execute_or_summarize(state, _FakeToolRegistry()))
    response = str(updated[state_module.STATE_KEY_RESPONSE_TEXT])
    assert response == "I checked and found no OpenTelemetry agents."
    assert not _looks_like_json_blob(response)


def test_execute_or_summarize_preserves_plain_text_for_commands() -> None:
    """Verifies command execution results keep their concise plain-text summary formatting."""
    class _FakeToolRegistry:
        async def call_tool(
            self,
            name: str,
            arguments: dict[str, Any],
        ) -> dict[str, Any]:
            del name, arguments
            plain_text = (
                "I found 2 available command(s): opamp/restart, Shutdown Agent."
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": plain_text,
                    }
                ]
            }

    state = {
        state_module.STATE_KEY_TOOL_NAME: "tool_commands",
        state_module.STATE_KEY_TOOL_ARGS: {},
    }
    updated = asyncio.run(nodes.execute_or_summarize(state, _FakeToolRegistry()))
    response = str(updated[state_module.STATE_KEY_RESPONSE_TEXT])
    assert "I found 2 available command(s)" in response
    assert "opamp/restart" in response
    assert "Shutdown Agent" in response
    assert not _looks_like_json_blob(response)


def test_execute_or_summarize_executes_tool_even_when_confirmation_flag_present() -> None:
    """Verifies execute_or_summarize still runs the selected tool when confirmation is already satisfied."""
    class _ConfirmToolRegistry:
        async def call_tool(
            self,
            name: str,
            arguments: dict[str, Any],
        ) -> dict[str, Any]:
            assert name == "tool_invoke_custom_command"
            assert arguments == {
                "client_id": "collector-a",
                "operation": "restart",
            }
            return {
                "content": {
                    "status": "queued",
                    "classifier": "opamp",
                    "action": "restart",
                    "client_id": "collector-a",
                }
            }

    state = {
        state_module.STATE_KEY_TOOL_NAME: "tool_invoke_custom_command",
        state_module.STATE_KEY_TOOL_ARGS: {
            "client_id": "collector-a",
            "operation": "restart",
        },
        state_module.STATE_KEY_TARGET: "collector-a",
        state_module.STATE_KEY_REQUIRES_CONFIRMATION: True,
    }

    updated = asyncio.run(
        nodes.execute_or_summarize(
            state,
            _ConfirmToolRegistry(),
        )
    )

    response = str(updated[state_module.STATE_KEY_RESPONSE_TEXT])
    assert "Queued command `opamp/restart` for client `collector-a`." in response


def test_execute_or_summarize_does_not_use_command_catalog_for_confirmation() -> None:
    """Verifies confirmation handling does not depend on command catalog metadata."""
    class _ConfirmToolRegistry:
        async def call_tool(
            self,
            name: str,
            arguments: dict[str, Any],
        ) -> dict[str, Any]:
            assert name == "tool_invoke_custom_command"
            assert arguments == {
                "client_id": "collector-a",
                "operation": "restart",
            }
            return {
                "content": {
                    "status": "queued",
                    "client_id": "collector-a",
                }
            }

    state = {
        state_module.STATE_KEY_TOOL_NAME: "tool_invoke_custom_command",
        state_module.STATE_KEY_TOOL_ARGS: {
            "client_id": "collector-a",
            "operation": "restart",
        },
        state_module.STATE_KEY_TARGET: "collector-a",
        state_module.STATE_KEY_REQUIRES_CONFIRMATION: True,
    }

    updated = asyncio.run(
        nodes.execute_or_summarize(
            state,
            _ConfirmToolRegistry(),
        )
    )

    response = str(updated[state_module.STATE_KEY_RESPONSE_TEXT])
    assert "Queued command for client `collector-a`." in response


def test_execute_or_summarize_applies_ai_formatter_when_available() -> None:
    """Verifies AI formatting is used for tool output when a formatter-capable planner is available."""
    class _FakeToolRegistry:
        async def call_tool(
            self,
            name: str,
            arguments: dict[str, Any],
        ) -> dict[str, Any]:
            del name, arguments
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "raw agent data",
                    }
                ]
            }

    captured: dict[str, Any] = {}

    async def _formatter(
        *,
        user_text: str,
        tool_name: str,
        tool_args: dict[str, Any],
        tool_result: dict[str, Any],
        default_response_text: str,
    ) -> str:
        captured["user_text"] = user_text
        captured["tool_name"] = tool_name
        captured["tool_args"] = tool_args
        captured["tool_result"] = tool_result
        captured["default_response_text"] = default_response_text
        return "*Agent Summary*\n- status: healthy"

    state = {
        state_module.STATE_KEY_NORMALIZED_TEXT: "status collector-a",
        state_module.STATE_KEY_TOOL_NAME: "tool.status",
        state_module.STATE_KEY_TOOL_ARGS: {"target": "collector-a"},
    }
    updated = asyncio.run(
        nodes.execute_or_summarize(
            state,
            _FakeToolRegistry(),
            tool_response_formatter=_formatter,
        )
    )

    response = str(updated[state_module.STATE_KEY_RESPONSE_TEXT])
    assert response == "*Agent Summary*\n- status: healthy"
    assert captured["user_text"] == "status collector-a"
    assert captured["tool_name"] == "tool.status"
    assert captured["tool_args"] == {"target": "collector-a"}
    assert captured["tool_result"] == {
        "content": [{"type": "text", "text": "raw agent data"}]
    }
    assert "raw agent data" in captured["default_response_text"]


def test_execute_or_summarize_calls_formatter_with_keyword_arguments() -> None:
    """Verifies tool-output formatting is invoked with the expected keyword arguments."""
    class _FakeToolRegistry:
        async def call_tool(
            self,
            name: str,
            arguments: dict[str, Any],
        ) -> dict[str, Any]:
            del name, arguments
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "raw data",
                    }
                ]
            }

    async def _keyword_only_formatter(
        *,
        user_text: str,
        tool_name: str,
        tool_args: dict[str, Any],
        tool_result: dict[str, Any],
        default_response_text: str,
    ) -> str:
        assert user_text == "status collector-a"
        assert tool_name == "tool.status"
        assert tool_args == {"target": "collector-a"}
        assert tool_result == {"content": [{"type": "text", "text": "raw data"}]}
        assert "raw data" in default_response_text
        return "formatted output"

    state = {
        state_module.STATE_KEY_NORMALIZED_TEXT: "status collector-a",
        state_module.STATE_KEY_TOOL_NAME: "tool.status",
        state_module.STATE_KEY_TOOL_ARGS: {"target": "collector-a"},
    }
    updated = asyncio.run(
        nodes.execute_or_summarize(
            state,
            _FakeToolRegistry(),
            tool_response_formatter=_keyword_only_formatter,
        )
    )

    assert updated[state_module.STATE_KEY_RESPONSE_TEXT] == "formatted output"


def test_execute_or_summarize_supports_multi_step_replanning() -> None:
    """Verifies execution can replan through multiple tool steps before returning a final response."""
    class _FakePlanner:
        def __init__(self) -> None:
            self.calls = 0

        async def plan(
            self,
            *,
            text: str,
            tools: list[dict[str, Any]],
            conversation_history: list[dict[str, str]] | None = None,
        ) -> dict[str, Any]:
            del tools, conversation_history
            self.calls += 1
            if self.calls == 1:
                assert "Latest executed tool: tool_otel_agents" in text
                return {
                    planner_engine.RESPONSE_TEXT_KEY: "",
                    planner_engine.TOOL_NAME_KEY: "tool_invoke_custom_command",
                    planner_engine.TOOL_ARGS_KEY: {
                        "client_id": "collector-a",
                        "operation": "restart",
                    },
                    planner_engine.REQUIRES_CONFIRMATION_KEY: False,
                }
            return {
                planner_engine.RESPONSE_TEXT_KEY: "Restart command queued for collector-a.",
                planner_engine.TOOL_NAME_KEY: None,
                planner_engine.TOOL_ARGS_KEY: {},
                planner_engine.REQUIRES_CONFIRMATION_KEY: False,
            }

    class _FakeToolRegistry:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        def list_names(self) -> list[str]:
            return ["tool_otel_agents", "tool_invoke_custom_command"]

        def get(self, name: str) -> dict[str, Any]:
            return {"name": name, "description": name}

        async def call_tool(
            self,
            name: str,
            arguments: dict[str, Any],
        ) -> dict[str, Any]:
            self.calls.append((name, dict(arguments)))
            if name == "tool_otel_agents":
                return {
                    "content": {
                        "total": 1,
                        "agents": [{"id": "collector-a"}],
                    }
                }
            if name == "tool_invoke_custom_command":
                return {
                    "content": {
                        "status": "queued",
                        "classifier": "opamp",
                        "action": "restart",
                        "client_id": "collector-a",
                    }
                }
            return {"content": {"status": "unexpected"}}

    planner = _FakePlanner()
    tool_registry = _FakeToolRegistry()
    state = {
        state_module.STATE_KEY_NORMALIZED_TEXT: "restart collector-a",
        state_module.STATE_KEY_TOOL_NAME: "tool_otel_agents",
        state_module.STATE_KEY_TOOL_ARGS: {"host_name": "collector-a"},
        state_module.STATE_KEY_TOOLS_AVAILABLE: [
            "tool_otel_agents",
            "tool_invoke_custom_command",
        ],
    }
    updated = asyncio.run(
        nodes.execute_or_summarize(
            state,
            tool_registry,
            planner=planner,
            max_planning_steps=4,
        )
    )

    assert tool_registry.calls == [
        ("tool_otel_agents", {"host_name": "collector-a"}),
        (
            "tool_invoke_custom_command",
            {"client_id": "collector-a", "operation": "restart"},
        ),
    ]
    assert planner.calls == 2
    assert updated[state_module.STATE_KEY_TOOL_NAME] == "tool_invoke_custom_command"
    assert "Restart command queued for collector-a." in str(
        updated[state_module.STATE_KEY_RESPONSE_TEXT]
    )


def test_execute_or_summarize_does_not_replan_in_api_command_mode() -> None:
    """Verifies API command mode skips multi-step replanning after a tool call."""
    class _FailIfCalledPlanner:
        async def plan(
            self,
            *,
            text: str,
            tools: list[dict[str, Any]],
            conversation_history: list[dict[str, str]] | None = None,
        ) -> dict[str, Any]:
            del text, tools, conversation_history
            raise AssertionError("planner.plan should not be called in api command mode")

    class _FakeToolRegistry:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        async def call_tool(
            self,
            name: str,
            arguments: dict[str, Any],
        ) -> dict[str, Any]:
            self.calls.append((name, dict(arguments)))
            return {
                "content": {
                    "status": "queued",
                    "client_id": "collector-a",
                }
            }

    tool_registry = _FakeToolRegistry()
    state = {
        state_module.STATE_KEY_API_COMMAND_MODE: True,
        state_module.STATE_KEY_TOOL_NAME: "tool_invoke_custom_command",
        state_module.STATE_KEY_TOOL_ARGS: {
            "client_id": "collector-a",
            "operation": "restart",
        },
    }
    updated = asyncio.run(
        nodes.execute_or_summarize(
            state,
            tool_registry,
            planner=_FailIfCalledPlanner(),
            max_planning_steps=4,
        )
    )

    assert len(tool_registry.calls) == 1
    assert "Queued command for client `collector-a`." in str(
        updated[state_module.STATE_KEY_RESPONSE_TEXT]
    )


def test_summarize_mapping_excludes_component_health_field() -> None:
    """Verifies summary rendering omits noisy component-health fields."""
    summary = nodes._summarize_mapping(
        {
            "status": "healthy",
            "component_health": "degraded",
            "details": {
                "uptime": "10m",
                "Component health": "critical",
            },
        }
    )

    assert "status is healthy" in summary
    assert "uptime" in summary
    assert "component_health" not in summary
    assert "Component health" not in summary


def test_summarize_agents_payload_renders_transposed_summary_table() -> None:
    """Verifies agent payload summaries include the transposed attribute-by-agent table."""
    payload = {
        "total": 2,
        "agents": [
            {
                "id": "agent-a",
                "remote_addr": "10.0.0.1",
                "agent_description": (
                    'identifying_attributes { key: "service.name" value { string_value: "orders" } }\n'
                    'identifying_attributes { key: "service.version" value { string_value: "1.0.0" } }\n'
                    'identifying_attributes { key: "host.name" value { string_value: "host-a" } }\n'
                ),
            },
            {
                "id": "agent-b",
                "remote_addr": "10.0.0.2",
                "agent_description": (
                    'identifying_attributes { key: "service.name" value { string_value: "payments" } }\n'
                    'identifying_attributes { key: "service.version" value { string_value: "2.1.4" } }\n'
                    'identifying_attributes { key: "host.name" value { string_value: "host-b" } }\n'
                ),
            },
        ],
    }

    summary = nodes._summarize_agents_payload(payload)
    assert "I found 2 OpenTelemetry agent(s)." in summary
    assert "Summary view (attributes x agents):" in summary
    assert "attribute" in summary
    assert "agent-a" in summary
    assert "agent-b" in summary
    assert "service.name" in summary
    assert "orders" in summary
    assert "payments" in summary


def test_render_agents_summary_table_aligns_and_truncates_cells() -> None:
    """Verifies rendered agent summary tables align columns and truncate oversized cells."""
    very_long_label = "agent-with-a-very-very-long-identifier-for-testing"
    very_long_host = "host-name-that-is-unusually-long-and-should-be-truncated"
    table = nodes._render_agents_summary_table(
        [
            {
                "id": very_long_label,
                "remote_addr": "10.0.0.1",
                "agent_description": (
                    'identifying_attributes { key: "service.name" value { string_value: "orders" } }\n'
                    f'identifying_attributes {{ key: "host.name" value {{ string_value: "{very_long_host}" }} }}\n'
                ),
            },
            {
                "id": "agent-short",
                "remote_addr": "10.0.0.2",
                "agent_description": (
                    'identifying_attributes { key: "service.name" value { string_value: "payments" } }\n'
                    'identifying_attributes { key: "host.name" value { string_value: "host-b" } }\n'
                ),
            },
        ]
    )
    assert table is not None
    lines = table.splitlines()
    assert len(lines) >= 3
    rendered_widths = {len(line) for line in lines}
    assert len(rendered_widths) == 1
    assert "..." in table


def test_render_agent_short_rich_text_includes_only_present_identity_values() -> None:
    """Verifies the short agent renderer includes only identity fields that are present."""
    agent = {
        "client_id": "abc123",
        "remote_addr": "10.0.0.10",
        "agent_description": (
            'identifying_attributes { key: "service.name" value { string_value: "orders-api" } }\n'
            'identifying_attributes { key: "service.version" value { string_value: "1.2.3" } }\n'
            'identifying_attributes { key: "host.name" value { string_value: "otel-host-01" } }\n'
        ),
    }

    rendered = nodes._render_agent_short_rich_text(agent)

    assert "service.name=orders-api" in rendered
    assert "service.version=1.2.3" in rendered
    assert "hostname=otel-host-01" in rendered
    assert "ip=10.0.0.10" in rendered
    assert "mac_address=" not in rendered
    assert "service.type=" not in rendered


def test_render_agent_long_rich_text_uses_openapi_descriptions_when_available() -> None:
    """Verifies the long agent renderer includes OpenAPI field descriptions when available."""
    agent = {
        "client_id": "agent-001",
        "agent_description": (
            'identifying_attributes { key: "service.name" value { string_value: "payments-api" } }\n'
        ),
    }
    openapi_spec = {
        "components": {
            "schemas": {
                "OtelAgent": {
                    "properties": {
                        "client_id": {"description": "Client ID from provider state."}
                    }
                }
            }
        }
    }

    descriptions = nodes._resolve_agent_field_descriptions(openapi_spec)
    rendered = nodes._render_agent_long_rich_text(
        agent,
        field_descriptions=descriptions,
    )

    assert "`client_id`: `agent-001` (Client ID from provider state.)" in rendered
    assert "`service.name`: `payments-api`" in rendered


def test_verify_ai_svc_connection_uses_connection_factory(
    monkeypatch: Any,
) -> None:
    """Verifies AI service verification is delegated through the connection factory."""
    captured: dict[str, Any] = {}

    class _FakeConnection:
        async def verify_connection(self, *, model: str) -> dict[str, Any]:
            captured["model"] = model
            return {"ok": True, "message": "ok"}

    def _fake_create_ai_connection(**kwargs: Any) -> _FakeConnection:
        captured["kwargs"] = kwargs
        return _FakeConnection()

    monkeypatch.setattr(
        ai_svc_planner,
        "create_ai_connection",
        _fake_create_ai_connection,
    )

    result = asyncio.run(
        ai_svc_planner.verify_ai_svc_connection(
            model="gpt-5.4",
            provider="openai",
            timeout_seconds=7,
            api_key_env_var=planner_engine.DEFAULT_AI_SVC_API_KEY_ENV,
            base_url="https://api.openai.com/v1",
        )
    )

    assert result["ok"] is True
    assert captured["kwargs"]["provider"] == "openai"
    assert captured["kwargs"]["timeout_seconds"] == 7
    assert captured["kwargs"]["api_key_env_var"] == planner_engine.DEFAULT_AI_SVC_API_KEY_ENV
    assert captured["kwargs"]["base_url"] == "https://api.openai.com/v1"
    assert captured["kwargs"]["temperature"] == 0.0
    assert captured["kwargs"]["max_completion_tokens"] == 1024
    assert captured["kwargs"]["verify_max_completion_tokens_attempts"] == (64, 512)
    assert captured["kwargs"]["verification_prompt"] == ""
    assert captured["model"] == "gpt-5.4"


def test_verify_ai_svc_connection_template_provider_is_not_ok() -> None:
    """Verifies the template AI provider reports a non-OK verification result."""
    result = asyncio.run(
        ai_svc_planner.verify_ai_svc_connection(
            model="gpt-5.4",
            provider="template",
            timeout_seconds=7,
            api_key_env_var=planner_engine.DEFAULT_AI_SVC_API_KEY_ENV,
            base_url="https://example.invalid/v1",
        )
    )
    assert result["ok"] is False
    assert "not implemented" in str(result["error"])


def test_openai_verify_connection_retries_on_output_limit_error(
    monkeypatch: Any,
) -> None:
    """Verifies OpenAI-compatible verification retries with a larger token limit after an output-limit error."""
    api_key_env_var = planner_engine.DEFAULT_AI_SVC_API_KEY_ENV
    os.environ[api_key_env_var] = "test-key"
    captured_max_tokens: list[int] = []

    class _FakeResponse:
        def __init__(
            self,
            *,
            url: str,
            fail_with_limit_error: bool,
            max_completion_tokens: int,
        ) -> None:
            self._url = url
            self._fail_with_limit_error = fail_with_limit_error
            self._max_completion_tokens = max_completion_tokens

        def raise_for_status(self) -> None:
            if self._fail_with_limit_error:
                request = httpx.Request("POST", self._url)
                response = httpx.Response(
                    400,
                    request=request,
                    text=(
                        '{"error":{"message":"Could not finish the message because '
                        'max_tokens or model output limit was reached."}}'
                    ),
                )
                raise httpx.HTTPStatusError(
                    "verification token limit",
                    request=request,
                    response=response,
                )

        def json(self) -> dict[str, Any]:
            return {
                "usage": {
                    "prompt_tokens": 11,
                    "completion_tokens": 5,
                    "total_tokens": 16,
                },
                "choices": [
                    {
                        "message": {
                            "content": (
                                f"verify ok {self._max_completion_tokens}"
                            )
                        }
                    }
                ],
            }

    class _FakeAsyncClient:
        def __init__(self, timeout: int) -> None:
            self.timeout = timeout

        async def __aenter__(self) -> _FakeAsyncClient:
            return self

        async def __aexit__(
            self,
            exc_type: Any,
            exc: Any,
            tb: Any,
        ) -> bool:
            return False

        async def post(
            self,
            url: str,
            *,
            headers: dict[str, str],
            json: dict[str, Any],
        ) -> _FakeResponse:
            del headers
            captured_max_tokens.append(int(json["max_completion_tokens"]))
            # First attempt fails with output limit; retry succeeds.
            return _FakeResponse(
                url=url,
                fail_with_limit_error=len(captured_max_tokens) == 1,
                max_completion_tokens=int(json["max_completion_tokens"]),
            )

    monkeypatch.setattr(
        openai_compatible_connection.httpx,
        "AsyncClient",
        _FakeAsyncClient,
    )

    connection = openai_compatible_connection.OpenAICompatibleConnection(
        provider="openai",
        api_key_env_var=api_key_env_var,
        base_url="https://api.openai.com/v1",
        timeout_seconds=7,
        verification_prompt="Connection check. Reply with OK.",
    )
    result = asyncio.run(connection.verify_connection(model="gpt-5.4"))

    assert result["ok"] is True
    assert captured_max_tokens == [64, 512]
    assert result["verify_max_completion_tokens_attempts"] == [64, 512]
    assert result["verification_attempt_count"] == 2
    assert result["verification_max_completion_tokens_used"] == 512
    assert result["usage"]["prompt_tokens"] == 11
    assert result["usage"]["completion_tokens"] == 5
    assert result["usage"]["total_tokens"] == 16
    os.environ.pop(api_key_env_var, None)


def test_openai_request_includes_provider_error_details_on_http_failure(
    monkeypatch: Any,
) -> None:
    """Verifies planner request failures include provider error details in the raised exception."""
    api_key_env_var = planner_engine.DEFAULT_AI_SVC_API_KEY_ENV
    os.environ[api_key_env_var] = "test-key"

    class _FakeErrorResponse:
        def __init__(self, *, url: str) -> None:
            self._url = url

        def raise_for_status(self) -> None:
            request = httpx.Request("POST", self._url)
            response = httpx.Response(
                400,
                request=request,
                text=(
                    '{"error":{"message":"Unsupported parameter: max_tokens",'
                    '"type":"invalid_request_error","param":"max_tokens",'
                    '"code":"unsupported_parameter"}}'
                ),
                headers={"content-type": "application/json"},
            )
            raise httpx.HTTPStatusError(
                "planner failure",
                request=request,
                response=response,
            )

    class _FakeAsyncClient:
        def __init__(self, timeout: int) -> None:
            self.timeout = timeout

        async def __aenter__(self) -> _FakeAsyncClient:
            return self

        async def __aexit__(
            self,
            exc_type: Any,
            exc: Any,
            tb: Any,
        ) -> bool:
            return False

        async def post(
            self,
            url: str,
            *,
            headers: dict[str, str],
            json: dict[str, Any],
        ) -> _FakeErrorResponse:
            del headers, json
            return _FakeErrorResponse(url=url)

    monkeypatch.setattr(
        openai_compatible_connection.httpx,
        "AsyncClient",
        _FakeAsyncClient,
    )

    connection = openai_compatible_connection.OpenAICompatibleConnection(
        provider="openai",
        api_key_env_var=api_key_env_var,
        base_url="https://api.openai.com/v1",
        timeout_seconds=7,
    )

    with pytest.raises(RuntimeError) as exc_info:
        asyncio.run(
            connection.request_json_schema_completion(
                model="gpt-5.2",
                messages=[{"role": "user", "content": "hello"}],
                schema_name="broker_plan",
                schema=planner_engine.BROKER_PLAN_JSON_SCHEMA,
            )
        )

    message = str(exc_info.value)
    assert "AI service returned 400 for planner request" in message
    assert "unsupported_parameter" in message
    assert "max_tokens" in message
    os.environ.pop(api_key_env_var, None)


def test_ai_svc_planner_includes_conversation_history_in_prompt() -> None:
    """Verifies AI planner requests include prior conversation history in the prompt payload."""
    captured: dict[str, Any] = {}

    class _FakeConnection:
        provider = "openai"
        api_key_env_var = "OPENAI_API_KEY"
        base_url = "https://api.openai.com/v1"
        timeout_seconds = 10

        def has_api_key(self) -> bool:
            return True

        async def request_json_schema_completion(
            self,
            *,
            model: str,
            messages: list[dict[str, str]],
            schema_name: str,
            schema: dict[str, Any],
            temperature: float | None = None,
            max_completion_tokens: int | None = None,
        ) -> str:
            captured["model"] = model
            captured["messages"] = messages
            captured["schema_name"] = schema_name
            captured["schema"] = schema
            captured["temperature"] = temperature
            captured["max_completion_tokens"] = max_completion_tokens
            return json.dumps(
                {
                    planner_engine.RESPONSE_TEXT_KEY: "",
                    planner_engine.TOOL_NAME_KEY: "tool.status",
                    planner_engine.TOOL_ARGS_KEY: '{"target":"collector-a"}',
                    planner_engine.REQUIRES_CONFIRMATION_KEY: False,
                }
            )

        async def verify_connection(self, *, model: str) -> dict[str, Any]:
            del model
            return {"ok": True}

    planner = ai_svc_planner.AISvcPlanner(
        model="gpt-5.4",
        connection=_FakeConnection(),
        system_prompt="planner system prompt",
        temperature=0.1,
    )
    plan = asyncio.run(
        planner.plan(
            text="confirm",
            tools=[{"name": "tool.status", "inputSchema": {"type": "object"}}],
            conversation_history=[
                {"role": "assistant", "content": "I can run restart for collector-a."},
                {"role": "user", "content": "confirm"},
            ],
        )
    )

    assert plan[planner_engine.TOOL_NAME_KEY] == "tool.status"
    assert captured["model"] == "gpt-5.4"
    assert captured["schema_name"] == "broker_plan"
    assert captured["schema"] == planner_engine.BROKER_PLAN_JSON_SCHEMA
    assert captured["temperature"] == 0.1
    assert captured["max_completion_tokens"] is None
    request_payload = json.loads(captured["messages"][1]["content"])
    assert request_payload["request_text"] == "confirm"
    assert request_payload["conversation_history"] == [
        {"role": "assistant", "content": "I can run restart for collector-a."},
        {"role": "user", "content": "confirm"},
    ]


def test_ai_svc_planner_formats_tool_response_for_slack() -> None:
    """Verifies AI planner formatting requests build the Slack-specific response payload."""
    captured: dict[str, Any] = {}

    class _FakeConnection:
        provider = "openai"
        api_key_env_var = "OPENAI_API_KEY"
        base_url = "https://api.openai.com/v1"
        timeout_seconds = 10

        def has_api_key(self) -> bool:
            return True

        async def request_json_schema_completion(
            self,
            *,
            model: str,
            messages: list[dict[str, str]],
            schema_name: str,
            schema: dict[str, Any],
            temperature: float | None = None,
            max_completion_tokens: int | None = None,
        ) -> str:
            captured["model"] = model
            captured["messages"] = messages
            captured["schema_name"] = schema_name
            captured["schema"] = schema
            captured["temperature"] = temperature
            captured["max_completion_tokens"] = max_completion_tokens
            return json.dumps({"formatted_text": "*Result*\n- status: healthy"})

        async def verify_connection(self, *, model: str) -> dict[str, Any]:
            del model
            return {"ok": True}

    planner = ai_svc_planner.AISvcPlanner(
        model="gpt-5.4",
        connection=_FakeConnection(),
        system_prompt="planner system prompt",
        temperature=0.1,
    )

    formatted = asyncio.run(
        planner.format_tool_response_for_slack(
            user_text="status collector-a",
            tool_name="tool.status",
            tool_args={"target": "collector-a"},
            tool_result={
                "status": "healthy",
                "Component health": "degraded",
                "content": [{"type": "text", "text": "healthy"}],
            },
            default_response_text="Tool result: status is healthy.",
        )
    )

    assert formatted == "*Result*\n- status: healthy"
    assert captured["model"] == "gpt-5.4"
    assert captured["schema_name"] == "broker_slack_tool_response"
    assert (
        captured["schema"]
        == ai_svc_planner.SLACK_FORMAT_RESULT_JSON_SCHEMA
    )
    assert captured["temperature"] == 0.1
    assert captured["max_completion_tokens"] is None
    assert captured["messages"][0]["role"] == "system"
    assert (
        captured["messages"][0]["content"]
        == ai_svc_planner.DEFAULT_SLACK_FORMAT_SYSTEM_PROMPT
    )
    formatter_payload = json.loads(captured["messages"][1]["content"])
    assert formatter_payload["user_request_text"] == "status collector-a"
    assert formatter_payload["tool_name"] == "tool.status"
    assert formatter_payload["tool_args"] == {"target": "collector-a"}
    assert formatter_payload["default_response_text"] == "Tool result: status is healthy."
    assert "healthy" in formatter_payload["tool_result_json"]
    assert "Component health" not in formatter_payload["tool_result_json"]
