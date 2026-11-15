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

"""Unit coverage for the configuration-driven development test runner."""

from __future__ import annotations

import importlib
import json
import logging
import sys
from pathlib import Path
from types import SimpleNamespace

test_commands = importlib.import_module("opamp_dev_tools.test_commands")


def _write_config(path: Path, payload: dict[str, object]) -> None:
    """Write one test-owned development suite configuration."""

    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_packaged_default_configuration_is_available(tmp_path: Path) -> None:
    """The installed developer CLI should carry its default suite catalog."""

    assert test_commands.dev_test_config_available(repo_root=tmp_path)
    selection, config_path = test_commands._parse_arguments(["list"], repo_root=tmp_path)
    configuration = test_commands._load_configuration(config_path)

    assert selection == "list"
    assert config_path == test_commands.DEFAULT_CONFIG_PATH
    assert "all" in configuration["suites"]


def test_python_project_discovery_materializes_only_projects_with_tests(tmp_path: Path) -> None:
    project_path = tmp_path / "sample-component"
    project_path.mkdir()
    (project_path / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")
    (project_path / "tests").mkdir()
    skipped_path = tmp_path / "without-tests"
    skipped_path.mkdir()
    (skipped_path / "pyproject.toml").write_text("[project]\nname='skip'\n", encoding="utf-8")
    test_payload = {
        "id": "unit-{project_id}",
        "label": "{project_label} tests",
        "command": ["uv", "run", "--project", "{project_path}", "pytest"],
        "working_directory": "{project_path}",
        "discovery": {
            "type": "python_projects",
            "pattern": "**/pyproject.toml",
            "test_directory": "tests",
        },
    }

    tasks = test_commands._resolve_test_definition(test_payload, repo_root=tmp_path)

    assert len(tasks) == 1
    assert tasks[0].task_id == "unit-sample-component"
    assert tasks[0].working_directory == project_path.resolve()


def test_suite_include_expansion_preserves_configured_order(tmp_path: Path) -> None:
    suites = {
        "all": {"includes": ["unit", "security"]},
        "unit": {
            "tests": [
                {"id": "unit", "command": ["unit-command"], "working_directory": "."}
            ]
        },
        "security": {
            "tests": [
                {
                    "id": "security",
                    "command": ["security-command"],
                    "working_directory": ".",
                }
            ]
        },
    }

    tasks = test_commands._resolve_suite_tasks("all", suites=suites, repo_root=tmp_path)

    assert [task.task_id for task in tasks] == ["unit", "security"]


def test_node_project_discovery_requires_configured_script(tmp_path: Path) -> None:
    project_path = tmp_path / "web-component"
    project_path.mkdir()
    (project_path / "package.json").write_text(
        json.dumps({"scripts": {"ui:unit": "vitest run"}}),
        encoding="utf-8",
    )
    ignored_path = tmp_path / "node_modules" / "dependency"
    ignored_path.mkdir(parents=True)
    (ignored_path / "package.json").write_text(
        json.dumps({"scripts": {"ui:unit": "do-not-run"}}),
        encoding="utf-8",
    )
    test_payload = {
        "id": "node-{project_id}",
        "command": ["npm", "run", "ui:unit"],
        "working_directory": "{project_path}",
        "discovery": {
            "type": "node_projects",
            "pattern": "**/package.json",
            "required_script": "ui:unit",
            "exclude": ["node_modules/**", "**/node_modules/**"],
        },
    }

    tasks = test_commands._resolve_test_definition(test_payload, repo_root=tmp_path)

    assert [task.task_id for task in tasks] == ["node-web-component"]


def test_file_project_discovery_materializes_lock_file_projects(tmp_path: Path) -> None:
    """File-marker discovery should create one task for each non-excluded lock project."""

    project_path = tmp_path / "locked-component"
    project_path.mkdir()
    (project_path / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    ignored_path = tmp_path / ".venv" / "ignored-component"
    ignored_path.mkdir(parents=True)
    (ignored_path / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    test_payload = {
        "id": "audit-{project_id}",
        "command": ["audit", "{project_path}"],
        "working_directory": ".",
        "discovery": {
            "type": "file_projects",
            "pattern": "**/uv.lock",
            "exclude": [".venv/**", "**/.venv/**"],
        },
    }

    tasks = test_commands._resolve_test_definition(test_payload, repo_root=tmp_path)

    assert [task.task_id for task in tasks] == ["audit-locked-component"]
    assert tasks[0].command == ("audit", "locked-component")


def test_optional_executable_task_is_discovered_only_when_available(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Optional tools should add tasks only when their executable is on PATH."""

    test_payload = {
        "id": "renovate-local",
        "command": ["{required_executable_path}", "--platform=local"],
        "working_directory": ".",
        "required_executable": "renovate",
    }
    monkeypatch.setattr(test_commands.shutil, "which", lambda _executable: None)

    unavailable_tasks = test_commands._resolve_test_definition(
        test_payload,
        repo_root=tmp_path,
    )

    monkeypatch.setattr(
        test_commands.shutil,
        "which",
        lambda _executable: str(tmp_path / "renovate"),
    )
    available_tasks = test_commands._resolve_test_definition(
        test_payload,
        repo_root=tmp_path,
    )

    assert unavailable_tasks == []
    assert [task.task_id for task in available_tasks] == ["renovate-local"]
    assert available_tasks[0].command[0] == str(tmp_path / "renovate")


def test_execute_workflow_streams_output_and_writes_timed_summary(
    tmp_path: Path,
    capsys,
) -> None:
    config_path = tmp_path / "test-suites.json"
    _write_config(
        config_path,
        {
            "report_directory": "reports",
            "state_file": "active.json",
            "suites": {
                "unit": {
                    "tests": [
                        {
                            "id": "sample",
                            "label": "Sample test",
                            "command": [sys.executable, "-c", "print('sample-output')"],
                            "working_directory": ".",
                        }
                    ]
                }
            },
        },
    )

    exit_code = test_commands.execute_test_suite_workflow(
        ["unit", "--config", str(config_path)],
        repo_root=tmp_path,
        prompt_text=lambda _prompt: "unit",
        logger=logging.getLogger("test-dev-tests"),
    )

    captured = capsys.readouterr().out
    summary_paths = list((tmp_path / "reports").glob("*-unit-summary.json"))
    assert exit_code == 0
    assert "sample-output" in captured
    assert "elapsed:" in captured
    assert len(summary_paths) == 1
    summary = json.loads(summary_paths[0].read_text(encoding="utf-8"))
    assert summary["status"] == "passed"
    assert summary["tests"][0]["duration_seconds"] >= 0
    assert not (tmp_path / "active.json").exists()


def test_terminate_uses_recorded_process_and_container_baseline(
    tmp_path: Path,
    monkeypatch,
) -> None:
    state_path = tmp_path / "active.json"
    state_path.write_text(
        json.dumps(
            {
                "pid": 1234,
                "container_runtime": "docker",
                "baseline_container_ids": ["existing-container"],
            }
        ),
        encoding="utf-8",
    )
    terminated_processes: list[int] = []
    cleanup_calls: list[tuple[str, set[str] | None]] = []
    monkeypatch.setattr(
        test_commands,
        "_terminate_process_tree",
        lambda process_id, logger: terminated_processes.append(process_id),
    )
    monkeypatch.setattr(
        test_commands,
        "_remove_new_containers",
        lambda runtime, baseline_ids, logger: cleanup_calls.append((runtime, baseline_ids)),
    )

    exit_code = test_commands.terminate_active_test_run(
        repo_root=tmp_path,
        configuration={"state_file": "active.json"},
        logger=logging.getLogger("test-dev-tests"),
    )

    assert exit_code == 0
    assert terminated_processes == [1234]
    assert cleanup_calls == [("docker", {"existing-container"})]
    assert not state_path.exists()


def test_container_cleanup_removes_only_ids_created_after_baseline(monkeypatch) -> None:
    invoked_commands: list[list[str]] = []
    monkeypatch.setattr(
        test_commands,
        "_container_ids",
        lambda runtime, logger: {"existing-container", "new-container"},
    )

    def fake_run(command, **_kwargs):
        """Capture the Docker removal command and return success."""

        invoked_commands.append(command)
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(test_commands.subprocess, "run", fake_run)

    test_commands._remove_new_containers(
        "docker",
        baseline_ids={"existing-container"},
        logger=logging.getLogger("test-dev-tests"),
    )

    assert invoked_commands == [["docker", "rm", "-f", "new-container"]]


def test_container_cleanup_is_skipped_without_safe_baseline(monkeypatch) -> None:
    def fail_container_listing(runtime, logger):
        """Fail if cleanup attempts a container listing without a baseline."""

        raise AssertionError(f"must not list containers with {runtime} and {logger}")

    monkeypatch.setattr(
        test_commands,
        "_container_ids",
        fail_container_listing,
    )

    test_commands._remove_new_containers(
        "docker",
        baseline_ids=None,
        logger=logging.getLogger("test-dev-tests"),
    )
