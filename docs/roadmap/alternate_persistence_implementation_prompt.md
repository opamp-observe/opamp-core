<!--
Copyright 2026 opamp.info
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Alternate Persistence Implementation Prompt

Status: planned roadmap specification

Last reviewed: 13 November 2026

Use this prompt when implementing an alternate persistence mechanism for the server credentials manager client-node mapping data.

## Objective

Extend `svr-credentials-mgr` so the mapping of client nodes to assigned connections can be stored in a persistence layer other than the current JSON file backend, while preserving current behavior, validation, reconciliation, API contracts, and UI expectations.

The implementation should build on the storage abstraction that already exists rather than bypassing it.

## Repository Context

Primary component:

- `svr-credentials-mgr`

Key files to inspect before making changes:

- `svr-credentials-mgr/src/svr_credentials_manager_service/storage.py`
- `svr-credentials-mgr/src/svr_credentials_manager_service/app.py`
- `svr-credentials-mgr/src/svr_credentials_manager_service/service_config.py`
- `svr-credentials-mgr/tests/test_storage.py`
- `svr-credentials-mgr/tests/test_app.py`
- `svr-credentials-mgr/readme.md`
- `agents.md`

## Current Design

The current implementation already has an abstraction layer for mapping persistence:

- `MappingPersistenceBackend` defines the persistence contract.
- `JsonFileMappingPersistenceBackend` is the default filesystem-backed implementation.
- `InMemoryMappingPersistenceBackend` exists for tests and lightweight injection.
- `ClientMappingStore` owns the domain behavior:
  - loading raw mapping data from the backend
  - normalizing data shape
  - reconciling mappings against active connections
  - dropping invalid assignments
  - reporting missing connections so the UI can surface status errors
  - saving the cleaned mapping back through the backend

This means new persistence work should plug into `MappingPersistenceBackend` and keep reconciliation rules centralized in `ClientMappingStore`.

## Implementation Goal

Add support for an alternate persistence backend, selectable via configuration, without breaking the default JSON-file workflow.

If no backend is explicitly configured, the service must continue to behave exactly as it does today.

## Preferred Direction

Implement SQLite as the second concrete backend unless repository conventions or platform constraints
make a different durable local store clearly better. Keep the abstraction suitable for a later
PostgreSQL backend, but do not add PostgreSQL infrastructure to the first implementation without a
demonstrated shared-deployment requirement.

Why SQLite is attractive:

- no separate infrastructure requirement
- transactional writes
- better corruption resistance than hand-managed JSON files
- easy local inspection
- good fit for a single-service embedded persistence layer

PostgreSQL remains a possible follow-up because it provides a well-supported shared relational store
for horizontally scaled deployments. It also introduces service lifecycle, credentials, migration,
availability, and operational ownership requirements that SQLite avoids.

## Functional Requirements

1. Add a configurable persistence backend selection mechanism.
2. Keep the existing JSON file backend as the default.
3. Allow backend-specific configuration values to be supplied through the existing shared service
   configuration flow under `opamp.svr_credentials_manager.storage`.
4. Ensure `ClientMappingStore` continues to reconcile loaded mappings against the currently available connections.
5. Ensure invalid or stale node-to-connection assignments are removed after reconciliation.
6. Preserve the current behavior where missing connections are surfaced to the UI as status errors and are not left assigned.
7. Do not change the public request or response shapes of existing APIs unless there is already an established config schema update pattern in the service.
8. Preserve deterministic behavior so tests remain stable.

## Non-Functional Requirements

- Keep cyclomatic complexity low. Avoid introducing methods that would exceed the service’s refactoring threshold.
- Keep storage-specific logic inside backend implementations.
- Keep business rules in `ClientMappingStore`.
- Use clear error messages when backend initialization or persistence fails.
- Prefer atomicity and transactional safety for writes.
- Maintain compatibility with unit tests and existing startup behavior.

## Constraints

- Do not remove or weaken the current reconciliation behavior.
- Do not duplicate reconciliation logic inside each backend.
- Do not couple API handlers directly to a concrete storage implementation.
- Do not break support for the configured JSON mapping file path.
- Do not introduce a dependency that requires a separately managed service unless there is a very strong reason and it is fully documented.
- Keep plaintext credential storage documentation and behavior unchanged unless the new backend explicitly needs a related note.

