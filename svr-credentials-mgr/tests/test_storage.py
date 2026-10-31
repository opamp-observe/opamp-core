# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Test credential and client-mapping persistence."""

import json
from pathlib import Path

import pytest
from opamp_plaintext_keyring import PlaintextFileKeyring

from svr_credentials_manager_service.storage import (
    ClientMappingStore,
    CredentialStore,
    InMemoryMappingPersistenceBackend,
    JsonFileMappingPersistenceBackend,
    MappingPersistenceBackend,
    MappingReconciliationResult,
    RemovedClientMapping,
    create_default_backend,
)


def test_credential_store_round_trip_and_delete(tmp_path: Path) -> None:
    """Definitions should round-trip through the default-compatible keyring API."""
    store = CredentialStore(PlaintextFileKeyring(tmp_path / "credentials.json"))
    store.save("production", {"opamp": {"headers": {"Authorization": "Bearer secret"}}})
    assert store.list_names() == ["production"]
    assert store.get("production")["opamp"]["headers"]["Authorization"] == "Bearer secret"
    assert store.delete("production") is True
    assert store.delete("production") is False


def test_mapping_store_round_trip(tmp_path: Path) -> None:
    """Many clients should be able to reference one named connection."""
    store = ClientMappingStore(tmp_path / "mappings.json")
    store.save({"client-b": "shared", "client-a": "shared"})
    assert store.load() == {"client-a": "shared", "client-b": "shared"}


def test_mapping_store_reconciles_missing_connections(tmp_path: Path) -> None:
    """Loading should remove assignments that reference missing connections."""
    store = ClientMappingStore(tmp_path / "mappings.json")
    store.save(
        {
            "client-a": "shared",
            "client-b": "missing-connection",
        }
    )

    result = store.load_and_reconcile(["shared"])

    assert isinstance(result, MappingReconciliationResult)
    assert result.mappings == {"client-a": "shared"}
    assert result.removed_assignments == (
        RemovedClientMapping(
            client_id="client-b",
            connection_name="missing-connection",
        ),
    )
    assert store.load() == {"client-a": "shared"}


def test_mapping_store_accepts_alternative_persistence_backend() -> None:
    """A custom mapping persistence backend should work through the same store abstraction."""
    backend = InMemoryMappingPersistenceBackend(
        {
            "client-a": "shared",
            "client-b": "missing-connection",
        }
    )
    store = ClientMappingStore(backend)

    result = store.load_and_reconcile(["shared"])

    assert result.mappings == {"client-a": "shared"}
    assert backend.load_mappings() == {"client-a": "shared"}


def test_json_file_mapping_backend_implements_mapping_persistence_contract(
    tmp_path: Path,
) -> None:
    """The JSON-file backend should satisfy the mapping persistence abstraction."""
    backend = JsonFileMappingPersistenceBackend(tmp_path / "mappings.json")

    assert isinstance(backend, MappingPersistenceBackend)
    backend.save_mappings({"client-b": "shared", "client-a": "shared"})

    assert backend.load_mappings() == {"client-a": "shared", "client-b": "shared"}


def test_default_backend_is_plaintext(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No backend selection should resolve to the bundled plaintext implementation."""
    monkeypatch.delenv("SVR_CREDENTIALS_KEYRING_BACKEND", raising=False)
    monkeypatch.setenv("SVR_CREDENTIALS_PLAINTEXT_PATH", str(tmp_path / "default.json"))
    assert isinstance(create_default_backend(), PlaintextFileKeyring)


def test_default_backend_can_load_plaintext_path_from_common_opamp_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default backend should honor the shared OpAMP config object."""
    monkeypatch.delenv("SVR_CREDENTIALS_KEYRING_BACKEND", raising=False)
    monkeypatch.delenv("SVR_CREDENTIALS_PLAINTEXT_PATH", raising=False)
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(
            {
                "opamp": {
                    "svr_credentials_manager": {
                        "storage": {
                            "plaintext_path": "runtime/credentials.json",
                        }
                    }
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    backend = create_default_backend(config_path)

    assert isinstance(backend, PlaintextFileKeyring)
    assert backend.file_path == (tmp_path / "runtime" / "credentials.json").resolve()


def test_env_plaintext_path_overrides_common_opamp_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Environment variables should override the shared OpAMP config file."""
    monkeypatch.delenv("SVR_CREDENTIALS_KEYRING_BACKEND", raising=False)
    config_path = tmp_path / "opamp.json"
    config_path.write_text(
        json.dumps(
            {
                "opamp": {
                    "svr_credentials_manager": {
                        "storage": {
                            "plaintext_path": "runtime/from-config.json",
                        }
                    }
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(
        "SVR_CREDENTIALS_PLAINTEXT_PATH",
        str(tmp_path / "runtime" / "from-env.json"),
    )

    backend = create_default_backend(config_path)

    assert isinstance(backend, PlaintextFileKeyring)
    assert backend.file_path == (tmp_path / "runtime" / "from-env.json").resolve()
