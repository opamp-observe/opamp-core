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

"""Build display-safe version details for installed provider custom commands."""

from __future__ import annotations

import re
from importlib import metadata

from opamp_provider.commands import get_command_metadata
from opamp_provider.custom_commands import installed_commands

COMMAND_NAME_KEY = "name"
COMMAND_VERSION_KEY = "version"
METADATA_DISPLAY_NAME_KEY = "displayname"
METADATA_OPERATION_KEY = "operation"
PROVIDER_PACKAGE_ROOT = "opamp_provider"
VERSION_TEXT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")


def _safe_version(value: object) -> str:
    """Accept a compact version token without filesystem path separators.

    Parameters
    ----------
    value:
        Optional extension-supplied version to validate for display.
    """
    candidate = str(value or "").strip()
    return candidate if VERSION_TEXT_PATTERN.fullmatch(candidate) else ""


def _distribution_version_for_module(module_name: str) -> str | None:
    """Return a package version for an unambiguous external command module.

    Parameters
    ----------
    module_name:
        Command implementation module used to locate its installed distribution.
    """
    package_root = module_name.partition(".")[0]
    if not package_root or package_root == PROVIDER_PACKAGE_ROOT:
        return None
    distributions = metadata.packages_distributions().get(package_root, [])
    if len(distributions) != 1:
        return None
    try:
        return _safe_version(metadata.version(distributions[0])) or None
    except metadata.PackageNotFoundError:
        return None


def custom_command_summaries(core_version: str) -> list[dict[str, str]]:
    """List installed custom commands and use the core version when none is available.

    Parameters
    ----------
    core_version:
        Provider product version used for built-in or unversioned commands.
    """
    external_commands = installed_commands()
    summaries: list[dict[str, str]] = []
    for command_metadata in get_command_metadata(custom_only=True):
        operation = str(command_metadata.get(METADATA_OPERATION_KEY, ""))
        name = str(command_metadata.get(METADATA_DISPLAY_NAME_KEY, operation)).strip()
        command = external_commands.get(operation)
        command_version = ""
        if command is not None:
            command_version = _safe_version(getattr(command, "version", None))
            if not command_version:
                command_version = _distribution_version_for_module(
                    type(command).__module__
                ) or ""
        summaries.append(
            {
                COMMAND_NAME_KEY: name or operation,
                COMMAND_VERSION_KEY: command_version or core_version,
            }
        )
    return summaries
