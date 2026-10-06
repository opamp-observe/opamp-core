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

from __future__ import annotations

from pathlib import Path

from opamp_dev_tools.components import (
    BuildComponent,
    build_artifacts,
    build_pdf,
    discover_build_components,
    run_component_tests,
    run_e2e_tests,
)


def test_discover_build_components_finds_known_projects() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    component_keys = {component.key for component in discover_build_components(repo_root)}
    assert "cli" in component_keys
    assert "provider" in component_keys
    assert "config-service" in component_keys
    assert "client-config-generator-service" in component_keys
    assert "dev-tools" not in component_keys


class _RuntimeStub:
    """Simple runtime double for component helper tests.

    Attributes
    ----------
    repo_root:
        Repository root used by the component helpers under test.
    commands:
        Commands requested by the helper so assertions can inspect them.
    info_messages:
        Informational messages emitted during the helper run.
    module_checks:
        Python module dependency checks requested by the helper.
    """

    def __init__(self, repo_root: Path) -> None:
        """Initialise the stub state captured by the tests.

        Parameters
        ----------
        repo_root:
            Repository root exposed to the helper under test.
        """
        self.repo_root = repo_root
        self.commands: list[list[str]] = []
        self.info_messages: list[str] = []
        self.module_checks: list[tuple[str, str, str | None]] = []

    def ensure_python_module(self, *, python_exe: str, module_name: str, pip_package: str | None = None) -> None:
        """Record module dependency checks requested by the helper.

        Parameters
        ----------
        python_exe:
            Python interpreter that would perform the dependency check.
        module_name:
            Import name that the helper expects to be available.
        pip_package:
            Package name that would be installed if the import were missing.
        """
        self.module_checks.append((python_exe, module_name, pip_package))

    def run(self, command: list[str], *, cwd: Path | None = None, **_: object) -> None:
        """Record subprocess commands instead of executing them.

        Parameters
        ----------
        command:
            Command line that the helper requested.
        cwd:
            Working directory that would have been used for the command.
        """
        del cwd
        self.commands.append(command)

    def info(self, message: str) -> None:
        """Record informational messages for later assertions.

        Parameters
        ----------
        message:
            Informational console text emitted by the helper.
        """
        self.info_messages.append(message)


def test_build_artifacts_installs_build_backend_requires_for_no_isolation(tmp_path: Path) -> None:
    component_root = tmp_path / "agent_broker"
    component_root.mkdir()
    (component_root / "pyproject.toml").write_text(
        "\n".join(
            [
                "[build-system]",
                'requires = ["hatchling>=1.25"]',
                'build-backend = "hatchling.build"',
                "",
                "[project]",
                'name = "opamp-broker"',
                'version = "0.4.1"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    runtime = _RuntimeStub(tmp_path)
    component = BuildComponent(
        key="agent_broker",
        path=component_root,
        project_name="opamp-broker",
        version="0.4.1",
    )

    issues_found = build_artifacts(
        runtime,
        components=[component],
        python_exe="python",
        no_isolation=True,
    )

    assert issues_found is False
    assert runtime.module_checks == [("python", "build", "build")]
    assert runtime.commands[0] == ["python", "-m", "pip", "install", "hatchling>=1.25"]
    assert runtime.commands[1][0:7] == [
        "python",
        "-m",
        "build",
        "--sdist",
        "--wheel",
        "--outdir",
        str(tmp_path / "dist" / "agent_broker"),
    ]
    assert "--no-isolation" in runtime.commands[1]


def test_build_pdf_uses_dev_tools_manual_builder(tmp_path: Path) -> None:
    runtime = _RuntimeStub(tmp_path)

    issues_found = build_pdf(
        runtime,
        python_exe="python",
        output="dist/manual/custom.pdf",
    )

    assert issues_found is False
    assert runtime.module_checks == [("python", "reportlab", "reportlab")]
    assert runtime.commands == [
        [
            "python",
            str(tmp_path / "dev-tools" / "src" / "opamp_dev_tools" / "pdf_manual.py"),
            "--repo-root",
            str(tmp_path),
            "--output",
            "dist/manual/custom.pdf",
        ]
    ]


def test_run_component_tests_installs_pytest_dependencies_for_python_tests(tmp_path: Path) -> None:
    component_root = tmp_path / "provider"
    tests_dir = component_root / "tests"
    tests_dir.mkdir(parents=True)
    runtime = _RuntimeStub(tmp_path)
    component = BuildComponent(
        key="provider",
        path=component_root,
        project_name="opamp-server",
        version="0.4.1",
    )

    issues_found = run_component_tests(
        runtime,
        components=[component],
        python_exe="python",
    )

    assert issues_found is False
    assert runtime.module_checks == [
        ("python", "pytest", "pytest"),
        ("python", "pytest_cov", "pytest-cov"),
        ("python", "pytest_asyncio", "pytest-asyncio"),
    ]
    assert runtime.commands == [["python", "-m", "pytest", "-s"]]


def test_run_e2e_tests_installs_pytest_dependencies(tmp_path: Path) -> None:
    runtime = _RuntimeStub(tmp_path)

    issues_found = run_e2e_tests(
        runtime,
        python_exe="python",
    )

    assert issues_found is False
    assert runtime.module_checks == [
        ("python", "pytest", "pytest"),
        ("python", "pytest_cov", "pytest-cov"),
        ("python", "pytest_asyncio", "pytest-asyncio"),
    ]
    assert runtime.commands == [["python", "-m", "pytest", "-s", "tests/test_socket_e2e.py"]]
