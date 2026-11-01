#!/usr/bin/env python3
#
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

"""Compatibility wrapper for the OpAMP MCP build-tool packaging helpers.

The implementation lives in `opamp_mcp_config.build_tool`, while this file
remains the executable/test-facing facade for source-tree workflows.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = Path(__file__).resolve().parent / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from opamp_mcp_config.build_tool import (  # noqa: E402
    DEFAULT_DIST_DIR,
    DEFAULT_SBOM_PATH,
    OUTPUT_BUILT_WHEEL_TEMPLATE,
    OUTPUT_WROTE_SBOM_TEMPLATE,
    _build_distribution,
    _build_parser,
    _build_sbom_payload,
    _clean_artifacts,
    _clean_source_build_state,
    _ensure_python_package,
    _install_wheel,
    _latest_wheel,
    _normalize_dist_name,
    _prepare_packaged_defaults,
    _read_wheel_metadata,
    _requirement_name,
    _restore_packaged_defaults,
    _run,
    _sha256,
    _write_sbom,
)


def main() -> None:
    """Build the MCP config packaging artifacts and optional wheel install."""
    args = _build_parser().parse_args()

    wheel_path = _build_distribution(
        python_exe=args.python,
        out_dir=args.out_dir,
        clean=not args.no_clean,
    )
    print(OUTPUT_BUILT_WHEEL_TEMPLATE.format(wheel_path=wheel_path))

    if not args.skip_sbom:
        sbom_path = _write_sbom(wheel_path, args.sbom_path)
        print(OUTPUT_WROTE_SBOM_TEMPLATE.format(sbom_path=sbom_path))

    if args.install:
        _install_wheel(args.python, wheel_path)


if __name__ == "__main__":
    main()
