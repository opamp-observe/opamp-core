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

# OpAMP Conversation Broker

The broker depends on the independently published `opamp-shared` runtime
library. Local `uv` development resolves it from `../shared`, and the broker
wheel no longer vendors the shared import package.

A standalone Python conversation broker that adds a conversational Slack surface to the
existing `fluent-opamp` MCP-enabled service.

## What it does

- Supports `/opamp` slash command
- Supports `@OpAMP` app mentions and direct-message chat
- Uses LangGraph for conversation management and planning
- Keeps short-lived conversation state in memory
- Expires idle threads and posts a polite sign-off
- Sends an explicit "going to bed" message on shutdown
- Reads the existing `fluent-opamp/config/opamp.json`
- Discovers MCP tools dynamically from the OpAMP provider
- Uses fixed OpAMP provider MCP JSON-RPC calls (`initialize`, `tools/list`, `tools/call`)
- Uses an LLM planner to interpret requests and choose from discovered tools only
- Uses structured JSON logging via Python's `logging`

## Project layout

- `opamp_broker/` application package
- `scripts/` helper scripts for setup/package
- `docs/` design and transcript documents
  - docs index: `docs/README.md`

## Folder purposes (agent_broker root)

- `docs/`: operational and design documentation, including setup/runbooks and architecture diagrams.
- `opamp_broker/`: main broker Python package and runtime entrypoint.
- `opamp_broker/config/`: broker runtime configuration and static config artifacts (for example broker defaults and Slack manifest).
- `opamp_broker/graph/`: conversation graph assembly, planning logic, and execution flow wiring.
- `opamp_broker/mcp/`: MCP transport client and tool registry integration used to call provider tools.
- `opamp_broker/mcp/proxy.py`: optional local MCP proxy endpoint so desktop clients can call the broker, which then proxies to the provider.
- `opamp_broker/session/`: in-memory session lifecycle management and idle-session sweeper logic.
- `opamp_broker/social_collaboration/`: abstract social-collaboration adapter interface and adapter factory.
- `opamp_broker/social_collaboration/adapters/`: concrete social-collaboration adapter implementations (for example Slack).
- `opamp_broker/slack/`: Slack-specific client and handler implementation used by the Slack social-collaboration adapter.
- `opamp_broker/utils/`: shared utility helpers used by broker modules.
- `scripts/`: helper scripts for Slack setup, packaging, and local development utilities.

## Pre-requisites

- Python 3.11+
- Slack app credentials:
  - bot token
  - signing secret
  - app token (for Socket Mode)
- Access to the existing `fluent-opamp` project checkout
- Network reachability from the broker to the provider's MCP endpoints
- `OPENAI_API_KEY` for LLM-backed planning (when `planner.llm_enabled=true`)

`ai_svc` naming is provider-neutral. Defaults target OpenAI:

- `planner.provider=openai`
- `planner.base_url=https://api.openai.com/v1`
- `planner.api_key_env_var=OPENAI_API_KEY`
- `planner.temperature=0.0`
- `planner.max_completion_tokens=1024`
- `planner.verify_max_completion_tokens_attempts=[64, 512]`
- `planner.prompts_config_path=planner_prompts.json`

## Recommended Slack scopes

- `app_mentions:read`
- `channels:history`
- `chat:write`
- `commands`
- `groups:history`
- `im:history`
- `im:write`
- `mpim:history`

## Quick start

1. Copy `opamp_broker/config/broker.ui_responses.json` to a runtime file, or rely on defaults.
2. Point `paths.opamp_config_path` at the existing `fluent-opamp/config/opamp.json`.
3. Configure Slack and env values:
   - Linux/macOS: `./scripts/configure_slack.sh`
   - Windows PowerShell: `.\scripts\configure_slack.ps1`
   - Manual guide: `docs/slack_configuration.md`
4. Export your LLM API key (recommended for tool-constrained LLM planning):
   - Linux/macOS: `export OPENAI_API_KEY=...`
   - Windows PowerShell: `$env:OPENAI_API_KEY = \"...\"`
   - The broker reads the env var named by `planner.api_key_env_var` (default `OPENAI_API_KEY`).
   - If you switch `planner.api_key_env_var` to a different key name, set that exact variable in `.env`/environment.
   - If you use a non-default provider, also set `planner.provider` in broker config.
5. Install dependencies:
   - `python -m venv .venv`
   - activate the venv
   - `pip install -r requirements.txt`
6. Run:
   - Preferred guided lifecycle via `opamp-cli`:
     - Start broker: `opamp-cli start broker`
     - Stop broker: `opamp-cli stop broker`
     - Show managed process state: `opamp-cli status`
   - If `opamp-cli` is not installed yet:
     - `PYTHONPATH=cli/src python3 -m opamp_cli start broker`
   - Show broker CLI options + version details: `python -m opamp_broker.broker_app -h`
   - Optional explicit adapter selection: `python -m opamp_broker.broker_app --social-collaboration slack`
   - Show broker version metadata: `python -m opamp_broker.broker_app --version`
   - Optional startup verification only: `python -m opamp_broker.broker_app --verify-startup social`
   - Optional AI service verification only: `python -m opamp_broker.broker_app --verify-startup ai_svc`
   - Optional full startup verification: `python -m opamp_broker.broker_app --verify-startup all`
7. Operational docs:
   - startup/shutdown + logging: `docs/broker_startup_and_shutdown.md`
   - AI provider extension guide: `docs/ai_provider_connections.md`
   - code structure diagrams: `docs/broker_code_structure.md`
   - documentation index: `docs/README.md`

## Notes

- This broker is intentionally stateless across restarts except for Slack-visible thread history.
- In-memory thread state is cleared after the configured idle timeout.
- On shutdown the broker tells active threads it is "going to bed" and clears working context.
- MCP connectivity is intentionally simplified to the provider `/mcp` endpoint and supports configurable connection strategy (`auto`/`json`/`sse`), protocol version attempts, timeout, and startup discovery retry/backoff via `mcp.*` settings.
- When `mcp_server.enabled` is `true`, the broker also exposes its own local `/mcp` proxy endpoint for desktop MCP clients and forwards `initialize`, `tools/list`, and `tools/call` upstream to the provider.
- Recommended deployment posture: send untrusted or agentic MCP traffic to the broker proxy first, not directly to the provider. This keeps richer provider APIs on an internal-only surface and lets the broker act as the narrower, easier-to-restrict boundary.
- Broker OTLP export uses the shared top-level `otlp-endpoints` block. If that block is not present in the broker config file, the broker inherits it from the referenced `paths.opamp_config_path` file.
- Ensure broker `mcp.connection_mode` aligns with provider response mode (SSE/streaming vs JSON). `auto` is recommended unless you explicitly need to force one mode.
- broker deployment packaging checks whether `opamp-cli` is available and warns when it is not detected
- the CLI is deployed separately from the broker package/zip and is now the preferred way to start/stop the broker locally
- Agent filters can be passed directly to the discovered listing tool, for example:
  - `/opamp tool_otel_agents service_instance_id=checkout host_name=prod-node invert_filter=true`
  - `/opamp show agents host_ip=10.0.0.5 client_version=1.2`
