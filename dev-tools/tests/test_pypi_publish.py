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

"""Tests for validated PyPI publication through uv."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from opamp_dev_tools import pypi_publish

WHEEL_VERSION = "0.6.0"
EXPECTED_DEFAULT_PYPI_PROJECTS = {
    "catalog-service",
    "client-config-generator-service",
    "config-service",
    "opamp-cli",
    "opamp-consumer",
    "opamp-consumer-sim",
    "opamp-server",
    "opamp-shared",
    "opamp-suite",
    "svr-credentials-manager-service",
}


class _FakeRuntime:
    """Capture PyPI publication commands and DEBUG messages.

    Attributes
    ----------
    repo_root:
        Temporary repository root containing wheel artifacts.
    commands:
        Commands delegated to the process runner.
    messages:
        Informational output emitted by the publisher.

    """

    def __init__(self, repo_root: Path) -> None:
        """Initialize capture state for one temporary repository.

        Parameters
        ----------
        repo_root:
            Temporary repository root containing test artifacts.

        """
        self.repo_root = repo_root
        self.commands: list[list[str]] = []
        self.messages: list[str] = []

    def info(self, message: str) -> None:
        """Capture one informational message.

        Parameters
        ----------
        message:
            Publisher message to retain for assertions.

        """
        self.messages.append(message)

    def run(
        self,
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
    ) -> None:
        """Capture one uv command without accessing an external index.

        Parameters
        ----------
        command:
            Complete uv publication command.
        cwd:
            Working directory selected for publication.
        env:
            Sanitized process environment passed to uv.

        """
        assert cwd == self.repo_root
        assert isinstance(env, dict)
        self.commands.append(command)


def test_default_project_set_matches_release_distributions() -> None:
    """Keep publication validation aligned with the complete release build."""
    assert set(pypi_publish.DEFAULT_PYPI_PROJECTS) == EXPECTED_DEFAULT_PYPI_PROJECTS


def _write_wheel(
    wheel_path: Path,
    *,
    project_name: str,
    dependencies: tuple[str, ...] = (),
) -> None:
    """Create a minimal wheel containing project and dependency metadata.

    Parameters
    ----------
    wheel_path:
        Destination archive path.
    project_name:
        Distribution name placed in the metadata.
    dependencies:
        ``Requires-Dist`` header values placed in the metadata.

    """
    wheel_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_lines = [
        "Metadata-Version: 2.1",
        f"Name: {project_name}",
        f"Version: {WHEEL_VERSION}",
    ]
    metadata_lines.extend(f"Requires-Dist: {dependency}" for dependency in dependencies)
    metadata_path = f"{project_name}-{WHEEL_VERSION}.dist-info/METADATA"
    with zipfile.ZipFile(wheel_path, mode="w") as wheel_archive:
        wheel_archive.writestr(metadata_path, "\n".join(metadata_lines) + "\n")


def test_publish_dry_run_validates_and_delegates_to_uv(tmp_path: Path) -> None:
    """Verify a partial dry run selects explicit wheels and TestPyPI endpoints.

    Parameters
    ----------
    tmp_path:
        Pytest-managed directory containing the synthetic wheel set.
    """
    shared_wheel = tmp_path / "dist" / "opamp_shared-0.6.0-py3-none-any.whl"
    provider_wheel = tmp_path / "dist" / "opamp_server-0.6.0-py3-none-any.whl"
    _write_wheel(shared_wheel, project_name="opamp-shared")
    _write_wheel(
        provider_wheel,
        project_name="opamp-server",
        dependencies=("opamp-shared==0.6.0",),
    )
    runtime = _FakeRuntime(tmp_path)

    issues_found = pypi_publish.publish_wheels_to_pypi(
        runtime,
        pypi_publish.PyPIPublishOptions(
            allow_partial=True,
            dry_run=True,
        ),
    )

    assert issues_found is False
    command = runtime.commands[0]
    assert command[:2] == ["uv", "publish"]
    assert "--dry-run" in command
    assert pypi_publish.PYPI_PUBLISH_URLS[pypi_publish.INDEX_TEST_PYPI] in command
    assert str(shared_wheel.resolve()) in command
    assert str(provider_wheel.resolve()) in command
    assert any("DEBUG: PyPI candidate" in message for message in runtime.messages)


def test_publish_requires_complete_standard_set_by_default(tmp_path: Path) -> None:
    """Verify the safe default rejects an incomplete first-party release set.

    Parameters
    ----------
    tmp_path:
        Pytest-managed directory containing an intentionally incomplete wheel set.
    """
    _write_wheel(
        tmp_path / "dist" / "opamp_shared-0.6.0-py3-none-any.whl",
        project_name="opamp-shared",
    )

    with pytest.raises(RuntimeError, match="wheel set is incomplete"):
        pypi_publish.publish_wheels_to_pypi(
            _FakeRuntime(tmp_path),
            pypi_publish.PyPIPublishOptions(dry_run=True),
        )


def test_partial_publish_requires_first_party_dependency_closure(tmp_path: Path) -> None:
    """Verify selected wheels cannot reference an omitted first-party dependency.

    Parameters
    ----------
    tmp_path:
        Pytest-managed directory containing a wheel with an unresolved local dependency.
    """
    _write_wheel(
        tmp_path / "dist" / "opamp_server-0.6.0-py3-none-any.whl",
        project_name="opamp-server",
        dependencies=("opamp-shared==0.6.0",),
    )

    with pytest.raises(RuntimeError, match="dependency closure is incomplete"):
        pypi_publish.publish_wheels_to_pypi(
            _FakeRuntime(tmp_path),
            pypi_publish.PyPIPublishOptions(
                allow_partial=True,
                dry_run=True,
            ),
        )
