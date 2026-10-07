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

"""Build configuration for standalone config-service wheel artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
SHARED_PACKAGE_NAME = "shared"
for candidate in (ROOT, ROOT / "src", REPO_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def _load_build_config() -> tuple[list[str], list[str], str, str, str]:
    import build_config

    return (
        build_config.DEV_REQUIRES,
        build_config.INSTALL_REQUIRES,
        build_config.PACKAGE_DESCRIPTION,
        build_config.PACKAGE_NAME,
        build_config.PACKAGE_VERSION,
    )


DEV_REQUIRES, INSTALL_REQUIRES, PACKAGE_DESCRIPTION, PACKAGE_NAME, PACKAGE_VERSION = _load_build_config()

try:
    from shared.packaging_warnings import warn_if_cli_missing
except ModuleNotFoundError:  # pragma: no cover - build fallback when shared package is unavailable
    warn_if_cli_missing = None

if warn_if_cli_missing is not None:
    warn_if_cli_missing(
        component_label="config-service wheel build",
        repo_root=REPO_ROOT,
    )


setup(
    name=PACKAGE_NAME,
    version=PACKAGE_VERSION,
    description=PACKAGE_DESCRIPTION,
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Phil Wilkins",
    license="Apache-2.0",
    packages=find_packages(
        where="src",
        include=["config_service", "config_service.*", "opamp_tools", "opamp_tools.*"],
    )
    + [SHARED_PACKAGE_NAME],
    package_dir={"": "src", SHARED_PACKAGE_NAME: "../shared"},
    include_package_data=True,
    package_data={
        "config_service": [
            "html/*",
            "config/*.json",
            "json-definitions/*.json",
            "json-definitions/**/*.json",
            "json-schemas/*.json",
            "json-schemas/**/*.json",
        ],
    },
    install_requires=INSTALL_REQUIRES,
    extras_require={
        "dev": DEV_REQUIRES,
    },
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "config-service=config_service.app:main",
        ]
    },
)
