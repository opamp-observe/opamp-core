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

"""Git hook setup helpers for the developer CLI."""

from __future__ import annotations

import os
from pathlib import Path

from .runtime import CommandRuntime

LEGACY_HOOK_SHIM = """#!/usr/bin/env bash
set -euo pipefail
# opamp-hook-shim: legacy .git/hooks fallback for GUI clients.
REPO_ROOT="$(git rev-parse --show-toplevel)"
exec "${REPO_ROOT}/.githooks/pre-commit" "$@"
"""


def apply_precommit_logic(runtime: CommandRuntime) -> bool:
    """Configure `.githooks` as the repository hook path and install a fallback shim."""
    repo_root = runtime.repo_root
    runtime.run(["git", "-C", str(repo_root), "config", "--local", "core.hooksPath", ".githooks"])
    pre_commit_path = repo_root / ".githooks" / "pre-commit"
    if not pre_commit_path.exists():
        raise RuntimeError(f"expected pre-commit hook at {pre_commit_path}")
    if os.name != "nt":
        current_mode = pre_commit_path.stat().st_mode
        pre_commit_path.chmod(current_mode | 0o111)

    git_common_dir = runtime.run(
        ["git", "-C", str(repo_root), "rev-parse", "--git-common-dir"],
        capture_output=True,
    ).stdout.strip()
    hooks_dir = Path(git_common_dir)
    if not hooks_dir.is_absolute():
        hooks_dir = (repo_root / hooks_dir).resolve()
    hooks_dir = hooks_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    legacy_pre_commit = hooks_dir / "pre-commit"
    if legacy_pre_commit.exists():
        content = legacy_pre_commit.read_text(encoding="utf-8", errors="ignore")
        if "opamp-hook-shim" not in content:
            runtime.info(f"Detected existing custom {legacy_pre_commit}; leaving it unchanged.")
            runtime.info(f"Configured git hooks path to {repo_root / '.githooks'}")
            return False

    legacy_pre_commit.write_text(LEGACY_HOOK_SHIM, encoding="utf-8")
    if os.name != "nt":
        current_mode = legacy_pre_commit.stat().st_mode
        legacy_pre_commit.chmod(current_mode | 0o111)

    runtime.info(f"Configured git hooks path to {repo_root / '.githooks'}")
    runtime.info(f"Verified fallback shim at {legacy_pre_commit}")
    return False
