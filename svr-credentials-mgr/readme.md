# Server credentials manager service

Copyright 2026 mp3monster.org. Licensed under the Apache License, Version 2.0.

This component manages named OpAMP `ServerToAgent.connection_settings` definitions, stores
their sensitive values in a keyring backend, tracks which client nodes are assigned to which
definition, and can apply a stored definition to assigned clients through the provider queue.

## What the component is for

The service exists to separate three concerns that are easy to conflate:

- connection definition authoring
- client-node assignment
- delivery of connection settings to agents

The UI lets an operator build reusable named connection definitions. A separate mapping file
then assigns zero or more client nodes to one of those definitions. When `Apply` is used, the
service builds a real OpAMP `ServerToAgent.connection_settings` payload and either:

- queues it to the provider for delivery to the client, or
- writes a fallback JSON log entry containing the JSON form of the gRPC object when the
  provider endpoint is unavailable

## Install and start

### Windows batch launcher

A windows script has been implemented as tactical option. Once the feature is ready, we should extend the CLI tool to run this functionality in standalone mode.

From Command Prompt, or by double-clicking the file:

```bat
start_service.bat
```

The launcher creates `.venv` and installs the service on first use, creates the `data`
directory, selects the plaintext backend, and starts the UI on port `8091`. Existing
`SVR_CREDENTIALS_*` environment values are respected.

Pass through host and port when needed:

```bat
start_service.bat --host 0.0.0.0 --port 8092
```

### Manual PowerShell setup

From `svr-credentials-mgr`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$env:SVR_CREDENTIALS_PLAINTEXT_PATH = "$PWD\data\credentials.json"
$env:SVR_CREDENTIALS_MAPPING_PATH = "$PWD\data\client-mappings.json"
$env:SVR_CREDENTIALS_FILE_DIRECTORY = "$PWD\data\connection-files"
svr-credentials-manager-service --host 127.0.0.1 --port 8091
```

Open `http://127.0.0.1:8091/svr-credentials-manager-service/ui`.

## Core data model

### Connection definitions

Each saved connection definition is keyed by name and stored in the selected keyring backend.
The definition schema maps to OpAMP `ConnectionSettingsOffers`.

The standard top-level sections are:

- `opamp`
- `own_metrics`
- `own_traces`
- `own_logs`

An additional top-level object, `other_connections`, can contain any number of named custom
connections.

### Client assignment mappings

Assignments are stored separately from the credential/keyring store in a JSON file shaped like:

```json
{
  "clients": {
    "client-a": "shared",
    "client-b": "production"
  }
}
```

This separation keeps the sensitive payload definitions in keyring while leaving the
client-to-definition relationships in a simple operational file.

The default implementation uses a JSON-file mapping backend, but the service now keeps mapping
reconciliation separate from persistence so alternative storage layers can be introduced through
the `MappingPersistenceBackend` abstraction without changing API behavior.

### Apply delivery

`Apply` builds one `ServerToAgent.connection_settings` payload from the stored definition, then
fans it out to all currently assigned client IDs for that definition.

Delivery order is:

1. Build the protobuf payload.
2. Resolve the assigned client IDs from the reconciled mapping file.
3. POST the payload to the provider `/api/clients/<client_id>/connection-settings` endpoint.
4. If the provider cannot be reached, append one JSONL fallback record containing the JSON
   representation of the gRPC object.

## Assignment constraints

The assignment rules enforced by the component are:

- One client node can be assigned to at most one connection definition at a time.
- One connection definition can be assigned to many client nodes.
- A mapping can only target a connection definition that currently exists in the credential
  store.
- If the mapping file references a connection that no longer exists, that assignment is removed
  during load/reconciliation.
- A connection definition cannot be deleted while at least one client node is still assigned to
  it.
- Applying a connection definition requires at least one assigned client node.
- Saving assignments for one connection replaces that connection’s current assignment set.
- Assigning a client node to a new connection reassigns it away from any prior connection.

### Where assignable client IDs come from

In embedded mode:

- the UI uses the host application's `/api/clients` provider route when present

In standalone mode:

