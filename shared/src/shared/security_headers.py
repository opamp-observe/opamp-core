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

"""Shared HTTP response-header protection for Quart browser surfaces."""

from __future__ import annotations

from quart import Quart, Response

CONTENT_SECURITY_POLICY_HEADER = "Content-Security-Policy"
CONTENT_SECURITY_POLICY_SEPARATOR = ";"
FRAME_ANCESTORS_DIRECTIVE = "frame-ancestors"
FRAME_ANCESTORS_NONE_POLICY = f"{FRAME_ANCESTORS_DIRECTIVE} 'none'"
X_FRAME_OPTIONS_DENY = "DENY"
X_FRAME_OPTIONS_HEADER = "X-Frame-Options"


def _deny_framing_in_content_security_policy(existing_policy: str) -> str:
    """Return a CSP that retains other directives and denies every frame ancestor.

    Parameters
    ----------
    existing_policy:
        Optional Content-Security-Policy value already set by the response producer.

    """
    retained_directives = [
        directive.strip()
        for directive in existing_policy.split(CONTENT_SECURITY_POLICY_SEPARATOR)
        if directive.strip()
        and directive.strip().split(maxsplit=1)[0].lower() != FRAME_ANCESTORS_DIRECTIVE
    ]
    retained_directives.append(FRAME_ANCESTORS_NONE_POLICY)
    return f"{CONTENT_SECURITY_POLICY_SEPARATOR} ".join(retained_directives)


def apply_clickjacking_protection(response: Response) -> Response:
    """Apply deny-by-default framing headers to an HTTP response.

    Parameters
    ----------
    response:
        Quart response whose existing CSP directives must be preserved where possible.

    """
    existing_policy = response.headers.get(CONTENT_SECURITY_POLICY_HEADER, "")
    response.headers[CONTENT_SECURITY_POLICY_HEADER] = _deny_framing_in_content_security_policy(
        existing_policy
    )
    response.headers[X_FRAME_OPTIONS_HEADER] = X_FRAME_OPTIONS_DENY
    return response


def register_clickjacking_protection(app: Quart) -> None:
    """Register the shared framing policy for every HTTP response from an app.

    Parameters
    ----------
    app:
        Quart application that owns the protected browser and API routes.

    """
    app.after_request(apply_clickjacking_protection)
