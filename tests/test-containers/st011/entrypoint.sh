#!/usr/bin/env bash
# Copyright 2026 mp3monster.org
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Run provider MCP, client configurator, and broker integration contracts with local doubles.
set -euo pipefail

results_dir="${RESULTS_DIR:-/host-output}"
staged_root="$(/runner/prepare_source.sh)"
mkdir -p "${results_dir}"

python -m pip install --no-cache-dir \
  "${staged_root}/provider[dev]" \
  "${staged_root}/mcp[dev,yaml]" \
  "${staged_root}/agent_broker[dev]"

set +e
{
  cd /tmp || exit 1
  python -m pytest -q \
    -o addopts= \
    "${staged_root}/provider/tests/test_mcptool_quart_bridge.py" \
    "${staged_root}/agent_broker/tests/test_agent_broker_mcp_proxy.py" \
    "${staged_root}/tests/test_mcp_configure_clients.py" \
    "${staged_root}/tests/test_mcp_build_config_tool.py" \
    "${staged_root}/tests/test_agent_broker_mcp_client.py" \
    "${staged_root}/tests/test_agent_broker_broker_app.py" \
    "${staged_root}/tests/test_agent_broker_planner_and_nodes.py" \
    "${staged_root}/tests/test_agent_broker_session_manager.py" \
    "${staged_root}/tests/test_agent_broker_slack_handlers.py" \
    "${staged_root}/tests/test_agent_broker_social_collaboration_factory.py" \
    --junitxml="${results_dir}/junit.xml"
} 2>&1 | tee "${results_dir}/verify.log"
scenario_status=${PIPESTATUS[0]}
set -e

scenario_result="passed"
if [[ "${scenario_status}" -ne 0 ]]; then
  scenario_result="failed"
fi
printf '{\n  "scenario": "ST-011",\n  "passed": %s,\n  "external_slack_calls": false,\n  "external_llm_calls": false\n}\n' \
  "$([[ "${scenario_status}" -eq 0 ]] && printf true || printf false)" \
  > "${results_dir}/summary.json"
printf '# ST-011 Container Results\n\n- Result: %s\n- External Slack calls: no\n- External LLM calls: no\n- Evidence: `verify.log`, `junit.xml`\n' \
  "${scenario_result}" > "${results_dir}/results.md"

exit "${scenario_status}"