- the UI can use seeded mock client IDs
- existing IDs already present in the mapping file are also considered valid choices

### Reconciliation behavior

When mappings are loaded, the service reconciles them against the current saved connection names.
If stale entries are removed:

- the cleaned mapping file is written back to disk
- the API includes a reconciliation message
- the UI status area shows the missing assignment cleanup

## Connection definition schema

### Standard section fields

Each of `opamp`, `own_metrics`, `own_traces`, and `own_logs` accepts the following fields:

- `enabled`
  - optional boolean
  - defaults to `true` when omitted
  - disabled sections are not serialized into the outbound payload
- `destination_endpoint`
  - optional string
  - must be an absolute `http://` or `https://` URL
- `headers`
  - optional JSON object of string keys to string values
- `certificate`
  - optional JSON object
  - supported keys:
    - `cert_file`
    - `private_key_file`
    - `ca_cert_file`
- `tls`
  - optional JSON object
  - supported keys:
    - `ca_pem_file`
    - `include_system_ca_certs_pool`
    - `insecure_skip_verify`
    - `min_version`
    - `max_version`
    - `cipher_suites`
- `proxy`
  - optional JSON object
  - supported keys:
    - `url`
    - `connect_headers`

### `other_connections`

`other_connections` is an object whose keys are operator-defined connection names. Each nested
value accepts the same fields as the standard sections plus:

- `other_settings`
  - optional JSON object
  - values are serialized into the OpAMP `AnyValue` map
  - scalar types preserved by the builder are:
    - boolean
    - integer
    - float
    - string

### Validation rules

The service currently enforces these validation rules before storage:

- connection names must be non-empty strings
- `other_connections` keys must be non-empty strings
- `headers`, `proxy.connect_headers`, and `other_settings` must be JSON objects
- `enabled`, `include_system_ca_certs_pool`, and `insecure_skip_verify` must be booleans
- `cipher_suites` must be a list of non-empty strings
- `destination_endpoint` and `proxy.url` must be valid absolute `http` or `https` URLs

### Practical limitation

Although OpenTelemetry and adjacent components often use gRPC-style endpoints, the current UI
validation only allows `http` and `https` URL schemes for `destination_endpoint` and `proxy.url`.
Values such as `grpc://...` and `socks5://...` are rejected by the service today.

## Runtime configuration

### CLI arguments

The standalone entrypoint accepts:

- `--host`
  - bind address
  - default: `127.0.0.1`
- `--port`
  - listen port
  - default: `8091`
- `--config-path`
  - optional JSON runtime config path

### JSON runtime config file

The current JSON runtime config file supports one settings block:

```json
{
  "storage": {
    "mapping_path": "./data/client-mappings.json"
  },
  "authorization": {
    "ui_use_authorization": "none"
  }
}
```

Supported JSON keys:

- `storage.mapping_path`
  - purpose: sets the mapping-file location
  - type: string path
  - used when `SVR_CREDENTIALS_MAPPING_PATH` is not set
- `authorization.ui_use_authorization`
  - purpose: sets the credentials-manager API auth mode from config
  - allowed values:
    - `none`
    - `config-token`
    - `idp`
  - useful when the service should explicitly switch auth off in config without relying on env

### Environment variables

#### Storage and filesystem

- `SVR_CREDENTIALS_CONFIG_PATH`
  - path to the JSON runtime config file
- `SVR_CREDENTIALS_MAPPING_PATH`
  - explicit path to the client assignment mapping file
  - overrides `storage.mapping_path`
- `SVR_CREDENTIALS_FILE_DIRECTORY`
  - directory where uploaded certificate and PEM files are stored
- `SVR_CREDENTIALS_TLS_VERSIONS_PATH`
  - path to the TLS-versions JSON document used by the UI
  - expected JSON shape:
    ```json
    { "versions": ["1.2", "1.3"] }
    ```

#### Keyring backend selection

- `SVR_CREDENTIALS_KEYRING_BACKEND`
  - allowed values:
    - `plaintext`
    - `cryptfile`
  - default: `plaintext`
