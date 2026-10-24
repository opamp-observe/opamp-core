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
from collections.abc import Callable
from functools import partial
from pathlib import Path

from .components import (
    BuildComponent,
    PytestRunOptions,
    ensure_pytest_dependencies,
    run_pytest_with_junit,
)
from .provider_ui import compact_provider_ui_assets
from .runtime import CommandRuntime

APP_ENABLE_DEV_FEATURES_ENV = "APP_ENABLE_DEV_FEATURES"
BANDIT_REPORT_FILE_NAME = "bandit.json"
BANDIT_TOOL_NAME = "bandit"
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
DETECT_SECRETS_REPORT_FILE_NAME = "detect-secrets.json"
DETECT_SECRETS_RESULTS_KEY = "results"
LINE_NUMBER_KEY = "line_number"
PIP_AUDIT_REPORT_FILE_NAME = "pip-audit.json"
PYTEST_IMPORT_MODE_ARGUMENT = "--import-mode=importlib"
PYTEST_REPORT_FILE_NAME = "pytest.xml"
RUFF_REPORT_FILE_NAME = "ruff.sarif"
SECURITY_REPORT_DIRECTORY = Path("dev-tools/runtime/security-reports")
SEMGREP_CONFIG_PATH = Path("security/semgrep.yml")
SEMGREP_REPORT_FILE_NAME = "semgrep.sarif"
SEMGREP_TOOL_NAME = "semgrep"


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
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        tool_name=SEMGREP_TOOL_NAME,
        pip_package=SEMGREP_TOOL_NAME,
    )
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        tool_name=BANDIT_TOOL_NAME,
        pip_package=BANDIT_TOOL_NAME,
    )
    ensure_pytest_dependencies(runtime, python_exe=python_exe)

    failure_messages: list[str] = []
    report_scope = "repository"
    compact_provider_ui_assets(runtime)
    pytest_report_path = _security_report_path(
        runtime,
        scope=report_scope,
        file_name=PYTEST_REPORT_FILE_NAME,
    )
    _run_security_step(
        runtime,
        label="pytest",
        operation=partial(
            run_pytest_with_junit,
            runtime,
            python_exe=python_exe,
            options=PytestRunOptions(
                cwd=runtime.repo_root,
                junit_path=pytest_report_path,
                arguments_before_report=(PYTEST_IMPORT_MODE_ARGUMENT,),
                env=env,
            ),
        ),
        failure_messages=failure_messages,
    )
    ruff_report_path = _security_report_path(
        runtime,
        scope=report_scope,
        file_name=RUFF_REPORT_FILE_NAME,
    )
    _run_security_step(
        runtime,
        label="ruff",
        operation=partial(
            runtime.run,
            [
                "ruff",
                "check",
                "--select",
                "S",
                "--ignore",
                ",".join(RUFF_SECURITY_IGNORE_CODES),
                "--output-format",
                "sarif",
                "--output-file",
                str(ruff_report_path),
                *REPO_RUFF_SECURITY_TARGETS,
            ],
            cwd=runtime.repo_root,
            env=env,
        ),
        failure_messages=failure_messages,
    )
    _run_security_step(
        runtime,
        label="detect-secrets",
        operation=partial(
            _scan_for_secrets,
            runtime,
            repo_root=runtime.repo_root,
            env=env,
            report_scope=report_scope,
        ),
        failure_messages=failure_messages,
    )
    audit_files = [
        runtime.repo_root / "requirements.txt",
        runtime.repo_root / "provider" / "requirements.txt",
        runtime.repo_root / "consumer" / "requirements.txt",
        runtime.repo_root / "agent_broker" / "requirements.txt",
    ]
    existing_files = [path for path in audit_files if path.exists()]
    _run_security_step(
        runtime,
        label="pip-audit",
        operation=partial(
            _audit_requirement_files,
            runtime,
            requirement_paths=existing_files,
            env=env,
            report_scope=report_scope,
        ),
        failure_messages=failure_messages,
    )
    _run_security_step(
        runtime,
        label="semgrep",
        operation=partial(
            _run_semgrep_report,
            runtime,
            targets=REPO_RUFF_SECURITY_TARGETS,
            env=env,
            report_scope=report_scope,
        ),
        failure_messages=failure_messages,
    )
    _run_security_step(
        runtime,
        label="bandit",
        operation=partial(
            _run_bandit_report,
            runtime,
            targets=REPO_RUFF_SECURITY_TARGETS,
            env=env,
            report_scope=report_scope,
        ),
        failure_messages=failure_messages,
    )
    _raise_collected_security_failures(failure_messages)
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
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        tool_name=SEMGREP_TOOL_NAME,
        pip_package=SEMGREP_TOOL_NAME,
    )
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        tool_name=BANDIT_TOOL_NAME,
        pip_package=BANDIT_TOOL_NAME,
    )
    ensure_pytest_dependencies(runtime, python_exe=python_exe)

    failure_messages: list[str] = []
    report_scope = component.key
    pytest_report_path = _security_report_path(
        runtime,
        scope=report_scope,
        file_name=PYTEST_REPORT_FILE_NAME,
    )
    _run_security_step(
        runtime,
        label="pytest",
        operation=partial(
            run_pytest_with_junit,
            runtime,
            python_exe=python_exe,
            options=PytestRunOptions(
                cwd=component.path,
                junit_path=pytest_report_path,
                env=env,
            ),
        ),
        failure_messages=failure_messages,
    )
    ruff_report_path = _security_report_path(
        runtime,
        scope=report_scope,
        file_name=RUFF_REPORT_FILE_NAME,
    )
    _run_security_step(
        runtime,
        label="ruff",
        operation=partial(
            runtime.run,
            [
                "ruff",
                "check",
                "--select",
                "S",
                "--ignore",
                ",".join(RUFF_SECURITY_IGNORE_CODES),
                "--output-format",
                "sarif",
                "--output-file",
                str(ruff_report_path),
                str(component.path),
            ],
            cwd=runtime.repo_root,
            env=env,
        ),
        failure_messages=failure_messages,
    )
    _run_security_step(
        runtime,
        label="detect-secrets",
        operation=partial(
            _scan_for_secrets,
            runtime,
            repo_root=runtime.repo_root,
            env=env,
            path_prefix=component.path.name,
            report_scope=report_scope,
        ),
        failure_messages=failure_messages,
    )

    requirement_path = component.path / "requirements.txt"
    if requirement_path.exists():
        _ensure_cli_tool(
            runtime,
            python_exe=python_exe,
            tool_name="pip-audit",
            pip_package="pip-audit",
        )
        _run_security_step(
            runtime,
            label="pip-audit",
            operation=partial(
                _audit_requirement_files,
                runtime,
                requirement_paths=[requirement_path],
                env=env,
                report_scope=report_scope,
            ),
            failure_messages=failure_messages,
        )
    else:
        runtime.info(f"No requirements.txt found for {component.key}; pip-audit skipped.")
    component_targets = (str(component.path.relative_to(runtime.repo_root)),)
    _run_security_step(
        runtime,
        label="semgrep",
        operation=partial(
            _run_semgrep_report,
            runtime,
            targets=component_targets,
            env=env,
            report_scope=report_scope,
        ),
        failure_messages=failure_messages,
    )
    _run_security_step(
        runtime,
        label="bandit",
        operation=partial(
            _run_bandit_report,
            runtime,
            targets=component_targets,
            env=env,
            report_scope=report_scope,
        ),
        failure_messages=failure_messages,
    )
    _raise_collected_security_failures(failure_messages)
    return False


