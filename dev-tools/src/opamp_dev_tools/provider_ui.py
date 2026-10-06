# Copyright 2026 mp3monster.org
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Provider web UI compaction helpers for the developer CLI."""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path


def compact_provider_ui_assets(
    runtime: object,
    *,
    html_dir: str = "provider/src/opamp_provider/html",
    clean_only: bool = False,
) -> bool:
    """Minify provider web UI JS assets into `.mini.js` files using esbuild."""
    repo_root = Path(getattr(runtime, "repo_root")).resolve()
    resolved_html_dir = _resolve_html_dir(repo_root, html_dir)
    js_filenames = _provider_ui_js_filenames(repo_root)
    if not resolved_html_dir.exists():
        raise RuntimeError(f"HTML directory not found: {resolved_html_dir}")

    for source_name in js_filenames:
        mini_path = resolved_html_dir / _mini_filename(source_name)
        if mini_path.exists():
            mini_path.unlink()
            runtime.info(f"Removed {mini_path}")

    if clean_only:
        runtime.info("Provider UI clean-only complete.")
        return False

    npx_command = _resolve_npx_command()

    for source_name in js_filenames:
        source_path = resolved_html_dir / source_name
        if not source_path.exists():
            raise RuntimeError(f"source UI JS file not found: {source_path}")
        mini_path = resolved_html_dir / _mini_filename(source_name)
        runtime.run(
            [
                npx_command,
                "--yes",
                "esbuild",
                str(source_path),
                "--minify",
                "--legal-comments=none",
                f"--outfile={mini_path}",
            ],
            cwd=repo_root,
        )
        runtime.info(
            f"Built {mini_path.name} ({mini_path.stat().st_size} bytes) from "
            f"{source_name} ({source_path.stat().st_size} bytes)"
        )

    runtime.info("Provider UI compaction complete.")
    return False


def _resolve_html_dir(repo_root: Path, html_dir: str) -> Path:
    path = Path(html_dir).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (repo_root / path).resolve()


def _resolve_npx_command() -> str:
    """Return the executable npx path so Windows ``.cmd`` launchers work."""
    npx_command = shutil.which("npx")
    if npx_command:
        return npx_command
    raise RuntimeError(
        "npx was not found on PATH. Install Node.js (which includes npm/npx) "
        "before running UI compaction."
    )


def _mini_filename(source_filename: str) -> str:
    """Return deterministic compacted filename for one source JS filename."""
    return source_filename.replace(".js", ".mini.js")


def _provider_ui_js_filenames(repo_root: Path) -> tuple[str, ...]:
    """Load the canonical provider UI asset list from provider source."""
    module_path = repo_root / "provider" / "src" / "opamp_provider" / "ui_assets.py"
    if not module_path.exists():
        raise RuntimeError(f"provider UI asset definitions not found: {module_path}")

    spec = importlib.util.spec_from_file_location("opamp_provider.ui_assets", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load provider UI asset definitions: {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    filenames = getattr(module, "PROVIDER_UI_JS_FILENAMES", None)
    if not isinstance(filenames, tuple) or not all(
        isinstance(item, str) and item.endswith(".js") for item in filenames
    ):
        raise RuntimeError(
            "provider UI asset definitions must expose PROVIDER_UI_JS_FILENAMES "
            "as a tuple[str, ...] of .js filenames"
        )
    return filenames
