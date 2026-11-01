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

"""Developer command for bumping configured component semantic versions."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .constants import (
    APP_ENABLE_DEV_FEATURES_ENV,
    CLI_VERSION_TARGETS_CONFIG_PATH,
    COMMAND_DEV_VERSION_BUMP,
    TRUE_VALUES,
)


def _parse_semver(version: str) -> tuple[int, int, int] | None:
    """Return `(major, minor, patch)` for a strict semantic version string."""
    match = re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", str(version or "").strip())
    if match is None:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _semver_text(parts: tuple[int, int, int]) -> str:
    """Return `MAJOR.MINOR.PATCH` text from numeric semantic version parts."""
    return f"{parts[0]}.{parts[1]}.{parts[2]}"


def _next_minor_semver(version: str) -> str:
    """Increment a semantic version by one minor version and reset patch to zero."""
    parts = _parse_semver(version)
    if parts is None:
        raise ValueError(f"current version must use MAJOR.MINOR.PATCH format: {version}")
    return _semver_text((parts[0], parts[1] + 1, 0))


def _semver_greater(candidate: str, current: str) -> bool:
    """Return whether `candidate` is a strict semantic-version increase."""
    candidate_parts = _parse_semver(candidate)
    current_parts = _parse_semver(current)
    if candidate_parts is None:
        raise ValueError("new version must use MAJOR.MINOR.PATCH format")
    if current_parts is None:
        raise ValueError(f"current version must use MAJOR.MINOR.PATCH format: {current}")
    return candidate_parts > current_parts


def _parse_dev_version_bump_args(args: list[str], *, repo_root: Path) -> dict[str, Any]:
    """Parse `dev-version-bump [VERSION] [--config path]` arguments."""
    config_path = (repo_root / CLI_VERSION_TARGETS_CONFIG_PATH).resolve()
    requested_version = ""
    index = 0
    while index < len(args):
        arg_text = str(args[index])
        if arg_text == "--config":
            index += 1
            if index >= len(args):
                raise ValueError("--config requires a path")
            raw_path = Path(args[index]).expanduser()
            config_path = raw_path.resolve() if raw_path.is_absolute() else (repo_root / raw_path).resolve()
        elif arg_text.startswith("--config="):
            raw_path = Path(arg_text.split("=", 1)[1]).expanduser()
            config_path = raw_path.resolve() if raw_path.is_absolute() else (repo_root / raw_path).resolve()
        elif arg_text.startswith("--"):
            raise ValueError(f"unsupported {COMMAND_DEV_VERSION_BUMP} option: {arg_text}")
        elif requested_version:
            raise ValueError(f"{COMMAND_DEV_VERSION_BUMP} accepts at most one VERSION argument")
        else:
            requested_version = arg_text
        index += 1
    return {"config_path": config_path, "requested_version": requested_version or None}


def _read_dev_version_config(config_path: Path) -> dict[str, Any]:
    """Load the JSON file that lists version-bearing targets."""
    if not config_path.exists():
        raise FileNotFoundError(f"version target config not found: {config_path}")
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid version target config JSON: {config_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("version target config must be a JSON object")
    _version_config_components(payload)
    return payload


def _version_config_components(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Return validated version components from the new or legacy config shape."""
    raw_components = config.get("components")
    if raw_components is None:
        if not isinstance(config.get("currentVersionSource"), dict):
            raise ValueError("version target config requires components or currentVersionSource")
        if not isinstance(config.get("targets"), list) or not config["targets"]:
            raise ValueError("version target config requires a non-empty targets list")
        return [
            {
                "id": "default",
                "currentVersionSource": config["currentVersionSource"],
                "targets": config["targets"],
            }
        ]
    if not isinstance(raw_components, list) or not raw_components:
        raise ValueError("version target config requires a non-empty components list")

    components: list[dict[str, Any]] = []
    for index, raw_component in enumerate(raw_components, start=1):
        if not isinstance(raw_component, dict):
            raise ValueError(f"version component {index} must be a JSON object")
        if not isinstance(raw_component.get("currentVersionSource"), dict):
            raise ValueError(f"version component {index} requires currentVersionSource")
        if not isinstance(raw_component.get("targets"), list) or not raw_component["targets"]:
            raise ValueError(f"version component {index} requires a non-empty targets list")
        components.append(raw_component)
    return components


def _version_component_label(component: dict[str, Any], index: int) -> str:
    """Return the human-readable component name used in bump output."""
    return str(
        component.get("label")
        or component.get("name")
        or component.get("id")
        or f"component-{index}"
    ).strip()


def _resolve_repo_path(repo_root: Path, raw_path: object) -> Path:
    """Resolve one target path relative to the repository root."""
    path_text = str(raw_path or "").strip()
    if not path_text:
        raise ValueError("version target path must not be empty")
    candidate = Path(path_text).expanduser()
    return candidate.resolve() if candidate.is_absolute() else (repo_root / candidate).resolve()


def _read_version_from_config_source(repo_root: Path, source: dict[str, Any]) -> str:
    """Read the canonical current version using the configured source pattern."""
    source_path = _resolve_repo_path(repo_root, source.get("path"))
    pattern = str(source.get("pattern") or "").strip()
    if not pattern:
        raise ValueError("currentVersionSource.pattern is required")
    if source_path.is_file() is not True:
        raise FileNotFoundError(f"current version source not found: {source_path}")
    content = source_path.read_text(encoding="utf-8")
    match = re.search(pattern, content, flags=re.MULTILINE)
    if match is None:
        raise ValueError(f"current version pattern not found in {source_path}")
    if not match.groups():
        raise ValueError("currentVersionSource.pattern must capture the version as group 1")
    version = str(match.group(1)).strip()
    if _parse_semver(version) is None:
        raise ValueError(f"current version must use MAJOR.MINOR.PATCH format: {version}")
    return version


