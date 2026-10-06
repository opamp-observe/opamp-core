# OpAMP Provider

Quart-based OpAMP server skeleton and web UI.

## Table of Contents

- [Quickstart (manual)](#quickstart-manual)
- [Run scripts](#run-scripts)
- [Configuration](#configuration)
- [Fields](#fields)
- [Human-In-Loop Approval Workflow](#human-in-loop-approval-workflow)
- [State Persistence and Restore](#state-persistence-and-restore)
- [CLI Overrides](#cli-overrides)
- [Running As A Service/Daemon](#running-as-a-servicedaemon)
- [Custom Actions](#custom-actions)
- [Web UI](#web-ui)
- [Optional Bearer Authentication](#optional-bearer-authentication)
- [IdP Settings Illustration](#idp-settings-illustration)
- [Shutdown API](#shutdown-api)

## Quickstart (manual)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Generate protobufs (optional; auto-generated on first import):

```bash
python -m opamp_provider.proto.ensure
```

Run the server:

```bash
python -m opamp_provider.server --port 4320
```

Installed CLI command:

```bash
opamp-provider --config-path ./config/opamp.json --port 4320
```

Packaging note:

- the provider runtime command `opamp-provider` is separate from the workspace launcher `opamp-cli`
- provider wheel builds warn when `opamp-cli` is not detected in the workspace or active Python environment
- install/deploy `opamp-cli` separately if you want the guided start/stop and status tooling

Version/help:

```bash
opamp-provider --version
opamp-provider --help
```

## Run scripts

Helper scripts live in `scripts/` at the repo root:

- Windows CMD: `scripts/run_opamp_server.cmd`
- Bash: `scripts/run_opamp_server.sh`

Both scripts write logs to `logs/opamp_server.log` and rotate it on startup.
If `logs/` does not exist yet, the scripts create it when logging starts.
For MCP client setup wrappers/canonical script usage, FastMCP client role, and
command-line parameters, see `../mcp/README.md`.

## Configuration

The provider reads `opamp.json` from the repo `config/` folder by default. You can override the
config file location with the `OPAMP_CONFIG_PATH` environment variable.

Provider configuration variants are also available in `config/`:

- `config/opamp.json`: default development config with embedded config editor, catalog, and client config generator UI
- `config/opamp.provider-with-editor-service.json`: provider plus embedded config editor UI
- `config/opamp.provider-with-editor-and-catalog-services.json`: provider plus embedded config editor and catalog UI
- `config/opamp.provider-with-client-config-generator-service.json`: provider plus embedded schema-driven client config generator UI

Example alternate launch:

```bash
opamp-provider --config-path ./config/opamp.provider-with-editor-and-catalog-services.json
```

Example `opamp.json`:

```json
{
  "provider": {
    "delayed_comms_seconds": 60,
    "significant_comms_seconds": 300,
    "webui_port": 8080,
    "minutes_keep_disconnected": 5,
    "retryAfterSeconds": 30,
    "client_event_history_size": 50,
    "log_level": "INFO",
    "default_heartbeat_frequency": 30,
    "latest_docs_url": "https://htmlpreview.github.io/?https://raw.githubusercontent.com/opamp-observe/opamp-core/main/github-landingpage/index.html",
    "human_in_loop_approval": false,
    "allow-mcp": false,
    "opamp-use-authorization": "none",
    "ui-use-authorization": "none",
    "state_persistence": {
      "enabled": true,
      "state_file_prefix": "runtime/opamp_server_state",
      "retention_count": 5,
      "flush_mode": "graceful_shutdown",
      "autosave_interval_seconds_since_change": 600
    },
    "tls": {
      "enabled": true,
      "cert_file": "certs/provider-server.pem",
      "key_file": "certs/provider-server-key.pem",
      "trust_anchor_mode": "none"
    }
  }
}
```

### Fields

- `provider.delayed_comms_seconds` (integer, optional, default `60`)
  Time in seconds before a client is marked delayed (amber).
- `provider.significant_comms_seconds` (integer, optional, default `300`)
  Time in seconds before a client is marked significantly delayed (red).
- `provider.webui_port` (integer, optional, default `8080`)
  Port for the provider UI and HTTP server.
- `provider.minutes_keep_disconnected` (integer, optional, default `30`)
  Minutes to retain disconnected clients before purging. Disconnections are
  purged during UI refresh at half this interval.
- `provider.retryAfterSeconds` (integer, optional, default `30`)
  Retry delay (in seconds) used when the server responds with an unavailable error.
- `provider.client_event_history_size` (integer, optional, default `50`)
  Maximum number of retained client history events.
- `provider.log_level` (string, optional, default `INFO`)
  Provider log level name (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
  Level names are resolved via Python `logging`.
- `provider.default_heartbeat_frequency` (integer, optional, default `30`)
  Default heartbeat interval assigned to clients.
- `provider.latest_docs_url` (string, optional, default landing-page preview URL)
  Redirect target URL for `GET /doc-set`.
- `provider.human_in_loop_approval` (boolean, optional, default `false`)
  Requires unknown agents to be reviewed in the Pending Approval workflow before they are accepted.
  This setting can be updated in the UI via Global Settings -> Server Settings.
- `provider.allow-mcp` (boolean, optional, default `false`)
  Controls whether the Streamable HTTP MCP route at `/mcp` is available.
  When `false`, `/mcp` and descendants are rejected even if the provider has other MCP transports enabled.
- `provider.opamp-use-authorization` (string, optional, default `"none"`)
  OpAMP transport authorization mode for `/v1/opamp` HTTP and WebSocket:
  - `none`: no OpAMP bearer-token enforcement.
  - `config-token`: require `Authorization: Bearer <token>` and compare against the
    `OPAMP_AUTH_STATIC_TOKEN` environment variable (this token is not read from `opamp.json`).
  - `idp`: require bearer token and validate as JWT using IdP settings
    (`OPAMP_AUTH_JWT_ISSUER`, `OPAMP_AUTH_JWT_AUDIENCE`, optional `OPAMP_AUTH_JWT_JWKS_URL`,
    `OPAMP_AUTH_JWT_LEEWAY_SECONDS`).
- `provider.ui-use-authorization` (string, optional, default `"none"`)
  Non-OpAMP authorization mode for HTTP and MCP transport routes (for example `/tool`, `/sse`,
  `/messages`, `/mcp` when enabled, `/api`, `/ui`, `/help`, `/doc-set`):
  - `none`: no non-OpAMP bearer-token enforcement.
  - `config-token`: require `Authorization: Bearer <token>` and compare against the
    `UI_AUTH_STATIC_TOKEN` environment variable (this token is not read from `opamp.json`).
  - `idp`: require bearer token and validate as JWT using IdP settings
    (`UI_AUTH_JWT_ISSUER`, `UI_AUTH_JWT_AUDIENCE`, optional `UI_AUTH_JWT_JWKS_URL`,
    `UI_AUTH_JWT_LEEWAY_SECONDS`).
- `provider.tls` (object, optional)
  TLS listener configuration for the single provider listener.
  If this section is omitted, provider runs HTTP-only.
  - `provider.tls.enabled` (boolean, optional, default `true` when `provider.tls` exists)
    Controls whether TLS is active. Set to `false` to force HTTP-only mode while keeping TLS file settings in config.
  - `provider.tls.cert_file` (string, required when `provider.tls.enabled=true`)
    Path to PEM server certificate file.
  - `provider.tls.key_file` (string, required when `provider.tls.enabled=true`)
    Path to PEM server private key file.
  - `provider.tls.trust_anchor_mode` (string, optional, default `"full_chain_to_root"`)
    Allowed values: `none`, `partial_chain`, `full_chain_to_root`.
    This value is validated for config consistency in the current phase.
    `scripts/run_opamp_server.* --https` sets this to `none` for local self-signed usage.
- `provider.state_persistence` (object, optional)
  Runtime state snapshot persistence configuration.
  - `provider.state_persistence.enabled` (boolean, optional, default `false`)
    Enables persistent runtime snapshots when `true`.
  - `provider.state_persistence.state_file_prefix` (string, optional, default `"runtime/opamp_server_state"`)
    Prefix used for timestamped snapshot files (`<prefix>.<YYYYMMDDTHHMMSSZ>.json`).
    The parent folder is created automatically when a snapshot is saved (for example,
    `server-state/` when `state_file_prefix` is `server-state/opamp_server_state`).
  - `provider.state_persistence.retention_count` (integer, optional, default `5`)
    Number of most-recent snapshots to keep.
  - `provider.state_persistence.flush_mode` (string, optional, default `"graceful_shutdown"`)
    Initial flush strategy; current implementation writes on graceful shutdown and autosave checkpoints.
  - `provider.state_persistence.autosave_interval_seconds_since_change` (integer, optional, default `600`)
    Autosave interval in seconds for non-heartbeat OpAMP state changes.

## Human-In-Loop Approval Workflow

When `provider.human_in_loop_approval` is enabled:

- Unknown agents are not added directly to the active client list.
- Their first payload is translated into a pending client record and stored in a pending-approval list.
- If payload-to-client transformation fails, the agent UID is added to a blocked list.
- Blocked agents are rejected on both HTTP and WebSocket transports.

The web UI displays a `Pending Approval` count in the top metadata bar.
Selecting it opens an approval dialog with:

- UID
- instance ID
- IP
- agent type/version
- host type
- accept/block decision per row (default `block`) and set-all controls

Submitting `OK` moves accepted agents into the active client list and adds blocked entries to the blocked list.

Related API endpoints:

- `GET /api/approvals/pending`
- `POST /api/approvals/pending`

## State Persistence and Restore

When `provider.state_persistence.enabled=true`, provider can write and restore runtime snapshots.

- Snapshot naming: `<state_file_prefix>.<YYYYMMDDTHHMMSSZ>.json` (UTC suffix).
- Snapshot retention: newest `retention_count` files are retained (default `5`).
- Blocked-agent snapshot payload is allowlisted to `instance_uid`, `ip`, and `blocked_at`.
- On restore, unknown persisted attributes are ignored; missing attributes are initialized with compatibility defaults and restore can queue a force-resync request for incomplete restored clients with valid UIDs.
- Global Settings -> Server Settings includes a `Save State Now` button for manual snapshot writes.

Restore CLI usage:

```bash
opamp-provider --config-path ./config/opamp.json --restore
```

Restores from the latest snapshot matching `state_file_prefix`.

```bash
opamp-provider --config-path ./config/opamp.json --restore ./runtime/opamp_server_state.20260409T103000Z.json
```

Restores from an explicit snapshot file path.

If restore fails (missing/unreadable/corrupt/incompatible file), provider logs the error and continues startup with empty/default in-memory state.

Manual snapshot API (used by the UI button):

```text
POST /api/settings/state/save
```

## CLI Overrides

You can override selected config values at runtime:

- `--config-path` overrides the config file location.
- `--diagnostic` enables diagnostic-only UI/API features and forces `DEBUG` logging for local troubleshooting.
- `--port` overrides `provider.webui_port`.
- `--log-level` overrides `provider.log_level`.
- `--restore` restores from latest snapshot for the configured `state_file_prefix`.
- `--restore <snapshot_file>` restores from an explicit snapshot file path.

## Running As A Service/Daemon

For Linux `systemd` and Windows service examples for provider and consumer deployments (and consumer launch permissions for Fluent Bit/Fluentd), see:

- `../docs/service_daemon_setup.md`

## Custom Actions

For the shared provider+consumer guide on implementing and deploying custom actions:

- `../docs/dev/adding_your_own_custom_action.md`

## Web UI

- Console: `http://localhost:8080/ui`
- Help: `http://localhost:8080/help`
- Optional catalog UI (when enabled): `http://localhost:8080/catalog`
- Optional catalog help page (when enabled): `http://localhost:8080/catalog/help`
- The help page includes the server component version generated from git commit/date metadata.
- Footer `Latest docs` links in the HTML pages go via `http://localhost:8080/doc-set`.
- By default, that provider redirect points at the published landing page preview URL from `provider.latest_docs_url`.
- Starting the provider with `--diagnostic` enables the `server-opamp-config` settings tab and other diagnostic-only endpoints used for local inspection/testing.
- JavaScript asset mode is controlled by `APP_ENABLE_DEV_FEATURES`:
  - truthy (`1`, `true`, `yes`, `on`): prefer readable source files
  - otherwise: prefer compacted files
- Provider UI asset compaction covers:
  - `web_ui_state.js`
  - `web_ui_functions.js`
  - `web_ui_framework.js`
  - `web_ui_bindings.js`
- Each source asset has a matching compacted file with the `.mini.js` suffix.
- If preferred assets are unavailable, provider falls back to available assets and logs a warning that the flag preference could not be honored.
- Minification workflow details are documented in `../docs/dev/minification_process.md`.
- Provider feature dropdown entries are configuration-driven from top-level `component-entry-points.quart` entries that provide `label` and `url` values.
- Provider can embed additional Quart components at startup via `component-entry-points.quart` entrypoints (for example config-service integration).
- The Client Config Generator is enabled with the same entry-point mechanism and exposes schema, list, load, validation, save, UI, and static-help routes only when its component entry is enabled.
- Provider catalog feature is configured under top-level `opamp.config_catalog` and scans configured folders/extensions for metadata columns derived from top comment lines (`config-service: key=value`).
- Embedded feature pages such as Config Editor, Config Catalog, and Client Config Generator show provider navigation in their headers; standalone deployments hide provider-only navigation.
- The main client table renders column filters directly beneath the headings.
- Text filters update immediately for free-text columns such as service instance ID and host fields.
- Connection status, health status, config version, host type, and host version use multi-select dropdown filters populated from the currently loaded table data.
- `Show Columns` / `Hide Columns` controls optional columns including `Health Status` and `First Registered`.
- The summary dialog uses `Connection Status` and `Health Status` labels consistently with the main table.

The UI includes a shutdown button that prompts for confirmation and calls the shutdown API.

## Optional Bearer Authentication

Authorization mode is config-driven and defaults to disabled (`none`) for both surfaces.
`opamp.json` selects each mode, while secrets/IdP settings are read from environment variables.

- `provider.opamp-use-authorization` controls `/v1/opamp` HTTP and WebSocket auth.
- `provider.ui-use-authorization` controls non-OpAMP HTTP and MCP/WebSocket auth.
- `provider.allow-mcp=false` keeps direct `/mcp` access disabled even when `/sse` or `/messages`
  transports remain available.
- `config-token` mode uses static token env vars:
  - OpAMP: `OPAMP_AUTH_STATIC_TOKEN`
  - Non-OpAMP: `UI_AUTH_STATIC_TOKEN`
- `idp` mode uses JWT env vars:
  - OpAMP: `OPAMP_AUTH_JWT_*`
  - Non-OpAMP: `UI_AUTH_JWT_*`

### IdP Settings Illustration

`opamp.json` selects independent auth modes for OpAMP and non-OpAMP routes:

```json
{
  "provider": {
    "opamp-use-authorization": "idp",
    "ui-use-authorization": "idp"
  }
}
```

Environment variables provide JWT validation settings for each surface:

```bash
# OpAMP transport JWT settings:
export OPAMP_AUTH_JWT_ISSUER='http://127.0.0.1:8081/realms/opamp'
export OPAMP_AUTH_JWT_AUDIENCE='opamp-mcp'
export OPAMP_AUTH_JWT_JWKS_URL='http://127.0.0.1:8081/realms/opamp/protocol/openid-connect/certs'
export OPAMP_AUTH_JWT_LEEWAY_SECONDS='30'

# Non-OpAMP JWT settings:
export UI_AUTH_JWT_ISSUER='http://127.0.0.1:8081/realms/opamp'
export UI_AUTH_JWT_AUDIENCE='opamp-ui'
export UI_AUTH_JWT_JWKS_URL='http://127.0.0.1:8081/realms/opamp/protocol/openid-connect/certs'
export UI_AUTH_JWT_LEEWAY_SECONDS='30'
```

At runtime, provider behavior is:

1. `provider.opamp-use-authorization=idp` enables bearer-token enforcement on `/v1/opamp`.
2. `provider.ui-use-authorization=idp` enables bearer-token enforcement for non-OpAMP HTTP and MCP/WebSocket routes.
3. `provider.allow-mcp=false` still blocks `/mcp` even when non-OpAMP auth would otherwise allow it.
4. `OPAMP_AUTH_JWT_*` defines OpAMP JWT validation; `UI_AUTH_JWT_*` defines non-OpAMP JWT validation.
5. Requests without a valid token are rejected (`401`/`403`).

See [docs/authentication.md](../docs/authentication.md) for full setup, Keycloak Docker script usage, and MCP token examples.

## Shutdown API

```
POST /api/shutdown
{"confirm": true}
```
