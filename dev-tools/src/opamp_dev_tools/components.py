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

"""Buildable component discovery and build helper functions."""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]

from .runtime import CommandRuntime, read_project_metadata

DEFAULT_REPO = "mp3monster/fluent-opamp"
PYTEST_JUNIT_ARGUMENT = "--junitxml"
TEST_RESULTS_DIRECTORY = Path("dev-tools/runtime/test-results")
COMPONENT_EXCLUDES = {
    ".git",
    ".github",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".vscode",
    "config",
    "demo",
    "dev-notes",
    "dev-tools",
    "dist",
    "docs",
    "github-landingpage",
    "proto",
    "runtime",
    "scripts",
    "server-state",
    "shared",
    "tests",
    "tools",
}


@dataclass(frozen=True)
class BuildComponent:
    """Metadata for one buildable repository component.

    Attributes
    ----------
    key:
        First-level repository directory name used for CLI selection.
    path:
        Absolute filesystem path to the component root directory.
    project_name:
        Published Python project name read from ``pyproject.toml``.
    version:
        Project version string read from ``pyproject.toml``.

    """

    key: str
    path: Path
    project_name: str
    version: str


@dataclass(frozen=True)
class PytestRunOptions:
    """Settings for one pytest invocation with retained JUnit output.

    Attributes
    ----------
    cwd:
        Working directory whose pytest configuration should apply.
    junit_path:
        Output path for the machine-readable JUnit report.
    arguments_before_report:
        Pytest options that must appear before the report option.
    test_targets:
        Optional test files or directories appended after the report option.
    env:
        Optional environment variables passed to pytest.

    """

    cwd: Path
    junit_path: Path
    arguments_before_report: tuple[str, ...] = ()
    test_targets: tuple[str, ...] = ()
    env: dict[str, str] | None = None


def discover_build_components(repo_root: Path) -> list[BuildComponent]:
    """Discover buildable first-level components from child `pyproject.toml` files."""
    components: list[BuildComponent] = []
    try:
        children = sorted(repo_root.iterdir())
    except OSError:
        return components
    for child in children:
        try:
            is_directory = child.is_dir()
        except OSError:
            continue
        if not is_directory or child.name in COMPONENT_EXCLUDES:
            continue
        pyproject_path = child / "pyproject.toml"
        try:
            has_pyproject = pyproject_path.exists()
        except OSError:
            continue
        if not has_pyproject:
            continue
        metadata = read_project_metadata(pyproject_path)
        components.append(
            BuildComponent(
                key=child.name,
                path=child.resolve(),
                project_name=metadata.get("name", child.name),
                version=metadata.get("version", ""),
            )
        )
    return components


def select_components(repo_root: Path, *, named_component: str | None) -> list[BuildComponent]:
    """Return either one selected component or every discovered component."""
    components = discover_build_components(repo_root)
    if named_component is None:
        return components
    for component in components:
        if component.key == named_component:
            return [component]
    valid_names = ", ".join(component.key for component in components)
    raise RuntimeError(f"unknown component `{named_component}`; valid values: {valid_names}")


def build_artifacts(
    runtime: CommandRuntime,
    *,
    components: list[BuildComponent],
    python_exe: str,
    no_isolation: bool,
) -> bool:
    """Build sdist and wheel artefacts for one or more components."""
    runtime.ensure_python_module(python_exe=python_exe, module_name="build", pip_package="build")
    dist_root = runtime.repo_root / "dist"
    for component in components:
        _clean_component_build_tree(component)
        if no_isolation:
            _ensure_build_backend_requirements(
                runtime,
                component=component,
                python_exe=python_exe,
            )
        out_dir = dist_root / component.key
        out_dir.mkdir(parents=True, exist_ok=True)
        command = [python_exe, "-m", "build", "--sdist", "--wheel", "--outdir", str(out_dir)]
        if no_isolation:
            command.append("--no-isolation")
        command.append(str(component.path))
        runtime.run(command, cwd=runtime.repo_root)
    return False


