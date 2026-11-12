# Copyright 2026 opamp.info
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

"""Docker-backed OWASP ZAP dynamic application security testing helpers."""

from __future__ import annotations

import logging
import re
import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .container_images import MANAGED_IMAGE_LABEL, resolve_container_runtime
from .runtime import CommandRuntime

BASELINE_MODE = "baseline"
FULL_MODE = "full"
DAST_SCAN_MODES = (BASELINE_MODE, FULL_MODE)
DEFAULT_DAST_SCOPE = "provider"
MANAGED_TARGET_NETWORK_ALIAS = "opamp-dast-target"
MANAGED_TARGET_PORT = 8080
DEFAULT_DAST_TARGET = f"http://{MANAGED_TARGET_NETWORK_ALIAS}:{MANAGED_TARGET_PORT}"
DEFAULT_SPIDER_MINUTES = 2
DEFAULT_STARTUP_TIMEOUT_MINUTES = 5
DEFAULT_TARGET_READY_TIMEOUT_SECONDS = 180
DEFAULT_ZAP_IMAGE = (
    "ghcr.io/zaproxy/zaproxy:2.17.0"
    "@sha256:9624669db72f54d86c4b46a7064518bd9bf79d8c61a4c31befa9923489f328af"
)
DOCKER_HOST_ALIAS = "host.docker.internal"
DOCKER_HOST_GATEWAY_MAPPING = f"{DOCKER_HOST_ALIAS}:host-gateway"
DOCKER_RUNTIME_NAMES = frozenset({"docker", "docker.exe"})
MANAGED_TARGET_DOCKERFILE = Path("dev-tools/docker/dast/Dockerfile")
MANAGED_TARGET_IMAGE = "opamp-dast-full-app:local"
MANAGED_TARGET_RESOURCE_PREFIX = "opamp-dast"
MANAGED_TARGET_RUN_ID_LENGTH = 12
MANAGED_TARGET_STATUS_HEALTHY = "healthy"
MANAGED_TARGET_STATUS_UNHEALTHY = "unhealthy"
MANAGED_TARGET_STATUS_EXITED = "exited"
MANAGED_TARGET_TERMINAL_STATUSES = frozenset(
    {MANAGED_TARGET_STATUS_UNHEALTHY, MANAGED_TARGET_STATUS_EXITED}
)
MANAGED_TARGET_STATUS_POLL_SECONDS = 1
CONTAINER_HEALTH_STATUS_FORMAT = (
    "{{if .State.Health}}{{.State.Health.Status}}"
    "{{else}}{{.State.Status}}{{end}}"
)
HTML_REPORT_FILE_NAME = "zap_report.html"
JSON_REPORT_FILE_NAME = "zap_report.json"
MARKDOWN_REPORT_FILE_NAME = "zap_report.md"
RULES_COPY_FILE_NAME = "zap_rules.conf"
RULES_GENERATED_FILE_NAME = "zap_generated_rules.conf"
SCAN_HOOK_COPY_FILE_NAME = "zap_scan_hooks.py"
XML_REPORT_FILE_NAME = "zap_report.xml"
ZAP_CONTAINER_WORK_DIRECTORY = "/zap/wrk"
ZAP_REPORT_DIRECTORY = Path("dev-tools/runtime/security-reports/zap")
ZAP_WORK_VOLUME_MODE = "rw"
BASELINE_SCAN_SCRIPT = "zap-baseline.py"
FULL_SCAN_SCRIPT = "zap-full-scan.py"
SCAN_SCRIPT_BY_MODE = {
    BASELINE_MODE: BASELINE_SCAN_SCRIPT,
    FULL_MODE: FULL_SCAN_SCRIPT,
}
HTTP_SCHEMES = frozenset({"http", "https"})
SCOPE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
SCAN_HOOK_SOURCE_PATH = Path(__file__).with_name("dast_scan_hooks.py")


@dataclass(frozen=True)
class DastScanOptions:  # pylint: disable=too-many-instance-attributes
    """Describe one isolated OWASP ZAP container scan.

    Attributes
    ----------
    mode:
        Packaged ZAP scan mode: passive ``baseline`` or active ``full``.
    target:
        HTTP or HTTPS URL that ZAP should crawl from inside its container.
    scope:
        Filesystem-safe report scope used below the retained report directory.
    configured_runtime:
        Optional explicit Docker or Podman executable selection.
    image:
        ZAP container image reference used for the scan.
    rules_file:
        Optional host-side ZAP rule configuration copied into the report workspace.
    spider_minutes:
        Maximum traditional spider duration passed to the packaged scan.
    startup_timeout_minutes:
        Maximum startup and passive-scan wait passed to the packaged scan.
    fail_on_warning:
        Whether ZAP warning-only results should fail the developer command.
    generate_rules:
        Whether ZAP should write a default rule configuration beside the reports.
    allow_active_scan:
        Explicit acknowledgement required before the full scan sends attack payloads.
    external_target:
        Whether to scan a separately managed URL instead of the isolated full-app container.

    """

    mode: str
    target: str = DEFAULT_DAST_TARGET
    scope: str = DEFAULT_DAST_SCOPE
    configured_runtime: str = ""
    image: str = DEFAULT_ZAP_IMAGE
    rules_file: Path | None = None
    spider_minutes: int = DEFAULT_SPIDER_MINUTES
    startup_timeout_minutes: int = DEFAULT_STARTUP_TIMEOUT_MINUTES
    fail_on_warning: bool = False
    generate_rules: bool = False
    allow_active_scan: bool = False
    external_target: bool = False


