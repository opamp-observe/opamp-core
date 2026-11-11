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
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .container_images import resolve_container_runtime
from .runtime import CommandRuntime

BASELINE_MODE = "baseline"
FULL_MODE = "full"
DAST_SCAN_MODES = (BASELINE_MODE, FULL_MODE)
DEFAULT_DAST_SCOPE = "provider"
DEFAULT_DAST_TARGET = "http://host.docker.internal:8080"
DEFAULT_SPIDER_MINUTES = 2
DEFAULT_STARTUP_TIMEOUT_MINUTES = 5
DEFAULT_ZAP_IMAGE = (
    "ghcr.io/zaproxy/zaproxy:2.17.0"
    "@sha256:9624669db72f54d86c4b46a7064518bd9bf79d8c61a4c31befa9923489f328af"
)
DOCKER_HOST_ALIAS = "host.docker.internal"
DOCKER_HOST_GATEWAY_MAPPING = f"{DOCKER_HOST_ALIAS}:host-gateway"
DOCKER_RUNTIME_NAMES = frozenset({"docker", "docker.exe"})
HTML_REPORT_FILE_NAME = "zap_report.html"
JSON_REPORT_FILE_NAME = "zap_report.json"
MARKDOWN_REPORT_FILE_NAME = "zap_report.md"
RULES_COPY_FILE_NAME = "zap_rules.conf"
RULES_GENERATED_FILE_NAME = "zap_generated_rules.conf"
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
    command = _build_zap_command(
        runtime_executable=runtime_executable,
        report_directory=report_directory,
        options=options,
        copied_rules_file=copied_rules_file,
    )
    runtime.info(f"DEBUG: OWASP ZAP mode={options.mode} target={options.target}")
    runtime.info(f"DEBUG: OWASP ZAP reports={report_directory}")
    runtime.run(command, cwd=runtime.repo_root)
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


def _build_zap_command(
    *,
    runtime_executable: str,
    report_directory: Path,
    options: DastScanOptions,
    copied_rules_file: Path | None,
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

    """
    command = [runtime_executable, "run", "--rm"]
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
