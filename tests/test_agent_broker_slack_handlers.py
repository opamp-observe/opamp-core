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

"""Tests for broker Slack command parsing and AI mode handling."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_BROKER_ROOT = REPO_ROOT / "agent_broker"
if str(AGENT_BROKER_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_BROKER_ROOT))


def _install_dependency_stubs() -> None:
    if "slack_bolt.async_app" in sys.modules:
        return

    slack_bolt_module = types.ModuleType("slack_bolt")
    slack_bolt_async_app_module = types.ModuleType("slack_bolt.async_app")

    class _DummyAsyncApp:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            return None

    slack_bolt_async_app_module.AsyncApp = _DummyAsyncApp
    slack_bolt_module.async_app = slack_bolt_async_app_module
    sys.modules["slack_bolt"] = slack_bolt_module
    sys.modules["slack_bolt.async_app"] = slack_bolt_async_app_module


_install_dependency_stubs()
handlers = importlib.import_module("opamp_broker.slack.handlers")


def test_extract_ai_mode_directive_handles_ai_off_with_and_without_remainder() -> None:
    """Verifies `AI Off` directives are detected with or without trailing text."""
    assert handlers._extract_ai_mode_directive("AI Off") == (
        handlers.AI_MODE_OFF,
        "",
    )
    assert handlers._extract_ai_mode_directive("AI Off status collector-a") == (
        handlers.AI_MODE_OFF,
        "status collector-a",
    )


def test_extract_ai_mode_directive_handles_ai_on_and_non_directive_text() -> None:
    """Verifies `AI On` directives are detected and plain text is left unchanged."""
    assert handlers._extract_ai_mode_directive("AI On, status collector-a") == (
        handlers.AI_MODE_ON,
        "status collector-a",
    )
    assert handlers._extract_ai_mode_directive("status collector-a") == (
        None,
        "status collector-a",
    )


def test_normalize_mode_command_text_removes_mentions_and_normalizes_spacing() -> None:
    """Verifies mode-command parsing ignores mentions and extra whitespace."""
    normalized = handlers._normalize_mode_command_text(" <@U123>   AI   Off  ")
    assert normalized == handlers.AI_MODE_OFF_EXACT_COMMAND


def test_ai_off_ack_text_matches_required_response() -> None:
    """Verifies the default AI-off acknowledgement text stays stable."""
    assert handlers.AI_MODE_OFF_ACK_TEXT == "Affirmative, Dave. I read you."


def test_resolve_ai_mode_off_ack_text_uses_configured_value() -> None:
    """Verifies configured AI-off acknowledgement text overrides the default."""
    configured = handlers._resolve_ai_mode_off_ack_text(
        {
            handlers.MESSAGE_KEY_AI_MODE_OFF_ACK_TEXT: "custom off ack",
        }
    )
    assert configured == "custom off ack"


def test_resolve_ai_mode_off_ack_text_falls_back_to_default() -> None:
    """Verifies missing AI-off acknowledgement config falls back to the default text."""
    configured = handlers._resolve_ai_mode_off_ack_text({})
    assert configured == handlers.AI_MODE_OFF_ACK_TEXT


def test_build_ai_mode_changed_text_supports_disabled_mode() -> None:
    """Verifies AI mode change messaging includes the disabled state wording."""
    assert (
        handlers._build_ai_mode_changed_text(handlers.AI_MODE_DISABLED)
        == handlers.AI_MODE_DISABLED_LOCK_TEXT
    )


def test_disabled_mode_blocks_ui_switches() -> None:
    """Verifies disabled deployments reject UI requests to switch AI mode."""
    assert handlers._is_ai_mode_ui_switch_allowed(handlers.AI_MODE_DISABLED) is False


def test_parse_api_command_requires_leading_slash() -> None:
    """Verifies strict API command parsing rejects messages without a slash prefix."""
    assert handlers._parse_api_command("api help") is None


def test_parse_api_command_supports_help_tools_and_call() -> None:
    """Verifies the parser accepts the supported help, tools, and call verbs."""
    help_request = handlers._parse_api_command("/opamp help")
    assert help_request is not None
    assert "immediate_response" in help_request

    tools_request = handlers._parse_api_command("/opamp tools status")
    assert tools_request is not None
    assert tools_request["verb"] == handlers.API_VERB_TOOLS
    assert tools_request["planner_text"] == "tools"
    assert tools_request["tools_filter"] == "status"

    call_request = handlers._parse_api_command(
        '/opamp call tool_status target=collector-a env="prod us"',
    )
    assert call_request is not None
    assert call_request["verb"] == handlers.API_VERB_CALL
    assert call_request["direct_tool_name"] == "tool_status"
    assert call_request["direct_tool_args"] == {
        "target": "collector-a",
        "env": "prod us",
    }


def test_parse_api_command_parses_json_and_rejects_mixed_call_args() -> None:
    """Verifies `/opamp call` accepts JSON args and rejects mixed arg styles."""
    json_request = handlers._parse_api_command(
        '/opamp call tool_status --json \'{"target":"collector-a"}\'',
    )
    assert json_request is not None
    assert json_request["direct_tool_args"] == {"target": "collector-a"}

    mixed_request = handlers._parse_api_command(
        '/opamp call tool_status --json \'{"target":"collector-a"}\' target=abc',
    )
    assert mixed_request is not None
    assert "Use either key=value arguments or `--json`, not both." in mixed_request["error"]


def test_parse_api_command_still_accepts_legacy_opamp_api_prefix() -> None:
    """Verifies the legacy `/opamp api` prefix still routes through strict parsing."""
    legacy_request = handlers._parse_api_command("/opamp api tools status")
    assert legacy_request is not None
    assert legacy_request["verb"] == handlers.API_VERB_TOOLS


def test_register_handlers_does_not_require_action_registration() -> None:
    """Verifies handler registration works even when Slack actions are unavailable."""
    class _FakeApp:
        def command(self, _name: str) -> Any:
            def _decorator(func: Any) -> Any:
                return func

            return _decorator

        def event(self, _name: str) -> Any:
            def _decorator(func: Any) -> Any:
                return func

            return _decorator

    class _FakeSessionManager:
        pass

    handlers.register_handlers(
        _FakeApp(),
        _FakeSessionManager(),
        object(),
        {
            "slack": {"command_name": "/opamp"},
            "messages": {"help": "help"},
        },
    )
