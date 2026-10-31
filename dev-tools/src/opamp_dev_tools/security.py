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

"""Security check helpers for the developer CLI."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]

from .components import (
    BuildComponent,
    PytestRunOptions,
    ensure_pytest_dependencies,
    run_pytest_with_junit,
)
from .provider_ui import compact_provider_ui_assets
from .runtime import CommandRuntime
from .sbom import normalize_dist_name, requirement_name

APP_ENABLE_DEV_FEATURES_ENV = "APP_ENABLE_DEV_FEATURES"
AUDIT_MANIFEST_PROJECT_KEY = "project"
AUDIT_MANIFEST_PROJECTS_KEY = "projects"
AUDIT_MANIFEST_REPORT_KEY = "report"
AUDIT_MANIFEST_STATUS_KEY = "status"
AUDIT_STATUS_FAILED = "failed"
AUDIT_STATUS_PASSED = "passed"
BANDIT_REPORT_FILE_NAME = "bandit.json"
BANDIT_PIP_REQUIREMENT = "bandit>=1.9.4"
BANDIT_TOOL_MODULE = "bandit"
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
    "consumer-sim/src",
    "cli/src",
    "catalog-service/src",
    "config-service/src",
    "client-config-generator-service/src",
    "agent_broker/opamp_broker",
    "dev-tools/src",
    "mcp/src",
    "mcp/configure_mcp_clients.py",
    "mcp/build_mcp_config_tool.py",
    "svr-credentials-mgr/src",
    "svr-credentials-mgr/plaintext-keyring/src",
    "shared",
    "scripts",
)
DETECT_SECRETS_REPORT_FILE_NAME = "detect-secrets.json"  # pragma: allowlist secret
DETECT_SECRETS_PIP_REQUIREMENT = "detect-secrets>=1.5.0"  # pragma: allowlist secret
DETECT_SECRETS_TOOL_MODULE = "detect_secrets"  # pragma: allowlist secret
DETECT_SECRETS_RESULTS_KEY = "results"  # pragma: allowlist secret
LINE_NUMBER_KEY = "line_number"
PIP_AUDIT_REPORT_FILE_NAME = "pip-audit.json"
PIP_AUDIT_REPORT_DIRECTORY_NAME = "pip-audit"
PIP_AUDIT_REQUIREMENTS_DIRECTORY_NAME = "requirements"
PIP_AUDIT_PIP_REQUIREMENT = "pip-audit>=2.10.1"
PIP_AUDIT_TOOL_MODULE = "pip_audit"
PROJECT_DEPENDENCIES_KEY = "dependencies"
PROJECT_METADATA_KEY = "project"
PROJECT_NAME_KEY = "name"
PYTEST_IMPORT_MODE_ARGUMENT = "--import-mode=importlib"
PYTEST_REPORT_FILE_NAME = "pytest.xml"
REPO_PYTHON_PROJECT_PATHS = (
    Path("agent_broker"),
    Path("catalog-service"),
    Path("cli"),
    Path("client-config-generator-service"),
    Path("config-service"),
    Path("consumer"),
    Path("consumer-sim"),
    Path("dev-tools"),
    Path("mcp"),
    Path("provider"),
    Path("svr-credentials-mgr"),
    Path("svr-credentials-mgr/plaintext-keyring"),
)
RUFF_REPORT_FILE_NAME = "ruff.sarif"
RUFF_PIP_REQUIREMENT = "ruff>=0.15.0"
RUFF_TOOL_MODULE = "ruff"
SECURITY_REPORT_DIRECTORY = Path("dev-tools/runtime/security-reports")
SEMGREP_CONFIG_PATH = Path("security/semgrep.yml")
SEMGREP_ENTRYPOINT_CODE = "from semgrep.console_scripts.pysemgrep import main; main()"
SEMGREP_MCP_MODULE = "mcp.server.fastmcp"
SEMGREP_MCP_REQUIREMENT = "mcp==1.29.0"
SEMGREP_REPORT_FILE_NAME = "semgrep.sarif"
SEMGREP_PIP_REQUIREMENT = "semgrep>=1.182.1"
SEMGREP_TOOL_MODULE = "semgrep"


@dataclass(frozen=True)
class ProjectAuditOptions:
    """Immutable settings shared by each project dependency audit.

    Attributes
    ----------
    python_exe:
        Python interpreter containing pip-audit.
    multiple_projects:
        Whether reports belong beneath the repository's per-project directory.
    env:
        Environment variables passed to pip-audit.
    report_scope:
        Stable name used for the retained security report directory.
    workspace_project_names:
        Normalized distribution names owned by projects in this audit run.

    """

    python_exe: str
    multiple_projects: bool
    env: dict[str, str]
    report_scope: str
    workspace_project_names: set[str]


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
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        module_name=RUFF_TOOL_MODULE,
        pip_package=RUFF_PIP_REQUIREMENT,
    )
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        module_name=DETECT_SECRETS_TOOL_MODULE,
        pip_package=DETECT_SECRETS_PIP_REQUIREMENT,
    )
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        module_name=PIP_AUDIT_TOOL_MODULE,
        pip_package=PIP_AUDIT_PIP_REQUIREMENT,
    )
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        module_name=SEMGREP_TOOL_MODULE,
        pip_package=SEMGREP_PIP_REQUIREMENT,
    )
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        module_name=SEMGREP_MCP_MODULE,
        pip_package=SEMGREP_MCP_REQUIREMENT,
    )
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        module_name=BANDIT_TOOL_MODULE,
        pip_package=BANDIT_PIP_REQUIREMENT,
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
                python_exe,
                "-m",
                RUFF_TOOL_MODULE,
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
            python_exe=python_exe,
            env=env,
            report_scope=report_scope,
        ),
        failure_messages=failure_messages,
    )
    project_paths = [
        runtime.repo_root / project_path
        for project_path in REPO_PYTHON_PROJECT_PATHS
        if (runtime.repo_root / project_path / "pyproject.toml").is_file()
    ]
    _run_security_step(
        runtime,
        label="pip-audit",
        operation=partial(
            _audit_python_projects,
            runtime,
            python_exe=python_exe,
            project_paths=project_paths,
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
            python_exe=python_exe,
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
            python_exe=python_exe,
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
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        module_name=RUFF_TOOL_MODULE,
        pip_package=RUFF_PIP_REQUIREMENT,
    )
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        module_name=DETECT_SECRETS_TOOL_MODULE,
        pip_package=DETECT_SECRETS_PIP_REQUIREMENT,
    )
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        module_name=SEMGREP_TOOL_MODULE,
        pip_package=SEMGREP_PIP_REQUIREMENT,
    )
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        module_name=SEMGREP_MCP_MODULE,
        pip_package=SEMGREP_MCP_REQUIREMENT,
    )
    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        module_name=BANDIT_TOOL_MODULE,
        pip_package=BANDIT_PIP_REQUIREMENT,
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
                python_exe,
                "-m",
                RUFF_TOOL_MODULE,
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
            python_exe=python_exe,
            env=env,
            path_prefix=component.path.name,
            report_scope=report_scope,
        ),
        failure_messages=failure_messages,
    )

    _ensure_cli_tool(
        runtime,
        python_exe=python_exe,
        module_name=PIP_AUDIT_TOOL_MODULE,
        pip_package=PIP_AUDIT_PIP_REQUIREMENT,
    )
    _run_security_step(
        runtime,
        label="pip-audit",
        operation=partial(
            _audit_python_projects,
            runtime,
            python_exe=python_exe,
            project_paths=[component.path],
            env=env,
            report_scope=report_scope,
        ),
        failure_messages=failure_messages,
    )
    component_targets = (str(component.path.relative_to(runtime.repo_root)),)
    _run_security_step(
        runtime,
        label="semgrep",
        operation=partial(
            _run_semgrep_report,
            runtime,
            python_exe=python_exe,
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
            python_exe=python_exe,
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
    module_name: str,
    pip_package: str,
) -> None:
    """Ensure a required security-tool module exists for the selected Python.

    Parameters
    ----------
    runtime:
        Shared command runtime used to install missing command-line tools.
    python_exe:
        Python interpreter used to install the missing tool via pip.
    module_name:
        Importable module that provides the command-line entry point.
    pip_package:
        Pip package name that provides the missing executable.

    """
    runtime.ensure_python_module(
        python_exe=python_exe,
        module_name=module_name,
        pip_package=pip_package,
    )


def _scan_for_secrets(
    runtime: CommandRuntime,
    *,
    python_exe: str,
    env: dict[str, str],
    path_prefix: str | None = None,
    report_scope: str = "repository",
) -> None:
    """Run detect-secrets against tracked files and record any findings.

    Parameters
    ----------
    runtime:
        Shared command runtime used for process execution and issue capture.
    python_exe:
        Python interpreter containing the versioned security dependencies.
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
            python_exe,
            "-m",
            DETECT_SECRETS_TOOL_MODULE,
            "scan",
            "--force-use-all-plugins",
            "--exclude-files",
            DETECT_SECRETS_EXCLUDE_REGEX,
            *scan_paths,
        ],
        cwd=runtime.repo_root,
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


