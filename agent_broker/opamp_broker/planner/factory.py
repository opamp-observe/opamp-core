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

"""Runtime factory for selecting planner implementations."""

from __future__ import annotations

from typing import Any

from opamp_broker.planner.ai_connection import AIConnection
from opamp_broker.planner.ai_connection_factory import (
    create_ai_connection,
    resolve_ai_runtime_settings,
)
from opamp_broker.planner.ai_svc_planner import AISvcPlanner
from opamp_broker.planner.rule_first_planner import RuleFirstPlanner
from opamp_broker.planner.types import Planner


def _build_ai_connection(runtime_settings: dict[str, Any]) -> AIConnection:
    """Build provider transport from normalized runtime settings.

    Why this helper exists:
    planner construction has a "fail-safe" branch that falls back to
    ``RuleFirstPlanner`` when provider configuration is invalid. Keeping the
    connection build in one helper makes that fail-safe boundary explicit.
    """
    return create_ai_connection(
        provider=str(runtime_settings["provider"]),
        api_key_env_var=str(runtime_settings["api_key_env_var"]),
        base_url=str(runtime_settings["base_url"]),
        timeout_seconds=int(runtime_settings["timeout_seconds"]),
        temperature=float(runtime_settings["temperature"]),
        max_completion_tokens=(
            int(runtime_settings["max_completion_tokens"])
            if runtime_settings["max_completion_tokens"] is not None
            else None
        ),
        verify_max_completion_tokens_attempts=tuple(
            int(value)
            for value in runtime_settings["verify_max_completion_tokens_attempts"]
        ),
        verification_prompt=str(runtime_settings["verification_prompt"]),
    )


def create_planner(config: dict[str, Any]) -> Planner:
    """Create the runtime planner from broker config with safe fallback behavior.

    Fail-safe behavior:
    when AI configuration is invalid, unsupported, or missing credentials, this
    function returns ``RuleFirstPlanner`` so broker command handling continues
    deterministically instead of failing startup.
    """
    runtime_settings = resolve_ai_runtime_settings(config)
    if not runtime_settings["llm_enabled"]:
        return RuleFirstPlanner()

    try:
        ai_connection = _build_ai_connection(runtime_settings)
    except ValueError:
        return RuleFirstPlanner()

    if not ai_connection.has_api_key():
        return RuleFirstPlanner()

    return AISvcPlanner(
        model=str(runtime_settings["model"]),
        connection=ai_connection,
        system_prompt=str(runtime_settings["system_prompt"]),
        slack_format_system_prompt=str(runtime_settings["slack_format_system_prompt"]),
        temperature=float(runtime_settings["temperature"]),
    )
