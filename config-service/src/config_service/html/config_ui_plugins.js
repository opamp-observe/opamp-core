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
    // Renderer for plugin cards and Fluent Bit-specific route/processor editors.
    var state = deps.state;
    var saveDoc = deps.saveDoc;
    var renderAll = deps.renderAll;
    var isReadOnlyMode = deps.isReadOnlyMode;
    var renderFieldRow = deps.renderFieldRow;
    var createCommentToggleButton = deps.createCommentToggleButton;
    var createCommentEditorPanel = deps.createCommentEditorPanel;
    var defaultForField = deps.defaultForField;
    var getPluginDefinition = deps.getPluginDefinition;
    var movePluginToSection = deps.movePluginToSection;
    var moveWithinPipeline = deps.moveWithinPipeline;
    var setValidationText = deps.setValidationText;
    var ensureDoc = deps.ensureDoc;
    var ensureFluentbitProcessors = deps.ensureFluentbitProcessors;
    var fluentbitProcessorRoot = deps.fluentbitProcessorRoot;
    var fluentbitProcessorSignals = deps.fluentbitProcessorSignals;
    var fluentbitSignalProcessorMap = deps.fluentbitSignalProcessorMap;
    var fluentbitProcessorDefinition = deps.fluentbitProcessorDefinition;
    var ensureFluentbitRoute = deps.ensureFluentbitRoute;
    var fluentbitRouteRoot = deps.fluentbitRouteRoot;
    var fluentbitRouteSignals = deps.fluentbitRouteSignals;
    var fluentbitRouteSignalByName = deps.fluentbitRouteSignalByName;
    var createFieldHelpButton = deps.createFieldHelpButton;
    var applyRequiredLabelStyle = deps.applyRequiredLabelStyle;
    var parseFlexibleRouteValue = deps.parseFlexibleRouteValue;
    var formatFlexibleRouteValue = deps.formatFlexibleRouteValue;

