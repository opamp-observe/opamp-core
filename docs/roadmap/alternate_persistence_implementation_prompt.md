# Alternate Persistence Implementation Prompt

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
- `agent.md`

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

Implement a second concrete backend, that support:
- SQLite
- Postgres
unless repo conventions or platform constraints make a different durable local store clearly better.

Why SQLite is attractive:

- no separate infrastructure requirement
- transactional writes
- better corruption resistance than hand-managed JSON files
- easy local inspection
- good fit for a single-service embedded persistence layer

Postgres is attractive because:
- Full RDBMS features
- very well adopted and considered enterprise capable
- Easiy to scale

## Functional Requirements

1. Add a configurable persistence backend selection mechanism.
2. Keep the existing JSON file backend as the default.
3. Allow backend-specific configuration values to be supplied through the existing service configuration flow.
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

Follow existing config patterns in `service_config.py` and keep names explicit. A structure along these lines is acceptable:

```json
{
  "clientNodeConnectionMapping": {
    "backend": "json",
    "filePath": "data/client-node-mapping.json",
    "sqlitePath": "data/client-node-mapping.db"
  }
}
```

Or, if the existing config style is flatter, adapt to that style consistently.

Recommended rules:

- `backend` allowed values: `json`, `sqlite`
- `filePath` required when `backend == "json"`
- `sqlitePath` required when `backend == "sqlite"`

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
5. Update `service_config.py` to parse and validate the new persistence options.
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

If SQLite is chosen, include tests that verify schema creation happens automatically when appropriate.

## Acceptance Criteria

The work is complete when:

- the service can run with either JSON or alternate persistence
- the default configuration still uses JSON and remains backward compatible
- stale mappings are removed during load reconciliation exactly as before
- missing connections still surface as UI-visible status errors
- unit tests cover both backends
- documentation explains configuration and operational constraints

## Verification Commands

Run the relevant checks from `svr-credentials-mgr`:

```bash
PYTHONPATH=src:plaintext-keyring/src python -m ruff check src tests
PYTHONPATH=src:plaintext-keyring/src python -m pytest -q tests/test_storage.py tests/test_app.py
```

If new dependencies are added, update the relevant packaging files and note any install implications in `readme.md`.

## Implementation Notes

- Keep the protobuf/apply-flow work separate from this task unless a shared utility truly needs to move.
- Be careful not to reintroduce hard dependencies in code paths that should still work in standalone or degraded modes.
- If a migration path from JSON to SQLite is added, make it explicit and opt-in unless there is already a migration pattern in the service.
- If you add a migration helper, it should read through the existing abstraction or a dedicated import routine, not by scattering file parsing logic through the app.

## Deliverable Style

Produce focused, low-complexity code with tests first, then update documentation. Favor small, reviewable changes and preserve the current architecture seam around `MappingPersistenceBackend`.
