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

"""Make the suite source package importable during repository-wide tests."""

from __future__ import annotations

import sys
from pathlib import Path

SUITE_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src"


def pytest_configure() -> None:
    """Add the suite source directory when tests run outside the uv environment."""
    source_root_text = str(SUITE_SOURCE_ROOT)
    if source_root_text not in sys.path:
        sys.path.insert(0, source_root_text)
