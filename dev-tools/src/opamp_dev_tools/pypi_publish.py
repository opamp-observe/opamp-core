# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Validate first-party wheel sets and publish them through ``uv publish``."""

from __future__ import annotations

import os
import re
import zipfile
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any

from .wheel_publish import WheelArtifact, discover_latest_wheels

DEFAULT_PYPI_DIST_ROOT = "dist"
INDEX_PYPI = "pypi"
INDEX_TEST_PYPI = "testpypi"
PYPI_INDEX_CHOICES = (INDEX_PYPI, INDEX_TEST_PYPI)
PYPI_PUBLISH_URLS = {
    INDEX_PYPI: "https://upload.pypi.org/legacy/",
    INDEX_TEST_PYPI: "https://test.pypi.org/legacy/",
}
PYPI_CHECK_URLS = {
    INDEX_PYPI: "https://pypi.org/simple/",
    INDEX_TEST_PYPI: "https://test.pypi.org/simple/",
}
REQUIRES_DIST_HEADER = "Requires-Dist"
WHEEL_METADATA_SUFFIX = ".dist-info/METADATA"
REQUIREMENT_NAME_PATTERN = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
DEFAULT_PYPI_PROJECTS = (
    "opamp-shared",
    "opamp-server",
    "config-service",
    "catalog-service",
    "client-config-generator-service",
    "svr-credentials-manager-service",
    "opamp-consumer",
    "opamp-suite",
)


@dataclass(frozen=True)
class PyPIPublishOptions:
    """Describe one validated PyPI wheel publication.

    Attributes
    ----------
    dist_root:
        Repository-relative or absolute directory searched recursively for wheels.
    index:
        Named public index destination, either PyPI or TestPyPI.
    allow_partial:
        Whether publication may omit packages from the standard release set.
    dry_run:
        Whether ``uv publish`` should validate without uploading files.

    """

    dist_root: str = DEFAULT_PYPI_DIST_ROOT
    index: str = INDEX_TEST_PYPI
    allow_partial: bool = False
    dry_run: bool = False


def publish_wheels_to_pypi(runtime: Any, options: PyPIPublishOptions) -> bool:
    """Validate the local wheel set and publish it with ``uv``.

    Parameters
    ----------
    runtime:
        Command runtime used for repository paths, subprocesses, and DEBUG output.
    options:
        Wheel discovery, destination, completeness, and dry-run settings.

    """
    if options.index not in PYPI_INDEX_CHOICES:
        raise RuntimeError(f"Unsupported Python package index: {options.index}")

    wheels = discover_latest_wheels(runtime.repo_root, options.dist_root)
    selected_by_name = {_normalize_project_name(wheel.project_name): wheel for wheel in wheels}
    _validate_expected_projects(selected_by_name, allow_partial=options.allow_partial)
    _validate_first_party_dependency_closure(selected_by_name)

    selected_wheels = sorted(
        selected_by_name.values(), key=lambda wheel: wheel.project_name.lower()
    )
    for wheel in selected_wheels:
        runtime.info(
            "DEBUG: PyPI candidate "
            f"project={wheel.project_name} version={wheel.version} path={wheel.path}"
        )

    command = [
        "uv",
        "publish",
        "--publish-url",
        PYPI_PUBLISH_URLS[options.index],
        "--check-url",
        PYPI_CHECK_URLS[options.index],
        "--trusted-publishing",
        "automatic",
    ]
    if options.dry_run:
        command.append("--dry-run")
    command.extend(str(wheel.path) for wheel in selected_wheels)

    publish_environment = dict(os.environ)
    runtime.run(command, cwd=runtime.repo_root, env=publish_environment)
    runtime.info(
        "PyPI publication "
        f"{'validation' if options.dry_run else 'upload'} complete: {options.index}"
    )
    return False


def _validate_expected_projects(
    selected_by_name: dict[str, WheelArtifact],
    *,
    allow_partial: bool,
) -> None:
    """Require the standard first-party release set unless partial mode is explicit.

    Parameters
    ----------
    selected_by_name:
        Normalized project names mapped to their selected wheel artifacts.
    allow_partial:
        Whether missing standard release projects should be accepted.

    """
    if allow_partial:
        return
    missing_projects = sorted(set(DEFAULT_PYPI_PROJECTS) - set(selected_by_name))
    if missing_projects:
        raise RuntimeError(
            "PyPI wheel set is incomplete; missing projects: " + ", ".join(missing_projects)
        )


def _validate_first_party_dependency_closure(
    selected_by_name: dict[str, WheelArtifact],
) -> None:
    """Ensure selected wheels include every referenced first-party distribution.

    Parameters
    ----------
    selected_by_name:
        Normalized project names mapped to their selected wheel artifacts.

    """
    required_project_names = set(DEFAULT_PYPI_PROJECTS)
    missing_dependencies: list[str] = []
    for wheel in selected_by_name.values():
        for dependency_name in _read_wheel_dependency_names(wheel.path):
            normalized_dependency = _normalize_project_name(dependency_name)
            if (
                normalized_dependency in required_project_names
                and normalized_dependency not in selected_by_name
            ):
                missing_dependencies.append(
                    f"{wheel.project_name} requires {normalized_dependency}"
                )
    if missing_dependencies:
        raise RuntimeError(
            "PyPI wheel dependency closure is incomplete: "
            + "; ".join(sorted(missing_dependencies))
        )


def _read_wheel_dependency_names(wheel_path: Path) -> set[str]:
    """Read normalized dependency project names from one wheel's metadata.

    Parameters
    ----------
    wheel_path:
        Wheel archive whose ``Requires-Dist`` headers should be inspected.

    """
    with zipfile.ZipFile(wheel_path) as wheel_archive:
        metadata_names = [
            name for name in wheel_archive.namelist() if name.endswith(WHEEL_METADATA_SUFFIX)
        ]
        if len(metadata_names) != 1:
            raise RuntimeError(f"Wheel must contain exactly one metadata file: {wheel_path}")
        metadata = BytesParser(policy=policy.default).parsebytes(
            wheel_archive.read(metadata_names[0])
        )

    dependency_names: set[str] = set()
    for requirement in metadata.get_all(REQUIRES_DIST_HEADER, []):
        match = REQUIREMENT_NAME_PATTERN.match(str(requirement))
        if match is not None:
            dependency_names.add(match.group(1))
    return dependency_names


def _normalize_project_name(project_name: str) -> str:
    """Return the PEP 503-style comparison form for a project name.

    Parameters
    ----------
    project_name:
        Distribution name read from wheel metadata or a dependency header.

    """
    return re.sub(r"[-_.]+", "-", str(project_name).strip()).lower()
