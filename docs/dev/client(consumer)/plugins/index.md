# Consumer Plugin Developer Guide

This guide explains how to add a new consumer plugin to the OpAMP consumer.
It is written for a developer who has a basic idea of the project, but who has
not lived inside the consumer code yet.

The short version is this: the installed `opamp-consumer` command reads the
active consumer configuration, looks at `consumer.service_type`, resolves that
value through the plugin registry, and then runs the selected plugin entry
point. The plugin itself normally builds a concrete `AbstractOpAMPClient`
subclass and then uses the shared bootstrap/runtime machinery to speak OpAMP,
manage process state, send heartbeats, handle restart commands, and apply
remote configuration when supported.

## Start Here

Read these pages in order the first time:

1. [Architecture And Loading](architecture-and-loading.md)
2. [Implementation Contract](implementation-contract.md)
3. [Configuration Hooks](configuration-hooks.md)
4. [Testing A Plugin](testing-a-plugin.md)
5. [Packaging And Deployment](packaging-and-deployment.md)
6. [AI Prompt Template](ai-prompt-template.md)

After that, you can usually edit only the page that matches the thing you are
changing. For example, a new plugin-specific JSON block normally only needs
changes in [Configuration Hooks](configuration-hooks.md) and the corresponding
plugin configuration page.

## Existing Docs Worth Keeping Open

These existing docs provide the surrounding context:

- [Consumer configuration reference](../../../../consumer/README.md)
- [Consumer plugin configuration pages](../../../../consumer/docs/plugins/fluent-bit.md)
- [Consumer client architecture diagram](../consumer_client_diagram.md)
- [Consumer mixins explained](../consumer_mixins.md)
- [Consumer restart and hot deploy](../consumer_restart_and_hot_deploy.md)
- [Consumer update controllers](../consumer_update_controllers.md)
- [Consumer custom handlers](../consumer_custom_handlers.md)
- [Deployment test container](../../../../tests/test-containers/opamp-consumer-deployment/README.md)

The architecture diagram is especially useful because it shows the router,
plugin loader, concrete clients, abstract base client, and process lifecycle
strategies in one place.

## What Counts As A Plugin?

In this consumer, a plugin is not a dynamically loaded class with a large custom
framework around it. A plugin is simply a Python callable, normally a `main()`
function, that can be resolved from a `service_type`.

There are two ways the consumer can discover that callable:

- Python package entry point in the `opamp_consumer.plugins` group.
- Runtime config entry under `consumer.plugins`.

Most production plugins should use a package entry point. Config entries are
still valuable for local experiments, tests, overrides, and disabling an
installed plugin without uninstalling its package.

## Built-In Examples

Use the built-ins as reference implementations:

- Fluent Bit: `consumer/src/opamp_consumer/fluentbit/`
- Fluentd: `consumer/src/opamp_consumer/fluentd/`
- Elastic Agent: `consumer/src/opamp_consumer/elastic_agent/`
- Elastic Heartbeat: `consumer/src/opamp_consumer/elastic_heartbeat/`
- Simulator: `consumer/src/opamp_consumer/simulator/`

Their operator-facing configuration pages live under
`consumer/docs/plugins/`. If you add a new plugin, add a page there too, and
link it from `consumer/README.md`.

## New Plugin Checklist

For a new consumer plugin, make these pieces line up:

1. Choose a stable `service_type`, such as `my_agent`.
2. Implement a zero-argument plugin entry point, normally `client.py:main`.
3. Add any plugin-specific config processing under `consumer.<service_type>`.
4. Register the plugin through one supported registry source:
   - built-in mapping in `consumer/src/opamp_consumer/builtin_consumer_plugins.json`
   - package entry point in `opamp_consumer.plugins`
   - runtime `consumer.plugins` config overlay
5. Add operator docs under `consumer/docs/plugins/<service-type>.md`.
6. Link that page from `consumer/README.md`.
7. Add focused unit tests for config parsing, lifecycle, metadata, and health.
8. Add router/entry-point coverage when the plugin is externally registered.
9. If the CLI should expose it in guided start/demo flows, add the CLI wiring
   described in [Architecture And Loading](architecture-and-loading.md#cli-and-demo-integration).

The important mental model is that the consumer plugin registry answers
"which Python callable handles this `service_type`?" The CLI answers "which
process should I start, with which config file?" Keep those responsibilities
separate.