def build_component_wheel(
    runtime: CommandRuntime,
    *,
    component: BuildComponent,
    python_exe: str,
    out_dir: Path,
    no_isolation: bool,
) -> Path:
    """Build one component wheel and return the resulting wheel path."""
    runtime.ensure_python_module(python_exe=python_exe, module_name="build", pip_package="build")
    _clean_component_build_tree(component)
    if no_isolation:
        _ensure_build_backend_requirements(
            runtime,
            component=component,
            python_exe=python_exe,
        )
    _clean_dir(out_dir)
    command = [
        python_exe,
        "-m",
        "build",
        "--wheel",
        "--outdir",
        str(out_dir),
    ]
    if no_isolation:
        command.append("--no-isolation")
    command.append(str(component.path))
    runtime.run(command, cwd=runtime.repo_root)
    wheels = sorted(out_dir.glob("*.whl"))
    if not wheels:
        raise RuntimeError(f"wheel build for {component.key} produced no .whl files")
    if len(wheels) > 1:
        runtime.info(
            f"Multiple wheels found for {component.key}; using latest: {wheels[-1].name}"
        )
    return wheels[-1]


def build_sboms(  # pylint: disable=too-many-locals,import-outside-toplevel
    runtime: CommandRuntime,
    *,
    components: list[BuildComponent],
    python_exe: str,
    no_isolation: bool,
    repo: str = DEFAULT_REPO,
) -> bool:
    """Generate SBOMs for one or more components."""
    repo_root = runtime.repo_root
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from opamp_dev_tools.sbom import (
        validate_wheel_artifact_sbom,
        write_wheel_artifact_sbom,
    )

    build_artifacts(
        runtime,
        components=components,
        python_exe=python_exe,
        no_isolation=no_isolation,
    )
    issue_found = False
    dist_root = repo_root / "dist"
    sbom_root = dist_root / "sbom"
    sbom_root.mkdir(parents=True, exist_ok=True)

    for component in components:
        custom_generator = component.path / "dev-tools" / "generate_sbom.py"
        if custom_generator.exists():
            output_path = sbom_root / f"{component.key}.cyclonedx.json"
            runtime.run(
                [python_exe, str(custom_generator), "--output", str(output_path)],
                cwd=repo_root,
            )
            continue
        wheel_path = _latest_wheel(dist_root / component.key)
        sbom_path = sbom_root / f"{component.key}.cyclonedx.json"
        written = write_wheel_artifact_sbom(
            repo_root=repo_root,
            python_exe=python_exe,
            artifact=wheel_path,
            sbom_path=sbom_path,
            root_component_name=component.project_name,
            repo=repo,
            component_dir=component.key,
        )
        validate_wheel_artifact_sbom(
            artifact=wheel_path,
            sbom_path=written,
            root_component_name=component.project_name,
            repo=repo,
        )
        runtime.info(f"Generated SBOM for {component.key}: {written}")
    return issue_found


def run_component_tests(
    runtime: CommandRuntime,
    *,
    components: list[BuildComponent],
    python_exe: str,
) -> bool:
    """Run unit and Playwright-capable tests for one or more components.

    Parameters
    ----------
    runtime:
        Shared command runtime used for command execution and reporting.
    components:
        Components whose Python and UI tests should be executed.
    python_exe:
        Python interpreter used for pytest-based test execution.

    """
    for component in components:
        tests_dir = component.path / "tests"
        if tests_dir.exists():
            ensure_pytest_dependencies(runtime, python_exe=python_exe)
            junit_path = _prepare_test_result_path(
                runtime,
                scope=component.key,
                file_name="pytest.xml",
            )
            run_pytest_with_junit(
                runtime,
                python_exe=python_exe,
                options=PytestRunOptions(
                    cwd=component.path,
                    junit_path=junit_path,
                ),
            )
        package_json = component.path / "package.json"
        playwright_config = component.path / "playwright.config.js"
        if package_json.exists():
            package_content = package_json.read_text(encoding="utf-8")
            if '"ui:unit"' in package_content:
                runtime.run(["npm", "run", "ui:unit"], cwd=component.path)
            if '"ui:test"' in package_content:
                runtime.run(["npm", "run", "ui:test"], cwd=component.path)
        elif playwright_config.exists():
            runtime.run(["npx", "playwright", "test"], cwd=component.path)
    return False


