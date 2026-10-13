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

REPO_ROOT = Path(__file__).resolve().parents[2]


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
    assert "2. fluent-resources" in stdout
    assert "3. build" in stdout
    assert "5. help" in stdout
    assert "Command complete. Returning to main menu." in stdout
    args = captured["args"]
    assert args.command_group == "dev"
    assert args.dev_command == "validate-schemas"


def test_help_command_prints_complete_parser_hierarchy(tmp_path: Path, capsys) -> None:
    """The help command should render nested commands from the active parser graph."""
    parser = cli.build_parser(tmp_path)
    args = parser.parse_args([cli.HELP_COMMAND])

    exit_code = cli._run_parsed_command(args)  # pylint: disable=protected-access
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Command hierarchy:" in output
    assert "opamp-dev-cli" in output
    assert "|-- dev" in output
    assert "|   |-- set" in output
    assert "|   |   `-- version" in output
    assert "|-- fluent-resources" in output
    assert "report-fluentbit-changes" in output
    assert "`-- help" in output


def test_help_discovers_config_service_fluent_resource_commands(capsys) -> None:
    """Repository help should include valid commands published by Config Service."""
    parser = cli.build_parser(REPO_ROOT)
    args = parser.parse_args([cli.HELP_COMMAND])

    exit_code = cli._run_parsed_command(args)  # pylint: disable=protected-access
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "generate-fluentbit-assets" in output
    assert "generate-fluentbit-markdown" in output


def test_dynamic_fluentbit_asset_command_dispatches_component_tool(monkeypatch) -> None:
    """A discovered Fluent command should execute through the component tool runner."""
    parser = cli.build_parser(REPO_ROOT)
    args = parser.parse_args(
        [
            cli.FLUENT_RESOURCES_COMMAND_GROUP,
            "generate-fluentbit-assets",
            "--version",
            "5.1.3",
        ]
    )
    captured: dict[str, object] = {}

    def fake_run_component_tool(runtime, **options) -> bool:  # type: ignore[no-untyped-def]
        """Capture dynamic dispatch inputs without running the generator."""
        captured["runtime"] = runtime
        captured["options"] = options
        return False

    monkeypatch.setattr(cli, "run_component_tool", fake_run_component_tool)
    runtime = object()

    issues_found = cli._dispatch_fluent_resources_command(  # pylint: disable=protected-access
        args,
        runtime,
    )

    assert issues_found is False
    assert captured["runtime"] is runtime
    options = captured["options"]
    assert options["python_exe"]
    assert options["args"] is args
    assert options["tool"].command == "generate-fluentbit-assets"


