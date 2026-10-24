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

const DEBUG_ARGUMENT = "--debug";
const DECIMAL_RADIX = 10;
const DEFAULT_SLOW_MOTION_MILLISECONDS = 250;
const HEADED_ARGUMENT = "--headed";
const HEADLESS_SLOW_MOTION_MILLISECONDS = 0;
const MINIMUM_SLOW_MOTION_MILLISECONDS = 0;
const SLOW_MOTION_ENVIRONMENT_VARIABLE = "PLAYWRIGHT_SLOW_MO_MS";
const PYTHON_COMMAND_ENVIRONMENT_VARIABLE = "PLAYWRIGHT_PYTHON_COMMAND";
const WATCH_MODE_ENVIRONMENT_VARIABLE = "PLAYWRIGHT_WATCH";
const WATCH_MODE_TRUE_VALUES = new Set(["1", "on", "true", "yes"]);
const WINDOWS_PLATFORM = "win32";
const WINDOWS_PYTHON_COMMAND = "py -3.11";
const POSIX_PYTHON_COMMAND = "python3";

/**
 * Return whether an environment value explicitly enables an optional behavior.
 *
 * @param {unknown} value - Environment value to normalize and compare.
 * @returns {boolean} True when the value is a supported affirmative token.
 */
function isEnabled(value) {
  return WATCH_MODE_TRUE_VALUES.has(String(value ?? "").trim().toLowerCase());
}

/**
 * Resolve the non-negative action delay used while a browser run is watched.
 *
 * @param {NodeJS.ProcessEnv} environment - Environment containing an optional delay override.
 * @returns {number} Delay in milliseconds between Playwright operations.
 */
function resolveSlowMotionMilliseconds(environment) {
  const configuredValue = String(
    environment[SLOW_MOTION_ENVIRONMENT_VARIABLE] ?? "",
  ).trim();
  if (!configuredValue) {
    return DEFAULT_SLOW_MOTION_MILLISECONDS;
  }
  const parsedValue = Number.parseInt(configuredValue, DECIMAL_RADIX);
  if (!Number.isFinite(parsedValue) || parsedValue < MINIMUM_SLOW_MOTION_MILLISECONDS) {
    return DEFAULT_SLOW_MOTION_MILLISECONDS;
  }
  return parsedValue;
}

/**
 * Build shared browser and evidence options for a Playwright configuration.
 *
 * @param {NodeJS.ProcessEnv} environment - Environment used to enable watch mode and set its delay.
 * @param {string[]} commandLineArguments - Playwright command arguments, including headed/debug flags.
 * @returns {{watchModeEnabled: boolean, workers: number|undefined, use: object}} Runtime options.
 */
function createPlaywrightRuntimeOptions(
  environment = process.env,
  commandLineArguments = process.argv,
) {
  const watchModeEnabled =
    isEnabled(environment[WATCH_MODE_ENVIRONMENT_VARIABLE]) ||
    commandLineArguments.includes(HEADED_ARGUMENT) ||
    commandLineArguments.includes(DEBUG_ARGUMENT);
  const slowMotionMilliseconds = watchModeEnabled
    ? resolveSlowMotionMilliseconds(environment)
    : HEADLESS_SLOW_MOTION_MILLISECONDS;

  return {
    watchModeEnabled,
    workers: watchModeEnabled ? 1 : undefined,
    use: {
      headless: !watchModeEnabled,
      launchOptions: {
        slowMo: slowMotionMilliseconds,
      },
      screenshot: watchModeEnabled ? "on" : "only-on-failure",
      trace: watchModeEnabled ? "on" : "retain-on-failure",
      video: watchModeEnabled ? "on" : "retain-on-failure",
    },
  };
}

/**
 * Quote one fixed environment value for a POSIX-compatible shell command.
 *
 * @param {unknown} value - Environment value to quote without shell expansion.
 * @returns {string} Single-quoted shell value.
 */
function quotePosixEnvironmentValue(value) {
  return `'${String(value).replaceAll("'", `'"'"'`)}'`;
}

/**
 * Build a cross-platform command that starts a Python Playwright web server.
 *
 * @param {object} options - Python paths, environment values, and module/script arguments.
 * @param {string[]} options.pythonPathEntries - Import paths passed through PYTHONPATH.
 * @param {Record<string, string>} options.environmentVariables - Additional child environment.
 * @param {string} options.pythonArguments - Arguments appended to the Python command.
 * @param {string} [options.platform] - Node platform identifier used for shell syntax.
 * @param {NodeJS.ProcessEnv} [options.environment] - Environment containing a Python override.
 * @returns {string} Command accepted by Playwright's webServer runner.
 */
function createPythonWebServerCommand({
  pythonPathEntries,
  environmentVariables,
  pythonArguments,
  platform = process.platform,
  environment = process.env,
}) {
  const pathDelimiter = platform === WINDOWS_PLATFORM ? ";" : ":";
  const commandEnvironment = {
    PYTHONPATH: pythonPathEntries.join(pathDelimiter),
    ...environmentVariables,
  };
  const configuredPythonCommand = String(
    environment[PYTHON_COMMAND_ENVIRONMENT_VARIABLE] ?? "",
  ).trim();
  const pythonCommand =
    configuredPythonCommand ||
    (platform === WINDOWS_PLATFORM ? WINDOWS_PYTHON_COMMAND : POSIX_PYTHON_COMMAND);

  if (platform === WINDOWS_PLATFORM) {
    const environmentPrefix = Object.entries(commandEnvironment)
      .map(([name, value]) => `set "${name}=${value}" &&`)
      .join(" ");
    return `${environmentPrefix} ${pythonCommand} ${pythonArguments}`;
  }

  const environmentPrefix = Object.entries(commandEnvironment)
    .map(([name, value]) => `${name}=${quotePosixEnvironmentValue(value)}`)
    .join(" ");
  return `${environmentPrefix} ${pythonCommand} ${pythonArguments}`;
}

module.exports = {
  DEFAULT_SLOW_MOTION_MILLISECONDS,
  createPlaywrightRuntimeOptions,
  createPythonWebServerCommand,
};
