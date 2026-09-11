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

"""Elastic Agent observer consumer using Elastic Agent CLI and monitoring API."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time
import tracemalloc
from typing import Any, cast
from urllib.parse import urlencode, urlsplit

import httpx
import yaml

from opamp_consumer import config as consumer_config
from opamp_consumer.abstract_client import (
    KEY_HEALTH,
    KEY_SERVICE_TYPE,
    LOCALHOST_BASE,
    AbstractOpAMPClient,
    _config_parameters_payload,
)
from opamp_consumer.client_bootstrap import (
    build_common_cli_parser,
    configure_logging_for_config,
    configure_observability_for_config,
    load_config_from_cli_args,
    log_runtime_config_path,
    maybe_print_cli_config,
    maybe_print_config_help,
    run_client,
    validate_runtime_server_config,
)
from opamp_consumer.client_observer_mixin import ClientObserverMixin
from opamp_consumer.client_runtime_mixin import (
    PROCESS_TRACKING_OBSERVER,
    _BaseClientProcessLifecycle,
    _normalize_process_tracking,
)
from opamp_consumer.config import CFG_AGENT_CONFIG_PATH, ConsumerConfig
from opamp_consumer.config_metadata import ConfigMetadata
from opamp_consumer.exceptions import AgentException
from opamp_consumer.plugin_config import (
    ConsumerPluginConfigContext,
    resolve_optional_path_from_config,
)
from opamp_consumer.process_utils import ProcessUtils
from opamp_consumer.proto import opamp_pb2
from opamp_consumer.reporting_flag import ReportingFlag
from opamp_consumer.startup_banner import log_consumer_startup_banner

VALUE_AGENT_TYPE_ELASTIC_AGENT = "Elastic Agent"
ELASTIC_AGENT_CONFIG_FLAG = "-c"
ELASTIC_AGENT_RUN_COMMAND = "run"
ELASTIC_AGENT_RESTART_COMMAND = "restart"
ELASTIC_AGENT_STATUS_COMMAND = "status"
ELASTIC_AGENT_OUTPUT_FLAG = "--output"
ELASTIC_AGENT_OUTPUT_JSON = "json"
ELASTIC_AGENT_DEFAULT_EXECUTABLE = "elastic-agent"
ELASTIC_AGENT_LIVENESS_PATH = "/liveness"
ELASTIC_AGENT_STATUS_PAYLOAD_KEY = "status"
ELASTIC_AGENT_COMPONENTS_PAYLOAD_KEY = "components"
ELASTIC_AGENT_MESSAGE_PAYLOAD_KEY = "message"
ELASTIC_AGENT_NAME_PAYLOAD_KEY = "name"
ELASTIC_AGENT_ID_PAYLOAD_KEY = "id"
ELASTIC_AGENT_VERSION_PAYLOAD_KEY = "version"
ELASTIC_AGENT_INFO_PAYLOAD_KEY = "info"
ELASTIC_AGENT_STATE_PAYLOAD_KEY = "state"
ELASTIC_AGENT_API_PAYLOAD_KEY = "api"
ELASTIC_AGENT_CLI_PAYLOAD_KEY = "cli_status"
ELASTIC_AGENT_CLI_ERROR_PAYLOAD_KEY = "cli_status_error"
ELASTIC_AGENT_LIVENESS_KEY = "liveness"
ELASTIC_AGENT_HTTP_CODE_KEY = "http_code"
ELASTIC_AGENT_HEALTHY_STATES = {"healthy", "online", "running", "ok"}
ELASTIC_AGENT_DEGRADED_STATES = {"degraded", "warning"}
ELASTIC_AGENT_UNHEALTHY_STATES = {"failed", "error", "stopped", "offline"}
ELASTIC_AGENT_STATE_NAMES = {
    0: "starting",
    1: "configuring",
    2: "healthy",
    3: "degraded",
    4: "failed",
    5: "stopping",
    6: "stopped",
}
DEFAULT_STOP_WAIT_SECONDS = 5.0
CFG_ELASTIC_AGENT_EXECUTABLE_PATH = "executable_path"
CFG_ELASTIC_AGENT_HOME_PATH = "home_path"
CFG_ELASTIC_AGENT_API_HOST = "api_host"
CFG_ELASTIC_AGENT_API_PORT = "api_port"
CFG_ELASTIC_AGENT_API_FAILON = "api_failon"
CFG_ELASTIC_AGENT_STATUS_TIMEOUT_SECONDS = "status_timeout_seconds"
ENV_ELASTIC_AGENT_EXECUTABLE_PATH = "OPAMP_ELASTIC_AGENT_EXECUTABLE_PATH"
ENV_ELASTIC_AGENT_HOME_PATH = "OPAMP_ELASTIC_AGENT_HOME_PATH"
ENV_ELASTIC_AGENT_API_HOST = "OPAMP_ELASTIC_AGENT_API_HOST"
ENV_ELASTIC_AGENT_API_PORT = "OPAMP_ELASTIC_AGENT_API_PORT"
ENV_ELASTIC_AGENT_API_FAILON = "OPAMP_ELASTIC_AGENT_API_FAILON"
DEFAULT_ELASTIC_AGENT_API_HOST = "localhost"
DEFAULT_ELASTIC_AGENT_API_PORT = 6791
DEFAULT_ELASTIC_AGENT_API_FAILON = "degraded"
DEFAULT_ELASTIC_AGENT_STATUS_TIMEOUT_SECONDS = 5.0
DEFAULT_ELASTIC_AGENT_STATUS_READY_ATTEMPTS = 3
DEFAULT_ELASTIC_AGENT_STATUS_READY_RETRY_SECONDS = 0.5
DEFAULT_LOGSTASH_CONNECT_TIMEOUT_SECONDS = 1.0
_ELASTIC_ENV_PROVIDER_REF = re.compile(r"\$\{(?P<body>env\.[^}]+)\}")


def _windows_no_console_kwargs() -> dict[str, Any]:
    """Return subprocess kwargs that suppress transient console windows on Windows."""
    if sys.platform != "win32":
        return {}
    creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if creationflags <= 0:
        return {}
    return {"creationflags": creationflags}


def _command_for_log(command: list[str]) -> str:
    """Return a readable shell-style command string for diagnostics."""
    return shlex.join(str(part) for part in command)


def _compact_output_for_log(text: str, *, limit: int = 500) -> str:
    """Return single-line process output suitable for exception messages."""
    compact_text = " ".join(str(text or "").strip().split())
    if len(compact_text) <= limit:
        return compact_text
    return f"{compact_text[:limit]}..."


def _status_payload_from_json_text(text: str) -> dict[str, Any]:
    """Parse Elastic Agent status JSON text into an object payload."""
    payload = json.loads(text or "{}")
    if not isinstance(payload, dict):
        raise AgentException("Elastic Agent status output was not a JSON object")
    return payload


def _version_from_status_payload(payload: dict[str, Any]) -> str | None:
    """Return Elastic Agent version from known status payload shapes."""
    version_value = payload.get(ELASTIC_AGENT_VERSION_PAYLOAD_KEY)
    info_payload = payload.get(ELASTIC_AGENT_INFO_PAYLOAD_KEY)
    if version_value is None and isinstance(info_payload, dict):
        version_value = info_payload.get(ELASTIC_AGENT_VERSION_PAYLOAD_KEY)
    if version_value:
        return str(version_value)
    return None


def _status_text_from_payload(payload: dict[str, Any]) -> str:
    """Return a readable status string from Elastic Agent status payload fields."""
    status_value = payload.get(ELASTIC_AGENT_STATUS_PAYLOAD_KEY)
    if status_value:
        return str(status_value)
    state_value = payload.get(ELASTIC_AGENT_STATE_PAYLOAD_KEY)
    if isinstance(state_value, int):
        return ELASTIC_AGENT_STATE_NAMES.get(state_value, str(state_value))
    if state_value is not None:
        return str(state_value)
    return "unknown"


def _resolve_elastic_env_provider_refs(value: str) -> str:
    """Resolve Elastic Agent `${env.NAME|'fallback'}` references for probes."""

    def resolve_match(match: re.Match[str]) -> str:
        parts = [part.strip() for part in match.group("body").split("|")]
        for part in parts:
            if part.startswith("env."):
                resolved = os.environ.get(part[4:])
                if resolved:
                    return resolved
                continue
            if len(part) >= 2 and part[0] == part[-1] and part[0] in {"'", '"'}:
                return part[1:-1]
            if part:
                return part
        return ""

    return _ELASTIC_ENV_PROVIDER_REF.sub(resolve_match, value)


def _resolve_optional_executable_from_config(
    *,
    raw_value: Any,
    config_path: pathlib.Path,
) -> str | None:
    """Resolve an executable value that may be a PATH command or a filesystem path."""
    normalized_value = str(raw_value).strip() if raw_value is not None else ""
    if not normalized_value:
        return None
    if (
        "/" not in normalized_value
        and "\\" not in normalized_value
        and not normalized_value.startswith((".", "~"))
        and not pathlib.PureWindowsPath(normalized_value).drive
    ):
        return normalized_value
    if pathlib.PureWindowsPath(normalized_value).is_absolute():
        return normalized_value
    return resolve_optional_path_from_config(
        raw_value=normalized_value,
        config_path=config_path,
    )


def _looks_like_executable_path(value: str) -> bool:
    """Return whether an executable value is path-like rather than a PATH command."""
    return (
        "/" in value
        or "\\" in value
        or value.startswith((".", "~"))
        or bool(pathlib.PureWindowsPath(value).drive)
    )


def process_consumer_config(
    context: ConsumerPluginConfigContext,
) -> dict[str, Any]:
    """Resolve Elastic Agent consumer config block into ConsumerConfig fields."""
    elastic_agent_raw = context.raw_section
    executable_path = os.environ.get(
        ENV_ELASTIC_AGENT_EXECUTABLE_PATH,
        elastic_agent_raw.get(CFG_ELASTIC_AGENT_EXECUTABLE_PATH),
    )
    home_path = os.environ.get(
        ENV_ELASTIC_AGENT_HOME_PATH,
        elastic_agent_raw.get(CFG_ELASTIC_AGENT_HOME_PATH),
    )
    api_host = os.environ.get(
        ENV_ELASTIC_AGENT_API_HOST,
        elastic_agent_raw.get(
            CFG_ELASTIC_AGENT_API_HOST,
            DEFAULT_ELASTIC_AGENT_API_HOST,
        ),
    )
    api_port = os.environ.get(
        ENV_ELASTIC_AGENT_API_PORT,
        elastic_agent_raw.get(
            CFG_ELASTIC_AGENT_API_PORT,
            DEFAULT_ELASTIC_AGENT_API_PORT,
        ),
    )
    resolved_api_port = (
        api_port if api_port is not None else DEFAULT_ELASTIC_AGENT_API_PORT
    )
    api_failon = os.environ.get(
        ENV_ELASTIC_AGENT_API_FAILON,
        elastic_agent_raw.get(
            CFG_ELASTIC_AGENT_API_FAILON,
            DEFAULT_ELASTIC_AGENT_API_FAILON,
        ),
    )
    timeout_seconds = elastic_agent_raw.get(
        CFG_ELASTIC_AGENT_STATUS_TIMEOUT_SECONDS,
        DEFAULT_ELASTIC_AGENT_STATUS_TIMEOUT_SECONDS,
    )
    return {
        "elastic_agent_executable_path": _resolve_optional_executable_from_config(
            raw_value=executable_path,
            config_path=context.config_path,
        ),
        "elastic_agent_home_path": resolve_optional_path_from_config(
            raw_value=home_path,
            config_path=context.config_path,
        ),
        "elastic_agent_api_host": str(api_host or DEFAULT_ELASTIC_AGENT_API_HOST),
        "elastic_agent_api_port": int(resolved_api_port),
        "elastic_agent_api_failon": str(
            api_failon or DEFAULT_ELASTIC_AGENT_API_FAILON
        ),
        "elastic_agent_status_timeout_seconds": float(timeout_seconds),
    }


def _host_token(host: str) -> str:
    """Return a URL-safe host token, bracketing IPv6 literals when required.

    Args:
        host: Configured host value.

    Returns:
        Host token suitable for embedding in an HTTP URL.
    """
    normalized_host = str(host or "localhost").strip() or "localhost"
    if ":" in normalized_host and not normalized_host.startswith("["):
        return f"[{normalized_host}]"
    return normalized_host


def _coerce_string_list(value: Any) -> list[str]:
    """Return config scalar/list values as a list of non-empty strings."""
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    normalized_value = str(value or "").strip()
    return [normalized_value] if normalized_value else []


def _logstash_hosts_from_agent_config(config_text: str) -> list[str]:
    """Extract Logstash output hosts from Elastic Agent YAML text."""
    loaded = yaml.safe_load(config_text) or {}
    if not isinstance(loaded, dict):
        return []
    outputs = loaded.get("outputs", {})
    if not isinstance(outputs, dict):
        return []

    hosts: list[str] = []
    for output in outputs.values():
        if not isinstance(output, dict):
            continue
        output_type = str(output.get("type") or "").strip().lower()
        if output_type != "logstash":
            continue
        hosts.extend(
            _resolve_elastic_env_provider_refs(host)
            for host in _coerce_string_list(output.get("hosts"))
        )
    return hosts


def _split_host_port(endpoint: str) -> tuple[str, int] | None:
    """Parse a Logstash host endpoint into host and port parts."""
    normalized_endpoint = endpoint.strip()
    if not normalized_endpoint:
        return None
    parsed = urlsplit(
        normalized_endpoint
        if "://" in normalized_endpoint
        else f"tcp://{normalized_endpoint}"
    )
    if parsed.hostname is None or parsed.port is None:
        return None
    return parsed.hostname, int(parsed.port)


def _host_looks_like_interface_name(host: str) -> bool:
    """Return whether a host value looks like a network interface name."""
    return bool(re.fullmatch(r"(?:eth|ens|enp|wlan|lo)\d*", host.strip().lower()))


class ElasticAgentCliLifecycle(_BaseClientProcessLifecycle):
    """Process lifecycle strategy that controls Elastic Agent through its CLI.

    The `run` command starts a foreground agent process for local/dev
    deployments. `restart` is delegated to the Elastic Agent CLI when possible;
    if the CLI cannot restart an unattached development process, the lifecycle
    falls back to stop/start using the tracked pid.
    """

    def _configured_executable(self) -> str:
        """Return the configured Elastic Agent executable command or path."""
        return str(
            self._owner.config.elastic_agent_executable_path
            or ELASTIC_AGENT_DEFAULT_EXECUTABLE
        )

    def _elastic_command(self, *args: str) -> list[str]:
        """Build an Elastic Agent CLI command.

        Args:
            *args: Command arguments to append after the executable.

        Returns:
            Command list for `subprocess`.
        """
        executable_path = self._configured_executable()
        return [self._resolve_executable_for_subprocess(executable_path), *args]

    def _working_directory(self) -> str | None:
        """Return configured Elastic Agent CLI working directory."""
        return self._owner.config.elastic_agent_home_path

    def _executable_lookup_path(self) -> str | None:
        """Return PATH text including the configured Elastic Agent home path."""
        path_parts: list[str] = []
        cwd = self._working_directory()
        if cwd:
            path_parts.append(str(cwd))
        env_path = os.environ.get("PATH")
        if env_path:
            path_parts.append(env_path)
        return os.pathsep.join(path_parts) if path_parts else None

    def _resolve_executable_for_subprocess(self, executable_path: str) -> str:
        """Resolve bare executable names before passing them to subprocess."""
        if _looks_like_executable_path(executable_path):
            return executable_path
        lookup_path = self._executable_lookup_path()
        resolved_path = shutil.which(executable_path, path=lookup_path)
        if not resolved_path:
            logging.getLogger(__name__).warning(
                "Elastic Agent executable not found in lookup path: %s cwd=%s",
                executable_path,
                self._working_directory(),
            )
            return executable_path
        if resolved_path != executable_path:
            logging.getLogger(__name__).info(
                "Elastic Agent executable resolved: %s -> %s",
                executable_path,
                resolved_path,
            )
        return resolved_path

    def _log_subprocess_error(
        self,
        *,
        logger: logging.Logger,
        action: str,
        error: BaseException,
        command: list[str],
        cwd: str | None,
        timeout_seconds: float | None = None,
        exc_info: bool = False,
    ) -> None:
        """Log subprocess failure diagnostics in a consistent shape."""
        logger.error(
            (
                "Elastic Agent %s failed: %s "
                "commandline=%s argv=%s cwd=%s configured_executable=%s "
                "lookup_path=%s process_cwd=%s path=%s timeout=%s"
            ),
            action,
            error,
            _command_for_log(command),
            command,
            cwd,
            self._configured_executable(),
            self._executable_lookup_path(),
            pathlib.Path.cwd(),
            os.environ.get("PATH", ""),
            timeout_seconds,
            exc_info=exc_info,
        )

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run a short Elastic Agent CLI command and capture text output.

        Args:
            *args: CLI arguments following the executable.

        Returns:
            Completed process containing stdout/stderr for parsing or logging.
        """
        timeout_seconds = float(
            self._owner.config.elastic_agent_status_timeout_seconds
        )
        command = self._elastic_command(*args)
        cwd = self._working_directory()
        logging.getLogger(__name__).info(
            "Elastic Agent CLI command: %s cwd=%s timeout=%s",
            _command_for_log(command),
            cwd,
            timeout_seconds,
        )
        try:
            # The executable and working directory are operator-supplied config,
            # while command verbs/flags are fixed constants from the Elastic CLI.
            return subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
                **_windows_no_console_kwargs(),
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as run_error:
            self._log_subprocess_error(
                logger=logging.getLogger(__name__),
                action="CLI command",
                error=run_error,
                command=command,
                cwd=cwd,
                timeout_seconds=timeout_seconds,
            )
            raise

    def _resolve_pid(self) -> int | None:
        """Resolve the tracked Elastic Agent pid from cache or regex discovery."""
        cached_pid = self._owner.data.observed_process_pid
        if cached_pid and ProcessUtils.is_process_running(cached_pid):
            return cached_pid

        regex = str(self._owner.config.process_detection_regex or "").strip()
        if not regex:
            return None
        pid = ProcessUtils.find_pid_by_regex(regex)
        self._owner.data.observed_process_pid = pid
        return pid

    def _configured_logstash_hosts(self) -> list[str]:
        """Return Logstash output hosts declared in the Elastic Agent config."""
        config_text = str(self._owner.config.agent_config_text or "")
        if not config_text:
            config_path = str(self._owner.config.agent_config_path or "").strip()
            if not config_path:
                return []
            path = pathlib.Path(config_path)
            if not path.exists():
                return []
            config_text = path.read_text(encoding=consumer_config.UTF8_ENCODING)
        try:
            return _logstash_hosts_from_agent_config(config_text)
        except Exception as config_error:
            logging.getLogger(__name__).warning(
                "Elastic Agent Logstash output probe skipped; failed to parse %s: %s",
                self._owner.config.agent_config_path,
                config_error,
            )
            return []

    def _probe_logstash_host(self, endpoint: str) -> tuple[bool, str]:
        """Return whether a configured Logstash host accepts TCP connections."""
        host_port = _split_host_port(endpoint)
        if host_port is None:
            return False, "endpoint is not a host:port value"
        host, port = host_port
        if _host_looks_like_interface_name(host):
            return (
                False,
                f"{host} looks like an interface name, not an IP address or hostname",
            )
        timeout_seconds = min(
            float(self._owner.config.elastic_agent_status_timeout_seconds),
            DEFAULT_LOGSTASH_CONNECT_TIMEOUT_SECONDS,
        )
        try:
            with socket.create_connection((host, port), timeout=timeout_seconds):
                return True, "reachable"
        except OSError as connect_error:
            return False, str(connect_error)

    def _log_logstash_output_readiness(self) -> bool:
        """Log configured Logstash output readiness before launching Elastic Agent."""
        logger = logging.getLogger(__name__)
        hosts = self._configured_logstash_hosts()
        if not hosts:
            logger.info(
                "Elastic Agent Logstash output probe skipped; no logstash outputs found"
            )
            return True

        logger.info(
            "Elastic Agent launch step: probing %s configured Logstash output endpoint(s)",
            len(hosts),
        )
        all_ready = True
        for endpoint in hosts:
            ready, detail = self._probe_logstash_host(endpoint)
            if ready:
                logger.info(
                    "Elastic Agent Logstash output endpoint reachable: %s",
                    endpoint,
                )
                continue
            all_ready = False
            logger.error(
                "Elastic Agent Logstash output endpoint unreachable: %s error=%s",
                endpoint,
                detail,
            )
        return all_ready

    def launch_agent_process(self) -> bool:
        """Start Elastic Agent with `elastic-agent run -c <config>`."""
        logger = logging.getLogger(__name__)
        logger.info("Elastic Agent launch step: preparing supervisor launch")
        config_path = str(self._owner.config.agent_config_path or "").strip()
        if not config_path:
            logger.error("%s is required for Elastic Agent launch", CFG_AGENT_CONFIG_PATH)
            return False
        if not self._log_logstash_output_readiness():
            logger.error(
                "Elastic Agent launch skipped because one or more configured "
                "Logstash endpoints are unreachable"
            )
            return False
        command = self._elastic_command(
            ELASTIC_AGENT_RUN_COMMAND,
            ELASTIC_AGENT_CONFIG_FLAG,
            config_path,
            *(self._owner.config.agent_additional_params or []),
        )
        logger.info(
            "Elastic Agent launch command: %s cwd=%s",
            _command_for_log(command),
            self._working_directory(),
        )
        try:
            with self._owner.data.process_lock:
                logger.info("Elastic Agent launch step: spawning Elastic Agent process")
                # The executable and config path are explicit operator config;
                # shell execution is not used.
                process = cast(
                    "subprocess.Popen[bytes]",
                    subprocess.Popen(  # noqa: S603
                        command,
                        cwd=self._working_directory(),
                        **_windows_no_console_kwargs(),
                    ),
                )
                self._owner.data.agent_process = process
                self._owner.data.observed_process_pid = process.pid
                self._owner.data.launched_at = time.time_ns()
                self._owner.data.allow_heartbeat = True
                logger.info(
                    "Elastic Agent launch step: process recorded pid=%s",
                    process.pid,
                )
        except FileNotFoundError as file_error:
            self._log_subprocess_error(
                logger=logger,
                action="launch",
                error=file_error,
                command=command,
                cwd=self._working_directory(),
            )
            return False
        except Exception as launch_error:  # pragma: no cover - env-dependent path
            self._log_subprocess_error(
                logger=logger,
                action="launch",
                error=launch_error,
                command=command,
                cwd=self._working_directory(),
                exc_info=True,
            )
            return False
        logger.info("Elastic Agent launched with pid=%s", self._owner.data.observed_process_pid)
        return True

    def terminate_agent_process(self) -> None:
        """Stop the tracked Elastic Agent development process gracefully."""
        logger = logging.getLogger(__name__)
        self._owner.data.allow_heartbeat = False
        process = self._owner.data.agent_process
        if process is not None:
            logger.info("Elastic Agent terminate process pid=%s", process.pid)
            process.terminate()
            try:
                process.wait(timeout=DEFAULT_STOP_WAIT_SECONDS)
            except subprocess.TimeoutExpired:
                logger.warning("Elastic Agent did not stop in time; killing process")
                logger.info("Elastic Agent kill process pid=%s", process.pid)
                process.kill()
                process.wait(timeout=DEFAULT_STOP_WAIT_SECONDS)
            self._owner.data.agent_process = None
            self._owner.data.observed_process_pid = None
            return

        pid = self._resolve_pid()
        if pid is None:
            logger.info("Elastic Agent stop skipped; no matching process found")
            return
        if ProcessUtils.can_send_signal():
            logger.info("Elastic Agent send termination signal pid=%s", pid)
            ProcessUtils.send_termination_signal(pid)
            time.sleep(1.0)
        if ProcessUtils.is_process_running(pid):
            logger.info("Elastic Agent terminate discovered process pid=%s", pid)
            ProcessUtils.terminate_process(pid)
        if ProcessUtils.is_process_running(pid):
            logger.info("Elastic Agent kill discovered process pid=%s", pid)
            ProcessUtils.kill_process(pid)
        if not ProcessUtils.is_process_running(pid):
            self._owner.data.observed_process_pid = None

    def restart_agent_process(self) -> bool:
        """Restart Elastic Agent through CLI, falling back to stop/start."""
        logger = logging.getLogger(__name__)
        lock_acquired = self._owner.data.process_lock.acquire(timeout=30)
        if not lock_acquired:
            raise AgentException(
                "Timed out waiting for process lock while restarting Elastic Agent"
            )
        try:
            restart_result = self._run_cli(ELASTIC_AGENT_RESTART_COMMAND)
            if restart_result.returncode == 0:
                logger.info("Elastic Agent CLI restart completed")
                return True
            logger.warning(
                "Elastic Agent CLI restart failed rc=%s stderr=%s",
                restart_result.returncode,
                restart_result.stderr,
            )
            self.terminate_agent_process()
            relaunched = self.launch_agent_process()
        finally:
            self._owner.data.process_lock.release()
        if not relaunched:
            raise AgentException("Failed to restart Elastic Agent")
        return relaunched

    def status_json(self) -> dict[str, Any]:
        """Return `elastic-agent status --output json` as a dictionary."""
        result = self._run_cli(
            ELASTIC_AGENT_STATUS_COMMAND,
            ELASTIC_AGENT_OUTPUT_FLAG,
            ELASTIC_AGENT_OUTPUT_JSON,
        )
        try:
            payload = _status_payload_from_json_text(result.stdout)
        except Exception:
            if result.returncode == 0:
                raise
            raise AgentException(
                "Elastic Agent status failed "
                f"rc={result.returncode} "
                f"stderr={_compact_output_for_log(result.stderr)} "
                f"stdout={_compact_output_for_log(result.stdout)}"
            )
        if result.returncode != 0:
            logging.getLogger(__name__).warning(
                "Elastic Agent status returned rc=%s with JSON payload; "
                "preserving status payload stderr=%s message=%s",
                result.returncode,
                _compact_output_for_log(result.stderr),
                _compact_output_for_log(
                    str(payload.get(ELASTIC_AGENT_MESSAGE_PAYLOAD_KEY) or "")
                ),
            )
        return payload


