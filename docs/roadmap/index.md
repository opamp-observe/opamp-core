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

# Roadmap

This doesn't commit to any timelines and doesn't provide any guarantees, but it does identify ideas that could be pursued and developed



## Agent-based features



### Extend Editor

Extend the editor to support additional agent types, covering:

- [Multi-agent configuration editor and Vector support](vector_multi_agent_configuration_editor.md) - implementation specification for refactoring `config-service`, adapting the Fluent Bit approach, and adding schema-driven Vector editing to the OpAMP server.
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)
- [Vector](https://vector.dev/)
- [Elastic Agent](https://www.elastic.co/elastic-agent)
- [Elastic Beats](https://www.elastic.co/beats/) ([Heartbeat](https://www.elastic.co/beats/heartbeat), etc)



### Configuration Intelligence

Incorporate a strategy for tracking the configuration versions across multiple agents beyond just [Fluent Bit](https://fluentbit.io/). Plus factor in the new 5.1 Fluent Bit configuration option. The mechanism would need to be at least partially configurable.

Would need to include:

- Best practice analysis for all the different agent types
- [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/)



### Self Monitoring

Implement the ability to accommodate self-monitoring - the Spec identifies a passing target for the [OTel](https://opentelemetry.io/) backend. Depending upon the client, this maybe a templated approach, and the provided backend is injected into the template.



## Supervisor / Observer config helper

Simplify the configuration process for the Supervisor / Observer - this could be via several possible paths:

- Server-side UI editor plugin that generates the config.
- Extend the CLI for a CLI-based configuration process that generates the file in the correct location - makes the config tuneable to a per-deployment model.



## Additional agent types

Consider providing support for additional agent types, including:

- [OpenObserve](https://openobserve.ai/)
- [Datadog](https://www.datadoghq.com/)
- Remaining [Elastic Beats](https://www.elastic.co/beats/)



## Reference configurations

Reference configurations to illustrate (and use the CLI to launch)

- Self-certification use of TLS (including mTLS)
- Configuration of authentication using [Keycloak](https://www.keycloak.org/) - with docs to point the way for other authentication 



# Automation and Deployment

## Incorporate a deployment function in the server that will allow the user to:
- SSH to a client and deploy an agent configuration,
- deploy the observer/supervisor,
- trigger the installation or update of the observability too e.g. Fluent Bit
- Deploy the initial container
- Allow the user to embed the feature into the server startup

We should conmsider whether the deployment of the observability tool and its code is provided as a custom command, minimizing what can be done via the SSH tunnel, but also raises the question of permissions for the client side functionality.

## Code signing

Look into using [sigstore](https://openssf.org/blog/2023/11/21/sigstore-simplifying-code-signing-for-open-source-ecosystems/) to sign the deployable artefacts.

### PyPI incorporation

Add project to [PyPI](https://pypi.org/). Need to consider whether it's a single PyPI project or several with different parts e.g. Consumer(s), Server, plugs

### Uninstall clean

The wheel deinstallation process should also clean up log files and other artefacts that get generated

### Automated (multi-cloud) regression setup



# Enhanced Tooling

Incorporate additions to help validate configuration of the agents such as:

- [Log Simulator](https://github.com/mp3monster/LogGenerator)
- New Metrics and traces simulation
