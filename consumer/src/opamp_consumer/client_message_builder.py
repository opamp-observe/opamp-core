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

"""Helpers for building outbound AgentToServer payloads."""

from __future__ import annotations

import logging
import mimetypes
import pathlib
import re
import time
from collections.abc import Callable
from typing import Any

from shared.agent_remote_config import AgentConfigMapFileEntry, build_agent_remote_config

from opamp_consumer.proto import opamp_pb2
from opamp_consumer.remote_config_status import (
    populate_agent_to_server_remote_config_status,
)
from opamp_consumer.reporting_flag import ReportingFlag

EFFECTIVE_CONFIG_CAPABILITY_NAME = "ReportsEffectiveConfig"
JSON_SUFFIXES = {".json"}
XML_SUFFIXES = {".xml"}
YAML_SUFFIXES = {".yaml", ".yml"}
JSON_CONTENT_TYPE = "application/json"
XML_CONTENT_TYPE = "application/xml"
YAML_CONTENT_TYPE = "application/x-yaml"
TEXT_PLAIN_CONTENT_TYPE = "text/plain"


def populate_agent_to_server(
    *,
    data: Any,
    msg: opamp_pb2.AgentToServer,
    get_agent_description: Callable[[], opamp_pb2.AgentDescription],
    get_agent_capabilities: Callable[[], int],
    is_capability_allowed: Callable[[str], bool],
    server_accepts_effective_config: bool,
    get_configuration_files: Callable[[], list[str]],
    get_custom_capabilities_payload: Callable[[], opamp_pb2.CustomCapabilities],
    populate_agent_to_server_health: Callable[
        [opamp_pb2.AgentToServer], opamp_pb2.AgentToServer
    ],
) -> opamp_pb2.AgentToServer:
    """Populate outbound AgentToServer fields based on reporting flags."""
    msg.sequence_num = data.msg_sequence_number
    data.msg_sequence_number = data.msg_sequence_number + 1
    msg.instance_uid = data.uid_instance

    if data.reporting_flags[ReportingFlag.REPORT_DESCRIPTION]:
        msg.agent_description.CopyFrom(get_agent_description())
        data.reporting_flags[ReportingFlag.REPORT_DESCRIPTION] = False

    if data.reporting_flags[ReportingFlag.REPORT_CAPABILITIES]:
        msg.capabilities = get_agent_capabilities()
        data.reporting_flags[ReportingFlag.REPORT_CAPABILITIES] = False

    if data.reporting_flags[ReportingFlag.REPORT_CUSTOM_CAPABILITIES]:
        custom_capabilities = get_custom_capabilities_payload()
        if custom_capabilities.capabilities:
            msg.custom_capabilities.CopyFrom(custom_capabilities)
        data.reporting_flags[ReportingFlag.REPORT_CUSTOM_CAPABILITIES] = False

    if data.reporting_flags[ReportingFlag.REPORT_HEALTH]:
        msg = populate_agent_to_server_health(msg)
        data.reporting_flags[ReportingFlag.REPORT_HEALTH] = False

    msg = populate_agent_to_server_remote_config_status(
        data=data,
        msg=msg,
    )

    if (
        data.config_changed
        and server_accepts_effective_config
        and is_capability_allowed(EFFECTIVE_CONFIG_CAPABILITY_NAME)
    ):
        msg = populate_agent_to_server_effective_config(
            msg=msg,
            configuration_files=get_configuration_files(),
        )
        data.config_changed = False
    return msg


def populate_agent_to_server_effective_config(
    *,
    msg: opamp_pb2.AgentToServer,
    configuration_files: list[str],
) -> opamp_pb2.AgentToServer:
    """Populate AgentToServer.effective_config from local configuration files."""
    logger = logging.getLogger(__name__)
    logger.debug("populate_agent_to_server_effective_config using %s", configuration_files)
    
    msg.ClearField("effective_config")
    file_entries = _read_effective_config_entries(configuration_files)
    if not file_entries:
        logger.warning(
            "effective_config generation skipped because no readable configuration files were found"
        )
        return msg

    remote_config = build_agent_remote_config(
        opamp_pb2.AgentRemoteConfig(),
        file_entries,
        include_hash=False,
    )
    msg.effective_config.config_map.CopyFrom(remote_config.config)
    logger.info(
        "generated effective_config payload file_count=%s files=%s",
        len(file_entries),
        ", ".join(file_entry.target_name for file_entry in file_entries),
    )
    return msg


