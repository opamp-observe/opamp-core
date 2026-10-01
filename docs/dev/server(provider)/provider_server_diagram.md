# Provider Server Architecture Diagram

This document contains Mermaid source diagrams for the provider/server side.
Rendered PNG versions are embedded in [docs/provider_server_diagrams.md](../../provider_server_diagrams.md).

## Class and Module Relationships

```mermaid
classDiagram
    direction LR

    class ProviderServerEntrypoint {
      <<module>>
      +main()
    }

    class ProviderApp {
      <<module>>
      +opamp_http()
      +opamp_websocket()
      +enforce_bearer_auth()
      +set_state_restore_status()
      +_process_websocket_agent_message()
      +_build_http_success_response()
      +_finalize_server()
    }

    class AppRoutesClients {
      <<module>>
      +register_client_routes()
      +list_clients()
      +queue_command()
      +set_client_actions()
      +set_requested_config()
      +queue_remote_config_offer()
      +queue_connection_settings_offer()
    }

    class AppRoutesSettings {
      <<module>>
      +register_settings_routes()
      +get_comms_settings()
      +update_comms_settings()
      +get_server_opamp_config()
      +save_state_snapshot_now()
    }

    class AppRoutesUI {
      <<module>>
      +register_ui_routes()
      +web_ui()
      +help_page()
      +latest_docs_redirect()
      +ui_features()
    }

    class MetricsRoutes {
      <<module>>
      +register_metrics_routes()
      +get_prometheus_metrics()
      +get_metrics_graphs()
    }

    class ServerToAgentResponseBuilder {
      +build_response()
      +has_dispatched_command_payload()
      +_apply_command_intent()
      +_apply_next_action()
    }

    class CommandQueue {
      <<module>>
      +queue_command_from_payload()
      +queue_custom_command_from_mcp()
      +build_custom_command_mcp_error_payload()
    }

    class AppPersistence {
      <<module>>
      +PersistenceTracker
      +request_process_shutdown()
    }

    class StatePersistence {
      <<module>>
      +save_state_snapshot()
      +restore_state_snapshot()
      +resolve_restore_snapshot_path()
      +list_snapshot_files()
      +prune_snapshot_files()
    }

    class ProviderUiAssets {
      <<module>>
      +load_provider_ui_assets()
      +render_help_html()
    }

    class ComponentFeatures {
      <<module>>
      +register_provider_component_entries()
      +ui_menu_items_from_component_entries()
    }

    class ProviderConfig {
      <<module>>
      +load_config_with_overrides()
      +set_config()
      +persist_provider_config()
      +_load_provider_tls_config()
    }

    class ProviderAuth {
      <<module>>
      +evaluate_bearer_auth()
      +evaluate_asgi_scope_auth()
      +reload_auth_settings()
    }

    class ClientStore {
      +upsert_from_agent_msg()
      +queue_command()
      +next_pending_command()
      +mark_command_sent()
      +set_next_actions()
      +pop_next_action()
      +set_agent_identification()
      +pop_agent_identification()
    }

    class ClientRecord
    class EventHistory
    class CommandRecord

    class CommandRegistry {
      <<module>>
      +command_object_factory()
      +get_command_metadata()
      +get_custom_capabilities_list()
    }

    class CommandObjectInterface {
      <<interface>>
      +get_command_classifier()
      +get_key_value_dictionary()
      +get_capability_fqdn()
      +isOpAMPStandard()
    }

    class RestartAgent
    class ChatOpCommand
    class CommandShutdownAgent
    class CommandNullCommand

    class ProviderTransport {
      <<module>>
      +encode_message()
      +decode_message()
    }

    class MCPRoutes {
      <<module>>
      +tool_openapi_spec()
      +list_connected_otel_agents()
      +list_all_commands()
    }

    class MCPBridge {
      <<module>>
      +register_tool_routes()
      +register_mcp_transport()
    }

    ProviderServerEntrypoint --> ProviderConfig
    ProviderServerEntrypoint --> ProviderApp
    ProviderServerEntrypoint --> ClientStore
    ProviderServerEntrypoint --> StatePersistence

    ProviderApp --> ProviderAuth
    ProviderApp --> ProviderConfig
    ProviderApp --> ClientStore
    ProviderApp --> CommandRegistry
    ProviderApp --> ProviderTransport
    ProviderApp --> MCPBridge
    ProviderApp --> ServerToAgentResponseBuilder
    ProviderApp --> AppRoutesClients
    ProviderApp --> AppRoutesSettings
    ProviderApp --> AppRoutesUI
    ProviderApp --> MetricsRoutes
    ProviderApp --> AppPersistence
    ProviderApp --> StatePersistence
    ProviderApp --> ProviderUiAssets
    ProviderApp --> ComponentFeatures
    AppRoutesClients --> CommandQueue
    AppRoutesClients --> ClientStore
    AppRoutesSettings --> ClientStore
    AppRoutesSettings --> StatePersistence
    MetricsRoutes --> ClientStore
    ServerToAgentResponseBuilder --> ClientStore

    ClientStore o-- ClientRecord
    ClientRecord o-- CommandRecord
    CommandRecord --|> EventHistory

    CommandRegistry ..> CommandObjectInterface
    RestartAgent ..|> CommandObjectInterface
    ChatOpCommand ..|> CommandObjectInterface
    CommandShutdownAgent ..|> CommandObjectInterface
    CommandNullCommand ..|> CommandObjectInterface

    MCPBridge --> ProviderAuth
    MCPBridge --> MCPRoutes
    MCPRoutes --> ClientStore
    MCPRoutes --> CommandRegistry
    MCPRoutes --> CommandQueue
```

