# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Manage mock client identifiers used by the standalone credentials UI."""


MOCK_CLIENT_PREFIX = "mock-client-"
DEFAULT_MOCK_CLIENT_COUNT = 20


class MockClientService:
    """Retain a list of available client identifiers for assignment workflows.

    The service keeps lightweight in-memory identifiers that the browser UI can
    use when the credentials manager runs without a provider client inventory.
    """

    def __init__(self) -> None:
        """Create an empty mock client directory."""
        self._client_ids: list[str] = []

    def list_client_ids(self) -> list[str]:
        """Return the currently available mock client identifiers."""
        return list(self._client_ids)

    def seed_default_clients(self) -> list[str]:
        """Populate the default 20 mock clients and return the resulting list."""
        self._client_ids = [
            f"{MOCK_CLIENT_PREFIX}{client_number:02d}"
            for client_number in range(1, DEFAULT_MOCK_CLIENT_COUNT + 1)
        ]
        return self.list_client_ids()
