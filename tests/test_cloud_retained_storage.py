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

"""Contract tests for retained cloud artifacts and regression results."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
AWS_DIRECTORY = REPOSITORY_ROOT / "cloud" / "aws"
AZURE_DIRECTORY = REPOSITORY_ROOT / "cloud" / "azure"
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "deploy_aws.yml"
OPERATOR_GUIDE_PATH = REPOSITORY_ROOT / "cloud" / "operator_guide.md"
REGRESSION_COMMAND_PATH = REPOSITORY_ROOT / "cloud" / "run_regression.py"

LICENSE_COPYRIGHT = "Copyright 2026 mp3monster.org"
LICENSE_GRANT = "Licensed under the Apache License, Version 2.0"


def _read(relative_path: Path) -> str:
    """Read one repository file using UTF-8 for portable assertions."""
    return relative_path.read_text(encoding="utf-8")


def test_aws_deploy_creates_timestamped_retained_storage() -> None:
    """Ensure AWS deployment creates private external storage and retains outputs."""
    bash_script = _read(AWS_DIRECTORY / "deploy.sh")
    powershell_script = _read(AWS_DIRECTORY / "deploy.ps1")

    assert "date -u +%Y%m%d%H%M%S" in bash_script
    assert "opamp-regression-${aws_account_id}-${DEPLOYMENT_TIMESTAMP}" in bash_script
    assert "put-public-access-block" in bash_script
    assert "regression-results" in bash_script
    assert "stack-outputs.json" in bash_script
    assert "ARTIFACT_BUCKET is required" not in bash_script
    assert "AWS::S3::Bucket" not in _read(AWS_DIRECTORY / "template.yaml")
    assert 'ToString("yyyyMMddHHmmss")' in powershell_script
    assert "opamp-regression-$awsAccountId-$deploymentTimestamp" in powershell_script
    assert "dist/aws-artifact-bucket.txt" in powershell_script


def test_aws_workflow_allows_generated_retained_bucket() -> None:
    """Ensure GitHub deployment permits automatic buckets and reports their names."""
    workflow = _read(WORKFLOW_PATH)

    assert "leave blank to create a timestamped bucket" in workflow
    assert 'echo "artifact_bucket is required"' not in workflow
    assert "dist/aws-artifact-bucket.txt" in workflow
    assert "not deleted when the CloudFormation stack is destroyed" in workflow


def test_azure_deploy_retains_results_outside_vm_resource_group() -> None:
    """Ensure Azure uses separate timestamped storage for artifacts and results."""
    bash_script = _read(AZURE_DIRECTORY / "deploy.sh")
    powershell_script = _read(AZURE_DIRECTORY / "deploy.ps1")

    assert "date -u +%Y%m%d%H%M%S" in bash_script
    assert 'RETENTION_RESOURCE_GROUP="${RETENTION_RESOURCE_GROUP:-${RESOURCE_GROUP}-retained}"' in bash_script
    assert 'STORAGE_ACCOUNT="opamp${DEPLOYMENT_TIMESTAMP}${subscription_suffix,,}"' in bash_script
    assert "opamp-regression-results" in bash_script
    assert "deployment-outputs.json" in bash_script
    assert 'artifactBaseUrl="$artifact_base_url"' in bash_script
    assert '"${RETENTION_RESOURCE_GROUP,,}" == "${RESOURCE_GROUP,,}"' in bash_script
    assert "Microsoft.Storage/storageAccounts" not in _read(AZURE_DIRECTORY / "mainTemplate.json")
    assert 'ToString("yyyyMMddHHmmss")' in powershell_script
    assert '"$ResourceGroup-retained"' in powershell_script
    assert "$RetentionResourceGroup -eq $ResourceGroup" in powershell_script
    assert "dist/azure-retention-storage-account.txt" in powershell_script


def test_bucket_cleanup_scripts_delete_only_selected_retained_storage() -> None:
    """Ensure each provider has explicit destructive storage cleanup entry points."""
    aws_bash = _read(AWS_DIRECTORY / "destroy-bucket.sh")
    aws_powershell = _read(AWS_DIRECTORY / "destroy-bucket.ps1")
    azure_bash = _read(AZURE_DIRECTORY / "destroy-bucket.sh")
    azure_powershell = _read(AZURE_DIRECTORY / "destroy-bucket.ps1")

    assert 'aws s3 rb "s3://$BUCKET_NAME" --force' in aws_bash
    assert '[string]$BucketName = ""' in aws_powershell
    assert "dist/aws-artifact-bucket.txt" in aws_bash
    assert "dist/aws-artifact-bucket.txt" in aws_powershell
    assert 'rm -f "$ARTIFACT_BUCKET_FILE"' in aws_bash
    assert "Remove-Item -LiteralPath $ArtifactBucketFile" in aws_powershell
    assert "az storage account show" in azure_bash
    assert "az storage account delete" in azure_bash
    assert '[Parameter(Mandatory = $true)][string]$StorageAccount' in azure_powershell
    assert "az group delete" not in azure_bash
    assert "az group delete" not in azure_powershell


def test_infrastructure_destroy_scripts_preserve_retained_storage() -> None:
    """Ensure ordinary teardown never invokes either provider's storage deletion."""
    aws_destroy = _read(AWS_DIRECTORY / "destroy.sh")
    azure_destroy = _read(AZURE_DIRECTORY / "destroy.sh")

    assert "aws s3 rb" not in aws_destroy
    assert "destroy-bucket.sh explicitly" in aws_destroy
    assert "az storage account delete" not in azure_destroy
    assert "destroy-bucket.sh explicitly" in azure_destroy


