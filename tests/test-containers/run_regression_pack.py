#!/usr/bin/env python3
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
#
# Copyright 2026 mp3monster.org

"""Run containerized OpAMP regression tests and summarize outcomes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

COMMAND_KEY = "command"
COMMANDS_KEY = "commands"
COMMAND_TAIL_LIMIT = 4000
DESCRIPTION_KEY = "description"
DURATION_SECONDS_KEY = "duration_seconds"
EXIT_CODE_KEY = "exit_code"
EVIDENCE_TAIL_LIMIT = 12000
JSON_REPORT_FILE_NAME = "regression-pack-results.json"
MARKDOWN_REPORT_FILE_NAME = "regression-pack-results.md"
STDERR_KEY = "stderr"
STDOUT_KEY = "stdout"
TEST_ID_KEY = "test_id"

EVIDENCE_FILE_NAMES = (
    "results.md",
    "summary.json",
    "verify.log",
    "compose.log",
)


@dataclass(frozen=True)
class RegressionTest:
    """Container regression entry with the commands needed to exercise it."""

    test_id: str
    """Stable regression identifier used by --only and report rows."""

    description: str
    """Human-readable description of the behavior under test."""

    commands: tuple[tuple[str, ...], ...]
    """Ordered shell commands; the first non-zero command fails the test."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _bash_path(path: Path) -> str:
    """Return a path string that Windows-hosted Bash can open."""
    resolved = path.resolve()
    if os.name != "nt":
        return str(resolved)
    drive = resolved.drive.rstrip(":").lower()
    tail = resolved.as_posix().split(":", 1)[-1]
    if drive:
        return f"/{drive}{tail}"
    return resolved.as_posix()


def _bash_executable() -> str:
    """Return a Bash executable, preferring Git Bash on Windows."""
    configured = str(os.environ.get("OPAMP_BASH") or "").strip()
    candidates = [configured] if configured else []
    if os.name == "nt":
        candidates.extend(
            [
                r"C:\Program Files\Git\bin\bash.exe",
                r"C:\Program Files\Git\usr\bin\bash.exe",
                r"C:\Program Files (x86)\Git\bin\bash.exe",
                r"C:\Program Files (x86)\Git\usr\bin\bash.exe",
            ]
        )
    candidates.append("bash")
    for candidate in candidates:
        if not candidate:
            continue
        if Path(candidate).is_file() or candidate == "bash":
            return candidate
    return "bash"


def _ensure_regression_directories(repo_root: Path) -> None:
    """Create host directories that are mounted by regression containers."""
    for directory in (
        repo_root / "dist" / "consumer",
        repo_root / "dist" / "test-reports" / "component-wheel-deployment",
        repo_root / "dist" / "test-reports" / "opamp-consumer-deployment" / "fluentbit",
        repo_root / "dist" / "test-reports" / "opamp-consumer-deployment" / "fluentd",
        repo_root / "dist" / "test-reports" / "opamp-consumer-deployment" / "elastic-heartbeat",
        repo_root / "dist" / "test-reports" / "agent-shutdown-e2e",
        repo_root / "dist" / "test-reports" / "agent-shutdown-e2e" / "provider",
        repo_root / "dist" / "test-reports" / "vector-plugin-e2e",
        repo_root / "dist" / "test-reports" / "vector-plugin-e2e" / "consumer-vector",
        repo_root / "dist" / "test-reports" / "config-service-ui-playwright-batch",
        repo_root / "config-service" / "dist",
    ):
        directory.mkdir(parents=True, exist_ok=True)