def _read_effective_config_entries(
    configuration_files: list[str],
) -> list[AgentConfigMapFileEntry]:
    """Read local config files into shared AgentConfigMap entry records."""
    logger = logging.getLogger(__name__)
    file_entries: list[AgentConfigMapFileEntry] = []
    for raw_path in configuration_files:
        normalized_path = str(raw_path or "").strip()
        if not normalized_path:
            continue
        source_path = pathlib.Path(normalized_path)
        try:
            body = source_path.read_bytes()
        except OSError as error:
            logger.warning(
                "failed to read effective_config source file path=%s error=%s",
                normalized_path,
                error,
            )
            continue
        file_entries.append(
            AgentConfigMapFileEntry(
                target_name=normalized_path,
                body=body,
                content_type=_resolve_effective_config_content_type(source_path),
            )
        )
    return file_entries


def _resolve_effective_config_content_type(source_path: pathlib.Path) -> str:
    """Infer a stable config content type from a local configuration file path."""
    suffix = source_path.suffix.lower()
    if suffix in JSON_SUFFIXES:
        return JSON_CONTENT_TYPE
    if suffix in XML_SUFFIXES:
        return XML_CONTENT_TYPE
    if suffix in YAML_SUFFIXES:
        return YAML_CONTENT_TYPE
    guessed_type, _ = mimetypes.guess_type(source_path.name)
    return guessed_type or TEXT_PLAIN_CONTENT_TYPE


def populate_agent_to_server_health(
    *,
    data: Any,
    msg: opamp_pb2.AgentToServer,
    health_from_metrics: Callable[[opamp_pb2.AgentToServer, str], opamp_pb2.AgentToServer],
    health_key: str,
    err_prefix: str,
    value_heartbeat_status: str,
    value_supervisor_no_state: str,
) -> opamp_pb2.AgentToServer:
    """Populate health fields on AgentToServer using latest heartbeat poll state."""
    healthy = True
    if data.last_heartbeat_results:
        healthy = (
            data.last_heartbeat_http_codes is not None
            and data.last_heartbeat_http_codes[health_key]
        )
        last_error = ""
        for value in data.last_heartbeat_results.values():
            text = str(value)
            if text.startswith(err_prefix):
                healthy = False
                last_error = text

            msg = health_from_metrics(msg, text)

        msg.health.status = value_heartbeat_status
        if not healthy and last_error:
            msg.health.last_error = last_error
    else:
        healthy = False
        msg.health.last_error = value_supervisor_no_state

    msg.health.start_time_unix_nano = time.time_ns() - data.launched_at
    msg.health.status_time_unix_nano = time.time_ns()
    msg.health.healthy = int(healthy)
    logging.getLogger(__name__).debug("Health info sending is >%s<", msg.health)
    return msg


def parse_fluentbit_metrics_health(
    msg: opamp_pb2.AgentToServer,
    text: str,
) -> opamp_pb2.AgentToServer:
    """Parse Fluent Bit metrics text and update component health entries in-place."""
    lines = text.splitlines()
    metric_pattern: str = 'errors_total{name="'
    for line in lines:
        line_idx = line.find(metric_pattern)
        if line_idx >= 0:
            name_start: int = line_idx + len(metric_pattern)
            name_end: int = line.index('"', name_start)
            component_name: str = line[name_start:name_end]
            last_num_text = re.findall(r"\d+(?:\.\d+)?", line[name_end:])[-1]
            last_num = int(last_num_text)
            msg.health.component_health_map[component_name].CopyFrom(
                opamp_pb2.ComponentHealth(
                    healthy=(last_num == 0),
                    status=f"error count={last_num_text}",
                )
            )
            logging.getLogger(__name__).debug(
                "Component metric %s",
                msg.health.component_health_map[component_name],
            )
    return msg
