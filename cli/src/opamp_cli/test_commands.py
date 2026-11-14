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

"""Configuration-driven development test execution for the OpAMP CLI."""

from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any, TextIO

CONFIG_KEY_COMMAND = "command"
CONFIG_KEY_CONTAINER_RUNTIME = "container_runtime"
CONFIG_KEY_CONTINUE_ON_FAILURE = "continue_on_failure"
CONFIG_KEY_DISCOVERY = "discovery"
CONFIG_KEY_DISCOVERY_EXCLUDE = "exclude"
CONFIG_KEY_DISCOVERY_PATTERN = "pattern"
CONFIG_KEY_DISCOVERY_REQUIRED_SCRIPT = "required_script"
CONFIG_KEY_DISCOVERY_TEST_DIRECTORY = "test_directory"
CONFIG_KEY_DISCOVERY_TYPE = "type"
CONFIG_KEY_ID = "id"
CONFIG_KEY_INCLUDES = "includes"
CONFIG_KEY_LABEL = "label"
CONFIG_KEY_REPORT_DIRECTORY = "report_directory"
CONFIG_KEY_STATE_FILE = "state_file"
CONFIG_KEY_SUITES = "suites"
CONFIG_KEY_TESTS = "tests"
CONFIG_KEY_USES_CONTAINERS = "uses_containers"
CONFIG_KEY_WORKING_DIRECTORY = "working_directory"
DISCOVERY_TYPE_PYTHON_PROJECTS = "python_projects"
DISCOVERY_TYPE_NODE_PROJECTS = "node_projects"
DEFAULT_CONFIG_PATH = Path("cli/config/dev_test_suites.json")
DEFAULT_REPORT_DIRECTORY = Path("cli/runtime/test-reports")
DEFAULT_STATE_FILE = Path("cli/runtime/dev_test_run.json")
DEFAULT_CONTAINER_RUNTIME = "docker"
DEFAULT_DISCOVERY_PATTERN = "**/pyproject.toml"
DEFAULT_TEST_DIRECTORY = "tests"
DEFAULT_SUITE = "all"
EXIT_CODE_INTERRUPTED = 130
FIELD_PROJECT_ID = "project_id"
FIELD_PROJECT_LABEL = "project_label"
FIELD_PROJECT_PATH = "project_path"
FIELD_REPO_ROOT = "repo_root"
OPTION_CONFIG = "--config"
PACKAGE_KEY_SCRIPTS = "scripts"
POPEN_KEY_BUFFER_SIZE = "bufsize"
POPEN_KEY_CREATION_FLAGS = "creationflags"
POPEN_KEY_CURRENT_WORKING_DIRECTORY = "cwd"
POPEN_KEY_START_NEW_SESSION = "start_new_session"
POPEN_KEY_STANDARD_ERROR = "stderr"
POPEN_KEY_STANDARD_OUTPUT = "stdout"
POPEN_KEY_TEXT = "text"
REPORT_KEY_COMPLETED_AT_UTC = "completed_at_utc"
REPORT_KEY_DURATION_SECONDS = "duration_seconds"
REPORT_KEY_STARTED_AT_UTC = "started_at_utc"
REPORT_KEY_STATUS = "status"
REPORT_KEY_SUITE = "suite"
REPORT_KEY_TESTS = "tests"
SELECTION_LIST = "list"
SELECTION_TERMINATE = "terminate"
STATE_KEY_BASELINE_CONTAINER_IDS = "baseline_container_ids"
STATE_KEY_CONTAINER_RUNTIME = "container_runtime"
STATE_KEY_LOG_PATH = "log_path"
STATE_KEY_PID = "pid"
STATE_KEY_STARTED_AT_UTC = "started_at_utc"
STATE_KEY_TASK_ID = "task_id"
STATUS_FAILED = "failed"
STATUS_INTERRUPTED = "interrupted"
STATUS_PASSED = "passed"
SUMMARY_DIVIDER = "-" * 78
WINDOWS_TASKKILL_EXECUTABLE = "taskkill"


