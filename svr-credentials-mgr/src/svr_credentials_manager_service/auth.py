# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Bearer-auth helpers aligned with provider non-OpAMP API protection."""

from __future__ import annotations

import hmac
import logging
import os
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path

from .service_config import (
    resolve_ui_auth_jwt_audience_from_config,
    resolve_ui_auth_jwt_issuer_from_config,
    resolve_ui_auth_jwt_jwks_url_from_config,
    resolve_ui_auth_jwt_leeway_seconds_from_config,
    resolve_ui_auth_static_token_from_config,
    resolve_ui_authorization_mode_from_config,
)

try:
    import jwt
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    jwt = None  # type: ignore[assignment]

PROVIDER_AUTH_MODE_NONE = "none"
PROVIDER_AUTH_MODE_CONFIG_TOKEN = "config-token"  # noqa: S105
PROVIDER_AUTH_MODE_IDP = "idp"

AUTH_MODE_DISABLED = "disabled"
AUTH_MODE_STATIC = "static"
AUTH_MODE_JWT = "jwt"

ENV_UI_USE_AUTHORIZATION = "SVR_CREDENTIALS_UI_USE_AUTHORIZATION"
ENV_UI_AUTH_STATIC_TOKEN = "UI_AUTH_STATIC_TOKEN"  # noqa: S105
ENV_UI_AUTH_JWT_ISSUER = "UI_AUTH_JWT_ISSUER"
ENV_UI_AUTH_JWT_AUDIENCE = "UI_AUTH_JWT_AUDIENCE"
ENV_UI_AUTH_JWT_JWKS_URL = "UI_AUTH_JWT_JWKS_URL"
ENV_UI_AUTH_JWT_LEEWAY_SECONDS = "UI_AUTH_JWT_LEEWAY_SECONDS"
ERR_INVALID_UI_AUTH_CONFIG = "invalid ui-use-authorization configuration"
WWW_AUTHENTICATE_BEARER = 'Bearer realm="svr-credentials-manager-service"'


@dataclass(frozen=True)
class AuthDecision:
    """Authorization decision for one API request."""

    allowed: bool
    status_code: int = HTTPStatus.OK
    error: str = ""
    reason: str = ""


def _provider_ui_authorization_mode() -> str:
    """Return provider-configured UI auth mode when provider is importable."""
    try:
        from opamp_provider import config as provider_config
    except Exception:  # pragma: no cover - provider package absent in standalone mode
        return PROVIDER_AUTH_MODE_NONE
    return str(getattr(provider_config.CONFIG, "ui_use_authorization", "")).strip().lower()


def resolve_ui_authorization_mode(config_path: Path | None = None) -> str:
    """Resolve service API auth mode from env, config, or provider settings."""
    configured_mode = str(os.environ.get(ENV_UI_USE_AUTHORIZATION, "")).strip().lower()
    if configured_mode:
        return configured_mode
    configured_mode = resolve_ui_authorization_mode_from_config(config_path)
    if configured_mode:
        return configured_mode
    return _provider_ui_authorization_mode()


def _provider_mode_to_auth_mode(provider_mode: str) -> str | None:
    """Map provider-style authorization values to auth-helper mode strings."""
    if provider_mode == PROVIDER_AUTH_MODE_NONE:
        return AUTH_MODE_DISABLED
    if provider_mode == PROVIDER_AUTH_MODE_CONFIG_TOKEN:
        return AUTH_MODE_STATIC
    if provider_mode == PROVIDER_AUTH_MODE_IDP:
        return AUTH_MODE_JWT
    return None


def _extract_bearer_token(authorization_header: str | None) -> str | None:
    """Extract the bearer token from an Authorization header value."""
    if authorization_header is None:
        return None
    value = str(authorization_header).strip()
    if not value:
        return None
    parts = value.split(" ", 1)
    if len(parts) != 2 or parts[0].strip().lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def _jwt_jwks_url(config_path: Path | None = None) -> str | None:
    """Return configured UI JWKS URL, deriving from issuer when needed."""
    configured_url = str(os.environ.get(ENV_UI_AUTH_JWT_JWKS_URL, "")).strip()
    if not configured_url:
        configured_url = str(
            resolve_ui_auth_jwt_jwks_url_from_config(config_path) or ""
        ).strip()
    if configured_url:
        return configured_url
    issuer = _jwt_issuer(config_path)
    if not issuer:
        return None
    return f"{issuer.rstrip('/')}/protocol/openid-connect/certs"


def _jwt_issuer(config_path: Path | None = None) -> str:
    """Return the configured JWT issuer from env-vars or runtime config."""
    configured_issuer = str(os.environ.get(ENV_UI_AUTH_JWT_ISSUER, "")).strip()
    if configured_issuer:
        return configured_issuer
    return str(resolve_ui_auth_jwt_issuer_from_config(config_path) or "").strip()


