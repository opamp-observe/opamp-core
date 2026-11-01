// Copyright 2026 opamp.info
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * Batch-validates Fluent Bit chapter YAML files through the Config Service UI.
 *
 * This is deliberately an end-to-end browser test instead of a direct API test.
 * It opens each source YAML file in the real editor, asks the UI to render it,
 * makes small representative edits, saves the result, and then checks the saved
 * YAML for expected metadata and accidental path loss.
 *
 * The script is used by:
 * - npm script `ui:chapter-batch`
 * - config-service/dev-tools/run_playwright_chapter_batch_with_podman.sh
 * - tests/test-containers/config-service-ui-playwright-batch/entrypoint.sh
 * - tests/test-containers/run_regression_pack.py
 */
import fs from "node:fs/promises";
import fssync from "node:fs";
import path from "node:path";
import { chromium } from "@playwright/test";
import yaml from "js-yaml";

/**
 * Parse simple `--key value` command line arguments.
 *
 * The runner only needs a small argument surface, so using a tiny parser keeps
 * this file self-contained inside the container image.
 */
function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) {
      continue;
    }
    const key = token.slice(2);
    const value = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : "true";
    args[key] = value;
  }
  return args;
}

/**
 * Compare version-like strings such as `3.0.10` and `3.1`.
 *
 * The UI exposes Fluent Bit versions as option labels. Sorting with this helper
 * lets the test choose the latest listed version instead of relying on the
 * browser's text order.
 */
function compareVersions(left, right) {
  const a = String(left || "").split(".").map((part) => Number(part) || 0);
  const b = String(right || "").split(".").map((part) => Number(part) || 0);
  const length = Math.max(a.length, b.length);
  for (let i = 0; i < length; i += 1) {
    const diff = (a[i] || 0) - (b[i] || 0);
    if (diff !== 0) {
      return diff;
    }
  }
  return 0;
}

/** Return today's date in the `YYYY-MM-DD` form expected by metadata fields. */
function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

/**
 * Convert a nested object/array/scalar tree into JSONPath-like leaf paths.
 *
 * Later, the runner compares source paths with saved paths. This catches a UI
 * round-trip that silently drops parts of the original configuration.
 */
function flattenPaths(value, prefix = "$") {
  const out = new Set();
  function walk(node, current) {
    if (Array.isArray(node)) {
      if (node.length === 0) {
        out.add(current);
        return;
      }
      node.forEach((item, index) => {
        walk(item, `${current}[${index}]`);
      });
      return;
    }
    if (node && typeof node === "object") {
      const keys = Object.keys(node);
      if (keys.length === 0) {
        out.add(current);
        return;
      }
      keys.forEach((key) => {
        walk(node[key], `${current}.${key}`);
      });
      return;
    }
    out.add(current);
  }
  walk(value, prefix);
  return out;
}

/** Recursively list all files under a directory. */
async function walkFiles(rootDir) {
  const discovered = [];
  async function recurse(dir) {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    for (const entry of entries) {
      const absolute = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        await recurse(absolute);
      } else {
        discovered.push(absolute);
      }
    }
  }
  await recurse(rootDir);
  return discovered;
}

/**
 * Return true when a path lives inside a chapter folder from the external
 * Fluent Bit example repository.
 */
function hasChapterSegment(filePath) {
  const normalized = filePath.replace(/\\/g, "/");
  return /\/Chapter[^/]*\//i.test(normalized);
}

/**
 * Discover candidate YAML files for the batch run.
 *
 * The JSON config controls extensions and skip patterns. Skip patterns are
 * important because the external sample repository contains Helm charts,
 * Kubernetes manifests, compose files, and answer files that are not direct
 * Config Service editor inputs.
 */
