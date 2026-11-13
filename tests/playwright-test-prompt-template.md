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

# Playwright Test Prompt Template

Use this template when asking Codex to create or update Playwright tests for `config-service/ui-tests/config-ui.spec.js`.

## Prompt Template

```text
Create Playwright test(s) for <feature or bug> in the Config Editor.

Context:
- Page: /config-service/ui
- Config type/version context: <fluentbit/fluentd and version if relevant>
- Current behavior: <what happens now>
- Expected behavior: <what should happen>

Test scope:
- Add test(s) to: config-service/ui-tests/config-ui.spec.js
- Use existing test style and selectors from that file.
- Keep tests deterministic and avoid timing flakiness.

Steps to automate:
1. <step 1>
2. <step 2>
3. <step 3>

Assertions:
- <assertion 1>
- <assertion 2>
- <assertion 3>

Constraints:
- Use the Apache 2.0 license header with `Copyright 2026 opamp.info`, following `license.txt`.
- Do not change config type/version unless the scenario requires it.
- Prefer role/name selectors for buttons and explicit CSS ids for fields.
- If needed, add/extend fixture files under config-service/ui-tests/fixtures.

Deliverables:
- Implement test code.
- Run `npm run ui:test -- --list` and confirm test is discovered.
- Summarize what was added and which file/lines changed.
```

## Example 1: Plugin Appears Immediately

```text
Create a Playwright regression test for plugin add behavior.

Context:
- Page: /config-service/ui
- Config type/version context: default Fluent Bit startup state
- Current behavior: plugin was not showing until changing type or version
- Expected behavior: plugin appears in plugin list immediately after Add Plugin

Test scope:
- Add test to config-service/ui-tests/config-ui.spec.js

Steps to automate:
1. Capture current values of #config-type-select and #version-select.
2. Select plugin section `inputs`.
3. Read currently selected value from #plugin-name.
4. Click "Add Plugin".

Assertions:
- #plugin-list contains the selected plugin name.
- #config-type-select value is unchanged.
- #version-select value is unchanged.
```

## Example 2: Mode Switch Panel Visibility

```text
Create a Playwright test to validate panel visibility when switching configuration type.

Context:
- Page: /config-service/ui
- Switch from Fluent Bit to Fluentd
- Expected behavior: Add Plugin panel hides, Labels and Workers panels show

Steps to automate:
1. Assert #add-plugin-panel is visible initially.
2. Assert #labels-panel and #workers-panel are hidden initially.
3. Change #config-type-select to fluentd.

Assertions:
- #add-plugin-panel is hidden.
- #labels-panel is visible.
- #workers-panel is visible.
```

## Example 3: Client Error Reporting

```text
Create a Playwright test to verify browser console errors are posted to backend.

Context:
- Page: /config-service/ui
- Endpoint: /config-service/api/v1/client-errors

Steps to automate:
1. Wait for a POST request matching /client-errors.
2. Trigger `console.error("playwright synthetic console error")` via page.evaluate.

Assertions:
- A POST request to /client-errors is captured.
- Request body contains `playwright synthetic console error`.
```

## Quick Tips

- Prefer assertions against stable IDs such as `#plugin-list`, `#parser-format`, `#yaml-output`.
- Use `await expect(...).toBeVisible()` or `toContainText()` instead of manual sleeps.
- Keep one behavior per test unless the flow is tightly coupled.
- Name tests in behavior language: `"<action> <expected result>"`.
