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

import json
import pathlib
import sys
from types import SimpleNamespace

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
CONSUMER_SIM_SRC = REPO_ROOT / "consumer-sim" / "src"
if str(CONSUMER_SIM_SRC) not in sys.path:
    sys.path.insert(0, str(CONSUMER_SIM_SRC))

import consumer_sim_launcher as launcher  # noqa: E402 - import requires runtime sys.path injection above


def test_build_instance_command_with_entrypoint_and_overrides(tmp_path: pathlib.Path) -> None:
    """Verify entrypoint-based command builds expected CLI args and normalized flags."""
    config_dir = tmp_path
    consumer_config = config_dir / "configs" / "consumer.json"
    consumer_config.parent.mkdir(parents=True)
    consumer_config.write_text("{}", encoding="utf-8")

    instance = {
        "name": "alpha",
        "entrypoint": "simulator",
        "config_path": "configs/consumer.json",
        "agent_config_path": "configs/fluent-bit.yaml",
        "overrides": {
            "server_url": "http://localhost:8080",
            "heartbeat-frequency": 42,
            "agent-additional-params": ["--dry-run", "--verbose"],
            "diagnostic": True,
        },
    }

    name, command, working_dir = launcher._build_instance_command(
        instance,
        base_dir=config_dir,
    )

    assert name == "alpha"
    assert command[:3] == [sys.executable, "-m", "opamp_consumer.simulator.client"]
    assert "--config-path" in command
    assert str(consumer_config.resolve()) in command
    assert "--agent-config-path" in command
    assert str((config_dir / "configs" / "fluent-bit.yaml").resolve()) in command
    assert "--server-url" in command
    assert "http://localhost:8080" in command
    assert "--heartbeat-frequency" in command
    assert "42" in command
    assert "--agent-additional-params" in command
    assert "--dry-run" in command
    assert "--verbose" in command
    assert "--diagnostic" in command
    assert working_dir == REPO_ROOT


def test_state_file_path_uses_payload_override(tmp_path: pathlib.Path) -> None:
    """Verify relative state_file path is resolved from config file parent directory."""
    config_path = tmp_path / "launch.json"
    payload = {"state_file": "runtime/pids.json"}
    resolved = launcher._state_file_path(config_path, payload)
    assert resolved == (tmp_path / "runtime" / "pids.json").resolve()


def test_validate_payload_against_schema_accepts_valid_payload(
    tmp_path: pathlib.Path,
) -> None:
    """Schema validator should accept a minimally valid launcher payload."""
    payload = {
        "instances": [
            {
                "name": "sim-01",
                "entrypoint": "simulator",
                "config_path": "configs/consumer.json",
            }
        ]
    }
    launcher._validate_payload_against_schema(
        payload,
        config_path=tmp_path / "launch.json",
    )


