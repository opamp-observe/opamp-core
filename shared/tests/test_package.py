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

"""Package-level tests for the independently distributed shared utilities."""

from shared.security_headers import (
    FORM_ACTION_SELF_POLICY,
    FRAME_ANCESTORS_NONE_POLICY,
    SHARED_CONTENT_SECURITY_POLICY,
    X_CONTENT_TYPE_OPTIONS_NOSNIFF,
)
from shared.uuid_utils import generate_uuid7_bytes

UUID_BYTE_LENGTH = 16


def test_shared_package_exposes_runtime_helpers() -> None:
    """Verify representative runtime helpers import from the packaged namespace."""
    assert FRAME_ANCESTORS_NONE_POLICY == "frame-ancestors 'none'"
    assert FORM_ACTION_SELF_POLICY == "form-action 'self'"
    assert SHARED_CONTENT_SECURITY_POLICY == (
        "frame-ancestors 'none'; form-action 'self'"
    )
    assert X_CONTENT_TYPE_OPTIONS_NOSNIFF == "nosniff"
    assert len(generate_uuid7_bytes()) == UUID_BYTE_LENGTH