- `SVR_CREDENTIALS_PLAINTEXT_PATH`
  - path to the plaintext keyring JSON file
  - used by the bundled plaintext keyring backend
- `SVR_CREDENTIALS_CRYPTFILE_PASSWORD`
  - required when `SVR_CREDENTIALS_KEYRING_BACKEND=cryptfile`
- `SVR_CREDENTIALS_CRYPTFILE_PATH`
  - optional encrypted keyring file path for the `cryptfile` backend

#### UI and API authorization

- `SVR_CREDENTIALS_UI_USE_AUTHORIZATION`
  - allowed values:
    - `none`
    - `config-token`
    - `idp`
  - purpose: protects the credentials-manager API routes
  - default behavior:
    - use this env var when set
    - otherwise, use `authorization.ui_use_authorization` from service config when set
    - otherwise, in embedded mode, fall back to the provider's `ui_use_authorization`
- `UI_AUTH_STATIC_TOKEN`
  - static bearer token used when `SVR_CREDENTIALS_UI_USE_AUTHORIZATION=config-token`
- `UI_AUTH_JWT_ISSUER`
  - expected JWT issuer when `SVR_CREDENTIALS_UI_USE_AUTHORIZATION=idp`
- `UI_AUTH_JWT_AUDIENCE`
  - expected JWT audience when `SVR_CREDENTIALS_UI_USE_AUTHORIZATION=idp`
- `UI_AUTH_JWT_JWKS_URL`
  - JWKS URL used for JWT signature verification
  - if omitted and `UI_AUTH_JWT_ISSUER` is set, the service derives:
    - `<issuer>/protocol/openid-connect/certs`
- `UI_AUTH_JWT_LEEWAY_SECONDS`
  - clock-skew leeway for JWT validation
  - default: `30`

### Authentication flow expectation

The credentials-manager UI does not expose a manual bearer-token entry field.

Authenticated deployments are expected to provide access through an external or host-managed
authentication flow, for example:

- a reverse proxy or gateway
- an embedded host application
- a browser/session-based login flow
- an IdP-backed authentication boundary

The backend still supports secured API modes, but credential entry is not performed in the page
itself.

#### Apply-to-provider integration

- `SVR_CREDENTIALS_PROVIDER_BASE_URL`
  - provider base URL used for `Apply`
  - when unset, the service uses the current request origin
- `SVR_CREDENTIALS_CONNECTION_APPLY_LOG_PATH`
  - JSONL fallback log path used when the provider endpoint is unavailable
  - default: `connection-settings-apply-fallback.jsonl`

## Plaintext credential storage

The plaintext keyring backend now has its own document:

- [docs/plaintext-keyring-storage.md](/mnt/d/dev/opamp/svr-credentials-mgr/docs/plaintext-keyring-storage.md)

That document covers:

- file path resolution order
- on-disk JSON structure
- security characteristics
- operational guidance and when to prefer `cryptfile`

## Standalone and embedded behavior

This package can run:

- as a freestanding service via `python -m svr_credentials_manager_service`
- inside a larger Quart application by calling
  `svr_credentials_manager_service.app.register_components(...)`

In embedded mode, the service can share provider auth behavior and client inventory routes. In
standalone mode, mock clients and local storage paths are the normal working model.

## Quality checks

```powershell
python -m ruff check src tests plaintext-keyring/src plaintext-keyring/tests
python -m pylint svr_credentials_manager_service connection_settings_builder opamp_plaintext_keyring
python -m pytest -q -s
node --check src/svr_credentials_manager_service/html/state.js
node --check src/svr_credentials_manager_service/html/functions.js
node --check src/svr_credentials_manager_service/html/app.js
node --check src/svr_credentials_manager_service/html/bindings.js
```

The project-level ST-007 container adds live provider and simulator delivery, unavailable-provider
fallback, storage-separation, reconciliation, and browser workflow coverage. From the repository
root, run:

```powershell
py -3.11 tests/test-containers/run_regression_pack.py --only st007
```

See [the ST-007 container guide](../tests/test-containers/st007/readme.md) for the complete coverage
matrix, direct Docker commands, retained evidence, and troubleshooting guidance.
