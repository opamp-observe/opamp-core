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

"""Contract tests for shared Python project packaging metadata."""

from pathlib import Path

import tomllib

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
APACHE_LICENSE_DECLARATION = 'license = "Apache-2.0"'
DEPRECATED_LICENSE_TABLE_PREFIX = "license = {"
PEP_639_HATCHLING_REQUIREMENT = 'requires = ["hatchling>=1.27"]'
REQUIRED_DEV_DEPENDENCIES = {
    "pylint>=3.0",
    "pytest>=8.0",
    "pytest-cov>=7.0.0",
    "ruff>=0.15.0",
}
REQUIRED_RUFF_RULES = {"E", "F", "I", "S", "UP"}
REQUIRED_SECURITY_DEPENDENCIES = {
    "bandit>=1.9.4",
    "detect-secrets>=1.5.0",
    "mcp==1.29.0",
    "pip-audit>=2.10.1",
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=7.0.0",
    "ruff>=0.15.0",
    "semgrep>=1.182.1",
}
SECURITY_TOOLING_PROJECT_PATH = "dev-tools/pyproject.toml"

PYTHON_PROJECT_PATHS = (
    "agent_broker/pyproject.toml",
    "catalog-service/pyproject.toml",
    "cli/pyproject.toml",
    "client-config-generator-service/pyproject.toml",
    "config-service/pyproject.toml",
    "consumer/pyproject.toml",
    "consumer-sim/pyproject.toml",
    "dev-tools/pyproject.toml",
    "mcp/pyproject.toml",
    "provider/pyproject.toml",
    "svr-credentials-mgr/pyproject.toml",
    "svr-credentials-mgr/plaintext-keyring/pyproject.toml",
)
HATCHLING_PROJECT_PATHS = (
    "agent_broker/pyproject.toml",
    "consumer/pyproject.toml",
    "provider/pyproject.toml",
)


def test_python_projects_use_pep_639_license_expressions() -> None:
    """Keep every packaged module on the non-deprecated SPDX license form."""
    for relative_path in PYTHON_PROJECT_PATHS:
        metadata = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
        assert APACHE_LICENSE_DECLARATION in metadata
        assert DEPRECATED_LICENSE_TABLE_PREFIX not in metadata


def test_hatchling_projects_require_pep_639_support() -> None:
    """Require the first Hatchling release that supports PEP 639 metadata."""
    for relative_path in HATCHLING_PROJECT_PATHS:
        metadata = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
        assert PEP_639_HATCHLING_REQUIREMENT in metadata


def test_python_projects_expose_the_shared_development_baseline() -> None:
    """Keep lint, test, and coverage dependencies available in every packaged module."""
    for relative_path in PYTHON_PROJECT_PATHS:
        with (REPOSITORY_ROOT / relative_path).open("rb") as project_handle:
            payload = tomllib.load(project_handle)
        dev_dependencies = set(payload["project"]["optional-dependencies"]["dev"])
        assert REQUIRED_DEV_DEPENDENCIES <= dev_dependencies, relative_path
        selected_rules = set(payload["tool"]["ruff"]["lint"]["select"])
        assert REQUIRED_RUFF_RULES <= selected_rules, relative_path


def test_developer_tools_declares_the_security_toolchain() -> None:
    """Keep the security gate's external tools reproducible through a named extra."""
    with (REPOSITORY_ROOT / SECURITY_TOOLING_PROJECT_PATH).open("rb") as project_handle:
        payload = tomllib.load(project_handle)
    security_dependencies = set(
        payload["project"]["optional-dependencies"]["security"]
    )
    assert REQUIRED_SECURITY_DEPENDENCIES == security_dependencies
