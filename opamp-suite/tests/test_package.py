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

"""Tests for the OpAMP suite metadata package."""

from pathlib import Path

import tomllib

from opamp_suite import __version__

PYPROJECT_PATH = Path(__file__).resolve().parents[1] / "pyproject.toml"
EXPECTED_RUNTIME_PROFILES = {
    "all",
    "catalog",
    "client-config-editor",
    "config-editor",
    "consumer",
    "credentials-editor",
    "editors",
    "server",
}


def test_package_version_matches_release_profile() -> None:
    """Verify the importable package exposes the profile release version."""
    assert __version__ == "0.6.0"


def test_runtime_installation_profiles_are_declared() -> None:
    """Verify aggregate and individual runtime installation profiles remain available."""
    metadata = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    declared_profiles = set(metadata["project"]["optional-dependencies"])

    assert EXPECTED_RUNTIME_PROFILES <= declared_profiles
