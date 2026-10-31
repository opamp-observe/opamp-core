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

"""Generate a CycloneDX SBOM for the standalone config-service package.

Relationship to `dev-tools/src/opamp_dev_tools/sbom.py`:
- this file is the config-service-specific wrapper that supplies package
  metadata, output defaults, and git label properties
- `opamp_dev_tools.sbom` is the canonical repo-side SBOM implementation shared
  by developer tooling without putting SBOM logic into the production `shared`
  package

This script delegates dependency discovery to the open-source `cyclonedx-py`
tool from the `cyclonedx-bom` package, then applies OpAMP-specific metadata:
1. root component identity is kept aligned with package metadata (`build_config`)
2. git label metadata from `update_component_versions.py` is attached as
   traceability properties (without replacing package identity/version)
3. root dependency graph entry is rewritten for stable SBOM consumers
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
DEV_TOOLS_SRC = REPO_ROOT / "dev-tools" / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(DEV_TOOLS_SRC) not in sys.path:
    sys.path.insert(0, str(DEV_TOOLS_SRC))

from opamp_dev_tools.sbom import (  # noqa: E402
    build_requirements_application_sbom_payload,
    ensure_python_package,
    write_sbom_file,
)

DEFAULT_OUTPUT = ROOT / "sbom" / "config-service-sbom.cdx.json"


def _load_version_helper_module() -> Any | None:
    """Load shared git label helpers used by the repository pre-commit hook."""
    module_path = REPO_ROOT / "scripts" / "update_component_versions.py"
    if not module_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("update_component_versions", module_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve_precommit_git_labels() -> dict[str, str]:
    """Return git label metadata from the shared pre-commit helper script."""
    helper = _load_version_helper_module()
    if helper is None:
        return {}
    try:
        label = str(helper._resolve_latest_git_label(REPO_ROOT) or "").strip()
        commits_since_label = int(helper._resolve_commits_since_label(REPO_ROOT, label) or 0)
        effective_label = str(
            helper._resolve_effective_label(label, commits_since_label=commits_since_label) or ""
        ).strip()
        metadata: dict[str, str] = {}
        if label:
            metadata["opamp.git_label"] = label
        if effective_label:
            metadata["opamp.effective_label"] = effective_label
        metadata["opamp.commits_since_label"] = str(commits_since_label)
    except Exception:
        return {}
    return metadata


def build_sbom() -> dict[str, Any]:
    from build_config import INSTALL_REQUIRES, PACKAGE_NAME, PACKAGE_VERSION

    return build_requirements_application_sbom_payload(
        repo_root=REPO_ROOT,
        python_exe=sys.executable,
        requirements=list(INSTALL_REQUIRES),
        root_component_name=str(PACKAGE_NAME).strip(),
        root_component_version=str(PACKAGE_VERSION).strip(),
        root_properties=_resolve_precommit_git_labels(),
        cwd=ROOT,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate config-service SBOM")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output SBOM path")
    args = parser.parse_args()

    ensure_python_package(
        repo_root=REPO_ROOT,
        python_exe=sys.executable,
        package_name="cyclonedx-bom",
    )
    write_sbom_file(build_sbom(), args.output)


if __name__ == "__main__":
    main()
