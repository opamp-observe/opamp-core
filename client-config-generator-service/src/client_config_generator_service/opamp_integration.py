# Copyright 2026 mp3monster.org
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

"""Provider plugin entry point for the client config generator service."""

from quart import Quart

from client_config_generator_service.app import register_client_config_generator_component


def register_client_config_generator_feature(opamp_app: Quart) -> None:
    """Mount generator UI and API routes into an OpAMP provider.

    Args:
        opamp_app: Existing provider Quart application.
    """
    register_client_config_generator_component(opamp_app)
