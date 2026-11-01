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

"""Run config-service backend linting and unit tests with coverage enabled."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_COVERAGE_INDEX = ROOT / "htmlcov" / "index.html"
XML_COVERAGE_REPORT = ROOT / "coverage.xml"


def run_step(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def report_coverage_outputs() -> None:
    """Summarize the generated coverage report artifacts for developers."""

    print(f"Coverage XML report: {XML_COVERAGE_REPORT}")
    print(f"Coverage HTML report: {HTML_COVERAGE_INDEX}")


def main() -> None:
    run_step(
        sys.executable,
        "-m",
        "ruff",
        "check",
        "src/config_service",
        "tests",
        "dev-tools",
        "setup.py",
        "build_config.py",
    )
    run_step(sys.executable, "-m", "pytest")
    report_coverage_outputs()


if __name__ == "__main__":
    main()
