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

  // Central runtime constants for storage and UI persistence.
  var LAST_FILE_COOKIE = "config_service_last_opened_name";
  var LAST_DOC_STORAGE = "config_service_last_opened_doc";
  var LAST_DOC_SOURCE_PATH_STORAGE = "config_service_last_opened_source_path";
  var CUSTOM_SERVICE_OPTION = "__custom__";
  var HEADER_PREFIX = "config-service";
  var SERVICE_OPTIONS = [];
  var PARSER_FORMATS = [];
  var serviceOptionsLoadInFlight = null;
  var dryRunAvailabilityRequestSerial = 0;
  var runtimeSettings = window.ConfigServiceRuntime || {};

  /** Show and bind the provider-history button when browser history is available. */
  function initializeHistoryBackButton() {
    var button = document.querySelector('[data-history-back-button="true"]');
    if (!button || button.getAttribute("aria-hidden") === "true") {
      return;
    }
    function syncVisibility() {
      if (window.history.length > 1) {
        button.removeAttribute("hidden");
      } else {
        button.setAttribute("hidden", "hidden");
      }
    }
    button.addEventListener("click", function navigateBack() {
      window.history.back();
    });
    window.addEventListener("pageshow", syncVisibility);
    syncVisibility();
  }

  function normalizedCollapsedSectionSet() {
    var raw = runtimeSettings.collapsedSections;
    var values = [];
    if (Array.isArray(raw)) {
      values = raw.slice();
    } else if (typeof raw === "string") {
      values = raw.split(",");
    }
    var out = {};
    values.forEach(function (value) {
      var normalized = String(value || "")
        .trim()
        .toLowerCase()
        .replace(/[\s\-]+/g, "_");
      if (!normalized) {
        return;
      }
      out[normalized] = true;
    });
    return out;
  }

  // Single source of truth for UI runtime state.
  // Most render functions are projections of this object.
  var state = {
    versions: [],
    selectedVersion: "",
    catalog: null,
    compiledSchema: null,
    configType: "fluentbit",
    doc: null,
    collapse: {},
    pluginSection: "inputs",
    pluginName: "",
    catalogLoaded: false,
    currentFileName: "",
    currentSourcePath: "",
    validationStatus: "neutral",
    issueCodeMap: {},
    pendingFocusFieldKey: "",
    serviceCollapsed: false,
    servicePanelCollapsed: false,
    envPanelCollapsed: false,
    upstreamServersPanelCollapsed: false,
    parsersPanelCollapsed: false,
    validationCollapsed: false,
    yamlCollapsed: false,
    pluginsPanelCollapsed: false,
    labelsPanelCollapsed: true,
    workersPanelCollapsed: true,
    saveFileHandle: null,
    currentFileDisplay: "",
    lastRenderedSignature: "",
    renderDirty: false,
    readOnly: false,
    commentOpen: {},
    sourceLineMap: {},
    preserveSourceLineMapOnce: false,
    includedDocuments: [],
    mergeIncludesForValidation: false,
    saveOnValidate: false,
    renderIncludesForRender: false,
    metadataPanelCollapsed: false,
    dryRunAvailable: false,
    dryRunCapability: null,
  };
  var api = window.ConfigServiceUiApi.create({
    apiBase: "/config-service/api/v1",
    uiFeaturesPath: "/api/ui/features",
  });
  (function applyInitialPanelCollapseConfig() {
    var collapsed = normalizedCollapsedSectionSet();
    var has = function (key) {
      return Boolean(collapsed[key]);
    };
    state.servicePanelCollapsed = has("service");
    state.envPanelCollapsed = has("environment_variables") || has("env");
    state.metadataPanelCollapsed =
      has("metadata_environment_variables") ||
      has("metadata_env") ||
      has("metadata_as_environment_variables");
    state.upstreamServersPanelCollapsed = has("upstream_servers") || has("upstream");
    state.parsersPanelCollapsed = has("parsers");
    state.pluginsPanelCollapsed = has("plugins");
    state.labelsPanelCollapsed = has("labels");
    state.workersPanelCollapsed = has("workers");
    state.validationCollapsed = has("validation");
    state.yamlCollapsed = has("rendered_configuration") || has("rendered");
  })();

  var uiHelpers = window.ConfigServiceUiHelpers || {};
  var commentHelpers = window.ConfigServiceUiComments.create({
    state: state,
    saveDoc: saveDoc,
    renderAll: renderAll,
    isReadOnlyMode: isReadOnlyMode,
  });

  var SERVICE_OPTION_BY_KEY = {};
  var PARSER_FORMAT_BY_KEY = {};

  function rebuildServiceOptionIndex() {
    SERVICE_OPTION_BY_KEY = {};
    SERVICE_OPTIONS.forEach(function (opt) {
      SERVICE_OPTION_BY_KEY[opt.key] = opt;
    });
  }

  function rebuildParserFormatIndex() {
    PARSER_FORMAT_BY_KEY = {};
    PARSER_FORMATS.forEach(function (formatDef) {
      PARSER_FORMAT_BY_KEY[formatDef.key] = formatDef;
    });
  }

  rebuildServiceOptionIndex();
  rebuildParserFormatIndex();

  function applyCssOverrides() {
    var overrides = runtimeSettings.cssOverrides;
    if (!Array.isArray(overrides) || overrides.length === 0) {
      return;
    }
    overrides.forEach(function (href) {
      if (!href || typeof href !== "string") {
        return;
      }
      var link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      link.setAttribute("data-config-service-override", "true");
      document.head.appendChild(link);
    });
  }

  function saveAsEnabled() {
    return Boolean(runtimeSettings.showSaveAs === true);
  }

  // Cache DOM lookups once during startup.
  // We intentionally keep this flat so render/event code can reference
  // stable element handles without repeated selector queries.
  var el = {
    featureMenuGroup: document.getElementById("featureMenuGroup"),
    featureMenuSelect: document.getElementById("featureMenuSelect"),
    openFile: document.getElementById("open-file"),
    openFileDisplay: document.getElementById("open-file-display"),
    browseFile: document.getElementById("browse-file"),
    saveConfig: document.getElementById("save-config"),
    saveAsConfig: document.getElementById("save-as-config"),
    viewRawConfig: document.getElementById("view-raw-config"),
    newConfig: document.getElementById("new-config"),
    versionSelect: document.getElementById("version-select"),
    configTypeSelect: document.getElementById("config-type-select"),
    pluginSection: document.getElementById("plugin-section"),
    pluginName: document.getElementById("plugin-name"),
    pluginHelpToggle: document.getElementById("plugin-help-toggle"),
    addPlugin: document.getElementById("add-plugin"),
    pluginList: document.getElementById("plugin-list"),
    pluginsToggle: document.getElementById("plugins-toggle"),
    pluginsBody: document.getElementById("plugins-body"),
    labelsPanel: document.getElementById("labels-panel"),
    labelsToggle: document.getElementById("labels-toggle"),
    labelsBody: document.getElementById("labels-body"),
    labelList: document.getElementById("label-list"),
    addLabel: document.getElementById("add-label"),
    workersPanel: document.getElementById("workers-panel"),
    workersToggle: document.getElementById("workers-toggle"),
    workersBody: document.getElementById("workers-body"),
    workerList: document.getElementById("worker-list"),
    addWorker: document.getElementById("add-worker"),
    servicePanel: document.getElementById("service-panel"),
    serviceToggle: document.getElementById("service-toggle"),
    serviceBody: document.getElementById("service-body"),
    serviceList: document.getElementById("service-list"),
    serviceOption: document.getElementById("service-option"),
    serviceCustomKey: document.getElementById("service-custom-key"),
    serviceValue: document.getElementById("service-value"),
    serviceHelpToggle: document.getElementById("service-help-toggle"),
    addServiceField: document.getElementById("add-service-field"),
    serviceOptionMeta: document.getElementById("service-option-meta"),
    envPanel: document.getElementById("env-panel"),
    envToggle: document.getElementById("env-toggle"),
    envBody: document.getElementById("env-body"),
    envList: document.getElementById("env-list"),
    envKeyInput: document.getElementById("env-key-input"),
    envValueInput: document.getElementById("env-value-input"),
    addEnvField: document.getElementById("add-env-field"),
    metadataEnvPanel: document.getElementById("metadata-env-panel"),
    metadataEnvToggle: document.getElementById("metadata-env-toggle"),
    metadataEnvBody: document.getElementById("metadata-env-body"),
    metadataEnvList: document.getElementById("metadata-env-list"),
    metadataEnvHelpToggle: document.getElementById("metadata-env-help-toggle"),
    metadataEnvKeyInput: document.getElementById("metadata-env-key-input"),
    metadataEnvKeyOptions: document.getElementById("metadata-env-key-options"),
    metadataEnvValueInput: document.getElementById("metadata-env-value-input"),
    metadataEnvValueOptions: document.getElementById("metadata-env-value-options"),
    addMetadataEnvField: document.getElementById("add-metadata-env-field"),
    upstreamServersPanel: document.getElementById("upstream-servers-panel"),
    upstreamServersToggle: document.getElementById("upstream-servers-toggle"),
    upstreamServersBody: document.getElementById("upstream-servers-body"),
    upstreamServersList: document.getElementById("upstream-servers-list"),
    upstreamServersHelpToggle: document.getElementById("upstream-servers-help-toggle"),
    upstreamServersMeta: document.getElementById("upstream-servers-meta"),
    addUpstreamServerGroup: document.getElementById("add-upstream-server-group"),
    parsersPanel: document.getElementById("parsers-panel"),
    parsersToggle: document.getElementById("parsers-toggle"),
    parsersBody: document.getElementById("parsers-body"),
    parserList: document.getElementById("parser-list"),
    parserFormat: document.getElementById("parser-format"),
    parserNameInput: document.getElementById("parser-name-input"),
    parserHelpToggle: document.getElementById("parser-help-toggle"),
    addParser: document.getElementById("add-parser"),
    parserFormatMeta: document.getElementById("parser-format-meta"),
    addPluginPanel: document.getElementById("add-plugin-panel"),
    pluginsPanel: document.getElementById("plugins-panel"),
    dryRunBtn: document.getElementById("dry-run-btn"),
    validateBtn: document.getElementById("validate-btn"),
    renderBtn: document.getElementById("render-btn"),
    statusPanel: document.getElementById("status-panel"),
    statusTime: document.getElementById("status-time"),
    statusMessage: document.getElementById("status-message"),
    validationHeader: document.getElementById("validation-header"),
    validationCard: document.getElementById("validation-card"),
    validationIncludeToggle: document.getElementById("validation-include-toggle"),
    validationSaveToggle: document.getElementById("validation-save-toggle"),
    validationToggle: document.getElementById("validation-toggle"),
    validationBody: document.getElementById("validation-body"),
    validationSummary: document.getElementById("validation-summary"),
    validationIssues: document.getElementById("validation-issues"),
    renderIncludeToggle: document.getElementById("render-include-toggle"),
    yamlToggle: document.getElementById("yaml-toggle"),
    yamlBody: document.getElementById("yaml-body"),
    yamlOutput: document.getElementById("yaml-output"),
    renderCard: document.getElementById("render-card"),
    rawConfigDialog: document.getElementById("raw-config-dialog"),
    rawConfigText: document.getElementById("raw-config-text"),
    rawConfigClose: document.getElementById("raw-config-close"),
  };

  function setCookie(name, value) {
    // Session cookie: intentionally omit expires/max-age so persistence ends
    // when the browser session closes.
    document.cookie =
      name +
      "=" +
      encodeURIComponent(value) +
      "; path=/; SameSite=Lax";
  }

  function getCookie(name) {
    var prefix = name + "=";
    var parts = document.cookie.split(";");
    for (var partIndex = 0; partIndex < parts.length; partIndex += 1) {
      var part = parts[partIndex].trim();
      if (part.indexOf(prefix) === 0) {
        return decodeURIComponent(part.substring(prefix.length));
      }
    }
    return null;
  }

  function clearCookie(name) {
    document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax";
  }

  function emptyDoc(version, configType) {
    return {
      version: version,
      configType: configType || "fluentbit",
      config: {
        env: {},
        service: {},
        parsers: [],
        upstream_servers: [],
        pipeline: { inputs: [], filters: [], outputs: [] },
        labels: [],
        workers: [],
        includes: [],
      },
      annotations: {},
    };
  }

  function compareVersionStrings(left, right) {
    var leftParts = String(left || "").split(".").map(function (part) { return Number(part) || 0; });
    var rightParts = String(right || "").split(".").map(function (part) { return Number(part) || 0; });
    var length = Math.max(leftParts.length, rightParts.length);
    for (var index = 0; index < length; index += 1) {
      var diff = (leftParts[index] || 0) - (rightParts[index] || 0);
      if (diff !== 0) {
        return diff;
      }
    }
    return 0;
  }

  function resolvePreferredVersion(versions, preferredVersion, fallbackDefault) {
    var candidates = Array.isArray(versions) ? versions.slice() : [];
    if (candidates.length === 0) {
      return "";
    }
    candidates.sort(compareVersionStrings);
    if (preferredVersion) {
      if (candidates.indexOf(preferredVersion) !== -1) {
        return preferredVersion;
      }
      for (var index = 0; index < candidates.length; index += 1) {
        if (compareVersionStrings(candidates[index], preferredVersion) > 0) {
          return candidates[index];
        }
      }
      return candidates[candidates.length - 1];
    }
    if (fallbackDefault && candidates.indexOf(fallbackDefault) !== -1) {
      return fallbackDefault;
    }
    return candidates[0];
  }

  function clearOpenFileSelection() {
    if (el.openFile) {
      el.openFile.value = "";
    }
    state.currentFileDisplay = "";
    state.currentSourcePath = "";
    try {
      localStorage.removeItem(LAST_DOC_SOURCE_PATH_STORAGE);
    } catch (_err) {
      // Ignore storage failures and keep the in-memory state authoritative.
    }
    if (el.openFileDisplay) {
      el.openFileDisplay.value = "";
    }
  }

  function isReadOnlyMode() {
    return Boolean(state.readOnly);
  }

  function normalizeConfigType(rawValue, fallback) {
    var value = String(rawValue || "").trim().toLowerCase();
    if (!value) {
      return String(fallback || "fluentbit");
    }
    if (value === "fluentbit" || value === "fluent-bit" || value === "fluent_bit" || value === "fluent bit") {
      return "fluentbit";
    }
    if (value === "fluentd" || value === "fluent-d" || value === "fluent_d" || value === "fluent d") {
      return "fluentd";
    }
    return String(fallback || value);
  }

  function setOpenFileDisplay(value) {
    state.currentFileDisplay = String(value || "").trim();
    if (el.openFileDisplay) {
      el.openFileDisplay.value = state.currentFileDisplay;
    }
  }

  function currentRenderSignature() {
    if (!state.doc) {
      return "";
    }
    return JSON.stringify({
      configType: state.configType,
      version: state.doc.version || state.selectedVersion,
      config: state.doc.config,
    });
  }

  function updateRenderedDirtyState() {
    if (el.renderCard) {
      el.renderCard.classList.toggle("is-stale", Boolean(state.renderDirty && el.yamlOutput.textContent));
    }
    if (el.yamlOutput) {
      el.yamlOutput.style.color = state.renderDirty ? "#ffd24d" : "#e5ebff";
    }
  }

  function updateDryRunButtonVisibility() {
    if (!el.dryRunBtn) {
      return;
    }
    var show = Boolean(state.dryRunAvailable && state.doc && state.selectedVersion);
    el.dryRunBtn.classList.toggle("hidden", !show);
    if (!show) {
      el.dryRunBtn.title = "";
      return;
    }
    var capability = state.dryRunCapability || {};
    if (capability.version_mismatch && capability.used_agent_version) {
      el.dryRunBtn.title =
        "Dry run uses configured validator version " + capability.used_agent_version + ".";
    } else {
      el.dryRunBtn.title = "Run external agent dry-run validation.";
    }
  }

  function loadDryRunAvailability() {
    if (!el.dryRunBtn) {
      return Promise.resolve(null);
    }
    var selectedVersion = String((state.doc && state.doc.version) || state.selectedVersion || "").trim();
    if (!selectedVersion) {
      state.dryRunAvailable = false;
      state.dryRunCapability = null;
      updateDryRunButtonVisibility();
      return Promise.resolve(null);
    }
    var requestSerial = dryRunAvailabilityRequestSerial + 1;
    dryRunAvailabilityRequestSerial = requestSerial;
    el.dryRunBtn.disabled = true;
    return api.getDryRunAvailability(selectedVersion, state.configType)
      .then(function (payload) {
        if (requestSerial !== dryRunAvailabilityRequestSerial) {
          return payload;
        }
        state.dryRunCapability = payload || {};
        state.dryRunAvailable = Boolean(payload && payload.available);
        updateDryRunButtonVisibility();
        return payload;
      })
      .catch(function (err) {
        if (requestSerial !== dryRunAvailabilityRequestSerial) {
          return null;
        }
        state.dryRunAvailable = false;
        state.dryRunCapability = { available: false, reason: String(err) };
        updateDryRunButtonVisibility();
        return null;
      })
      .finally(function () {
        if (requestSerial !== dryRunAvailabilityRequestSerial || !el.dryRunBtn) {
          return;
        }
        el.dryRunBtn.disabled = isReadOnlyMode() || !state.dryRunAvailable;
      });
  }

  function updateReadOnlyState() {
    var readOnly = isReadOnlyMode();
    el.newConfig.disabled = readOnly;
    el.saveConfig.disabled = readOnly;
    el.saveAsConfig.disabled = readOnly;
    el.saveAsConfig.hidden = !saveAsEnabled();
    el.configTypeSelect.disabled = readOnly || hasConfiguredContent();
    el.versionSelect.disabled = readOnly || !Array.isArray(state.versions) || state.versions.length === 0;
    el.addServiceField.disabled = readOnly;
    el.serviceOption.disabled = readOnly;
    el.serviceCustomKey.disabled = readOnly;
    el.serviceValue.disabled = readOnly;
    el.addParser.disabled = readOnly;
    el.parserFormat.disabled = readOnly;
    el.parserNameInput.disabled = readOnly;
    el.addPlugin.disabled = readOnly || !(state.catalog && el.pluginName && el.pluginName.value);
    el.pluginSection.disabled = readOnly;
    el.pluginName.disabled = readOnly;
    el.addLabel.disabled = readOnly;
    el.addWorker.disabled = readOnly;
    if (el.envKeyInput) {
      el.envKeyInput.disabled = readOnly;
    }
    if (el.envValueInput) {
      el.envValueInput.disabled = readOnly;
    }
    if (el.addEnvField) {
      el.addEnvField.disabled = readOnly;
    }
    if (el.metadataEnvKeyInput) {
      el.metadataEnvKeyInput.disabled = readOnly;
    }
    if (el.metadataEnvValueInput) {
      el.metadataEnvValueInput.disabled = readOnly;
    }
    if (el.addMetadataEnvField) {
      el.addMetadataEnvField.disabled = readOnly;
    }
    if (el.addUpstreamServerGroup) {
      el.addUpstreamServerGroup.disabled = readOnly;
    }
    if (el.validationIncludeToggle) {
      el.validationIncludeToggle.disabled = false;
    }
    if (el.validationSaveToggle) {
      el.validationSaveToggle.disabled = readOnly;
    }
    if (el.renderIncludeToggle) {
      el.renderIncludeToggle.disabled = false;
    }
    if (el.parserHelpToggle) {
      var parserFormat = selectedParserFormatDefinition();
      el.parserHelpToggle.disabled = !(parserFormat && parserFormat.doc_url);
    }
    Array.prototype.forEach.call(
      document.querySelectorAll(
        ".plugin-card input, .plugin-card select, .plugin-card textarea, " +
          ".nested-panel input, .nested-panel select, .nested-panel textarea, " +
          ".plugin-card button, .nested-panel button, .comment-editor textarea"
      ),
      function (node) {
        if (!node || !node.id) {
          // continue
        }
        var allowAction = node.id === "validation-toggle" ||
          node.id === "yaml-toggle" ||
          node.id === "dry-run-btn" ||
          node.id === "validate-btn" ||
          node.id === "render-btn";
        if (allowAction) {
          return;
        }
        if (node.classList && (node.classList.contains("icon-help") || node.textContent === "Collapse" || node.textContent === "Expand")) {
          node.disabled = false;
          return;
        }
        node.disabled = readOnly;
      }
    );
    if (el.dryRunBtn) {
      el.dryRunBtn.disabled = readOnly || !state.dryRunAvailable;
    }
  }

  function normalizeIssuePath(path) {
    var text = String(path || "").trim();
    if (!text) {
      return "$";
    }
    if (text === "$.config") {
      return "$";
    }
    if (text.indexOf("$.config.") === 0) {
      return "$." + text.substring("$.config.".length);
    }
    return text;
  }

  function lookupIssueSourceLine(path) {
    var normalized = normalizeIssuePath(path);
    var map = state.sourceLineMap || {};
    if (Object.prototype.hasOwnProperty.call(map, normalized)) {
      return map[normalized];
    }
    var candidate = normalized;
    while (candidate && candidate !== "$") {
      if (Object.prototype.hasOwnProperty.call(map, candidate)) {
        return map[candidate];
      }
      if (/\[[0-9]+\]$/.test(candidate)) {
        candidate = candidate.replace(/\[[0-9]+\]$/, "");
        continue;
      }
      candidate = candidate.replace(/(?:\[[0-9]+\])?\.[^.[]+$/, "");
      if (!candidate) {
        break;
      }
      if (candidate === "") {
        candidate = "$";
      }
    }
    return null;
  }

  function prependConfigHeader(text, configType, version, commentPrefix) {
    return uiHelpers.prependConfigHeader(text, configType, version, commentPrefix);
  }

  function pluginGroups() {
    if (!state.catalog || !state.catalog.plugins) {
      return { inputs: {}, filters: {}, outputs: {} };
    }
    return state.catalog.plugins;
  }

  function isFluentdMode() {
    return state.configType === "fluentd";
  }

  function defaultForField(field) {
    return uiHelpers.defaultForField(field);
  }

  function getEnumOptions(field) {
    return uiHelpers.getEnumOptions(field);
  }

  function normalizeEnumAliasValue(enumOptions, value) {
    return uiHelpers.normalizeEnumAliasValue(enumOptions, value);
  }

  function replaceServiceValueControl(tagName) {
    var current = el.serviceValue;
    if (current && current.tagName && current.tagName.toLowerCase() === tagName.toLowerCase()) {
      return current;
    }
    var replacement = document.createElement(tagName);
    replacement.id = "service-value";
    replacement.className = current.className || "";
    replacement.placeholder = current.placeholder || "";
    replacement.value = current.value || "";
    current.parentNode.replaceChild(replacement, current);
    el.serviceValue = replacement;
    return replacement;
  }

  function ensureDoc() {
    // Normalize and migrate older document shapes into the current in-memory
    // contract expected by render/save/validate logic.
    if (!state.doc) {
      state.doc = emptyDoc(state.selectedVersion, state.configType);
    }
    state.configType = normalizeConfigType(state.configType, "fluentbit");
    state.doc.configType = normalizeConfigType(state.doc.configType || state.configType, state.configType);
    if (!state.doc.config || typeof state.doc.config !== "object") {
      state.doc.config = {};
    }
    if (state.doc.pipeline && (!state.doc.config.pipeline || typeof state.doc.config.pipeline !== "object")) {
      state.doc.config.pipeline = state.doc.pipeline;
    }
    if (
      !state.doc.config.pipeline &&
      (
        Array.isArray(state.doc.config.inputs) ||
        Array.isArray(state.doc.config.filters) ||
        Array.isArray(state.doc.config.outputs)
      )
    ) {
      state.doc.config.pipeline = {
        inputs: Array.isArray(state.doc.config.inputs) ? state.doc.config.inputs : [],
        filters: Array.isArray(state.doc.config.filters) ? state.doc.config.filters : [],
        outputs: Array.isArray(state.doc.config.outputs) ? state.doc.config.outputs : [],
      };
      delete state.doc.config.inputs;
      delete state.doc.config.filters;
      delete state.doc.config.outputs;
    }
    if (
      state.doc.config.plugins &&
      typeof state.doc.config.plugins === "object" &&
      !state.doc.config.pipeline
    ) {
      state.doc.config.pipeline = {
        inputs: Array.isArray(state.doc.config.plugins.inputs) ? state.doc.config.plugins.inputs : [],
        filters: Array.isArray(state.doc.config.plugins.filters) ? state.doc.config.plugins.filters : [],
        outputs: Array.isArray(state.doc.config.plugins.outputs) ? state.doc.config.plugins.outputs : [],
      };
    }
    if (!state.doc.annotations || typeof state.doc.annotations !== "object") {
      state.doc.annotations = {};
    }
    if (!state.doc.config.service || typeof state.doc.config.service !== "object") {
      state.doc.config.service = {};
    }
    if (!state.doc.config.env || typeof state.doc.config.env !== "object" || Array.isArray(state.doc.config.env)) {
      state.doc.config.env = {};
    }
    if (!Array.isArray(state.doc.config.parsers)) {
      state.doc.config.parsers = [];
    }
    if (!Array.isArray(state.doc.config.upstream_servers)) {
      state.doc.config.upstream_servers = [];
    }
    state.doc.config.upstream_servers.forEach(function (group) {
      if (!group || typeof group !== "object") {
        return;
      }
      if (!Array.isArray(group.nodes)) {
        group.nodes = [];
      }
    });
    if (!state.doc.config.pipeline || typeof state.doc.config.pipeline !== "object") {
      state.doc.config.pipeline = {};
    }
    if (!Array.isArray(state.doc.config.labels)) {
      state.doc.config.labels = [];
    }
    if (!Array.isArray(state.doc.config.workers)) {
      state.doc.config.workers = [];
    }
    if (!Array.isArray(state.doc.config.includes)) {
      state.doc.config.includes = [];
    }
    ["inputs", "filters", "outputs"].forEach(function (section) {
      if (!Array.isArray(state.doc.config.pipeline[section])) {
        state.doc.config.pipeline[section] = [];
      }
      state.doc.config.pipeline[section].forEach(function (instance) {
        if (
          section === "inputs" &&
          instance &&
          typeof instance === "object" &&
          instance.routes &&
          !instance.route
        ) {
          instance.route = instance.routes;
          delete instance.routes;
        }
      });
    });
    migrateLegacyAnnotationsToMeta();
  }

  function ensureMetaBlock(target) {
    return commentHelpers.ensureMetaBlock(target);
  }

  function ensureFieldCommentMap(target) {
    return commentHelpers.ensureFieldCommentMap(target);
  }

  function commentLinesToText(lines) {
    return commentHelpers.commentLinesToText(lines);
  }

  function textToCommentLines(value) {
    return commentHelpers.textToCommentLines(value);
  }

  function objectCommentText(target) {
    return commentHelpers.objectCommentText(target);
  }

  function setObjectCommentText(target, value) {
    commentHelpers.setObjectCommentText(target, value);
  }

  function fieldCommentText(target, fieldName) {
    return commentHelpers.fieldCommentText(target, fieldName);
  }

  function setFieldCommentText(target, fieldName, value) {
    commentHelpers.setFieldCommentText(target, fieldName, value);
  }

  function renameFieldComment(target, oldFieldName, newFieldName) {
    commentHelpers.renameFieldComment(target, oldFieldName, newFieldName);
  }

  function clearFieldComment(target, fieldName) {
    commentHelpers.clearFieldComment(target, fieldName);
  }

  function tokenizeLegacyCommentPath(path) {
    return commentHelpers.tokenizeLegacyCommentPath(path);
  }

  function migrateLegacyAnnotationsToMeta() {
    commentHelpers.migrateLegacyAnnotationsToMeta();
  }

  function createCommentEditor(target, labelText, fieldName) {
    return commentHelpers.createCommentEditor(target, labelText, fieldName);
  }

  function hasCommentText(target, fieldName) {
    return commentHelpers.hasCommentText(target, fieldName);
  }

  function isCommentEditorOpen(toggleKey, target, fieldName) {
    return commentHelpers.isCommentEditorOpen(toggleKey, target, fieldName);
  }

  function setCommentEditorOpen(toggleKey, isOpen) {
    commentHelpers.setCommentEditorOpen(toggleKey, isOpen);
  }

  function createCommentToggleButton(toggleKey, target, fieldName, labelText) {
    return commentHelpers.createCommentToggleButton(toggleKey, target, fieldName, labelText);
  }

  function createCommentEditorPanel(target, labelText, fieldName, toggleKey) {
    return commentHelpers.createCommentEditorPanel(target, labelText, fieldName, toggleKey);
  }

  function todaysIsoDate() {
    return new Date().toISOString().slice(0, 10);
  }

  function refreshConfigurationDateMetadata() {
    if (!state.doc || !state.doc.config || !state.doc.config.env || typeof state.doc.config.env !== "object") {
      return false;
    }
    var metadataDateKey = "_metadata.configuration_date";
    if (!Object.prototype.hasOwnProperty.call(state.doc.config.env, metadataDateKey)) {
      return false;
    }
    var today = todaysIsoDate();
    if (state.doc.config.env[metadataDateKey] === today) {
      return false;
    }
    state.doc.config.env[metadataDateKey] = today;
    return true;
  }

  function saveDoc() {
    if (!state.doc) {
      return;
    }
    refreshConfigurationDateMetadata();
    localStorage.setItem(LAST_DOC_STORAGE, JSON.stringify(state.doc));
    if (state.currentSourcePath) {
      localStorage.setItem(LAST_DOC_SOURCE_PATH_STORAGE, state.currentSourcePath);
    } else {
      localStorage.removeItem(LAST_DOC_SOURCE_PATH_STORAGE);
    }
    if (state.preserveSourceLineMapOnce) {
      state.preserveSourceLineMapOnce = false;
    } else {
      state.sourceLineMap = {};
    }
    markValidationDirtyOnEdit();
    if (state.lastRenderedSignature && state.lastRenderedSignature !== currentRenderSignature()) {
      state.renderDirty = true;
      updateRenderedDirtyState();
    }
    updateConfigTypeDisabledState();
  }

  function markValidationDirtyOnEdit() {
    if (state.validationStatus === "neutral") {
      return;
    }
    state.validationStatus = "neutral";
    renderValidationState(null);
  }

  function renderValidationState(result) {
    // Convert backend validation payload into user-facing summary + issue list.
    var errors = (result && Array.isArray(result.errors)) ? result.errors.slice() : [];
    errors.sort(function (leftIssue, rightIssue) {
      return Number((leftIssue && leftIssue.order) || 0) - Number((rightIssue && rightIssue.order) || 0);
    });
    var hasBlockingErrors = errors.some(function (issue) {
      return String((issue && issue.severity) || "error").toLowerCase() === "error";
    });
    var hasWarnings = errors.some(function (issue) {
      return String((issue && issue.severity) || "").toLowerCase() === "warning";
    });
    var hasIssues = errors.length > 0 || (result && result.ok === false);
    var isValid = Boolean(result && result.ok === true && errors.length === 0);

    el.validationHeader.classList.remove("is-valid", "is-warning", "has-errors");
    el.validationSummary.classList.remove("is-valid", "is-warning", "has-errors");
    el.validationIssues.innerHTML = "";

    if (isValid) {
      state.validationStatus = "valid";
      el.validationHeader.classList.add("is-valid");
      el.validationSummary.classList.add("is-valid");
      el.validationSummary.textContent = "Configuration is valid.";
      state.validationCollapsed = false;
    } else if (hasBlockingErrors) {
      state.validationStatus = "error";
      el.validationHeader.classList.add("has-errors");
      el.validationSummary.classList.add("has-errors");
      el.validationSummary.textContent = errors.length > 0
        ? "Validation found " + errors.length + " error" + (errors.length === 1 ? "" : "s") + "."
        : "Validation failed.";
      state.validationCollapsed = false;
    } else if (hasWarnings) {
      state.validationStatus = "warning";
      el.validationHeader.classList.add("is-warning");
      el.validationSummary.classList.add("is-warning");
      el.validationSummary.textContent = "Validation found " + errors.length + " warning" + (errors.length === 1 ? "" : "s") + ".";
      state.validationCollapsed = false;
    } else if (hasIssues) {
      state.validationStatus = "error";
      el.validationHeader.classList.add("has-errors");
      el.validationSummary.classList.add("has-errors");
      el.validationSummary.textContent = errors.length > 0
        ? "Validation found " + errors.length + " issue" + (errors.length === 1 ? "" : "s") + "."
        : "Validation failed.";
      state.validationCollapsed = false;
    }

    if (hasIssues) {
      errors.forEach(function (issue, idx) {
        var item = document.createElement("li");
        var severity = String((issue && issue.severity) || "error").toLowerCase();
        item.classList.add("severity-" + severity);
        var code = String((issue && issue.code) || "unknown_issue");
        var mapping = state.issueCodeMap[code] || state.issueCodeMap.unknown_issue || null;
        var friendlyLabel = mapping && mapping.label ? mapping.label : code;
        var messageText = issue && issue.message
          ? issue.message
          : "Validation error #" + (idx + 1);
        var detailBits = [];
        if (issue && issue.path) {
          detailBits.push("Path: " + issue.path);
        }
        var sourceLine = issue && issue.line ? issue.line : lookupIssueSourceLine(issue && issue.path);
        if (sourceLine) {
          detailBits.push("Line: " + sourceLine);
        }
        if (issue && issue.severity) {
          detailBits.push("Severity: " + issue.severity);
        }
        if (issue && issue.source) {
          detailBits.push("Source: " + issue.source);
        }
        item.textContent =
          friendlyLabel +
          ": " +
          messageText +
          (detailBits.length > 0 ? " (" + detailBits.join(" | ") + ")" : "");

        el.validationIssues.appendChild(item);
      });
    } else {
      state.validationStatus = "neutral";
      el.validationSummary.textContent = "Run validation to inspect the current configuration.";
      state.validationCollapsed = false;
    }

    updateResultPanels();
  }

  function formatStatusTimestamp() {
    return new Date().toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "medium",
    });
  }

  function setValidationText(text) {
    renderValidationState({
      ok: false,
      errors: [
        {
          message: String(text || "Validation failed."),
          path: "$",
          code: "ui_message",
          severity: "error",
          source: "ui",
        },
      ],
    });
  }

  function setStatusMessage(text) {
    var message = String(text || "").trim();
    if (!message) {
      el.statusTime.textContent = "";
      el.statusMessage.textContent = "";
      el.statusPanel.classList.add("hidden");
      return;
    }
    el.statusTime.textContent = formatStatusTimestamp();
    el.statusMessage.textContent = message;
    el.statusPanel.classList.remove("hidden");
  }

  function setYamlText(text, markFresh) {
    el.yamlOutput.textContent = text || "";
    if (markFresh === true) {
      state.lastRenderedSignature = currentRenderSignature();
      state.renderDirty = false;
    }
    updateRenderedDirtyState();
    updateResultPanels();
  }

  function updateResultPanels() {
    el.validationBody.classList.toggle("is-collapsed", state.validationCollapsed);
    el.validationToggle.textContent = state.validationCollapsed ? "Open" : "Collapse";
    el.yamlBody.classList.toggle("is-collapsed", state.yamlCollapsed);
    el.yamlToggle.textContent = state.yamlCollapsed ? "Open" : "Collapse";
  }

  function updateSectionPanels() {
    // Keep panel collapsed/open CSS and toggle labels synchronized with state.
    if (el.serviceBody && el.serviceToggle) {
      el.serviceBody.classList.toggle("is-collapsed", state.servicePanelCollapsed);
      el.serviceToggle.textContent = state.servicePanelCollapsed ? "Open" : "Collapse";
    }
    if (el.envBody && el.envToggle) {
      el.envBody.classList.toggle("is-collapsed", state.envPanelCollapsed);
      el.envToggle.textContent = state.envPanelCollapsed ? "Open" : "Collapse";
    }
    if (el.metadataEnvBody && el.metadataEnvToggle) {
      el.metadataEnvBody.classList.toggle("is-collapsed", state.metadataPanelCollapsed);
      el.metadataEnvToggle.textContent = state.metadataPanelCollapsed ? "Open" : "Collapse";
    }
    if (el.upstreamServersBody && el.upstreamServersToggle) {
      el.upstreamServersBody.classList.toggle("is-collapsed", state.upstreamServersPanelCollapsed);
      el.upstreamServersToggle.textContent = state.upstreamServersPanelCollapsed ? "Open" : "Collapse";
    }
    if (el.parsersBody && el.parsersToggle) {
      el.parsersBody.classList.toggle("is-collapsed", state.parsersPanelCollapsed);
      el.parsersToggle.textContent = state.parsersPanelCollapsed ? "Open" : "Collapse";
    }
    if (el.pluginsBody && el.pluginsToggle) {
      el.pluginsBody.classList.toggle("is-collapsed", state.pluginsPanelCollapsed);
      el.pluginsToggle.textContent = state.pluginsPanelCollapsed ? "Open" : "Collapse";
    }
    if (el.labelsBody && el.labelsToggle) {
      el.labelsBody.classList.toggle("is-collapsed", state.labelsPanelCollapsed);
      el.labelsToggle.textContent = state.labelsPanelCollapsed ? "Open" : "Collapse";
    }
    if (el.workersBody && el.workersToggle) {
      el.workersBody.classList.toggle("is-collapsed", state.workersPanelCollapsed);
      el.workersToggle.textContent = state.workersPanelCollapsed ? "Open" : "Collapse";
    }
  }

  function repopulatePluginNameSelect() {
    var groups = pluginGroups();
    var map = groups[state.pluginSection] || {};
    var names = Object.keys(map).sort();
    el.pluginName.innerHTML = "";
    names.forEach(function (name) {
      var opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      el.pluginName.appendChild(opt);
    });
    state.pluginName = names[0] || "";
    el.pluginName.value = state.pluginName;
    updatePluginHelpState();
    updateAddPluginState();
  }

  function repopulateVersions() {
    el.versionSelect.innerHTML = "";
    if (!Array.isArray(state.versions) || state.versions.length === 0) {
      var emptyOption = document.createElement("option");
      emptyOption.value = "";
      emptyOption.textContent = "No versions available";
      el.versionSelect.appendChild(emptyOption);
      el.versionSelect.value = "";
      el.versionSelect.disabled = true;
      return;
    }
    state.versions.forEach(function (versionValue) {
      var opt = document.createElement("option");
      opt.value = versionValue;
      opt.textContent = versionValue;
      el.versionSelect.appendChild(opt);
    });
    el.versionSelect.disabled = isReadOnlyMode() ? true : false;
    el.versionSelect.value = state.selectedVersion;
  }

  function loadVersionsForType(configType, preferredVersion) {
    var normalizedType = normalizeConfigType(configType, "fluentbit");
    return api.getVersions(normalizedType).then(function (data) {
      var versions = Array.isArray(data.versions) ? data.versions.slice() : [];
      state.versions = versions;
      var currentPreferred = preferredVersion || state.selectedVersion || "";
      state.selectedVersion = resolvePreferredVersion(versions, currentPreferred, data.default || "");
      state.configType = normalizeConfigType(data.config_type, normalizedType);

      if (state.doc) {
        state.doc.version = state.selectedVersion;
        state.doc.configType = state.configType;
      }

      repopulateVersions();
      updateFluentdSectionVisibility();
      return loadDryRunAvailability().then(function () {
        return {
          versions: versions,
          defaultVersion: data.default || "",
        };
      });
    });
  }

  function selectedServiceOption() {
    var selectedKey = String(el.serviceOption.value || "");
    return SERVICE_OPTION_BY_KEY[selectedKey] || null;
  }

  function selectedParserFormatDefinition() {
    var selectedKey = String((el.parserFormat && el.parserFormat.value) || "");
    return PARSER_FORMAT_BY_KEY[selectedKey] || null;
  }

  function repopulateServiceOptionSelect() {
    el.serviceOption.innerHTML = "";
    SERVICE_OPTIONS.forEach(function (opt) {
      var option = document.createElement("option");
      option.value = opt.key;
      option.textContent = opt.key;
      el.serviceOption.appendChild(option);
    });
    var customOpt = document.createElement("option");
    customOpt.value = CUSTOM_SERVICE_OPTION;
    customOpt.textContent = "custom...";
    el.serviceOption.appendChild(customOpt);
    el.serviceOption.value = SERVICE_OPTIONS[0] ? SERVICE_OPTIONS[0].key : CUSTOM_SERVICE_OPTION;
    updateServiceOptionUI();
  }

  function repopulateParserFormatSelect() {
    if (!el.parserFormat) {
      return;
    }
    el.parserFormat.innerHTML = "";
    PARSER_FORMATS.forEach(function (formatDef) {
      var option = document.createElement("option");
      option.value = formatDef.key;
      option.textContent = formatDef.key;
      el.parserFormat.appendChild(option);
    });
    updateParserFormatUI();
  }

  function updateServiceOptionUI() {
    var opt = selectedServiceOption();
    var isCustom = el.serviceOption.value === CUSTOM_SERVICE_OPTION;
    if (el.serviceCustomKey && el.serviceCustomKey.parentElement) {
      el.serviceCustomKey.parentElement.classList.toggle("hidden", !isCustom);
    }
    if (opt) {
      var enumOptions = getEnumOptions(opt);
      if (String(opt.data_type || "").toLowerCase() === "enum" && enumOptions.length > 0) {
        var select = replaceServiceValueControl("select");
        select.innerHTML = "";
        enumOptions.forEach(function (value) {
          var option = document.createElement("option");
          option.value = String(value);
          option.textContent = String(value);
          select.appendChild(option);
        });
        select.value = String(
          normalizeEnumAliasValue(
            enumOptions,
            Object.prototype.hasOwnProperty.call(opt, "default") && opt.default !== ""
              ? opt.default
              : enumOptions[0]
          )
        );
        select.disabled = isReadOnlyMode();
      } else if (String(opt.data_type || "").toLowerCase() === "code") {
        var codeInput = replaceServiceValueControl("textarea");
        codeInput.placeholder = String(opt.default || "");
        codeInput.value = "";
        prepareCodeTextarea(codeInput);
        codeInput.disabled = isReadOnlyMode();
      } else {
        var input = replaceServiceValueControl("input");
        input.type = "text";
        input.placeholder = String(opt.default);
        input.value = "";
        input.disabled = isReadOnlyMode();
      }
      el.serviceOptionMeta.innerHTML = opt.reference
        ? opt.description +
          " " +
          '<a href=\"' +
          opt.reference +
          '\" target=\"_blank\" rel=\"noreferrer\">reference</a>'
        : opt.description;
      el.serviceHelpToggle.disabled = false;
      el.serviceHelpToggle.title = opt.key + ": " + opt.description;
    } else {
      var customInput = replaceServiceValueControl("input");
      customInput.type = "text";
      customInput.placeholder = "value";
      customInput.value = "";
      customInput.disabled = isReadOnlyMode();
      el.serviceOptionMeta.textContent = "Define a custom service key and value.";
      el.serviceHelpToggle.disabled = isCustom;
      el.serviceHelpToggle.title = isCustom
        ? "Custom keys do not have linked Fluent Bit documentation."
        : "Select a service option to view help.";
    }
  }

  function updateParserFormatUI() {
    var formatDef = selectedParserFormatDefinition();
    if (!formatDef) {
      el.parserFormatMeta.textContent = "No parser formats available for this version.";
      el.parserHelpToggle.disabled = true;
      el.parserHelpToggle.title = "No parser format documentation is available.";
      return;
    }
    el.parserFormatMeta.textContent = formatDef.description || "";
    el.parserHelpToggle.disabled = !formatDef.doc_url;
    el.parserHelpToggle.title = formatDef.key + ": " + String(formatDef.description || "Open parser format documentation.");
  }

  function parseTextValue(raw, dataType) {
    return uiHelpers.parseTextValue(raw, dataType);
  }

  function maxCodeEditorHeight() {
    var viewport = window.innerHeight || 800;
    return Math.max(180, viewport - 260);
  }

  function resizeCodeTextarea(textarea) {
    if (!textarea) {
      return;
    }
    textarea.style.height = "auto";
    textarea.style.height = String(Math.max(140, Math.min(textarea.scrollHeight, maxCodeEditorHeight()))) + "px";
  }

  function prepareCodeTextarea(textarea) {
    if (!textarea) {
      return;
    }
    textarea.classList.add("code-input");
    textarea.setAttribute("spellcheck", "false");
    textarea.setAttribute("wrap", "off");
    textarea.style.maxHeight = String(maxCodeEditorHeight()) + "px";
    resizeCodeTextarea(textarea);
    if (textarea.dataset.codeResizeBound !== "true") {
      textarea.addEventListener("input", function () {
        resizeCodeTextarea(textarea);
      });
      textarea.dataset.codeResizeBound = "true";
    }
  }

  function parseServiceValue(raw) {
    return uiHelpers.parseServiceValue(raw);
  }

  function parseServiceValueByType(raw, dataType) {
    return uiHelpers.parseServiceValueByType(raw, dataType);
  }

  function fieldInputValue(value, dataType) {
    return uiHelpers.fieldInputValue(value, dataType);
  }

  function parseFlexibleRouteValue(raw) {
    return uiHelpers.parseFlexibleRouteValue(raw);
  }

  function formatFlexibleRouteValue(value) {
    return uiHelpers.formatFlexibleRouteValue(value);
  }

  function flattenPlugins() {
    ensureDoc();
    var out = [];
    ["inputs", "filters", "outputs"].forEach(function (section) {
      state.doc.config.pipeline[section].forEach(function (instance, index) {
        out.push({ section: section, index: index, instance: instance });
      });
    });
    return out;
  }

  function flattenPipeline(pipeline, prefix) {
    var out = [];
    if (!pipeline || typeof pipeline !== "object") {
      return out;
    }
    ["inputs", "filters", "outputs"].forEach(function (section) {
      var list = Array.isArray(pipeline[section]) ? pipeline[section] : [];
      list.forEach(function (instance, index) {
        out.push({
          section: section,
          index: index,
          instance: instance,
          prefix: prefix || "main",
          pipeline: pipeline,
        });
      });
    });
    return out;
  }

  function hasConfiguredContent() {
    ensureDoc();
    var serviceCount = Object.keys(state.doc.config.service || {}).filter(function (key) {
      return key !== "_meta";
    }).length;
    var parserCount = Array.isArray(state.doc.config.parsers) ? state.doc.config.parsers.length : 0;
    var upstreamGroupCount = Array.isArray(state.doc.config.upstream_servers) ? state.doc.config.upstream_servers.length : 0;
    var pluginCount = flattenPlugins().length;
    var labelCount = Array.isArray(state.doc.config.labels) ? state.doc.config.labels.length : 0;
    var workerCount = Array.isArray(state.doc.config.workers) ? state.doc.config.workers.length : 0;
    return serviceCount > 0 || parserCount > 0 || upstreamGroupCount > 0 || pluginCount > 0 || labelCount > 0 || workerCount > 0;
  }

  function updateConfigTypeDisabledState() {
    el.configTypeSelect.disabled = isReadOnlyMode() || hasConfiguredContent();
  }

  function defaultSaveFileName() {
    var base = state.currentFileName || getCookie(LAST_FILE_COOKIE) || "";
    if (base && !/^new-\d+$/i.test(base)) {
      if (state.configType === "fluentd") {
        return /\.conf$/i.test(base) ? base : base.replace(/\.[^.]+$/, "") + ".conf";
      }
      if (/\.ya?ml$/i.test(base)) {
        return base;
      }
      return /\.[^.]+$/.test(base) ? base.replace(/\.[^.]+$/, "") + ".yaml" : base + ".yaml";
    }
    var version = String((state.doc && state.doc.version) || state.selectedVersion || "config").replace(/[^\w.-]+/g, "-");
    var configType = String((state.doc && state.doc.configType) || state.configType || "fluentbit").replace(/[^\w.-]+/g, "-");
    return "config-service-" + configType + "-" + version + (state.configType === "fluentd" ? ".conf" : ".yaml");
  }

  function downloadBlob(fileName, blob) {
    var url = window.URL.createObjectURL(blob);
    var anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = fileName;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    window.URL.revokeObjectURL(url);
  }

  function shouldPromptForSaveLocation() {
    var name = String(state.currentFileName || "").trim();
    if (!name) {
      return true;
    }
    return /^new-\d+$/i.test(name);
  }

  function pickerTypesForCurrentConfig() {
    if (state.configType === "fluentd") {
      return [
        {
          description: "Fluentd configuration",
          accept: {
            "text/plain": [".conf"],
          },
        },
      ];
    }
    return [
      {
        description: "Fluent Bit configuration",
        accept: {
          "text/yaml": [".yaml", ".yml"],
        },
      },
    ];
  }

  function buildSaveBlob() {
    if (state.configType === "fluentd") {
      return api.renderFluentd(state.doc.version, {
        config: state.doc.config,
        annotations: state.doc.annotations || {},
        include_config_header: true,
      }).then(function (result) {
        var renderedText = String(result.rendered_output || result.text || "");
        return {
          blob: new Blob([renderedText], { type: "text/plain" }),
          text: renderedText,
        };
      });
    }
    return api.renderYaml(state.doc.version, state.configType, {
      config: state.doc.config,
      annotations: state.doc.annotations || {},
      included_documents: state.includedDocuments || [],
      include_comments: true,
      render_included_files: false,
      include_config_header: true,
    }).then(function (result) {
      var renderedText = String(result.rendered_output || result.yaml || "");
      return {
        blob: new Blob([renderedText], { type: "text/yaml" }),
        text: renderedText,
      };
    });
  }

  function writeToSaveHandle(handle, blob) {
    return handle.createWritable().then(function (writable) {
      return writable.write(blob).then(function () {
        return writable.close();
      });
    });
  }

  function reportBrowserSaveMechanism(mode, fileName) {
    api.reportUiError({
      kind: "browser_save_mechanism_used",
      source: "config_service_ui_save",
      message: "Browser save mechanism used via " + String(mode || "unknown") + " for " + String(fileName || "config"),
      path: window.location.href,
    });
  }

  function openRawConfigDialog(text) {
    if (!el.rawConfigDialog || !el.rawConfigText || !el.rawConfigClose) {
      return;
    }
    el.rawConfigText.value = String(text || "");
    el.rawConfigDialog.classList.remove("hidden");
    el.rawConfigClose.focus();
  }

  function closeRawConfigDialog() {
    if (!el.rawConfigDialog || !el.rawConfigText) {
      return;
    }
    el.rawConfigDialog.classList.add("hidden");
    el.rawConfigText.value = "";
  }

  function triggerRawConfigView() {
    if (!state.doc) {
      setStatusMessage("Load or create a configuration before viewing raw text.");
      return;
    }
    buildSaveBlob()
      .then(function (result) {
        openRawConfigDialog(String((result && result.text) || ""));
      })
      .catch(function (err) {
        setStatusMessage("Raw configuration view failed.");
        setValidationText(String(err));
      });
  }

  function renderFeatureMenuItems(items) {
    if (!el.featureMenuGroup || !el.featureMenuSelect) {
      return;
    }
    var list = Array.isArray(items) ? items : [];
    el.featureMenuSelect.innerHTML = "";
    var placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Open...";
    el.featureMenuSelect.appendChild(placeholder);

    list.forEach(function (item) {
      var label = String(item && item.label ? item.label : "").trim();
      var url = String(item && item.url ? item.url : "").trim();
      var target = String(item && item.target ? item.target : "_self").trim() || "_self";
      if (!label || !url) {
        return;
      }
      var option = document.createElement("option");
      option.value = url;
      option.textContent = label;
      option.dataset.target = target;
      el.featureMenuSelect.appendChild(option);
    });

    var hasItems = el.featureMenuSelect.options.length > 1;
    el.featureMenuGroup.classList.toggle("hidden", !hasItems);
    el.featureMenuSelect.selectedIndex = 0;
  }

  function fetchUiFeatureMenu() {
    if (!el.featureMenuGroup || !el.featureMenuSelect) {
      return Promise.resolve();
    }
    return api.getUiFeatures()
      .then(function (payload) {
        if (!payload) {
          el.featureMenuGroup.classList.add("hidden");
          return;
        }
        var items = Array.isArray(payload.items) ? payload.items : [];
        renderFeatureMenuItems(items);
      })
      .catch(function () {
        el.featureMenuGroup.classList.add("hidden");
      });
  }

  function handleFeatureMenuSelection() {
    if (!el.featureMenuSelect) {
      return;
    }
    var selected = el.featureMenuSelect.options[el.featureMenuSelect.selectedIndex];
    if (!selected) {
      return;
    }
    var url = String(selected.value || "").trim();
    if (!url) {
      return;
    }
    var target = String(selected.dataset.target || "_self").trim() || "_self";
    if (target === "_blank") {
      window.open(url, "_blank", "noopener,noreferrer");
    } else {
      window.location.assign(url);
    }
    el.featureMenuSelect.selectedIndex = 0;
  }

  function requestedSourcePathFromLocation() {
    try {
      var current = new URL(window.location.href);
      return String(current.searchParams.get("source_path") || "").trim();
    } catch (_err) {
      return "";
    }
  }

  function loadConfigurationFromServerPath(sourcePath, options) {
    var settings = options && typeof options === "object" ? options : {};
    var normalizedSourcePath = String(sourcePath || "").trim();
    if (!normalizedSourcePath) {
      return Promise.resolve(false);
    }
    return api.loadSourceFile(normalizedSourcePath, state.configType)
      .then(function (payload) {
        var fileName = String(payload.file_name || "").trim();
        var text = String(payload.text || "");
        var resolvedSourcePath = String(payload.source_path || normalizedSourcePath || "").trim();
        return loadConfigurationTextFromSource(text, fileName, fileName, resolvedSourcePath);
      })
      .then(function () {
        if (settings.clearLocationSourcePath === true) {
          var current = new URL(window.location.href);
          current.searchParams.delete("source_path");
          window.history.replaceState({}, "", current.pathname + current.search + current.hash);
        }
        return true;
      })
      .catch(function (err) {
        setValidationText(String(err));
        setStatusMessage("Failed to load source configuration from path.");
        return false;
      });
  }

  function configServiceOpenSourcePath() {
    return loadConfigurationFromServerPath(requestedSourcePathFromLocation(), {
      clearLocationSourcePath: true,
    });
  }

  function loadConfigurationTextFromSource(text, fileName, selectedDisplay, sourcePath) {
    var normalizedName = String(fileName || "").trim() || "config";
    var normalizedDisplay = String(selectedDisplay || "").trim() || normalizedName;
    state.currentSourcePath = String(sourcePath || "").trim();
    return api.prepareFileForLoad(text, normalizedName, state.configType).then(function (preparedFile) {
      if (/\.json$/i.test(normalizedName)) {
        var parsed = JSON.parse(preparedFile.body || "");
        state.doc = parsed;
        ensureDoc();
        state.includedDocuments = Array.isArray(parsed.included_documents) ? parsed.included_documents : [];
        state.configType = normalizeConfigType(
          preparedFile.config_type || parsed.configType || "fluentbit",
          "fluentbit"
        );
        state.doc.configType = state.configType;
        state.sourceLineMap = {};
        state.currentFileName = normalizedName;
        state.saveFileHandle = null;
        setOpenFileDisplay(normalizedDisplay);
        el.configTypeSelect.value = state.configType;
        setCookie(LAST_FILE_COOKIE, normalizedName);
        return loadVersionsForType(
          state.configType,
          preparedFile.version || parsed.version || state.selectedVersion
        )
          .then(function () {
            state.doc.version = state.selectedVersion;
            state.preserveSourceLineMapOnce = true;
            saveDoc();
            setStatusMessage("Loaded configuration file " + normalizedName);
            if (!state.selectedVersion) {
              renderAll();
              return null;
            }
            el.versionSelect.value = state.selectedVersion;
            return loadCatalog(state.selectedVersion);
          })
          .then(function () {
            if (!state.selectedVersion) {
              return null;
            }
            return loadServiceOptions(state.selectedVersion);
          })
          .then(function () {
            if (!state.selectedVersion) {
              return null;
            }
            return loadParserOptions(state.selectedVersion);
          })
          .then(renderAll);
      }

      if (/\.ya?ml$/i.test(normalizedName)) {
        state.configType = "fluentbit";
        el.configTypeSelect.value = state.configType;
        state.sourceLineMap = preparedFile.source_line_map || {};
        return loadVersionsForType(state.configType, preparedFile.version || state.selectedVersion)
          .then(function () {
            return api.parseFluentbit(state.selectedVersion, { text: preparedFile.body || "" });
          })
          .then(function (result) {
            state.doc = {
              version: state.selectedVersion,
              configType: "fluentbit",
              config: result.config || emptyDoc(state.selectedVersion, "fluentbit").config,
              annotations: {},
            };
            state.includedDocuments = Array.isArray(result.included_documents) ? result.included_documents : [];
            ensureDoc();
            state.currentFileName = normalizedName;
            state.saveFileHandle = null;
            setOpenFileDisplay(normalizedDisplay);
            setCookie(LAST_FILE_COOKIE, normalizedName);
            state.preserveSourceLineMapOnce = true;
            saveDoc();
            if (Array.isArray(result.errors) && result.errors.length > 0) {
              setStatusMessage("There were problems loading configuration file " + normalizedName + ". Recognized sections were loaded.");
              renderValidationState({ ok: false, errors: result.errors });
            } else {
              setStatusMessage("Loaded configuration file " + normalizedName);
              renderValidationState(null);
            }
            return loadCatalog(state.selectedVersion);
          })
          .then(function () {
            return loadServiceOptions(state.selectedVersion);
          })
          .then(function () {
            return loadParserOptions(state.selectedVersion);
          })
          .then(renderAll);
      }

      state.configType = normalizeConfigType(preparedFile.config_type || "fluentd", "fluentd");
      el.configTypeSelect.value = state.configType;
      state.sourceLineMap = preparedFile.source_line_map || {};
      state.currentFileName = normalizedName;
      state.saveFileHandle = null;
      setOpenFileDisplay(normalizedDisplay);
      setCookie(LAST_FILE_COOKIE, normalizedName);
      return loadVersionsForType(state.configType, preparedFile.version || state.selectedVersion)
        .then(function () {
          return api.parseFluentd(state.selectedVersion, { text: preparedFile.body || "" });
        })
        .then(function (result) {
          state.doc = {
            version: state.selectedVersion,
            configType: "fluentd",
            config: result.config || emptyDoc(state.selectedVersion, "fluentd").config,
            annotations: {},
          };
          state.includedDocuments = Array.isArray(result.included_documents) ? result.included_documents : [];
          ensureDoc();
          state.preserveSourceLineMapOnce = true;
          saveDoc();
          setStatusMessage("Loaded configuration file " + normalizedName);
          return loadCatalog(state.selectedVersion);
        })
        .then(function () {
          return loadServiceOptions(state.selectedVersion);
        })
        .then(function () {
          return loadParserOptions(state.selectedVersion);
        })
        .then(renderAll);
    });
  }

  function triggerConfigDownload(forcePrompt) {
    if (!state.doc) {
      setStatusMessage("Nothing to save yet.");
      return;
    }
    var fileName = defaultSaveFileName();
    buildSaveBlob()
      .then(function (result) {
        if ((forcePrompt || state.saveFileHandle || shouldPromptForSaveLocation()) && typeof window.showSaveFilePicker === "function") {
          var handlePromise = !forcePrompt && state.saveFileHandle
            ? Promise.resolve(state.saveFileHandle).then(function (handle) {
                reportBrowserSaveMechanism("file-system-access-handle", fileName);
                return handle;
              })
            : window.showSaveFilePicker({
                suggestedName: fileName,
                types: pickerTypesForCurrentConfig(),
              }).then(function (handle) {
                reportBrowserSaveMechanism("showSaveFilePicker", fileName);
                return handle;
              });
          return handlePromise.then(function (handle) {
            state.saveFileHandle = handle;
            return writeToSaveHandle(handle, result.blob).then(function () {
              state.currentFileName = handle.name || fileName;
              setOpenFileDisplay(handle.name || fileName);
              setCookie(LAST_FILE_COOKIE, state.currentFileName);
              saveDoc();
              setStatusMessage("Saved configuration as " + state.currentFileName);
            });
          });
        }

        reportBrowserSaveMechanism("anchor-download", fileName);
        downloadBlob(fileName, result.blob);
        state.currentFileName = fileName;
        setOpenFileDisplay(fileName);
        setCookie(LAST_FILE_COOKIE, fileName);
        saveDoc();
        setStatusMessage("Saved configuration as " + fileName);
      })
      .catch(function (err) {
        if (err && err.name === "AbortError") {
          setStatusMessage("Save cancelled.");
          return;
        }
        setValidationText(String(err));
      });
  }

  function validateCurrentDocument(options) {
    var settings = options && typeof options === "object" ? options : {};
    var saveOnSuccess = Boolean(settings.saveOnSuccess);
    if (!state.doc) {
      return Promise.resolve(null);
    }
    if (state.mergeIncludesForValidation && (!Array.isArray(state.includedDocuments) || state.includedDocuments.length === 0)) {
      setStatusMessage("Validation include merge is enabled, but no included files are loaded in memory.");
    }
    if (saveOnSuccess && !state.currentSourcePath) {
      window.alert("Save if valid is only available for files opened from the server catalog.");
      return Promise.resolve(null);
    }
    var payload = {
      config: state.doc.config,
      annotations: state.doc.annotations || {},
      included_documents: Array.isArray(state.includedDocuments) ? state.includedDocuments : [],
      merge_includes_for_validation: Boolean(state.mergeIncludesForValidation),
      save_on_success: saveOnSuccess,
      save_source_path: state.currentSourcePath || "",
      include_config_header: true,
      profile: "strict",
    };
    return api.validateDocument(state.doc.version, state.configType, payload)
      .then(function (result) {
        renderValidationState(result);
        if (result && result.saved) {
          setStatusMessage(result.save_message || "Saved validated configuration.");
        }
        if (result && result.save_declined) {
          window.alert(result.save_message || "Validation failed; file was not saved.");
        }
        return result;
      })
      .catch(function (err) {
        if (err && err.payload && Array.isArray(err.payload.errors)) {
          renderValidationState({ ok: false, errors: err.payload.errors });
        } else {
          setValidationText(String(err));
        }
        if (saveOnSuccess) {
          var message = err && err.payload && err.payload.save_message
            ? String(err.payload.save_message)
            : "Validation failed; file was not saved.";
          window.alert(message);
        }
        throw err;
      });
  }

  function updateAddPluginState() {
    var hasCatalog = Boolean(state.catalog && state.catalog.plugins);
    var hasPluginValue = Boolean(el.pluginName && el.pluginName.value);
    el.addPlugin.disabled = isReadOnlyMode() || !(hasCatalog && hasPluginValue);
  }

  function updateFluentdSectionVisibility() {
    var show = isFluentdMode();
    el.labelsPanel.classList.toggle("hidden", !show);
    el.workersPanel.classList.toggle("hidden", !show);
    if (el.addPluginPanel) {
      el.addPluginPanel.classList.toggle("hidden", show);
    }
    if (el.pluginsPanel) {
      el.pluginsPanel.classList.toggle("hidden", false);
    }
    if (el.envPanel) {
      el.envPanel.classList.toggle("hidden", show);
    }
    if (el.metadataEnvPanel) {
      el.metadataEnvPanel.classList.toggle("hidden", show);
    }
    if (el.upstreamServersPanel) {
      el.upstreamServersPanel.classList.toggle("hidden", show);
    }
    if (el.parsersPanel) {
      el.parsersPanel.classList.toggle("hidden", show);
    }
  }

  function selectedPluginDefinition() {
    var groups = pluginGroups();
    var selectedPluginName = String(el.pluginName.value || state.pluginName || "").trim();
    if (!selectedPluginName) {
      return null;
    }
    return (groups[state.pluginSection] && groups[state.pluginSection][selectedPluginName]) || null;
  }

  function fluentbitProcessorRoot() {
    if (!state.catalog || !state.catalog.common || !state.catalog.common.processors) {
      return null;
    }
    return state.catalog.common.processors;
  }

  function fluentbitProcessorSignals() {
    var root = fluentbitProcessorRoot();
    return (root && root.signals) || {};
  }

  function fluentbitSignalProcessorMap(signalName) {
    var signals = fluentbitProcessorSignals();
    var signalDef = signals[signalName] || {};
    var available = {};
    Object.keys(signalDef.processors || {}).forEach(function (name) {
      available[name] = signalDef.processors[name];
    });
    if (signalName === "logs" && signalDef.allow_filters_as_processors && state.catalog && state.catalog.plugins) {
      var filterDefs = state.catalog.plugins.filters || {};
      Object.keys(filterDefs).forEach(function (name) {
        available[name] = filterDefs[name];
      });
    }
    return available;
  }

  function fluentbitProcessorDefinition(signalName, processorName) {
    return fluentbitSignalProcessorMap(signalName)[processorName] || null;
  }

  function ensureFluentbitProcessors(instance) {
    if (!instance.processors || typeof instance.processors !== "object") {
      instance.processors = {};
    }
    ["logs", "metrics", "traces"].forEach(function (signalName) {
      if (!Array.isArray(instance.processors[signalName])) {
        instance.processors[signalName] = [];
      }
    });
  }

  function versionAtLeast(actual, minimum) {
    return uiHelpers.versionAtLeast(actual, minimum);
  }

  function supportsFluentbitRoutingUi() {
    return state.configType === "fluentbit" && versionAtLeast(state.selectedVersion, "4.2.0");
  }

  function fallbackFluentbitRouteDefinition() {
    return {
      description: "Optional Fluent Bit conditional routing rules for input plugins.",
      doc_url: "https://docs.fluentbit.io/manual/data-pipeline/router#conditional-routing",
      supported_sections: ["inputs"],
      signals: [
        { name: "logs", description: "Routes log records.", implemented: true },
        { name: "metrics", description: "Routes metric records. Fluent Bit currently parses these routes but does not evaluate them.", implemented: false },
        { name: "traces", description: "Routes trace records. Fluent Bit currently parses these routes but does not evaluate them.", implemented: false },
        { name: "any", description: "Routes all signal types. Fluent Bit currently evaluates logs only.", implemented: true }
      ]
    };
  }

  function fluentbitRouteRoot() {
    if (state.catalog && state.catalog.common && state.catalog.common.route) {
      return state.catalog.common.route;
    }
    if (supportsFluentbitRoutingUi()) {
      return fallbackFluentbitRouteDefinition();
    }
    return null;
  }

  function fluentbitRouteSignals() {
    var root = fluentbitRouteRoot();
    return Array.isArray(root && root.signals) ? root.signals.slice() : [];
  }

  function fluentbitRouteSignalByName(signalName) {
    var signals = fluentbitRouteSignals();
    for (var signalIndex = 0; signalIndex < signals.length; signalIndex += 1) {
      if (signals[signalIndex] && signals[signalIndex].name === signalName) {
        return signals[signalIndex];
      }
    }
    return null;
  }

  function ensureFluentbitRoute(instance) {
    if (!instance.route || typeof instance.route !== "object") {
      instance.route = { per_record_routing: true };
    }
    if (instance.route.per_record_routing === undefined) {
      instance.route.per_record_routing = true;
    }
    fluentbitRouteSignals().forEach(function (signalMeta) {
      var signalName = signalMeta && signalMeta.name;
      if (!signalName) {
        return;
      }
      if (!Array.isArray(instance.route[signalName])) {
        instance.route[signalName] = [];
      }
    });
  }

  function getPluginDefinition(section, pluginName) {
    var groups = pluginGroups();
    return (groups[section] && groups[section][pluginName]) || null;
  }

  function updatePluginHelpState() {
    var pluginDef = selectedPluginDefinition();
    var selectedPluginName = String(el.pluginName.value || state.pluginName || "").trim();
    if (!pluginDef || !pluginDef.doc_url) {
      el.pluginHelpToggle.disabled = true;
      el.pluginHelpToggle.title = selectedPluginName
        ? "No linked documentation is available for this plugin."
        : "Select a plugin to view help.";
      return;
    }

    el.pluginHelpToggle.disabled = false;
    el.pluginHelpToggle.title = selectedPluginName + ": " + String(pluginDef.description || "Open plugin documentation.");
  }

  function createFieldHelpButton(field, alignRight) {
    var helpBtn = document.createElement("button");
    helpBtn.type = "button";
    helpBtn.textContent = "?";
    helpBtn.className = "icon-help";
    if (alignRight) {
      helpBtn.classList.add("right-align");
    }
    var description = String(field.description || "Open field documentation.");
    var reference = String(field.reference || "").trim();
    helpBtn.title = description;
    if (!reference) {
      helpBtn.disabled = true;
      return helpBtn;
    }
    helpBtn.setAttribute("aria-label", "Open help for " + field.name);
    helpBtn.addEventListener("click", function () {
      window.open(reference, "_blank", "noopener,noreferrer");
    });
    return helpBtn;
  }

  function applyRequiredLabelStyle(label, isRequired) {
    if (isRequired) {
      label.classList.add("is-required");
    } else {
      label.classList.remove("is-required");
    }
  }

  function renderFieldRow(instance, field, options) {
    // Shared schema-driven field renderer used by plugin/service/parser UIs.
    options = options || {};
    var block = document.createElement("div");
    block.className = "field-block";
    if (options.commentTarget && options.commentFieldName) {
      block.classList.add("comment-group");
    }

    var row = document.createElement("div");
    row.className = "field-row";
    if (options.optional) {
      row.classList.add("optional-field-row");
    }

    var label = document.createElement("label");
    label.textContent = field.name;
    applyRequiredLabelStyle(label, Boolean(field.required));
    row.appendChild(label);

    var dataType = String(field.data_type || "string").toLowerCase();
    var enumOptions = getEnumOptions(field);
    if (dataType === "enum" && enumOptions.length > 0) {
      var select = document.createElement("select");
      enumOptions.forEach(function (value) {
        var option = document.createElement("option");
        option.value = String(value);
        option.textContent = String(value);
        select.appendChild(option);
      });
      select.value = normalizeEnumAliasValue(
        enumOptions,
        fieldInputValue(instance[field.name], field.data_type) || String(enumOptions[0])
      ) || String(enumOptions[0]);
      if (options.focusKey && state.pendingFocusFieldKey === options.focusKey) {
        setTimeout(function () {
          select.focus();
        }, 0);
        state.pendingFocusFieldKey = "";
      }
      select.addEventListener("change", function () {
        instance[field.name] = select.value;
        saveDoc();
      });
      select.disabled = isReadOnlyMode();
      row.appendChild(select);
    } else if (dataType === "boolean") {
      var checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = Boolean(instance[field.name]);
      if (options.focusKey && state.pendingFocusFieldKey === options.focusKey) {
        setTimeout(function () {
          checkbox.focus();
        }, 0);
        state.pendingFocusFieldKey = "";
      }
      checkbox.addEventListener("change", function () {
        instance[field.name] = checkbox.checked;
        saveDoc();
      });
      checkbox.disabled = isReadOnlyMode();
      row.appendChild(checkbox);
    } else {
      var isStructured = dataType === "array" || dataType === "list" || dataType === "object" || dataType === "map";
      var isCode = dataType === "code";
      var input = isStructured || isCode ? document.createElement("textarea") : document.createElement("input");
      input.value = fieldInputValue(instance[field.name], field.data_type);
      input.placeholder = field.description || "";
      input.title = field.description || "";
      if (isCode) {
        prepareCodeTextarea(input);
      }
      if (options.focusKey && state.pendingFocusFieldKey === options.focusKey) {
        setTimeout(function () {
          input.focus();
          if (typeof input.select === "function") {
            input.select();
          }
          if (isCode) {
            resizeCodeTextarea(input);
          }
        }, 0);
        state.pendingFocusFieldKey = "";
      }
      input.addEventListener("change", function () {
        instance[field.name] = parseTextValue(input.value, field.data_type);
        saveDoc();
      });
      input.disabled = isReadOnlyMode();
      row.appendChild(input);
    }

    var actions = document.createElement("div");
    actions.className = "field-row-actions";
    actions.appendChild(createFieldHelpButton(field, false));

    if (options.commentTarget && options.commentFieldName) {
      var commentToggle = createCommentToggleButton(
        options.commentToggleKey || "",
        options.commentTarget,
        options.commentFieldName,
        "comment editor for " + options.commentFieldName
      );
      actions.appendChild(commentToggle);
    }

    if (options.optional && typeof options.onRemove === "function") {
      var removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.textContent = "-";
      removeBtn.className = "icon-remove";
      removeBtn.title = "Remove attribute";
      removeBtn.disabled = isReadOnlyMode();
      removeBtn.addEventListener("click", options.onRemove);
      actions.appendChild(removeBtn);
    }

    row.appendChild(actions);

    block.appendChild(row);
    if (options.commentTarget && options.commentFieldName) {
      block.appendChild(
        createCommentEditorPanel(
          options.commentTarget,
          "Comment",
          options.commentFieldName,
          options.commentToggleKey || ""
        )
      );
    }

    return block;
  }


  var pluginUi = window.ConfigServiceUiPlugins.create({
    state: state,
    saveDoc: saveDoc,
    renderAll: renderAll,
    isReadOnlyMode: isReadOnlyMode,
    renderFieldRow: renderFieldRow,
    createCommentToggleButton: createCommentToggleButton,
    createCommentEditorPanel: createCommentEditorPanel,
    defaultForField: defaultForField,
    getPluginDefinition: getPluginDefinition,
    movePluginToSection: movePluginToSection,
    moveWithinPipeline: moveWithinPipeline,
    setValidationText: setValidationText,
    ensureDoc: ensureDoc,
    ensureFluentbitProcessors: ensureFluentbitProcessors,
    fluentbitProcessorRoot: fluentbitProcessorRoot,
    fluentbitProcessorSignals: fluentbitProcessorSignals,
    fluentbitSignalProcessorMap: fluentbitSignalProcessorMap,
    fluentbitProcessorDefinition: fluentbitProcessorDefinition,
    ensureFluentbitRoute: ensureFluentbitRoute,
    fluentbitRouteRoot: fluentbitRouteRoot,
    fluentbitRouteSignals: fluentbitRouteSignals,
    fluentbitRouteSignalByName: fluentbitRouteSignalByName,
    createFieldHelpButton: createFieldHelpButton,
    applyRequiredLabelStyle: applyRequiredLabelStyle,
    parseFlexibleRouteValue: parseFlexibleRouteValue,
    formatFlexibleRouteValue: formatFlexibleRouteValue,
  });

  var sectionsUi = window.ConfigServiceUiSections.create({
    state: state,
    el: el,
    saveDoc: saveDoc,
    renderAll: renderAll,
    ensureDoc: ensureDoc,
    isReadOnlyMode: isReadOnlyMode,
    createCommentToggleButton: createCommentToggleButton,
    createCommentEditorPanel: createCommentEditorPanel,
    renameFieldComment: renameFieldComment,
    clearFieldComment: clearFieldComment,
    renderFieldRow: renderFieldRow,
    createFieldHelpButton: createFieldHelpButton,
    applyRequiredLabelStyle: applyRequiredLabelStyle,
    parseServiceValueByType: parseServiceValueByType,
    parseServiceValue: parseServiceValue,
    normalizeEnumAliasValue: normalizeEnumAliasValue,
    getEnumOptions: getEnumOptions,
    prepareCodeTextarea: prepareCodeTextarea,
    parserFormatFields: parserFormatFields,
    getServiceOptionByKey: function (key) {
      return SERVICE_OPTION_BY_KEY[key] || null;
    },
    getParserFormatByKey: function (key) {
      return PARSER_FORMAT_BY_KEY[key] || null;
    },
    defaultForField: defaultForField,
  });

  var envUi = window.ConfigServiceUiEnv.create({
    state: state,
    el: el,
    saveDoc: saveDoc,
    ensureDoc: ensureDoc,
    isReadOnlyMode: isReadOnlyMode,
    parseServiceValue: parseServiceValue,
  });

  function moveWithinPipeline(pipeline, section, index, direction, pathPrefix) {
    if (isReadOnlyMode()) {
      return;
    }
    var list = pipeline[section];
    var target = index + direction;
    if (target < 0 || target >= list.length) {
      return;
    }
    if (pathPrefix) {
    }
    var temp = list[target];
    list[target] = list[index];
    list[index] = temp;
    saveDoc();
    renderAll();
  }

  function remapPluginInstanceForSection(instance, targetPluginDef) {
    var nextInstance = { name: instance.name };
    var targetFields = (targetPluginDef && targetPluginDef.fields) || [];
    targetFields.forEach(function (field) {
      if (Object.prototype.hasOwnProperty.call(instance, field.name)) {
        nextInstance[field.name] = instance[field.name];
        return;
      }
      if (field.required) {
        nextInstance[field.name] = defaultForField(field);
      }
    });
    return nextInstance;
  }

  function movePluginToSection(pipeline, section, index, instance, targetSection, pathPrefix) {
    if (isReadOnlyMode()) {
      return;
    }
    if (targetSection === section) {
      return;
    }
    var targetPluginDef = getPluginDefinition(targetSection, instance.name);
    if (!targetPluginDef) {
      setValidationText(
        "Plugin '" + instance.name + "' is not available in the '" + targetSection + "' section."
      );
      return;
    }
    var nextInstance = remapPluginInstanceForSection(instance, targetPluginDef);
    if (pathPrefix) {
    }
    pipeline[section].splice(index, 1);
    pipeline[targetSection].push(nextInstance);
    saveDoc();
    setValidationText("");
    renderAll();
  }

    function renderPluginCard(flatIndex, section, index, instance, pipeline, keyPrefix, pathPrefix) {
    return pluginUi.renderPluginCard(flatIndex, section, index, instance, pipeline, keyPrefix, pathPrefix);
  }

