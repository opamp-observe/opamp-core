/*
 * Copyright 2026 opamp.info
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function () {
  "use strict";

  function normalizeConfigType(rawValue, fallback) {
    var value = String(rawValue || "").trim().toLowerCase();
    if (!value) {
      return String(fallback || "");
    }
    if (value === "fluentbit" || value === "fluent-bit" || value === "fluent_bit" || value === "fluent bit") {
      return "fluentbit";
    }
    if (value === "fluentd" || value === "fluent-d" || value === "fluent_d" || value === "fluent d") {
      return "fluentd";
    }
    return String(fallback || value);
  }

  function buildConfigTypeQuery(configType, fallback) {
    var normalized = normalizeConfigType(configType, fallback);
    if (!normalized) {
      return "";
    }
    return "?config_type=" + encodeURIComponent(normalized);
  }

  function fetchJson(url, options) {
    return fetch(url, options || {}).then(function (resp) {
      return resp.text().then(function (text) {
        var data = {};
        try {
          data = text ? JSON.parse(text) : {};
        } catch (_parseError) {
          data = { error: text };
        }
        if (!resp.ok) {
          var err = new Error(
            data.error ||
            (Array.isArray(data.errors) && data.errors.length > 0 && data.errors[0].message) ||
            JSON.stringify(data)
          );
          err.payload = data;
          err.status = resp.status;
          throw err;
        }
        return data;
      });
    });
  }

  function postJson(url, payload) {
    return fetchJson(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    });
  }

  function formatConsoleArgs(args) {
    var parts = [];
    for (var index = 0; index < args.length; index += 1) {
      var item = args[index];
      if (item === undefined) {
        parts.push("undefined");
      } else if (item === null) {
        parts.push("null");
      } else if (item instanceof Error) {
        parts.push(item.message || String(item));
      } else if (typeof item === "object") {
        try {
          parts.push(JSON.stringify(item));
        } catch (_serializeError) {
          parts.push(String(item));
        }
      } else {
        parts.push(String(item));
      }
    }
    return parts.join(" ");
  }

  function create(options) {
    var settings = options && typeof options === "object" ? options : {};
    var apiBase = String(settings.apiBase || "/config-service/api/v1");
    var uiFeaturesPath = String(settings.uiFeaturesPath || "/api/ui/features");
    var lastUiErrorFingerprint = "";
    var lastUiErrorAt = 0;
    var isReportingUiError = false;

    function reportUiError(details) {
      var payload = details && typeof details === "object" ? details : {};
      var fingerprint = JSON.stringify({
        kind: payload.kind || "",
        message: payload.message || "",
        source: payload.source || "",
        path: payload.path || "",
        line: payload.line || "",
        column: payload.column || "",
      });
      var now = Date.now();
      if (fingerprint === lastUiErrorFingerprint && now - lastUiErrorAt < 4000) {
        return;
      }
      lastUiErrorFingerprint = fingerprint;
      lastUiErrorAt = now;
      if (!isReportingUiError) {
        isReportingUiError = true;
        try {
          console.error(
            "[Config Editor Error]",
            String(payload.kind || "runtime_error"),
            String(payload.message || "Unknown UI error"),
            payload
          );
        } catch (_consoleErr) {
          // Keep error reporting resilient.
        }
        isReportingUiError = false;
      }
      fetch(apiBase + "/client-errors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind: String(payload.kind || "runtime_error"),
          message: String(payload.message || "Unknown UI error"),
          source: String(payload.source || "browser"),
          path: String(payload.path || window.location.href || ""),
          stack: payload.stack ? String(payload.stack) : "",
          line: payload.line === undefined ? null : payload.line,
          column: payload.column === undefined ? null : payload.column,
        }),
        keepalive: true,
      }).catch(function (err) {
        if (!isReportingUiError) {
          isReportingUiError = true;
          try {
            console.error(
              "[Config Editor Error] Failed to post UI error to backend:",
              err && err.message ? err.message : String(err)
            );
          } catch (_consoleErr) {
            // Avoid error-reporting loops when the backend is unavailable.
          }
          isReportingUiError = false;
        }
      });
    }

    function installGlobalUiErrorHandlers() {
      if (!window.__CONFIG_SERVICE_UI_CONSOLE_ERROR_PATCHED__) {
        window.__CONFIG_SERVICE_UI_CONSOLE_ERROR_PATCHED__ = true;
        var originalConsoleError = console.error;
        console.error = function () {
          var args = Array.prototype.slice.call(arguments);
          originalConsoleError.apply(console, args);
          if (isReportingUiError) {
            return;
          }
          reportUiError({
            kind: "console_error",
            message: formatConsoleArgs(args) || "console.error called",
            source: "browser_console",
            path: window.location.href,
          });
        };
      }

      window.addEventListener("error", function (event) {
        var error = event && event.error;
        reportUiError({
          kind: "window_error",
          message: error && error.message ? error.message : String((event && event.message) || "Unhandled UI error"),
          source: event && event.filename ? event.filename : "browser",
          path: window.location.href,
          stack: error && error.stack ? error.stack : "",
          line: event && event.lineno ? event.lineno : null,
          column: event && event.colno ? event.colno : null,
        });
      });

      window.addEventListener("unhandledrejection", function (event) {
        var reason = event ? event.reason : null;
        var message = "Unhandled promise rejection";
        var stack = "";
        if (reason && typeof reason === "object") {
          message = String(reason.message || message);
          stack = reason.stack ? String(reason.stack) : "";
        } else if (reason !== undefined && reason !== null) {
          message = String(reason);
        }
        reportUiError({
          kind: "unhandledrejection",
          message: message,
          source: "browser",
          path: window.location.href,
          stack: stack,
        });
      });
    }

    return {
      fetchJson: fetchJson,
      reportUiError: reportUiError,
      installGlobalUiErrorHandlers: installGlobalUiErrorHandlers,
      getHealth: function () {
        return fetchJson(apiBase + "/health");
      },
      getIssueCodes: function () {
        return fetchJson(apiBase + "/issue-codes");
      },
      getVersions: function (configType) {
        return fetchJson(apiBase + "/versions" + buildConfigTypeQuery(configType, "fluentbit"));
      },
      getDryRunAvailability: function (version, configType) {
        return fetchJson(
          apiBase +
            "/agent-validation/availability/" +
            encodeURIComponent(version) +
            buildConfigTypeQuery(configType, "fluentbit")
        );
      },
      renderFluentd: function (version, payload) {
        return postJson(apiBase + "/render/fluentd/" + encodeURIComponent(version), payload);
      },
      renderYaml: function (version, configType, payload) {
        return postJson(
          apiBase + "/render/yaml/" + encodeURIComponent(version) + buildConfigTypeQuery(configType, "fluentbit"),
          payload
        );
      },
      prepareFileForLoad: function (text, fileName, configType) {
        return postJson(apiBase + "/ui/prepare-file", {
          text: String(text || ""),
          file_name: String(fileName || ""),
          config_type: String(configType || ""),
        });
      },
      getUiFeatures: function () {
        return fetch(uiFeaturesPath)
          .then(function (resp) {
            if (!resp.ok) {
              return null;
            }
            return resp.json();
          });
      },
      loadSourceFile: function (sourcePath, configType) {
        return postJson(apiBase + "/ui/load-source-file", {
          source_path: String(sourcePath || ""),
          config_type: String(configType || ""),
        });
      },
      parseFluentbit: function (version, payload) {
        return postJson(apiBase + "/parse/fluentbit/" + encodeURIComponent(version), payload);
      },
      parseFluentd: function (version, payload) {
        return postJson(apiBase + "/parse/fluentd/" + encodeURIComponent(version), payload);
      },
      validateDocument: function (version, configType, payload) {
        return postJson(
          apiBase + "/validate/" + encodeURIComponent(version) + buildConfigTypeQuery(configType, "fluentbit"),
          payload
        );
      },
      getSchema: function (version, configType, payload) {
        return postJson(
          apiBase + "/schema/" + encodeURIComponent(version) + buildConfigTypeQuery(configType, "fluentbit"),
          payload
        );
      },
      getCatalog: function (version, configType) {
        return fetchJson(
          apiBase + "/catalog/" + encodeURIComponent(version) + buildConfigTypeQuery(configType, "fluentbit")
        );
      },
      getServiceOptions: function (version, configType) {
        return fetchJson(
          apiBase + "/service-options/" + encodeURIComponent(version) + buildConfigTypeQuery(configType, "")
        );
      },
      getParserOptions: function (version, configType) {
        return fetchJson(
          apiBase + "/parser-options/" + encodeURIComponent(version) + buildConfigTypeQuery(configType, "")
        );
      },
      runDryRun: function (version, configType, payload) {
        return postJson(
          apiBase + "/agent-validation/dry-run/" + encodeURIComponent(version) + buildConfigTypeQuery(configType, "fluentbit"),
          payload
        );
      },
    };
  }

  window.ConfigServiceUiApi = {
    create: create,
    fetchJson: fetchJson,
  };
})();
