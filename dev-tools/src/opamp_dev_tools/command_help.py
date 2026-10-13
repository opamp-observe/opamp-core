# Copyright 2026 mp3monster.org
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

"""Render a command hierarchy from the developer CLI argparse graph."""

from __future__ import annotations

import argparse
from collections.abc import Mapping

DEFAULT_PROGRAM_NAME = "opamp-dev-cli"
HIERARCHY_TITLE = "Command hierarchy:"


def render_command_hierarchy(
    parser: argparse.ArgumentParser,
    *,
    program_name: str = DEFAULT_PROGRAM_NAME,
) -> str:
    """Return a tree containing every registered command and description.

    Parameters
    ----------
    parser:
        Fully configured argument parser whose subcommands are traversed.
    program_name:
        Installed command name displayed at the root of the hierarchy.

    """
    lines = [HIERARCHY_TITLE, program_name]
    subparsers = _subparser_choices(parser)
    descriptions = _subparser_descriptions(parser)
    _append_command_nodes(
        lines,
        subparsers,
        descriptions=descriptions,
        prefix="",
    )
    return "\n".join(lines)


def _append_command_nodes(
    lines: list[str],
    commands: Mapping[str, argparse.ArgumentParser],
    *,
    descriptions: Mapping[str, str],
    prefix: str,
) -> None:
    """Append one command level and recursively render its child parsers.

    Parameters
    ----------
    lines:
        Mutable output lines receiving the hierarchy.
    commands:
        Ordered command-name to parser mapping for the current level.
    descriptions:
        Help descriptions associated with the current command names.
    prefix:
        Tree indentation and ancestor connector prefix.

    """
    command_items = list(commands.items())
    for command_index, (command_name, command_parser) in enumerate(command_items):
        is_last_command = command_index == len(command_items) - 1
        connector = "`-- " if is_last_command else "|-- "
        description = descriptions.get(command_name, "").strip()
        description_suffix = f" - {description}" if description else ""
        lines.append(f"{prefix}{connector}{command_name}{description_suffix}")
        child_prefix = f"{prefix}{'    ' if is_last_command else '|   '}"
        _append_command_nodes(
            lines,
            _subparser_choices(command_parser),
            descriptions=_subparser_descriptions(command_parser),
            prefix=child_prefix,
        )


def _subparser_choices(
    parser: argparse.ArgumentParser,
) -> Mapping[str, argparse.ArgumentParser]:
    """Return child command parsers registered on one parser.

    Parameters
    ----------
    parser:
        Parser inspected for an argparse subparser action.

    """
    action = _subparser_action(parser)
    return action.choices if action is not None else {}


def _subparser_descriptions(parser: argparse.ArgumentParser) -> dict[str, str]:
    """Return help descriptions registered for one subcommand level.

    Parameters
    ----------
    parser:
        Parser inspected for subcommand pseudo-actions and their help text.

    """
    action = _subparser_action(parser)
    if action is None:
        return {}
    return {
        choice.dest: str(choice.help or "")
        for choice in action._choices_actions  # pylint: disable=protected-access
    }


def _subparser_action(
    parser: argparse.ArgumentParser,
) -> argparse._SubParsersAction | None:  # pylint: disable=protected-access
    """Return the subparser action owned by a parser, when present.

    Parameters
    ----------
    parser:
        Parser whose registered actions are inspected.

    """
    for action in parser._actions:  # pylint: disable=protected-access
        if isinstance(action, argparse._SubParsersAction):  # pylint: disable=protected-access
            return action
    return None
