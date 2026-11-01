# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Translate stored definitions into OpAMP protobuf messages."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

FIELD_CONNECTIONS = ("opamp", "own_metrics", "own_traces", "own_logs")
FIELD_OTHER_CONNECTIONS = "other_connections"
FIELD_HEADERS = "headers"
FIELD_CONNECT_HEADERS = "connect_headers"
FIELD_CERTIFICATE = "certificate"
FIELD_TLS = "tls"
FIELD_PROXY = "proxy"
FIELD_ENABLED = "enabled"
CERTIFICATE_FILE_FIELDS = {
    "cert_file": "cert",
    "private_key_file": "private_key",
    "ca_cert_file": "ca_cert",
}


class ConnectionSettingsBuilder:  # pylint: disable=too-few-public-methods
    """Build a ServerToAgent message using an injected generated OpAMP module.

    ``protobuf_module`` is an ``opamp_pb2``-compatible module. Injection keeps this package
    discrete and allows a host application to use the exact OpAMP payload version it owns.
    """

    def __init__(self, protobuf_module: ModuleType, file_root: Path | None = None) -> None:
        """Retain the generated module and optional base directory for relative file references."""
        self.protobuf_module = protobuf_module
        self.file_root = file_root or Path.cwd()

    def build(self, definition: dict[str, Any]) -> Any:
        """Create and populate one ServerToAgent message from ``definition``."""
        message = self.protobuf_module.ServerToAgent()
        offers = message.connection_settings
        canonical = json.dumps(definition, sort_keys=True, separators=(",", ":")).encode("utf-8")
        offers.hash = hashlib.sha256(canonical).digest()
        for field_name in FIELD_CONNECTIONS:
            field_definition = definition.get(field_name)
            if field_definition and field_definition.get(FIELD_ENABLED, True):
                self._populate_connection(getattr(offers, field_name), field_definition)
        other_definitions = definition.get(FIELD_OTHER_CONNECTIONS, {})
        for connection_name, field_definition in other_definitions.items():
            if not field_definition.get(FIELD_ENABLED, True):
                continue
            target = offers.other_connections[connection_name]
            self._populate_connection(target, field_definition)
            for setting_key, setting_value in field_definition.get("other_settings", {}).items():
                self._set_any_value(target.other_settings[setting_key], setting_value)
        return message

    def _populate_connection(self, target: Any, definition: dict[str, Any]) -> None:
        """Populate shared endpoint, auth, TLS, certificate, and proxy attributes."""
        if definition.get("destination_endpoint"):
            target.destination_endpoint = definition["destination_endpoint"]
        self._populate_headers(target.headers, definition.get(FIELD_HEADERS, {}))
        certificate = definition.get(FIELD_CERTIFICATE, {})
        for reference_field, target_field in CERTIFICATE_FILE_FIELDS.items():
            if certificate.get(reference_field):
                setattr(
                    target.certificate,
                    target_field,
                    self._read_file(certificate[reference_field]),
                )
        tls = definition.get(FIELD_TLS, {})
        for field_name in (
            "include_system_ca_certs_pool",
            "insecure_skip_verify",
            "min_version",
            "max_version",
        ):
            if field_name in tls:
                setattr(target.tls, field_name, tls[field_name])
        if tls.get("ca_pem_file"):
            ca_pem_bytes = self._read_file(tls["ca_pem_file"])
            target.tls.ca_pem_contents = ca_pem_bytes.decode("utf-8")
        target.tls.cipher_suites.extend(tls.get("cipher_suites", []))
        proxy = definition.get(FIELD_PROXY, {})
        if proxy.get("url"):
            target.proxy.url = proxy["url"]
        self._populate_headers(target.proxy.connect_headers, proxy.get(FIELD_CONNECT_HEADERS, {}))

    def _read_file(self, reference: str) -> bytes:
        """Read an absolute reference or one relative to the configured ``file_root``."""
        reference_path = Path(reference).expanduser()
        selected_path = (
            reference_path
            if reference_path.is_absolute()
            else self.file_root / reference_path
        )
        return selected_path.resolve().read_bytes()

    @staticmethod
    def _populate_headers(target: Any, headers: dict[str, str]) -> None:
        """Append all ``headers`` to an OpAMP Headers message."""
        for header_key, header_value in headers.items():
            header = target.headers.add()
            header.key = header_key
            header.value = header_value

    @staticmethod
    def _set_any_value(target: Any, value: Any) -> None:
        """Set a protobuf AnyValue scalar while preserving the Python scalar type."""
        if isinstance(value, bool):
            target.bool_value = value
        elif isinstance(value, int):
            target.int_value = value
        elif isinstance(value, float):
            target.double_value = value
        else:
            target.string_value = str(value)