def _default_tests(repo_root: Path) -> list[RegressionTest]:
    bash = _bash_executable()
    consumer_plugin_image = "opamp-consumer-plugin-startup-regression:latest"
    component_wheel_image = "opamp-component-wheel-deployment:latest"
    client_config_generator_deployment_image = (
        "opamp-client-config-generator-deployment:latest"
    )
    consumer_deployment_image = "opamp-consumer-deployment-test:latest"
    config_service_ui_image = "config-service-ui-playwright-batch:latest"
    return [
        RegressionTest(
            test_id="component-wheel-deployment",
            description=(
                "Builds every Python component wheel and installs each one into a clean "
                "virtual environment to validate deployment packaging."
            ),
            commands=(
                (
                    "docker",
                    "build",
                    "-f",
                    str(repo_root / "tests/test-containers/component-wheel-deployment/Dockerfile"),
                    "-t",
                    component_wheel_image,
                    str(repo_root / "tests/test-containers/component-wheel-deployment"),
                ),
                (
                    "docker",
                    "run",
                    "--rm",
                    "-e",
                    "OPAMP_REPO=/workspace/opamp",
                    "-e",
                    "RESULTS_DIR=/host-output",
                    "-v",
                    f"{repo_root}:/workspace/opamp",
                    "-v",
                    f"{repo_root / 'dist/test-reports/component-wheel-deployment'}:/host-output",
                    component_wheel_image,
                ),
            ),
        ),
        RegressionTest(
            test_id="client-config-generator-service-deployment",
            description=(
                "Verifies enabled provider deployment exposes the client config generator "
                "while a disabled component entry leaves its menu item and routes unavailable."
            ),
            commands=(
                (
                    "docker",
                    "build",
                    "-f",
                    str(
                        repo_root
                        / "tests/test-containers/client-config-generator-service-deployment/Dockerfile"
                    ),
                    "-t",
                    client_config_generator_deployment_image,
                    str(
                        repo_root
                        / "tests/test-containers/client-config-generator-service-deployment"
                    ),
                ),
                (
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{repo_root}:/workspace/opamp",
                    client_config_generator_deployment_image,
                ),
            ),
        ),
        RegressionTest(
            test_id="consumer-plugin-startup",
            description="Builds and runs the consumer plugin startup regression container.",
            commands=(
                (
                    "docker",
                    "build",
                    "-f",
                    str(repo_root / "tests/test-containers/consumer-plugin-startup/Dockerfile"),
                    "-t",
                    consumer_plugin_image,
                    str(repo_root / "tests/test-containers/consumer-plugin-startup"),
                ),
                (
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{repo_root}:/workspace/opamp",
                    consumer_plugin_image,
                ),
            ),
        ),
        RegressionTest(
            test_id="opamp-consumer-deployment-smoke",
            description=(
                "Builds the consumer wheel, then smoke-tests Fluent Bit, Fluentd, and Elastic Heartbeat "
                "deployment containers through install, plugin verification, and config staging."
            ),
            commands=(
                (
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "build",
                ),
                (
                    sys.executable,
                    "-m",
                    "build",
                    "--wheel",
                    "--outdir",
                    str(repo_root / "dist/consumer"),
                    str(repo_root / "consumer"),
                ),
                (
                    "docker",
                    "build",
                    "-f",
                    str(repo_root / "tests/test-containers/opamp-consumer-deployment/Dockerfile"),
                    "-t",
                    consumer_deployment_image,
                    str(repo_root / "tests/test-containers/opamp-consumer-deployment"),
                ),
                (
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{repo_root}:/host-assets",
                    "-v",
                    f"{repo_root / 'tests/test-containers/opamp-consumer-deployment/examples'}:/config",
                    "-v",
                    f"{repo_root / 'dist/test-reports/opamp-consumer-deployment/fluentbit'}:/host-output",
                    "--add-host",
                    "host.docker.internal:host-gateway",
                    "-e",
                    "TEST_CONTAINER_CONFIG=/config/regression-fluentbit.env",
                    consumer_deployment_image,
                ),
                (
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{repo_root}:/host-assets",
                    "-v",
                    f"{repo_root / 'tests/test-containers/opamp-consumer-deployment/examples'}:/config",
                    "-v",
                    f"{repo_root / 'dist/test-reports/opamp-consumer-deployment/fluentd'}:/host-output",
                    "--add-host",
                    "host.docker.internal:host-gateway",
                    "-e",
                    "TEST_CONTAINER_CONFIG=/config/regression-fluentd.env",
                    consumer_deployment_image,
                ),
                (
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{repo_root}:/host-assets",
                    "-v",
                    f"{repo_root / 'tests/test-containers/opamp-consumer-deployment/examples'}:/config",
                    "-v",
                    f"{repo_root / 'dist/test-reports/opamp-consumer-deployment/elastic-heartbeat'}:/host-output",
                    "--add-host",
                    "host.docker.internal:host-gateway",
                    "-e",
                    "TEST_CONTAINER_CONFIG=/config/regression-elastic-heartbeat.env",
                    consumer_deployment_image,
                ),
            ),
        ),
        RegressionTest(
            test_id="st001",
            description="Runs ST-001 socket and HTTP simulator/provider container scenarios.",
            commands=((bash, _bash_path(repo_root / "tests/test-containers/st001/scripts/run_st001.sh"), "all"),),
        ),
        RegressionTest(
            test_id="agent-shutdown-e2e",
            description=(
                "Uses the provider UI to shut down all six built-in consumer types "
                "in sequence, then verifies process exit and provider disconnect state."
            ),
            commands=(
                (
                    bash,
                    _bash_path(
                        repo_root
                        / "tests/test-containers/agent-shutdown-e2e/scripts/run_agent_shutdown_e2e.sh"
                    ),
                ),
            ),
        ),
        RegressionTest(
            test_id="st002",
            description="Runs ST-002 socket and HTTP simulator/provider container scenarios.",
            commands=((bash, _bash_path(repo_root / "tests/test-containers/st002/scripts/run_st002.sh"), "all"),),
        ),
        RegressionTest(
            test_id="st004",
            description="Runs ST-004 Keycloak authorization container scenario.",
            commands=((bash, _bash_path(repo_root / "tests/test-containers/st004/scripts/run_st004.sh"), "keycloak"),),
        ),
        RegressionTest(
            test_id="vector-plugin-e2e",
            description=(
                "Runs a provider plus Vector-supervising consumer and verifies "
                "Vector health/output evidence."
            ),
            commands=((bash, _bash_path(repo_root / "tests/test-containers/vector-plugin-e2e/scripts/run_vector_plugin_e2e.sh")),),
        ),
        RegressionTest(
            test_id="config-service-ui-playwright-batch",
            description=(
                "Builds the Config Service wheel and runs the Playwright chapter "
                "batch validation container."
            ),
            commands=(
                (
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "build",
                ),
                (
                    sys.executable,
                    "-m",
                    "build",
                    "--wheel",
                    "--outdir",
                    str(repo_root / "config-service/dist"),
                    str(repo_root / "config-service"),
                ),
                (
                    "docker",
                    "build",
                    "-f",
                    str(repo_root / "tests/test-containers/config-service-ui-playwright-batch/Dockerfile"),
                    "-t",
                    config_service_ui_image,
                    str(repo_root),
                ),
                (
                    "docker",
                    "run",
                    "--rm",
                    "--ipc=host",
                    "-e",
                    "OPAMP_REPO=/workspace/opamp",
                    "-e",
                    "CONFIG_SERVICE_DIR=/workspace/opamp/config-service",
                    "-e",
                    "CONFIG_SERVICE_CONFIG_PATH=/workspace/opamp/config-service/config/config-service.json",
                    "-e",
                    "WHEEL_DIR=/workspace/opamp/config-service/dist",
                    "-e",
                    "RESULTS_DIR=/workspace/opamp/dist/test-reports/config-service-ui-playwright-batch",
                    "-e",
                    "PLAYWRIGHT_BATCH_CONFIG=/workspace/opamp/config-service/dev-tools/playwright-batch-config/default-batch-config.json",
                    "-v",
                    f"{repo_root}:/workspace/opamp",
                    config_service_ui_image,
                ),
            ),
        ),
    ]


