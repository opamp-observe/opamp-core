# Roadmap

This doesn't commit to any timelines and doesn't provide any guarantees, but it does identify ideas that could be pursued and developed



## Agent-based features



### Extend Editor

Extend the editor to support additional agent types, covering:

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
