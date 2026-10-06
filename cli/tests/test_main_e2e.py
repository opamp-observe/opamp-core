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

"""CLI end-to-end test coverage.

Test-case reference: cli/docs/TEST_CASES.md
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _cli_entrypoint() -> Path:
    return (_repo_root() / "cli" / "main.py").resolve()


def _run_cli(
    *args: str,
    cwd: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, str(_cli_entrypoint()), *args],
        cwd=str(cwd or _repo_root()),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


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


def test_help_command_prints_usage() -> None:
    completed = _run_cli("--help")

    assert completed.returncode == 0
    assert "Usage:" in completed.stdout
    assert "opamp-cli start server" in completed.stdout
    assert "opamp-cli setup-venv" in completed.stdout
    assert "opamp-cli cli-config summary" in completed.stdout
    assert "opamp-cli dev-containers" in completed.stdout
    assert "opamp-cli dev-version-bump" in completed.stdout


def test_status_command_reports_runtime_paths() -> None:
    completed = _run_cli("status")

    assert completed.returncode == 0
    assert "OpAMP config file:" in completed.stdout
    assert "OpAMP config loaded:" in completed.stdout
    assert "CLI config file:" in completed.stdout
    assert "State file:" in completed.stdout
    assert "Log directory:" in completed.stdout
    assert "CLI log file:" in completed.stdout


def test_list_command_reports_option_hierarchy() -> None:
    completed = _run_cli("list")

    assert completed.returncode == 0
    assert "Control flags:" in completed.stdout
    assert "Top-level commands:" in completed.stdout
    assert "Config commands:" in completed.stdout
    assert "CLI config commands:" in completed.stdout
    assert "  cli-config:" in completed.stdout
    assert "    - view" in completed.stdout
    assert "    - summary" in completed.stdout
    assert "    - change-config" in completed.stdout
    assert "  config:" in completed.stdout
    assert "    - validate <path>" in completed.stdout
    assert "    - metadata <path>" in completed.stdout
    assert "Guided actions:" in completed.stdout


def test_cli_config_summary_e2e_reports_default_config() -> None:
    completed = _run_cli("cli-config", "summary")

    assert completed.returncode == 0
    assert "CLI config summary:" in completed.stdout
    assert "- Demo configs:" in completed.stdout
    assert "- CLI config file:" in completed.stdout


def test_dev_version_bump_is_recognized_as_dev_command() -> None:
    completed = _run_cli("dev-version-bump", "9.9.9", "--config", "missing.json")

    assert completed.returncode == 1
    assert "dev-version-bump is only available when APP_ENABLE_DEV_FEATURES=true" in completed.stderr


def test_list_command_reports_dev_version_bump_when_developer_features_enabled() -> None:
    completed = _run_cli("list", extra_env={"APP_ENABLE_DEV_FEATURES": "true"})

    assert completed.returncode == 0
    assert "  - dev-version-bump" in completed.stdout


def test_direct_execution_runs_python_command() -> None:
    completed = _run_cli(sys.executable, "-c", "print('cli-e2e-ok')")

    assert completed.returncode == 0
    assert "cli-e2e-ok" in completed.stdout


def test_script_generation_writes_os_native_script(tmp_path: Path) -> None:
    completed = _run_cli("script", "demo-start", "echo", "hello", cwd=tmp_path)

    expected = tmp_path / "scripts" / f"demo-start{'.cmd' if os.name == 'nt' else '.sh'}"
    assert completed.returncode == 0
    assert expected.exists()
    assert "Generated script:" in completed.stdout
    assert "echo hello" in expected.read_text(encoding="utf-8")


def test_unknown_guided_target_returns_error() -> None:
    completed = _run_cli("start", "does-not-exist")

    assert completed.returncode == 1
    assert "Unknown start target" in completed.stderr


def test_unknown_restart_target_returns_error() -> None:
    completed = _run_cli("restart", "does-not-exist")

    assert completed.returncode == 1
    assert "Unknown restart target" in completed.stderr


def test_config_validate_single_file_e2e(tmp_path: Path) -> None:
    config_path = tmp_path / "single.yaml"
    config_path.write_text(_sample_fluentbit_config(), encoding="utf-8")

    completed = _run_cli("config", "validate", str(config_path))
    report_path = _report_path_from_output(completed.stdout)

    assert completed.returncode == 0
    assert "Validation result: no error" in completed.stdout
    assert report_path.exists()
    assert f"File: {config_path.resolve()}" in report_path.read_text(encoding="utf-8")


def test_config_validate_directory_e2e(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    first = config_dir / "first.yaml"
    second = config_dir / "second.yaml"
    first.write_text(_sample_fluentbit_config(), encoding="utf-8")
    second.write_text(_sample_fluentbit_config(), encoding="utf-8")

    completed = _run_cli("config", "validate", str(config_dir))
    report_path = _report_path_from_output(completed.stdout)
    report_text = report_path.read_text(encoding="utf-8")

    assert completed.returncode == 0
    assert f"File: {first.resolve()}" in report_text
    assert f"File: {second.resolve()}" in report_text


def test_config_validate_directory_e2e_returns_error_when_any_file_is_invalid(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    valid_path = config_dir / "valid.yaml"
    invalid_path = config_dir / "invalid.yaml"
    valid_path.write_text(_sample_fluentbit_config(), encoding="utf-8")
    invalid_path.write_text(_invalid_fluentbit_config_missing_required_tag(), encoding="utf-8")

    completed = _run_cli("config", "validate", str(config_dir))
    report_path = _report_path_from_output(completed.stdout)
    report_text = report_path.read_text(encoding="utf-8")

    assert completed.returncode == 1
    assert f"File: {valid_path.resolve()}" in report_text
    assert f"File: {invalid_path.resolve()}" in report_text
    assert "Validation result: issues found" in report_text


def test_config_metadata_directory_e2e_preserves_existing_header(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    missing = config_dir / "missing.yaml"
    existing = config_dir / "existing.yaml"
    missing.write_text(_sample_fluentbit_config(), encoding="utf-8")
    original_existing = (
        "# config-service: config_type=fluentbit\n"
        "# config-service: version=4.2.4\n"
        + _sample_fluentbit_config()
    )
    existing.write_text(original_existing, encoding="utf-8")

    completed = _run_cli("config", "metadata", str(config_dir))
    report_path = _report_path_from_output(completed.stdout)
    report_text = report_path.read_text(encoding="utf-8")

    assert completed.returncode == 0
    assert missing.read_text(encoding="utf-8").startswith(
        "# config-service: config_type=fluentbit\n"
        "# config-service: version=5.0.4\n"
    )
    assert existing.read_text(encoding="utf-8") == original_existing
    assert f"File: {missing.resolve()}" in report_text
    assert f"File: {existing.resolve()}" in report_text
