#!/usr/bin/env python3
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

"""Container runtime helpers for the OpAMP CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from .common import _normalized_label, _slugify
    from .constants import (
        ACTION_KEY_LOG_NAME,
        ACTION_KEY_METADATA,
        ACTION_KEY_RECORD_NAME,
        ACTION_KIND_BACKGROUND_START,
        LOCALHOST_ADDRESS,
    )
except ImportError:
    from common import _normalized_label, _slugify  # type: ignore[no-redef]
    from constants import (  # type: ignore[no-redef]
        ACTION_KEY_LOG_NAME,
        ACTION_KEY_METADATA,
        ACTION_KEY_RECORD_NAME,
        ACTION_KIND_BACKGROUND_START,
        LOCALHOST_ADDRESS,
    )

CONTAINER_RECORD_PREFIX = "Container"
CONTAINER_STOP_TIMEOUT_SECONDS = 10


def container_runtime_executable() -> str | None:
    """Return an available container runtime executable, if one is configured."""
    configured = str(os.environ.get("OPAMP_CONTAINER_RUNTIME") or "").strip()
    candidates = [configured] if configured else ["docker", "podman"]
    for candidate in candidates:
        if not candidate:
            continue
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def container_runtime_ready(
    runtime: str,
    *,
    windows_no_console_kwargs: Callable[[], dict[str, Any]],
) -> tuple[bool, str]:
    """Return whether the container runtime can talk to its backend service."""
    try:
        completed = subprocess.run(  # noqa: S603
            [runtime, "info"],
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
            **windows_no_console_kwargs(),
        )
    except subprocess.TimeoutExpired:
        return False, f"{runtime} info timed out"
    except OSError as exc:
        return False, str(exc)

    if completed.returncode == 0:
        return True, ""
    details = (completed.stderr or completed.stdout or "").strip()
    if not details:
        details = f"{runtime} info exited with code {completed.returncode}"
    return False, details


def container_readiness_tcp(ports: list[str]) -> str:
    """Return a host TCP endpoint derived from the first published port mapping."""
    for port_mapping in ports:
        parts = [part for part in str(port_mapping or "").split(":") if part]
        if len(parts) < 2:
            continue
        host = LOCALHOST_ADDRESS
        host_port = parts[-2]
        if len(parts) > 2:
            host = parts[-3]
        try:
            int(host_port)
        except ValueError:
            continue
        return f"{host}:{host_port}"
    return ""


def print_container_runtime_unavailable(runtime: str, details: str) -> None:
    """Print a concise runtime readiness failure with common recovery hints."""
    runtime_name = Path(runtime).name.lower()
    print(
        f"Container runtime is installed but not ready: {runtime}",
        file=sys.stderr,
    )
    if details:
        print(details, file=sys.stderr)
    if "podman" in runtime_name:
        print(
            "Start Podman's VM with `podman machine start`, then retry.",
            file=sys.stderr,
        )
    elif "docker" in runtime_name:
        print(
            "Start Docker Desktop or the Docker daemon, then retry.",
            file=sys.stderr,
        )


def container_entry_id(entry: dict[str, Any]) -> str:
    """Return stable identifier text for one configured container entry."""
    return str(
        entry.get("id")
        or entry.get("name")
        or entry.get("label")
        or ""
    ).strip()


def configured_container_entries(
    *,
    demo_config_path: Path,
    demo_profiles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return unique container start entries from the dev CLI profile config."""
    try:
        payload = json.loads(demo_config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    entries: list[dict[str, Any]] = []
    top_level = payload.get("containers", [])
    if isinstance(top_level, list):
        entries.extend(dict(item) for item in top_level if isinstance(item, dict))
    for profile in demo_profiles:
        profile_name = str(profile.get("name") or "").strip()
        for item in profile.get("containers", []):
            if not isinstance(item, dict):
                continue
            entry = dict(item)
            entry.setdefault("profile", profile_name)
            entries.append(entry)

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        entry_id = container_entry_id(entry)
        if not entry_id:
            continue
        normalized = _normalized_label(entry_id)
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(entry)
    return deduped


def container_image_from_entry(entry: dict[str, Any]) -> str:
    """Return the configured image, preferring explicit image candidates."""
    candidates = entry.get("image_candidates", [])
    if isinstance(candidates, list):
        for candidate in candidates:
            image = str(candidate or "").strip()
            if image:
                return image
    return str(entry.get("image") or "").strip()


def container_runtime_supports_replace(runtime: str) -> bool:
    """Return whether the runtime supports replacing a named container on run."""
    return Path(runtime).name.lower().startswith("podman")


def mapped_container_path_to_host_path(
    *,
    container_path: str,
    volumes: list[dict[str, Any]],
    resolve_path_from_repo: Callable[[str], Path],
) -> Path | None:
    """Map a configured container path back to a host path when possible."""
    normalized_container_path = str(container_path or "").strip().replace("\\", "/")
    if not normalized_container_path:
        return None
    for volume in volumes:
        host_path = str(volume.get("host_path") or "").strip()
        mounted_path = str(volume.get("container_path") or "").strip().replace("\\", "/")
        if not host_path or not mounted_path:
            continue
        if normalized_container_path == mounted_path:
            return resolve_path_from_repo(host_path)
        prefix = mounted_path.rstrip("/") + "/"
        if normalized_container_path.startswith(prefix):
            suffix = normalized_container_path[len(prefix) :]
            return (resolve_path_from_repo(host_path) / suffix).resolve()
    return None


def container_start_action_from_entry(
    entry: dict[str, Any],
    *,
    runtime: str,
    repo_root: Path,
    profile_name: str | None = None,
    resolve_path_from_repo: Callable[[str], Path],
    command_text_from_args: Callable[[list[str]], str],
    background_start_action: Callable[..., dict[str, Any]],
    build_exec_env: Callable[[], dict[str, str]],
    demo_record_prefix: Callable[[str], str],
) -> dict[str, Any] | None:
    """Build one background start action from a configured container entry."""
    entry_id = container_entry_id(entry)
    if not entry_id:
        return None
    base_label = str(entry.get("label") or entry_id).strip()
    image = container_image_from_entry(entry)
    if not image:
        return None

    ensure_dirs: list[str] = []
    for raw_path in entry.get("ensure_dirs", []):
        if not str(raw_path or "").strip():
            continue
        ensure_dirs.append(str(resolve_path_from_repo(str(raw_path))))

    argv = [runtime, "run", "--rm"]
    container_name = str(entry.get("container_name") or "").strip()
    if (
        container_name
        and bool(entry.get("replace_existing"))
        and container_runtime_supports_replace(runtime)
    ):
        argv.append("--replace")
    if container_name:
        argv.extend(["--name", container_name])
    ports = [str(port or "").strip() for port in entry.get("ports", [])]
    for port_text in ports:
        if port_text:
            argv.extend(["-p", port_text])
    environment = entry.get("environment", {})
    if isinstance(environment, dict):
        for key, value in environment.items():
            if not str(key).strip():
                continue
            argv.extend(["-e", f"{key}={value}"])
    for volume in entry.get("volumes", []):
        if not isinstance(volume, dict):
            continue
        host_path_raw = str(volume.get("host_path") or "").strip()
        target_container_path = str(volume.get("container_path") or "").strip()
        if not host_path_raw or not target_container_path:
            continue
        host_path = resolve_path_from_repo(host_path_raw)
        mode = ":ro" if bool(volume.get("read_only")) else ""
        argv.extend(["-v", f"{host_path}:{target_container_path}{mode}"])
    for extra_arg in entry.get("extra_args", []):
        extra_text = str(extra_arg or "").strip()
        if extra_text:
            argv.append(extra_text)
    argv.append(image)
    for command_part in entry.get("command", []):
        command_text = str(command_part or "").strip()
        if command_text:
            argv.append(command_text)

    action_label = base_label
    record_name = f"{CONTAINER_RECORD_PREFIX}:{base_label}"
    log_name = f"container-{_slugify(base_label)}"
    metadata: dict[str, Any] = {
        "container_id": entry_id,
        "container_name": container_name,
        "container_runtime": runtime,
        "container_image": image,
    }
    if profile_name:
        action_label = f"{base_label} ({profile_name})"
        record_name = f"{demo_record_prefix(profile_name)}:{CONTAINER_RECORD_PREFIX}:{base_label}"
        log_name = f"demo-{_slugify(profile_name)}-container-{_slugify(base_label)}"
        metadata["demo_profile"] = profile_name

    aliases = [
        entry_id,
        base_label,
        *(str(alias) for alias in entry.get("aliases", []) if str(alias).strip()),
    ]
    return background_start_action(
        action_id=f"container_{_slugify(entry_id).replace('-', '_')}",
        label=action_label,
        command_text=command_text_from_args(argv),
        argv=argv,
        cwd=repo_root,
        env=build_exec_env(),
        readiness_tcp=container_readiness_tcp(ports),
    ) | {
        ACTION_KEY_RECORD_NAME: record_name,
        ACTION_KEY_METADATA: metadata,
        ACTION_KEY_LOG_NAME: log_name,
        "aliases": aliases,
        "ensure_dirs": ensure_dirs,
    }


def stop_recorded_container(
    record: dict[str, Any],
    *,
    logger: Any,
    windows_no_console_kwargs: Callable[[], dict[str, Any]],
) -> bool:
    """Stop a recorded container through its runtime, when metadata is available."""
    metadata = record.get(ACTION_KEY_METADATA, {})
    if not isinstance(metadata, dict):
        return False
    runtime = str(metadata.get("container_runtime") or "").strip()
    target = str(
        metadata.get("container_name")
        or metadata.get("container_id")
        or ""
    ).strip()
    if not runtime or not target:
        return False
    command = [
        runtime,
        "stop",
        "--time",
        str(CONTAINER_STOP_TIMEOUT_SECONDS),
        target,
    ]
    try:
        completed = subprocess.run(  # noqa: S603
            command,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=CONTAINER_STOP_TIMEOUT_SECONDS + 5,
            **windows_no_console_kwargs(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning(
            "container stop command failed target=%s runtime=%s error=%s",
            target,
            runtime,
            exc,
        )
        return False
    if int(completed.returncode) != 0:
        logger.warning(
            "container stop command exited non-zero target=%s runtime=%s exit_code=%s",
            target,
            runtime,
            int(completed.returncode),
        )
        return False
    logger.info("stopped recorded container target=%s runtime=%s", target, runtime)
    print(f"Stopped container {target}")
    return True


def container_background_kind() -> str:
    """Return the action kind used by container start actions."""
    return ACTION_KIND_BACKGROUND_START
