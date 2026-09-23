# OpAMP Feature Completion, ToDos and Future Features
The following represents a brain dump of things that we want to/need to do. The ToDos are the primary focus, but may not be delivered immediately as we work toward a minimal implementation.

## OpAMP Specification

The following is a summary of the features  based on the message exchange and the progress made, gaps and things that aren't in our plans.

### Client to Server

Here's a markdown table with one row per `AgentToServer` message field:

| Field                         | Spec Status | Implementation Status | Spec Description                                             | Implementation Notes                                         |
| ----------------------------- | ----------- | --------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| `instance_uid`                | Stable      | Done                  | Globally unique identifier of the running Agent instance. Must be 16 bytes, generated using UUID v7. Must be set on every message. |                                                              |
| `sequence_num`                | Stable      | Done                  | Monotonically incrementing counter (by 1 per message) so the Server can detect missed messages. |                                                              |
| `agent_description`           | Stable      | Done                  | Describes the Agent: its type, version, OS, and where it runs. Should be omitted if unchanged since last message. |                                                              |
| `capabilities`                | Stable      | Done                  | Bitmask of `AgentCapabilities` flags declaring what the Agent supports. Must always be set. |  |
| `health`                      | Beta        | Done                   | Current health of the Agent and its sub-components. May be omitted if unchanged since last message. | Basic Fluent API interrogation is used |
| `effective_config`            | Stable      | ToDo                  | The Agent's current active configuration (may differ from the remote config). Should be omitted if unchanged since last message. | We use the metrics to get health of sources. |
| `remote_config_status`        | Stable      | Inprogress    | Status of the last remote configuration received from the Server. Should be omitted if unchanged since last message. |                                                              |
| `package_statuses`            | Beta        | Not Planned           | List of Agent packages and their installation/update statuses. Should be omitted if unchanged since last message. | Makes more sense with Fluentd as greater package portfolio   |
| `agent_disconnect`            | Stable      | Done             | Must be set in the last `AgentToServer` message before the Agent disconnects. |                                                              |
| `**flags**`                   | Stable      | Done             | Bitmask of `AgentToServerFlags`. Currently includes `RequestInstanceUid` to ask the Server to assign a new instance UID. |                                                              |
| `connection_settings_request` | Development | Long Term             | A request from the Agent to initiate creation of new connection settings (agent-initiated CSR flow). |                                                              |
| `custom_capabilities`         | Development | Done                  | Declares custom/extension capabilities supported by this Agent. | This is support the ChatOps concept. Documentation provided on how to add your own. |
| `custom_message`              | Development | Done                  | An arbitrary custom message sent from the Agent to the Server, scoped to a declared custom capability. | This is support the ChatOps concept                          |
| `available_components`        | Development | Not Planned           | Lists the components available in the Agent. Should only be set when `ReportsAvailableComponents` capability is declared. |                                                              |
| `connection_settings_status`  | Development | Not Planned           | Reports the status of connection settings previously offered by the Server. Should be omitted if unchanged since last message. | This would be invasive to Fluent Bit                         |



### Server to Client

Here's the markdown table for `ServerToAgent` message fields:

| Field                  | Spec Status | Implementation Status | Spec Description                                             | Implementation Notes                |
| ---------------------- | ----------- | --------------------- | ------------------------------------------------------------ | ----------------------------------- |
| `instance_uid`         | Stable      | Done                  | The Agent instance identifier. Must match the `instance_uid` previously received in the `AgentToServer` message. Used to route messages when multiple Agents share a single connection. |                                     |
| `error_response`       | Stable      | Done                  | Set when the Server encountered an error processing an `AgentToServer` message. When set, all other fields (except `instance_uid`) must be unset. |                                     |
| `remote_config`        | Stable      | Inprogress    | Set when the Server has a remote configuration offer for the Agent. Workinbg for some types of agent |                                     |
| `connection_settings`  | Beta        | Long Term             | Set when the Server wants the Agent to change one or more client connection settings (destination, headers, certificate, etc.). |                                     |
| `packages_available`   | Beta        | Not Planned           | Set when the Server has packages to offer to the Agent for download/installation. |                                     |
| `**flags**`            | Stable      | Partial                  | Bitmask of `ServerToAgentFlags`. Includes `ReportFullState` (asks Agent to resend full status, e.g. after Server restart) and `ReportAvailableComponents` (asks Agent to send full component details rather than just a hash). |                                     |
| `capabilities`         | Stable      | Done                  | Bitmask of `ServerCapabilities` flags. Must be set in the first `ServerToAgent` message; may be omitted (set to 0) in subsequent messages. | Advertisement is config-driven; see `provider.allow-remote-config`, `provider.allow-effective-config`, `provider.allow-connection-settings`, and `provider.allow-connection-settings-request`. |
| `agent_identification` | Stable      | Done            | Used to override the Agent's `instance_uid`. When `new_instance_uid` is set, the Agent must adopt it for all further communication. |                                     |
| `**command**`          | Beta        | Done                  | Set when the Server wants the Agent to perform a command (currently only `Restart`). When set, all fields other than `instance_uid` and `capabilities` are ignored. |                                     |
| `custom_capabilities`  | Development | Done                 | Declares custom/extension capabilities supported by the Server. | This is support the ChatOps concept |
| `custom_message`       | Development | Done                | An arbitrary custom message sent from the Server to the Agent, scoped to a declared custom capability. | This is support the ChatOps concept |

