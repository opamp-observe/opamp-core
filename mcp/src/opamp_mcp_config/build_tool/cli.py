"""CLI entrypoint helpers for the MCP build-tool packaging utility."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from opamp_mcp_config.build_tool.constants import (
    DEFAULT_DIST_DIR,
    DEFAULT_SBOM_PATH,
    OUTPUT_BUILT_WHEEL_TEMPLATE,
    OUTPUT_WROTE_SBOM_TEMPLATE,
)
from opamp_mcp_config.build_tool.distribution import _build_distribution, _install_wheel
from opamp_mcp_config.build_tool.sbom import _write_sbom


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the MCP packaging helper."""
    parser = argparse.ArgumentParser(
        description="Build the OpAMP MCP config tool wheel and SBOM."
    )
    parser.add_argument("--python", default=sys.executable, help="Python executable to use")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_DIST_DIR,
        help="Wheel output directory",
    )
    parser.add_argument(
        "--sbom-path",
        type=Path,
        default=DEFAULT_SBOM_PATH,
        help="CycloneDX SBOM output path",
    )
    parser.add_argument("--install", action="store_true", help="Install the built wheel with pip")
    parser.add_argument(
        "--skip-sbom",
        action="store_true",
        help="Build artifacts without writing SBOM",
    )
    parser.add_argument("--no-clean", action="store_true", help="Keep existing MCP build artifacts")
    return parser


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
