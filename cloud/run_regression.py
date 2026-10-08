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

"""Run the regression pack and retain its reports in AWS or Azure storage."""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

AWS_PROVIDER = "aws"
AZURE_PROVIDER = "azure"
DEFAULT_AWS_BUCKET_FILE = "dist/aws-artifact-bucket.txt"
DEFAULT_AWS_PREFIX = "regression-results"
DEFAULT_AZURE_CONTAINER = "opamp-regression-results"
DEFAULT_AZURE_STORAGE_FILE = "dist/azure-retention-storage-account.txt"
DEFAULT_RESULTS_DIRECTORY = "dist/test-reports"
MANIFEST_FILE_NAME = "cloud_upload_manifest.json"
MANIFEST_CREATED_AT_KEY = "created_at_utc"
MANIFEST_DESTINATION_KEY = "destination"
MANIFEST_PROVIDER_KEY = "provider"
MANIFEST_REGRESSION_EXIT_CODE_KEY = "regression_exit_code"
MANIFEST_RESULT_SET_KEY = "result_set"
MANIFEST_STATUS_KEY = "status"
MANIFEST_UPLOAD_EXIT_CODE_KEY = "upload_exit_code"
REPORT_BUILD_COMMANDS_KEY = "build_commands"
REPORT_COMMANDS_KEY = "commands"
REPORT_COMPONENT_ID_KEY = "component_id"
REPORT_DESCRIPTION_KEY = "description"
REPORT_DETAIL_KEY = "detail"
REPORT_EXIT_CODE_KEY = "exit_code"
REPORT_NAME_KEY = "name"
REPORT_PASSED_KEY = "passed"
REPORT_RESULTS_KEY = "results"
REPORT_STAGE_KEY = "stage"
REPORT_STDERR_KEY = "stderr"
REPORT_STDOUT_KEY = "stdout"
REPORT_TEST_ID_KEY = "test_id"
REPORTS_FILE_PATTERN = "*-results.json"
PROVIDER_CHOICES = (AWS_PROVIDER, AZURE_PROVIDER)
REGRESSION_RUNNER = "tests/test-containers/run_regression_pack.py"
SUMMARY_TEXT_LIMIT = 500
STATUS_PASSED = "passed"
STATUS_REGRESSION_FAILED = "regression_failed"
STATUS_UPLOAD_FAILED = "upload_failed"
STATUS_UPLOAD_ONLY = "upload_only"

LOGGER = logging.getLogger(__name__)


def _repository_root() -> Path:
    """Return the repository root containing this provider-neutral command."""
    return Path(__file__).resolve().parents[1]


def _resolve_repository_path(repository_root: Path, configured_path: str) -> Path:
    """Resolve a configured path, keeping relative paths anchored to the repository."""
    candidate_path = Path(configured_path).expanduser()
    if candidate_path.is_absolute():
        return candidate_path.resolve()
    return (repository_root / candidate_path).resolve()


def _read_retained_storage_name(storage_file: Path, provider: str) -> str:
    """Read the storage name saved by deployment, validating that it is usable."""
    if not storage_file.is_file():
        raise RuntimeError(
            f"No {provider} retained-storage marker exists at {storage_file}. "
            "Deploy first or pass --storage-name."
        )
    storage_name = storage_file.read_text(encoding="utf-8-sig").strip()
    if not storage_name:
        raise RuntimeError(f"The retained-storage marker is empty: {storage_file}")
    return storage_name


def _run_command(command: list[str], repository_root: Path) -> int:
    """Run one visible child command and return its process exit code."""
    LOGGER.debug("Running command: %s", subprocess.list2cmdline(command))
    completed_process = subprocess.run(
        command,
        cwd=repository_root,
        check=False,
    )
    return int(completed_process.returncode)


def _run_regression_pack(
    arguments: argparse.Namespace,
    repository_root: Path,
    results_directory: Path,
) -> int:
    """Run selected regression tests while preserving the pack's normal CLI behavior."""
    command = [
        sys.executable,
        str(repository_root / REGRESSION_RUNNER),
        "--output-dir",
        str(results_directory / "regression-pack"),
    ]
    for test_id in arguments.only:
        command.extend(("--only", test_id))
    for test_id in arguments.skip:
        command.extend(("--skip", test_id))
    if arguments.continue_on_failure:
        command.append("--continue-on-failure")
    return _run_command(command, repository_root)


