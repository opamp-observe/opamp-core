# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Test the standalone plaintext keyring plugin."""

import json
from pathlib import Path

import pytest
from keyring.errors import PasswordDeleteError

from opamp_plaintext_keyring import PlaintextFileKeyring


def test_plaintext_backend_crud(tmp_path: Path) -> None:
    """The backend should persist readable values and implement keyring deletion semantics."""
    path = tmp_path / "keyring.json"
    backend = PlaintextFileKeyring(path)
    backend.set_password("service", "account", "visible-secret")
    assert backend.get_password("service", "account") == "visible-secret"
    assert json.loads(path.read_text(encoding="utf-8"))["service"]["account"] == "visible-secret"
    backend.delete_password("service", "account")
    assert backend.get_password("service", "account") is None
    with pytest.raises(PasswordDeleteError):
        backend.delete_password("service", "missing")
