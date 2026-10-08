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

    assert "CONFIGURED_CLOUD_PROVIDER: ${{ vars.CLOUD_PROVIDER || '' }}" in workflow
    assert "DEFAULT_CLOUD_PROVIDER: ${{ github.event_name == 'push' && 'aws' || 'none' }}" in workflow
    assert "REQUESTED_CLOUD_PROVIDER: ${{ inputs.cloud_provider || 'configured' }}" in workflow
    assert 'cloud_provider="$DEFAULT_CLOUD_PROVIDER"' in workflow
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


def test_workflow_avoids_external_marketplace_actions() -> None:
    """Keep the workflow compatible with the organization-owned action policy."""
    workflow = _workflow_text()

    assert "uses:" not in workflow
    assert "ACTIONS_ID_TOKEN_REQUEST_URL" in workflow
    assert "assume-role-with-web-identity" in workflow
    assert "az login" in workflow
    assert "x-access-token:%s" in workflow
    assert "AUTHORIZATION: basic $checkout_auth_header" in workflow
    assert "AUTHORIZATION: bearer $GITHUB_TOKEN" not in workflow
    assert "::add-mask::$aws_access_key_id" in workflow
    assert "::add-mask::$aws_secret_access_key" in workflow
    assert "::add-mask::$aws_session_token" in workflow


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

    assert "Validate AWS repository configuration" in workflow
    assert "AWS_ROLE_TO_ASSUME repository secret is required for AWS mode" in workflow
    assert "AWS_KEY_NAME repository variable is required for AWS mode" in workflow
    assert "AWS_ADMIN_SOURCE_CIDR repository variable is required for AWS mode" in workflow
    assert "Set CLOUD_PROVIDER to none" in workflow
    assert "PARAMETERS_FILE: cloud/aws/parameters.workflow.env" in workflow
    assert "run: bash cloud/aws/deploy.sh" in workflow


def test_aws_mode_runs_and_retains_regression_evidence() -> None:
    """Run the regression pack after deployment and publish evidence before failing."""
    workflow = _workflow_text()

    assert "timeout-minutes: 180" in workflow
    assert "id: aws_regression" in workflow
    assert "AWS_REGRESSION_ONLY: ${{ vars.AWS_REGRESSION_ONLY }}" in workflow
    assert "AWS_REGRESSION_SKIP: ${{ vars.AWS_REGRESSION_SKIP }}" in workflow
    assert "python3 cloud/run_regression.py" in workflow
    assert "set +e\n          python3 cloud/run_regression.py" in workflow
    assert "regression_exit_code=$?\n          set -e" in workflow
    assert "--provider aws --aws-region" in workflow
    assert "regression_arguments+=(--only \"$test_id\")" in workflow
    assert "regression_arguments+=(--skip \"$test_id\")" in workflow
    assert "regression-pack-results.md" in workflow
    assert "AWS regression passed, but retained evidence upload failed" in workflow
    assert "AWS regression report: $regression_report" in workflow
    assert "AWS regression upload manifest: $upload_manifest" in workflow
    assert "No regression-pack-results.md file was found" in workflow
    assert "Fail when AWS regression or evidence upload failed" in workflow


def test_operator_guide_documents_cloud_provider_control() -> None:
    """Document provider values and required repository configuration."""
    operator_guide = OPERATOR_GUIDE_PATH.read_text(encoding="utf-8")

    assert "## Main workflow cloud control" in operator_guide
    assert "`CLOUD_PROVIDER`" in operator_guide
    assert "`azure`" in operator_guide
    assert "`aws`" in operator_guide
    assert "Use `aws` for pushes to `main`" in operator_guide
    assert "`AWS_ROLE_TO_ASSUME`" in operator_guide
    assert "`AWS_REGRESSION_ONLY`" in operator_guide
