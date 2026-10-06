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

"""Elastic Heartbeat consumer plugin.

This plugin is intentionally written as a reference for Elastic Beat monitor
plugins. Heartbeat, Metricbeat, Filebeat, and related Beat binaries share a
similar execution model:

- a Beat executable is launched in the foreground by the consumer;
- the Beat reads a YAML file passed with `-c`;
- the Beat exposes a local HTTP endpoint when `http.enabled` is true;
- event delivery is configured in the Beat YAML, usually through `output.*`.

The OpAMP consumer supervises the Beat process and reports local HTTP status
through OpAMP heartbeats. It does not parse or proxy the telemetry events
produced by Heartbeat.
"""

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
from urllib.parse import urlsplit

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
    looks_like_executable_path,
    resolve_optional_executable_from_config,
    resolve_optional_path_from_config,
)
from opamp_consumer.process_utils import ProcessUtils
from opamp_consumer.proto import opamp_pb2
from opamp_consumer.reporting_flag import ReportingFlag
from opamp_consumer.startup_banner import log_consumer_startup_banner

VALUE_AGENT_TYPE_ELASTIC_HEARTBEAT = "Elastic Heartbeat"
ELASTIC_HEARTBEAT_DEFAULT_EXECUTABLE = "heartbeat"
ELASTIC_HEARTBEAT_CONFIG_FLAG = "-c"
ELASTIC_HEARTBEAT_FOREGROUND_FLAG = "-e"
ELASTIC_HEARTBEAT_TEST_CONFIG_COMMAND = "test"
ELASTIC_HEARTBEAT_TEST_CONFIG_TARGET = "config"
ELASTIC_HEARTBEAT_HTTP_ROOT_PATH = "/"
ELASTIC_HEARTBEAT_HTTP_STATS_PATH = "/stats"
ELASTIC_HEARTBEAT_DEFAULT_API_HOST = "127.0.0.1"
ELASTIC_HEARTBEAT_DEFAULT_API_PORT = 5066
DEFAULT_HEARTBEAT_STATUS_TIMEOUT_SECONDS = 5.0
DEFAULT_STOP_WAIT_SECONDS = 5.0
DEFAULT_LOGSTASH_CONNECT_TIMEOUT_SECONDS = 1.0
CFG_HEARTBEAT_EXECUTABLE_PATH = "executable_path"
CFG_HEARTBEAT_HOME_PATH = "home_path"
CFG_HEARTBEAT_API_HOST = "api_host"
CFG_HEARTBEAT_API_PORT = "api_port"
CFG_HEARTBEAT_STATUS_TIMEOUT_SECONDS = "status_timeout_seconds"
ENV_HEARTBEAT_EXECUTABLE_PATH = "OPAMP_ELASTIC_HEARTBEAT_EXECUTABLE_PATH"
ENV_HEARTBEAT_HOME_PATH = "OPAMP_ELASTIC_HEARTBEAT_HOME_PATH"
ENV_HEARTBEAT_API_HOST = "OPAMP_ELASTIC_HEARTBEAT_API_HOST"
ENV_HEARTBEAT_API_PORT = "OPAMP_ELASTIC_HEARTBEAT_API_PORT"
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


def _coerce_string_list(value: Any) -> list[str]:
    """Return config scalar/list values as a list of non-empty strings."""
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    normalized_value = str(value or "").strip()
    return [normalized_value] if normalized_value else []


def _resolve_elastic_env_provider_refs(value: str) -> str:
    """Resolve Elastic `${env.NAME|'fallback'}` references used in Beat YAML."""

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


