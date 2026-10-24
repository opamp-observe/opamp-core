/* Copyright 2026 mp3monster.org; Licensed under the Apache License, Version 2.0. */
const path = require("node:path");
const { defineConfig } = require("@playwright/test");
const {
  createPlaywrightRuntimeOptions,
} = require("/runner/playwright_runtime_options.cjs");

const resultsDirectory = process.env.ST007_RESULTS_DIR || "/host-output";
const runtimeOptions = createPlaywrightRuntimeOptions();

module.exports = defineConfig({
  testDir: "/runner",
  testMatch: "st007_ui.spec.js",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: 0,
  workers: runtimeOptions.workers,
  outputDir: path.join(resultsDirectory, "playwright"),
  reporter: [
    ["list"],
    ["junit", { outputFile: path.join(resultsDirectory, "playwright-junit.xml") }],
  ],
  use: {
    ...runtimeOptions.use,
    baseURL: process.env.ST007_BASE_URL || "http://127.0.0.1:18191",
    trace: "on",
  },
});