function renderProcessorCondition(instance, procPathPrefix) {
    // Condition block is nested JSON-like data, so we use a compact focused UI.
    var frame = document.createElement("div");
    frame.className = "nested-panel";
    var title = document.createElement("h4");
    title.textContent = "Condition";
    frame.appendChild(title);

    var row = document.createElement("div");
    row.className = "field-row";

    var opLabel = document.createElement("label");
    opLabel.textContent = "Operator";
    row.appendChild(opLabel);

    var opSelect = document.createElement("select");
    ["and", "or"].forEach(function (value) {
      var option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      opSelect.appendChild(option);
    });
    opSelect.value = String((instance.condition && instance.condition.op) || "and");
    opSelect.addEventListener("change", function () {
      if (isReadOnlyMode()) {
        return;
      }
      if (!instance.condition || typeof instance.condition !== "object") {
        instance.condition = { op: "and", rules: [] };
      }
      instance.condition.op = opSelect.value;
      saveDoc();
    });
    opSelect.disabled = isReadOnlyMode();
    row.appendChild(opSelect);
    frame.appendChild(row);

    var rulesRow = document.createElement("div");
    rulesRow.className = "field-row";
    var rulesLabel = document.createElement("label");
    rulesLabel.textContent = "Rules JSON";
    rulesRow.appendChild(rulesLabel);
    var rulesInput = document.createElement("textarea");
    try {
      rulesInput.value = JSON.stringify((instance.condition && instance.condition.rules) || [], null, 2);
    } catch (_serializeError) {
      rulesInput.value = "[]";
    }
    rulesInput.placeholder = '[{"field":"$level","op":"eq","value":"error"}]';
    rulesInput.addEventListener("change", function () {
      if (isReadOnlyMode()) {
        return;
      }
      if (!instance.condition || typeof instance.condition !== "object") {
        instance.condition = { op: opSelect.value, rules: [] };
      }
      try {
        var parsed = JSON.parse(rulesInput.value || "[]");
        instance.condition.rules = Array.isArray(parsed) ? parsed : [];
      } catch (_err) {
        instance.condition.rules = [];
      }
      saveDoc();
    });
    rulesInput.disabled = isReadOnlyMode();
    rulesRow.appendChild(rulesInput);
    frame.appendChild(rulesRow);

    var removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "-";
    removeBtn.className = "icon-remove";
    removeBtn.title = "Remove condition";
    removeBtn.disabled = isReadOnlyMode();
    removeBtn.addEventListener("click", function () {
      delete instance.condition;
      saveDoc();
      renderAll();
    });
    frame.appendChild(removeBtn);

    return frame;
  }

  function renderProcessorCard(signalName, processorIndex, processorInstance, keyPrefix, collection, processorPath) {
    var procDef = fluentbitProcessorDefinition(signalName, processorInstance.name);
    var card = document.createElement("div");
    card.className = "plugin-card";

    var key = keyPrefix + ":processor:" + signalName + ":" + processorIndex;
    var collapsed = Boolean(state.collapse[key]);

    var head = document.createElement("div");
    head.className = "plugin-head";

    var left = document.createElement("div");
    left.className = "plugin-head-main";
    var title = document.createElement("strong");
    title.textContent = "#" + (processorIndex + 1) + " " + processorInstance.name + " (" + signalName + ")";
    left.appendChild(title);
    head.appendChild(left);

    var actions = document.createElement("div");
    actions.className = "plugin-actions";

    actions.appendChild(
      createCommentToggleButton(
        key + ":comment",
        processorInstance,
        "",
        "processor comment editor"
      )
    );

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
    removeBtn.title = "Remove processor";
    removeBtn.disabled = isReadOnlyMode();
    removeBtn.addEventListener("click", function () {
      collection.splice(processorIndex, 1);
      saveDoc();
      renderAll();
    });
    actions.appendChild(removeBtn);

    head.appendChild(actions);
    card.appendChild(head);

    if (collapsed) {
      return card;
    }

    var fieldsWrap = document.createElement("div");
    fieldsWrap.className = "field-grid";
    var fields = (procDef && procDef.fields) || [];
    var requiredFields = fields.filter(function (field) {
      return field.required;
    });
    var currentOptionalFields = fields.filter(function (field) {
      return !field.required && Object.prototype.hasOwnProperty.call(processorInstance, field.name);
    });

    requiredFields.forEach(function (field) {
      fieldsWrap.appendChild(
        renderFieldRow(processorInstance, field, {
          optional: false,
          focusKey: key + ":" + field.name,
          commentTarget: processorInstance,
          commentFieldName: field.name,
          commentToggleKey: key + ":" + field.name + ":comment",
        })
      );
    });

    currentOptionalFields.forEach(function (field) {
      fieldsWrap.appendChild(
        renderFieldRow(processorInstance, field, {
          optional: true,
          focusKey: key + ":" + field.name,
          commentTarget: processorInstance,
          commentFieldName: field.name,
          commentToggleKey: key + ":" + field.name + ":comment",
          onRemove: function () {
            delete processorInstance[field.name];
            saveDoc();
            renderAll();
          },
        })
      );
    });
    card.appendChild(createCommentEditorPanel(processorInstance, "Processor Comment", "", key + ":comment"));
    card.appendChild(fieldsWrap);

    var missingOptional = fields.filter(function (field) {
      return !field.required && !Object.prototype.hasOwnProperty.call(processorInstance, field.name);
    });
    if (missingOptional.length > 0) {
      var optionalRow = document.createElement("div");
      optionalRow.className = "optional-row";
      var optionalSel = document.createElement("select");
      var emptyOpt = document.createElement("option");
      emptyOpt.value = "";
      emptyOpt.textContent = "Select optional processor attribute...";
      optionalSel.appendChild(emptyOpt);
      missingOptional.forEach(function (field) {
        var opt = document.createElement("option");
        opt.value = field.name;
        opt.textContent = field.name;
        optionalSel.appendChild(opt);
      });
      optionalRow.appendChild(optionalSel);

      var optionalDivider = document.createElement("span");
      optionalDivider.className = "optional-divider";
      optionalDivider.setAttribute("aria-hidden", "true");
      optionalRow.appendChild(optionalDivider);

      var addOptional = document.createElement("button");
      addOptional.type = "button";
      addOptional.textContent = "Add Optional";
      addOptional.addEventListener("click", function () {
        var selected = optionalSel.value;
        if (!selected) {
          return;
        }
        var field = fields.find(function (item) {
          return item.name === selected;
        });
        if (!field) {
          return;
        }
        processorInstance[field.name] = defaultForField(field);
        saveDoc();
        renderAll();
      });
      optionalRow.appendChild(addOptional);
      card.appendChild(optionalRow);
    }

    if (procDef && procDef.supports_condition) {
      var conditionWrap = document.createElement("div");
      conditionWrap.className = "nested-panel";
      if (processorInstance.condition && typeof processorInstance.condition === "object") {
        card.appendChild(renderProcessorCondition(processorInstance, key));
      } else {
        var addCondition = document.createElement("button");
        addCondition.type = "button";
        addCondition.textContent = "Add Condition";
        addCondition.addEventListener("click", function () {
          processorInstance.condition = { op: "and", rules: [] };
          saveDoc();
          renderAll();
        });
        conditionWrap.appendChild(addCondition);
        card.appendChild(conditionWrap);
      }
    }

    return card;
  }

  function renderFluentbitProcessorsPanel(section, index, instance, keyPrefix, pluginPath) {
    // Fluent Bit processors are grouped by signal type (logs/metrics/traces).
    ensureFluentbitProcessors(instance);

    var frame = document.createElement("div");
    frame.className = "nested-panel";

    var heading = document.createElement("h4");
    heading.textContent = "Processors";
    frame.appendChild(heading);

    var controls = document.createElement("div");
    controls.className = "row";

    var signalLabel = document.createElement("label");
    signalLabel.textContent = "Signal";
    var signalSelect = document.createElement("select");
    Object.keys(fluentbitProcessorSignals()).forEach(function (signalName) {
      var option = document.createElement("option");
      option.value = signalName;
      option.textContent = signalName;
      signalSelect.appendChild(option);
    });
    signalLabel.appendChild(signalSelect);
    controls.appendChild(signalLabel);

    var procLabel = document.createElement("label");
    procLabel.textContent = "Processor";
    var procSelect = document.createElement("select");
    procLabel.appendChild(procSelect);
    controls.appendChild(procLabel);

    var helpBtn = document.createElement("button");
    helpBtn.type = "button";
    helpBtn.textContent = "?";
    helpBtn.className = "icon-help";
    controls.appendChild(helpBtn);

    var addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.textContent = "Add Processor";
    controls.appendChild(addBtn);

    function refreshProcessorSelect() {
      var signalName = signalSelect.value;
      var available = fluentbitSignalProcessorMap(signalName);
      var names = Object.keys(available).sort();
      procSelect.innerHTML = "";
      names.forEach(function (name) {
        var option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        procSelect.appendChild(option);
      });
      var def = names.length > 0 ? available[names[0]] : null;
      helpBtn.disabled = !(def && def.doc_url);
      helpBtn.title = def && def.description ? def.description : "Open processor documentation.";
    }

    signalSelect.addEventListener("change", refreshProcessorSelect);
    procSelect.addEventListener("change", function () {
      var def = fluentbitProcessorDefinition(signalSelect.value, procSelect.value);
      helpBtn.disabled = !(def && def.doc_url);
      helpBtn.title = def && def.description ? def.description : "Open processor documentation.";
    });
    helpBtn.addEventListener("click", function () {
      var def = fluentbitProcessorDefinition(signalSelect.value, procSelect.value);
      if (!def || !def.doc_url) {
        setValidationText("No linked processor documentation is available for the current selection.");
        return;
      }
      window.open(def.doc_url, "_blank", "noopener,noreferrer");
    });
    addBtn.addEventListener("click", function () {
      var signalName = signalSelect.value;
      var processorName = procSelect.value;
      var def = fluentbitProcessorDefinition(signalName, processorName);
      if (!def) {
        return;
      }
      var item = { name: processorName };
      (def.fields || []).forEach(function (field) {
        if (field.required) {
          item[field.name] = defaultForField(field);
        }
      });
      instance.processors[signalName].push(item);
      saveDoc();
      renderAll();
    });
    refreshProcessorSelect();
    frame.appendChild(controls);

    ["logs", "metrics", "traces"].forEach(function (signalName) {
      var items = instance.processors[signalName];
      if (!Array.isArray(items) || items.length === 0) {
        return;
      }
      var signalWrap = document.createElement("div");
      signalWrap.className = "container-stack";
      var signalTitle = document.createElement("h4");
      signalTitle.textContent = signalName;
      signalWrap.appendChild(signalTitle);
      items.forEach(function (processorInstance, processorIndex) {
        signalWrap.appendChild(
          renderProcessorCard(
            signalName,
            processorIndex,
            processorInstance,
            keyPrefix + ":" + section + ":" + index,
            items,
            pluginPath + ".processors." + signalName + "[" + processorIndex + "]"
          )
        );
      });
      frame.appendChild(signalWrap);
    });

    return frame;
  }

  function renderAddFluentbitProcessorsPanel(instance) {
    var root = fluentbitProcessorRoot() || {};
    var addProcessorsWrap = document.createElement("div");
    addProcessorsWrap.className = "nested-panel";

    var addProcessorsHead = document.createElement("div");
    addProcessorsHead.className = "plugin-head";
    var addProcessorsHeadMain = document.createElement("div");
    addProcessorsHeadMain.className = "plugin-head-main";
    var addProcessorsTitle = document.createElement("h4");
    addProcessorsTitle.textContent = "Processors";
    addProcessorsHeadMain.appendChild(addProcessorsTitle);
    addProcessorsHead.appendChild(addProcessorsHeadMain);

    var addProcessorsActions = document.createElement("div");
    addProcessorsActions.className = "plugin-actions";
    var addProcessorsHelp = document.createElement("button");
    addProcessorsHelp.type = "button";
    addProcessorsHelp.textContent = "?";
    addProcessorsHelp.className = "icon-help";
    addProcessorsHelp.title = String(root.description || "Open Fluent Bit processor documentation.");
    addProcessorsHelp.disabled = !root.doc_url;
    addProcessorsHelp.addEventListener("click", function () {
      if (root.doc_url) {
        window.open(root.doc_url, "_blank", "noopener,noreferrer");
      }
    });
    addProcessorsActions.appendChild(addProcessorsHelp);
    addProcessorsHead.appendChild(addProcessorsActions);
    addProcessorsWrap.appendChild(addProcessorsHead);

    var addProcessorsBtn = document.createElement("button");
    addProcessorsBtn.type = "button";
    addProcessorsBtn.textContent = "Add Processors";
    addProcessorsBtn.disabled = isReadOnlyMode();
    addProcessorsBtn.addEventListener("click", function () {
      instance.processors = { logs: [] };
      saveDoc();
      renderAll();
    });
    addProcessorsWrap.appendChild(addProcessorsBtn);

    return addProcessorsWrap;
  }

  function availableRouteOutputTargets() {
    ensureDoc();
    var targets = [];
    var seen = {};
    var counters = {};
    state.doc.config.pipeline.outputs.forEach(function (outputInstance) {
      if (!outputInstance || typeof outputInstance !== "object") {
        return;
      }
      var alias = String(outputInstance.alias || "").trim();
      if (alias && !seen[alias]) {
        seen[alias] = true;
        targets.push(alias);
      }
      var name = String(outputInstance.name || "").trim();
      if (!name) {
        return;
      }
      if (!seen[name]) {
        seen[name] = true;
        targets.push(name);
      }
      var sequence = counters[name] || 0;
      var generated = name + "." + sequence;
      counters[name] = sequence + 1;
      if (!seen[generated]) {
        seen[generated] = true;
        targets.push(generated);
      }
    });
    return targets;
  }

  function renderRouteRuleEditor(rule, ruleIndex, rules, pathPrefix) {
    var block = document.createElement("div");
    block.className = "nested-panel";

    var titleRow = document.createElement("div");
    titleRow.className = "plugin-head";
    var title = document.createElement("strong");
    title.textContent = "Rule " + (ruleIndex + 1);
    titleRow.appendChild(title);

    var removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "-";
    removeBtn.className = "icon-remove";
    removeBtn.title = "Remove rule";
    removeBtn.disabled = isReadOnlyMode();
    removeBtn.addEventListener("click", function () {
      rules.splice(ruleIndex, 1);
      saveDoc();
      renderAll();
    });
    titleRow.appendChild(removeBtn);
    block.appendChild(titleRow);

    var body = document.createElement("div");
    body.className = "field-grid";

    body.appendChild(
      renderFieldRow(rule, {
        name: "context",
        data_type: "enum",
        required: false,
        description: "Where Fluent Bit should look for the field during route evaluation.",
        reference: "https://docs.fluentbit.io/manual/data-pipeline/router#conditional-routing",
        enum_options: [
          "body",
          "group_attributes",
          "group_metadata",
          "metadata",
          "otel_resource_attributes",
          "otel_scope_attributes",
          "otel_scope_metadata",
        ],
      }, {
        optional: false,
        focusKey: pathPrefix + ":context",
      })
    );
    body.appendChild(
      renderFieldRow(rule, {
        name: "field",
        data_type: "string",
        required: true,
        description: "Field to evaluate using Fluent Bit record accessor syntax.",
        reference: "https://docs.fluentbit.io/manual/data-pipeline/router#conditional-routing",
      }, {
        optional: false,
        focusKey: pathPrefix + ":field",
      })
    );
    body.appendChild(
      renderFieldRow(rule, {
        name: "op",
        data_type: "enum",
        required: true,
        description: "Comparison operator used by this route rule.",
        reference: "https://docs.fluentbit.io/manual/data-pipeline/router#conditional-routing",
        enum_options: [
          "eq",
          "gt",
          "gte",
          "in",
          "lt",
          "lte",
          "neq",
          "not_in",
          "not_regex",
          "regex",
        ],
      }, {
        optional: false,
        focusKey: pathPrefix + ":op",
      })
    );

    var valueBlock = document.createElement("div");
    valueBlock.className = "field-block";
    var valueRow = document.createElement("div");
    valueRow.className = "field-row";
    var valueLabel = document.createElement("label");
    valueLabel.textContent = "value";
    applyRequiredLabelStyle(valueLabel, true);
    valueRow.appendChild(valueLabel);
    var valueInput = document.createElement("textarea");
    valueInput.value = formatFlexibleRouteValue(rule.value);
    valueInput.placeholder = "Use JSON for arrays, objects, booleans, or numbers.";
    valueInput.title = "Use JSON syntax when the comparison value is an array or object.";
    valueInput.addEventListener("change", function () {
      rule.value = parseFlexibleRouteValue(valueInput.value);
      saveDoc();
    });
    valueInput.disabled = isReadOnlyMode();
    valueRow.appendChild(valueInput);
    valueRow.appendChild(
      createFieldHelpButton(
        {
          name: "value",
          description: "Comparison value. Use JSON syntax for arrays with in or not_in.",
          reference: "https://docs.fluentbit.io/manual/data-pipeline/router#conditional-routing",
        },
        false
      )
    );
    valueBlock.appendChild(valueRow);
    body.appendChild(valueBlock);

    block.appendChild(body);
    return block;
  }

  function renderRouteEntryCard(signalName, routeEntry, routeIndex, signalRoutes, pluginPath) {
    if (!routeEntry.condition || typeof routeEntry.condition !== "object") {
      routeEntry.condition = { op: "and", rules: [] };
    }
    if (!routeEntry.to || typeof routeEntry.to !== "object") {
      routeEntry.to = { outputs: [] };
    }
    if (!Array.isArray(routeEntry.condition.rules)) {
      routeEntry.condition.rules = [];
    }
    if (!Array.isArray(routeEntry.to.outputs)) {
      routeEntry.to.outputs = [];
    }

    var card = document.createElement("div");
    card.className = "plugin-card route-card";
    var key = pluginPath + ":route:" + signalName + ":" + routeIndex;
    var collapsed = Boolean(state.collapse[key]);

    var head = document.createElement("div");
    head.className = "plugin-head";
    var titleWrap = document.createElement("div");
    titleWrap.className = "plugin-head-main";
    var title = document.createElement("strong");
    title.textContent = routeEntry.name ? routeEntry.name : signalName + " route " + (routeIndex + 1);
    titleWrap.appendChild(title);
    head.appendChild(titleWrap);

    var actions = document.createElement("div");
    actions.className = "plugin-actions";
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
    removeBtn.title = "Remove route";
    removeBtn.disabled = isReadOnlyMode();
    removeBtn.addEventListener("click", function () {
      signalRoutes.splice(routeIndex, 1);
      saveDoc();
      renderAll();
    });
    actions.appendChild(removeBtn);
    head.appendChild(actions);
    card.appendChild(head);

    if (collapsed) {
      return card;
    }

    var body = document.createElement("div");
    body.className = "field-grid";
    body.appendChild(
      renderFieldRow(routeEntry, {
        name: "name",
        data_type: "string",
        required: true,
        description: "Unique identifier for this conditional route.",
        reference: "https://docs.fluentbit.io/manual/data-pipeline/router#conditional-routing",
      }, {
        optional: false,
        focusKey: key + ":name",
      })
    );
    card.appendChild(body);

    var conditionPanel = document.createElement("div");
    conditionPanel.className = "nested-panel route-nested-panel";
    var conditionTitle = document.createElement("h4");
    conditionTitle.textContent = "Condition";
    conditionPanel.appendChild(conditionTitle);

    var defaultRow = document.createElement("div");
    defaultRow.className = "field-row";
    var defaultLabel = document.createElement("label");
    defaultLabel.textContent = "default";
    applyRequiredLabelStyle(defaultLabel, false);
    defaultRow.appendChild(defaultLabel);
    var defaultCheckbox = document.createElement("input");
    defaultCheckbox.type = "checkbox";
    defaultCheckbox.checked = routeEntry.condition.default === true;
    defaultCheckbox.disabled = isReadOnlyMode();
    defaultCheckbox.addEventListener("change", function () {
      routeEntry.condition.default = defaultCheckbox.checked;
      if (defaultCheckbox.checked) {
        delete routeEntry.condition.op;
        routeEntry.condition.rules = [];
      } else {
        routeEntry.condition.op = routeEntry.condition.op || "and";
        routeEntry.condition.rules = Array.isArray(routeEntry.condition.rules) ? routeEntry.condition.rules : [];
      }
      saveDoc();
      renderAll();
    });
    defaultRow.appendChild(defaultCheckbox);
    defaultRow.appendChild(
      createFieldHelpButton(
        {
          name: "default",
          description: "Match records that did not match any earlier route.",
          reference: "https://docs.fluentbit.io/manual/data-pipeline/router#conditional-routing",
        },
        false
      )
    );
    conditionPanel.appendChild(defaultRow);

    if (routeEntry.condition.default !== true) {
      conditionPanel.appendChild(
        renderFieldRow(routeEntry.condition, {
          name: "op",
          data_type: "enum",
          required: true,
          description: "How Fluent Bit combines route condition rules.",
          reference: "https://docs.fluentbit.io/manual/data-pipeline/router#conditional-routing",
          enum_options: ["and", "or"],
        }, {
          optional: false,
          focusKey: key + ":condition:op",
        })
      );

      routeEntry.condition.rules.forEach(function (rule, ruleIndex) {
        conditionPanel.appendChild(
          renderRouteRuleEditor(
            rule,
            ruleIndex,
            routeEntry.condition.rules,
            key + ":condition:rules:" + ruleIndex
          )
        );
      });

      var addRuleBtn = document.createElement("button");
      addRuleBtn.type = "button";
      addRuleBtn.textContent = "Add Rule";
      addRuleBtn.disabled = isReadOnlyMode();
      addRuleBtn.addEventListener("click", function () {
        routeEntry.condition.rules.push({
          context: "body",
          field: "",
          op: "eq",
          value: "",
        });
        saveDoc();
        renderAll();
      });
      conditionPanel.appendChild(addRuleBtn);
    }

    card.appendChild(conditionPanel);

    var outputsPanel = document.createElement("div");
    outputsPanel.className = "nested-panel route-nested-panel";
    var outputsTitle = document.createElement("h4");
    outputsTitle.textContent = "To Outputs";
    outputsPanel.appendChild(outputsTitle);
    var availableTargets = availableRouteOutputTargets();

    routeEntry.to.outputs.forEach(function (outputName, outputIndex) {
      var outputRow = document.createElement("div");
      outputRow.className = "field-row";
      var outputLabel = document.createElement("label");
      outputLabel.textContent = outputIndex === 0 ? "outputs" : "";
      applyRequiredLabelStyle(outputLabel, outputIndex === 0);
      outputRow.appendChild(outputLabel);
      var outputSelect = document.createElement("select");
      var options = availableTargets.slice();
      if (outputName && options.indexOf(outputName) === -1) {
        options.unshift(outputName);
      }
      options.forEach(function (target) {
        var option = document.createElement("option");
        option.value = target;
        option.textContent = target;
        outputSelect.appendChild(option);
      });
      if (!options.length) {
        var empty = document.createElement("option");
        empty.value = "";
        empty.textContent = "No configured outputs yet";
        outputSelect.appendChild(empty);
      }
      outputSelect.value = outputName || "";
      outputSelect.disabled = isReadOnlyMode();
      outputSelect.addEventListener("change", function () {
        routeEntry.to.outputs[outputIndex] = outputSelect.value;
        saveDoc();
      });
      outputRow.appendChild(outputSelect);
      var removeOutputBtn = document.createElement("button");
      removeOutputBtn.type = "button";
      removeOutputBtn.textContent = "-";
      removeOutputBtn.className = "icon-remove right-align";
      removeOutputBtn.title = "Remove output destination";
      removeOutputBtn.disabled = isReadOnlyMode();
      removeOutputBtn.addEventListener("click", function () {
        routeEntry.to.outputs.splice(outputIndex, 1);
        saveDoc();
        renderAll();
      });
      outputRow.appendChild(removeOutputBtn);
      outputsPanel.appendChild(outputRow);
    });

    var addOutputBtn = document.createElement("button");
    addOutputBtn.type = "button";
    addOutputBtn.textContent = "Add Output";
    addOutputBtn.disabled = isReadOnlyMode();
    addOutputBtn.addEventListener("click", function () {
      var targets = availableRouteOutputTargets();
      routeEntry.to.outputs.push(targets.length > 0 ? targets[0] : "");
      saveDoc();
      renderAll();
    });
    outputsPanel.appendChild(addOutputBtn);
    card.appendChild(outputsPanel);

    return card;
  }

  function renderFluentbitRoutePanel(instance, pluginPath) {
    // Fluent Bit route editor supports per-signal routing with conditions.
    ensureFluentbitRoute(instance);

    var routeRoot = fluentbitRouteRoot();
    var frame = document.createElement("div");
    frame.className = "nested-panel route-panel";

    var headingRow = document.createElement("div");
    headingRow.className = "plugin-head";
    var headingWrap = document.createElement("div");
    headingWrap.className = "plugin-head-main";
    var heading = document.createElement("h4");
    heading.textContent = "Route";
    headingWrap.appendChild(heading);
    headingRow.appendChild(headingWrap);
    var headingActions = document.createElement("div");
    headingActions.className = "plugin-actions";
    var routeHelp = document.createElement("button");
    routeHelp.type = "button";
    routeHelp.textContent = "?";
    routeHelp.className = "icon-help";
    routeHelp.title = String(routeRoot.description || "Open Fluent Bit route documentation.");
    routeHelp.disabled = !routeRoot.doc_url;
    routeHelp.addEventListener("click", function () {
      if (routeRoot.doc_url) {
        window.open(routeRoot.doc_url, "_blank", "noopener,noreferrer");
      }
    });
    headingActions.appendChild(routeHelp);
    var removeRouteBtn = document.createElement("button");
    removeRouteBtn.type = "button";
    removeRouteBtn.textContent = "-";
    removeRouteBtn.className = "icon-remove";
    removeRouteBtn.title = "Remove route configuration";
    removeRouteBtn.disabled = isReadOnlyMode();
    removeRouteBtn.addEventListener("click", function () {
      delete instance.route;
      saveDoc();
      renderAll();
    });
    headingActions.appendChild(removeRouteBtn);
    headingRow.appendChild(headingActions);
    frame.appendChild(headingRow);

    var perRecordRoutingBlock = renderFieldRow(instance.route, {
        name: "per_record_routing",
        data_type: "boolean",
        required: false,
        description: "Enable per-record conditional route evaluation for this input.",
        reference: "https://docs.fluentbit.io/manual/data-pipeline/router#conditional-routing",
      }, {
        optional: false,
        focusKey: pluginPath + ":route:per_record_routing",
      });
    var perRecordRoutingRow = perRecordRoutingBlock.querySelector(".field-row");
    if (perRecordRoutingRow) {
      perRecordRoutingRow.classList.add("route-per-record-row");
    }
    frame.appendChild(perRecordRoutingBlock);

    var controls = document.createElement("div");
    controls.className = "optional-row";
    var signalSelect = document.createElement("select");
    fluentbitRouteSignals().forEach(function (signalMeta) {
      var option = document.createElement("option");
      option.value = signalMeta.name;
      option.textContent = signalMeta.name;
      signalSelect.appendChild(option);
    });
    controls.appendChild(signalSelect);
    var addRouteBtn = document.createElement("button");
    addRouteBtn.type = "button";
    addRouteBtn.textContent = "Add Route Entry";
    addRouteBtn.disabled = isReadOnlyMode();
    addRouteBtn.addEventListener("click", function () {
      var signalName = signalSelect.value || "logs";
      if (!Array.isArray(instance.route[signalName])) {
        instance.route[signalName] = [];
      }
      instance.route[signalName].push({
        name: "",
        condition: { op: "and", rules: [] },
        to: { outputs: [] },
      });
      saveDoc();
      renderAll();
    });
    controls.appendChild(addRouteBtn);
    frame.appendChild(controls);

    fluentbitRouteSignals().forEach(function (signalMeta) {
      var signalName = signalMeta.name;
      var items = instance.route[signalName];
      if (!Array.isArray(items) || items.length === 0) {
        return;
      }
      var signalWrap = document.createElement("div");
      signalWrap.className = "container-stack";
      var signalTitle = document.createElement("h4");
      signalTitle.textContent = signalName;
      signalWrap.appendChild(signalTitle);
      if (signalMeta.implemented === false) {
        var warning = document.createElement("p");
        warning.className = "route-signal-note";
        warning.textContent = "Fluent Bit parses this signal today, but does not fully evaluate it yet.";
        signalWrap.appendChild(warning);
      }
      items.forEach(function (routeEntry, routeIndex) {
        signalWrap.appendChild(
          renderRouteEntryCard(
            signalName,
            routeEntry,
            routeIndex,
            items,
            pluginPath
          )
        );
      });
      frame.appendChild(signalWrap);
    });

    return frame;
  }

