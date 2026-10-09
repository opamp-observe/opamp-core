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

"""Security check helpers for the developer CLI."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from .components import BuildComponent, ensure_pytest_dependencies
from .provider_ui import compact_provider_ui_assets
from .runtime import CommandRuntime

APP_ENABLE_DEV_FEATURES_ENV = "APP_ENABLE_DEV_FEATURES"
DETECT_SECRETS_EXCLUDE_REGEX = (
    r"(^\.git/|^\.venv/|^dist/|^logs/|^runtime/|^server-state/|^dev-notes/|"
    r"^build/|/build/|^node_modules/|/node_modules/|^\.pytest_cache/|"
    r"^catalog-service/node_modules/|^config-service/node_modules/|"
    r"^provider/node_modules/)"
)
RUFF_SECURITY_IGNORE_CODES = (
    "S104",
    "S105",
    "S110",
    "S112",
    "S310",
    "S311",
    "S506",
    "S602",
    "S603",
    "S607",
)
REPO_RUFF_SECURITY_TARGETS = (
    "provider/src",
    "consumer/src",
    "cli/src",
    "catalog-service/src",
    "config-service/src",
    "client-config-generator-service/src",
    "agent_broker/opamp_broker",
    "shared",
    "scripts",
)
PYTEST_IMPORT_MODE_ARGUMENT = "--import-mode=importlib"


def run_repo_security_checks(runtime: CommandRuntime, *, python_exe: str) -> bool:
    """Run the consolidated repository-wide security workflow.

    Parameters
    ----------
    runtime:
        Shared command runtime used for process execution and issue capture.
    python_exe:
        Python interpreter used for pytest execution and dependency installs.

    """
    env = _security_env(runtime)
    _ensure_cli_tool(runtime, python_exe=python_exe, tool_name="ruff", pip_package="ruff")
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        tool_name="detect-secrets",
        pip_package="detect-secrets",
    )
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        tool_name="pip-audit",
        pip_package="pip-audit",
    )
    ensure_pytest_dependencies(runtime, python_exe=python_exe)

    compact_provider_ui_assets(runtime)
    runtime.run(
        [python_exe, "-m", "pytest", "-s", PYTEST_IMPORT_MODE_ARGUMENT],
        cwd=runtime.repo_root,
        env=env,
    )
    runtime.run(
        [
            "ruff",
            "check",
            "--select",
            "S",
            "--ignore",
            ",".join(RUFF_SECURITY_IGNORE_CODES),
            *REPO_RUFF_SECURITY_TARGETS,
        ],
        cwd=runtime.repo_root,
        env=env,
    )
    _scan_for_secrets(runtime, repo_root=runtime.repo_root, env=env)
    audit_files = [
        runtime.repo_root / "requirements.txt",
        runtime.repo_root / "provider" / "requirements.txt",
        runtime.repo_root / "consumer" / "requirements.txt",
        runtime.repo_root / "agent_broker" / "requirements.txt",
    ]
    existing_files = [path for path in audit_files if path.exists()]
    if existing_files:
        command = ["pip-audit"]
        for path in existing_files:
            command.extend(["-r", str(path.relative_to(runtime.repo_root))])
        runtime.run(command, cwd=runtime.repo_root, env=env)
    runtime.info("Security checks complete.")
    return False


def run_component_security_checks(
    runtime: CommandRuntime,
    *,
    component: BuildComponent,
    python_exe: str,
) -> bool:
    """Run a smaller security suite focused on one component.

    Parameters
    ----------
    runtime:
        Shared command runtime used for process execution and issue capture.
    component:
        Component whose focused security checks should be executed.
    python_exe:
        Python interpreter used for pytest execution and dependency installs.

    """
    env = _security_env(runtime)
    _ensure_cli_tool(runtime, python_exe=python_exe, tool_name="ruff", pip_package="ruff")
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        tool_name="detect-secrets",
        pip_package="detect-secrets",
    )
    ensure_pytest_dependencies(runtime, python_exe=python_exe)

    runtime.run([python_exe, "-m", "pytest", "-s"], cwd=component.path, env=env)
    runtime.run(
        [
            "ruff",
            "check",
            "--select",
            "S",
            "--ignore",
            ",".join(RUFF_SECURITY_IGNORE_CODES),
            str(component.path),
        ],
        cwd=runtime.repo_root,
        env=env,
    )
    _scan_for_secrets(runtime, repo_root=runtime.repo_root, env=env, path_prefix=component.path.name)

    requirement_path = component.path / "requirements.txt"
    if requirement_path.exists():
        _ensure_cli_tool(
            runtime,
            python_exe=python_exe,
            tool_name="pip-audit",
            pip_package="pip-audit",
        )
        runtime.run(
            ["pip-audit", "-r", str(requirement_path.relative_to(runtime.repo_root))],
            cwd=runtime.repo_root,
            env=env,
        )
    else:
        runtime.info(f"No requirements.txt found for {component.key}; pip-audit skipped.")
    return False


def _ensure_cli_tool(
    runtime: CommandRuntime,
    *,
    python_exe: str,
    tool_name: str,
    pip_package: str,
) -> None:
    """Ensure a required external CLI tool exists before use.

    Parameters
    ----------
    runtime:
        Shared command runtime used to install missing command-line tools.
    python_exe:
        Python interpreter used to install the missing tool via pip.
    tool_name:
        Executable name that should be present on the PATH.
    pip_package:
        Pip package name that provides the missing executable.

    """
    if shutil.which(tool_name):
        return
    runtime.info(f"CLI tool `{tool_name}` not found; installing `{pip_package}`...")
    runtime.run([python_exe, "-m", "pip", "install", pip_package], cwd=runtime.repo_root)


def _scan_for_secrets(
    runtime: CommandRuntime,
    *,
    repo_root: Path,
    env: dict[str, str],
    path_prefix: str | None = None,
) -> None:
    """Run detect-secrets against tracked files and record any findings.

    Parameters
    ----------
    runtime:
        Shared command runtime used for process execution and issue capture.
    repo_root:
        Repository root from which tracked files should be enumerated.
    env:
        Environment variables passed to the subprocess commands.
    path_prefix:
        Optional repository-relative prefix used to limit the tracked file
        scan to a single component subtree.

    """
    tracked_files = _tracked_files_for_secret_scan(
        runtime,
        repo_root=repo_root,
        env=env,
        path_prefix=path_prefix,
    )
    if not tracked_files:
        runtime.info("No tracked files found for detect-secrets scan.")
        return
    completed = runtime.run(
        [
            "detect-secrets",
            "scan",
            "--force-use-all-plugins",
            "--exclude-files",
            DETECT_SECRETS_EXCLUDE_REGEX,
            *tracked_files,
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
    )
    flattened_findings = _flatten_detect_secrets_findings(completed.stdout)
    if not flattened_findings:
        return
    _record_detect_secret_findings(runtime, flattened_findings)
    raise RuntimeError("detect-secrets reported potential secrets")


def _tracked_files_for_secret_scan(
    runtime: CommandRuntime,
    *,
    repo_root: Path,
    env: dict[str, str],
    path_prefix: str | None,
) -> list[str]:
    """Return tracked files that should be scanned by detect-secrets."""
    tracked_output = runtime.run(
        ["git", "ls-files"],
        cwd=repo_root,
        env=env,
        capture_output=True,
    ).stdout
    tracked_files: list[str] = []
    for line in tracked_output.splitlines():
        candidate = line.strip()
        if _should_skip_tracked_secret_scan_path(candidate, path_prefix=path_prefix):
            continue
        tracked_files.append(candidate)
    return tracked_files


def _should_skip_tracked_secret_scan_path(candidate: str, *, path_prefix: str | None) -> bool:
    """Return whether a tracked path should be excluded from secret scanning."""
    if not candidate or candidate.startswith("dev-notes"):
        return True
    if path_prefix is None:
        return False
    return not candidate.startswith(f"{path_prefix}/") and candidate != path_prefix


def _flatten_detect_secrets_findings(scan_output: str) -> list[tuple[str, int]]:
    """Flatten detect-secrets JSON output into file and line-number pairs."""
    payload = json.loads(scan_output.strip() or "{}")
    findings = payload.get("results", {})
    if not isinstance(findings, dict):
        return []
    flattened_findings: list[tuple[str, int]] = []
    for file_path, matches in findings.items():
        if not isinstance(matches, list):
            continue
        for match in matches:
            if not isinstance(match, dict):
                continue
            flattened_findings.append(
                (str(file_path), int(match.get("line_number", 0) or 0))
            )
    return flattened_findings


def _record_detect_secret_findings(
    runtime: CommandRuntime,
    findings: list[tuple[str, int]],
) -> None:
    """Record detect-secrets findings in the structured issue log."""
    for file_path, line_number in findings:
        runtime.record_issue(
            "potential secret detected",
            category="detect-secrets",
            path=file_path,
            details={"line_number": line_number},
        )


def _security_env(runtime: CommandRuntime) -> dict[str, str]:
    """Build the environment used for security checks.

    Parameters
    ----------
    runtime:
        Runtime instance retained for interface consistency with sibling
        helpers and future environment customization.

    """
    del runtime
    env = os.environ.copy()
    env.pop(APP_ENABLE_DEV_FEATURES_ENV, None)
    return env
