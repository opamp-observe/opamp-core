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

"""Contract tests for the GitHub-to-PyPI release workflow."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "publish_pypi.yml"
PYPI_ENVIRONMENT_DECLARATION = "      name: pypi"
TRUSTED_PUBLISHING_ARGUMENT = "--trusted-publishing always"
PYPI_TOKEN_SECRET_REFERENCE = "secrets.PYPI"
DEFAULT_BRANCH_REFERENCE = "github.ref == 'refs/heads/main'"
TEST_WORKFLOW_FILE = "main_fluent-opamp.yml"


def test_pypi_release_workflow_builds_before_publishing() -> None:
    """Require release and manual triggers plus the validated release-assets build."""
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "  release:" in workflow
    assert "  workflow_dispatch:" in workflow
    assert ".venv/bin/opamp-dev-cli build release-assets --skip-manual" in workflow
    assert ".venv/bin/opamp-dev-cli dev publish-pypi --index pypi --dry-run" in workflow
    assert "needs:\n      - verify_tests" in workflow
    assert "needs:\n      - build" in workflow


def test_pypi_release_workflow_requires_successful_tests_for_same_commit() -> None:
    """Require a completed successful main-branch test run for the release SHA."""
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    verification_section, build_and_publish_sections = workflow.split("  build:\n", maxsplit=1)

    assert "  verify_tests:" in verification_section
    assert "actions: read" in verification_section
    assert f"REQUIRED_WORKFLOW_FILE: {TEST_WORKFLOW_FILE}" in verification_section
    assert "EXPECTED_SHA: ${{ github.sha }}" in verification_section
    assert '--data-urlencode "head_sha=$EXPECTED_SHA"' in verification_section
    assert '--data-urlencode "status=completed"' in verification_section
    assert ".conclusion == $expected_conclusion" in verification_section
    assert "needs:\n      - verify_tests" in build_and_publish_sections


def test_pypi_release_workflow_uses_oidc_in_publish_job_only() -> None:
    """Keep long-lived tokens out of the workflow and require trusted publishing."""
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    build_section, publish_section = workflow.split("  publish:\n", maxsplit=1)

    assert "id-token: write" not in build_section
    assert "id-token: write" in publish_section
    assert PYPI_ENVIRONMENT_DECLARATION in publish_section
    assert TRUSTED_PUBLISHING_ARGUMENT in publish_section
    assert PYPI_TOKEN_SECRET_REFERENCE not in workflow
    assert DEFAULT_BRANCH_REFERENCE in publish_section


def test_pypi_release_workflow_transfers_only_built_wheels() -> None:
    """Require an artifact boundary between unprivileged build and OIDC publish jobs."""
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "name: pypi-distributions" in workflow
    assert "actions/upload-artifact@" in workflow
    assert "actions/download-artifact@" in workflow
    assert "pypi-dist/*.whl" in workflow
    assert "path: dist" in workflow
    assert "dist/*.whl" in workflow
    assert "Generate PEP 740 attestations" in workflow
