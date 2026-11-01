# Copyright 2026 opamp.info
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

"""Simulator OpAMP consumer that replays scripted responses per server request type."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
import sys
import time
import traceback
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from opamp_consumer import config as consumer_config
from opamp_consumer.abstract_client import (
    KEY_HEALTH,
    KEY_SERVICE_INSTANCE_ID,
    KEY_SERVICE_TYPE,
    KEY_SERVICE_VERSION,
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
from opamp_consumer.config import ConsumerConfig
from opamp_consumer.config_metadata import (
    CONFIG_METADATA_KEY_SERVICE_INSTANCE_ID,
    CONFIG_METADATA_KEY_SERVICE_INSTANCE_UID,
    ConfigMetadata,
)
from opamp_consumer.exceptions import AgentException
from opamp_consumer.proto import anyvalue_pb2, opamp_pb2
from opamp_consumer.simulator.config_metadata import extract_simulator_config_metadata
from opamp_consumer.startup_banner import log_consumer_startup_banner

SIMULATOR_ACTION_ACCEPT = "accept"  # Action indicating the default handler should run.
SIMULATOR_ACTION_IGNORE = "ignore"  # Action indicating the request should be ignored.
SIMULATOR_ACTION_ERROR = "error"  # Action indicating simulated request failure.
SIMULATOR_REQUEST_FALLBACK_KEY = "*"  # Optional catch-all request key in simulator config.
SIMULATOR_CONFIG_RESPONSES_KEY = "responses"
# Optional top-level key wrapping scripted response lists.
SIMULATOR_VALUE_AGENT_TYPE = "simulator"  # service.type value exposed by simulator client.
SIMULATOR_METADATA_SERVICE_INSTANCE_UID = CONFIG_METADATA_KEY_SERVICE_INSTANCE_UID
# JSON key for simulator service instance id passed via --agent-additional-params.
SIMULATOR_METADATA_SERVICE_INSTANCE_ID = CONFIG_METADATA_KEY_SERVICE_INSTANCE_ID
# Alternate JSON key for simulator service instance id.
SIMULATOR_METADATA_CLIENT_VERSION = "client_version"
# JSON key for simulator client version override.
SIMULATOR_METADATA_CONFIG_VERSION = "config_version"
# JSON key for simulator config version metadata.
SIMULATOR_ATTRIBUTE_CONFIG_VERSION = "config.version"
# AgentDescription non-identifying metadata key for simulator config version.
SIMULATOR_PROCESS_RECORD_FILE_ENV = "OPAMP_SIM_PROCESS_RECORD_FILE"
# Environment variable carrying launcher process record state-file path.
SIMULATOR_PROCESS_RECORD_NAME_ENV = "OPAMP_SIM_PROCESS_RECORD_NAME"
# Environment variable carrying launcher process record instance name.
SIMULATOR_STATUS_CHECK_SECONDS = 30.0  # Poll interval for process record shutdown status checks.
PROCESS_RECORD_KEY_INSTANCES = "instances"  # Launcher state file instances key.
PROCESS_RECORD_KEY_NAME = "name"  # Launcher state file instance name key.
PROCESS_RECORD_KEY_STATUS = "status"  # Launcher state file status key.
PROCESS_RECORD_STATUS_SHUTDOWN = "shutdown"
# Launcher state status requesting graceful simulator shutdown.
PROCESS_RECORD_STATUS_SHUTTING_DOWN = "shuttingdown"
# Launcher state status set by simulator once shutdown has been acknowledged.
ENV_APP_ENABLE_DEV_FEATURES = "APP_ENABLE_DEV_FEATURES"
# Required startup flag that explicitly enables simulator runtime in development environments.
_TRUE_FLAG_VALUES = {"1", "true", "yes", "on"}
# Accepted truthy values for dev feature flag checks.

REQUEST_ERROR_RESPONSE = "error_response"
REQUEST_REMOTE_CONFIG = "remote_config"
REQUEST_CONNECTION_SETTINGS = "connection_settings"
REQUEST_PACKAGES_AVAILABLE = "packages_available"
REQUEST_FLAGS = "flags"
REQUEST_CAPABILITIES = "capabilities"
REQUEST_AGENT_IDENTIFICATION = "agent_identification"
REQUEST_COMMAND = "command"
REQUEST_CUSTOM_CAPABILITIES = "custom_capabilities"
REQUEST_CUSTOM_MESSAGE = "custom_message"

SIMULATOR_SERVER_REQUEST_TYPES = (
    REQUEST_ERROR_RESPONSE,
    REQUEST_REMOTE_CONFIG,
    REQUEST_CONNECTION_SETTINGS,
    REQUEST_PACKAGES_AVAILABLE,
    REQUEST_FLAGS,
    REQUEST_CAPABILITIES,
    REQUEST_AGENT_IDENTIFICATION,
    REQUEST_COMMAND,
    REQUEST_CUSTOM_CAPABILITIES,
    REQUEST_CUSTOM_MESSAGE,
)

_VALID_SIMULATOR_ACTIONS = {
    SIMULATOR_ACTION_ACCEPT,
    SIMULATOR_ACTION_IGNORE,
    SIMULATOR_ACTION_ERROR,
}


def _is_dev_features_enabled(flag_value: str | None) -> bool:
    """Return whether the simulator dev-features flag value is enabled."""
    if flag_value is None:
        return False
    return str(flag_value).strip().lower() in _TRUE_FLAG_VALUES


def _validate_simulator_dev_features_flag(logger: logging.Logger) -> bool:
    """Validate required simulator startup flag and log failures consistently.

    Why this gate exists:
    simulator workloads are development-only; this explicit opt-in prevents
    accidental startup in environments where simulator traffic is not expected.
    """
    raw_value = os.getenv(ENV_APP_ENABLE_DEV_FEATURES)
    if _is_dev_features_enabled(raw_value):
        return True
    if raw_value is None:
        logger.error(
            "simulator startup blocked: required environment flag %s is not set",
            ENV_APP_ENABLE_DEV_FEATURES,
        )
    else:
        logger.error(
            "simulator startup blocked: required environment flag %s must be true but was '%s'",
            ENV_APP_ENABLE_DEV_FEATURES,
            raw_value,
        )
    logger.error(
        "simulator shutting down gracefully before sending any details to the server"
    )
    return False


@dataclass(frozen=True)
class ScriptedResponse:
    """Normalized simulator response selection for one request occurrence."""

    action: str
    message: str | None = None


def _normalize_scripted_response(
    *,
    request_type: str,
    raw_response: Any,
) -> ScriptedResponse:
    """Normalize one raw scripted response entry into a supported action."""
    if isinstance(raw_response, str):
        action = raw_response.strip().lower()
        message = None
    elif isinstance(raw_response, dict):
        action = str(
            raw_response.get("action")
            or raw_response.get("response")
            or SIMULATOR_ACTION_ACCEPT
        ).strip().lower()
        raw_message = raw_response.get("message")
        message = str(raw_message).strip() if raw_message is not None else None
    else:
        raise ValueError(
            f"simulator response for '{request_type}' must be a string or object"
        )

    if action not in _VALID_SIMULATOR_ACTIONS:
        raise ValueError(
            f"simulator response action for '{request_type}' must be one of "
            f"{sorted(_VALID_SIMULATOR_ACTIONS)}"
        )
    return ScriptedResponse(action=action, message=message)


def _normalize_response_sequence(*, request_type: str, raw_value: Any) -> list[ScriptedResponse]:
    """Normalize one request type response sequence and ensure it is non-empty."""
    entries = raw_value
    if isinstance(raw_value, (str, dict)):
        entries = [raw_value]

    if not isinstance(entries, list) or not entries:
        raise ValueError(
            f"simulator responses for '{request_type}' must be a non-empty list"
        )
    return [
        _normalize_scripted_response(
            request_type=request_type,
            raw_response=item,
        )
        for item in entries
    ]


def _load_scripted_responses(path: str) -> dict[str, list[ScriptedResponse]]:
    """Load and normalize simulator scripted response sequences from JSON file."""
    config_path = pathlib.Path(path)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("simulator responses file root must be a JSON object")

    raw_responses = payload.get(SIMULATOR_CONFIG_RESPONSES_KEY, payload)
    if not isinstance(raw_responses, dict):
        raise ValueError("simulator responses payload must be a JSON object")

    normalized: dict[str, list[ScriptedResponse]] = {}
    for key, raw_value in raw_responses.items():
        request_type = str(key).strip()
        if not request_type:
            raise ValueError("simulator response keys cannot be empty")
        if (
            request_type not in SIMULATOR_SERVER_REQUEST_TYPES
            and request_type != SIMULATOR_REQUEST_FALLBACK_KEY
        ):
            raise ValueError(
                f"unsupported simulator request type '{request_type}' in responses file"
            )
        normalized[request_type] = _normalize_response_sequence(
            request_type=request_type,
            raw_value=raw_value,
        )

    fallback_sequence = normalized.get(SIMULATOR_REQUEST_FALLBACK_KEY)
    # Ensure every known request type has an explicit sequence.
    for request_type in SIMULATOR_SERVER_REQUEST_TYPES:
        normalized.setdefault(
            request_type,
            list(fallback_sequence)
            if fallback_sequence
            else [ScriptedResponse(action=SIMULATOR_ACTION_ACCEPT)],
        )
    return normalized


class SimulatorOpAMPClient(AbstractOpAMPClient):
    """Concrete OpAMP client using scripted responses for server requests."""

    _runtime_agent_command = "simulator"
    _runtime_config_flag = "-c"
    _heartbeat_paths = ("/simulator/health",)
    _value_agent_type = "Simulator"
    SUPPORTED_AGENT_CAPABILITY_NAMES = (
        *consumer_config.MANDATORY_AGENT_CAPABILITY_NAMES,
        "AcceptsRemoteConfig",
        "ReportsEffectiveConfig",
        "ReportsHeartbeat",
    )

    def __init__(self, base_url: str, config: ConsumerConfig | None = None) -> None:
        """Create simulator client and load scripted response plan."""
        super().__init__(base_url, config)
        self.data.agent_type_name = "Simulator"
        self.data.agent_version = "scripted"
        if not self.config.simulator_responses_path:
            raise ValueError(
                "simulator_responses_path is required for simulator client runtime"
            )
        self._scripted_responses = _load_scripted_responses(
            self.config.simulator_responses_path
        )
        self._scripted_indexes = {
            key: 0 for key in self._scripted_responses
        }
        self._simulator_metadata = extract_simulator_config_metadata(
            self.config.agent_additional_params
        )
        self._simulator_client_version = self._simulator_metadata.version
        service_instance_id = self._simulator_metadata.additional_metadata.get(
            SIMULATOR_METADATA_SERVICE_INSTANCE_UID
        ) or self._simulator_metadata.additional_metadata.get(
            SIMULATOR_METADATA_SERVICE_INSTANCE_ID
        )
        if service_instance_id:
            self.config.service_instance_id = service_instance_id
        config_version = self._simulator_metadata.config_version
        if config_version:
            self.config.config_version = config_version
        if self._simulator_metadata.config_data:
            self.config.agent_config_text = self._simulator_metadata.config_data
        if self._simulator_client_version:
            self.data.agent_version = self._simulator_client_version
        process_record_file = str(
            os.getenv(SIMULATOR_PROCESS_RECORD_FILE_ENV, "") or ""
        ).strip()
        process_record_name = str(
            os.getenv(SIMULATOR_PROCESS_RECORD_NAME_ENV, "") or ""
        ).strip()
        self._process_record_file = (
            pathlib.Path(process_record_file).expanduser().resolve()
            if process_record_file
            else None
        )
        self._process_record_name = process_record_name or None
        self._last_process_record_status_check = 0.0

    def get_custom_handler_folder(self) -> pathlib.Path:
        """Return simulator custom handler folder path."""
        return pathlib.Path(__file__).resolve().parent / "custom_handlers"

    def get_config_metadata(self) -> ConfigMetadata:
        """Return structured metadata extracted from simulator CLI metadata JSON."""
        return extract_simulator_config_metadata(self.config.agent_additional_params)

    def launch_agent_process(self) -> bool:
        """No-op launch for simulator mode."""
        logging.getLogger(__name__).info(
            "simulator mode enabled; skipping managed agent launch"
        )
        self.data.launched_at = time.time_ns()
        return True

    def terminate_agent_process(self) -> None:
        """No-op terminate for simulator mode."""
        self.data.allow_heartbeat = False

    def restart_agent_process(self) -> bool:
        """No-op restart for simulator mode."""
        logging.getLogger(__name__).info(
            "simulator mode received restart request; restart is simulated"
        )
        return True

    def _load_process_record_payload(self) -> dict[str, Any] | None:
        """Load launcher process record JSON payload for status polling."""
        if self._process_record_file is None:
            return None
        try:
            payload = json.loads(self._process_record_file.read_text(encoding="utf-8"))
        except Exception as exc:  # pylint: disable=broad-except
            logging.getLogger(__name__).warning(
                "failed reading simulator process record file %s: %s",
                self._process_record_file,
                exc,
            )
            return None
        if not isinstance(payload, dict):
            return None
        return payload

    def _persist_process_record_payload(self, payload: dict[str, Any]) -> bool:
        """Persist launcher process record payload using atomic replace."""
        if self._process_record_file is None:
            return False
        try:
            self._process_record_file.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self._process_record_file.with_suffix(
                f"{self._process_record_file.suffix}.tmp.{os.getpid()}"
            )
            temp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            os.replace(temp_path, self._process_record_file)
            return True
        except Exception as exc:
            logging.getLogger(__name__).warning(
                "failed persisting simulator process record file %s: %s",
                self._process_record_file,
                exc,
            )
            return False

    def _check_process_record_shutdown_status(self) -> bool:
        """Return True when launcher requested shutdown for this simulator instance.

        When shutdown is requested, this also updates status to `shuttingdown`.
        """
        if self._process_record_file is None or not self._process_record_name:
            return False

        payload = self._load_process_record_payload()
        if payload is None:
            return False
        instances = payload.get(PROCESS_RECORD_KEY_INSTANCES)
        if not isinstance(instances, list):
            return False

        for instance in instances:
            if not isinstance(instance, dict):
                continue
            if str(instance.get(PROCESS_RECORD_KEY_NAME, "")).strip() != self._process_record_name:
                continue
            status = str(instance.get(PROCESS_RECORD_KEY_STATUS, "")).strip().lower()
            if status != PROCESS_RECORD_STATUS_SHUTDOWN:
                return False
            instance[PROCESS_RECORD_KEY_STATUS] = PROCESS_RECORD_STATUS_SHUTTING_DOWN
            persisted = self._persist_process_record_payload(payload)
            if not persisted:
                logging.getLogger(__name__).warning(
                    "shutdown requested for simulator %s but process record update failed",
                    self._process_record_name,
                )
            return True
        return False

    def check_semaphore(self) -> bool:
        """Check launcher process record status every 30 seconds for shutdown."""
        now = time.monotonic()
        if (
            now - float(self._last_process_record_status_check)
            >= SIMULATOR_STATUS_CHECK_SECONDS
        ):
            self._last_process_record_status_check = now
            if self._check_process_record_shutdown_status():
                logging.getLogger(__name__).info(
                    "simulator shutdown status detected for %s; exiting gracefully",
                    self._process_record_name or "<unknown>",
                )
                return True
        return super().check_semaphore()

    def poll_local_status_with_codes(
        self, port: int
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Return synthetic heartbeat status for simulator mode."""
        del port
        return (
            {KEY_HEALTH: '{"status":"simulated","healthy":true}'},
            {KEY_HEALTH: "200"},
        )

    def add_agent_version(self, port: int) -> None:
        """Set a deterministic simulator version string."""
        del port
        self.data.agent_type_name = "Simulator"
        self.data.agent_version = self._simulator_client_version or "scripted"

    def get_agent_description(
        self, instance_uid: bytes | str | None = None
    ) -> opamp_pb2.AgentDescription:
        """Build description and force simulator service type marker."""
        self.data.agent_type_name = "Simulator"
        description = super().get_agent_description(instance_uid)
        if self._simulator_client_version:
            for attribute in description.identifying_attributes:
                if attribute.key == KEY_SERVICE_VERSION:
                    attribute.value.string_value = self._simulator_client_version
                    break
        for attribute in description.identifying_attributes:
            if attribute.key == KEY_SERVICE_TYPE:
                attribute.value.string_value = SIMULATOR_VALUE_AGENT_TYPE
                break
        config_version = str(self.config.config_version or "").strip()
        if config_version:
            description.non_identifying_attributes.append(
                anyvalue_pb2.KeyValue(
                    key=SIMULATOR_ATTRIBUTE_CONFIG_VERSION,
                    value=anyvalue_pb2.AnyValue(string_value=config_version),
                )
            )
        service_instance_id = str(self.config.service_instance_id or "").strip()
        if service_instance_id and not any(
            item.key == KEY_SERVICE_INSTANCE_ID
            for item in description.identifying_attributes
        ):
            description.identifying_attributes.append(
                anyvalue_pb2.KeyValue(
                    key=KEY_SERVICE_INSTANCE_ID,
                    value=anyvalue_pb2.AnyValue(string_value=service_instance_id),
                )
            )
        return description

    def _next_scripted_response(self, request_type: str) -> ScriptedResponse:
        """Return next scripted response for request type, wrapping sequence indexes."""
        sequence = self._scripted_responses.get(request_type)
        if not sequence:
            sequence = self._scripted_responses.get(SIMULATOR_REQUEST_FALLBACK_KEY)
        if not sequence:
            return ScriptedResponse(action=SIMULATOR_ACTION_ACCEPT)

        index = int(self._scripted_indexes.get(request_type, 0))
        selected = sequence[index % len(sequence)]
        self._scripted_indexes[request_type] = (index + 1) % len(sequence)
        return selected

    def _handle_scripted_request(
        self,
        request_type: str,
        default_handler: Callable[[], None],
    ) -> None:
        """Apply scripted response policy for one server request."""
        logger = logging.getLogger(__name__)
        response = self._next_scripted_response(request_type)
        logger.info(
            "simulator request=%s action=%s message=%s",
            request_type,
            response.action,
            response.message,
        )
        if response.action == SIMULATOR_ACTION_ACCEPT:
            default_handler()
            return
        if response.action == SIMULATOR_ACTION_IGNORE:
            return
        if response.action == SIMULATOR_ACTION_ERROR:
            raise AgentException(
                response.message or f"simulated failure for request '{request_type}'"
            )

    def handle_error_response(self, error_response: opamp_pb2.ServerErrorResponse) -> None:
        base = super()
        self._handle_scripted_request(
            REQUEST_ERROR_RESPONSE,
            lambda: base.handle_error_response(error_response),
        )

    def handle_remote_config(self, remote_config: opamp_pb2.AgentRemoteConfig) -> None:
        base = super()
        self._handle_scripted_request(
            REQUEST_REMOTE_CONFIG,
            lambda: base.handle_remote_config(remote_config),
        )

    def handle_connection_settings(
        self, connection_settings: opamp_pb2.ConnectionSettingsOffers
    ) -> None:
        base = super()
        self._handle_scripted_request(
            REQUEST_CONNECTION_SETTINGS,
            lambda: base.handle_connection_settings(connection_settings),
        )

    def handle_packages_available(
        self, packages_available: opamp_pb2.PackagesAvailable
    ) -> None:
        base = super()
        self._handle_scripted_request(
            REQUEST_PACKAGES_AVAILABLE,
            lambda: base.handle_packages_available(packages_available),
        )

    def handle_flags(self, flags: int) -> None:
        base = super()
        self._handle_scripted_request(
            REQUEST_FLAGS,
            lambda: base.handle_flags(flags),
        )

    def handle_capabilities(self, capabilities: int) -> None:
        base = super()
        self._handle_scripted_request(
            REQUEST_CAPABILITIES,
            lambda: base.handle_capabilities(capabilities),
        )

    def handle_agent_identification(
        self, agent_identification: opamp_pb2.AgentIdentification
    ) -> None:
        base = super()
        self._handle_scripted_request(
            REQUEST_AGENT_IDENTIFICATION,
            lambda: base.handle_agent_identification(agent_identification),
        )

    def handle_command(self, command: opamp_pb2.ServerToAgentCommand) -> None:
        base = super()
        self._handle_scripted_request(
            REQUEST_COMMAND,
            lambda: base.handle_command(command),
        )

    def handle_custom_capabilities(
        self, custom_capabilities: opamp_pb2.CustomCapabilities
    ) -> None:
        base = super()
        self._handle_scripted_request(
            REQUEST_CUSTOM_CAPABILITIES,
            lambda: base.handle_custom_capabilities(custom_capabilities),
        )

    def handle_custom_message(self, custom_message: opamp_pb2.CustomMessage) -> None:
        base = super()
        self._handle_scripted_request(
            REQUEST_CUSTOM_MESSAGE,
            lambda: base.handle_custom_message(custom_message),
        )


