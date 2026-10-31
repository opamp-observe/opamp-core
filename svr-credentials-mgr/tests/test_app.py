# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Test service API and UI routes."""

import json
from io import BytesIO
from pathlib import Path

import pytest
from opamp_plaintext_keyring import PlaintextFileKeyring
from quart import Quart
from werkzeug.datastructures import FileStorage

from svr_credentials_manager_service.app import create_app
from svr_credentials_manager_service.opamp_integration import (
    register_credentials_manager_feature,
)
from svr_credentials_manager_service.storage import ClientMappingStore, CredentialStore


@pytest.mark.asyncio
async def test_connection_and_mapping_workflow(tmp_path: Path) -> None:
    """The API should support named definitions and many-to-one mappings."""
    app = create_app(
        credential_store=CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json")),
        mapping_store=ClientMappingStore(tmp_path / "mappings.json"),
        file_directory=tmp_path / "connection-files",
    )
    client = app.test_client()
    definition = {"opamp": {"destination_endpoint": "https://example.test", "headers": {}}}
    response = await client.put(
        "/svr-credentials-manager-service/api/v1/connections/shared",
        json={"definition": definition},
    )
    assert response.status_code == 200
    response = await client.put(
        "/svr-credentials-manager-service/api/v1/mappings",
        json={"mappings": {"agent-one": "shared", "agent-two": "shared"}},
    )
    assert response.status_code == 200
    assert (await response.get_json())["mappings"]["agent-two"] == "shared"
    response = await client.delete(
        "/svr-credentials-manager-service/api/v1/connections/shared"
    )
    assert response.status_code == 400
    response = await client.get("/svr-credentials-manager-service/ui")
    assert response.status_code == 200
    response_data = await response.get_data()
    assert b"Server Credentials Manager" in response_data
    assert response.headers["Cache-Control"].startswith("no-store")
    assert b"ui/help" in response_data
    assert b"opamp-logo.png" in response_data
    assert b">Help<" in response_data
    assert b"Reload UI" in response_data
    assert b"Add Test Clients" in response_data
    assert b'id="reload-ui" class="reload-ui hidden"' in response_data
    assert b'id="add-test-clients" class="reload-ui secondary-action hidden"' in response_data
    assert b"connections-table" in response_data
    assert b"filter-connection-name" in response_data
    assert b"filter-assigned-client" in response_data
    assert b"assignment-dialog" in response_data
    assert b"auth-token-input" not in response_data
    assert b"Assign" in response_data
    assert b"Licensed under Apache 2.0" in response_data
    assert b"Client mappings" not in response_data
    assert b"Existing credential" not in response_data
    assert b'delete-connection' not in response_data
    assert b'id="other-name" disabled' in response_data
    assert b"__SVR_CREDENTIALS_ASSET_VERSION__" not in response_data
    assert b"app.css?v=" in response_data
    asset_response = await client.get(
        "/svr-credentials-manager-service/ui/assets/app.css"
    )
    assert asset_response.status_code == 200
    assert asset_response.headers["Cache-Control"].startswith("no-store")
    logo_response = await client.get(
        "/svr-credentials-manager-service/ui/assets/opamp-logo.png"
    )
    assert logo_response.status_code == 200
    assert logo_response.headers["Cache-Control"].startswith("no-store")
    help_response = await client.get("/svr-credentials-manager-service/ui/help")
    assert help_response.status_code == 200
    help_data = await help_response.get_data()
    assert b"Server Credentials Manager UI" in help_data
    assert b"Defined Connections Filters" in help_data
    assert help_response.headers["Cache-Control"].startswith("no-store")


@pytest.mark.asyncio
async def test_health_reports_dev_features_disabled_by_default(tmp_path: Path) -> None:
    """The UI health payload should disable dev-only controls by default."""
    app = create_app(
        credential_store=CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json")),
        mapping_store=ClientMappingStore(tmp_path / "mappings.json"),
        file_directory=tmp_path / "connection-files",
    )

    response = await app.test_client().get("/svr-credentials-manager-service/api/v1/health")

    assert response.status_code == 200
    assert (await response.get_json())["app_enable_dev_features"] is False


