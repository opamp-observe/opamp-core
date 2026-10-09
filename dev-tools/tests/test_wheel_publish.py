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

"""Tests for publishing latest wheel artifacts from local and cloud sources."""

from __future__ import annotations

import os
import subprocess
import tarfile
import zipfile
from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from opamp_dev_tools import wheel_publish
from opamp_dev_tools.runtime import CommandRuntimeError

FIRST_TIMESTAMP = 1_700_000_000
SECOND_TIMESTAMP = FIRST_TIMESTAMP + 100
PUBLISH_ARGUMENT_ARTIFACT_PATHS = "artifact_paths"
PUBLISH_ARGUMENT_REPOSITORY = "repo"
PUBLISH_ARGUMENT_TAG = "tag"


class _FakeRuntime:
    """Capture wheel upload commands and messages.

    Attributes
    ----------
    repo_root:
        Temporary repository root containing test wheels and marker files.
    commands:
        Provider CLI commands observed during the test.
    messages:
        Informational messages emitted by the publishing workflow.

    """

    def __init__(self, repo_root: Path) -> None:
        """Initialize the fake runtime for a temporary repository.

        Parameters
        ----------
        repo_root:
            Temporary root used for wheel discovery and marker lookup.

        """
        self.repo_root = repo_root
        self.commands: list[list[str]] = []
        self.messages: list[str] = []

    def info(self, message: str) -> None:
        """Capture one informational publishing message.

        Parameters
        ----------
        message:
            Console message emitted by the publishing workflow.

        """
        self.messages.append(message)

    def run(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        """Capture one cloud-provider CLI command.

        Parameters
        ----------
        command:
            AWS or Azure upload command to record.

        """
        self.commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")


class _DownloadRuntime(_FakeRuntime):
    """Capture commands and simulate provider downloads on the host.

    Attributes
    ----------
    command_effect:
        Callback that creates files in response to provider CLI commands.

    """

    def __init__(self, repo_root: Path, command_effect: Callable[[list[str]], None]) -> None:
        """Initialize the runtime with a provider command callback.

        Parameters
        ----------
        repo_root:
            Temporary repository root containing marker files.
        command_effect:
            Callback invoked after each captured command.

        """
        super().__init__(repo_root)
        self.command_effect = command_effect

    def run(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        """Capture one command and apply its simulated download effect.

        Parameters
        ----------
        command:
            AWS or Azure command being simulated.

        """
        completed = super().run(command)
        self.command_effect(command)
        return completed


class _AwsDiscoveryRuntime(_FakeRuntime):
    """Return a configured result for retained AWS bucket discovery.

    Attributes
    ----------
    bucket_output:
        AWS CLI text returned by the simulated list-buckets query.

    """

    def __init__(self, repo_root: Path, bucket_output: str) -> None:
        """Initialize the runtime with simulated AWS query output.

        Parameters
        ----------
        repo_root:
            Temporary repository root containing wheels and marker files.
        bucket_output:
            Bucket name or empty AWS CLI query result returned to the resolver.

        """
        super().__init__(repo_root)
        self.bucket_output = bucket_output

    def run(
        self,
        command: list[str],
        *,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        """Capture the AWS query and return its configured text output.

        Parameters
        ----------
        command:
            AWS CLI command being simulated.
        capture_output:
            Whether the caller requested captured standard output.

        """
        self.commands.append(command)
        assert capture_output is True
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=self.bucket_output,
            stderr="",
        )


def _write_wheel(
    wheel_path: Path,
    *,
    project_name: str,
    version: str,
    timestamp: int,
) -> None:
    """Create a minimal wheel archive with package identity metadata.

    Parameters
    ----------
    wheel_path:
        Destination wheel archive path.
    project_name:
        Distribution name written into METADATA.
    version:
        Distribution version written into METADATA.
    timestamp:
        Modification timestamp used by latest-wheel selection.

    """
    wheel_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path = f"{project_name}-{version}.dist-info/METADATA"
    with zipfile.ZipFile(wheel_path, mode="w") as wheel_archive:
        wheel_archive.writestr(
            metadata_path,
            f"Metadata-Version: 2.1\nName: {project_name}\nVersion: {version}\n",
        )
    os.utime(wheel_path, (timestamp, timestamp))


def test_discover_latest_wheels_selects_newest_build_per_project(tmp_path: Path) -> None:
    """Wheel discovery should retain only the newest host build per package."""
    _write_wheel(
        tmp_path / "dist" / "old" / "example-1.0-py3-none-any.whl",
        project_name="Example_Package",
        version="1.0",
        timestamp=FIRST_TIMESTAMP,
    )
    newest_path = tmp_path / "dist" / "new" / "example-1.1-py3-none-any.whl"
    _write_wheel(
        newest_path,
        project_name="example-package",
        version="1.1",
        timestamp=SECOND_TIMESTAMP,
    )
    _write_wheel(
        tmp_path / "dist" / "other-2.0-py3-none-any.whl",
        project_name="Other",
        version="2.0",
        timestamp=FIRST_TIMESTAMP,
    )

    wheels = wheel_publish.discover_latest_wheels(tmp_path, "dist")

    assert [wheel.project_name for wheel in wheels] == ["example-package", "Other"]
    assert wheels[0].path == newest_path.resolve()


def test_upload_latest_wheels_to_aws_uses_bucket_marker(tmp_path: Path) -> None:
    """AWS uploads should use the deployment marker when no bucket is explicit."""
    wheel_path = tmp_path / "dist" / "example-1.0-py3-none-any.whl"
    _write_wheel(
        wheel_path,
        project_name="example",
        version="1.0",
        timestamp=FIRST_TIMESTAMP,
    )
    marker_path = tmp_path / wheel_publish.AWS_STORAGE_MARKER
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text("opamp-artifacts\n", encoding="utf-8")
    runtime = _FakeRuntime(tmp_path)

    wheel_publish.push_latest_wheels_to_cloud(
        runtime,
        wheel_publish.WheelUploadOptions(
            origin="aws",
            release="v1.2.3",
            aws_region="eu-west-1",
        ),
    )

    assert runtime.commands == [
        [
            "aws",
            "s3",
            "cp",
            str(wheel_path.resolve()),
            "s3://opamp-artifacts/releases/v1.2.3/wheels/example-1.0-py3-none-any.whl",
            "--region",
            "eu-west-1",
            "--only-show-errors",
        ]
    ]


def test_push_to_aws_discovers_and_records_latest_bucket(tmp_path: Path) -> None:
    """AWS transfers should discover the newest retained bucket without a marker."""
    _write_wheel(
        tmp_path / "dist" / "example-1.0-py3-none-any.whl",
        project_name="example",
        version="1.0",
        timestamp=FIRST_TIMESTAMP,
    )
    discovered_bucket = "opamp-regression-123456789012-2026-10-09-12-00-00"
    runtime = _AwsDiscoveryRuntime(tmp_path, f"{discovered_bucket}\n")

    wheel_publish.push_latest_wheels_to_cloud(
        runtime,
        wheel_publish.WheelUploadOptions(
            origin="aws",
            release="v1.2.3",
            dry_run=True,
        ),
    )

    assert runtime.commands[0][:3] == ["aws", "s3api", "list-buckets"]
    assert wheel_publish.AWS_RETAINED_BUCKET_PREFIX in runtime.commands[0][4]
    assert (tmp_path / wheel_publish.AWS_STORAGE_MARKER).read_text(
        encoding="utf-8"
    ) == f"{discovered_bucket}\n"
    assert any(f"s3://{discovered_bucket}/" in message for message in runtime.messages)


@pytest.mark.parametrize("bucket_output", ["None\n", "\n"])
def test_push_to_aws_reports_when_discovery_finds_no_bucket(
    tmp_path: Path,
    bucket_output: str,
) -> None:
    """AWS discovery should explain how to recover when no retained bucket exists.

    Parameters
    ----------
    tmp_path:
        Temporary repository root containing a wheel and empty marker.
    bucket_output:
        Empty result representation returned by the AWS CLI.

    """
    _write_wheel(
        tmp_path / "dist" / "example-1.0-py3-none-any.whl",
        project_name="example",
        version="1.0",
        timestamp=FIRST_TIMESTAMP,
    )
    marker_path = tmp_path / wheel_publish.AWS_STORAGE_MARKER
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text("\n", encoding="utf-8")
    runtime = _AwsDiscoveryRuntime(tmp_path, bucket_output)

    with pytest.raises(RuntimeError, match="Deploy AWS first or pass --storage-name"):
        wheel_publish.push_latest_wheels_to_cloud(
            runtime,
            wheel_publish.WheelUploadOptions(
                origin="aws",
                release="v1.2.3",
                dry_run=True,
            ),
        )

    assert marker_path.read_text(encoding="utf-8") == "\n"


def test_push_to_aws_reports_discovery_authentication_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """AWS discovery failures should provide authentication recovery guidance."""
    _write_wheel(
        tmp_path / "dist" / "example-1.0-py3-none-any.whl",
        project_name="example",
        version="1.0",
        timestamp=FIRST_TIMESTAMP,
    )
    runtime = _FakeRuntime(tmp_path)

    def fail_aws_query(
        _command: list[str],
        *,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        """Simulate an AWS CLI session or authorization failure.

        Parameters
        ----------
        _command:
            AWS CLI discovery command supplied by the resolver.
        capture_output:
            Whether command output was requested by the resolver.

        """
        assert capture_output is True
        raise CommandRuntimeError("AWS session expired")

    monkeypatch.setattr(runtime, "run", fail_aws_query)

    with pytest.raises(RuntimeError, match="Authenticate the AWS CLI"):
        wheel_publish.push_latest_wheels_to_cloud(
            runtime,
            wheel_publish.WheelUploadOptions(
                origin="aws",
                release="v1.2.3",
                dry_run=True,
            ),
        )


def test_upload_latest_wheels_to_azure_uses_explicit_account(tmp_path: Path) -> None:
    """Azure uploads should target the requested account and release prefix."""
    wheel_path = tmp_path / "dist" / "example-1.0-py3-none-any.whl"
    _write_wheel(
        wheel_path,
        project_name="example",
        version="1.0",
        timestamp=FIRST_TIMESTAMP,
    )
    runtime = _FakeRuntime(tmp_path)

    wheel_publish.push_latest_wheels_to_cloud(
        runtime,
        wheel_publish.WheelUploadOptions(
            origin="azure",
            release="release/one",
            storage_name="opampstorage",
            azure_container="releases",
        ),
    )

    assert runtime.commands[0] == [
        "az",
        "storage",
        "blob",
        "upload",
        "--account-name",
        "opampstorage",
        "--container-name",
        "releases",
        "--name",
        "releases/release%2Fone/wheels/example-1.0-py3-none-any.whl",
        "--file",
        str(wheel_path.resolve()),
        "--auth-mode",
        "login",
        "--overwrite",
        "true",
    ]


def test_push_to_azure_uses_storage_account_marker(tmp_path: Path) -> None:
    """Azure pushes should read a non-empty storage account marker."""
    wheel_path = tmp_path / "dist" / "example-1.0-py3-none-any.whl"
    _write_wheel(
        wheel_path,
        project_name="example",
        version="1.0",
        timestamp=FIRST_TIMESTAMP,
    )
    marker_path = tmp_path / wheel_publish.AZURE_STORAGE_MARKER
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text("markedaccount\n", encoding="utf-8")
    runtime = _FakeRuntime(tmp_path)

    wheel_publish.push_latest_wheels_to_cloud(
        runtime,
        wheel_publish.WheelUploadOptions(
            origin="azure",
            release="v1.2.3",
            dry_run=True,
        ),
    )

    assert any("--account-name markedaccount" in message for message in runtime.messages)


def test_upload_latest_wheels_to_github_reuses_release_publisher(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """GitHub uploads should delegate selected wheels to the release API helper."""
    wheel_path = tmp_path / "dist" / "example-1.0-py3-none-any.whl"
    _write_wheel(
        wheel_path,
        project_name="example",
        version="1.0",
        timestamp=FIRST_TIMESTAMP,
    )
    captured_calls: list[tuple[str, str, list[Path]]] = []

    def fake_publish_github_release_files(**arguments: object) -> None:
        """Capture the repository, tag, and asset paths passed to GitHub.

        Parameters
        ----------
        arguments:
            Keyword arguments accepted by the release publishing helper.

        """
        captured_calls.append(
            (
                str(arguments[PUBLISH_ARGUMENT_REPOSITORY]),
                str(arguments[PUBLISH_ARGUMENT_TAG]),
                list(arguments[PUBLISH_ARGUMENT_ARTIFACT_PATHS]),  # type: ignore[arg-type]
            )
        )

    monkeypatch.setattr(
        wheel_publish,
        "publish_github_release_files",
        fake_publish_github_release_files,
    )
    runtime = _FakeRuntime(tmp_path)

    wheel_publish.upload_latest_wheels(
        runtime,
        wheel_publish.WheelUploadOptions(
            origin="local",
            release="v1.2.3",
            repository="example/repository",
            github_token="token",
        ),
    )

    assert captured_calls == [
        ("example/repository", "v1.2.3", [wheel_path.resolve()])
    ]


def test_upload_latest_wheels_github_dry_run_skips_release_api(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """A GitHub dry run should not resolve credentials or call the API."""
    _write_wheel(
        tmp_path / "dist" / "example-1.0-py3-none-any.whl",
        project_name="example",
        version="1.0",
        timestamp=FIRST_TIMESTAMP,
    )

    def fail_publish(**_arguments: object) -> None:
        """Fail if dry-run publishing reaches the GitHub API helper."""
        raise AssertionError("GitHub publisher must not run during a dry run")

    monkeypatch.setattr(wheel_publish, "publish_github_release_files", fail_publish)
    runtime = _FakeRuntime(tmp_path)

    wheel_publish.upload_latest_wheels(
        runtime,
        wheel_publish.WheelUploadOptions(
            origin="local",
            release="v1.2.3",
            dry_run=True,
        ),
    )

    assert any("Would upload" in message for message in runtime.messages)


def test_upload_latest_wheels_aws_dry_run_reports_without_execution(tmp_path: Path) -> None:
    """An AWS dry run should report the command without invoking the runtime."""
    _write_wheel(
        tmp_path / "dist" / "example-1.0-py3-none-any.whl",
        project_name="example",
        version="1.0",
        timestamp=FIRST_TIMESTAMP,
    )
    runtime = _FakeRuntime(tmp_path)

    wheel_publish.push_latest_wheels_to_cloud(
        runtime,
        wheel_publish.WheelUploadOptions(
            origin="aws",
            release="v1.2.3",
            storage_name="bucket",
            dry_run=True,
        ),
    )

    assert not runtime.commands
    assert any("Would run: aws s3 cp" in message for message in runtime.messages)


@pytest.mark.parametrize(
    ("origin", "expected_fallback"),
    [
        ("aws", "Fallback source"),
        ("azure", "Fallback command"),
    ],
)
def test_upload_wheels_cloud_dry_run_reports_github_destination(
    tmp_path: Path,
    origin: str,
    expected_fallback: str,
) -> None:
    """Cloud-to-GitHub dry runs should report both retrieval stages and GitHub.

    Parameters
    ----------
    tmp_path:
        Temporary repository root used by the fake runtime.
    origin:
        Cloud provider whose retrieval commands should be reported.
    expected_fallback:
        Message fragment identifying the provider-specific fallback.

    """
    runtime = _FakeRuntime(tmp_path)

    wheel_publish.upload_latest_wheels(
        runtime,
        wheel_publish.WheelUploadOptions(
            origin=origin,
            release="v1.2.3",
            storage_name="latest-storage",
            dry_run=True,
        ),
    )

    assert not runtime.commands
    assert any(expected_fallback in message for message in runtime.messages)
    assert any("Would publish wheels" in message for message in runtime.messages)


def test_wheel_discovery_reports_missing_and_empty_directories(tmp_path: Path) -> None:
    """Wheel discovery should distinguish absent directories from empty ones."""
    with pytest.raises(RuntimeError, match="does not exist"):
        wheel_publish.discover_latest_wheels(tmp_path, "missing")

    empty_dist = tmp_path / "empty-dist"
    empty_dist.mkdir()
    with pytest.raises(RuntimeError, match="No wheel files"):
        wheel_publish.discover_latest_wheels(tmp_path, str(empty_dist))


def test_wheel_discovery_rejects_invalid_wheel_metadata(tmp_path: Path) -> None:
    """Malformed wheels should fail before any provider upload is attempted."""
    no_metadata_path = tmp_path / "dist" / "no-metadata.whl"
    no_metadata_path.parent.mkdir(parents=True)
    with zipfile.ZipFile(no_metadata_path, mode="w") as wheel_archive:
        wheel_archive.writestr("package/module.py", "")
    with pytest.raises(RuntimeError, match="exactly one METADATA"):
        wheel_publish.discover_latest_wheels(tmp_path, "dist")

    no_metadata_path.unlink()
    missing_version_path = tmp_path / "dist" / "missing-version.whl"
    with zipfile.ZipFile(missing_version_path, mode="w") as wheel_archive:
        wheel_archive.writestr(
            "example-1.0.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: example\n",
        )
    with pytest.raises(RuntimeError, match="missing Name or Version"):
        wheel_publish.discover_latest_wheels(tmp_path, "dist")


def test_upload_validation_reports_bad_origin_release_prefix_and_markers(tmp_path: Path) -> None:
    """Invalid destinations should fail before provider CLIs are invoked."""
    _write_wheel(
        tmp_path / "dist" / "example-1.0-py3-none-any.whl",
        project_name="example",
        version="1.0",
        timestamp=FIRST_TIMESTAMP,
    )
    runtime = _FakeRuntime(tmp_path)

    with pytest.raises(RuntimeError, match="Release name must not be empty"):
        wheel_publish.push_latest_wheels_to_cloud(
            runtime,
            wheel_publish.WheelUploadOptions(origin="aws", release=" ", storage_name="bucket"),
        )
    with pytest.raises(RuntimeError, match="prefix must not be empty"):
        wheel_publish.push_latest_wheels_to_cloud(
            runtime,
            wheel_publish.WheelUploadOptions(origin="aws", release="v1", prefix="/"),
        )
    with pytest.raises(RuntimeError, match="Unsupported wheel upload origin"):
        wheel_publish.upload_latest_wheels(
            runtime,
            wheel_publish.WheelUploadOptions(origin="unknown", release="v1"),
        )
    with pytest.raises(RuntimeError, match="Unsupported cloud push origin"):
        wheel_publish.push_latest_wheels_to_cloud(
            runtime,
            wheel_publish.WheelUploadOptions(origin="local", release="v1"),
        )
    with pytest.raises(RuntimeError, match="Unsupported cloud retrieval origin"):
        wheel_publish._retrieve_cloud_wheels(  # pylint: disable=protected-access
            runtime,
            options=wheel_publish.WheelUploadOptions(origin="local", release="v1"),
            destination=tmp_path,
        )
    with pytest.raises(RuntimeError, match="marker file does not exist"):
        wheel_publish.upload_latest_wheels(
            runtime,
            wheel_publish.WheelUploadOptions(origin="azure", release="v1"),
        )

    marker_path = tmp_path / wheel_publish.AZURE_STORAGE_MARKER
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text("\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="marker file is empty"):
        wheel_publish.upload_latest_wheels(
            runtime,
            wheel_publish.WheelUploadOptions(origin="azure", release="v1"),
        )


def test_upload_wheels_retrieves_aws_release_prefix_then_publishes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """AWS origin should download release wheels before publishing to GitHub."""
    marker_path = tmp_path / wheel_publish.AWS_STORAGE_MARKER
    marker_path.parent.mkdir(parents=True)
    marker_path.write_text("latest-bucket\n", encoding="utf-8")

    def create_downloaded_wheel(command: list[str]) -> None:
        """Create a wheel when the simulated recursive S3 copy runs."""
        if "--recursive" not in command:
            return
        _write_wheel(
            Path(command[4]) / "example-2.0-py3-none-any.whl",
            project_name="example",
            version="2.0",
            timestamp=SECOND_TIMESTAMP,
        )

    published_names: list[list[str]] = []

    def capture_publish(**arguments: object) -> None:
        """Capture downloaded artifact names passed to GitHub."""
        artifact_paths = list(arguments[PUBLISH_ARGUMENT_ARTIFACT_PATHS])  # type: ignore[arg-type]
        published_names.append([artifact_path.name for artifact_path in artifact_paths])

    monkeypatch.setattr(wheel_publish, "publish_github_release_files", capture_publish)
    runtime = _DownloadRuntime(tmp_path, create_downloaded_wheel)

    wheel_publish.upload_latest_wheels(
        runtime,
        wheel_publish.WheelUploadOptions(origin="aws", release="v2.0.0"),
    )

    assert runtime.commands[0][3] == "s3://latest-bucket/releases/v2.0.0/wheels/"
    assert published_names == [["example-2.0-py3-none-any.whl"]]


def test_upload_wheels_aws_falls_back_to_deployment_archive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """AWS origin should extract wheels from the deployment archive fallback."""
    source_wheel = tmp_path / "source" / "example-3.0-py3-none-any.whl"
    _write_wheel(
        source_wheel,
        project_name="example",
        version="3.0",
        timestamp=SECOND_TIMESTAMP,
    )

    def create_downloaded_archive(command: list[str]) -> None:
        """Create the deployment archive when its S3 copy is simulated."""
        if "--recursive" in command:
            return
        archive_path = Path(command[4])
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive_path, mode="w:gz") as archive:
            archive.add(source_wheel, arcname=f"wheels/{source_wheel.name}")

    published_names: list[str] = []

    def capture_publish(**arguments: object) -> None:
        """Capture the extracted wheel name passed to GitHub."""
        artifact_paths = list(arguments[PUBLISH_ARGUMENT_ARTIFACT_PATHS])  # type: ignore[arg-type]
        published_names.extend(artifact_path.name for artifact_path in artifact_paths)

    monkeypatch.setattr(wheel_publish, "publish_github_release_files", capture_publish)
    runtime = _DownloadRuntime(tmp_path, create_downloaded_archive)

    wheel_publish.upload_latest_wheels(
        runtime,
        wheel_publish.WheelUploadOptions(
            origin="aws",
            release="v3.0.0",
            storage_name="latest-bucket",
        ),
    )

    assert len(runtime.commands) == 2
    assert runtime.commands[1][3].endswith(wheel_publish.AWS_DEFAULT_ARTIFACT_KEY)
    assert published_names == [source_wheel.name]


def test_upload_wheels_azure_falls_back_to_artifact_container(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Azure origin should retrieve deployment wheels when release wheels are absent."""
    command_count = 0

    def create_fallback_wheel(command: list[str]) -> None:
        """Create a wheel only for the second Azure batch download."""
        nonlocal command_count
        command_count += 1
        if command_count != 2:
            return
        destination_index = command.index("--destination") + 1
        _write_wheel(
            Path(command[destination_index]) / "wheels" / "example-4.0-py3-none-any.whl",
            project_name="example",
            version="4.0",
            timestamp=SECOND_TIMESTAMP,
        )

    published_names: list[str] = []

    def capture_publish(**arguments: object) -> None:
        """Capture the Azure-downloaded wheel passed to GitHub."""
        artifact_paths = list(arguments[PUBLISH_ARGUMENT_ARTIFACT_PATHS])  # type: ignore[arg-type]
        published_names.extend(artifact_path.name for artifact_path in artifact_paths)

    monkeypatch.setattr(wheel_publish, "publish_github_release_files", capture_publish)
    runtime = _DownloadRuntime(tmp_path, create_fallback_wheel)

    wheel_publish.upload_latest_wheels(
        runtime,
        wheel_publish.WheelUploadOptions(
            origin="azure",
            release="v4.0.0",
            storage_name="latestaccount",
        ),
    )

    assert len(runtime.commands) == 2
    assert "opamp-cloud" in runtime.commands[1]
    assert published_names == ["example-4.0-py3-none-any.whl"]


def test_upload_wheels_azure_uses_release_prefix_when_available(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Azure origin should publish release-prefix wheels without fallback retrieval."""

    def create_release_wheel(command: list[str]) -> None:
        """Create a wheel during the first simulated Azure batch download.

        Parameters
        ----------
        command:
            Azure batch download command containing the destination path.

        """
        destination_index = command.index("--destination") + 1
        _write_wheel(
            Path(command[destination_index]) / "example-5.0-py3-none-any.whl",
            project_name="example",
            version="5.0",
            timestamp=SECOND_TIMESTAMP,
        )

    published_names: list[str] = []

    def capture_publish(**arguments: object) -> None:
        """Capture the Azure release wheel passed to GitHub.

        Parameters
        ----------
        arguments:
            Keyword arguments accepted by the release publishing helper.

        """
        artifact_paths = list(arguments[PUBLISH_ARGUMENT_ARTIFACT_PATHS])  # type: ignore[arg-type]
        published_names.extend(artifact_path.name for artifact_path in artifact_paths)

    monkeypatch.setattr(wheel_publish, "publish_github_release_files", capture_publish)
    runtime = _DownloadRuntime(tmp_path, create_release_wheel)

    wheel_publish.upload_latest_wheels(
        runtime,
        wheel_publish.WheelUploadOptions(
            origin="azure",
            release="v5.0.0",
            storage_name="latestaccount",
        ),
    )

    assert len(runtime.commands) == 1
    assert "releases/v5.0.0/wheels/*.whl" in runtime.commands[0]
    assert published_names == ["example-5.0-py3-none-any.whl"]


def test_extract_wheels_rejects_archive_without_readable_wheels(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """AWS fallback extraction should reject archives without readable wheels."""
    non_wheel_member = MagicMock()
    non_wheel_member.isfile.return_value = False
    non_wheel_member.name = "wheels/"
    unreadable_wheel_member = MagicMock()
    unreadable_wheel_member.isfile.return_value = True
    unreadable_wheel_member.name = "wheels/unreadable.whl"
    fake_archive = MagicMock()
    fake_archive.getmembers.return_value = [non_wheel_member, unreadable_wheel_member]
    fake_archive.extractfile.return_value = None
    archive_context = MagicMock()
    archive_context.__enter__.return_value = fake_archive

    def fake_tar_open(_archive_path: Path, *, mode: str) -> MagicMock:
        """Return a simulated archive with no readable wheel payload.

        Parameters
        ----------
        _archive_path:
            Ignored archive path supplied by the extraction helper.
        mode:
            Archive read mode supplied by the extraction helper.

        """
        assert mode == "r:gz"
        return archive_context

    monkeypatch.setattr(wheel_publish.tarfile, "open", fake_tar_open)

    with pytest.raises(RuntimeError, match="contains no wheel files"):
        wheel_publish._extract_wheels_from_tar(  # pylint: disable=protected-access
            tmp_path / "artifacts.tar.gz",
            tmp_path / "wheels",
        )
