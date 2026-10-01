/*
 * Copyright 2026 mp3monster.org
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

(function exposeClientConfigGeneratorFunctions(globalObject) {
  "use strict";

  const API_PREFIX = "/client-config-generator-service/api/v1";
  const KEY_CONFIGURATION = "configuration";
  const KEY_CONFIGURATIONS = "configurations";
  const KEY_ERROR = "error";
  const KEY_ERRORS = "errors";
  const KEY_MESSAGE = "message";
  const KEY_NAME = "name";
  const KEY_PATH = "path";
  const KEY_SCHEMA = "schema";
  const KEY_VALID = "valid";
  const KEY_UI_CONTROL = "x-control";
  const KEY_UI_OPTIONS = "x-options";
  const KEY_UI_REFRESH_FORM = "x-refresh-form";
  const KEY_UI_SECTION = "x-ui-section";
  const KEY_UI_VISIBLE_WHEN = "x-visible-when";
  const KEY_VALUES = "values";
  const KEY_VISIBLE_PATH = "path";
  const UI_CONTROL_MULTI_SELECT = "multi-select";
  const PROCESS_TRACKING_PATH = "consumer.processTracking";

  /** Create behavior functions with explicit browser dependencies. */
  function create(dependencies) {
    const documentObject = dependencies.documentObject;
    const fetchFunction = dependencies.fetchFunction;
    const state = dependencies.state;

    /** Return a nested value for a dot-delimited schema path. */
    function getPathValue(rootValue, fieldPath) {
      return fieldPath.split(".").reduce(function resolvePath(currentValue, pathPart) {
        if (!currentValue || typeof currentValue !== "object") {
          return undefined;
        }
        return currentValue[pathPart];
      }, rootValue);
    }

    /** Assign a nested value, creating intermediate objects as required. */
    function setPathValue(rootValue, fieldPath, fieldValue) {
      const pathParts = fieldPath.split(".");
      const finalPart = pathParts.pop();
      let targetValue = rootValue;
      pathParts.forEach(function createPath(pathPart) {
        if (!targetValue[pathPart] || typeof targetValue[pathPart] !== "object") {
          targetValue[pathPart] = {};
        }
        targetValue = targetValue[pathPart];
      });
      targetValue[finalPart] = fieldValue;
    }

    /** Build a configuration object populated from schema defaults. */
    function defaultsFromSchema(schemaDefinition) {
      if (Object.prototype.hasOwnProperty.call(schemaDefinition, "default")) {
        return structuredClone(schemaDefinition.default);
      }
      if (schemaDefinition.type === "object") {
        const defaultObject = {};
        Object.entries(schemaDefinition.properties || {}).forEach(function applyProperty(entry) {
          const propertyName = entry[0];
          const propertySchema = entry[1];
          const defaultValue = defaultsFromSchema(propertySchema);
          if (defaultValue !== undefined) {
            defaultObject[propertyName] = defaultValue;
          }
        });
        return defaultObject;
      }
      if (schemaDefinition.type === "array") {
        return [];
      }
      return undefined;
    }

    /** Return whether a schema property is visible in the active mode. */
    function supportsCurrentMode(schemaDefinition) {
      const supportedModes = schemaDefinition["x-modes"];
      return !Array.isArray(supportedModes) || supportedModes.includes(state.mode);
    }

    /** Return whether a schema property passes its data-driven visibility rule. */
    function supportsVisibilityRule(schemaDefinition) {
      const visibilityRule = schemaDefinition[KEY_UI_VISIBLE_WHEN];
      if (!visibilityRule || typeof visibilityRule !== "object") {
        return true;
      }
      const sourcePath = String(visibilityRule[KEY_VISIBLE_PATH] || "").trim();
      if (!sourcePath) {
        return true;
      }
      const currentValue = getPathValue(state.configuration, sourcePath);
      const visibleValues = visibilityRule[KEY_VALUES];
      if (Array.isArray(visibleValues)) {
        return visibleValues.includes(currentValue);
      }
      return Boolean(currentValue);
    }

    /** Return whether a schema property should render in the active UI state. */
    function supportsCurrentUiState(schemaDefinition) {
      return supportsCurrentMode(schemaDefinition) && supportsVisibilityRule(schemaDefinition);
    }

    /** Convert a form input value to its schema data type. */
    function valueFromInput(inputElement, schemaType) {
      if (schemaType === "boolean") {
        return inputElement.checked;
      }
      if (schemaType === "integer") {
        return inputElement.value === "" ? undefined : Number.parseInt(inputElement.value, 10);
      }
      if (schemaType === "array") {
        if (inputElement.multiple === true) {
          return Array.from(inputElement.selectedOptions).map(function selectedValue(optionElement) {
            return optionElement.value;
          });
        }
        return inputElement.value.split(",").map(function trimItem(itemValue) {
          return itemValue.trim();
        }).filter(Boolean);
      }
      return inputElement.value;
    }

    /** Read visible generated controls back into the current configuration. */
    function collectConfiguration() {
      documentObject.querySelectorAll("[data-config-path]").forEach(function collectInput(inputElement) {
        const fieldValue = valueFromInput(inputElement, inputElement.dataset.schemaType);
        if (fieldValue !== undefined) {
          setPathValue(state.configuration, inputElement.dataset.configPath, fieldValue);
        }
      });
      setPathValue(state.configuration, PROCESS_TRACKING_PATH, state.mode);
      updatePreview();
      return state.configuration;
    }

    /** Return a stable DOM id for a schema field path. */
    function fieldControlId(fieldPath) {
      return `field-${fieldPath.replace(/[^A-Za-z0-9_-]/g, "-")}`;
    }

    /** Return schema-defined select options with value and display label fields. */
    function optionDefinitions(schemaDefinition) {
      if (Array.isArray(schemaDefinition[KEY_UI_OPTIONS])) {
        return schemaDefinition[KEY_UI_OPTIONS].map(function normalizeOption(optionDefinition) {
          if (optionDefinition && typeof optionDefinition === "object") {
            return {
              label: String(optionDefinition.label || optionDefinition.value || ""),
              value: String(optionDefinition.value || optionDefinition.label || ""),
            };
          }
          return {
            label: String(optionDefinition),
            value: String(optionDefinition),
          };
        });
      }
      const enumValues = Array.isArray(schemaDefinition.enum) ? schemaDefinition.enum :
        Array.isArray(schemaDefinition.items && schemaDefinition.items.enum) ?
          schemaDefinition.items.enum : [];
      return enumValues.map(function enumOption(optionValue) {
        return {
          label: String(optionValue),
          value: String(optionValue),
        };
      });
    }

    /** Create a side-by-side field row with label, help text, and control. */
    function createFieldRow(schemaDefinition, inputElement, fieldPath) {
      const wrapperElement = documentObject.createElement("div");
      const labelElement = documentObject.createElement("label");
      const labelTextElement = documentObject.createElement("span");
      inputElement.id = fieldControlId(fieldPath);
      wrapperElement.className = "generated-field";
      labelElement.className = "generated-field-label";
      labelElement.htmlFor = inputElement.id;
      labelTextElement.textContent = schemaDefinition.title || "Setting";
      labelElement.append(labelTextElement);
      if (schemaDefinition.description) {
        const descriptionElement = documentObject.createElement("span");
        descriptionElement.className = "field-description";
        descriptionElement.textContent = schemaDefinition.description;
        labelElement.append(descriptionElement);
      }
      inputElement.classList.add("generated-field-control");
      wrapperElement.append(labelElement, inputElement);
      return wrapperElement;
    }

    /** Create a browser control for one scalar or string-array schema property. */
    function createInput(schemaDefinition, fieldPath) {
      const currentValue = getPathValue(state.configuration, fieldPath);
      let inputElement;
      const optionItems = optionDefinitions(schemaDefinition);
      if (
        schemaDefinition.type === "array" &&
        (schemaDefinition[KEY_UI_CONTROL] === UI_CONTROL_MULTI_SELECT || optionItems.length > 0)
      ) {
        const selectedValues = Array.isArray(currentValue) ? currentValue : [];
        inputElement = documentObject.createElement("select");
        inputElement.multiple = true;
        inputElement.size = Math.min(Math.max(optionItems.length, 3), 8);
        optionItems.forEach(function addMultiOption(optionItem) {
          const optionElement = documentObject.createElement("option");
          optionElement.value = optionItem.value;
          optionElement.textContent = optionItem.label;
          optionElement.selected = selectedValues.includes(optionItem.value);
          inputElement.append(optionElement);
        });
      } else if (optionItems.length > 0 && Array.isArray(schemaDefinition.enum)) {
        inputElement = documentObject.createElement("select");
        optionItems.forEach(function addOption(optionItem) {
          const optionElement = documentObject.createElement("option");
          optionElement.value = optionItem.value;
          optionElement.textContent = optionItem.label;
          optionElement.selected = optionItem.value === currentValue;
          inputElement.append(optionElement);
        });
      } else {
        inputElement = documentObject.createElement("input");
        inputElement.type = schemaDefinition.type === "boolean" ? "checkbox" :
          schemaDefinition.type === "integer" ? "number" :
          schemaDefinition["x-secret"] === true ? "password" : "text";
        if (schemaDefinition.minimum !== undefined) {
          inputElement.min = String(schemaDefinition.minimum);
        }
        if (schemaDefinition.maximum !== undefined) {
          inputElement.max = String(schemaDefinition.maximum);
        }
        if (schemaDefinition.type === "boolean") {
          inputElement.checked = Boolean(currentValue);
        } else if (schemaDefinition.type === "array") {
          inputElement.value = Array.isArray(currentValue) ? currentValue.join(", ") : "";
          inputElement.placeholder = "Comma-separated values";
        } else {
          inputElement.value = currentValue === undefined ? "" : String(currentValue);
        }
      }
      inputElement.dataset.configPath = fieldPath;
      inputElement.dataset.schemaType = schemaDefinition.type;
      inputElement.addEventListener("input", collectConfiguration);
      inputElement.addEventListener("change", function collectChangedInput() {
        collectConfiguration();
        if (schemaDefinition[KEY_UI_REFRESH_FORM] === true) {
          renderForm();
        }
      });
      return inputElement;
    }

    /** Render selected schema property entries into the target fieldset. */
    function renderEntries(entries, parentElement, pathPrefix) {
      entries.forEach(function renderProperty(entry) {
        const propertyName = entry[0];
        const propertySchema = entry[1];
        const fieldPath = pathPrefix ? `${pathPrefix}.${propertyName}` : propertyName;
        if (!supportsCurrentUiState(propertySchema) || fieldPath === PROCESS_TRACKING_PATH) {
          return;
        }
        if (propertySchema.type === "object") {
          const fieldsetElement = documentObject.createElement("fieldset");
          const legendElement = documentObject.createElement("legend");
          legendElement.textContent = propertySchema.title || propertyName;
          fieldsetElement.append(legendElement);
          renderEntries(Object.entries(propertySchema.properties || {}), fieldsetElement, fieldPath);
          parentElement.append(fieldsetElement);
          return;
        }
        const inputElement = createInput(propertySchema, fieldPath);
        const labelElement = createFieldRow(propertySchema, inputElement, fieldPath);
        if (propertySchema.type === "boolean") {
          labelElement.classList.add("checkbox-field");
        }
        parentElement.append(labelElement);
      });
    }

    /** Group visible object entries by schema-provided UI section name. */
    function groupEntriesBySection(schemaDefinition, pathPrefix) {
      const groupedEntries = new Map();
      groupedEntries.set("", []);
      Object.entries(schemaDefinition.properties || {}).forEach(function collectEntry(entry) {
        const propertyName = entry[0];
        const propertySchema = entry[1];
        const fieldPath = pathPrefix ? `${pathPrefix}.${propertyName}` : propertyName;
        if (!supportsCurrentUiState(propertySchema) || fieldPath === PROCESS_TRACKING_PATH) {
          return;
        }
        const sectionName = String(propertySchema[KEY_UI_SECTION] || "");
        if (!groupedEntries.has(sectionName)) {
          groupedEntries.set(sectionName, []);
        }
        groupedEntries.get(sectionName).push(entry);
      });
      return groupedEntries;
    }

    /** Render one fieldset section for a schema object and selected entries. */
    function renderFieldset(parentElement, legendText, entries, pathPrefix) {
      if (!entries || entries.length === 0) {
        return;
      }
      const fieldsetElement = documentObject.createElement("fieldset");
      const legendElement = documentObject.createElement("legend");
      legendElement.textContent = legendText;
      fieldsetElement.append(legendElement);
      renderEntries(entries, fieldsetElement, pathPrefix);
      parentElement.append(fieldsetElement);
    }

    /** Recursively render object properties from the server-provided schema. */
    function renderObject(schemaDefinition, parentElement, pathPrefix) {
      Object.entries(schemaDefinition.properties || {}).forEach(function renderProperty(entry) {
        const propertyName = entry[0];
        const propertySchema = entry[1];
        const fieldPath = pathPrefix ? `${pathPrefix}.${propertyName}` : propertyName;
        if (!supportsCurrentUiState(propertySchema) || fieldPath === PROCESS_TRACKING_PATH) {
          return;
        }
        if (propertySchema.type !== "object") {
          renderEntries([entry], parentElement, pathPrefix);
          return;
        }
        const groupedEntries = groupEntriesBySection(propertySchema, fieldPath);
        renderFieldset(
          parentElement,
          propertySchema.title || propertyName,
          groupedEntries.get(""),
          fieldPath,
        );
        groupedEntries.forEach(function renderSection(sectionEntries, sectionName) {
          if (!sectionName) {
            return;
          }
          renderFieldset(parentElement, sectionName, sectionEntries, fieldPath);
        });
      });
    }

    /** Rebuild the form after schema, mode, or loaded configuration changes. */
    function renderForm() {
      const formElement = documentObject.getElementById("configurationForm");
      formElement.replaceChildren();
      renderObject(state.schema, formElement, "");
      documentObject.getElementById("processMode").value = state.mode;
      updatePreview();
    }

    /** Display the current configuration as formatted JSON. */
    function updatePreview() {
      documentObject.getElementById("jsonPreview").textContent = JSON.stringify(
        state.configuration,
        null,
        2,
      );
    }

    /** Update the read-only file display to mirror the selected stored file. */
    function updateSelectedConfigurationDisplay() {
      const displayElement = documentObject.getElementById("selectedConfigurationDisplay");
      const selectedName = String(state.selectedConfigurationName || "").trim();
      displayElement.value = selectedName;
      displayElement.placeholder = selectedName ? "" : "No file selected";
    }

    /** Set a concise success or error status message. */
    function setStatus(message, isError) {
      const statusPanel = documentObject.getElementById("statusPanel");
      const statusMessage = documentObject.querySelector("#statusPanel .status-message");
      const statusElement = documentObject.getElementById("statusMessage");
      statusElement.textContent = message;
      statusMessage.className = isError ? "status-message error" : "status-message success";
      statusPanel.classList.toggle("hidden", !message);
    }

    /** Fetch JSON and throw an API-provided message for unsuccessful responses. */
    async function fetchJson(url, options) {
      const response = await fetchFunction(url, options);
      const responsePayload = await response.json();
      if (!response.ok) {
        throw new Error(responsePayload[KEY_ERROR] || `Request failed (${response.status})`);
      }
      return responsePayload;
    }

    /** Refresh the saved-configuration selector from service storage. */
    async function refreshConfigurationList(selectedName) {
      const responsePayload = await fetchJson(`${API_PREFIX}/configurations`);
      const selectElement = documentObject.getElementById("configurationSelect");
      selectElement.replaceChildren();
      const newOption = documentObject.createElement("option");
      newOption.value = "";
      newOption.textContent = "New configuration";
      selectElement.append(newOption);
      responsePayload[KEY_CONFIGURATIONS].forEach(function addConfiguration(configurationName) {
        const optionElement = documentObject.createElement("option");
        optionElement.value = configurationName;
        optionElement.textContent = configurationName;
        optionElement.selected = configurationName === selectedName;
        selectElement.append(optionElement);
      });
      state.selectedConfigurationName = selectedName || "";
      updateSelectedConfigurationDisplay();
    }

    /** Reveal the saved-file selector, refresh available files, and focus the picker. */
    async function browseConfigurationFiles() {
      const browserPanel = documentObject.getElementById("configurationBrowserPanel");
      const selectElement = documentObject.getElementById("configurationSelect");
      try {
        await refreshConfigurationList(state.selectedConfigurationName);
      } catch (error) {
        setStatus(error.message, true);
      }
      browserPanel.classList.remove("hidden");
      selectElement.focus();
      const savedConfigurationCount = Math.max(selectElement.options.length - 1, 0);
      if (savedConfigurationCount > 0) {
        setStatus(`Choose from ${savedConfigurationCount} saved configuration file(s).`, false);
        return;
      }
      setStatus("No saved configuration files were found. Use Save as to create one.", false);
    }

    /** Synchronize the read-only file display and save target from the selector. */
    function selectConfigurationName(configurationName) {
      state.selectedConfigurationName = configurationName || "";
      updateSelectedConfigurationDisplay();
      if (configurationName) {
        documentObject.getElementById("configurationName").value = configurationName;
      }
    }

    /** Start a new configuration from schema defaults and clear saved-file selection. */
    function startNewConfiguration() {
      state.selectedConfigurationName = "";
      documentObject.getElementById("configurationSelect").value = "";
      documentObject.getElementById("configurationName").value = "opamp-consumer.json";
      state.configuration = defaultsFromSchema(state.schema) || {};
      state.mode = getPathValue(state.configuration, PROCESS_TRACKING_PATH) || "Supervisor";
      renderForm();
      updateSelectedConfigurationDisplay();
      setStatus("Started a new configuration from schema defaults.", false);
    }

    /** Load the selected file into schema-generated controls. */
    async function loadSelectedConfiguration() {
      const selectElement = documentObject.getElementById("configurationSelect");
      if (!selectElement.value) {
        startNewConfiguration();
        return;
      }
      try {
        const encodedName = selectElement.value.split("/").map(encodeURIComponent).join("/");
        const responsePayload = await fetchJson(`${API_PREFIX}/configurations/${encodedName}`);
        state.configuration = responsePayload[KEY_CONFIGURATION];
        state.mode = getPathValue(state.configuration, PROCESS_TRACKING_PATH) || "Supervisor";
        documentObject.getElementById("configurationName").value = responsePayload[KEY_NAME];
        state.selectedConfigurationName = responsePayload[KEY_NAME];
        updateSelectedConfigurationDisplay();
        renderForm();
        setStatus(`Loaded ${responsePayload[KEY_NAME]}.`, false);
      } catch (error) {
        setStatus(error.message, true);
      }
    }

    /** Validate the current configuration and report field paths. */
    async function validateConfiguration() {
      collectConfiguration();
      try {
        const requestBody = {};
        requestBody[KEY_CONFIGURATION] = state.configuration;
        const responsePayload = await fetchJson(`${API_PREFIX}/validate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestBody),
        });
        if (responsePayload[KEY_VALID]) {
          setStatus("Configuration is valid.", false);
          return true;
        }
        const messages = responsePayload[KEY_ERRORS].map(function formatError(errorItem) {
          return `${errorItem[KEY_PATH] || "configuration"}: ${errorItem[KEY_MESSAGE]}`;
        });
        setStatus(messages.join("\n"), true);
        return false;
      } catch (error) {
        setStatus(error.message, true);
        return false;
      }
    }

    /** Save the current configuration using the selected relative JSON name. */
    async function saveConfiguration() {
      collectConfiguration();
      const configurationName = documentObject.getElementById("configurationName").value.trim();
      if (!configurationName) {
        setStatus("Enter a .json file name before saving.", true);
        return;
      }
      try {
        const encodedName = configurationName.split("/").map(encodeURIComponent).join("/");
        const requestBody = {};
        requestBody[KEY_CONFIGURATION] = state.configuration;
        const responsePayload = await fetchJson(`${API_PREFIX}/configurations/${encodedName}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestBody),
        });
        await refreshConfigurationList(responsePayload[KEY_NAME]);
        documentObject.getElementById("configurationName").value = responsePayload[KEY_NAME];
        setStatus(`Saved ${responsePayload[KEY_NAME]}.`, false);
      } catch (error) {
        setStatus(error.message, true);
      }
    }

    /** Switch process ownership mode and rebuild mode-specific controls. */
    function setMode(modeName) {
      collectConfiguration();
      state.mode = modeName;
      setPathValue(state.configuration, PROCESS_TRACKING_PATH, modeName);
      renderForm();
    }

    /** Load schema defaults and the available file list without showing startup status. */
    async function initialize() {
      try {
        const schemaPayload = await fetchJson(`${API_PREFIX}/schema`);
        state.schema = schemaPayload[KEY_SCHEMA];
        state.configuration = defaultsFromSchema(state.schema) || {};
        state.mode = getPathValue(state.configuration, PROCESS_TRACKING_PATH) || "Supervisor";
        renderForm();
        await refreshConfigurationList("");
      } catch (error) {
        setStatus(error.message, true);
      }
    }

    return {
      initialize,
      loadSelectedConfiguration,
      saveConfiguration,
      browseConfigurationFiles,
      setMode,
      selectConfigurationName,
      startNewConfiguration,
      validateConfiguration,
    };
  }

  globalObject.ClientConfigGeneratorFunctions = { create };
})(window);