def _audit_python_projects(
    runtime: CommandRuntime,
    *,
    python_exe: str,
    project_paths: list[Path],
    env: dict[str, str],
    report_scope: str,
) -> None:
    """Audit packaged projects and retain pip-audit JSON for every project.

    Parameters
    ----------
    runtime:
        Shared command runtime used for process execution.
    python_exe:
        Python interpreter containing pip-audit.
    project_paths:
        Project directories containing the ``pyproject.toml`` files to audit.
    env:
        Environment variables passed to pip-audit.
    report_scope:
        Stable name used for the retained report directory.

    """
    if not project_paths:
        runtime.info("No pyproject.toml files found; pip-audit skipped.")
        return
    multiple_projects = len(project_paths) > 1
    workspace_project_names = _workspace_project_names(project_paths)
    audit_options = ProjectAuditOptions(
        python_exe=python_exe,
        multiple_projects=multiple_projects,
        env=env,
        report_scope=report_scope,
        workspace_project_names=workspace_project_names,
    )
    audit_failures: list[str] = []
    report_entries: list[dict[str, str]] = []
    for project_path in project_paths:
        report_entry, audit_failure = _audit_python_project(
            runtime,
            project_path=project_path,
            options=audit_options,
        )
        report_entries.append(report_entry)
        if audit_failure:
            audit_failures.append(audit_failure)

    if multiple_projects:
        manifest_path = _security_report_path(
            runtime,
            scope=report_scope,
            file_name=PIP_AUDIT_REPORT_FILE_NAME,
        )
        manifest_path.write_text(
            json.dumps(
                {AUDIT_MANIFEST_PROJECTS_KEY: report_entries},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    if audit_failures:
        raise RuntimeError("pip-audit failed: " + "; ".join(audit_failures))


def _audit_python_project(
    runtime: CommandRuntime,
    *,
    project_path: Path,
    options: ProjectAuditOptions,
) -> tuple[dict[str, str], str | None]:
    """Audit one project's third-party dependencies and describe its result.

    Parameters
    ----------
    runtime:
        Shared command runtime used for process execution.
    project_path:
        Project directory containing the source ``pyproject.toml``.
    options:
        Interpreter, report layout, environment, and workspace package settings.

    """
    relative_project_path = project_path.relative_to(runtime.repo_root)
    project_report_name = relative_project_path.as_posix().replace("/", "__") + ".json"
    report_file_name = (
        str(Path(PIP_AUDIT_REPORT_DIRECTORY_NAME) / project_report_name)
        if options.multiple_projects
        else PIP_AUDIT_REPORT_FILE_NAME
    )
    report_path = _security_report_path(
        runtime,
        scope=options.report_scope,
        file_name=report_file_name,
    )
    requirements_path = _write_audit_requirements(
        runtime,
        project_path=project_path,
        report_scope=options.report_scope,
        workspace_project_names=options.workspace_project_names,
    )
    try:
        runtime.run(
            [
                options.python_exe,
                "-m",
                PIP_AUDIT_TOOL_MODULE,
                "--strict",
                "--format",
                "json",
                "--output",
                str(report_path),
                "--requirement",
                str(requirements_path),
            ],
            cwd=runtime.repo_root,
            env=options.env,
        )
        status = AUDIT_STATUS_PASSED
        audit_failure = None
    except RuntimeError as error:
        status = AUDIT_STATUS_FAILED
        audit_failure = f"{relative_project_path}: {error}"
    return (
        {
            AUDIT_MANIFEST_PROJECT_KEY: relative_project_path.as_posix(),
            AUDIT_MANIFEST_REPORT_KEY: report_path.relative_to(runtime.repo_root).as_posix(),
            AUDIT_MANIFEST_STATUS_KEY: status,
        },
        audit_failure,
    )


def _workspace_project_names(project_paths: list[Path]) -> set[str]:
    """Return normalized distribution names owned by the audited workspace.

    Parameters
    ----------
    project_paths:
        Project directories whose ``pyproject.toml`` metadata defines local packages.

    """
    project_names: set[str] = set()
    for project_path in project_paths:
        project_metadata = _read_project_metadata(project_path)
        project_name = project_metadata.get(PROJECT_NAME_KEY)
        if isinstance(project_name, str) and project_name.strip():
            project_names.add(normalize_dist_name(project_name))
    return project_names


def _write_audit_requirements(
    runtime: CommandRuntime,
    *,
    project_path: Path,
    report_scope: str,
    workspace_project_names: set[str],
) -> Path:
    """Write third-party project dependencies to a pip-audit input file.

    Local workspace packages are omitted because they are not resolvable from the public
    package index and each package is audited independently from its own TOML metadata.

    Parameters
    ----------
    runtime:
        Shared command runtime whose repository root owns the generated audit input.
    project_path:
        Project directory containing the source ``pyproject.toml``.
    report_scope:
        Stable name used for the retained security report directory.
    workspace_project_names:
        Normalized distribution names owned by projects in this audit run.

    """
    project_metadata = _read_project_metadata(project_path)
    dependency_values = project_metadata.get(PROJECT_DEPENDENCIES_KEY, [])
    dependencies = (
        [str(dependency) for dependency in dependency_values]
        if isinstance(dependency_values, list)
        else []
    )
    auditable_dependencies = [
        dependency
        for dependency in dependencies
        if normalize_dist_name(requirement_name(dependency)) not in workspace_project_names
    ]
    relative_project_path = project_path.relative_to(runtime.repo_root)
    requirements_name = relative_project_path.as_posix().replace("/", "__") + ".txt"
    requirements_path = _security_report_path(
        runtime,
        scope=report_scope,
        file_name=str(Path(PIP_AUDIT_REQUIREMENTS_DIRECTORY_NAME) / requirements_name),
    )
    content = "\n".join(auditable_dependencies)
    requirements_path.write_text(content + ("\n" if content else ""), encoding="utf-8")
    return requirements_path


def _read_project_metadata(project_path: Path) -> dict[str, object]:
    """Read the project table from one package's TOML metadata.

    Parameters
    ----------
    project_path:
        Project directory containing ``pyproject.toml``.

    """
    pyproject_path = project_path / "pyproject.toml"
    if not pyproject_path.is_file():
        return {}
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project_metadata = payload.get(PROJECT_METADATA_KEY, {})
    if not isinstance(project_metadata, dict):
        return {}
    return project_metadata


def _run_semgrep_report(
    runtime: CommandRuntime,
    *,
    python_exe: str,
    targets: tuple[str, ...],
    env: dict[str, str],
    report_scope: str,
) -> None:
    """Run reviewed Semgrep rules and retain report-only SARIF evidence.

    Parameters
    ----------
    runtime:
        Shared command runtime used for process execution.
    python_exe:
        Python interpreter containing Semgrep.
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
            python_exe,
            "-c",
            SEMGREP_ENTRYPOINT_CODE,
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
    python_exe: str,
    targets: tuple[str, ...],
    env: dict[str, str],
    report_scope: str,
) -> None:
    """Run Bandit in evaluation mode and retain its native JSON report.

    Parameters
    ----------
    runtime:
        Shared command runtime used for process execution.
    python_exe:
        Python interpreter containing Bandit.
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
            python_exe,
            "-m",
            BANDIT_TOOL_MODULE,
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
    report_path = report_directory / file_name
    report_path.parent.mkdir(parents=True, exist_ok=True)
    return report_path


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