@dataclass(frozen=True)
class TestTask:
    """Describe one resolved test process.

    Attributes:
        task_id: Stable identifier used in console and retained reports.
        label: Human-readable description of the test process.
        command: Argument vector executed without a shell.
        working_directory: Directory from which the process is started.
        uses_containers: Whether newly created containers must be tracked and removed.
    """

    task_id: str
    label: str
    command: tuple[str, ...]
    working_directory: Path
    uses_containers: bool


# A retained result deliberately carries the full standalone report record.
# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class TestResult:
    """Describe the outcome and retained output for one test process.

    Attributes:
        task_id: Stable identifier copied from the resolved task.
        label: Human-readable test description.
        status: Passed, failed, or interrupted result state.
        exit_code: Child-process exit code.
        duration_seconds: Wall-clock execution time in seconds.
        command: Argument vector used to run the test.
        working_directory: Directory from which the test ran.
        log_path: Path of the complete captured console output.
    """

    task_id: str
    label: str
    status: str
    exit_code: int
    duration_seconds: float
    command: tuple[str, ...]
    working_directory: str
    log_path: str


def dev_test_config_available(*, repo_root: Path, config_path: Path | None = None) -> bool:
    """Return whether the default or caller-selected test configuration exists.

    Parameters:
        repo_root: Repository root used to resolve relative configuration paths.
        config_path: Optional configuration path override.
    """

    return _resolve_repo_path(repo_root, config_path or DEFAULT_CONFIG_PATH).is_file()


def execute_dev_tests_workflow(
    argv: list[str],
    *,
    repo_root: Path,
    dev_features_enabled: bool,
    prompt_text: Callable[[str], str],
    logger: logging.Logger,
) -> int:
    """Select, discover, run, or terminate development tests.

    Parameters:
        argv: Tokens following the ``dev-tests`` command.
        repo_root: Repository root containing configuration and test projects.
        dev_features_enabled: Whether development-only CLI features are enabled.
        prompt_text: Interactive input callback used when no suite is supplied.
        logger: CLI logger receiving debug-level execution details.
    """

    if dev_features_enabled is not True:
        print("dev-tests requires APP_ENABLE_DEV_FEATURES=true")
        return 2
    selection, config_path = _parse_arguments(argv, repo_root=repo_root)
    configuration = _load_configuration(config_path)
    suites = _suite_mapping(configuration)
    if not selection:
        selection = _prompt_for_selection(suites, prompt_text=prompt_text)
    if selection == SELECTION_TERMINATE:
        return terminate_active_test_run(
            repo_root=repo_root,
            configuration=configuration,
            logger=logger,
        )
    if selection == SELECTION_LIST:
        _print_discovered_suites(suites, repo_root=repo_root)
        return 0
    if selection not in suites:
        valid_values = ", ".join([*suites, SELECTION_LIST, SELECTION_TERMINATE])
        raise ValueError(f"unknown test selection {selection!r}; choose one of: {valid_values}")

    tasks = _resolve_suite_tasks(selection, suites=suites, repo_root=repo_root)
    if not tasks:
        raise ValueError(f"test suite {selection!r} did not discover any tests")
    logger.debug("resolved dev test suite selection=%s tasks=%s", selection, len(tasks))
    return _run_tasks(
        selection,
        tasks=tasks,
        configuration=configuration,
        repo_root=repo_root,
        logger=logger,
    )


def terminate_active_test_run(
    *,
    repo_root: Path,
    configuration: dict[str, Any],
    logger: logging.Logger,
) -> int:
    """Terminate the recorded test process tree and containers it created.

    Parameters:
        repo_root: Repository root used to resolve the configured state path.
        configuration: Loaded test-suite configuration.
        logger: CLI logger receiving process and container cleanup details.
    """

    state_path = _configured_path(
        configuration,
        CONFIG_KEY_STATE_FILE,
        DEFAULT_STATE_FILE,
        repo_root=repo_root,
    )
    state = _read_state(state_path)
    if not state:
        print("No active development test process is recorded.")
        return 0
    process_id = int(state.get(STATE_KEY_PID) or 0)
    if process_id > 0:
        _terminate_process_tree(process_id, logger=logger)
    runtime = str(state.get(STATE_KEY_CONTAINER_RUNTIME) or DEFAULT_CONTAINER_RUNTIME)
    baseline_ids = _optional_string_set(state.get(STATE_KEY_BASELINE_CONTAINER_IDS))
    _remove_new_containers(runtime, baseline_ids=baseline_ids, logger=logger)
    state_path.unlink(missing_ok=True)
    print(f"Terminated active test process {process_id} and its newly created containers.")
    return 0


