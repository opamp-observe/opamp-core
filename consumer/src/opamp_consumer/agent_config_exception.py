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

"""Base agent exception type for the OpAMP consumer."""

from opamp_consumer import AgentException


class AgentConfigException(AgentException, ValueError):
    """Raised when consumer agent operations fail because of a configuration issue."""

    def __init__(self, message: str, config_name: None | str = None) -> None:
        """Initialize the exception with a human-readable message."""
        if config_name is None:
            config_name = "--NOT KNOWN--"
        self.config_name = config_name
                
        super().__init__(message)

    def get_missing_config_name(self) -> str | None:
        """Return the specific configuration value that cause the problem"""
        return self.config_name
