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

"""Shared provider UI asset definitions used by runtime and build tooling."""

from __future__ import annotations

PROVIDER_UI_JS_FILENAMES = (
    "web_ui_state.js",
    "web_ui_functions.js",
    "web_ui_framework.js",
    "web_ui_bindings.js",
)


def mini_filename(source_filename: str) -> str:
    """Return the compacted asset filename for one provider UI JavaScript file."""
    return source_filename.replace(".js", ".mini.js")
