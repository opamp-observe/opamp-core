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

"""Tests for Docker and Podman project image cleanup."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from opamp_dev_tools import container_images


class _FakeRuntime:
    """Capture image cleanup commands and provide deterministic list output.

    Attributes
    ----------
    outputs:
        Ordered stdout payloads returned by image-list commands.
    commands:
        Commands observed during the test.
    messages:
        Informational messages emitted by the cleanup workflow.

    """

    def __init__(self, outputs: list[str]) -> None:
        """Initialize the fake with image-list output.

        Parameters
        ----------
        outputs:
            Ordered stdout payloads consumed by captured-output commands.

        """
        self.outputs = list(outputs)
        self.commands: list[list[str]] = []
        self.messages: list[str] = []

    def info(self, message: str) -> None:
        """Capture one informational message.

        Parameters
        ----------
        message:
            Console message emitted by the cleanup workflow.

        """
        self.messages.append(message)

    def run(
        self,
        command: list[str],
        *,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        """Capture one command and return queued image-list output.

        Parameters
        ----------
        command:
            Docker or Podman command being executed.
        capture_output:
            Whether the caller expects image-list stdout.

        """
        self.commands.append(command)
        stdout = self.outputs.pop(0) if capture_output else ""
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")


def test_resolve_container_runtime_prefers_environment(monkeypatch) -> None:
    """The standardized environment selection should precede auto-detection."""
    monkeypatch.setenv(container_images.CONTAINER_RUNTIME_ENV, "podman")
    monkeypatch.setattr(container_images.shutil, "which", lambda candidate: f"/bin/{candidate}")

    executable = container_images.resolve_container_runtime()

    assert executable == "/bin/podman"


def test_resolve_container_runtime_falls_back_to_podman(monkeypatch) -> None:
    """Auto-detection should continue to Podman when Docker is unavailable."""
    monkeypatch.delenv(container_images.CONTAINER_RUNTIME_ENV, raising=False)
    monkeypatch.setattr(
        container_images.shutil,
        "which",
        lambda candidate: "podman.exe" if candidate == "podman" else None,
    )

    executable = container_images.resolve_container_runtime()

    assert executable == "podman.exe"


def test_resolve_container_runtime_reports_missing_selection(monkeypatch) -> None:
    """A requested runtime that is absent should produce an actionable error."""
    monkeypatch.setattr(container_images.shutil, "which", lambda _candidate: None)

    with pytest.raises(RuntimeError, match="docker.*was not found"):
        container_images.resolve_container_runtime("docker")


def test_clean_project_images_dry_run_does_not_remove(monkeypatch) -> None:
    """Dry-run cleanup should list labelled images without deleting them."""
    monkeypatch.setattr(container_images.shutil, "which", lambda candidate: candidate)
    runtime = _FakeRuntime(["sha256:managed\topamp-st001:latest\n"])

    issues_found = container_images.clean_project_images(
        runtime,
        configured_runtime="docker",
        dry_run=True,
    )

    assert issues_found is False
    assert len(runtime.commands) == 1
    assert f"label={container_images.MANAGED_IMAGE_LABEL}" in runtime.commands[0]
    assert any("Would remove image opamp-st001:latest" in message for message in runtime.messages)


def test_clean_project_images_includes_deduplicated_legacy_images(monkeypatch) -> None:
    """Legacy mode should include opamp-prefixed images without duplicate removals."""
    monkeypatch.setattr(container_images.shutil, "which", lambda candidate: candidate)
    runtime = _FakeRuntime(
        [
            "sha256:managed\topamp-st001:latest\n",
            (
                "sha256:managed\topamp-st001:latest\n"
                "sha256:legacy\tlocal/opamp-old-test:latest\n"
                "sha256:other\tunrelated:latest\n"
            ),
        ]
    )

    container_images.clean_project_images(
        runtime,
        configured_runtime="podman",
        include_legacy=True,
        force=True,
    )

    removal_commands = [command for command in runtime.commands if command[1:3] == ["image", "rm"]]
    assert removal_commands == [
        ["podman", "image", "rm", "--force", "sha256:legacy"],
        ["podman", "image", "rm", "--force", "sha256:managed"],
    ]


def test_clean_project_images_handles_empty_and_malformed_list_output(monkeypatch) -> None:
    """Cleanup should ignore malformed rows and succeed when no image matches."""
    monkeypatch.setattr(container_images.shutil, "which", lambda candidate: candidate)
    runtime = _FakeRuntime(["malformed-row\n\tmissing-id\n"])

    issues_found = container_images.clean_project_images(
        runtime,
        configured_runtime="docker",
    )

    assert issues_found is False
    assert len(runtime.commands) == 1
    assert "No OpAMP-managed container images were found." in runtime.messages


def test_clean_project_images_removes_without_force_by_default(monkeypatch) -> None:
    """Normal cleanup should avoid the runtime force flag unless requested."""
    monkeypatch.setattr(container_images.shutil, "which", lambda candidate: candidate)
    runtime = _FakeRuntime(["sha256:managed\topamp-test:latest\n"])

    container_images.clean_project_images(runtime, configured_runtime="docker")

    assert runtime.commands[-1] == ["docker", "image", "rm", "sha256:managed"]


def test_all_regression_dockerfiles_have_managed_image_label() -> None:
    """Every project-built regression image should be discoverable for cleanup."""
    repo_root = Path(__file__).resolve().parents[2]
    dockerfiles = sorted((repo_root / "tests" / "test-containers").rglob("Dockerfile*"))

    assert dockerfiles
    for dockerfile in dockerfiles:
        content = dockerfile.read_text(encoding="utf-8")
        assert (
            f'LABEL {container_images.MANAGED_IMAGE_LABEL_KEY}="'
            f'{container_images.MANAGED_IMAGE_LABEL_VALUE}"'
        ) in content, dockerfile
