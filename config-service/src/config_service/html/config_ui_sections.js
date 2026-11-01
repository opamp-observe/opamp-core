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

  function create(deps) {
    // Renderer for Service + Parser sections.
    // Plugin-specific rendering lives in config_ui_plugins.js.
    var state = deps.state;
    var el = deps.el;
    var saveDoc = deps.saveDoc;
    var renderAll = deps.renderAll;
    var ensureDoc = deps.ensureDoc;
    var isReadOnlyMode = deps.isReadOnlyMode;
    var createCommentToggleButton = deps.createCommentToggleButton;
    var createCommentEditorPanel = deps.createCommentEditorPanel;
    var renderFieldRow = deps.renderFieldRow;
    var createFieldHelpButton = deps.createFieldHelpButton;
    var applyRequiredLabelStyle = deps.applyRequiredLabelStyle;
    var parseServiceValueByType = deps.parseServiceValueByType;
    var parseServiceValue = deps.parseServiceValue;
    var normalizeEnumAliasValue = deps.normalizeEnumAliasValue;
    var getEnumOptions = deps.getEnumOptions;
    var prepareCodeTextarea = deps.prepareCodeTextarea;
    var parserFormatFields = deps.parserFormatFields;
    var getServiceOptionByKey = deps.getServiceOptionByKey;
    var getParserFormatByKey = deps.getParserFormatByKey;
    var defaultForField = deps.defaultForField;

function renderParserCard(parserInstance, parserIndex) {
    // Schema-driven parser card with required and optional field handling.
    var parserFormat = getParserFormatByKey(String(parserInstance.format || ""));
    var card = document.createElement("div");
    card.className = "plugin-card";

    var key = "parser:" + parserIndex;
    var collapsed = Boolean(state.collapse[key]);

    var head = document.createElement("div");
    head.className = "plugin-head";

    var left = document.createElement("div");
    left.className = "plugin-head-main";
    var title = document.createElement("strong");
    title.textContent = "#" + (parserIndex + 1) + " " + String(parserInstance.name || "(unnamed)") + " (" + String(parserInstance.format || "unknown") + ")";
    left.appendChild(title);
    head.appendChild(left);

    var actions = document.createElement("div");
    actions.className = "plugin-actions";
    actions.appendChild(createCommentToggleButton(key + ":comment", parserInstance, "", "parser comment editor"));

    var collapseBtn = document.createElement("button");
    collapseBtn.type = "button";
    collapseBtn.textContent = collapsed ? "Expand" : "Collapse";
    collapseBtn.addEventListener("click", function () {
      state.collapse[key] = !collapsed;
      renderAll();
    });
    actions.appendChild(collapseBtn);

    var removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "-";
    removeBtn.className = "icon-remove";
    removeBtn.title = "Remove parser";
    removeBtn.disabled = isReadOnlyMode();
    removeBtn.addEventListener("click", function () {
      state.doc.config.parsers.splice(parserIndex, 1);
      saveDoc();
      renderAll();
    });
    actions.appendChild(removeBtn);

    head.appendChild(actions);
    card.appendChild(head);

    if (collapsed) {
      return card;
    }

    card.appendChild(createCommentEditorPanel(parserInstance, "Parser Comment", "", key + ":comment"));

    var body = document.createElement("div");
    body.className = "field-grid";

    body.appendChild(
      renderFieldRow(parserInstance, {
        name: "name",
        data_type: "string",
        required: true,
        description: "Sets the name of your parser.",
        reference: parserFormat ? String(parserFormat.doc_url || "") : "",
      }, {
        optional: false,
        focusKey: key + ":name",
        commentTarget: parserInstance,
        commentFieldName: "name",
        commentToggleKey: key + ":name:comment",
      })
    );

    var formatBlock = document.createElement("div");
    formatBlock.className = "field-block";
    var formatRow = document.createElement("div");
    formatRow.className = "field-row";
    var formatLabel = document.createElement("label");
    formatLabel.textContent = "format";
    applyRequiredLabelStyle(formatLabel, true);
    formatRow.appendChild(formatLabel);
    var formatValue = document.createElement("span");
    formatValue.className = "readonly-value";
    formatValue.textContent = String(parserInstance.format || "");
    formatRow.appendChild(formatValue);
    formatRow.appendChild(
      createFieldHelpButton(
        {
          name: "format",
          description: parserFormat ? String(parserFormat.description || "Parser format.") : "Parser format.",
          reference: parserFormat ? String(parserFormat.doc_url || "") : "",
        },
        false
      )
    );
    formatBlock.appendChild(formatRow);
    body.appendChild(formatBlock);

    var fields = parserFormatFields(parserFormat);
    var requiredFields = fields.filter(function (field) {
      return field.required;
    });
    var currentOptionalFields = fields.filter(function (field) {
      return !field.required && Object.prototype.hasOwnProperty.call(parserInstance, field.name);
    });

    requiredFields.forEach(function (field) {
      body.appendChild(
        renderFieldRow(parserInstance, field, {
          optional: false,
          focusKey: key + ":" + field.name,
          commentTarget: parserInstance,
          commentFieldName: field.name,
          commentToggleKey: key + ":" + field.name + ":comment",
        })
      );
    });

    currentOptionalFields.forEach(function (field) {
      body.appendChild(
        renderFieldRow(parserInstance, field, {
          optional: true,
          focusKey: key + ":" + field.name,
          commentTarget: parserInstance,
          commentFieldName: field.name,
          commentToggleKey: key + ":" + field.name + ":comment",
          onRemove: function () {
            delete parserInstance[field.name];
            saveDoc();
            renderAll();
          },
        })
      );
    });

    card.appendChild(body);

    var missingOptional = fields.filter(function (field) {
      return !field.required && !Object.prototype.hasOwnProperty.call(parserInstance, field.name);
    });
    if (missingOptional.length > 0) {
      var optionalRow = document.createElement("div");
      optionalRow.className = "optional-row";
      var optionalSel = document.createElement("select");
      var emptyOpt = document.createElement("option");
      emptyOpt.value = "";
      emptyOpt.textContent = "Select optional parser attribute...";
      optionalSel.appendChild(emptyOpt);
      missingOptional.forEach(function (field) {
        var option = document.createElement("option");
        option.value = field.name;
        option.textContent = field.name;
        optionalSel.appendChild(option);
      });
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
        parserInstance[field.name] = defaultForField(field);
        state.pendingFocusFieldKey = key + ":" + field.name;
        saveDoc();
        renderAll();
      });
      optionalRow.appendChild(addOptional);
      card.appendChild(optionalRow);
    }

    return card;
  }

  function renderParsers() {
    ensureDoc();
    if (!el.parserList) {
      return;
    }
    el.parserList.innerHTML = "";
    if (!Array.isArray(state.doc.config.parsers) || state.doc.config.parsers.length === 0) {
      var empty = document.createElement("p");
      empty.textContent = "No parsers configured.";
      el.parserList.appendChild(empty);
      return;
    }
    state.doc.config.parsers.forEach(function (parserInstance, parserIndex) {
      el.parserList.appendChild(renderParserCard(parserInstance, parserIndex));
    });
  }

  function renderService() {
    // Service section is key/value based but enriched with schema metadata
    // where available (enum values, descriptions, references).
    ensureDoc();
    el.serviceList.innerHTML = "";
    var entries = Object.entries(state.doc.config.service || {}).filter(function (entry) {
      return entry[0] !== "_meta";
    });
    if (entries.length === 0) {
      var empty = document.createElement("p");
      empty.textContent = "No service settings configured.";
      el.serviceList.appendChild(empty);
      return;
    }

    var card = document.createElement("div");
    card.className = "plugin-card service-card";

    var head = document.createElement("div");
    head.className = "plugin-head";

    var left = document.createElement("div");
    left.className = "plugin-head-main";

    head.appendChild(left);

    var actions = document.createElement("div");
    actions.className = "plugin-actions";
    var collapseBtn = document.createElement("button");
    collapseBtn.type = "button";
    collapseBtn.textContent = state.serviceCollapsed ? "Expand" : "Collapse";
    collapseBtn.addEventListener("click", function () {
      state.serviceCollapsed = !state.serviceCollapsed;
      renderService();
    });
    actions.appendChild(collapseBtn);
    head.appendChild(actions);

    card.appendChild(head);

    if (state.serviceCollapsed) {
      el.serviceList.appendChild(card);
      return;
    }

    var body = document.createElement("div");
    body.className = "field-grid";

    entries.forEach(function (entry) {
      var key = entry[0];
      var value = entry[1];
      var knownServiceOption = getServiceOptionByKey(key);
      var row = document.createElement("div");
      row.className = "service-row";
      if (knownServiceOption) {
        row.title = knownServiceOption.description || "";
      }

      var keyInput = document.createElement("input");
      keyInput.value = key;
      keyInput.disabled = isReadOnlyMode();
      keyInput.addEventListener("change", function () {
        var newKey = keyInput.value.trim();
        if (!newKey || newKey === key) {
          keyInput.value = key;
          return;
        }
        state.doc.config.service[newKey] = state.doc.config.service[key];
        delete state.doc.config.service[key];
        saveDoc();
        renderService();
      });
      row.appendChild(keyInput);

      var valueInput = document.createElement("input");
      var serviceDataType = knownServiceOption ? String(knownServiceOption.data_type || "").toLowerCase() : "";
      if (knownServiceOption && serviceDataType === "enum") {
        valueInput = document.createElement("select");
        var serviceEnumOptions = getEnumOptions(knownServiceOption);
        serviceEnumOptions.forEach(function (enumValue) {
          var option = document.createElement("option");
          option.value = String(enumValue);
          option.textContent = String(enumValue);
          valueInput.appendChild(option);
        });
        valueInput.value = String(normalizeEnumAliasValue(serviceEnumOptions, value));
        valueInput.disabled = isReadOnlyMode();
      } else if (knownServiceOption && serviceDataType === "code") {
        valueInput = document.createElement("textarea");
        if (typeof value === "object") {
          try {
            valueInput.value = JSON.stringify(value, null, 2);
          } catch (_serializeError) {
            valueInput.value = String(value);
          }
        } else {
          valueInput.value = String(value);
        }
        prepareCodeTextarea(valueInput);
        valueInput.disabled = isReadOnlyMode();
      } else {
        valueInput = document.createElement("input");
        if (typeof value === "object") {
          try {
            valueInput.value = JSON.stringify(value);
          } catch (_serializeError) {
            valueInput.value = String(value);
          }
        } else {
          valueInput.value = String(value);
        }
        valueInput.disabled = isReadOnlyMode();
      }
      valueInput.addEventListener("change", function () {
        if (knownServiceOption) {
          state.doc.config.service[key] = parseServiceValueByType(
            valueInput.value,
            knownServiceOption.data_type
          );
        } else {
          state.doc.config.service[key] = parseServiceValue(valueInput.value);
        }
        saveDoc();
      });
      row.appendChild(valueInput);

      row.appendChild(
        createFieldHelpButton(
          {
            name: key,
            description: knownServiceOption ? knownServiceOption.description : "No linked service attribute documentation available.",
            reference: knownServiceOption ? knownServiceOption.reference : "",
          },
          false
        )
      );

      row.appendChild(
      (function () {
        var removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.textContent = "-";
        removeBtn.className = "icon-remove right-align";
        removeBtn.title = "Remove service field";
        removeBtn.disabled = isReadOnlyMode();
        removeBtn.addEventListener("click", function () {
          delete state.doc.config.service[key];
          saveDoc();
          renderService();
        });
        return removeBtn;
      })()
      );

      body.appendChild(row);
    });

    card.appendChild(body);
    el.serviceList.appendChild(card);
  }

    return {
      renderParsers: renderParsers,
      renderService: renderService,
    };
  }

  global.ConfigServiceUiSections = {
    create: create,
  };
})(window);
