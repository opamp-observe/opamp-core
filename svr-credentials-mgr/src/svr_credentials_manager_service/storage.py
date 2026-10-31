# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Persist named connection definitions and client mappings."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import keyring.backend
import keyring.errors
from opamp_plaintext_keyring import PlaintextFileKeyring

from .service_config import (
    resolve_cryptfile_password_from_config,
    resolve_cryptfile_path_from_config,
    resolve_keyring_backend_from_config,
    resolve_plaintext_path_from_config,
)

ENV_CRYPTFILE_PASSWORD = "SVR_CREDENTIALS_CRYPTFILE_PASSWORD"  # noqa: S105
ENV_CRYPTFILE_PATH = "SVR_CREDENTIALS_CRYPTFILE_PATH"
ENV_KEYRING_BACKEND = "SVR_CREDENTIALS_KEYRING_BACKEND"
ENV_PLAINTEXT_PATH = "SVR_CREDENTIALS_PLAINTEXT_PATH"
KEYRING_SERVICE = "opamp-server-connection-settings"
KEYRING_INDEX_ACCOUNT = "__connection_names__"
KEYRING_DEFINITION_PREFIX = "connection:"
MAPPING_KEY_CLIENTS = "clients"
MAPPING_KEY_CONNECTION = "connection"
DEFAULT_CRYPTFILE_NAME = "credentials.cfg"
BACKEND_PLAINTEXT = "plaintext"
BACKEND_CRYPTFILE = "cryptfile"


@dataclass(frozen=True)
class RemovedClientMapping:
    """One stale client-to-connection assignment removed during reconciliation."""

    client_id: str
    connection_name: str


@dataclass(frozen=True)
class MappingReconciliationResult:
    """Result returned when client mappings are loaded and reconciled."""

    mappings: dict[str, str]
    removed_assignments: tuple[RemovedClientMapping, ...] = ()


class MappingPersistenceBackend(ABC):
    """Abstract persistence adapter for client-to-connection mappings.

    Implementations own the actual storage mechanism. The higher-level
    ``ClientMappingStore`` keeps reconciliation and validation behavior consistent
    regardless of whether mappings are stored in JSON files, databases, or other
    persistence layers.
    """

    @abstractmethod
    def load_mappings(self) -> dict[str, str]:
        """Return the current client-to-connection mapping snapshot."""

    @abstractmethod
    def save_mappings(self, mappings: dict[str, str]) -> None:
        """Persist ``mappings`` using the implementation-specific storage layer."""