def _parse_arguments(argv: list[str], *, repo_root: Path) -> tuple[str, Path]:
    """Parse suite selection and optional configuration path.

    Parameters:
        argv: Tokens supplied to the development test command.
        repo_root: Repository root used to resolve the default configuration.
    """

    selection = ""
    config_path = _resolve_repo_path(repo_root, DEFAULT_CONFIG_PATH)
    argument_index = 0
    while argument_index < len(argv):
        token = str(argv[argument_index]).strip()
        if token == OPTION_CONFIG:
            argument_index += 1
            if argument_index >= len(argv):
                raise ValueError(f"{OPTION_CONFIG} requires a path")
            config_path = _resolve_repo_path(repo_root, Path(argv[argument_index]))
        elif not selection:
            selection = token.lower()
        else:
            raise ValueError(f"unexpected dev-tests argument: {token}")
        argument_index += 1
    return selection, config_path


def _load_configuration(config_path: Path) -> dict[str, Any]:
    """Load and minimally validate one JSON test configuration.

    Parameters:
        config_path: JSON file defining suites and test tasks.
    """

    if not config_path.is_file():
        raise FileNotFoundError(f"development test configuration not found: {config_path}")
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("development test configuration must be a JSON object")
    _suite_mapping(payload)
    return payload


def _suite_mapping(configuration: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return validated suite objects from a loaded configuration.

    Parameters:
        configuration: Loaded JSON configuration object.
    """

    raw_suites = configuration.get(CONFIG_KEY_SUITES)
    if not isinstance(raw_suites, dict) or not raw_suites:
        raise ValueError("development test configuration requires a non-empty suites object")
    suites: dict[str, dict[str, Any]] = {}
    for suite_name, suite_payload in raw_suites.items():
        if not isinstance(suite_payload, dict):
            raise ValueError(f"suite {suite_name!r} must be a JSON object")
        suites[str(suite_name)] = suite_payload
    return suites


def _prompt_for_selection(
    suites: dict[str, dict[str, Any]],
    *,
    prompt_text: Callable[[str], str],
) -> str:
    """Prompt for one configured suite using a number or suite name.

    Parameters:
        suites: Configured suites keyed by command selection.
        prompt_text: Interactive input callback.
    """

    suite_names = list(suites)
    print("Development test suites:")
    for position, suite_name in enumerate(suite_names, start=1):
        label = str(suites[suite_name].get(CONFIG_KEY_LABEL) or suite_name)
        print(f"  {position}. {label} ({suite_name})")
    response = str(
        prompt_text(f"Select suite [{DEFAULT_SUITE}]: ") or DEFAULT_SUITE
    ).strip().lower()
    if response.isdigit():
        selected_position = int(response) - 1
        if 0 <= selected_position < len(suite_names):
            return suite_names[selected_position]
    return response


def _print_discovered_suites(
    suites: dict[str, dict[str, Any]],
    *,
    repo_root: Path,
) -> None:
    """Print configured suites and every task they currently discover.

    Parameters:
        suites: Configured suite mapping.
        repo_root: Repository root used during task discovery.
    """

    for suite_name, suite_payload in suites.items():
        label = str(suite_payload.get(CONFIG_KEY_LABEL) or suite_name)
        tasks = _resolve_suite_tasks(suite_name, suites=suites, repo_root=repo_root)
        print(f"{suite_name}: {label} ({len(tasks)} tests)")
        for task in tasks:
            print(f"  - {task.task_id}: {task.label}")


def _resolve_suite_tasks(
    suite_name: str,
    *,
    suites: dict[str, dict[str, Any]],
    repo_root: Path,
    active_suites: tuple[str, ...] = (),
) -> list[TestTask]:
    """Expand included suites and discovery templates into concrete tasks.

    Parameters:
        suite_name: Suite key to expand.
        suites: All configured suites.
        repo_root: Repository root used to discover projects and resolve paths.
        active_suites: Parent expansion chain used to reject include cycles.
    """

    if suite_name in active_suites:
        chain = " -> ".join((*active_suites, suite_name))
        raise ValueError(f"cyclic test suite include detected: {chain}")
    suite_payload = suites.get(suite_name)
    if suite_payload is None:
        raise ValueError(f"included test suite is not configured: {suite_name}")
    tasks: list[TestTask] = []
    raw_includes = suite_payload.get(CONFIG_KEY_INCLUDES, [])
    if not isinstance(raw_includes, list):
        raise ValueError(f"suite {suite_name!r} includes must be a list")
    for included_suite in raw_includes:
        tasks.extend(
            _resolve_suite_tasks(
                str(included_suite),
                suites=suites,
                repo_root=repo_root,
                active_suites=(*active_suites, suite_name),
            )
        )
    raw_tests = suite_payload.get(CONFIG_KEY_TESTS, [])
    if not isinstance(raw_tests, list):
        raise ValueError(f"suite {suite_name!r} tests must be a list")
    for test_payload in raw_tests:
        if not isinstance(test_payload, dict):
            raise ValueError(f"suite {suite_name!r} contains a non-object test")
        tasks.extend(_resolve_test_definition(test_payload, repo_root=repo_root))
    return tasks


def _resolve_test_definition(test_payload: dict[str, Any], *, repo_root: Path) -> list[TestTask]:
    """Resolve a static task or project-discovery task template.

    Parameters:
        test_payload: Configured test definition.
        repo_root: Repository root used for discovery and path resolution.
    """

    # Discovery templates necessarily carry the marker, exclusion, and formatting
    # values together; keeping them local makes one configuration entry auditable.
    # pylint: disable=too-many-locals
    discovery = test_payload.get(CONFIG_KEY_DISCOVERY)
    if discovery is None:
        return [_materialize_task(test_payload, repo_root=repo_root, fields={})]
    if not isinstance(discovery, dict):
        raise ValueError("test discovery must be a JSON object")
    discovery_type = str(discovery.get(CONFIG_KEY_DISCOVERY_TYPE) or "")
    supported_types = {DISCOVERY_TYPE_NODE_PROJECTS, DISCOVERY_TYPE_PYTHON_PROJECTS}
    if discovery_type not in supported_types:
        raise ValueError(f"unsupported test discovery type: {discovery_type!r}")
    pattern = str(discovery.get(CONFIG_KEY_DISCOVERY_PATTERN) or DEFAULT_DISCOVERY_PATTERN)
    excludes = [str(value) for value in discovery.get(CONFIG_KEY_DISCOVERY_EXCLUDE, [])]
    tasks: list[TestTask] = []
    for project_marker_path in sorted(repo_root.glob(pattern)):
        relative_marker = project_marker_path.relative_to(repo_root)
        relative_text = relative_marker.as_posix()
        if _matches_any_pattern(relative_text, excludes):
            continue
        project_path = project_marker_path.parent
        if discovery_type == DISCOVERY_TYPE_PYTHON_PROJECTS:
            test_directory = str(
                discovery.get(CONFIG_KEY_DISCOVERY_TEST_DIRECTORY) or DEFAULT_TEST_DIRECTORY
            )
            if not (project_path / test_directory).is_dir():
                continue
        elif discovery_type == DISCOVERY_TYPE_NODE_PROJECTS:
            required_script = str(
                discovery.get(CONFIG_KEY_DISCOVERY_REQUIRED_SCRIPT) or ""
            ).strip()
            if not required_script or not _package_defines_script(
                project_marker_path,
                required_script=required_script,
            ):
                continue
        if not project_marker_path.is_file():
            continue
        relative_project = project_path.relative_to(repo_root).as_posix()
        project_id = relative_project.replace("/", "-").replace("_", "-")
        fields = {
            FIELD_PROJECT_ID: project_id,
            FIELD_PROJECT_LABEL: relative_project,
            FIELD_PROJECT_PATH: relative_project,
            FIELD_REPO_ROOT: str(repo_root),
        }
        tasks.append(_materialize_task(test_payload, repo_root=repo_root, fields=fields))
    return tasks


def _materialize_task(
    test_payload: dict[str, Any],
    *,
    repo_root: Path,
    fields: dict[str, str],
) -> TestTask:
    """Format one configured test definition into an executable task.

    Parameters:
        test_payload: Test definition containing command and metadata templates.
        repo_root: Repository root used to resolve the working directory.
        fields: Discovery values available to string templates.
    """

    task_id = str(test_payload.get(CONFIG_KEY_ID) or "").format_map(fields).strip()
    if not task_id:
        raise ValueError("every development test requires an id")
    label = str(test_payload.get(CONFIG_KEY_LABEL) or task_id).format_map(fields)
    raw_command = test_payload.get(CONFIG_KEY_COMMAND)
    if not isinstance(raw_command, list) or not raw_command:
        raise ValueError(f"development test {task_id!r} requires a command list")
    command = tuple(str(value).format_map(fields) for value in raw_command)
    working_directory_text = str(
        test_payload.get(CONFIG_KEY_WORKING_DIRECTORY) or "."
    ).format_map(fields)
    working_directory = _resolve_repo_path(repo_root, Path(working_directory_text))
    if not working_directory.is_dir():
        raise ValueError(f"working directory for {task_id!r} does not exist: {working_directory}")
    return TestTask(
        task_id=task_id,
        label=label,
        command=command,
        working_directory=working_directory,
        uses_containers=bool(test_payload.get(CONFIG_KEY_USES_CONTAINERS, False)),
    )


def _matches_any_pattern(relative_path: str, patterns: list[str]) -> bool:
    """Return whether a repository-relative path matches an exclusion pattern.

    Parameters:
        relative_path: POSIX-style path relative to the repository root.
        patterns: Glob-style patterns from configuration.
    """

    return any(fnmatchcase(relative_path, pattern) for pattern in patterns)


def _package_defines_script(package_path: Path, *, required_script: str) -> bool:
    """Return whether a package JSON file defines the requested npm script.

    Parameters:
        package_path: Candidate ``package.json`` path discovered from configuration.
        required_script: Script key that must exist in the package's scripts object.
    """

    try:
        payload = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    scripts = payload.get(PACKAGE_KEY_SCRIPTS) if isinstance(payload, dict) else None
    return isinstance(scripts, dict) and bool(str(scripts.get(required_script) or "").strip())


def _run_tasks(
    suite_name: str,
    *,
    tasks: list[TestTask],
    configuration: dict[str, Any],
    repo_root: Path,
    logger: logging.Logger,
) -> int:
    """Execute every resolved task, retaining logs and a JSON summary.

    Parameters:
        suite_name: Selected suite name retained in the summary.
        tasks: Ordered concrete test tasks.
        configuration: Loaded runner configuration.
        repo_root: Repository root used for configured output paths.
        logger: CLI logger receiving debug execution details.
    """

    # Suite execution keeps paths, timing, and aggregate results together so every
    # task is reported even when an earlier task fails.
    # pylint: disable=too-many-locals
    report_directory = _configured_path(
        configuration,
        CONFIG_KEY_REPORT_DIRECTORY,
        DEFAULT_REPORT_DIRECTORY,
        repo_root=repo_root,
    )
    state_path = _configured_path(
        configuration,
        CONFIG_KEY_STATE_FILE,
        DEFAULT_STATE_FILE,
        repo_root=repo_root,
    )
    runtime = str(configuration.get(CONFIG_KEY_CONTAINER_RUNTIME) or DEFAULT_CONTAINER_RUNTIME)
    report_directory.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc)
    run_id = started_at.strftime("%Y%m%dT%H%M%SZ")
    results: list[TestResult] = []
    selected_suite = _suite_mapping(configuration)[suite_name]
    continue_on_failure = bool(selected_suite.get(CONFIG_KEY_CONTINUE_ON_FAILURE, True))
    print(f"Running {len(tasks)} tests for suite '{suite_name}'.")
    for task_position, task in enumerate(tasks, start=1):
        log_path = report_directory / f"{run_id}-{task.task_id}.log"
        print(f"\n[{task_position}/{len(tasks)}] {task.label}")
        print(f"Command: {' '.join(task.command)}")
        result = _run_task(
            task,
            log_path=log_path,
            state_path=state_path,
            runtime=runtime,
            logger=logger,
        )
        results.append(result)
        print(
            f"Result: {result.status}; exit code: {result.exit_code}; "
            f"elapsed: {result.duration_seconds:.3f}s"
        )
        print(f"Output: {result.log_path}")
        if result.status == STATUS_INTERRUPTED:
            break
        if result.exit_code != 0 and continue_on_failure is not True:
            break
    summary_path = report_directory / f"{run_id}-{suite_name}-summary.json"
    _write_summary(
        summary_path,
        suite_name=suite_name,
        started_at=started_at,
        results=results,
    )
    _print_summary(results, summary_path=summary_path)
    if any(result.status == STATUS_INTERRUPTED for result in results):
        return EXIT_CODE_INTERRUPTED
    return 1 if any(result.exit_code != 0 for result in results) else 0


def _run_task(
    task: TestTask,
    *,
    log_path: Path,
    state_path: Path,
    runtime: str,
    logger: logging.Logger,
) -> TestResult:
    """Run one process while streaming and retaining its combined output.

    Parameters:
        task: Fully resolved test command and metadata.
        log_path: File receiving combined stdout and stderr.
        state_path: File used by a concurrent terminate command.
        runtime: Container runtime used to find and remove test containers.
        logger: CLI logger receiving debug process details.
    """

    baseline_ids = _container_ids(runtime, logger=logger) if task.uses_containers else set()
    started_at = time.perf_counter()
    process: subprocess.Popen[str] | None = None
    exit_code = 1
    status = STATUS_FAILED
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with log_path.open("w", encoding="utf-8") as output_file:
            process = _start_process(task, output_file=output_file, logger=logger)
            _write_state(
                state_path,
                {
                    STATE_KEY_BASELINE_CONTAINER_IDS: (
                        sorted(baseline_ids) if baseline_ids is not None else None
                    ),
                    STATE_KEY_CONTAINER_RUNTIME: runtime,
                    STATE_KEY_LOG_PATH: str(log_path),
                    STATE_KEY_PID: process.pid,
                    STATE_KEY_STARTED_AT_UTC: datetime.now(timezone.utc).isoformat(),
                    STATE_KEY_TASK_ID: task.task_id,
                },
            )
            _stream_process_output(process, output_file=output_file)
            exit_code = process.wait()
            status = STATUS_PASSED if exit_code == 0 else STATUS_FAILED
    except KeyboardInterrupt:
        status = STATUS_INTERRUPTED
        exit_code = EXIT_CODE_INTERRUPTED
        if process is not None:
            _terminate_process_tree(process.pid, logger=logger)
        print("\nTest execution interrupted; terminating the active process and containers.")
    except OSError as error:
        status = STATUS_FAILED
        exit_code = 1
        failure_message = f"Unable to start test process: {error}"
        print(failure_message)
        with log_path.open("a", encoding="utf-8") as output_file:
            output_file.write(f"{failure_message}\n")
    finally:
        if task.uses_containers:
            _remove_new_containers(runtime, baseline_ids=baseline_ids, logger=logger)
        state_path.unlink(missing_ok=True)
    duration = time.perf_counter() - started_at
    return TestResult(
        task_id=task.task_id,
        label=task.label,
        status=status,
        exit_code=exit_code,
        duration_seconds=round(duration, 6),
        command=task.command,
        working_directory=str(task.working_directory),
        log_path=str(log_path),
    )


def _start_process(
    task: TestTask,
    *,
    output_file: TextIO,
    logger: logging.Logger,
) -> subprocess.Popen[str]:
    """Start one test in a distinct process group for safe tree termination.

    Parameters:
        task: Test command and working directory to execute.
        output_file: Retained output file referenced in debug diagnostics.
        logger: CLI logger receiving command details.
    """

    logger.debug(
        "starting test process task=%s cwd=%s output=%s command=%s",
        task.task_id,
        task.working_directory,
        output_file.name,
        task.command,
    )
    process_options: dict[str, Any] = {
        POPEN_KEY_BUFFER_SIZE: 1,
        POPEN_KEY_CURRENT_WORKING_DIRECTORY: str(task.working_directory),
        POPEN_KEY_STANDARD_ERROR: subprocess.STDOUT,
        POPEN_KEY_STANDARD_OUTPUT: subprocess.PIPE,
        POPEN_KEY_TEXT: True,
    }
    if os.name == "nt":
        process_options[POPEN_KEY_CREATION_FLAGS] = int(
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        )
    else:
        process_options[POPEN_KEY_START_NEW_SESSION] = True
    return subprocess.Popen(list(task.command), **process_options)  # noqa: S603


def _stream_process_output(process: subprocess.Popen[str], *, output_file: TextIO) -> None:
    """Echo combined child output to the terminal and retained log.

    Parameters:
        process: Running child process with stdout captured as text.
        output_file: Open UTF-8 log file receiving each output line.
    """

    if process.stdout is None:
        return
    for output_line in process.stdout:
        print(output_line, end="", flush=True)
        output_file.write(output_line)
        output_file.flush()


def _terminate_process_tree(process_id: int, *, logger: logging.Logger) -> None:
    """Terminate a child process and all processes beneath it.

    Parameters:
        process_id: Root process identifier recorded for the active task.
        logger: CLI logger receiving cleanup diagnostics.
    """

    logger.debug("terminating active test process tree pid=%s", process_id)
    try:
        if os.name == "nt":
            subprocess.run(  # noqa: S603
                [WINDOWS_TASKKILL_EXECUTABLE, "/PID", str(process_id), "/T", "/F"],
                check=False,
                capture_output=True,
                text=True,
            )
            return
        os.killpg(process_id, signal.SIGTERM)  # type: ignore[attr-defined]  # pylint: disable=no-member
    except (OSError, ProcessLookupError) as error:
        logger.debug("test process tree was already stopped pid=%s error=%s", process_id, error)


def _container_ids(runtime: str, *, logger: logging.Logger) -> set[str] | None:
    """Return visible container identifiers, or ``None`` when listing fails.

    Parameters:
        runtime: Docker-compatible executable name or path.
        logger: CLI logger receiving unavailable-runtime diagnostics.
    """

    try:
        completed = subprocess.run(  # noqa: S603
            [runtime, "ps", "-aq"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        logger.debug("container runtime unavailable runtime=%s error=%s", runtime, error)
        return None
    if completed.returncode != 0:
        logger.debug(
            "container listing failed runtime=%s exit_code=%s stderr=%s",
            runtime,
            completed.returncode,
            completed.stderr.strip(),
        )
        return None
    return {line.strip() for line in completed.stdout.splitlines() if line.strip()}


def _remove_new_containers(
    runtime: str,
    *,
    baseline_ids: set[str] | None,
    logger: logging.Logger,
) -> None:
    """Force-remove containers created after the task baseline was captured.

    Parameters:
        runtime: Docker-compatible executable name or path.
        baseline_ids: Container identifiers that predated the active task, or
            ``None`` when the safe baseline could not be captured.
        logger: CLI logger receiving cleanup diagnostics.
    """

    if baseline_ids is None:
        logger.warning(
            "container cleanup skipped because the pre-test container baseline was unavailable"
        )
        return
    current_ids = _container_ids(runtime, logger=logger)
    if current_ids is None:
        logger.warning("container cleanup skipped because current containers could not be listed")
        return
    created_ids = sorted(current_ids - baseline_ids)
    if not created_ids:
        return
    logger.debug("removing test-created containers runtime=%s ids=%s", runtime, created_ids)
    try:
        completed = subprocess.run(  # noqa: S603
            [runtime, "rm", "-f", *created_ids],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        logger.warning("unable to remove test containers: %s", error)
        return
    if completed.returncode != 0:
        logger.warning("container cleanup failed: %s", completed.stderr.strip())


def _configured_path(
    configuration: dict[str, Any],
    key: str,
    default_path: Path,
    *,
    repo_root: Path,
) -> Path:
    """Resolve one configured repository-relative output path.

    Parameters:
        configuration: Loaded test configuration.
        key: Named configuration key containing the path.
        default_path: Path used when the setting is absent.
        repo_root: Repository root used for relative paths.
    """

    configured_value = str(configuration.get(key) or default_path)
    return _resolve_repo_path(repo_root, Path(configured_value))


def _resolve_repo_path(repo_root: Path, path: Path) -> Path:
    """Resolve an absolute path or a path relative to the repository root.

    Parameters:
        repo_root: Repository root used for relative values.
        path: Absolute or repository-relative path.
    """

    return path.resolve() if path.is_absolute() else (repo_root / path).resolve()


def _write_state(state_path: Path, state: dict[str, Any]) -> None:
    """Atomically retain active process details for external termination.

    Parameters:
        state_path: Destination JSON state path.
        state: Serializable active task metadata.
    """

    state_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = state_path.with_suffix(f"{state_path.suffix}.tmp")
    temporary_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(state_path)


def _read_state(state_path: Path) -> dict[str, Any]:
    """Read active test state, returning an empty object when absent.

    Parameters:
        state_path: JSON state file used by the active runner.
    """

    if not state_path.is_file():
        return {}
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _optional_string_set(value: object) -> set[str] | None:
    """Convert a JSON list into strings or preserve an unavailable baseline.

    Parameters:
        value: Possible list of container identifiers, or ``None`` when the
            baseline inventory was unavailable.
    """

    if value is None:
        return None
    if not isinstance(value, list):
        return None
    return {str(entry).strip() for entry in value if str(entry).strip()}


def _write_summary(
    summary_path: Path,
    *,
    suite_name: str,
    started_at: datetime,
    results: list[TestResult],
) -> None:
    """Write a machine-readable result and timing summary.

    Parameters:
        summary_path: JSON report destination.
        suite_name: Selected suite name.
        started_at: UTC time at which suite execution began.
        results: Ordered per-test outcomes.
    """

    payload = {
        REPORT_KEY_COMPLETED_AT_UTC: datetime.now(timezone.utc).isoformat(),
        REPORT_KEY_DURATION_SECONDS: round(
            sum(result.duration_seconds for result in results),
            6,
        ),
        REPORT_KEY_STARTED_AT_UTC: started_at.isoformat(),
        REPORT_KEY_STATUS: (
            STATUS_PASSED
            if all(result.exit_code == 0 for result in results)
            else STATUS_FAILED
        ),
        REPORT_KEY_SUITE: suite_name,
        REPORT_KEY_TESTS: [asdict(result) for result in results],
    }
    summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _print_summary(results: list[TestResult], *, summary_path: Path) -> None:
    """Print the status and elapsed time of every completed test.

    Parameters:
        results: Ordered per-test outcomes.
        summary_path: Retained JSON report path shown to the developer.
    """

    print(f"\n{SUMMARY_DIVIDER}")
    print("Development test summary")
    print(SUMMARY_DIVIDER)
    for result in results:
        print(
            f"{result.status.upper():11} {result.duration_seconds:10.3f}s  "
            f"{result.task_id}"
        )
    print(SUMMARY_DIVIDER)
    print(f"Total elapsed: {sum(result.duration_seconds for result in results):.3f}s")
    print(f"Summary report: {summary_path}")


__all__ = [
    "TestResult",
    "TestTask",
    "dev_test_config_available",
    "execute_dev_tests_workflow",
    "terminate_active_test_run",
]
