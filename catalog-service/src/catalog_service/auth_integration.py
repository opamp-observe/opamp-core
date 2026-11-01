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

from __future__ import annotations

import logging
from dataclasses import dataclass
from http import HTTPStatus
from importlib import import_module
from typing import Any

ERR_UI_AUTH_CONFIG_INVALID = "invalid ui-use-authorization configuration"
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class UIAuthResult:
    """Normalized auth decision used by catalog-service HTTP handlers."""

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
    """Evaluate non-OpAMP HTTP auth using the provider auth stack when available."""
    try:
        provider_auth = import_module("opamp_provider.auth")
        opamp_protocol = import_module("opamp_provider.opamp_protocol")
    except ModuleNotFoundError:
        # Freestanding catalog deployments may not include provider auth modules.
        # In that case preserve historical standalone behavior and allow access.
        LOGGER.info(
            "provider auth modules unavailable; allowing catalog request without provider-backed auth path=%s method=%s",
            path,
            method,
        )
        return UIAuthResult(allowed=True)

    decision: Any = opamp_protocol.evaluate_non_opamp_http_auth(
        path=path,
        method=method,
        authorization_header=authorization_header,
        remote_addr=remote_addr,
        invalid_config_error=ERR_UI_AUTH_CONFIG_INVALID,
    )
    if decision.allowed:
        LOGGER.debug(
            "catalog auth allowed path=%s method=%s remote_addr=%s",
            path,
            method,
            remote_addr,
        )
        return UIAuthResult(allowed=True)

    www_authenticate = None
    if decision.status_code == HTTPStatus.UNAUTHORIZED:
        www_authenticate = str(provider_auth.WWW_AUTHENTICATE_BEARER)

    result = UIAuthResult(
        allowed=False,
        status_code=int(decision.status_code),
        error=str(decision.error or "authorization failed"),
        www_authenticate=www_authenticate,
    )
    LOGGER.warning(
        "catalog auth rejected path=%s method=%s remote_addr=%s status_code=%s error=%s",
        path,
        method,
        remote_addr,
        int(result.status_code),
        result.error,
    )
    return result
