# Provider Server Diagrams Guide

This page explains the rendered provider/server diagrams and links each one back to Mermaid source and related docs.

## Source and Related Docs

- Mermaid source: [docs/dev/server(provider)/provider_server_diagram.md](<dev/server(provider)/provider_server_diagram.md>)
- Provider endpoint inventory: [docs/endpoints.md](endpoints.md)
- Provider auth setup and token modes: [docs/authentication.md](authentication.md)
- Command queue and payload internals: [docs/dev/command_process_implementation_note.md](dev/command_process_implementation_note.md)
- Mixin design reference (consumer-side pattern): [docs/dev/client(consumer)/consumer_mixins.md](<dev/client(consumer)/consumer_mixins.md>)

## Diagram 1: Class and Module Relationships

![Provider class and module relationships](provider_server_diagram_1.png)

What this shows:

- `server.py` bootstraps config and starts Quart.
- `app.py` owns OpAMP transport handlers and wires route modules, response building, persistence, metrics, UI assets, and MCP transport.
- `app_routes_clients.py`, `app_routes_settings.py`, `app_routes_ui.py`, and `metrics/routes.py` own the HTTP route families that used to be described as a single `app.py` surface.
- `ServerToAgentResponseBuilder` builds outbound protocol responses from store state, queued commands, and HTTP-only next actions.
- `state.py` (`STORE`) is the in-memory source of truth for client records and queued commands.
- `command_queue.py`, `commands.py`, and command implementation classes validate queue requests and build command/custom payload shapes.
- `mcptool` route and transport bridge modules expose MCP and integrate auth checks for MCP ASGI traffic.

## Diagram 2: Runtime Entrypoints and Transport

![Provider runtime entrypoints and transport](provider_server_diagram_2.png)

What this shows:

- Script/CLI entrypoints into `opamp_provider.server`.
- Startup path through config load, store defaults, and `app.run(...)`.
- Optional persisted-state restore before serving when `--restore` is used and persistence is enabled.
- Observability attachment before Quart starts.
- Conditional startup mode:
  - HTTP when provider TLS is not configured.
  - HTTPS when provider TLS cert/key settings are configured.
- Parallel request surfaces: OpAMP HTTP, OpAMP WebSocket, REST/UI/tool APIs, and metrics endpoints.

## Diagram 3: Command Queue and Dispatch Pipeline

![Provider command queue and dispatch pipeline](provider_server_diagram_3.png)

What this shows:

- How `/api/clients/<client_id>/commands` delegates to `command_queue.queue_command_from_payload(...)`.
- How normalized requests queue `CommandRecord` entries on both `ClientRecord.commands` and visible event history.
- Where command object factories are used for concrete command types.
- How pending commands are consumed on the next client check-in and encoded as:
  - `ServerToAgent.command`
  - `ServerToAgent.custom_message`
  - or `ServerToAgent.flags` (full-state resync)
- How sent commands are marked complete in store state.

## Diagram 4: Auth and MCP Transport Routing

![Provider auth and transport routing](provider_server_diagram_4.png)

What this shows:

- HTTP route protection via `@app.before_request` and `evaluate_bearer_auth(...)`.
- MCP ASGI protection via `register_mcp_transport(...)` wrapper and `evaluate_asgi_scope_auth(...)`.
- The difference between protected MCP/tool paths and the protocol handling path for `/v1/opamp` WebSocket.