def run_e2e_tests(runtime: CommandRuntime, *, python_exe: str) -> bool:
    """Run repository end-to-end tests.

    Parameters
    ----------
    runtime:
        Shared command runtime used for command execution and reporting.
    python_exe:
        Python interpreter used for pytest-based end-to-end test execution.

    """
    ensure_pytest_dependencies(runtime, python_exe=python_exe)
    junit_path = _prepare_test_result_path(
        runtime,
        scope="e2e",
        file_name="pytest.xml",
    )
    run_pytest_with_junit(
        runtime,
        python_exe=python_exe,
        options=PytestRunOptions(
            cwd=runtime.repo_root,
            junit_path=junit_path,
            test_targets=("tests/test_socket_e2e.py",),
        ),
    )
    return False


def run_pytest_with_junit(
    runtime: CommandRuntime,
    *,
    python_exe: str,
    options: PytestRunOptions,
) -> None:
    """Run pytest and retain a JUnit report at a caller-selected path.

    Parameters
    ----------
    runtime:
        Shared command runtime used for process execution.
    python_exe:
        Python interpreter used to invoke pytest.
    options:
        Working directory, report path, optional arguments, and environment
        used for the pytest invocation.

    """
    runtime.run(
        [
            python_exe,
            "-m",
            "pytest",
            "-s",
            *options.arguments_before_report,
            f"{PYTEST_JUNIT_ARGUMENT}={options.junit_path}",
            *options.test_targets,
        ],
        cwd=options.cwd,
        env=options.env,
    )


def _prepare_test_result_path(
    runtime: CommandRuntime,
    *,
    scope: str,
    file_name: str,
) -> Path:
    """Create a stable test-result directory and return one output path.

    Parameters
    ----------
    runtime:
        Shared command runtime whose repository root owns the result tree.
    scope:
        Component or suite name used to keep reports from different runs separate.
    file_name:
        Report filename created by the invoked test runner.

    """
    result_directory = runtime.repo_root / TEST_RESULTS_DIRECTORY / scope
    result_directory.mkdir(parents=True, exist_ok=True)
    return result_directory / file_name


def ensure_pytest_dependencies(runtime: CommandRuntime, *, python_exe: str) -> None:
    """Install the pytest packages expected by repository pytest settings.

    Parameters
    ----------
    runtime:
        Shared command runtime used to probe and install Python modules.
    python_exe:
        Python interpreter used to validate imports and install missing test
        dependencies.

    """
    runtime.ensure_python_module(
        python_exe=python_exe,
        module_name="pytest",
        pip_package="pytest",
    )
    runtime.ensure_python_module(
        python_exe=python_exe,
        module_name="pytest_cov",
        pip_package="pytest-cov",
    )
    runtime.ensure_python_module(
        python_exe=python_exe,
        module_name="pytest_asyncio",
        pip_package="pytest-asyncio",
    )


def build_pdf(runtime: CommandRuntime, *, python_exe: str, output: str | None = None) -> bool:
    """Generate the OpAMP PDF manual via the dev-tools implementation."""
    runtime.ensure_python_module(
        python_exe=python_exe,
        module_name="reportlab",
        pip_package="reportlab",
    )
    command = [
        python_exe,
        str(runtime.repo_root / "dev-tools" / "src" / "opamp_dev_tools" / "pdf_manual.py"),
        "--repo-root",
        str(runtime.repo_root),
    ]
    if output:
        command.extend(["--output", output])
    runtime.run(command, cwd=runtime.repo_root)
    return False


