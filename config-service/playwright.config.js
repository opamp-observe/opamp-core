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

import { defineConfig } from "@playwright/test";
import playwrightRuntimeOptions from "../tests/playwright_runtime_options.cjs";

const testResultsDirectory = "test-results";
const runtimeOptions = playwrightRuntimeOptions.createPlaywrightRuntimeOptions();
const createPythonWebServerCommand = playwrightRuntimeOptions.createPythonWebServerCommand;

export default defineConfig({
  testDir: "./ui-tests",
  timeout: 30_000,
  expect: {
    timeout: 5_000,
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
    baseURL: "http://127.0.0.1:8091",
  },
  webServer: {
    command: createPythonWebServerCommand({
      pythonPathEntries: ["src"],
      environmentVariables: { APP_ENABLE_DEV_FEATURES: "1" },
      pythonArguments:
        "-m config_service --config-path config/config-service.json --port 8091",
    }),
    url: "http://127.0.0.1:8091/config-service/api/v1/health",
    cwd: ".",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
