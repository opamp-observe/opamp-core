# Copyright 2026 mp3monster.org
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

"""Tests for broker startup, shutdown, and CLI/logging behavior."""

from __future__ import annotations

import asyncio
import importlib
import json
import logging
import os
import subprocess
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_BROKER_ROOT = REPO_ROOT / "agent_broker"
if str(AGENT_BROKER_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_BROKER_ROOT))


def _install_dependency_stubs() -> None:
    if "langgraph.graph" not in sys.modules:
        langgraph_module = types.ModuleType("langgraph")
        langgraph_graph_module = types.ModuleType("langgraph.graph")
        langgraph_graph_module.END = "END"

        class _DummyStateGraph:
            def __init__(self, *_args: Any, **_kwargs: Any) -> None:
                return None

            def add_node(self, *_args: Any, **_kwargs: Any) -> None:
                return None

            def set_entry_point(self, *_args: Any, **_kwargs: Any) -> None:
                return None

            def add_edge(self, *_args: Any, **_kwargs: Any) -> None:
                return None

            def compile(self) -> object:
                return object()

        langgraph_graph_module.StateGraph = _DummyStateGraph
        langgraph_module.graph = langgraph_graph_module
        sys.modules["langgraph"] = langgraph_module
        sys.modules["langgraph.graph"] = langgraph_graph_module

    if "slack_bolt.async_app" not in sys.modules:
        slack_bolt_module = types.ModuleType("slack_bolt")
        slack_bolt_async_app_module = types.ModuleType("slack_bolt.async_app")

        class _DummyAsyncApp:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                return None

        slack_bolt_async_app_module.AsyncApp = _DummyAsyncApp
        slack_bolt_module.async_app = slack_bolt_async_app_module
        sys.modules["slack_bolt"] = slack_bolt_module
        sys.modules["slack_bolt.async_app"] = slack_bolt_async_app_module

    if "slack_bolt.adapter.socket_mode.async_handler" not in sys.modules:
        slack_adapter_module = types.ModuleType("slack_bolt.adapter")
        slack_socket_mode_module = types.ModuleType("slack_bolt.adapter.socket_mode")
        slack_async_handler_module = types.ModuleType(
            "slack_bolt.adapter.socket_mode.async_handler"
        )

        class _DummyAsyncSocketModeHandler:
            def __init__(self, *_args: Any, **_kwargs: Any) -> None:
                return None

            async def start_async(self) -> None:
                return None

        slack_async_handler_module.AsyncSocketModeHandler = _DummyAsyncSocketModeHandler
        slack_socket_mode_module.async_handler = slack_async_handler_module
        slack_adapter_module.socket_mode = slack_socket_mode_module
        sys.modules["slack_bolt.adapter"] = slack_adapter_module
        sys.modules["slack_bolt.adapter.socket_mode"] = slack_socket_mode_module
        sys.modules["slack_bolt.adapter.socket_mode.async_handler"] = (
            slack_async_handler_module
        )


_install_dependency_stubs()
broker_app = importlib.import_module("opamp_broker.broker_app")


def test_broker_app_imports_shared_when_started_from_agent_broker_cwd() -> None:
    """Verifies source-tree command-line starts can import repo-level shared modules."""
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import opamp_broker.broker_app; import shared.observability; print('ok')",
        ],
        cwd=str(AGENT_BROKER_ROOT),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "ok" in completed.stdout


def _base_config(send_shutdown_goodbye: bool) -> dict[str, Any]:
    return {
        "broker": {
            "log_level": "INFO",
            "idle_timeout_seconds": 1200,
            "sweeper_interval_seconds": 30,
            "send_idle_goodbye": True,
            "send_shutdown_goodbye": send_shutdown_goodbye,
        },
        "messages": {
            "idle_goodbye": "idle",
            "shutdown_goodbye": "shutdown",
            "help": "help",
        },
        "derived": {"provider_routes": {"mcp_url": "http://mcp.example.invalid"}},
        "mcp": {
            "request_timeout_seconds": 15,
            "startup_discovery_max_attempts": 1,
            "startup_discovery_initial_backoff_seconds": 0.0,
            "startup_discovery_max_backoff_seconds": 0.0,
            "startup_discovery_backoff_multiplier": 1.0,
            "startup_discovery_jitter_seconds": 0.0,
        },
        "slack": {"command_name": "/opamp"},
        "social_collaboration": {"implementation": "slack"},
        "planner": {"llm_enabled": True, "AIState": "on"},
    }


