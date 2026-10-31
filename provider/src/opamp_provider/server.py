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

"""CLI entrypoint for the OpAMP provider server."""

from __future__ import annotations

import argparse
import json
import logging
import logging.config
import os
import pathlib
import sys
from typing import Any

from opamp_provider import config as provider_config
from opamp_provider.app import app, set_state_restore_status
from opamp_provider.component_version import component_version_text
from opamp_provider.state import STORE
from opamp_provider.state_persistence import (
    RESTORE_AUTO,
    resolve_restore_snapshot_path,
    restore_state_snapshot,
)
from shared.observability import attach_observability

ENV_PROVIDER_LOGGING_CONFIG_PATH = "OPAMP_PROVIDER_LOGGING_CONFIG"
DEFAULT_PROVIDER_LOGGING_CONFIG_FILENAME = "provider_logging.json"


def _normalize_log_level_name(log_level: str | int | None) -> str:
    """Return canonical logging level name for dictConfig usage."""
    if isinstance(log_level, int):
        level_name = logging.getLevelName(log_level)
        if isinstance(level_name, str):
            return level_name.upper()
        return "INFO"
    return str(log_level or "INFO").strip().upper() or "INFO"


def _default_logging_config(level_name: str) -> dict[str, Any]:
    """Return fallback logging dictConfig when no config file is available."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
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


def _load_logging_config(level_name: str) -> dict[str, Any]:
    """Load provider logging dictConfig from env/default path with fallback."""
    configured_path = os.getenv(ENV_PROVIDER_LOGGING_CONFIG_PATH)
    config_path = (
        pathlib.Path(configured_path)
        if configured_path
        else pathlib.Path(__file__).with_name(DEFAULT_PROVIDER_LOGGING_CONFIG_FILENAME)
    )
    if config_path.is_file():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            if isinstance(config, dict):
                config.setdefault("version", 1)
                config.setdefault("disable_existing_loggers", False)
                root = config.setdefault("root", {})
                if isinstance(root, dict):
                    root["level"] = level_name
                return config
        except Exception as exc:  # pragma: no cover - defensive fallback.
            print(
                f"failed to load provider logging config {config_path}: {exc}",
                file=sys.stderr,
            )
    return _default_logging_config(level_name)


def _configure_logging(log_level: str | int | None) -> None:
    """Configure logging with dictConfig while preserving test harness handlers."""
    level_name = _normalize_log_level_name(log_level)
    root_logger = logging.getLogger()
    if root_logger.handlers:
        logging.config.dictConfig(
            {
                "version": 1,
                "incremental": True,
                "root": {"level": level_name},
            }
        )
        return
    logging.config.dictConfig(_load_logging_config(level_name))


def _provider_tls_run_kwargs(config: provider_config.ProviderConfig) -> dict[str, str]:
    """Return Quart TLS run kwargs for configured provider TLS settings."""
    tls_config = config.tls
    if tls_config is None:
        return {}
    return {
        "certfile": tls_config.cert_file,
        "keyfile": tls_config.key_file,
    }


def _emit_bootstrap_line(message: str) -> None:
    """Emit one immediate bootstrap line before standard logging is ready."""
    print(f"[provider-bootstrap] {message}", file=sys.stderr, flush=True)


def _build_argument_parser(version_text: str) -> argparse.ArgumentParser:
    """Build the provider CLI argument parser."""
    parser = argparse.ArgumentParser(
        description=f"OpAMP provider server. Version: {version_text}"
    )
    parser.add_argument("--config-path", type=str)
    parser.add_argument(
        "--diagnostic",
        action="store_true",
        help=(
            "enable diagnostic-only UI/API features and force DEBUG logging "
            "(intended for local troubleshooting)"
        ),
    )
    parser.add_argument("--host", type=str, default="127.0.0.1", help="bind address")
    parser.add_argument(
        "--port",
        type=int,
        help="port for the OpAMP provider/web UI (defaults to config webui_port)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        help="logging level name override (for example DEBUG, INFO, WARNING)",
    )
    parser.add_argument(
        "--restore",
        nargs="?",
        const=RESTORE_AUTO,
        default=None,
        metavar="SNAPSHOT_FILE",
        help="restore persisted provider state from latest snapshot or explicit file path",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version_text}",
    )
    return parser


def _resolve_log_level_override(args: argparse.Namespace) -> str | None:
    """Return the startup log-level override requested on the CLI."""
    return "DEBUG" if bool(args.diagnostic) else args.log_level


def _load_provider_runtime_config(
    args: argparse.Namespace,
    *,
    logger: logging.Logger,
) -> provider_config.ProviderConfig:
    """Resolve config path, apply CLI overrides, and cache provider config."""
    effective_config_path = provider_config.get_effective_config_path(
        args.config_path
    ).resolve()
    logger.info("using provider config path: %s", effective_config_path)
    os.environ[provider_config.ENV_OPAMP_CONFIG_PATH] = str(effective_config_path)
    try:
        config = provider_config.load_config_with_overrides(
            config_path=effective_config_path,
            log_level=_resolve_log_level_override(args),
        )
    except Exception as exc:
        logger.warning(
            "failed loading provider config file path=%s",
            effective_config_path,
            exc_info=exc,
        )
        raise
    provider_config.set_config(config)
    return config


def _initialize_provider_runtime(
    config: provider_config.ProviderConfig,
    *,
    logger: logging.Logger,
) -> None:
    """Initialize shared provider runtime state from loaded configuration."""
    logger.info(
        "state persistence file prefix: %s",
        config.state_persistence.state_file_prefix,
    )
    STORE.set_default_heartbeat_frequency(
        config.default_heartbeat_frequency,
        max_events=config.client_event_history_size,
        record_event=False,
    )


def _apply_restore_option(
    *,
    config: provider_config.ProviderConfig,
    restore_option: str | None,
    logger: logging.Logger,
) -> None:
    """Restore provider state when requested, otherwise record skipped status."""
    if restore_option is None:
        set_state_restore_status("not_requested")
        logger.info(
            "state restore not requested; server will start with empty in-memory state"
        )
        return

    if config.state_persistence.enabled is not True:
        set_state_restore_status(
            "skipped",
            "state persistence disabled; restore request ignored",
        )
        logger.warning("restore requested but state persistence is disabled")
        logger.info(
            "state restore skipped; server will start with empty in-memory state"
        )
        return

    try:
        restore_path = resolve_restore_snapshot_path(
            state_file_prefix=config.state_persistence.state_file_prefix,
            restore_option=restore_option,
        )
    except FileNotFoundError as exc:
        set_state_restore_status("missing", str(exc))
        logger.warning("restore requested but snapshot missing: %s", exc)
        logger.info(
            "state restore fallback: no snapshot file available, starting with empty in-memory state"
        )
        return

    logger.info("state restore using snapshot file: %s", restore_path)
    try:
        summary = restore_state_snapshot(
            store=STORE,
            snapshot_path=restore_path,
            logger=logger,
        )
        set_state_restore_status("restored", json.dumps(summary, sort_keys=True))
    except FileNotFoundError as exc:
        set_state_restore_status("missing", str(exc))
        logger.warning("restore snapshot missing: %s", exc)
        logger.info(
            "state restore fallback: no snapshot file available, starting with empty in-memory state"
        )
    except Exception as exc:
        set_state_restore_status("failed", str(exc))
        logger.warning(
            "failed restoring provider state from %s",
            restore_path,
            exc_info=exc,
        )
        logger.info(
            "state restore fallback: invalid/corrupt snapshot, starting with empty in-memory state"
        )


def _set_diagnostic_mode(enabled: bool, *, logger: logging.Logger) -> None:
    """Store provider diagnostic-mode state for UI/API feature gating."""
    app.config["DIAGNOSTIC_MODE"] = bool(enabled)
    logger.info("provider diagnostic mode enabled=%s", bool(enabled))


def main() -> None:
    """Load config overrides and start the Quart app."""
    version_text = component_version_text()
    parser = _build_argument_parser(version_text)
    args = parser.parse_args()
    _emit_bootstrap_line(
        f"parsed_args host={args.host} port={args.port} config_path={args.config_path or ''}"
    )
    _configure_logging("INFO")
    logger = logging.getLogger(__name__)
    config = _load_provider_runtime_config(args, logger=logger)
    _initialize_provider_runtime(config, logger=logger)
    _apply_restore_option(
        config=config,
        restore_option=args.restore,
        logger=logger,
    )

    resolved_log_level = provider_config.resolve_log_level(config.log_level)
    _configure_logging(resolved_log_level)
    attach_observability(
        app,
        service_name="opamp-provider",
        config=config.observability,
        log_level=resolved_log_level,
    )
    _set_diagnostic_mode(bool(args.diagnostic), logger=logger)
    port = args.port if args.port is not None else config.webui_port
    _emit_bootstrap_line(f"starting_app host={args.host} port={port}")
    app.run(
        host=args.host,
        port=port,
        **_provider_tls_run_kwargs(config),
    )


if __name__ == "__main__":
    main()
