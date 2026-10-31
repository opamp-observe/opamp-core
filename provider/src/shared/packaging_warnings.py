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

"""Packaging-time warnings shared across OpAMP component build flows."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

try:
    from importlib import metadata as importlib_metadata
except ImportError:  # pragma: no cover - Python < 3.8 fallback
    import importlib_metadata  # type: ignore

LOGGER = logging.getLogger(__name__)

CLI_DIR_NAME = "cli"
CLI_PYPROJECT_FILE = "pyproject.toml"
CLI_SRC_DIR = "src"
CLI_PACKAGE_DIR = "opamp_cli"
CLI_MAIN_FILE = "main.py"
CLI_DISTRIBUTION_NAMES = ("opamp-cli", "opamp_cli")
CLI_MISSING_WARNING_TEMPLATE = (
    "warning: {component_label} did not detect the OpAMP CLI. "
    "The CLI is packaged separately as `opamp-cli`; review whether it should "
    "also be installed or deployed alongside this component."
)


def _detect_cli_source(repo_root: Path) -> str | None:
    """Return the CLI source marker path when the workspace includes the CLI component."""
    cli_root = repo_root / CLI_DIR_NAME
    markers = [
        cli_root / CLI_PYPROJECT_FILE,
        cli_root / CLI_SRC_DIR / CLI_PACKAGE_DIR / CLI_MAIN_FILE,
    ]
    LOGGER.info("detecting CLI source repo_root=%s", repo_root)
    if all(marker.exists() for marker in markers):
        resolved = str(cli_root.resolve())
        LOGGER.info("detected CLI source path=%s", resolved)
        return resolved
    LOGGER.warning("CLI source markers not found repo_root=%s", repo_root)
    return None


def _detect_cli_distribution() -> str | None:
    """Return the installed CLI distribution version when available."""
    LOGGER.info("detecting installed CLI distribution")
    for dist_name in CLI_DISTRIBUTION_NAMES:
        try:
            version = importlib_metadata.version(dist_name)
        except importlib_metadata.PackageNotFoundError:
            LOGGER.debug("CLI distribution not installed dist_name=%s", dist_name)
            continue
        distribution = f"{dist_name}=={version}"
        LOGGER.info("detected installed CLI distribution=%s", distribution)
        return distribution
    LOGGER.warning("no installed CLI distribution detected")
    return None


def build_cli_missing_warning(*, component_label: str, repo_root: Path) -> str | None:
    """Return a packaging warning when the OpAMP CLI is not available."""
    LOGGER.info("building CLI availability warning component_label=%s", component_label)
    source_path = _detect_cli_source(repo_root)
    installed_dist = _detect_cli_distribution()
    if source_path or installed_dist:
        LOGGER.info(
            "CLI availability satisfied component_label=%s source_path=%s installed_dist=%s",
            component_label,
            source_path,
            installed_dist,
        )
        return None

    warning = CLI_MISSING_WARNING_TEMPLATE.format(component_label=component_label)
    LOGGER.warning("CLI availability warning generated component_label=%s", component_label)
    return warning


def warn_if_cli_missing(*, component_label: str, repo_root: Path) -> bool:
    """Print a packaging warning when the OpAMP CLI is not available."""
    LOGGER.info("checking whether CLI warning should be printed component_label=%s", component_label)
    warning = build_cli_missing_warning(
        component_label=component_label,
        repo_root=repo_root,
    )
    if warning is None:
        LOGGER.info("no CLI warning needed component_label=%s", component_label)
        return False
    print(warning, file=sys.stderr)
    LOGGER.warning("printed CLI warning component_label=%s", component_label)
    return True
