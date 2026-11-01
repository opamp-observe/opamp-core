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


class AgentValidationError(RuntimeError):
    """Base error for external agent validation orchestration."""


class AgentConfigError(AgentValidationError):
    """Raised when external validation config entries are invalid."""


class AgentNotSupportedError(AgentValidationError):
    """Raised when no configured validator entry matches the requested type/version."""


class AgentAdapterNotSupportedError(AgentValidationError):
    """Raised when no adapter implementation matches the configured adapter key."""


class AgentCommandBuildError(AgentValidationError):
    """Raised when an adapter cannot build a valid execution command."""
