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

"""Contract tests for shared Python project packaging metadata."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
APACHE_LICENSE_DECLARATION = 'license = "Apache-2.0"'
DEPRECATED_LICENSE_TABLE_PREFIX = "license = {"
PEP_639_HATCHLING_REQUIREMENT = 'requires = ["hatchling>=1.27"]'

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
