#!/usr/bin/env python3
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

"""Verify a standalone opamp-cli wheel does not advertise developer CLI commands."""

from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import logging
import os
import shutil
import subprocess
from pathlib import Path

CLI_EXECUTABLE = "opamp-cli"
DEV_CLI_DISTRIBUTION = "opamp-dev-tools"
DEV_CLI_EXECUTABLES = ("opamp-dev-cli", "opamp-dev-tools", "opamp-cli-dev")
DEV_CLI_MODULE = "opamp_dev_tools"
ENV_RESULTS_DIRECTORY = "RESULTS_DIR"
FORBIDDEN_HELP_MARKERS = (
    "opamp-cli dev [developer-command...]",
    "opamp-cli dev-tests",
    "opamp-dev-cli",
)
FORBIDDEN_LIST_ENTRIES = ("dev", "dev-tests")
KEY_COMMANDS = "commands"
KEY_DEV_DISTRIBUTION_INSTALLED = "dev_distribution_installed"
KEY_DEV_EXECUTABLES = "dev_executables"
KEY_DEV_MODULE_INSTALLED = "dev_module_installed"
KEY_HELP = "help"
KEY_LIST = "list"
KEY_PASSED = "passed"
KEY_RETURN_CODE = "return_code"
KEY_STDERR = "stderr"
KEY_STDOUT = "stdout"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
RESULTS_FILE_NAME = "standalone-cli-results.json"
RESULTS_MARKDOWN_FILE_NAME = "results.md"
SUMMARY_FILE_NAME = "summary.json"
UTF8_ENCODING = "utf-8"

LOGGER = logging.getLogger(__name__)


def _run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Run the installed CLI and capture its deployment-visible command surface.

    Args:
        arguments: Command-line arguments passed to the installed executable.

    Returns:
        Completed process containing the exit code and captured text streams.
    """

    command = [CLI_EXECUTABLE, *arguments]
    LOGGER.debug("running standalone CLI command=%s", command)
    return subprocess.run(  # noqa: S603 - executable is a fixed installed entry point
        command,
        check=False,
        capture_output=True,
        text=True,
    )


def _command_payload(
    completed_process: subprocess.CompletedProcess[str],
) -> dict[str, object]:
    """Return serializable evidence for one installed CLI invocation.

    Args:
        completed_process: Captured subprocess result to preserve as evidence.

    Returns:
        Structured command result containing status and both output streams.
    """

    return {
        KEY_RETURN_CODE: completed_process.returncode,
        KEY_STDERR: completed_process.stderr,
        KEY_STDOUT: completed_process.stdout,
    }


def _top_level_list_entries(list_output: str) -> set[str]:
    """Extract top-level command names from the installed CLI list output.

    Args:
        list_output: Complete text returned by ``opamp-cli list``.

    Returns:
        Command names printed in the top-level section.
    """

    entries: set[str] = set()
    in_top_level_section = False
    for output_line in list_output.splitlines():
        if output_line == "Top-level commands:":
            in_top_level_section = True
            continue
        if in_top_level_section and output_line and not output_line.startswith("  - "):
            break
        if in_top_level_section and output_line.startswith("  - "):
            entries.add(output_line.removeprefix("  - ").strip())
    return entries


def _distribution_installed(distribution_name: str) -> bool:
    """Return whether one distribution exists in the isolated environment.

    Args:
        distribution_name: Installed package name queried through metadata.

    Returns:
        ``True`` only when package metadata can be resolved.
    """

    try:
        importlib.metadata.distribution(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return False
    return True


def main() -> int:
    """Verify package isolation, command discovery, and rendered help output."""

    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    results_directory = Path(os.environ.get(ENV_RESULTS_DIRECTORY, "/host-output"))
    results_directory.mkdir(parents=True, exist_ok=True)

    help_process = _run_cli("--help")
    list_process = _run_cli("list")
    resolved_dev_executables = {
        executable_name: shutil.which(executable_name)
        for executable_name in DEV_CLI_EXECUTABLES
    }
    dev_distribution_installed = _distribution_installed(DEV_CLI_DISTRIBUTION)
    dev_module_installed = importlib.util.find_spec(DEV_CLI_MODULE) is not None
    top_level_entries = _top_level_list_entries(list_process.stdout)

    assertions = [
        help_process.returncode == 0,
        list_process.returncode == 0,
        not dev_distribution_installed,
        not dev_module_installed,
        all(path is None for path in resolved_dev_executables.values()),
        all(marker not in help_process.stdout for marker in FORBIDDEN_HELP_MARKERS),
        all(entry not in top_level_entries for entry in FORBIDDEN_LIST_ENTRIES),
    ]
    passed = all(assertions)
    evidence = {
        KEY_COMMANDS: {
            KEY_HELP: _command_payload(help_process),
            KEY_LIST: _command_payload(list_process),
        },
        KEY_DEV_DISTRIBUTION_INSTALLED: dev_distribution_installed,
        KEY_DEV_EXECUTABLES: resolved_dev_executables,
        KEY_DEV_MODULE_INSTALLED: dev_module_installed,
        KEY_PASSED: passed,
    }
    evidence_text = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    (results_directory / RESULTS_FILE_NAME).write_text(
        evidence_text,
        encoding=UTF8_ENCODING,
    )
    (results_directory / SUMMARY_FILE_NAME).write_text(
        json.dumps({KEY_PASSED: passed}, indent=2) + "\n",
        encoding=UTF8_ENCODING,
    )
    result_label = "passed" if passed else "failed"
    (results_directory / RESULTS_MARKDOWN_FILE_NAME).write_text(
        "# Standalone opamp-cli Deployment Results\n\n"
        f"- Result: {result_label}\n"
        f"- Developer distribution installed: {dev_distribution_installed}\n"
        f"- Developer module installed: {dev_module_installed}\n",
        encoding=UTF8_ENCODING,
    )
    print(evidence_text, end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
