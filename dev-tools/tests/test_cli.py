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

from __future__ import annotations

from pathlib import Path

import opamp_dev_tools.cli as cli


class _FakeRuntime:
    """Minimal runtime double for CLI menu tests.

    Attributes
    ----------
    repo_root:
        Repository root passed into the runtime constructor by the CLI.
    tool_root:
        Dev-tools root passed into the runtime constructor by the CLI.
    command_slug:
        Log filename slug built from the parsed command path.
    """

    def __init__(self, *, repo_root: Path, tool_root: Path, command_slug: str) -> None:
        """Capture constructor values so the tests can inspect them.

        Parameters
        ----------
        repo_root:
            Repository root selected for the CLI invocation under test.
        tool_root:
            Dev-tools directory derived from the repository root.
        command_slug:
            Log filename slug derived from the parsed command.
        """
        self.repo_root = repo_root
        self.tool_root = tool_root
        self.command_slug = command_slug

    def record_error(self, message: str, **_: object) -> None:
        """Fail the test if the CLI reports an unexpected runtime error.

        Parameters
        ----------
        message:
            Error message produced by the CLI runtime.
        """
        raise AssertionError(f"unexpected runtime error: {message}")

    def write_logs(self) -> None:
        """Skip log writing in menu-focused unit tests."""
        return None

    def print_log_summary(self) -> None:
        """Skip log summary output in menu-focused unit tests."""
        return None


def test_main_without_arguments_prompts_for_command_group(
    monkeypatch,
    capsys,
) -> None:
    responses = iter(["1", "1", "q"])
    captured: dict[str, object] = {}

    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    monkeypatch.setattr(cli, "CommandRuntime", _FakeRuntime)

    def fake_dispatch(args, runtime) -> bool:  # type: ignore[no-untyped-def]
        captured["args"] = args
        captured["runtime"] = runtime
        return False

    monkeypatch.setattr(cli, "_dispatch", fake_dispatch)

    exit_code = cli.main([])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert "Repository root:" in stdout
    assert "(current working directory)" in stdout
    assert "Command groups:" in stdout
    assert "1. dev" in stdout
    assert "2. build" in stdout
    assert "Command complete. Returning to main menu." in stdout
    args = captured["args"]
    assert args.command_group == "dev"
    assert args.dev_command == "validate-schemas"


def test_main_without_arguments_supports_dev_sync_command(
    monkeypatch,
    capsys,
) -> None:
    responses = iter(["1", "3", "q"])
    captured: dict[str, object] = {}

    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    monkeypatch.setattr(cli, "CommandRuntime", _FakeRuntime)

    def fake_dispatch(args, runtime) -> bool:  # type: ignore[no-untyped-def]
        captured["args"] = args
        captured["runtime"] = runtime
        return False

    monkeypatch.setattr(cli, "_dispatch", fake_dispatch)

    exit_code = cli.main([])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert "sync config-service-json" in stdout
    assert "Returning to main menu." in stdout
    args = captured["args"]
    assert args.command_group == "dev"
    assert args.dev_command == "sync"
    assert args.sync_command == "config-service-json"


def test_main_without_arguments_supports_build_js_complexity_command(
    monkeypatch,
    capsys,
) -> None:
    responses = iter(["2", "7", "", "", "q"])
    captured: dict[str, object] = {}

    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    monkeypatch.setattr(cli, "CommandRuntime", _FakeRuntime)

    def fake_dispatch(args, runtime) -> bool:  # type: ignore[no-untyped-def]
        captured["args"] = args
        captured["runtime"] = runtime
        return False

    monkeypatch.setattr(cli, "_dispatch", fake_dispatch)

    exit_code = cli.main([])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert "js-complexity" in stdout
    args = captured["args"]
    assert args.command_group == "build"
    assert args.build_command == "js-complexity"


def test_main_without_arguments_can_quit_immediately(monkeypatch, capsys) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "q")

    exit_code = cli.main([])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert "Repository root:" in stdout
    assert "Command groups:" in stdout


def test_main_without_arguments_quitting_submenu_returns_to_main_menu(
    monkeypatch,
    capsys,
) -> None:
    responses = iter(["1", "q", "q"])

    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    exit_code = cli.main([])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert stdout.count("Command groups:") == 2
    assert "Dev commands:" in stdout
    assert "Returning to main menu." in stdout
    assert "Exiting developer CLI." in stdout


