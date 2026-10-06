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

"""Contract tests for selectable cloud deployment in the main workflow."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "main_fluent-opamp.yml"
OPERATOR_GUIDE_PATH = REPOSITORY_ROOT / "cloud" / "operator_guide.md"


def _workflow_text() -> str:
    """Read the main workflow as text without YAML's special `on` coercion."""
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def test_workflow_accepts_azure_aws_or_no_cloud_provider() -> None:
    """Expose the supported deployment modes through one validated control."""
    workflow = _workflow_text()

    assert "CONFIGURED_CLOUD_PROVIDER: ${{ vars.CLOUD_PROVIDER || 'none' }}" in workflow
    assert "REQUESTED_CLOUD_PROVIDER: ${{ inputs.cloud_provider || 'configured' }}" in workflow
    assert "azure|aws|none" in workflow
    assert "CLOUD_PROVIDER must be azure, aws, or none" in workflow


def test_provider_jobs_are_mutually_gated_by_selected_output() -> None:
    """Ensure only the selected provider can request cloud credentials."""
    workflow = _workflow_text()

    assert "deploy_azure:" in workflow
    assert "deploy_aws:" in workflow
    assert "no_cloud_deployment:" in workflow
    assert "outputs.cloud_provider == 'azure'" in workflow
    assert "outputs.cloud_provider == 'aws'" in workflow
    assert "outputs.cloud_provider == 'none'" in workflow
    assert workflow.count("uses: azure/login@v2") == 1
    assert workflow.count("uses: aws-actions/configure-aws-credentials@v6.3.0") == 1


def test_no_cloud_mode_keeps_the_build_enabled() -> None:
    """Keep validation active when cloud deployment is intentionally disabled."""
    workflow = _workflow_text()
    build_section = workflow.split("  build:", maxsplit=1)[1].split(
        "  deploy_azure:", maxsplit=1
    )[0]
    build_job_header = build_section.split("    steps:", maxsplit=1)[0]

    assert "if: needs.select_cloud_provider.outputs.cloud_provider" not in build_job_header
    assert "pip install -r requirements.txt" in build_section


def test_aws_mode_uses_the_existing_cloudformation_deployment() -> None:
    """Route AWS mode through the tested repository deployment script."""
    workflow = _workflow_text()

    assert "AWS_KEY_NAME repository variable is required" in workflow
    assert "AWS_ADMIN_SOURCE_CIDR repository variable is required" in workflow
    assert "PARAMETERS_FILE: cloud/aws/parameters.workflow.env" in workflow
    assert "run: bash cloud/aws/deploy.sh" in workflow


def test_operator_guide_documents_cloud_provider_control() -> None:
    """Document provider values and required repository configuration."""
    operator_guide = OPERATOR_GUIDE_PATH.read_text(encoding="utf-8")

    assert "## Main workflow cloud control" in operator_guide
    assert "`CLOUD_PROVIDER`" in operator_guide
    assert "`azure`" in operator_guide
    assert "`aws`" in operator_guide
    assert "`none` or unset" in operator_guide
    assert "`AWS_ROLE_TO_ASSUME`" in operator_guide