def _yaml_get(payload: dict[str, Any], dotted_key: str) -> Any:
    """Read a dotted Beat YAML key from flat or nested YAML structures."""
    if dotted_key in payload:
        return payload[dotted_key]
    current: Any = payload
    for part in dotted_key.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _beat_http_settings_from_config(config_text: str) -> tuple[str | None, int | None]:
    """Return `http.host` and `http.port` from Beat YAML text when present."""
    loaded = yaml.safe_load(config_text) or {}
    if not isinstance(loaded, dict):
        return None, None
    enabled = _yaml_get(loaded, "http.enabled")
    if enabled is False:
        return None, None
    host_value = _yaml_get(loaded, "http.host")
    port_value = _yaml_get(loaded, "http.port")
    host = str(host_value).strip() if host_value is not None else None
    port = int(port_value) if port_value is not None else None
    return host or None, port


def _logstash_hosts_from_beat_config(config_text: str) -> list[str]:
    """Extract Logstash output hosts from Elastic Beat YAML text."""
    loaded = yaml.safe_load(config_text) or {}
    if not isinstance(loaded, dict):
        return []
    output = _yaml_get(loaded, "output.logstash")
    if not isinstance(output, dict):
        return []
    return [
        _resolve_elastic_env_provider_refs(host)
        for host in _coerce_string_list(output.get("hosts"))
    ]


def _split_host_port(endpoint: str) -> tuple[str, int] | None:
    """Parse a Logstash endpoint into host and port parts."""
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


def _beat_status_is_healthy(status_code: int, payload_text: str) -> bool:
    """Return whether a Beat HTTP response should be reported as healthy."""
    if status_code < 200 or status_code > 299:
        return False
    try:
        payload = json.loads(payload_text or "{}")
    except json.JSONDecodeError:
        return True
    if not isinstance(payload, dict):
        return True
    status_value = str(payload.get("status") or "").strip().lower()
    if not status_value:
        return True
    return status_value not in {"failed", "error", "stopped", "degraded"}


def process_consumer_config(
    context: ConsumerPluginConfigContext,
) -> dict[str, Any]:
    """Resolve Elastic Heartbeat plugin config into ConsumerConfig fields.

    The same shape can be reused by future Beat monitor plugins. Keep
    executable/home/status settings inside `consumer.elastic_heartbeat` so the
    shared consumer keys remain agent-neutral.
    """
    heartbeat_raw = context.raw_section
    executable_path = os.environ.get(
        ENV_HEARTBEAT_EXECUTABLE_PATH,
        heartbeat_raw.get(CFG_HEARTBEAT_EXECUTABLE_PATH),
    )
    home_path = os.environ.get(
        ENV_HEARTBEAT_HOME_PATH,
        heartbeat_raw.get(CFG_HEARTBEAT_HOME_PATH),
    )
    api_host = os.environ.get(
        ENV_HEARTBEAT_API_HOST,
        heartbeat_raw.get(CFG_HEARTBEAT_API_HOST, ELASTIC_HEARTBEAT_DEFAULT_API_HOST),
    )
    api_port = os.environ.get(
        ENV_HEARTBEAT_API_PORT,
        heartbeat_raw.get(CFG_HEARTBEAT_API_PORT, ELASTIC_HEARTBEAT_DEFAULT_API_PORT),
    )
    timeout_seconds = heartbeat_raw.get(
        CFG_HEARTBEAT_STATUS_TIMEOUT_SECONDS,
        DEFAULT_HEARTBEAT_STATUS_TIMEOUT_SECONDS,
    )
    return {
        "elastic_heartbeat_executable_path": resolve_optional_executable_from_config(
            raw_value=executable_path,
            config_path=context.config_path,
        ),
        "elastic_heartbeat_home_path": resolve_optional_path_from_config(
            raw_value=home_path,
            config_path=context.config_path,
        ),
        "elastic_heartbeat_api_host": str(
            api_host or ELASTIC_HEARTBEAT_DEFAULT_API_HOST
        ),
        "elastic_heartbeat_api_port": int(
            api_port or ELASTIC_HEARTBEAT_DEFAULT_API_PORT
        ),
        "elastic_heartbeat_status_timeout_seconds": float(timeout_seconds),
    }


