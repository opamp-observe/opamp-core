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

"""Expose the independently packaged shared source to broker tests."""

import sys
from pathlib import Path

SHARED_SOURCE_PATH = Path(__file__).resolve().parents[2] / "shared" / "src"
resolved_shared_source_path = str(SHARED_SOURCE_PATH.resolve())
if resolved_shared_source_path not in sys.path:
    sys.path.insert(0, resolved_shared_source_path)
