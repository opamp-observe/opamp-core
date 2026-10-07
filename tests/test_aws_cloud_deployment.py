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

"""Contract tests for the AWS CloudFormation and deployment entry points."""

from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
AWS_DIRECTORY = REPOSITORY_ROOT / "cloud" / "aws"
TEMPLATE_PATH = AWS_DIRECTORY / "template.yaml"
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "deploy_aws.yml"

PARAMETERS_KEY = "Parameters"
RESOURCES_KEY = "Resources"
OUTPUTS_KEY = "Outputs"
TYPE_KEY = "Type"
PROPERTIES_KEY = "Properties"
SECURITY_GROUP_INGRESS_KEY = "SecurityGroupIngress"
FROM_PORT_KEY = "FromPort"
METADATA_OPTIONS_KEY = "MetadataOptions"
HTTP_TOKENS_KEY = "HttpTokens"
IAM_INSTANCE_PROFILE_KEY = "IamInstanceProfile"
USER_DATA_KEY = "UserData"
BASE64_KEY = "Fn::Base64"
SUBSTITUTION_KEY = "Fn::Sub"
GENERATE_SECRET_STRING_KEY = "GenerateSecretString"
ACTION_KEY = "Action"
BLOCK_DEVICE_MAPPINGS_KEY = "BlockDeviceMappings"
CIDR_IP_KEY = "CidrIp"
DEFAULT_KEY = "Default"
DELETE_ON_TERMINATION_KEY = "DeleteOnTermination"
DEPENDS_ON_KEY = "DependsOn"
EBS_KEY = "Ebs"
ENCRYPTED_KEY = "Encrypted"
POLICIES_KEY = "Policies"
POLICY_DOCUMENT_KEY = "PolicyDocument"
REF_KEY = "Ref"
STATEMENT_KEY = "Statement"

CONSUMER_INSTANCE_RESOURCE = "ConsumerInstance"
CONSUMER_PROFILE_RESOURCE = "ConsumerInstanceProfile"
CONSUMER_ROLE_RESOURCE = "ConsumerInstanceRole"
CONSUMER_SECURITY_GROUP_RESOURCE = "ConsumerSecurityGroup"
KEYCLOAK_SECRET_RESOURCE = "KeycloakAdminSecret"
SERVER_INSTANCE_RESOURCE = "ServerInstance"
SERVER_PROFILE_RESOURCE = "ServerInstanceProfile"
SERVER_ROLE_RESOURCE = "ServerInstanceRole"
SERVER_SECURITY_GROUP_RESOURCE = "ServerSecurityGroup"
SERVER_WAIT_CONDITION_RESOURCE = "ServerWaitCondition"
GET_SECRET_VALUE_ACTION = "secretsmanager:GetSecretValue"
LATEST_AMI_ID_PARAMETER = "LatestAmiId"

SERVER_INBOUND_PORTS = {22, 443, 8443}
CONSUMER_INBOUND_PORTS = {22}

EXPECTED_PARAMETERS = {
    "AdminSourceCidr",
    "ArtifactBucket",
    "ArtifactKey",
    "ConsumerPrivateIp",
    "InstanceType",
    "KeyName",
    "KeycloakAdminUser",
    "LatestAmiId",
    "NamePrefix",
    "PublicSubnetCidr",
    "ServerPrivateIp",
    "VpcCidr",
}
EXPECTED_OUTPUTS = {
    "ConsumerInstanceId",
    "ConsumerSsh",
    "KeycloakAdminSecretArn",
    "KeycloakUrl",
    "OpampUiUrl",
    "ServerInstanceId",
    "ServerSsh",
}
EXPECTED_RESOURCE_TYPES = {
    "AWS::CloudFormation::WaitCondition",
    "AWS::EC2::EIP",
    "AWS::EC2::Instance",
    "AWS::EC2::InternetGateway",
    "AWS::EC2::SecurityGroup",
    "AWS::EC2::Subnet",
    "AWS::EC2::VPC",
    "AWS::IAM::InstanceProfile",
    "AWS::IAM::Role",
    "AWS::SecretsManager::Secret",
}
UBUNTU_2204_AMI_PARAMETER = (
    "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id"
)


def _load_template() -> dict:
    """Load the CloudFormation YAML with ordinary mapping-based intrinsic functions."""
    return yaml.safe_load(TEMPLATE_PATH.read_text(encoding="utf-8"))


