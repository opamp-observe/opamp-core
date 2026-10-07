#!/usr/bin/env python3
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

"""Create or update cloud OIDC resources used by GitHub Actions deployment."""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

LOGGER = logging.getLogger(__name__)

ADMINISTRATOR_ACCESS_POLICY_ARN = "arn:aws:iam::aws:policy/AdministratorAccess"
AWS_COMMAND = "aws"
AWS_OUTPUT_TEXT = "text"
AWS_PROVIDER = "aws"
AZURE_AUDIENCE = "api://AzureADTokenExchange"
AZURE_CLIENT_ID_SECRET = "AZUREAPPSERVICE_CLIENTID_195EE0A2DA3947CAA0427043CC5FEEFF"
AZURE_COMMAND = "az"
AZURE_DEFAULT_APP_NAME = "opamp-github-deploy"
AZURE_DEFAULT_FEDERATED_CREDENTIAL_NAME = "opamp-core-main"
AZURE_DEFAULT_ROLE = "Contributor"
AZURE_ISSUER = "https://token.actions.githubusercontent.com"
AZURE_PROVIDER = "azure"
AZURE_RESOURCE_GROUP_VARIABLE = "AZURE_RESOURCE_GROUP"
AZURE_SUBSCRIPTION_ID_SECRET = "AZUREAPPSERVICE_SUBSCRIPTIONID_F23BE392CBB5496182D244751F520677"
AZURE_TENANT_ID_SECRET = "AZUREAPPSERVICE_TENANTID_40CBF888FD894E9EA2D20C44941831DC"
AZURE_WEBAPP_NAME_VARIABLE = "AZURE_APP_NAME"
DEFAULT_AUDIENCE = "sts.amazonaws.com"
DEFAULT_BRANCH = "main"
DEFAULT_GITHUB_ORGANIZATION = "opamp-observe"
DEFAULT_GITHUB_ORGANIZATION_ID = "331386630"
DEFAULT_GITHUB_REPOSITORY = "opamp-core"
DEFAULT_GITHUB_REPOSITORY_ID = "1181137273"
DEFAULT_GITHUB_API_URL = "https://api.github.com"
DEFAULT_GITHUB_HOST = "github.com"
DEFAULT_GITHUB_TOKEN_ENVIRONMENT_VARIABLE = "GITHUB_TOKEN"
DEFAULT_LOG_LEVEL = "DEBUG"
DEFAULT_ROLE_NAME = "opamp-github-deploy"
GITHUB_OIDC_HOST = "token.actions.githubusercontent.com"
GITHUB_OIDC_URL = f"https://{GITHUB_OIDC_HOST}"
NONE_PROVIDER = "none"
PROVIDER_CHOICES = ("", AWS_PROVIDER, AZURE_PROVIDER, NONE_PROVIDER)

ACTION_KEY = "Action"
AUDIENCE_CONDITION_KEY = f"{GITHUB_OIDC_HOST}:aud"
CONDITION_KEY = "Condition"
EFFECT_KEY = "Effect"
FEDERATED_KEY = "Federated"
PRINCIPAL_KEY = "Principal"
STATEMENT_KEY = "Statement"
STRING_EQUALS_KEY = "StringEquals"
SUBJECT_CONDITION_KEY = f"{GITHUB_OIDC_HOST}:sub"
VERSION_KEY = "Version"

ALLOW_EFFECT = "Allow"
ASSUME_ROLE_WITH_WEB_IDENTITY_ACTION = "sts:AssumeRoleWithWebIdentity"
AWS_ADMIN_SOURCE_CIDR_VARIABLE = "AWS_ADMIN_SOURCE_CIDR"
AWS_KEY_NAME_VARIABLE = "AWS_KEY_NAME"
AWS_ROLE_TO_ASSUME_SECRET = "AWS_ROLE_TO_ASSUME"
CLOUD_PROVIDER_VARIABLE = "CLOUD_PROVIDER"
GITHUB_ACCEPT_HEADER = "application/vnd.github+json"
GITHUB_API_VERSION = "2026-03-10"
GITHUB_AUTHORIZATION_HEADER_PREFIX = "Bearer "
GITHUB_JSON_CONTENT_TYPE = "application/json"
GITHUB_TOKEN_SOURCE_AUTO = "auto"
GITHUB_TOKEN_SOURCE_ENV = "env"
GITHUB_TOKEN_SOURCE_GH = "gh"
GITHUB_TOKEN_SOURCE_GIT = "git"
GITHUB_TOKEN_SOURCES = (
    GITHUB_TOKEN_SOURCE_AUTO,
    GITHUB_TOKEN_SOURCE_ENV,
    GITHUB_TOKEN_SOURCE_GH,
    GITHUB_TOKEN_SOURCE_GIT,
)
HTTP_CREATED = 201
HTTP_NO_CONTENT = 204
HTTP_NOT_FOUND = 404
HTTP_OK = 200
POLICY_VERSION = "2012-10-17"

KEY_ID_KEY = "key_id"
PUBLIC_KEY_KEY = "key"

