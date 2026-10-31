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

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationAgentEntry:
    """Immutable runtime model for one external agent validation configuration.

    Each instance maps one configured validator command (plus optional version
    targeting) that `ExternalAgentValidationService` can resolve and execute.
    """

    agent_type: str
    command_path: str
    command_args: list[str] = field(default_factory=list)
    agent_version: str | None = None
    adapter: str | None = None
    send_config_via_stdin: bool = False
    environment: dict[str, str] = field(default_factory=dict)
    working_directory: str | None = None
    success_exit_codes: list[int] = field(default_factory=lambda: [0])
    dry_run_validation_enabled: bool = True

    @property
    def normalized_agent_type(self) -> str:
        return str(self.agent_type or "").strip().lower()

    @property
    def normalized_agent_version(self) -> str | None:
        value = str(self.agent_version or "").strip()
        return value if value else None

    @property
    def adapter_key(self) -> str:
        adapter_value = str(self.adapter or "").strip().lower()
        if adapter_value:
            return adapter_value
        return self.normalized_agent_type