def _user_data(template: dict, resource_name: str) -> str:
    """Return the Fn::Sub user-data script for the named EC2 resource."""
    return template[RESOURCES_KEY][resource_name][PROPERTIES_KEY][USER_DATA_KEY][BASE64_KEY][
        SUBSTITUTION_KEY
    ]


def test_template_exposes_complete_parameter_and_output_contract() -> None:
    """Ensure command-line and workflow inputs map to stable template parameters and outputs."""
    template = _load_template()

    assert set(template[PARAMETERS_KEY]) == EXPECTED_PARAMETERS
    assert set(template[OUTPUTS_KEY]) == EXPECTED_OUTPUTS


def test_template_uses_published_ubuntu_2204_ami_parameter() -> None:
    """Use Canonical's published gp2 namespace while EC2 overrides disks to gp3."""
    template = _load_template()

    assert (
        template[PARAMETERS_KEY][LATEST_AMI_ID_PARAMETER][DEFAULT_KEY]
        == UBUNTU_2204_AMI_PARAMETER
    )


def test_template_contains_expected_aws_resource_families() -> None:
    """Ensure the AWS stack includes compute, network, identity, secret, and readiness resources."""
    template = _load_template()
    resource_types = {
        resource[TYPE_KEY] for resource in template[RESOURCES_KEY].values()
    }

    assert EXPECTED_RESOURCE_TYPES <= resource_types


def test_security_groups_limit_inbound_ports() -> None:
    """Ensure only the intended public service ports and restricted SSH are exposed."""
    resources = _load_template()[RESOURCES_KEY]
    server_ingress = resources[SERVER_SECURITY_GROUP_RESOURCE][PROPERTIES_KEY][
        SECURITY_GROUP_INGRESS_KEY
    ]
    consumer_ingress = resources[CONSUMER_SECURITY_GROUP_RESOURCE][PROPERTIES_KEY][
        SECURITY_GROUP_INGRESS_KEY
    ]

    assert {rule[FROM_PORT_KEY] for rule in server_ingress} == SERVER_INBOUND_PORTS
    assert {rule[FROM_PORT_KEY] for rule in consumer_ingress} == CONSUMER_INBOUND_PORTS
    assert server_ingress[-1][CIDR_IP_KEY] == {REF_KEY: "AdminSourceCidr"}
    assert consumer_ingress[0][CIDR_IP_KEY] == {REF_KEY: "AdminSourceCidr"}


def test_instances_require_imdsv2_and_encrypted_boot_volumes() -> None:
    """Ensure both EC2 roles enforce metadata tokens and encrypted disposable root volumes."""
    resources = _load_template()[RESOURCES_KEY]

    for resource_name in (SERVER_INSTANCE_RESOURCE, CONSUMER_INSTANCE_RESOURCE):
        properties = resources[resource_name][PROPERTIES_KEY]
        assert properties[METADATA_OPTIONS_KEY][HTTP_TOKENS_KEY] == "required"
        root_volume = properties[BLOCK_DEVICE_MAPPINGS_KEY][0][EBS_KEY]
        assert root_volume[ENCRYPTED_KEY] is True
        assert root_volume[DELETE_ON_TERMINATION_KEY] is True


def test_bootstrap_uses_private_artifacts_generated_secret_and_wait_signals() -> None:
    """Ensure VM bootstrap downloads through IAM and reports real readiness to CloudFormation."""
    template = _load_template()
    resources = template[RESOURCES_KEY]
    server_user_data = _user_data(template, SERVER_INSTANCE_RESOURCE)
    consumer_user_data = _user_data(template, CONSUMER_INSTANCE_RESOURCE)

    assert resources[KEYCLOAK_SECRET_RESOURCE][PROPERTIES_KEY][GENERATE_SECRET_STRING_KEY]
    assert "aws s3 cp 's3://${ArtifactBucket}/${ArtifactKey}'" in server_user_data
    assert "aws secretsmanager get-secret-value" in server_user_data
    assert "OPAMP_WHEEL_SOURCE_DIR" in server_user_data
    assert "signal_cloudformation SUCCESS" in server_user_data
    assert "OPAMP_DEPLOYMENT_PLATFORM=AWS" in consumer_user_data
    assert SERVER_WAIT_CONDITION_RESOURCE in resources[CONSUMER_INSTANCE_RESOURCE][DEPENDS_ON_KEY]