@pytest.mark.asyncio
async def test_health_reports_dev_features_when_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The UI health payload should expose APP_ENABLE_DEV_FEATURES when truthy."""
    monkeypatch.setenv("APP_ENABLE_DEV_FEATURES", "true")
    app = create_app(
        credential_store=CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json")),
        mapping_store=ClientMappingStore(tmp_path / "mappings.json"),
        file_directory=tmp_path / "connection-files",
    )

    response = await app.test_client().get("/svr-credentials-manager-service/api/v1/health")

    assert response.status_code == 200
    assert (await response.get_json())["app_enable_dev_features"] is True


@pytest.mark.asyncio
async def test_upload_connection_file_returns_backend_reference(tmp_path: Path) -> None:
    """A selected PEM file should be copied into managed storage and referenced by path."""
    app = create_app(
        credential_store=CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json")),
        mapping_store=ClientMappingStore(tmp_path / "mappings.json"),
        file_directory=tmp_path / "connection-files",
    )
    client = app.test_client()
    response = await client.post(
        "/svr-credentials-manager-service/api/v1/files",
        files={
            "file": FileStorage(
                stream=BytesIO(b"certificate-data"),
                filename="client.pem",
            )
        },
    )
    assert response.status_code == 200
    reference = Path((await response.get_json())["reference"])
    assert reference.read_bytes() == b"certificate-data"


@pytest.mark.asyncio
async def test_tls_versions_are_loaded_from_configuration(tmp_path: Path) -> None:
    """The TLS options endpoint should return values from its configured JSON file."""
    configuration_path = tmp_path / "tls_versions.json"
    configuration_path.write_text('{"versions":["1.2","1.3"]}', encoding="utf-8")
    app = create_app(
        credential_store=CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json")),
        mapping_store=ClientMappingStore(tmp_path / "mappings.json"),
        file_directory=tmp_path / "connection-files",
        tls_versions_path=configuration_path,
    )
    response = await app.test_client().get(
        "/svr-credentials-manager-service/api/v1/options/tls-versions"
    )
    assert response.status_code == 200
    assert (await response.get_json())["versions"] == ["1.2", "1.3"]


@pytest.mark.asyncio
async def test_mapping_store_path_can_be_loaded_from_service_config(tmp_path: Path) -> None:
    """The service should honor mapping storage from the shared OpAMP config object."""
    config_path = tmp_path / "opamp.json"
    configured_mapping_path = tmp_path / "runtime" / "client-mappings.json"
    config_path.write_text(
        json.dumps(
            {
                "opamp": {
                    "svr_credentials_manager": {
                        "storage": {
                            "mapping_path": "runtime/client-mappings.json",
                        }
                    }
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    app = create_app(
        credential_store=CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json")),
        config_path=config_path,
        file_directory=tmp_path / "connection-files",
    )
    client = app.test_client()
    response = await client.put(
        "/svr-credentials-manager-service/api/v1/connections/shared",
        json={"definition": {"opamp": {"destination_endpoint": "https://example.test"}}},
    )
    assert response.status_code == 200

    response = await client.put(
        "/svr-credentials-manager-service/api/v1/mappings",
        json={"mappings": {"agent-one": "shared"}},
    )

    assert response.status_code == 200
    assert configured_mapping_path.exists()
    assert json.loads(configured_mapping_path.read_text(encoding="utf-8")) == {
        "clients": {"agent-one": "shared"}
    }


@pytest.mark.asyncio
async def test_common_opamp_config_can_drive_default_storage_paths(tmp_path: Path) -> None:
    """Default store paths should come from the shared OpAMP config object."""
    config_path = tmp_path / "opamp.json"
    tls_versions_path = tmp_path / "runtime" / "tls_versions.json"
    tls_versions_path.parent.mkdir(parents=True, exist_ok=True)
    tls_versions_path.write_text('{"versions":["1.0","1.3"]}', encoding="utf-8")
    config_path.write_text(
        json.dumps(
            {
                "opamp": {
                    "svr_credentials_manager": {
                        "storage": {
                            "plaintext_path": "runtime/credentials.json",
                            "mapping_path": "runtime/mappings.json",
                            "file_directory": "runtime/connection-files",
                            "tls_versions_path": "runtime/tls_versions.json",
                        }
                    }
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    app = create_app(config_path=config_path)
    client = app.test_client()

    save_response = await client.put(
        "/svr-credentials-manager-service/api/v1/connections/shared",
        json={"definition": {"opamp": {"destination_endpoint": "https://example.test"}}},
    )
    assert save_response.status_code == 200

    mapping_response = await client.put(
        "/svr-credentials-manager-service/api/v1/mappings",
        json={"mappings": {"agent-one": "shared"}},
    )
    assert mapping_response.status_code == 200

    upload_response = await client.post(
        "/svr-credentials-manager-service/api/v1/files",
        files={
            "file": FileStorage(
                stream=BytesIO(b"certificate-data"),
                filename="client.pem",
            )
        },
    )
    assert upload_response.status_code == 200
    uploaded_reference = Path((await upload_response.get_json())["reference"])

    tls_response = await client.get(
        "/svr-credentials-manager-service/api/v1/options/tls-versions"
    )
    assert tls_response.status_code == 200
    assert (await tls_response.get_json())["versions"] == ["1.0", "1.3"]

    configured_credentials_path = tmp_path / "runtime" / "credentials.json"
    configured_mapping_path = tmp_path / "runtime" / "mappings.json"
    configured_file_directory = tmp_path / "runtime" / "connection-files"
    assert configured_credentials_path.exists()
    assert configured_mapping_path.exists()
    assert uploaded_reference.parent == configured_file_directory.resolve()
    assert uploaded_reference.read_bytes() == b"certificate-data"


@pytest.mark.asyncio
async def test_env_storage_overrides_common_opamp_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Environment paths should override the shared OpAMP config file."""
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(
            {
                "opamp": {
                    "svr_credentials_manager": {
                        "storage": {
                            "mapping_path": "runtime/from-config.json",
                        }
                    }
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    env_mapping_path = tmp_path / "runtime" / "from-env.json"
    monkeypatch.setenv("SVR_CREDENTIALS_MAPPING_PATH", str(env_mapping_path))
    app = create_app(
        credential_store=CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json")),
        config_path=config_path,
        file_directory=tmp_path / "connection-files",
    )
    client = app.test_client()
    connection_response = await client.put(
        "/svr-credentials-manager-service/api/v1/connections/shared",
        json={"definition": {"opamp": {"destination_endpoint": "https://example.test"}}},
    )
    assert connection_response.status_code == 200

    response = await client.put(
        "/svr-credentials-manager-service/api/v1/mappings",
        json={"mappings": {"agent-one": "shared"}},
    )

    assert response.status_code == 200
    assert not (tmp_path / "runtime" / "from-config.json").exists()
    assert env_mapping_path.exists()
    assert json.loads(env_mapping_path.read_text(encoding="utf-8")) == {
        "clients": {"agent-one": "shared"}
    }


@pytest.mark.asyncio
async def test_service_config_can_switch_api_authentication_off(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The service config file should be able to disable API auth explicitly."""
    config_path = tmp_path / "service-config.json"
    config_path.write_text(
        json.dumps(
            {
                "authorization": {
                    "ui_use_authorization": "none",
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SVR_CREDENTIALS_CONFIG_PATH", str(config_path))
    app = create_app(
        credential_store=CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json")),
        mapping_store=ClientMappingStore(tmp_path / "mappings.json"),
        file_directory=tmp_path / "connection-files",
    )

    response = await app.test_client().get("/svr-credentials-manager-service/api/v1/mappings")

    assert response.status_code == 200
    assert (await response.get_json())["mappings"] == {}


@pytest.mark.asyncio
async def test_common_opamp_config_can_enable_static_api_auth(tmp_path: Path) -> None:
    """Static bearer auth settings should be readable from the shared OpAMP config."""
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(
            {
                "opamp": {
                    "svr_credentials_manager": {
                        "authorization": {
                            "ui_use_authorization": "config-token",
                            "ui_auth_static_token": "expected-token",
                        }
                    }
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    app = create_app(
        config_path=config_path,
        credential_store=CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json")),
        mapping_store=ClientMappingStore(tmp_path / "mappings.json"),
        file_directory=tmp_path / "connection-files",
    )

    unauthorized_response = await app.test_client().get(
        "/svr-credentials-manager-service/api/v1/mappings"
    )
    authorized_response = await app.test_client().get(
        "/svr-credentials-manager-service/api/v1/mappings",
        headers={"Authorization": "Bearer expected-token"},
    )

    assert unauthorized_response.status_code == 401
    assert (await unauthorized_response.get_json())["error"] == "missing bearer token"
    assert authorized_response.status_code == 200
    assert (await authorized_response.get_json())["mappings"] == {}


@pytest.mark.asyncio
async def test_opamp_integration_registers_embedded_credentials_manager_from_shared_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The provider embedding entrypoint should use the shared OpAMP config shape."""
    config_path = tmp_path / "opamp.json"
    tls_versions_path = tmp_path / "runtime" / "tls_versions.json"
    tls_versions_path.parent.mkdir(parents=True, exist_ok=True)
    tls_versions_path.write_text('{"versions":["1.2","1.3"]}', encoding="utf-8")
    config_path.write_text(
        json.dumps(
            {
                "opamp": {
                    "svr_credentials_manager": {
                        "storage": {
                            "plaintext_path": "runtime/credentials.json",
                            "mapping_path": "runtime/mappings.json",
                            "file_directory": "runtime/connection-files",
                            "tls_versions_path": "runtime/tls_versions.json",
                        },
                        "authorization": {
                            "ui_use_authorization": "none",
                        },
                    }
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPAMP_CONFIG_PATH", str(config_path))
    app = Quart(__name__)
    register_credentials_manager_feature(app)
    client = app.test_client()

    save_response = await client.put(
        "/svr-credentials-manager-service/api/v1/connections/shared",
        json={"definition": {"opamp": {"destination_endpoint": "https://example.test"}}},
    )
    assert save_response.status_code == 200

    mapping_response = await client.put(
        "/svr-credentials-manager-service/api/v1/mappings",
        json={"mappings": {"agent-one": "shared"}},
    )
    assert mapping_response.status_code == 200

    ui_response = await client.get("/svr-credentials-manager-service/ui")
    tls_response = await client.get(
        "/svr-credentials-manager-service/api/v1/options/tls-versions"
    )

    assert ui_response.status_code == 200
    assert tls_response.status_code == 200
    assert (await tls_response.get_json())["versions"] == ["1.2", "1.3"]
    assert (tmp_path / "runtime" / "credentials.json").exists()
    assert (tmp_path / "runtime" / "mappings.json").exists()


@pytest.mark.asyncio
async def test_mock_clients_can_be_seeded_for_assignment_testing(tmp_path: Path) -> None:
    """The service should seed and return 20 mock clients for standalone testing."""
    app = create_app(
        credential_store=CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json")),
        mapping_store=ClientMappingStore(tmp_path / "mappings.json"),
        file_directory=tmp_path / "connection-files",
    )
    client = app.test_client()
    initial_response = await client.get(
        "/svr-credentials-manager-service/api/v1/mock-clients"
    )
    assert initial_response.status_code == 200
    assert (await initial_response.get_json())["clients"] == []

    seed_response = await client.post(
        "/svr-credentials-manager-service/api/v1/mock-clients"
    )
    assert seed_response.status_code == 200
    seeded_clients = (await seed_response.get_json())["clients"]
    assert len(seeded_clients) == 20
    assert seeded_clients[0] == "mock-client-01"
    assert seeded_clients[-1] == "mock-client-20"

    seeded_list_response = await client.get(
        "/svr-credentials-manager-service/api/v1/mock-clients"
    )
    assert seeded_list_response.status_code == 200
    assert (await seeded_list_response.get_json())["clients"] == seeded_clients


@pytest.mark.asyncio
async def test_api_requires_bearer_token_when_static_auth_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """API requests should require a bearer token when static auth is enabled."""
    monkeypatch.setenv("SVR_CREDENTIALS_UI_USE_AUTHORIZATION", "config-token")
    monkeypatch.setenv("UI_AUTH_STATIC_TOKEN", "expected-token")
    app = create_app(
        credential_store=CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json")),
        mapping_store=ClientMappingStore(tmp_path / "mappings.json"),
        file_directory=tmp_path / "connection-files",
    )

    api_response = await app.test_client().get("/svr-credentials-manager-service/api/v1/mappings")

    assert api_response.status_code == 401
    assert api_response.headers["WWW-Authenticate"] == (
        'Bearer realm="svr-credentials-manager-service"'
    )
    assert (await api_response.get_json())["error"] == "missing bearer token"

    ui_response = await app.test_client().get("/svr-credentials-manager-service/ui")
    assert ui_response.status_code == 200


@pytest.mark.asyncio
async def test_api_accepts_valid_bearer_token_when_static_auth_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """API requests should succeed when the configured static bearer token is supplied."""
    monkeypatch.setenv("SVR_CREDENTIALS_UI_USE_AUTHORIZATION", "config-token")
    monkeypatch.setenv("UI_AUTH_STATIC_TOKEN", "expected-token")
    app = create_app(
        credential_store=CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json")),
        mapping_store=ClientMappingStore(tmp_path / "mappings.json"),
        file_directory=tmp_path / "connection-files",
    )

    response = await app.test_client().get(
        "/svr-credentials-manager-service/api/v1/mappings",
        headers={"Authorization": "Bearer expected-token"},
    )

    assert response.status_code == 200
    assert (await response.get_json())["mappings"] == {}


@pytest.mark.asyncio
async def test_api_rejects_invalid_bearer_token_when_static_auth_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """API requests should reject incorrect static bearer tokens."""
    monkeypatch.setenv("SVR_CREDENTIALS_UI_USE_AUTHORIZATION", "config-token")
    monkeypatch.setenv("UI_AUTH_STATIC_TOKEN", "expected-token")
    app = create_app(
        credential_store=CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json")),
        mapping_store=ClientMappingStore(tmp_path / "mappings.json"),
        file_directory=tmp_path / "connection-files",
    )

    response = await app.test_client().get(
        "/svr-credentials-manager-service/api/v1/mappings",
        headers={"Authorization": "Bearer wrong-token"},
    )

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == (
        'Bearer realm="svr-credentials-manager-service"'
    )
    assert (await response.get_json())["error"] == "invalid bearer token"


@pytest.mark.asyncio
async def test_get_mappings_reconciles_missing_connections_and_reports_cleanup(
    tmp_path: Path,
) -> None:
    """Loading mappings should remove stale assignments and return a cleanup message."""
    credential_store = CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json"))
    credential_store.save("shared", {"opamp": {"destination_endpoint": "https://example.test"}})
    mapping_store = ClientMappingStore(tmp_path / "mappings.json")
    mapping_store.save(
        {
            "missing-node": "missing-connection",
            "valid-node": "shared",
        }
    )
    app = create_app(
        credential_store=credential_store,
        mapping_store=mapping_store,
        file_directory=tmp_path / "connection-files",
    )

    response = await app.test_client().get("/svr-credentials-manager-service/api/v1/mappings")

    assert response.status_code == 200
    payload = await response.get_json()
    assert payload["mappings"] == {"valid-node": "shared"}
    assert payload["reconciliation"]["message"].startswith(
        "Removed assignments for missing connections:"
    )
    assert payload["reconciliation"]["removed_assignments"] == [
        {
            "client_id": "missing-node",
            "connection_name": "missing-connection",
        }
    ]
    assert mapping_store.load() == {"valid-node": "shared"}


@pytest.mark.asyncio
async def test_apply_connection_writes_fallback_json_when_provider_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Standalone apply should fall back to JSON logging even without protobuf runtime support."""
    from svr_credentials_manager_service import apply_service

    fallback_log_path = tmp_path / "connection-apply-fallback.jsonl"
    monkeypatch.setenv(
        "SVR_CREDENTIALS_CONNECTION_APPLY_LOG_PATH",
        str(fallback_log_path),
    )
    monkeypatch.delenv("SVR_CREDENTIALS_PROVIDER_BASE_URL", raising=False)
    credential_store = CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json"))
    credential_store.save(
        "shared",
        {"opamp": {"destination_endpoint": "https://example.test", "headers": {}}},
    )
    mapping_store = ClientMappingStore(tmp_path / "mappings.json")
    mapping_store.save({"valid-node": "shared"})
    app = create_app(
        credential_store=credential_store,
        mapping_store=mapping_store,
        file_directory=tmp_path / "connection-files",
    )

    def raise_missing_dependency() -> object:
        raise apply_service.ApplyDependencyError(
            "Apply requires the protobuf dependency. Install the service with its updated "
            "dependencies and retry."
        )

    monkeypatch.setattr(
        apply_service,
        "_load_opamp_protobuf_module",
        raise_missing_dependency,
    )

    response = await app.test_client().post(
        "/svr-credentials-manager-service/api/v1/connections/shared/apply"
    )

    assert response.status_code == 200
    payload = await response.get_json()
    assert payload["message"].startswith(
        "Applied shared to 1 client using fallback JSON log at "
    )
    assert payload["results"] == [
        {
            "client_id": "valid-node",
            "connection_name": "shared",
            "delivery": "fallback_log",
            "log_path": str(fallback_log_path),
        }
    ]
    logged_records = [
        json.loads(line)
        for line in fallback_log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(logged_records) == 1
    assert logged_records[0]["client_id"] == "valid-node"
    assert logged_records[0]["connection_name"] == "shared"
    assert (
        logged_records[0]["server_to_agent"]["connection_settings"]["opamp"][
            "destination_endpoint"
        ]
        == "https://example.test"
    )


@pytest.mark.asyncio
async def test_apply_connection_rejects_unassigned_definitions(tmp_path: Path) -> None:
    """Applying a definition without assigned clients should be rejected cleanly."""
    credential_store = CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json"))
    credential_store.save(
        "shared",
        {"opamp": {"destination_endpoint": "https://example.test", "headers": {}}},
    )
    app = create_app(
        credential_store=credential_store,
        mapping_store=ClientMappingStore(tmp_path / "mappings.json"),
        file_directory=tmp_path / "connection-files",
    )

    response = await app.test_client().post(
        "/svr-credentials-manager-service/api/v1/connections/shared/apply"
    )

    assert response.status_code == 400
    assert (await response.get_json())["error"] == (
        "Connection is not assigned to any client nodes"
    )


@pytest.mark.asyncio
async def test_apply_connection_reports_missing_protobuf_dependency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Applying should return a service error when provider delivery is requested without protobuf."""
    from svr_credentials_manager_service import apply_service

    credential_store = CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json"))
    credential_store.save(
        "shared",
        {"opamp": {"destination_endpoint": "https://example.test", "headers": {}}},
    )
    mapping_store = ClientMappingStore(tmp_path / "mappings.json")
    mapping_store.save({"valid-node": "shared"})
    app = create_app(
        credential_store=credential_store,
        mapping_store=mapping_store,
        file_directory=tmp_path / "connection-files",
    )
    monkeypatch.setenv("SVR_CREDENTIALS_PROVIDER_BASE_URL", "http://provider.example")

    def raise_missing_dependency() -> object:
        raise apply_service.ApplyDependencyError(
            "Apply requires the protobuf dependency. Install the service with its updated "
            "dependencies and retry."
        )

    monkeypatch.setattr(
        apply_service,
        "_load_opamp_protobuf_module",
        raise_missing_dependency,
    )

    response = await app.test_client().post(
        "/svr-credentials-manager-service/api/v1/connections/shared/apply"
    )

    assert response.status_code == 503
    assert (await response.get_json())["error"] == (
        "Apply requires the protobuf dependency. Install the service with its updated "
        "dependencies and retry."
    )


@pytest.mark.asyncio
async def test_save_connection_rejects_invalid_endpoint_addresses(tmp_path: Path) -> None:
    """The save endpoint should reject destination and proxy addresses that are not HTTP URLs."""
    app = create_app(
        credential_store=CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json")),
        mapping_store=ClientMappingStore(tmp_path / "mappings.json"),
        file_directory=tmp_path / "connection-files",
    )
    client = app.test_client()

    response = await client.put(
        "/svr-credentials-manager-service/api/v1/connections/invalid-endpoint",
        json={
            "definition": {
                "opamp": {
                    "destination_endpoint": "grpc://collector.example:4317",
                    "headers": {},
                }
            }
        },
    )

    assert response.status_code == 400
    assert "destination_endpoint" in (await response.get_json())["error"]

    response = await client.put(
        "/svr-credentials-manager-service/api/v1/connections/invalid-proxy",
        json={
            "definition": {
                "opamp": {
                    "destination_endpoint": "https://collector.example:4317",
                    "headers": {},
                    "proxy": {"url": "socks5://proxy.internal:1080", "connect_headers": {}},
                }
            }
        },
    )

    assert response.status_code == 400
    assert "proxy.url" in (await response.get_json())["error"]


@pytest.mark.asyncio
async def test_save_connection_rejects_invalid_json_object_fields(tmp_path: Path) -> None:
    """The save endpoint should reject JSON-backed fields when callers send non-object values."""
    app = create_app(
        credential_store=CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json")),
        mapping_store=ClientMappingStore(tmp_path / "mappings.json"),
        file_directory=tmp_path / "connection-files",
    )
    client = app.test_client()

    response = await client.put(
        "/svr-credentials-manager-service/api/v1/connections/invalid-json",
        json={
            "definition": {
                "opamp": {
                    "destination_endpoint": "https://collector.example:4317",
                    "headers": ["Authorization"],
                    "other_settings": {},
                }
            }
        },
    )

    assert response.status_code == 400
    assert "headers" in (await response.get_json())["error"]

    response = await client.put(
        "/svr-credentials-manager-service/api/v1/connections/invalid-other-json",
        json={
            "definition": {
                "other_connections": {
                    "custom-http": {
                        "destination_endpoint": "https://collector.example:4317",
                        "headers": {},
                        "other_settings": ["tenant-a"],
                    }
                }
            }
        },
    )

    assert response.status_code == 400
    assert "other_settings" in (await response.get_json())["error"]
