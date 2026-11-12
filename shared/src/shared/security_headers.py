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
CONTENT_SECURITY_POLICY_REPORT_ONLY_HEADER = "Content-Security-Policy-Report-Only"
CONTENT_SECURITY_POLICY_SEPARATOR = ";"
BASE_URI_NONE_POLICY = "base-uri 'none'"
CONNECT_SRC_SELF_POLICY = "connect-src 'self'"
DEFAULT_SRC_SELF_POLICY = "default-src 'self'"
FRAME_ANCESTORS_DIRECTIVE = "frame-ancestors"
FRAME_ANCESTORS_NONE_POLICY = f"{FRAME_ANCESTORS_DIRECTIVE} 'none'"
FONT_SRC_SELF_POLICY = "font-src 'self'"
FORM_ACTION_DIRECTIVE = "form-action"
FORM_ACTION_SELF_POLICY = f"{FORM_ACTION_DIRECTIVE} 'self'"
FRAME_SRC_NONE_POLICY = "frame-src 'none'"
IMG_SRC_SELF_DATA_POLICY = "img-src 'self' data:"
MANIFEST_SRC_SELF_POLICY = "manifest-src 'self'"
OBJECT_SRC_NONE_POLICY = "object-src 'none'"
SCRIPT_SRC_SELF_POLICY = "script-src 'self'"
STYLE_SRC_SELF_POLICY = "style-src 'self'"
WORKER_SRC_NONE_POLICY = "worker-src 'none'"
SHARED_CONTENT_SECURITY_POLICY_DIRECTIVES = (
    FRAME_ANCESTORS_NONE_POLICY,
    FORM_ACTION_SELF_POLICY,
)
SHARED_CONTENT_SECURITY_POLICY = f"{CONTENT_SECURITY_POLICY_SEPARATOR} ".join(
    SHARED_CONTENT_SECURITY_POLICY_DIRECTIVES
)
STRICT_REPORT_ONLY_CONTENT_SECURITY_POLICY_DIRECTIVES = (
    DEFAULT_SRC_SELF_POLICY,
    BASE_URI_NONE_POLICY,
    OBJECT_SRC_NONE_POLICY,
    FRAME_ANCESTORS_NONE_POLICY,
    FORM_ACTION_SELF_POLICY,
    SCRIPT_SRC_SELF_POLICY,
    STYLE_SRC_SELF_POLICY,
    IMG_SRC_SELF_DATA_POLICY,
    FONT_SRC_SELF_POLICY,
    CONNECT_SRC_SELF_POLICY,
    FRAME_SRC_NONE_POLICY,
    MANIFEST_SRC_SELF_POLICY,
    WORKER_SRC_NONE_POLICY,
)
STRICT_REPORT_ONLY_CONTENT_SECURITY_POLICY = f"{CONTENT_SECURITY_POLICY_SEPARATOR} ".join(
    STRICT_REPORT_ONLY_CONTENT_SECURITY_POLICY_DIRECTIVES
)
X_FRAME_OPTIONS_DENY = "DENY"
X_FRAME_OPTIONS_HEADER = "X-Frame-Options"
X_CONTENT_TYPE_OPTIONS_HEADER = "X-Content-Type-Options"
X_CONTENT_TYPE_OPTIONS_NOSNIFF = "nosniff"


def _merge_enforced_directives(
    existing_policy: str,
    enforced_directives: tuple[str, ...],
) -> str:
    """Retain unrelated CSP directives and replace every shared directive.

    Parameters
    ----------
    existing_policy:
        Optional Content-Security-Policy value already set by the response producer.
    enforced_directives:
        Complete directive values that replace directives with the same names.

    Returns
    -------
    str
        Merged policy containing retained producer directives followed by shared directives.

    """
    enforced_directive_names = {
        policy.split(maxsplit=1)[0].lower()
        for policy in enforced_directives
    }
    retained_directives = [
        directive.strip()
        for directive in existing_policy.split(CONTENT_SECURITY_POLICY_SEPARATOR)
        if directive.strip()
        and directive.strip().split(maxsplit=1)[0].lower() not in enforced_directive_names
    ]
    retained_directives.extend(enforced_directives)
    return f"{CONTENT_SECURITY_POLICY_SEPARATOR} ".join(retained_directives)


def _enforce_shared_content_security_policy(existing_policy: str) -> str:
    """Apply enforced framing and form restrictions while retaining other directives.

    Parameters
    ----------
    existing_policy:
        Optional enforced Content-Security-Policy value set by the response producer.

    Returns
    -------
    str
        Policy with framing denied and form submissions restricted to the same origin.

    """
    return _merge_enforced_directives(
        existing_policy,
        SHARED_CONTENT_SECURITY_POLICY_DIRECTIVES,
    )


def _enforce_strict_report_only_content_security_policy(existing_policy: str) -> str:
    """Apply the strict monitoring policy while retaining reporting directives.

    Parameters
    ----------
    existing_policy:
        Optional report-only policy whose unrelated directives, including report destinations,
        must remain available.

    Returns
    -------
    str
        Strict report-only policy augmented by unrelated producer directives.

    """
    return _merge_enforced_directives(
        existing_policy,
        STRICT_REPORT_ONLY_CONTENT_SECURITY_POLICY_DIRECTIVES,
    )


def apply_security_headers(response: Response) -> Response:
    """Apply shared browser security headers to an HTTP response.

    Parameters
    ----------
    response:
        Quart response whose existing CSP directives must be preserved where possible and whose
        framing, form submission destinations, and MIME handling must be restricted. A strict
        report-only policy is added so incompatible UI resources are observable before enforcement.

    Returns
    -------
    Response
        The supplied response with the shared browser security policy applied.

    """
    existing_policy = response.headers.get(CONTENT_SECURITY_POLICY_HEADER, "")
    response.headers[CONTENT_SECURITY_POLICY_HEADER] = _enforce_shared_content_security_policy(
        existing_policy
    )
    existing_report_only_policy = response.headers.get(
        CONTENT_SECURITY_POLICY_REPORT_ONLY_HEADER,
        "",
    )
    response.headers[CONTENT_SECURITY_POLICY_REPORT_ONLY_HEADER] = (
        _enforce_strict_report_only_content_security_policy(existing_report_only_policy)
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
