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

"""Build and install each OpAMP component wheel in isolated clean venvs."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import tomllib

CONFIG_CONSUMER_KEY = "consumer"
CONFIG_CONSUMER_AGENT_ADDITIONAL_PARAMS_KEY = "agent_additional_params"
CONFIG_CONSUMER_AGENT_CONFIG_PATH_KEY = "agent_config_path"
CONFIG_CONSUMER_HEARTBEAT_FREQUENCY_KEY = "heartbeat_frequency"
CONFIG_CONSUMER_LOG_LEVEL_KEY = "log_level"
CONFIG_CONSUMER_SERVER_AUTHORIZATION_KEY = "server-authorization"
CONFIG_CONSUMER_SERVER_URL_KEY = "server_url"
CONFIG_CONSUMER_SERVICE_TYPE_KEY = "service_type"
CONFIG_CONSUMER_TLS_KEY = "tls"
CONFIG_CONSUMER_TLS_VERIFY_SERVER_KEY = "verify_server"
CONFIG_FILE_NAME = "opamp.json"
CONFIG_PROVIDER_KEY = "provider"
CONFIG_PROVIDER_LOG_LEVEL_KEY = "log_level"
CONFIG_PROVIDER_STATE_PERSISTENCE_ENABLED_KEY = "enabled"
CONFIG_PROVIDER_STATE_PERSISTENCE_KEY = "state_persistence"
CONFIG_PROVIDER_TLS_ENABLED_KEY = "enabled"
CONFIG_PROVIDER_TLS_KEY = "tls"
DEFAULT_CONSUMER_HEARTBEAT_FREQUENCY = 30
DEFAULT_CONSUMER_LOG_LEVEL = "debug"
DEFAULT_CONSUMER_SERVER_AUTHORIZATION = "none"
DEFAULT_CONSUMER_SERVER_URL = "http://localhost:8080"
DEFAULT_CONSUMER_SERVICE_TYPE = "fluentbit"
DEFAULT_PROVIDER_LOG_LEVEL = "DEBUG"
ENV_OPAMP_CONFIG_PATH = "OPAMP_CONFIG_PATH"
ENV_PYTHONNOUSERSITE = "PYTHONNOUSERSITE"
ENV_PYTHONPATH = "PYTHONPATH"


@dataclass(frozen=True)
class Component:
    """Describe one packaged component that must install and import cleanly."""

    component_id: str
    """Stable test/report identifier for the component."""

    path: str
    """Repository-relative path to the component's Python package root."""

    imports: tuple[str, ...]
    """Primary modules that must import successfully from the installed wheel."""


