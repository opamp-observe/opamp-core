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

"""Tests for parser-derived developer CLI hierarchy rendering."""

from __future__ import annotations

import argparse

from opamp_dev_tools.command_help import render_command_hierarchy


def test_render_command_hierarchy_includes_nested_commands_and_help() -> None:
    """Hierarchy output should preserve parser order, nesting, and descriptions."""
    parser = argparse.ArgumentParser()
    root_subparsers = parser.add_subparsers(dest="command", required=True)
    alpha_parser = root_subparsers.add_parser("alpha", help="Alpha operations")
    alpha_subparsers = alpha_parser.add_subparsers(dest="alpha_command", required=True)
    alpha_subparsers.add_parser("child", help="Child operation")
    root_subparsers.add_parser("beta")

    hierarchy = render_command_hierarchy(parser, program_name="example-cli")

    assert hierarchy == (
        "Command hierarchy:\n"
        "example-cli\n"
        "|-- alpha - Alpha operations\n"
        "|   `-- child - Child operation\n"
        "`-- beta"
    )


def test_render_command_hierarchy_supports_a_parser_without_commands() -> None:
    """A parser without subcommands should still render a useful root."""
    parser = argparse.ArgumentParser()

    hierarchy = render_command_hierarchy(parser)

    assert hierarchy == "Command hierarchy:\nopamp-dev-cli"
