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

"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const {
  DEFAULT_SLOW_MOTION_MILLISECONDS,
  createPlaywrightRuntimeOptions,
  createPythonWebServerCommand,
} = require("./playwright_runtime_options.cjs");

const CUSTOM_SLOW_MOTION_MILLISECONDS = 425;

test("headless mode remains the default and retains only failure evidence", () => {
  const runtimeOptions = createPlaywrightRuntimeOptions({}, []);

  assert.equal(runtimeOptions.watchModeEnabled, false);
  assert.equal(runtimeOptions.workers, undefined);
  assert.equal(runtimeOptions.use.headless, true);
  assert.equal(runtimeOptions.use.launchOptions.slowMo, 0);
  assert.equal(runtimeOptions.use.screenshot, "only-on-failure");
  assert.equal(runtimeOptions.use.trace, "retain-on-failure");
  assert.equal(runtimeOptions.use.video, "retain-on-failure");
});

test("headed command line mode is slowed and records every test", () => {
  const runtimeOptions = createPlaywrightRuntimeOptions({}, ["--headed"]);

  assert.equal(runtimeOptions.watchModeEnabled, true);
  assert.equal(runtimeOptions.workers, 1);
  assert.equal(runtimeOptions.use.headless, false);
  assert.equal(
    runtimeOptions.use.launchOptions.slowMo,
    DEFAULT_SLOW_MOTION_MILLISECONDS,
  );
  assert.equal(runtimeOptions.use.screenshot, "on");
  assert.equal(runtimeOptions.use.trace, "on");
  assert.equal(runtimeOptions.use.video, "on");
});

test("environment mode accepts a custom slow motion delay", () => {
  const runtimeOptions = createPlaywrightRuntimeOptions(
    {
      PLAYWRIGHT_SLOW_MO_MS: String(CUSTOM_SLOW_MOTION_MILLISECONDS),
      PLAYWRIGHT_WATCH: "true",
    },
    [],
  );

  assert.equal(runtimeOptions.watchModeEnabled, true);
  assert.equal(runtimeOptions.use.launchOptions.slowMo, CUSTOM_SLOW_MOTION_MILLISECONDS);
});

test("invalid slow motion values fall back to the watchable default", () => {
  const runtimeOptions = createPlaywrightRuntimeOptions(
    {
      PLAYWRIGHT_SLOW_MO_MS: "not-a-number",
      PLAYWRIGHT_WATCH: "yes",
    },
    [],
  );

  assert.equal(
    runtimeOptions.use.launchOptions.slowMo,
    DEFAULT_SLOW_MOTION_MILLISECONDS,
  );
});

test("Python web server commands use Windows environment syntax and path delimiters", () => {
  const command = createPythonWebServerCommand({
    pythonPathEntries: ["src", "../config-service/src"],
    environmentVariables: { APP_ENABLE_DEV_FEATURES: "1" },
    pythonArguments: "-m catalog_service --port 8291",
    platform: "win32",
    environment: {},
  });

  assert.equal(
    command,
    'set "PYTHONPATH=src;../config-service/src" && set "APP_ENABLE_DEV_FEATURES=1" && py -3.11 -m catalog_service --port 8291',
  );
});

test("Python web server commands use POSIX environment syntax and overrides", () => {
  const command = createPythonWebServerCommand({
    pythonPathEntries: ["src", "../config-service/src"],
    environmentVariables: { APP_ENABLE_DEV_FEATURES: "1" },
    pythonArguments: "-m catalog_service --port 8291",
    platform: "linux",
    environment: { PLAYWRIGHT_PYTHON_COMMAND: "python-custom" },
  });

  assert.equal(
    command,
    "PYTHONPATH='src:../config-service/src' APP_ENABLE_DEV_FEATURES='1' python-custom -m catalog_service --port 8291",
  );
});