## Runtime Entrypoints and Transport

```mermaid
flowchart TD
    A["scripts/run_opamp_server.sh or .cmd"] --> B["python -m opamp_provider.server"]
    C["installed CLI: opamp-provider"] --> B

    B --> D["server.main()"]
    D --> E["provider_config.load_config_with_overrides(...)"]
    E --> F["provider_config.set_config(...)"]
    F --> G["STORE.set_default_heartbeat_frequency(...)"]
    G --> H{"--restore requested and persistence enabled?"}
    H -->|Yes| I["restore_state_snapshot(...)"]
    H -->|No| J["record restore skipped/not requested"]
    I --> K["attach_observability(...)"]
    J --> K
    K --> L{"provider.tls configured?"}
    L -->|No| M["Quart app.run(host, port)"]
    L -->|Yes| N["Quart app.run(host, port, certfile, keyfile)"]

    M --> O["POST /v1/opamp"]
    M --> P["WEBSOCKET /v1/opamp"]
    M --> Q["/api/* + /tool/* + /ui + /help + /doc-set + /metrics/*"]

    N --> O
    N --> P
    N --> Q

    O --> R["opamp_http()"]
    R --> S["STORE.upsert_from_agent_msg(..., channel=HTTP)"]
    S --> T["ServerToAgentResponseBuilder.build_response(...)"]
    T --> U["ServerToAgent protobuf response"]

    P --> V["opamp_websocket()"]
    V --> W["decode_message() + AgentToServer parse"]
    W --> X["STORE.upsert_from_agent_msg(..., channel=websocket)"]
    X --> Y["ServerToAgentResponseBuilder.build_response(...)"]
    Y --> Z["encode_message() + websocket.send(...)"]
```

## Command Queue and Dispatch Pipeline

```mermaid
flowchart TD
    A["Web UI or API caller"] --> B["POST /api/clients/:client_id/commands"]
    B --> C["app_routes_clients.queue_command(...)"]
    C --> D["command_queue.queue_command_from_payload(...)"]

    D --> E{"Concrete command object available?"}
    E -->|Yes| F["command_object_factory(...)"]
    E -->|No| G["Use normalized pairs directly"]
    F --> H["STORE.queue_command(...)"]
    G --> H

    H --> I["CommandRecord stored on ClientRecord.commands and events"]

    J["Client check-in via HTTP or websocket"] --> K["STORE.next_pending_command(client_id)"]
    K --> L["ServerToAgentResponseBuilder.build_response(...)"]
    L --> M["_apply_command_intent(...)"]
    M --> N{"Builder selected"}
    N -->|command/restart| O["ServerToAgent.command"]
    N -->|command/forceresync| P["ServerToAgent.flags ReportFullState"]
    N -->|custom/custom_command| Q["ServerToAgent.custom_message"]

    O --> R["Transmit response to client"]
    P --> R
    Q --> R

    R --> S["STORE.mark_command_sent(...)"]
```

## Auth and MCP Transport Routing

```mermaid
flowchart TD
    A["Incoming request"] --> B{"Transport type"}

    B -->|HTTP to Quart route| C["@app.before_request enforce_bearer_auth()"]
    C --> D["provider_auth.evaluate_bearer_auth(...)"]
    D --> E{"Allowed?"}
    E -->|No| F["Return JSON 401/503 (+ WWW-Authenticate for 401)"]
    E -->|Yes| G["Continue to route handler"]

    B -->|ASGI scope for /sse, /messages, /mcp| H["register_mcp_transport() dispatch wrapper"]
    H --> I["provider_auth.evaluate_asgi_scope_auth(scope)"]
    I --> J{"Allowed?"}
    J -->|No| K["ASGI auth rejection payload"]
    J -->|Yes| L["Forward to FastMCP ASGI app"]

    B -->|WebSocket /v1/opamp| M["opamp_websocket()"]
    M --> N["decode_message() + provider protocol handling"]

    O["Non-OpAMP HTTP routes (for example /tool, /sse, /messages, /mcp, /api, /ui, /help, /doc-set)"] --> C
    O --> I
```
