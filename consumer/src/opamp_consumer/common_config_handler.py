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

"""Helpers for applying OpAMP `AgentRemoteConfig` payloads."""

from __future__ import annotations

import json
import logging
import pathlib
import shutil
from datetime import datetime
from typing import TYPE_CHECKING

from defusedxml import ElementTree as xml_etree
from shared.agent_remote_config import calculate_agent_config_map_hash

from opamp_consumer.proto import opamp_pb2
from opamp_consumer.remote_agent_config_content_type_error import (
    RemoteAgentConfigContentTypeError,
)
from opamp_consumer.remote_agent_config_error import RemoteAgentConfigError
from opamp_consumer.remote_agent_config_hash_mismatch_error import (
    RemoteAgentConfigHashMismatchError,
)
from opamp_consumer.remote_agent_config_validation_error import (
    RemoteAgentConfigValidationError,
)
from opamp_consumer.remote_agent_config_write_error import (
    RemoteAgentConfigWriteError,
)

if TYPE_CHECKING:
    from opamp_consumer.opamp_client_interface import OpAMPClientInterface

LOGGER = logging.getLogger(__name__)
BACKUP_TIMESTAMP_FORMAT = "%Y-%m-%d--%H-%M-%S"
REMOTE_CONFIG_STATUS_APPLIED = opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_APPLIED
REMOTE_CONFIG_STATUS_APPLYING = opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_APPLYING
REMOTE_CONFIG_STATUS_FAILED = opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_FAILED
STRUCTURED_JSON_CONTENT_TYPES = {"application/json", "text/json"}
STRUCTURED_XML_CONTENT_TYPES = {"application/xml", "text/xml"}
STRUCTURED_YAML_CONTENT_TYPES = {
    "application/yaml",
    "application/x-yaml",
    "text/yaml",
    "text/x-yaml",
}
RECOGNIZED_BINARY_CONTENT_TYPES = {
    "application/gzip",
    "application/octet-stream",
    "application/pdf",
    "application/zip",
}
RECOGNIZED_BINARY_PREFIXES = ("audio/", "font/", "image/", "video/")


