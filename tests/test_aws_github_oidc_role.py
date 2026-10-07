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

"""Unit tests for the cloud GitHub OIDC helper."""

from __future__ import annotations

import builtins
import importlib.util
import logging
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "cloud" / "aws" / "scripts" / "configure_github_oidc_role.py"

CONDITION_KEY = "Condition"
FEDERATED_KEY = "Federated"
PRINCIPAL_KEY = "Principal"
STATEMENT_KEY = "Statement"
STRING_EQUALS_KEY = "StringEquals"
SUBJECT_CONDITION_KEY = "token.actions.githubusercontent.com:sub"

GITHUB_API_URL = "https://api.github.example.test"
GITHUB_OWNER = "opamp-observe"
GITHUB_REPOSITORY = "opamp-core"
GITHUB_TOKEN = "github-token"


@pytest.fixture(name="oidc_role_module")
def fixture_oidc_role_module() -> ModuleType:
    """Load the standalone helper script as an importable module for focused tests."""
    module_spec = importlib.util.spec_from_file_location("aws_oidc_role", SCRIPT_PATH)
    assert module_spec is not None
    assert module_spec.loader is not None
    oidc_role_module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = oidc_role_module
    module_spec.loader.exec_module(oidc_role_module)
    return oidc_role_module


def test_trust_policy_scopes_github_subjects_to_main_branch(
    oidc_role_module: ModuleType,
) -> None:
    """Ensure the generated trust policy limits GitHub OIDC access to this repository."""
    config = oidc_role_module.AwsOidcRoleConfig(
        audience="sts.amazonaws.com",
        branch="main",
        github_organization="opamp-observe",
        github_organization_id="331386630",
        github_repository="opamp-core",
        github_repository_id="1181137273",
        role_name="opamp-github-deploy",
    )

    trust_policy = oidc_role_module.build_trust_policy(
        config,
        "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com",
    )

    statement = trust_policy[STATEMENT_KEY][0]
    assert statement[PRINCIPAL_KEY][FEDERATED_KEY].endswith(
        "oidc-provider/token.actions.githubusercontent.com"
    )
    subject_values = statement[CONDITION_KEY][STRING_EQUALS_KEY][SUBJECT_CONDITION_KEY]
    assert subject_values == [
        "repo:opamp-observe/opamp-core:ref:refs/heads/main",
        "repo:opamp-observe@331386630/opamp-core@1181137273:ref:refs/heads/main",
    ]