## Suggested Configuration Shape

Follow the shared configuration pattern already implemented in `service_config.py`. Environment
variables remain higher precedence than the shared JSON file, and relative paths resolve from the
configuration file location. A structure along these lines is acceptable:

```json
{
  "opamp": {
    "svr_credentials_manager": {
      "storage": {
        "mapping_backend": "json",
        "mapping_path": "./data/client-node-mapping.json",
        "mapping_sqlite_path": "./data/client-node-mapping.db"
      }
    }
  }
}
```

Recommended rules:

- `mapping_backend` allowed values: `json`, `sqlite`
- `mapping_path` is used when `mapping_backend == "json"`
- `mapping_sqlite_path` is required when `mapping_backend == "sqlite"`
- `SVR_CREDENTIALS_MAPPING_BACKEND` and backend-specific environment variables override JSON values
- existing deployments that only set `storage.mapping_path` continue to select the JSON backend

If config validation already exists elsewhere, integrate with it instead of inventing a parallel validator.

## Suggested Data Model For SQLite

If SQLite is used, keep the schema intentionally small. One table is likely enough:

- `client_node_connection_mapping`
  - `client_id` TEXT PRIMARY KEY
  - `connection_id` TEXT NOT NULL

Optional metadata fields are acceptable only if they solve a real problem:

- `updated_at`
- `source`

Avoid over-design. The domain model is currently simple.

## Suggested Implementation Steps

1. Review `storage.py` and document what must remain backend-agnostic.
2. Add a new backend class implementing `MappingPersistenceBackend`.
3. Add backend-specific initialization and serialization logic inside that class only.
4. Update application wiring in `app.py` so configuration chooses the backend at startup.
5. Update `service_config.py` to parse and validate the new persistence options with the established
   precedence: explicit argument, environment variable, shared JSON, legacy compatibility, then default.
6. Preserve backward compatibility for existing deployments that only provide a JSON path.
7. Add or update tests for:
   - backend selection
   - loading existing mappings
   - reconciliation of stale assignments
   - saving cleaned mappings
   - startup with default config
   - startup with alternate backend config
8. Update `readme.md` with the new configuration options and operational notes.

## Testing Expectations

At minimum, extend tests in:

- `svr-credentials-mgr/tests/test_storage.py`
- `svr-credentials-mgr/tests/test_app.py`

Tests should cover:

- `MappingPersistenceBackend` contract compliance
- parity between JSON and alternate backends
- persistence round-trip behavior
- reconciliation after loading stale mappings
- behavior when the backend store starts empty
- behavior when backend data is malformed or unavailable

Include SQLite tests that verify schema creation happens automatically and safely when appropriate.

## Acceptance Criteria

The work is complete when:

- the service can run with either JSON or alternate persistence
- the default configuration still uses JSON and remains backward compatible
- stale mappings are removed during load reconciliation exactly as before
- missing connections still surface as UI-visible status errors
- unit tests cover both backends
- documentation explains configuration and operational constraints

## Verification Commands

Synchronize the development environment from the repository root:

```bash
uv sync --project svr-credentials-mgr --extra dev
```

Run the relevant checks from the repository root; `--directory` keeps the commands portable across
Windows and Linux shells:

```bash
uv run --directory svr-credentials-mgr --locked python -m ruff check src tests
uv run --directory svr-credentials-mgr --locked python -m pylint src/svr_credentials_manager_service
uv run --directory svr-credentials-mgr --locked python -m pytest -q -s tests/test_storage.py tests/test_app.py
```

If new dependencies are added, update the relevant packaging files and note any install implications in `readme.md`.

## Implementation Notes

- Keep the protobuf/apply-flow work separate from this task unless a shared utility truly needs to move.
- Be careful not to reintroduce hard dependencies in code paths that should still work in standalone or degraded modes.
- If a migration path from JSON to SQLite is added, make it explicit and opt-in unless there is already a migration pattern in the service.
- If you add a migration helper, it should read through the existing abstraction or a dedicated import routine, not by scattering file parsing logic through the app.

## Deliverable Style

Produce focused, low-complexity code with tests first, then update documentation. Favor small, reviewable changes and preserve the current architecture seam around `MappingPersistenceBackend`.
