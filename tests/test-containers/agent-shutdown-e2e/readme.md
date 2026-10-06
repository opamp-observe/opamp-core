# Agent Shutdown End-to-End Regression

This container regression proves that the provider UI can shut down a consumer
running as an agent supervisor and that both sides converge on the correct final
state. The scenario runs the packaged supervisor deployment types in sequence:

- Fluent Bit
- Fluentd
- Elastic Agent
- Elastic Heartbeat
- Vector
- Simulator

The first five types run a real managed agent executable. Simulator has no
managed child by design, so its iteration proves registration, UI command
delivery, clean consumer exit, and the absence of an unexpected child process.

## What The Test Does

For each agent type, the runner:

1. Starts a real provider container and a consumer container that supervises the
   real agent executable, except for simulator's intentional no-child model.
2. Waits until the provider reports the expected service instance and the Docker
   process table contains `opamp-consumer` and, where applicable, the managed
   agent.
3. Opens `/ui` in headless Chromium, selects the matching agent row, opens the
   **Commands** tab, selects **Shutdown Agent**, accepts the confirmation prompt,
   and clicks **Send Command**.
4. Confirms the browser received HTTP `201` from
   `/api/clients/<client_id>/commands` and records the exact UI request payload.
5. Waits for the provider record to show `disconnected: true` and a
   `shutdownagent` command with a non-null `sent_at` timestamp.
6. Confirms the consumer exits with code `0`, then uses `docker top` to prove
   that neither the consumer supervisor nor its managed agent process remains.

The consumer wrapper deliberately keeps only its shell container alive after
the consumer exits. This makes absence of the two tested process groups directly
observable instead of inferring it merely from container termination.

The runtime image copies Fluent Bit 5.0.3, Elastic Agent 9.3.3, and Vector 0.58.0
from their official images. Fluentd 1.19.0 and Elastic Heartbeat 9.3.3 are
installed through the deployment bootstrap's normal package paths.

## Server-Side Instruction

The browser uses the normal server UI workflow. The UI submits a custom command
with classifier `custom`, operation `shutdownagent`, capability
`org.mp3monster.opamp_provider.command_shutdown_agent`, and source `ui`. The
provider queues that command and delivers it on the agent's next OpAMP exchange.

Server-side success requires both of these API observations:

- the matching command record has a populated `sent_at` value;
- the client record has `disconnected: true` and a populated `disconnected_at`
  value after the consumer sends its final OpAMP disconnect message.

## Run

From the repository root:

```bash
python tests/test-containers/run_regression_pack.py --only agent-shutdown-e2e
```

To run the scenario script directly:

```bash
bash tests/test-containers/agent-shutdown-e2e/scripts/run_agent_shutdown_e2e.sh
```

A typical warm run takes 4-7 minutes. Allow 15-30 minutes for a first run on a
machine that must download the Playwright and agent images. Network speed,
Docker image cache state, and Fluentd native-extension compilation dominate the
execution time.

For a focused diagnostic run, set `AGENT_SHUTDOWN_AGENT_TYPES` to a
space-separated subset, for example `fluentbit vector`. The regression-pack
entry always uses the default full sequence.

## Evidence

Evidence is written under:

```text
dist/test-reports/agent-shutdown-e2e/
```

Each agent subdirectory includes:

- `ui-shutdown.json` and `ui-shutdown.png` for the browser action;
- `api-client-live.json` and `api-client-shutdown.json` for provider state;
- `processes-before.json` and `processes-after.json` for process state;
- `consumer-exit-code.txt` and `consumer-container.log` for consumer shutdown;
- `summary.json` and `results.md` for pass/fail checks.

The top-level `summary.json` and `results.md` pass only when every selected
agent iteration passes. The default run selects all six built-in consumer types.
