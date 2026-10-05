<!--
Copyright 2026 mp3monster.org
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

# Consumer Implementations

This page summarizes the built-in `opamp-consumer` implementations and the
OpAMP client capabilities that each implementation can advertise.

The built-in implementation list comes from
[`consumer/src/opamp_consumer/builtin_consumer_plugins.json`](../consumer/src/opamp_consumer/builtin_consumer_plugins.json).
Capabilities marked `Yes` are supported by the concrete client class. At
runtime, `consumer.agent_capabilities` is still merged with the mandatory
capabilities and intersected with the selected client's supported list.

## OpAMP Capability Sources

The OpAMP specification defines the `AgentCapabilities` bitmask and states that
agents may update capabilities over time. The same section defines
`ReportsStatus`, `AcceptsRemoteConfig`, and `ReportsEffectiveConfig`; the
remote-configuration section further states that a client must set
`AcceptsRemoteConfig` before a server may offer remote configuration.
Heartbeat support is described separately through `ReportsHeartbeat` and the
heartbeat interval negotiation flow.

Source documents:

- [OpenTelemetry OpAMP specification](https://opentelemetry.io/docs/specs/opamp/)
- [AgentCapabilities enum](https://opentelemetry.io/docs/specs/opamp/#agentcapabilities)
- [Remote configuration](https://opentelemetry.io/docs/specs/opamp/#remote-configuration)
- [Heartbeat reporting](https://opentelemetry.io/docs/specs/opamp/#heartbeat)

## Built-In Consumer Matrix

| `consumer.service_type` | Concrete client | Local implementation source | Target/status source documents | `ReportsStatus` | `AcceptsRestartCommand` | `ReportsHealth` | `AcceptsRemoteConfig` | `ReportsEffectiveConfig` | `ReportsHeartbeat` |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| `fluentbit` | Fluent Bit supervisor client | [`opamp_consumer.fluentbit.client.OpAMPClient`](../consumer/src/opamp_consumer/fluentbit/client.py) | [Fluent Bit monitoring API](https://docs.fluentbit.io/manual/administration/monitoring), [Fluent Bit hot reload](https://docs.fluentbit.io/manual/administration/hot-reload) | Yes | Yes | Yes | Yes | Yes | Yes |
| `fluentd` | Fluentd supervisor client | [`opamp_consumer.fluentd.client.FluentdOpAMPClient`](../consumer/src/opamp_consumer/fluentd/client.py) | [Fluentd `monitor_agent`](https://docs.fluentd.org/input/monitor_agent), [Fluentd configuration file reload](https://docs.fluentd.org/configuration/config-file) | Yes | Yes | Yes | Yes | Yes | Yes |
| `elastic_agent` | Elastic Agent CLI/status client | [`opamp_consumer.elastic_agent.client.ElasticAgentOpAMPClient`](../consumer/src/opamp_consumer/elastic_agent/client.py) | [Elastic Agent command reference](https://www.elastic.co/docs/reference/fleet/agent-command-reference) | Yes | Yes | Yes | Yes | Yes | Yes |
| `elastic_heartbeat` | Elastic Heartbeat Beat-style client | [`opamp_consumer.elastic_heartbeat.client.ElasticHeartbeatOpAMPClient`](../consumer/src/opamp_consumer/elastic_heartbeat/client.py) | [Heartbeat command reference](https://www.elastic.co/docs/reference/beats/heartbeat/command-line-options), [Heartbeat HTTP endpoint](https://www.elastic.co/docs/reference/beats/heartbeat/http-endpoint) | Yes | Yes | Yes | Yes | Yes | Yes |
| `simulator` | Scripted simulator client | [`opamp_consumer.simulator.client.SimulatorOpAMPClient`](../consumer/src/opamp_consumer/simulator/client.py) | Local scripted responses only; see [Simulator Consumer Configuration](../consumer/docs/plugins/simulator.md) | Yes | Yes | Yes | Yes | Yes | Yes |
| `vector` | Vector supervisor client | [`opamp_consumer.vector.client.VectorOpAMPClient`](../consumer/src/opamp_consumer/vector/client.py) | [Vector Observability API](https://vector.dev/docs/reference/api/) | Yes | Yes | Yes | Yes | Yes | Yes |

## Notes

- `ReportsStatus`, `AcceptsRestartCommand`, and `ReportsHealth` are mandatory
  consumer capabilities in this codebase.
- `AcceptsRemoteConfig`, `ReportsEffectiveConfig`, and `ReportsHeartbeat` are
  implemented by all current built-in clients, but they can still be omitted
  from a specific runtime configuration if `consumer.agent_capabilities` does
  not request them.
- `ReportsEffectiveConfig` means the consumer can report the effective file
  content it is managing. It does not mean the underlying target process exposes
  a native OpAMP effective-configuration API.
- The `simulator` implementation is development/test focused and does not
  launch a real telemetry agent.
