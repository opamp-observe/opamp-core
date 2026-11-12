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

"""Shared HTTP response-header protections for Quart browser surfaces."""

from __future__ import annotations

from quart import Quart, Response

CONTENT_SECURITY_POLICY_HEADER = "Content-Security-Policy"
CONTENT_SECURITY_POLICY_SEPARATOR = ";"
FRAME_ANCESTORS_DIRECTIVE = "frame-ancestors"
FRAME_ANCESTORS_NONE_POLICY = f"{FRAME_ANCESTORS_DIRECTIVE} 'none'"
FORM_ACTION_DIRECTIVE = "form-action"
FORM_ACTION_SELF_POLICY = f"{FORM_ACTION_DIRECTIVE} 'self'"
SHARED_CONTENT_SECURITY_POLICY_DIRECTIVES = (
    FRAME_ANCESTORS_NONE_POLICY,
    FORM_ACTION_SELF_POLICY,
)
SHARED_CONTENT_SECURITY_POLICY = f"{CONTENT_SECURITY_POLICY_SEPARATOR} ".join(
    SHARED_CONTENT_SECURITY_POLICY_DIRECTIVES
)
X_FRAME_OPTIONS_DENY = "DENY"
X_FRAME_OPTIONS_HEADER = "X-Frame-Options"
X_CONTENT_TYPE_OPTIONS_HEADER = "X-Content-Type-Options"
X_CONTENT_TYPE_OPTIONS_NOSNIFF = "nosniff"


def _enforce_shared_content_security_policy(existing_policy: str) -> str:
    """Return a CSP that retains unrelated directives and applies the shared restrictions.

    Parameters
    ----------
    existing_policy:
        Optional Content-Security-Policy value already set by the response producer.

    Returns
    -------
    str
        Policy with framing denied and form submissions restricted to the same origin.

    """
    enforced_directive_names = {
        policy.split(maxsplit=1)[0].lower()
        for policy in SHARED_CONTENT_SECURITY_POLICY_DIRECTIVES
    }
    retained_directives = [
        directive.strip()
        for directive in existing_policy.split(CONTENT_SECURITY_POLICY_SEPARATOR)
        if directive.strip()
        and directive.strip().split(maxsplit=1)[0].lower() not in enforced_directive_names
    ]
    retained_directives.extend(SHARED_CONTENT_SECURITY_POLICY_DIRECTIVES)
    return f"{CONTENT_SECURITY_POLICY_SEPARATOR} ".join(retained_directives)


def apply_security_headers(response: Response) -> Response:
    """Apply shared browser security headers to an HTTP response.

    Parameters
    ----------
    response:
        Quart response whose existing CSP directives must be preserved where possible and whose
        framing, form submission destinations, and MIME handling must be restricted.

    Returns
    -------
    Response
        The supplied response with the shared browser security policy applied.

    """
    existing_policy = response.headers.get(CONTENT_SECURITY_POLICY_HEADER, "")
    response.headers[CONTENT_SECURITY_POLICY_HEADER] = _enforce_shared_content_security_policy(
        existing_policy
    )
    response.headers[X_FRAME_OPTIONS_HEADER] = X_FRAME_OPTIONS_DENY
    response.headers[X_CONTENT_TYPE_OPTIONS_HEADER] = X_CONTENT_TYPE_OPTIONS_NOSNIFF
    return response


def register_security_headers(app: Quart) -> None:
    """Register the shared browser security policy for every response from an app.

    Parameters
    ----------
    app:
        Quart application that owns the protected browser and API routes.

    """
    app.after_request(apply_security_headers)


def apply_clickjacking_protection(response: Response) -> Response:
    """Apply shared security headers through the former clickjacking-specific API.

    Parameters
    ----------
    response:
        Quart response passed by callers that still use the compatibility function.

    """
    return apply_security_headers(response)


def register_clickjacking_protection(app: Quart) -> None:
    """Register shared security headers through the former clickjacking-specific API.

    Parameters
    ----------
    app:
        Quart application passed by callers that still use the compatibility function.

    """
    register_security_headers(app)
