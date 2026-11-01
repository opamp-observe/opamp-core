# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Test creation of the repository's OpAMP ServerToAgent protobuf payload."""

import sys
from pathlib import Path

from connection_settings_builder import ConnectionSettingsBuilder

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROVIDER_SOURCE = REPOSITORY_ROOT / "provider" / "src"
sys.path.insert(0, str(PROVIDER_SOURCE))

from opamp_provider.proto import opamp_pb2  # noqa: E402


def test_build_complete_connection_settings_message(tmp_path: Path) -> None:
    """The builder should translate shared and type-specific OpAMP fields."""
    certificate_path = tmp_path / "client.pem"
    certificate_path.write_bytes(b"certificate-data")
    definition = {
        "opamp": {
            "enabled": True,
            "destination_endpoint": "https://opamp.example",
            "headers": {"Authorization": "Bearer secret"},
            "certificate": {"cert_file": str(certificate_path)},
            "tls": {"min_version": "1.2", "cipher_suites": ["suite-one"]},
            "proxy": {"url": "http://proxy.example", "connect_headers": {"Proxy": "token"}},
        },
        "other_connections": {
            "database": {
                "enabled": False,
                "destination_endpoint": "postgres://db.example",
                "other_settings": {"port": 5432, "enabled": True},
            }
        },
    }
    message = ConnectionSettingsBuilder(opamp_pb2).build(definition)
    assert message.connection_settings.opamp.destination_endpoint == "https://opamp.example"
    assert message.connection_settings.opamp.headers.headers[0].key == "Authorization"
    assert message.connection_settings.opamp.certificate.cert == b"certificate-data"
    assert "database" not in message.connection_settings.other_connections
    assert len(message.connection_settings.hash) == 32
