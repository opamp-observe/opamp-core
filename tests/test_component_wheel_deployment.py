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

"""Unit tests for the component wheel deployment regression harness."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import tomllib

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
COMPONENT_RUNNER_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "test-containers"
    / "component-wheel-deployment"
    / "scripts"
    / "run_component_wheel_deployment.py"
)
CONSUMER_PYPROJECT_PATH = REPOSITORY_ROOT / "consumer" / "pyproject.toml"
AGENT_BROKER_PYPROJECT_PATH = REPOSITORY_ROOT / "agent_broker" / "pyproject.toml"
CATALOG_SERVICE_PYPROJECT_PATH = REPOSITORY_ROOT / "catalog-service" / "pyproject.toml"
CLIENT_CONFIG_GENERATOR_PYPROJECT_PATH = (
    REPOSITORY_ROOT / "client-config-generator-service" / "pyproject.toml"
)
CONFIG_SERVICE_SETUP_PATH = REPOSITORY_ROOT / "config-service" / "setup.py"
CONFIG_SERVICE_PYPROJECT_PATH = REPOSITORY_ROOT / "config-service" / "pyproject.toml"
PROVIDER_PYPROJECT_PATH = REPOSITORY_ROOT / "provider" / "pyproject.toml"
SHARED_PYPROJECT_PATH = REPOSITORY_ROOT / "shared" / "pyproject.toml"
SHARED_DISTRIBUTION_REQUIREMENT = "opamp-shared==0.6.0"


def _load_component_runner_module() -> ModuleType:
    """Load the standalone component wheel harness for focused unit tests."""
    module_spec = importlib.util.spec_from_file_location(
        "component_wheel_deployment_runner",
        COMPONENT_RUNNER_PATH,
    )
    assert module_spec is not None
    assert module_spec.loader is not None
    component_runner_module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = component_runner_module
    module_spec.loader.exec_module(component_runner_module)
    return component_runner_module


@pytest.fixture(name="component_runner_module")
def fixture_component_runner_module() -> ModuleType:
    """Provide a freshly loaded component wheel harness module."""
    return _load_component_runner_module()


def _write_sample_pyproject(component_path: Path) -> None:
    """Create minimal packaging metadata consumed by the harness under test."""
    component_path.mkdir(parents=True)
    (component_path / "pyproject.toml").write_text(
        """[project]
name = "sample-component"
version = "0.0.1"

[project.scripts]
sample-component = "sample_module:main"
""",
        encoding="utf-8",
    )


def test_component_import_check_uses_isolated_config_and_workdir(
    component_runner_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify import checks use generated config and cannot see the source tree."""
    repository_root = tmp_path / "repo"
    clean_root = tmp_path / "clean"
    wheelhouse = tmp_path / "wheelhouse"
    component_path = repository_root / "sample-component"
    wheel_path = wheelhouse / "sample_component-0.0.1-py3-none-any.whl"
    _write_sample_pyproject(component_path)
    clean_root.mkdir()
    wheelhouse.mkdir()
    wheel_path.write_text("placeholder wheel", encoding="utf-8")
    captured_runs: list[dict[str, Any]] = []

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        timeout: int = 900,
    ) -> dict[str, object]:
        """Capture harness subprocess calls without creating venvs or installing wheels."""
        captured_runs.append(
            {
                "command": command,
                "cwd": cwd,
                "env": env,
                "timeout": timeout,
            }
        )
        return {
            "command": command,
            "exit_code": 0,
            "duration_seconds": 0.0,
            "stdout": "",
            "stderr": "",
        }

    monkeypatch.setattr(component_runner_module, "_run", fake_run)
    component = component_runner_module.Component(
        "sample-component",
        "sample-component",
        ("sample_module",),
    )

    result = component_runner_module._test_component(
        component,
        repo_root=repository_root,
        clean_root=clean_root,
        wheelhouse=wheelhouse,
        wheels_by_component={"sample-component": wheel_path},
    )

    assert result["passed"] is True
    import_run = next(
        run
        for run in captured_runs
        if "importlib.import_module" in " ".join(run["command"])
    )
    expected_config_path = clean_root / "opamp.json"
    expected_import_work_dir = clean_root / "import-workdirs" / "sample-component"
    assert import_run["cwd"] == expected_import_work_dir
    assert import_run["env"][component_runner_module.ENV_OPAMP_CONFIG_PATH] == str(
        expected_config_path
    )
    assert import_run["env"][component_runner_module.ENV_PYTHONNOUSERSITE] == "1"
    assert component_runner_module.ENV_PYTHONPATH not in import_run["env"]
    assert expected_config_path.is_file()


def test_runtime_components_depend_on_shared_distribution() -> None:
    """Ensure component wheels depend on rather than bundle the shared package."""
    pyproject_paths = [
        PROVIDER_PYPROJECT_PATH,
        CONSUMER_PYPROJECT_PATH,
        AGENT_BROKER_PYPROJECT_PATH,
        CATALOG_SERVICE_PYPROJECT_PATH,
        CLIENT_CONFIG_GENERATOR_PYPROJECT_PATH,
        CONFIG_SERVICE_PYPROJECT_PATH,
    ]

    for pyproject_path in pyproject_paths:
        pyproject_payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        assert SHARED_DISTRIBUTION_REQUIREMENT in pyproject_payload["project"]["dependencies"]
        assert pyproject_payload["tool"]["uv"]["sources"]["opamp-shared"]["path"] == "../shared"


def test_component_builds_do_not_claim_shared_package_files() -> None:
    """Ensure component build configuration leaves shared files to opamp-shared."""
    provider_payload = tomllib.loads(PROVIDER_PYPROJECT_PATH.read_text(encoding="utf-8"))
    consumer_payload = tomllib.loads(CONSUMER_PYPROJECT_PATH.read_text(encoding="utf-8"))
    broker_payload = tomllib.loads(AGENT_BROKER_PYPROJECT_PATH.read_text(encoding="utf-8"))
    catalog_payload = tomllib.loads(CATALOG_SERVICE_PYPROJECT_PATH.read_text(encoding="utf-8"))
    generator_payload = tomllib.loads(
        CLIENT_CONFIG_GENERATOR_PYPROJECT_PATH.read_text(encoding="utf-8")
    )
    setuptools_config = catalog_payload["tool"]["setuptools"]
    generator_setuptools_config = generator_payload["tool"]["setuptools"]
    config_service_setup = CONFIG_SERVICE_SETUP_PATH.read_text(encoding="utf-8")

    assert provider_payload["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == [
        "src/opamp_provider"
    ]
    assert "force-include" not in consumer_payload["tool"]["hatch"]["build"]["targets"]["wheel"]
    assert "force-include" not in broker_payload["tool"]["hatch"]["build"]["targets"]["wheel"]
    assert setuptools_config["package-dir"] == {"": "src"}
    assert "shared" not in setuptools_config["packages"]
    assert 'SHARED_PACKAGE_NAME = "shared"' not in config_service_setup
    assert 'package_dir={"": "src"}' in config_service_setup
    assert generator_setuptools_config["package-dir"] == {"": "src"}
    assert "shared" not in generator_setuptools_config["packages"]


def test_shared_distribution_owns_shared_import_package() -> None:
    """Verify opamp-shared is the sole package metadata owner for shared imports."""
    shared_payload = tomllib.loads(SHARED_PYPROJECT_PATH.read_text(encoding="utf-8"))

    assert shared_payload["project"]["name"] == "opamp-shared"
    assert shared_payload["tool"]["setuptools"]["packages"] == ["shared"]
