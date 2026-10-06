# Copyright 2026 mp3monster.org
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Repository version bump helpers for the developer CLI."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .runtime import CommandRuntime, prompt_int
from .version_metadata import main as refresh_version_metadata


@dataclass(frozen=True)
class VersionTarget:
    """One file pattern that carries the repository package version."""

    path: str
    pattern: str
    replacement: str


VERSION_TARGETS: tuple[VersionTarget, ...] = (
    VersionTarget(path="agent_broker/pyproject.toml", pattern=r'^version = "[^"]+"$', replacement='version = "{version}"'),
    VersionTarget(path="catalog-service/pyproject.toml", pattern=r'^version = "[^"]+"$', replacement='version = "{version}"'),
    VersionTarget(path="client-config-generator-service/pyproject.toml", pattern=r'^version = "[^"]+"$', replacement='version = "{version}"'),
    VersionTarget(path="client-config-generator-service/src/client_config_generator_service/__init__.py", pattern=r'^__version__ = "[^"]+"$', replacement='__version__ = "{version}"'),
    VersionTarget(path="cli/pyproject.toml", pattern=r'^version = "[^"]+"$', replacement='version = "{version}"'),
    VersionTarget(path="config-service/pyproject.toml", pattern=r'^version = "[^"]+"$', replacement='version = "{version}"'),
    VersionTarget(path="config-service/build_config.py", pattern=r'^PACKAGE_VERSION = "[^"]+"$', replacement='PACKAGE_VERSION = "{version}"'),
    VersionTarget(path="consumer/pyproject.toml", pattern=r'^version = "[^"]+"$', replacement='version = "{version}"'),
    VersionTarget(path="consumer-sim/pyproject.toml", pattern=r'^version = "[^"]+"$', replacement='version = "{version}"'),
    VersionTarget(path="mcp/pyproject.toml", pattern=r'^version = "[^"]+"$', replacement='version = "{version}"'),
    VersionTarget(path="provider/pyproject.toml", pattern=r'^version = "[^"]+"$', replacement='version = "{version}"'),
    VersionTarget(path="tests/test_mcp_build_config_tool.py", pattern=r'\d+\.\d+\.\d+', replacement="{version}"),
)


def read_current_version(repo_root: Path) -> str:
    """Read the canonical version from the CLI component pyproject."""
    pyproject_path = repo_root / "cli" / "pyproject.toml"
    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', content, flags=re.MULTILINE)
    if match is None:
        raise RuntimeError(f"unable to locate version in {pyproject_path}")
    return str(match.group(1))


def prompt_for_version(current_version: str) -> str:
    """Interactively prompt for a new semantic version."""
    major_text, minor_text, patch_text = (current_version.split(".") + ["0", "0", "0"])[:3]
    major = prompt_int("New major version", default=int(major_text))
    minor = prompt_int("New minor version", default=int(minor_text))
    patch = prompt_int("New patch version", default=int(patch_text))
    return f"{major}.{minor}.{patch}"


def set_repository_version(
    runtime: CommandRuntime,
    *,
    version: str | None,
) -> bool:
    """Update hard-coded package versions and refresh generated version metadata."""
    current_version = read_current_version(runtime.repo_root)
    runtime.info(f"Current hard-coded version: {current_version}")
    selected_version = version or prompt_for_version(current_version)
    if not re.fullmatch(r"\d+\.\d+\.\d+", selected_version):
        raise RuntimeError("new version must use MAJOR.MINOR.PATCH format")

    runtime.info(f"Setting repository version to {selected_version}")
    for target in VERSION_TARGETS:
        target_path = runtime.repo_root / target.path
        original = target_path.read_text(encoding="utf-8")
        updated, replacements = re.subn(
            target.pattern,
            target.replacement.format(version=selected_version),
            original,
            count=0,
            flags=re.MULTILINE,
        )
        if replacements == 0:
            runtime.record_issue(
                "version pattern not found while updating file",
                category="version-update-missed-target",
                path=target_path,
                details={"pattern": target.pattern},
            )
            continue
        target_path.write_text(updated, encoding="utf-8")
        runtime.info(f"Updated {target_path}")

    refresh_version_metadata(["--repo-root", str(runtime.repo_root)])
    return bool(runtime.issue_records)