def test_aws_destroy_polls_until_cloudformation_deletion_completes() -> None:
    """Ensure AWS teardown reports status every 30 seconds until terminal state."""
    bash_script = _read(AWS_DIRECTORY / "destroy.sh")
    powershell_script = _read(AWS_DIRECTORY / "destroy.ps1")

    assert 'DELETE_POLL_INTERVAL_SECONDS="${DELETE_POLL_INTERVAL_SECONDS:-30}"' in bash_script
    assert "aws cloudformation describe-stacks" in bash_script
    assert 'sleep "$DELETE_POLL_INTERVAL_SECONDS"' in bash_script
    assert 'DELETE_FAILED_STATUS="DELETE_FAILED"' in bash_script
    assert "[int]$PollIntervalSeconds = 30" in powershell_script
    assert "aws cloudformation describe-stacks" in powershell_script
    assert "$stackAlreadyDeleted = $true" in powershell_script
    assert "CloudFormation stack $StackName no longer exists" in powershell_script
    assert '$ErrorActionPreference = "Continue"' in powershell_script
    assert "$ErrorActionPreference = $previousErrorActionPreference" in powershell_script
    assert "2>&1" in powershell_script
    assert "Start-Sleep -Seconds $PollIntervalSeconds" in powershell_script
    assert '$deleteFailedStatus = "DELETE_FAILED"' in powershell_script


def test_new_and_replaced_cloud_scripts_are_licensed() -> None:
    """Ensure retained-storage implementation files carry the project license header."""
    source_paths = [
        AWS_DIRECTORY / "destroy-bucket.sh",
        AWS_DIRECTORY / "destroy-bucket.ps1",
        AZURE_DIRECTORY / "deploy.sh",
        AZURE_DIRECTORY / "deploy.ps1",
        AZURE_DIRECTORY / "destroy.sh",
        AZURE_DIRECTORY / "destroy.ps1",
        AZURE_DIRECTORY / "destroy-bucket.sh",
        AZURE_DIRECTORY / "destroy-bucket.ps1",
        AZURE_DIRECTORY / "scripts" / "package-cloud-artifacts.ps1",
    ]

    for source_path in source_paths:
        source_text = _read(source_path)
        assert LICENSE_COPYRIGHT in source_text
        assert LICENSE_GRANT in source_text


