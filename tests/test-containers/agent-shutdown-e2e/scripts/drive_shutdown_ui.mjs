#!/usr/bin/env node
/*
 * Copyright 2026 mp3monster.org
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * http://www.apache.org/licenses/LICENSE-2.0
 */

import fs from "node:fs/promises";
import { chromium } from "playwright";

const CAPABILITY_FQDN = "org.mp3monster.opamp_provider.command_shutdown_agent";
const DEFAULT_BASE_URL = "http://provider:8080";
const DEFAULT_EVIDENCE_PATH = "/evidence/ui-shutdown.json";
const DEFAULT_TIMEOUT_MS = 120_000;

/** Build the browser-driver configuration from environment variables. */
function loadConfiguration() {
  return {
    baseUrl: String(process.env.PROVIDER_BASE_URL || DEFAULT_BASE_URL).replace(/\/$/, ""),
    evidencePath: String(process.env.UI_EVIDENCE_PATH || DEFAULT_EVIDENCE_PATH),
    serviceInstanceId: String(process.env.SERVICE_INSTANCE_ID || "").trim(),
    timeoutMs: Number(process.env.UI_TIMEOUT_MS || DEFAULT_TIMEOUT_MS),
  };
}

/** Exercise the same provider controls used by an operator to queue shutdown. */
async function sendShutdownFromUi(configuration) {
  if (!configuration.serviceInstanceId) {
    throw new Error("SERVICE_INSTANCE_ID is required");
  }

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const evidence = {
    base_url: configuration.baseUrl,
    service_instance_id: configuration.serviceInstanceId,
    capability: CAPABILITY_FQDN,
    command_response_status: null,
    command_request_payload: null,
  };

  try {
    page.setDefaultTimeout(configuration.timeoutMs);
    await page.goto(`${configuration.baseUrl}/ui`, { waitUntil: "networkidle" });

    const agentRow = page.locator("#clientBody tr", {
      hasText: configuration.serviceInstanceId,
    });
    await agentRow.first().waitFor({ state: "visible" });
    await agentRow.first().click();
    await page.locator('button[data-tab="commands"]').click();
    await page.locator("#customCommandSelect").selectOption(CAPABILITY_FQDN);

    page.once("dialog", async dialog => {
      await dialog.accept();
    });

    const commandResponsePromise = page.waitForResponse(response => {
      return response.request().method() === "POST"
        && response.url().includes("/api/clients/")
        && response.url().endsWith("/commands");
    });
    await page.locator("#sendCustomCommandBtn").click();
    const commandResponse = await commandResponsePromise;
    evidence.command_response_status = commandResponse.status();
    evidence.command_request_payload = commandResponse.request().postDataJSON();
    if (commandResponse.status() !== 201) {
      throw new Error(`Shutdown command returned HTTP ${commandResponse.status()}`);
    }

    await page.screenshot({
      path: configuration.evidencePath.replace(/\.json$/i, ".png"),
      fullPage: true,
    });
    evidence.result = "passed";
  } catch (error) {
    evidence.result = "failed";
    evidence.error = String(error && error.stack ? error.stack : error);
    await page.screenshot({
      path: configuration.evidencePath.replace(/\.json$/i, "-failure.png"),
      fullPage: true,
    }).catch(() => {});
    throw error;
  } finally {
    await fs.writeFile(configuration.evidencePath, `${JSON.stringify(evidence, null, 2)}\n`);
    await browser.close();
  }
}

const configuration = loadConfiguration();
await sendShutdownFromUi(configuration);