def _write_upload_manifest(
    results_directory: Path,
    provider: str,
    result_set: str,
    destination: str,
    regression_exit_code: int | None,
    upload_exit_code: int | None,
) -> Path:
    """Record what was uploaded and whether the associated regression run passed."""
    manifest_path = results_directory / MANIFEST_FILE_NAME
    manifest = {
        MANIFEST_CREATED_AT_KEY: datetime.now(UTC).isoformat(),
        MANIFEST_DESTINATION_KEY: destination,
        MANIFEST_PROVIDER_KEY: provider,
        MANIFEST_REGRESSION_EXIT_CODE_KEY: regression_exit_code,
        MANIFEST_RESULT_SET_KEY: result_set,
        MANIFEST_STATUS_KEY: _manifest_status(regression_exit_code, upload_exit_code),
        MANIFEST_UPLOAD_EXIT_CODE_KEY: upload_exit_code,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _manifest_status(
    regression_exit_code: int | None,
    upload_exit_code: int | None,
) -> str:
    """Resolve a compact manifest status from regression and upload outcomes."""
    if upload_exit_code not in (None, 0):
        return STATUS_UPLOAD_FAILED
    if regression_exit_code not in (None, 0):
        return STATUS_REGRESSION_FAILED
    if regression_exit_code is None:
        return STATUS_UPLOAD_ONLY
    return STATUS_PASSED


def _tail_text(value: object, limit: int = SUMMARY_TEXT_LIMIT) -> str:
    """Return a compact tail of a captured command stream for failure logs."""
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def _summarize_failed_command(command_payload: dict[str, object]) -> str:
    """Summarize one failed command payload from a regression report."""
    stage = str(command_payload.get(REPORT_STAGE_KEY) or "").strip()
    exit_code = command_payload.get(REPORT_EXIT_CODE_KEY)
    stdout_tail = _tail_text(command_payload.get(REPORT_STDOUT_KEY))
    stderr_tail = _tail_text(command_payload.get(REPORT_STDERR_KEY))
    parts = [f"exit={exit_code}"]
    if stage:
        parts.append(f"stage={stage}")
    if stderr_tail:
        parts.append(f"stderr={stderr_tail}")
    elif stdout_tail:
        parts.append(f"stdout={stdout_tail}")
    return "; ".join(parts)


def _collect_regression_failure_summaries(results_directory: Path) -> list[str]:
    """Collect concise failure lines from retained regression JSON reports."""
    summaries: list[str] = []
    for report_path in sorted(results_directory.rglob(REPORTS_FILE_PATTERN)):
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            summaries.append(f"{report_path.name}: unreadable report: {exc}")
            continue
        report_name = str(payload.get(REPORT_NAME_KEY) or report_path.stem)
        for result in payload.get(REPORT_RESULTS_KEY, []):
            if not isinstance(result, dict):
                continue
            if result.get(REPORT_PASSED_KEY) is True or result.get(REPORT_EXIT_CODE_KEY) == 0:
                continue
            result_id = str(
                result.get(REPORT_TEST_ID_KEY)
                or result.get(REPORT_COMPONENT_ID_KEY)
                or result.get(REPORT_DESCRIPTION_KEY)
                or "unknown"
            )
            detail = str(result.get(REPORT_DETAIL_KEY) or "").strip()
            stage = str(result.get(REPORT_STAGE_KEY) or "").strip()
            line = f"{report_name}: {result_id} failed"
            if stage:
                line = f"{line} at {stage}"
            if detail:
                line = f"{line}: {detail}"
            for command_payload in result.get(REPORT_COMMANDS_KEY, []):
                if (
                    isinstance(command_payload, dict)
                    and command_payload.get(REPORT_EXIT_CODE_KEY) not in (None, 0)
                ):
                    line = f"{line} ({_summarize_failed_command(command_payload)})"
                    break
            summaries.append(line)
        for command_payload in payload.get(REPORT_BUILD_COMMANDS_KEY, []):
            if (
                isinstance(command_payload, dict)
                and command_payload.get(REPORT_EXIT_CODE_KEY) not in (None, 0)
            ):
                summaries.append(
                    f"{report_name}: build command failed "
                    f"({_summarize_failed_command(command_payload)})"
                )
    return summaries


def _upload_aws_results(
    arguments: argparse.Namespace,
    repository_root: Path,
    results_directory: Path,
    storage_name: str,
    result_set: str,
) -> tuple[int, str]:
    """Upload the report tree to the timestamped prefix in an S3 bucket."""
    destination = (
        f"s3://{storage_name}/{arguments.aws_prefix.strip('/')}/{result_set}/test-reports/"
    )
    command = [
        "aws",
        "s3",
        "cp",
        str(results_directory),
        destination,
        "--recursive",
        "--region",
        arguments.aws_region,
    ]
    return _run_command(command, repository_root), destination


def _upload_azure_results(
    arguments: argparse.Namespace,
    repository_root: Path,
    results_directory: Path,
    storage_name: str,
    result_set: str,
) -> tuple[int, str]:
    """Upload the report tree to a timestamped path in an Azure blob container."""
    destination_path = f"{result_set}/test-reports"
    destination = (
        f"https://{storage_name}.blob.core.windows.net/"
        f"{arguments.azure_container}/{destination_path}/"
    )
    command = [
        "az",
        "storage",
        "blob",
        "upload-batch",
        "--account-name",
        storage_name,
        "--destination",
        arguments.azure_container,
        "--destination-path",
        destination_path,
        "--source",
        str(results_directory),
        "--auth-mode",
        "key",
        "--overwrite",
    ]
    return _run_command(command, repository_root), destination


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line contract shared by AWS and Azure operators."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, choices=PROVIDER_CHOICES)
    parser.add_argument("--only", action="append", default=[], help="run only this test id")
    parser.add_argument("--skip", action="append", default=[], help="skip this test id")
    parser.add_argument("--continue-on-failure", action="store_true")
    parser.add_argument(
        "--upload-only",
        action="store_true",
        help="upload existing reports without running the regression pack",
    )
    parser.add_argument("--result-set", default="", help="storage path; defaults to UTC time")
    parser.add_argument("--results-directory", default=DEFAULT_RESULTS_DIRECTORY)
    parser.add_argument("--storage-name", default="", help="S3 bucket or storage account")
    parser.add_argument("--aws-region", default="eu-west-2")
    parser.add_argument("--aws-prefix", default=DEFAULT_AWS_PREFIX)
    parser.add_argument("--azure-container", default=DEFAULT_AZURE_CONTAINER)
    parser.add_argument("--log-level", default="DEBUG")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run or reuse reports, then publish them while preserving test failure status."""
    arguments = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, arguments.log_level.upper(), logging.DEBUG),
        format="%(levelname)s %(message)s",
    )
    repository_root = _repository_root()
    results_directory = _resolve_repository_path(
        repository_root, arguments.results_directory
    )
    results_directory.mkdir(parents=True, exist_ok=True)

    regression_exit_code: int | None = None
    if not arguments.upload_only:
        regression_exit_code = _run_regression_pack(
            arguments, repository_root, results_directory
        )

    result_files = [path for path in results_directory.rglob("*") if path.is_file()]
    if not result_files:
        raise RuntimeError(f"No regression result files found in {results_directory}")

    result_set = arguments.result_set or datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    if arguments.provider == AWS_PROVIDER:
        storage_file = _resolve_repository_path(repository_root, DEFAULT_AWS_BUCKET_FILE)
        storage_name = arguments.storage_name or _read_retained_storage_name(
            storage_file, AWS_PROVIDER
        )
        destination = (
            f"s3://{storage_name}/{arguments.aws_prefix.strip('/')}/"
            f"{result_set}/test-reports/"
        )
        _write_upload_manifest(
            results_directory,
            arguments.provider,
            result_set,
            destination,
            regression_exit_code,
            None,
        )
        upload_exit_code, destination = _upload_aws_results(
            arguments, repository_root, results_directory, storage_name, result_set
        )
    else:
        storage_file = _resolve_repository_path(
            repository_root, DEFAULT_AZURE_STORAGE_FILE
        )
        storage_name = arguments.storage_name or _read_retained_storage_name(
            storage_file, AZURE_PROVIDER
        )
        destination = (
            f"https://{storage_name}.blob.core.windows.net/"
            f"{arguments.azure_container}/{result_set}/test-reports/"
        )
        _write_upload_manifest(
            results_directory,
            arguments.provider,
            result_set,
            destination,
            regression_exit_code,
            None,
        )
        upload_exit_code, destination = _upload_azure_results(
            arguments, repository_root, results_directory, storage_name, result_set
        )

    _write_upload_manifest(
        results_directory,
        arguments.provider,
        result_set,
        destination,
        regression_exit_code,
        upload_exit_code,
    )
    if upload_exit_code != 0:
        if regression_exit_code in (None, 0):
            LOGGER.error(
                "Regression result upload failed with exit code %s after the "
                "regression pack passed",
                upload_exit_code,
            )
        else:
            LOGGER.error(
                "Regression result upload failed with exit code %s after the "
                "regression pack returned %s",
                upload_exit_code,
                regression_exit_code,
            )
        return upload_exit_code
    LOGGER.info("Retained regression results: %s", destination)
    if regression_exit_code not in (None, 0):
        for failure_summary in _collect_regression_failure_summaries(results_directory):
            LOGGER.error("Regression failure: %s", failure_summary)
        LOGGER.error("Regression pack failed with exit code %s", regression_exit_code)
    return regression_exit_code or 0


if __name__ == "__main__":
    raise SystemExit(main())