def _jwt_audience(config_path: Path | None = None) -> str:
    """Return the configured JWT audience from env-vars or runtime config."""
    configured_audience = str(os.environ.get(ENV_UI_AUTH_JWT_AUDIENCE, "")).strip()
    if configured_audience:
        return configured_audience
    return str(resolve_ui_auth_jwt_audience_from_config(config_path) or "").strip()


def _jwt_leeway_seconds(config_path: Path | None = None) -> int:
    """Return configured JWT clock-skew leeway in seconds."""
    configured_leeway = os.environ.get(ENV_UI_AUTH_JWT_LEEWAY_SECONDS, "").strip()
    try:
        if configured_leeway:
            return max(0, int(configured_leeway))
        return max(
            0,
            int(resolve_ui_auth_jwt_leeway_seconds_from_config(config_path) or 30),
        )
    except ValueError:
        return 30


def _reject(
    *,
    status_code: int,
    error: str,
    reason: str,
    path: str,
    method: str,
    remote_addr: str | None,
    mode: str,
) -> AuthDecision:
    """Return a rejected auth decision and emit a structured warning."""
    logging.getLogger(__name__).warning(
        "credentials-manager authorization rejected mode=%s method=%s path=%s remote_addr=%s reason=%s",
        mode,
        method,
        path,
        remote_addr or "unknown",
        reason,
    )
    return AuthDecision(
        allowed=False,
        status_code=status_code,
        error=error,
        reason=reason,
    )


def _validate_jwt_token(token: str, config_path: Path | None = None) -> str | None:
    """Validate JWT signature and issuer/audience claims."""
    if jwt is None:
        return "jwt mode requires PyJWT dependency"
    jwks_url = _jwt_jwks_url(config_path)
    if not jwks_url:
        return (
            f"jwt mode requires {ENV_UI_AUTH_JWT_JWKS_URL} "
            f"or {ENV_UI_AUTH_JWT_ISSUER}"
        )
    try:
        signing_key = jwt.PyJWKClient(jwks_url).get_signing_key_from_jwt(token)
        audience = _jwt_audience(config_path) or None
        issuer = _jwt_issuer(config_path) or None
        jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
            audience=audience,
            issuer=issuer,
            options={
                "verify_aud": bool(audience),
                "verify_iss": bool(issuer),
            },
            leeway=_jwt_leeway_seconds(config_path),
        )
    except Exception as error:  # pragma: no cover - library exception classes vary
        return f"jwt validation failed: {error}"
    return None


def evaluate_api_auth(
    *,
    path: str,
    method: str,
    authorization_header: str | None,
    remote_addr: str | None,
    config_path: Path | None = None,
) -> AuthDecision:
    """Authorize one credentials-manager API request."""
    provider_mode = resolve_ui_authorization_mode(config_path)
    auth_mode = _provider_mode_to_auth_mode(provider_mode)
    if auth_mode is None:
        return _reject(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            error=ERR_INVALID_UI_AUTH_CONFIG,
            reason=f"unsupported mode {provider_mode}",
            path=path,
            method=method,
            remote_addr=remote_addr,
            mode=provider_mode,
        )
    if method.upper() == "OPTIONS" or auth_mode == AUTH_MODE_DISABLED:
        return AuthDecision(allowed=True)

    token = _extract_bearer_token(authorization_header)
    if token is None:
        return _reject(
            status_code=HTTPStatus.UNAUTHORIZED,
            error="missing bearer token",
            reason="authorization header missing or malformed",
            path=path,
            method=method,
            remote_addr=remote_addr,
            mode=auth_mode,
        )

    if auth_mode == AUTH_MODE_STATIC:
        configured_token = str(os.environ.get(ENV_UI_AUTH_STATIC_TOKEN, "")).strip()
        if not configured_token:
            configured_token = str(
                resolve_ui_auth_static_token_from_config(config_path) or ""
            ).strip()
        if not configured_token:
            return _reject(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                error="static auth token is not configured",
                reason=f"{ENV_UI_AUTH_STATIC_TOKEN} not set",
                path=path,
                method=method,
                remote_addr=remote_addr,
                mode=auth_mode,
            )
        if not hmac.compare_digest(token, configured_token):
            return _reject(
                status_code=HTTPStatus.UNAUTHORIZED,
                error="invalid bearer token",
                reason="static token mismatch",
                path=path,
                method=method,
                remote_addr=remote_addr,
                mode=auth_mode,
            )
        return AuthDecision(allowed=True)

    jwt_validation_error = _validate_jwt_token(token, config_path)
    if jwt_validation_error:
        return _reject(
            status_code=HTTPStatus.UNAUTHORIZED,
            error="invalid bearer token",
            reason=jwt_validation_error,
            path=path,
            method=method,
            remote_addr=remote_addr,
            mode=auth_mode,
        )
    return AuthDecision(allowed=True)