@dataclass(frozen=True)
class ManagedDastDeployment:
    """Identify the private container resources owned by one DAST run.

    Attributes
    ----------
    network_name:
        Unique private container network shared only by the application and ZAP containers.
    container_name:
        Unique full-application target container removed after the scan.

    """

    network_name: str
    container_name: str


def run_dast_scan(runtime: CommandRuntime, *, options: DastScanOptions) -> bool:
    """Run one Docker-backed ZAP scan and retain portable report artifacts.

    Parameters
    ----------
    runtime:
        Shared developer CLI runtime used for paths, logging, and process execution.
    options:
        Validated scan configuration controlling the image, target, policy, and reports.

    """
    _validate_scan_options(options)
    runtime_executable = resolve_container_runtime(options.configured_runtime)
    report_directory = (
        runtime.repo_root / ZAP_REPORT_DIRECTORY / options.scope / options.mode
    ).resolve()
    report_directory.mkdir(parents=True, exist_ok=True)
    copied_rules_file = _copy_rules_file(
        runtime,
        source_path=options.rules_file,
        report_directory=report_directory,
    )
    copied_scan_hook = _copy_scan_hook(report_directory=report_directory)
    deployment: ManagedDastDeployment | None = None
    try:
        if not options.external_target:
            deployment = _start_managed_target(
                runtime,
                runtime_executable=runtime_executable,
                options=options,
            )
        command = _build_zap_command(
            runtime_executable=runtime_executable,
            report_directory=report_directory,
            options=options,
            copied_rules_file=copied_rules_file,
            copied_scan_hook=copied_scan_hook,
            network_name=deployment.network_name if deployment is not None else None,
        )
        target_kind = "external" if options.external_target else "isolated full-app container"
        runtime.info(
            f"DEBUG: OWASP ZAP mode={options.mode} target={options.target} kind={target_kind}"
        )
        runtime.info(f"DEBUG: OWASP ZAP reports={report_directory}")
        runtime.run(command, cwd=runtime.repo_root)
    finally:
        if deployment is not None:
            _stop_managed_target(
                runtime,
                runtime_executable=runtime_executable,
                deployment=deployment,
            )
    runtime.info(f"OWASP ZAP {options.mode} scan complete: {report_directory}")
    return False


def _validate_scan_options(options: DastScanOptions) -> None:
    """Reject unsafe or unsupported scan values before starting a container.

    Parameters
    ----------
    options:
        Candidate options supplied by direct or guided CLI parsing.

    """
    if options.mode not in DAST_SCAN_MODES:
        raise ValueError(f"Unsupported DAST mode: {options.mode}")
    parsed_target = urlparse(options.target)
    if parsed_target.scheme not in HTTP_SCHEMES or not parsed_target.hostname:
        raise ValueError("DAST target must be an absolute HTTP or HTTPS URL")
    if not options.external_target and parsed_target.hostname != MANAGED_TARGET_NETWORK_ALIAS:
        raise ValueError(
            f"Managed DAST scans must target {MANAGED_TARGET_NETWORK_ALIAS}; use "
            "--external-target only for a separately managed deployment"
        )
    if not SCOPE_PATTERN.fullmatch(options.scope):
        raise ValueError(
            "DAST scope must start with an alphanumeric character and contain only "
            "letters, numbers, dots, underscores, or hyphens"
        )
    if options.spider_minutes <= 0:
        raise ValueError("DAST spider minutes must be greater than zero")
    if options.startup_timeout_minutes <= 0:
        raise ValueError("DAST startup timeout minutes must be greater than zero")
    if not options.image.strip():
        raise ValueError("DAST image must not be empty")
    if options.rules_file is not None and options.generate_rules:
        raise ValueError("Use either an existing rules file or --generate-rules, not both")
    if options.mode == FULL_MODE and not options.allow_active_scan:
        raise ValueError(
            "Full ZAP scans send attack payloads; rerun with --allow-active-scan "
            "against a disposable test deployment"
        )