async def _run_main_with_fakes(
    monkeypatch: pytest.MonkeyPatch,
    *,
    refresh_raises: Exception | None = None,
    send_shutdown_goodbye: bool = True,
    llm_enabled: bool | None = None,
    ai_state: str | None = None,
    ai_config_complete: bool = True,
    social_collaboration_implementation: str | None = None,
    verify_startup: str = "none",
    social_verify_result: dict[str, Any] | None = None,
    ai_svc_verify_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    captured: dict[str, Any] = {"register_handlers_calls": []}
    config = _base_config(send_shutdown_goodbye=send_shutdown_goodbye)
    if llm_enabled is not None:
        config["planner"]["llm_enabled"] = llm_enabled
    if ai_state is not None:
        config["planner"]["AIState"] = ai_state

    class FakeLogger:
        def __init__(self) -> None:
            self.info_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
            self.warning_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
            self.error_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

        def info(self, *args: Any, **kwargs: Any) -> None:
            self.info_calls.append((args, kwargs))

        def warning(self, *args: Any, **kwargs: Any) -> None:
            self.warning_calls.append((args, kwargs))

        def error(self, *args: Any, **kwargs: Any) -> None:
            self.error_calls.append((args, kwargs))

    class FakeMCPClient:
        instances: list[FakeMCPClient] = []

        def __init__(
            self,
            mcp_url: str,
            timeout_seconds: int = 30,
            **kwargs: Any,
        ) -> None:
            self.mcp_url = mcp_url
            self.timeout_seconds = timeout_seconds
            self.kwargs = kwargs
            self.closed = False
            FakeMCPClient.instances.append(self)

        async def close(self) -> None:
            self.closed = True

    class FakeToolRegistry:
        instances: list[FakeToolRegistry] = []

        def __init__(self, client: FakeMCPClient) -> None:
            self.client = client
            self.refreshed = False
            FakeToolRegistry.instances.append(self)

        async def refresh(self) -> None:
            if refresh_raises is not None:
                raise refresh_raises
            self.refreshed = True

    class FakeSessionManager:
        instances: list[FakeSessionManager] = []

        def __init__(self, default_ai_mode: str = "on") -> None:
            self.default_ai_mode = default_ai_mode
            self.deleted: list[str] = []
            self.sessions = [
                SimpleNamespace(
                    channel_id="C123",
                    thread_ts="T123",
                    key="K123",
                ),
                SimpleNamespace(
                    channel_id="C456",
                    thread_ts="T456",
                    key="K456",
                ),
            ]
            FakeSessionManager.instances.append(self)

        async def all_sessions(self) -> list[SimpleNamespace]:
            return list(self.sessions)

        async def delete(self, key: str) -> None:
            self.deleted.append(key)

        async def upsert(
            self,
            team_id: str,
            channel_id: str,
            thread_ts: str,
            user_id: str | None = None,
        ) -> SimpleNamespace:
            return SimpleNamespace(key=f"{team_id}:{channel_id}:{thread_ts}")

        async def update(self, key: str, **kwargs: Any) -> None:
            return None

    class FakeSweeper:
        instances: list[FakeSweeper] = []

        def __init__(
            self,
            session_manager: FakeSessionManager,
            idle_timeout_seconds: int,
            interval_seconds: int,
            on_expire: Any,
        ) -> None:
            self.session_manager = session_manager
            self.idle_timeout_seconds = idle_timeout_seconds
            self.interval_seconds = interval_seconds
            self.on_expire = on_expire
            self.stop_called = False
            FakeSweeper.instances.append(self)

        async def run(self) -> None:
            await asyncio.sleep(3600)

        def stop(self) -> None:
            self.stop_called = True

    fake_logger = FakeLogger()
    graph_sentinel = object()
    real_loop = asyncio.get_running_loop()
    post_messages: list[dict[str, Any]] = []

    class FakeLoop:
        def __init__(self) -> None:
            self._callback_scheduled = False

        def add_signal_handler(self, sig: Any, callback: Any) -> None:
            if not self._callback_scheduled:
                self._callback_scheduled = True
                real_loop.call_soon(callback)

    fake_loop = FakeLoop()

    class FakeSocialCollaborationAdapter:
        def __init__(self, implementation: str) -> None:
            self.implementation = implementation
            self.registered = False

        def register_handlers(
            self,
            session_manager: FakeSessionManager,
            compiled_graph: Any,
            cfg: dict[str, Any],
        ) -> None:
            self.registered = True
            captured["register_handlers_calls"].append(
                {
                    "session_manager": session_manager,
                    "compiled_graph": compiled_graph,
                    "config": cfg,
                }
            )

        async def start(self) -> None:
            captured["social_collaboration_started"] = True
            await asyncio.sleep(3600)

        async def post_message(
            self, *, channel_id: str, thread_ts: str, text: str
        ) -> None:
            post_messages.append(
                {"channel": channel_id, "thread_ts": thread_ts, "text": text}
            )

        async def verify_connection(self) -> dict[str, Any]:
            return social_verify_result or {"ok": True, "message": "social ok"}

    class FakeAIConnection:
        def __init__(self, has_api_key: bool) -> None:
            self._has_api_key = has_api_key

        def has_api_key(self) -> bool:
            return self._has_api_key

        async def verify_connection(self, *, model: str) -> dict[str, Any]:
            return ai_svc_verify_result or {"ok": True, "message": "ai svc ok", "model": model}

    def fake_create_ai_connection(**kwargs: Any) -> FakeAIConnection:
        captured["ai_connection_factory_kwargs"] = kwargs
        return FakeAIConnection(ai_config_complete)

    def fake_create_social_collaboration_adapter(
        implementation: str,
    ) -> FakeSocialCollaborationAdapter:
        captured["social_collaboration_implementation"] = implementation
        adapter = FakeSocialCollaborationAdapter(implementation)
        captured["social_collaboration_adapter"] = adapter
        return adapter

    monkeypatch.setattr(broker_app, "load_dotenv", lambda: None)
    monkeypatch.setattr(
        broker_app,
        "get_effective_config_path",
        lambda _config_path=None: Path("/tmp/broker.ui_responses.json"),
    )
    monkeypatch.setattr(
        broker_app,
        "load_runtime_config",
        lambda _config_path=None: config,
    )
    monkeypatch.setattr(broker_app, "configure_logging", lambda _level: None)
    monkeypatch.setattr(broker_app, "MCPClient", FakeMCPClient)
    monkeypatch.setattr(broker_app, "MCPToolRegistry", FakeToolRegistry)
    monkeypatch.setattr(
        broker_app,
        "build_graph",
        lambda _registry, _config=None: graph_sentinel,
    )
    monkeypatch.setattr(broker_app, "SessionManager", FakeSessionManager)
    monkeypatch.setattr(broker_app, "SessionSweeper", FakeSweeper)
    monkeypatch.setattr(
        broker_app,
        "create_social_collaboration_adapter",
        fake_create_social_collaboration_adapter,
    )
    monkeypatch.setattr(
        broker_app,
        "create_ai_connection",
        fake_create_ai_connection,
    )
    monkeypatch.setattr(broker_app, "logger", fake_logger)
    monkeypatch.setattr(broker_app.asyncio, "get_running_loop", lambda: fake_loop)
    startup_ok = await broker_app.main(
        social_collaboration_implementation=social_collaboration_implementation,
        verify_startup=verify_startup,
    )

    captured["logger"] = fake_logger
    captured["startup_ok"] = startup_ok
    captured["post_messages"] = post_messages
    captured["graph"] = graph_sentinel
    captured["mcp_client"] = FakeMCPClient.instances[0] if FakeMCPClient.instances else None
    captured["tool_registry"] = (
        FakeToolRegistry.instances[0] if FakeToolRegistry.instances else None
    )
    captured["session_manager"] = (
        FakeSessionManager.instances[0] if FakeSessionManager.instances else None
    )
    captured["sweeper"] = FakeSweeper.instances[0] if FakeSweeper.instances else None
    return captured


def test_main_startup_and_shutdown_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies the broker starts core services and shuts them down cleanly."""
    captured = asyncio.run(_run_main_with_fakes(monkeypatch, send_shutdown_goodbye=True))

    assert captured["social_collaboration_implementation"] == "slack"
    assert captured["register_handlers_calls"], "handlers should be registered"
    first_call = captured["register_handlers_calls"][0]
    assert first_call["compiled_graph"] is captured["graph"]
    assert first_call["config"]["broker"]["send_shutdown_goodbye"] is True

    assert captured["tool_registry"].refreshed is True
    assert captured["sweeper"].stop_called is True
    assert captured["mcp_client"].closed is True
    assert captured["session_manager"].deleted == ["K123", "K456"]
    assert captured["post_messages"] == [
        {"channel": "C123", "thread_ts": "T123", "text": "shutdown"},
        {"channel": "C456", "thread_ts": "T456", "text": "shutdown"},
    ]
    assert any(
        args == ("using broker config path: %s", Path("/tmp/broker.ui_responses.json"))
        for args, _kwargs in captured["logger"].info_calls
    )


def test_main_continues_when_tool_refresh_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies startup continues even when initial MCP tool discovery fails."""
    captured = asyncio.run(
        _run_main_with_fakes(
            monkeypatch,
            refresh_raises=RuntimeError("refresh failed"),
            send_shutdown_goodbye=False,
        )
    )

    assert captured["register_handlers_calls"], "main should continue after refresh failure"
    assert captured["mcp_client"].closed is True
    assert captured["post_messages"] == []
    assert captured["session_manager"].deleted == []
    assert captured["logger"].warning_calls
    first_warning_args, first_warning_kwargs = captured["logger"].warning_calls[0]
    assert str(first_warning_args[0]).startswith("initial tool discovery failed")
    assert first_warning_kwargs["extra"]["event"] == "mcp.tools.discovery_failed"
    assert first_warning_kwargs["extra"]["context"]["error"] == "refresh failed"


def test_main_uses_cli_social_collaboration_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies the CLI social-collaboration override wins over config values."""
    captured = asyncio.run(
        _run_main_with_fakes(
            monkeypatch,
            social_collaboration_implementation="slack",
        )
    )
    assert captured["social_collaboration_implementation"] == "slack"


def test_main_sets_disabled_default_ai_mode_when_llm_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies disabled LLM planning forces sessions into disabled AI mode."""
    captured = asyncio.run(
        _run_main_with_fakes(
            monkeypatch,
            llm_enabled=False,
        )
    )
    assert captured["session_manager"].default_ai_mode == broker_app.AI_MODE_DISABLED


def test_main_uses_configured_ai_state_off_when_ai_is_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies configured AI mode `off` is respected when AI dependencies are ready."""
    captured = asyncio.run(
        _run_main_with_fakes(
            monkeypatch,
            ai_state="off",
            ai_config_complete=True,
        )
    )
    assert captured["session_manager"].default_ai_mode == broker_app.AI_MODE_OFF


def test_main_uses_configured_ai_state_disabled_even_when_ai_is_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies configured AI mode `disabled` is preserved even with AI available."""
    captured = asyncio.run(
        _run_main_with_fakes(
            monkeypatch,
            ai_state="disabled",
            ai_config_complete=True,
        )
    )
    assert captured["session_manager"].default_ai_mode == broker_app.AI_MODE_DISABLED


def test_main_forces_disabled_when_ai_config_incomplete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies incomplete AI configuration downgrades runtime AI mode to disabled."""
    captured = asyncio.run(
        _run_main_with_fakes(
            monkeypatch,
            ai_state="on",
            ai_config_complete=False,
        )
    )
    assert captured["session_manager"].default_ai_mode == broker_app.AI_MODE_DISABLED


def test_main_startup_verification_all_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies startup verification exits successfully when all checks pass."""
    captured = asyncio.run(
        _run_main_with_fakes(
            monkeypatch,
            verify_startup="all",
            social_verify_result={"ok": True, "message": "social ok"},
            ai_svc_verify_result={"ok": True, "message": "ai ok"},
        )
    )

    assert captured["startup_ok"] is True
    assert captured["mcp_client"] is None
    assert captured["register_handlers_calls"] == []


def test_main_startup_verification_all_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies startup verification returns failure when social and AI checks fail."""
    captured = asyncio.run(
        _run_main_with_fakes(
            monkeypatch,
            verify_startup="all",
            social_verify_result={"ok": False, "error": "slack bad"},
            ai_svc_verify_result={"ok": False, "error": "ai bad"},
        )
    )

    assert captured["startup_ok"] is False
    assert captured["mcp_client"] is None
    assert captured["register_handlers_calls"] == []
    assert captured["logger"].error_calls


def test_load_logging_config_uses_file_without_overriding_root_level(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verifies file-based logging config preserves the root logger level."""
    logging_path = tmp_path / "broker_logging.json"
    logging_path.write_text(
        json.dumps(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "handlers": {},
                "root": {"level": "DEBUG", "handlers": []},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(broker_app.ENV_BROKER_LOGGING_CONFIG_PATH, str(logging_path))

    config, config_path = broker_app._load_logging_config("INFO")

    assert config_path == logging_path
    assert config["root"]["level"] == "DEBUG"


def test_configure_logging_warns_when_broker_log_level_is_ignored(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verifies a warning is logged when broker log level is overridden by file config."""
    logging_path = tmp_path / "broker_logging.json"
    logging_path.write_text(
        json.dumps(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "handlers": {},
                "root": {"level": "DEBUG", "handlers": []},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(broker_app.ENV_BROKER_LOGGING_CONFIG_PATH, str(logging_path))

    captured_config: dict[str, Any] = {}

    monkeypatch.setattr(
        broker_app.logging.config,
        "dictConfig",
        lambda config: captured_config.update({"config": config}),
    )
    with caplog.at_level(logging.WARNING, logger=broker_app.__name__):
        broker_app.configure_logging("INFO")

    assert captured_config["config"]["root"]["level"] == "DEBUG"
    assert "ignored because logging config file is present" in caplog.text


def test_build_cli_parser_help_includes_version_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies CLI help text includes broker version details and runtime options."""
    monkeypatch.setattr(
        broker_app,
        "load_component_version_info",
        lambda: {
            "version": "v1.2.3 abcdef123456 (23 Apr 2026 12:00:00 UTC+00:00)",
            "git_label": "v1.2.3",
            "git_commit": "abcdef123456",
            "git_commit_date_friendly": "23 Apr 2026 12:00:00 UTC+00:00",
        },
    )
    parser = broker_app._build_cli_parser()
    help_text = parser.format_help()

    assert "-h, --help" in help_text
    assert "--config-path" in help_text
    assert "--social-collaboration" in help_text
    assert "--verify-startup" in help_text
    assert "--version" in help_text
    assert "Version details:" in help_text
    assert "git_label: v1.2.3" in help_text
    assert "git_commit: abcdef123456" in help_text
    assert "git_commit_date: 23 Apr 2026 12:00:00 UTC+00:00" in help_text
