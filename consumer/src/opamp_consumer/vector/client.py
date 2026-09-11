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

"""Vector-specific OpAMP consumer implementation."""

from __future__ import annotations

import asyncio
import logging
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Any

from opamp_consumer import config as consumer_config
from opamp_consumer.abstract_client import (
    KEY_HEALTH,
    KEY_SERVICE_TYPE,
    LOCALHOST_BASE,
    AbstractOpAMPClient,
    _config_parameters_payload,
    resolve_service_instance_id_template,
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
from opamp_consumer.config_metadata import (
    CONFIG_METADATA_KEY_AGENT_DESCRIPTION,
    CONFIG_METADATA_KEY_SERVICE_INSTANCE_ID,
    ConfigMetadata,
)
from opamp_consumer.plugin_config import (
    ConsumerPluginConfigContext,
    resolve_optional_path_from_config,
)
from opamp_consumer.proto import opamp_pb2
from opamp_consumer.reporting_flag import ReportingFlag
from opamp_consumer.startup_banner import log_consumer_startup_banner
from opamp_consumer.vector.config_metadata import extract_vector_config_metadata

VECTOR_CMD = "vector"
VECTOR_CONFIG_FLAG = "--config"
VALUE_AGENT_TYPE_VECTOR = "Vector"
VECTOR_DEFAULT_API_HOST = "127.0.0.1"
VECTOR_DEFAULT_API_PORT = 8686
DEFAULT_VECTOR_STATUS_TIMEOUT_SECONDS = 5.0
CFG_VECTOR_EXECUTABLE_PATH = "executable_path"
CFG_VECTOR_API_HOST = "api_host"
CFG_VECTOR_API_PORT = "api_port"
CFG_VECTOR_STATUS_TIMEOUT_SECONDS = "status_timeout_seconds"
ENV_VECTOR_EXECUTABLE_PATH = "OPAMP_VECTOR_EXECUTABLE_PATH"
ENV_VECTOR_API_HOST = "OPAMP_VECTOR_API_HOST"
ENV_VECTOR_API_PORT = "OPAMP_VECTOR_API_PORT"
VECTOR_HEALTH_PATH = "/health"


def _looks_like_executable_path(value: str) -> bool:
    """Return True when the value should be treated as a direct executable path."""
    normalized = str(value or "").strip()
    if not normalized:
        return False
    return (
        pathlib.PureWindowsPath(normalized).is_absolute()
        or pathlib.Path(normalized).is_absolute()
        or any(separator in normalized for separator in ("/", "\\"))
    )


def _resolve_optional_executable_from_config(
    *,
    raw_value: Any,
    config_path: pathlib.Path,
) -> str | None:
    normalized_value = str(raw_value).strip() if raw_value is not None else ""
    if not normalized_value:
        return None
    if not _looks_like_executable_path(normalized_value):
        return normalized_value
    return resolve_optional_path_from_config(
        raw_value=normalized_value,
        config_path=config_path,
    )


def _parse_vector_api_address(config_text: str) -> tuple[str | None, int | None, bool | None]:
    """Return `(host, port, enabled)` from a Vector YAML config."""
    try:
        import yaml  # type: ignore[import-not-found]

        payload = yaml.safe_load(config_text) or {}
    except Exception as error:
        logging.getLogger(__name__).warning("failed to parse Vector config: %s", error)
        return None, None, None
    if not isinstance(payload, dict):
        return None, None, None
    api = payload.get("api")
    if not isinstance(api, dict):
        return None, None, None
    enabled = api.get("enabled")
    address = str(api.get("address") or "").strip()
    if not address:
        return None, None, bool(enabled) if enabled is not None else None
    host, _, port_text = address.rpartition(":")
    if not host:
        return None, None, bool(enabled) if enabled is not None else None
    try:
        return host.strip("[]"), int(port_text), bool(enabled) if enabled is not None else None
    except ValueError:
        logging.getLogger(__name__).warning("invalid Vector api.address port: %s", address)
        return host.strip("[]"), None, bool(enabled) if enabled is not None else None


def process_consumer_config(
    context: ConsumerPluginConfigContext,
) -> dict[str, Any]:
    """Resolve Vector plugin config into ConsumerConfig fields."""
    vector_raw = context.raw_section
    executable_path = os.environ.get(
        ENV_VECTOR_EXECUTABLE_PATH,
        vector_raw.get(CFG_VECTOR_EXECUTABLE_PATH, VECTOR_CMD),
    )
    api_host = os.environ.get(
        ENV_VECTOR_API_HOST,
        vector_raw.get(CFG_VECTOR_API_HOST, VECTOR_DEFAULT_API_HOST),
    )
    api_port = os.environ.get(
        ENV_VECTOR_API_PORT,
        vector_raw.get(CFG_VECTOR_API_PORT, VECTOR_DEFAULT_API_PORT),
    )
    timeout_seconds = vector_raw.get(
        CFG_VECTOR_STATUS_TIMEOUT_SECONDS,
        DEFAULT_VECTOR_STATUS_TIMEOUT_SECONDS,
    )
    return {
        "vector_executable_path": _resolve_optional_executable_from_config(
            raw_value=executable_path,
            config_path=context.config_path,
        ),
        "vector_api_host": str(api_host or VECTOR_DEFAULT_API_HOST),
        "vector_api_port": int(api_port or VECTOR_DEFAULT_API_PORT),
        "vector_status_timeout_seconds": float(timeout_seconds),
    }


def load_vector_config(config: ConsumerConfig) -> ConsumerConfig:
    """Load Vector API settings and metadata into the consumer config."""
    path = config.agent_config_path
    if not path:
        raise ValueError(f"{CFG_AGENT_CONFIG_PATH} is not set")

    metadata = extract_vector_config_metadata(
        path,
        resolve_service_instance_id_template_fn=resolve_service_instance_id_template,
    )
    if metadata.config_data:
        config.agent_config_text = metadata.config_data
    if metadata.config_version:
        config.config_version = metadata.config_version

    agent_description = metadata.additional_metadata.get(
        CONFIG_METADATA_KEY_AGENT_DESCRIPTION
    )
    if agent_description:
        config.agent_description = agent_description

    service_instance_id = metadata.additional_metadata.get(
        CONFIG_METADATA_KEY_SERVICE_INSTANCE_ID
    )
    if service_instance_id:
        config.service_instance_id = service_instance_id

    host, port, enabled = _parse_vector_api_address(metadata.config_data)
    if host:
        config.vector_api_host = host
        config.agent_http_listen = host
    if port is not None:
        config.vector_api_port = port
        config.client_status_port = port
        config.agent_http_port = port
    if enabled is not None:
        config.agent_http_server = "on" if enabled else "off"
    if config.client_status_port is None:
        config.client_status_port = int(
            getattr(config, "vector_api_port", VECTOR_DEFAULT_API_PORT)
            or VECTOR_DEFAULT_API_PORT
        )
        config.agent_http_port = config.client_status_port
    return config


class VectorLifecycle(_BaseClientProcessLifecycle):
    """Supervisor lifecycle for Vector foreground processes."""

    def _configured_executable(self) -> str:
        return str(getattr(self._owner.config, "vector_executable_path", None) or VECTOR_CMD)

    def _resolve_executable_for_subprocess(self, executable_path: str) -> str:
        if _looks_like_executable_path(executable_path):
            return executable_path
        resolved_path = shutil.which(executable_path)
        if not resolved_path:
            logging.getLogger(__name__).warning("Vector executable not found: %s", executable_path)
            return executable_path
        return resolved_path

    def _command(self) -> list[str]:
        return [
            self._resolve_executable_for_subprocess(self._configured_executable()),
            *(self._owner.config.agent_additional_params or []),
            VECTOR_CONFIG_FLAG,
            str(self._owner.config.agent_config_path),
        ]

    def launch_agent_process(self) -> bool:
        logger = logging.getLogger(__name__)
        command = self._command()
        try:
            with self._owner.data.process_lock:
                self._owner.data.agent_process = subprocess.Popen(command)
                self._owner.data.observed_process_pid = None
        except Exception as error:
            logger.exception("Vector launch failed for command %s: %s", command, error)
            return False
        logger.info("Vector launch result = %s", self._owner.data.agent_process)
        return True

    def terminate_agent_process(self) -> None:
        with self._owner.data.process_lock:
            process = self._owner.data.agent_process
            self._owner.data.allow_heartbeat = False
            if process is None:
                return
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            self._owner.data.agent_process = None

    def restart_agent_process(self) -> bool:
        self.terminate_agent_process()
        return self.launch_agent_process()


class VectorOpAMPClient(AbstractOpAMPClient):
    """Concrete OpAMP client implementation for Vector."""

    _runtime_agent_command = VECTOR_CMD
    _runtime_config_flag = VECTOR_CONFIG_FLAG
    _heartbeat_paths = (VECTOR_HEALTH_PATH,)
    _value_agent_type = VALUE_AGENT_TYPE_VECTOR
    SUPPORTED_AGENT_CAPABILITY_NAMES = (
        *consumer_config.MANDATORY_AGENT_CAPABILITY_NAMES,
        "AcceptsRemoteConfig",
        "ReportsEffectiveConfig",
        "ReportsHeartbeat",
    )

    def __init__(self, base_url: str, config: ConsumerConfig | None = None) -> None:
        super().__init__(base_url, config)
        self.data.agent_type_name = VALUE_AGENT_TYPE_VECTOR
        self._localhost_base = self._vector_base_url()
        self._http_timeout_seconds = float(
            getattr(
                self.config,
                "vector_status_timeout_seconds",
                DEFAULT_VECTOR_STATUS_TIMEOUT_SECONDS,
            )
            or DEFAULT_VECTOR_STATUS_TIMEOUT_SECONDS
        )

    def _create_runtime_process_lifecycle(self) -> _BaseClientProcessLifecycle:
        tracking_mode = _normalize_process_tracking(
            getattr(self.config, "process_tracking", None)
        )
        if tracking_mode == PROCESS_TRACKING_OBSERVER:
            logging.getLogger(__name__).info(
                "Vector lifecycle step: using observer attach strategy"
            )
            return ClientObserverMixin(self)
        return VectorLifecycle(self)

    def _vector_base_url(self) -> str:
        host = str(
            getattr(self.config, "vector_api_host", VECTOR_DEFAULT_API_HOST)
            or VECTOR_DEFAULT_API_HOST
        ).strip()
        if host == "0.0.0.0":
            host = "127.0.0.1"
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        return f"http://{host}"

    def get_custom_handler_folder(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parent / "custom_handlers"

    def get_config_metadata(self) -> ConfigMetadata:
        return extract_vector_config_metadata(
            self.config.agent_config_path,
            resolve_service_instance_id_template_fn=resolve_service_instance_id_template,
        )

    def add_agent_version(self, port: int) -> None:
        executable = str(getattr(self.config, "vector_executable_path", None) or VECTOR_CMD)
        if not _looks_like_executable_path(executable):
            executable = shutil.which(executable) or executable
        try:
            completed = subprocess.run(
                [executable, "--version"],
                text=True,
                capture_output=True,
                timeout=3,
                check=False,
            )
            version_text = (completed.stdout or completed.stderr).strip()
            if version_text:
                self.data.agent_version = version_text
        except Exception as error:
            logging.getLogger(__name__).warning("failed to read Vector version: %s", error)

    def _health_from_metrics(
        self, msg: opamp_pb2.AgentToServer, text: str
    ) -> opamp_pb2.AgentToServer:
        status = str(text or "").strip()
        healthy = status.lower() in {"ok", "true", "healthy"} or '"ok"' in status.lower()
        msg.health.component_health_map[KEY_HEALTH].CopyFrom(
            opamp_pb2.ComponentHealth(
                healthy=healthy,
                status=status or "unknown",
            )
        )
        if not healthy:
            self.data.reporting_flags[ReportingFlag.REPORT_HEALTH] = True
        return msg

    def poll_local_status_with_codes(
        self, port: int
    ) -> tuple[dict[str, str], dict[str, str]]:
        self._localhost_base = self._vector_base_url()
        return super().poll_local_status_with_codes(port)

    def get_agent_description(
        self, instance_uid: bytes | str | None = None
    ) -> opamp_pb2.AgentDescription:
        self.data.agent_type_name = VALUE_AGENT_TYPE_VECTOR
        description = super().get_agent_description(instance_uid)
        for attribute in description.identifying_attributes:
            if attribute.key == KEY_SERVICE_TYPE:
                attribute.value.string_value = VALUE_AGENT_TYPE_VECTOR
                break
        return description


def main() -> None:
    """Run Vector bootstrap with API-aware config processing."""
    try:
        parser = build_common_cli_parser()
        args = parser.parse_args()
        if maybe_print_cli_config(args=args):
            return
        config = load_config_from_cli_args(args)
        logger = configure_logging_for_config(config)
        consumer_config_path = log_runtime_config_path(
            logger=logger,
            runtime_name="consumer",
            config_path=getattr(args, "config_path", None),
        )
        log_consumer_startup_banner(
            logger=logger,
            config=config,
            runtime_name="consumer",
            consumer_config_path=consumer_config_path,
        )
        if maybe_print_config_help(
            args=args,
            config=config,
            config_parameters_payload_builder=_config_parameters_payload,
        ):
            return

        config = load_vector_config(config)
        config = validate_runtime_server_config(
            config=config,
            localhost_base=LOCALHOST_BASE,
            missing_status_port_error="client_status_port not found for Vector",
        )
        configure_observability_for_config(
            config=config,
            default_service_name="opamp-consumer-vector",
        )
        client = VectorOpAMPClient(config.server_url or "", config)
        client.launch_agent_process()
        client.add_agent_version(config.client_status_port or VECTOR_DEFAULT_API_PORT)
        logger.info("introducing vector client to server")
        asyncio.run(run_client(client))
        asyncio.run(client._heartbeat_loop(config.client_status_port or VECTOR_DEFAULT_API_PORT))
        client.terminate_agent_process()
    except KeyboardInterrupt as keyboard_interrupt:
        print("... vector keyboard\n %s", keyboard_interrupt)
    except SystemExit as system_exit:
        print("... vector brutal exit\n %s", system_exit)
    except Exception as err:
        print("... vector bzzzzzzzzzzz")
        print(err)


if __name__ == "__main__":
    main()
    print("... Bye")
    sys.exit(1)
