"""Wheel/sdist build helpers for the MCP packaging utility."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from opamp_mcp_config.build_tool.constants import (
    ARTIFACT_GLOB,
    BUILD_FLAG_OUTDIR,
    BUILD_FLAG_SDIST,
    BUILD_FLAG_WHEEL,
    ERROR_CONFIG_ROOT_NOT_OBJECT,
    ERROR_DEPLOYMENT_NOT_OBJECT,
    ERROR_NO_WHEEL_FOUND,
    JSON_INDENT,
    MODULE_BUILD,
    MODULE_PIP,
    OUTPUT_COMMAND_PREFIX,
    OUTPUT_PACKAGE_INSTALLING_TEMPLATE,
    PACKAGE_NAME_BUILD,
    PACKAGED_DEFAULTS_PATH,
    PIP_INSTALL_SUBCOMMAND,
    PIP_SHOW_SUBCOMMAND,
    ROOT,
    SOURCE_BUILD_DIR,
    SOURCE_DEFAULTS_PATH,
    SOURCE_EGG_INFO_DIR,
    UTF8_ENCODING,
    WHEEL_GLOB,
)


def _run(command: list[str], *, cwd: Path = ROOT) -> None:
    """Run one internally assembled build command and echo it.

    Parameters
    ----------
    command:
        Argument vector built by this packaging utility.
    cwd:
        Working directory in which the build command should run.

    """
    print(f"{OUTPUT_COMMAND_PREFIX}{' '.join(command)}")
    # The caller builds command arguments from fixed packaging operations, without a shell.
    subprocess.run(command, cwd=str(cwd), check=True)  # noqa: S603


def _ensure_python_package(python_exe: str, package_name: str) -> None:
    """Ensure one trusted build dependency exists for the selected interpreter.

    Parameters
    ----------
    python_exe:
        Selected Python interpreter path.
    package_name:
        Build dependency owned by the packaging workflow.

    """
    # Both values come from fixed packaging constants or the active interpreter.
    probe = subprocess.run(  # noqa: S603
        [python_exe, "-m", MODULE_PIP, PIP_SHOW_SUBCOMMAND, package_name],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if probe.returncode == 0:
        return
    print(OUTPUT_PACKAGE_INSTALLING_TEMPLATE.format(package_name=package_name))
    _run([python_exe, "-m", MODULE_PIP, PIP_INSTALL_SUBCOMMAND, package_name])


def _clean_artifacts(out_dir: Path) -> None:
    """Remove previous packaged artifacts for this MCP utility."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for path in out_dir.glob(ARTIFACT_GLOB):
        if path.is_file():
            path.unlink()


def _clean_source_build_state() -> None:
    """Remove setuptools/build scratch directories from the source tree."""
    for path in (SOURCE_BUILD_DIR, SOURCE_EGG_INFO_DIR):
        if path.exists():
            shutil.rmtree(path)


def _prepare_packaged_defaults(
    *,
    source_path: Path = SOURCE_DEFAULTS_PATH,
    packaged_path: Path = PACKAGED_DEFAULTS_PATH,
) -> bytes | None:
    """Create packaged defaults derived from the source-tree defaults file."""
    original_content = packaged_path.read_bytes() if packaged_path.exists() else None
    payload = json.loads(source_path.read_text(encoding=UTF8_ENCODING))
    if not isinstance(payload, dict):
        raise ValueError(ERROR_CONFIG_ROOT_NOT_OBJECT.format(path=source_path))
    deployment = payload.setdefault("deployment", {})
    if not isinstance(deployment, dict):
        raise ValueError(ERROR_DEPLOYMENT_NOT_OBJECT.format(path=source_path))
    deployment["mode"] = "package"
    packaged_path.parent.mkdir(parents=True, exist_ok=True)
    packaged_path.write_text(
        json.dumps(payload, indent=JSON_INDENT) + "\n",
        encoding=UTF8_ENCODING,
    )
    return original_content


def _restore_packaged_defaults(
    original_content: bytes | None,
    *,
    packaged_path: Path = PACKAGED_DEFAULTS_PATH,
) -> None:
    """Restore or remove the generated package resource defaults file."""
    if original_content is None:
        if packaged_path.exists():
            packaged_path.unlink()
        return
    packaged_path.write_bytes(original_content)


def _latest_wheel(out_dir: Path) -> Path:
    """Return the newest matching wheel artifact from one output directory."""
    wheels = sorted(out_dir.glob(WHEEL_GLOB))
    if not wheels:
        raise RuntimeError(ERROR_NO_WHEEL_FOUND.format(out_dir=out_dir))
    return wheels[-1]


def _build_distribution(*, python_exe: str, out_dir: Path, clean: bool) -> Path:
    """Build wheel and sdist artifacts, then return the latest wheel path."""
    _ensure_python_package(python_exe, PACKAGE_NAME_BUILD)
    if clean:
        _clean_artifacts(out_dir)
        _clean_source_build_state()
    else:
        out_dir.mkdir(parents=True, exist_ok=True)

    packaged_defaults = _prepare_packaged_defaults()
    try:
        _run(
            [
                python_exe,
                "-m",
                MODULE_BUILD,
                BUILD_FLAG_WHEEL,
                BUILD_FLAG_SDIST,
                BUILD_FLAG_OUTDIR,
                str(out_dir),
                str(ROOT),
            ]
        )
        return _latest_wheel(out_dir)
    finally:
        _restore_packaged_defaults(packaged_defaults)
        if clean:
            _clean_source_build_state()


def _install_wheel(python_exe: str, wheel_path: Path) -> None:
    """Install one built wheel into the selected Python interpreter."""
    _run(
        [
            python_exe,
            "-m",
            MODULE_PIP,
            PIP_INSTALL_SUBCOMMAND,
            "--force-reinstall",
            str(wheel_path),
        ]
    )