async function discoverYamlFiles(sourceRoot, config) {
  const allFiles = await walkFiles(sourceRoot);
  const extensions = Array.isArray(config.yamlExtensions) && config.yamlExtensions.length > 0
    ? config.yamlExtensions.map((ext) => String(ext).toLowerCase())
    : [".yaml", ".yml"];
  const excludePatterns = Array.isArray(config.excludePathPatterns)
    ? config.excludePathPatterns.map((pattern) => new RegExp(String(pattern), "i"))
    : [];

  return allFiles
    .filter((filePath) => hasChapterSegment(filePath))
    .filter((filePath) => extensions.includes(path.extname(filePath).toLowerCase()))
    .filter((filePath) => {
      const normalized = path.relative(sourceRoot, filePath).replace(/\\/g, "/");
      return !excludePatterns.some((pattern) => pattern.test(normalized));
    })
    .sort((left, right) => left.localeCompare(right));
}

/** Load YAML from disk, preserving multi-document YAML as an array. */
function loadYamlFile(filePath) {
  const raw = fssync.readFileSync(filePath, "utf-8");
  const docs = yaml.loadAll(raw);
  if (!docs || docs.length === 0) {
    return {};
  }
  if (docs.length === 1) {
    return docs[0] || {};
  }
  return docs;
}

/**
 * Parse YAML that was saved by the browser workflow.
 *
 * Validation issues are reported later, so parse errors become an empty object
 * here instead of interrupting result collection for the current file.
 */
function safeYamlParse(text) {
  try {
    const parsed = yaml.load(text);
    return parsed || {};
  } catch (_err) {
    return {};
  }
}

/**
 * Some panels can be collapsed in the editor. This opens a panel only when the
 * visible toggle says `Open`, leaving already-open panels alone.
 */
async function ensurePanelOpenIfCollapsed(page, toggleSelector) {
  const toggle = page.locator(toggleSelector);
  if ((await toggle.count()) === 0) {
    return;
  }
  const label = String((await toggle.first().textContent()) || "").trim().toLowerCase();
  if (label === "open") {
    await toggle.first().click();
  }
}

/** Read the UI version selector and return the highest version-like option. */
async function uiLatestVersion(page) {
  const options = await page.locator("#version-select option").allTextContents();
  const normalized = options.map((entry) => String(entry || "").trim()).filter(Boolean);
  if (normalized.length === 0) {
    return "";
  }
  normalized.sort(compareVersions);
  return normalized[normalized.length - 1];
}

/**
 * Wait until plugin catalog data has loaded.
 *
 * The editor cannot parse and render loaded files until the plugin selector has
 * at least one option, so this wait avoids racing the startup API calls.
 */
async function waitForCatalogOptions(page) {
  await page.locator("#plugin-name").waitFor({ timeout: 20_000 });
  await page.waitForFunction(() => {
    const select = document.querySelector("#plugin-name");
    return Boolean(select && select.options && select.options.length > 0);
  }, { timeout: 20_000 });
}

/**
 * Count pipeline plugins in the original YAML model.
 *
 * The runner uses this count as a rough readiness signal after the UI opens a
 * file. It waits until at least this many plugin cards appear in the editor.
 */
function countSourcePlugins(sourceModel) {
  const pipeline = sourceModel && sourceModel.config && sourceModel.config.pipeline
    ? sourceModel.config.pipeline
    : sourceModel && sourceModel.pipeline
      ? sourceModel.pipeline
      : {};
  return ["inputs", "filters", "outputs"].reduce((total, section) => {
    const entries = pipeline && Array.isArray(pipeline[section]) ? pipeline[section] : [];
    return total + entries.length;
  }, 0);
}

/**
 * Wait for the selected file name and expected plugin cards to appear in the UI.
 */
async function waitForConfigurationLoad(page, yamlFile, sourceModel) {
  const fileName = path.basename(yamlFile);
  await page.waitForFunction((expected) => {
    const display = document.querySelector("#open-file-display");
    return Boolean(display && String(display.value || "").includes(expected));
  }, fileName, { timeout: 30_000 });

  const expectedPlugins = countSourcePlugins(sourceModel);
  if (expectedPlugins > 0) {
    await page.waitForFunction((minimum) => {
      return document.querySelectorAll("#plugin-list .plugin-card").length >= minimum;
    }, expectedPlugins, { timeout: 30_000 });
  }
}