class JsonFileMappingPersistenceBackend(MappingPersistenceBackend):
    """Persist client mappings in the existing JSON-file document format.

    ``path`` is the mapping document location managed with atomic replacement.
    This keeps the current on-disk behavior while allowing ``ClientMappingStore``
    to work with different persistence backends in the future.
    """

    def __init__(self, path: Path) -> None:
        """Create a JSON-file mapping backend rooted at ``path``."""
        self.path = path

    def load_mappings(self) -> dict[str, str]:
        """Read client mappings, treating a missing document as an empty mapping."""
        if not self.path.exists():
            return {}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        clients = payload.get(MAPPING_KEY_CLIENTS, {})
        return {str(client): str(connection) for client, connection in clients.items()}

    def save_mappings(self, mappings: dict[str, str]) -> None:
        """Atomically replace the mapping document with ``mappings``."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        payload = {MAPPING_KEY_CLIENTS: dict(sorted(mappings.items()))}
        temporary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary_path.replace(self.path)


class InMemoryMappingPersistenceBackend(MappingPersistenceBackend):
    """Keep client mappings in memory for tests or embedded custom integrations."""

    def __init__(self, mappings: dict[str, str] | None = None) -> None:
        """Seed the in-memory backend with optional ``mappings``."""
        self.mappings = dict(mappings or {})

    def load_mappings(self) -> dict[str, str]:
        """Return a copy of the current in-memory mapping snapshot."""
        return dict(self.mappings)

    def save_mappings(self, mappings: dict[str, str]) -> None:
        """Replace the current in-memory mapping snapshot."""
        self.mappings = dict(sorted(mappings.items()))


class CredentialStore:
    """Store complete connection definitions behind the Python keyring API.

    ``backend`` is the selected keyring backend. Definitions and their index are stored as
    keyring secrets so endpoint, certificate, header, and authentication data share protection.
    """

    def __init__(self, backend: keyring.backend.KeyringBackend) -> None:
        """Create a store using ``backend`` for every read and write."""
        self.backend = backend

    def list_names(self) -> list[str]:
        """Return the sorted connection-name index without exposing stored values."""
        serialized = self.backend.get_password(KEYRING_SERVICE, KEYRING_INDEX_ACCOUNT)
        if not serialized:
            return []
        names = json.loads(serialized)
        return sorted(str(name) for name in names)

    def get(self, name: str) -> dict[str, Any] | None:
        """Load the connection identified by ``name``, returning ``None`` when absent."""
        serialized = self.backend.get_password(KEYRING_SERVICE, KEYRING_DEFINITION_PREFIX + name)
        return json.loads(serialized) if serialized else None

    def save(self, name: str, definition: dict[str, Any]) -> None:
        """Save ``definition`` under ``name`` and update the private name index."""
        names = set(self.list_names())
        names.add(name)
        self.backend.set_password(
            KEYRING_SERVICE,
            KEYRING_DEFINITION_PREFIX + name,
            json.dumps(definition, sort_keys=True),
        )
        self.backend.set_password(KEYRING_SERVICE, KEYRING_INDEX_ACCOUNT, json.dumps(sorted(names)))

    def delete(self, name: str) -> bool:
        """Delete ``name`` and return whether an indexed definition existed."""
        names = set(self.list_names())
        if name not in names:
            return False
        try:
            self.backend.delete_password(
                KEYRING_SERVICE, KEYRING_DEFINITION_PREFIX + name
            )
        except keyring.errors.PasswordDeleteError:
            pass
        names.remove(name)
        self.backend.set_password(KEYRING_SERVICE, KEYRING_INDEX_ACCOUNT, json.dumps(sorted(names)))
        return True


class ClientMappingStore:
    """Maintain the many-clients-to-one-connection mapping through a backend adapter.

    ``backend_or_path`` may be either:

    - a ``Path`` for the default JSON-file persistence backend
    - a ``MappingPersistenceBackend`` implementation for alternate storage layers

    Reconciliation behavior stays centralized here so alternate persistence
    implementations do not need to reimplement stale-assignment cleanup.
    """

    def __init__(self, backend_or_path: MappingPersistenceBackend | Path) -> None:
        """Create a mapping store using ``backend_or_path`` for persistence."""
        if isinstance(backend_or_path, MappingPersistenceBackend):
            self.backend = backend_or_path
            return
        self.backend = JsonFileMappingPersistenceBackend(Path(backend_or_path))

    def load(self) -> dict[str, str]:
        """Read client mappings from the configured persistence backend."""
        return self.backend.load_mappings()

    def load_and_reconcile(
        self,
        valid_connection_names: list[str] | tuple[str, ...] | set[str],
    ) -> MappingReconciliationResult:
        """Remove mappings that reference unknown connections and persist the cleaned result."""
        valid_connections = {str(name).strip() for name in valid_connection_names if str(name).strip()}
        current_mappings = self.load()
        removed_assignments: list[RemovedClientMapping] = []
        reconciled_mappings: dict[str, str] = {}
        for client_id, connection_name in current_mappings.items():
            if connection_name in valid_connections:
                reconciled_mappings[client_id] = connection_name
                continue
            removed_assignments.append(
                RemovedClientMapping(
                    client_id=client_id,
                    connection_name=connection_name,
                )
            )
        if removed_assignments:
            self.save(reconciled_mappings)
        ordered_removed_assignments = tuple(
            sorted(
                removed_assignments,
                key=lambda assignment: (assignment.client_id, assignment.connection_name),
            )
        )
        return MappingReconciliationResult(
            mappings=reconciled_mappings,
            removed_assignments=ordered_removed_assignments,
        )

    def save(self, mappings: dict[str, str]) -> None:
        """Replace mappings through the configured persistence backend."""
        self.backend.save_mappings(mappings)


def create_cryptfile_backend(config_path: Path | None = None) -> keyring.backend.KeyringBackend:
    """Create the encrypted-file backend from env-vars or runtime config."""
    from keyrings.cryptfile.cryptfile import CryptFileKeyring

    encryption_password = os.environ.get(ENV_CRYPTFILE_PASSWORD, "").strip()
    if not encryption_password:
        encryption_password = str(
            resolve_cryptfile_password_from_config(config_path) or ""
        ).strip()
    if not encryption_password:
        raise RuntimeError(f"{ENV_CRYPTFILE_PASSWORD} must be set")
    backend = CryptFileKeyring()
    configured_path = os.environ.get(ENV_CRYPTFILE_PATH, "").strip()
    if not configured_path:
        configured_path = str(resolve_cryptfile_path_from_config(config_path) or "").strip()
    if configured_path:
        credentials_path = Path(configured_path).expanduser().resolve()
        credentials_path.parent.mkdir(parents=True, exist_ok=True)
        backend.file_path = str(credentials_path)
    backend.keyring_key = encryption_password
    return backend


def create_default_backend(config_path: Path | None = None) -> keyring.backend.KeyringBackend:
    """Create the configured backend, defaulting to the local plaintext plugin."""
    backend_name = os.environ.get(ENV_KEYRING_BACKEND, "").strip().lower()
    if not backend_name:
        backend_name = str(resolve_keyring_backend_from_config(config_path) or "").strip().lower()
    if not backend_name:
        backend_name = BACKEND_PLAINTEXT
    if backend_name == BACKEND_CRYPTFILE:
        return create_cryptfile_backend(config_path)
    if backend_name != BACKEND_PLAINTEXT:
        raise RuntimeError(f"Unsupported {ENV_KEYRING_BACKEND} value: {backend_name}")
    configured_path = os.environ.get(ENV_PLAINTEXT_PATH, "").strip()
    if not configured_path:
        configured_path = str(resolve_plaintext_path_from_config(config_path) or "").strip()
    if configured_path:
        return PlaintextFileKeyring(configured_path)
    return PlaintextFileKeyring()
