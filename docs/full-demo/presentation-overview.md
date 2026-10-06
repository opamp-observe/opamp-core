# Full Demo Presentation Overview

## Slide 1: Demo Purpose

This demo shows one OpAMP provider managing five different telemetry agents through a shared server UI.

Key points:

- Fluent Bit and Fluentd run in supervisor mode, so the consumer launches and manages the agent process.
- Vector, Elastic Agent, and Elastic Heartbeat run in observer mode, so the consumer attaches to already-running agents.
- Fluent Bit and Vector use the OpAMP WebSocket transport.
- Fluentd, Elastic Agent, and Elastic Heartbeat use the OpAMP HTTP transport.
- Active and replacement configurations are visible in the server catalog and can be deployed from the UI.
- Agent binaries can be resolved from `PATH` or supplied as absolute paths, with `use-demo-agent-paths.cmd` provided for the default local `D:\dev-tools` layout.

## Slide 2: Runtime Topology

```mermaid
flowchart LR
    UI[Server UI<br/>Config Catalog<br/>Client Config Generator]
    Provider[OpAMP Provider<br/>127.0.0.1:8080]
    Generator[Client Config Generator<br/>schema-driven JSON files]
    Logstash[Logstash Container<br/>beats input :5044]

    FBC[Fluent Bit Consumer<br/>Supervisor mode]
    FDC[Fluentd Consumer<br/>Supervisor mode]
    VC[Vector Consumer<br/>Observer mode]
    EAC[Elastic Agent Consumer<br/>Observer mode]
    HBC[Heartbeat Consumer<br/>Observer mode]

    FB[Fluent Bit]
    FD[Fluentd]
    V[Vector]
    EA[Elastic Agent]
    HB[Elastic Heartbeat]

    UI --> Provider
    UI --> Generator
    Generator -->|save/load generated consumer configs| Provider

    FBC <-->|WebSocket OpAMP| Provider
    VC <-->|WebSocket OpAMP| Provider
    FDC <-->|HTTP OpAMP| Provider
    EAC <-->|HTTP OpAMP| Provider
    HBC <-->|HTTP OpAMP| Provider

    FBC -->|launches and supervises| FB
    FDC -->|launches and supervises| FD
    VC -.->|observes local API/process| V
    EAC -.->|observes local API/process| EA
    HBC -.->|observes local API/process| HB

    EA -->|events| Logstash
    HB -->|events| Logstash
```

## Slide 3: Transport Split

```mermaid
flowchart TB
    Provider[OpAMP Provider<br/>/v1/opamp]

    subgraph SocketTransport[Socket transport]
      FB[Fluent Bit Consumer<br/>transport: websocket]
      V[Vector Consumer<br/>transport: websocket]
    end

    subgraph HttpTransport[HTTP transport]
      FD[Fluentd Consumer<br/>transport: http]
      EA[Elastic Agent Consumer<br/>transport: http]
      HB[Heartbeat Consumer<br/>transport: http]
    end

    FB <-->|persistent WebSocket| Provider
    V <-->|persistent WebSocket| Provider
    FD <-->|poll/request HTTP| Provider
    EA <-->|poll/request HTTP| Provider
    HB <-->|poll/request HTTP| Provider
```

Speaker note:

The socket side demonstrates long-lived OpAMP connectivity for agents that benefit from persistent control channels. The HTTP side keeps the rest of the estate on the simpler request/response path.

## Slide 4: Configuration Deployment Flow

```mermaid
sequenceDiagram
    participant Operator
    participant UI as Server UI
    participant Catalog as Config Catalog
    participant Generator as Client Config Generator
    participant Provider as OpAMP Provider
    participant Consumer as Selected Consumer
    participant Agent

    Operator->>UI: Select connected client
    Operator->>Generator: Generate or adjust consumer JSON (optional)
    Generator-->>UI: Saved JSON configuration file
    UI->>Catalog: Browse replacement configs
    Catalog-->>UI: Return docs/full-demo/replacements entry
    Operator->>UI: Deploy selected config
    UI->>Provider: Queue remote config
    Provider->>Consumer: Send AgentRemoteConfig
    Consumer->>Agent: Apply or stage agent config
    Consumer-->>Provider: RemoteConfigStatus and EffectiveConfig
    Provider-->>UI: Show updated status
```

## Slide 5: Files To Point At

| Purpose | Path |
|---|---|
| Provider and catalog setup | `docs/full-demo/provider/opamp-provider-full-demo.json` |
| Active agent configs | `docs/full-demo/active` |
| Replacement configs | `docs/full-demo/replacements` |
| Consumer OpAMP configs | `docs/full-demo/consumers` |
| Logstash pipeline | `docs/full-demo/logstash/logstash.container.conf` |
| Add local agents to `PATH` | `docs/full-demo/use-demo-agent-paths.cmd` |
| Start observer-mode agents | `docs/full-demo/start-observed-agents.ps1` |
| Stop observer-mode agents | `docs/full-demo/stop-observed-agents.ps1` |

## Slide 6: Demo Success Criteria

The demo is healthy when:

- All five consumers appear in the server UI.
- Fluent Bit and Vector show WebSocket-backed OpAMP connectivity.
- Fluentd, Elastic Agent, and Heartbeat show HTTP-backed OpAMP connectivity.
- Fluent Bit and Fluentd are managed as supervisor processes.
- Vector, Elastic Agent, and Heartbeat are detected by observer-mode consumers.
- Replacement configs from `docs/full-demo/replacements` can be selected and sent from the UI.
- Elastic Agent and Heartbeat events arrive in the Logstash container output directory.