AZURE_AUDIENCES_KEY = "audiences"
AZURE_DESCRIPTION_KEY = "description"
AZURE_ISSUER_KEY = "issuer"
AZURE_NAME_KEY = "name"
AZURE_SUBJECT_KEY = "subject"
AZURE_FAKE_APP_ID = "00000000-0000-0000-0000-000000000001"
AZURE_FAKE_OBJECT_ID = "00000000-0000-0000-0000-000000000002"
AZURE_FAKE_SUBSCRIPTION_ID = "00000000-0000-0000-0000-000000000003"
AZURE_FAKE_TENANT_ID = "00000000-0000-0000-0000-000000000004"


@dataclass(frozen=True)
class AwsOidcRoleConfig:
    """Configuration values that define the GitHub-trusted AWS IAM role.

    Attributes:
        audience: The OIDC audience that AWS STS accepts from GitHub tokens.
        branch: The GitHub branch allowed to assume the role.
        github_organization: The GitHub organization name allowed in default subjects.
        github_organization_id: The immutable GitHub organization id allowed in new subjects.
        github_repository: The GitHub repository name allowed in default subjects.
        github_repository_id: The immutable GitHub repository id allowed in new subjects.
        role_name: The IAM role name to create or update.
    """

    audience: str
    branch: str
    github_organization: str
    github_organization_id: str
    github_repository: str
    github_repository_id: str
    role_name: str


@dataclass(frozen=True)
class GitHubActionsConfig:
    """Configuration values for writing GitHub Actions secrets and variables.

    Attributes:
        api_url: Base URL for the GitHub REST API.
        owner: Repository owner or organization name.
        repository: Repository name without owner or `.git` suffix.
        token: GitHub token with Actions secrets and variables write access.
    """

    api_url: str
    owner: str
    repository: str
    token: str