/** Wait until the rendered YAML output panel contains text. */
async function waitForRenderedConfiguration(page) {
  await page.waitForFunction(() => {
    const output = document.querySelector("#yaml-output");
    return Boolean(output && String(output.textContent || "").trim().length > 0);
  }, { timeout: 30_000 });
}

/**
 * Click Render and wait for the output panel to be refreshed.
 *
 * A previous output snapshot is supplied to ensure the script observes a new
 * render instead of reusing stale text from a prior operation.
 */
async function renderFromUi(page) {
  const output = page.locator("#yaml-output");
  const previous = (await output.textContent().catch(() => "")) || "";
  await page.getByRole("button", { name: "Render" }).click();
  await page.waitForFunction((previousText) => {
    const status = document.querySelector("#status-message");
    const rendered = document.querySelector("#yaml-output");
    const text = String(rendered && rendered.textContent || "").trim();
    return Boolean(
      status &&
      String(status.textContent || "").includes("Rendered configuration updated.") &&
      text.length > 0 &&
      text !== String(previousText || "").trim()
    );
  }, previous, { timeout: 30_000 });
}

/** Add one metadata variable using the same controls a user would use. */
async function addMetadataVariable(page, key, value) {
  await page.locator("#metadata-env-key-input").fill(String(key));
  await page.locator("#metadata-env-value-input").fill(String(value));
  await page.getByRole("button", { name: "Add Metadata Variable" }).click();
}

/**
 * Make small edits across each visible plugin card.
 *
 * The goal is not to rewrite every field. It is to prove that text controls,
 * selects, checkboxes, and comment editors remain usable across a broad set of
 * real chapter examples.
 */
async function annotatePlugins(page, suffix) {
  const cards = page.locator("#plugin-list .plugin-card");
  const count = await cards.count();
  for (let i = 0; i < count; i += 1) {
    const card = cards.nth(i);
    const commentToggle = card.locator("button[aria-label*='plugin comment editor']");
    if ((await commentToggle.count()) > 0) {
      await commentToggle.first().click();
      const textarea = card.locator(".comment-editor textarea");
      if ((await textarea.count()) > 0) {
        await textarea.first().fill(`batch-comment ${suffix} plugin-${i + 1}`);
      }
    }

    const controls = card.locator(".field-grid .field-row input:not([disabled]), .field-grid .field-row textarea:not([disabled]), .field-grid .field-row select:not([disabled])");
    const controlCount = await controls.count();
    for (let controlIndex = 0; controlIndex < controlCount; controlIndex += 1) {
      if (controlIndex % 2 === 0) {
        continue;
      }
      const control = controls.nth(controlIndex);
      const tagName = await control.evaluate((element) => element.tagName.toLowerCase());
      if (tagName === "select") {
        const optionValues = await control.locator("option").evaluateAll((nodes) => nodes.map((node) => node.value).filter(Boolean));
        if (optionValues.length > 1) {
          await control.selectOption(optionValues[optionValues.length - 1]);
        }
      } else if (tagName === "input" && String(await control.getAttribute("type") || "").toLowerCase() === "checkbox") {
        if (controlIndex % 4 === 1) {
          await control.check();
        } else {
          await control.uncheck();
        }
      } else {
        const current = (await control.inputValue()) || "";
        await control.fill(`${current} batch-${controlIndex}`.trim());
      }
    }
  }
  return count;
}

/**
 * Add one configured optional plugin field when that field exists.
 *
 * Missing controls are warnings, not failures, because not every source YAML
 * contains the target plugin declared by the batch config.
 */
