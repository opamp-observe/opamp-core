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

"""Generate Fluent Bit schema and attribute-reference Markdown documents."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_SERVICE_ROOT = REPO_ROOT / "config-service"
QUICK_REFERENCE_DIR = CONFIG_SERVICE_ROOT / "dev-tools" / "quick-references"
SCHEMA_SCRIPT = QUICK_REFERENCE_DIR / "generate_fluentbit_schema_quick_reference.py"
ATTRIBUTE_SCRIPT = QUICK_REFERENCE_DIR / "generate_fluentbit_plugin_attribute_reference.py"
def _run(script: Path, *, versions: list[str]) -> None:
    """Run one quick-reference generator for every requested Fluent Bit version.

    Parameters
    ----------
    script:
        Generator entry point executed through the active Python interpreter.
    versions:
        Fluent Bit versions passed as repeated ``--version`` options.

    """
    command = [sys.executable, str(script)]
    for version in versions:
        command.extend(["--version", version])
    subprocess.run(command, check=True, cwd=str(REPO_ROOT))  # noqa: S603


def parse_args() -> argparse.Namespace:
    """Parse selected versions and reference types from command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate Fluent Bit markdown quick references from local schemas "
            "and catalog JSON."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="append",
        dest="versions",
        required=True,
        help="Fluent Bit version to generate. Repeat for multiple versions.",
    )
    parser.add_argument(
        "--skip-schema-reference",
        action="store_true",
        help="Skip the schema quick-reference markdown generator.",
    )
    parser.add_argument(
        "--skip-attribute-reference",
        action="store_true",
        help="Skip the plugin attribute reference markdown generator.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the selected schema and attribute-reference generators."""
    args = parse_args()
    if not args.skip_schema_reference:
        _run(SCHEMA_SCRIPT, versions=args.versions)
    if not args.skip_attribute_reference:
        _run(ATTRIBUTE_SCRIPT, versions=args.versions)


if __name__ == "__main__":
    main()
