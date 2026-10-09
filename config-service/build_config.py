#!/usr/bin/env python3
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

"""Shared package metadata for config-service build and tooling flows."""

from __future__ import annotations

PACKAGE_NAME = "config-service"
PACKAGE_VERSION = "0.6.0"
PACKAGE_DESCRIPTION = "Tool for viewing and editing observability agent configurations."
INSTALL_REQUIRES = [
    "quart>=0.19.4",
    "pydantic>=2,<3",
    "lark>=1.2.2",
    "luaparser>=4.0.0",
]
DEV_REQUIRES = [
    "pylint>=3.0",
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=7.0.0",
    "ruff>=0.15.0",
]