class ElasticAgentOpAMPClient(AbstractOpAMPClient):
    """Concrete OpAMP observer implementation for Elastic Agent.

    This client controls Elastic Agent through the Elastic Agent CLI and uses
    the monitoring HTTP liveness endpoint for local API status checks.
    """

    _runtime_agent_command = ELASTIC_AGENT_DEFAULT_EXECUTABLE
    _runtime_config_flag = ELASTIC_AGENT_CONFIG_FLAG
    _heartbeat_paths = (ELASTIC_AGENT_LIVENESS_PATH,)
    _value_agent_type = VALUE_AGENT_TYPE_ELASTIC_AGENT
    _elastic_cli_lifecycle: ElasticAgentCliLifecycle | None = None
    SUPPORTED_AGENT_CAPABILITY_NAMES = (
        *consumer_config.MANDATORY_AGENT_CAPABILITY_NAMES,
        "AcceptsRemoteConfig",
        "ReportsEffectiveConfig",
        "ReportsHeartbeat",
    )

    def __init__(self, base_url: str, config: ConsumerConfig | None = None) -> None:
        """Initialize Elastic Agent runtime defaults.

        Args:
            base_url: OpAMP provider URL.
            config: Consumer configuration for this client instance.
        """
        super().__init__(base_url, config)
        self.data.agent_type_name = VALUE_AGENT_TYPE_ELASTIC_AGENT

    def get_custom_handler_folder(self) -> pathlib.Path:
        """Return default custom handler folder for Elastic Agent commands."""
        return pathlib.Path(__file__).resolve().parent / "custom_handlers"

    def get_config_metadata(self) -> ConfigMetadata:
        """Return empty metadata because Elastic Agent YAML has no OpAMP comments."""
        return ConfigMetadata()

    def _create_runtime_process_lifecycle(
        self,
    ) -> _BaseClientProcessLifecycle:
        """Create process lifecycle honoring configured process tracking."""
        logger = logging.getLogger(__name__)
        tracking_mode = _normalize_process_tracking(
            getattr(self.config, "process_tracking", None)
        )
        logger.info(
            "Elastic Agent lifecycle step: process_tracking=%s",
            tracking_mode,
        )
        if tracking_mode == PROCESS_TRACKING_OBSERVER:
            logger.info("Elastic Agent lifecycle step: using observer attach strategy")
            return ClientObserverMixin(self)
        logger.info("Elastic Agent lifecycle step: using supervisor CLI strategy")
        return ElasticAgentCliLifecycle(self)

    def _elastic_cli(self) -> ElasticAgentCliLifecycle:
        """Return Elastic Agent CLI helper used for status/version commands."""
        logger = logging.getLogger(__name__)
        lifecycle = self._runtime_lifecycle()
        if isinstance(lifecycle, ElasticAgentCliLifecycle):
            logger.info("Elastic Agent status step: using runtime CLI lifecycle")
            return lifecycle
        if self._elastic_cli_lifecycle is None:
            logger.info("Elastic Agent status step: creating CLI helper for observer mode")
            self._elastic_cli_lifecycle = ElasticAgentCliLifecycle(self)
        return self._elastic_cli_lifecycle

    def _liveness_url(self, port: int) -> str:
        """Build Elastic Agent monitoring API liveness URL.

        Args:
            port: API port used for the liveness call.

        Returns:
            Fully qualified liveness URL including `failon`.
        """
        host = _host_token(self.config.elastic_agent_api_host)
        query = urlencode({"failon": self.config.elastic_agent_api_failon})
        return f"http://{host}:{int(port)}{ELASTIC_AGENT_LIVENESS_PATH}?{query}"

    def _read_liveness(self, port: int) -> dict[str, Any]:
        """Call the Elastic Agent monitoring HTTP API and return status details."""
        url = self._liveness_url(port)
        logging.getLogger(__name__).info(
            "Elastic Agent status step: polling liveness url=%s timeout=%s",
            url,
            float(self.config.elastic_agent_status_timeout_seconds),
        )
        response = httpx.get(
            url,
            timeout=float(self.config.elastic_agent_status_timeout_seconds),
        )
        logging.getLogger(__name__).info(
            "Elastic Agent status step: liveness response status_code=%s",
            response.status_code,
        )
        return {
            ELASTIC_AGENT_HTTP_CODE_KEY: response.status_code,
            ELASTIC_AGENT_STATUS_PAYLOAD_KEY: response.text.strip(),
            "url": url,
        }

    def _read_status_payload(self, port: int) -> dict[str, Any]:
        """Read Elastic Agent status from API and CLI into one JSON payload."""
        logger = logging.getLogger(__name__)
        logger.info(
            "Elastic Agent status step: collecting API and CLI status port=%s",
            port,
        )
        liveness = self._read_liveness(port)
        payload: dict[str, Any] = {
            ELASTIC_AGENT_API_PAYLOAD_KEY: {
                ELASTIC_AGENT_LIVENESS_KEY: liveness,
            },
        }
        try:
            payload[ELASTIC_AGENT_CLI_PAYLOAD_KEY] = self._elastic_cli().status_json()
        except Exception as status_error:  # pragma: no cover - runtime path
            payload[ELASTIC_AGENT_CLI_ERROR_PAYLOAD_KEY] = str(status_error)
            self.data.reporting_flags[ReportingFlag.REPORT_HEALTH] = True
            logger.warning(
                "Elastic Agent status step: CLI status unavailable; "
                "using liveness-only health payload: %s",
                status_error,
            )
        else:
            logger.info("Elastic Agent status step: collected API and CLI status")
        return payload

    def _status_json_when_ready(self) -> dict[str, Any]:
        """Read CLI status, retrying the brief startup control-socket race."""
        logger = logging.getLogger(__name__)
        last_error: Exception | None = None
        for attempt in range(1, DEFAULT_ELASTIC_AGENT_STATUS_READY_ATTEMPTS + 1):
            try:
                return self._elastic_cli().status_json()
            except Exception as status_error:  # pragma: no cover - runtime path
                last_error = status_error
                if attempt >= DEFAULT_ELASTIC_AGENT_STATUS_READY_ATTEMPTS:
                    break
                logger.info(
                    "Elastic Agent version step: CLI status not ready "
                    "attempt=%s/%s error=%s",
                    attempt,
                    DEFAULT_ELASTIC_AGENT_STATUS_READY_ATTEMPTS,
                    status_error,
                )
                time.sleep(DEFAULT_ELASTIC_AGENT_STATUS_READY_RETRY_SECONDS)
        if last_error is None:
            raise AgentException("Elastic Agent status was not attempted")
        raise last_error

    def add_agent_version(self, port: int) -> None:
        """Read Elastic Agent version from `status --output json`.

        Args:
            port: Local API port; retained for compatibility with shared
                heartbeat loop hooks.
        """
        del port
        logger = logging.getLogger(__name__)
        logger.info("Elastic Agent version step: reading version from CLI status")
        try:
            payload = self._status_json_when_ready()
        except Exception as status_error:  # pragma: no cover - runtime/network path
            logger.warning(
                "failed to read Elastic Agent version: %s",
                status_error,
            )
            return
        version_value = _version_from_status_payload(payload)
        if version_value:
            self.data.agent_version = version_value
            logger.info("Elastic Agent version step: detected version=%s", version_value)
        else:
            logger.info("Elastic Agent version step: CLI status did not include version")
        self.data.agent_type_name = VALUE_AGENT_TYPE_ELASTIC_AGENT

    def poll_local_status_with_codes(
        self, port: int
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Poll Elastic Agent liveness API and CLI status.

        Args:
            port: Elastic Agent monitoring HTTP API port.

        Returns:
            Tuple of heartbeat result and HTTP code maps.
        """
        results: dict[str, str] = {}
        codes: dict[str, str] = {}
        try:
            payload = self._read_status_payload(port)
            liveness = payload[ELASTIC_AGENT_API_PAYLOAD_KEY][
                ELASTIC_AGENT_LIVENESS_KEY
            ]
            status_code = int(liveness[ELASTIC_AGENT_HTTP_CODE_KEY])
            results[KEY_HEALTH] = json.dumps(payload, sort_keys=True)
            codes[KEY_HEALTH] = str(status_code)
            if (status_code < 200) or (status_code > 299):
                self.data.reporting_flags[ReportingFlag.REPORT_HEALTH] = True
        except Exception as status_error:  # pragma: no cover - runtime path
            results[KEY_HEALTH] = f"{self._error_prefix}{status_error}"
            codes[KEY_HEALTH] = self._error_status
            self.data.reporting_flags[ReportingFlag.REPORT_HEALTH] = True
            logging.getLogger(__name__).warning(
                "Elastic Agent status poll failed: %s",
                status_error,
            )
        return results, codes

    def _component_is_healthy(self, status_value: str) -> bool:
        """Return whether an Elastic status string is healthy enough for OpAMP."""
        normalized_status = status_value.strip().lower()
        if normalized_status in ELASTIC_AGENT_UNHEALTHY_STATES:
            return False
        if normalized_status in ELASTIC_AGENT_DEGRADED_STATES:
            return False
        return normalized_status in ELASTIC_AGENT_HEALTHY_STATES

    def _health_from_metrics(
        self,
        msg: opamp_pb2.AgentToServer,
        text: str,
    ) -> opamp_pb2.AgentToServer:
        """Transform Elastic Agent status JSON into OpAMP component health.

        Args:
            msg: AgentToServer message whose component map is updated.
            text: JSON text created from Elastic API and CLI status payloads.

        Returns:
            The same message with Elastic component health entries.
        """
        logger = logging.getLogger(__name__)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as json_error:
            logger.warning("failed to parse Elastic Agent status JSON: %s", json_error)
            return msg
        if not isinstance(payload, dict):
            return msg

        cli_status = payload.get(ELASTIC_AGENT_CLI_PAYLOAD_KEY)
        if not isinstance(cli_status, dict):
            return msg
        status_text = _status_text_from_payload(cli_status)
        status_message = str(
            cli_status.get(ELASTIC_AGENT_MESSAGE_PAYLOAD_KEY) or ""
        ).strip()
        status_payload = status_text
        if status_message:
            status_payload = f"{status_text}: {status_message}"
        msg.health.component_health_map[VALUE_AGENT_TYPE_ELASTIC_AGENT].CopyFrom(
            opamp_pb2.ComponentHealth(
                healthy=self._component_is_healthy(status_text),
                status=status_payload,
            )
        )

        components = cli_status.get(ELASTIC_AGENT_COMPONENTS_PAYLOAD_KEY, [])
        if not isinstance(components, list):
            return msg
        for component_index, component in enumerate(components):
            if not isinstance(component, dict):
                continue
            component_name = str(
                component.get(ELASTIC_AGENT_NAME_PAYLOAD_KEY)
                or component.get(ELASTIC_AGENT_ID_PAYLOAD_KEY)
                or f"component_{component_index}"
            )
            component_status = _status_text_from_payload(component)
            component_message = str(
                component.get(ELASTIC_AGENT_MESSAGE_PAYLOAD_KEY) or ""
            ).strip()
            status_payload = component_status
            if component_message:
                status_payload = f"{component_status}: {component_message}"
            msg.health.component_health_map[component_name].CopyFrom(
                opamp_pb2.ComponentHealth(
                    healthy=self._component_is_healthy(component_status),
                    status=status_payload,
                )
            )
        return msg

    def get_agent_description(
        self,
        instance_uid: bytes | str | None = None,
    ) -> opamp_pb2.AgentDescription:
        """Build Elastic Agent description with stable service type."""
        self.data.agent_type_name = VALUE_AGENT_TYPE_ELASTIC_AGENT
        description = super().get_agent_description(instance_uid)
        for attribute in description.identifying_attributes:
            if attribute.key == KEY_SERVICE_TYPE:
                attribute.value.string_value = VALUE_AGENT_TYPE_ELASTIC_AGENT
                break
        return description


def load_elastic_agent_config(config: ConsumerConfig) -> ConsumerConfig:
    """Load Elastic Agent observer settings into generic consumer fields.

    Args:
        config: Consumer configuration to enrich.

    Returns:
        The same configuration object with status port and config text loaded.
    """
    logger = logging.getLogger(__name__)
    logger.info("Elastic Agent config step: loading agent config")
    if not config.agent_config_path:
        raise ValueError(f"{CFG_AGENT_CONFIG_PATH} is not set")
    config_path = pathlib.Path(config.agent_config_path)
    logger.info("Elastic Agent config step: reading agent_config_path=%s", config_path)
    config.agent_config_text = config_path.read_text(
        encoding=consumer_config.UTF8_ENCODING
    )
    config.client_status_port = int(config.elastic_agent_api_port)
    config.agent_http_port = int(config.elastic_agent_api_port)
    config.agent_http_listen = config.elastic_agent_api_host
    config.agent_http_server = "on"
    logger.info(
        (
            "Elastic Agent config step: monitoring api host=%s port=%s "
            "process_tracking=%s"
        ),
        config.elastic_agent_api_host,
        config.elastic_agent_api_port,
        config.process_tracking,
    )
    return config


def main() -> None:
    """Run the Elastic Agent observer consumer bootstrap flow."""
    try:
        tracemalloc.start()
        parser = build_common_cli_parser()
        args = parser.parse_args()
        if maybe_print_cli_config(args=args):
            return
        config = load_config_from_cli_args(args)
        logger = configure_logging_for_config(config)
        logger.info("Elastic Agent bootstrap step: logging configured")
        consumer_config_path = log_runtime_config_path(
            logger=logger,
            runtime_name="consumer-elastic-agent",
            config_path=getattr(args, "config_path", None),
        )
        log_consumer_startup_banner(
            logger=logger,
            config=config,
            runtime_name="consumer-elastic-agent",
            consumer_config_path=consumer_config_path,
        )

        if maybe_print_config_help(
            args=args,
            config=config,
            config_parameters_payload_builder=_config_parameters_payload,
        ):
            return

        logger.info("Elastic Agent bootstrap step: loading Elastic Agent config")
        config = load_elastic_agent_config(config)
        logger.info("Elastic Agent bootstrap step: validating runtime server config")
        config = validate_runtime_server_config(
            config=config,
            localhost_base=LOCALHOST_BASE,
            missing_status_port_error="client_status_port not found for Elastic Agent",
        )
        logger.info("Elastic Agent bootstrap step: configuring observability")
        configure_observability_for_config(
            config=config,
            default_service_name="opamp-consumer-elastic-agent",
        )
        if config.server_url is None:
            raise ValueError("validated runtime config missing server_url")
        if config.client_status_port is None:
            raise ValueError("validated runtime config missing client_status_port")

        logger.info(
            "Elastic Agent bootstrap step: creating client server_url=%s status_port=%s",
            config.server_url,
            config.client_status_port,
        )
        client = ElasticAgentOpAMPClient(config.server_url, config)
        logger.info("Elastic Agent bootstrap step: launching or attaching agent process")
        if not client.launch_agent_process():
            raise AgentException("Elastic Agent launch failed")
        logger.info("Elastic Agent bootstrap step: reading agent version")
        client.add_agent_version(int(config.client_status_port))
        logger.info("Elastic Agent bootstrap step: introducing client to OpAMP server")
        asyncio.run(run_client(client))
        logger.info("Elastic Agent bootstrap step: starting heartbeat loop")
        asyncio.run(client._heartbeat_loop(int(config.client_status_port)))
        logger.info("Elastic Agent bootstrap step: heartbeat loop ended; terminating lifecycle")
        client.terminate_agent_process()
    except KeyboardInterrupt as keyboard_interrupt:
        print(f"... Elastic Agent keyboard interrupt\n {keyboard_interrupt}")
    except SystemExit as system_exit:
        print(f"... Elastic Agent brutal exit\n {system_exit}")
    except Exception as error:
        print(f"... Elastic Agent consumer stopped\n {error}")


if __name__ == "__main__":
    main()
    print("... Bye")
    sys.exit(1)
