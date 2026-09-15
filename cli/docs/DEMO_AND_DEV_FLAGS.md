# CLI Demo Mode And Dev Flags

This note documents two behavior switches used by the OpAMP CLI and nearby consumer workflows:

- `OPAMP_DEMO`
- `APP_ENABLE_DEV_FEATURES`

This file is intentionally kept as a standalone CLI note rather than being linked from the main project docs.

## `OPAMP_DEMO`

`OPAMP_DEMO` is the flag that enables demo-specific guided options in `opamp-cli`.

When it is set to a truthy value such as `1`, `true`, `yes`, or `on`, the CLI adds profile-based demo actions to guided `start` and `stop`.

The current profile lookup file is:

- `cli/config/demo_consumer_profiles.json`

Each profile in that file provides:

- a logical profile name
- an optional `scenario_description`
- a consumer simulator instances file
- a Fluent Bit OpAMP config path
- a Fluentd OpAMP config path
- an Elastic Agent OpAMP config path
- an Elastic Heartbeat OpAMP config path
- a Vector OpAMP config path
- optional profile-level agent config path overrides for legacy configs
- optional container start commands

For new demo setup, prefer putting agent paths in `consumer.agent_config_path`
inside each OpAMP JSON config. The CLI only needs profile-level
`agent_config_path` when the consumer config does not already provide one.

When `OPAMP_DEMO` is enabled:

- `opamp-cli start` includes `Demo consumers (<profile-name>)` entries
- `opamp-cli stop` includes matching demo stop entries
- `opamp-cli demo` acts as shorthand for `opamp-cli start demo consumers`
- `start demo consumers` acts as a category selector and offers the named profiles from the lookup file
- the guided selector accepts `d<number>` so the scenario description can be viewed before choosing a profile
- demo-launched process records are written into `cli/runtime/managed_processes.json`
- those records are profile-scoped, so one demo profile can be stopped independently of another
- profiles can start configured containers before consumers, so dependency services such as Logstash can come up first

The `Demo setup (Elastic Agent self-monitoring to Logstash)` profile uses:

- `tests/logstash/opamp-consumer-elastic-agent-logstash-plugin.json`
- `tests/logstash/elastic-agent.yml`
- the `logstash-local` container entry from `cli/config/demo_consumer_profiles.json`

The launch sequence is:

1. Start the configured Logstash container on host port `5044`.
2. Start `opamp_consumer.client` with the Elastic Agent consumer config.
3. The consumer loads the `elastic_agent` plugin and launches Elastic Agent with the self-monitoring YAML.
4. Elastic Agent sends its monitoring logs and metrics to local Logstash.

The `Demo setup (Elastic Heartbeat supervisor to Logstash)` profile uses:

- `tests/logstash/opamp-consumer-elastic-heartbeat-logstash-plugin.json`
- `tests/logstash/heartbeat.yml`
- the `logstash-heartbeat-local` container entry from `cli/config/demo_consumer_profiles.json`

The launch sequence is:

1. Start the configured Logstash container on host port `5044`.
2. Start `opamp_consumer.client` with the Elastic Heartbeat consumer config.
3. The consumer loads the `elastic_heartbeat` plugin and launches Heartbeat as a supervisor-managed process.
4. Heartbeat monitors `localhost` and `blog.mp3monster.org` every 5 seconds, sends events to Logstash, and Logstash writes `tests/logstash/out/heartbeat-events.jsonl`.

The `Demo setup (Full multi-agent remote config)` profile uses `docs/full-demo`:

- Fluent Bit and Fluentd consumers run in supervisor mode.
- Vector, Elastic Agent, and Elastic Heartbeat consumers run in observer mode.
- The profile starts the `logstash-full-demo` container before launching consumers.
- The profile points only at consumer OpAMP JSON files; each JSON file supplies
  its own `consumer.agent_config_path`.
- The matching provider config exposes `docs/full-demo/active`, `docs/full-demo/replacements`, and `docs/full-demo/consumers` through the server catalog so replacement configs can be deployed from the UI.

## `APP_ENABLE_DEV_FEATURES`

`APP_ENABLE_DEV_FEATURES` is not a CLI-only flag. It is a broader runtime flag used by development-oriented workflows.

In the CLI-related area, it currently matters most for simulator-oriented startup paths.

Current use:

- the simulator launcher wrappers set it before starting consumer-sim
- the CLI demo-consumer start flow sets it for the simulator start step
- interactive CLI startup reports it when it is already enabled in the current environment

Relevant CLI behavior:

- demo profile starts set `APP_ENABLE_DEV_FEATURES=true` when invoking `consumer-sim`
- startup messaging in interactive CLI only mentions this flag when it is actually detected as enabled
- when the Fluent Bit dev-generator scripts are present, `opamp-cli dev-flb-config` is exposed as a guided developer workflow
- `opamp-cli dev-pid-lookup` is exposed as a dev-only workflow for regex-based running-process PID lookup
- `opamp-cli dev-version-bump` is exposed as a dev-only workflow for updating configured semantic version identifiers
- `opamp-cli dev-containers` is exposed when a supported container runtime and configured container starts are available
- the Fluent Bit workflow discovers tool metadata from:
  - `config-service/dev-tools/generate_fluentbit_assets.py`
  - `config-service/dev-tools/generate_fluentbit_markdown.py`
- the CLI uses the metadata exported by those scripts to keep prompts and supported flags aligned with the tools themselves

`dev-version-bump` uses `cli/config/version_targets.json` by default. That file
defines independently bumped components, each with its own current-version
source and version-bearing files. When no version argument is supplied, the
command increments each component's current semantic version by one minor
version and resets patch to zero. When a version argument is supplied, it must
use `MAJOR.MINOR.PATCH` format and be greater than every component version it
would update.

One important non-CLI interaction is the security checks flow:

- `scripts/security_checks.py` explicitly removes `APP_ENABLE_DEV_FEATURES` from the environment before running checks

That keeps validation runs aligned with non-dev behavior.

## CLI Replacements

The CLI now covers the main lifecycle operations that older wrapper scripts previously handled. Those workflows can be performed with:

- `opamp-cli start simulator`
- `opamp-cli stop simulator`
- `opamp-cli start fluentbit client`
- `opamp-cli stop fluentbit client`
- `opamp-cli start vector client`
- `opamp-cli stop vector client`
- `opamp-cli start fluentd client`
- `opamp-cli stop fluentd client`
- `opamp-cli dev-containers logstash`

## Scripts That Should Not Be Treated As Direct CLI Replacements

The following scripts still have distinct behavior and should not be grouped into the removal list just because the CLI now covers much of the normal consumer lifecycle:

- `scripts/start_fluentd.sh`
- `scripts/start_fluentd.cmd`
- `scripts/terminate_fluent_bit.sh`
- `scripts/terminate_fluent_bit.cmd`

Why they are different:

- `start_fluentd.*` starts Fluentd directly, not the OpAMP consumer wrapper flow
- `terminate_fluent_bit.*` is an emergency direct process terminator for `fluent-bit`

Those may still be useful as low-level operational helpers even if the CLI becomes the primary entrypoint.
