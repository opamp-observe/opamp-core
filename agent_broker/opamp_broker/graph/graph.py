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

"""LangGraph construction for the broker conversation decision flow.

This module assembles nodes and edges in one location so behavior changes can be
reviewed as topology updates instead of scattered registration calls.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from opamp_broker.graph.constants import (
    EDGE_CLASSIFY_TO_PLAN,
    EDGE_NORMALIZE_TO_CLASSIFY,
    EDGE_PLAN_TO_EXECUTE,
    NODE_CLASSIFY_INTENT,
    NODE_EXECUTE_OR_SUMMARIZE,
    NODE_NORMALIZE_INPUT,
    NODE_PLAN_ACTION,
)
from opamp_broker.graph.nodes import (
    DEFAULT_MCP_SERVER_OFFLINE_MESSAGE,
    PLANNER_MAX_EXECUTION_STEPS_DEFAULT,
    classify_intent,
    execute_or_summarize,
    normalize_input,
    plan_action,
)
from opamp_broker.graph.state import STATE_KEY_AI_ENABLED, BrokerState
from opamp_broker.mcp.tools import MCPToolRegistry
from opamp_broker.planner import create_planner
from opamp_broker.planner.ai_svc_planner import AISvcPlanner
from opamp_broker.planner.rule_first_planner import RuleFirstPlanner


def build_graph(
    tool_registry: MCPToolRegistry,
    config: dict | None = None,
):
    """Compile and return the broker conversation graph.

    Why this approach:
    dependency injection for ``tool_registry`` lets node logic remain pure while
    still reaching MCP tooling via closures at runtime.

    Args:
        tool_registry: Registry used by planning/execution nodes for tool lookup.
        config: Runtime broker config used to construct the planner strategy.

    Returns:
        Any: A compiled LangGraph runnable supporting ``ainvoke``.
    """
    cfg = config or {}
    planner = create_planner(cfg)
    ai_planner = planner if isinstance(planner, AISvcPlanner) else None
    rule_planner = RuleFirstPlanner()
    planner_cfg = cfg.get("planner", {}) if isinstance(cfg, dict) else {}
    max_execution_steps_raw = (
        planner_cfg.get("max_execution_steps")
        if isinstance(planner_cfg, dict)
        else None
    )
    if max_execution_steps_raw is None:
        max_execution_steps = PLANNER_MAX_EXECUTION_STEPS_DEFAULT
    else:
        try:
            max_execution_steps = int(max_execution_steps_raw)
        except (TypeError, ValueError):
            max_execution_steps = PLANNER_MAX_EXECUTION_STEPS_DEFAULT
    offline_message = (
        cfg.get("messages", {}).get("server_offline")
        if isinstance(cfg, dict)
        else None
    )
    if not isinstance(offline_message, str) or not offline_message.strip():
        offline_message = DEFAULT_MCP_SERVER_OFFLINE_MESSAGE

    graph = StateGraph(BrokerState)
    graph.add_node(NODE_NORMALIZE_INPUT, normalize_input)
    graph.add_node(NODE_CLASSIFY_INTENT, classify_intent)

    async def _plan_action_node(state: BrokerState) -> BrokerState:
        """Bridge injected planner dependencies into async plan node."""
        ai_enabled = bool(state.get(STATE_KEY_AI_ENABLED, True))
        planner_impl = ai_planner if (ai_planner is not None and ai_enabled) else rule_planner
        return await plan_action(
            state,
            tool_registry,
            planner_impl,
            offline_message,
        )

    async def _execute_or_summarize_node(state: BrokerState) -> BrokerState:
        """Bridge injected MCP dependencies into async execution node."""
        formatter = None
        planner_impl = None
        ai_enabled = bool(state.get(STATE_KEY_AI_ENABLED, True))
        if ai_planner is not None and ai_enabled:
            formatter = ai_planner.format_tool_response_for_slack
            planner_impl = ai_planner
        return await execute_or_summarize(
            state,
            tool_registry,
            offline_message,
            tool_response_formatter=formatter,
            planner=planner_impl,
            max_planning_steps=max_execution_steps,
        )

    graph.add_node(
        NODE_PLAN_ACTION,
        _plan_action_node,
    )
    graph.add_node(
        NODE_EXECUTE_OR_SUMMARIZE,
        _execute_or_summarize_node,
    )

    graph.set_entry_point(NODE_NORMALIZE_INPUT)
    graph.add_edge(*EDGE_NORMALIZE_TO_CLASSIFY)
    graph.add_edge(*EDGE_CLASSIFY_TO_PLAN)
    graph.add_edge(*EDGE_PLAN_TO_EXECUTE)
    graph.add_edge(NODE_EXECUTE_OR_SUMMARIZE, END)
    return graph.compile()
