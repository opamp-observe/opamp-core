# UI Testing

`config-service` now includes browser-based UI behavior tests using Playwright.

## Prompt Standard

Use `tests/playwright-test-prompt-template.md` as the canonical prompt format when asking Codex to
add or update Playwright coverage for `config-service/ui-tests/config-ui.spec.js`.

Use this populated suite instance as the starting point:

```text
Create Playwright regression test(s) for Config Editor field behavior, mode switching, partial
load handling, metadata editing, and save/render output.

Context:
- Page: /config-service/ui
- Config type/version context: default Fluent Bit startup state, Fluentd mode switching, and
  fixture-driven Fluent Bit YAML loads
- Current behavior: the suite covers service and parser dropdowns, plugin add behavior without
  config-type churn, client-error reporting, tooltip text quality, partial YAML load warnings,
  metadata separation, and header comment save/render output
- Expected behavior: stable controls stay populated, mode switching updates the right panels,
  partial loads remain usable while surfacing warnings, metadata keys stay separated from normal
  environment values, and save/render output preserves header comment ordering

Test scope:
- Add test(s) to: `config-service/ui-tests/config-ui.spec.js`
- Use existing test style and selectors from that file.
- Keep tests deterministic and avoid timing flakiness.

Steps to automate:
1. Open `/config-service/ui`, wait for the page heading and parser/plugin option lists to load,
   and capture the current config type/version when the scenario should preserve them.
2. Exercise service and parser controls, add plugins, and switch config type to `fluentd` only
   when the scenario is about panel visibility.
3. Load fixture YAML files from `config-service/ui-tests/fixtures` to validate partial-load
   warnings and metadata/environment separation.
4. Trigger `console.error(...)` and assert the client-errors endpoint receives the browser payload.
5. Use Save and Render flows to verify metadata normalization and header comment ordering in the
   downloaded or rendered output.

Assertions:
- Service and parser dropdowns expose expected enum and parser values.
- Adding a plugin updates `#plugin-list` immediately without changing config type or version.
- Switching to Fluentd hides `#add-plugin-panel` and shows `#labels-panel` and `#workers-panel`.
- Help tooltip text remains human-readable and excludes raw `http://` and `https://` URLs.
- Partial YAML load warnings populate `#status-message` and `#validation-issues` while preserving
  visible loaded plugin content.
- Metadata keys are separated from normal environment values and saved with `_metadata.` prefixes.
- Header comments are written before saved content and prepended to rendered output.

Constraints:
- Do not change config type/version unless the scenario requires it.
- Prefer role/name selectors for buttons and explicit CSS ids for fields.
- If needed, add or extend fixture files under config-service/ui-tests/fixtures.

Deliverables:
- Implement test code.
- Run `npm run ui:test -- --list` and confirm test is discovered.
- Summarize what was added and which files changed.
```

## What these tests cover
The Playwright suite focuses on high-value UI behaviors that are awkward to verify with backend tests alone.

Current test catalog (`config-service/ui-tests/config-ui.spec.js`):

1. `service log_level dropdown shows all expected enum values`
   - Verifies service `log_level` exposes the expected enum choices.
2. `parser format dropdown loads Fluent Bit parser formats`
   - Verifies parser formats are loaded and include expected entries (for example `json`).
3. `added plugin appears immediately without changing config type or version`
   - Verifies newly added plugin cards appear immediately, without forcing type/version changes.
4. `console errors are posted to the server client-errors endpoint`
   - Verifies browser `console.error(...)` is forwarded to `/config-service/api/v1/client-errors`.
5. `plugin panel visibility stays mode-consistent when switching config type`
   - Verifies Fluent Bit/Fluentd mode switching keeps plugin/label/worker panels consistent.
6. `plugin field help tooltip does not include raw URLs`
   - Verifies plugin field tooltip text remains human-readable and not raw links.
7. `loading partial Fluent Bit YAML shows loaded sections, status warning, and validation issue lines`
   - Verifies partial-load behavior, warning status, and validation line hints.
8. `service field help button keeps human-readable tooltip text only`
   - Verifies service field help text quality constraints.
9. `renderer panel exposes include loaded files toggle`
   - Verifies renderer controls include the include-files toggle.
10. `metadata keys are separated from normal environment variables when loading YAML`
    - Verifies `_metadata.*` keys are shown in metadata panel, not normal env panel.
11. `metadata keys can be added and are saved with the _metadata prefix`
    - Verifies metadata add/edit/save path and key normalization.
12. `view raw opens a read-only resizable text dialog`
    - Verifies raw save text opens in a read-only dialog with a single close action and resizable, scrollable layout.

Quick listing command:

```bash
cd config-service
npm run ui:test -- --list
```

## Location
- Playwright config: `config-service/playwright.config.js`
- Browser tests: `config-service/ui-tests/`
- UI fixtures: `config-service/ui-tests/fixtures/`

## Prerequisites
1. Node.js with `npm` / `npx`
2. Python 3.10+
3. Linux browser runtime dependencies required by Playwright Chromium

## Install and run manually
From repository root:

```bash
cd config-service
npm install
npx playwright install-deps chromium
npx playwright install chromium
npm run ui:test
```

Headed mode:

```bash
cd config-service
npm run ui:test:headed
```

## One-command runner
From repository root:

```bash
config-service/dev-tools/run_ui_quality_checks.sh
```

This runner will:
1. install Node dependencies
2. install the Chromium browser used by Playwright
3. run the Playwright UI suite

Note:
1. On Linux, Playwright may still require system packages such as `libnspr4`.
2. If browser launch fails with a missing shared-library error, run:

```bash
cd config-service
npx playwright install-deps chromium
```

3. `install-deps` may require `sudo`, depending on the machine.

## Container runner (recommended for dependency issues)
From repository root:

```bash
config-service/dev-tools/run_ui_quality_checks_in_container.sh
```

To run only the metadata scenarios:

```bash
config-service/dev-tools/run_ui_quality_checks_in_container.sh -g "metadata"
```

This runner:
1. verifies Docker daemon availability
2. runs Playwright inside `mcr.microsoft.com/playwright:v1.64.0-noble`
3. installs Python and Node dependencies in-container
4. executes the UI tests, forwarding any extra Playwright arguments

## Runtime model
The Playwright suite tests the Python-served UI, not the old standalone frontend dev server.

Playwright starts:
1. `python3 -m config_service`
2. with `APP_ENABLE_DEV_FEATURES=1`
3. on port `8091`

That means the tests exercise the actual packaged HTML/CSS/JS served by Quart.

## Notes on tooltip testing
Native browser tooltips are not asserted visually.

Instead, tests verify:
1. the `title` attribute text
2. whether help controls are enabled or disabled
3. whether linked documentation targets are correct

That approach is more stable across browsers and CI environments.
