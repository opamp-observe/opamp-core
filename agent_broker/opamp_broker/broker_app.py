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
#
# Attribution: opamp_broker runtime orchestration maintained by mp3monster.org.
"""Application entrypoint that wires configuration, Slack I/O, MCP, and sessions.

This module centralizes lifecycle orchestration so startup and shutdown behavior
stays in one place. Keeping the sequence in a single coroutine simplifies
resource management for async components like socket mode and session sweeping.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import logging.config
import os
import random
import signal
import sys
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _add_source_tree_repo_root_to_path() -> None:
    """Make repo-level shared modules importable when run from source checkout."""
    try:
        repo_root = Path(__file__).resolve().parents[2]
    except IndexError:  # pragma: no cover - defensive for unusual import loaders
        return
    if (repo_root / "shared").is_dir() is not True:
        return
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)


_add_source_tree_repo_root_to_path()

from dotenv import load_dotenv
from hypercorn.asyncio import serve
from hypercorn.config import Config as HypercornConfig
from shared.observability import (
    attach_observability,
    configure_process_observability,
    load_observability_config_from_payload,
)

from opamp_broker.component_version import (
    component_version_text,
    load_component_version_info,
)
from opamp_broker.config.loader import get_effective_config_path, load_runtime_config
from opamp_broker.graph.graph import build_graph
from opamp_broker.mcp.client import MCPClient
from opamp_broker.mcp.proxy import MCPProxyService, create_mcp_proxy_app
from opamp_broker.mcp.tools import MCPToolRegistry
from opamp_broker.planner.ai_connection_factory import (
    create_ai_connection,
    resolve_ai_runtime_settings,
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
from opamp_broker.session.sweeper import SessionSweeper
from opamp_broker.social_collaboration.factory import (
    create_social_collaboration_adapter,
)

ENV_BROKER_LOGGING_CONFIG_PATH = "OPAMP_BROKER_LOGGING_CONFIG"
DEFAULT_BROKER_LOGGING_CONFIG_FILENAME = "broker_logging.json"
DEFAULT_SOCIAL_COLLABORATION_IMPLEMENTATION = "slack"
STARTUP_VERIFICATION_CHOICES = ("none", "social", "ai_svc", "all")
AI_STATE_CONFIG_KEY = "AIState"
AI_STATE_CONFIG_KEY_ALT = "ai_state"
AI_STATE_ALLOWED_VALUES = (AI_MODE_ON, AI_MODE_OFF, AI_MODE_DISABLED)


def _normalize_log_level_name(log_level: str | int | None) -> str:
    """Return a valid logging level name for dictConfig."""
    if isinstance(log_level, int):
        normalized = logging.getLevelName(log_level)
        if isinstance(normalized, str):
            return normalized.upper()
        return "INFO"
    normalized = str(log_level or "INFO").strip().upper()
    resolved = logging.getLevelName(normalized)
    if isinstance(resolved, int):
        return normalized
    return "INFO"


def _default_logging_config(level_name: str) -> dict[str, Any]:
    """Return fallback logging config used when file loading is unavailable."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "{\"timestamp\":\"%(asctime)s\",\"level\":\"%(levelname)s\","
                "\"logger\":\"%(name)s\",\"message\":\"%(message)s\"}",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            }
        },
        "root": {"level": level_name, "handlers": ["console"]},
    }


def _normalize_logging_config_levels(
    config: dict[str, Any],
    fallback_level_name: str,
) -> dict[str, Any]:
    """Normalize dictConfig level fields so case variants like ``debug`` are valid."""
    root_config = config.get("root")
    if isinstance(root_config, dict):
        root_level = root_config.get("level", fallback_level_name)
        root_config["level"] = _normalize_log_level_name(root_level)

    handlers = config.get("handlers")
    if isinstance(handlers, dict):
        for handler_config in handlers.values():
            if isinstance(handler_config, dict) and "level" in handler_config:
                handler_config["level"] = _normalize_log_level_name(
                    handler_config.get("level")
                )

    loggers = config.get("loggers")
    if isinstance(loggers, dict):
        for logger_config in loggers.values():
            if isinstance(logger_config, dict) and "level" in logger_config:
                logger_config["level"] = _normalize_log_level_name(
                    logger_config.get("level")
                )

    return config