def _version_target_optional(target: dict[str, Any]) -> bool:
    """Return whether a missing version target should be skipped."""
    raw_value = target.get("optional", False)
    if isinstance(raw_value, bool):
        return raw_value
    return str(raw_value or "").strip().lower() in TRUE_VALUES


def _planned_configured_version_target(
    *,
    repo_root: Path,
    target: dict[str, Any],
    version: str,
) -> dict[str, Any]:
    """Validate and stage one version target update without writing it."""
    target_path = _resolve_repo_path(repo_root, target.get("path"))
    pattern = str(target.get("pattern") or "").strip()
    replacement_template = str(target.get("replacement") or "")
    optional = _version_target_optional(target)
    if not pattern:
        raise ValueError(f"version target pattern is required for {target_path}")
    if "{version}" not in replacement_template:
        raise ValueError(f"version target replacement must include {{version}} for {target_path}")
    if target_path.is_file() is not True:
        if optional:
            return {
                "path": target_path,
                "optional": True,
                "missing": True,
                "replacements": 0,
                "updated": None,
            }
        raise FileNotFoundError(f"version target not found: {target_path}")
    count = int(target.get("count", 0) or 0)
    original = target_path.read_text(encoding="utf-8")
    updated, replacements = re.subn(
        pattern,
        replacement_template.format(version=version),
        original,
        count=max(0, count),
        flags=re.MULTILINE,
    )
    return {
        "path": target_path,
        "optional": optional,
        "missing": False,
        "replacements": replacements,
        "updated": updated,
    }


def _update_configured_version_target(
    *,
    repo_root: Path,
    target: dict[str, Any],
    version: str,
) -> tuple[Path, int]:
    """Apply one configured version replacement and return the path/count."""
    planned_target = _planned_configured_version_target(
        repo_root=repo_root,
        target=target,
        version=version,
    )
    target_path = Path(planned_target["path"])
    replacements = int(planned_target["replacements"])
    updated = planned_target.get("updated")
    if replacements > 0 and isinstance(updated, str):
        target_path.write_text(updated, encoding="utf-8")
    return target_path, replacements


def execute_dev_version_bump_workflow(
    args: list[str] | None = None,
    *,
    repo_root_provider: Callable[[], Path],
    dev_features_enabled: Callable[[], bool],
) -> int:
    """Update configured component semantic versions in dev mode."""
    if dev_features_enabled() is not True:
        print(
            f"{COMMAND_DEV_VERSION_BUMP} is only available when {APP_ENABLE_DEV_FEATURES_ENV}=true.",
            file=sys.stderr,
        )
        return 1

    try:
        repo_root = repo_root_provider()
        parsed_args = _parse_dev_version_bump_args(list(args or []), repo_root=repo_root)
        config_path = Path(parsed_args["config_path"])
        config = _read_dev_version_config(config_path)
        requested_version = parsed_args["requested_version"]
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    planned_updates: list[dict[str, Any]] = []
    pattern_misses: list[Path] = []
    optional_missing: list[Path] = []
    try:
        for index, component in enumerate(_version_config_components(config), start=1):
            label = _version_component_label(component, index)
            current_version = _read_version_from_config_source(repo_root, component["currentVersionSource"])
            next_version = str(requested_version or _next_minor_semver(current_version))
            is_greater = _semver_greater(next_version, current_version)
            if is_greater is not True:
                print(
                    f"New version {next_version} for {label} must be greater than "
                    f"current version {current_version}.",
                    file=sys.stderr,
                )
                return 1
            targets: list[dict[str, Any]] = []
            for raw_target in component["targets"]:
                if not isinstance(raw_target, dict):
                    raise ValueError("each version target must be a JSON object")
                planned_target = _planned_configured_version_target(
                    repo_root=repo_root,
                    target=raw_target,
                    version=next_version,
                )
                if bool(planned_target.get("missing")):
                    optional_missing.append(Path(planned_target["path"]))
                elif int(planned_target["replacements"]) <= 0:
                    pattern_misses.append(Path(planned_target["path"]))
                targets.append(planned_target)
            planned_updates.append(
                {
                    "label": label,
                    "current_version": current_version,
                    "next_version": next_version,
                    "targets": targets,
                }
            )
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if pattern_misses:
        print("Version update aborted before writing changes.", file=sys.stderr)
        print("The following target pattern(s) did not match:", file=sys.stderr)
        for target_path in pattern_misses:
            print(f"  - {target_path}", file=sys.stderr)
        return 1

    print(f"Version target config: {config_path}")
    print(f"Version components: {len(planned_updates)}")

    updated_count = 0
    for planned_update in planned_updates:
        print(
            f"{planned_update['label']}: "
            f"{planned_update['current_version']} -> {planned_update['next_version']}"
        )
        for planned_target in planned_update["targets"]:
            target_path = Path(planned_target["path"])
            if bool(planned_target.get("missing")):
                print(f"Skipped optional missing target {target_path}")
                continue
            replacements = int(planned_target["replacements"])
            if replacements <= 0:
                print(f"Skipped {target_path} (pattern not found)")
                continue
            updated = planned_target.get("updated")
            if isinstance(updated, str):
                target_path.write_text(updated, encoding="utf-8")
            updated_count += 1
            print(f"Updated {target_path} ({replacements} replacement(s))")

    if optional_missing:
        print(f"Optional missing targets skipped: {len(optional_missing)}")
    print(f"Version update complete: {updated_count} target(s) updated.")
    return 0
