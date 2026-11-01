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

# OpAMP for Open-Source Observability Agents

This repository is an open, extensible implementation of the OpenTelemetry
[Open Agent Management Protocol (OpAMP)](https://opentelemetry.io/docs/specs/opamp/).
It provides both an OpAMP provider (server/control plane) and consumer
(client/supervisor) implementations for managing heterogeneous observability agents,
with a particular focus on bringing existing open-source tools into an OpAMP-managed
fleet without requiring invasive changes to those tools.

## What OpAMP Is

Telemetry agents are normally good at moving logs, metrics, and traces, but operating a
large fleet raises a different set of questions: Which agents are alive? Which version
and configuration are they running? How can configuration or a restart be delivered
consistently? How can these operations span different agent technologies?

OpAMP defines a vendor-neutral control-plane protocol for that problem. An OpAMP client
reports an agent's identity, capabilities, health, and configuration state to an OpAMP
server. Subject to the capabilities negotiated by both sides, the server can return
configuration, connection settings, commands, package offers, or implementation-specific
custom messages. Communication uses Protobuf messages over HTTP or WebSocket.

The management client does not have to be built into the observed agent. The
[OpAMP specification](https://opentelemetry.io/docs/specs/opamp/#communication-model) explicitly allows it to be integrated, a plugin, a sidecar, or a separate supervisor.
That separation is important: it lets mature agents participate in a standard management
plane while preserving their existing data plane and deployment model.

### Why OpAMP is valuable

- **One contract for a mixed fleet.** Operators can use common identity, health,
  heartbeat, configuration, and command semantics across agent types and vendors.
- **Fleet-level visibility and control.** A server can maintain a central view of
  distributed agents and deliver intent through one protocol instead of bespoke node
  integrations.
- **Capability-led interoperability.** Clients and servers advertise what they support,
  allowing partial implementations to cooperate without pretending every agent has the
  same features.
- **Separation from telemetry transport.** OpAMP manages the agents; it does not replace
  OTLP or the other destinations to which those agents send data.
- **A path for existing software.** The supervisor model can add management behavior
  around an agent without first changing the agent's codebase.

## What This Implementation Brings

This project turns the protocol into an operator-oriented, open-source management stack.
It includes both ends of the OpAMP exchange and the practical services around them:

- a provider with HTTP and WebSocket OpAMP transports, a browser console, APIs, command
  and remote-configuration workflows, authentication options, state persistence, and
  optional MCP exposure;
- A specialization of the supervisor concept referred to as an observer, ideal for tapping into existing deployments to control the existing telemetry agents.
- prebuilt consumer plugins for Fluent Bit, Fluentd, Elastic Agent, Elastic Heartbeat, Vector, (which understand how to use the telemetry agents interfaces to provide the OpAMP capabilities).
  and scripted simulation, within a framework that supports supervisor and observer
  lifecycle strategies;
- built-in reporting for identity, status, health, effective configuration, remote
  configuration status, heartbeat, restart, and custom capability/message paths, subject
  to the selected consumer's advertised capabilities;
- optional configuration editing and validation, a configuration catalog, a schema-driven
  consumer configuration generator, and a server connection-credentials manager;
- custom actions and dynamically discovered consumer plugins, so new agents and local
  operations can be added without turning the core into a product-specific fork; and
- an optional conversation broker that exposes constrained provider tools through
  collaboration channels and AI-assisted planning.

The current built-in support is recorded in the [consumer capability matrix](docs/consumer_implementations.md), while the
[feature and specification alignment](docs/features.md) identifies partial, planned, and deliberately unsupported areas. This is a working framework with useful end-to-end paths, not a claim that every optional OpAMP capability is complete.

### Design ideals

The implementation is guided by a few practical ideals:

- **Open-source first.** Fluent Bit, Fluentd, Vector, and other accessible agent
  ecosystems should be manageable without requiring a proprietary agent or control plane.
- **Integrate rather than invade.** Supervisor mode can own an agent process, while
  observer mode can attach management and reporting to an already managed process.
- **Pluggability over hard-coding.** Consumer entry points, custom command handlers,
  provider component entry points, collaboration adapters, and optional services keep
  agent-specific behavior at explicit boundaries.
- **Useful with a small footprint.** The core provider and consumer can run without a
  mandatory heavyweight database or every optional service. Additional capabilities can
  be deployed only where they add value.
- **Low-friction experimentation.** Python, JSON configuration, packaged command-line
  entry points, simulators, and local tooling make it possible to get from zero to a
  visible OpAMP exchange quickly.
- **Protocol alignment without protocol confinement.** Standard OpAMP behavior remains
  the base, while documented custom messages and MCP tools provide controlled extension
  points for agent-specific operations.

These goals expand on the project's [implementation philosophy](docs/dev/implementation_philosophy.md) and the original [OpAMP with Fluent Bit: Observability and ChatOps](https://blog.mp3monster.org/2026/03/23/opamp-with-fluent-bit/) project write-up.

## Brief Demo

There is a demo recorded as part of the Open Source Observability Day conference:

 https://youtu.be/tKQjnS6wbsc 

The recording illustrates features that contribute to the 0.6 release.

## How It Compares with the OpenTelemetry Implementations

OpenTelemetry currently provides several related building blocks rather than one
all-purpose operator product:

- [`opamp-go`](https://github.com/open-telemetry/opamp-go) supplies reusable Go client
  and server protocol implementations and examples.
- The Collector's
  [`opamp` extension](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/extension/opampextension)
  provides an in-process OpAMP client for the OpenTelemetry Collector and is currently
  marked alpha.
- The
  [OpenTelemetry Collector OpAMP Supervisor](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/cmd/opampsupervisor)
  is a reference supervisor specialized for launching and managing an OpenTelemetry
  Collector. It expects an OpAMP server and implements a broader set of Collector-focused
  protocol capabilities than this project currently does.

| Area | OpenTelemetry implementation | This project |
| --- | --- | --- |
| Primary target | OpenTelemetry Collector and reusable Go protocol integrations | Existing open-source agents including Fluent Bit, Fluentd, Vector, and selected Elastic agents |
| Agent integration | Native Collector extension or Collector-specific external supervisor | External consumer plugins using supervisor or observer mode |
| Server offering | Go server library and example server; the Collector supervisor requires a separate server | Operator-facing provider with UI, API, persistence, command/config workflows, and optional MCP |
| Protocol breadth | The reference supervisor covers more of the Collector-oriented OpAMP capability set | A deliberately partial implementation focused on working multi-agent operational paths and extensibility |
| Extension model | Go APIs, custom builds, Collector components, and emerging supervisor extensions | Python package entry points, agent adapters, custom actions/messages, Quart component entry points, and optional services |
| Human interface | Determined by the selected external OpAMP backend | Built-in web console plus optional CLI, MCP, ChatOps, and AI-assisted tool orchestration |

The approaches are complementary. The OpenTelemetry implementations are the stronger fit
for native Collector management and protocol-library reuse. This project explores how the
same open protocol can manage a broader open-source estate and provide the surrounding
operator experience. Protocol conformance is intended to make clients and servers
interchangeable, but cross-implementation compatibility still needs systematic testing
before it should be assumed in production.

## ChatOps and AIOps

The provider can expose a bounded set of operational tools through Model Context Protocol
(MCP). The optional conversation broker discovers those tools and makes them available
through Slack today; the collaboration layer is designed so other adapters can be added.
Two interaction styles can coexist:

- **ChatOps:** deterministic commands such as listing agents, checking state, or invoking
  an explicitly named tool provide a shared operational interface in a team channel.
- **AI-assisted operations:** a configured language model can translate natural language
  into a bounded, multi-step plan that uses only the tools discovered from the provider,
  stops on repeated work or a configured step limit, and summarizes the result.

That creates a path such as:

```text
Operator -> collaboration channel -> broker/planner -> MCP tools
         -> OpAMP provider -> selected consumer -> managed agent
```

Practical uses include fleet queries, guided diagnosis, configuration validation before
deployment, targeted restart or custom-action workflows, and plain-language summaries of
agent state. The design also keeps the central routing and policy boundary at the provider
instead of requiring chat tooling to connect independently to every managed node, an idea
described further in the
[project ChatOps article](https://blog.mp3monster.org/2026/03/23/opamp-with-fluent-bit/).

This is a foundation for AIOps, not an unrestricted autonomous control loop. Production
deployments should combine tool allowlisting and bounded planning with provider
authentication, network controls, human approval where appropriate, and retained
operational evidence. See the [conversation broker](agent_broker/README.md) and its
[strict command and AI planning model](agent_broker/docs/slack_command_syntax.md).

## Components and Repository Layout

The required and optional components, deployment roles, build/package entry points, and
folder-level map have moved to
[components and repository layout](docs/components_and_repository_layout.md).

At minimum, the provider can run by itself as a server. A meaningful end-to-end OpAMP
session requires the provider and at least one consumer. The editor, catalog, generator,
credentials manager, CLI, broker, MCP setup tooling, and simulator are optional.

## Documentation

The `Build and deploy GitHub Pages` workflow publishes `docs/` only from the
`main` branch when documentation changes. The repository Pages source must be
set to **GitHub Actions**; the workflow preserves the `docs/CNAME` custom domain
configuration for `opamp.info`. The organization Actions policy must allow the
GitHub-owned `actions/upload-pages-artifact` and `actions/deploy-pages` actions.

- [Product installation](docs/installation.md) — deployment scenarios, released wheels,
  automation, and command-line tooling.
- [Documentation hub](docs/README.md) — full setup, architecture, and run instructions.
- [Components and repository layout](docs/components_and_repository_layout.md) — component
  roles, required/optional status, packaging, and folder map.
- [Features and specification alignment](docs/features.md) — implemented, partial,
  planned, and deliberately unsupported protocol areas.
- [Consumer implementations](docs/consumer_implementations.md) — built-in client and
  capability matrix.
- [Provider diagrams](docs/provider_server_diagrams.md) and
  [consumer diagrams](docs/consumer_client_diagrams.md) — architecture walkthroughs.
- [Provider guide](provider/README.md) and [consumer guide](consumer/README.md) — runtime
  configuration and component-specific behavior.
- [Conversation broker](agent_broker/README.md) — ChatOps, AI provider, MCP, and
  collaboration-channel setup.
- [Roadmap](docs/roadmap/index.md) — future ideas without timeline commitments.
