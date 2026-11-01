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

"""Start catalog-service from the repository using a local config file."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    """Return the repository root from this script location."""
    return Path(__file__).resolve().parents[2]


def _default_config_path() -> Path:
    """Return the default freestanding example config path."""
    return (_repo_root() / "catalog-service" / "config" / "catalog-service.freestanding.example.json").resolve()


def _catalog_service_src() -> Path:
    """Return the catalog-service source directory."""
    return (_repo_root() / "catalog-service" / "src").resolve()


def _build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for the launcher."""
    parser = argparse.ArgumentParser(
        description="Start catalog-service from the repository workspace.",
    )
    parser.add_argument(
        "--config-path",
        default=str(_default_config_path()),
        help="Path to the catalog-service JSON config file.",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind address for the Quart server.",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Override the listen port from config.",
    )
    return parser


def main() -> int:
    """Launch the standalone catalog-service app with repo-local imports."""
    parser = _build_parser()
    args = parser.parse_args()

    src_path = _catalog_service_src()
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from catalog_service.app import create_app
    from catalog_service.runtime_config import ENV_CATALOG_SERVICE_CONFIG_PATH, resolve_web_port

    os.environ[ENV_CATALOG_SERVICE_CONFIG_PATH] = str(Path(args.config_path).resolve())

    app = create_app(mode="standalone", config_path=args.config_path)
    app.run(
        host=args.host,
        port=args.port or resolve_web_port(args.config_path),
        debug=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
