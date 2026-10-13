/* Copyright 2026 mp3monster.org; Licensed under the Apache License, Version 2.0. */
const path = require("node:path");
const { expect, test } = require("@playwright/test");

const browserConnectionName = "browser-complete";
const resultsDirectory = process.env.ST007_RESULTS_DIR || "/host-output";
const uiPath = "/svr-credentials-manager-service/ui";
const confidentialMarker = ["st007", "browser", "private", "value"].join("-");
const headerAccessName = "X-ST007-Access";
const mockClientIds = ["mock-client-01", "mock-client-02"];
const otherSettingEnabledKey = "enabled";
const otherSettingRatioKey = "ratio";
const otherSettingRetriesKey = "retries";
const otherSettingTenantKey = "tenant";

/**
 * Populate the active connection section with endpoint and structured JSON values.
 * @param {import("@playwright/test").Page} page Browser page containing the editor.
 * @param {{endpoint: string, headers?: object, otherSettings?: object}} options Section values.
 */
async function fillCurrentSection(page, options) {
  await page.locator("#destination-endpoint").fill(options.endpoint);
  await page.locator("#headers").fill(JSON.stringify(options.headers || {}));
  if (options.otherSettings) {
    await page.locator("#other-settings").fill(JSON.stringify(options.otherSettings));
  }
}

test("browser creates, assigns, and applies a complete connection definition", async ({ page }) => {
  // Exercise the operator workflow while retaining screenshot and trace evidence.
  await page.goto(uiPath);
  await expect(page.getByRole("heading", { name: "Server Credentials Manager" })).toBeVisible();
  await expect(page.locator("#status")).toContainText(
    "Removed assignments for missing connections"
  );

  await page.locator("#add-test-clients").click();
  await expect(page.locator("#status")).toContainText("Added 20 mock clients");

  await page.locator("#connection-name").fill(browserConnectionName);
  await fillCurrentSection(page, {
    endpoint: "https://opamp.browser.test/v1",
    headers: { [headerAccessName]: confidentialMarker },
  });

  await page.locator("#tab-own-metrics").click();
  await fillCurrentSection(page, { endpoint: "https://metrics.browser.test/v1" });
  await page.locator("#tab-own-traces").click();
  await fillCurrentSection(page, { endpoint: "https://traces.browser.test/v1" });
  await page.locator("#tab-own-logs").click();
  await fillCurrentSection(page, { endpoint: "https://logs.browser.test/v1" });
  await page.locator("#tab-other").click();
  await page.locator("#other-name").fill("archive");
  await fillCurrentSection(page, {
    endpoint: "https://archive.browser.test/v1",
    otherSettings: {
      [otherSettingEnabledKey]: true,
      [otherSettingRetriesKey]: 3,
      [otherSettingRatioKey]: 1.5,
      [otherSettingTenantKey]: "browser",
    },
  });

  await page.locator("#save-connection-bottom").click();
  await expect(page.locator("#status")).toHaveText(`Saved ${browserConnectionName}.`);
  await expect(page.locator("#connection-items")).toContainText(browserConnectionName);
  await expect(page.locator("#connection-items")).not.toContainText(confidentialMarker);

  const connectionRow = page.locator("#connection-items .connection-row").filter({
    hasText: browserConnectionName,
  });
  await connectionRow.getByRole("button", { name: "Assign" }).click();
  await page.locator("#assignment-available").selectOption(mockClientIds);
  await page.locator("#assign-selected-clients").click();
  await page.locator("#assignment-save").click();
  await expect(page.locator("#status")).toHaveText(
    `Saved assignments for ${browserConnectionName}.`
  );

  await connectionRow.getByRole("button", { name: "Apply" }).click();
  await expect(page.locator("#status")).toContainText(
    `Applied ${browserConnectionName} to 2 clients using fallback JSON log`
  );

  const listResponse = await page.request.get(
    "/svr-credentials-manager-service/api/v1/connections"
  );
  expect(await listResponse.text()).not.toContain(confidentialMarker);
  await page.screenshot({
    path: path.join(resultsDirectory, "screenshots", "st007-browser-workflow.png"),
    fullPage: true,
  });
});
