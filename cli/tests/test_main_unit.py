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

"""CLI unit test coverage.

Test-case reference: cli/docs/TEST_CASES.md
"""

from __future__ import annotations

import importlib
import json
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

cli_main = importlib.import_module("opamp_cli.main")
container_management = importlib.import_module("opamp_cli.container_management")
dev_commands = importlib.import_module("opamp_cli.dev_commands")
setup_venv = importlib.import_module("opamp_cli.setup_venv")
version_bump = importlib.import_module("opamp_cli.version_bump")


def _sample_fluentbit_config() -> str:
    return (
        "service:\n"
        "  flush: 1\n"
        "pipeline:\n"
        "  inputs:\n"
        "    - name: dummy\n"
        "      tag: test\n"
        "  outputs:\n"
        "    - name: stdout\n"
        "      match: \"*\"\n"
    )


def _invalid_fluentbit_config_missing_required_tag() -> str:
    return (
        "service:\n"
        "  flush: 1\n"
        "pipeline:\n"
        "  inputs:\n"
        "    - name: exec\n"
        "      command: ls -al\n"
        "  outputs:\n"
        "    - name: stdout\n"
        "      match: \"*\"\n"
    )


def _report_path_from_output(output: str) -> Path:
    match = re.search(r"Report file: (.+)", output)
    assert match is not None
    return Path(match.group(1).strip())


def test_split_script_directive_parses_output_name_and_command() -> None:
    output_name, command_text = cli_main._split_script_directive(  # type: ignore[attr-defined]
        "script demo-start echo hello"
    )

    assert output_name == "demo-start"
    assert command_text == "echo hello"


def test_normalize_python_script_command_prefixes_python_launcher() -> None:
    normalized = cli_main._normalize_python_script_command(  # type: ignore[attr-defined]
        "cli/main.py --help",
        launcher="python3",
    )

    assert normalized == "\"python3\" cli/main.py --help"


def test_command_text_from_args_preserves_shell_quoting() -> None:
    command_text = cli_main._command_text_from_args(  # type: ignore[attr-defined]
        ["python", "-c", "print('cli-e2e-ok')"]
    )

    assert "python" in command_text
    assert "-c" in command_text
    assert "cli-e2e-ok" in command_text


def test_build_exec_env_enables_unbuffered_python_output(monkeypatch) -> None:
    monkeypatch.setattr(cli_main.os, "environ", {"PATH": "/tmp/bin"})

    env = cli_main._build_exec_env()  # type: ignore[attr-defined]

    assert env["PYTHONUNBUFFERED"] == "1"


def test_split_guided_command_supports_restart() -> None:
    parsed = cli_main._split_guided_command("restart server")  # type: ignore[attr-defined]
    parsed_no_target = cli_main._split_guided_command("restart")  # type: ignore[attr-defined]

    assert parsed == ("restart", "server")
    assert parsed_no_target == ("restart", "")


def test_materialize_ordered_actions_preserves_order_and_skips_missing() -> None:
    actions = cli_main._materialize_ordered_actions(  # type: ignore[attr-defined]
        order=["two", "missing", "one"],
        action_map={
            "one": {"id": "one", "label": "One"},
            "two": {"id": "two", "label": "Two"},
        },
    )

    assert [label for label, _action in actions] == ["Two", "One"]


def test_catalog_launch_config_path_enables_catalog(tmp_path: Path, monkeypatch) -> None:
    runtime_dir = tmp_path / "runtime"
    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)

    config_path = tmp_path / "opamp.json"
    base_config = {
        "opamp": {
            "config_catalog": {
                "enabled": False,
                "sources": [{"folder": "config-service/json-definitions", "extensions": [".json"]}],
            }
        }
    }
    config_path.write_text(json.dumps(base_config) + "\n", encoding="utf-8")

    generated = cli_main._catalog_launch_config_path(  # type: ignore[attr-defined]
        base_config_path=config_path,
        base_config=base_config,
    )

    assert generated == (runtime_dir / "catalog-service.json").resolve()
    payload = json.loads(generated.read_text(encoding="utf-8"))
    assert payload["opamp"]["config_catalog"]["enabled"] is True
    assert payload["_generated_from"] == str(config_path.resolve())


def test_process_tail_setting_round_trip(tmp_path: Path, monkeypatch) -> None:
    runtime_dir = tmp_path / "runtime"
    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)

    cli_main.process_tail.set_process_tail_enabled(
        True,
        load_settings=cli_main._load_cli_settings,  # type: ignore[attr-defined]
        save_settings=cli_main._save_cli_settings,  # type: ignore[attr-defined]
        settings_path=cli_main._cli_settings_path,  # type: ignore[attr-defined]
        logger=cli_main._get_logger(),  # type: ignore[attr-defined]
    )

    assert cli_main.process_tail.process_tail_enabled(
        load_settings=cli_main._load_cli_settings,  # type: ignore[attr-defined]
    ) is True
    payload = json.loads((runtime_dir / "settings.json").read_text(encoding="utf-8"))
    assert payload["enable_process_tail"] is True


def test_disable_enable_process_tail_alias_disables_setting(tmp_path: Path, monkeypatch) -> None:
    runtime_dir = tmp_path / "runtime"
    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)

    cli_main.process_tail.set_process_tail_enabled(
        True,
        load_settings=cli_main._load_cli_settings,  # type: ignore[attr-defined]
        save_settings=cli_main._save_cli_settings,  # type: ignore[attr-defined]
        settings_path=cli_main._cli_settings_path,  # type: ignore[attr-defined]
        logger=cli_main._get_logger(),  # type: ignore[attr-defined]
    )
    exit_code = cli_main._handle_command("disable enable-process-tail")  # type: ignore[attr-defined]

    assert exit_code == 0
    assert cli_main.process_tail.process_tail_enabled(
        load_settings=cli_main._load_cli_settings,  # type: ignore[attr-defined]
    ) is False