def test_start_instances_fails_fast_on_schema_violation(
    tmp_path: pathlib.Path,
    monkeypatch,
) -> None:
    """Start must fail with a strong, explicit schema-validation message."""
    config_path = tmp_path / "launch.json"
    config_path.write_text(
        json.dumps(
            {
                "instances": [
                    {
                        "name": "sim-01",
                        "entrypoint": "simulator",
                        "bad_key": "unexpected",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv(launcher.ENV_APP_ENABLE_DEV_FEATURES, "true")

    with pytest.raises(RuntimeError, match="FATAL CONFIG SCHEMA VALIDATION FAILED") as exc_info:
        launcher._start_instances(config_path)

    error_text = str(exc_info.value)
    assert "config-file=" in error_text
    assert "schema-file=" in error_text
    assert "Validation issues:" in error_text


def test_start_instances_requires_development_features_before_loading_config(
    tmp_path: pathlib.Path,
    monkeypatch,
) -> None:
    """Startup must stop before reading configuration when development features are disabled."""
    config_path = tmp_path / "launch.json"
    monkeypatch.delenv(launcher.ENV_APP_ENABLE_DEV_FEATURES, raising=False)
    monkeypatch.setattr(
        launcher,
        "_load_launcher_payload",
        lambda _config_path: pytest.fail("configuration must not be loaded"),
    )

    with pytest.raises(RuntimeError, match="APP_ENABLE_DEV_FEATURES=true"):
        launcher._start_instances(config_path)


def test_build_process_environment_sets_process_record_context() -> None:
    """Launcher should inject process-record file/name for simulator status polling."""
    env = launcher._build_process_environment(
        {"env": {"A": "B"}},
        repo_root=REPO_ROOT,
        process_record_file=REPO_ROOT / "consumer-sim" / "runtime" / "launcher_state.json",
        instance_name="sim-01",
    )

    assert env[launcher.ENV_SIM_PROCESS_RECORD_NAME] == "sim-01"
    assert env[launcher.ENV_SIM_PROCESS_RECORD_FILE].endswith("launcher_state.json")


def test_clear_stale_shutdown_semaphore_removes_file(tmp_path: pathlib.Path) -> None:
    """Launcher should remove stale OpAMPSupervisor.signal before start."""
    semaphore_file = tmp_path / launcher.SEMAPHORE_FILENAME
    semaphore_file.write_text("", encoding="utf-8")

    launcher._clear_stale_shutdown_semaphore(working_dir=tmp_path)

    assert semaphore_file.exists() is False


def test_is_process_running_uses_tasklist_on_windows(monkeypatch) -> None:
    """Windows PID checks should use tasklist instead of os.kill."""
    called = {"kill": 0}

    def fake_kill(_pid: int, _signal: int) -> None:
        called["kill"] += 1
        raise OSError(87, "The parameter is incorrect")

    def fake_run(*_args, **_kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout='"python.exe","4321","Console","1","12,000 K"\n',
        )

    monkeypatch.setattr(launcher, "_is_windows", lambda: True)
    monkeypatch.setattr(launcher.os, "kill", fake_kill)
    monkeypatch.setattr(launcher.subprocess, "run", fake_run)

    assert launcher._is_process_running(4321) is True
    assert called["kill"] == 0


def test_normalize_custom_command_string() -> None:
    """Verify custom command strings are shell-split into argv tokens."""
    assert launcher._normalize_command("python -m opamp_consumer.fluentd.client") == [
        "python",
        "-m",
        "opamp_consumer.fluentd.client",
    ]


def test_build_entrypoint_command_supports_simulator() -> None:
    """Verify simulator entrypoint builds python module command."""
    command = launcher._build_entrypoint_command("simulator")
    assert command == [sys.executable, "-m", "opamp_consumer.simulator.client"]


def test_build_parser_includes_component_version(monkeypatch) -> None:
    """CLI parser should surface component version in description and --version flag."""
    monkeypatch.setattr(launcher, "component_version_text", lambda: "test-version")
    parser = launcher._build_parser()
    assert "test-version" in str(parser.description)
    assert any("--version" in action.option_strings for action in parser._actions)


def test_build_entrypoint_command_rejects_non_simulator() -> None:
    """Verify non-simulator entrypoints are rejected."""
    with pytest.raises(ValueError, match="supports 'simulator' only"):
        launcher._build_entrypoint_command("fluentbit")


def test_build_instance_command_rejects_non_simulator_custom_command(
    tmp_path: pathlib.Path,
) -> None:
    """Verify custom commands must still target the simulator client."""
    config_dir = tmp_path
    consumer_config = config_dir / "configs" / "consumer.json"
    consumer_config.parent.mkdir(parents=True)
    consumer_config.write_text("{}", encoding="utf-8")
    instance = {
        "name": "alpha",
        "command": "python -m opamp_consumer.fluentd.client",
        "config_path": "configs/consumer.json",
    }

    with pytest.raises(ValueError, match="must launch the simulator client"):
        launcher._build_instance_command(
            instance,
            base_dir=config_dir,
        )


def test_start_instances_clears_stale_semaphore_in_working_dir(
    tmp_path: pathlib.Path,
    monkeypatch,
) -> None:
    """Start should clear stale semaphore files before launching simulator instances."""
    config_path = tmp_path / "launch.json"
    consumer_config = tmp_path / "configs" / "consumer.json"
    consumer_config.parent.mkdir(parents=True)
    consumer_config.write_text("{}", encoding="utf-8")
    working_dir = tmp_path / "work"
    working_dir.mkdir(parents=True, exist_ok=True)
    semaphore_file = working_dir / launcher.SEMAPHORE_FILENAME
    semaphore_file.write_text("", encoding="utf-8")
    config_path.write_text(
        json.dumps(
            {
                "state_file": "runtime/state.json",
                "instances": [
                    {
                        "name": "sim-start-01",
                        "entrypoint": "simulator",
                        "config_path": "configs/consumer.json",
                        "working_dir": "work",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(launcher.ENV_APP_ENABLE_DEV_FEATURES, "true")

    class _FakeProcess:
        pid = 43210

    monkeypatch.setattr(launcher, "_is_process_running", lambda _pid: False)
    monkeypatch.setattr(
        launcher.subprocess,
        "Popen",
        lambda *_args, **_kwargs: _FakeProcess(),
    )

    launcher._start_instances(config_path)

    assert semaphore_file.exists() is False
    state_path = (tmp_path / "runtime" / "state.json").resolve()
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["instances"][0]["name"] == "sim-start-01"
    assert payload["instances"][0]["status"] == launcher.STATUS_RUNNING


def test_stop_single_instance_waits_90_seconds_before_force(monkeypatch) -> None:
    """Stop flow should wait 90s for graceful exit before brute force."""
    waits: list[float] = []
    force_calls = {"count": 0}
    monotonic_values = iter([0.0, 89.0, 90.1])

    monkeypatch.setattr(launcher, "_is_process_running", lambda _pid: True)
    monkeypatch.setattr(launcher.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(launcher.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        launcher,
        "_wait_for_exit",
        lambda _pid, timeout: waits.append(timeout) or True,
    )
    monkeypatch.setattr(
        launcher,
        "_send_forceful_stop",
        lambda _pid, _pgid: force_calls.__setitem__("count", force_calls["count"] + 1),
    )

    stopped = launcher._stop_single_instance(
        {
            "name": "sim-a",
            "pid": 1001,
        }
    )

    assert stopped is True
    assert waits == [launcher.TERMINATE_WAIT_SECONDS]
    assert force_calls["count"] == 1


def test_stop_single_instance_graceful_exit_avoids_force(monkeypatch) -> None:
    """If process exits within grace period, force stop should not be used."""
    force_calls = {"count": 0}
    running_checks = iter([True, False])
    monotonic_values = iter([0.0, 1.0])

    monkeypatch.setattr(launcher, "_is_process_running", lambda _pid: next(running_checks))
    monkeypatch.setattr(launcher.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(
        launcher,
        "_send_forceful_stop",
        lambda _pid, _pgid: force_calls.__setitem__("count", force_calls["count"] + 1),
    )

    stopped = launcher._stop_single_instance(
        {
            "name": "sim-b",
            "pid": 1002,
        }
    )

    assert stopped is True
    assert force_calls["count"] == 0


def test_stop_single_instance_logs_shuttingdown_and_exit_markers(
    tmp_path: pathlib.Path,
    monkeypatch,
    capsys,
) -> None:
    """State transition to shuttingdown and process disappearance should be emphasized."""
    state_file = tmp_path / "state.json"
    state_file.write_text(
        json.dumps(
            {
                "instances": [
                    {"name": "sim-c", "pid": 1003, "status": launcher.STATUS_SHUTTING_DOWN}
                ]
            }
        ),
        encoding="utf-8",
    )
    running_checks = iter([True, True, False])
    monotonic_values = iter([0.0, 1.0, 2.0])
    monkeypatch.setattr(launcher, "_is_process_running", lambda _pid: next(running_checks))
    monkeypatch.setattr(launcher.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(launcher.time, "sleep", lambda _seconds: None)

    stopped = launcher._stop_single_instance(
        {
            "name": "sim-c",
            "pid": 1003,
        },
        state_file=state_file,
    )

    out = capsys.readouterr().out
    assert stopped is True
    assert "----- [consumer-sim] simulator state changed to shuttingdown name=sim-c pid=1003 -----" in out
    assert "====== [consumer-sim] process no longer detected name=sim-c pid=1003 ======" in out


def test_stop_instances_removes_stopped_records_and_keeps_failed(
    tmp_path: pathlib.Path,
    monkeypatch,
) -> None:
    """Stop should prune successful records from state file and keep failures."""
    config_path = tmp_path / "launch.json"
    config_path.write_text(json.dumps({"state_file": "state.json"}), encoding="utf-8")
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "launched_at": "2026-04-19T00:00:00Z",
                "instances": [
                    {"name": "sim-ok", "pid": 2001},
                    {"name": "sim-fail", "pid": 2002},
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        launcher,
        "_stop_single_instance",
        lambda instance, **_kwargs: str(instance.get("name")) == "sim-ok",
    )

    launcher._stop_instances(config_path)

    assert state_path.exists() is True
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert isinstance(payload.get("instances"), list)
    assert payload["instances"] == [
        {"name": "sim-fail", "pid": 2002, "status": launcher.STATUS_SHUTDOWN}
    ]


def test_stop_instances_removes_state_file_when_all_stopped(
    tmp_path: pathlib.Path,
    monkeypatch,
) -> None:
    """Stop should delete state file when all records stop successfully."""
    config_path = tmp_path / "launch.json"
    config_path.write_text(json.dumps({"state_file": "state.json"}), encoding="utf-8")
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "launched_at": "2026-04-19T00:00:00Z",
                "instances": [
                    {"name": "sim-a", "pid": 3001},
                    {"name": "sim-b", "pid": 3002},
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(launcher, "_stop_single_instance", lambda _instance, **_kwargs: True)

    launcher._stop_instances(config_path)

    assert state_path.exists() is False


def test_is_process_running_handles_windows_bad_format_oserror(monkeypatch) -> None:
    """Windows tasklist failures should be treated as not running."""

    monkeypatch.setattr(launcher, "_is_windows", lambda: True)
    monkeypatch.setattr(
        launcher.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("bad format")),
    )

    assert launcher._is_process_running(12345) is False
