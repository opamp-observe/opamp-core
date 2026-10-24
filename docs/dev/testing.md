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

# Testing and Result Review

This guide describes the repository test layers, the commands developers should run, and the
files to inspect after a run. The developer CLI is the preferred entry point because it applies
the same component discovery and result layout across the repository.

## Test Layers

| Layer | Purpose | Primary runner |
|---|---|---|
| Python unit and integration | Component logic, endpoint behavior, protocol handling, and regressions | pytest |
| Browser unit | JavaScript behavior that does not require a running service | Vitest |
| Browser end to end | Python-served HTML/CSS/JavaScript and user workflows | Playwright |
| Repository end to end | Cross-process socket and service behavior | pytest |
| Security gate | Tests plus SAST, secret detection, and dependency auditing | developer CLI |

Generic web scanners cannot fully exercise OpAMP messages, supervised command execution, MCP
tool boundaries, or certificate identity rules. Those trust boundaries should continue to receive
targeted pytest and integration coverage alongside scanner-based checks.

## Setup

Create the shared development environment from the repository root:

```bash
python cli/main.py setup-venv
```

Install Playwright browsers before the first browser run in a checkout:

```bash
cd config-service
npx playwright install chromium
```

On Linux, `npx playwright install-deps chromium` may also be required.

## Watchable Playwright Runs

Playwright remains headless by default. A headed or debug run automatically enables watch mode,
which uses one worker, waits 250 milliseconds between browser operations, and records a trace,
video, and screenshot for every test. From `catalog-service`, `config-service`, or
`svr-credentials-mgr`, run:

```bash
npm run ui:test:watch
```

The provider does not have its own Node package manifest, so run its equivalent directly:

```bash
cd provider
npx playwright test --headed
```

Set `PLAYWRIGHT_SLOW_MO_MS` to change the delay. `PLAYWRIGHT_WATCH=1` provides the same behavior
without adding `--headed`, which is useful for custom commands. For example, in PowerShell:

```powershell
$env:PLAYWRIGHT_WATCH = "1"
$env:PLAYWRIGHT_SLOW_MO_MS = "500"
npm run ui:test
Remove-Item Env:\PLAYWRIGHT_WATCH, Env:\PLAYWRIGHT_SLOW_MO_MS
```

In Bash:

```bash
PLAYWRIGHT_WATCH=1 PLAYWRIGHT_SLOW_MO_MS=500 npm run ui:test
```

Watch-mode evidence is written below the component's `test-results/artifacts/` directory. The
HTML and JUnit reports use the same locations as a normal headless run. Do not enable watch mode
in unattended CI because it opens a visible browser and retains substantially more evidence.

## Running Tests

Run one component while developing a focused change:

```bash
opamp-dev-cli build test named provider
```

Run every discovered component before broad or cross-component changes:

```bash
opamp-dev-cli build test all
```

Run the repository end-to-end suite:

```bash
opamp-dev-cli build test e2e
```

Each packaged Python component also supports its module-local quality baseline from that
component directory:

```bash
python -m ruff check src tests
python -m pylint src
python -m pytest -q -s
```

Adjust the source paths to match the component's `pyproject.toml`. Use direct pytest selection
while iterating, but finish with the component command so its complete configured coverage is run.

## Running the Security Gate

For a focused component change:

```bash
opamp-dev-cli build secure named config-service
```

For broad, shared-contract, refactor, build, or release changes:

```bash
opamp-dev-cli build secure all
```

The compatibility entry point runs the same full-repository gate:

```bash
python scripts/security_checks.py
```

The gate compacts provider UI assets, runs pytest, checks Ruff security rules, scans tracked files
with `detect-secrets`, audits Python requirements with `pip-audit`, and produces Semgrep and Bandit
evaluation reports. Semgrep uses the reviewed repository rules in `security/semgrep.yml`; it does
not download an automatically changing ruleset.

