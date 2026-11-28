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

"""Version source and installed custom-command display tests."""

from __future__ import annotations

from importlib import metadata
from pathlib import Path

from opamp_provider import component_version, provider_version
from opamp_provider.provider_version import (
    COMMAND_NAME_KEY,
    COMMAND_VERSION_KEY,
    METADATA_DISPLAY_NAME_KEY,
    METADATA_OPERATION_KEY,
)

CORE_VERSION = "0.8.0"
EXTERNAL_VERSION = "2.4.1"
EXPLICIT_VERSION = "3.0.2"
EXTERNAL_DISTRIBUTION = "example-command-package"


def test_product_version_prefers_version_bump_source(tmp_path: Path, monkeypatch) -> None:
    """Use pyproject metadata so an editable source checkout follows version bumps."""
    project_path = tmp_path / "pyproject.toml"
    project_path.write_text(
        '[project]\nname = "opamp-server"\nversion = "0.8.0"\n', encoding="utf-8"
    )
    monkeypatch.setattr(component_version, "_SOURCE_PROJECT_PATH", project_path)
    monkeypatch.setattr(component_version.metadata, "version", lambda _name: "0.6.0")

    assert component_version.product_version_text() == CORE_VERSION


def test_product_version_uses_installed_metadata_without_source(tmp_path: Path, monkeypatch) -> None:
    """Read wheel metadata when the source pyproject is not deployed."""
    monkeypatch.setattr(component_version, "_SOURCE_PROJECT_PATH", tmp_path / "missing.toml")
    monkeypatch.setattr(component_version.metadata, "version", lambda _name: CORE_VERSION)

    assert component_version.product_version_text() == CORE_VERSION


def test_product_version_reports_unknown_without_package(tmp_path: Path, monkeypatch) -> None:
    """Keep the tab usable when neither source nor wheel metadata exists."""
    monkeypatch.setattr(component_version, "_SOURCE_PROJECT_PATH", tmp_path / "missing.toml")

    def missing_distribution(distribution_name: str) -> str:
        """Model a missing distribution for the requested package name."""
        raise metadata.PackageNotFoundError(distribution_name)

    monkeypatch.setattr(component_version.metadata, "version", missing_distribution)
    assert component_version.product_version_text() == "unknown"


class ExplicitVersionCommand:
    """Represent an extension with its own command-specific version."""

    version = EXPLICIT_VERSION  # Version supplied directly by the extension.


class DistributionVersionCommand:
    """Represent an extension whose package supplies its version."""

    __module__ = "example_command.commands"  # Module resolved to the test distribution.


class UnversionedCommand:
    """Represent an extension without usable package metadata."""

    __module__ = "unknown_command.commands"  # Module absent from distribution metadata.


class PathVersionCommand:
    """Represent an extension that mistakenly provides a filesystem path."""

    version = "C:\\packages\\dependency"  # Invalid display version rejected by the tab.


def test_custom_command_summaries_resolve_version_precedence(monkeypatch) -> None:
    """Prefer command version, then distribution version, then core version."""
    command_rows = [
        {METADATA_OPERATION_KEY: "built-in", METADATA_DISPLAY_NAME_KEY: "Built In"},
        {METADATA_OPERATION_KEY: "explicit", METADATA_DISPLAY_NAME_KEY: "Explicit"},
        {METADATA_OPERATION_KEY: "distributed", METADATA_DISPLAY_NAME_KEY: "Distributed"},
        {METADATA_OPERATION_KEY: "unversioned", METADATA_DISPLAY_NAME_KEY: "Unversioned"},
        {METADATA_OPERATION_KEY: "path", METADATA_DISPLAY_NAME_KEY: "Path Version"},
    ]
    commands = {
        "explicit": ExplicitVersionCommand(),
        "distributed": DistributionVersionCommand(),
        "unversioned": UnversionedCommand(),
        "path": PathVersionCommand(),
    }
    monkeypatch.setattr(provider_version, "get_command_metadata", lambda **_kwargs: command_rows)
    monkeypatch.setattr(provider_version, "installed_commands", lambda: commands)
    monkeypatch.setattr(
        provider_version.metadata,
        "packages_distributions",
        lambda: {"example_command": [EXTERNAL_DISTRIBUTION]},
    )
    monkeypatch.setattr(
        provider_version.metadata,
        "version",
        lambda distribution_name: EXTERNAL_VERSION if distribution_name == EXTERNAL_DISTRIBUTION else "",
    )

    summaries = provider_version.custom_command_summaries(CORE_VERSION)

    assert summaries == [
        {COMMAND_NAME_KEY: "Built In", COMMAND_VERSION_KEY: CORE_VERSION},
        {COMMAND_NAME_KEY: "Explicit", COMMAND_VERSION_KEY: EXPLICIT_VERSION},
        {COMMAND_NAME_KEY: "Distributed", COMMAND_VERSION_KEY: EXTERNAL_VERSION},
        {COMMAND_NAME_KEY: "Unversioned", COMMAND_VERSION_KEY: CORE_VERSION},
        {COMMAND_NAME_KEY: "Path Version", COMMAND_VERSION_KEY: CORE_VERSION},
    ]
    assert "example_command.commands" not in str(summaries)
    assert "dependency" not in str(summaries)


def test_command_package_version_falls_back_for_provider_or_missing_distribution(
    monkeypatch,
) -> None:
    """Avoid misreporting provider or missing package metadata as command version."""
    monkeypatch.setattr(
        provider_version.metadata,
        "packages_distributions",
        lambda: {"missing_command": [EXTERNAL_DISTRIBUTION]},
    )

    def missing_distribution(distribution_name: str) -> str:
        """Model a package that disappeared after command discovery."""
        raise metadata.PackageNotFoundError(distribution_name)

    monkeypatch.setattr(provider_version.metadata, "version", missing_distribution)
    assert provider_version._distribution_version_for_module("opamp_provider.command") is None
    assert provider_version._distribution_version_for_module("missing_command.command") is None