function renderPluginCard(flatIndex, section, index, instance, pipeline, keyPrefix, pathPrefix) {
    // Main plugin card renderer for inputs/filters/outputs.
    // Includes move/reorder controls plus optional Fluent Bit extensions.
    var pluginDef = getPluginDefinition(section, instance.name);
    var card = document.createElement("div");
    card.className = "plugin-card";

    var key = (keyPrefix || "main") + ":" + section + "-" + index;
    var pluginPath = (pathPrefix || "$.pipeline") + "." + section + "[" + index + "]";
    var collapsed = Boolean(state.collapse[key]);

    var head = document.createElement("div");
    head.className = "plugin-head";

    var left = document.createElement("div");
    left.className = "plugin-head-main";
    var title = document.createElement("strong");
    title.textContent = "#" + (flatIndex + 1) + " " + instance.name;
    left.appendChild(title);

    var sectionIcons = document.createElement("div");
    sectionIcons.className = "section-icon-group";
    [
      { key: "inputs", label: "I", title: "Input" },
      { key: "filters", label: "F", title: "Filter" },
      { key: "outputs", label: "O", title: "Output" },
    ].forEach(function (sectionMeta) {
      var targetPluginDef = getPluginDefinition(sectionMeta.key, instance.name);
      var iconBtn = document.createElement("button");
      iconBtn.type = "button";
      iconBtn.textContent = sectionMeta.label;
      iconBtn.className = "section-icon";
      if (sectionMeta.key === section) {
        iconBtn.classList.add("is-active");
      }
      if (!targetPluginDef) {
        iconBtn.disabled = true;
        iconBtn.classList.add("is-disabled");
      } else if (isReadOnlyMode()) {
        iconBtn.disabled = true;
      }
      iconBtn.title = sectionMeta.title;
      iconBtn.setAttribute(
        "aria-label",
        targetPluginDef
          ? "Move plugin to " + sectionMeta.title + " section"
          : sectionMeta.title + " section unavailable for this plugin"
      );
      if (targetPluginDef && sectionMeta.key !== section) {
        iconBtn.addEventListener("click", function () {
          movePluginToSection(pipeline, section, index, instance, sectionMeta.key, pathPrefix || "$.pipeline");
        });
      }
      sectionIcons.appendChild(iconBtn);
    });
    left.appendChild(sectionIcons);

    head.appendChild(left);

    var actions = document.createElement("div");
    actions.className = "plugin-actions";

    actions.appendChild(createCommentToggleButton(key + ":comment", instance, "", "plugin comment editor"));

    var collapseBtn = document.createElement("button");
    collapseBtn.type = "button";
    collapseBtn.textContent = collapsed ? "Expand" : "Collapse";
    collapseBtn.addEventListener("click", function () {
      state.collapse[key] = !collapsed;
      renderAll();
    });
    actions.appendChild(collapseBtn);

    var upBtn = document.createElement("button");
    upBtn.type = "button";
    upBtn.textContent = "↑";
    upBtn.className = "icon-button";
    upBtn.title = "Move plugin up";
    upBtn.disabled = isReadOnlyMode() || index === 0;
    upBtn.addEventListener("click", function () {
      moveWithinPipeline(pipeline, section, index, -1, pathPrefix || "$.pipeline");
    });
    actions.appendChild(upBtn);

    var downBtn = document.createElement("button");
    downBtn.type = "button";
    downBtn.textContent = "↓";
    downBtn.className = "icon-button";
    downBtn.title = "Move plugin down";
    downBtn.disabled = isReadOnlyMode() || index >= pipeline[section].length - 1;
    downBtn.addEventListener("click", function () {
      moveWithinPipeline(pipeline, section, index, 1, pathPrefix || "$.pipeline");
    });
    actions.appendChild(downBtn);

    var removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "-";
    removeBtn.className = "icon-remove";
    removeBtn.title = "Remove plugin";
    removeBtn.disabled = isReadOnlyMode();
    removeBtn.addEventListener("click", function () {
      pipeline[section].splice(index, 1);
      saveDoc();
      renderAll();
    });
    actions.appendChild(removeBtn);

    head.appendChild(actions);
    card.appendChild(head);

    if (!collapsed) {
      card.appendChild(createCommentEditorPanel(instance, "Plugin Comment", "", key + ":comment"));

      var fieldsWrap = document.createElement("div");
      fieldsWrap.className = "field-grid";

      var fields = (pluginDef && pluginDef.fields) || [];
      var requiredFields = fields.filter(function (field) {
        return field.required;
      });
      var currentOptionalFields = fields.filter(function (field) {
        return !field.required && Object.prototype.hasOwnProperty.call(instance, field.name);
      });

      requiredFields.forEach(function (field) {
        var focusKey = section + ":" + index + ":" + field.name;
        fieldsWrap.appendChild(
          renderFieldRow(instance, field, {
            optional: false,
            focusKey: focusKey,
            onRemove: null,
            commentTarget: instance,
            commentFieldName: field.name,
            commentToggleKey: key + ":" + field.name + ":comment",
          })
        );
      });

      currentOptionalFields.forEach(function (field) {
        var focusKey = section + ":" + index + ":" + field.name;
        fieldsWrap.appendChild(
          renderFieldRow(instance, field, {
            optional: true,
            focusKey: focusKey,
            commentTarget: instance,
            commentFieldName: field.name,
            commentToggleKey: key + ":" + field.name + ":comment",
            onRemove: function () {
              delete instance[field.name];
              saveDoc();
              renderAll();
            },
          })
        );
      });

      card.appendChild(fieldsWrap);

      var missingOptional = fields.filter(function (fieldDefinition) {
        return !fieldDefinition.required && !Object.prototype.hasOwnProperty.call(instance, fieldDefinition.name);
      });
      if (missingOptional.length > 0) {
        var optionalRow = document.createElement("div");
        optionalRow.className = "optional-row";
        var optionalSel = document.createElement("select");
        var emptyOpt = document.createElement("option");
        emptyOpt.value = "";
        emptyOpt.textContent = "Select optional attribute...";
        optionalSel.appendChild(emptyOpt);
        missingOptional.forEach(function (fieldDefinition) {
          var opt = document.createElement("option");
          opt.value = fieldDefinition.name;
          opt.textContent = fieldDefinition.name;
          optionalSel.appendChild(opt);
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
          var field = fields.find(function (fieldDefinition) {
            return fieldDefinition.name === selected;
          });
          if (!field) {
            return;
          }
          instance[field.name] = defaultForField(field);
          state.pendingFocusFieldKey = section + ":" + index + ":" + field.name;
          saveDoc();
          renderAll();
        });
        optionalRow.appendChild(addOptional);

        card.appendChild(optionalRow);
      }

      if (state.configType === "fluentbit" && section === "inputs" && fluentbitRouteRoot()) {
        if (instance.route && typeof instance.route === "object") {
          card.appendChild(renderFluentbitRoutePanel(instance, pluginPath));
        } else {
          var addRouteWrap = document.createElement("div");
          addRouteWrap.className = "nested-panel";
          var addRouteHead = document.createElement("div");
          addRouteHead.className = "plugin-head";
          var addRouteHeadMain = document.createElement("div");
          addRouteHeadMain.className = "plugin-head-main";
          var addRouteTitle = document.createElement("h4");
          addRouteTitle.textContent = "Route";
          addRouteHeadMain.appendChild(addRouteTitle);
          addRouteHead.appendChild(addRouteHeadMain);
          var addRouteActions = document.createElement("div");
          addRouteActions.className = "plugin-actions";
          var addRouteHelp = document.createElement("button");
          addRouteHelp.type = "button";
          addRouteHelp.textContent = "?";
          addRouteHelp.className = "icon-help";
          addRouteHelp.title = String(fluentbitRouteRoot().description || "Open Fluent Bit route documentation.");
          addRouteHelp.disabled = !fluentbitRouteRoot().doc_url;
          addRouteHelp.addEventListener("click", function () {
            if (fluentbitRouteRoot().doc_url) {
              window.open(fluentbitRouteRoot().doc_url, "_blank", "noopener,noreferrer");
            }
          });
          addRouteActions.appendChild(addRouteHelp);
          addRouteHead.appendChild(addRouteActions);
          addRouteWrap.appendChild(addRouteHead);
          var addRouteBtn = document.createElement("button");
          addRouteBtn.type = "button";
          addRouteBtn.textContent = "Add Route";
          addRouteBtn.disabled = isReadOnlyMode();
          addRouteBtn.addEventListener("click", function () {
            instance.route = { per_record_routing: true, logs: [] };
            saveDoc();
            renderAll();
          });
          addRouteWrap.appendChild(addRouteBtn);
          card.appendChild(addRouteWrap);
        }
      }

      if (state.configType === "fluentbit" && (section === "inputs" || section === "outputs") && fluentbitProcessorRoot()) {
        if (instance.processors && typeof instance.processors === "object") {
          card.appendChild(renderFluentbitProcessorsPanel(section, index, instance, keyPrefix || "main", pluginPath));
        } else {
          card.appendChild(renderAddFluentbitProcessorsPanel(instance));
        }
      }
    }

    return card;
  }

    return {
      renderPluginCard: renderPluginCard,
    };
  }

  global.ConfigServiceUiPlugins = {
    create: create,
  };
})(window);