def test_consumer_role_cannot_read_keycloak_secret() -> None:
    """Keep administrator secret access on the server role only."""
    resources = _load_template()[RESOURCES_KEY]
    server_policies = resources[SERVER_ROLE_RESOURCE][PROPERTIES_KEY][POLICIES_KEY]
    consumer_policies = resources[CONSUMER_ROLE_RESOURCE][PROPERTIES_KEY][POLICIES_KEY]
    server_actions = {
        action
        for policy in server_policies
        for statement in policy[POLICY_DOCUMENT_KEY][STATEMENT_KEY]
        for action in statement[ACTION_KEY]
    }
    consumer_actions = {
        action
        for policy in consumer_policies
        for statement in policy[POLICY_DOCUMENT_KEY][STATEMENT_KEY]
        for action in statement[ACTION_KEY]
    }

    assert GET_SECRET_VALUE_ACTION in server_actions
    assert GET_SECRET_VALUE_ACTION not in consumer_actions
    assert resources[SERVER_INSTANCE_RESOURCE][PROPERTIES_KEY][IAM_INSTANCE_PROFILE_KEY] == {
        REF_KEY: SERVER_PROFILE_RESOURCE
    }
    assert resources[CONSUMER_INSTANCE_RESOURCE][PROPERTIES_KEY][IAM_INSTANCE_PROFILE_KEY] == {
        REF_KEY: CONSUMER_PROFILE_RESOURCE
    }


def test_github_workflow_uses_manual_oidc_deployment() -> None:
    """Ensure GitHub deployment is deliberate and handles credentials and inputs safely."""
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "push:" not in workflow
    assert "id-token: write" in workflow
    assert "uses:" not in workflow
    assert "ACTIONS_ID_TOKEN_REQUEST_URL" in workflow
    assert "assume-role-with-web-identity" in workflow
    assert "x-access-token:%s" in workflow
    assert "AUTHORIZATION: basic $checkout_auth_header" in workflow
    assert "Validate AWS workflow configuration" in workflow
    assert "AWS_ROLE_TO_ASSUME repository secret is required" in workflow
    assert "secrets.AWS_ROLE_TO_ASSUME" in workflow
    assert "secrets.AWS_ACCESS_KEY_ID" not in workflow
    assert '"NamePrefix=${{ inputs.name_prefix }}"' not in workflow
    assert "INPUT_NAME_PREFIX: ${{ inputs.name_prefix }}" in workflow
    assert "bash cloud/aws/deploy.sh" in workflow
    assert "bash cloud/aws/destroy.sh" in workflow
    assert "connection_details.md" in workflow
    assert 'cat "$connection_guide"' in workflow


def test_command_line_scripts_and_parameters_are_consistent() -> None:
    """Ensure every CLI entry point is licensed and uses the shared AWS parameter names."""
    source_paths = [
        AWS_DIRECTORY / "deploy.sh",
        AWS_DIRECTORY / "deploy.ps1",
        AWS_DIRECTORY / "destroy.sh",
        AWS_DIRECTORY / "destroy.ps1",
        AWS_DIRECTORY / "destroy-bucket.sh",
        AWS_DIRECTORY / "destroy-bucket.ps1",
        AWS_DIRECTORY / "scripts" / "configure_github_oidc_role.py",
        AWS_DIRECTORY / "scripts" / "package-cloud-artifacts.sh",
        AWS_DIRECTORY / "scripts" / "package-cloud-artifacts.ps1",
        AWS_DIRECTORY / "parameters.example.env",
        AWS_DIRECTORY / "readme.md",
        TEMPLATE_PATH,
        WORKFLOW_PATH,
    ]

    for source_path in source_paths:
        source_text = source_path.read_text(encoding="utf-8")
        assert "Copyright 2026 mp3monster.org" in source_text
        assert "Licensed under the Apache License, Version 2.0" in source_text

    parameter_text = (AWS_DIRECTORY / "parameters.example.env").read_text(encoding="utf-8")
    assert "KeyName=REPLACE_WITH_EXISTING_EC2_KEY_PAIR_NAME" in parameter_text
    assert "AdminSourceCidr=REPLACE_WITH_YOUR_PUBLIC_IP/32" in parameter_text


