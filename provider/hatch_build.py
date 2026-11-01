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

"""Provider build hook warnings shared with the standalone packaging flows."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface[Any]):
    """Emit packaging warnings before provider wheels are created."""

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """Warn when the OpAMP CLI is missing during a provider package build."""
        del version, build_data

        repo_root = Path(self.root).resolve().parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))

        try:
            from shared.packaging_warnings import warn_if_cli_missing
        except ModuleNotFoundError:  # pragma: no cover - isolated build fallback
            return

        warn_if_cli_missing(
            component_label="provider wheel build",
            repo_root=repo_root,
        )