@dataclass(frozen=True)
class AzureOidcConfig:
    """Configuration values that define the Azure trusted GitHub application.

    Attributes:
        app_name: The Microsoft Entra application display name.
        branch: The GitHub branch allowed to authenticate through federation.
        federated_credential_name: Base name for generated federated credentials.
        github_organization: The GitHub organization name allowed in default subjects.
        github_organization_id: The immutable GitHub organization id allowed in new subjects.
        github_repository: The GitHub repository name allowed in default subjects.
        github_repository_id: The immutable GitHub repository id allowed in new subjects.
    """

    app_name: str
    branch: str
    federated_credential_name: str
    github_organization: str
    github_organization_id: str
    github_repository: str
    github_repository_id: str


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for cloud OIDC resource creation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role-name", default=DEFAULT_ROLE_NAME)
    parser.add_argument("--github-organization", default=DEFAULT_GITHUB_ORGANIZATION)
    parser.add_argument("--github-repository", default=DEFAULT_GITHUB_REPOSITORY)
    parser.add_argument("--github-organization-id", default=DEFAULT_GITHUB_ORGANIZATION_ID)
    parser.add_argument("--github-repository-id", default=DEFAULT_GITHUB_REPOSITORY_ID)
    parser.add_argument("--github-api-url", default=DEFAULT_GITHUB_API_URL)
    parser.add_argument("--github-host", default=DEFAULT_GITHUB_HOST)
    parser.add_argument(
        "--github-token",
        default="",
        help="GitHub token; highest-precedence token source when supplied",
    )
    parser.add_argument(
        "--github-token-env",
        default=DEFAULT_GITHUB_TOKEN_ENVIRONMENT_VARIABLE,
        help="environment variable to read when --github-token is not supplied",
    )
    parser.add_argument(
        "--github-token-source",
        choices=GITHUB_TOKEN_SOURCES,
        default=GITHUB_TOKEN_SOURCE_AUTO,
        help=(
            "token discovery source: auto uses --github-token, env, then gh; "
            "git explicitly reads the local Git credential helper"
        ),
    )
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--audience", default=DEFAULT_AUDIENCE)
    parser.add_argument(
        "--configure-github",
        action="store_true",
        help="write provider secrets and selected variables through GitHub's REST APIs",
    )
    parser.add_argument(
        "--aws-key-name",
        default="",
        help="optional value to upsert as the AWS_KEY_NAME GitHub Actions variable",
    )
    parser.add_argument(
        "--aws-admin-source-cidr",
        default="",
        help="optional value to upsert as the AWS_ADMIN_SOURCE_CIDR GitHub Actions variable",
    )
    parser.add_argument(
        "--cloud-provider",
        default="",
        choices=PROVIDER_CHOICES,
        help="cloud provider to configure and optional CLOUD_PROVIDER GitHub variable value",
    )
    parser.add_argument("--azure-app-name", default=AZURE_DEFAULT_APP_NAME)
    parser.add_argument(
        "--azure-federated-credential-name",
        default=AZURE_DEFAULT_FEDERATED_CREDENTIAL_NAME,
    )
    parser.add_argument("--azure-subscription-id", default="")
    parser.add_argument("--azure-tenant-id", default="")
    parser.add_argument("--azure-role", default=AZURE_DEFAULT_ROLE)
    parser.add_argument("--azure-role-scope", default="")
    parser.add_argument("--azure-webapp-name", default="")
    parser.add_argument("--azure-resource-group", default="")
    parser.add_argument(
        "--assign-azure-role",
        action="store_true",
        help="assign the Azure role to the generated service principal",
    )
    parser.add_argument(
        "--attach-administrator-access",
        action="store_true",
        help="attach AWS managed AdministratorAccess for disposable regression accounts",
    )
    parser.add_argument(
        "--managed-policy-arn",
        action="append",
        default=[],
        help="attach one managed IAM policy ARN; may be repeated",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--log-level", default=DEFAULT_LOG_LEVEL)
    return parser


def _run_command(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run one AWS CLI command, logging the command and returning its completed process."""
    LOGGER.debug("Running command: %s", subprocess.list2cmdline(command))
    completed_process = subprocess.run(
        command,
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        text=True,
    )
    if check and completed_process.returncode != 0:
        raise RuntimeError(
            "Command failed with exit code "
            f"{completed_process.returncode}: {subprocess.list2cmdline(command)}\n"
            f"{completed_process.stderr.strip()}"
        )
    return completed_process


def _run_command_with_input(
    command: list[str],
    command_input: str,
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run one command with stdin content and return its completed process."""
    LOGGER.debug("Running command: %s", subprocess.list2cmdline(command))
    completed_process = subprocess.run(
        command,
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        input=command_input,
        text=True,
    )
    if check and completed_process.returncode != 0:
        raise RuntimeError(
            "Command failed with exit code "
            f"{completed_process.returncode}: {subprocess.list2cmdline(command)}\n"
            f"{completed_process.stderr.strip()}"
        )
    return completed_process


def _github_request(
    github_config: GitHubActionsConfig,
    method: str,
    path: str,
    payload: dict[str, object] | None = None,
    *,
    expected_statuses: tuple[int, ...] = (HTTP_OK,),
) -> tuple[int, dict[str, object]]:
    """Call one GitHub REST API endpoint and return its status and JSON payload."""
    request_url = f"{github_config.api_url.rstrip('/')}{path}"
    request_body = None
    if payload is not None:
        request_body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        request_url,
        data=request_body,
        method=method,
        headers={
            "Accept": GITHUB_ACCEPT_HEADER,
            "Authorization": f"{GITHUB_AUTHORIZATION_HEADER_PREFIX}{github_config.token}",
            "Content-Type": GITHUB_JSON_CONTENT_TYPE,
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            response_status = int(response.status)
            response_text = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        response_status = int(error.code)
        response_text = error.read().decode("utf-8")
        if response_status not in expected_statuses:
            raise RuntimeError(
                f"GitHub API request failed with HTTP {response_status}: {method} {path}\n"
                f"{response_text}"
            ) from error
    if response_status not in expected_statuses:
        raise RuntimeError(
            f"GitHub API request returned HTTP {response_status}: {method} {path}\n"
            f"{response_text}"
        )
    if not response_text.strip():
        return response_status, {}
    return response_status, json.loads(response_text)


def _run_or_print(command: list[str], *, dry_run: bool, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a CLI command unless dry-run mode should only print the operation."""
    if dry_run:
        LOGGER.info("DRY RUN: %s", subprocess.list2cmdline(command))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
    return _run_command(command, check=check)


def _encrypt_github_secret(public_key_base64: str, secret_value: str) -> str:
    """Encrypt a GitHub Actions secret with the repository public key."""
    from nacl import encoding, public

    public_key = public.PublicKey(public_key_base64.encode("utf-8"), encoding.Base64Encoder)
    sealed_box = public.SealedBox(public_key)
    encrypted_secret = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted_secret).decode("utf-8")


def _ensure_pynacl_available() -> None:
    """Verify PyNaCl is installed before GitHub secret encryption is needed."""
    try:
        from nacl import encoding as _encoding  # noqa: F401
        from nacl import public as _public  # noqa: F401
    except ImportError as import_error:
        LOGGER.error("PyNaCl is required when --configure-github is used.")
        LOGGER.error("Install it from the repository root with:")
        LOGGER.error("  py -3 -m pip install -r requirements.txt")
        LOGGER.error("Or install only the dependency with:")
        LOGGER.error("  py -3 -m pip install PyNaCl")
        raise RuntimeError("PyNaCl is not installed.") from import_error


def _github_host_from_api_url(api_url: str) -> str:
    """Infer a GitHub host from the REST API URL for local token discovery."""
    parsed_url = urllib.parse.urlparse(api_url)
    host_name = parsed_url.hostname or DEFAULT_GITHUB_HOST
    if host_name == "api.github.com":
        return DEFAULT_GITHUB_HOST
    return host_name


def _github_token_from_gh(host_name: str) -> str:
    """Return a token from the local GitHub CLI login when available."""
    command = ["gh", "auth", "token"]
    if host_name != DEFAULT_GITHUB_HOST:
        command.extend(["--hostname", host_name])
    completed_process = _run_command(command, check=False)
    if completed_process.returncode != 0:
        return ""
    return completed_process.stdout.strip()


def _parse_git_credential_output(credential_output: str) -> dict[str, str]:
    """Parse key-value lines returned by `git credential fill`."""
    credential_values: dict[str, str] = {}
    for output_line in credential_output.splitlines():
        if "=" not in output_line:
            continue
        credential_key, credential_value = output_line.split("=", maxsplit=1)
        credential_values[credential_key] = credential_value
    return credential_values


def _github_token_from_git_credential(host_name: str) -> str:
    """Return a GitHub token or password from the local Git credential helper."""
    credential_input = f"protocol=https\nhost={host_name}\n\n"
    completed_process = _run_command_with_input(
        ["git", "credential", "fill"],
        credential_input,
        check=False,
    )
    if completed_process.returncode != 0:
        return ""
    credential_values = _parse_git_credential_output(completed_process.stdout)
    return credential_values.get("password", "").strip()


def _resolve_github_token(arguments: argparse.Namespace, *, dry_run: bool) -> str:
    """Resolve a GitHub token from explicit, environment, gh, or Git credential sources."""
    if arguments.github_token:
        return arguments.github_token
    if dry_run:
        return "dry-run-token"

    environment_token = os.environ.get(arguments.github_token_env, "")
    if arguments.github_token_source in (GITHUB_TOKEN_SOURCE_AUTO, GITHUB_TOKEN_SOURCE_ENV):
        if environment_token:
            LOGGER.info("Using GitHub token from %s", arguments.github_token_env)
            return environment_token
        if arguments.github_token_source == GITHUB_TOKEN_SOURCE_ENV:
            return ""

    github_host = arguments.github_host or _github_host_from_api_url(arguments.github_api_url)
    if arguments.github_token_source in (GITHUB_TOKEN_SOURCE_AUTO, GITHUB_TOKEN_SOURCE_GH):
        gh_token = _github_token_from_gh(github_host)
        if gh_token:
            LOGGER.info("Using GitHub token from local gh authentication")
            return gh_token
        if arguments.github_token_source == GITHUB_TOKEN_SOURCE_GH:
            return ""

    if arguments.github_token_source == GITHUB_TOKEN_SOURCE_GIT:
        git_token = _github_token_from_git_credential(github_host)
        if git_token:
            LOGGER.info("Using GitHub token from local Git credential helper")
            return git_token
    return ""


def _account_id(*, dry_run: bool) -> str:
    """Return the current AWS account id used to build provider and role ARNs."""
    if dry_run:
        return "123456789012"
    completed_process = _run_command(
        [
            AWS_COMMAND,
            "sts",
            "get-caller-identity",
            "--query",
            "Account",
            "--output",
            AWS_OUTPUT_TEXT,
        ]
    )
    return completed_process.stdout.strip()


def _azure_account_field(field_name: str, fake_value: str, *, dry_run: bool) -> str:
    """Return one Azure account field from the active Azure CLI subscription."""
    if dry_run:
        return fake_value
    completed_process = _run_command(
        [
            AZURE_COMMAND,
            "account",
            "show",
            "--query",
            field_name,
            "--output",
            AWS_OUTPUT_TEXT,
        ]
    )
    return completed_process.stdout.strip()


def _selected_azure_subscription_id(arguments: argparse.Namespace, *, dry_run: bool) -> str:
    """Return the Azure subscription id supplied by the user or active Azure CLI account."""
    return arguments.azure_subscription_id or _azure_account_field(
        "id",
        AZURE_FAKE_SUBSCRIPTION_ID,
        dry_run=dry_run,
    )


def _selected_azure_tenant_id(arguments: argparse.Namespace, *, dry_run: bool) -> str:
    """Return the Azure tenant id supplied by the user or active Azure CLI account."""
    return arguments.azure_tenant_id or _azure_account_field(
        "tenantId",
        AZURE_FAKE_TENANT_ID,
        dry_run=dry_run,
    )


def _provider_arn(account_id: str) -> str:
    """Build the GitHub OIDC provider ARN for the selected AWS account."""
    return f"arn:aws:iam::{account_id}:oidc-provider/{GITHUB_OIDC_HOST}"


def _role_arn(account_id: str, role_name: str) -> str:
    """Build the IAM role ARN that must be stored in GitHub as AWS_ROLE_TO_ASSUME."""
    return f"arn:aws:iam::{account_id}:role/{role_name}"


def _subject_values(config: AwsOidcRoleConfig) -> list[str]:
    """Return accepted GitHub OIDC subject values for branch-scoped deployment."""
    default_subject = (
        f"repo:{config.github_organization}/{config.github_repository}:"
        f"ref:refs/heads/{config.branch}"
    )
    immutable_subject = (
        f"repo:{config.github_organization}@{config.github_organization_id}/"
        f"{config.github_repository}@{config.github_repository_id}:"
        f"ref:refs/heads/{config.branch}"
    )
    return [default_subject, immutable_subject]


def _azure_subject_values(config: AzureOidcConfig) -> list[str]:
    """Return accepted GitHub OIDC subjects for Azure branch-scoped deployment."""
    default_subject = (
        f"repo:{config.github_organization}/{config.github_repository}:"
        f"ref:refs/heads/{config.branch}"
    )
    immutable_subject = (
        f"repo:{config.github_organization}@{config.github_organization_id}/"
        f"{config.github_repository}@{config.github_repository_id}:"
        f"ref:refs/heads/{config.branch}"
    )
    return [default_subject, immutable_subject]


def build_trust_policy(config: AwsOidcRoleConfig, provider_arn: str) -> dict[str, object]:
    """Build the IAM trust policy that allows GitHub Actions to assume the role."""
    return {
        VERSION_KEY: POLICY_VERSION,
        STATEMENT_KEY: [
            {
                EFFECT_KEY: ALLOW_EFFECT,
                PRINCIPAL_KEY: {FEDERATED_KEY: provider_arn},
                ACTION_KEY: ASSUME_ROLE_WITH_WEB_IDENTITY_ACTION,
                CONDITION_KEY: {
                    STRING_EQUALS_KEY: {
                        AUDIENCE_CONDITION_KEY: config.audience,
                        SUBJECT_CONDITION_KEY: _subject_values(config),
                    }
                },
            }
        ],
    }


def _ensure_oidc_provider(provider_arn: str, config: AwsOidcRoleConfig, *, dry_run: bool) -> None:
    """Create the GitHub OIDC provider when the AWS account does not already have it."""
    probe_command = [
        AWS_COMMAND,
        "iam",
        "get-open-id-connect-provider",
        "--open-id-connect-provider-arn",
        provider_arn,
    ]
    if dry_run:
        LOGGER.info("DRY RUN: %s", subprocess.list2cmdline(probe_command))
    else:
        completed_process = _run_command(probe_command, check=False)
        if completed_process.returncode == 0:
            LOGGER.info("GitHub OIDC provider already exists: %s", provider_arn)
            return

    _run_or_print(
        [
            AWS_COMMAND,
            "iam",
            "create-open-id-connect-provider",
            "--url",
            GITHUB_OIDC_URL,
            "--client-id-list",
            config.audience,
        ],
        dry_run=dry_run,
    )


def _role_exists(role_name: str, *, dry_run: bool) -> bool:
    """Return whether the named role exists so the script can create or update it."""
    if dry_run:
        LOGGER.info(
            "DRY RUN: %s",
            subprocess.list2cmdline([AWS_COMMAND, "iam", "get-role", "--role-name", role_name]),
        )
        return False
    completed_process = _run_command(
        [AWS_COMMAND, "iam", "get-role", "--role-name", role_name],
        check=False,
    )
    return completed_process.returncode == 0


def _write_json_policy(policy_payload: dict[str, object], policy_path: Path) -> None:
    """Write the trust policy JSON in a deterministic format for AWS CLI input."""
    policy_path.write_text(
        json.dumps(policy_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _create_or_update_role(
    role_name: str,
    trust_policy: dict[str, object],
    *,
    dry_run: bool,
) -> None:
    """Create the IAM role or update its assume-role policy when it already exists."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        policy_path = Path(temporary_directory) / "github-oidc-trust-policy.json"
        _write_json_policy(trust_policy, policy_path)
        policy_document_argument = f"file://{policy_path}"
        if _role_exists(role_name, dry_run=dry_run):
            _run_or_print(
                [
                    AWS_COMMAND,
                    "iam",
                    "update-assume-role-policy",
                    "--role-name",
                    role_name,
                    "--policy-document",
                    policy_document_argument,
                ],
                dry_run=dry_run,
            )
            return

        _run_or_print(
            [
                AWS_COMMAND,
                "iam",
                "create-role",
                "--role-name",
                role_name,
                "--assume-role-policy-document",
                policy_document_argument,
            ],
            dry_run=dry_run,
        )


def _attach_managed_policies(
    role_name: str,
    managed_policy_arns: list[str],
    *,
    dry_run: bool,
) -> None:
    """Attach selected managed IAM policies so the role can perform deployment work."""
    for managed_policy_arn in managed_policy_arns:
        _run_or_print(
            [
                AWS_COMMAND,
                "iam",
                "attach-role-policy",
                "--role-name",
                role_name,
                "--policy-arn",
                managed_policy_arn,
            ],
            dry_run=dry_run,
        )


def _azure_application_from_output(output_text: str) -> tuple[str, str] | None:
    """Parse Azure CLI TSV output into application object id and client id."""
    stripped_output = output_text.strip()
    if not stripped_output:
        return None
    output_parts = stripped_output.split()
    if len(output_parts) < 2:
        return None
    return output_parts[0], output_parts[1]


def _ensure_azure_application(
    config: AzureOidcConfig,
    *,
    dry_run: bool,
) -> tuple[str, str]:
    """Create or reuse the Microsoft Entra app registration and service principal."""
    if dry_run:
        LOGGER.info(
            "DRY RUN: %s",
            subprocess.list2cmdline(
                [
                    AZURE_COMMAND,
                    "ad",
                    "app",
                    "list",
                    "--display-name",
                    config.app_name,
                    "--query",
                    "[0].[id,appId]",
                    "--output",
                    "tsv",
                ]
            ),
        )
        LOGGER.info(
            "DRY RUN: %s",
            subprocess.list2cmdline(
                [
                    AZURE_COMMAND,
                    "ad",
                    "sp",
                    "create",
                    "--id",
                    AZURE_FAKE_APP_ID,
                ]
            ),
        )
        return AZURE_FAKE_OBJECT_ID, AZURE_FAKE_APP_ID

    completed_process = _run_command(
        [
            AZURE_COMMAND,
            "ad",
            "app",
            "list",
            "--display-name",
            config.app_name,
            "--query",
            "[0].[id,appId]",
            "--output",
            "tsv",
        ],
        check=False,
    )
    azure_application = _azure_application_from_output(completed_process.stdout)
    if azure_application is None:
        completed_process = _run_command(
            [
                AZURE_COMMAND,
                "ad",
                "app",
                "create",
                "--display-name",
                config.app_name,
                "--query",
                "[id,appId]",
                "--output",
                "tsv",
            ]
        )
        azure_application = _azure_application_from_output(completed_process.stdout)
    if azure_application is None:
        raise RuntimeError(f"Unable to resolve Azure application ids for {config.app_name}.")

    app_object_id, app_client_id = azure_application
    completed_process = _run_command(
        [AZURE_COMMAND, "ad", "sp", "show", "--id", app_client_id],
        check=False,
    )
    if completed_process.returncode != 0:
        _run_command([AZURE_COMMAND, "ad", "sp", "create", "--id", app_client_id])
    return app_object_id, app_client_id


def _azure_federated_credential_payload(
    credential_name: str,
    subject: str,
) -> dict[str, object]:
    """Build the Azure federated credential payload for a GitHub subject."""
    return {
        AZURE_NAME_KEY: credential_name,
        AZURE_ISSUER_KEY: AZURE_ISSUER,
        AZURE_SUBJECT_KEY: subject,
        AZURE_AUDIENCES_KEY: [AZURE_AUDIENCE],
        AZURE_DESCRIPTION_KEY: "GitHub Actions OIDC deployment credential for OpAMP.",
    }


def _write_azure_federated_credential_payload(
    payload: dict[str, object],
    credential_path: Path,
) -> None:
    """Write one Azure federated credential payload as deterministic JSON."""
    credential_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _ensure_azure_federated_credentials(
    app_object_id: str,
    config: AzureOidcConfig,
    *,
    dry_run: bool,
) -> None:
    """Create GitHub branch federated credentials on the Microsoft Entra app."""
    credential_subjects = _azure_subject_values(config)
    credential_names = [
        config.federated_credential_name,
        f"{config.federated_credential_name}-immutable",
    ]
    with tempfile.TemporaryDirectory() as temporary_directory:
        for credential_name, credential_subject in zip(credential_names, credential_subjects, strict=True):
            credential_path = Path(temporary_directory) / f"{credential_name}.json"
            _write_azure_federated_credential_payload(
                _azure_federated_credential_payload(credential_name, credential_subject),
                credential_path,
            )
            if dry_run:
                LOGGER.info(
                    "DRY RUN: %s",
                    subprocess.list2cmdline(
                        [
                            AZURE_COMMAND,
                            "ad",
                            "app",
                            "federated-credential",
                            "create",
                            "--id",
                            app_object_id,
                            "--parameters",
                            str(credential_path),
                        ]
                    ),
                )
                continue

            existing_credential = _run_command(
                [
                    AZURE_COMMAND,
                    "ad",
                    "app",
                    "federated-credential",
                    "list",
                    "--id",
                    app_object_id,
                    "--query",
                    f"[?name=='{credential_name}'].id | [0]",
                    "--output",
                    "tsv",
                ],
                check=False,
            ).stdout.strip()
            if existing_credential:
                _run_command(
                    [
                        AZURE_COMMAND,
                        "ad",
                        "app",
                        "federated-credential",
                        "delete",
                        "--id",
                        app_object_id,
                        "--federated-credential-id",
                        existing_credential,
                    ]
                )
            _run_command(
                [
                    AZURE_COMMAND,
                    "ad",
                    "app",
                    "federated-credential",
                    "create",
                    "--id",
                    app_object_id,
                    "--parameters",
                    str(credential_path),
                ]
            )


def _ensure_azure_role_assignment(
    app_client_id: str,
    role_name: str,
    role_scope: str,
    *,
    dry_run: bool,
) -> None:
    """Assign the selected Azure role to the generated service principal."""
    if dry_run:
        LOGGER.info(
            "DRY RUN: %s",
            subprocess.list2cmdline(
                [
                    AZURE_COMMAND,
                    "role",
                    "assignment",
                    "create",
                    "--assignee",
                    app_client_id,
                    "--role",
                    role_name,
                    "--scope",
                    role_scope,
                ]
            ),
        )
        return
    existing_assignment = _run_command(
        [
            AZURE_COMMAND,
            "role",
            "assignment",
            "list",
            "--assignee",
            app_client_id,
            "--role",
            role_name,
            "--scope",
            role_scope,
            "--query",
            "[0].id",
            "--output",
            "tsv",
        ],
        check=False,
    ).stdout.strip()
    if existing_assignment:
        LOGGER.info("Azure role assignment already exists: %s", existing_assignment)
        return
    _run_command(
        [
            AZURE_COMMAND,
            "role",
            "assignment",
            "create",
            "--assignee",
            app_client_id,
            "--role",
            role_name,
            "--scope",
            role_scope,
        ]
    )


def _github_repository_path(github_config: GitHubActionsConfig) -> str:
    """Return the REST API path prefix for the configured GitHub repository."""
    return f"/repos/{github_config.owner}/{github_config.repository}"


def _put_github_secret(
    github_config: GitHubActionsConfig,
    secret_name: str,
    secret_value: str,
    *,
    dry_run: bool,
) -> None:
    """Create or update one GitHub Actions repository secret through the REST API."""
    if dry_run:
        LOGGER.info("DRY RUN: upsert GitHub Actions secret %s", secret_name)
        return
    public_key_path = f"{_github_repository_path(github_config)}/actions/secrets/public-key"
    _, public_key_payload = _github_request(github_config, "GET", public_key_path)
    encrypted_value = _encrypt_github_secret(
        str(public_key_payload[PUBLIC_KEY_KEY]),
        secret_value,
    )
    secret_path = f"{_github_repository_path(github_config)}/actions/secrets/{secret_name}"
    _github_request(
        github_config,
        "PUT",
        secret_path,
        {
            "encrypted_value": encrypted_value,
            KEY_ID_KEY: public_key_payload[KEY_ID_KEY],
        },
        expected_statuses=(HTTP_CREATED, HTTP_NO_CONTENT),
    )
    LOGGER.info("Configured GitHub Actions secret: %s", secret_name)


def _upsert_github_variable(
    github_config: GitHubActionsConfig,
    variable_name: str,
    variable_value: str,
    *,
    dry_run: bool,
) -> None:
    """Create or update one GitHub Actions repository variable through the REST API."""
    if dry_run:
        LOGGER.info("DRY RUN: upsert GitHub Actions variable %s=%s", variable_name, variable_value)
        return
    variable_path = f"{_github_repository_path(github_config)}/actions/variables/{variable_name}"
    response_status, _ = _github_request(
        github_config,
        "GET",
        variable_path,
        expected_statuses=(HTTP_OK, HTTP_NOT_FOUND),
    )
    if response_status == HTTP_NOT_FOUND:
        _github_request(
            github_config,
            "POST",
            f"{_github_repository_path(github_config)}/actions/variables",
            {"name": variable_name, "value": variable_value},
            expected_statuses=(HTTP_CREATED,),
        )
    else:
        _github_request(
            github_config,
            "PATCH",
            variable_path,
            {"name": variable_name, "value": variable_value},
            expected_statuses=(HTTP_NO_CONTENT,),
        )
    LOGGER.info("Configured GitHub Actions variable: %s", variable_name)


def _configure_github_actions(
    github_config: GitHubActionsConfig,
    secrets: dict[str, str],
    variables: dict[str, str],
    *,
    dry_run: bool,
) -> None:
    """Configure GitHub Actions with selected provider secrets and variables."""
    for secret_name, secret_value in secrets.items():
        if secret_value:
            _put_github_secret(
                github_config,
                secret_name,
                secret_value,
                dry_run=dry_run,
            )
    for variable_name, variable_value in variables.items():
        if variable_value:
            _upsert_github_variable(
                github_config,
                variable_name,
                variable_value,
                dry_run=dry_run,
            )


def _config_from_arguments(arguments: argparse.Namespace) -> AwsOidcRoleConfig:
    """Convert parsed command-line values into the role configuration object."""
    return AwsOidcRoleConfig(
        audience=arguments.audience,
        branch=arguments.branch,
        github_organization=arguments.github_organization,
        github_organization_id=arguments.github_organization_id,
        github_repository=arguments.github_repository,
        github_repository_id=arguments.github_repository_id,
        role_name=arguments.role_name,
    )


def _azure_config_from_arguments(arguments: argparse.Namespace) -> AzureOidcConfig:
    """Convert parsed command-line values into the Azure OIDC configuration object."""
    return AzureOidcConfig(
        app_name=arguments.azure_app_name,
        branch=arguments.branch,
        federated_credential_name=arguments.azure_federated_credential_name,
        github_organization=arguments.github_organization,
        github_organization_id=arguments.github_organization_id,
        github_repository=arguments.github_repository,
        github_repository_id=arguments.github_repository_id,
    )


def _github_config_from_arguments(
    arguments: argparse.Namespace,
    *,
    dry_run: bool,
) -> GitHubActionsConfig:
    """Convert parsed command-line values into the GitHub REST API configuration."""
    github_token = _resolve_github_token(arguments, dry_run=dry_run)
    if not github_token:
        raise RuntimeError(
            "A GitHub token is required when --configure-github is used. "
            f"Pass --github-token, set {arguments.github_token_env}, authenticate "
            "with gh, or use --github-token-source git to read the local Git "
            "credential helper."
        )
    return GitHubActionsConfig(
        api_url=arguments.github_api_url,
        owner=arguments.github_organization,
        repository=arguments.github_repository,
        token=github_token,
    )


def _github_variables_from_arguments(arguments: argparse.Namespace) -> dict[str, str]:
    """Return the GitHub Actions variables requested on the command line."""
    return {
        AWS_ADMIN_SOURCE_CIDR_VARIABLE: arguments.aws_admin_source_cidr,
        AWS_KEY_NAME_VARIABLE: arguments.aws_key_name,
        AZURE_RESOURCE_GROUP_VARIABLE: arguments.azure_resource_group,
        AZURE_WEBAPP_NAME_VARIABLE: arguments.azure_webapp_name,
        CLOUD_PROVIDER_VARIABLE: arguments.cloud_provider,
    }


def _selected_provider(arguments: argparse.Namespace) -> str:
    """Return the provider to configure, preserving AWS as the legacy default."""
    return arguments.cloud_provider or AWS_PROVIDER


def _configure_aws_resources(
    arguments: argparse.Namespace,
    *,
    dry_run: bool,
) -> tuple[dict[str, str], dict[str, str]]:
    """Configure AWS OIDC resources and return GitHub secrets and variables."""
    config = _config_from_arguments(arguments)
    managed_policy_arns = list(arguments.managed_policy_arn)
    if arguments.attach_administrator_access:
        managed_policy_arns.append(ADMINISTRATOR_ACCESS_POLICY_ARN)

    selected_account_id = _account_id(dry_run=dry_run)
    selected_provider_arn = _provider_arn(selected_account_id)
    selected_role_arn = _role_arn(selected_account_id, config.role_name)
    trust_policy = build_trust_policy(config, selected_provider_arn)

    _ensure_oidc_provider(selected_provider_arn, config, dry_run=dry_run)
    _create_or_update_role(config.role_name, trust_policy, dry_run=dry_run)
    _attach_managed_policies(config.role_name, managed_policy_arns, dry_run=dry_run)

    print()
    print("GitHub repository secret:")
    print(f"{AWS_ROLE_TO_ASSUME_SECRET}={selected_role_arn}")
    if not managed_policy_arns:
        print()
        print(
            "No IAM permissions were attached. Attach a managed policy or custom "
            "least-privilege policy before running the deployment workflow."
        )
    return {AWS_ROLE_TO_ASSUME_SECRET: selected_role_arn}, _github_variables_from_arguments(arguments)


def _configure_azure_resources(
    arguments: argparse.Namespace,
    *,
    dry_run: bool,
) -> tuple[dict[str, str], dict[str, str]]:
    """Configure Azure OIDC resources and return GitHub secrets and variables."""
    config = _azure_config_from_arguments(arguments)
    subscription_id = _selected_azure_subscription_id(arguments, dry_run=dry_run)
    tenant_id = _selected_azure_tenant_id(arguments, dry_run=dry_run)
    role_scope = arguments.azure_role_scope or f"/subscriptions/{subscription_id}"

    app_object_id, app_client_id = _ensure_azure_application(config, dry_run=dry_run)
    _ensure_azure_federated_credentials(app_object_id, config, dry_run=dry_run)
    if arguments.assign_azure_role:
        _ensure_azure_role_assignment(
            app_client_id,
            arguments.azure_role,
            role_scope,
            dry_run=dry_run,
        )

    print()
    print("GitHub repository secrets:")
    print(f"{AZURE_CLIENT_ID_SECRET}={app_client_id}")
    print(f"{AZURE_TENANT_ID_SECRET}={tenant_id}")
    print(f"{AZURE_SUBSCRIPTION_ID_SECRET}={subscription_id}")
    if not arguments.assign_azure_role:
        print()
        print(
            "No Azure role was assigned. Pass --assign-azure-role or assign a "
            "least-privilege role before running the Azure deployment workflow."
        )
    return (
        {
            AZURE_CLIENT_ID_SECRET: app_client_id,
            AZURE_TENANT_ID_SECRET: tenant_id,
            AZURE_SUBSCRIPTION_ID_SECRET: subscription_id,
        },
        _github_variables_from_arguments(arguments),
    )


def main(argv: list[str] | None = None) -> int:
    """Create or update cloud OIDC resources and optionally configure GitHub."""
    arguments = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, arguments.log_level.upper(), logging.DEBUG),
        format="%(levelname)s %(message)s",
    )
    if arguments.configure_github and not arguments.dry_run:
        _ensure_pynacl_available()

    selected_cloud_provider = _selected_provider(arguments)
    if selected_cloud_provider == AWS_PROVIDER:
        secrets, variables = _configure_aws_resources(arguments, dry_run=arguments.dry_run)
    elif selected_cloud_provider == AZURE_PROVIDER:
        secrets, variables = _configure_azure_resources(arguments, dry_run=arguments.dry_run)
    else:
        secrets = {}
        variables = _github_variables_from_arguments(arguments)

    if arguments.configure_github:
        _configure_github_actions(
            _github_config_from_arguments(arguments, dry_run=arguments.dry_run),
            secrets,
            variables,
            dry_run=arguments.dry_run,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