def _load_logging_config(level_name: str) -> tuple[dict[str, Any], Path | None]:
    """Load broker logging dictConfig and return source path when file-backed."""
    configured_path = os.getenv(ENV_BROKER_LOGGING_CONFIG_PATH)
    config_path = Path(configured_path) if configured_path else Path(__file__).with_name(
        DEFAULT_BROKER_LOGGING_CONFIG_FILENAME
    )
    if config_path.is_file():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            if isinstance(config, dict):
                config.setdefault("version", 1)
                config.setdefault("disable_existing_loggers", False)
                _normalize_logging_config_levels(
                    config,
                    fallback_level_name=level_name,
                )
                return config, config_path
        except Exception as exc:  # pragma: no cover - defensive fallback.
            print(
                f"failed to load broker logging config {config_path}: {exc}",
                file=sys.stderr,
            )
    return _default_logging_config(level_name), None


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging via dictConfig with level overrides."""
    level_name = _normalize_log_level_name(level)
    config, config_path = _load_logging_config(level_name)
    logging.config.dictConfig(config)
    if config_path is not None:
        logging.getLogger(__name__).warning(
            "broker.log_level=%s ignored because logging config file is present: %s",
            level_name,
            str(config_path),
        )


logger = logging.getLogger(__name__)


def _build_cli_parser() -> argparse.ArgumentParser:
    """Build broker CLI parser for runtime config and adapter selection."""
    version_info = load_component_version_info()
    version_text = str(version_info.get("version", component_version_text()))
    version_epilog = "\n".join(
        [
            "Version details:",
            f"  version: {version_text}",
            f"  git_label: {version_info.get('git_label', 'unknown')}",
            f"  git_commit: {version_info.get('git_commit', 'unknown')}",
            f"  git_commit_date: {version_info.get('git_commit_date_friendly', 'unknown')}",
        ]
    )
    parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter,
        description="OpAMP conversation broker runtime.",
        epilog=version_epilog,
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="show this help message (including version details) and exit",
    )
    parser.add_argument(
        "--config-path",
        type=str,
        help=(
            "optional explicit broker config path; defaults to BROKER_CONFIG_PATH "
            "or bundled config"
        ),
    )
    parser.add_argument(
        "--social-collaboration",
        type=str,
        default=None,
        help=(
            "social collaboration implementation to use "
            f"(default: {DEFAULT_SOCIAL_COLLABORATION_IMPLEMENTATION})"
        ),
    )
    parser.add_argument(
        "--verify-startup",
        type=str,
        choices=STARTUP_VERIFICATION_CHOICES,
        default="none",
        help=(
            "run startup connection checks and exit. "
            "Options: none, social, ai_svc, all"
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version_text}",
    )
    return parser


def _resolve_social_collaboration_implementation(
    config: dict[str, Any],
    cli_override: str | None,
) -> str:
    """Resolve desired social collaboration implementation from CLI/config."""
    if cli_override and str(cli_override).strip():
        return str(cli_override).strip().lower()
    social_collaboration = config.get("social_collaboration", {})
    if isinstance(social_collaboration, dict):
        configured_implementation = social_collaboration.get("implementation")
        if configured_implementation and str(configured_implementation).strip():
            return str(configured_implementation).strip().lower()
    return DEFAULT_SOCIAL_COLLABORATION_IMPLEMENTATION


def _is_startup_verification_enabled(mode: str) -> bool:
    """Return whether startup verification mode should run."""
    return mode in {"social", "ai_svc", "all"}


def _resolve_mcp_proxy_settings(config: dict[str, Any]) -> dict[str, Any]:
    """Resolve broker-hosted MCP proxy listener settings."""
    mcp_server = config.get("mcp_server", {})
    if not isinstance(mcp_server, dict):
        mcp_server = {}
    path = str(mcp_server.get("path", "/mcp")).strip() or "/mcp"
    if not path.startswith("/"):
        path = f"/{path}"
    return {
        "enabled": bool(mcp_server.get("enabled", False)),
        "host": str(mcp_server.get("host", "127.0.0.1")).strip() or "127.0.0.1",
        "port": int(mcp_server.get("port", 8080)),
        "path": path,
    }


def _resolve_planner_runtime_settings(config: dict[str, Any]) -> dict[str, Any]:
    """Resolve planner runtime settings and key-presence diagnostics."""
    return resolve_ai_runtime_settings(config)


def _normalize_ai_state(value: Any) -> str:
    """Normalize configured AI state values with a safe default."""
    candidate = str(value or "").strip().lower()
    if candidate in AI_STATE_ALLOWED_VALUES:
        return candidate
    return AI_MODE_ON


def _resolve_configured_ai_state(config: dict[str, Any]) -> str:
    """Resolve configured initial AI state from runtime config."""
    planner_cfg = config.get("planner", {}) if isinstance(config, dict) else {}
    if not isinstance(planner_cfg, dict):
        return AI_MODE_ON
    configured_state = planner_cfg.get(
        AI_STATE_CONFIG_KEY,
        planner_cfg.get(AI_STATE_CONFIG_KEY_ALT, AI_MODE_ON),
    )
    return _normalize_ai_state(configured_state)


def _build_ai_connection_for_runtime_settings(
    runtime_settings: dict[str, Any],
):
    """Create AI transport from normalized runtime settings."""
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


def _resolve_default_client_ai_mode(config: dict[str, Any]) -> str:
    """Resolve initial per-client AI mode from config and AI readiness checks.

    Rules:
    1. `planner.AIState=disabled` always wins and locks mode.
    2. If AI config is incomplete, mode is forced to `disabled`.
    3. Otherwise `planner.AIState` (`on` or `off`) is used as the initial mode.
    """
    configured_ai_state = _resolve_configured_ai_state(config)
    if configured_ai_state == AI_MODE_DISABLED:
        return AI_MODE_DISABLED

    planner_settings = _resolve_planner_runtime_settings(config)
    if not bool(planner_settings.get("llm_enabled", True)):
        logger.warning(
            "AI mode forced to DISABLED because planner.llm_enabled is false.",
            extra={
                "event": "broker.ai_mode.forced_disabled",
                "context": {
                    "reason": "planner.llm_enabled=false",
                    "configured_ai_state": configured_ai_state,
                },
            },
        )
        return AI_MODE_DISABLED

    try:
        ai_connection = _build_ai_connection_for_runtime_settings(planner_settings)
    except Exception as exc:
        logger.warning(
            "AI mode forced to DISABLED because AI config is incomplete: %s",
            str(exc),
            extra={
                "event": "broker.ai_mode.forced_disabled",
                "context": {
                    "reason": str(exc),
                    "configured_ai_state": configured_ai_state,
                },
            },
        )
        return AI_MODE_DISABLED

    if not ai_connection.has_api_key():
        reason = (
            "missing API key value for env var "
            f"{planner_settings['api_key_env_var']}"
        )
        logger.warning(
            "AI mode forced to DISABLED because AI config is incomplete: %s",
            reason,
            extra={
                "event": "broker.ai_mode.forced_disabled",
                "context": {
                    "reason": reason,
                    "configured_ai_state": configured_ai_state,
                },
            },
        )
        return AI_MODE_DISABLED

    return configured_ai_state if configured_ai_state in {AI_MODE_ON, AI_MODE_OFF} else AI_MODE_ON


def _resolve_mcp_retry_settings(config: dict[str, Any]) -> dict[str, Any]:
    """Resolve MCP discovery retry settings from runtime config with safe defaults."""
    mcp_config = config.get("mcp", {}) if isinstance(config, dict) else {}
    if not isinstance(mcp_config, dict):
        mcp_config = {}

    def _coerce_int(value: Any, default: int, minimum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        return max(minimum, parsed)

    def _coerce_float(value: Any, default: float, minimum: float) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            parsed = default
        return max(minimum, parsed)

    attempts = _coerce_int(
        mcp_config.get("startup_discovery_max_attempts", 5),
        default=5,
        minimum=1,
    )
    initial_backoff_seconds = _coerce_float(
        mcp_config.get("startup_discovery_initial_backoff_seconds", 0.5),
        default=0.5,
        minimum=0.0,
    )
    max_backoff_seconds = _coerce_float(
        mcp_config.get("startup_discovery_max_backoff_seconds", 5.0),
        default=5.0,
        minimum=0.0,
    )
    backoff_multiplier = _coerce_float(
        mcp_config.get("startup_discovery_backoff_multiplier", 2.0),
        default=2.0,
        minimum=1.0,
    )
    jitter_seconds = _coerce_float(
        mcp_config.get("startup_discovery_jitter_seconds", 0.25),
        default=0.25,
        minimum=0.0,
    )

    return {
        "attempts": attempts,
        "initial_backoff_seconds": initial_backoff_seconds,
        "max_backoff_seconds": max_backoff_seconds,
        "backoff_multiplier": backoff_multiplier,
        "jitter_seconds": jitter_seconds,
    }


def _resolve_mcp_connection_settings(config: dict[str, Any]) -> dict[str, Any]:
    """Resolve MCP connection strategy from runtime config."""
    mcp_config = config.get("mcp", {}) if isinstance(config, dict) else {}
    if not isinstance(mcp_config, dict):
        mcp_config = {}

    connection_mode = str(mcp_config.get("connection_mode", "auto")).strip().lower()
    if connection_mode not in {"auto", "json", "sse"}:
        connection_mode = "auto"

    protocol_attempts_value = mcp_config.get(
        "protocol_version_attempts",
        ["2025-06-18", "2025-03-26"],
    )
    parsed_protocol_attempts: list[str] = []
    if isinstance(protocol_attempts_value, str):
        parsed_protocol_attempts = [
            item.strip()
            for item in protocol_attempts_value.split(",")
            if item.strip()
        ]
    elif isinstance(protocol_attempts_value, list):
        parsed_protocol_attempts = [
            str(item).strip()
            for item in protocol_attempts_value
            if str(item).strip()
        ]
    if not parsed_protocol_attempts:
        parsed_protocol_attempts = ["2025-06-18", "2025-03-26"]

    return {
        "connection_mode": connection_mode,
        "protocol_version_attempts": tuple(parsed_protocol_attempts),
    }


async def _refresh_tools_with_backoff(
    *,
    tool_registry: MCPToolRegistry,
    mcp_url: str,
    retry_settings: dict[str, Any],
) -> None:
    """Refresh MCP tools with retry/backoff to tolerate provider startup lag."""
    max_attempts = int(retry_settings["attempts"])
    initial_backoff_seconds = float(retry_settings["initial_backoff_seconds"])
    max_backoff_seconds = float(retry_settings["max_backoff_seconds"])
    backoff_multiplier = float(retry_settings["backoff_multiplier"])
    jitter_seconds = float(retry_settings["jitter_seconds"])
    current_backoff_seconds = initial_backoff_seconds

    for attempt_index in range(1, max_attempts + 1):
        try:
            await tool_registry.refresh()
            if attempt_index > 1:
                logger.info(
                    "MCP tool discovery recovered after retries",
                    extra={
                        "event": "mcp.tools.discovery_retry_recovered",
                        "context": {
                            "attempt": attempt_index,
                            "max_attempts": max_attempts,
                            "mcp_url": mcp_url,
                        },
                    },
                )
            return
        except Exception as exc:
            if attempt_index >= max_attempts:
                raise
            jitter_value = random.uniform(0.0, jitter_seconds) if jitter_seconds > 0 else 0.0  # noqa: S311
            sleep_seconds = min(max_backoff_seconds, current_backoff_seconds) + jitter_value
            logger.info(
                "MCP tool discovery attempt %s/%s failed; retrying in %.2fs",
                attempt_index,
                max_attempts,
                sleep_seconds,
                extra={
                    "event": "mcp.tools.discovery_retry_scheduled",
                    "context": {
                        "attempt": attempt_index,
                        "max_attempts": max_attempts,
                        "mcp_url": mcp_url,
                        "retry_delay_seconds": sleep_seconds,
                        "error": str(exc),
                    },
                },
            )
            await asyncio.sleep(sleep_seconds)
            current_backoff_seconds = min(
                max_backoff_seconds,
                current_backoff_seconds * backoff_multiplier,
            )


async def _run_startup_verification(
    *,
    config: dict[str, Any],
    social_collaboration_implementation: str,
    verify_startup: str,
) -> bool:
    """Run requested startup verification checks and log each outcome."""
    checks_passed = True

    if verify_startup in {"social", "all"}:
        try:
            adapter = create_social_collaboration_adapter(
                social_collaboration_implementation
            )
            social_result = await adapter.verify_connection()
        except Exception as exc:
            social_result = {"ok": False, "error": str(exc)}

        if social_result.get("ok"):
            logger.info(
                "***** social collaboration verification succeeded *****",
                extra={
                    "event": "broker.verification.social.success",
                    "context": {
                        "implementation": social_collaboration_implementation,
                        "result": social_result,
                    },
                },
            )
        else:
            checks_passed = False
            logger.error(
                "***** social collaboration verification failed *****",
                extra={
                    "event": "broker.verification.social.failed",
                    "context": {
                        "implementation": social_collaboration_implementation,
                        "result": social_result,
                    },
                },
            )

    if verify_startup in {"ai_svc", "all"}:
        planner_settings = _resolve_planner_runtime_settings(config)
        logger.info(
            "***** AI service verification parameters: provider=%s model=%s base_url=%s api_key_env_var=%s timeout_seconds=%s api_key_present=%s temperature=%s max_completion_tokens=%s verify_max_completion_tokens_attempts=%s prompts_config_path=%s *****",
            planner_settings["provider"],
            planner_settings["model"],
            planner_settings["base_url"],
            planner_settings["api_key_env_var"],
            planner_settings["timeout_seconds"],
            planner_settings["api_key_present"],
            planner_settings["temperature"],
            planner_settings["max_completion_tokens"],
            planner_settings["verify_max_completion_tokens_attempts"],
            planner_settings["prompts_config_path"],
            extra={
                "event": "broker.verification.ai_svc.parameters",
                "context": planner_settings,
            },
        )
        try:
            ai_connection = _build_ai_connection_for_runtime_settings(planner_settings)
        except Exception as exc:
            ai_svc_result = {"ok": False, "error": str(exc)}
        else:
            ai_svc_result = await ai_connection.verify_connection(
                model=str(planner_settings["model"]),
            )
        if ai_svc_result.get("ok"):
            logger.info(
                "***** AI service verification succeeded *****",
                extra={
                    "event": "broker.verification.ai_svc.success",
                    "context": ai_svc_result,
                },
            )
        else:
            checks_passed = False
            failure_reason = str(ai_svc_result.get("error", "unknown verification error"))
            logger.error(
                "***** AI service verification failed: %s *****",
                failure_reason,
                extra={
                    "event": "broker.verification.ai_svc.failed",
                    "context": ai_svc_result,
                },
            )

    logger.info(
        "startup verification complete",
        extra={
            "event": "broker.verification.complete",
            "context": {
                "verify_startup": verify_startup,
                "checks_passed": checks_passed,
            },
        },
    )
    return checks_passed


async def main(
    *,
    config_path: str | None = None,
    social_collaboration_implementation: str | None = None,
    verify_startup: str = "none",
) -> bool:
    """Start the broker runtime and keep it alive until shutdown is requested.

    Why this is structured this way:
    startup is ordered to fail fast on missing credentials, then initialize MCP
    and tool discovery before registering Slack handlers, so requests do not hit
    a half-initialized runtime.

    Returns:
        bool: ``True`` on successful startup flow/verification, else ``False``.
    """
    load_dotenv()
    broker_started_at_utc = datetime.now(timezone.utc).isoformat()
    effective_config_path = get_effective_config_path(config_path)
    config = load_runtime_config(config_path)
    configure_logging(config["broker"]["log_level"])
    logger.info("using broker config path: %s", effective_config_path)
    observability_config = load_observability_config_from_payload(config)
    configure_process_observability(
        service_name="opamp-broker",
        config=observability_config,
        log_level=getattr(
            logging,
            str(config["broker"]["log_level"]).strip().upper(),
            logging.INFO,
        ),
    )
    selected_social_collaboration_implementation = (
        _resolve_social_collaboration_implementation(
            config,
            social_collaboration_implementation,
        )
    )
    mcp_connection_settings = _resolve_mcp_connection_settings(config)
    logger.info(
        "broker starting",
        extra={
            "event": "broker.start",
            "context": {
                **config["derived"]["provider_routes"],
                "social_collaboration_implementation": (
                    selected_social_collaboration_implementation
                ),
                "mcp_connection_mode": mcp_connection_settings["connection_mode"],
                "mcp_protocol_version_attempts": list(
                    mcp_connection_settings["protocol_version_attempts"]
                ),
            },
        },
    )

    if _is_startup_verification_enabled(verify_startup):
        return await _run_startup_verification(
            config=config,
            social_collaboration_implementation=(
                selected_social_collaboration_implementation
            ),
            verify_startup=verify_startup,
        )

    mcp_client = MCPClient(
        config["derived"]["provider_routes"]["mcp_url"],
        timeout_seconds=config["mcp"]["request_timeout_seconds"],
        **mcp_connection_settings,
    )
    tool_registry = MCPToolRegistry(mcp_client)
    mcp_retry_settings = _resolve_mcp_retry_settings(config)
    mcp_proxy_settings = _resolve_mcp_proxy_settings(config)
    mcp_proxy_service: MCPProxyService | None = None
    mcp_proxy_shutdown_event: asyncio.Event | None = None
    mcp_proxy_task: asyncio.Task[Any] | None = None
    try:
        await _refresh_tools_with_backoff(
            tool_registry=tool_registry,
            mcp_url=config["derived"]["provider_routes"]["mcp_url"],
            retry_settings=mcp_retry_settings,
        )
    except Exception as exc:
        logger.warning(
            "initial tool discovery failed: mcp_url=%s error=%s",
            config["derived"]["provider_routes"]["mcp_url"],
            str(exc),
            extra={
                "event": "mcp.tools.discovery_failed",
                "context": {
                    "mcp_url": config["derived"]["provider_routes"]["mcp_url"],
                    "error": str(exc),
                },
            },
        )

    if mcp_proxy_settings["enabled"]:
        mcp_proxy_service = MCPProxyService(
            mcp_url=config["derived"]["provider_routes"]["mcp_url"],
            timeout_seconds=config["mcp"]["request_timeout_seconds"],
            connection_mode=mcp_connection_settings["connection_mode"],
            protocol_version_attempts=mcp_connection_settings[
                "protocol_version_attempts"
            ],
        )
        mcp_proxy_app = create_mcp_proxy_app(
            proxy_service=mcp_proxy_service,
            mcp_path=mcp_proxy_settings["path"],
        )
        attach_observability(
            mcp_proxy_app,
            service_name="opamp-broker",
            config=observability_config,
            log_level=getattr(
                logging,
                str(config["broker"]["log_level"]).strip().upper(),
                logging.INFO,
            ),
        )
        mcp_proxy_config = HypercornConfig()
        mcp_proxy_config.bind = [
            f"{mcp_proxy_settings['host']}:{mcp_proxy_settings['port']}"
        ]
        mcp_proxy_shutdown_event = asyncio.Event()
        mcp_proxy_task = asyncio.create_task(
            serve(
                mcp_proxy_app,
                mcp_proxy_config,
                shutdown_trigger=mcp_proxy_shutdown_event.wait,
            ),
            name="mcp-proxy-http",
        )
        logger.info(
            "broker MCP proxy listening at http://%s:%s%s",
            mcp_proxy_settings["host"],
            mcp_proxy_settings["port"],
            mcp_proxy_settings["path"],
            extra={
                "event": "broker.mcp_proxy.started",
                "context": {
                    "host": mcp_proxy_settings["host"],
                    "port": mcp_proxy_settings["port"],
                    "path": mcp_proxy_settings["path"],
                },
            },
        )

    graph = build_graph(tool_registry, config)
    default_ai_mode = _resolve_default_client_ai_mode(config)
    session_manager = SessionManager(default_ai_mode=default_ai_mode)
    try:
        social_collaboration_adapter = create_social_collaboration_adapter(
            selected_social_collaboration_implementation
        )
    except KeyError as exc:
        if (
            mcp_proxy_settings["enabled"]
            and selected_social_collaboration_implementation == "slack"
        ):
            logger.warning(
                "Slack credentials were not available; falling back to MCP-only broker mode because mcp_server.enabled=true: %s",
                exc,
            )
            selected_social_collaboration_implementation = "none"
            social_collaboration_adapter = create_social_collaboration_adapter("none")
        else:
            raise
    social_collaboration_adapter.register_handlers(
        session_manager,
        graph,
        config,
    )

    async def on_expire(channel_id: str, thread_ts: str, session_key: str) -> None:
        """Handle idle-session expiry by notifying collaboration channel and clearing state.

        Why this callback exists:
        session cleanup logic is injected into the sweeper to keep expiration
        policy separate from session traversal logic.

        Args:
            channel_id: Collaboration channel containing the expired conversation.
            thread_ts: Collaboration thread/message id for reply targeting.
            session_key: Internal session identifier to remove.

        Returns:
            None: Sends optional notification and deletes the session.
        """
        if config["broker"]["send_idle_goodbye"]:
            await social_collaboration_adapter.post_message(
                channel_id=channel_id,
                thread_ts=thread_ts,
                text=config["messages"]["idle_goodbye"],
            )
        await session_manager.delete(session_key)

    sweeper = SessionSweeper(
        session_manager=session_manager,
        idle_timeout_seconds=config["broker"]["idle_timeout_seconds"],
        interval_seconds=config["broker"]["sweeper_interval_seconds"],
        on_expire=on_expire,
    )
    sweeper_task = asyncio.create_task(sweeper.run(), name="session-sweeper")
    social_collaboration_task = asyncio.create_task(
        social_collaboration_adapter.start(),
        name=f"{selected_social_collaboration_implementation}-social-collaboration",
    )

    stop_event = asyncio.Event()

    async def shutdown() -> None:
        """Stop background tasks and flush goodbye messages before exit.

        Why this is explicit:
        chat-visible shutdown messages and client closure are best-effort work
        that should happen before process termination to avoid dangling context.

        Returns:
            None: Signals the main loop to continue teardown.
        """
        logger.info("shutdown requested", extra={"event": "broker.shutdown_requested"})
        sweeper.stop()
        if config["broker"]["send_shutdown_goodbye"]:
            sessions = await session_manager.all_sessions()
            for session in sessions:
                with suppress(Exception):
                    await social_collaboration_adapter.post_message(
                        channel_id=session.channel_id,
                        thread_ts=session.thread_ts,
                        text=config["messages"]["shutdown_goodbye"],
                    )
                await session_manager.delete(session.key)
        cumulative_tokens = OpenAICompatibleConnection.get_cumulative_tokens_since_startup()
        logger.info(
            "AI token totals since startup input_tokens=%s output_tokens=%s total_tokens=%s broker_started_at_utc=%s",
            cumulative_tokens["input_tokens"],
            cumulative_tokens["output_tokens"],
            cumulative_tokens["total_tokens"],
            broker_started_at_utc,
            extra={
                "event": "broker.shutdown.ai_token_totals",
                "context": {
                    **cumulative_tokens,
                    "broker_started_at_utc": broker_started_at_utc,
                },
            },
        )
        if mcp_proxy_shutdown_event is not None:
            mcp_proxy_shutdown_event.set()
        if mcp_proxy_service is not None:
            await mcp_proxy_service.close()
        await mcp_client.close()
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))

    await stop_event.wait()

    tasks_to_cancel = [sweeper_task, social_collaboration_task]
    if mcp_proxy_task is not None:
        tasks_to_cancel.append(mcp_proxy_task)
    for task in tasks_to_cancel:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
    return True


def run() -> None:
    """Synchronous wrapper for console-script entrypoint execution.

    Why this approach:
    packaging entrypoints expect a sync callable, so this wrapper bridges to the
    async runtime by owning event-loop creation.

    Returns:
        None: Blocks until the broker runtime exits.
    """
    args = _build_cli_parser().parse_args()
    startup_ok = asyncio.run(
        main(
            config_path=args.config_path,
            social_collaboration_implementation=args.social_collaboration,
            verify_startup=args.verify_startup,
        )
    )
    if _is_startup_verification_enabled(args.verify_startup) and not startup_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
