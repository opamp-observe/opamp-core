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

# On-demand local CI runner

The local Docker runner is registered only to the private
[`opamp-observe/opamp-private-ci`](https://github.com/opamp-observe/opamp-private-ci)
repository. Its allowlist currently contains only `opamp-observe/opamp-core`.
Ordinary push and pull request workflows in this public repository continue to
use GitHub-hosted runners. A reviewed commit can be built manually on the local
runner without granting public workflows access to the machine.

1. Review the exact commit, then obtain its full 40-character SHA. The commit
   must already be available in `opamp-observe/opamp-core` on GitHub.
2. Start the runner from the separate `D:\dev\opamp-runner` bundle:
   `D:\dev\opamp-runner\scripts\runner.cmd start`.
3. Dispatch from this repository:
   `.\scripts\run_local_ci.cmd -ReviewedSha <full-commit-sha> -TestSuite all`.
4. Inspect the run in the private CI repository's Actions tab. The hosted
   validation job checks the allowlist and SHA; the local job verifies checkout
   and runs the configured unit, end-to-end, security, and dependency tests.
   Reports are uploaded even when a test fails. To retrieve them, run
   `.\scripts\get_local_ci_artifacts.cmd -RunId <run-id>`; the default output
   directory is `dist/local-ci-artifacts/<run-id>`.
5. Once the runner is idle, stop it:
   `D:\dev\opamp-runner\scripts\runner.cmd stop`.

Use `-TestSuite regression-pack` to run the 16 container scenarios alone,
optionally with `-RegressionTestId <scenario-id>`. Use `-TestSuite syntax` for
a quick source check. The local runner bundle's
`docs/runner_capabilities.md` describes the available runner types, reports,
and limits. It also documents enrollment of further public source
repositories and the limits of runner fallback. Keep CI workflow edits in the
private repository restricted to trusted maintainers. Never dispatch a commit
whose code or dependencies have not been reviewed.

GitHub's `runs-on` label list matches one runner with every listed label;
it is not an ordered fallback list. An offline local runner leaves the private
job queued, while this repository's normal GitHub-hosted workflows continue
independently. A future hosted fallback would need an explicit target choice
or a trusted controller that cancels and redispatches a queued job. See
[GitHub runner selection](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job)
and [self-hosted runner routing](https://docs.github.com/en/actions/reference/runners/self-hosted-runners).
