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

"""Optional reuse of provider-managed browser and API authentication."""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from importlib import import_module
from typing import Any

ERR_UI_AUTH_CONFIG_INVALID = "invalid ui-use-authorization configuration"


@dataclass(frozen=True)
class UIAuthResult:
    """Normalized provider authentication decision for generator requests."""

    allowed: bool  # Whether request processing may continue.
    status_code: int = HTTPStatus.OK  # HTTP response status used when rejected.
    error: str = ""  # Safe error text returned to the caller.
    www_authenticate: str | None = None  # Optional bearer challenge header.


def evaluate_ui_http_auth(
    *,
    path: str,
    method: str,
    authorization_header: str | None,
    remote_addr: str | None,
) -> UIAuthResult:
    """Apply provider authentication when installed, otherwise allow standalone use.

    Args:
        path: Request path used for protected-prefix checks.
        method: Incoming HTTP method.
        authorization_header: Optional browser-managed authorization header.
        remote_addr: Caller address used for provider security logging.
    """
    try:
        provider_auth = import_module("opamp_provider.auth")
        provider_protocol = import_module("opamp_provider.opamp_protocol")
    except ModuleNotFoundError:
        return UIAuthResult(allowed=True)

    decision: Any = provider_protocol.evaluate_non_opamp_http_auth(
        path=path,
        method=method,
        authorization_header=authorization_header,
        remote_addr=remote_addr,
        invalid_config_error=ERR_UI_AUTH_CONFIG_INVALID,
    )
    if decision.allowed:
        return UIAuthResult(allowed=True)
    challenge = None
    if decision.status_code == HTTPStatus.UNAUTHORIZED:
        challenge = str(provider_auth.WWW_AUTHENTICATE_BEARER)
    return UIAuthResult(
        allowed=False,
        status_code=int(decision.status_code),
        error=str(decision.error or "authorization failed"),
        www_authenticate=challenge,
    )
