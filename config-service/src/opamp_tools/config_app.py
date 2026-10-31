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

"""Stable entrypoints for config-service Quart component registration."""

from __future__ import annotations

from quart import Quart


def register_api_component(app: Quart) -> None:
    from config_service.app import register_api_component as _register_api_component

    _register_api_component(app)


def register_ui_component(app: Quart) -> None:
    from config_service.app import register_ui_component as _register_ui_component

    _register_ui_component(app)