def _managed_resource_name(*, resource_kind: str, options: DastScanOptions) -> str:
    """Return a unique, traceable container resource name for one scan.

    Parameters
    ----------
    resource_kind:
        Short resource classifier such as ``network`` or ``target``.
    options:
        Scan settings whose scope and mode make local resource listings understandable.

    """
    run_id = uuid.uuid4().hex[:MANAGED_TARGET_RUN_ID_LENGTH]
    name_parts = (
        MANAGED_TARGET_RESOURCE_PREFIX,
        options.scope,
        options.mode,
        resource_kind,
        run_id,
    )
    return "-".join(name_parts)


def _start_managed_target(
    runtime: CommandRuntime,
    *,
    runtime_executable: str,
    options: DastScanOptions,
) -> ManagedDastDeployment:
    """Build and start the isolated full-app container used as the ZAP target.

    The application container is never published to a host port. ZAP reaches it only through a
    unique private container network, preventing unrelated host development servers from being
    crawled accidentally.

    Parameters
    ----------
    runtime:
        Developer CLI runtime used to execute and log container commands.
    runtime_executable:
        Resolved Docker or Podman executable.
    options:
        Scan settings used to create traceable resource names.

    """
    dockerfile_path = (runtime.repo_root / MANAGED_TARGET_DOCKERFILE).resolve()
    if not dockerfile_path.is_file():
        raise FileNotFoundError(f"DAST target Dockerfile was not found: {dockerfile_path}")

    runtime.info(f"DEBUG: building isolated DAST target image={MANAGED_TARGET_IMAGE}")
    runtime.run(
        [
            runtime_executable,
            "build",
            "--file",
            str(dockerfile_path),
            "--tag",
            MANAGED_TARGET_IMAGE,
            str(runtime.repo_root),
        ],
        cwd=runtime.repo_root,
    )

    deployment = ManagedDastDeployment(
        network_name=_managed_resource_name(resource_kind="network", options=options),
        container_name=_managed_resource_name(resource_kind="target", options=options),
    )
    network_created = False
    container_started = False
    try:
        runtime.run([runtime_executable, "network", "create", deployment.network_name])
        network_created = True
        runtime.run(
            [
                runtime_executable,
                "run",
                "--detach",
                "--name",
                deployment.container_name,
                "--network",
                deployment.network_name,
                "--network-alias",
                MANAGED_TARGET_NETWORK_ALIAS,
                "--label",
                MANAGED_IMAGE_LABEL,
                MANAGED_TARGET_IMAGE,
            ]
        )
        container_started = True
        _wait_for_managed_target(
            runtime,
            runtime_executable=runtime_executable,
            deployment=deployment,
        )
    except Exception:
        if container_started:
            runtime.run(
                [runtime_executable, "container", "rm", "--force", deployment.container_name],
                check=False,
            )
        if network_created:
            runtime.run(
                [runtime_executable, "network", "rm", deployment.network_name],
                check=False,
            )
        raise
    return deployment


def _wait_for_managed_target(
    runtime: CommandRuntime,
    *,
    runtime_executable: str,
    deployment: ManagedDastDeployment,
) -> None:
    """Wait until the target image health check confirms the full app is ready.

    Parameters
    ----------
    runtime:
        Developer CLI runtime used to inspect the target container.
    runtime_executable:
        Resolved Docker or Podman executable.
    deployment:
        Managed deployment whose application container must become healthy.

    """
    deadline = time.monotonic() + DEFAULT_TARGET_READY_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        completed = runtime.run(
            [
                runtime_executable,
                "inspect",
                "--format",
                CONTAINER_HEALTH_STATUS_FORMAT,
                deployment.container_name,
            ],
            check=False,
            capture_output=True,
        )
        status = (completed.stdout or "").strip().lower()
        runtime.info(f"DEBUG: isolated DAST target status={status or 'unknown'}")
        if status == MANAGED_TARGET_STATUS_HEALTHY:
            return
        if status in MANAGED_TARGET_TERMINAL_STATUSES:
            break
        time.sleep(MANAGED_TARGET_STATUS_POLL_SECONDS)

    logs = runtime.run(
        [runtime_executable, "container", "logs", deployment.container_name],
        check=False,
        capture_output=True,
    )
    combined_logs = "\n".join(
        value.strip() for value in (logs.stdout or "", logs.stderr or "") if value.strip()
    )
    raise RuntimeError(
        "Isolated DAST target did not become healthy"
        + (f":\n{combined_logs}" if combined_logs else "")
    )


