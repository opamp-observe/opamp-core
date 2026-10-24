// Copyright 2026 mp3monster.org
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

const { defineConfig } = require("@playwright/test");
const {
  createPlaywrightRuntimeOptions,
  createPythonWebServerCommand,
} = require("../tests/playwright_runtime_options.cjs");

const testResultsDirectory = "test-results";
const runtimeOptions = createPlaywrightRuntimeOptions();

module.exports = defineConfig({
  testDir: "./ui-tests",
  timeout: 45_000,
  expect: {
    timeout: 8_000,
  },
  fullyParallel: false,
  retries: 0,
  workers: runtimeOptions.workers,
  outputDir: `${testResultsDirectory}/artifacts`,
  reporter: [
    ["list"],
    ["html", { outputFolder: `${testResultsDirectory}/playwright-report`, open: "never" }],
    ["junit", { outputFile: `${testResultsDirectory}/playwright-junit.xml` }],
  ],
  use: {
    ...runtimeOptions.use,
  },
  projects: [
    {
      name: "with-endpoints",
      use: {
        baseURL: "http://127.0.0.1:8181",
      },
    },
    {
      name: "without-endpoints",
      use: {
        baseURL: "http://127.0.0.1:8182",
      },
    },
    {
      name: "catalog-readonly",
      use: {
        baseURL: "http://127.0.0.1:8183",
      },
    },
  ],
  webServer: [
    {
      command: createPythonWebServerCommand({
        pythonPathEntries: ["provider/src", "config-service/src"],
        environmentVariables: {
          APP_ENABLE_DEV_FEATURES: "1",
          OPAMP_CONFIG_PATH: "provider/ui-tests/fixtures/opamp-with-endpoints.json",
        },
        pythonArguments: "-m opamp_provider.server --host 127.0.0.1 --port 8181",
      }),
      url: "http://127.0.0.1:8181/ui",
      cwd: "..",
      reuseExistingServer: true,
      timeout: 180_000,
    },
    {
      command: createPythonWebServerCommand({
        pythonPathEntries: ["provider/src", "config-service/src"],
        environmentVariables: {
          APP_ENABLE_DEV_FEATURES: "1",
          OPAMP_CONFIG_PATH: "provider/ui-tests/fixtures/opamp-without-endpoints.json",
        },
        pythonArguments: "-m opamp_provider.server --host 127.0.0.1 --port 8182",
      }),
      url: "http://127.0.0.1:8182/ui",
      cwd: "..",
      reuseExistingServer: true,
      timeout: 180_000,
    },
    {
      command: createPythonWebServerCommand({
        pythonPathEntries: ["provider/src", "config-service/src"],
        environmentVariables: {
          APP_ENABLE_DEV_FEATURES: "1",
          OPAMP_CONFIG_PATH: "provider/ui-tests/fixtures/opamp-catalog-readonly.json",
        },
        pythonArguments: "-m opamp_provider.server --host 127.0.0.1 --port 8183",
      }),
      url: "http://127.0.0.1:8183/ui",
      cwd: "..",
      reuseExistingServer: true,
      timeout: 180_000,
    },
  ],
});