def test_windows_no_console_kwargs_returns_create_no_window(monkeypatch) -> None:
    monkeypatch.setattr(cli_main, "_is_windows", lambda: True)
    monkeypatch.setattr(cli_main.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    kwargs = cli_main._windows_no_console_kwargs()  # type: ignore[attr-defined]

    assert kwargs == {"creationflags": 0x08000000}


def test_background_start_suppresses_windows_console(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class FakeProcess:
        pid = 456

        def poll(self) -> None:
            return None

    def fake_popen(argv: list[str], **kwargs: Any) -> FakeProcess:
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return FakeProcess()

    monkeypatch.setattr(cli_main, "_is_windows", lambda: True)
    monkeypatch.setattr(cli_main.subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200, raising=False)
    monkeypatch.setattr(cli_main.subprocess, "DETACHED_PROCESS", 0x00000008, raising=False)
    monkeypatch.setattr(cli_main.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)
    monkeypatch.setattr(cli_main.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(cli_main.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        cli_main,
        "_get_logger",
        lambda: SimpleNamespace(
            info=lambda *_args, **_kwargs: None,
            warning=lambda *_args, **_kwargs: None,
            exception=lambda *_args, **_kwargs: None,
        ),
    )
    monkeypatch.setattr(cli_main, "_wait_for_background_start", lambda **_kwargs: (True, ""))
    monkeypatch.setattr(cli_main, "_record_cli_process", lambda **_kwargs: None)
    monkeypatch.setattr(cli_main.process_tail, "open_process_tail_if_enabled", lambda **_kwargs: None)
    monkeypatch.setattr(cli_main, "_cli_log_dir", lambda: tmp_path / "logs")

    exit_code = cli_main._launch_background_process(  # type: ignore[attr-defined]
        {
            "label": "Client",
            "argv": ["python", "-m", "opamp_consumer.client"],
            "cwd": str(tmp_path),
            "env": {"PATH": "test-path"},
        }
    )

    assert exit_code == 0
    assert captured["argv"] == ["python", "-m", "opamp_consumer.client"]
    assert captured["kwargs"]["creationflags"] & 0x08000000


def test_main_writes_component_lifecycle_log(tmp_path: Path, monkeypatch) -> None:
    runtime_dir = tmp_path / "runtime"
    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)

    exit_code = cli_main.main(["status"])

    log_path = runtime_dir / "logs" / "opamp_cli.log"
    assert exit_code == 0
    assert log_path.exists()
    log_text = log_path.read_text(encoding="utf-8")
    assert "CLI main started" in log_text
    assert "printing CLI status" in log_text
    assert "CLI main completed command" in log_text


def test_status_command_reports_default_opamp_config_path(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    runtime_dir = tmp_path / "runtime"
    repo_root = tmp_path / "repo"
    config_path = repo_root / "config" / "opamp.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text('{"opamp": {}}\n', encoding="utf-8")
    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)
    monkeypatch.setattr(cli_main, "_repo_root", lambda: repo_root)
    monkeypatch.delenv("OPAMP_CONFIG_PATH", raising=False)

    exit_code = cli_main.main(["status"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert f"OpAMP config file: {config_path.resolve()} (default)" in output
    assert "OpAMP config loaded: yes" in output


def test_status_command_reports_env_opamp_config_path(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    runtime_dir = tmp_path / "runtime"
    repo_root = tmp_path / "repo"
    config_path = repo_root / "config" / "custom-opamp.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text('{"opamp": {}}\n', encoding="utf-8")
    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)
    monkeypatch.setattr(cli_main, "_repo_root", lambda: repo_root)
    monkeypatch.setenv("OPAMP_CONFIG_PATH", "config/custom-opamp.json")

    exit_code = cli_main.main(["status"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert f"OpAMP config file: {config_path.resolve()} (OPAMP_CONFIG_PATH)" in output
    assert "OpAMP config loaded: yes" in output


def test_status_command_reports_invalid_opamp_config(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    runtime_dir = tmp_path / "runtime"
    repo_root = tmp_path / "repo"
    config_path = repo_root / "config" / "opamp.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)
    monkeypatch.setattr(cli_main, "_repo_root", lambda: repo_root)
    monkeypatch.delenv("OPAMP_CONFIG_PATH", raising=False)

    exit_code = cli_main.main(["status"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert f"OpAMP config file: {config_path.resolve()} (default)" in output
    assert "OpAMP config loaded: no (invalid JSON:" in output


def test_clear_logs_removes_cli_and_configured_log_files(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    runtime_dir = tmp_path / "runtime"
    repo_root = tmp_path / "repo"
    cli_logs = runtime_dir / "logs"
    cli_logs.mkdir(parents=True)
    cli_log = cli_logs / "opamp_cli.log"
    launch_log = cli_logs / "consumer.log"
    report_json = cli_logs / "config-report.json"
    keep_text = cli_logs / "notes.txt"
    launch_log.write_text("consumer\n", encoding="utf-8")
    report_json.write_text("{}\n", encoding="utf-8")
    keep_text.write_text("keep\n", encoding="utf-8")

    state_path = runtime_dir / "managed_processes.json"
    state_path.write_text(
        json.dumps(
            {
                "processes": [
                    {
                        "name": "consumer",
                        "pid": 123,
                        "log_file": str(launch_log),
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )

    config_dir = repo_root / "config"
    agent_log_dir = repo_root / "agent-logs"
    config_dir.mkdir(parents=True)
    agent_log_dir.mkdir()
    (agent_log_dir / "elastic-agent.ndjson").write_text("{}\n", encoding="utf-8")
    (agent_log_dir / "keep.tmp").write_text("keep\n", encoding="utf-8")
    (config_dir / "elastic-agent.yml").write_text(
        "agent.logging.files:\n"
        "  path: ../agent-logs\n",
        encoding="utf-8",
    )
    (config_dir / "opamp.json").write_text(
        json.dumps({"consumer": {"agent_config_path": "elastic-agent.yml"}}) + "\n",
        encoding="utf-8",
    )

    demo_config = repo_root / "cli" / "config" / "demo_consumer_profiles.json"
    logstash_out = repo_root / "tests" / "logstash" / "out"
    logstash_logs = logstash_out / "logs"
    demo_config.parent.mkdir(parents=True)
    logstash_logs.mkdir(parents=True)
    (logstash_out / "all-events.json").write_text("{}\n", encoding="utf-8")
    (logstash_logs / "logstash.log").write_text("logstash\n", encoding="utf-8")
    (logstash_out / "keep.tmp").write_text("keep\n", encoding="utf-8")
    demo_config.write_text(
        json.dumps(
            {
                "profiles": [
                    {
                        "name": "Logstash demo",
                        "containers": [
                            {
                                "id": "logstash-local",
                                "label": "Logstash local pipeline",
                                "image": "logstash:9.5.1",
                                "ensure_dirs": ["tests/logstash/out"],
                                "volumes": [
                                    {
                                        "host_path": "tests/logstash/out",
                                        "container_path": "/usr/share/logstash/out",
                                    }
                                ],
                                "command": [
                                    "logstash",
                                    "--path.logs",
                                    "/usr/share/logstash/out/logs",
                                ],
                            }
                        ],
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)
    monkeypatch.setattr(cli_main, "_repo_root", lambda: repo_root)
    monkeypatch.delenv("OPAMP_CONFIG_PATH", raising=False)

    exit_code = cli_main.main(["clear-logs"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Log directories checked:" in output
    assert "Log files deleted:" in output
    assert cli_log.exists() is False
    assert launch_log.exists() is False
    assert report_json.exists() is False
    assert (agent_log_dir / "elastic-agent.ndjson").exists() is False
    assert (logstash_out / "all-events.json").exists() is False
    assert (logstash_logs / "logstash.log").exists() is False
    assert keep_text.exists() is True
    assert (agent_log_dir / "keep.tmp").exists() is True
    assert (logstash_out / "keep.tmp").exists() is True
    assert state_path.exists() is True


def test_list_command_reports_config_options_when_available(capsys) -> None:
    exit_code = cli_main.main(["list"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "clear-logs" in output
    assert "Config commands:" in output
    assert "  config:" in output
    assert "    - validate <path>" in output
    assert "    - metadata <path>" in output


def test_interactive_startup_notes_include_list_command_without_running_list(
    monkeypatch,
    capsys,
) -> None:
    def eof_input(_prompt: str) -> str:
        raise EOFError

    def fake_print_option_hierarchy() -> int:
        raise AssertionError("interactive startup should not run list automatically")

    monkeypatch.setattr(cli_main, "_top_level_commands", lambda: ["list", "exit"])
    monkeypatch.setattr(cli_main, "_prompt_toolkit_input_reader", lambda _words: None)
    monkeypatch.setattr(cli_main, "_builtin_tty_input_reader", lambda _words: None)
    monkeypatch.setattr(cli_main, "_setup_readline_completion", lambda _words: None)
    monkeypatch.setattr(cli_main, "_is_windows", lambda: False)
    monkeypatch.setattr(cli_main, "_fluentbit_dev_tool_available", lambda: False)
    monkeypatch.setattr(cli_main, "_mcp_dev_tool_available", lambda: False)
    monkeypatch.setattr(cli_main, "_dev_pid_lookup_available", lambda: False)
    monkeypatch.setattr(cli_main, "_dev_version_bump_available", lambda: False)
    monkeypatch.setattr(cli_main, "_detected_behavior_flags", lambda: [])
    monkeypatch.setattr(cli_main, "_print_option_hierarchy", fake_print_option_hierarchy)
    monkeypatch.setattr("builtins.input", eof_input)

    exit_code = cli_main._interactive_loop()  # type: ignore[attr-defined]
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Use 'list' to see all available commands." in output
    assert "Current command hierarchy" not in output


def test_help_includes_process_tail_commands(capsys) -> None:
    exit_code = cli_main.main(["help"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "opamp-cli enable-process-tail" in output
    assert "opamp-cli disable-process-tail" in output
    assert "`enable-process-tail` opens a new shell" in output
    assert "`disable-process-tail` stops opening log-tail shells" in output


def test_help_includes_setup_venv_command(capsys) -> None:
    exit_code = cli_main.main(["help"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "opamp-cli setup-venv" in output
    assert "`setup-venv` creates or updates" in output


def test_top_level_commands_include_setup_venv(monkeypatch) -> None:
    monkeypatch.setattr(cli_main, "_demo_mode_enabled", lambda: False)
    monkeypatch.setattr(cli_main, "_fluentbit_dev_tool_available", lambda: False)
    monkeypatch.setattr(cli_main, "_mcp_dev_tool_available", lambda: False)
    monkeypatch.setattr(cli_main, "_dev_pid_lookup_available", lambda: False)
    monkeypatch.setattr(container_management, "container_runtime_executable", lambda: None)

    commands = cli_main._top_level_commands()  # type: ignore[attr-defined]

    assert "setup-venv" in commands


def test_parse_setup_venv_args_supports_options(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    options = setup_venv.parse_setup_venv_args(
        ["--venv", "envs/opamp", "--dry-run", "--skip-node"],
        repo_root=repo_root,
    )

    assert options["venv_dir"] == (repo_root / "envs" / "opamp").resolve()
    assert options["dry_run"] is True
    assert options["skip_node"] is True


def test_setup_venv_dry_run_lists_python_and_node_steps(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "cli").mkdir(parents=True)
    (repo_root / "cli" / "pyproject.toml").write_text("[project]\nname = 'opamp-cli'\n")
    (repo_root / "tools" / "mermaid").mkdir(parents=True)
    (repo_root / "tools" / "mermaid" / "package.json").write_text('{"scripts": {}}\n')
    (repo_root / "requirements.txt").write_text("prompt_toolkit>=3.0\n")
    monkeypatch.setattr(cli_main, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(cli_main, "_is_windows", lambda: False)
    monkeypatch.setattr(setup_venv.shutil, "which", lambda name: f"/usr/bin/{name}")

    exit_code = cli_main.main(["setup-venv", "--dry-run"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Dry run: commands will be printed but not executed." in output
    assert '"-m" "venv"' in output or "-m venv" in output
    assert (
        '"pip" "install" "--upgrade" "pip"' in output
        or "pip install --upgrade pip" in output
    )
    assert '"pip" "install" "-r"' in output or "pip install -r" in output
    assert '"pip" "install" "-e"' in output or "pip install -e" in output
    assert "cli[dev]" in output
    assert "npm" in output and "install" in output
    assert "Dry run complete." in output


def test_prompt_setup_venv_activation_opens_shell_when_accepted(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = tmp_path / "repo"
    venv_dir = repo_root / ".venv"
    activate_script = venv_dir / "bin" / "activate"
    activate_script.parent.mkdir(parents=True)
    activate_script.write_text("# activate\n", encoding="utf-8")
    captured: dict[str, Any] = {}

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["argv"] = list(argv)
        captured["kwargs"] = dict(kwargs)
        return subprocess.CompletedProcess(args=argv, returncode=0)

    monkeypatch.setattr(cli_main, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(cli_main, "_is_windows", lambda: False)
    monkeypatch.setenv("SHELL", "/bin/bash")
    monkeypatch.setattr(setup_venv.subprocess, "run", fake_run)

    code = setup_venv.prompt_setup_venv_activation(
        venv_dir,
        input_reader=lambda _prompt: "y",
        prompt_text=lambda prompt: "y",
        parse_yes_no=lambda value, default: cli_main._parse_yes_no(value, default=default),  # type: ignore[attr-defined]
        open_shell=lambda path: setup_venv.open_setup_venv_shell(
            path,
            repo_root=repo_root,
            is_windows=False,
        ),
    )

    assert code == 0
    assert captured["argv"][0] == "/bin/bash"
    assert captured["argv"][1] == "-c"
    assert str(activate_script.resolve()) in captured["argv"][2]
    assert captured["kwargs"]["check"] is False


def test_prompt_setup_venv_activation_can_be_declined(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    venv_dir = tmp_path / ".venv"

    def fail_open_shell(_venv_dir: Path) -> int:
        raise AssertionError("activation shell should not open")

    code = setup_venv.prompt_setup_venv_activation(
        venv_dir,
        input_reader=lambda _prompt: "n",
        prompt_text=lambda prompt: "n",
        parse_yes_no=lambda value, default: cli_main._parse_yes_no(value, default=default),  # type: ignore[attr-defined]
        open_shell=fail_open_shell,
    )
    output = capsys.readouterr().out

    assert code == 0
    assert f"Virtual environment is ready: {venv_dir.resolve()}" in output


def test_prompt_setup_venv_activation_skips_prompt_without_tty(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    venv_dir = tmp_path / ".venv"

    def fail_open_shell(_venv_dir: Path) -> int:
        raise AssertionError("activation shell should not open")

    code = setup_venv.prompt_setup_venv_activation(
        venv_dir,
        prompt_text=lambda prompt: "",
        parse_yes_no=lambda value, default: cli_main._parse_yes_no(value, default=default),  # type: ignore[attr-defined]
        open_shell=fail_open_shell,
        activation_prompt_available=lambda: False,
    )
    output = capsys.readouterr().out

    assert code == 0
    assert f"Virtual environment is ready: {venv_dir.resolve()}" in output


def test_config_validate_single_file_writes_report(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    runtime_dir = tmp_path / "runtime"
    config_path = tmp_path / "valid.yaml"
    config_path.write_text(_sample_fluentbit_config(), encoding="utf-8")
    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)

    exit_code = cli_main.main(["config", "validate", str(config_path)])
    output = capsys.readouterr().out
    report_path = _report_path_from_output(output)

    assert exit_code == 0
    assert "Validation result: no error" in output
    assert report_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    assert f"File: {config_path.resolve()}" in report_text
    assert "Config type: fluentbit" in report_text
    assert "Validation result: no error" in report_text


def test_config_validate_directory_reports_each_file_with_spacing(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    runtime_dir = tmp_path / "runtime"
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    first = config_dir / "one.yaml"
    second = config_dir / "two.yaml"
    first.write_text(_sample_fluentbit_config(), encoding="utf-8")
    second.write_text(_sample_fluentbit_config(), encoding="utf-8")
    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)

    exit_code = cli_main.main(["config", "validate", str(config_dir)])
    output = capsys.readouterr().out
    report_path = _report_path_from_output(output)

    assert exit_code == 0
    report_text = report_path.read_text(encoding="utf-8")
    assert f"File: {first.resolve()}" in report_text
    assert f"File: {second.resolve()}" in report_text
    assert "\n\n\n\nFile: " in report_text


def test_config_validate_single_file_returns_error_when_issues_found(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    runtime_dir = tmp_path / "runtime"
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(_invalid_fluentbit_config_missing_required_tag(), encoding="utf-8")
    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)

    exit_code = cli_main.main(["config", "validate", str(config_path)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Validation result: issues found" in output
    assert "missing_required_field" in output


def test_config_validate_directory_returns_error_when_any_file_has_issues(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    runtime_dir = tmp_path / "runtime"
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    valid_path = config_dir / "valid.yaml"
    invalid_path = config_dir / "invalid.yaml"
    valid_path.write_text(_sample_fluentbit_config(), encoding="utf-8")
    invalid_path.write_text(_invalid_fluentbit_config_missing_required_tag(), encoding="utf-8")
    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)

    exit_code = cli_main.main(["config", "validate", str(config_dir)])
    output = capsys.readouterr().out
    report_path = _report_path_from_output(output)
    report_text = report_path.read_text(encoding="utf-8")

    assert exit_code == 1
    assert f"File: {valid_path.resolve()}" in report_text
    assert f"File: {invalid_path.resolve()}" in report_text
    assert "Validation result: issues found" in report_text


def test_config_metadata_adds_missing_header_values(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    runtime_dir = tmp_path / "runtime"
    config_path = tmp_path / "missing.yaml"
    config_path.write_text(_sample_fluentbit_config(), encoding="utf-8")
    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)

    exit_code = cli_main.main(["config", "metadata", str(config_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    updated_text = config_path.read_text(encoding="utf-8")
    assert updated_text.startswith(
        "# config-service: config_type=fluentbit\n"
        "# config-service: version=5.0.4\n"
    )
    assert "Metadata status: applied missing metadata fields config_type, version" in output


def test_config_metadata_preserves_existing_header_values(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    runtime_dir = tmp_path / "runtime"
    config_path = tmp_path / "existing.yaml"
    original = (
        "# config-service: config_type=fluentbit\n"
        "# config-service: version=4.2.4\n"
        + _sample_fluentbit_config()
    )
    config_path.write_text(original, encoding="utf-8")
    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)

    exit_code = cli_main.main(["config", "metadata", str(config_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert config_path.read_text(encoding="utf-8") == original
    assert "Config type: fluentbit" in output
    assert "Version: 4.2.4" in output
    assert "existing metadata preserved" in output


def test_is_process_running_uses_tasklist_on_windows(monkeypatch) -> None:
    captured_commands: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
        captured_commands.append(command)
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout='"python.exe","4321","Console","1","10,240 K"\n',
            stderr="",
        )

    monkeypatch.setattr(cli_main, "_is_windows", lambda: True)
    monkeypatch.setattr(cli_main.subprocess, "run", fake_run)

    is_running = cli_main._is_process_running(4321)  # type: ignore[attr-defined]

    assert is_running is True
    assert captured_commands == [["tasklist", "/FI", "PID eq 4321", "/FO", "CSV", "/NH"]]


def test_status_command_handles_windows_managed_processes(tmp_path: Path, monkeypatch, capsys) -> None:
    runtime_dir = tmp_path / "runtime"
    state_path = runtime_dir / "managed_processes.json"
    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)
    monkeypatch.setattr(cli_main, "_is_windows", lambda: True)
    monkeypatch.setattr(
        cli_main.os,
        "kill",
        lambda _pid, _signal: (_ for _ in ()).throw(AssertionError("os.kill should not be used")),
    )

    runtime_dir.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "processes": [
                    {
                        "name": "Server",
                        "pid": 9876,
                        "started_at": "2026-06-03T15:50:04Z",
                        "cwd": "D:/dev/opamp",
                        "log_file": "D:/dev/opamp/cli/runtime/logs/server.log",
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )

    def fake_run(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout='"python.exe","9876","Console","1","10,240 K"\n',
            stderr="",
        )

    monkeypatch.setattr(cli_main.subprocess, "run", fake_run)

    exit_code = cli_main.main(["status"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Managed processes: 1" in output
    assert "status: running" in output


def test_rejected_guided_action_is_logged(tmp_path: Path, monkeypatch) -> None:
    runtime_dir = tmp_path / "runtime"
    monkeypatch.setattr(cli_main, "_cli_runtime_dir", lambda: runtime_dir)

    exit_code = cli_main._execute_guided_action(  # type: ignore[attr-defined]
        input_reader=None,
        intent="start",
        selection="does-not-exist",
    )

    log_path = runtime_dir / "logs" / "opamp_cli.log"
    assert exit_code == 1
    assert log_path.exists()
    log_text = log_path.read_text(encoding="utf-8")
    assert "rejected guided action" in log_text
    assert "does-not-exist" in log_text


def test_resolve_guided_action_matches_aliases() -> None:
    start_action = cli_main._resolve_guided_action("start", "catalog")  # type: ignore[attr-defined]
    stop_action = cli_main._resolve_guided_action("stop", "clients")  # type: ignore[attr-defined]
    stop_all_action = cli_main._resolve_guided_action("stop", "all")  # type: ignore[attr-defined]
    restart_action = cli_main._resolve_guided_action("restart", "catalog")  # type: ignore[attr-defined]

    assert start_action is not None
    assert start_action["label"] == "Catalog"
    assert "-m catalog_service " in str(start_action.get("command_text") or "")
    assert stop_action is not None
    assert stop_action["label"] == "All clients"
    stop_command = str(stop_action.get("command_text") or "")
    assert "opamp_consumer\\.fluentbit\\.client" in stop_command
    assert "opamp_consumer\\.fluentd\\.client" in stop_command
    assert "opamp_consumer\\.client" in stop_command
    assert "opamp_consumer\\.fluentbit_client" not in stop_command
    assert "opamp_consumer\\.fluentd_client" not in stop_command
    assert stop_all_action is not None
    assert stop_all_action["label"] == "All managed processes"
    assert restart_action is not None
    assert restart_action["label"] == "Catalog"


def test_start_and_stop_action_orders_are_stable(monkeypatch) -> None:
    monkeypatch.delenv("OPAMP_DEMO", raising=False)
    start_labels = [label for label, _action in cli_main._start_actions()]  # type: ignore[attr-defined]
    stop_labels = [label for label, _action in cli_main._stop_actions()]  # type: ignore[attr-defined]
    restart_labels = [label for label, _action in cli_main._restart_actions()]  # type: ignore[attr-defined]

    assert start_labels == [
        "Server",
        "Catalog",
        "Config Editor",
        "Broker",
        "Simulator",
        "Fluent Bit client",
        "Fluentd client",
        "Vector client",
    ]
    assert stop_labels == [
        "Server",
        "Catalog",
        "Broker",
        "Simulator",
        "Config Editor",
        "Fluent Bit client",
        "Fluentd client",
        "Vector client",
        "All clients",
        "All managed processes",
    ]
    assert restart_labels == start_labels


def test_clear_stale_supervisor_signal_removes_existing_file(tmp_path: Path) -> None:
    signal_path = tmp_path / cli_main.SUPERVISOR_SEMAPHORE_FILENAME
    signal_path.write_text("", encoding="utf-8")

    cli_main._clear_stale_supervisor_signal(cwd=tmp_path)  # type: ignore[attr-defined]

    assert signal_path.exists() is False


def test_broker_stop_action_uses_cli_managed_process_records() -> None:
    stop_action = cli_main._resolve_guided_action("stop", "broker")  # type: ignore[attr-defined]

    assert stop_action is not None
    assert stop_action["kind"] == "stop_recorded"
    assert stop_action["record_names"] == ["Broker"]


def test_script_mode_generates_broker_launcher_script(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = cli_main._handle_command(  # type: ignore[attr-defined]
        "script broker-launch python -m opamp_broker.broker_app "
        "--config-path ./opamp_broker/config/broker.ui_responses.json"
    )

    suffix = ".cmd" if cli_main._is_windows() else ".sh"  # type: ignore[attr-defined]
    script_path = tmp_path / "scripts" / f"broker-launch{suffix}"

    assert exit_code == 0
    assert script_path.exists()
    script_text = script_path.read_text(encoding="utf-8")
    assert "python -m opamp_broker.broker_app" in script_text
    assert "--config-path ./opamp_broker/config/broker.ui_responses.json" in script_text


def test_list_command_prints_hierarchy(monkeypatch, capsys) -> None:
    monkeypatch.delenv("OPAMP_DEMO", raising=False)

    exit_code = cli_main._handle_command("list")  # type: ignore[attr-defined]
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Control flags:" in output
    assert "Top-level commands:" in output
    assert "Guided actions:" in output
    assert "start:" in output
    assert "stop:" in output
    assert "restart:" in output


def test_list_command_reflects_demo_flag(monkeypatch, tmp_path: Path, capsys) -> None:
    demo_config = tmp_path / "demo_profiles.json"
    demo_config.write_text(
        json.dumps(
            {
                "profiles": [
                    {
                        "name": "script-defaults",
                        "simulator": {"instances_path": "consumer-sim/consumer_instances.json"},
                        "fluentbit": {
                            "config_path": "tests/opamp.json",
                            "agent_config_path": "tests/fluent-bit.yaml",
                        },
                        "fluentd": {
                            "config_path": "consumer/opamp-fluentd.json",
                            "agent_config_path": "consumer/fluentd.conf",
                        },
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPAMP_DEMO", "true")
    monkeypatch.setattr(cli_main, "_demo_consumer_config_path", lambda: demo_config)

    exit_code = cli_main._handle_command("list")  # type: ignore[attr-defined]
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "OPAMP_DEMO: enabled" in output
    assert "  - demo" in output
    assert "Demo consumers (1: script-defaults)" in output


def test_restart_action_runs_stop_wait_cleanup_then_start(monkeypatch) -> None:
    events: list[str] = []
    restart_action = {
        "id": "server",
        "kind": "restart",
        "label": "Server",
        "start_action": {"id": "server", "kind": "background_start", "label": "Server"},
        "stop_action": {"id": "server", "kind": "shell", "label": "Server"},
    }

    def fake_stop(_action):
        events.append("stop")
        return 0

    def fake_tracked_pids(**_kwargs):
        events.append("track")
        return [4242]

    def fake_wait(**_kwargs):
        events.append("wait")
        return True, []

    def fake_prune():
        events.append("cleanup")
        return {"processes": []}

    def fake_start(_action):
        events.append("start")
        return 0

    monkeypatch.setattr(cli_main, "_execute_stop_action", fake_stop)
    monkeypatch.setattr(cli_main, "_tracked_restart_pids", fake_tracked_pids)
    monkeypatch.setattr(cli_main, "_wait_for_pids_to_exit", fake_wait)
    monkeypatch.setattr(cli_main, "_prune_cli_process_state", fake_prune)
    monkeypatch.setattr(cli_main, "_execute_start_action", fake_start)

    code = cli_main._execute_restart_action(restart_action)  # type: ignore[attr-defined]

    assert code == 0
    assert events == ["track", "stop", "wait", "cleanup", "start"]


def test_demo_mode_adds_profile_actions(monkeypatch, tmp_path: Path) -> None:
    demo_config = tmp_path / "demo_profiles.json"
    demo_config.write_text(
        json.dumps(
            {
                "profiles": [
                    {
                        "name": "script-defaults",
                        "simulator": {"instances_path": "consumer-sim/consumer_instances.json"},
                        "fluentbit": {
                            "config_path": "tests/opamp.json",
                            "agent_config_path": "tests/fluent-bit.yaml",
                        },
                        "fluentd": {
                            "config_path": "consumer/opamp-fluentd.json",
                            "agent_config_path": "consumer/fluentd.conf",
                        },
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("OPAMP_DEMO", "true")
    monkeypatch.setattr(cli_main, "_demo_consumer_config_path", lambda: demo_config)

    start_labels = [label for label, _action in cli_main._start_actions()]  # type: ignore[attr-defined]
    stop_labels = [label for label, _action in cli_main._stop_actions()]  # type: ignore[attr-defined]

    assert "Demo consumers (1: script-defaults)" in start_labels
    assert "Demo consumers (1: script-defaults)" in stop_labels


def test_demo_profile_loader_prefers_scenario_description(monkeypatch, tmp_path: Path) -> None:
    demo_config = tmp_path / "demo_profiles.json"
    demo_config.write_text(
        json.dumps(
            {
                "profiles": [
                    {
                        "name": "repo-defaults",
                        "description": "legacy description",
                        "scenario_description": "preferred scenario description",
                        "simulator": {"instances_path": "consumer-sim/config/consumer_instances.json"},
                        "fluentbit": {
                            "config_path": "config/opamp.json",
                            "agent_config_path": "consumer/fluent-bit.yaml",
                        },
                        "fluentd": {
                            "config_path": "config/opamp.json",
                            "agent_config_path": "consumer/fluentd.conf",
                        },
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cli_main, "_demo_consumer_config_path", lambda: demo_config)

    profiles = cli_main._load_demo_consumer_profiles()  # type: ignore[attr-defined]

    assert profiles[0]["scenario_description"] == "preferred scenario description"


def test_demo_profile_loader_carries_elastic_agent_and_container_config(
    monkeypatch,
    tmp_path: Path,
) -> None:
    demo_config = tmp_path / "demo_profiles.json"
    demo_config.write_text(
        json.dumps(
            {
                "profiles": [
                    {
                        "name": "elastic-logstash",
                        "containers": [
                            {
                                "id": "logstash-local",
                                "label": "Logstash local pipeline",
                            }
                        ],
                        "elastic_agent": {
                            "config_path": "tests/logstash/opamp-consumer-elastic-agent-logstash-plugin.json",
                            "agent_config_path": "tests/logstash/elastic-agent.yml",
                        },
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cli_main, "_demo_consumer_config_path", lambda: demo_config)

    profiles = cli_main._load_demo_consumer_profiles()  # type: ignore[attr-defined]

    assert profiles[0]["containers"][0]["id"] == "logstash-local"
    assert profiles[0]["elastic_agent"]["config_path"].endswith("logstash-plugin.json")


def test_checked_in_full_demo_profile_covers_all_agent_types() -> None:
    profiles = cli_main._load_demo_consumer_profiles()  # type: ignore[attr-defined]
    profile = next(
        item for item in profiles if item["name"] == "Demo setup (Full multi-agent remote config)"
    )

    assert profile["containers"][0]["id"] == "logstash-full-demo"
    assert set(profile) >= {
        "fluentbit",
        "fluentd",
        "vector",
        "elastic_agent",
        "elastic_heartbeat",
    }
    assert profile["elastic_heartbeat"]["config_path"].endswith("opamp-heartbeat.json")
    assert json.loads(
        (cli_main._repo_root() / profile["fluentbit"]["config_path"]).read_text(encoding="utf-8")
    )["consumer"]["agent_config_path"] == "docs/full-demo/active/fluent-bit.yaml"
    assert json.loads(
        (cli_main._repo_root() / profile["vector"]["config_path"]).read_text(encoding="utf-8")
    )["consumer"]["agent_config_path"] == "docs/full-demo/active/vector.yaml"
    for component in ("fluentd", "elastic_agent", "elastic_heartbeat"):
        config = json.loads(
            (cli_main._repo_root() / profile[component]["config_path"]).read_text(encoding="utf-8")
        )
        assert config["consumer"]["agent_config_path"].startswith("docs/full-demo/active/")


def test_demo_consumer_action_carries_scenario_description() -> None:
    action = cli_main._demo_consumer_start_action(  # type: ignore[attr-defined]
        {
            "name": "repo-defaults",
            "scenario_description": "Profile scenario text",
        }
    )

    assert action["scenario_description"] == "Profile scenario text"


def test_demo_profile_alias_resolves_guided_action(monkeypatch, tmp_path: Path) -> None:
    demo_config = tmp_path / "demo_profiles.json"
    demo_config.write_text(
        json.dumps(
            {
                "profiles": [
                    {
                        "name": "repo-defaults",
                        "simulator": {"instances_path": "consumer-sim/consumer_instances.json"},
                        "fluentbit": {
                            "config_path": "config/opamp.json",
                            "agent_config_path": "consumer/fluent-bit.yaml",
                        },
                        "fluentd": {
                            "config_path": "config/opamp.json",
                            "agent_config_path": "consumer/fluentd.conf",
                        },
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("OPAMP_DEMO", "true")
    monkeypatch.setattr(cli_main, "_demo_consumer_config_path", lambda: demo_config)

    action = cli_main._resolve_guided_action("start", "demo consumers repo-defaults")  # type: ignore[attr-defined]

    assert action is not None
    assert action["kind"] == "demo_consumers_start"
    assert action["profile_name"] == "repo-defaults"


def test_demo_profile_numeric_alias_resolves_guided_action(monkeypatch, tmp_path: Path) -> None:
    demo_config = tmp_path / "demo_profiles.json"
    demo_config.write_text(
        json.dumps(
            {
                "profiles": [
                    {
                        "name": "script-defaults",
                        "simulator": {"instances_path": "consumer-sim/consumer_instances.json"},
                    },
                    {
                        "name": "repo-defaults",
                        "simulator": {"instances_path": "consumer-sim/consumer_instances.json"},
                    },
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("OPAMP_DEMO", "true")
    monkeypatch.setattr(cli_main, "_demo_consumer_config_path", lambda: demo_config)

    action = cli_main._resolve_guided_action("start", "demo 2")  # type: ignore[attr-defined]

    assert action is not None
    assert action["kind"] == "demo_consumers_start"
    assert action["profile_name"] == "repo-defaults"
    assert action["profile_index"] == 2


def test_start_numeric_selection_resolves_displayed_option(monkeypatch) -> None:
    actions = [
        ("Server", {"label": "Server", "kind": "background_start"}),
        ("Broker", {"label": "Broker", "kind": "background_start"}),
    ]
    monkeypatch.setattr(cli_main, "_guided_actions_for_intent", lambda _intent: actions)

    action = cli_main._resolve_guided_action("start", "2")  # type: ignore[attr-defined]

    assert action == {"label": "Broker", "kind": "background_start"}


def test_stop_numeric_selection_resolves_displayed_option(monkeypatch) -> None:
    actions = [
        ("Server", {"label": "Server", "kind": "stop_recorded"}),
        ("All clients", {"label": "All clients", "kind": "shell"}),
    ]
    monkeypatch.setattr(cli_main, "_guided_actions_for_intent", lambda _intent: actions)

    action = cli_main._resolve_guided_action("stop", "2")  # type: ignore[attr-defined]

    assert action == {"label": "All clients", "kind": "shell"}


def test_numeric_selection_outside_displayed_options_is_not_resolved(
    monkeypatch,
) -> None:
    actions = [
        ("Server", {"label": "Server", "kind": "background_start"}),
    ]
    monkeypatch.setattr(cli_main, "_guided_actions_for_intent", lambda _intent: actions)

    action = cli_main._resolve_guided_action("start", "2")  # type: ignore[attr-defined]

    assert action is None


def test_top_level_commands_include_demo_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("OPAMP_DEMO", "true")

    commands = cli_main._top_level_commands()  # type: ignore[attr-defined]

    assert "demo" in commands


def test_split_guided_command_maps_demo_shorthand_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("OPAMP_DEMO", "true")

    assert cli_main._split_guided_command("demo") == ("start", "demo consumers")  # type: ignore[attr-defined]
    assert cli_main._split_guided_command("demo repo-defaults") == ("start", "demo repo-defaults")  # type: ignore[attr-defined]
    assert cli_main._split_guided_command("demo 2") == ("start", "demo 2")  # type: ignore[attr-defined]


def test_split_guided_command_ignores_demo_shorthand_when_disabled(monkeypatch) -> None:
    monkeypatch.delenv("OPAMP_DEMO", raising=False)

    assert cli_main._split_guided_command("demo") is None  # type: ignore[attr-defined]


def test_start_demo_consumers_prompts_for_profile_choices(monkeypatch, tmp_path: Path) -> None:
    demo_config = tmp_path / "demo_profiles.json"
    demo_config.write_text(
        json.dumps(
            {
                "profiles": [
                    {
                        "name": "script-defaults",
                        "simulator": {"instances_path": "consumer-sim/consumer_instances.json"},
                        "fluentbit": {
                            "config_path": "tests/opamp.json",
                            "agent_config_path": "tests/fluent-bit.yaml",
                        },
                        "fluentd": {
                            "config_path": "consumer/opamp-fluentd.json",
                            "agent_config_path": "consumer/fluentd.conf",
                        },
                    },
                    {
                        "name": "repo-defaults",
                        "simulator": {"instances_path": "consumer-sim/consumer_instances.json"},
                        "fluentbit": {
                            "config_path": "config/opamp.json",
                            "agent_config_path": "consumer/fluent-bit.yaml",
                        },
                        "fluentd": {
                            "config_path": "config/opamp.json",
                            "agent_config_path": "consumer/fluentd.conf",
                        },
                    },
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPAMP_DEMO", "true")
    monkeypatch.setattr(cli_main, "_demo_consumer_config_path", lambda: demo_config)

    captured_labels: list[str] = []

    def fake_select(*, input_reader, intent, actions):  # type: ignore[no-untyped-def]
        del input_reader
        del intent
        captured_labels.extend(label for label, _action in actions)
        return actions[0][1]

    monkeypatch.setattr(cli_main, "_select_guided_action", fake_select)
    monkeypatch.setattr(cli_main, "_execute_start_action", lambda action: 0)

    code = cli_main._execute_guided_action(  # type: ignore[attr-defined]
        input_reader=None,
        intent="start",
        selection="demo consumers",
    )

    assert code == 0
    assert captured_labels == [
        "Demo consumers (1: script-defaults)",
        "Demo consumers (2: repo-defaults)",
    ]


def test_select_guided_action_can_show_scenario_description_before_selection(
    monkeypatch,
    capsys,
) -> None:
    responses = iter(["d1", "1"])
    actions = [
        (
            "Demo consumers (repo-defaults)",
            {
                "label": "Demo consumers (repo-defaults)",
                "scenario_description": "Starts the simulator and both consumer clients with repo defaults.",
            },
        )
    ]
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    selected = cli_main._select_guided_action(  # type: ignore[attr-defined]
        input_reader=None,
        intent="start",
        actions=actions,
    )
    output = capsys.readouterr().out

    assert selected == actions[0][1]
    assert "d<number>. view scenario description" in output
    assert "Starts the simulator and both consumer clients with repo defaults." in output


def test_start_demo_consumers_allows_partial_observer_profile(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path
    observer_config = repo_root / "tests" / "opamp-consumer-observer.json"
    fluentbit_config = repo_root / "consumer" / "fluent-bit.yaml"
    simulator_instances = repo_root / "consumer-sim" / "config" / "consumer_instance-1.json"
    observer_config.parent.mkdir(parents=True, exist_ok=True)
    fluentbit_config.parent.mkdir(parents=True, exist_ok=True)
    simulator_instances.parent.mkdir(parents=True, exist_ok=True)
    observer_config.write_text("{}\n", encoding="utf-8")
    fluentbit_config.write_text("service:\n  flush: 1\n", encoding="utf-8")
    simulator_instances.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(cli_main, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(
        cli_main,
        "_demo_profile_by_name",
        lambda _name: {
            "name": "Demo setup (Flbx1 Observer)",
            "fluentbit": {
                "config_path": "tests/opamp-consumer-observer.json",
                "agent_config_path": "consumer/fluent-bit.yaml",
            },
            "simulator": {
                "instances_path": "consumer-sim/config/consumer_instance-1.json",
            },
        },
    )
    monkeypatch.setattr(cli_main, "_launch_background_process", lambda _action: 0)
    monkeypatch.setattr(cli_main, "_record_simulator_batch", lambda _action: 0)

    code = cli_main._start_demo_consumers(  # type: ignore[attr-defined]
        {"profile_name": "Demo setup (Flbx1 Observer)"}
    )

    assert code == 0


def test_start_demo_consumers_uses_configured_agent_path_without_profile_override(
    monkeypatch,
    tmp_path: Path,
) -> None:
    profile_name = "config-driven-vector"
    repo_root = tmp_path
    config_path = repo_root / "consumer" / "opamp-vector.json"
    agent_path = repo_root / "docs" / "vector-self-monitor" / "vector-self-monitor.yaml"
    config_path.parent.mkdir(parents=True)
    agent_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "consumer": {
                    "server_url": "http://localhost:8080",
                    "agent_config_path": str(agent_path),
                    "agent_additional_params": [],
                    "service_type": "vector",
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )
    agent_path.write_text("api:\n  enabled: true\n", encoding="utf-8")
    monkeypatch.setattr(cli_main, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(
        cli_main,
        "_demo_profile_by_name",
        lambda _name: {
            "name": profile_name,
            "vector": {
                "config_path": "consumer/opamp-vector.json",
            },
        },
    )
    launched: list[dict[str, Any]] = []
    monkeypatch.setattr(cli_main, "_launch_background_process", lambda action: launched.append(action) or 0)

    code = cli_main._start_demo_consumers(  # type: ignore[attr-defined]
        {"profile_name": profile_name}
    )

    assert code == 0
    assert len(launched) == 1
    assert launched[0]["label"] == f"Vector client ({profile_name})"
    assert "--config-path" in launched[0]["argv"]
    assert "--agent-config-path" not in launched[0]["argv"]
    assert launched[0]["record_name"] == f"Demo:{profile_name}:Vector client"


def test_container_start_action_uses_configured_runtime_command(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    (repo_root / "tests" / "logstash").mkdir(parents=True)
    (repo_root / "tests" / "logstash" / "logstash.container.conf").write_text(
        "input {}\n",
        encoding="utf-8",
    )
    action = container_management.container_start_action_from_entry(
        {
            "id": "logstash-local",
            "label": "Logstash local pipeline",
            "container_name": "opamp-logstash",
            "replace_existing": True,
            "image_candidates": ["docker.elastic.co/logstash/logstash:9.5.1", "logstash:9.5.1"],
            "ports": ["127.0.0.1:5044:5044"],
            "volumes": [
                {
                    "host_path": "tests/logstash/logstash.container.conf",
                    "container_path": "/usr/share/logstash/pipeline/logstash.conf",
                    "read_only": True,
                }
            ],
            "ensure_dirs": ["tests/logstash/out"],
            "command": ["logstash", "-f", "/usr/share/logstash/pipeline/logstash.conf"],
        },
        runtime="/usr/bin/podman",
        repo_root=repo_root,
        resolve_path_from_repo=lambda raw_path: (repo_root / raw_path).resolve(),
        command_text_from_args=cli_main._command_text_from_args,  # type: ignore[attr-defined]
        background_start_action=cli_main._background_start_action,  # type: ignore[attr-defined]
        build_exec_env=cli_main._build_exec_env,  # type: ignore[attr-defined]
        demo_record_prefix=cli_main._demo_record_prefix,  # type: ignore[attr-defined]
    )

    assert action is not None
    argv = action["argv"]
    assert argv[:6] == [
        "/usr/bin/podman",
        "run",
        "--rm",
        "--replace",
        "--name",
        "opamp-logstash",
    ]
    assert argv[6] == "-p"
    assert "127.0.0.1:5044:5044" in argv
    assert "docker.elastic.co/logstash/logstash:9.5.1" in argv
    assert "/usr/share/logstash/pipeline/logstash.conf" in " ".join(argv)
    assert action["ensure_dirs"] == [str(repo_root / "tests" / "logstash" / "out")]
    assert action["metadata"]["container_name"] == "opamp-logstash"
    assert action["readiness_tcp"] == "127.0.0.1:5044"


def test_container_start_action_omits_replace_for_docker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    action = container_management.container_start_action_from_entry(
        {
            "id": "logstash-local",
            "label": "Logstash local pipeline",
            "container_name": "opamp-logstash",
            "replace_existing": True,
            "image": "logstash:9.5.1",
        },
        runtime="/usr/bin/docker",
        repo_root=repo_root,
        resolve_path_from_repo=lambda raw_path: (repo_root / raw_path).resolve(),
        command_text_from_args=cli_main._command_text_from_args,  # type: ignore[attr-defined]
        background_start_action=cli_main._background_start_action,  # type: ignore[attr-defined]
        build_exec_env=cli_main._build_exec_env,  # type: ignore[attr-defined]
        demo_record_prefix=cli_main._demo_record_prefix,  # type: ignore[attr-defined]
    )

    assert action is not None
    argv = action["argv"]
    assert argv[:5] == [
        "/usr/bin/docker",
        "run",
        "--rm",
        "--name",
        "opamp-logstash",
    ]
    assert "--replace" not in argv


def test_container_readiness_tcp_supports_host_qualified_port() -> None:
    endpoint = container_management.container_readiness_tcp(["127.0.0.1:15044:5044"])

    assert endpoint == "127.0.0.1:15044"


def test_wait_for_background_start_waits_for_tcp_readiness(
    monkeypatch,
    tmp_path: Path,
) -> None:
    process = SimpleNamespace(poll=lambda: None)
    attempts = {"count": 0}

    def fake_tcp_ready(endpoint: str) -> bool:
        attempts["count"] += 1
        assert endpoint == "127.0.0.1:5044"
        return attempts["count"] == 2

    monkeypatch.setattr(cli_main, "_tcp_ready", fake_tcp_ready)
    monkeypatch.setattr(cli_main.time, "sleep", lambda _seconds: None)

    ready, reason = cli_main._wait_for_background_start(  # type: ignore[attr-defined]
        process=process,
        log_file=tmp_path / "process.log",
        readiness_url="",
        readiness_tcp="127.0.0.1:5044",
    )

    assert ready is True
    assert reason == ""
    assert attempts["count"] == 2


def test_dev_containers_command_is_listed_when_runtime_and_actions_available(
    monkeypatch,
) -> None:
    monkeypatch.setattr(container_management, "container_runtime_executable", lambda: "/usr/bin/podman")
    monkeypatch.setattr(
        cli_main,
        "_configured_container_start_actions",
        lambda: [("Logstash local pipeline", {"label": "Logstash local pipeline"})],
    )

    commands = cli_main._top_level_commands()  # type: ignore[attr-defined]

    assert "dev-containers" in commands


def test_execute_dev_container_workflow_launches_selected_action(monkeypatch) -> None:
    launched: list[str] = []
    action = {
        "label": "Logstash local pipeline",
        "aliases": ["logstash"],
    }
    monkeypatch.setattr(container_management, "container_runtime_executable", lambda: "/usr/bin/podman")
    monkeypatch.setattr(container_management, "container_runtime_ready", lambda _runtime, **_kwargs: (True, ""))
    monkeypatch.setattr(
        cli_main,
        "_configured_container_start_actions",
        lambda: [("Logstash local pipeline", action)],
    )
    monkeypatch.setattr(
        cli_main,
        "_launch_background_process",
        lambda selected: launched.append(selected["label"]) or 0,
    )

    code = dev_commands.execute_dev_container_workflow(
        command_name="dev-containers",
        selection="logstash",
        container_runtime_executable=container_management.container_runtime_executable,
        container_runtime_ready=lambda runtime: container_management.container_runtime_ready(
            runtime,
            windows_no_console_kwargs=cli_main._windows_no_console_kwargs,  # type: ignore[attr-defined]
        ),
        print_container_runtime_unavailable=container_management.print_container_runtime_unavailable,
        configured_container_start_actions=cli_main._configured_container_start_actions,  # type: ignore[attr-defined]
        action_matches_alias=cli_main._action_matches_alias,  # type: ignore[attr-defined]
        select_guided_action=lambda _intent, _actions: None,
        launch_background_process=cli_main._launch_background_process,  # type: ignore[attr-defined]
    )

    assert code == 0
    assert launched == ["Logstash local pipeline"]


def test_execute_dev_container_workflow_rejects_unready_runtime(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(container_management, "container_runtime_executable", lambda: "/usr/bin/podman")
    monkeypatch.setattr(
        container_management,
        "container_runtime_ready",
        lambda _runtime, **_kwargs: (False, "unable to connect to Podman socket"),
    )

    code = dev_commands.execute_dev_container_workflow(
        command_name="dev-containers",
        selection="logstash",
        container_runtime_executable=container_management.container_runtime_executable,
        container_runtime_ready=lambda runtime: container_management.container_runtime_ready(
            runtime,
            windows_no_console_kwargs=cli_main._windows_no_console_kwargs,  # type: ignore[attr-defined]
        ),
        print_container_runtime_unavailable=container_management.print_container_runtime_unavailable,
        configured_container_start_actions=cli_main._configured_container_start_actions,  # type: ignore[attr-defined]
        action_matches_alias=cli_main._action_matches_alias,  # type: ignore[attr-defined]
        select_guided_action=lambda _intent, _actions: None,
        launch_background_process=cli_main._launch_background_process,  # type: ignore[attr-defined]
    )

    assert code == 1
    captured = capsys.readouterr()
    assert "Container runtime is installed but not ready" in captured.err
    assert "unable to connect to Podman socket" in captured.err
    assert "podman machine start" in captured.err


def test_start_demo_consumers_runs_container_then_elastic_agent_client(
    monkeypatch,
    tmp_path: Path,
) -> None:
    profile_name = "elastic-logstash"
    repo_root = tmp_path
    config_path = repo_root / "tests" / "logstash" / "opamp-consumer-elastic-agent-logstash-plugin.json"
    agent_path = repo_root / "tests" / "logstash" / "elastic-agent.yml"
    pipeline_path = repo_root / "tests" / "logstash" / "logstash.container.conf"
    pipeline_path.parent.mkdir(parents=True)
    config_path.write_text("{}\n", encoding="utf-8")
    agent_path.write_text("outputs: {}\n", encoding="utf-8")
    pipeline_path.write_text("input {}\n", encoding="utf-8")
    monkeypatch.setattr(cli_main, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(container_management, "container_runtime_executable", lambda: "/usr/bin/podman")
    monkeypatch.setattr(container_management, "container_runtime_ready", lambda _runtime, **_kwargs: (True, ""))
    monkeypatch.setattr(
        cli_main,
        "_demo_profile_by_name",
        lambda _name: {
            "name": profile_name,
            "containers": [
                {
                    "id": "logstash-local",
                    "label": "Logstash local pipeline",
                    "image": "logstash:9.5.1",
                    "volumes": [
                        {
                            "host_path": "tests/logstash/logstash.container.conf",
                            "container_path": "/usr/share/logstash/pipeline/logstash.conf",
                            "read_only": True,
                        }
                    ],
                }
            ],
            "elastic_agent": {
                "config_path": "tests/logstash/opamp-consumer-elastic-agent-logstash-plugin.json",
                "agent_config_path": "tests/logstash/elastic-agent.yml",
            },
        },
    )
    launched: list[dict[str, Any]] = []

    def fake_launch(action):
        launched.append(action)
        return 0

    monkeypatch.setattr(cli_main, "_launch_background_process", fake_launch)

    code = cli_main._start_demo_consumers(  # type: ignore[attr-defined]
        {"profile_name": profile_name}
    )

    assert code == 0
    assert [item["label"] for item in launched] == [
        f"Logstash local pipeline ({profile_name})",
        f"Elastic Agent client ({profile_name})",
    ]
    assert launched[1]["argv"][:3] == [
        cli_main.sys.executable,
        "-m",
        "opamp_consumer.client",
    ]
    assert launched[1]["clear_supervisor_signal"] is True


def test_start_demo_consumers_rejects_unready_container_runtime(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    profile_name = "elastic-logstash"
    repo_root = tmp_path
    config_path = repo_root / "tests" / "logstash" / "opamp-consumer-elastic-agent-logstash-plugin.json"
    agent_path = repo_root / "tests" / "logstash" / "elastic-agent.yml"
    pipeline_path = repo_root / "tests" / "logstash" / "logstash.container.conf"
    pipeline_path.parent.mkdir(parents=True)
    config_path.write_text("{}\n", encoding="utf-8")
    agent_path.write_text("outputs: {}\n", encoding="utf-8")
    pipeline_path.write_text("input {}\n", encoding="utf-8")
    monkeypatch.setattr(cli_main, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(container_management, "container_runtime_executable", lambda: "/usr/bin/podman")
    monkeypatch.setattr(
        container_management,
        "container_runtime_ready",
        lambda _runtime, **_kwargs: (False, "Cannot connect to Podman"),
    )
    monkeypatch.setattr(
        cli_main,
        "_demo_profile_by_name",
        lambda _name: {
            "name": profile_name,
            "containers": [
                {
                    "id": "logstash-local",
                    "label": "Logstash local pipeline",
                    "image": "logstash:9.5.1",
                    "volumes": [
                        {
                            "host_path": "tests/logstash/logstash.container.conf",
                            "container_path": "/usr/share/logstash/pipeline/logstash.conf",
                            "read_only": True,
                        }
                    ],
                }
            ],
            "elastic_agent": {
                "config_path": "tests/logstash/opamp-consumer-elastic-agent-logstash-plugin.json",
                "agent_config_path": "tests/logstash/elastic-agent.yml",
            },
        },
    )
    launched: list[dict[str, Any]] = []
    monkeypatch.setattr(cli_main, "_launch_background_process", launched.append)

    code = cli_main._start_demo_consumers(  # type: ignore[attr-defined]
        {"profile_name": profile_name}
    )

    assert code == 1
    assert launched == []
    captured = capsys.readouterr()
    assert "Container runtime is installed but not ready" in captured.err
    assert "Cannot connect to Podman" in captured.err
    assert "podman machine start" in captured.err


def test_start_demo_consumers_rejects_incomplete_fluentd_configuration(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    monkeypatch.setattr(cli_main, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        cli_main,
        "_demo_profile_by_name",
        lambda _name: {
            "name": "broken-profile",
            "fluentd": {
                "agent_config_path": "consumer/fluentd.conf",
            },
        },
    )

    code = cli_main._start_demo_consumers(  # type: ignore[attr-defined]
        {"profile_name": "broken-profile"}
    )
    output = capsys.readouterr().err

    assert code == 1
    assert "Fluentd configuration is incomplete" in output


def test_stop_all_recorded_processes_loops_all_record_names(monkeypatch) -> None:
    monkeypatch.setattr(
        cli_main,
        "_prune_cli_process_state",
        lambda: {
            "processes": [
                {"name": "Server", "pid": 1001},
                {"name": "Fluent Bit client", "pid": 1002},
                {"name": "Server", "pid": 1003},
            ]
        },
    )
    captured: dict[str, list[str]] = {"names": []}

    def fake_stop(names):
        captured["names"] = list(names)
        return 0

    monkeypatch.setattr(cli_main, "_stop_recorded_processes", fake_stop)

    code = cli_main._stop_all_recorded_processes()  # type: ignore[attr-defined]

    assert code == 0
    assert sorted(captured["names"]) == ["Fluent Bit client", "Server"]


def test_stop_recorded_processes_reports_when_nothing_matches(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli_main,
        "_prune_cli_process_state",
        lambda: {
            "processes": [
                {"name": "Config Editor", "pid": 1001},
            ]
        },
    )

    code = cli_main._stop_recorded_processes(["Server"])  # type: ignore[attr-defined]
    output = capsys.readouterr().out

    assert code == 0
    assert "No recorded process IDs found for that selection." in output


def test_stop_recorded_processes_uses_container_runtime_stop(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        cli_main,
        "_prune_cli_process_state",
        lambda: {
            "processes": [
                {
                    "name": "Demo:elastic-logstash:Container:Logstash local pipeline",
                    "pid": 1001,
                    "metadata": {
                        "container_runtime": "/usr/bin/podman",
                        "container_id": "logstash-local",
                        "container_name": "opamp-logstash",
                    },
                },
            ]
        },
    )
    removed: list[set[str]] = []
    commands: list[list[str]] = []
    monkeypatch.setattr(cli_main, "_remove_cli_process_records", removed.append)
    monkeypatch.setattr(cli_main, "_is_windows", lambda: False)
    monkeypatch.setattr(
        cli_main.os,
        "kill",
        lambda _pid, _signal: pytest.fail("container stop should not kill the PID"),
    )

    def fake_run(command, **_kwargs):
        commands.append(list(command))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(cli_main.subprocess, "run", fake_run)

    record_name = "Demo:elastic-logstash:Container:Logstash local pipeline"
    code = cli_main._stop_recorded_processes([record_name])  # type: ignore[attr-defined]
    output = capsys.readouterr().out

    assert code == 0
    assert commands == [
        [
            "/usr/bin/podman",
            "stop",
            "--time",
            str(container_management.CONTAINER_STOP_TIMEOUT_SECONDS),
            "opamp-logstash",
        ]
    ]
    assert removed == [{record_name}]
    assert "Stopped container opamp-logstash" in output
    assert f"Stopped {record_name} pid=1001" in output


def test_execute_stop_server_propagates_failure_when_not_running(monkeypatch, capsys) -> None:
    action = cli_main._resolve_guided_action("stop", "server")  # type: ignore[attr-defined]
    captured: dict[str, str] = {"command": ""}

    def fake_handle_command(command_text: str) -> int:
        captured["command"] = command_text
        return 1

    monkeypatch.setattr(cli_main, "_handle_command", fake_handle_command)

    assert action is not None

    code = cli_main._execute_stop_action(action)  # type: ignore[attr-defined]
    output = capsys.readouterr().out

    assert code == 1
    assert "Executing:" in output
    assert "127.0.0.1:8080" in captured["command"]
    assert "/api/shutdown" in captured["command"]


def test_stop_all_recorded_processes_reports_when_none_recorded(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_main, "_prune_cli_process_state", lambda: {"processes": []})

    code = cli_main._stop_all_recorded_processes()  # type: ignore[attr-defined]
    output = capsys.readouterr().out

    assert code == 0
    assert "No recorded managed processes to stop." in output


def test_record_simulator_batch_reports_logged_failure_detail(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    log_file = tmp_path / "simulator.log"
    state_file = tmp_path / "launcher_state.json"

    def fake_prepare_log(**_kwargs) -> Path:
        log_file.write_text("", encoding="utf-8")
        return log_file

    def fake_run(argv: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        stdout_handle = kwargs["stdout"]
        stdout_handle.write(
            "[consumer-sim] cannot start: existing launched consumer instances are still running\n"
        )
        return subprocess.CompletedProcess(args=argv, returncode=1)

    monkeypatch.setattr(cli_main, "_prepare_launch_log", fake_prepare_log)
    monkeypatch.setattr(cli_main.subprocess, "run", fake_run)

    code = cli_main._record_simulator_batch(  # type: ignore[attr-defined]
        {
            "label": "Simulator",
            "command_text": "python consumer-sim/src/consumer_sim_launcher.py start",
            "argv": ["python", "consumer-sim/src/consumer_sim_launcher.py", "start"],
            "cwd": str(tmp_path),
            "env": {},
            "state_file": str(state_file),
        }
    )
    captured = capsys.readouterr()

    assert code == 1
    assert "Simulator failed to start:" in captured.err
    assert "existing launched consumer instances are still running" in captured.err
    assert str(log_file) in captured.err


def test_record_simulator_batch_short_circuits_when_already_running(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    state_file = tmp_path / "launcher_state.json"
    state_file.write_text(
        json.dumps(
            {
                "instances": [
                    {"name": "consumer-simulator-1", "pid": 4321},
                    {"name": "consumer-simulator-2", "pid": 4322},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(cli_main, "_is_process_running", lambda pid: pid in {4321, 4322})
    monkeypatch.setattr(
        cli_main.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("launcher should not run")),
    )

    code = cli_main._record_simulator_batch(  # type: ignore[attr-defined]
        {
            "label": "Simulator",
            "command_text": "python consumer-sim/src/consumer_sim_launcher.py start",
            "argv": ["python", "consumer-sim/src/consumer_sim_launcher.py", "start"],
            "cwd": str(tmp_path),
            "env": {},
            "state_file": str(state_file),
        }
    )
    captured = capsys.readouterr()

    assert code == 1
    assert "Simulator already running:" in captured.err
    assert "consumer-simulator-1" in captured.err
    assert "consumer-simulator-2" in captured.err
    assert "Stop simulator before starting it again." in captured.err


def test_detected_behavior_flags_returns_empty_when_none_set(monkeypatch) -> None:
    monkeypatch.delenv("OPAMP_DEMO", raising=False)
    monkeypatch.delenv("APP_ENABLE_DEV_FEATURES", raising=False)
    monkeypatch.setattr(
        cli_main.process_tail,
        "process_tail_enabled",
        lambda *, load_settings: False,
    )

    detected = cli_main._detected_behavior_flags()  # type: ignore[attr-defined]

    assert detected == []


def test_detected_behavior_flags_returns_only_enabled_flags(monkeypatch) -> None:
    monkeypatch.setenv("OPAMP_DEMO", "true")
    monkeypatch.setenv("APP_ENABLE_DEV_FEATURES", "true")
    monkeypatch.setattr(
        cli_main.process_tail,
        "process_tail_enabled",
        lambda *, load_settings: True,
    )

    detected = cli_main._detected_behavior_flags()  # type: ignore[attr-defined]

    assert "OPAMP_DEMO=true" in detected
    assert "APP_ENABLE_DEV_FEATURES=true" in detected
    assert "enable_process_tail=true" in detected


def test_top_level_commands_include_dev_flb_config_only_when_available(monkeypatch) -> None:
    monkeypatch.setattr(cli_main, "_demo_mode_enabled", lambda: False)
    monkeypatch.setattr(cli_main, "_fluentbit_dev_tool_available", lambda: True)
    monkeypatch.setattr(cli_main, "_mcp_dev_tool_available", lambda: False)

    commands = cli_main._top_level_commands()  # type: ignore[attr-defined]

    assert "dev-flb-config" in commands

    monkeypatch.setattr(cli_main, "_fluentbit_dev_tool_available", lambda: False)
    commands = cli_main._top_level_commands()  # type: ignore[attr-defined]
    assert "dev-flb-config" not in commands


def test_top_level_commands_include_dev_mcp_config_only_when_available(monkeypatch) -> None:
    monkeypatch.setattr(cli_main, "_demo_mode_enabled", lambda: False)
    monkeypatch.setattr(cli_main, "_fluentbit_dev_tool_available", lambda: False)
    monkeypatch.setattr(cli_main, "_mcp_dev_tool_available", lambda: True)
    monkeypatch.setattr(cli_main, "_dev_pid_lookup_available", lambda: False)

    commands = cli_main._top_level_commands()  # type: ignore[attr-defined]

    assert "dev-mcp-config" in commands

    monkeypatch.setattr(cli_main, "_mcp_dev_tool_available", lambda: False)
    commands = cli_main._top_level_commands()  # type: ignore[attr-defined]
    assert "dev-mcp-config" not in commands


def test_top_level_commands_include_dev_pid_lookup_only_when_available(monkeypatch) -> None:
    monkeypatch.setattr(cli_main, "_demo_mode_enabled", lambda: False)
    monkeypatch.setattr(cli_main, "_fluentbit_dev_tool_available", lambda: False)
    monkeypatch.setattr(cli_main, "_mcp_dev_tool_available", lambda: False)
    monkeypatch.setattr(cli_main, "_dev_pid_lookup_available", lambda: True)

    commands = cli_main._top_level_commands()  # type: ignore[attr-defined]

    assert "dev-pid-lookup" in commands

    monkeypatch.setattr(cli_main, "_dev_pid_lookup_available", lambda: False)
    commands = cli_main._top_level_commands()  # type: ignore[attr-defined]
    assert "dev-pid-lookup" not in commands


def test_handle_command_routes_dev_flb_config_to_workflow(monkeypatch) -> None:
    called: dict[str, int] = {"count": 0}

    def fake_workflow(**kwargs):  # type: ignore[no-untyped-def]
        assert kwargs["command_name"] == "dev-flb-config"
        called["count"] += 1
        return 0

    monkeypatch.setattr(dev_commands, "execute_dev_tool_workflow", fake_workflow)

    code = cli_main._handle_command("dev-flb-config")  # type: ignore[attr-defined]

    assert code == 0
    assert called["count"] == 1


def test_handle_command_routes_dev_mcp_config_to_workflow(monkeypatch) -> None:
    called: dict[str, int] = {"count": 0}

    def fake_workflow(**kwargs):  # type: ignore[no-untyped-def]
        assert kwargs["command_name"] == "dev-mcp-config"
        called["count"] += 1
        return 0

    monkeypatch.setattr(dev_commands, "execute_dev_tool_workflow", fake_workflow)

    code = cli_main._handle_command("dev-mcp-config")  # type: ignore[attr-defined]

    assert code == 0
    assert called["count"] == 1


def test_handle_command_routes_dev_pid_lookup_to_workflow(monkeypatch) -> None:
    called: dict[str, int] = {"count": 0}

    def fake_workflow(**kwargs):  # type: ignore[no-untyped-def]
        assert kwargs["command_name"] == "dev-pid-lookup"
        called["count"] += 1
        return 0

    monkeypatch.setattr(dev_commands, "execute_dev_pid_lookup_workflow", fake_workflow)

    code = cli_main._handle_command("dev-pid-lookup")  # type: ignore[attr-defined]

    assert code == 0
    assert called["count"] == 1


def test_execute_dev_fluentbit_config_workflow_prompts_and_runs_selected_tool(monkeypatch) -> None:
    specs = [
        {
            "id": "fluentbit_assets",
            "label": "Generate Fluent Bit assets",
            "description": "Generate catalog artifacts.",
            "script_path": "/tmp/generate_fluentbit_assets.py",
            "arguments": [
                {
                    "name": "versions",
                    "flag": "--version",
                    "prompt": "Version",
                    "required": True,
                    "multiple": True,
                    "default": "5.0.7",
                },
                {
                    "name": "generate_schemas",
                    "prompt": "Generate schemas",
                    "kind": "bool",
                    "default": True,
                    "args_when_false": ["--no-schemas"],
                },
            ],
        }
    ]

    prompts = iter(["1", "5.0.7,5.0.8", "n"])
    captured: dict[str, list[str]] = {"argv": []}

    def fake_reader(_prompt: str) -> str:
        return next(prompts)

    def fake_run(argv: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
        captured["argv"] = list(argv)
        return subprocess.CompletedProcess(args=argv, returncode=0)

    monkeypatch.setattr(dev_commands.subprocess, "run", fake_run)

    code = dev_commands.execute_dev_tool_workflow(
        command_name="dev-flb-config",
        tool_family_label="Fluent Bit",
        specs=specs,
        dev_features_enabled=True,
        prompt_text=fake_reader,
        parse_yes_no=lambda value, default: cli_main._parse_yes_no(value, default=default),  # type: ignore[attr-defined]
        command_text_from_args=cli_main._command_text_from_args,  # type: ignore[attr-defined]
        repo_root=Path.cwd(),
        build_exec_env=cli_main._build_exec_env,  # type: ignore[attr-defined]
        logger=cli_main._get_logger(),  # type: ignore[attr-defined]
    )

    assert code == 0
    assert captured["argv"] == [
        cli_main.sys.executable,
        str(Path("/tmp/generate_fluentbit_assets.py").resolve()),
        "--version",
        "5.0.7",
        "--version",
        "5.0.8",
        "--no-schemas",
    ]


def test_execute_dev_mcp_config_workflow_prompts_and_runs_selected_tool(monkeypatch) -> None:
    specs = [
        {
            "id": "mcp_client_config",
            "label": "Configure MCP clients",
            "description": "Update MCP client settings.",
            "script_path": "/tmp/configure_mcp_clients.py",
            "fixed_args": ["--yes"],
            "arguments": [
                {
                    "name": "clients",
                    "flag": "--clients",
                    "prompt": "Enabled clients",
                    "required": True,
                    "default": "claude,codex,vscode",
                },
                {
                    "name": "server_host",
                    "flag": "--server-host",
                    "prompt": "Server host",
                    "default": "localhost",
                },
                {
                    "name": "preview",
                    "prompt": "Preview only",
                    "kind": "bool",
                    "default": False,
                    "args_when_true": ["--preview"],
                },
            ],
        }
    ]

    prompts = iter(["1", "claude,codex", "broker.local", "y"])
    captured: dict[str, list[str]] = {"argv": []}

    def fake_reader(_prompt: str) -> str:
        return next(prompts)

    def fake_run(argv: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
        captured["argv"] = list(argv)
        return subprocess.CompletedProcess(args=argv, returncode=0)

    monkeypatch.setattr(dev_commands.subprocess, "run", fake_run)

    code = dev_commands.execute_dev_tool_workflow(
        command_name="dev-mcp-config",
        tool_family_label="MCP",
        specs=specs,
        dev_features_enabled=True,
        prompt_text=fake_reader,
        parse_yes_no=lambda value, default: cli_main._parse_yes_no(value, default=default),  # type: ignore[attr-defined]
        command_text_from_args=cli_main._command_text_from_args,  # type: ignore[attr-defined]
        repo_root=Path.cwd(),
        build_exec_env=cli_main._build_exec_env,  # type: ignore[attr-defined]
        logger=cli_main._get_logger(),  # type: ignore[attr-defined]
    )

    assert code == 0
    assert captured["argv"] == [
        cli_main.sys.executable,
        str(Path("/tmp/configure_mcp_clients.py").resolve()),
        "--yes",
        "--clients",
        "claude,codex",
        "--server-host",
        "broker.local",
        "--preview",
    ]


def _write_version_bump_fixture(repo_root: Path) -> Path:
    """Create a small version target fixture under a temporary repo root."""
    (repo_root / "cli").mkdir(parents=True)
    (repo_root / "component").mkdir()
    (repo_root / "cli" / "pyproject.toml").write_text(
        '[project]\nname = "opamp-cli"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )
    (repo_root / "component" / "pyproject.toml").write_text(
        '[project]\nname = "component"\nversion = "0.9.0"\n',
        encoding="utf-8",
    )
    (repo_root / "component" / "package-lock.json").write_text(
        '{\n'
        '  "name": "component",\n'
        '  "version": "0.9.0",\n'
        '  "packages": {\n'
        '    "": {"version": "0.9.0"},\n'
        '    "node_modules/example": {"version": "3.4.5"}\n'
        '  }\n'
        '}\n',
        encoding="utf-8",
    )
    config_path = repo_root / "version-targets.json"
    config_path.write_text(
        json.dumps(
            {
                "components": [
                    {
                        "id": "cli",
                        "currentVersionSource": {
                            "path": "cli/pyproject.toml",
                            "pattern": '^version = "([^"]+)"$',
                        },
                        "targets": [
                            {
                                "path": "cli/pyproject.toml",
                                "pattern": '^version = "[^"]+"$',
                                "replacement": 'version = "{version}"',
                            },
                        ],
                    },
                    {
                        "id": "component",
                        "currentVersionSource": {
                            "path": "component/pyproject.toml",
                            "pattern": '^version = "([^"]+)"$',
                        },
                        "targets": [
                            {
                                "path": "component/pyproject.toml",
                                "pattern": '^version = "[^"]+"$',
                                "replacement": 'version = "{version}"',
                            },
                            {
                                "path": "component/package-lock.json",
                                "pattern": '"version": "[^"]+"',
                                "replacement": '"version": "{version}"',
                                "count": 2,
                            },
                        ],
                    },
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return config_path


def test_default_version_targets_config_matches_repo() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    config_path = repo_root / "cli" / "config" / "version_targets.json"

    config = version_bump._read_dev_version_config(config_path)  # type: ignore[attr-defined]
    components = version_bump._version_config_components(config)  # type: ignore[attr-defined]

    assert len(components) > 1
    for component in components:
        current_version = version_bump._read_version_from_config_source(  # type: ignore[attr-defined]
            repo_root,
            component["currentVersionSource"],
        )
        assert re.fullmatch(r"\d+\.\d+\.\d+", current_version)
        for target in component["targets"]:
            target_path = version_bump._resolve_repo_path(  # type: ignore[attr-defined]
                repo_root,
                target["path"],
            )
            if version_bump._version_target_optional(target) and not target_path.exists():  # type: ignore[attr-defined]
                continue
            assert target_path.exists(), f"missing version target: {target['path']}"
            target_text = target_path.read_text(encoding="utf-8")
            assert re.search(
                target["pattern"],
                target_text,
                flags=re.MULTILINE,
            ), f"version pattern did not match: {target['path']}"


def test_dev_version_bump_requires_developer_features(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_main, "_dev_features_enabled", lambda: False)

    code = version_bump.execute_dev_version_bump_workflow(
        [],
        repo_root_provider=cli_main._repo_root,  # type: ignore[attr-defined]
        dev_features_enabled=cli_main._dev_features_enabled,  # type: ignore[attr-defined]
    )
    captured = capsys.readouterr()

    assert code == 1
    assert "dev-version-bump is only available when APP_ENABLE_DEV_FEATURES=true" in captured.err


def test_dev_version_bump_defaults_to_next_minor_version(
    tmp_path: Path,
    capsys,
) -> None:
    repo_root = tmp_path / "repo"
    config_path = _write_version_bump_fixture(repo_root)
    code = version_bump.execute_dev_version_bump_workflow(
        ["--config", str(config_path)],
        repo_root_provider=lambda: repo_root,
        dev_features_enabled=lambda: True,
    )
    output = capsys.readouterr().out

    assert code == 0
    assert "cli: 1.2.3 -> 1.3.0" in output
    assert "component: 0.9.0 -> 0.10.0" in output
    assert 'version = "1.3.0"' in (repo_root / "cli" / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.10.0"' in (repo_root / "component" / "pyproject.toml").read_text(encoding="utf-8")
    package_lock_text = (repo_root / "component" / "package-lock.json").read_text(encoding="utf-8")
    assert '"version": "0.10.0"' in package_lock_text
    assert '"version": "3.4.5"' in package_lock_text


def test_dev_version_bump_skips_optional_missing_target(
    tmp_path: Path,
    capsys,
) -> None:
    repo_root = tmp_path / "repo"
    config_path = _write_version_bump_fixture(repo_root)
    (repo_root / "component" / "package-lock.json").unlink()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["components"][1]["targets"][1]["optional"] = True
    config_path.write_text(json.dumps(config), encoding="utf-8")
    code = version_bump.execute_dev_version_bump_workflow(
        ["--config", str(config_path)],
        repo_root_provider=lambda: repo_root,
        dev_features_enabled=lambda: True,
    )
    output = capsys.readouterr().out

    assert code == 0
    assert "Skipped optional missing target" in output
    assert "Optional missing targets skipped: 1" in output
    assert 'version = "1.3.0"' in (repo_root / "cli" / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.10.0"' in (repo_root / "component" / "pyproject.toml").read_text(encoding="utf-8")


def test_dev_version_bump_missing_required_target_aborts_before_writes(
    tmp_path: Path,
    capsys,
) -> None:
    repo_root = tmp_path / "repo"
    config_path = _write_version_bump_fixture(repo_root)
    (repo_root / "component" / "package-lock.json").unlink()
    code = version_bump.execute_dev_version_bump_workflow(
        ["--config", str(config_path)],
        repo_root_provider=lambda: repo_root,
        dev_features_enabled=lambda: True,
    )
    captured = capsys.readouterr()

    assert code == 1
    assert "version target not found:" in captured.err
    assert 'version = "1.2.3"' in (repo_root / "cli" / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.9.0"' in (repo_root / "component" / "pyproject.toml").read_text(encoding="utf-8")


def test_dev_version_bump_accepts_explicit_greater_version(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    config_path = _write_version_bump_fixture(repo_root)
    code = version_bump.execute_dev_version_bump_workflow(
        ["2.0.0", "--config", str(config_path)],
        repo_root_provider=lambda: repo_root,
        dev_features_enabled=lambda: True,
    )

    assert code == 0
    assert 'version = "2.0.0"' in (repo_root / "cli" / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "2.0.0"' in (repo_root / "component" / "pyproject.toml").read_text(encoding="utf-8")


def test_dev_version_bump_rejects_non_greater_explicit_version(
    tmp_path: Path,
    capsys,
) -> None:
    repo_root = tmp_path / "repo"
    config_path = _write_version_bump_fixture(repo_root)
    code = version_bump.execute_dev_version_bump_workflow(
        ["1.2.3", "--config", str(config_path)],
        repo_root_provider=lambda: repo_root,
        dev_features_enabled=lambda: True,
    )
    captured = capsys.readouterr()

    assert code == 1
    assert "for cli must be greater than current version 1.2.3" in captured.err
    assert 'version = "1.2.3"' in (repo_root / "cli" / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.9.0"' in (repo_root / "component" / "pyproject.toml").read_text(encoding="utf-8")


def test_dev_version_bump_rejects_invalid_semantic_version(
    tmp_path: Path,
    capsys,
) -> None:
    repo_root = tmp_path / "repo"
    config_path = _write_version_bump_fixture(repo_root)
    code = version_bump.execute_dev_version_bump_workflow(
        ["1.3", "--config", str(config_path)],
        repo_root_provider=lambda: repo_root,
        dev_features_enabled=lambda: True,
    )
    captured = capsys.readouterr()

    assert code == 1
    assert "new version must use MAJOR.MINOR.PATCH format" in captured.err


def test_handle_command_routes_dev_version_bump_to_workflow(monkeypatch) -> None:
    called: dict[str, list[str]] = {"args": []}

    def fake_workflow(args, **_kwargs):  # type: ignore[no-untyped-def]
        called["args"] = list(args)
        return 0

    monkeypatch.setattr(cli_main, "execute_dev_version_bump_workflow", fake_workflow)

    code = cli_main._handle_command("dev-version-bump 1.4.0 --config custom.json")  # type: ignore[attr-defined]

    assert code == 0
    assert called["args"] == ["1.4.0", "--config", "custom.json"]


def test_top_level_commands_include_dev_version_bump_only_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr(cli_main, "_demo_mode_enabled", lambda: False)
    monkeypatch.setattr(cli_main, "_fluentbit_dev_tool_available", lambda: False)
    monkeypatch.setattr(cli_main, "_mcp_dev_tool_available", lambda: False)
    monkeypatch.setattr(cli_main, "_dev_pid_lookup_available", lambda: False)
    monkeypatch.setattr(container_management, "container_runtime_executable", lambda: None)
    monkeypatch.setattr(cli_main, "_dev_version_bump_available", lambda: True)

    commands = cli_main._top_level_commands()  # type: ignore[attr-defined]

    assert "dev-version-bump" in commands

    monkeypatch.setattr(cli_main, "_dev_version_bump_available", lambda: False)
    commands = cli_main._top_level_commands()  # type: ignore[attr-defined]
    assert "dev-version-bump" not in commands


def test_config_subcommand_prefix_detects_second_level_keyword() -> None:
    assert cli_main._config_subcommand_prefix("config ") == ""  # type: ignore[attr-defined]
    assert cli_main._config_subcommand_prefix("config val") == "val"  # type: ignore[attr-defined]
    assert cli_main._config_subcommand_prefix("config validate ./cfg.yaml") is None  # type: ignore[attr-defined]


def test_completion_candidates_keep_config_base_separate_from_subcommand() -> None:
    base, prefix, matches = cli_main._completion_candidates(  # type: ignore[attr-defined]
        "config va",
        entries=["config", "status"],
    )

    assert base == "config "
    assert prefix == "va"
    assert matches == ["validate"]


def test_prompt_toolkit_reader_offers_config_subcommands_and_paths(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _FakeCompletion:
        def __init__(self, text: str, start_position: int = 0) -> None:
            self.text = text
            self.start_position = start_position

    class _FakePathCompleter:
        def __init__(self, *, expanduser: bool) -> None:
            self.expanduser = expanduser

        def get_completions(self, document, complete_event):  # type: ignore[no-untyped-def]
            captured["path_document"] = document.text_before_cursor
            return [_FakeCompletion("./config.yaml")]

    def fake_prompt(prompt_text: str, *, completer, complete_while_typing: bool):  # type: ignore[no-untyped-def]
        captured["prompt_text"] = prompt_text
        captured["completer"] = completer
        captured["complete_while_typing"] = complete_while_typing
        return ""

    def fake_import_module(name: str):  # type: ignore[no-untyped-def]
        if name == "prompt_toolkit":
            return SimpleNamespace(prompt=fake_prompt)
        if name == "prompt_toolkit.completion":
            return SimpleNamespace(
                Completer=object,
                Completion=_FakeCompletion,
                PathCompleter=_FakePathCompleter,
            )
        raise ImportError(name)

    monkeypatch.setattr(cli_main.importlib, "import_module", fake_import_module)
    monkeypatch.setattr(cli_main.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli_main.sys.stdout, "isatty", lambda: True)

    reader = cli_main._prompt_toolkit_input_reader(["config"])  # type: ignore[attr-defined]

    assert reader is not None

    reader("opamp> ")
    completer = captured["completer"]

    completions = list(
        completer.get_completions(  # type: ignore[union-attr]
            SimpleNamespace(text_before_cursor="config "),
            None,
        )
    )
    assert [item.text for item in completions] == ["validate", "metadata"]

    path_completions = list(
        completer.get_completions(  # type: ignore[union-attr]
            SimpleNamespace(text_before_cursor="config validate "),
            None,
        )
    )
    assert [item.text for item in path_completions] == ["./config.yaml"]
    assert captured["path_document"] == "config validate "


def test_execute_dev_pid_lookup_workflow_reports_matches(monkeypatch, capsys) -> None:
    code = dev_commands.execute_dev_pid_lookup_workflow(
        command_name="dev-pid-lookup",
        dev_features_enabled=True,
        prompt_text=lambda _prompt: "consumer_sim_launcher",
        running_process_entries=lambda: (
            True,
            [
                {
                    "pid": 4321,
                    "name": "python",
                    "command_line": "python consumer-sim/src/consumer_sim_launcher.py start",
                },
                {
                    "pid": 1234,
                    "name": "fluent-bit",
                    "command_line": "fluent-bit -c fluent-bit.yaml",
                },
            ],
        ),
        process_entries_matching_pattern=lambda processes, pattern: cli_main._process_entries_matching_pattern(  # type: ignore[attr-defined]
            processes,
            pattern=pattern,
        ),
        print_pid_lookup_results=cli_main._print_pid_lookup_results,  # type: ignore[attr-defined]
    )
    output = capsys.readouterr().out

    assert code == 0
    assert "Regex: consumer_sim_launcher" in output
    assert "Matched 1 process(es):" in output
    assert "python" in output
    assert "pid: 4321" in output


def test_execute_dev_pid_lookup_workflow_reports_no_matches(monkeypatch, capsys) -> None:
    code = dev_commands.execute_dev_pid_lookup_workflow(
        command_name="dev-pid-lookup",
        dev_features_enabled=True,
        prompt_text=lambda _prompt: "fluentd",
        running_process_entries=lambda: (
            True,
            [
                {
                    "pid": 4321,
                    "name": "python",
                    "command_line": "python provider/server.py",
                }
            ],
        ),
        process_entries_matching_pattern=lambda processes, pattern: cli_main._process_entries_matching_pattern(  # type: ignore[attr-defined]
            processes,
            pattern=pattern,
        ),
        print_pid_lookup_results=cli_main._print_pid_lookup_results,  # type: ignore[attr-defined]
    )
    output = capsys.readouterr().out

    assert code == 1
    assert "No running processes matched the regular expression." in output
