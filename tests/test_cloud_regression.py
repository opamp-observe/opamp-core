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

"""Unit tests for running and retaining cloud regression evidence."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGRESSION_COMMAND_PATH = REPOSITORY_ROOT / "cloud" / "run_regression.py"
TEST_RESULT_SET = "20261006123000"


def _load_regression_module() -> ModuleType:
    """Load the standalone cloud command as a module for focused unit tests."""
    module_spec = importlib.util.spec_from_file_location(
        "cloud_run_regression", REGRESSION_COMMAND_PATH
    )
    assert module_spec is not None
    assert module_spec.loader is not None
    regression_module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(regression_module)
    return regression_module


@pytest.fixture(name="regression_module")
def fixture_regression_module() -> ModuleType:
    """Provide a newly loaded command module so monkeypatches never leak."""
    return _load_regression_module()


def _prepare_reports(repository_root: Path, storage_file: str, storage_name: str) -> None:
    """Create representative reports and a deployment-generated storage marker."""
    reports_directory = repository_root / "dist" / "test-reports"
    reports_directory.mkdir(parents=True)
    (reports_directory / "summary.json").write_text("{}\n", encoding="utf-8")
    marker_path = repository_root / storage_file
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(storage_name + "\n", encoding="utf-8")


def test_aws_upload_only_uses_saved_bucket_and_timestamped_prefix(
    regression_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Publish existing reports to the retained bucket saved by AWS deployment."""
    bucket_name = "opamp-regression-example"
    _prepare_reports(tmp_path, "dist/aws-artifact-bucket.txt", bucket_name)
    captured_commands: list[list[str]] = []
    monkeypatch.setattr(regression_module, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(
        regression_module,
        "_run_command",
        lambda command, _repository_root: captured_commands.append(command) or 0,
    )

    exit_code = regression_module.main(
        [
            "--provider",
            "aws",
            "--upload-only",
            "--result-set",
            TEST_RESULT_SET,
        ]
    )

    assert exit_code == 0
    assert captured_commands == [
        [
            "aws",
            "s3",
            "cp",
            str(tmp_path / "dist" / "test-reports"),
            f"s3://{bucket_name}/regression-results/{TEST_RESULT_SET}/test-reports/",
            "--recursive",
            "--region",
            "eu-west-2",
        ]
    ]
    manifest = json.loads(
        (tmp_path / "dist/test-reports/cloud_upload_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["provider"] == "aws"
    assert manifest["regression_exit_code"] is None


def test_azure_upload_only_uses_saved_storage_account(
    regression_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Publish existing reports to the private container created by Azure deployment."""
    storage_account = "opampexample"
    _prepare_reports(
        tmp_path,
        "dist/azure-retention-storage-account.txt",
        storage_account,
    )
    captured_commands: list[list[str]] = []
    monkeypatch.setattr(regression_module, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(
        regression_module,
        "_run_command",
        lambda command, _repository_root: captured_commands.append(command) or 0,
    )

    exit_code = regression_module.main(
        [
            "--provider",
            "azure",
            "--upload-only",
            "--result-set",
            TEST_RESULT_SET,
        ]
    )

    assert exit_code == 0
    assert captured_commands[0][:4] == ["az", "storage", "blob", "upload-batch"]
    assert "--destination-path" in captured_commands[0]
    assert f"{TEST_RESULT_SET}/test-reports" in captured_commands[0]
    assert storage_account in captured_commands[0]


def test_failed_regression_is_uploaded_and_failure_status_is_returned(
    regression_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Retain failure evidence before returning the regression process status."""
    regression_failure_code = 7
    _prepare_reports(tmp_path, "dist/aws-artifact-bucket.txt", "failure-bucket")
    monkeypatch.setattr(regression_module, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(
        regression_module,
        "_run_regression_pack",
        lambda _arguments, _repository_root, _results_directory: regression_failure_code,
    )
    monkeypatch.setattr(
        regression_module,
        "_upload_aws_results",
        lambda *_arguments: (0, "s3://failure-bucket/regression-results/evidence/"),
    )

    exit_code = regression_module.main(
        ["--provider", "aws", "--result-set", TEST_RESULT_SET]
    )

    assert exit_code == regression_failure_code
    manifest = json.loads(
        (tmp_path / "dist/test-reports/cloud_upload_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["regression_exit_code"] == regression_failure_code


def test_missing_reports_are_not_represented_as_a_completed_upload(
    regression_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Reject upload-only operation when no test evidence exists locally."""
    monkeypatch.setattr(regression_module, "_repository_root", lambda: tmp_path)

    with pytest.raises(RuntimeError, match="No regression result files found"):
        regression_module.main(["--provider", "aws", "--upload-only"])