def _run_security_step(
    runtime: CommandRuntime,
    *,
    label: str,
    operation: Callable[[], object],
    failure_messages: list[str],
) -> None:
    """Run one independent gate step and retain its failure for final reporting.

    Parameters
    ----------
    runtime:
        Shared command runtime used to report continuation after a failed step.
    label:
        Human-readable tool or test name included in the consolidated failure.
    operation:
        Zero-argument callable that performs the independent gate step.
    failure_messages:
        Mutable collection that receives a concise failure description.

    """
    try:
        operation()
    except Exception as error:  # pylint: disable=broad-except
        failure_messages.append(f"{label}: {error}")
        runtime.info(f"{label} failed; continuing to retain the remaining security reports.")


def _raise_collected_security_failures(failure_messages: list[str]) -> None:
    """Raise one final error after every independent security step has run.

    Parameters
    ----------
    failure_messages:
        Failure descriptions collected while the gate continued through its steps.

    """
    if failure_messages:
        raise RuntimeError("Security checks failed: " + "; ".join(failure_messages))


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
    report_scope: str = "repository",
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
    report_scope:
        Stable name used for the retained native JSON report directory.

    """
    scan_paths = [path_prefix] if path_prefix else []
    completed = runtime.run(
        [
            "detect-secrets",
            "scan",
            "--force-use-all-plugins",
            "--exclude-files",
            DETECT_SECRETS_EXCLUDE_REGEX,
            *scan_paths,
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
    )
    report_path = _security_report_path(
        runtime,
        scope=report_scope,
        file_name=DETECT_SECRETS_REPORT_FILE_NAME,
    )
    report_path.write_text(completed.stdout.strip() + "\n", encoding="utf-8")
    flattened_findings = _flatten_detect_secrets_findings(completed.stdout)
    if not flattened_findings:
        return
    _record_detect_secret_findings(runtime, flattened_findings)
    raise RuntimeError("detect-secrets reported potential secrets")
def _flatten_detect_secrets_findings(scan_output: str) -> list[tuple[str, int]]:
    """Flatten detect-secrets JSON output into file and line-number pairs."""
    payload = json.loads(scan_output.strip() or "{}")
    findings = payload.get(DETECT_SECRETS_RESULTS_KEY, {})
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
                (str(file_path), int(match.get(LINE_NUMBER_KEY, 0) or 0))
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
            details={LINE_NUMBER_KEY: line_number},
        )


def _audit_requirement_files(
    runtime: CommandRuntime,
    *,
    requirement_paths: list[Path],
    env: dict[str, str],
    report_scope: str,
) -> None:
    """Audit requirement files and retain pip-audit's native JSON output.

    Parameters
    ----------
    runtime:
        Shared command runtime used for process execution.
    requirement_paths:
        Existing requirement files that define the environments to audit.
    env:
        Environment variables passed to pip-audit.
    report_scope:
        Stable name used for the retained report directory.

    """
    if not requirement_paths:
        runtime.info("No requirements.txt files found; pip-audit skipped.")
        return
    report_path = _security_report_path(
        runtime,
        scope=report_scope,
        file_name=PIP_AUDIT_REPORT_FILE_NAME,
    )
    command = ["pip-audit", "--format", "json", "--output", str(report_path)]
    for requirement_path in requirement_paths:
        command.extend(["-r", str(requirement_path.relative_to(runtime.repo_root))])
    runtime.run(command, cwd=runtime.repo_root, env=env)


def _run_semgrep_report(
    runtime: CommandRuntime,
    *,
    targets: tuple[str, ...],
    env: dict[str, str],
    report_scope: str,
) -> None:
    """Run reviewed Semgrep rules and retain report-only SARIF evidence.

    Parameters
    ----------
    runtime:
        Shared command runtime used for process execution.
    targets:
        Repository-relative source paths Semgrep should inspect.
    env:
        Environment variables passed to Semgrep.
    report_scope:
        Stable name used for the retained report directory.

    """
    report_path = _security_report_path(
        runtime,
        scope=report_scope,
        file_name=SEMGREP_REPORT_FILE_NAME,
    )
    runtime.run(
        [
            SEMGREP_TOOL_NAME,
            "scan",
            "--config",
            str(runtime.repo_root / SEMGREP_CONFIG_PATH),
            "--metrics",
            "off",
            "--sarif",
            "--output",
            str(report_path),
            *targets,
        ],
        cwd=runtime.repo_root,
        env=env,
    )


def _run_bandit_report(
    runtime: CommandRuntime,
    *,
    targets: tuple[str, ...],
    env: dict[str, str],
    report_scope: str,
) -> None:
    """Run Bandit in evaluation mode and retain its native JSON report.

    Parameters
    ----------
    runtime:
        Shared command runtime used for process execution.
    targets:
        Repository-relative source paths Bandit should inspect.
    env:
        Environment variables passed to Bandit.
    report_scope:
        Stable name used for the retained report directory.

    """
    report_path = _security_report_path(
        runtime,
        scope=report_scope,
        file_name=BANDIT_REPORT_FILE_NAME,
    )
    runtime.run(
        [
            BANDIT_TOOL_NAME,
            "-r",
            *targets,
            "--format",
            "json",
            "--output",
            str(report_path),
            "--exit-zero",
        ],
        cwd=runtime.repo_root,
        env=env,
    )


def _security_report_path(
    runtime: CommandRuntime,
    *,
    scope: str,
    file_name: str,
) -> Path:
    """Create a stable security-report directory and return one output path.

    Parameters
    ----------
    runtime:
        Shared command runtime whose repository root owns the report tree.
    scope:
        Repository or component name used to separate report sets.
    file_name:
        Report filename created by the invoked security tool.

    """
    report_directory = runtime.repo_root / SECURITY_REPORT_DIRECTORY / scope
    report_directory.mkdir(parents=True, exist_ok=True)
    return report_directory / file_name


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