async function addAdditionalPluginAttribute(page, config, result) {
  const cfg = config.additionalPluginAttribute || {};
  const pluginName = String(cfg.pluginName || "").trim();
  const field = String(cfg.field || "").trim();
  const value = cfg.value;
  if (!pluginName || !field) {
    result.warnings.push("additionalPluginAttribute not configured; skipping optional attribute mutation.");
    return;
  }

  const cards = page.locator("#plugin-list .plugin-card");
  const count = await cards.count();
  let targetCard = null;
  for (let i = 0; i < count; i += 1) {
    const card = cards.nth(i);
    const heading = String((await card.locator(".plugin-head strong").first().textContent()) || "");
    if (heading.toLowerCase().includes(pluginName.toLowerCase())) {
      targetCard = card;
      break;
    }
  }

  if (!targetCard) {
    result.warnings.push(`No plugin card found for '${pluginName}'.`);
    return;
  }

  const optionalSelect = targetCard.locator(".optional-row select");
  const addOptionalBtn = targetCard.getByRole("button", { name: "Add Optional" });
  if ((await optionalSelect.count()) === 0 || (await addOptionalBtn.count()) === 0) {
    result.warnings.push(`Optional attribute controls unavailable for plugin '${pluginName}'.`);
    return;
  }

  const available = await optionalSelect.first().locator("option").evaluateAll((nodes) => nodes.map((node) => node.value));
  if (!available.includes(field)) {
    result.warnings.push(`Optional field '${field}' not available for plugin '${pluginName}'.`);
    return;
  }

  await optionalSelect.first().selectOption(field);
  await addOptionalBtn.first().click();

  const matchingRow = targetCard.locator(".field-row", { has: targetCard.locator(`label:has-text('${field}')`) }).first();
  if ((await matchingRow.count()) === 0) {
    result.warnings.push(`Added field '${field}' but could not locate editable row.`);
    return;
  }

  const editable = matchingRow.locator("input:not([disabled]), textarea:not([disabled]), select:not([disabled])").first();
  if ((await editable.count()) === 0) {
    result.warnings.push(`Field '${field}' is not editable in UI.`);
    return;
  }

  const tagName = await editable.evaluate((element) => element.tagName.toLowerCase());
  if (tagName === "select") {
    const options = await editable.locator("option").evaluateAll((nodes) => nodes.map((node) => node.value).filter(Boolean));
    if (options.length > 0) {
      await editable.selectOption(String(value || options[0]));
    }
  } else {
    await editable.fill(String(value === undefined || value === null ? "" : value));
  }
}

/**
 * Save through the browser download flow and copy the download to the artifact
 * directory used by the regression pack.
 */
async function saveFromUi(page, destinationPath) {
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.locator("#save-config").click(),
  ]);

  const tmpPath = await download.path();
  if (!tmpPath) {
    throw new Error("Playwright did not provide a download path for saved file.");
  }
  await fs.copyFile(tmpPath, destinationPath);
  return destinationPath;
}

/**
 * Return the actual Fluent Bit config payload from either supported saved shape.
 *
 * Some documents are saved as `{ config: ... }`; others are direct config
 * payloads. Normalizing here keeps the result checks simple.
 */
function configPayload(savedModel) {
  if (savedModel && savedModel.config && typeof savedModel.config === "object") {
    return savedModel.config;
  }
  return savedModel || {};
}

/**
 * Check the saved YAML for the edits the test intentionally made.
 *
 * Failures here mean the UI could complete the browser workflow but the saved
 * file did not contain expected metadata, comments, or optional field edits.
 */
