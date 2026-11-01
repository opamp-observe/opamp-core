# Copyright 2026 opamp.info
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

"""Shared git-derived version metadata helpers used by developer tooling."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

COMPONENT_VERSION_TARGETS: dict[str, str] = {
    "server": "provider/src/opamp_provider/version.json",
    "broker": "agent_broker/opamp_broker/version.json",
    "consumer": "consumer/src/opamp_consumer/version.json",
    "consumer-sim": "consumer-sim/version.json",
}
SECONDARY_COMPONENT_VERSION_TARGETS: dict[str, tuple[str, ...]] = {
    "consumer-sim": ("consumer-sim/src/opamp_consumer_sim/version.json",),
}
UNKNOWN_VALUE = "unknown"
SEMVER_LABEL_PATTERN = re.compile(
    r"^(?P<prefix>v?)"
    r"(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
MAJOR_MINOR_LABEL_PATTERN = re.compile(
    r"^(?P<prefix>v?)"
    r"(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)$"
)


def _run_git_command(repo_root: Path, args: list[str]) -> str | None:
    """Return git command output or ``None`` when unavailable."""
    try:
        output = subprocess.check_output(
            ["git", *args],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return output or None


def _resolve_git_commit(repo_root: Path) -> str:
    commit = _run_git_command(repo_root, ["rev-parse", "--short=12", "HEAD"])
    return commit or UNKNOWN_VALUE


def _resolve_git_commit_date(repo_root: Path) -> str:
    commit_date = _run_git_command(repo_root, ["show", "-s", "--format=%cI", "HEAD"])
    if commit_date:
        return commit_date
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _resolve_latest_git_label(repo_root: Path) -> str:
    label = _run_git_command(repo_root, ["describe", "--tags", "--abbrev=0"])
    return str(label or "").strip()


def _increment_patch_semver_label(label: str, *, patch_delta: int = 1) -> str | None:
    safe_patch_delta = max(1, int(patch_delta))
    candidate = str(label or "").strip()
    if not candidate:
        return None
    match = SEMVER_LABEL_PATTERN.fullmatch(candidate)
    if match is not None:
        prefix = str(match.group("prefix") or "")
        major = int(match.group("major"))
        minor = int(match.group("minor"))
        patch = int(match.group("patch")) + safe_patch_delta
        return f"{prefix}{major}.{minor}.{patch}"
    major_minor_match = MAJOR_MINOR_LABEL_PATTERN.fullmatch(candidate)
    if major_minor_match is not None:
        prefix = str(major_minor_match.group("prefix") or "")
        major = int(major_minor_match.group("major"))
        minor = int(major_minor_match.group("minor"))
        return f"{prefix}{major}.{minor}.{safe_patch_delta}"
    return None


def _resolve_commits_since_label(repo_root: Path, label: str) -> int:
    candidate = str(label or "").strip()
    if not candidate:
        return 0
    commits_since = _run_git_command(repo_root, ["rev-list", "--count", f"{candidate}..HEAD"])
    if commits_since is None:
        return 0
    try:
        return max(0, int(commits_since))
    except ValueError:
        return 0


def _resolve_effective_label(label: str, *, commits_since_label: int = 0) -> str:
    patch_delta = max(0, int(commits_since_label)) + 1
    bumped = _increment_patch_semver_label(label, patch_delta=patch_delta)
    if bumped is not None:
        return bumped
    return str(label or "").strip()


def _parse_iso_datetime(value: str) -> datetime | None:
    candidate = str(value).strip()
    if not candidate:
        return None
    normalized = candidate.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _friendly_datetime_text(iso_value: str) -> str:
    parsed = _parse_iso_datetime(iso_value)
    if parsed is None:
        return str(iso_value)
    offset = parsed.strftime("%z")
    offset = f"{offset[:3]}:{offset[3:]}" if offset else "+00:00"
    return f"{parsed.strftime('%d %b %Y %H:%M:%S')} UTC{offset}"


def _build_version_text(*, label: str, commit: str, commit_date_friendly: str) -> str:
    if str(label).strip():
        return f"{label} {commit} ({commit_date_friendly})"
    return f"{commit} ({commit_date_friendly})"


def _build_version_payload(
    *,
    component: str,
    commit: str,
    commit_date: str,
    label: str,
    commits_since_label: int,
) -> dict[str, str]:
    effective_label = _resolve_effective_label(
        label,
        commits_since_label=commits_since_label,
    )
    commit_date_friendly = _friendly_datetime_text(commit_date)
    version_text = _build_version_text(
        label=effective_label,
        commit=commit,
        commit_date_friendly=commit_date_friendly,
    )
    return {
        "component": component,
        "git_label": label,
        "effective_label": effective_label,
        "git_commit": commit,
        "git_commit_date": commit_date,
        "git_commit_date_friendly": commit_date_friendly,
        "version": version_text,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def _write_json(path: Path, payload: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for refreshing git-derived version metadata."""
    parser = argparse.ArgumentParser(
        description="Generate component version metadata from git HEAD."
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=str(Path(__file__).resolve().parents[3]),
        help="repository root path",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress per-file update output",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Generate and write version metadata files for all configured components."""
    args = _build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve()
    commit = _resolve_git_commit(repo_root)
    commit_date = _resolve_git_commit_date(repo_root)
    label = _resolve_latest_git_label(repo_root)
    commits_since_label = _resolve_commits_since_label(repo_root, label)

    for component, relative_target in COMPONENT_VERSION_TARGETS.items():
        target_path = repo_root / relative_target
        payload = _build_version_payload(
            component=component,
            commit=commit,
            commit_date=commit_date,
            label=label,
            commits_since_label=commits_since_label,
        )
        _write_json(target_path, payload)
        if not args.quiet:
            print(f"[version] updated {component}: {target_path}")
        for secondary_target in SECONDARY_COMPONENT_VERSION_TARGETS.get(component, ()):
            secondary_path = repo_root / secondary_target
            _write_json(secondary_path, payload)
            if not args.quiet:
                print(f"[version] updated {component}: {secondary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
