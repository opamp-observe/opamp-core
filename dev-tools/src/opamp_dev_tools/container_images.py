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

"""Discover and remove project-managed Docker or Podman images."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from typing import Any

CONTAINER_RUNTIME_ENV = "OPAMP_CONTAINER_RUNTIME"
CONTAINER_RUNTIME_CHOICES = ("docker", "podman")
IMAGE_LIST_FORMAT = "{{.ID}}\t{{.Repository}}:{{.Tag}}"
IMAGE_ROW_SEPARATOR = "\t"
LEGACY_IMAGE_REPOSITORY_PREFIX = "opamp-"
MANAGED_IMAGE_LABEL_KEY = "opamp-observe.managed"
MANAGED_IMAGE_LABEL_VALUE = "true"
MANAGED_IMAGE_LABEL = f"{MANAGED_IMAGE_LABEL_KEY}={MANAGED_IMAGE_LABEL_VALUE}"


@dataclass(frozen=True)
class ContainerImage:
    """Describe one locally stored project container image.

    Attributes
    ----------
    image_id:
        Runtime-assigned identifier used when removing the image.
    repository_tag:
        Human-readable repository and tag shown in cleanup output.

    """

    image_id: str
    repository_tag: str


def resolve_container_runtime(configured_runtime: str = "") -> str:
    """Resolve the selected Docker or Podman executable.

    Parameters
    ----------
    configured_runtime:
        Optional command-line selection. When omitted, the
        ``OPAMP_CONTAINER_RUNTIME`` environment variable is checked before
        Docker and Podman are auto-detected.

    """
    requested_runtime = configured_runtime.strip() or os.environ.get(
        CONTAINER_RUNTIME_ENV, ""
    ).strip()
    candidates = (requested_runtime,) if requested_runtime else CONTAINER_RUNTIME_CHOICES
    for candidate in candidates:
        executable = shutil.which(candidate)
        if executable:
            return executable
    requested_description = requested_runtime or "docker or podman"
    raise RuntimeError(
        f"Container runtime '{requested_description}' was not found. "
        f"Install it or set {CONTAINER_RUNTIME_ENV}."
    )


def clean_project_images(
    runtime: Any,
    *,
    configured_runtime: str = "",
    include_legacy: bool = False,
    force: bool = False,
    dry_run: bool = False,
) -> bool:
    """Remove project-managed images from the selected container runtime.

    Parameters
    ----------
    runtime:
        Command runtime used for subprocess execution and console logging.
    configured_runtime:
        Optional explicit ``docker`` or ``podman`` selection.
    include_legacy:
        Whether to include unlabelled images whose repository starts with
        ``opamp-`` from builds created before managed labels were introduced.
    force:
        Whether to ask the runtime to remove images referenced by containers.
    dry_run:
        Whether to report matching images without deleting them.

    """
    runtime_executable = resolve_container_runtime(configured_runtime)
    runtime.info(f"DEBUG: selected container runtime: {runtime_executable}")
    managed_images = _list_images(
        runtime,
        runtime_executable=runtime_executable,
        label_filter=MANAGED_IMAGE_LABEL,
    )
    images_by_id = {image.image_id: image for image in managed_images}

    if include_legacy:
        for image in _list_images(runtime, runtime_executable=runtime_executable):
            if _is_legacy_project_image(image):
                images_by_id.setdefault(image.image_id, image)

    images = sorted(images_by_id.values(), key=lambda image: image.repository_tag)
    if not images:
        runtime.info("No OpAMP-managed container images were found.")
        return False

    action = "Would remove" if dry_run else "Removing"
    for image in images:
        runtime.info(f"{action} image {image.repository_tag} ({image.image_id})")
        if dry_run:
            continue
        remove_command = [runtime_executable, "image", "rm"]
        if force:
            remove_command.append("--force")
        remove_command.append(image.image_id)
        runtime.run(remove_command)
    return False


def _list_images(
    runtime: Any,
    *,
    runtime_executable: str,
    label_filter: str = "",
) -> list[ContainerImage]:
    """List local images, optionally restricting them by an image label.

    Parameters
    ----------
    runtime:
        Command runtime used to execute the image-list command.
    runtime_executable:
        Resolved Docker or Podman executable path.
    label_filter:
        Optional exact label key/value used to restrict returned images.

    """
    command = [runtime_executable, "image", "ls"]
    if label_filter:
        command.extend(["--filter", f"label={label_filter}"])
    command.extend(["--format", IMAGE_LIST_FORMAT])
    completed = runtime.run(command, capture_output=True)
    return _parse_image_rows(completed.stdout or "")


def _parse_image_rows(output: str) -> list[ContainerImage]:
    """Parse formatted Docker or Podman image-list output.

    Parameters
    ----------
    output:
        Tab-separated image IDs and repository tags emitted by the runtime.

    """
    images: list[ContainerImage] = []
    for raw_line in output.splitlines():
        image_id, separator, repository_tag = raw_line.partition(IMAGE_ROW_SEPARATOR)
        if not separator or not image_id.strip():
            continue
        images.append(
            ContainerImage(
                image_id=image_id.strip(),
                repository_tag=repository_tag.strip(),
            )
        )
    return images


def _is_legacy_project_image(image: ContainerImage) -> bool:
    """Return whether an unlabelled image follows the legacy OpAMP naming convention.

    Parameters
    ----------
    image:
        Image metadata returned by Docker or Podman.

    """
    repository = image.repository_tag.rsplit("/", maxsplit=1)[-1]
    return repository.startswith(LEGACY_IMAGE_REPOSITORY_PREFIX)
