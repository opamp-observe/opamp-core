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

"""JavaScript and TypeScript cyclomatic-complexity checks for developer builds."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from .runtime import CommandRuntimeError

if TYPE_CHECKING:
    from .runtime import CommandRuntime


DEFAULT_MAX_COMPLEXITY = 20
SUPPORTED_SOURCE_SUFFIXES = frozenset(
    {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"}
)
IGNORED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "htmlcov",
        "node_modules",
        "runtime",
    }
)
IGNORED_FILE_SUFFIXES = (".mini.js", ".min.js")
DEFAULT_TARGET_PATHS = (
    "catalog-service/src",
    "catalog-service/ui-tests",
    "catalog-service/playwright.config.js",
    "config-service/src",
    "config-service/frontend/src",
    "config-service/frontend/vite.config.ts",
    "config-service/ui-tests",
    "config-service/ui-unit-tests",
    "config-service/dev-tools/playwright_chapter_batch_runner.mjs",
    "config-service/playwright.config.js",
    "config-service/vitest.config.js",
    "provider/src",
    "provider/ui-tests",
    "provider/playwright.config.js",
)
ESLINT_RUNNER_PACKAGES = ("eslint@9", "@typescript-eslint/parser@8")


def run_javascript_complexity_checks(
    runtime: CommandRuntime,
    *,
    max_complexity: int = DEFAULT_MAX_COMPLEXITY,
    target_paths: list[str] | None = None,
) -> bool:
    """Run ESLint complexity checks across repository JavaScript/TypeScript sources."""
    if int(max_complexity) <= 0:
        raise RuntimeError("max complexity must be a positive integer")

    _require_npx()
    repo_root = Path(runtime.repo_root).resolve()
    selected_targets = list(target_paths or DEFAULT_TARGET_PATHS)
    files = _collect_target_files(repo_root, target_paths=selected_targets)
    if not files:
        raise RuntimeError(
            "no JavaScript or TypeScript source files matched the selected complexity-check paths"
        )

    runtime.info(
        "Running JavaScript/TypeScript cyclomatic-complexity checks "
        f"(max={int(max_complexity)}) across {len(files)} file(s)."
    )
    with tempfile.TemporaryDirectory(prefix="opamp-js-complexity-") as temp_dir:
        config_path = Path(temp_dir) / "eslint-complexity.config.mjs"
        config_path.write_text(
            _eslint_flat_config_text(max_complexity=int(max_complexity)),
            encoding="utf-8",
        )
        command = _eslint_command(
            repo_root=repo_root,
            config_path=config_path,
            files=files,
        )
        completed = runtime.run(
            command,
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )

    output = _combined_process_output(completed)
    if output:
        _emit_command_output(runtime, output)

    if int(completed.returncode) == 0:
        runtime.info("JavaScript/TypeScript complexity checks passed.")
        return False

    if int(completed.returncode) == 1:
        runtime.record_issue(
            "JavaScript/TypeScript cyclomatic-complexity violations were found.",
            category="javascript-complexity",
            details={
                "max_complexity": int(max_complexity),
                "target_paths": selected_targets,
                "file_count": len(files),
                "output": output,
            },
        )
        return True

    runtime.record_error(
        "ESLint complexity check failed to execute successfully.",
        category="javascript-complexity",
        command=command,
        details={
            "returncode": int(completed.returncode),
            "output": output,
        },
    )
    raise CommandRuntimeError("JavaScript/TypeScript complexity check failed to execute")


def _collect_target_files(repo_root: Path, *, target_paths: list[str]) -> list[Path]:
    """Return sorted source files for the configured complexity-check targets."""
    collected: set[Path] = set()
    for raw_target in target_paths:
        target = _resolve_target_path(repo_root, raw_target)
        if target.is_file():
            if _is_supported_source_file(target):
                collected.add(target.resolve())
            continue
        if target.is_dir() is not True:
            continue
        for path in target.rglob("*"):
            if path.is_dir():
                continue
            if _path_contains_ignored_directory(path.relative_to(repo_root)):
                continue
            if _is_supported_source_file(path):
                collected.add(path.resolve())
    return sorted(collected)


def _resolve_target_path(repo_root: Path, raw_target: str) -> Path:
    """Resolve one configured or user-supplied path against the repository root."""
    candidate = Path(str(raw_target or "").strip()).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (repo_root / candidate).resolve()


def _path_contains_ignored_directory(relative_path: Path) -> bool:
    """Return whether a path traverses a directory ignored by complexity checks."""
    return any(part in IGNORED_DIRECTORY_NAMES for part in relative_path.parts[:-1])


def _is_supported_source_file(path: Path) -> bool:
    """Return whether a file should be included in the complexity run."""
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SOURCE_SUFFIXES:
        return False
    lower_name = path.name.lower()
    if any(lower_name.endswith(ignored_suffix) for ignored_suffix in IGNORED_FILE_SUFFIXES):
        return False
    return True


def _eslint_flat_config_text(*, max_complexity: int) -> str:
    """Return a temporary flat ESLint config that enforces complexity limits."""
    return "\n".join(
        [
            'import tsParser from "@typescript-eslint/parser";',
            "",
            "export default [",
            "  {",
            '    files: ["**/*.js", "**/*.jsx", "**/*.mjs", "**/*.cjs"],',
            "    languageOptions: {",
            '      ecmaVersion: "latest",',
            '      sourceType: "module",',
            "      parserOptions: {",
            "        ecmaFeatures: { jsx: true },",
            "      },",
            "    },",
            "    rules: {",
            f'      complexity: ["error", {{ max: {int(max_complexity)} }}],',
            "    },",
            "  },",
            "  {",
            '    files: ["**/*.ts", "**/*.tsx", "**/*.mts", "**/*.cts"],',
            "    languageOptions: {",
            "      parser: tsParser,",
            "      parserOptions: {",
            '        ecmaVersion: "latest",',
            '        sourceType: "module",',
            "        ecmaFeatures: { jsx: true },",
            "      },",
            "    },",
            "    rules: {",
            f'      complexity: ["error", {{ max: {int(max_complexity)} }}],',
            "    },",
            "  },",
            "];",
            "",
        ]
    )


def _eslint_command(*, repo_root: Path, config_path: Path, files: list[Path]) -> list[str]:
    """Build the `npx eslint` command used for complexity enforcement."""
    command = ["npx", "--yes"]
    for package_name in ESLINT_RUNNER_PACKAGES:
        command.extend(["--package", package_name])
    command.extend(
        [
            "eslint",
            "--no-config-lookup",
            "--config",
            str(config_path),
            "--format",
            "stylish",
        ]
    )
    command.extend(_display_path(repo_root, path) for path in files)
    return command


def _display_path(repo_root: Path, path: Path) -> str:
    """Return a stable display path for one file relative to the repo root when possible."""
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _combined_process_output(completed: subprocess.CompletedProcess[str]) -> str:
    """Return combined stdout/stderr output from one completed ESLint process."""
    stdout = str(completed.stdout or "").strip()
    stderr = str(completed.stderr or "").strip()
    if stdout and stderr:
        return stdout + "\n" + stderr
    return stdout or stderr


def _emit_command_output(runtime: CommandRuntime, output: str) -> None:
    """Echo tool output through the runtime one line at a time."""
    for line in str(output or "").splitlines():
        runtime.info(line)


def _require_npx() -> None:
    """Require `npx` to be available before launching ESLint."""
    if shutil.which("npx"):
        return
    raise RuntimeError(
        "npx was not found on PATH. Install Node.js (which includes npm/npx) "
        "before running JavaScript complexity checks."
    )