def build_docs(runtime: CommandRuntime, *, python_exe: str) -> bool:
    """Regenerate Fluent Bit quick-reference markdown from local JSON artifacts."""
    versions = _discover_fluentbit_versions(runtime.repo_root)
    if not versions:
        runtime.record_issue(
            "no Fluent Bit versions discovered for markdown generation",
            category="docs-generation",
        )
        return True
    command = [
        python_exe,
        str(runtime.repo_root / "config-service" / "dev-tools" / "generate_fluentbit_markdown.py"),
    ]
    for version in versions:
        command.extend(["--version", version])
    runtime.run(command, cwd=runtime.repo_root)
    return False


def build_diagrams(runtime: CommandRuntime) -> bool:
    """Render Mermaid diagram sources into PNG images."""
    renderer = runtime.repo_root / "scripts" / "render_mermaid_png.sh"
    if not renderer.exists():
        raise RuntimeError(f"missing Mermaid renderer wrapper: {renderer}")
    diagram_paths = sorted(runtime.repo_root.rglob("*.mmd"))
    if not diagram_paths:
        runtime.info("No Mermaid `.mmd` files found.")
        return False
    for diagram_path in diagram_paths:
        output_path = diagram_path.with_suffix(".png")
        runtime.run(
            [str(renderer), "-i", str(diagram_path), "-o", str(output_path)],
            cwd=runtime.repo_root,
        )
    return False


def _clean_dir(path: Path) -> None:
    """Remove build files from one directory, creating it when absent."""
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_file():
            child.unlink()


def _clean_component_build_tree(component: BuildComponent) -> None:
    """Remove one component's local build tree before packaging.

    This prevents deleted or renamed source modules from surviving in a stale
    ``build/lib`` directory and being copied into a later wheel.

    Parameters
    ----------
    component:
        Build component whose exact local ``build`` path should be cleared.

    """
    build_directory = component.path / "build"
    if build_directory.is_symlink() or build_directory.is_file():
        build_directory.unlink()
    elif build_directory.is_dir():
        shutil.rmtree(build_directory)


def _discover_fluentbit_versions(repo_root: Path) -> list[str]:
    source_dir = repo_root / "config-service" / "json-definitions"
    versions: set[str] = set()
    if source_dir.exists():
        for path in source_dir.glob("fluent-bit-*-all-plugins-catalog.json"):
            version = (
                path.name
                .removeprefix("fluent-bit-")
                .removesuffix("-all-plugins-catalog.json")
                .strip()
            )
            if version:
                versions.add(version)
    return sorted(versions)


def _ensure_build_backend_requirements(
    runtime: CommandRuntime,
    *,
    component: BuildComponent,
    python_exe: str,
) -> None:
    """Install build backend requirements when using `python -m build --no-isolation`."""
    pyproject_path = component.path / "pyproject.toml"
    if not pyproject_path.exists():
        return
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    build_system = payload.get("build-system")
    if not isinstance(build_system, dict):
        return
    requirements = build_system.get("requires")
    if not isinstance(requirements, list):
        return
    normalized_requirements = [
        str(requirement).strip()
        for requirement in requirements
        if str(requirement).strip()
    ]
    if not normalized_requirements:
        return
    runtime.info(
        f"Installing build backend requirements for {component.key}: "
        + ", ".join(normalized_requirements)
    )
    runtime.run(
        [python_exe, "-m", "pip", "install", *normalized_requirements],
        cwd=runtime.repo_root,
    )


def _latest_wheel(directory: Path) -> Path:
    wheels = sorted(directory.glob("*.whl"))
    if not wheels:
        raise RuntimeError(f"no wheel artifacts found in {directory}")
    return wheels[-1]