def test_all_cloud_command_scripts_are_licensed() -> None:
    """Keep operator-facing Bash and PowerShell entry points consistently licensed."""
    source_paths = [
        source_path
        for cloud_directory in (AWS_DIRECTORY, AZURE_DIRECTORY)
        for pattern in ("*.sh", "*.ps1")
        for source_path in cloud_directory.rglob(pattern)
    ]

    assert source_paths
    for source_path in source_paths:
        source_text = _read(source_path)
        assert LICENSE_COPYRIGHT in source_text
        assert LICENSE_GRANT in source_text


def test_cloud_operator_guide_explains_provider_neutral_lifecycle() -> None:
    """Give IaC operators a shared map of lifecycle, ownership, and failures."""
    operator_guide = _read(OPERATOR_GUIDE_PATH)
    aws_readme = _read(AWS_DIRECTORY / "readme.md")
    azure_readme = _read(AZURE_DIRECTORY / "README.md")

    assert LICENSE_COPYRIGHT in operator_guide
    assert "## Provider vocabulary" in operator_guide
    assert "## Deployment phases" in operator_guide
    assert "## Resource ownership" in operator_guide
    assert "## Reading failures" in operator_guide
    assert "## Safe reruns" in operator_guide
    assert "../operator_guide.md" in aws_readme
    assert "../operator_guide.md" in azure_readme


def test_cloud_powershell_scripts_support_windows_powershell_encoding() -> None:
    """Avoid PowerShell 7-only encoding names in deployment and packaging scripts."""
    powershell_paths = [
        AWS_DIRECTORY / "deploy.ps1",
        AWS_DIRECTORY / "scripts" / "package-cloud-artifacts.ps1",
        AZURE_DIRECTORY / "deploy.ps1",
        AZURE_DIRECTORY / "scripts" / "package-cloud-artifacts.ps1",
    ]

    for powershell_path in powershell_paths:
        source_text = _read(powershell_path)
        assert "-encoding utf8nobom" not in source_text.lower()
        assert "System.Text.UTF8Encoding" in source_text


def test_cloud_powershell_packagers_normalize_linux_script_line_endings() -> None:
    """Ensure artifacts contain Bash-readable scripts after a Windows checkout."""
    powershell_paths = [
        AWS_DIRECTORY / "scripts" / "package-cloud-artifacts.ps1",
        AZURE_DIRECTORY / "scripts" / "package-cloud-artifacts.ps1",
    ]

    for powershell_path in powershell_paths:
        source_text = _read(powershell_path)
        assert '.Replace("`r`n", "`n")' in source_text
        assert "$runtimeScriptDestination" in source_text
        assert "[IO.File]::WriteAllText(" in source_text


def test_cloud_powershell_packagers_write_linux_wheel_manifests() -> None:
    """Ensure wheel paths read by Bash cannot retain Windows carriage returns."""
    powershell_paths = [
        AWS_DIRECTORY / "scripts" / "package-cloud-artifacts.ps1",
        AZURE_DIRECTORY / "scripts" / "package-cloud-artifacts.ps1",
    ]

    for powershell_path in powershell_paths:
        source_text = _read(powershell_path)
        assert '$wheelManifestContent = [string]::Join("`n", [string[]]$wheelNames) + "`n"' in source_text
        assert "[IO.File]::WriteAllLines(" not in source_text


def test_cloud_bash_packagers_limit_recursive_cleanup_to_dist() -> None:
    """Prevent a custom artifact path from expanding recursive cleanup scope."""
    bash_paths = [
        AWS_DIRECTORY / "scripts" / "package-cloud-artifacts.sh",
        AZURE_DIRECTORY / "scripts" / "package-cloud-artifacts.sh",
    ]

    for bash_path in bash_paths:
        source_text = _read(bash_path)
        assert '"$REPO_ROOT"/dist/*)' in source_text
        assert "OUTPUT_DIR must be inside" in source_text
        assert source_text.index("OUTPUT_DIR must be inside") < source_text.index(
            'rm -rf "$OUTPUT_DIR"'
        )


