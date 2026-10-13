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

"""Discover, validate, register, and execute component-owned developer tools."""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .runtime import CommandRuntime

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

MANIFEST_FILENAME = "opamp_dev_cli_tools.json"
MANIFEST_RELATIVE_PATH = Path("dev-tools") / MANIFEST_FILENAME
SUPPORTED_SCHEMA_VERSION = 1
SUPPORTED_ACTIONS = frozenset({"append", "store", "store_true"})
SUPPORTED_VALUE_TYPES = frozenset({"integer", "string"})
DEFAULT_OPERATION_ID = "component-default"
COMMAND_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
DESTINATION_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

KEY_ACTION = "action"
KEY_ALLOW_NONE = "allow_none"
KEY_ARGUMENTS = "arguments"
KEY_CHOICES = "choices"
KEY_COMMAND = "command"
KEY_COMMAND_GROUP = "command_group"
KEY_DEFAULT = "default"
KEY_DESCRIPTION = "description"
KEY_DESTINATION = "destination"
KEY_EXCLUSIVE_GROUP = "exclusive_group"
KEY_EXCLUSIVE_GROUPS = "exclusive_groups"
KEY_FLAGS = "flags"
KEY_GUIDED_FOR = "guided_for"
KEY_HELP = "help"
KEY_ID = "id"
KEY_LABEL = "label"
KEY_NONE_LABEL = "none_label"
KEY_PROMPT = "prompt"
KEY_REQUIRED = "required"
KEY_SCHEMA_VERSION = "schema_version"
KEY_SCRIPT = "script"
KEY_SELECTION_LABEL = "selection_label"
KEY_TOOLS = "tools"
KEY_VALUE_TYPE = "value_type"

NAMESPACE_TOOL_ATTRIBUTE = "_component_tool_spec"


@dataclass(frozen=True)
class ComponentToolArgument:  # pylint: disable=too-many-instance-attributes
    """Describe one command-line argument exported by a component tool.

    Attributes
    ----------
    destination:
        Namespace attribute populated by argparse.
    flags:
        Command-line option names accepted for the argument.
    action:
        Supported argparse-style storage action.
    help_text:
        Contextual help shown for the argument.
    value_type:
        Scalar conversion applied by argparse.
    choices:
        Optional accepted scalar values.
    required:
        Whether direct command-line use must provide the argument.
    prompt:
        Guided-mode question for the argument.
    default:
        Guided-mode default. Direct mode leaves omitted values to the component script.
    exclusive_group:
        Optional identifier for a mutually exclusive argument group.
    selection_label:
        Guided-mode label used when choosing an exclusive operation.
    guided_for:
        Optional operation identifiers for which guided mode asks this argument.
    """

    destination: str
    flags: tuple[str, ...]
    action: str
    help_text: str
    value_type: str
    choices: tuple[str, ...]
    required: bool
    prompt: str
    default: str | bool | int | None
    exclusive_group: str
    selection_label: str
    guided_for: tuple[str, ...]


@dataclass(frozen=True)
class ComponentToolExclusiveGroup:
    """Describe guided and argparse behavior for mutually exclusive arguments.

    Attributes
    ----------
    identifier:
        Stable group identifier referenced by argument specifications.
    prompt:
        Guided-mode menu title for the group.
    allow_none:
        Whether no group argument may be selected.
    none_label:
        Guided-mode explanation of the no-selection behavior.
    """

    identifier: str
    prompt: str
    allow_none: bool
    none_label: str


@dataclass(frozen=True)
class ComponentToolSpec:  # pylint: disable=too-many-instance-attributes
    """Describe one validated component-owned command exposed by the developer CLI.

    Attributes
    ----------
    identifier:
        Component-scoped stable identifier used for diagnostics.
    component_name:
        Repository component directory that published the tool.
    command_group:
        Existing developer CLI root group receiving the command.
    command:
        Subcommand registered beneath the command group.
    description:
        Human-readable command help.
    script_path:
        Validated absolute path to the component-owned Python entry point.
    arguments:
        Validated command argument definitions.
    exclusive_groups:
        Validated mutually exclusive group definitions.
    """

    identifier: str
    component_name: str
    command_group: str
    command: str
    description: str
    script_path: Path
    arguments: tuple[ComponentToolArgument, ...]
    exclusive_groups: tuple[ComponentToolExclusiveGroup, ...]


