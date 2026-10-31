# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Provide a deliberately unencrypted JSON-file keyring backend."""

from __future__ import annotations

import json
import os
from pathlib import Path

from keyring.backend import KeyringBackend
from keyring.errors import PasswordDeleteError

ENV_PLAINTEXT_FILE = "SVR_CREDENTIALS_PLAINTEXT_PATH"
DEFAULT_DIRECTORY = ".opamp"
DEFAULT_FILENAME = "credentials-plaintext.json"
FILE_MODE_OWNER_ONLY = 0o600


class PlaintextFileKeyring(KeyringBackend):
    """Store keyring service/account values in a human-readable JSON file.

    ``file_path`` is configurable through ``SVR_CREDENTIALS_PLAINTEXT_PATH``. This backend
    provides no encryption and is intended for controlled development environments.
    """

    priority = 1

    def __init__(self, file_path: str | Path | None = None) -> None:
        """Use ``file_path`` or the environment/default user-data location."""
        super().__init__()
        configured_path = file_path or os.environ.get(ENV_PLAINTEXT_FILE)
        self.file_path = Path(configured_path).expanduser() if configured_path else (
            Path.home() / DEFAULT_DIRECTORY / DEFAULT_FILENAME
        )

    def get_password(self, service: str, username: str) -> str | None:
        """Return the stored value for ``service`` and ``username`` when present."""
        return self._read().get(service, {}).get(username)

    def set_password(self, service: str, username: str, password: str) -> None:
        """Persist ``password`` for the keyring ``service`` and ``username`` pair."""
        payload = self._read()
        payload.setdefault(service, {})[username] = password
        self._write(payload)

    def delete_password(self, service: str, username: str) -> None:
        """Delete a keyring entry or raise the keyring-standard missing-entry error."""
        payload = self._read()
        if username not in payload.get(service, {}):
            raise PasswordDeleteError("Password not found")
        del payload[service][username]
        if not payload[service]:
            del payload[service]
        self._write(payload)

    def _read(self) -> dict[str, dict[str, str]]:
        """Read the JSON document, returning an empty keyring before first use."""
        if not self.file_path.exists():
            return {}
        return json.loads(self.file_path.read_text(encoding="utf-8"))

    def _write(self, payload: dict[str, dict[str, str]]) -> None:
        """Atomically write ``payload`` and request owner-only file permissions."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.file_path.with_suffix(self.file_path.suffix + ".tmp")
        temporary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        os.chmod(temporary_path, FILE_MODE_OWNER_ONLY)
        temporary_path.replace(self.file_path)