def test_main_without_arguments_quitting_nested_submenu_returns_to_main_menu(
    monkeypatch,
    capsys,
) -> None:
    responses = iter(["2", "1", "q", "q"])

    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    exit_code = cli.main([])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert stdout.count("Command groups:") == 2
    assert "Build commands:" in stdout
    assert "artefact scope:" in stdout
    assert "Returning to main menu." in stdout
    assert "Exiting developer CLI." in stdout


def test_main_without_arguments_supports_certificate_ensure_provider_config(
    monkeypatch,
    capsys,
) -> None:
    responses = iter(["3", "2", "q"])
    captured: dict[str, object] = {}

    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    monkeypatch.setattr(cli, "CommandRuntime", _FakeRuntime)

    def fake_dispatch(args, runtime) -> bool:  # type: ignore[no-untyped-def]
        captured["args"] = args
        captured["runtime"] = runtime
        return False

    monkeypatch.setattr(cli, "_dispatch", fake_dispatch)

    exit_code = cli.main([])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert "ensure-provider-config" in stdout
    assert "Exiting developer CLI." in stdout
    args = captured["args"]
    assert args.command_group == "certificate"
    assert args.certificate_command == "ensure-provider-config"


def test_main_without_arguments_returns_to_main_menu_after_command(
    monkeypatch,
    capsys,
) -> None:
    responses = iter(["1", "1", "q"])
    dispatch_calls: list[object] = []

    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    monkeypatch.setattr(cli, "CommandRuntime", _FakeRuntime)

    def fake_dispatch(args, runtime) -> bool:  # type: ignore[no-untyped-def]
        dispatch_calls.append((args, runtime))
        return False

    monkeypatch.setattr(cli, "_dispatch", fake_dispatch)

    exit_code = cli.main([])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert len(dispatch_calls) == 1
    assert stdout.count("Command groups:") == 2
    assert "Command complete. Returning to main menu." in stdout


def test_main_defaults_repo_root_to_launch_directory(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("builtins.input", lambda _: "q")

    exit_code = cli.main([])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert f"Repository root: {tmp_path.resolve()} (current working directory)" in stdout


def test_main_prefers_explicit_repo_root(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    explicit_root = tmp_path / "custom-root"
    explicit_root.mkdir()
    monkeypatch.setattr("builtins.input", lambda _: "q")

    exit_code = cli.main(["--repo-root", str(explicit_root)])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert f"Repository root: {explicit_root.resolve()}" in stdout
    assert "(current working directory)" not in stdout


def test_parser_accepts_container_image_cleanup_options(tmp_path: Path) -> None:
    """The direct CLI should expose runtime-aware managed image cleanup."""
    parser = cli.build_parser(tmp_path)

    args = parser.parse_args(
        [
            "dev",
            "clean-images",
            "--runtime",
            "podman",
            "--include-legacy",
            "--force",
            "--dry-run",
        ]
    )

    assert args.dev_command == "clean-images"
    assert args.runtime == "podman"
    assert args.include_legacy is True
    assert args.force is True
    assert args.dry_run is True


def test_parser_accepts_wheel_upload_origin_and_release(tmp_path: Path) -> None:
    """The direct CLI should require a release name and supported origin."""
    parser = cli.build_parser(tmp_path)

    args = parser.parse_args(
        [
            "dev",
            "upload-wheels",
            "--origin",
            "azure",
            "--release",
            "v5.1.0",
            "--storage-name",
            "opampstorage",
        ]
    )

    assert args.dev_command == "upload-wheels"
    assert args.origin == "azure"
    assert args.release == "v5.1.0"
    assert args.storage_name == "opampstorage"


def test_parser_accepts_local_wheel_upload_and_cloud_push(tmp_path: Path) -> None:
    """The CLI should separate GitHub publishing from local-to-cloud pushes."""
    parser = cli.build_parser(tmp_path)

    upload_args = parser.parse_args(
        ["dev", "upload-wheels", "--origin", "local", "--release", "v5.1.0"]
    )
    push_args = parser.parse_args(
        ["dev", "push-to-cloud", "--origin", "aws", "--release", "v5.1.0"]
    )

    assert upload_args.origin == "local"
    assert upload_args.repository == "opamp-observe/opamp-core"
    assert push_args.dev_command == "push-to-cloud"
    assert push_args.origin == "aws"