Connection settings policy note:

- We intentionally do not support `ReportsOwnTraces`, `ReportsOwnMetrics`, or `ReportsOwnLogs` as direct connection-settings management features in this project.
- See the configuration policy in [consumer/README.md](../consumer/README.md#connection-settings).

## Additional Tooling
In addition to the core server we have several supporting tools. These aren't specifically identified as part of the OpAMP specification, but are a natural extension of the server features we have built out. But can be used independently.

## Future Features
* Not really a feature, but somethings we want to drive across the board, extend testing to provide more than just unit tests, such as:
  * more E2E test scenarios
  * Increased focus on the  unhappy path tests
  * Establish CI/CD using cloud hyperscalers 
  * Quick reference documentation as static pages
  * Publish the coverage stats
  
* Fully incorporate OTel metrics and traces internally
* Extended testing of Wheel and PIP deployments into fresh environments (including publishing PIPs through PyPI)

### Server (aka Provider) & Client (aka Consumer)
* GitHub-driven test rig, including validating against 3rd party server or client implementation for functional behaviour tests.
* Docs on [readthedocs](https://about.readthedocs.com/pricing/#/community)
* Complete implementation of the Remote Config mechanism
* Handshake for bearer token allocation and [mTLS](https://goteleport.com/learn/what-is-mtls/)
* Support Elastic stack and just individual beats

### Client Side

In the code base, this is often referred to as the consumer.

* Allow consumer attributes to come from the commenting block in Fluent Bit and Fluentd configuration (exploit Configuration Service 'annotations') - partially implemented
* Share namespace when running in a K8s deployment
* Configuration refinements to manage beats / Elastic Stack OSS
* Enhance agent observability so that it can be incorporated into the observed agent monitoring for the ***observer*** deployment (.i.e process discovery rather than process launch) using the `consumer.processDetectionRegex` 
* Root page (e.g. localhost:8080) provides a redirect button (or buttons) for each of the services available. If no other components deployed then directs to correct URL



### Server Side

The main OpAMP Server, which provides the UI and controls for the deployed client (consumers). Plus, controllable additions like the catalogue manager and config editor.

##### Main Server

* Extend the persistence mechanism beyond the initial file mechanism (investigate Quart features for Postgres and SQLite)
* Load configurations and distribute to relevant nodes
* Certificate management - this is messy to set up and test properly, so provide scripts to self-cert and a basic Identity solution
* Enhance the build and deploy to create several versions of the service that can be installed, including:
* Debug mode 
  * Intended to help build customisations, and troubleshoot deployment scenarios
  * Will deploy all the components (Client, Server, Configuration, Utility scripts, documentation)
  * enables all the debug features, 
  * Will trigger the installation of development tool dependencies
* Full server:
  * Will include the Config service integrated into the server
  * Will include the client
  * Will include the agent_broker, allowing the Slack integration to be used.
  * WONT include all development dependencies
* Reference documentation/implementation for custom messages

##### Config Editor (Config Service)

The config editor and its tools can be used to edit Fluent Bit and Fluentd configuration files.

- Improve the validation feedback
- Look at how we could provide a more visual representation of the configuration
- Consider incorporating a classic to YAML capability - integrate the utility previously built?
- The root page (e.g., localhost:8080) provides a redirect button (or buttons) for each available service. If no other components are deployed, then it directs to the correct URL.
- Look at incorporating the `Fluent Bit Classic to YAML converter` (from [here](https://github.com/mp3monster/fluent-bit-classic-to-yaml-converter)) when deployed.

##### Catalog

The catalog component will look into all the defined locations and retrieve the relevant metadata, so the deployed version can be understood

- Use the catalog to select the configurations for the remote deployment task on the main server 
- Interact with Git as a catalog source
- The root page (e.g., localhost:8080) provides a redirect button (or buttons) for each available service. If no other components are deployed, then it directs to the correct URL



### Broker

The broker provides the interoperability layer with social channels and Agents when the LLM usage is allowed

- Extend social connectivity - considering the following:
  - MS Teams
  - Discord
  - [LibreChat](https://www.librechat.ai/)

### Configuration Editor (Configuration Service)
* Extended testing to ensure all plugins are correctly configured
* Extend the validation techniques (so we can provide a proper URL validation)
* Evaluate extensibility so we could provide structure to support (in priority order):

  * OTel standard collector
  * Elastic stack/beats
* Validation additional rules:

  * If one attribute is set, then so should others, e.g. `oath.validate` is true, then `oauth2.issuer` needs to be set
  * Validator for IPs so we can confirm IPv4 is correct - needs consideration - confirm whether Fluent Bit will handle hostname/DNS as an alternate to IP?
  * duration validation as some fields allow you to express the value as n seconds, n minutes e.g. input fluent-bit-metrics
* Take into account custom plugins
* Extend the number of versions that we have configuration definitions

### CLI

- Explore the overhead and issues that using the CLI as a universal launcher would create (it would simplify the means to integrate the launching of the Client, Server and Broker with the OS)

- Enhance the discovery mechanism so that additional CLI tools can be provided when different components are deployed

- Parameterised Docker - where the container as all the components, but the Docker container RUN is driven through the CLI

- Enhance the demo feature, particularly to enable us to create a large number of simulator instances.

  


### Others

- Dev tool util:
  - validates the configuration files for the configurations
  - All `opamp-dev-cli` to be used from `opamp-cli`