def _stop_managed_target(
    runtime: CommandRuntime,
    *,
    runtime_executable: str,
    deployment: ManagedDastDeployment,
) -> None:
    """Remove the isolated application container and its private network.

    Parameters
    ----------
    runtime:
        Developer CLI runtime used to execute best-effort cleanup commands.
    runtime_executable:
        Resolved Docker or Podman executable.
    deployment:
        Managed resources created for the completed or failed scan.

    """
    runtime.info(f"DEBUG: removing isolated DAST target={deployment.container_name}")
    runtime.run(
        [runtime_executable, "container", "rm", "--force", deployment.container_name],
        check=False,
    )
    runtime.run(
        [runtime_executable, "network", "rm", deployment.network_name],
        check=False,
    )


def _copy_rules_file(
    runtime: CommandRuntime,
    *,
    source_path: Path | None,
    report_directory: Path,
) -> Path | None:
    """Copy an optional rule policy into the container-writable report workspace.

    Parameters
    ----------
    runtime:
        Runtime whose repository root resolves relative policy paths.
    source_path:
        Optional absolute or repository-relative rule configuration path.
    report_directory:
        Host directory mounted as the ZAP working directory.

    """
    if source_path is None:
        return None
    resolved_source = source_path
    if not resolved_source.is_absolute():
        resolved_source = runtime.repo_root / resolved_source
    resolved_source = resolved_source.resolve()
    if not resolved_source.is_file():
        raise FileNotFoundError(f"ZAP rules file was not found: {resolved_source}")
    copied_rules_path = report_directory / RULES_COPY_FILE_NAME
    if resolved_source != copied_rules_path.resolve():
        shutil.copyfile(resolved_source, copied_rules_path)
    return copied_rules_path


def _copy_scan_hook(*, report_directory: Path) -> Path:
    """Copy the packaged false-positive filter into the mounted ZAP workspace.

    ZAP's packaged scans load hook files from the mounted working directory. Copying the hook
    beside the reports works for source and installed-wheel executions on Windows and Linux.

    Parameters:
        report_directory: Host directory mounted as the ZAP working directory.

    Returns:
        Path to the copied scan hook inside the report workspace.

    Raises:
        FileNotFoundError: If the installed developer-tools package omits the hook module.
    """
    if not SCAN_HOOK_SOURCE_PATH.is_file():
        raise FileNotFoundError(f"Packaged ZAP scan hook was not found: {SCAN_HOOK_SOURCE_PATH}")
    copied_hook_path = report_directory / SCAN_HOOK_COPY_FILE_NAME
    shutil.copyfile(SCAN_HOOK_SOURCE_PATH, copied_hook_path)
    return copied_hook_path


# The packaged scan has distinct policy, workspace, hook, and network inputs that remain clearer
# as named keyword-only arguments than as an opaque transport context object.
# pylint: disable-next=too-many-arguments
def _build_zap_command(
    *,
    runtime_executable: str,
    report_directory: Path,
    options: DastScanOptions,
    copied_rules_file: Path | None,
    copied_scan_hook: Path,
    network_name: str | None = None,
) -> list[str]:
    """Build a shell-independent Docker or Podman argument vector for ZAP.

    Parameters
    ----------
    runtime_executable:
        Resolved container runtime executable path.
    report_directory:
        Absolute host report directory mounted into the ZAP container.
    options:
        Validated scan settings rendered as packaged-scan arguments.
    copied_rules_file:
        Optional policy copy located inside the mounted report workspace.
    copied_scan_hook:
        False-positive filter hook located inside the mounted report workspace.
    network_name:
        Optional private application network joined by the ZAP container.

    """
    command = [runtime_executable, "run", "--rm"]
    if network_name is not None:
        command.extend(["--network", network_name])
    runtime_name = Path(runtime_executable).name.lower()
    target_hostname = urlparse(options.target).hostname
    if runtime_name in DOCKER_RUNTIME_NAMES and target_hostname == DOCKER_HOST_ALIAS:
        command.extend(["--add-host", DOCKER_HOST_GATEWAY_MAPPING])
    volume_source = report_directory.resolve().as_posix()
    command.extend(
        [
            "--volume",
            f"{volume_source}:{ZAP_CONTAINER_WORK_DIRECTORY}:{ZAP_WORK_VOLUME_MODE}",
            options.image,
            SCAN_SCRIPT_BY_MODE[options.mode],
            f"--hook={copied_scan_hook.name}",
            "-t",
            options.target,
            "-m",
            str(options.spider_minutes),
            "-T",
            str(options.startup_timeout_minutes),
            "-d",
            "-r",
            HTML_REPORT_FILE_NAME,
            "-J",
            JSON_REPORT_FILE_NAME,
            "-x",
            XML_REPORT_FILE_NAME,
            "-w",
            MARKDOWN_REPORT_FILE_NAME,
        ]
    )
    if not options.fail_on_warning:
        command.append("-I")
    if copied_rules_file is not None:
        command.extend(["-c", copied_rules_file.name])
    if options.generate_rules:
        command.extend(["-g", RULES_GENERATED_FILE_NAME])
    return command