class ElasticHeartbeatLifecycle(_BaseClientProcessLifecycle):
    """Supervisor lifecycle for Beat-style foreground processes."""

    def _configured_executable(self) -> str:
        """Return the configured Heartbeat executable command or path."""
        return str(
            self._owner.config.elastic_heartbeat_executable_path
            or ELASTIC_HEARTBEAT_DEFAULT_EXECUTABLE
        )

    def _working_directory(self) -> str | None:
        """Return configured Heartbeat working directory."""
        return self._owner.config.elastic_heartbeat_home_path

    def _executable_lookup_path(self) -> str | None:
        """Return PATH text including the configured Beat home path."""
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
        if looks_like_executable_path(executable_path):
            return executable_path
        resolved_path = shutil.which(executable_path, path=self._executable_lookup_path())
        if not resolved_path:
            logging.getLogger(__name__).warning(
                "Elastic Heartbeat executable not found in lookup path: %s cwd=%s",
                executable_path,
                self._working_directory(),
            )
            return executable_path
        if resolved_path != executable_path:
            logging.getLogger(__name__).info(
                "Elastic Heartbeat executable resolved: %s -> %s",
                executable_path,
                resolved_path,
            )
        return resolved_path

    def _heartbeat_command(self, *args: str) -> list[str]:
        """Build a Heartbeat command from fixed plugin verbs/flags."""
        return [self._resolve_executable_for_subprocess(self._configured_executable()), *args]

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
                "Elastic Heartbeat %s failed: %s commandline=%s argv=%s "
                "cwd=%s configured_executable=%s lookup_path=%s process_cwd=%s "
                "path=%s timeout=%s"
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

    def _configured_logstash_hosts(self) -> list[str]:
        """Return Logstash output hosts declared in Heartbeat YAML."""
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
            return _logstash_hosts_from_beat_config(config_text)
        except Exception as config_error:
            logging.getLogger(__name__).warning(
                "Elastic Heartbeat Logstash output probe skipped; failed to parse %s: %s",
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
            float(self._owner.config.elastic_heartbeat_status_timeout_seconds),
            DEFAULT_LOGSTASH_CONNECT_TIMEOUT_SECONDS,
        )
        try:
            with socket.create_connection((host, port), timeout=timeout_seconds):
                return True, "reachable"
        except OSError as connect_error:
            return False, str(connect_error)

    def _log_logstash_output_readiness(self) -> bool:
        """Log configured Logstash output readiness before launching Heartbeat."""
        logger = logging.getLogger(__name__)
        hosts = self._configured_logstash_hosts()
        if not hosts:
            logger.info(
                "Elastic Heartbeat Logstash output probe skipped; no logstash output found"
            )
            return True
        logger.info(
            "Elastic Heartbeat launch step: probing %s Logstash output endpoint(s)",
            len(hosts),
        )
        all_ready = True
        for endpoint in hosts:
            ready, detail = self._probe_logstash_host(endpoint)
            if ready:
                logger.info(
                    "Elastic Heartbeat Logstash output endpoint reachable: %s",
                    endpoint,
                )
                continue
            all_ready = False
            logger.error(
                "Elastic Heartbeat Logstash output endpoint unreachable: %s error=%s",
                endpoint,
                detail,
            )
        return all_ready

    def launch_agent_process(self) -> bool:
        """Start Heartbeat with `heartbeat -e -c <config>` in supervisor mode."""
        logger = logging.getLogger(__name__)
        logger.info("Elastic Heartbeat launch step: preparing supervisor launch")
        config_path = str(self._owner.config.agent_config_path or "").strip()
        if not config_path:
            logger.error("%s is required for Elastic Heartbeat launch", CFG_AGENT_CONFIG_PATH)
            return False
        if not self._log_logstash_output_readiness():
            logger.error(
                "Elastic Heartbeat launch skipped because one or more configured "
                "Logstash endpoints are unreachable"
            )
            return False
        command = self._heartbeat_command(
            ELASTIC_HEARTBEAT_FOREGROUND_FLAG,
            ELASTIC_HEARTBEAT_CONFIG_FLAG,
            config_path,
            *(self._owner.config.agent_additional_params or []),
        )
        logger.info(
            "Elastic Heartbeat launch command: %s cwd=%s",
            _command_for_log(command),
            self._working_directory(),
        )
        try:
            with self._owner.data.process_lock:
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
        except FileNotFoundError as file_error:
            self._log_subprocess_error(
                logger=logger,
                action="launch",
                error=file_error,
                command=command,
                cwd=self._working_directory(),
            )
            return False
        except Exception as launch_error:  # pragma: no cover - env-dependent
            self._log_subprocess_error(
                logger=logger,
                action="launch",
                error=launch_error,
                command=command,
                cwd=self._working_directory(),
                exc_info=True,
            )
            return False
        logger.info("Elastic Heartbeat launched with pid=%s", self._owner.data.observed_process_pid)
        return True

    def terminate_agent_process(self) -> None:
        """Stop the tracked Heartbeat foreground process gracefully."""
        logger = logging.getLogger(__name__)
        self._owner.data.allow_heartbeat = False
        process = self._owner.data.agent_process
        if process is not None:
            logger.info("Elastic Heartbeat terminate process pid=%s", process.pid)
            process.terminate()
            try:
                process.wait(timeout=DEFAULT_STOP_WAIT_SECONDS)
            except subprocess.TimeoutExpired:
                logger.warning("Elastic Heartbeat did not stop in time; killing process")
                process.kill()
                process.wait(timeout=DEFAULT_STOP_WAIT_SECONDS)
            self._owner.data.agent_process = None
            self._owner.data.observed_process_pid = None
            return

        pid = self._owner.data.observed_process_pid
        if pid is None:
            regex = str(self._owner.config.process_detection_regex or "").strip()
            pid = ProcessUtils.find_pid_by_regex(regex) if regex else None
        if pid is None:
            logger.info("Elastic Heartbeat stop skipped; no matching process found")
            return
        if ProcessUtils.can_send_signal():
            ProcessUtils.send_termination_signal(pid)
            time.sleep(1.0)
        if ProcessUtils.is_process_running(pid):
            ProcessUtils.terminate_process(pid)
        if ProcessUtils.is_process_running(pid):
            ProcessUtils.kill_process(pid)
        if not ProcessUtils.is_process_running(pid):
            self._owner.data.observed_process_pid = None

    def restart_agent_process(self) -> bool:
        """Restart Heartbeat with stop/start semantics."""
        self.terminate_agent_process()
        relaunched = self.launch_agent_process()
        if not relaunched:
            raise AgentException("Failed to restart Elastic Heartbeat")
        return relaunched

    def test_config(self) -> subprocess.CompletedProcess[str]:
        """Run `heartbeat test config` for diagnostics and container smoke tests."""
        timeout_seconds = float(
            self._owner.config.elastic_heartbeat_status_timeout_seconds
        )
        command = self._heartbeat_command(
            ELASTIC_HEARTBEAT_TEST_CONFIG_COMMAND,
            ELASTIC_HEARTBEAT_TEST_CONFIG_TARGET,
            ELASTIC_HEARTBEAT_CONFIG_FLAG,
            str(self._owner.config.agent_config_path or ""),
        )
        logging.getLogger(__name__).info(
            "Elastic Heartbeat config test command: %s cwd=%s timeout=%s",
            _command_for_log(command),
            self._working_directory(),
            timeout_seconds,
        )
        return subprocess.run(  # noqa: S603
            command,
            cwd=self._working_directory(),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            **_windows_no_console_kwargs(),
        )