Pytest, Ruff, `detect-secrets`, and `pip-audit` are blocking checks. Semgrep findings and Bandit
findings are initially report-only so maintainers can compare their unique signal with Ruff and
agree a baseline. Scanner execution or configuration failures still fail the command. Promote a
Semgrep or Bandit rule to blocking only after existing findings have been triaged and the policy is
documented.

Independent gate steps continue after a failure so later tools can still write their reports. The
command returns a failure after all steps finish and lists each failed step; a red pytest result,
for example, does not hide the static-analysis or dependency-audit evidence.

Dynamic application security testing is a separate runtime concern. ZAP, Nuclei, or API fuzzing
must target disposable test deployments, especially for active scans. They are not part of the
local static security gate yet; planned security work is tracked in the
[security roadmap](../roadmap/index.md#enhance-the-security-aspect-of-the-process).

## Reviewing Results

Start with the terminal result and command exit code, then use the retained files for detail or CI
ingestion.

| Result | Location | How to review it |
|---|---|---|
| pytest component JUnit | `dev-tools/runtime/test-results/<component>/pytest.xml` | IDE test viewer or any JUnit-compatible viewer |
| pytest end-to-end JUnit | `dev-tools/runtime/test-results/e2e/pytest.xml` | JUnit-compatible viewer |
| Python coverage | `<component>/coverage.xml` | Coverage-aware IDE, CI coverage service, or XML viewer |
| Config-service HTML coverage | `config-service/htmlcov/index.html` | Open in a browser |
| Playwright HTML report | `<component>/test-results/playwright-report/index.html` | Open in a browser |
| Playwright JUnit | `<component>/test-results/playwright-junit.xml` | JUnit-compatible viewer |
| Playwright failure evidence | `<component>/test-results/artifacts/` | Inspect retained traces, screenshots, and videos |
| Vitest JUnit | `config-service/test-results/vitest-junit.xml` | JUnit-compatible viewer |
| Security pytest JUnit | `dev-tools/runtime/security-reports/<scope>/pytest.xml` | JUnit-compatible viewer |
| Ruff findings | `dev-tools/runtime/security-reports/<scope>/ruff.sarif` | SARIF viewer or GitHub code-scanning ingestion |
| Semgrep findings | `dev-tools/runtime/security-reports/<scope>/semgrep.sarif` | SARIF viewer or GitHub code-scanning ingestion |
| Bandit findings | `dev-tools/runtime/security-reports/<scope>/bandit.json` | JSON viewer; compare with Ruff findings |
| Secret scan | `dev-tools/runtime/security-reports/<scope>/detect-secrets.json` | JSON viewer; validate every candidate without copying secrets into issues |
| Dependency audit | `dev-tools/runtime/security-reports/<scope>/pip-audit.json` | JSON viewer; review package, advisory, and fixed-version data |
| Developer CLI issues/errors | `dev-tools/runtime/logs/*-issues.json` and `*-errors.json` | Use the paths printed at command completion |

`<scope>` is `repository` for `secure all` and the component directory name for `secure named`.
The runtime and test-result directories are generated evidence and are not source-controlled.
Subsequent runs of the same scope replace stable report files; copy a report elsewhere when it must
be retained for a release or investigation.

## Review Order

1. Confirm the command exit code and read the first failing tool in the terminal.
2. Open the matching JUnit, SARIF, JSON, or HTML result from the table above.
3. For browser failures, inspect the Playwright trace before relying only on a screenshot.
4. For security findings, validate reachability and trust boundaries before suppressing a rule.
5. Add or update a regression test with every defect fix, then rerun the focused suite and the
   appropriate repository gate.

CI jobs should retain the relevant `test-results`, `coverage.xml`, and
`dev-tools/runtime/security-reports` paths as job artifacts. SARIF files are suitable for a code
scanning interface; JUnit files are suitable for test-result summaries. The console log remains
useful for diagnosis but should not be the only retained evidence.