def _tail_text(value: object, limit: int) -> str:
    """Return a compact tail of command or evidence output.

    Parameters:
    - value: Stream text or other value to render into the Markdown report.
    - limit: Maximum character count retained from the end of the text.
    """
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def _markdown_code_block(value: str, language: str = "text") -> list[str]:
    """Render a fenced Markdown code block for diagnostic report details.

    Parameters:
    - value: Text to include inside the fenced block.
    - language: Optional Markdown language tag for syntax highlighting.
    """
    return [f"```{language}", value, "```"]


def _append_failed_command_details(
    lines: list[str],
    result: dict[str, object],
) -> None:
    """Append captured stdout/stderr for the failed command in a result.

    Parameters:
    - lines: Mutable Markdown line buffer for the report being written.
    - result: Regression result payload containing command execution records.
    """
    command_payloads = result.get(COMMANDS_KEY, [])
    if not isinstance(command_payloads, list):
        return
    for command_payload in command_payloads:
        if not isinstance(command_payload, dict):
            continue
        if int(command_payload.get(EXIT_CODE_KEY) or 0) == 0:
            continue
        command = command_payload.get(COMMAND_KEY, [])
        command_text = " ".join(str(part) for part in command) if isinstance(command, list) else str(command)
        lines.extend(["", f"- Command: `{command_text}`"])
        lines.append(f"- Exit code: `{command_payload.get(EXIT_CODE_KEY)}`")
        stderr_tail = _tail_text(command_payload.get(STDERR_KEY), COMMAND_TAIL_LIMIT)
        stdout_tail = _tail_text(command_payload.get(STDOUT_KEY), COMMAND_TAIL_LIMIT)
        if stderr_tail:
            lines.extend(["", "stderr tail:"])
            lines.extend(_markdown_code_block(stderr_tail))
        if stdout_tail:
            lines.extend(["", "stdout tail:"])
            lines.extend(_markdown_code_block(stdout_tail))
        return