class CommonConfigHandler:
    """Static helpers for validating and applying remote config payloads."""

    @staticmethod
    def apply_remote_config(
        remote_config: opamp_pb2.AgentRemoteConfig,
        opamp_client: OpAMPClientInterface,
    ) -> None:
        """Validate and apply a remote-config payload to the local filesystem."""
        try:
            CommonConfigHandler._validate_remote_config_hash(remote_config)

            config_entries = remote_config.config.config_map
            if not config_entries:
                LOGGER.info("remote config payload contained no config files")
                opamp_client.set_remote_config_status(
                    remote_config,
                    REMOTE_CONFIG_STATUS_APPLIED,
                )
                return

            for filename, config_file in sorted(config_entries.items()):
                CommonConfigHandler._apply_config_file(
                    filename=filename,
                    config_file=config_file,
                    opamp_client=opamp_client,
                )

            opamp_client.set_remote_config_status(
                remote_config,
                REMOTE_CONFIG_STATUS_APPLYING,
            )

            try:
                reloaded = opamp_client.hot_reload()
            except Exception as reload_error:  # pragma: no cover - defensive interface guard
                opamp_client.set_remote_config_status(
                    remote_config,
                    REMOTE_CONFIG_STATUS_FAILED,
                    str(reload_error),
                )
                LOGGER.warning("remote config applied but hot reload failed: %s", reload_error)
                return
            opamp_client.set_remote_config_status(
                remote_config,
                REMOTE_CONFIG_STATUS_APPLIED,
            )
            if reloaded:
                LOGGER.info("remote config hot reload triggered successfully")
            else:
                LOGGER.info("remote config applied without hot reload support")
        except RemoteAgentConfigError as apply_error:
            opamp_client.set_remote_config_status(
                remote_config,
                REMOTE_CONFIG_STATUS_FAILED,
                str(apply_error),
            )
            raise

    @staticmethod
    def calculate_config_hash(config: opamp_pb2.AgentConfigMap) -> bytes:
        """Return a SHA-256 digest for the deterministic serialized config map."""
        return calculate_agent_config_map_hash(config)

    @staticmethod
    def _validate_remote_config_hash(remote_config: opamp_pb2.AgentRemoteConfig) -> None:
        """Compare the supplied `config_hash` against the actual config-map digest."""
        if not remote_config.config_hash:
            LOGGER.info("remote config payload did not include config_hash")
            return

        calculated_hash = CommonConfigHandler.calculate_config_hash(remote_config.config)
        if calculated_hash != remote_config.config_hash:
            raise RemoteAgentConfigHashMismatchError(
                "remote config hash mismatch: "
                f"expected={remote_config.config_hash.hex()} "
                f"actual={calculated_hash.hex()}"
            )
        LOGGER.info("remote config hash matched provided config_hash=%s", calculated_hash.hex())

    @staticmethod
    def _apply_config_file(
        *,
        filename: str,
        config_file: opamp_pb2.AgentConfigFile,
        opamp_client: OpAMPClientInterface,
    ) -> None:
        """Apply one config file with backup, validation, cleanup, and recovery."""
        target_path = pathlib.Path(filename)
        backup_path = CommonConfigHandler._create_backup_if_present(target_path)
        try:
            CommonConfigHandler._validate_config_file_payload(
                filename=filename,
                config_file=config_file,
            )
        except RemoteAgentConfigError:
            CommonConfigHandler._delete_backup_copy(backup_path)
            raise

        try:
            opamp_client.write_config_file(filename, config_file.body)
        except RemoteAgentConfigWriteError:
            CommonConfigHandler._recover_failed_write(
                target_path=target_path,
                backup_path=backup_path,
            )
            raise
        except Exception as write_error:
            CommonConfigHandler._recover_failed_write(
                target_path=target_path,
                backup_path=backup_path,
            )
            raise RemoteAgentConfigWriteError(
                f"failed to write remote config file '{filename}': {write_error}"
            ) from write_error

        CommonConfigHandler._delete_backup_copy(backup_path)
        LOGGER.info("applied remote config file path=%s", target_path)

    @staticmethod
    def _create_backup_if_present(target_path: pathlib.Path) -> pathlib.Path | None:
        """Create a timestamped backup of an existing file before modification."""
        if not target_path.exists():
            return None

        timestamp = datetime.now().strftime(BACKUP_TIMESTAMP_FORMAT)
        backup_path = target_path.with_name(f"{target_path.name}.{timestamp}")
        shutil.copy2(target_path, backup_path)
        LOGGER.info("created remote config backup path=%s backup=%s", target_path, backup_path)
        return backup_path

    @staticmethod
    def _delete_backup_copy(backup_path: pathlib.Path | None) -> None:
        """Remove a temporary backup copy once processing has completed safely."""
        if backup_path is None or not backup_path.exists():
            return
        backup_path.unlink()

    @staticmethod
    def _recover_failed_write(
        *,
        target_path: pathlib.Path,
        backup_path: pathlib.Path | None,
    ) -> None:
        """Remove any partial write and restore the prior file if a backup exists."""
        if target_path.exists():
            target_path.unlink()
        if backup_path is not None and backup_path.exists():
            backup_path.replace(target_path)

    @staticmethod
    def _validate_config_file_payload(
        *,
        filename: str,
        config_file: opamp_pb2.AgentConfigFile,
    ) -> None:
        """Reject binary payloads and validate structured text payloads."""
        normalized_content_type = CommonConfigHandler._normalize_content_type(
            config_file.content_type
        )
        if not normalized_content_type:
            return
        if CommonConfigHandler._is_recognized_binary_content_type(normalized_content_type):
            raise RemoteAgentConfigContentTypeError(
                f"binary content type is not supported for '{filename}': "
                f"{normalized_content_type}"
            )

        body_text = CommonConfigHandler._decode_body_text(
            filename=filename,
            body=config_file.body,
        )
        CommonConfigHandler._validate_structured_text(
            filename=filename,
            body_text=body_text,
            normalized_content_type=normalized_content_type,
        )

    @staticmethod
    def _normalize_content_type(content_type: str) -> str:
        """Normalize content type values by lowercasing and dropping parameters."""
        return str(content_type or "").split(";", 1)[0].strip().lower()

    @staticmethod
    def _is_recognized_binary_content_type(content_type: str) -> bool:
        """Return whether the content type is one we explicitly treat as binary."""
        return content_type in RECOGNIZED_BINARY_CONTENT_TYPES or content_type.startswith(
            RECOGNIZED_BINARY_PREFIXES
        )

    @staticmethod
    def _decode_body_text(*, filename: str, body: bytes) -> str:
        """Decode config bytes as UTF-8 text before validation or file writes."""
        try:
            return body.decode("utf-8")
        except UnicodeDecodeError as decode_error:
            raise RemoteAgentConfigValidationError(
                f"remote config file '{filename}' is not valid UTF-8 text"
            ) from decode_error

    @staticmethod
    def _validate_structured_text(
        *,
        filename: str,
        body_text: str,
        normalized_content_type: str,
    ) -> None:
        """Run basic validation for well-known structured text content types."""
        # TODO: Investigate reusing the editor/schema validation logic for deeper checks.
        if normalized_content_type in STRUCTURED_JSON_CONTENT_TYPES:
            CommonConfigHandler._validate_json_text(filename=filename, body_text=body_text)
            return
        if normalized_content_type in STRUCTURED_XML_CONTENT_TYPES:
            CommonConfigHandler._validate_xml_text(filename=filename, body_text=body_text)
            return
        if normalized_content_type in STRUCTURED_YAML_CONTENT_TYPES:
            CommonConfigHandler._validate_yaml_text(filename=filename, body_text=body_text)

    @staticmethod
    def _validate_json_text(*, filename: str, body_text: str) -> None:
        """Validate JSON payload syntax."""
        try:
            json.loads(body_text)
        except json.JSONDecodeError as parse_error:
            raise RemoteAgentConfigValidationError(
                f"remote config file '{filename}' contains invalid JSON: {parse_error}"
            ) from parse_error

    @staticmethod
    def _validate_xml_text(*, filename: str, body_text: str) -> None:
        """Validate XML payload syntax."""
        try:
            xml_etree.fromstring(body_text)
        except xml_etree.ParseError as parse_error:
            raise RemoteAgentConfigValidationError(
                f"remote config file '{filename}' contains invalid XML: {parse_error}"
            ) from parse_error

    @staticmethod
    def _validate_yaml_text(*, filename: str, body_text: str) -> None:
        """Validate YAML payload syntax using PyYAML when available."""
        try:
            import yaml  # type: ignore[import-not-found]
        except ImportError as import_error:
            raise RemoteAgentConfigValidationError(
                "YAML validation requires PyYAML to be installed"
            ) from import_error

        try:
            yaml.safe_load(body_text)
        except Exception as parse_error:  # pragma: no cover - parser-specific subclasses vary
            raise RemoteAgentConfigValidationError(
                f"remote config file '{filename}' contains invalid YAML: {parse_error}"
            ) from parse_error
