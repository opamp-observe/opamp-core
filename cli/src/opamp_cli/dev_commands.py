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

"""Developer-only command workflows for the OpAMP CLI."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

try:
    from .common import _normalized_label, _slugify
    from .constants import APP_ENABLE_DEV_FEATURES_ENV, INTENT_START
except ImportError:
    from common import _normalized_label, _slugify  # type: ignore[no-redef]
    from constants import APP_ENABLE_DEV_FEATURES_ENV, INTENT_START  # type: ignore[no-redef]


def load_dev_tool_spec_from_script(
    script_path: Path,
    *,
    load_module_from_path: Callable[[str, Path], ModuleType | None],
) -> dict[str, Any] | None:
    """Load one self-described CLI dev-tool spec from a Python script."""
    if script_path.is_file() is not True:
        return None
    module_name = f"opamp_cli_dev_tool_{_slugify(script_path.stem)}"
    module = load_module_from_path(module_name, script_path)
    if module is None:
        return None

    spec_payload: Any = None
    spec_factory = getattr(module, "cli_dev_tool_spec", None)
    if callable(spec_factory):
        try:
            spec_payload = spec_factory()
        except Exception:
            return None
    elif isinstance(getattr(module, "CLI_DEV_TOOL_SPEC", None), dict):
        spec_payload = dict(getattr(module, "CLI_DEV_TOOL_SPEC"))
    if not isinstance(spec_payload, dict):
        return None

    spec = json.loads(json.dumps(spec_payload))
    spec["script_path"] = str(script_path.resolve())
    spec.setdefault("id", _slugify(str(spec.get("label") or script_path.stem)).replace("-", "_"))
    spec.setdefault("label", script_path.stem)
    spec.setdefault("description", "")
    arguments = spec.get("arguments", [])
    spec["arguments"] = arguments if isinstance(arguments, list) else []
    return spec


def prompt_dev_tool_selection(
    specs: list[dict[str, Any]],
    *,
    command_name: str,
    tool_family_label: str,
    prompt_text: Callable[[str], str],
) -> list[dict[str, Any]] | None:
    """Prompt for one or all dev-tool specs to run."""
    if not specs:
        return None
    print(f"Choose a {tool_family_label} dev utility:")
    for index, spec in enumerate(specs, start=1):
        label = str(spec.get("label") or f"Tool {index}")
        description = str(spec.get("description") or "").strip()
        print(f"  {index}. {label}")
        if description:
            print(f"     {description}")
    if len(specs) > 1:
        print(f"  {len(specs) + 1}. Run all")
    print("  0. cancel")

    while True:
        try:
            selected = prompt_text(f"{command_name}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if selected in {"0", "", "cancel", "c"}:
            return None
        if selected.isdigit():
            index = int(selected)
            if 1 <= index <= len(specs):
                return [specs[index - 1]]
            if len(specs) > 1 and index == len(specs) + 1:
                return list(specs)
        normalized = _normalized_label(selected)
        if normalized == _normalized_label("run all") and len(specs) > 1:
            return list(specs)
        for spec in specs:
            label = str(spec.get("label") or "")
            if _normalized_label(label) == normalized:
                return [spec]
        print("Please choose a valid number from the list.")


def prompt_dev_tool_arguments(
    spec: dict[str, Any],
    *,
    prompt_text: Callable[[str], str],
    parse_yes_no: Callable[[str, bool], bool | None],
) -> dict[str, Any] | None:
    """Prompt for one dev-tool spec argument set."""
    answers: dict[str, Any] = {}
    for field in spec.get("arguments", []):
        if not isinstance(field, dict):
            continue
        name = str(field.get("name") or "").strip()
        if not name:
            continue
        prompt_label = str(field.get("prompt") or name).strip()
        default = field.get("default")
        kind = str(field.get("kind") or "text").strip().lower()
        choices = [str(item) for item in field.get("choices", []) if str(item).strip()]
        required = bool(field.get("required"))
        multiple = bool(field.get("multiple"))

        while True:
            default_suffix = ""
            if kind == "bool":
                default_suffix = " [Y/n]" if bool(default) else " [y/N]"
            elif default not in {None, ""}:
                default_suffix = f" [{default}]"
            try:
                raw_value = prompt_text(f"{prompt_label}{default_suffix}: ")
            except (EOFError, KeyboardInterrupt):
                print()
                return None
            value = str(raw_value or "").strip()
            if kind == "bool":
                parsed_bool = parse_yes_no(value, bool(default))
                if parsed_bool is None:
                    print("Please answer yes or no.")
                    continue
                answers[name] = parsed_bool
                break
            if not value:
                value = str(default or "").strip()
            if required and not value:
                print("A value is required.")
                continue
            if choices and value:
                matching = next((choice for choice in choices if choice.lower() == value.lower()), None)
                if matching is None:
                    print(f"Choose one of: {', '.join(choices)}")
                    continue
                answers[name] = matching
                break
            if multiple:
                answers[name] = [item.strip() for item in value.split(",") if item.strip()]
                if required and not answers[name]:
                    print("At least one value is required.")
                    continue
                break
            answers[name] = value
            break
    return answers


def dev_tool_argv(
    spec: dict[str, Any],
    answers: dict[str, Any],
    *,
    python_executable: str = sys.executable,
) -> list[str]:
    """Build argv for one self-described dev tool."""
    script_path = Path(str(spec.get("script_path") or "")).resolve()
    argv = [python_executable, str(script_path)]
    argv.extend(str(item) for item in spec.get("fixed_args", []))
    for field in spec.get("arguments", []):
        if not isinstance(field, dict):
            continue
        name = str(field.get("name") or "").strip()
        if not name:
            continue
        value = answers.get(name)
        kind = str(field.get("kind") or "text").strip().lower()
        if kind == "bool":
            bool_value = bool(value)
            argv.extend(str(item) for item in field.get("args_when_true" if bool_value else "args_when_false", []))
            continue
        flag = str(field.get("flag") or "").strip()
        if not flag:
            continue
        if field.get("multiple"):
            for item in value or []:
                argv.extend([flag, str(item)])
            continue
        text_value = str(value or "").strip()
        if text_value:
            argv.extend([flag, text_value])
    return argv


def run_dev_tool_spec(
    spec: dict[str, Any],
    answers: dict[str, Any],
    *,
    command_text_from_args: Callable[[list[str]], str],
    repo_root: Path,
    build_exec_env: Callable[[], dict[str, str]],
    logger: Any,
) -> int:
    """Execute one configured dev-tool spec in the foreground."""
    argv = dev_tool_argv(spec, answers)
    logger.info("executing dev tool label=%s argv=%s", spec.get("label"), argv)
    print(f"Executing: {command_text_from_args(argv)}")
    completed = subprocess.run(  # noqa: S603
        argv,
        cwd=str(repo_root),
        env=build_exec_env(),
        check=False,
    )
    return int(completed.returncode)


def execute_dev_tool_workflow(
    *,
    command_name: str,
    tool_family_label: str,
    specs: list[dict[str, Any]],
    dev_features_enabled: bool,
    prompt_text: Callable[[str], str],
    parse_yes_no: Callable[[str, bool], bool | None],
    command_text_from_args: Callable[[list[str]], str],
    repo_root: Path,
    build_exec_env: Callable[[], dict[str, str]],
    logger: Any,
) -> int:
    """Prompt for and run one or more self-described developer utilities."""
    if dev_features_enabled is not True:
        print(
            f"{command_name} is only available when {APP_ENABLE_DEV_FEATURES_ENV}=true.",
            file=sys.stderr,
        )
        return 1
    if not specs:
        print(
            f"{command_name} is unavailable because the {tool_family_label} dev tool scripts could not be located.",
            file=sys.stderr,
        )
        return 1
    selected_specs = prompt_dev_tool_selection(
        specs,
        command_name=command_name,
        tool_family_label=tool_family_label,
        prompt_text=prompt_text,
    )
    if not selected_specs:
        return 0
    for spec in selected_specs:
        print(f"Configure: {spec.get('label')}")
        answers = prompt_dev_tool_arguments(
            spec,
            prompt_text=prompt_text,
            parse_yes_no=parse_yes_no,
        )
        if answers is None:
            return 0
        exit_code = run_dev_tool_spec(
            spec,
            answers,
            command_text_from_args=command_text_from_args,
            repo_root=repo_root,
            build_exec_env=build_exec_env,
            logger=logger,
        )
        if exit_code != 0:
            return exit_code
    return 0


def prompt_pid_lookup_regex(*, prompt_text: Callable[[str], str]) -> str | None:
    """Prompt for the regex used by the dev PID lookup workflow."""
    try:
        raw_value = prompt_text("Process regular expression (blank to cancel): ")
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    pattern_text = str(raw_value or "").strip()
    return pattern_text or None


def execute_dev_pid_lookup_workflow(
    *,
    command_name: str,
    dev_features_enabled: bool,
    prompt_text: Callable[[str], str],
    running_process_entries: Callable[[], tuple[bool, list[dict[str, Any]]]],
    process_entries_matching_pattern: Callable[[list[dict[str, Any]], re.Pattern[str]], list[dict[str, Any]]],
    print_pid_lookup_results: Callable[[str, list[dict[str, Any]]], None],
) -> int:
    """Prompt for a regex and report running processes that match it."""
    if dev_features_enabled is not True:
        print(
            f"{command_name} is only available when {APP_ENABLE_DEV_FEATURES_ENV}=true.",
            file=sys.stderr,
        )
        return 1
    pattern_text = prompt_pid_lookup_regex(prompt_text=prompt_text)
    if pattern_text is None:
        return 0
    try:
        pattern = re.compile(pattern_text, re.IGNORECASE)
    except re.error as exc:
        print(f"Invalid regular expression: {exc}", file=sys.stderr)
        return 1
    snapshot_ok, processes = running_process_entries()
    if snapshot_ok is not True:
        print("Unable to collect the running process list.", file=sys.stderr)
        return 1
    matches = process_entries_matching_pattern(processes, pattern)
    print_pid_lookup_results(pattern_text, matches)
    return 0 if matches else 1


def execute_dev_container_workflow(
    *,
    command_name: str,
    selection: str,
    container_runtime_executable: Callable[[], str | None],
    container_runtime_ready: Callable[[str], tuple[bool, str]],
    print_container_runtime_unavailable: Callable[[str, str], None],
    configured_container_start_actions: Callable[[], list[tuple[str, dict[str, Any]]]],
    action_matches_alias: Callable[[dict[str, Any], str], bool],
    select_guided_action: Callable[[str, list[tuple[str, dict[str, Any]]]], dict[str, Any] | None],
    launch_background_process: Callable[[dict[str, Any]], int],
) -> int:
    """Prompt for and start one configured development container."""
    runtime = container_runtime_executable()
    if not runtime:
        print(
            f"{command_name} is unavailable because neither docker nor podman could be found.",
            file=sys.stderr,
        )
        return 1
    runtime_ready, runtime_details = container_runtime_ready(runtime)
    if runtime_ready is not True:
        print_container_runtime_unavailable(runtime, runtime_details)
        return 1
    actions = configured_container_start_actions()
    if not actions:
        print("No configured container start commands were found.", file=sys.stderr)
        return 1

    selected_action: dict[str, Any] | None = None
    if selection:
        for _label, action in actions:
            if action_matches_alias(action, selection):
                selected_action = action
                break
        if selected_action is None:
            available = ", ".join(label for label, _action in actions)
            print(
                f"Unknown container start target '{selection}'. Available: {available}",
                file=sys.stderr,
            )
            return 1
    else:
        selected_action = select_guided_action(INTENT_START, actions)
        if selected_action is None:
            return 0

    print(f"Selected: {selected_action.get('label', 'container')}")
    return launch_background_process(selected_action)