def test_dry_run_prints_github_secret_value(
    oidc_role_module: ModuleType,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify dry-run mode avoids AWS calls while still reporting the GitHub secret value."""
    exit_code = oidc_role_module.main(
        ["--dry-run", "--attach-administrator-access", "--configure-github"]
    )

    captured_output = capsys.readouterr()
    assert exit_code == 0
    assert "AWS_ROLE_TO_ASSUME=arn:aws:iam::123456789012:role/opamp-github-deploy" in (
        captured_output.out
    )


def test_configure_github_actions_writes_secret_and_variables(
    oidc_role_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure GitHub API configuration encrypts the role secret and upserts variables."""
    github_config = oidc_role_module.GitHubActionsConfig(
        api_url=GITHUB_API_URL,
        owner=GITHUB_OWNER,
        repository=GITHUB_REPOSITORY,
        token=GITHUB_TOKEN,
    )
    captured_requests: list[tuple[str, str, dict[str, object] | None]] = []

    def fake_github_request(
        _github_config: object,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
        *,
        expected_statuses: tuple[int, ...] = (200,),
    ) -> tuple[int, dict[str, object]]:
        """Capture GitHub API requests and return representative endpoint payloads."""
        captured_requests.append((method, path, payload))
        if path.endswith("/actions/secrets/public-key"):
            return 200, {"key": "public-key", "key_id": "key-id"}
        if method == "GET":
            return 404, {}
        return expected_statuses[0], {}

    monkeypatch.setattr(oidc_role_module, "_github_request", fake_github_request)
    monkeypatch.setattr(
        oidc_role_module,
        "_encrypt_github_secret",
        lambda public_key, secret_value: f"encrypted:{public_key}:{secret_value}",
    )

    oidc_role_module._configure_github_actions(
        github_config,
        {
            "AWS_ROLE_TO_ASSUME": "arn:aws:iam::123456789012:role/opamp-github-deploy",
        },
        {
            "AWS_ADMIN_SOURCE_CIDR": "203.0.113.10/32",
            "AWS_KEY_NAME": "opamp-regression",
            "CLOUD_PROVIDER": "aws",
        },
        dry_run=False,
    )

    assert captured_requests[0][:2] == (
        "GET",
        "/repos/opamp-observe/opamp-core/actions/secrets/public-key",
    )
    assert captured_requests[1] == (
        "PUT",
        "/repos/opamp-observe/opamp-core/actions/secrets/AWS_ROLE_TO_ASSUME",
        {
            "encrypted_value": (
                "encrypted:public-key:arn:aws:iam::123456789012:role/opamp-github-deploy"
            ),
            "key_id": "key-id",
        },
    )
    assert ("POST", "/repos/opamp-observe/opamp-core/actions/variables", {
        "name": "AWS_KEY_NAME",
        "value": "opamp-regression",
    }) in captured_requests
    assert ("POST", "/repos/opamp-observe/opamp-core/actions/variables", {
        "name": "AWS_ADMIN_SOURCE_CIDR",
        "value": "203.0.113.10/32",
    }) in captured_requests
    assert ("POST", "/repos/opamp-observe/opamp-core/actions/variables", {
        "name": "CLOUD_PROVIDER",
        "value": "aws",
    }) in captured_requests


def test_azure_subjects_scope_github_federation_to_main_branch(
    oidc_role_module: ModuleType,
) -> None:
    """Ensure Azure federation is limited to accepted repository subjects."""
    config = oidc_role_module.AzureOidcConfig(
        app_name="opamp-github-deploy",
        branch="main",
        federated_credential_name="opamp-core-main",
        github_organization="opamp-observe",
        github_organization_id="331386630",
        github_repository="opamp-core",
        github_repository_id="1181137273",
    )

    subject_values = oidc_role_module._azure_subject_values(config)
    credential_payload = oidc_role_module._azure_federated_credential_payload(
        "opamp-core-main",
        subject_values[0],
    )

    assert subject_values == [
        "repo:opamp-observe/opamp-core:ref:refs/heads/main",
        "repo:opamp-observe@331386630/opamp-core@1181137273:ref:refs/heads/main",
    ]
    assert credential_payload[oidc_role_module.AZURE_ISSUER_KEY] == (
        "https://token.actions.githubusercontent.com"
    )
    assert credential_payload[oidc_role_module.AZURE_AUDIENCES_KEY] == [
        "api://AzureADTokenExchange"
    ]
    assert credential_payload[oidc_role_module.AZURE_SUBJECT_KEY] == subject_values[0]


def test_azure_dry_run_prints_github_secret_values_and_variables(
    oidc_role_module: ModuleType,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify Azure mode reports the GitHub settings used by the main workflow."""
    exit_code = oidc_role_module.main(
        [
            "--dry-run",
            "--cloud-provider",
            "azure",
            "--configure-github",
            "--assign-azure-role",
            "--azure-webapp-name",
            "fluent-opamp",
            "--azure-resource-group",
            "opamp-regression-rg",
        ]
    )

    captured_output = capsys.readouterr()

    assert exit_code == 0
    assert (
        "AZUREAPPSERVICE_CLIENTID_195EE0A2DA3947CAA0427043CC5FEEFF="
        "00000000-0000-0000-0000-000000000001"
    ) in captured_output.out
    assert (
        "AZUREAPPSERVICE_TENANTID_40CBF888FD894E9EA2D20C44941831DC="
        "00000000-0000-0000-0000-000000000004"
    ) in captured_output.out
    assert (
        "AZUREAPPSERVICE_SUBSCRIPTIONID_F23BE392CBB5496182D244751F520677="
        "00000000-0000-0000-0000-000000000003"
    ) in captured_output.out


def test_cloud_provider_selects_azure_resource_configuration(
    oidc_role_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure the cloud-provider argument routes resource creation to Azure."""
    captured_provider_calls: list[str] = []

    def fake_configure_azure_resources(
        _arguments: object,
        *,
        dry_run: bool,
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Capture Azure routing and return representative GitHub settings."""
        captured_provider_calls.append(f"azure:{dry_run}")
        return (
            {"AZUREAPPSERVICE_CLIENTID_195EE0A2DA3947CAA0427043CC5FEEFF": "client-id"},
            {"CLOUD_PROVIDER": "azure"},
        )

    def fake_configure_aws_resources(
        _arguments: object,
        *,
        dry_run: bool,
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Fail the test if Azure selection accidentally configures AWS."""
        captured_provider_calls.append(f"aws:{dry_run}")
        return {}, {}

    monkeypatch.setattr(
        oidc_role_module,
        "_configure_azure_resources",
        fake_configure_azure_resources,
    )
    monkeypatch.setattr(
        oidc_role_module,
        "_configure_aws_resources",
        fake_configure_aws_resources,
    )

    exit_code = oidc_role_module.main(["--dry-run", "--cloud-provider", "azure"])

    assert exit_code == 0
    assert captured_provider_calls == ["azure:True"]


def test_github_token_can_be_resolved_from_gh_authentication(
    oidc_role_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Use local GitHub CLI authentication when no explicit token is provided."""
    arguments = oidc_role_module._build_parser().parse_args(["--configure-github"])

    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(
        oidc_role_module,
        "_run_command",
        lambda command, check=True: subprocess.CompletedProcess(
            command,
            0,
            stdout="gh-token\n",
            stderr="",
        ),
    )

    resolved_token = oidc_role_module._resolve_github_token(arguments, dry_run=False)

    assert resolved_token == "gh-token"


def test_github_token_can_be_resolved_from_git_credential_helper(
    oidc_role_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Read a token from the local Git credential helper when explicitly requested."""
    arguments = oidc_role_module._build_parser().parse_args(
        ["--configure-github", "--github-token-source", "git"]
    )
    captured_inputs: list[str] = []

    def fake_run_command_with_input(
        command: list[str],
        command_input: str,
        *,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Capture Git credential stdin and return a stored token."""
        captured_inputs.append(command_input)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="protocol=https\nhost=github.com\npassword=git-token\n",
            stderr="",
        )

    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(
        oidc_role_module,
        "_run_command_with_input",
        fake_run_command_with_input,
    )

    resolved_token = oidc_role_module._resolve_github_token(arguments, dry_run=False)

    assert resolved_token == "git-token"
    assert captured_inputs == ["protocol=https\nhost=github.com\n\n"]


def test_missing_pynacl_logs_install_instructions(
    oidc_role_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Fail early with installation guidance when GitHub secret encryption is unavailable."""
    original_import = builtins.__import__

    def fake_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        """Simulate PyNaCl not being installed while leaving other imports alone."""
        if name == "nacl":
            raise ImportError("No module named nacl")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError, match="PyNaCl"):
        oidc_role_module._ensure_pynacl_available()

    assert "PyNaCl is required when --configure-github is used." in caplog.text
    assert "py -3 -m pip install -r requirements.txt" in caplog.text