function checkSavedOutput(savedModel, savedRaw, latestVersion, config) {
  const issues = [];
  const payload = configPayload(savedModel);
  const env = (payload && payload.env) || {};
  const expectedMetadata = {
    "_metadata.config_version": latestVersion,
  };

  Object.entries(expectedMetadata).forEach(([key, expected]) => {
    const actual = Object.prototype.hasOwnProperty.call(env, key) ? String(env[key]) : "";
    if (String(expected) && actual !== String(expected)) {
      issues.push(`Expected ${key}=${expected}, found '${actual || "<missing>"}'.`);
    }
  });

  if (!Object.prototype.hasOwnProperty.call(env, "_metadata.configuration_date")) {
    issues.push("Expected _metadata.configuration_date to be present.");
  }

  const additional = config.additionalPluginAttribute || {};
  if (additional.pluginName && additional.field) {
    const allPlugins = [];
    const pipeline = (payload && payload.pipeline) || {};
    ["inputs", "filters", "outputs"].forEach((section) => {
      const list = Array.isArray(pipeline[section]) ? pipeline[section] : [];
      list.forEach((plugin) => allPlugins.push(plugin));
    });

    const matching = allPlugins.find((plugin) => String(plugin && plugin.name || "").toLowerCase() === String(additional.pluginName).toLowerCase());
    if (!matching) {
      return issues;
    } else if (!Object.prototype.hasOwnProperty.call(matching, additional.field)) {
      issues.push(`Saved output missing plugin field '${additional.field}' on '${additional.pluginName}'.`);
    }
  }

  const hasPluginComment = (() => {
    if (String(savedRaw || "").includes("batch-comment")) {
      return true;
    }
    const pipeline = (payload && payload.pipeline) || {};
    return ["inputs", "filters", "outputs"].some((section) => {
      const list = Array.isArray(pipeline[section]) ? pipeline[section] : [];
      return list.some((plugin) => plugin && plugin._meta && Array.isArray(plugin._meta.comment_lines) && plugin._meta.comment_lines.length > 0);
    });
  })();

  if (!hasPluginComment) {
    issues.push("Saved output has no plugin comments in _meta.comment_lines.");
  }

  return issues;
}

/** Write pretty JSON, creating parent directories when needed. */
async function writeJson(filePath, payload) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, JSON.stringify(payload, null, 2), "utf-8");
}

/**
 * Orchestrate the full batch:
 * 1. load CLI arguments and JSON config
 * 2. discover source YAML files
 * 3. open each file in a fresh browser context
 * 4. render, edit, save, and compare output
 * 5. write JSON reports and set the process exit code
 */