def _append_evidence_file_details(
    lines: list[str],
    result: dict[str, object],
    output_dir: Path,
) -> None:
    """Append relevant per-scenario evidence files for a failed result.

    Parameters:
    - lines: Mutable Markdown line buffer for the report being written.
    - result: Regression result payload used to resolve the sibling evidence tree.
    - output_dir: Regression-pack report directory under dist/test-reports.
    """
    test_id = str(result.get(TEST_ID_KEY) or "").strip()
    if not test_id:
        return
    evidence_root = output_dir.parent / test_id
    if not evidence_root.is_dir():
        return

    evidence_paths: list[Path] = []
    for evidence_file_name in EVIDENCE_FILE_NAMES:
        evidence_paths.extend(sorted(evidence_root.rglob(evidence_file_name)))
    if not evidence_paths:
        return

    lines.extend(["", "Evidence file tails:"])
    for evidence_path in evidence_paths:
        relative_path = evidence_path.relative_to(output_dir.parent)
        lines.extend(["", f"`{relative_path.as_posix()}`:"])
        try:
            evidence_text = evidence_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            lines.append(f"Unable to read evidence file: {exc}")
            continue
        lines.extend(_markdown_code_block(_tail_text(evidence_text, EVIDENCE_TAIL_LIMIT)))


def _append_failure_details(
    lines: list[str],
    results: list[dict[str, object]],
    output_dir: Path,
) -> None:
    """Append failure diagnostics after the summary table.

    Parameters:
    - lines: Mutable Markdown line buffer for the report being written.
    - results: Regression result payloads created by the runner.
    - output_dir: Directory receiving the Markdown and JSON pack reports.
    """
    failed_results = [
        result for result in results if int(result.get(EXIT_CODE_KEY) or 0) != 0
    ]
    if not failed_results:
        return
    lines.extend(["", "## Failures", ""])
    for result in failed_results:
        lines.append(f"### {result.get(TEST_ID_KEY)}")
        _append_failed_command_details(lines, result)
        _append_evidence_file_details(lines, result, output_dir)
        lines.append("")


def _write_reports(results: list[dict[str, object]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    passed = all(int(result[EXIT_CODE_KEY]) == 0 for result in results)
    payload = {
        "name": "opamp-container-regression-pack",
        "passed": passed,
        "results": results,
    }
    (output_dir / JSON_REPORT_FILE_NAME).write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# OpAMP Container Regression Pack Results",
        "",
        "| Test | Status | Exit code | Duration |",
        "|---|---|---:|---:|",
    ]
    for result in results:
        status = "passed" if int(result[EXIT_CODE_KEY]) == 0 else "failed"
        lines.append(
            f"| {result[TEST_ID_KEY]} | {status} | {result[EXIT_CODE_KEY]} | "
            f"{result[DURATION_SECONDS_KEY]}s |"
        )
    lines.append("")
    lines.append(f"Overall: {'passed' if passed else 'failed'}")
    lines.append("")
    _append_failure_details(lines, results, output_dir)
    (output_dir / MARKDOWN_REPORT_FILE_NAME).write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def _run_test(test: RegressionTest, *, repo_root: Path) -> dict[str, object]:
    started = time.monotonic()
    command_results: list[dict[str, object]] = []
    exit_code = 0
    command_env = os.environ.copy()
    command_env.setdefault("OPAMP_PYTHON", sys.executable)
    for command in test.commands:
        print(f"[regression-pack] {test.test_id}: {' '.join(command)}", flush=True)
        completed = subprocess.run(
            list(command),
            cwd=str(repo_root),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
            env=command_env,
        )
        command_results.append(
            {
                "command": list(command),
                "exit_code": int(completed.returncode),
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
        if completed.returncode != 0:
            exit_code = int(completed.returncode)
            break
    duration = round(time.monotonic() - started, 3)
    return {
        "test_id": test.test_id,
        "description": test.description,
        "exit_code": exit_code,
        "duration_seconds": duration,
        "commands": command_results,
    }


def main(argv: list[str] | None = None) -> int:
    repo_root = _repo_root()
    _ensure_regression_directories(repo_root)
    tests = _default_tests(repo_root)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list regression tests and exit")
    parser.add_argument("--only", action="append", default=[], help="run only the named test id; can be repeated")
    parser.add_argument("--skip", action="append", default=[], help="skip the named test id; can be repeated")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root / "dist/test-reports/regression-pack",
        help="directory for JSON and Markdown summary reports",
    )
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="run remaining tests after a failure instead of stopping early",
    )
    args = parser.parse_args(argv)

    selected = tests
    if args.only:
        requested = set(args.only)
        selected = [test for test in selected if test.test_id in requested]
    if args.skip:
        skipped = set(args.skip)
        selected = [test for test in selected if test.test_id not in skipped]

    if args.list:
        for test in selected:
            print(f"{test.test_id}: {test.description}")
        return 0

    results: list[dict[str, object]] = []
    for test in selected:
        result = _run_test(test, repo_root=repo_root)
        results.append(result)
        if int(result["exit_code"]) != 0 and not args.continue_on_failure:
            break

    _write_reports(results, args.output_dir.resolve())
    return 0 if all(int(result["exit_code"]) == 0 for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