function parserFormatFields(parserFormat) {
    return Array.isArray(parserFormat && parserFormat.fields) ? parserFormat.fields : [];
  }

    function renderParsers() {
    return sectionsUi.renderParsers();
  }

  function renderService() {
    return sectionsUi.renderService();
  }

  function renderEnv() {
    return envUi.renderEnv();
  }

  function normalizeSchemaFieldDataType(prop, enumValues) {
    if (Array.isArray(enumValues) && enumValues.length > 0) {
      return "enum";
    }
    var rawType = String((prop && (prop["x-config-data-type"] || prop.type)) || "string").toLowerCase();
    if (
      rawType === "string" ||
      rawType === "boolean" ||
      rawType === "integer" ||
      rawType === "number" ||
      rawType === "array" ||
      rawType === "object" ||
      rawType === "list" ||
      rawType === "map" ||
      rawType === "code" ||
      rawType === "enum"
    ) {
      return rawType;
    }
    return "string";
  }

  function schemaFieldDefinition(name, prop, requiredLookup, defaultReference) {
    var enumValues = Array.isArray(prop && prop.enum) ? prop.enum.slice() : [];
    return {
      name: String(name || "").trim(),
      data_type: normalizeSchemaFieldDataType(prop, enumValues),
      required: Boolean(requiredLookup && requiredLookup[name]),
      description: String((prop && prop.description) || ""),
      reference: String((prop && prop["x-doc-reference"]) || defaultReference || ""),
      enum_options: enumValues,
    };
  }

  function fallbackUpstreamServersSchemaDefinition() {
    var reference = "https://docs.fluentbit.io/manual/administration/configuring-fluent-bit/yaml/upstream-servers-section";
    return {
      description: "Root-level upstream server groups for output plugin load-balancing.",
      reference: reference,
      groupFields: [
        {
          name: "name",
          data_type: "string",
          required: true,
          description: "Upstream group identifier.",
          reference: reference,
          enum_options: [],
        },
      ],
      nodeFields: [
        {
          name: "name",
          data_type: "string",
          required: true,
          description: "Node identifier.",
          reference: reference,
          enum_options: [],
        },
        {
          name: "host",
          data_type: "string",
          required: true,
          description: "Host/IP address for the upstream node.",
          reference: reference,
          enum_options: [],
        },
        {
          name: "port",
          data_type: "integer",
          required: true,
          description: "TCP port for the upstream node endpoint.",
          reference: reference,
          enum_options: [],
        },
        {
          name: "tls",
          data_type: "boolean",
          required: false,
          description: "Enable TLS for this node connection.",
          reference: reference,
          enum_options: [],
        },
        {
          name: "tls_verify",
          data_type: "boolean",
          required: false,
          description: "Verify TLS peer certificate when TLS is enabled.",
          reference: reference,
          enum_options: [],
        },
        {
          name: "shared_key",
          data_type: "string",
          required: false,
          description: "Shared key for secured upstream communication.",
          reference: reference,
          enum_options: [],
        },
      ],
    };
  }

  function upstreamServersSchemaDefinition() {
    var fallback = fallbackUpstreamServersSchemaDefinition();
    var root =
      state.compiledSchema &&
      state.compiledSchema.properties &&
      state.compiledSchema.properties.config &&
      state.compiledSchema.properties.config.properties &&
      state.compiledSchema.properties.config.properties.upstream_servers;
    if (!root || typeof root !== "object") {
      return fallback;
    }

    var reference = String(root["x-doc-reference"] || fallback.reference || "");
    var groupSchema = root.items && typeof root.items === "object" ? root.items : {};
    var groupProps = groupSchema.properties && typeof groupSchema.properties === "object" ? groupSchema.properties : {};
    var groupRequired = {};
    (Array.isArray(groupSchema.required) ? groupSchema.required : []).forEach(function (name) {
      groupRequired[String(name)] = true;
    });

    var nodeArraySchema = groupProps.nodes && typeof groupProps.nodes === "object" ? groupProps.nodes : {};
    var nodeSchema = nodeArraySchema.items && typeof nodeArraySchema.items === "object" ? nodeArraySchema.items : {};
    var nodeProps = nodeSchema.properties && typeof nodeSchema.properties === "object" ? nodeSchema.properties : {};
    var nodeRequired = {};
    (Array.isArray(nodeSchema.required) ? nodeSchema.required : []).forEach(function (name) {
      nodeRequired[String(name)] = true;
    });

    var groupFields = Object.keys(groupProps)
      .filter(function (name) {
        return name !== "_meta" && name !== "nodes";
      })
      .map(function (name) {
        return schemaFieldDefinition(name, groupProps[name], groupRequired, reference);
      })
      .filter(function (field) {
        return Boolean(field && field.name);
      });

    var nodeFields = Object.keys(nodeProps)
      .filter(function (name) {
        return name !== "_meta";
      })
      .map(function (name) {
        return schemaFieldDefinition(name, nodeProps[name], nodeRequired, reference);
      })
      .filter(function (field) {
        return Boolean(field && field.name);
      });

    return {
      description: String(root.description || fallback.description || ""),
      reference: reference,
      groupFields: groupFields.length > 0 ? groupFields : fallback.groupFields,
      nodeFields: nodeFields.length > 0 ? nodeFields : fallback.nodeFields,
    };
  }

  function newUpstreamNode(schemaDef) {
    var definition = schemaDef || upstreamServersSchemaDefinition();
    var instance = {};
    (definition.nodeFields || []).forEach(function (field) {
      if (field && field.required) {
        instance[field.name] = defaultForField(field);
      }
    });
    return instance;
  }

  function newUpstreamGroup(schemaDef) {
    var definition = schemaDef || upstreamServersSchemaDefinition();
    var instance = { nodes: [] };
    (definition.groupFields || []).forEach(function (field) {
      if (field && field.required) {
        instance[field.name] = defaultForField(field);
      }
    });
    instance.nodes.push(newUpstreamNode(definition));
    return instance;
  }

  function renderOptionalFieldAdder(instance, fields, keyPrefix) {
    var missingOptional = fields.filter(function (field) {
      return !field.required && !Object.prototype.hasOwnProperty.call(instance, field.name);
    });
    if (missingOptional.length === 0) {
      return null;
    }

    var optionalRow = document.createElement("div");
    optionalRow.className = "optional-row";

    var optionalSel = document.createElement("select");
    var emptyOpt = document.createElement("option");
    emptyOpt.value = "";
    emptyOpt.textContent = "Select optional attribute...";
    optionalSel.appendChild(emptyOpt);
    missingOptional.forEach(function (field) {
      var option = document.createElement("option");
      option.value = field.name;
      option.textContent = field.name;
      optionalSel.appendChild(option);
    });
    optionalSel.disabled = isReadOnlyMode();
    optionalRow.appendChild(optionalSel);

    var optionalDivider = document.createElement("span");
    optionalDivider.className = "optional-divider";
    optionalDivider.setAttribute("aria-hidden", "true");
    optionalRow.appendChild(optionalDivider);

    var addOptional = document.createElement("button");
    addOptional.type = "button";
    addOptional.textContent = "Add Optional";
    addOptional.disabled = isReadOnlyMode();
    addOptional.addEventListener("click", function () {
      var selected = optionalSel.value;
      if (!selected) {
        return;
      }
      var field = fields.find(function (candidate) {
        return candidate.name === selected;
      });
      if (!field) {
        return;
      }
      instance[field.name] = defaultForField(field);
      state.pendingFocusFieldKey = keyPrefix + ":" + field.name;
      saveDoc();
      renderAll();
    });
    optionalRow.appendChild(addOptional);
    return optionalRow;
  }

  function renderUpstreamNodeCard(group, groupIndex, node, nodeIndex, schemaDef) {
    var collapseKey = "upstream-node:" + groupIndex + ":" + nodeIndex;
    var collapsed = Boolean(state.collapse[collapseKey]);
    var card = document.createElement("div");
    card.className = "plugin-card";

    var head = document.createElement("div");
    head.className = "plugin-head";
    var left = document.createElement("div");
    left.className = "plugin-head-main";
    var title = document.createElement("strong");
    title.textContent = "#" + (nodeIndex + 1) + " Node: " + String(node.name || "(unnamed)");
    left.appendChild(title);
    head.appendChild(left);

    var actions = document.createElement("div");
    actions.className = "plugin-actions";
    actions.appendChild(createCommentToggleButton(collapseKey + ":comment", node, "", "upstream node comment editor"));

    var collapseBtn = document.createElement("button");
    collapseBtn.type = "button";
    collapseBtn.textContent = collapsed ? "Expand" : "Collapse";
    collapseBtn.addEventListener("click", function () {
      state.collapse[collapseKey] = !collapsed;
      renderAll();
    });
    actions.appendChild(collapseBtn);

    var removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "-";
    removeBtn.className = "icon-remove";
    removeBtn.title = "Remove upstream node";
    removeBtn.disabled = isReadOnlyMode();
    removeBtn.addEventListener("click", function () {
      group.nodes.splice(nodeIndex, 1);
      saveDoc();
      renderAll();
    });
    actions.appendChild(removeBtn);
    head.appendChild(actions);
    card.appendChild(head);

    if (collapsed) {
      return card;
    }

    card.appendChild(createCommentEditorPanel(node, "Node Comment", "", collapseKey + ":comment"));

    var body = document.createElement("div");
    body.className = "field-grid";
    var fields = Array.isArray(schemaDef.nodeFields) ? schemaDef.nodeFields : [];

    var requiredFields = fields.filter(function (field) {
      return Boolean(field.required);
    });
    var currentOptionalFields = fields.filter(function (field) {
      return !field.required && Object.prototype.hasOwnProperty.call(node, field.name);
    });

    requiredFields.forEach(function (field) {
      body.appendChild(
        renderFieldRow(node, field, {
          optional: false,
          focusKey: collapseKey + ":" + field.name,
          commentTarget: node,
          commentFieldName: field.name,
          commentToggleKey: collapseKey + ":" + field.name + ":comment",
        })
      );
    });

    currentOptionalFields.forEach(function (field) {
      body.appendChild(
        renderFieldRow(node, field, {
          optional: true,
          focusKey: collapseKey + ":" + field.name,
          commentTarget: node,
          commentFieldName: field.name,
          commentToggleKey: collapseKey + ":" + field.name + ":comment",
          onRemove: function () {
            delete node[field.name];
            clearFieldComment(node, field.name);
            saveDoc();
            renderAll();
          },
        })
      );
    });
    card.appendChild(body);

    var optionalRow = renderOptionalFieldAdder(node, fields, collapseKey);
    if (optionalRow) {
      card.appendChild(optionalRow);
    }
    return card;
  }

  function renderUpstreamGroupCard(group, groupIndex, schemaDef) {
    if (!Array.isArray(group.nodes)) {
      group.nodes = [];
    }
    var collapseKey = "upstream-group:" + groupIndex;
    var collapsed = Boolean(state.collapse[collapseKey]);
    var card = document.createElement("div");
    card.className = "plugin-card";

    var head = document.createElement("div");
    head.className = "plugin-head";
    var left = document.createElement("div");
    left.className = "plugin-head-main";
    var title = document.createElement("strong");
    title.textContent = "#" + (groupIndex + 1) + " Group: " + String(group.name || "(unnamed)");
    left.appendChild(title);
    head.appendChild(left);

    var actions = document.createElement("div");
    actions.className = "plugin-actions";
    actions.appendChild(createCommentToggleButton(collapseKey + ":comment", group, "", "upstream group comment editor"));

    var collapseBtn = document.createElement("button");
    collapseBtn.type = "button";
    collapseBtn.textContent = collapsed ? "Expand" : "Collapse";
    collapseBtn.addEventListener("click", function () {
      state.collapse[collapseKey] = !collapsed;
      renderAll();
    });
    actions.appendChild(collapseBtn);

    var removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "-";
    removeBtn.className = "icon-remove";
    removeBtn.title = "Remove upstream server group";
    removeBtn.disabled = isReadOnlyMode();
    removeBtn.addEventListener("click", function () {
      state.doc.config.upstream_servers.splice(groupIndex, 1);
      saveDoc();
      renderAll();
    });
    actions.appendChild(removeBtn);
    head.appendChild(actions);
    card.appendChild(head);

    if (collapsed) {
      return card;
    }

    card.appendChild(createCommentEditorPanel(group, "Group Comment", "", collapseKey + ":comment"));

    var body = document.createElement("div");
    body.className = "field-grid";
    var fields = Array.isArray(schemaDef.groupFields) ? schemaDef.groupFields : [];

    var requiredFields = fields.filter(function (field) {
      return Boolean(field.required);
    });
    var currentOptionalFields = fields.filter(function (field) {
      return !field.required && Object.prototype.hasOwnProperty.call(group, field.name);
    });

    requiredFields.forEach(function (field) {
      body.appendChild(
        renderFieldRow(group, field, {
          optional: false,
          focusKey: collapseKey + ":" + field.name,
          commentTarget: group,
          commentFieldName: field.name,
          commentToggleKey: collapseKey + ":" + field.name + ":comment",
        })
      );
    });

    currentOptionalFields.forEach(function (field) {
      body.appendChild(
        renderFieldRow(group, field, {
          optional: true,
          focusKey: collapseKey + ":" + field.name,
          commentTarget: group,
          commentFieldName: field.name,
          commentToggleKey: collapseKey + ":" + field.name + ":comment",
          onRemove: function () {
            delete group[field.name];
            clearFieldComment(group, field.name);
            saveDoc();
            renderAll();
          },
        })
      );
    });
    card.appendChild(body);

    var optionalRow = renderOptionalFieldAdder(group, fields, collapseKey);
    if (optionalRow) {
      card.appendChild(optionalRow);
    }

    var nodesPanel = document.createElement("div");
    nodesPanel.className = "nested-panel";
    var nodesHeading = document.createElement("h4");
    nodesHeading.textContent = "Nodes";
    nodesPanel.appendChild(nodesHeading);

    var nodesControls = document.createElement("div");
    nodesControls.className = "row";
    var addNode = document.createElement("button");
    addNode.type = "button";
    addNode.textContent = "Add Node";
    addNode.disabled = isReadOnlyMode();
    addNode.addEventListener("click", function () {
      group.nodes.push(newUpstreamNode(schemaDef));
      saveDoc();
      renderAll();
    });
    nodesControls.appendChild(addNode);
    nodesPanel.appendChild(nodesControls);

    var nodesHolder = document.createElement("div");
    nodesHolder.className = "container-stack";
    if (!Array.isArray(group.nodes) || group.nodes.length === 0) {
      var emptyNodes = document.createElement("p");
      emptyNodes.textContent = "No nodes configured.";
      nodesHolder.appendChild(emptyNodes);
    } else {
      group.nodes.forEach(function (node, nodeIndex) {
        if (!node || typeof node !== "object") {
          node = {};
          group.nodes[nodeIndex] = node;
        }
        nodesHolder.appendChild(renderUpstreamNodeCard(group, groupIndex, node, nodeIndex, schemaDef));
      });
    }
    nodesPanel.appendChild(nodesHolder);
    card.appendChild(nodesPanel);
    return card;
  }

  function renderUpstreamServers() {
    ensureDoc();
    if (!el.upstreamServersList) {
      return;
    }
    el.upstreamServersList.innerHTML = "";
    var schemaDef = upstreamServersSchemaDefinition();
    if (el.upstreamServersMeta) {
      el.upstreamServersMeta.textContent = String(schemaDef.description || "");
    }
    if (el.upstreamServersHelpToggle) {
      var hasReference = Boolean(schemaDef.reference);
      el.upstreamServersHelpToggle.disabled = !hasReference;
      el.upstreamServersHelpToggle.title = hasReference
        ? "Open upstream servers documentation."
        : "No linked upstream server documentation is available for this schema.";
    }

    if (!Array.isArray(state.doc.config.upstream_servers) || state.doc.config.upstream_servers.length === 0) {
      var empty = document.createElement("p");
      empty.textContent = "No upstream server groups configured.";
      el.upstreamServersList.appendChild(empty);
      return;
    }

    state.doc.config.upstream_servers.forEach(function (group, groupIndex) {
      if (!group || typeof group !== "object") {
        group = {};
        state.doc.config.upstream_servers[groupIndex] = group;
      }
      el.upstreamServersList.appendChild(renderUpstreamGroupCard(group, groupIndex, schemaDef));
    });
  }