COMPONENTS: tuple[Component, ...] = (
    Component("provider", "provider", ("opamp_provider.server", "shared.opamp_config")),
    Component(
        "consumer",
        "consumer",
        (
            "opamp_consumer.client",
            "opamp_consumer.fluentbit.client",
            "opamp_consumer.fluentd.client",
            "opamp_consumer.elastic_agent.client",
            "opamp_consumer.elastic_heartbeat.client",
            "opamp_consumer.simulator.client",
        ),
    ),
    Component("consumer-sim", "consumer-sim", ("consumer_sim_launcher", "opamp_consumer_sim")),
    Component("config-service", "config-service", ("config_service.app",)),
    Component(
        "client-config-generator-service",
        "client-config-generator-service",
        ("client_config_generator_service.app",),
    ),
    Component("catalog-service", "catalog-service", ("catalog_service.app",)),
    Component("cli", "cli", ("opamp_cli.main",)),
    Component("agent-broker", "agent_broker", ("opamp_broker.broker_app",)),
    Component("mcp", "mcp", ("configure_mcp_clients", "opamp_mcp_config")),
    Component(
        "plaintext-keyring",
        "svr-credentials-mgr/plaintext-keyring",
        ("opamp_plaintext_keyring.backend",),
    ),
    Component(
        "credentials-manager",
        "svr-credentials-mgr",
        ("connection_settings_builder.builder", "svr_credentials_manager_service.app"),
    ),
    Component("dev-tools", "dev-tools", ("opamp_dev_tools.cli",)),
)


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 900,
) -> dict[str, object]:
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return {
        "command": command,
        "exit_code": int(completed.returncode),
        "duration_seconds": round(time.monotonic() - started, 3),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _fail_result(component: Component, stage: str, detail: str, commands: list[dict[str, object]]) -> dict[str, object]:
    return {
        "component_id": component.component_id,
        "path": component.path,
        "distribution": None,
        "wheel": None,
        "stage": stage,
        "passed": False,
        "detail": detail,
        "commands": commands,
    }


def _read_project_metadata(component_path: Path) -> tuple[str, list[str], dict[str, list[str]]]:
    pyproject = component_path / "pyproject.toml"
    with pyproject.open("rb") as handle:
        payload = tomllib.load(handle)
    project = payload.get("project", {})
    scripts = sorted((project.get("scripts") or {}).keys())
    entry_points = {
        group: sorted(entries.keys())
        for group, entries in (project.get("entry-points") or {}).items()
        if isinstance(entries, dict)
    }
    return str(project["name"]), scripts, entry_points


def _venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _clear_directory_contents(directory: Path) -> None:
    """Remove existing report files without deleting a possible mount point."""
    directory.mkdir(parents=True, exist_ok=True)
    for child in directory.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


def _build_all_wheels(repo_root: Path, wheelhouse: Path) -> tuple[list[dict[str, object]], dict[str, Path]]:
    commands: list[dict[str, object]] = []
    wheels_by_component: dict[str, Path] = {}
    for component in COMPONENTS:
        before = set(wheelhouse.glob("*.whl"))
        component_path = repo_root / component.path
        result = _run(
            [
                sys.executable,
                "-m",
                "build",
                "--wheel",
                "--outdir",
                str(wheelhouse),
                str(component_path),
            ],
            cwd=repo_root,
        )
        commands.append(
            {
                "component_id": component.component_id,
                "stage": "build",
                **result,
            }
        )
        if result["exit_code"] != 0:
            continue
        created = sorted(set(wheelhouse.glob("*.whl")) - before, key=lambda path: path.stat().st_mtime)
        if not created:
            created = sorted(wheelhouse.glob("*.whl"), key=lambda path: path.stat().st_mtime)
        if created:
            wheels_by_component[component.component_id] = created[-1]
    return commands, wheels_by_component


def _check_imports(imports: tuple[str, ...]) -> str:
    joined = ", ".join(repr(value) for value in imports)
    return (
        "import importlib\n"
        f"modules = [{joined}]\n"
        "for module in modules:\n"
        "    importlib.import_module(module)\n"
    )


def _check_entry_points(distribution: str, scripts: list[str], entry_points: dict[str, list[str]]) -> str:
    payload = json.dumps(
        {
            "distribution": distribution,
            "scripts": scripts,
            "entry_points": entry_points,
        }
    )
    return (
        "import importlib.metadata as metadata\n"
        "payload = "
        + repr(payload)
        + "\n"
        "expected = __import__('json').loads(payload)\n"
        "dist = metadata.distribution(expected['distribution'])\n"
        "points = {(point.group, point.name) for point in dist.entry_points}\n"
        "for script in expected['scripts']:\n"
        "    assert ('console_scripts', script) in points, script\n"
        "for group, names in expected['entry_points'].items():\n"
        "    for name in names:\n"
        "        assert (group, name) in points, f'{group}:{name}'\n"
    )


def _write_import_config(clean_root: Path) -> Path:
    """Create the minimal runtime config needed by import-time module checks.

    Args:
        clean_root: Scratch directory owned by this harness run.

    Returns:
        Path to the generated OpAMP config JSON file.
    """
    config_path = clean_root / CONFIG_FILE_NAME
    payload = {
        CONFIG_PROVIDER_KEY: {
            CONFIG_PROVIDER_LOG_LEVEL_KEY: DEFAULT_PROVIDER_LOG_LEVEL,
            CONFIG_PROVIDER_TLS_KEY: {
                CONFIG_PROVIDER_TLS_ENABLED_KEY: False,
            },
            CONFIG_PROVIDER_STATE_PERSISTENCE_KEY: {
                CONFIG_PROVIDER_STATE_PERSISTENCE_ENABLED_KEY: False,
            },
        },
        CONFIG_CONSUMER_KEY: {
            CONFIG_CONSUMER_SERVER_URL_KEY: DEFAULT_CONSUMER_SERVER_URL,
            CONFIG_CONSUMER_AGENT_CONFIG_PATH_KEY: ".",
            CONFIG_CONSUMER_AGENT_ADDITIONAL_PARAMS_KEY: [],
            CONFIG_CONSUMER_HEARTBEAT_FREQUENCY_KEY: DEFAULT_CONSUMER_HEARTBEAT_FREQUENCY,
            CONFIG_CONSUMER_SERVICE_TYPE_KEY: DEFAULT_CONSUMER_SERVICE_TYPE,
            CONFIG_CONSUMER_LOG_LEVEL_KEY: DEFAULT_CONSUMER_LOG_LEVEL,
            CONFIG_CONSUMER_SERVER_AUTHORIZATION_KEY: DEFAULT_CONSUMER_SERVER_AUTHORIZATION,
            CONFIG_CONSUMER_TLS_KEY: {
                CONFIG_CONSUMER_TLS_VERIFY_SERVER_KEY: False,
            },
        },
    }
    config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return config_path


def _isolated_import_environment(config_path: Path) -> dict[str, str]:
    """Build an import-check environment that cannot see the source checkout.

    Args:
        config_path: Generated OpAMP config path to expose through the standard
            runtime override.

    Returns:
        Environment mapping for subprocess import and metadata checks.
    """
    environment = os.environ.copy()
    environment[ENV_OPAMP_CONFIG_PATH] = str(config_path)
    environment[ENV_PYTHONNOUSERSITE] = "1"
    environment.pop(ENV_PYTHONPATH, None)
    return environment


def _test_component(
    component: Component,
    *,
    repo_root: Path,
    clean_root: Path,
    wheelhouse: Path,
    wheels_by_component: dict[str, Path],
) -> dict[str, object]:
    commands: list[dict[str, object]] = []
    component_path = repo_root / component.path
    if not component_path.exists():
        return _fail_result(component, "discover", f"missing component path: {component_path}", commands)

    try:
        distribution, scripts, entry_points = _read_project_metadata(component_path)
    except (KeyError, OSError, tomllib.TOMLDecodeError) as exc:
        return _fail_result(component, "metadata", str(exc), commands)

    wheel = wheels_by_component.get(component.component_id)
    if wheel is None or not wheel.exists():
        return _fail_result(component, "build", "wheel was not produced", commands)

    venv_dir = clean_root / "venvs" / component.component_id
    result = _run([sys.executable, "-m", "venv", str(venv_dir)], cwd=repo_root)
    commands.append({"stage": "venv", **result})
    if result["exit_code"] != 0:
        return _fail_result(component, "venv", "failed to create virtual environment", commands)

    python = _venv_python(venv_dir)
    result = _run(
        [str(python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
        cwd=repo_root,
    )
    commands.append({"stage": "pip-bootstrap", **result})
    if result["exit_code"] != 0:
        return _fail_result(component, "pip-bootstrap", "failed to bootstrap pip", commands)

    result = _run(
        [str(python), "-m", "pip", "install", "--find-links", str(wheelhouse), str(wheel)],
        cwd=repo_root,
    )
    commands.append({"stage": "install", **result})
    if result["exit_code"] != 0:
        return _fail_result(component, "install", f"failed to install {wheel.name}", commands)

    result = _run([str(python), "-m", "pip", "check"], cwd=repo_root)
    commands.append({"stage": "pip-check", **result})
    if result["exit_code"] != 0:
        return _fail_result(component, "pip-check", "installed dependencies are inconsistent", commands)

    import_config_path = _write_import_config(clean_root)
    import_work_dir = clean_root / "import-workdirs" / component.component_id
    import_work_dir.mkdir(parents=True, exist_ok=True)
    import_environment = _isolated_import_environment(import_config_path)
    result = _run(
        [str(python), "-c", _check_imports(component.imports)],
        cwd=import_work_dir,
        env=import_environment,
    )
    commands.append({"stage": "import", **result})
    if result["exit_code"] != 0:
        return _fail_result(component, "import", "one or more import checks failed", commands)

    result = _run(
        [str(python), "-c", _check_entry_points(distribution, scripts, entry_points)],
        cwd=import_work_dir,
        env=import_environment,
    )
    commands.append({"stage": "entry-points", **result})
    if result["exit_code"] != 0:
        return _fail_result(component, "entry-points", "entry point metadata did not match pyproject.toml", commands)

    return {
        "component_id": component.component_id,
        "path": component.path,
        "distribution": distribution,
        "wheel": wheel.name,
        "stage": "complete",
        "passed": True,
        "detail": "wheel built, installed, dependency-checked, imported, and entry points verified",
        "commands": commands,
    }


def _write_reports(results: list[dict[str, object]], build_commands: list[dict[str, object]], results_dir: Path) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    passed = all(bool(result["passed"]) for result in results) and all(
        int(command["exit_code"]) == 0 for command in build_commands
    )
    payload = {
        "name": "component-wheel-deployment",
        "passed": passed,
        "build_commands": build_commands,
        "results": results,
    }
    (results_dir / "component-wheel-deployment-results.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Component Wheel Deployment Results",
        "",
        "| Component | Distribution | Status | Stage | Wheel |",
        "|---|---|---|---|---|",
    ]
    for result in results:
        status = "passed" if result["passed"] else "failed"
        lines.append(
            "| {component} | {distribution} | {status} | {stage} | {wheel} |".format(
                component=result["component_id"],
                distribution=result.get("distribution") or "",
                status=status,
                stage=result["stage"],
                wheel=result.get("wheel") or "",
            )
        )
    lines.extend(["", f"Overall: {'passed' if passed else 'failed'}", ""])
    (results_dir / "component-wheel-deployment-results.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace/opamp"))
    parser.add_argument("--results-dir", type=Path, default=Path("/host-output"))
    parser.add_argument("--clean-root", type=Path, default=Path("/tmp/opamp-component-wheel-deployment"))
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    clean_root = args.clean_root.resolve()
    if clean_root.exists():
        shutil.rmtree(clean_root)
    clean_root.mkdir(parents=True)
    _clear_directory_contents(args.results_dir)
    wheelhouse = clean_root / "wheelhouse"
    wheelhouse.mkdir(parents=True)

    build_commands, wheels_by_component = _build_all_wheels(repo_root, wheelhouse)
    results = [
        _test_component(
            component,
            repo_root=repo_root,
            clean_root=clean_root,
            wheelhouse=wheelhouse,
            wheels_by_component=wheels_by_component,
        )
        for component in COMPONENTS
    ]
    _write_reports(results, build_commands, args.results_dir)
    passed = all(bool(result["passed"]) for result in results) and all(
        int(command["exit_code"]) == 0 for command in build_commands
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
