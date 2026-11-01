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

"""Compatibility facade for consumer exception imports."""

from opamp_consumer.agent_exception import AgentException
from opamp_consumer.command_exception import CommandException
from opamp_consumer.remote_agent_config_content_type_error import (
    RemoteAgentConfigContentTypeError,
)
from opamp_consumer.remote_agent_config_error import RemoteAgentConfigError
from opamp_consumer.remote_agent_config_hash_mismatch_error import (
    RemoteAgentConfigHashMismatchError,
)
from opamp_consumer.remote_agent_config_validation_error import (
    RemoteAgentConfigValidationError,
)
from opamp_consumer.remote_agent_config_write_error import (
    RemoteAgentConfigWriteError,
)

__all__ = [
    "AgentException",
    "CommandException",
    "RemoteAgentConfigContentTypeError",
    "RemoteAgentConfigError",
    "RemoteAgentConfigHashMismatchError",
    "RemoteAgentConfigValidationError",
    "RemoteAgentConfigWriteError",
]
