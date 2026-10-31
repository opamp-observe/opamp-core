#!/usr/bin/env python3
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
# 
from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from importlib import import_module
from typing import Any

ERR_UI_AUTH_CONFIG_INVALID = "invalid ui-use-authorization configuration"


@dataclass(frozen=True)
class UIAuthResult:
    """Normalized auth decision used by config-service HTTP handlers."""

    allowed: bool
    status_code: int = HTTPStatus.OK
    error: str = ""
    www_authenticate: str | None = None


def evaluate_ui_http_auth(
    *,
    path: str,
    method: str,
    authorization_header: str | None,
    remote_addr: str | None,
) -> UIAuthResult:
    """Evaluate non-OpAMP HTTP auth using provider auth stack when available.

    This intentionally reuses OpAMP provider auth modules to avoid introducing a
    separate auth model for config-service.
    """
    try:
        provider_auth = import_module("opamp_provider.auth")
        opamp_protocol = import_module("opamp_provider.opamp_protocol")
    except ModuleNotFoundError:
        # Mitigates local/dev standalone runs where provider package is absent.
        # In that mode we keep UI routes usable by allowing requests through.
        return UIAuthResult(allowed=True)

    decision: Any = opamp_protocol.evaluate_non_opamp_http_auth(
        path=path,
        method=method,
        authorization_header=authorization_header,
        remote_addr=remote_addr,
        invalid_config_error=ERR_UI_AUTH_CONFIG_INVALID,
    )
    if decision.allowed:
        return UIAuthResult(allowed=True)

    www_authenticate = None
    if decision.status_code == HTTPStatus.UNAUTHORIZED:
        www_authenticate = str(provider_auth.WWW_AUTHENTICATE_BEARER)

    return UIAuthResult(
        allowed=False,
        status_code=int(decision.status_code),
        error=str(decision.error or "authorization failed"),
        www_authenticate=www_authenticate,
    )
