#!/usr/bin/env python3
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

"""Top-level `config` command support for the OpAMP CLI."""

from __future__ import annotations

import argparse
import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COMMAND_CONFIG = "config"
COMMAND_CONFIG_VALIDATE = "validate"
COMMAND_CONFIG_METADATA = "metadata"
UTF8_ENCODING = "utf-8"


def config_command_available(*, repo_root: Path) -> bool:
    """Return whether config-service-backed CLI config commands are available."""
    return _load_cli_support_class(repo_root=repo_root) is not None


def execute_config_command(
    *,
    argv: list[str],
    repo_root: Path,
    log_dir: Path,
) -> int:
    """Execute one `opamp-cli config ...` command."""
    parser = argparse.ArgumentParser(
        prog="opamp-cli config",
        description="Validate config files and manage config-service metadata headers.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    validate_parser = subparsers.add_parser(
        COMMAND_CONFIG_VALIDATE,
        help="Validate one config file or every supported config file under a folder",
    )
    validate_parser.add_argument("target", help="Config file or folder path")

    metadata_parser = subparsers.add_parser(
        COMMAND_CONFIG_METADATA,
        help="Add missing config-service metadata headers to one file or folder tree",
    )
    metadata_parser.add_argument("target", help="Config file or folder path")

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    cli_support_class = _load_cli_support_class(repo_root=repo_root)
    if cli_support_class is None:
        print(
            (
                "Error: config-service support was not detected, so "
                "`opamp-cli config` is unavailable."
            ),
            file=sys.stderr,
        )
        return 1

    cli_support = cli_support_class(repo_root=repo_root)
    target_path = Path(str(args.target or "")).expanduser()
    try:
        if args.subcommand == COMMAND_CONFIG_VALIDATE:
            report = cli_support.validate_path(target_path)
        else:
            report = cli_support.ensure_metadata_path(target_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    output_path = (
        log_dir
        / f"config-{args.subcommand}-{_report_timestamp()}.log"
    ).resolve()
    rendered = report.render()
    output_path.write_text(rendered, encoding=UTF8_ENCODING)
    print(rendered, end="" if rendered.endswith("\n") else "\n")
    print(f"Report file: {output_path}")
    if args.subcommand == COMMAND_CONFIG_VALIDATE and report.has_issues:
        return 1
    return 0


def _report_timestamp() -> str:
    """Return a filesystem-friendly UTC timestamp for generated report files."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _load_cli_support_class(*, repo_root: Path) -> type[Any] | None:
    """Return the config-service CLI support class when present."""
    try:
        return _import_cli_support_class()
    except ImportError:
        support_src = (repo_root / "config-service" / "src").resolve()
        if support_src.is_dir() is not True:
            return None
        if str(repo_root.resolve()) not in sys.path:
            sys.path.insert(0, str(repo_root.resolve()))
        if str(support_src) not in sys.path:
            sys.path.insert(0, str(support_src))
        try:
            return _import_cli_support_class()
        except ImportError:
            return None


def _import_cli_support_class() -> type[Any]:
    """Import and return `config_service.cli_support.CliConfigSupport`."""
    module = importlib.import_module("config_service.cli_support")
    return getattr(module, "CliConfigSupport")