async function main() {
  const args = parseArgs(process.argv.slice(2));
  const baseUrl = String(args["base-url"] || "http://127.0.0.1:8091/config-service/ui");
  const sourceRoot = path.resolve(String(args["source-root"] || process.cwd()));
  const configFile = path.resolve(String(args["config-file"] || "./dev-tools/playwright-batch-config/default-batch-config.json"));
  const reportFile = path.resolve(String(args["report-file"] || "./dev-tools/playwright-batch-artifacts/execution-report.json"));
  const outputDir = path.resolve(String(args["output-dir"] || "./dev-tools/playwright-batch-artifacts/modified"));
  const discrepancyDir = path.resolve(String(args["discrepancy-dir"] || "./dev-tools/playwright-batch-artifacts/discrepancies"));

  const config = JSON.parse(await fs.readFile(configFile, "utf-8"));
  const yamlFiles = await discoverYamlFiles(sourceRoot, config);

  const report = {
    started_at: new Date().toISOString(),
    base_url: baseUrl,
    source_root: sourceRoot,
    config_file: configFile,
    total_files: yamlFiles.length,
    passed: 0,
    failed: 0,
    with_discrepancies: 0,
    results: [],
  };

  if (yamlFiles.length === 0) {
    report.finished_at = new Date().toISOString();
    await writeJson(reportFile, report);
    console.log(`No YAML files found under ${sourceRoot}`);
    return;
  }

  await fs.mkdir(outputDir, { recursive: true });
  await fs.mkdir(discrepancyDir, { recursive: true });

  const browser = await chromium.launch({ headless: true });

  try {
    for (const yamlFile of yamlFiles) {
      const started = Date.now();
      const relative = path.relative(sourceRoot, yamlFile);
      const result = {
        source_file: yamlFile,
        relative_source_file: relative,
        output_file: "",
        status: "passed",
        plugin_count: 0,
        missing_paths: [],
        warnings: [],
        errors: [],
        duration_ms: 0,
      };

      const context = await browser.newContext({ acceptDownloads: true });
      await context.addInitScript(() => {
        Object.defineProperty(window, "showSaveFilePicker", {
          configurable: true,
          writable: true,
          value: undefined,
        });
      });
      const page = await context.newPage();

      try {
        const sourceModel = loadYamlFile(yamlFile);

        await page.goto(baseUrl, { waitUntil: "domcontentloaded" });
        await page.getByRole("heading", { name: "Config Service" }).waitFor({ timeout: 20_000 });
        await waitForCatalogOptions(page);

        await page.getByRole("button", { name: "New Configuration" }).click();
        await page.locator("#open-file").setInputFiles(yamlFile);
        await waitForConfigurationLoad(page, yamlFile, sourceModel);

        await renderFromUi(page);

        const latestVersion = await uiLatestVersion(page);
        if (!latestVersion) {
          result.warnings.push("Could not determine latest version from UI version selector.");
        }

        await ensurePanelOpenIfCollapsed(page, "#metadata-env-toggle");
        await addMetadataVariable(page, "config_version", latestVersion || "");
        await addMetadataVariable(page, "SCM_config_version", `${path.basename(yamlFile, path.extname(yamlFile))}-rev`);
        await addMetadataVariable(page, "configuration_date", todayIsoDate());

        result.plugin_count = await annotatePlugins(page, path.basename(yamlFile));
        await addAdditionalPluginAttribute(page, config, result);

        await renderFromUi(page);
        const outputBaseName = `${path.basename(yamlFile, path.extname(yamlFile))}${String(config.saveSuffix || "-ui-validated")}${path.extname(yamlFile) || ".yaml"}`;
        const outputPath = path.join(outputDir, outputBaseName);
        await saveFromUi(page, outputPath);
        result.output_file = outputPath;

        const savedRaw = await fs.readFile(outputPath, "utf-8");
        const savedModel = safeYamlParse(savedRaw);
        const sourcePaths = flattenPaths(sourceModel);
        const savedPaths = flattenPaths(savedModel);
        result.missing_paths = Array.from(sourcePaths).filter((pathToken) => !savedPaths.has(pathToken));

        if (result.missing_paths.length > 0) {
          result.status = "discrepancy";
          result.warnings.push(`Saved output missing ${result.missing_paths.length} source path(s).`);
        }

        const outputIssues = checkSavedOutput(savedModel, savedRaw, latestVersion, config);
        if (outputIssues.length > 0) {
          result.status = "failed";
          result.errors.push(...outputIssues);
        }
      } catch (err) {
        result.status = "failed";
        result.errors.push(err && err.message ? err.message : String(err));
      } finally {
        result.duration_ms = Date.now() - started;
        await context.close();
      }

      if (result.status === "passed") {
        report.passed += 1;
      } else if (result.status === "discrepancy") {
        report.with_discrepancies += 1;
        const discrepancyPath = path.join(discrepancyDir, `${path.basename(yamlFile)}.discrepancy.json`);
        await writeJson(discrepancyPath, result);
      } else {
        report.failed += 1;
        const discrepancyPath = path.join(discrepancyDir, `${path.basename(yamlFile)}.failure.json`);
        await writeJson(discrepancyPath, result);
      }

      report.results.push(result);
      console.log(`[${result.status.toUpperCase()}] ${result.relative_source_file}`);
    }
  } finally {
    await browser.close();
  }

  report.finished_at = new Date().toISOString();
  await writeJson(reportFile, report);

  const hasFailures = report.failed > 0 || report.with_discrepancies > 0;
  if (hasFailures) {
    console.log(`Completed with issues. failed=${report.failed}, discrepancies=${report.with_discrepancies}`);
    process.exitCode = 1;
  } else {
    console.log(`Completed successfully. passed=${report.passed}`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