class ElasticHeartbeatOpAMPClient(AbstractOpAMPClient):
    """Concrete OpAMP supervisor implementation for Elastic Heartbeat."""

    _runtime_agent_command = ELASTIC_HEARTBEAT_DEFAULT_EXECUTABLE
    _runtime_config_flag = ELASTIC_HEARTBEAT_CONFIG_FLAG
    _heartbeat_paths = (ELASTIC_HEARTBEAT_HTTP_ROOT_PATH, ELASTIC_HEARTBEAT_HTTP_STATS_PATH)
    _value_agent_type = VALUE_AGENT_TYPE_ELASTIC_HEARTBEAT
    _localhost_base = "http://127.0.0.1"
    _json_key_agent = "beat"
    SUPPORTED_AGENT_CAPABILITY_NAMES = (
        *consumer_config.MANDATORY_AGENT_CAPABILITY_NAMES,
        "AcceptsRemoteConfig",
        "ReportsEffectiveConfig",
        "ReportsHeartbeat",
    )

    def __init__(self, base_url: str, config: ConsumerConfig | None = None) -> None:
        """Initialize Heartbeat runtime defaults."""
        super().__init__(base_url, config)
        self.data.agent_type_name = VALUE_AGENT_TYPE_ELASTIC_HEARTBEAT
        self._localhost_base = (
            f"http://{self.config.elastic_heartbeat_api_host}"
        )
        self._http_timeout_seconds = float(
            self.config.elastic_heartbeat_status_timeout_seconds
        )

    def get_custom_handler_folder(self) -> pathlib.Path:
        """Return default custom handler folder for Heartbeat commands."""
        return pathlib.Path(__file__).resolve().parent / "custom_handlers"

    def get_config_metadata(self) -> ConfigMetadata:
        """Return empty metadata because Heartbeat YAML has no OpAMP comments."""
        return ConfigMetadata()

    def _create_runtime_process_lifecycle(
        self,
    ) -> _BaseClientProcessLifecycle:
        """Create process lifecycle honoring configured process tracking."""
        tracking_mode = _normalize_process_tracking(
            getattr(self.config, "process_tracking", None)
        )
        if tracking_mode == PROCESS_TRACKING_OBSERVER:
            logging.getLogger(__name__).info(
                "Elastic Heartbeat lifecycle step: using observer attach strategy"
            )
            return ClientObserverMixin(self)
        logging.getLogger(__name__).info(
            "Elastic Heartbeat lifecycle step: using supervisor strategy"
        )
        return ElasticHeartbeatLifecycle(self)

    def poll_local_status_with_codes(
        self, port: int
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Poll Beat HTTP status endpoints and collect response bodies/codes."""
        results, codes = super().poll_local_status_with_codes(port)
        root_key = self._heartbeat_key(ELASTIC_HEARTBEAT_HTTP_ROOT_PATH)
        root_text = results.get(root_key, "")
        root_code = codes.get(root_key, "0")
        if root_key in results:
            results[KEY_HEALTH] = results[root_key]
            codes[KEY_HEALTH] = codes.get(root_key, "0")
        try:
            status_code = int(root_code)
        except ValueError:
            status_code = 0
        if not _beat_status_is_healthy(status_code, root_text):
            self.data.reporting_flags[ReportingFlag.REPORT_HEALTH] = True
        return results, codes

    def _health_from_metrics(
        self,
        msg: opamp_pb2.AgentToServer,
        text: str,
    ) -> opamp_pb2.AgentToServer:
        """Map Beat HTTP status JSON into OpAMP component health."""
        try:
            payload = json.loads(text or "{}")
        except json.JSONDecodeError:
            payload = {}
        healthy = _beat_status_is_healthy(200, text)
        status = "healthy" if healthy else "unhealthy"
        if isinstance(payload, dict):
            status = str(payload.get("status") or status)
        msg.health.component_health_map[VALUE_AGENT_TYPE_ELASTIC_HEARTBEAT].CopyFrom(
            opamp_pb2.ComponentHealth(healthy=healthy, status=status)
        )
        return msg

    def get_agent_description(
        self,
        instance_uid: bytes | str | None = None,
    ) -> opamp_pb2.AgentDescription:
        """Build Heartbeat description with stable service type."""
        self.data.agent_type_name = VALUE_AGENT_TYPE_ELASTIC_HEARTBEAT
        fallback_instance_uid = instance_uid
        if fallback_instance_uid is None and not self.config.service_instance_id:
            fallback_instance_uid = self.config.service_name
        description = super().get_agent_description(fallback_instance_uid)
        for attribute in description.identifying_attributes:
            if attribute.key == KEY_SERVICE_TYPE:
                attribute.value.string_value = VALUE_AGENT_TYPE_ELASTIC_HEARTBEAT
                break
        return description


def load_elastic_heartbeat_config(config: ConsumerConfig) -> ConsumerConfig:
    """Load Heartbeat YAML and status endpoint settings into shared fields."""
    logger = logging.getLogger(__name__)
    if not config.agent_config_path:
        raise ValueError(f"{CFG_AGENT_CONFIG_PATH} is not set")
    config_path = pathlib.Path(config.agent_config_path)
    logger.info("Elastic Heartbeat config step: reading agent_config_path=%s", config_path)
    config.agent_config_text = config_path.read_text(
        encoding=consumer_config.UTF8_ENCODING
    )
    config_host, config_port = _beat_http_settings_from_config(config.agent_config_text)
    if config_host:
        config.elastic_heartbeat_api_host = config_host
    if config_port is not None:
        config.elastic_heartbeat_api_port = config_port
    config.client_status_port = int(config.elastic_heartbeat_api_port)
    config.agent_http_port = int(config.elastic_heartbeat_api_port)
    config.agent_http_listen = config.elastic_heartbeat_api_host
    config.agent_http_server = "on"
    logger.info(
        "Elastic Heartbeat config step: monitoring api host=%s port=%s process_tracking=%s",
        config.elastic_heartbeat_api_host,
        config.elastic_heartbeat_api_port,
        config.process_tracking,
    )
    return config


def main() -> None:
    """Run the Elastic Heartbeat consumer bootstrap flow."""
    try:
        tracemalloc.start()
        parser = build_common_cli_parser()
        args = parser.parse_args()
        if maybe_print_cli_config(args=args):
            return
        config = load_config_from_cli_args(args)
        logger = configure_logging_for_config(config)
        consumer_config_path = log_runtime_config_path(
            logger=logger,
            runtime_name="consumer-elastic-heartbeat",
            config_path=getattr(args, "config_path", None),
        )
        log_consumer_startup_banner(
            logger=logger,
            config=config,
            runtime_name="consumer-elastic-heartbeat",
            consumer_config_path=consumer_config_path,
        )
        if maybe_print_config_help(
            args=args,
            config=config,
            config_parameters_payload_builder=_config_parameters_payload,
        ):
            return

        config = load_elastic_heartbeat_config(config)
        config = validate_runtime_server_config(
            config=config,
            localhost_base=LOCALHOST_BASE,
            missing_status_port_error="client_status_port not found for Elastic Heartbeat",
        )
        configure_observability_for_config(
            config=config,
            default_service_name="opamp-consumer-elastic-heartbeat",
        )
        if config.server_url is None:
            raise ValueError("validated runtime config missing server_url")
        if config.client_status_port is None:
            raise ValueError("validated runtime config missing client_status_port")

        client = ElasticHeartbeatOpAMPClient(config.server_url, config)
        if not client.launch_agent_process():
            raise AgentException("Elastic Heartbeat launch failed")
        client.add_agent_version(int(config.client_status_port))
        asyncio.run(run_client(client))
        asyncio.run(client._heartbeat_loop(int(config.client_status_port)))
        client.terminate_agent_process()
    except KeyboardInterrupt as keyboard_interrupt:
        print(f"... Elastic Heartbeat keyboard interrupt\n {keyboard_interrupt}")
    except SystemExit as system_exit:
        print(f"... Elastic Heartbeat brutal exit\n {system_exit}")
    except Exception as error:
        print(f"... Elastic Heartbeat consumer stopped\n {error}")


if __name__ == "__main__":
    main()
    print("... Bye")
    sys.exit(1)
