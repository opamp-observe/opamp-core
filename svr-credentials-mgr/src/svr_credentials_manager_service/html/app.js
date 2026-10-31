/* Copyright 2026 opamp.info; Licensed under the Apache License, Version 2.0. */
window.CredentialManagerApp = {
  create: function create(deps) {
    const apiBase = "/svr-credentials-manager-service/api/v1";
    const functions = deps.functions;
    const state = deps.state;
    const standardConnectionLabels = {
      opamp: "OpAMP",
      own_metrics: "Own metrics",
      own_traces: "Own traces",
      own_logs: "Own logs"
    };
    const CONNECTION_NAME_FILTER_KEY = "connectionName";
    const ASSIGNED_CLIENT_FILTER_KEY = "assignedClient";

    const otherConnectionInput = function otherConnectionInput() {
      return functions.element("other-name");
    };

    const currentConnectionInput = function currentConnectionInput() {
      return functions.element("connection-name");
    };

    const sectionStateKey = function sectionStateKey(kind, otherName) {
      return kind === "other" ? `other:${String(otherName || "").trim()}` : kind;
    };

    const sortedValues = function sortedValues(values) {
      return [...new Set(values)].sort(function sortValues(leftValue, rightValue) {
        return leftValue.localeCompare(rightValue);
      });
    };

    const getOtherConnectionNames = function getOtherConnectionNames() {
      const definitionNames = Object.keys(state.definition.other_connections || {});
      const draftNames = Object.keys(state.sectionDrafts)
        .filter(function filterOtherDraft(sectionKey) {
          return sectionKey.startsWith("other:");
        })
        .map(function mapOtherDraft(sectionKey) {
          return sectionKey.slice(6).trim();
        })
        .filter(Boolean);
      return sortedValues(definitionNames.concat(draftNames));
    };

    const defaultOtherConnectionName = function defaultOtherConnectionName() {
      return getOtherConnectionNames()[0] || "";
    };

    const setActiveOtherConnectionName = function setActiveOtherConnectionName(name) {
      const normalizedName = String(name || "").trim();
      state.activeOtherName = normalizedName;
      otherConnectionInput().value = normalizedName;
    };

    const currentSectionKey = function currentSectionKey() {
      return sectionStateKey(state.activeKind, state.activeOtherName);
    };

    const structuredSectionForKey = function structuredSectionForKey(sectionKey) {
      if (sectionKey.startsWith("other:")) {
        return state.definition.other_connections?.[sectionKey.slice(6)];
      }
      return state.definition[sectionKey];
    };

    const draftForKey = function draftForKey(sectionKey) {
      if (state.sectionDrafts[sectionKey]) {
        return state.sectionDrafts[sectionKey];
      }
      const structuredSection = structuredSectionForKey(sectionKey);
      if (!structuredSection) {
        return null;
      }
      state.sectionDrafts[sectionKey] = functions.draftFromSection(structuredSection);
      return state.sectionDrafts[sectionKey];
    };

    const preserve = function preserve() {
      const key = currentSectionKey();
      if (!key) {
        return;
      }
      state.sectionDrafts[key] = functions.readSectionDraft();
    };

    const refreshCopyOptions = function refreshCopyOptions() {
      const standardOptions = Object.entries(standardConnectionLabels).map(
        function renderStandardOption(entry) {
          return `<option value="${entry[0]}">${entry[1]}</option>`;
        }
      );
      const otherOptions = getOtherConnectionNames().map(function renderOtherOption(name) {
        const escapedName = functions.escapeHtml(name);
        return `<option value="other:${escapedName}">Other: ${escapedName}</option>`;
      });
      functions.element("copy-from").innerHTML =
        '<option value="">Select a connection…</option>'
        + standardOptions.concat(otherOptions).join("");
    };

    const show = function show() {
      const isOtherConnection = state.activeKind === "other";
      const otherNameField = functions.element("other-name-wrap");
      otherNameField.classList.toggle("hidden", !isOtherConnection);
      otherConnectionInput().disabled = !isOtherConnection;
      if (isOtherConnection && !state.activeOtherName) {
        setActiveOtherConnectionName(defaultOtherConnectionName());
      }
      document.querySelectorAll(".connection-tab").forEach(function syncTabState(tab) {
        const isActive = tab.dataset.kind === state.activeKind;
        tab.classList.toggle("active", isActive);
        tab.setAttribute("aria-selected", String(isActive));
        tab.tabIndex = isActive ? 0 : -1;
        if (isActive) {
          functions.element("connection-tab-panel").setAttribute("aria-labelledby", tab.id);
        }
      });
      const key = currentSectionKey();
      const sectionDraft = draftForKey(key);
      functions.writeSectionDraft(sectionDraft || {});
      refreshCopyOptions();
    };

    const activate = function activate(kind) {
      preserve();
      state.activeKind = kind;
      show();
    };

    const copyFrom = function copyFrom(sourceKey) {
      if (!sourceKey) {
        return;
      }
      preserve();
      const sourceDraft = draftForKey(sourceKey);
      if (!sourceDraft) {
        throw new Error("The selected source connection has no saved fields");
      }
      const targetKey = currentSectionKey();
      if (!targetKey) {
        throw new Error("Enter an Other connection name before copying fields");
      }
      const copiedSectionDraft = JSON.parse(JSON.stringify(sourceDraft));
      state.sectionDrafts[targetKey] = copiedSectionDraft;
      functions.writeSectionDraft(copiedSectionDraft);
      functions.element("copy-from").value = "";
      functions.status("Copied fields into the current tab.");
    };

    const upload = async function upload(input) {
      if (!input.files.length) {
        return;
      }
      const reference = await functions.uploadFile(input.files[0]);
      functions.element(input.dataset.reference).value = reference;
      functions.status(`Uploaded ${input.files[0].name}.`);
    };

    const loadTlsVersions = async function loadTlsVersions() {
      state.tlsVersions = (await functions.requestJson(`${apiBase}/options/tls-versions`)).versions;
      const optionMarkup = '<option value="">Not specified</option>'
        + state.tlsVersions.map(function renderOption(version) {
          const escapedVersion = functions.escapeHtml(version);
          return `<option value="${escapedVersion}">${escapedVersion}</option>`;
        }).join("");
      functions.element("tls-min").innerHTML = optionMarkup;
      functions.element("tls-max").innerHTML = optionMarkup;
    };

    const syncDeveloperActionsVisibility = function syncDeveloperActionsVisibility() {
      const hidden = state.appEnableDevFeatures !== true;
      functions.element("add-test-clients").classList.toggle("hidden", hidden);
      functions.element("reload-ui").classList.toggle("hidden", hidden);
    };

    const loadUiHealth = async function loadUiHealth() {
      const payload = await functions.requestJson(`${apiBase}/health`);
      state.appEnableDevFeatures = payload?.app_enable_dev_features === true;
      syncDeveloperActionsVisibility();
    };

    const reconciliationStatusMessage = function reconciliationStatusMessage(payload) {
      const message = String(payload?.reconciliation?.message || "").trim();
      return message ? `Error: ${message}` : "";
    };

    const applyMappingsPayload = function applyMappingsPayload(payload) {
      state.mappings = payload?.mappings || {};
      renderConnections();
      return reconciliationStatusMessage(payload);
    };

    const connectionAssignments = function connectionAssignments(connectionName) {
      return sortedValues(
        Object.entries(state.mappings)
          .filter(function matchConnection(entry) {
            return entry[1] === connectionName;
          })
          .map(function collectClientId(entry) {
            return entry[0];
          })
      );
    };

    const assignmentSummary = function assignmentSummary(connectionName) {
      const assignedClientIds = connectionAssignments(connectionName);
      if (!assignedClientIds.length) {
        return "No client nodes assigned";
      }
      const previewClientIds = assignedClientIds.slice(0, 3).join(", ");
      const extraCount = assignedClientIds.length - 3;
      if (extraCount > 0) {
        return `${previewClientIds} +${extraCount} more`;
      }
      return previewClientIds;
    };

    const normalizedFilterValue = function normalizedFilterValue(value) {
      return String(value || "").trim().toLowerCase();
    };

    const connectionMatchesFilters = function connectionMatchesFilters(connectionName) {
      const connectionNameFilter = normalizedFilterValue(
        state.connectionFilters[CONNECTION_NAME_FILTER_KEY]
      );
      const assignedClientFilter = normalizedFilterValue(
        state.connectionFilters[ASSIGNED_CLIENT_FILTER_KEY]
      );
      if (
        connectionNameFilter
        && !connectionName.toLowerCase().includes(connectionNameFilter)
      ) {
        return false;
      }
      if (!assignedClientFilter) {
        return true;
      }
      return connectionAssignments(connectionName).some(function matchAssignedClient(clientId) {
        return clientId.toLowerCase().includes(assignedClientFilter);
      });
    };

    const filteredConnectionNames = function filteredConnectionNames() {
      return state.names.filter(function filterConnectionNames(connectionName) {
        return connectionMatchesFilters(connectionName);
      });
    };

    const updateConnectionFilter = function updateConnectionFilter(filterKey, filterValue) {
      state.connectionFilters[filterKey] = String(filterValue || "");
      renderConnections();
    };

    const renderConnections = function renderConnections() {
      const tableBody = functions.element("connection-items");
      if (!state.names.length) {
        tableBody.innerHTML = '<tr><td class="empty-connections" colspan="3">No connections have been defined.</td></tr>';
        return;
      }
      const visibleConnectionNames = filteredConnectionNames();
      if (!visibleConnectionNames.length) {
        tableBody.innerHTML = '<tr><td class="empty-connections" colspan="3">No connections match the current filters.</td></tr>';
        return;
      }
      const selectedConnectionName = currentConnectionInput().value.trim();
      tableBody.innerHTML = visibleConnectionNames.map(function renderConnectionRow(name) {
        const escapedName = functions.escapeHtml(name);
        const assignedClientIds = connectionAssignments(name);
        const countLabel = assignedClientIds.length === 1 ? "1 client" : `${assignedClientIds.length} clients`;
        const isSelected = selectedConnectionName === name;
        return `
          <tr class="connection-row${isSelected ? " is-selected" : ""}" data-name="${escapedName}" tabindex="0" aria-selected="${isSelected ? "true" : "false"}">
            <td>
              <span class="connection-name-text">${escapedName}</span>
            </td>
            <td>
              <div class="connection-assignment-summary">${functions.escapeHtml(assignmentSummary(name))}</div>
              <div class="connection-assignment-summary">${functions.escapeHtml(countLabel)}</div>
            </td>
            <td class="actions-column">
              <div class="connection-actions">
                <button class="button-link apply-connection" type="button" data-name="${escapedName}">Apply</button>
                <button class="button-link assign-connection" type="button" data-name="${escapedName}">Assign</button>
                <button class="icon-remove remove-connection" type="button" title="Delete connection" aria-label="Delete connection ${escapedName}" data-name="${escapedName}">-</button>
              </div>
            </td>
          </tr>
        `;
      }).join("");
    };

    const refreshNames = async function refreshNames() {
      state.names = (await functions.requestJson(`${apiBase}/connections`)).names;
      renderConnections();
    };

    const load = async function load(name) {
      if (!name) {
        state.definition = {};
        state.sectionDrafts = {};
        currentConnectionInput().value = "";
        setActiveOtherConnectionName("");
        show();
        renderConnections();
        return;
      }
      const payload = await functions.requestJson(`${apiBase}/connections/${encodeURIComponent(name)}`);
      state.definition = payload.definition;
      state.sectionDrafts = {};
      currentConnectionInput().value = name;
      setActiveOtherConnectionName(defaultOtherConnectionName());
      show();
      renderConnections();
      functions.status(`Loaded ${name}.`);
    };

    const buildDefinitionFromDrafts = function buildDefinitionFromDrafts() {
      const builtDefinition = {};
      Object.keys(standardConnectionLabels).forEach(function buildStandardSection(kind) {
        const sectionDraft = draftForKey(kind);
        if (sectionDraft) {
          builtDefinition[kind] = functions.sectionFromDraft(sectionDraft);
        }
      });
      const otherConnections = {};
      getOtherConnectionNames().forEach(function buildOtherSection(otherConnectionName) {
        const sectionDraft = draftForKey(sectionStateKey("other", otherConnectionName));
        if (sectionDraft) {
          otherConnections[otherConnectionName] = functions.sectionFromDraft(sectionDraft);
        }
      });
      if (Object.keys(otherConnections).length) {
        builtDefinition.other_connections = otherConnections;
      }
      return builtDefinition;
    };

    const save = async function save() {
      preserve();
      const name = currentConnectionInput().value.trim();
      if (!name) {
        throw new Error("Connection name is required");
      }
      state.definition = buildDefinitionFromDrafts();
      await functions.requestJson(`${apiBase}/connections/${encodeURIComponent(name)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ definition: state.definition })
      });
      await refreshNames();
      functions.status(`Saved ${name}.`);
    };

    const removeConnectionByName = async function removeConnectionByName(name) {
      const normalizedName = String(name || "").trim();
      if (!normalizedName) {
        return;
      }
      if (!window.confirm(`Delete connection ${normalizedName}?`)) {
        return;
      }
      await functions.requestJson(`${apiBase}/connections/${encodeURIComponent(normalizedName)}`, {
        method: "DELETE"
      });
      if (currentConnectionInput().value.trim() === normalizedName) {
        state.definition = {};
        state.sectionDrafts = {};
        currentConnectionInput().value = "";
        setActiveOtherConnectionName("");
        show();
      }
      await refreshNames();
      functions.status(`Deleted ${normalizedName}.`);
    };

    const remove = async function remove() {
      await removeConnectionByName(currentConnectionInput().value.trim());
    };

    const applyConnectionByName = async function applyConnectionByName(name) {
      const normalizedName = String(name || "").trim();
      if (!normalizedName) {
        throw new Error("Connection name is required");
      }
      const response = await functions.requestJson(
        `${apiBase}/connections/${encodeURIComponent(normalizedName)}/apply`,
        {
          method: "POST"
        }
      );
      functions.status(response.message || `Applied ${normalizedName}.`);
    };

    const loadMappings = async function loadMappings() {
      const statusMessage = applyMappingsPayload(
        await functions.requestJson(`${apiBase}/mappings`)
      );
      if (statusMessage) {
        functions.status(statusMessage);
      }
    };

    const loadAvailableClients = async function loadAvailableClients() {
      const mockClientPayload = await functions.requestJson(`${apiBase}/mock-clients`);
      const providerPayload = await functions.requestJsonIfOk("/api/clients");
      const mockClientIds = Array.isArray(mockClientPayload?.clients)
        ? mockClientPayload.clients.map(function collectMockClientId(clientId) {
          return String(clientId || "").trim();
        }).filter(Boolean)
        : [];
      const providerClientIds = Array.isArray(providerPayload?.clients)
        ? providerPayload.clients.map(function collectClientId(client) {
          return String(client.client_id || "").trim();
        }).filter(Boolean)
        : [];
      state.knownClientIds = sortedValues(
        mockClientIds.concat(providerClientIds, Object.keys(state.mappings))
      );
    };

    const addTestClients = async function addTestClients() {
      const mockClientPayload = await functions.requestJson(`${apiBase}/mock-clients`, {
        method: "POST"
      });
      await loadAvailableClients();
      if (!functions.element("assignment-dialog").classList.contains("hidden")) {
        renderAssignmentDialog();
      }
      functions.status(`Added ${mockClientPayload.clients.length} mock clients.`);
    };

    const availableAssignmentClientIds = function availableAssignmentClientIds(connectionName) {
      const assignedClientIds = new Set(state.assignmentDraftClientIds);
      return sortedValues(
        state.knownClientIds.concat(Object.keys(state.mappings))
      ).filter(function filterAssigned(clientId) {
        return !assignedClientIds.has(clientId);
      });
    };

    const assignmentOptionLabel = function assignmentOptionLabel(clientId, connectionName) {
      const mappedConnection = state.mappings[clientId];
      if (mappedConnection && mappedConnection !== connectionName) {
        return `${clientId} (assigned to ${mappedConnection})`;
      }
      return clientId;
    };

    const renderAssignmentList = function renderAssignmentList(selectId, clientIds, connectionName) {
      const select = functions.element(selectId);
      select.innerHTML = clientIds.map(function renderOption(clientId) {
        const escapedClientId = functions.escapeHtml(clientId);
        const escapedLabel = functions.escapeHtml(
          assignmentOptionLabel(clientId, connectionName)
        );
        return `<option value="${escapedClientId}">${escapedLabel}</option>`;
      }).join("");
    };

    const renderAssignmentDialog = function renderAssignmentDialog() {
      functions.element("assignment-connection-name").textContent = state.assignmentConnectionName || "-";
      renderAssignmentList(
        "assignment-available",
        availableAssignmentClientIds(state.assignmentConnectionName),
        state.assignmentConnectionName
      );
      renderAssignmentList(
        "assignment-selected",
        state.assignmentDraftClientIds,
        state.assignmentConnectionName
      );
    };

    const openAssignment = async function openAssignment(connectionName) {
      state.assignmentConnectionName = connectionName;
      state.assignmentDraftClientIds = connectionAssignments(connectionName);
      await loadAvailableClients();
      renderAssignmentDialog();
      functions.element("assignment-dialog").classList.remove("hidden");
    };

    const closeAssignment = function closeAssignment() {
      functions.element("assignment-dialog").classList.add("hidden");
      state.assignmentConnectionName = "";
      state.assignmentDraftClientIds = [];
    };

    const selectedOptionValues = function selectedOptionValues(selectId) {
      return Array.from(functions.element(selectId).selectedOptions).map(
        function collectValue(option) {
          return String(option.value || "").trim();
        }
      ).filter(Boolean);
    };

    const assignSelectedClients = function assignSelectedClients() {
      state.assignmentDraftClientIds = sortedValues(
        state.assignmentDraftClientIds.concat(selectedOptionValues("assignment-available"))
      );
      renderAssignmentDialog();
    };

    const unassignSelectedClients = function unassignSelectedClients() {
      const selectedClientIds = new Set(selectedOptionValues("assignment-selected"));
      state.assignmentDraftClientIds = state.assignmentDraftClientIds.filter(
        function keepAssigned(clientId) {
          return !selectedClientIds.has(clientId);
        }
      );
      renderAssignmentDialog();
    };

    const saveAssignment = async function saveAssignment() {
      const connectionName = state.assignmentConnectionName;
      const nextMappings = { ...state.mappings };
      Object.keys(nextMappings).forEach(function clearCurrentAssignments(clientId) {
        if (nextMappings[clientId] === connectionName) {
          delete nextMappings[clientId];
        }
      });
      state.assignmentDraftClientIds.forEach(function applyAssignment(clientId) {
        nextMappings[clientId] = connectionName;
      });
      const response = await functions.requestJson(`${apiBase}/mappings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mappings: nextMappings })
      });
      applyMappingsPayload(response);
      await loadAvailableClients();
      renderConnections();
      closeAssignment();
      functions.status(`Saved assignments for ${connectionName}.`);
    };

    const initialize = async function initialize() {
      await loadUiHealth();
      await loadTlsVersions();
      await refreshNames();
      await loadMappings();
      await loadAvailableClients();
      show();
    };

    return {
      initialize: initialize,
      load: load,
      save: save,
      applyConnectionByName: applyConnectionByName,
      remove: remove,
      removeConnectionByName: removeConnectionByName,
      preserve: preserve,
      show: show,
      activate: activate,
      copyFrom: copyFrom,
      upload: upload,
      addTestClients: addTestClients,
      openAssignment: openAssignment,
      closeAssignment: closeAssignment,
      assignSelectedClients: assignSelectedClients,
      unassignSelectedClients: unassignSelectedClients,
      saveAssignment: saveAssignment,
      renderConnections: renderConnections,
      updateConnectionFilter: updateConnectionFilter
    };
  }
};