def test_cloud_powershell_deploy_paths_are_repository_relative() -> None:
    """Keep local deployment files independent of the caller's working directory."""
    aws_script = _read(AWS_DIRECTORY / "deploy.ps1")
    azure_script = _read(AZURE_DIRECTORY / "deploy.ps1")

    for powershell_script in (aws_script, azure_script):
        assert 'Join-Path $PSScriptRoot "..\\.."' in powershell_script
        assert "[IO.Path]::IsPathRooted" in powershell_script

    assert 'Join-Path $repositoryRoot "dist/aws-regression-results/' in aws_script
    assert 'Join-Path $repositoryRoot "dist/azure-regression-results/' in azure_script


def test_aws_parameters_are_validated_before_creating_resources() -> None:
    """Reject example values before packaging artifacts or creating retained storage."""
    bash_script = _read(AWS_DIRECTORY / "deploy.sh")
    powershell_script = _read(AWS_DIRECTORY / "deploy.ps1")

    assert bash_script.index("parameter_overrides=()") < bash_script.index(
        'if [[ -z "$ARTIFACT_BUCKET" ]]'
    )
    assert powershell_script.index("$parameterOverrides = @()") < powershell_script.index(
        "if (-not $ArtifactBucket)"
    )
    for deployment_script in (bash_script, powershell_script):
        assert "aws ec2 describe-key-pairs" in deployment_script


def test_aws_deploy_detects_placeholder_administrator_cidr() -> None:
    """Resolve the example administrator CIDR to a validated public IPv4 address."""
    bash_script = _read(AWS_DIRECTORY / "deploy.sh")
    powershell_script = _read(AWS_DIRECTORY / "deploy.ps1")
    readme = _read(AWS_DIRECTORY / "readme.md")

    for deployment_script in (bash_script, powershell_script):
        assert "https://checkip.amazonaws.com" in deployment_script
        assert "Detected administrator source CIDR" in deployment_script
        assert "Set AdminSourceCidr" in deployment_script

    assert "IPv4Address" in bash_script
    assert "System.Net.IPAddress" in powershell_script
    assert "Explicit values are never replaced" in readme


def test_aws_deploy_reports_failed_cloudformation_events() -> None:
    """Print actionable resource events when CloudFormation deployment fails."""
    bash_script = _read(AWS_DIRECTORY / "deploy.sh")
    powershell_script = _read(AWS_DIRECTORY / "deploy.ps1")

    for deployment_script in (bash_script, powershell_script):
        assert "cloudformation describe-stack-events" in deployment_script
        assert "contains(ResourceStatus, 'FAILED')" in deployment_script
        assert "ResourceStatusReason" in deployment_script
        assert "CloudFormation failed resource events:" in deployment_script


def test_aws_deploy_can_create_and_store_an_ec2_key_pair() -> None:
    """Cover opt-in key generation, local protection, and failed-write cleanup."""
    bash_script = _read(AWS_DIRECTORY / "deploy.sh")
    powershell_script = _read(AWS_DIRECTORY / "deploy.ps1")
    readme = _read(AWS_DIRECTORY / "readme.md")

    assert 'CREATE_KEY_PAIR="${CREATE_KEY_PAIR:-false}"' in bash_script
    assert "create_ec2_key_pair" in bash_script
    assert "aws ec2 create-key-pair" in bash_script
    assert 'chmod 600 "$private_key_file"' in bash_script
    assert "aws ec2 delete-key-pair" in bash_script
    assert "[switch]$CreateKeyPair" in powershell_script
    assert '[string]$NewKeyPairName = ""' in powershell_script
    assert "aws ec2 create-key-pair" in powershell_script
    assert "[IO.File]::WriteAllText" in powershell_script
    assert "icacls.exe" in powershell_script
    assert "aws ec2 delete-key-pair" in powershell_script
    assert "dist/aws-key-pairs/<key-pair-name>.pem" in readme
    assert "-CreateKeyPair" in readme


