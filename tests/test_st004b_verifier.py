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

"""Unit coverage for the ST-004B verifier and local JWT issuer."""

# Scenario scripts intentionally expose private helpers only to this focused test.
# pylint: disable=protected-access

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import jwt

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VERIFIER_MODULE_NAME = "st004b_verify"
ISSUER_MODULE_NAME = "st004b_issuer"
JWT_OPTION_VERIFY_SIGNATURE = "verify_signature"
EXPECTED_UNAUTHORIZED_STATUS = 401
EXPECTED_STATIC_UI_TOOL_CHECKS = {
    "static_ui_tool_missing",
    "static_ui_tool_valid",
}
COMPOSE_PATH = (
    REPOSITORY_ROOT / "tests" / "test-containers" / "st004b" / "docker-compose.yml"
)
GITLEAKS_ALLOW_MARKER = "# gitleaks:allow"
JWT_AUDIENCE_ENVIRONMENT_KEYS = (
    "OPAMP_AUTH_JWT_AUDIENCE:",
    "UI_AUTH_JWT_AUDIENCE:",
)
VERIFIER_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "test-containers"
    / "st004b"
    / "scripts"
    / "verify_st004b.py"
)
ISSUER_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "test-containers"
    / "st004b"
    / "scripts"
    / "jwt_issuer.py"
)


def _load_module(module_name: str, module_path: Path):
    """Load one scenario script from its non-package filesystem path.

    Args:
        module_name: Unique name registered for the loaded script.
        module_path: Python script path to execute as a module.
    """
    module_spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert module_spec is not None
    assert module_spec.loader is not None
    loaded_module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_name] = loaded_module
    module_spec.loader.exec_module(loaded_module)
    return loaded_module


def test_verifier_registers_every_documented_profile() -> None:
    """Every command-line profile should have one verification implementation."""
    verifier = _load_module(VERIFIER_MODULE_NAME, VERIFIER_PATH)

    assert set(verifier.SUPPORTED_PROFILES) == set(verifier.PROFILE_VERIFIERS)


def test_public_jwt_audiences_are_explicitly_allowlisted_for_gitleaks() -> None:
    """Public JWT audience fixtures should retain narrowly scoped scanner annotations."""
    compose_lines = COMPOSE_PATH.read_text(encoding="utf-8").splitlines()

    for environment_key in JWT_AUDIENCE_ENVIRONMENT_KEYS:
        matching_lines = [line for line in compose_lines if environment_key in line]
        assert len(matching_lines) == 1
        assert GITLEAKS_ALLOW_MARKER in matching_lines[0]


def test_route_check_records_expected_and_observed_status(monkeypatch) -> None:
    """Route evidence should retain status expectations and response details."""
    verifier = _load_module(VERIFIER_MODULE_NAME, VERIFIER_PATH)
    monkeypatch.setattr(
        verifier,
        "_request",
        lambda *args, **kwargs: (EXPECTED_UNAUTHORIZED_STATUS, "rejected"),
    )

    result = verifier._route_check(
        name="missing_token",
        url="http://provider/api/clients",
        expected_statuses={EXPECTED_UNAUTHORIZED_STATUS},
    )

    assert result[verifier.KEY_PASSED] is True
    assert result[verifier.KEY_STATUS] == EXPECTED_UNAUTHORIZED_STATUS
    assert result[verifier.KEY_BODY] == "rejected"


def test_jwt_issuer_creates_isolated_claim_variants() -> None:
    """Signed negative JWTs should differ only in their targeted claims."""
    issuer = _load_module(ISSUER_MODULE_NAME, ISSUER_PATH)

    valid_claims = jwt.decode(
        issuer._mint_token(issuer.CASE_VALID),
        options={JWT_OPTION_VERIFY_SIGNATURE: False},
    )
    expired_claims = jwt.decode(
        issuer._mint_token(issuer.CASE_EXPIRED),
        options={JWT_OPTION_VERIFY_SIGNATURE: False},
    )
    wrong_issuer_claims = jwt.decode(
        issuer._mint_token(issuer.CASE_WRONG_ISSUER),
        options={JWT_OPTION_VERIFY_SIGNATURE: False},
    )

    assert valid_claims[issuer.KEY_ISSUER] == issuer.ISSUER
    assert expired_claims[issuer.KEY_EXPIRATION] < valid_claims[issuer.KEY_ISSUED_AT]
    assert wrong_issuer_claims[issuer.KEY_ISSUER] == issuer.WRONG_ISSUER
    assert wrong_issuer_claims[issuer.KEY_AUDIENCE] == issuer.AUDIENCE


def test_static_ui_profile_checks_tool_authorization(monkeypatch) -> None:
    """Static UI-token coverage should include rejected and accepted tool requests."""
    verifier = _load_module(VERIFIER_MODULE_NAME, VERIFIER_PATH)
    monkeypatch.setattr(
        verifier,
        "_request",
        lambda *args, **kwargs: (EXPECTED_UNAUTHORIZED_STATUS, "rejected"),
    )
    monkeypatch.setattr(verifier, "_wait_for_client", lambda **kwargs: {})

    checks = verifier._verify_static_ui(
        "http://provider",
        verifier.DEFAULT_VERIFY_TIMEOUT_SECONDS,
        "http://issuer",
        None,
    )
    check_names = {check[verifier.KEY_NAME] for check in checks}

    assert EXPECTED_STATIC_UI_TOOL_CHECKS.issubset(check_names)


def test_report_writer_includes_profile_checks_and_evidence(tmp_path: Path) -> None:
    """Profile reports should remain reviewable without opening raw JSON."""
    verifier = _load_module(VERIFIER_MODULE_NAME, VERIFIER_PATH)
    report_path = tmp_path / verifier.REPORT_FILE_NAME
    check = verifier._check("sample", True, 200, 200)

    verifier._write_report(
        report_path,
        profile=verifier.PROFILE_NO_AUTH,
        checks=[check],
        evidence={verifier.SUMMARY_FILE_NAME: "summary.json"},
        result=verifier.PASSED_RESULT,
    )

    report = report_path.read_text(encoding=verifier.UTF_8_ENCODING)
    assert "ST-004B Results - no-auth" in report
    assert "| sample | `200` | `200` | PASS |" in report
    assert "summary.json" in report
