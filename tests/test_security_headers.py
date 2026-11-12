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

"""Tests for the shared deny-by-default clickjacking response policy."""

import pytest
from quart import Quart, Response
from shared.security_headers import (
    CONTENT_SECURITY_POLICY_HEADER,
    FRAME_ANCESTORS_NONE_POLICY,
    X_FRAME_OPTIONS_DENY,
    X_FRAME_OPTIONS_HEADER,
    apply_clickjacking_protection,
    register_clickjacking_protection,
)

EXISTING_CONTENT_SECURITY_POLICY = "default-src 'self'; frame-ancestors https://example.com"
EXPECTED_MERGED_CONTENT_SECURITY_POLICY = "default-src 'self'; frame-ancestors 'none'"


def test_clickjacking_policy_preserves_csp_and_replaces_frame_ancestors() -> None:
    """Verify a permissive ancestor directive cannot weaken the shared policy."""
    response = Response("protected")
    response.headers[CONTENT_SECURITY_POLICY_HEADER] = EXISTING_CONTENT_SECURITY_POLICY

    protected_response = apply_clickjacking_protection(response)

    assert (
        protected_response.headers[CONTENT_SECURITY_POLICY_HEADER]
        == EXPECTED_MERGED_CONTENT_SECURITY_POLICY
    )
    assert protected_response.headers[X_FRAME_OPTIONS_HEADER] == X_FRAME_OPTIONS_DENY


@pytest.mark.asyncio
async def test_registered_policy_covers_success_and_error_responses() -> None:
    """Verify the global hook protects normal responses and Quart-generated errors."""
    app = Quart(__name__)
    register_clickjacking_protection(app)

    @app.get("/protected")
    async def protected_route() -> str:
        """Return a representative successful browser response."""
        return "protected"

    client = app.test_client()
    successful_response = await client.get("/protected")
    missing_response = await client.get("/missing")

    for response in (successful_response, missing_response):
        assert (
            response.headers[CONTENT_SECURITY_POLICY_HEADER]
            == FRAME_ANCESTORS_NONE_POLICY
        )
        assert response.headers[X_FRAME_OPTIONS_HEADER] == X_FRAME_OPTIONS_DENY