def test_aws_deploy_infers_existing_key_pair_from_private_key_file() -> None:
    """Allow retained generated keys to be reused without editing parameter files."""
    bash_script = _read(AWS_DIRECTORY / "deploy.sh")
    powershell_script = _read(AWS_DIRECTORY / "deploy.ps1")

    assert 'private_key_file_key_pair_name="${private_key_file_name%.pem}"' in bash_script
    assert "Using EC2 key pair inferred from private key file" in bash_script
    assert "--filters \"Name=key-name,Values=$selected_key_pair_name\"" in bash_script
    assert "[IO.Path]::GetFileNameWithoutExtension($PrivateKeyFile)" in powershell_script
    assert "Using EC2 key pair inferred from private key file" in powershell_script
    assert '--filters "Name=key-name,Values=$selectedKeyPairName"' in powershell_script


def test_cloud_deployments_generate_and_retain_connection_guides() -> None:
    """Ensure both providers generate URL and SSH documentation after deployment."""
    aws_bash = _read(AWS_DIRECTORY / "deploy.sh")
    aws_powershell = _read(AWS_DIRECTORY / "deploy.ps1")
    azure_bash = _read(AZURE_DIRECTORY / "deploy.sh")
    azure_powershell = _read(AZURE_DIRECTORY / "deploy.ps1")

    for deployment_script in (aws_bash, aws_powershell, azure_bash, azure_powershell):
        assert "generate_cloud_connection_guide.py" in deployment_script
        assert "connection_details.md" in deployment_script
        assert "Connection guide:" in deployment_script

    assert "--ssh-private-key" in aws_bash
    assert "$PrivateKeyFile" in aws_powershell
    assert "SSH_PRIVATE_KEY_FILE" in azure_bash
    assert "$SshPrivateKeyFile" in azure_powershell


def test_cloud_regression_command_runs_and_uploads_reports_for_both_providers() -> None:
    """Ensure regression reports have an executable path into retained cloud storage."""
    regression_command = _read(REGRESSION_COMMAND_PATH)
    aws_readme = _read(AWS_DIRECTORY / "readme.md")
    azure_readme = _read(AZURE_DIRECTORY / "README.md")

    assert LICENSE_COPYRIGHT in regression_command
    assert LICENSE_GRANT in regression_command
    assert "run_regression_pack.py" in regression_command
    assert '"aws",' in regression_command
    assert '"az",' in regression_command
    assert '"--upload-only"' in regression_command
    assert "cloud_upload_manifest.json" in regression_command
    assert "cloud/run_regression.py --provider aws" in aws_readme
    assert "cloud/run_regression.py --provider azure" in azure_readme


def test_cloud_powershell_deploys_use_one_native_python_argument_array() -> None:
    """Prevent Windows PowerShell from dropping a second splatted argument array."""
    powershell_paths = [
        AWS_DIRECTORY / "deploy.ps1",
        AZURE_DIRECTORY / "deploy.ps1",
    ]

    for powershell_path in powershell_paths:
        source_text = _read(powershell_path)
        assert "$pythonInvocationArguments = @($pythonArguments) + $connectionGuideArguments" in source_text
        assert "& $pythonCommand @pythonInvocationArguments" in source_text
        assert "@pythonArguments @connectionGuideArguments" not in source_text
        assert "Test-Path -LiteralPath $connectionGuideFile -PathType Leaf" in source_text
        assert "(Get-Item -LiteralPath $connectionGuideFile).Length -eq 0" in source_text


def test_cloud_guides_document_retention_and_explicit_cleanup() -> None:
    """Ensure operators are warned that infrastructure teardown retains storage."""
    aws_readme = _read(AWS_DIRECTORY / "readme.md")
    azure_readme = _read(AZURE_DIRECTORY / "README.md")

    assert "dist/aws-artifact-bucket.txt" in aws_readme
    assert "cloud/aws/destroy-bucket.sh" in aws_readme
    assert "intentionally retained" in aws_readme
    assert "dist/azure-retention-storage-account.txt" in azure_readme
    assert "cloud/azure/destroy-bucket.sh" in azure_readme
    assert "private deployment-output record" in azure_readme
