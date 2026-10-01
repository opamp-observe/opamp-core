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

from __future__ import annotations

from pathlib import Path

import opamp_dev_tools.provider_ui as provider_ui


class _RuntimeStub:
    """Capture provider UI compaction commands and create simulated outputs."""

    def __init__(self, repo_root: Path) -> None:
        """Initialize captured commands for the supplied repository root."""
        self.repo_root = repo_root
        self.commands: list[list[str]] = []
        self.messages: list[str] = []

    def run(self, command: list[str], *, cwd: Path | None = None, **_: object) -> None:
        """Record a command and materialize its requested output asset."""
        del cwd
        self.commands.append(command)
        outfile_flag = next((part for part in command if part.startswith("--outfile=")), "")
        if outfile_flag:
            outfile = Path(outfile_flag.partition("=")[2])
            outfile.parent.mkdir(parents=True, exist_ok=True)
            outfile.write_text("minified();\n", encoding="utf-8")

    def info(self, message: str) -> None:
        """Record one informational message from the helper."""
        self.messages.append(message)


def test_compact_provider_ui_assets_builds_mini_files(tmp_path: Path, monkeypatch) -> None:
    _write_provider_ui_assets_module(
        tmp_path,
        filenames=("web_ui_state.js", "web_ui_bindings.js"),
    )
    html_dir = tmp_path / "provider" / "src" / "opamp_provider" / "html"
    html_dir.mkdir(parents=True, exist_ok=True)
    (html_dir / "web_ui_state.js").write_text("const state = 1;\n", encoding="utf-8")
    (html_dir / "web_ui_bindings.js").write_text("const bindings = 2;\n", encoding="utf-8")
    monkeypatch.setattr(provider_ui.shutil, "which", lambda tool: "/usr/bin/npx" if tool == "npx" else None)
    runtime = _RuntimeStub(tmp_path)

    issues_found = provider_ui.compact_provider_ui_assets(runtime)

    assert issues_found is False
    assert len(runtime.commands) == 2
    assert runtime.commands[0][0:3] == ["/usr/bin/npx", "--yes", "esbuild"]
    assert (html_dir / "web_ui_state.mini.js").read_text(encoding="utf-8") == "minified();\n"
    assert (html_dir / "web_ui_bindings.mini.js").read_text(encoding="utf-8") == "minified();\n"
    assert runtime.messages[-1] == "Provider UI compaction complete."


def test_compact_provider_ui_assets_clean_only_removes_existing_minified_files(
    tmp_path: Path,
) -> None:
    _write_provider_ui_assets_module(
        tmp_path,
        filenames=("web_ui_state.js",),
    )
    html_dir = tmp_path / "provider" / "src" / "opamp_provider" / "html"
    html_dir.mkdir(parents=True, exist_ok=True)
    (html_dir / "web_ui_state.mini.js").write_text("old-minified();\n", encoding="utf-8")
    runtime = _RuntimeStub(tmp_path)

    issues_found = provider_ui.compact_provider_ui_assets(runtime, clean_only=True)

    assert issues_found is False
    assert runtime.commands == []
    assert not (html_dir / "web_ui_state.mini.js").exists()
    assert runtime.messages[-1] == "Provider UI clean-only complete."


def _write_provider_ui_assets_module(repo_root: Path, *, filenames: tuple[str, ...]) -> None:
    module_path = repo_root / "provider" / "src" / "opamp_provider" / "ui_assets.py"
    module_path.parent.mkdir(parents=True, exist_ok=True)
    filenames_repr = ", ".join(repr(name) for name in filenames)
    module_path.write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "",
                f"PROVIDER_UI_JS_FILENAMES = ({filenames_repr},)",
                "",
            ]
        ),
        encoding="utf-8",
    )