def main() -> None:
    """Run simulator bootstrap with scripted request-response behavior."""
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
            runtime_name="simulator",
            config_path=getattr(args, "config_path", None),
        )
        log_consumer_startup_banner(
            logger=logger,
            config=config,
            runtime_name="simulator",
            consumer_config_path=consumer_config_path,
        )

        if maybe_print_config_help(
            args=args,
            config=config,
            config_parameters_payload_builder=_config_parameters_payload,
        ):
            return

        # Simulator has no managed local runtime endpoint; force a synthetic port.
        if config.client_status_port is None:
            config.client_status_port = 1
        config = validate_runtime_server_config(
            config=config,
            localhost_base=LOCALHOST_BASE,
            missing_status_port_error=(
                "client_status_port must be set for simulator runtime normalization"
            ),
        )
        configure_observability_for_config(
            config=config,
            default_service_name="opamp-consumer-simulator",
        )
        if config.server_url is None:
            raise ValueError("validated runtime config missing server_url")
        if config.client_status_port is None:
            raise ValueError("validated runtime config missing client_status_port")
        client_status_port = int(config.client_status_port)
        if not _validate_simulator_dev_features_flag(logger):
            return

        logger.debug("setting up OpAMP simulator client")
        client = SimulatorOpAMPClient(config.server_url, config)
        client.launch_agent_process()
        client.add_agent_version(client_status_port)
        logger.info("introducing simulator client to server")
        asyncio.run(run_client(client))
        asyncio.run(client._heartbeat_loop(client_status_port))
        client.terminate_agent_process()
    except KeyboardInterrupt as keyboard_interrupt:
        print("... simulator keyboard\n %s", keyboard_interrupt)
    except SystemExit as system_exit:
        print("... simulator brutal exit\n %s", system_exit)
    except Exception as err: # pylint: disable=broad-except
        print("... simulator bzzzzzzzzzzz \n %s \n %s", err, traceback.format_exc())


if __name__ == "__main__":
    main()
    print("... Bye")
    sys.exit(1)