def test_shared_vm_scripts_support_both_cloud_artifact_flows() -> None:
    """Ensure shared Azure-compatible bootstrap scripts accept local AWS archives and labels."""
    install_script = (
        REPOSITORY_ROOT / "cloud" / "azure" / "scripts" / "install-opamp.sh"
    ).read_text(encoding="utf-8")
    consumer_script = (
        REPOSITORY_ROOT / "cloud" / "azure" / "scripts" / "start-opamp-consumer.sh"
    ).read_text(encoding="utf-8")
    server_script = (
        REPOSITORY_ROOT / "cloud" / "azure" / "scripts" / "start-opamp-server.sh"
    ).read_text(encoding="utf-8")

    assert "OPAMP_WHEEL_SOURCE_DIR" in install_script
    assert "docker.io" in install_script
    assert "docker-compose-plugin" not in install_script
    assert install_script.count('wheel_name="${wheel_name%$\'\\r\'}"') == 2
    assert "https://github.com/opamp-observe/opamp-core.git" in install_script
    assert "OPAMP_DEPLOYMENT_PLATFORM" in consumer_script
    assert '"log_level": "debug"' in consumer_script
    assert '"log_level": "DEBUG"' in server_script
    assert "OPAMP_SERVER_PRIVATE_IP" in server_script
    assert '--hostname="https://$OPAMP_PUBLIC_HOST:8443"' in server_script
    assert "--hostname-url" not in server_script
    assert "wait_for_keycloak" in server_script
    assert 'docker logs --tail 80 "$KEYCLOAK_CONTAINER_NAME"' in server_script


def test_wait_conditions_include_installer_failure_details() -> None:
    """Expose the installer tail in CloudFormation instead of only its wrapper line."""
    server_user_data = _user_data(_load_template(), SERVER_INSTANCE_RESOURCE)
    consumer_user_data = _user_data(_load_template(), CONSUMER_INSTANCE_RESOURCE)

    assert 'Server installer failed: $installer_error' in server_user_data
    assert 'Consumer installer failed: $installer_error' in consumer_user_data
    assert "tail -n 3" in server_user_data
    assert "tail -n 3" in consumer_user_data
    assert "/var/log/opamp-server-start.log" in server_user_data
    assert "Server startup failed: $server_start_error" in server_user_data


def test_aws_readme_explains_installer_bootstrap_recovery() -> None:
    """Document rebuilding a Windows-created archive after installer failure."""
    readme = (AWS_DIRECTORY / "readme.md").read_text(encoding="utf-8")

    assert "bootstrap failed at line 28" in readme
    assert "deploy again without" in readme
    assert "`-SkipPackage`" in readme
    assert "/var/log/opamp-install.log" in readme


def test_aws_readme_documents_github_oidc_role_creation() -> None:
    """Document creating the AWS role used by GitHub's OIDC token exchange."""
    readme = (AWS_DIRECTORY / "readme.md").read_text(encoding="utf-8")

    assert "### Create the GitHub OIDC resources" in readme
    assert "configure_github_oidc_role.py --attach-administrator-access" in readme
    assert "--configure-github" in readme
    assert "PyNaCl" in readme
    assert "--github-token-source git" in readme
    assert "Windows PowerShell" in readme
    assert "py -3 cloud\\aws\\scripts\\configure_github_oidc_role.py `" in readme
    assert "Windows `cmd.exe`" in readme
    assert "py -3 cloud\\aws\\scripts\\configure_github_oidc_role.py ^" in readme
    assert "gh auth token" in readme
    assert "Actions secrets API" in readme
    assert "Actions variables API" in readme
    assert "aws iam create-open-id-connect-provider" in readme
    assert "token.actions.githubusercontent.com" in readme
    assert "aws iam create-role" in readme
    assert "sts:AssumeRoleWithWebIdentity" in readme
    assert "repo:opamp-observe/opamp-core:ref:refs/heads/main" in readme
    assert "repo:opamp-observe@331386630/opamp-core@1181137273:ref:refs/heads/main" in readme
    assert "AWS_ROLE_TO_ASSUME" in readme
    assert "--cloud-provider azure" in readme
    assert "--assign-azure-role" in readme
    assert "api://AzureADTokenExchange" in readme
    assert "AZURE_APP_NAME" in readme
    assert "AZURE_RESOURCE_GROUP" in readme