def discover_component_tools(repo_root: Path) -> list[ComponentToolSpec]:
    """Return valid component tool specifications found below the repository root.

    Parameters
    ----------
    repo_root:
        Repository whose first-level components may publish developer-tool manifests.

    """
    discovered_tools: list[ComponentToolSpec] = []
    try:
        component_paths = sorted(repo_root.iterdir())
    except OSError as exc:
        LOGGER.debug("unable to enumerate component tools root=%s error=%s", repo_root, exc)
        return discovered_tools
    command_paths: set[tuple[str, str]] = set()
    for component_path in component_paths:
        manifest_path = component_path / MANIFEST_RELATIVE_PATH
        try:
            if not component_path.is_dir() or not manifest_path.is_file():
                continue
            manifest_tools = _load_manifest(component_path, manifest_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            LOGGER.debug(
                "ignored invalid component tool manifest path=%s error=%s",
                manifest_path,
                exc,
            )
            continue
        for tool in manifest_tools:
            command_path = (tool.command_group, tool.command)
            if command_path in command_paths:
                LOGGER.debug(
                    "ignored duplicate component command group=%s command=%s component=%s",
                    tool.command_group,
                    tool.command,
                    tool.component_name,
                )
                continue
            command_paths.add(command_path)
            discovered_tools.append(tool)
    return discovered_tools


def tools_for_group(
    tools: list[ComponentToolSpec],
    command_group: str,
) -> list[ComponentToolSpec]:
    """Return component tools registered for one root command group.

    Parameters
    ----------
    tools:
        Discovered component tool specifications.
    command_group:
        Root CLI command group to select.

    """
    return [tool for tool in tools if tool.command_group == command_group]


def register_component_tool_parser(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
    tool: ComponentToolSpec,
) -> None:
    """Register one validated component tool beneath an argparse subparser collection.

    Parameters
    ----------
    subparsers:
        Argparse subparser action that owns the component command.
    tool:
        Validated tool specification to register.

    """
    tool_parser = subparsers.add_parser(tool.command, help=tool.description)
    tool_parser.set_defaults(**{NAMESPACE_TOOL_ATTRIBUTE: tool})
    exclusive_parsers = {
        group.identifier: tool_parser.add_mutually_exclusive_group(
            required=not group.allow_none
        )
        for group in tool.exclusive_groups
    }
    for argument in tool.arguments:
        argument_owner = exclusive_parsers.get(argument.exclusive_group, tool_parser)
        argument_options: dict[str, Any] = {
            "action": argument.action,
            "dest": argument.destination,
            "default": argparse.SUPPRESS,
            "help": argument.help_text,
        }
        if argument.action not in {"store_true"}:
            argument_options["type"] = int if argument.value_type == "integer" else str
        if argument.choices:
            argument_options["choices"] = argument.choices
        if argument.required and not argument.exclusive_group:
            argument_options["required"] = True
        argument_owner.add_argument(*argument.flags, **argument_options)


def component_tool_from_args(args: argparse.Namespace) -> ComponentToolSpec | None:
    """Return the discovered tool attached to parsed arguments, when present.

    Parameters
    ----------
    args:
        Parsed developer CLI namespace.

    """
    tool = getattr(args, NAMESPACE_TOOL_ATTRIBUTE, None)
    return tool if isinstance(tool, ComponentToolSpec) else None


def run_component_tool(
    runtime: CommandRuntime,
    *,
    python_exe: str,
    args: argparse.Namespace,
    tool: ComponentToolSpec,
) -> bool:
    """Run one component-owned Python tool with validated parsed arguments.

    Parameters
    ----------
    runtime:
        Shared command runtime used for subprocess execution and diagnostics.
    python_exe:
        Python interpreter selected by the global CLI option.
    args:
        Parsed namespace containing component argument values.
    tool:
        Validated component tool specification to execute.

    """
    command = [python_exe, str(tool.script_path)]
    for argument in tool.arguments:
        if not hasattr(args, argument.destination):
            continue
        value = getattr(args, argument.destination)
        if argument.action == "store_true":
            if value:
                command.append(argument.flags[0])
            continue
        values = value if argument.action == "append" else [value]
        for argument_value in values:
            command.extend([argument.flags[0], str(argument_value)])
    runtime.run(command, cwd=runtime.repo_root)
    return False


def _load_manifest(component_path: Path, manifest_path: Path) -> list[ComponentToolSpec]:
    """Load and validate one component-owned manifest.

    Parameters
    ----------
    component_path:
        Absolute or repository-relative component directory owning the manifest.
    manifest_path:
        JSON manifest path to load.

    """
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    root_payload = _required_mapping(payload, "manifest root")
    if root_payload.get(KEY_SCHEMA_VERSION) != SUPPORTED_SCHEMA_VERSION:
        raise ValueError("unsupported component tool manifest schema version")
    raw_tools = root_payload.get(KEY_TOOLS)
    if not isinstance(raw_tools, list):
        raise ValueError("component tool manifest 'tools' must be an array")
    tools = [
        _parse_tool(component_path.resolve(), _required_mapping(raw_tool, "tool"))
        for raw_tool in raw_tools
    ]
    command_paths = [(tool.command_group, tool.command) for tool in tools]
    if len(command_paths) != len(set(command_paths)):
        raise ValueError("component tool manifest contains duplicate command paths")
    return tools


def _parse_tool(  # pylint: disable=too-many-locals
    component_path: Path,
    payload: dict[str, Any],
) -> ComponentToolSpec:
    """Validate one raw tool mapping and return its immutable representation.

    Parameters
    ----------
    component_path:
        Resolved component directory used to constrain the entry-point path.
    payload:
        Raw JSON object describing one component tool.

    """
    identifier = _required_name(payload, KEY_ID, DESTINATION_NAME_PATTERN)
    command_group = _required_name(payload, KEY_COMMAND_GROUP, COMMAND_NAME_PATTERN)
    command = _required_name(payload, KEY_COMMAND, COMMAND_NAME_PATTERN)
    description = _required_string(payload, KEY_DESCRIPTION)
    script_value = _required_string(payload, KEY_SCRIPT)
    script_path = (component_path / script_value).resolve()
    if (
        not script_path.is_relative_to(component_path)
        or script_path.suffix.lower() != ".py"
        or not script_path.is_file()
    ):
        raise ValueError(
            f"component tool script is missing or outside its component: {script_value}"
        )
    raw_groups = payload.get(KEY_EXCLUSIVE_GROUPS, [])
    raw_arguments = payload.get(KEY_ARGUMENTS, [])
    if not isinstance(raw_groups, list) or not isinstance(raw_arguments, list):
        raise ValueError("tool arguments and exclusive_groups must be arrays")
    exclusive_groups = tuple(
        _parse_exclusive_group(_required_mapping(raw_group, "exclusive group"))
        for raw_group in raw_groups
    )
    arguments = tuple(
        _parse_argument(_required_mapping(raw_argument, "argument"))
        for raw_argument in raw_arguments
    )
    group_ids = {group.identifier for group in exclusive_groups}
    if len(group_ids) != len(exclusive_groups):
        raise ValueError("tool contains duplicate exclusive group identifiers")
    has_unknown_group = any(
        argument.exclusive_group not in group_ids
        for argument in arguments
        if argument.exclusive_group
    )
    if has_unknown_group:
        raise ValueError("tool argument references an unknown exclusive group")
    destinations = [argument.destination for argument in arguments]
    if len(destinations) != len(set(destinations)):
        raise ValueError("tool contains duplicate argument destinations")
    flags = [flag for argument in arguments for flag in argument.flags]
    if len(flags) != len(set(flags)):
        raise ValueError("tool contains duplicate argument flags")
    operation_ids = {DEFAULT_OPERATION_ID, *destinations}
    if any(
        operation_id not in operation_ids
        for argument in arguments
        for operation_id in argument.guided_for
    ):
        raise ValueError("tool argument guided_for references an unknown operation")
    return ComponentToolSpec(
        identifier=identifier,
        component_name=component_path.name,
        command_group=command_group,
        command=command,
        description=description,
        script_path=script_path,
        arguments=arguments,
        exclusive_groups=exclusive_groups,
    )


def _parse_exclusive_group(payload: dict[str, Any]) -> ComponentToolExclusiveGroup:
    """Validate one mutually exclusive argument-group definition.

    Parameters
    ----------
    payload:
        Raw JSON object describing the group.

    """
    return ComponentToolExclusiveGroup(
        identifier=_required_name(payload, KEY_ID, DESTINATION_NAME_PATTERN),
        prompt=_required_string(payload, KEY_PROMPT),
        allow_none=_optional_bool(payload, KEY_ALLOW_NONE, default=False),
        none_label=str(payload.get(KEY_NONE_LABEL, "Use component default")),
    )


def _parse_argument(payload: dict[str, Any]) -> ComponentToolArgument:
    """Validate one command argument definition.

    Parameters
    ----------
    payload:
        Raw JSON object describing the argument.

    """
    destination = _required_name(payload, KEY_DESTINATION, DESTINATION_NAME_PATTERN)
    raw_flags = payload.get(KEY_FLAGS)
    if (
        not isinstance(raw_flags, list)
        or not raw_flags
        or any(not isinstance(flag, str) or not flag.startswith("--") for flag in raw_flags)
    ):
        raise ValueError(f"argument '{destination}' flags must be non-empty long options")
    action = str(payload.get(KEY_ACTION, "store"))
    value_type = str(payload.get(KEY_VALUE_TYPE, "string"))
    if action not in SUPPORTED_ACTIONS:
        raise ValueError(f"argument '{destination}' has unsupported action '{action}'")
    if value_type not in SUPPORTED_VALUE_TYPES:
        raise ValueError(f"argument '{destination}' has unsupported value type '{value_type}'")
    raw_choices = payload.get(KEY_CHOICES, [])
    if not isinstance(raw_choices, list) or any(
        not isinstance(choice, str) for choice in raw_choices
    ):
        raise ValueError(f"argument '{destination}' choices must be strings")
    raw_guided_for = payload.get(KEY_GUIDED_FOR, [])
    if not isinstance(raw_guided_for, list) or any(
        not isinstance(operation_id, str) for operation_id in raw_guided_for
    ):
        raise ValueError(f"argument '{destination}' guided_for must contain strings")
    return ComponentToolArgument(
        destination=destination,
        flags=tuple(raw_flags),
        action=action,
        help_text=_required_string(payload, KEY_HELP),
        value_type=value_type,
        choices=tuple(raw_choices),
        required=_optional_bool(payload, KEY_REQUIRED, default=False),
        prompt=str(payload.get(KEY_PROMPT, destination.replace("_", " ").capitalize())),
        default=payload.get(KEY_DEFAULT),
        exclusive_group=str(payload.get(KEY_EXCLUSIVE_GROUP, "")),
        selection_label=str(payload.get(KEY_SELECTION_LABEL, "")),
        guided_for=tuple(raw_guided_for),
    )


def _required_mapping(value: Any, label: str) -> dict[str, Any]:
    """Return a JSON-object value or raise a descriptive validation error.

    Parameters
    ----------
    value:
        Candidate mapping value.
    label:
        Human-readable location used in validation errors.

    """
    if not isinstance(value, dict):
        raise ValueError(f"component tool {label} must be an object")
    return value


def _required_string(payload: dict[str, Any], key: str) -> str:
    """Return one required non-empty string from a manifest mapping.

    Parameters
    ----------
    payload:
        Manifest mapping containing the value.
    key:
        String key whose value is required.

    """
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"component tool field '{key}' must be a non-empty string")
    return value.strip()


def _required_name(
    payload: dict[str, Any],
    key: str,
    pattern: re.Pattern[str],
) -> str:
    """Return one required identifier after validating its naming convention.

    Parameters
    ----------
    payload:
        Manifest mapping containing the identifier.
    key:
        String key whose identifier is required.
    pattern:
        Compiled regular expression defining accepted identifier values.

    """
    value = _required_string(payload, key)
    if pattern.fullmatch(value) is None:
        raise ValueError(f"component tool field '{key}' has invalid identifier '{value}'")
    return value


def _optional_bool(payload: dict[str, Any], key: str, *, default: bool) -> bool:
    """Return one optional boolean while rejecting truthy non-boolean values.

    Parameters
    ----------
    payload:
        Manifest mapping containing the optional value.
    key:
        String key whose value is inspected.
    default:
        Boolean returned when the key is absent.

    """
    value = payload.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"component tool field '{key}' must be a boolean")
    return value