function renderPlugins() {
    ensureDoc();
    el.pluginList.innerHTML = "";
    var flattened = flattenPlugins();
    if (flattened.length === 0) {
      var empty = document.createElement("p");
      empty.textContent = "No plugins yet. Use Add Plugin to create entries.";
      el.pluginList.appendChild(empty);
      return;
    }

    flattened.forEach(function (entry, flatIndex) {
      el.pluginList.appendChild(
        renderPluginCard(flatIndex, entry.section, entry.index, entry.instance, state.doc.config.pipeline, "main", "$.pipeline")
      );
    });
  }

  function nextLabelName() {
    ensureDoc();
    return "@label" + String((state.doc.config.labels || []).length + 1);
  }

  function nextWorkerName() {
    ensureDoc();
    return String((state.doc.config.workers || []).length);
  }

  function createScopedPluginAdder(pipeline, prefix) {
    var row = document.createElement("div");
    row.className = "nested-panel";

    var heading = document.createElement("h4");
    heading.textContent = "Add Plugin";
    row.appendChild(heading);

    var controls = document.createElement("div");
    controls.className = "row";

    var sectionLabel = document.createElement("label");
    sectionLabel.textContent = "Section";
    var sectionSelect = document.createElement("select");
    ["inputs", "filters", "outputs"].forEach(function (sectionName) {
      var option = document.createElement("option");
      option.value = sectionName;
      option.textContent = sectionName;
      sectionSelect.appendChild(option);
    });
    sectionLabel.appendChild(sectionSelect);
    controls.appendChild(sectionLabel);

    var pluginLabel = document.createElement("label");
    pluginLabel.textContent = "Plugin";
    var pluginSelect = document.createElement("select");
    pluginLabel.appendChild(pluginSelect);
    controls.appendChild(pluginLabel);

    var helpBtn = document.createElement("button");
    helpBtn.type = "button";
    helpBtn.textContent = "?";
    helpBtn.className = "icon-help";
    controls.appendChild(helpBtn);

    var addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.textContent = "Add Plugin";
    controls.appendChild(addBtn);

    function refreshPluginSelect() {
      var section = sectionSelect.value;
      var names = Object.keys(pluginGroups()[section] || {}).sort();
      pluginSelect.innerHTML = "";
      names.forEach(function (name) {
        var option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        pluginSelect.appendChild(option);
      });
      helpBtn.disabled = names.length === 0;
      if (names.length > 0) {
        var def = getPluginDefinition(section, names[0]);
        helpBtn.title = def && def.description ? def.description : "Open plugin documentation.";
      }
    }

    sectionSelect.addEventListener("change", refreshPluginSelect);
    sectionSelect.disabled = isReadOnlyMode();
    pluginSelect.addEventListener("change", function () {
      var def = getPluginDefinition(sectionSelect.value, pluginSelect.value);
      helpBtn.disabled = !(def && def.doc_url);
      helpBtn.title = def && def.description ? def.description : "Open plugin documentation.";
    });
    helpBtn.addEventListener("click", function () {
      var def = getPluginDefinition(sectionSelect.value, pluginSelect.value);
      if (!def || !def.doc_url) {
        setValidationText("No linked documentation is available for the selected Fluentd plugin.");
        return;
      }
      window.open(def.doc_url, "_blank", "noopener,noreferrer");
    });
    pluginSelect.disabled = isReadOnlyMode();
    addBtn.addEventListener("click", function () {
      var section = sectionSelect.value;
      var name = pluginSelect.value;
      var def = getPluginDefinition(section, name);
      if (!def) {
        return;
      }
      var instance = { name: name };
      (def.fields || []).forEach(function (field) {
        if (field.required) {
          instance[field.name] = defaultForField(field);
        }
      });
      pipeline[section].push(instance);
      saveDoc();
      renderAll();
    });
    addBtn.disabled = isReadOnlyMode();

    refreshPluginSelect();
    row.appendChild(controls);
    return row;
  }

  function renderContainerPlugins(target, pipeline, prefix, pathPrefix) {
    var flattened = flattenPipeline(pipeline, prefix);
    if (flattened.length === 0) {
      var empty = document.createElement("p");
      empty.textContent = "No plugins configured in this scope yet.";
      target.appendChild(empty);
      return;
    }
    flattened.forEach(function (entry, flatIndex) {
      target.appendChild(
        renderPluginCard(flatIndex, entry.section, entry.index, entry.instance, pipeline, prefix, pathPrefix)
      );
    });
  }

  function renderNamedContainerCard(kind, collection, index, item) {
    if (!item.pipeline || typeof item.pipeline !== "object") {
      item.pipeline = { inputs: [], filters: [], outputs: [] };
    }
    ["inputs", "filters", "outputs"].forEach(function (sectionName) {
      if (!Array.isArray(item.pipeline[sectionName])) {
        item.pipeline[sectionName] = [];
      }
    });
    var card = document.createElement("div");
    card.className = "plugin-card";
    var collapseKey = kind + ":" + index;
    var collapsed = Boolean(state.collapse[collapseKey]);

    var head = document.createElement("div");
    head.className = "plugin-head";

    var left = document.createElement("div");
    left.className = "plugin-head-main";
    var title = document.createElement("strong");
    title.textContent = "#" + (index + 1) + " " + (kind === "label" ? "Label" : "Worker");
    left.appendChild(title);
    head.appendChild(left);

    var actions = document.createElement("div");
    actions.className = "plugin-actions";
    actions.appendChild(createCommentToggleButton(collapseKey + ":comment", item, "", kind + " comment editor"));

    var collapseBtn = document.createElement("button");
    collapseBtn.type = "button";
    collapseBtn.textContent = collapsed ? "Expand" : "Collapse";
    collapseBtn.addEventListener("click", function () {
      state.collapse[collapseKey] = !collapsed;
      renderAll();
    });
    actions.appendChild(collapseBtn);

    var removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "-";
    removeBtn.className = "icon-remove";
    removeBtn.title = "Remove " + kind;
    removeBtn.disabled = isReadOnlyMode();
    removeBtn.addEventListener("click", function () {
      collection.splice(index, 1);
      saveDoc();
      renderAll();
    });
    actions.appendChild(removeBtn);

    head.appendChild(actions);
    card.appendChild(head);

    if (collapsed) {
      return card;
    }

    var meta = document.createElement("div");
    meta.className = "container-meta-row";
    var nameLabel = document.createElement("label");
    nameLabel.textContent = "Name";
    var nameInput = document.createElement("input");
    nameInput.value = String(item.name || "");
    nameInput.disabled = isReadOnlyMode();
    nameInput.addEventListener("change", function () {
      item.name = nameInput.value.trim();
      saveDoc();
    });
    nameLabel.appendChild(nameInput);
    meta.appendChild(nameLabel);
    card.appendChild(meta);
    card.appendChild(createCommentEditorPanel(item, "Comment", "", collapseKey + ":comment"));

    card.appendChild(createScopedPluginAdder(item.pipeline, kind + ":" + index));

    var pluginHolder = document.createElement("div");
    pluginHolder.className = "container-stack";
    renderContainerPlugins(pluginHolder, item.pipeline, kind + ":" + index, "$." + kind + "s[" + index + "].pipeline");
    card.appendChild(pluginHolder);

    return card;
  }

  function renderLabelsAndWorkers() {
    ensureDoc();
    updateFluentdSectionVisibility();
    if (!isFluentdMode()) {
      return;
    }

    el.labelList.innerHTML = "";
    if (!Array.isArray(state.doc.config.labels) || state.doc.config.labels.length === 0) {
      var emptyLabels = document.createElement("p");
      emptyLabels.textContent = "No labels configured.";
      el.labelList.appendChild(emptyLabels);
    } else {
      state.doc.config.labels.forEach(function (label, index) {
        el.labelList.appendChild(renderNamedContainerCard("label", state.doc.config.labels, index, label));
      });
    }

    el.workerList.innerHTML = "";
    if (!Array.isArray(state.doc.config.workers) || state.doc.config.workers.length === 0) {
      var emptyWorkers = document.createElement("p");
      emptyWorkers.textContent = "No workers configured.";
      el.workerList.appendChild(emptyWorkers);
    } else {
      state.doc.config.workers.forEach(function (worker, index) {
        el.workerList.appendChild(renderNamedContainerCard("worker", state.doc.config.workers, index, worker));
      });
    }
  }

  function safeRenderSection(name, renderFn) {
    try {
      renderFn();
    } catch (err) {
      api.reportUiError({
        kind: "render_error",
        message: "Failed rendering section '" + String(name || "unknown") + "': " + String((err && err.message) || err),
        source: "config_ui.js",
        path: window.location.href,
        stack: err && err.stack ? String(err.stack) : "",
      });
    }
  }

  function renderAll() {
    // Global rerender entry point; this ordering keeps cross-panel state stable.
    safeRenderSection("service", renderService);
    safeRenderSection("environment_variables", renderEnv);
    safeRenderSection("plugins", renderPlugins);
    safeRenderSection("upstream_servers", renderUpstreamServers);
    safeRenderSection("parsers", renderParsers);
    safeRenderSection("labels_workers", renderLabelsAndWorkers);
    safeRenderSection("config_type_state", updateConfigTypeDisabledState);
    safeRenderSection("read_only_state", updateReadOnlyState);
    safeRenderSection("panel_visibility", updateSectionPanels);
  }

  function loadRuntimeSchema(version) {
    if (!version) {
      state.compiledSchema = null;
      return Promise.resolve(null);
    }
    return api.getSchema(version, state.configType, { strict: false })
      .then(function (payload) {
        state.compiledSchema = payload && payload.schema ? payload.schema : null;
        return state.compiledSchema;
      })
      .catch(function () {
        state.compiledSchema = null;
        return null;
      });
  }

  function loadCatalog(version) {
    return api.getCatalog(version, state.configType).then(function (catalog) {
      state.catalog = catalog;
      state.catalogLoaded = true;
      return loadRuntimeSchema(version).then(function () {
        repopulatePluginNameSelect();
        renderAll();
        return catalog;
      });
    });
  }

  function loadServiceOptions(version) {
    function parseServiceOptionsPayload(payload) {
      var rawOptions = [];
      if (payload && Array.isArray(payload.options)) {
        rawOptions = payload.options;
      } else if (payload && payload.options && typeof payload.options === "object") {
        rawOptions = Object.keys(payload.options)
          .map(function (key) {
            var value = payload.options[key];
            if (value && typeof value === "object") {
              return Object.assign({ name: key }, value);
            }
            return null;
          })
          .filter(Boolean);
      }
      return rawOptions
        .filter(function (item) {
          return item && (typeof item.name === "string" || typeof item.key === "string");
        })
        .map(function (item) {
          var optionKey = String(item.name || item.key || "").trim();
          if (!optionKey) {
            return null;
          }
          return {
            name: optionKey,
            key: optionKey,
            data_type: item.data_type || "string",
            default: Object.prototype.hasOwnProperty.call(item, "default") ? item.default : "",
            description: item.description || "",
            reference: item.reference || "",
            enum_options: Array.isArray(item.enum_options)
              ? item.enum_options.slice()
              : (Array.isArray(item.called_enum_options) ? item.called_enum_options.slice() : []),
            validation_rule: item.validation_rule || null,
          };
        })
        .filter(Boolean);
    }

    var normalizedType = normalizeConfigType(state.configType, "fluentbit");
    var fallbackType = normalizedType === "fluentbit" ? "fluentd" : "fluentbit";
    var queryCandidates = [normalizedType, fallbackType, ""];

    function attemptLoad(index) {
      if (index >= queryCandidates.length) {
        return Promise.reject(new Error("Service options unavailable."));
      }
      var queryType = queryCandidates[index];
      return api.getServiceOptions(version, queryType)
        .then(function (payload) {
          var parsed = parseServiceOptionsPayload(payload);
          if (parsed.length > 0) {
            return parsed;
          }
          throw new Error("Empty service options payload.");
        })
        .catch(function () {
          return attemptLoad(index + 1);
        });
    }

    return attemptLoad(0)
      .then(function (parsed) {
        SERVICE_OPTIONS = parsed;
        rebuildServiceOptionIndex();
        repopulateServiceOptionSelect();
        renderService();
      })
      .catch(function (_err) {
        SERVICE_OPTIONS = [];
        rebuildServiceOptionIndex();
        repopulateServiceOptionSelect();
        renderService();
        setStatusMessage("Service option definitions could not be loaded; only custom keys are available.");
      });
  }

  function ensureServiceOptionsLoaded(triggeredByUser) {
    if (SERVICE_OPTIONS.length > 0) {
      return Promise.resolve(true);
    }
    if (!state.selectedVersion) {
      return Promise.resolve(false);
    }
    if (serviceOptionsLoadInFlight) {
      return serviceOptionsLoadInFlight;
    }
    serviceOptionsLoadInFlight = loadServiceOptions(state.selectedVersion)
      .then(function () {
        return SERVICE_OPTIONS.length > 0;
      })
      .catch(function () {
        return false;
      })
      .finally(function () {
        serviceOptionsLoadInFlight = null;
      });
    return serviceOptionsLoadInFlight.then(function (loaded) {
      if (!loaded && triggeredByUser) {
        setStatusMessage("Service options are still unavailable. Check version/type selection.");
      }
      return loaded;
    });
  }

  function loadParserOptions(version) {
    function parseParserFormatsPayload(payload) {
      if (!payload || typeof payload !== "object") {
        return [];
      }

      var parserFormats = payload.parser_formats;
      if (parserFormats && typeof parserFormats === "object" && !Array.isArray(parserFormats)) {
        return Object.keys(parserFormats)
          .sort()
          .map(function (key) {
            var item = parserFormats[key] || {};
            return {
              key: key,
              title: item.title || key,
              description: item.description || "",
              doc_url: item.doc_url || "",
              fields: Array.isArray(item.fields) ? item.fields : [],
            };
          });
      }

      var options = Array.isArray(payload.options) ? payload.options : [];
      return options
        .map(function (item) {
          if (!item || typeof item !== "object") {
            return null;
          }
          var key = String(item.key || item.name || "").trim();
          if (!key) {
            return null;
          }
          return {
            key: key,
            title: item.title || key,
            description: item.description || "",
            doc_url: item.doc_url || "",
            fields: Array.isArray(item.fields) ? item.fields : [],
          };
        })
        .filter(Boolean)
        .sort(function (left, right) {
          return left.key.localeCompare(right.key);
        });
    }

    var normalizedType = normalizeConfigType(state.configType, "fluentbit");
    var queryCandidates = [];
    if (normalizedType) {
      queryCandidates.push(normalizedType);
    }
    if (normalizedType !== "fluentbit") {
      queryCandidates.push("fluentbit");
    }
    if (normalizedType !== "fluentd") {
      queryCandidates.push("fluentd");
    }
    queryCandidates.push("");

    function attemptLoad(index) {
      if (index >= queryCandidates.length) {
        return Promise.reject(new Error("Parser options unavailable."));
      }
      var queryType = queryCandidates[index];
      return api.getParserOptions(version, queryType)
        .then(function (payload) {
          var parsed = parseParserFormatsPayload(payload);
          if (parsed.length > 0) {
            return parsed;
          }
          throw new Error("Empty parser options payload.");
        })
        .catch(function () {
          return attemptLoad(index + 1);
        });
    }

    return attemptLoad(0)
      .then(function (parsed) {
        PARSER_FORMATS = parsed;
        rebuildParserFormatIndex();
        repopulateParserFormatSelect();
        renderParsers();
      })
      .catch(function (_err) {
        PARSER_FORMATS = [];
        rebuildParserFormatIndex();
        repopulateParserFormatSelect();
        renderParsers();
        if (!isFluentdMode()) {
          setStatusMessage("Parser format definitions could not be loaded for this version/type.");
        }
      });
  }

  function initEvents() {
    // Wire all DOM event handlers once at startup.
    window.addEventListener("resize", function () {
      Array.prototype.forEach.call(document.querySelectorAll("textarea.code-input"), function (node) {
        prepareCodeTextarea(node);
      });
    });

    el.newConfig.addEventListener("click", function () {
      state.doc = emptyDoc(state.selectedVersion, state.configType);
      state.includedDocuments = [];
      state.mergeIncludesForValidation = false;
      state.saveOnValidate = false;
      if (el.validationIncludeToggle) {
        el.validationIncludeToggle.checked = false;
      }
      if (el.validationSaveToggle) {
        el.validationSaveToggle.checked = false;
      }
      state.currentFileName = "";
      state.saveFileHandle = null;
      state.sourceLineMap = {};
      clearOpenFileSelection();
      setCookie(LAST_FILE_COOKIE, "new-" + Date.now());
      saveDoc();
      setStatusMessage("Started a new configuration.");
      renderAll();
    });

    el.browseFile.addEventListener("click", function () {
      el.openFile.value = "";
      el.openFile.click();
    });

    el.saveConfig.addEventListener("click", function () {
      if (state.currentSourcePath) {
        setStatusMessage("Validating before saving configuration back to the server file.");
        validateCurrentDocument({ saveOnSuccess: true }).catch(function (_err) {
          // Validation/render details are already reflected in the UI.
        });
        return;
      }
      triggerConfigDownload(true);
    });

    el.saveAsConfig.addEventListener("click", function () {
      triggerConfigDownload(true);
    });

    if (el.viewRawConfig) {
      el.viewRawConfig.addEventListener("click", function () {
        triggerRawConfigView();
      });
    }

    if (el.rawConfigClose) {
      el.rawConfigClose.addEventListener("click", closeRawConfigDialog);
    }

    el.validationToggle.addEventListener("click", function () {
      state.validationCollapsed = !state.validationCollapsed;
      updateResultPanels();
    });

    el.yamlToggle.addEventListener("click", function () {
      state.yamlCollapsed = !state.yamlCollapsed;
      updateResultPanels();
    });

    el.pluginsToggle.addEventListener("click", function () {
      state.pluginsPanelCollapsed = !state.pluginsPanelCollapsed;
      updateSectionPanels();
    });

    el.parsersToggle.addEventListener("click", function () {
      state.parsersPanelCollapsed = !state.parsersPanelCollapsed;
      updateSectionPanels();
    });

    el.labelsToggle.addEventListener("click", function () {
      state.labelsPanelCollapsed = !state.labelsPanelCollapsed;
      updateSectionPanels();
    });

    el.workersToggle.addEventListener("click", function () {
      state.workersPanelCollapsed = !state.workersPanelCollapsed;
      updateSectionPanels();
    });

    if (el.serviceToggle) {
      el.serviceToggle.addEventListener("click", function () {
        state.servicePanelCollapsed = !state.servicePanelCollapsed;
        updateSectionPanels();
      });
    }

    if (el.envToggle) {
      el.envToggle.addEventListener("click", function () {
        state.envPanelCollapsed = !state.envPanelCollapsed;
        updateSectionPanels();
      });
    }

    if (el.metadataEnvToggle) {
      el.metadataEnvToggle.addEventListener("click", function () {
        state.metadataPanelCollapsed = !state.metadataPanelCollapsed;
        updateSectionPanels();
      });
    }

    if (el.upstreamServersToggle) {
      el.upstreamServersToggle.addEventListener("click", function () {
        state.upstreamServersPanelCollapsed = !state.upstreamServersPanelCollapsed;
        updateSectionPanels();
      });
    }

    if (el.metadataEnvHelpToggle) {
      el.metadataEnvHelpToggle.addEventListener("click", function () {
        window.open("/config-service/ui/docs/metadata-env", "_blank", "noopener,noreferrer");
      });
    }

    if (el.upstreamServersHelpToggle) {
      el.upstreamServersHelpToggle.addEventListener("click", function () {
        var schemaDef = upstreamServersSchemaDefinition();
        if (!schemaDef || !schemaDef.reference) {
          setValidationText("No linked documentation is available for upstream servers in this schema.");
          return;
        }
        window.open(schemaDef.reference, "_blank", "noopener,noreferrer");
      });
    }

    el.versionSelect.addEventListener("change", function () {
      state.selectedVersion = el.versionSelect.value;
      if (state.doc) {
        state.doc.version = state.selectedVersion;
      }
      loadCatalog(state.selectedVersion)
        .then(function () {
          return loadServiceOptions(state.selectedVersion);
        })
        .then(function () {
          return loadParserOptions(state.selectedVersion);
        })
        .then(function () {
          return loadDryRunAvailability();
        })
        .catch(function (err) {
          setValidationText(String(err));
        });
      saveDoc();
    });

    el.configTypeSelect.addEventListener("change", function () {
      state.configType = normalizeConfigType(el.configTypeSelect.value, "fluentbit");
      if (state.doc) {
        state.doc.configType = state.configType;
      }
      loadVersionsForType(state.configType)
        .then(function () {
              if (!state.selectedVersion) {
                state.catalog = null;
                state.catalogLoaded = false;
                state.compiledSchema = null;
                SERVICE_OPTIONS = [];
                PARSER_FORMATS = [];
            rebuildServiceOptionIndex();
            rebuildParserFormatIndex();
            repopulateServiceOptionSelect();
            repopulateParserFormatSelect();
            renderAll();
            saveDoc();
            return null;
          }
          return loadCatalog(state.selectedVersion).then(function () {
            return loadServiceOptions(state.selectedVersion);
          }).then(function () {
            return loadParserOptions(state.selectedVersion);
          });
        })
        .then(function () {
          renderAll();
          saveDoc();
        })
        .catch(function (err) {
          setValidationText(String(err));
        });
    });

    el.pluginSection.addEventListener("change", function () {
      state.pluginSection = el.pluginSection.value;
      repopulatePluginNameSelect();
      updatePluginHelpState();
      updateAddPluginState();
    });

    el.pluginName.addEventListener("change", function () {
      state.pluginName = el.pluginName.value || "";
      updatePluginHelpState();
      updateAddPluginState();
    });

    el.pluginHelpToggle.addEventListener("click", function () {
      var pluginDef = selectedPluginDefinition();
      if (!pluginDef || !pluginDef.doc_url) {
        setValidationText("No linked documentation is available for the current plugin selection.");
        return;
      }
      window.open(pluginDef.doc_url, "_blank", "noopener,noreferrer");
    });

    el.addPlugin.addEventListener("click", function () {
      ensureDoc();
      if (!state.catalogLoaded || !state.catalog) {
        setValidationText("Catalog not loaded yet. Please wait and try again.");
        return;
      }
      state.pluginSection = String((el.pluginSection && el.pluginSection.value) || state.pluginSection || "inputs").trim() || "inputs";
      if ((!el.pluginName || !el.pluginName.value) && el.pluginName) {
        repopulatePluginNameSelect();
      }
      var selectedPluginName = String(el.pluginName.value || state.pluginName || "").trim();
      if (!selectedPluginName) {
        setValidationText("Select a plugin before adding.");
        return;
      }
      var groups = pluginGroups();
      var def = groups[state.pluginSection] && groups[state.pluginSection][selectedPluginName];
      if (!def) {
        setValidationText(
          "Selected plugin is unavailable for section '" +
            state.pluginSection +
            "'. Re-select section/plugin and try again."
        );
        return;
      }
      var instance = { name: selectedPluginName };
      (def.fields || []).forEach(function (field) {
        if (field.required) {
          instance[field.name] = defaultForField(field);
        }
      });
      state.doc.config.pipeline[state.pluginSection].push(instance);
      state.pluginName = selectedPluginName;
      saveDoc();
      renderAll();
      updateAddPluginState();
      setStatusMessage("Added plugin '" + selectedPluginName + "' to " + state.pluginSection + ".");
    });

    el.addServiceField.addEventListener("click", function () {
      ensureDoc();
      var selected = selectedServiceOption();
      var key = selected ? selected.key : "";
      if (el.serviceOption.value === CUSTOM_SERVICE_OPTION) {
        key = String(el.serviceCustomKey.value || "").trim();
      }
      if (!key) {
        return;
      }

      if (selected && el.serviceOption.value !== CUSTOM_SERVICE_OPTION) {
        state.doc.config.service[key] = parseServiceValueByType(
          el.serviceValue.value,
          selected.data_type
        );
      } else {
        state.doc.config.service[key] = parseServiceValue(el.serviceValue.value);
      }

      el.serviceCustomKey.value = "";
      el.serviceValue.value = "";
      saveDoc();
      renderService();
    });

    envUi.bindEvents();

    el.serviceOption.addEventListener("change", function () {
      updateServiceOptionUI();
    });

    el.serviceOption.addEventListener("focus", function () {
      if (SERVICE_OPTIONS.length === 0) {
        ensureServiceOptionsLoaded(true);
      }
    });

    el.serviceOption.addEventListener("pointerdown", function () {
      if (SERVICE_OPTIONS.length === 0) {
        ensureServiceOptionsLoaded(true);
      }
    });

    el.serviceHelpToggle.addEventListener("click", function () {
      var opt = selectedServiceOption();
      var isCustom = el.serviceOption.value === CUSTOM_SERVICE_OPTION;
      if (!opt || isCustom || !opt.reference) {
        setValidationText("No linked documentation is available for the current selection.");
        return;
      }
      window.open(opt.reference, "_blank", "noopener,noreferrer");
    });

    el.parserFormat.addEventListener("change", function () {
      updateParserFormatUI();
    });

    el.parserHelpToggle.addEventListener("click", function () {
      var formatDef = selectedParserFormatDefinition();
      if (!formatDef || !formatDef.doc_url) {
        setValidationText("No linked documentation is available for the current parser format selection.");
        return;
      }
      window.open(formatDef.doc_url, "_blank", "noopener,noreferrer");
    });

    el.addParser.addEventListener("click", function () {
      ensureDoc();
      var formatDef = selectedParserFormatDefinition();
      var parserName = String((el.parserNameInput && el.parserNameInput.value) || "").trim();
      if (!formatDef) {
        setValidationText("Select a parser format before adding.");
        return;
      }
      if (!parserName) {
        setValidationText("Provide a parser name before adding.");
        return;
      }
      var parserInstance = {
        name: parserName,
        format: formatDef.key,
      };
      parserFormatFields(formatDef).forEach(function (field) {
        if (field.required) {
          parserInstance[field.name] = defaultForField(field);
        }
      });
      state.doc.config.parsers.push(parserInstance);
      el.parserNameInput.value = "";
      saveDoc();
      setValidationText("");
      renderAll();
    });

    if (el.addUpstreamServerGroup) {
      el.addUpstreamServerGroup.addEventListener("click", function () {
        ensureDoc();
        if (isFluentdMode()) {
          return;
        }
        var schemaDef = upstreamServersSchemaDefinition();
        state.doc.config.upstream_servers.push(newUpstreamGroup(schemaDef));
        saveDoc();
        setValidationText("");
        renderAll();
      });
    }

    el.addLabel.addEventListener("click", function () {
      ensureDoc();
      state.doc.config.labels.push({
        name: nextLabelName(),
        pipeline: { inputs: [], filters: [], outputs: [] },
        includes: [],
      });
      saveDoc();
      renderAll();
    });

    el.addWorker.addEventListener("click", function () {
      ensureDoc();
      state.doc.config.workers.push({
        name: nextWorkerName(),
        pipeline: { inputs: [], filters: [], outputs: [] },
        labels: [],
        includes: [],
      });
      saveDoc();
      renderAll();
    });

    el.openFile.addEventListener("change", function (event) {
      var file = event.target.files && event.target.files[0];
      if (!file) {
        return;
      }
      var selectedDisplay = String(file.name || "").trim();
      file
        .text()
        .then(function (text) {
          return loadConfigurationTextFromSource(text, file.name, selectedDisplay);
        })
        .catch(function (err) {
          if (err && err.payload && Array.isArray(err.payload.errors)) {
            renderValidationState({ ok: false, errors: err.payload.errors });
            setStatusMessage("There were problems loading configuration file " + file.name + ".");
            return;
          }
          setValidationText(String(err));
          setStatusMessage("There were problems loading configuration file " + file.name + ".");
        });
    });

    if (el.featureMenuSelect) {
      el.featureMenuSelect.addEventListener("change", handleFeatureMenuSelection);
    }

    if (el.validationIncludeToggle) {
      el.validationIncludeToggle.addEventListener("change", function () {
        state.mergeIncludesForValidation = Boolean(el.validationIncludeToggle.checked);
      });
    }

    if (el.validationSaveToggle) {
      el.validationSaveToggle.addEventListener("change", function () {
        state.saveOnValidate = Boolean(el.validationSaveToggle.checked);
      });
    }

    if (el.renderIncludeToggle) {
      el.renderIncludeToggle.addEventListener("change", function () {
        state.renderIncludesForRender = Boolean(el.renderIncludeToggle.checked);
      });
    }

    el.validateBtn.addEventListener("click", function () {
      validateCurrentDocument({ saveOnSuccess: Boolean(state.saveOnValidate) }).catch(function (_err) {
        // Validation/render details are already reflected in the UI.
      });
    });

    if (el.dryRunBtn) {
      el.dryRunBtn.addEventListener("click", function () {
        if (!state.doc) {
          return;
        }
        var dryRunPayload = {
          config: state.doc.config,
          annotations: state.doc.annotations || {},
          included_documents: Array.isArray(state.includedDocuments) ? state.includedDocuments : [],
          merge_includes_for_validation: Boolean(state.mergeIncludesForValidation),
          profile: "strict",
        };
        api.runDryRun(state.doc.version, state.configType, dryRunPayload)
          .then(function (result) {
            var messages = Array.isArray(result && result.messages) ? result.messages : [];
            if (result && result.ok) {
              renderValidationState({ ok: true, errors: [] });
              var summary = messages.length > 0 ? " " + messages.join(" | ") : "";
              setStatusMessage("Dry run completed successfully." + summary);
              return;
            }
            var issues = messages.map(function (message, index) {
              return {
                order: index + 1,
                code: "dry_run_validation_error",
                path: "$",
                message: String(message),
                severity: "error",
                source: "external_agent",
              };
            });
            if (issues.length === 0) {
              issues = [
                {
                  order: 1,
                  code: "dry_run_validation_error",
                  path: "$",
                  message: String((result && result.error) || "Dry run validation failed."),
                  severity: "error",
                  source: "external_agent",
                },
              ];
            }
            renderValidationState({ ok: false, errors: issues });
            setStatusMessage("Dry run reported validation issues.");
          })
          .catch(function (err) {
            setValidationText(String(err));
            setStatusMessage("Dry run validation failed to execute.");
          });
      });
    }

    el.renderBtn.addEventListener("click", function () {
      if (!state.doc) {
        setStatusMessage("Load or create a configuration before rendering.");
        return;
      }
      var payload = {
        config: state.doc.config,
        annotations: state.doc.annotations || {},
        included_documents: Array.isArray(state.includedDocuments) ? state.includedDocuments : [],
        include_comments: true,
        render_included_files: Boolean(state.renderIncludesForRender),
      };
      if (state.renderIncludesForRender && (!Array.isArray(state.includedDocuments) || state.includedDocuments.length === 0)) {
        setStatusMessage("Include rendering is enabled, but no included files are loaded in memory.");
      }
      state.yamlCollapsed = false;
      updateResultPanels();
      (state.configType === "fluentd"
        ? api.renderFluentd(state.doc.version, payload)
        : api.renderYaml(state.doc.version, state.configType, payload))
        .then(function (result) {
          var renderedOutput = String(
            result.rendered_output ||
            result.yaml ||
            result.text ||
            ""
          );
          setStatusMessage("Rendered configuration updated.");
          setYamlText(renderedOutput, true);
        })
        .catch(function (err) {
          setStatusMessage("Rendering failed.");
          setYamlText(String(err));
        });
    });
  }

  function init() {
    initializeHistoryBackButton();
    api.installGlobalUiErrorHandlers();
    applyCssOverrides();
    repopulateServiceOptionSelect();
    repopulateParserFormatSelect();
    updateAddPluginState();
    renderValidationState(null);
    setYamlText("");
    updateResultPanels();
    updateSectionPanels();
    initEvents();
    fetchUiFeatureMenu();

    api.getHealth()
      .then(function (health) {
        state.readOnly = Boolean(health.read_only);
        updateReadOnlyState();
      })
      .catch(function (err) {
        state.catalogLoaded = false;
        updateAddPluginState();
        setValidationText(String(err));
      });

    api.getIssueCodes()
      .then(function (payload) {
        state.issueCodeMap = (payload && payload.codes) || {};
      })
      .catch(function (_err) {
        state.issueCodeMap = {};
      });

    var requestedSourcePath = requestedSourcePathFromLocation();
    loadVersionsForType(state.configType)
      .then(function () {
        if (requestedSourcePath) {
          clearOpenFileSelection();
          state.currentFileName = "";
          state.doc = null;
          return configServiceOpenSourcePath().then(function (opened) {
            if (opened) {
              return true;
            }
            state.doc = emptyDoc(state.selectedVersion, state.configType);
            ensureDoc();
            state.doc.configType = state.configType;
            el.configTypeSelect.value = state.configType;
            return false;
          });
        }

        var cookieDoc = localStorage.getItem(LAST_DOC_STORAGE);
        var cookieName = getCookie(LAST_FILE_COOKIE);
        if (cookieDoc && cookieName) {
          try {
            var parsed = JSON.parse(cookieDoc);
            state.doc = parsed;
            state.configType = normalizeConfigType(parsed.configType || "fluentbit", "fluentbit");
            state.currentFileName = cookieName;
            state.currentSourcePath = String(
              localStorage.getItem(LAST_DOC_SOURCE_PATH_STORAGE) || ""
            ).trim();
            setOpenFileDisplay(/^new-\d+$/i.test(cookieName) ? "" : cookieName);
          } catch (_storedDocumentParseError) {
            clearCookie(LAST_FILE_COOKIE);
            localStorage.removeItem(LAST_DOC_STORAGE);
            localStorage.removeItem(LAST_DOC_SOURCE_PATH_STORAGE);
          }
        }

        if (!state.doc) {
          state.doc = emptyDoc(state.selectedVersion, state.configType);
        }

        ensureDoc();
        state.doc.configType = state.configType;
        el.configTypeSelect.value = state.configType;
        return loadVersionsForType(state.configType, state.doc.version || state.selectedVersion);
      })
      .then(function (openedRequestedSourcePath) {
        if (openedRequestedSourcePath === true) {
          updateReadOnlyState();
          updateRenderedDirtyState();
          return null;
        }
        if (!state.selectedVersion) {
          renderAll();
          return null;
        }
        return loadCatalog(state.selectedVersion).then(function () {
          return loadServiceOptions(state.selectedVersion);
        }).then(function () {
          return loadParserOptions(state.selectedVersion);
        });
      })
      .then(function () {
        renderAll();
        updateReadOnlyState();
        updateRenderedDirtyState();
        return null;
      })
      .catch(function (err) {
        setValidationText(String(err));
      });
  }

  init();
})();