def test_guided_component_tool_uses_latest_release_defaults(monkeypatch) -> None:
    """Guided discovery should allow Config Service to resolve the latest release."""
    responses = iter(
        [
            "2",  # generate-fluentbit-assets
            "1",  # component default: generate latest stable
            "1",  # source component default
            "",  # GitHub ref
            "",  # timeout
            "n",  # no-register
            "n",  # no-schemas
            "",  # previous version
            "n",  # no-inherit
            "",  # summary directory
            "",  # backup directory
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt_text: next(responses))

    tokens = cli._prompt_for_fluent_resources_tokens(  # pylint: disable=protected-access
        REPO_ROOT
    )

    assert tokens == [
        cli.FLUENT_RESOURCES_COMMAND_GROUP,
        "generate-fluentbit-assets",
    ]


def test_guided_component_tool_only_prompts_for_removal_options(monkeypatch) -> None:
    """A removal operation should skip generation-only component questions."""
    responses = iter(
        [
            "2",  # generate-fluentbit-assets
            "3",  # remove named version
            "5.1.3",
            "5.0.4",
            "",  # summary directory
            "",  # backup directory
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt_text: next(responses))

    tokens = cli._prompt_for_fluent_resources_tokens(  # pylint: disable=protected-access
        REPO_ROOT
    )

    assert tokens == [
        cli.FLUENT_RESOURCES_COMMAND_GROUP,
        "generate-fluentbit-assets",
        "--remove-version",
        "5.1.3",
        "--replacement-default",
        "5.0.4",
    ]


def test_guided_selection_passes_labels_to_completion(monkeypatch) -> None:
    """Guided menus should offer command labels and quit aliases for completion."""
    captured: dict[str, object] = {}

    def fake_prompt(prompt_text: str, options: list[str]) -> str:
        """Capture completion choices and return a named selection."""
        captured["prompt_text"] = prompt_text
        captured["options"] = options
        return "fluent-resources"

    monkeypatch.setattr(cli, "prompt_with_completion", fake_prompt)

    selection = cli._prompt_for_selection(  # pylint: disable=protected-access
        "Commands",
        [("dev", "Developer commands"), ("fluent-resources", "Fluent commands")],
    )

    assert selection == "fluent-resources"
    assert captured == {
        "prompt_text": "Select an option: ",
        "options": ["dev", "fluent-resources", "q", "quit", "exit"],
    }


def test_guided_help_prints_hierarchy_and_returns_to_main_menu(
    monkeypatch,
    capsys,
) -> None:
    """Guided mode should expose hierarchy help without creating a command runtime."""
    responses = iter(["5", "q"])
    monkeypatch.setattr("builtins.input", lambda _prompt_text: next(responses))

    exit_code = cli.main([])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Command hierarchy:" in output
    assert "opamp-dev-cli" in output
    assert "Command complete. Returning to main menu." in output
    assert "Exiting developer CLI." in output


def test_main_without_arguments_supports_build_js_complexity_command(
    monkeypatch,
    capsys,
) -> None:
    responses = iter(["3", "7", "", "", "q"])
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
    responses = iter(["3", "1", "q", "q"])

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
    responses = iter(["4", "2", "q"])
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


def test_parser_accepts_cache_and_egg_folder_purge_options(tmp_path: Path) -> None:
    """The direct CLI should expose dry-run generated-folder cleanup."""
    parser = cli.build_parser(tmp_path)

    args = parser.parse_args(["dev", cli.PURGE_CACHE_EGG_COMMAND, "--dry-run"])

    assert args.dev_command == cli.PURGE_CACHE_EGG_COMMAND
    assert args.dry_run is True


def test_parser_accepts_fluent_resource_change_report_options(tmp_path: Path) -> None:
    """The Fluent resources group should expose explicit catalog comparison versions."""
    parser = cli.build_parser(tmp_path)

    args = parser.parse_args(
        [
            cli.FLUENT_RESOURCES_COMMAND_GROUP,
            cli.REPORT_FLUENTBIT_CHANGES_COMMAND,
            "--current-version",
            "5.0.4",
            "--previous-version",
            "4.2.4",
            "--output-dir",
            "reports",
            "--online",
            "--source",
            "github",
            "--github-ref",
            "v5.0.4",
            "--timeout",
            "41",
        ]
    )

    assert args.current_version == "5.0.4"
    assert args.previous_version == "4.2.4"
    assert args.output_dir == "reports"
    assert args.online is True
    assert args.source == "github"
    assert args.github_ref == "v5.0.4"
    assert args.timeout == 41


def test_top_level_dispatch_and_slug_include_fluent_resources(monkeypatch) -> None:
    """Top-level routing and log names should retain the Fluent resource hierarchy."""
    parser = cli.build_parser(Path.cwd())
    args = parser.parse_args(
        [cli.FLUENT_RESOURCES_COMMAND_GROUP, cli.REPORT_FLUENTBIT_CHANGES_COMMAND]
    )
    runtime = object()
    captured: dict[str, object] = {}

    def fake_dispatch(received_args, received_runtime) -> bool:  # type: ignore[no-untyped-def]
        """Capture the routed namespace and runtime."""
        captured["args"] = received_args
        captured["runtime"] = received_runtime
        return False

    monkeypatch.setattr(cli, "_dispatch_fluent_resources_command", fake_dispatch)

    issues_found = cli._dispatch(args, runtime)  # pylint: disable=protected-access

    assert issues_found is False
    assert captured == {"args": args, "runtime": runtime}
    assert (
        cli._command_slug_from_args(args)  # pylint: disable=protected-access
        == "fluent-resources-report-fluentbit-changes"
    )


def test_dispatch_fluent_resources_command_runs_fluentbit_change_report(monkeypatch) -> None:
    """Fluent resource dispatch should pass all catalog report selections through."""
    parser = cli.build_parser(Path.cwd())
    args = parser.parse_args(
        [
            cli.FLUENT_RESOURCES_COMMAND_GROUP,
            cli.REPORT_FLUENTBIT_CHANGES_COMMAND,
            "--current-version",
            "5.0.4",
            "--previous-version",
            "4.2.4",
            "--output-dir",
            "reports",
            "--online",
            "--source",
            "website",
            "--github-ref",
            "main",
            "--timeout",
            "45",
        ]
    )
    captured: dict[str, object] = {}
    runtime = object()

    def fake_report(received_runtime, **options) -> bool:  # type: ignore[no-untyped-def]
        """Capture report dispatch values without reading catalog files."""
        captured["runtime"] = received_runtime
        captured["options"] = options
        return False

    monkeypatch.setattr(cli, "report_fluentbit_changes", fake_report)

    issues_found = cli._dispatch_fluent_resources_command(  # pylint: disable=protected-access
        args,
        runtime,
    )

    assert issues_found is False
    assert captured == {
        "runtime": runtime,
        "options": {
            "current_version": "5.0.4",
            "previous_version": "4.2.4",
            "output_dir": "reports",
            "online": True,
            "documentation_source": "website",
            "github_ref": "main",
            "timeout": 45,
        },
    }


def test_main_without_arguments_supports_fluentbit_change_report(
    monkeypatch,
    capsys,
) -> None:
    """Guided mode should collect optional Fluent Bit comparison settings."""
    responses = iter(["2", "1", "n", "5.0.4", "4.2.4", "reports", "q"])
    captured: dict[str, object] = {}

    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    monkeypatch.setattr(cli, "CommandRuntime", _FakeRuntime)

    def fake_dispatch(args, runtime) -> bool:  # type: ignore[no-untyped-def]
        """Capture guided report arguments without reading catalog files."""
        captured["args"] = args
        captured["runtime"] = runtime
        return False

    monkeypatch.setattr(cli, "_dispatch", fake_dispatch)

    exit_code = cli.main([])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert cli.REPORT_FLUENTBIT_CHANGES_COMMAND in stdout
    args = captured["args"]
    assert args.current_version == "5.0.4"
    assert args.previous_version == "4.2.4"
    assert args.output_dir == "reports"
    assert args.online is False


def test_guided_fluentbit_change_report_supports_current_online_release(
    monkeypatch,
    capsys,
) -> None:
    """Guided mode should allow an online comparison with no named version."""
    responses = iter(["2", "1", "y", "", "5.0.4", "reports", "q"])
    captured: dict[str, object] = {}

    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    monkeypatch.setattr(cli, "CommandRuntime", _FakeRuntime)

    def fake_dispatch(args, runtime) -> bool:  # type: ignore[no-untyped-def]
        """Capture guided online arguments without retrieving documentation."""
        captured["args"] = args
        captured["runtime"] = runtime
        return False

    monkeypatch.setattr(cli, "_dispatch", fake_dispatch)

    exit_code = cli.main([])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert cli.REPORT_FLUENTBIT_CHANGES_COMMAND in stdout
    args = captured["args"]
    assert args.online is True
    assert args.current_version == ""
    assert args.previous_version == "5.0.4"


def test_dispatch_dev_command_runs_cache_and_egg_folder_purge(monkeypatch) -> None:
    """Developer command dispatch should pass the dry-run choice to cleanup."""
    parser = cli.build_parser(Path.cwd())
    args = parser.parse_args(["dev", cli.PURGE_CACHE_EGG_COMMAND, "--dry-run"])
    captured: dict[str, object] = {}
    runtime = object()

    def fake_purge(received_runtime, *, dry_run: bool) -> bool:  # type: ignore[no-untyped-def]
        """Capture cleanup arguments without accessing the filesystem."""
        captured["runtime"] = received_runtime
        captured["dry_run"] = dry_run
        return False

    monkeypatch.setattr(cli, "purge_cache_and_egg_folders", fake_purge)

    issues_found = cli._dispatch_dev_command(args, runtime)  # pylint: disable=protected-access

    assert issues_found is False
    assert captured == {"runtime": runtime, "dry_run": True}


def test_main_without_arguments_supports_cache_and_egg_folder_purge(
    monkeypatch,
    capsys,
) -> None:
    """Guided mode should expose generated-folder cleanup and dry-run selection."""
    responses = iter(["1", "5", "y", "q"])
    captured: dict[str, object] = {}

    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    monkeypatch.setattr(cli, "CommandRuntime", _FakeRuntime)

    def fake_dispatch(args, runtime) -> bool:  # type: ignore[no-untyped-def]
        """Capture the guided command without performing filesystem cleanup."""
        captured["args"] = args
        captured["runtime"] = runtime
        return False

    monkeypatch.setattr(cli, "_dispatch", fake_dispatch)

    exit_code = cli.main([])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert cli.PURGE_CACHE_EGG_COMMAND in stdout
    args = captured["args"]
    assert args.dev_command == cli.PURGE_CACHE_EGG_COMMAND
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
