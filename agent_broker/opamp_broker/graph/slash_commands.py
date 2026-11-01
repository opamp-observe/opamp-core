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

"""Helpers for slash-command control flow in broker planning nodes.

This module isolates the `/...` command-mode logic so `nodes.py` can focus on
general planning and execution flow.
"""

from __future__ import annotations

from opamp_broker.graph.state import (
    STATE_KEY_API_COMMAND_MODE,
    STATE_KEY_DIRECT_TOOL_ARGS,
    STATE_KEY_DIRECT_TOOL_NAME,
    STATE_KEY_REQUIRES_CONFIRMATION,
    STATE_KEY_RESPONSE_TEXT,
    STATE_KEY_TARGET,
    STATE_KEY_TOOL_ARGS,
    STATE_KEY_TOOL_NAME,
    BrokerState,
)


def apply_slash_command_overrides(
    state: BrokerState,
    tool_names: list[str],
) -> bool:
    """Apply slash-command direct-tool shortcuts before planner usage.

    Returns:
        bool: ``True`` when the request was fully handled and planning should
        stop, ``False`` when standard planner flow should continue.
    """
    api_command_mode = bool(state.get(STATE_KEY_API_COMMAND_MODE, False))
    direct_tool_name_raw = state.get(STATE_KEY_DIRECT_TOOL_NAME)
    direct_tool_name = (
        str(direct_tool_name_raw).strip()
        if isinstance(direct_tool_name_raw, str)
        else ""
    )
    if api_command_mode and direct_tool_name:
        if direct_tool_name not in tool_names:
            state[STATE_KEY_RESPONSE_TEXT] = (
                f"Unknown tool `{direct_tool_name}`. Use `/opamp tools`."
            )
            return True
        direct_tool_args_raw = state.get(STATE_KEY_DIRECT_TOOL_ARGS, {})
        direct_tool_args = (
            direct_tool_args_raw
            if isinstance(direct_tool_args_raw, dict)
            else {}
        )
        state[STATE_KEY_TOOL_NAME] = direct_tool_name
        state[STATE_KEY_TOOL_ARGS] = direct_tool_args
        state[STATE_KEY_REQUIRES_CONFIRMATION] = False
        direct_target = direct_tool_args.get(STATE_KEY_TARGET)
        state[STATE_KEY_TARGET] = (
            str(direct_target) if direct_target is not None else None
        )
        return True

    return False
