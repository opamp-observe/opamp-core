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

"""Virtual environment setup workflow for the OpAMP CLI."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

DEFAULT_DEVELOPMENT_EXTRAS = "dev"
DEVELOPER_TOOLS_EXTRAS = "dev,security"
DEVELOPER_TOOLS_PATH = Path("dev-tools")
OPAMP_VENV_PYTHON_COMPONENTS = (
    Path("cli"),
    Path("provider"),
    Path("consumer"),
    Path("consumer-sim"),
    Path("config-service"),
    Path("catalog-service"),
    Path("agent_broker"),
    Path("mcp"),
    Path("dev-tools"),
    Path("svr-credentials-mgr") / "plaintext-keyring",
    Path("svr-credentials-mgr"),
)
OPAMP_VENV_NODE_TOOLING = (
    Path("catalog-service"),
    Path("config-service"),
    Path("config-service") / "frontend",
    Path("svr-credentials-mgr"),
    Path("tools") / "mermaid",
)


def resolve_setup_venv_path(raw_path: str, *, repo_root: Path) -> Path:
    """Resolve a setup-venv target path relative to the repository root."""
    candidate = Path(str(raw_path or "").strip()).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (repo_root / candidate).resolve()


def parse_setup_venv_args(args: list[str], *, repo_root: Path) -> dict[str, Any]:
    """Parse setup-venv options from command-line arguments."""
    options: dict[str, Any] = {
        "venv_dir": (repo_root / ".venv").resolve(),
        "dry_run": False,
        "skip_node": False,
    }
    index = 0
    while index < len(args):
        option = str(args[index])
        if option == "--dry-run":
            options["dry_run"] = True
        elif option == "--skip-node":
            options["skip_node"] = True
        elif option == "--venv":
            index += 1
            if index >= len(args):
                raise ValueError("setup-venv --venv requires a path")
            options["venv_dir"] = resolve_setup_venv_path(args[index], repo_root=repo_root)
        elif option.startswith("--venv="):
            options["venv_dir"] = resolve_setup_venv_path(option.split("=", 1)[1], repo_root=repo_root)
        else:
            raise ValueError(f"unknown setup-venv option: {option}")
        index += 1
    return options


def venv_bin_dir(venv_dir: Path, *, is_windows: bool) -> Path:
    """Return the scripts/bin directory for one virtual environment."""
    return venv_dir / ("Scripts" if is_windows else "bin")


def venv_python_executable(venv_dir: Path, *, is_windows: bool) -> Path:
    """Return the Python executable path inside one virtual environment."""
    executable_name = "python.exe" if is_windows else "python"
    return (venv_bin_dir(venv_dir, is_windows=is_windows) / executable_name).resolve()


def powershell_single_quote(value: str | Path) -> str:
    """Return one PowerShell single-quoted literal."""
    return "'" + str(value).replace("'", "''") + "'"


def setup_venv_activation_prompt_available() -> bool:
    """Return whether setup-venv should ask about opening an activated shell."""
    return bool(sys.stdin.isatty() and sys.stdout.isatty())


def open_setup_venv_shell(
    venv_dir: Path,
    *,
    repo_root: Path,
    is_windows: bool,
) -> int:
    """Open a child shell with the repository virtual environment activated."""
    resolved_repo_root = repo_root.resolve()
    resolved_venv = venv_dir.resolve()
    if is_windows:
        activate_ps1 = resolved_venv / "Scripts" / "Activate.ps1"
        powershell = (
            shutil.which("pwsh")
            or shutil.which("powershell")
            or shutil.which("powershell.exe")
        )
        if powershell and activate_ps1.is_file():
            command = (
                "& { "
                f". {powershell_single_quote(activate_ps1)}; "
                f"Set-Location -LiteralPath {powershell_single_quote(resolved_repo_root)}; "
                "Write-Host 'OpAMP virtual environment activated. Type exit to return.' "
                "}"
            )
            print("Opening an activated PowerShell session. Type `exit` to return.")
            completed = subprocess.run(  # noqa: S603
                [
                    powershell,
                    "-NoExit",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    command,
                ],
                check=False,
            )
            return int(completed.returncode)

        activate_bat = resolved_venv / "Scripts" / "activate.bat"
        command_processor = os.environ.get("ComSpec") or shutil.which("cmd.exe") or "cmd.exe"
        if activate_bat.is_file():
            command = f'call "{activate_bat}" && cd /d "{resolved_repo_root}"'
            print("Opening an activated cmd.exe session. Type `exit` to return.")
            completed = subprocess.run(  # noqa: S603
                [command_processor, "/K", command],
                check=False,
            )
            return int(completed.returncode)

        print(
            f"Could not find virtual environment activation files under {resolved_venv}",
            file=sys.stderr,
        )
        return 1

    activate_script = resolved_venv / "bin" / "activate"
    shell = os.environ.get("SHELL") or shutil.which("bash") or shutil.which("sh") or "sh"
    if activate_script.is_file():
        command = (
            f". {shlex.quote(str(activate_script))}; "
            f"cd {shlex.quote(str(resolved_repo_root))}; "
            "echo 'OpAMP virtual environment activated. Type exit to return.'; "
            f"exec {shlex.quote(shell)} -i"
        )
        print(f"Opening an activated shell: {shell}. Type `exit` to return.")
        completed = subprocess.run([shell, "-c", command], check=False)  # noqa: S603
        return int(completed.returncode)

    env = os.environ.copy()
    env["VIRTUAL_ENV"] = str(resolved_venv)
    env.pop("PYTHONHOME", None)
    env["PATH"] = f"{resolved_venv / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    print(f"Opening a shell with VIRTUAL_ENV set: {shell}. Type `exit` to return.")
    completed = subprocess.run(  # noqa: S603
        [shell],
        cwd=str(resolved_repo_root),
        env=env,
        check=False,
    )
    return int(completed.returncode)


def prompt_setup_venv_activation(
    venv_dir: Path,
    *,
    input_reader: Callable[[str], str] | None = None,
    prompt_text: Callable[[str], str],
    parse_yes_no: Callable[[str, bool], bool | None],
    open_shell: Callable[[Path], int],
    activation_prompt_available: Callable[[], bool] = setup_venv_activation_prompt_available,
) -> int:
    """Prompt the user to open an activated virtual environment shell."""
    resolved_venv = venv_dir.resolve()
    if input_reader is None and activation_prompt_available() is not True:
        print(f"Virtual environment is ready: {resolved_venv}")
        return 0

    while True:
        try:
            raw_value = prompt_text("Activate the virtual environment now? [Y/n]: ")
        except (EOFError, KeyboardInterrupt):
            print()
            print(f"Virtual environment is ready: {resolved_venv}")
            return 0
        choice = parse_yes_no(raw_value, True)
        if choice is None:
            print("Please answer yes or no.")
            continue
        if choice is not True:
            print(f"Virtual environment is ready: {resolved_venv}")
            return 0
        return open_shell(resolved_venv)


def run_setup_venv_step(
    argv: list[str],
    *,
    cwd: Path,
    dry_run: bool,
    command_text_from_args: Callable[[list[str]], str],
    windows_no_console_kwargs: Callable[[], dict[str, Any]],
) -> int:
    """Run or print one setup-venv command."""
    prefix = "Would run" if dry_run else "Running"
    print(f"{prefix}: {command_text_from_args(argv)} (cwd={cwd.resolve()})")
    if dry_run:
        return 0
    completed = subprocess.run(  # noqa: S603
        argv,
        cwd=str(cwd),
        check=False,
        **windows_no_console_kwargs(),
    )
    return int(completed.returncode)


def python_setup_venv_steps(
    *,
    repo_root: Path,
    venv_dir: Path,
    is_windows: bool,
    python_executable: str = sys.executable,
) -> list[tuple[list[str], Path]]:
    """Return ordered Python setup commands for the OpAMP repository environment."""
    venv_python = venv_python_executable(venv_dir, is_windows=is_windows)
    steps: list[tuple[list[str], Path]] = [
        ([python_executable, "-m", "venv", str(venv_dir)], repo_root),
        (
            [
                str(venv_python),
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip",
                "setuptools>=82",
                "wheel",
                "build",
                "hatchling>=1.25",
            ],
            repo_root,
        ),
    ]

    root_requirements = repo_root / "requirements.txt"
    if root_requirements.is_file() and root_requirements.stat().st_size > 0:
        steps.append(
            (
                [str(venv_python), "-m", "pip", "install", "-r", str(root_requirements)],
                repo_root,
            )
        )

    for relative_path in OPAMP_VENV_PYTHON_COMPONENTS:
        component_dir = (repo_root / relative_path).resolve()
        if (component_dir / "pyproject.toml").is_file():
            extras = (
                DEVELOPER_TOOLS_EXTRAS
                if relative_path == DEVELOPER_TOOLS_PATH
                else DEFAULT_DEVELOPMENT_EXTRAS
            )
            steps.append(
                (
                    [
                        str(venv_python),
                        "-m",
                        "pip",
                        "install",
                        "-e",
                        f"{component_dir}[{extras}]",
                    ],
                    repo_root,
                )
            )
    return steps


def node_setup_venv_steps(repo_root: Path, *, npm_executable: str) -> list[tuple[list[str], Path]]:
    """Return ordered Node tooling install commands for local dev tools."""
    steps: list[tuple[list[str], Path]] = []
    for relative_path in OPAMP_VENV_NODE_TOOLING:
        package_dir = (repo_root / relative_path).resolve()
        if (package_dir / "package.json").is_file():
            steps.append(([npm_executable, "install"], package_dir))
    return steps


def execute_setup_venv_workflow(
    args: list[str],
    *,
    repo_root: Path,
    is_windows: bool,
    command_text_from_args: Callable[[list[str]], str],
    windows_no_console_kwargs: Callable[[], dict[str, Any]],
    prompt_activation: Callable[[Path], int],
) -> int:
    """Create/update the OpAMP repository virtual environment and local tooling."""
    resolved_repo_root = repo_root.resolve()
    options = parse_setup_venv_args(args, repo_root=resolved_repo_root)
    venv_dir = Path(options["venv_dir"]).resolve()
    dry_run = bool(options["dry_run"])
    skip_node = bool(options["skip_node"])

    print(f"OpAMP repository: {resolved_repo_root}")
    print(f"Virtual environment: {venv_dir}")
    if dry_run:
        print("Dry run: commands will be printed but not executed.")

    for argv, cwd in python_setup_venv_steps(
        repo_root=resolved_repo_root,
        venv_dir=venv_dir,
        is_windows=is_windows,
    ):
        code = run_setup_venv_step(
            argv,
            cwd=cwd,
            dry_run=dry_run,
            command_text_from_args=command_text_from_args,
            windows_no_console_kwargs=windows_no_console_kwargs,
        )
        if code != 0:
            print(f"setup-venv failed with exit code {code}", file=sys.stderr)
            return code

    if skip_node:
        print("Skipping Node tooling install because --skip-node was supplied.")
    else:
        npm_executable = shutil.which("npm")
        if npm_executable is None:
            if dry_run:
                npm_executable = "npm"
            else:
                print(
                    "setup-venv could not find npm on PATH; rerun with --skip-node "
                    "to install only Python dependencies.",
                    file=sys.stderr,
                )
                return 1
        for argv, cwd in node_setup_venv_steps(resolved_repo_root, npm_executable=npm_executable):
            code = run_setup_venv_step(
                argv,
                cwd=cwd,
                dry_run=dry_run,
                command_text_from_args=command_text_from_args,
                windows_no_console_kwargs=windows_no_console_kwargs,
            )
            if code != 0:
                print(f"setup-venv failed with exit code {code}", file=sys.stderr)
                return code

    if dry_run:
        print("Dry run complete.")
    else:
        print("OpAMP virtual environment setup complete.")
        return prompt_activation(venv_dir)
    return 0
