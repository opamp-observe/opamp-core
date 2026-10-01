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

"""Tests for optional provider authentication reuse."""

from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace

from client_config_generator_service import auth_integration


def test_auth_allows_standalone_requests_without_provider_modules(monkeypatch) -> None:
    """Standalone installs without provider auth should remain usable."""
    def missing_import(_: str) -> object:
        """Simulate provider packages not being installed."""
        raise ModuleNotFoundError

    monkeypatch.setattr(auth_integration, "import_module", missing_import)

    result = auth_integration.evaluate_ui_http_auth(
        path="/client-config-generator-service/api/v1/schema",
        method="GET",
        authorization_header=None,
        remote_addr="127.0.0.1",
    )

    assert result.allowed is True


def test_auth_returns_provider_allow_and_reject_decisions(monkeypatch) -> None:
    """Embedded installs should normalize provider auth outcomes and challenges."""
    provider_auth = SimpleNamespace(WWW_AUTHENTICATE_BEARER='Bearer realm="test"')
    decisions = [
        SimpleNamespace(allowed=True, status_code=HTTPStatus.OK, error=""),
        SimpleNamespace(
            allowed=False,
            status_code=HTTPStatus.UNAUTHORIZED,
            error="missing bearer token",
        ),
    ]
    provider_protocol = SimpleNamespace(
        evaluate_non_opamp_http_auth=lambda **_: decisions.pop(0)
    )

    def fake_import(module_name: str) -> object:
        """Return the provider test doubles by their requested module name."""
        return provider_auth if module_name.endswith(".auth") else provider_protocol

    monkeypatch.setattr(auth_integration, "import_module", fake_import)
    allowed_result = auth_integration.evaluate_ui_http_auth(
        path="/api",
        method="GET",
        authorization_header=None,
        remote_addr=None,
    )
    rejected_result = auth_integration.evaluate_ui_http_auth(
        path="/api",
        method="GET",
        authorization_header=None,
        remote_addr=None,
    )

    assert allowed_result.allowed is True
    assert rejected_result.allowed is False
    assert rejected_result.status_code == HTTPStatus.UNAUTHORIZED
    assert rejected_result.www_authenticate == 'Bearer realm="test"'
