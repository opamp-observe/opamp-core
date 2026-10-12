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

"""Validate ST-010 sdists, SBOMs, and installed CLI help/version surfaces."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import tomllib

ARTIFACTS_KEY = "artifacts"
HELP_KEY = "help"
INSTALLED_CLI_KEY = "installed_cli"
SBOMS_KEY = "sboms"
SDISTS_KEY = "sdists"
COMPONENTS = (
    ("provider", "provider"),
    ("consumer", "consumer"),
    ("consumer-sim", "consumer-sim"),
    ("config-service", "config-service"),
    ("client-config-generator-service", "client-config-generator-service"),
    ("catalog-service", "catalog-service"),
    ("cli", "cli"),
    ("agent-broker", "agent_broker"),
    ("mcp", "mcp"),
    ("plaintext-keyring", "svr-credentials-mgr/plaintext-keyring"),
    ("credentials-manager", "svr-credentials-mgr"),
    ("dev-tools", "dev-tools"),
)
PROJECT_KEY = "project"
PROJECT_NAME_KEY = "name"
REPOSITORY_NAME = "mp3monster/fluent-opamp"
UTF8_ENCODING = "utf-8"
VERSION_KEY = "version"


def _project_name(component_path: Path) -> str:
    """Read the declared distribution name from one component pyproject file."""
    with (component_path / "pyproject.toml").open("rb") as project_handle:
        payload = tomllib.load(project_handle)
    return str(payload[PROJECT_KEY][PROJECT_NAME_KEY])


def _build_sdists(repo_root: Path, output_root: Path) -> dict[str, str]:
    """Build one source distribution for every packaged component."""
    built_sdists: dict[str, str] = {}
    for component_id, relative_path in COMPONENTS:
        component_path = repo_root / relative_path
        component_output = output_root / component_id
        component_output.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "build",
                "--sdist",
                "--outdir",
                str(component_output),
                str(component_path),
            ],
            cwd=repo_root,
            check=True,
        )
        sdists = sorted(component_output.glob("*.tar.gz"))
        if len(sdists) != 1:
            raise RuntimeError(f"expected one sdist for {component_id}, found {len(sdists)}")
        built_sdists[component_id] = sdists[0].name
    return built_sdists


def _write_sboms(repo_root: Path, wheelhouse: Path, output_root: Path) -> dict[str, str]:
    """Generate and validate a CycloneDX document for every component wheel."""
    from opamp_dev_tools.sbom import (  # pylint: disable=import-outside-toplevel
        validate_wheel_artifact_sbom,
        write_wheel_artifact_sbom,
    )

    sboms: dict[str, str] = {}
    for component_id, relative_path in COMPONENTS:
        project_name = _project_name(repo_root / relative_path)
        normalized_name = project_name.replace("-", "_")
        wheel_candidates = sorted(wheelhouse.glob(f"{normalized_name}-*.whl"))
        if len(wheel_candidates) != 1:
            raise RuntimeError(
                f"expected one wheel matching {normalized_name} for {component_id}, "
                f"found {len(wheel_candidates)}"
            )
        wheel_path = wheel_candidates[0]
        sbom_path = output_root / f"{component_id}.cyclonedx.json"
        write_wheel_artifact_sbom(
            repo_root=repo_root,
            python_exe=sys.executable,
            artifact=wheel_path,
            sbom_path=sbom_path,
            root_component_name=project_name,
            repo=REPOSITORY_NAME,
            component_dir=relative_path,
        )
        validate_wheel_artifact_sbom(
            artifact=wheel_path,
            sbom_path=sbom_path,
            root_component_name=project_name,
            repo=REPOSITORY_NAME,
        )
        sboms[component_id] = sbom_path.name
    return sboms


def _verify_installed_cli(clean_root: Path) -> dict[str, str]:
    """Run help and version using the isolated CLI wheel environment."""
    cli_path = clean_root / "venvs" / "cli" / "bin" / "opamp-cli"
    help_result = subprocess.run(
        [str(cli_path), "--help"],
        text=True,
        capture_output=True,
        check=True,
    )
    version_result = subprocess.run(
        [str(cli_path), "--version"],
        text=True,
        capture_output=True,
        check=True,
    )
    if "Usage:" not in help_result.stdout:
        raise RuntimeError("installed CLI help output did not contain Usage")
    if not version_result.stdout.strip().startswith("opamp-cli "):
        raise RuntimeError("installed CLI version output was missing the component name")
    return {
        HELP_KEY: help_result.stdout,
        VERSION_KEY: version_result.stdout.strip(),
    }


def main() -> int:
    """Parse paths and validate all supplemental ST-010 release outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--clean-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    sdist_root = arguments.clean_root / "sdists"
    sbom_root = arguments.output_dir / "sbom"
    sbom_root.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        SDISTS_KEY: _build_sdists(arguments.repo_root, sdist_root),
        SBOMS_KEY: _write_sboms(
            arguments.repo_root,
            arguments.clean_root / "wheelhouse",
            sbom_root,
        ),
        INSTALLED_CLI_KEY: _verify_installed_cli(arguments.clean_root),
    }
    (arguments.output_dir / "artifacts.json").write_text(
        json.dumps({ARTIFACTS_KEY: payload}, indent=2) + "\n",
        encoding=UTF8_ENCODING,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
