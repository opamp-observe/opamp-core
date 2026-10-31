#!/usr/bin/env python3
# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Start a seeded credentials-manager instance for Playwright tests."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIRECTORY = ROOT / "ui-tests" / ".runtime"

for source_path in (ROOT / "src", ROOT / "plaintext-keyring" / "src"):
    resolved = str(source_path.resolve())
    if resolved not in sys.path:
        sys.path.insert(0, resolved)

from opamp_plaintext_keyring import PlaintextFileKeyring  # noqa: E402
from svr_credentials_manager_service.storage import ClientMappingStore, CredentialStore  # noqa: E402
from svr_credentials_manager_service.app import create_app  # noqa: E402


def prepare_runtime() -> tuple[Path, Path, Path]:
    """Reset and seed the runtime files used by the UI suite."""
    if RUNTIME_DIRECTORY.exists():
        shutil.rmtree(RUNTIME_DIRECTORY)
    RUNTIME_DIRECTORY.mkdir(parents=True, exist_ok=True)
    credentials_path = RUNTIME_DIRECTORY / "credentials.json"
    mappings_path = RUNTIME_DIRECTORY / "client-mappings.json"
    files_path = RUNTIME_DIRECTORY / "connection-files"
    files_path.mkdir(parents=True, exist_ok=True)
    config_path = RUNTIME_DIRECTORY / "service-config.json"

    credential_store = CredentialStore(PlaintextFileKeyring(credentials_path))
    credential_store.save(
        "shared",
        {"opamp": {"destination_endpoint": "https://example.test", "headers": {}}},
    )
    ClientMappingStore(mappings_path).save(
        {
            "missing-node": "missing-connection",
            "valid-node": "shared",
        }
    )
    config_path.write_text(
        json.dumps(
            {"storage": {"mapping_path": str(mappings_path)}},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return credentials_path, config_path, files_path


def main() -> None:
    """Seed the test runtime and launch the Quart service."""
    host = os.environ.get("PLAYWRIGHT_SVR_CREDENTIALS_HOST", "127.0.0.1")
    port = int(os.environ.get("PLAYWRIGHT_SVR_CREDENTIALS_PORT", "8191"))
    credentials_path, config_path, files_path = prepare_runtime()
    os.environ["SVR_CREDENTIALS_PLAINTEXT_PATH"] = str(credentials_path)
    os.environ["SVR_CREDENTIALS_CONFIG_PATH"] = str(config_path)
    os.environ["SVR_CREDENTIALS_FILE_DIRECTORY"] = str(files_path)
    os.environ["SVR_CREDENTIALS_CONNECTION_APPLY_LOG_PATH"] = str(
        RUNTIME_DIRECTORY / "connection-apply-fallback.jsonl"
    )
    create_app().run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
