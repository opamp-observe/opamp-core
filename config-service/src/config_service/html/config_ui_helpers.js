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

(function (global) {
  "use strict";

  function prependConfigHeader(text, configType, version, commentPrefix) {
    // Adds a stable metadata header used when files are reloaded later.
    var prefix = commentPrefix || "#";
    var header = [
      prefix + " config-service: config_type=" + String(configType || ""),
      prefix + " config-service: version=" + String(version || ""),
    ].join("\n");
    return header + "\n" + String(text || "");
  }

  function versionAtLeast(actual, minimum) {
    // Semantic-ish numeric compare that tolerates uneven dot segment lengths.
    var actualParts = String(actual || "").split(".").map(function (part) {
      return Number(part || 0);
    });
    var minimumParts = String(minimum || "").split(".").map(function (part) {
      return Number(part || 0);
    });
    var length = Math.max(actualParts.length, minimumParts.length);
    for (var index = 0; index < length; index += 1) {
      var left = actualParts[index] || 0;
      var right = minimumParts[index] || 0;
      if (left > right) {
        return true;
      }
      if (left < right) {
        return false;
      }
    }
    return true;
  }

  function getEnumOptions(field) {
    if (!field || typeof field !== "object") {
      return [];
    }
    if (Array.isArray(field.enum_options)) {
      return field.enum_options.slice();
    }
    if (Array.isArray(field.called_enum_options)) {
      return field.called_enum_options.slice();
    }
    return [];
  }

  function defaultForField(field) {
    var enumOptions = getEnumOptions(field);
    if (enumOptions.length > 0) {
      if (Object.prototype.hasOwnProperty.call(field, "default") && field.default !== "") {
        return field.default;
      }
      return enumOptions[0];
    }
    if (Object.prototype.hasOwnProperty.call(field, "default")) {
      return field.default;
    }
    var dataType = String(field.data_type || "string").toLowerCase();
    if (dataType === "integer" || dataType === "number" || dataType === "float") {
      return 0;
    }
    if (dataType === "boolean") {
      return false;
    }
    if (dataType === "array" || dataType === "list") {
      return [];
    }
    if (dataType === "object" || dataType === "map") {
      return {};
    }
    return "";
  }

  function normalizeEnumAliasValue(enumOptions, value) {
    // Maps common bool-like aliases to enum values for on/off style fields.
    var options = Array.isArray(enumOptions) ? enumOptions.map(function (item) { return String(item); }) : [];
    if (options.length === 0) {
      return value;
    }
    var raw = value;
    if (raw === undefined || raw === null) {
      return raw;
    }
    var text = String(raw).trim();
    var lower = text.toLowerCase();
    if (options.indexOf("on") !== -1 && options.indexOf("off") !== -1) {
      if (raw === true || lower === "true" || lower === "1" || lower === "yes" || lower === "on") {
        return "on";
      }
      if (raw === false || lower === "false" || lower === "0" || lower === "no" || lower === "off") {
        return "off";
      }
    }
    return text;
  }

  function parseTextValue(raw, dataType) {
    var normalizedDataType = String(dataType || "string").toLowerCase();
    if (normalizedDataType === "integer") {
      var integerValue = Number(raw);
      return Number.isFinite(integerValue) ? Math.trunc(integerValue) : 0;
    }
    if (normalizedDataType === "number" || normalizedDataType === "float") {
      var numberValue = Number(raw);
      return Number.isFinite(numberValue) ? numberValue : 0;
    }
    if (
      normalizedDataType === "array" ||
      normalizedDataType === "list" ||
      normalizedDataType === "object" ||
      normalizedDataType === "map"
    ) {
      try {
        return raw
          ? JSON.parse(raw)
          : normalizedDataType === "array" || normalizedDataType === "list"
            ? []
            : {};
      } catch (_parseError) {
        return raw;
      }
    }
    return raw;
  }

  function parseServiceValue(raw) {
    // Best-effort parse used by free-form service/env inputs.
    var textValue = String(raw || "").trim();
    if (textValue === "true") {
      return true;
    }
    if (textValue === "false") {
      return false;
    }
    if (textValue !== "" && !Number.isNaN(Number(textValue))) {
      return Number(textValue);
    }
    try {
      if (
        (textValue.startsWith("{") && textValue.endsWith("}")) ||
        (textValue.startsWith("[") && textValue.endsWith("]"))
      ) {
        return JSON.parse(textValue);
      }
    } catch (_parseError) {
      return raw;
    }
    return raw;
  }

  function parseServiceValueByType(raw, dataType) {
    // Type-aware parse for schema-defined fields.
    var normalizedDataType = String(dataType || "string").toLowerCase();
    if (normalizedDataType === "enum") {
      return String(raw || "");
    }
    if (normalizedDataType === "boolean") {
      var normalizedBooleanText = String(raw || "").trim().toLowerCase();
      return (
        normalizedBooleanText === "true" ||
        normalizedBooleanText === "1" ||
        normalizedBooleanText === "yes" ||
        normalizedBooleanText === "on"
      );
    }
    if (normalizedDataType === "integer") {
      var integerValue = Number(raw);
      return Number.isFinite(integerValue) ? Math.trunc(integerValue) : 0;
    }
    if (normalizedDataType === "number" || normalizedDataType === "float") {
      var floatValue = Number(raw);
      return Number.isFinite(floatValue) ? floatValue : 0;
    }
    return parseServiceValue(raw);
  }

  function fieldInputValue(value, dataType) {
    var normalizedDataType = String(dataType || "string").toLowerCase();
    if (
      normalizedDataType === "array" ||
      normalizedDataType === "list" ||
      normalizedDataType === "object" ||
      normalizedDataType === "map"
    ) {
      try {
        return JSON.stringify(value === undefined ? null : value);
      } catch (_serializeError) {
        return String(value || "");
      }
    }
    if (value === undefined || value === null) {
      return "";
    }
    return String(value);
  }

  function parseFlexibleRouteValue(raw) {
    // Route rules can hold scalar or structured values; parse conservatively.
    var text = String(raw || "").trim();
    if (text === "") {
      return "";
    }
    try {
      if (
        (text.startsWith("[") && text.endsWith("]")) ||
        (text.startsWith("{") && text.endsWith("}")) ||
        text === "true" ||
        text === "false" ||
        text === "null"
      ) {
        return JSON.parse(text);
      }
    } catch (_parseError) {
      return raw;
    }
    if (!Number.isNaN(Number(text)) && text !== "") {
      return Number(text);
    }
    return raw;
  }

  function formatFlexibleRouteValue(value) {
    if (value === undefined || value === null) {
      return value === null ? "null" : "";
    }
    if (typeof value === "object") {
      try {
        return JSON.stringify(value);
      } catch (_serializeError) {
        return String(value);
      }
    }
    return String(value);
  }

  global.ConfigServiceUiHelpers = {
    prependConfigHeader: prependConfigHeader,
    versionAtLeast: versionAtLeast,
    getEnumOptions: getEnumOptions,
    defaultForField: defaultForField,
    normalizeEnumAliasValue: normalizeEnumAliasValue,
    parseTextValue: parseTextValue,
    parseServiceValue: parseServiceValue,
    parseServiceValueByType: parseServiceValueByType,
    fieldInputValue: fieldInputValue,
    parseFlexibleRouteValue: parseFlexibleRouteValue,
    formatFlexibleRouteValue: formatFlexibleRouteValue,
  };
})(window);
