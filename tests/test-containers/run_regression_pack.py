#!/usr/bin/env python3
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


@dataclass(frozen=True)
class RegressionTest:
    test_id: str
    description: str
    commands: tuple[tuple[str, ...], ...]


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


def _write_reports(results: list[dict[str, object]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    passed = all(int(result["exit_code"]) == 0 for result in results)
    payload = {
        "name": "opamp-container-regression-pack",
        "passed": passed,
        "results": results,
    }
    (output_dir / "regression-pack-results.json").write_text(
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
        status = "passed" if int(result["exit_code"]) == 0 else "failed"
        lines.append(
            f"| {result['test_id']} | {status} | {result['exit_code']} | {result['duration_seconds']}s |"
        )
    lines.append("")
    lines.append(f"Overall: {'passed' if passed else 'failed'}")
    lines.append("")
    (output_dir / "regression-pack-results.md").write_text(
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
