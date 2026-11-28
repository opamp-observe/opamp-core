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

    const CATALOG_FEATURE_ENTRY_POINT = "catalog_service.opamp_integration:register_catalog_feature";
    const CONFIG_SERVICE_FEATURE_ENTRY_POINT = "config_service.opamp_integration:register_config_service_feature";
    const CATALOG_SELECTION_CALLBACK_QUERY = "selection_callback";
    const CATALOG_SELECTION_APPLIED_MESSAGE_TYPE = "opamp-catalog-selection-applied";

    const TABLE_COLUMN_DEFINITIONS = Object.freeze({
      service_instance_id: { label: "Service Instance ID", sortKey: "service_instance_id" },
      instance_uid: { label: "Instance UID", sortKey: "client_id" },
      status: {
        label: "Connection Status",
        headerHtml: "Connection<br>Status",
        sortKey: "status",
      },
      health_status: {
        label: "Health Status",
        headerHtml: "Health<br>Status",
        sortKey: "health_status",
      },
      last_seen: { label: "Last Seen", sortKey: "last_communication" },
      config_version: {
        label: "Config Version",
        headerHtml: "Config<br>Version",
        sortKey: "current_config_version",
      },
      first_registered: { label: "First Registered", sortKey: "first_seen" },
      client_version: { label: "Client Version", sortKey: "client_version" },
      host_type: { label: "Host Type", sortKey: "host_type" },
      host_version: { label: "Host Version", sortKey: "host_version" },
      host_name: { label: "Host Name", sortKey: "host_name" },
      host_ip: { label: "Host IP", sortKey: "host_ip" },
    });
    const TABLE_COLUMN_KEYS = Object.freeze(Object.keys(TABLE_COLUMN_DEFINITIONS));
    const OPTIONAL_TABLE_COLUMNS = Object.freeze([
      "health_status",
      "first_registered",
      "client_version",
      "host_type",
      "host_version",
      "host_name",
      "host_ip",
    ]);
    const MULTI_SELECT_FILTER_COLUMNS = Object.freeze([
      "status",
      "health_status",
      "config_version",
      "host_type",
      "host_version",
    ]);
    const DEFAULT_VISIBLE_COLUMNS = Object.freeze({
      service_instance_id: true,
      instance_uid: true,
      status: true,
      last_seen: true,
      config_version: true,
      health_status: false,
      first_registered: false,
      client_version: false,
      host_type: false,
      host_version: false,
      host_name: false,
      host_ip: false,
    });
    let modalResizeState = null;

    function clampValue(value, minValue, maxValue) {
      return Math.min(Math.max(value, minValue), maxValue);
    }

    function clearModalResizeState() {
      modalResizeState = null;
      document.body.classList.remove("modal-resizing");
      document.removeEventListener("pointermove", handleModalResizePointerMove);
      document.removeEventListener("pointerup", endModalResize);
      document.removeEventListener("pointercancel", endModalResize);
    }

    function resetModalCardSize() {
      if (!modalCard) return;
      clearModalResizeState();
      modalCard.style.width = "";
      modalCard.style.height = "";
      delete modalCard.dataset.minWidth;
      delete modalCard.dataset.minHeight;
    }

    function captureModalCardMinSize() {
      if (!modalCard || !modal.classList.contains("open")) return;
      if (modalCard.dataset.minWidth && modalCard.dataset.minHeight) return;
      const rect = modalCard.getBoundingClientRect();
      modalCard.dataset.minWidth = String(Math.round(rect.width));
      modalCard.dataset.minHeight = String(Math.round(rect.height));
    }

    function clampOpenModalCardToViewport() {
      if (!modalCard || !modal.classList.contains("open")) return;
      captureModalCardMinSize();
      if (!modalCard.style.width && !modalCard.style.height) return;
      const rect = modalCard.getBoundingClientRect();
      const storedMinWidth = parseFloat(modalCard.dataset.minWidth || "");
      const storedMinHeight = parseFloat(modalCard.dataset.minHeight || "");
      const maxWidth = Math.max(320, window.innerWidth - 48);
      const maxHeight = Math.max(320, window.innerHeight - 48);
      const minWidth = Number.isFinite(storedMinWidth)
        ? Math.min(storedMinWidth, maxWidth)
        : Math.min(rect.width, maxWidth);
      const minHeight = Number.isFinite(storedMinHeight)
        ? Math.min(storedMinHeight, maxHeight)
        : Math.min(rect.height, maxHeight);
      modalCard.style.width = `${Math.round(clampValue(rect.width, minWidth, maxWidth))}px`;
      modalCard.style.height = `${Math.round(clampValue(rect.height, minHeight, maxHeight))}px`;
    }

    function handleModalResizePointerMove(event) {
      if (!modalResizeState || !modalCard) return;
      event.preventDefault();
      const maxWidth = Math.max(320, window.innerWidth - 48);
      const maxHeight = Math.max(320, window.innerHeight - 48);
      const minWidth = Math.min(modalResizeState.minWidth, maxWidth);
      const minHeight = Math.min(modalResizeState.minHeight, maxHeight);
      const width = clampValue(
        modalResizeState.startWidth + (event.clientX - modalResizeState.startX),
        minWidth,
        maxWidth
      );
      const height = clampValue(
        modalResizeState.startHeight + (event.clientY - modalResizeState.startY),
        minHeight,
        maxHeight
      );
      modalCard.style.width = `${Math.round(width)}px`;
      modalCard.style.height = `${Math.round(height)}px`;
    }

    function endModalResize() {
      clearModalResizeState();
    }

    function beginModalResize(event) {
      if (!modalCard || !modal.classList.contains("open")) return;
      if (typeof event.button === "number" && event.button !== 0) return;
      captureModalCardMinSize();
      const rect = modalCard.getBoundingClientRect();
      modalResizeState = {
        startX: event.clientX,
        startY: event.clientY,
        startWidth: rect.width,
        startHeight: rect.height,
        minWidth: parseFloat(modalCard.dataset.minWidth || "") || rect.width,
        minHeight: parseFloat(modalCard.dataset.minHeight || "") || rect.height,
      };
      document.body.classList.add("modal-resizing");
      document.addEventListener("pointermove", handleModalResizePointerMove);
      document.addEventListener("pointerup", endModalResize);
      document.addEventListener("pointercancel", endModalResize);
      event.preventDefault();
    }

    let draggingRemoteConfigSelectionClientId = "";
    let draggingRemoteConfigSelectionIndex = -1;

    async function fetchSettings() {
      const resp = await apiFetch("/api/settings/comms");
      if (!resp.ok) return;
      const data = await resp.json();
      state.delayed = data.delayed_comms_seconds ?? 60;
      state.significant = data.significant_comms_seconds ?? 300;
      state.clientEventHistorySize = data.client_event_history_size ?? 50;
      state.stateSaveFolder = String(data.state_save_folder || "runtime");
      const retentionCount = parseInt(data.retention_count, 10);
      state.retentionCount =
        Number.isNaN(retentionCount) || retentionCount <= 0
          ? 5
          : retentionCount;
      const snapshotFileCount = parseInt(data.state_snapshot_file_count, 10);
      state.stateSnapshotFileCount =
        Number.isNaN(snapshotFileCount) || snapshotFileCount < 0
          ? 0
          : snapshotFileCount;
      const autosaveInterval = parseInt(
        data.autosave_interval_seconds_since_change,
        10
      );
      state.autosaveIntervalSecondsSinceChange =
        Number.isNaN(autosaveInterval) || autosaveInterval <= 0
          ? 600
          : autosaveInterval;
      state.humanInLoopApproval = data.human_in_loop_approval === true;
      state.statePersistenceEnabled = data.state_persistence_enabled === true;
      state.advertisedCapabilities = Array.isArray(data.advertised_capabilities)
        ? data.advertised_capabilities
        : [];
      state.tlsEnabled = data.tls_enabled === true;
      state.httpsCertificateExpiryDate =
        typeof data.https_certificate_expiry_date === "string"
          ? data.https_certificate_expiry_date
          : null;
      state.httpsCertificateDaysRemaining =
        Number.isInteger(data.https_certificate_days_remaining)
          ? data.https_certificate_days_remaining
          : null;
      state.httpsCertificateExpiringSoon =
        data.https_certificate_expiring_soon === true;
      updatePendingApprovalVisibility();
    }

    function renderHttpsCertificateExpiryRow() {
      if (!httpsCertificateExpiryGroup || !httpsCertificateExpiryOutput) return;
      if (state.tlsEnabled !== true) {
        httpsCertificateExpiryGroup.classList.add("hidden");
        httpsCertificateExpiryGroup.classList.remove("expiring-soon");
        httpsCertificateExpiryOutput.textContent = "--";
        return;
      }
      httpsCertificateExpiryGroup.classList.remove("hidden");
      const expiryDate = state.httpsCertificateExpiryDate;
      if (expiryDate) {
        const daysRemaining = state.httpsCertificateDaysRemaining;
        if (Number.isInteger(daysRemaining)) {
          httpsCertificateExpiryOutput.textContent =
            `${expiryDate} (${daysRemaining} day${daysRemaining === 1 ? "" : "s"} remaining)`;
        } else {
          httpsCertificateExpiryOutput.textContent = expiryDate;
        }
      } else {
        httpsCertificateExpiryOutput.textContent = "Unavailable";
      }
      const expiringSoon =
        state.httpsCertificateExpiringSoon === true
        || (
          Number.isInteger(state.httpsCertificateDaysRemaining)
          && state.httpsCertificateDaysRemaining <= 30
        );
      httpsCertificateExpiryGroup.classList.toggle("expiring-soon", expiringSoon);
    }

    async function fetchClientSettings() {
      const resp = await apiFetch("/api/settings/client");
      if (!resp.ok) return;
      const data = await resp.json();
      const defaultHeartbeatFrequency = parseInt(
        data.default_heartbeat_frequency,
        10
      );
      if (!Number.isNaN(defaultHeartbeatFrequency) && defaultHeartbeatFrequency > 0) {
        state.defaultHeartbeatFrequency = defaultHeartbeatFrequency;
      }
    }

    async function fetchDiagnosticSettings() {
      const resp = await apiFetch("/api/settings/diagnostic");
      if (!resp.ok) {
        state.diagnosticEnabled = false;
        state.statePersistenceEnabled = false;
        return;
      }
      const data = await resp.json();
      state.diagnosticEnabled = data.diagnostic_enabled === true;
      state.statePersistenceEnabled = data.state_persistence_enabled === true;
    }

    async function loadServerOpampConfigTab() {
      if (!state.diagnosticEnabled) {
        serverOpampConfigPathOutput.textContent = "Diagnostic mode disabled";
        serverOpampConfigOutput.textContent =
          "Diagnostic mode disabled. Start server with --diagnostic to enable this tab.";
        return;
      }
      const resp = await apiFetch("/api/settings/server-opamp-config");
      if (!resp.ok) {
        if (resp.status === 403) {
          serverOpampConfigPathOutput.textContent = "Diagnostic mode disabled";
          serverOpampConfigOutput.textContent =
            "Diagnostic mode disabled. Restart server with --diagnostic.";
          return;
        }
        serverOpampConfigPathOutput.textContent = "Unavailable";
        serverOpampConfigOutput.textContent =
          "Failed to load provider config from server.";
        return;
      }
      const data = await resp.json();
      const configPath = String(data.config_path || "").trim();
      const configText = data.config_text;
      if (!configPath || typeof configText !== "string") {
        serverOpampConfigPathOutput.textContent = "Invalid payload";
        serverOpampConfigOutput.textContent =
          "Server returned an invalid diagnostic response payload.";
        return;
      }
      serverOpampConfigPathOutput.textContent = configPath;
      serverOpampConfigOutput.textContent = configText;
    }

    async function fetchGlobalSettingsHelp() {
      applyGlobalSettingsHelp(DEFAULT_GLOBAL_SETTINGS_HELP);
      const resp = await apiFetch("/api/help/global-settings");
      if (!resp.ok) return;
      const data = await resp.json();
      const fields = data && typeof data.fields === "object" ? data.fields : {};
      applyGlobalSettingsHelp(fields);
    }

    function applyGlobalSettingsHelp(fields) {
      const resolvedFields = {};
      Object.keys(DEFAULT_GLOBAL_SETTINGS_HELP).forEach(key => {
        const incoming = fields && typeof fields[key] === "object" ? fields[key] : {};
        resolvedFields[key] = {
          label: String(incoming.label || DEFAULT_GLOBAL_SETTINGS_HELP[key].label),
          tooltip: String(incoming.tooltip || DEFAULT_GLOBAL_SETTINGS_HELP[key].tooltip),
        };
      });
      const bindings = [
        {
          key: "delayed_comms_seconds",
          label: delayedCommsSecondsLabel,
          icon: document.querySelector('.help-icon[data-help-key="delayed_comms_seconds"]'),
        },
        {
          key: "significant_comms_seconds",
          label: significantCommsSecondsLabel,
          icon: document.querySelector('.help-icon[data-help-key="significant_comms_seconds"]'),
        },
        {
          key: "default_heartbeat_frequency",
          label: defaultHeartbeatFrequencyLabel,
          icon: document.querySelector('.help-icon[data-help-key="default_heartbeat_frequency"]'),
        },
        {
          key: "client_event_history_size",
          label: clientEventHistorySizeLabel,
          icon: document.querySelector('.help-icon[data-help-key="client_event_history_size"]'),
        },
        {
          key: "human_in_loop_approval",
          label: humanInLoopApprovalLabel,
          icon: document.querySelector('.help-icon[data-help-key="human_in_loop_approval"]'),
        },
        {
          key: "state_persistence_enabled",
          label: statePersistenceEnabledLabel,
          icon: document.querySelector('.help-icon[data-help-key="state_persistence_enabled"]'),
        },
        {
          key: "state_save_folder",
          label: stateSaveFolderLabel,
          icon: document.querySelector('.help-icon[data-help-key="state_save_folder"]'),
        },
        {
          key: "retention_count",
          label: retentionCountLabel,
          icon: document.querySelector('.help-icon[data-help-key="retention_count"]'),
        },
        {
          key: "autosave_interval_seconds_since_change",
          label: autosaveIntervalLabel,
          icon: document.querySelector('.help-icon[data-help-key="autosave_interval_seconds_since_change"]'),
        },
      ];
      bindings.forEach(binding => {
        const item = resolvedFields[binding.key];
        if (!item) return;
        if (binding.label) binding.label.textContent = item.label;
        if (binding.icon) {
          binding.icon.title = item.tooltip;
          binding.icon.dataset.helpText = item.tooltip;
          binding.icon.setAttribute("aria-label", `${item.label} help`);
        }
      });
      bindHelpIcons();
    }

    function bindHelpIcons() {
      document.querySelectorAll(".help-icon[data-help-key]").forEach(icon => {
        if (icon.dataset.helpBound === "true") return;
        icon.dataset.helpBound = "true";
        icon.addEventListener("click", event => {
          event.preventDefault();
          event.stopPropagation();
          const target = event.currentTarget;
          const tooltipText = String(target.dataset.helpText || target.title || "").trim();
          if (!tooltipText) return;
          if (activeHelpPopover && activeHelpIcon === target) {
            hideHelpPopover();
            return;
          }
          showHelpPopover(target, tooltipText);
        });
      });
    }

    function showHelpPopover(icon, tooltipText) {
      hideHelpPopover();
      const popover = document.createElement("div");
      popover.className = "help-popover";
      popover.setAttribute("role", "tooltip");
      popover.textContent = tooltipText;
      document.body.appendChild(popover);

      const iconRect = icon.getBoundingClientRect();
      const popoverRect = popover.getBoundingClientRect();
      let left = iconRect.left + (iconRect.width / 2) - (popoverRect.width / 2);
      left = Math.max(8, Math.min(left, window.innerWidth - popoverRect.width - 8));
      let top = iconRect.bottom + 8;
      if (top + popoverRect.height > window.innerHeight - 8) {
        top = iconRect.top - popoverRect.height - 8;
      }
      if (top < 8) top = 8;
      popover.style.left = `${left}px`;
      popover.style.top = `${top}px`;
      activeHelpPopover = popover;
      activeHelpIcon = icon;
    }

    function hideHelpPopover() {
      if (!activeHelpPopover) return;
      activeHelpPopover.remove();
      activeHelpPopover = null;
      activeHelpIcon = null;
    }

    async function fetchCustomCommands() {
      const clientId = activeClient && activeClient.client_id
        ? String(activeClient.client_id)
        : "";
      const query = clientId
        ? `?client_id=${encodeURIComponent(clientId)}`
        : "";
      const resp = await apiFetch(`/api/commands/custom${query}`);
      if (!resp.ok) return;
      const data = await resp.json();
      state.customCommands = Array.isArray(data.commands) ? data.commands : [];
    }

    function updatePendingApprovalCount(countValue) {
      const parsed = parseInt(countValue, 10);
      pendingApprovalCount.textContent = Number.isNaN(parsed) ? "0" : String(parsed);
    }

    function updatePendingApprovalVisibility() {
      const enabled = state.humanInLoopApproval === true;
      pendingApprovalPill.classList.toggle("hidden", !enabled);
      pendingApprovalPill.setAttribute("aria-hidden", enabled ? "false" : "true");
      pendingApprovalPill.tabIndex = enabled ? 0 : -1;
      if (!enabled && pendingApprovalModal.classList.contains("open")) {
        closePendingApprovalModal();
      }
    }

    async function fetchPendingApprovals() {
      if (state.humanInLoopApproval !== true) {
        state.pendingApprovals = [];
        updatePendingApprovalCount(0);
        return;
      }
      const resp = await apiFetch("/api/approvals/pending");
      if (!resp.ok) return;
      const data = await resp.json();
      state.pendingApprovals = Array.isArray(data.clients) ? data.clients : [];
      updatePendingApprovalCount(state.pendingApprovals.length);
      if (pendingApprovalModal.classList.contains("open")) {
        renderPendingApprovalTable();
      }
    }

    function renderFeatureMenuItems(items) {
      if (!featureMenuGroup || !featureMenuSelect) return;
      const list = Array.isArray(items) ? items : [];
      featureMenuSelect.innerHTML = "";
      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = "Open...";
      featureMenuSelect.appendChild(placeholder);

      list.forEach(item => {
        const label = String(item && item.label ? item.label : "").trim();
        const url = String(item && item.url ? item.url : "").trim();
        const target = String(item && item.target ? item.target : "_self").trim() || "_self";
        if (!label || !url) return;
        const opt = document.createElement("option");
        opt.value = url;
        opt.textContent = label;
        opt.dataset.target = target;
        featureMenuSelect.appendChild(opt);
      });
      const hasItems = featureMenuSelect.options.length > 1;
      featureMenuGroup.classList.toggle("hidden", !hasItems);
      featureMenuSelect.selectedIndex = 0;
    }

    function updateRequestedConfigEditingState() {
      if (!requestedConfigPanel || !configInput || !saveConfigBtn) return;
      const configServiceAvailable = state.configServiceFeatureAvailable === true;
      requestedConfigPanel.classList.toggle("hidden", configServiceAvailable);
      configInput.readOnly = false;
      configInput.classList.remove("requested-config-readonly");
      saveConfigBtn.disabled = false;
      saveConfigBtn.title = "";
    }

    async function fetchUiFeatureMenu() {
      if (!featureMenuGroup || !featureMenuSelect) return;
      state.catalogFeatureUrl = "";
      state.configServiceFeatureAvailable = false;
      const resp = await apiFetch("/api/ui/features");
      if (!resp.ok) {
        featureMenuGroup.classList.add("hidden");
        updateRequestedConfigEditingState();
        return;
      }
      const payload = await resp.json();
      const items = Array.isArray(payload.items) ? payload.items : [];
      const configServiceItem = items.find(item => {
        return String(item && item.entry_point ? item.entry_point : "").trim()
          === CONFIG_SERVICE_FEATURE_ENTRY_POINT;
      });
      const catalogItem = items.find(item => {
        return String(item && item.entry_point ? item.entry_point : "").trim()
          === CATALOG_FEATURE_ENTRY_POINT;
      });
      state.configServiceFeatureAvailable = Boolean(
        configServiceItem && String(configServiceItem.url || "").trim()
      );
      state.catalogFeatureUrl = catalogItem ? String(catalogItem.url || "").trim() : "";
      renderFeatureMenuItems(items);
      updateRequestedConfigEditingState();
      if (activeClient && modal.classList.contains("open")) {
        updateRequestedConfigEditingState();
        renderRemoteConfigSelectionTable(activeClient);
      }
    }

    function basenameForPath(pathValue) {
      const normalizedPath = String(pathValue || "").trim();
      if (!normalizedPath) return "";
      const parts = normalizedPath.split(/[\\/]/);
      return String(parts[parts.length - 1] || "").trim();
    }

    function normalizeRemoteConfigSelectionItem(item, index = 0) {
      if (!item || typeof item !== "object") return null;
      const sourcePath = String(item.source_path || "").trim();
      const targetName = String(item.target_name || "").trim();
      const filename = String(
        item.filename
        || basenameForPath(targetName)
        || basenameForPath(sourcePath)
        || `selection-${index + 1}`
      ).trim();
      if (!sourcePath || !targetName) return null;
      return {
        source_path: sourcePath,
        target_name: targetName,
        filename,
      };
    }

    function normalizeRemoteConfigSelectionItems(files) {
      const items = Array.isArray(files) ? files : [];
      const normalized = [];
      items.forEach((item, index) => {
        const normalizedItem = normalizeRemoteConfigSelectionItem(item, index);
        if (normalizedItem) {
          normalized.push(normalizedItem);
        }
      });
      return normalized;
    }

    function remoteConfigSelectionsForClient(clientId) {
      const normalizedClientId = String(clientId || "").trim();
      if (!normalizedClientId) return [];
      return normalizeRemoteConfigSelectionItems(
        state.remoteConfigSelectionsByClient[normalizedClientId]
      );
    }

    function setRemoteConfigSelectionsForClient(clientId, files) {
      const normalizedClientId = String(clientId || "").trim();
      if (!normalizedClientId) return;
      state.remoteConfigSelectionsByClient[normalizedClientId] =
        normalizeRemoteConfigSelectionItems(files);
    }

    function setRemoteConfigStatus(message, tone = "") {
      if (!remoteConfigStatus) return;
      remoteConfigStatus.textContent = String(message || "");
      remoteConfigStatus.classList.remove("success", "error");
      if (tone === "success" || tone === "error") {
        remoteConfigStatus.classList.add(tone);
      }
    }

    function clearRemoteConfigStatus() {
      setRemoteConfigStatus("");
    }

    function renderRemoteConfigSelectionTable(client) {
      if (
        !remoteConfigEnhancedPanel
        || !remoteConfigCatalogHint
        || !remoteConfigEmptyState
        || !remoteConfigSelectionBody
        || !remoteConfigSelectionTable
        || !selectRemoteConfigsBtn
        || !sendRemoteConfigFilesBtn
      ) {
        return;
      }

      const providerAllowsRemoteConfig =
        client && client.provider_remote_config_enabled === true;
      const capabilityReported = client && client.remote_config_capability_reported === true;
      const clientAllowsRemoteConfig =
        client && client.remote_config_files_allowed === true;
      remoteConfigEnhancedPanel.classList.toggle(
        "hidden",
        clientAllowsRemoteConfig !== true
      );
      if (clientAllowsRemoteConfig !== true) {
        remoteConfigSelectionBody.innerHTML = "";
        remoteConfigSelectionTable.classList.add("hidden");
        remoteConfigEmptyState.classList.remove("hidden");
        selectRemoteConfigsBtn.classList.add("hidden");
        sendRemoteConfigFilesBtn.disabled = true;
        remoteConfigCatalogHint.textContent = providerAllowsRemoteConfig
          ? "Remote config file selection is disabled because this client is not reporting remote-config support."
          : "Remote config file selection is disabled by provider configuration.";
        clearRemoteConfigStatus();
        return;
      }

      const clientId = String(client && client.client_id ? client.client_id : "").trim();
      const selections = remoteConfigSelectionsForClient(clientId);
      const catalogAvailable = Boolean(String(state.catalogFeatureUrl || "").trim());

      selectRemoteConfigsBtn.classList.toggle("hidden", !catalogAvailable);
      sendRemoteConfigFilesBtn.disabled = selections.length === 0;
      sendRemoteConfigFilesBtn.title = selections.length === 0
        ? "Select one or more catalog files before sending remote config"
        : "Queue the selected remote configuration files for this client";

      if (catalogAvailable) {
        remoteConfigCatalogHint.textContent = capabilityReported
          ? "Use Select Configs to choose catalog files, then send them when you are ready."
          : (
            "Use Select Configs to choose catalog files. "
            + "Sending may still be rejected until the client reports remote-config support."
          );
      } else {
        remoteConfigCatalogHint.textContent =
          "Catalog-based remote config selection is not available in this deployment.";
      }

      remoteConfigSelectionBody.innerHTML = "";
      if (selections.length === 0) {
        remoteConfigSelectionTable.classList.add("hidden");
        remoteConfigEmptyState.classList.remove("hidden");
        return;
      }

      remoteConfigSelectionTable.classList.remove("hidden");
      remoteConfigEmptyState.classList.add("hidden");
      selections.forEach((selection, index) => {
        const row = document.createElement("tr");
        row.className = "remote-config-row";
        row.draggable = true;
        row.dataset.selectionIndex = String(index);
        row.addEventListener("dragstart", event => {
          draggingRemoteConfigSelectionClientId = clientId;
          draggingRemoteConfigSelectionIndex = index;
          row.classList.add("dragging");
          if (event.dataTransfer) {
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", `${clientId}:${index}`);
          }
        });
        row.addEventListener("dragover", event => {
          if (
            draggingRemoteConfigSelectionClientId !== clientId
            || draggingRemoteConfigSelectionIndex === index
          ) {
            return;
          }
          event.preventDefault();
          const rect = row.getBoundingClientRect();
          const placeAfter = (event.clientY - rect.top) > (rect.height / 2);
          row.classList.toggle("drag-over-top", !placeAfter);
          row.classList.toggle("drag-over-bottom", placeAfter);
          if (event.dataTransfer) {
            event.dataTransfer.dropEffect = "move";
          }
        });
        row.addEventListener("dragleave", () => {
          row.classList.remove("drag-over-top", "drag-over-bottom");
        });
        row.addEventListener("drop", event => {
          if (
            draggingRemoteConfigSelectionClientId !== clientId
            || draggingRemoteConfigSelectionIndex < 0
            || draggingRemoteConfigSelectionIndex === index
          ) {
            return;
          }
          event.preventDefault();
          const rect = row.getBoundingClientRect();
          const placeAfter = (event.clientY - rect.top) > (rect.height / 2);
          moveRemoteConfigSelectionToIndex(
            clientId,
            draggingRemoteConfigSelectionIndex,
            index,
            placeAfter
          );
        });
        row.addEventListener("dragend", () => {
          draggingRemoteConfigSelectionClientId = "";
          draggingRemoteConfigSelectionIndex = -1;
          row.classList.remove("dragging", "drag-over-top", "drag-over-bottom");
          remoteConfigSelectionBody.querySelectorAll(".remote-config-row").forEach(item => {
            item.classList.remove("dragging", "drag-over-top", "drag-over-bottom");
          });
        });

        const filenameCell = document.createElement("td");
        filenameCell.textContent = selection.filename || selection.target_name;
        row.appendChild(filenameCell);

        const actionsCell = document.createElement("td");
        actionsCell.className = "remote-config-actions";

        const dragHandle = document.createElement("span");
        dragHandle.className = "remote-config-drag-handle";
        dragHandle.textContent = "⋮⋮";
        dragHandle.title = "Drag to reorder selected remote config files";
        actionsCell.appendChild(dragHandle);

        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.textContent = "Remove";
        removeButton.addEventListener("click", () => {
          removeRemoteConfigSelection(clientId, index);
        });
        actionsCell.appendChild(removeButton);

        row.appendChild(actionsCell);
        remoteConfigSelectionBody.appendChild(row);
      });
    }

    function moveRemoteConfigSelectionToIndex(clientId, fromIndex, targetIndex, placeAfter) {
      const selections = remoteConfigSelectionsForClient(clientId);
      const currentIndex = Number(fromIndex);
      const targetRowIndex = Number(targetIndex);
      if (
        currentIndex < 0
        || currentIndex >= selections.length
        || targetRowIndex < 0
        || targetRowIndex >= selections.length
      ) {
        return;
      }
      const nextSelections = [...selections];
      const [movedSelection] = nextSelections.splice(currentIndex, 1);
      let insertIndex = placeAfter === true ? targetRowIndex + 1 : targetRowIndex;
      if (currentIndex < insertIndex) {
        insertIndex -= 1;
      }
      nextSelections.splice(insertIndex, 0, movedSelection);
      setRemoteConfigSelectionsForClient(clientId, nextSelections);
      if (activeClient && activeClient.client_id === clientId) {
        renderRemoteConfigSelectionTable(activeClient);
        setRemoteConfigStatus("Updated remote config file order.", "success");
      }
    }

    function removeRemoteConfigSelection(clientId, index) {
      const selections = remoteConfigSelectionsForClient(clientId);
      const currentIndex = Number(index);
      if (currentIndex < 0 || currentIndex >= selections.length) {
        return;
      }
      const nextSelections = selections.filter((_item, itemIndex) => itemIndex !== currentIndex);
      setRemoteConfigSelectionsForClient(clientId, nextSelections);
      if (activeClient && activeClient.client_id === clientId) {
        renderRemoteConfigSelectionTable(activeClient);
        setRemoteConfigStatus(
          nextSelections.length === 0
            ? "Removed selected remote config file."
            : "Updated remote config file selection.",
          "success"
        );
      }
    }

    function remoteConfigSelectionCallbackUrl(clientId) {
      const targetUrl = new URL(
        `/api/clients/${encodeURIComponent(clientId)}/remote-config-selection`,
        window.location.origin
      );
      return targetUrl.toString();
    }

    function openRemoteConfigCatalogPopup() {
      if (!activeClient) return;
      const catalogUrl = String(state.catalogFeatureUrl || "").trim();
      if (!catalogUrl) {
        setRemoteConfigStatus(
          "Catalog-based selection is not available in this deployment.",
          "error"
        );
        return;
      }
      const popupUrl = new URL(catalogUrl, window.location.origin);
      popupUrl.searchParams.set(
        CATALOG_SELECTION_CALLBACK_QUERY,
        remoteConfigSelectionCallbackUrl(activeClient.client_id)
      );
      window.open(
        popupUrl.toString(),
        `catalog-selection-${String(activeClient.client_id || "client").trim()}`,
        "popup=yes,width=1200,height=900,resizable=yes,scrollbars=yes"
      );
    }

    function handleCatalogSelectionMessage(event) {
      if (!event || event.origin !== window.location.origin) return;
      const payload = event.data;
      if (!payload || typeof payload !== "object") return;
      if (payload.type !== CATALOG_SELECTION_APPLIED_MESSAGE_TYPE) return;

      const clientId = String(payload.client_id || "").trim();
      if (!clientId) return;
      const files = normalizeRemoteConfigSelectionItems(payload.files);
      setRemoteConfigSelectionsForClient(clientId, files);
      if (activeClient && activeClient.client_id === clientId) {
        renderRemoteConfigSelectionTable(activeClient);
        setRemoteConfigStatus(
          files.length === 1
            ? "Selected 1 remote config file from the catalog."
            : `Selected ${files.length} remote config files from the catalog.`,
          "success"
        );
      }
    }

    async function sendRemoteConfigFiles() {
      if (!activeClient || !sendRemoteConfigFilesBtn) return;
      const clientId = String(activeClient.client_id || "").trim();
      const selections = remoteConfigSelectionsForClient(clientId);
      if (selections.length === 0) {
        setRemoteConfigStatus(
          "Select one or more remote config files before sending.",
          "error"
        );
        return;
      }

      const originalLabel = sendRemoteConfigFilesBtn.textContent;
      sendRemoteConfigFilesBtn.disabled = true;
      sendRemoteConfigFilesBtn.textContent = "Sending...";
      setRemoteConfigStatus("Queueing remote config files...");

      try {
        const resp = await apiFetch(`/api/clients/${clientId}/remote-config`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            files: selections.map(selection => ({
              source_path: selection.source_path,
              target_name: selection.target_name,
            })),
          }),
        });
        const payload = await resp.json().catch(() => ({}));
        if (!resp.ok) {
          const errorMessage = String(
            payload && payload.error
              ? payload.error
              : "Failed to queue remote config files."
          );
          setRemoteConfigStatus(errorMessage, "error");
          return;
        }

        if (Array.isArray(payload.files)) {
          setRemoteConfigSelectionsForClient(clientId, payload.files);
        }
        const queuedCount = Array.isArray(payload.files) ? payload.files.length : selections.length;
        const queuedMessage = queuedCount === 1
          ? "Queued 1 remote config file."
          : `Queued ${queuedCount} remote config files.`;

        const preservedCustomCommandState = captureCustomCommandState();
        const healthPanelOpen = !componentHealthPanel.classList.contains("hidden");
        await fetchClients();
        const refreshed = state.clients.find(
          clientEntry => clientEntry.client_id === clientId
        );
        if (refreshed) {
          openModal(refreshed, {
            ...captureOpenModalState(),
            customCommandState: preservedCustomCommandState,
            healthPanelOpen: healthPanelOpen,
          });
        }
        setRemoteConfigStatus(queuedMessage, "success");
      } catch (_error) {
        setRemoteConfigStatus("Failed to queue remote config files.", "error");
      } finally {
        sendRemoteConfigFilesBtn.disabled = false;
        sendRemoteConfigFilesBtn.textContent = originalLabel;
        if (activeClient && activeClient.client_id === clientId) {
          renderRemoteConfigSelectionTable(activeClient);
        }
      }
    }

    function handleFeatureMenuSelection() {
      if (!featureMenuSelect) return;
      const selected = featureMenuSelect.options[featureMenuSelect.selectedIndex];
      if (!selected) return;
      const url = String(selected.value || "").trim();
      if (!url) return;
      const target = String(selected.dataset.target || "_self").trim() || "_self";
      if (target === "_blank") {
        window.open(url, "_blank", "noopener,noreferrer");
      } else {
        window.location.assign(url);
      }
      featureMenuSelect.selectedIndex = 0;
    }

    function defaultColumnOrder() {
      return [...TABLE_COLUMN_KEYS];
    }

    function defaultVisibleColumns() {
      return { ...DEFAULT_VISIBLE_COLUMNS };
    }

    function sanitizeColumnOrder(rawOrder) {
      const incoming = Array.isArray(rawOrder) ? rawOrder : [];
      const unique = [];
      incoming.forEach(key => {
        const normalized = String(key || "").trim();
        if (!TABLE_COLUMN_KEYS.includes(normalized)) return;
        if (unique.includes(normalized)) return;
        unique.push(normalized);
      });
      TABLE_COLUMN_KEYS.forEach(key => {
        if (!unique.includes(key)) unique.push(key);
      });
      return unique;
    }

    function sanitizeVisibleColumns(rawVisible) {
      const visible = defaultVisibleColumns();
      if (!rawVisible || typeof rawVisible !== "object") {
        return visible;
      }
      OPTIONAL_TABLE_COLUMNS.forEach(key => {
        if (Object.prototype.hasOwnProperty.call(rawVisible, key)) {
          visible[key] = rawVisible[key] === true;
        }
      });
      return visible;
    }

    function readCookieValue(name) {
      const encodedName = `${encodeURIComponent(name)}=`;
      const parts = String(document.cookie || "").split(";");
      for (const part of parts) {
        const trimmed = part.trim();
        if (!trimmed.startsWith(encodedName)) continue;
        return decodeURIComponent(trimmed.slice(encodedName.length));
      }
      return "";
    }

    function writeCookieValue(name, value) {
      document.cookie = [
        `${encodeURIComponent(name)}=${encodeURIComponent(value)}`,
        `max-age=${UI_PREFS_COOKIE_MAX_AGE_SECONDS}`,
        "path=/",
        "samesite=lax",
      ].join("; ");
    }

    function persistUiPreferencesToCookie() {
      const payload = {
        v: 1,
        columnOrder: sanitizeColumnOrder(state.columnOrder),
        visibleColumns: sanitizeVisibleColumns(state.visibleColumns),
      };
      try {
        writeCookieValue(UI_PREFS_COOKIE_NAME, JSON.stringify(payload));
      } catch (_error) {
        // Ignore cookie failures and continue with in-memory preferences.
      }
    }

    function loadUiPreferencesFromCookie() {
      state.columnOrder = defaultColumnOrder();
      state.visibleColumns = defaultVisibleColumns();
      state.columnControlsCollapsed = true;
      state.columnFilters = {};

      try {
        const raw = readCookieValue(UI_PREFS_COOKIE_NAME);
        if (!raw) return;
        const payload = JSON.parse(raw);
        if (!payload || typeof payload !== "object") return;
        state.columnOrder = sanitizeColumnOrder(payload.columnOrder);
        state.visibleColumns = sanitizeVisibleColumns(payload.visibleColumns);
      } catch (_error) {
        // Ignore malformed cookie payloads and fall back to defaults.
      }
    }

    function setColumnsCollapsed(collapsed) {
      const isCollapsed = collapsed === true;
      state.columnControlsCollapsed = isCollapsed;
      columnControls.classList.toggle("collapsed", isCollapsed);
      toggleColumnsBtn.textContent = isCollapsed ? "Show Columns" : "Hide Columns";
      toggleColumnsBtn.setAttribute("aria-expanded", isCollapsed ? "false" : "true");
      toggleColumnsBtn.classList.toggle("closed", isCollapsed);
    }

    function visibleOptionalColumnCount() {
      return OPTIONAL_TABLE_COLUMNS.filter(key => state.visibleColumns[key] === true).length;
    }

    function updateColumnsButtonState() {
      const visibleCount = visibleOptionalColumnCount();
      toggleColumnsBtn.classList.toggle(
        "columns-active",
        state.columnControlsCollapsed === true && visibleCount > 0
      );
    }

    function writeColumnControlsToInputs() {
      columnToggleInputs.forEach(input => {
        const key = String(input.dataset.columnToggle || "").trim();
        if (!key) return;
        input.checked = state.visibleColumns[key] === true;
      });
      setColumnsCollapsed(state.columnControlsCollapsed);
      updateColumnsButtonState();
    }

    function syncColumnSelectionFromInputs() {
      OPTIONAL_TABLE_COLUMNS.forEach(key => {
        const input = columnToggleInputs.find(
          item => String(item.dataset.columnToggle || "").trim() === key
        );
        if (!input) return;
        state.visibleColumns[key] = input.checked === true;
      });
      state.visibleColumns = sanitizeVisibleColumns(state.visibleColumns);
      TABLE_COLUMN_KEYS.forEach(key => {
        if (state.visibleColumns[key] === true) return;
        if (MULTI_SELECT_FILTER_COLUMNS.includes(key)) {
          state.columnFilters[key] = [];
        } else {
          state.columnFilters[key] = "";
        }
      });
    }

    function toggleColumnsPanel() {
      setColumnsCollapsed(state.columnControlsCollapsed !== true);
      updateColumnsButtonState();
    }

    function getVisibleOrderedColumnKeys() {
      return sanitizeColumnOrder(state.columnOrder).filter(
        key => state.visibleColumns[key] === true
      );
    }

    function defaultColumnFilterValue(columnKey) {
      return MULTI_SELECT_FILTER_COLUMNS.includes(columnKey) ? [] : "";
    }

    function normalizeColumnFilterValue(columnKey, value) {
      if (MULTI_SELECT_FILTER_COLUMNS.includes(columnKey)) {
        const values = Array.isArray(value) ? value : [value];
        const normalized = [];
        values.forEach(item => {
          const candidate = String(item || "").trim();
          if (!candidate || normalized.includes(candidate)) return;
          normalized.push(candidate);
        });
        return normalized;
      }
      return String(value || "").trim();
    }

    function normalizeColumnFilters(filters) {
      const next = {};
      TABLE_COLUMN_KEYS.forEach(columnKey => {
        next[columnKey] = defaultColumnFilterValue(columnKey);
      });
      if (!filters || typeof filters !== "object") return next;
      TABLE_COLUMN_KEYS.forEach(columnKey => {
        if (!Object.prototype.hasOwnProperty.call(filters, columnKey)) return;
        next[columnKey] = normalizeColumnFilterValue(columnKey, filters[columnKey]);
      });
      return next;
    }

    function moveColumnRelativeToTarget(dragKey, targetKey, placeAfter) {
      const normalizedDrag = String(dragKey || "").trim();
      const normalizedTarget = String(targetKey || "").trim();
      if (!normalizedDrag || !normalizedTarget) return false;
      if (normalizedDrag === normalizedTarget) return false;
      const current = sanitizeColumnOrder(state.columnOrder);
      const withoutDrag = current.filter(key => key !== normalizedDrag);
      const targetIndex = withoutDrag.indexOf(normalizedTarget);
      if (targetIndex < 0) return false;
      const insertIndex = placeAfter ? targetIndex + 1 : targetIndex;
      withoutDrag.splice(insertIndex, 0, normalizedDrag);
      state.columnOrder = sanitizeColumnOrder(withoutDrag);
      return true;
    }

    function getClientHostMetadata(client) {
      const agentDesc = client && client.agent_description ? String(client.agent_description) : "";
      const hostType = extractAgentField(agentDesc, "os_type");
      const hostVersion = extractAgentField(agentDesc, "os_version");
      const hostName = extractAgentField(agentDesc, "hostname");
      const reportedIpAddress =
        extractAgentField(agentDesc, "ip_address")
        || extractAgentField(agentDesc, "ip")
        || extractAgentField(agentDesc, "host.ip");
      const sourceIpAddress = client && client.remote_addr ? String(client.remote_addr) : "";
      return {
        hostType: String(hostType || "").trim(),
        hostVersion: String(hostVersion || "").trim(),
        hostName: String(hostName || "").trim(),
        hostIp: String(reportedIpAddress || sourceIpAddress || "").trim(),
      };
    }

    function displayFilterValue(value) {
      const normalized = String(value || "").trim();
      return normalized || "--";
    }

    function clientValueForColumn(client, columnKey) {
      const hostMeta = getClientHostMetadata(client);
      if (columnKey === "service_instance_id") return getClientDisplayId(client);
      if (columnKey === "instance_uid") return String(client && client.client_id ? client.client_id : "--");
      if (columnKey === "status") return computeStatus(client).label;
      if (columnKey === "health_status") return getClientHealthInfo(client).summary;
      if (columnKey === "last_seen") {
        return client && client.last_communication
          ? new Date(client.last_communication).toLocaleString()
          : "--";
      }
      if (columnKey === "config_version") return String(client && client.current_config_version ? client.current_config_version : "--");
      if (columnKey === "first_registered") {
        return client && client.first_seen
          ? new Date(client.first_seen).toLocaleString()
          : "--";
      }
      if (columnKey === "client_version") return String(client && client.client_version ? client.client_version : "--");
      if (columnKey === "host_type") return hostMeta.hostType || "--";
      if (columnKey === "host_version") return hostMeta.hostVersion || "--";
      if (columnKey === "host_name") return hostMeta.hostName || "--";
      if (columnKey === "host_ip") return hostMeta.hostIp || "--";
      return "--";
    }

    function discoveredValuesForColumn(columnKey) {
      const values = [];
      state.clients.forEach(client => {
        const value = displayFilterValue(clientValueForColumn(client, columnKey));
        if (!values.includes(value)) {
          values.push(value);
        }
      });
      if (columnKey === "status") {
        const order = ["ok", "delayed", "late", "disconnected", "unknown", "--"];
        return values.sort((a, b) => {
          const aIndex = order.indexOf(a);
          const bIndex = order.indexOf(b);
          const safeA = aIndex >= 0 ? aIndex : order.length;
          const safeB = bIndex >= 0 ? bIndex : order.length;
          if (safeA !== safeB) return safeA - safeB;
          return a.localeCompare(b);
        });
      }
      if (columnKey === "health_status") {
        const order = ["healthy", "unhealthy", "unknown", "--"];
        return values.sort((a, b) => {
          const aIndex = order.indexOf(a);
          const bIndex = order.indexOf(b);
          const safeA = aIndex >= 0 ? aIndex : order.length;
          const safeB = bIndex >= 0 ? bIndex : order.length;
          if (safeA !== safeB) return safeA - safeB;
          return a.localeCompare(b);
        });
      }
      return values.sort((a, b) => a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" }));
    }

    function toComparableValue(value) {
      if (typeof value === "number") return value;
      return String(value || "").toLowerCase();
    }

    function getSortValue(client, sortKey) {
      const key = String(sortKey || "").trim();
      if (key === "service_instance_id") {
        return toComparableValue(getClientDisplayId(client));
      }
      if (key === "status") {
        const status = computeStatus(client);
        if (status.cls === "late-red") return 3;
        if (status.cls === "late-amber") return 2;
        if (status.cls === "disconnected") return 1;
        if (status.label === "ok") return 0;
        return -1;
      }
      if (key === "last_communication") {
        const rawDate = client && client.last_communication
          ? new Date(client.last_communication).getTime()
          : 0;
        return Number.isNaN(rawDate) ? 0 : rawDate;
      }
      if (key === "health_status") {
        const healthInfo = getClientHealthInfo(client);
        if (healthInfo.summary === "unhealthy") return 2;
        if (healthInfo.summary === "healthy") return 1;
        return 0;
      }
      if (key === "first_seen") {
        const rawDate = client && client.first_seen
          ? new Date(client.first_seen).getTime()
          : 0;
        return Number.isNaN(rawDate) ? 0 : rawDate;
      }
      if (key === "host_type" || key === "host_version" || key === "host_name" || key === "host_ip") {
        const hostMeta = getClientHostMetadata(client);
        if (key === "host_type") return toComparableValue(hostMeta.hostType);
        if (key === "host_version") return toComparableValue(hostMeta.hostVersion);
        if (key === "host_name") return toComparableValue(hostMeta.hostName);
        return toComparableValue(hostMeta.hostIp);
      }
      return toComparableValue(client && client[key] !== undefined ? client[key] : "");
    }

    function toggleSortByKey(key) {
      const normalizedKey = String(key || "").trim();
      if (!normalizedKey) return;
      if (state.sortKey === normalizedKey) {
        state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      } else {
        state.sortKey = normalizedKey;
        state.sortDir = "asc";
      }
      renderTable();
    }

    function renderClientTableHeader() {
      if (!clientTableHeaderRow) return;
      const visibleColumns = getVisibleOrderedColumnKeys();
      clientTableHeaderRow.innerHTML = "";
      visibleColumns.forEach(columnKey => {
        const columnMeta = TABLE_COLUMN_DEFINITIONS[columnKey];
        if (!columnMeta) return;
        const th = document.createElement("th");
        th.className = "column-header";
        th.draggable = true;
        th.dataset.columnKey = columnKey;
        th.dataset.sort = columnMeta.sortKey;
        th.title = `${columnMeta.label} (click to sort, drag to reorder)`;
        if (columnMeta.headerHtml) {
          th.innerHTML = columnMeta.headerHtml;
        } else {
          th.textContent = columnMeta.label;
        }
        th.addEventListener("click", () => {
          if (skipSortClickForColumn && skipSortClickForColumn === columnKey) {
            skipSortClickForColumn = "";
            return;
          }
          toggleSortByKey(columnMeta.sortKey);
        });
        th.addEventListener("dragstart", event => {
          draggingColumnKey = columnKey;
          th.classList.add("dragging");
          if (event.dataTransfer) {
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", columnKey);
          }
        });
        th.addEventListener("dragover", event => {
          if (!draggingColumnKey || draggingColumnKey === columnKey) return;
          event.preventDefault();
          th.classList.add("drag-over");
          if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
        });
        th.addEventListener("dragleave", () => {
          th.classList.remove("drag-over");
        });
        th.addEventListener("drop", event => {
          event.preventDefault();
          th.classList.remove("drag-over");
          const dragKey = draggingColumnKey;
          if (!dragKey || dragKey === columnKey) return;
          const rect = th.getBoundingClientRect();
          const placeAfter = (event.clientX - rect.left) > (rect.width / 2);
          const moved = moveColumnRelativeToTarget(dragKey, columnKey, placeAfter);
          if (!moved) return;
          skipSortClickForColumn = columnKey;
          persistUiPreferencesToCookie();
          renderTable();
        });
        th.addEventListener("dragend", () => {
          draggingColumnKey = "";
          th.classList.remove("dragging");
          clientTableHeaderRow.querySelectorAll(".drag-over").forEach(item => {
            item.classList.remove("drag-over");
          });
        });
        clientTableHeaderRow.appendChild(th);
      });
      renderClientTableFilterRow();
    }

    function setColumnFilterValue(columnKey, value) {
      state.columnFilters[columnKey] = normalizeColumnFilterValue(columnKey, value);
      state.page = 1;
      renderClientTableBody();
    }

    function formatMultiSelectFilterSummary(columnKey) {
      const selected = normalizeColumnFilterValue(columnKey, state.columnFilters[columnKey]);
      if (selected.length === 0) return "All";
      if (selected.length === 1) return selected[0];
      return `${selected.length} selected`;
    }

    function renderClientTableFilterRow() {
      if (!clientTableFilterRow) return;
      const visibleColumns = getVisibleOrderedColumnKeys();
      clientTableFilterRow.innerHTML = "";
      visibleColumns.forEach(columnKey => {
        const th = document.createElement("th");
        th.dataset.columnKey = columnKey;
        th.addEventListener("click", event => {
          event.stopPropagation();
        });
        if (MULTI_SELECT_FILTER_COLUMNS.includes(columnKey)) {
          const details = document.createElement("details");
          details.className = "table-filter-multiselect";
          const summary = document.createElement("summary");
          summary.textContent = formatMultiSelectFilterSummary(columnKey);
          details.appendChild(summary);

          const menu = document.createElement("div");
          menu.className = "table-filter-multiselect-menu";
          discoveredValuesForColumn(columnKey).forEach(value => {
            const optionLabel = document.createElement("label");
            optionLabel.className = "table-filter-option";
            const checkbox = document.createElement("input");
            const optionText = document.createElement("span");
            checkbox.type = "checkbox";
            checkbox.value = value;
            checkbox.checked = normalizeColumnFilterValue(columnKey, state.columnFilters[columnKey]).includes(value);
            checkbox.addEventListener("click", event => {
              event.stopPropagation();
            });
            checkbox.addEventListener("change", () => {
              const selected = Array.from(menu.querySelectorAll('input[type="checkbox"]:checked'))
                .map(item => String(item.value || "").trim())
                .filter(Boolean);
              state.columnFilters[columnKey] = normalizeColumnFilterValue(columnKey, selected);
              summary.textContent = formatMultiSelectFilterSummary(columnKey);
              state.page = 1;
              renderClientTableBody();
            });
            optionText.textContent = value;
            optionLabel.appendChild(checkbox);
            optionLabel.appendChild(optionText);
            menu.appendChild(optionLabel);
          });
          details.appendChild(menu);
          th.appendChild(details);
        } else if (["service_instance_id", "instance_uid", "client_version", "host_name", "host_ip"].includes(columnKey)) {
          const input = document.createElement("input");
          input.type = "text";
          input.placeholder = `Filter ${TABLE_COLUMN_DEFINITIONS[columnKey].label}`;
          input.value = String(state.columnFilters[columnKey] || "");
          input.addEventListener("click", event => {
            event.stopPropagation();
          });
          input.addEventListener("input", () => {
            setColumnFilterValue(columnKey, input.value);
          });
          th.appendChild(input);
        }
        clientTableFilterRow.appendChild(th);
      });
    }

    function applyOptionalColumnSelection() {
      syncColumnSelectionFromInputs();
      persistUiPreferencesToCookie();
      state.page = 1;
      renderTable();
      updateColumnsButtonState();
    }

    async function fetchClients() {
      const resp = await apiFetch("/api/clients");
      if (!resp.ok) return;
      const data = await resp.json();
      state.clients = data.clients || [];
      lastUpdated.textContent = new Date().toLocaleTimeString();
      if (state.humanInLoopApproval === true) {
        updatePendingApprovalCount(data.pending_approval_total ?? state.pendingApprovals.length);
      } else {
        updatePendingApprovalCount(0);
      }
      renderTable();
      refreshOpenModal();
    }

    function computeStatus(client) {
      if (client.disconnected) {
        return { label: "disconnected", cls: "disconnected" };
      }
      if (!client.last_communication) {
        return { label: "unknown", cls: "" };
      }
      const last = new Date(client.last_communication);
      const delta = (Date.now() - last.getTime()) / 1000;
      if (delta > state.significant) {
        return { label: "late", cls: "late-red" };
      }
      if (delta > state.delayed) {
        return { label: "delayed", cls: "late-amber" };
      }
      return { label: "ok", cls: "" };
    }

    function hasPending(client) {
      const hasConfig = Boolean(client.requested_config);
      const hasCommand = Array.isArray(client.commands) && client.commands.some(cmd => !cmd.sent_at);
      return hasConfig || hasCommand;
    }

    function renderCellForColumn(client, status, columnKey) {
      const td = document.createElement("td");
      const hostMeta = getClientHostMetadata(client);
      const healthInfo = getClientHealthInfo(client);
      if (columnKey === "service_instance_id") {
        td.textContent = getClientDisplayId(client);
        return td;
      }
      if (columnKey === "instance_uid") {
        td.textContent = String(client.client_id ?? "--");
        return td;
      }
      if (columnKey === "status") {
        td.innerHTML = `<span class="status-dot ${status.cls}"><span class="dot"></span>${status.label}</span>`;
        return td;
      }
      if (columnKey === "health_status") {
        td.innerHTML = `<span class="${healthInfo.textClass}">${healthInfo.summary}</span>`;
        return td;
      }
      if (columnKey === "last_seen") {
        td.textContent = client.last_communication
          ? new Date(client.last_communication).toLocaleString()
          : "--";
        return td;
      }
      if (columnKey === "config_version") {
        td.textContent = String(client.current_config_version ?? "--");
        return td;
      }
      if (columnKey === "first_registered") {
        td.textContent = client.first_seen
          ? new Date(client.first_seen).toLocaleString()
          : "--";
        return td;
      }
      if (columnKey === "client_version") {
        td.textContent = String(client.client_version ?? "--");
        return td;
      }
      if (columnKey === "host_type") {
        td.textContent = hostMeta.hostType || "--";
        return td;
      }
      if (columnKey === "host_version") {
        td.textContent = hostMeta.hostVersion || "--";
        return td;
      }
      if (columnKey === "host_name") {
        td.textContent = hostMeta.hostName || "--";
        return td;
      }
      if (columnKey === "host_ip") {
        td.textContent = hostMeta.hostIp || "--";
        return td;
      }
      td.textContent = "--";
      return td;
    }

    function clientMatchesColumnFilters(client) {
      return TABLE_COLUMN_KEYS.every(columnKey => {
        const activeFilter = state.columnFilters[columnKey];
        if (MULTI_SELECT_FILTER_COLUMNS.includes(columnKey)) {
          const selected = normalizeColumnFilterValue(columnKey, activeFilter);
          if (selected.length === 0) return true;
          return selected.includes(displayFilterValue(clientValueForColumn(client, columnKey)));
        }
        const needle = String(activeFilter || "").trim().toLowerCase();
        if (!needle) return true;
        return displayFilterValue(clientValueForColumn(client, columnKey)).toLowerCase().includes(needle);
      });
    }

    function sortedFilteredClients() {
      const filtered = state.clients.filter(clientMatchesColumnFilters);
      return [...filtered].sort((a, b) => {
        const dir = state.sortDir === "asc" ? 1 : -1;
        const av = getSortValue(a, state.sortKey);
        const bv = getSortValue(b, state.sortKey);
        return av > bv ? dir : av < bv ? -dir : 0;
      });
    }

    function totalPages() {
      return Math.max(1, Math.ceil(sortedFilteredClients().length / state.pageSize));
    }

    function renderClientTableBody() {
      const sorted = sortedFilteredClients();
      agentCount.textContent = String(sorted.length);

      const total = totalPages();
      const pagination = document.querySelector(".pagination");
      if (pagination) {
        pagination.style.display = total > 1 ? "flex" : "none";
      }
      if (state.page > total) state.page = total;
      const start = (state.page - 1) * state.pageSize;
      const pageItems = sorted.slice(start, start + state.pageSize);
      const visibleColumns = getVisibleOrderedColumnKeys();

      let amber = 0;
      let red = 0;
      clientBody.innerHTML = "";
      pageItems.forEach(client => {
        const status = computeStatus(client);
        if (!client.disconnected) {
          if (status.cls === "late-amber") amber += 1;
          if (status.cls === "late-red") red += 1;
        }

        const tr = document.createElement("tr");
        if (status.cls === "late-amber") tr.classList.add("row-amber");
        if (status.cls === "late-red") tr.classList.add("row-red");
        if (status.cls === "disconnected") tr.classList.add("row-disconnected");
        if (hasPending(client)) tr.classList.add("pending-border");
        tr.addEventListener("click", () => openModal(client));
        tr.addEventListener("contextmenu", event => {
          event.preventDefault();
          contextClient = client;
          contextMenu.style.left = `${event.clientX}px`;
          contextMenu.style.top = `${event.clientY}px`;
          contextMenu.classList.add("open");
        });

        visibleColumns.forEach(columnKey => {
          tr.appendChild(renderCellForColumn(client, status, columnKey));
        });
        clientBody.appendChild(tr);
      });

      amberCount.textContent = amber;
      redCount.textContent = red;
      pageNum.textContent = state.page;
      pageTotal.textContent = total;
      pageJump.value = state.page;
    }

    function renderTable() {
      renderClientTableHeader();
      updateColumnsButtonState();
      renderClientTableBody();
    }

    function activeTabName() {
      const activeBtn = tabButtons.find(btn => btn.classList.contains("active"));
      return activeBtn?.dataset.tab || "summary";
    }

    function refreshOpenModal() {
      if (!activeClient || !modal.classList.contains("open")) return;
      const refreshed = state.clients.find(
        clientEntry => clientEntry.client_id === activeClient.client_id
      );
      if (!refreshed) {
        closeModal();
        return;
      }
      openModal(refreshed, captureOpenModalState());
    }

    function openModal(client, options = {}) {
      const preserveTab = options.preserveTab === true;
      const desiredTab = preserveTab ? activeTabName() : "summary";
      const customCommandState = options.customCommandState || null;
      const preserveHealthPanel = options.healthPanelOpen === true;
      const preserveClientDataPanel = options.clientDataOpen === true;
      activeClient = client;
      const status = computeStatus(client);
      modalCard.classList.remove("late-amber", "late-red", "row-disconnected");
      if (status.cls === "late-amber") modalCard.classList.add("late-amber");
      if (status.cls === "late-red") modalCard.classList.add("late-red");
      if (status.cls === "disconnected") modalCard.classList.add("row-disconnected");

      modalFields.innerHTML = "";
      componentHealthPanel.classList.add("hidden");
      componentHealthBody.innerHTML = "";
      clientDataPanel.classList.add("hidden");
      clientDataYaml.textContent = "";
      toggleDataBtn.classList.remove("hidden");
      toggleDataBtn.textContent = "View Data";
      const agentDesc = client.agent_description || "";
      const serviceName = extractAgentField(agentDesc, "service.name");
      const serviceInstanceId = extractAgentField(agentDesc, "service.instance.id");
      const hostType = extractAgentField(agentDesc, "os_type");
      const hostVersion = extractAgentField(agentDesc, "os_version");
      const hostName = extractAgentField(agentDesc, "hostname");
      const macAddress = extractAgentField(agentDesc, "mac_address");
      const reportedIpAddress =
        extractAgentField(agentDesc, "ip_address")
        || extractAgentField(agentDesc, "ip")
        || extractAgentField(agentDesc, "host.ip");
      const sourceIpAddress = client && client.remote_addr ? String(client.remote_addr) : "";
      const ipAddress = reportedIpAddress || sourceIpAddress;
      const nextExpected = computeNextExpected(client);
      const instanceUid = client.client_id ?? "--";
      const titleName = serviceInstanceId || "Client";
      modalTitle.textContent = `${titleName} (${instanceUid})`;
      const healthInfo = getClientHealthInfo(client);
      const hasDisplayValue = value => typeof value === "string" && value.trim() !== "";

      const fields = [];
      fields.push([
        "Connection Status",
        `<span class="status-dot modal-status ${status.cls}"><span class="dot"></span>${status.label}</span>`,
      ]);
      if (serviceName) {
        fields.push(["Service Name", serviceName, true]);
      }
      if (serviceInstanceId) {
        fields.push(["Service Instance ID", serviceInstanceId, true]);
      }
      fields.push(["Instance UID", instanceUid, true]);
      fields.push([
        "Health Status",
        healthInfo.hasComponents
          ? `<button type="button" class="data-toggle" title="click for more details" aria-label="click for more details"><span class="${healthInfo.textClass}">${healthInfo.summary}</span></button>`
          : `<span class="${healthInfo.textClass}">${healthInfo.summary}</span>`,
      ]);
      if (hostType) {
        fields.push(["Host Type", hostType]);
      }
      if (hostVersion) {
        fields.push(["Host Version", hostVersion]);
      }
      if (hostName) {
        fields.push(["Host Name", hostName]);
      }
      if (hasDisplayValue(macAddress)) {
        fields.push(["MAC Address", String(macAddress).trim()]);
      }
      if (hasDisplayValue(ipAddress)) {
        fields.push(["IP Address", String(ipAddress).trim()]);
      }
      fields.push(
        ["First Registered", client.first_seen ? new Date(client.first_seen).toLocaleString() : "--"],
        ["Last Communication", client.last_communication ? new Date(client.last_communication).toLocaleString() : "--"],
        ["Next Expected", nextExpected ? new Date(nextExpected).toLocaleString() : "--"],
        ["Requested Config", client.requested_config_version ?? "--"],
        [
          "Remote Config Files Allowed",
          client.remote_config_files_allowed === true ? "Yes" : "No",
        ],
        ["Client Version", client.client_version ?? "--"],
        ["Last Channel", client.last_channel ?? "--"],
        ["Capabilities", renderCapabilitiesList(client.capabilities)],
      );
      fields.forEach(([label, value, fullWidth]) => {
        const div = document.createElement("div");
        div.className = "field";
        if (fullWidth === true) {
          div.classList.add("full-width");
        }
        div.innerHTML = `<label>${label}</label><div>${value}</div>`;
        if (label === "Health Status" && healthInfo.hasComponents) {
          const btn = div.querySelector("button");
          if (btn) {
            btn.addEventListener("click", () => {
              const isHidden = componentHealthPanel.classList.contains("hidden");
              if (isHidden) {
                renderComponentHealthMap(healthInfo.componentMap);
                componentHealthPanel.classList.remove("hidden");
              } else {
                componentHealthPanel.classList.add("hidden");
              }
            });
          }
        }
        modalFields.appendChild(div);
      });

      configInput.value = formatConfigValue(client.requested_config) || "";
      updateRequestedConfigEditingState();
      currentConfigOutput.textContent = formatConfigValue(client.current_config) || "--";
      clearRemoteConfigStatus();
      renderRemoteConfigSelectionTable(client);
      if (preserveHealthPanel && healthInfo.hasComponents) {
        renderComponentHealthMap(healthInfo.componentMap);
        componentHealthPanel.classList.remove("hidden");
      }
      if (preserveClientDataPanel) {
        clientDataYaml.textContent = toYaml(normalizeClientData(activeClient));
        clientDataPanel.classList.remove("hidden");
        toggleDataBtn.classList.add("hidden");
      }
      renderEventsHistory(client);
      renderCommandButtons(client, customCommandState);
      fetchCustomCommands().then(() => {
        if (!activeClient || activeClient.client_id !== client.client_id) return;
        const preserved = captureCustomCommandState();
        renderCommandButtons(activeClient, preserved);
      });
      let nextTab = desiredTab;
      if (nextTab === "history" && historyTabBtn.classList.contains("hidden")) {
        nextTab = "summary";
      }
      setActiveTab(nextTab);
      modal.classList.add("open");
      requestAnimationFrame(captureModalCardMinSize);
    }

    function closeModal() {
      modal.classList.remove("open");
      activeClient = null;
      resetModalCardSize();
      configInput.value = "";
      updateRequestedConfigEditingState();
      currentConfigOutput.textContent = "";
      clearRemoteConfigStatus();
      if (remoteConfigSelectionBody) {
        remoteConfigSelectionBody.innerHTML = "";
      }
      if (remoteConfigSelectionTable) {
        remoteConfigSelectionTable.classList.add("hidden");
      }
      if (remoteConfigEmptyState) {
        remoteConfigEmptyState.classList.remove("hidden");
      }
      if (remoteConfigEnhancedPanel) {
        remoteConfigEnhancedPanel.classList.add("hidden");
      }
      eventsHistoryList.innerHTML = "";
      historyTabBtn.classList.add("hidden");
      componentHealthPanel.classList.add("hidden");
      componentHealthBody.innerHTML = "";
      toggleDataBtn.classList.remove("hidden");
      toggleDataBtn.textContent = "View Data";
    }

    function yamlScalar(value) {
      if (value === null || value === undefined) return "null";
      if (typeof value === "number" || typeof value === "boolean") return String(value);
      if (typeof value === "string") {
        if (value.includes("\n")) {
          return `|\n${value.split("\n").map(line => `  ${line}`).join("\n")}`;
        }
        const needsQuote = value === "" || /[:#\\[\\]{}&,*!?|>\\-]|^\\s|\\s$/.test(value);
        if (!needsQuote) return value;
        return `'${value.replace(/'/g, "''")}'`;
      }
      return String(value);
    }

    function toYaml(value, indent = 0) {
      const pad = " ".repeat(indent);
      if (Array.isArray(value)) {
        if (value.length === 0) return `${pad}[]`;
        return value
          .map(item => {
            if (item && typeof item === "object") {
              return `${pad}-\n${toYaml(item, indent + 2)}`;
            }
            return `${pad}- ${yamlScalar(item)}`;
          })
          .join("\n");
      }
      if (value && typeof value === "object") {
        const entries = Object.entries(value).sort(([a], [b]) => a.localeCompare(b));
        if (entries.length === 0) return `${pad}{}`;
        return entries
          .map(([key, val]) => {
            if (val && typeof val === "object") {
              return `${pad}${key}:\n${toYaml(val, indent + 2)}`;
            }
            const scalar = yamlScalar(val);
            if (typeof val === "string" && scalar.startsWith("|\n")) {
              return `${pad}${key}: ${scalar.replace(/\n/g, `\n${pad}  `)}`;
            }
            return `${pad}${key}: ${scalar}`;
          })
          .join("\n");
      }
      return `${pad}${yamlScalar(value)}`;
    }

    function normalizeClientData(client) {
      const clone = JSON.parse(JSON.stringify(client));
      const parseAgentDescription = (text) => {
        if (!text || typeof text !== "string") return text;
        const attrs = [];
        const patterns = [
          { type: "string", regex: /key: "([^"]+)"[\s\S]*?string_value: "([^"]*)"/g },
          { type: "bytes", regex: /key: "([^"]+)"[\s\S]*?bytes_value: "([^"]*)"/g },
          { type: "int", regex: /key: "([^"]+)"[\s\S]*?int_value: ([0-9-]+)/g },
          { type: "bool", regex: /key: "([^"]+)"[\s\S]*?bool_value: (true|false)/g },
          { type: "double", regex: /key: "([^"]+)"[\s\S]*?double_value: ([0-9eE+\\.-]+)/g },
        ];
        for (const pattern of patterns) {
          let match;
          while ((match = pattern.regex.exec(text)) !== null) {
            const key = match[1];
            let value = match[2];
            if (pattern.type === "int") value = parseInt(value, 10);
            if (pattern.type === "double") value = parseFloat(value);
            if (pattern.type === "bool") value = value === "true";
            attrs.push({ key, value, type: pattern.type });
          }
        }
        if (attrs.length === 0) return text;
        const map = {};
        attrs.forEach(item => {
          map[item.key] = item.value;
        });
        return { attributes: attrs, map };
      };
      const parseIfJson = (value) => {
        if (typeof value !== "string") return value;
        const trimmed = value.trim();
        if (!trimmed) return value;
        if (!(trimmed.startsWith("{") || trimmed.startsWith("["))) return value;
        try {
          return JSON.parse(trimmed);
        } catch {
          return value;
        }
      };
      clone.agent_description = parseAgentDescription(clone.agent_description);
      clone.current_config = parseIfJson(clone.current_config);
      clone.requested_config = parseIfJson(clone.requested_config);
      return clone;
    }

    function toggleClientData() {
      if (!activeClient) return;
      const hidden = clientDataPanel.classList.contains("hidden");
      if (hidden) {
        clientDataYaml.textContent = toYaml(normalizeClientData(activeClient));
        clientDataPanel.classList.remove("hidden");
        toggleDataBtn.classList.add("hidden");
      } else {
        clientDataPanel.classList.add("hidden");
        clientDataYaml.textContent = "";
        toggleDataBtn.classList.remove("hidden");
        toggleDataBtn.textContent = "View Data";
      }
    }

    function setActiveTab(tabName) {
      tabButtons.forEach(btn => {
        const isActive = btn.dataset.tab === tabName;
        btn.classList.toggle("active", isActive);
      });
      Object.entries(tabPanels).forEach(([key, panel]) => {
        panel.classList.toggle("active", key === tabName);
      });
    }

    function setActiveSettingsTab(tabName) {
      if (
        tabName === "server-opamp-config"
        && settingsTabServerOpampConfigBtn.classList.contains("hidden")
      ) {
        tabName = "server";
      }
      settingsTabButtons.forEach(btn => {
        const isActive = btn.dataset.settingsTab === tabName;
        btn.classList.toggle("active", isActive);
      });
      Object.entries(settingsTabPanels).forEach(([key, panel]) => {
        panel.classList.toggle("active", key === tabName);
      });
      hideHelpPopover();
      saveServerSettingsBtn.classList.toggle("hidden", tabName !== "server");
      saveGlobalSettingsBtn.classList.toggle("hidden", tabName === "server-opamp-config");
      if (tabName === "server-opamp-config") {
        void loadServerOpampConfigTab();
      } else if (tabName === "version") {
        void loadProviderVersionTab();
      }
    }

    async function loadProviderVersionTab() {
      // Load only the provider's display-safe version and registered plugin summary.
      if (!providerVersionText || !providerPluginsList) return;
      providerVersionText.textContent = "Loading version information…";
      providerPluginsList.textContent = "Loading plugin information…";
      try {
        const response = await apiFetch("/api/ui/version");
        if (!response.ok) throw new Error("Version request failed");
        const summary = await response.json();
        providerVersionText.textContent = String(summary.version || "Unknown");
        providerPluginsList.replaceChildren();
        const plugins = Array.isArray(summary.plugins) ? summary.plugins : [];
        plugins.forEach(plugin => {
          const row = document.createElement("div");
          row.className = "version-plugin-row";
          const heading = document.createElement("strong");
          heading.textContent = `${String(plugin.name || "Plugin")}: ${plugin.available === true ? "Available" : "Unavailable"}`;
          const description = document.createElement("span");
          description.textContent = String(plugin.description || "");
          row.append(heading, description);
          if (Array.isArray(plugin.commands) && plugin.commands.length > 0) {
            const commandList = document.createElement("ul");
            commandList.className = "version-command-list";
            plugin.commands.forEach(command => {
              const commandItem = document.createElement("li");
              commandItem.textContent = `${String(command.name || "Command")} — version ${String(command.version || summary.version || "Unknown")}`;
              commandList.appendChild(commandItem);
            });
            row.appendChild(commandList);
          }
          providerPluginsList.appendChild(row);
        });
      } catch (error) {
        providerVersionText.textContent = "Version information unavailable.";
        providerPluginsList.textContent = "Plugin information unavailable.";
      }
    }

    async function openGlobalSettingsModal() {
      await fetchSettings();
      await fetchClientSettings();
      await fetchDiagnosticSettings();
      delayedCommsSecondsInput.value = String(state.delayed);
      significantCommsSecondsInput.value = String(state.significant);
      clientEventHistorySizeInput.value = String(state.clientEventHistorySize);
      stateSaveFolderInput.value = String(state.stateSaveFolder || "runtime");
      retentionCountInput.value = String(state.retentionCount);
      autosaveIntervalInput.value = String(state.autosaveIntervalSecondsSinceChange);
      humanInLoopApprovalInput.checked = state.humanInLoopApproval === true;
      statePersistenceEnabledInput.checked = state.statePersistenceEnabled === true;
      renderAdvertisedCapabilities();
      renderHttpsCertificateExpiryRow();
      defaultHeartbeatFrequencyInput.value = String(state.defaultHeartbeatFrequency);
      settingsTabServerOpampConfigBtn.classList.toggle("hidden", !state.diagnosticEnabled);
      if (statePersistenceGroup) {
        statePersistenceGroup.classList.toggle(
          "hidden",
          state.statePersistenceEnabled !== true
        );
      }
      updateStatePersistenceUsageDisplay();
      if (saveStateNowBtn) {
        saveStateNowBtn.disabled = state.statePersistenceEnabled !== true;
      }
      if (state.statePersistenceEnabled === true) {
        setSaveStateNowStatus("No manual snapshot run yet.");
      } else {
        setSaveStateNowStatus(
          "State persistence is disabled in provider settings.",
          "error"
        );
      }
      setActiveSettingsTab("server");
      globalSettingsModal.classList.add("open");
    }

    function closeGlobalSettingsModal() {
      hideHelpPopover();
      globalSettingsModal.classList.remove("open");
    }

    function updateStatePersistenceUsageDisplay() {
      if (stateSnapshotFileCountOutput) {
        stateSnapshotFileCountOutput.textContent = (
          `current number of stored states is ${state.stateSnapshotFileCount}`
        );
      }
    }

    function setSaveStateNowStatus(message, tone = "") {
      if (!saveStateNowStatus) return;
      saveStateNowStatus.textContent = String(message || "");
      saveStateNowStatus.classList.remove("success", "error");
      if (tone === "success" || tone === "error") {
        saveStateNowStatus.classList.add(tone);
      }
    }

    function renderAdvertisedCapabilities() {
      if (!advertisedCapabilitiesBody) return;
      const capabilities = Array.isArray(state.advertisedCapabilities)
        ? state.advertisedCapabilities
        : [];
      advertisedCapabilitiesBody.innerHTML = "";
      if (capabilities.length === 0) {
        const emptyState = document.createElement("div");
        emptyState.className = "settings-inline-status";
        emptyState.textContent = "No advertised capability metadata is available.";
        advertisedCapabilitiesBody.appendChild(emptyState);
        return;
      }
      capabilities.forEach(capability => {
        const row = document.createElement("div");
        row.className = "settings-row settings-row-capability";

        const label = document.createElement("label");
        label.textContent = String(capability && capability.label ? capability.label : "--");
        row.appendChild(label);

        const switchLabel = document.createElement("label");
        switchLabel.className = "settings-switch settings-switch-disabled";
        switchLabel.setAttribute("aria-disabled", "true");

        const input = document.createElement("input");
        input.className = "settings-switch-input";
        input.type = "checkbox";
        input.disabled = true;
        input.checked = capability && capability.enabled === true;
        switchLabel.appendChild(input);

        const track = document.createElement("span");
        track.className = "settings-switch-track";
        track.setAttribute("aria-hidden", "true");
        switchLabel.appendChild(track);

        const stateLabel = document.createElement("span");
        stateLabel.className = "settings-switch-state";
        stateLabel.setAttribute("aria-hidden", "true");
        switchLabel.appendChild(stateLabel);
        row.appendChild(switchLabel);

        const status = document.createElement("span");
        status.className = "settings-inline-status";
        status.textContent = capability && capability.enabled === true
          ? "Advertised"
          : "Not advertised";
        row.appendChild(status);

        advertisedCapabilitiesBody.appendChild(row);
      });
    }

    async function saveStateNowFromSettings() {
      if (!saveStateNowBtn) return;
      saveStateNowBtn.disabled = true;
      const originalLabel = saveStateNowBtn.textContent;
      saveStateNowBtn.textContent = "Saving...";
      setSaveStateNowStatus("Saving snapshot...");
      try {
        const resp = await apiFetch("/api/settings/state/save", {
          method: "POST",
        });
        const payload = await resp.json().catch(() => ({}));
        if (!resp.ok) {
          const errorMessage = String(
            payload && payload.error
              ? payload.error
              : "Failed to save provider state snapshot."
          );
          setSaveStateNowStatus(errorMessage, "error");
          return;
        }
        const snapshotPath = String(payload.snapshot_path || "").trim();
        await fetchSettings();
        updateStatePersistenceUsageDisplay();
        if (snapshotPath) {
          const snapshotName = snapshotPath.split(/[\\/]/).pop() || snapshotPath;
          setSaveStateNowStatus(`Created: ${snapshotName}`, "success");
          return;
        }
        setSaveStateNowStatus("Snapshot saved.", "success");
      } catch (_error) {
        setSaveStateNowStatus(
          "Failed to save provider state snapshot.",
          "error"
        );
      } finally {
        saveStateNowBtn.disabled = false;
        saveStateNowBtn.textContent = originalLabel;
      }
    }

    function resetPendingApprovalDecisions() {
      pendingApprovalDecisions = {};
      state.pendingApprovals.forEach(client => {
        if (!client || !client.client_id) return;
        pendingApprovalDecisions[String(client.client_id)] = "block";
      });
    }

    function pendingApprovalDetails(client) {
      const agentDesc = client && client.agent_description ? String(client.agent_description) : "";
      const instanceId = extractAgentField(agentDesc, "service.instance.id") || "--";
      const serviceName = extractAgentField(agentDesc, "service.name") || "--";
      const hostType = extractAgentField(agentDesc, "os_type") || "--";
      const clientVersion = client && client.client_version ? String(client.client_version) : "--";
      const ipAddress = client && client.remote_addr ? String(client.remote_addr) : "--";
      return {
        uid: client && client.client_id ? String(client.client_id) : "--",
        instanceId,
        ipAddress,
        agentTypeVersion: `${serviceName} / ${clientVersion}`,
        hostType,
      };
    }

    function renderPendingApprovalTable() {
      if (!Array.isArray(state.pendingApprovals) || state.pendingApprovals.length === 0) {
        pendingApprovalBody.innerHTML = '<tr><td colspan="6" class="approval-empty">No pending approvals.</td></tr>';
        return;
      }
      pendingApprovalBody.innerHTML = "";
      state.pendingApprovals.forEach((client, index) => {
        if (!client || !client.client_id) return;
        const details = pendingApprovalDetails(client);
        const decisionValue = pendingApprovalDecisions[details.uid] || "block";
        const rowToggleId = `pending-approval-${index}-${details.uid.replace(/[^A-Za-z0-9_-]/g, "_")}`;
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${details.uid}</td>
          <td>${details.instanceId}</td>
          <td>${details.ipAddress}</td>
          <td>${details.agentTypeVersion}</td>
          <td>${details.hostType}</td>
          <td>
            <label class="approval-toggle" for="${rowToggleId}">
              <input
                id="${rowToggleId}"
                type="checkbox"
                class="approval-toggle-input"
                data-pending-client-id="${details.uid}"
                aria-label="Pending approval decision for ${details.uid}"
              />
              <span class="approval-toggle-track" aria-hidden="true"></span>
              <span class="approval-toggle-state"></span>
            </label>
          </td>
        `;
        const toggle = row.querySelector("input[data-pending-client-id]");
        const stateLabel = row.querySelector(".approval-toggle-state");
        const applyDecision = decision => {
          const normalized = String(decision || "").toLowerCase() === "approve" ? "approve" : "block";
          pendingApprovalDecisions[details.uid] = normalized;
          if (toggle) {
            toggle.checked = normalized === "approve";
          }
          if (stateLabel) {
            stateLabel.textContent = normalized === "approve" ? "Accept" : "Block";
          }
        };
        if (toggle) {
          applyDecision(decisionValue);
          toggle.addEventListener("change", () => {
            applyDecision(toggle.checked ? "approve" : "block");
          });
        }
        pendingApprovalBody.appendChild(row);
      });
    }

    function setAllPendingApprovals(decision) {
      const normalized = String(decision || "").toLowerCase() === "approve" ? "approve" : "block";
      state.pendingApprovals.forEach(client => {
        if (!client || !client.client_id) return;
        pendingApprovalDecisions[String(client.client_id)] = normalized;
      });
      pendingApprovalBody.querySelectorAll("input[data-pending-client-id]").forEach(toggle => {
        toggle.checked = normalized === "approve";
        toggle.dispatchEvent(new Event("change"));
      });
    }

    async function openPendingApprovalModal() {
      if (state.humanInLoopApproval !== true) {
        return;
      }
      await fetchPendingApprovals();
      resetPendingApprovalDecisions();
      renderPendingApprovalTable();
      pendingApprovalModal.classList.add("open");
    }

    function closePendingApprovalModal() {
      pendingApprovalModal.classList.remove("open");
    }

    async function savePendingApprovalDecisions() {
      if (!Array.isArray(state.pendingApprovals) || state.pendingApprovals.length === 0) {
        closePendingApprovalModal();
        return;
      }
      const decisions = state.pendingApprovals
        .filter(client => client && client.client_id)
        .map(client => ({
          client_id: String(client.client_id),
          decision: pendingApprovalDecisions[String(client.client_id)] === "approve"
            ? "approve"
            : "block",
        }));
      const resp = await apiFetch("/api/approvals/pending", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decisions }),
      });
      if (!resp.ok) {
        window.alert("Failed to apply pending approval decisions.");
        return;
      }
      closePendingApprovalModal();
      await fetchPendingApprovals();
      await fetchClients();
    }

    async function saveGlobalSettings() {
      const proposedDelayed = parseInt(delayedCommsSecondsInput.value, 10);
      const proposedSignificant = parseInt(significantCommsSecondsInput.value, 10);
      const proposedClientEventHistorySize = parseInt(
        clientEventHistorySizeInput.value,
        10
      );
      const proposedStateSaveFolder = String(stateSaveFolderInput.value || "").trim();
      const proposedRetentionCount = parseInt(retentionCountInput.value, 10);
      const proposedAutosaveInterval = parseInt(autosaveIntervalInput.value, 10);
      const proposedHumanInLoopApproval = humanInLoopApprovalInput.checked === true;
      const proposedValue = parseInt(defaultHeartbeatFrequencyInput.value, 10);
      if (Number.isNaN(proposedDelayed) || proposedDelayed <= 0) {
        window.alert("delayed_comms_seconds must be a positive integer.");
        return;
      }
      if (Number.isNaN(proposedSignificant) || proposedSignificant <= 0) {
        window.alert("significant_comms_seconds must be a positive integer.");
        return;
      }
      if (proposedDelayed >= proposedSignificant) {
        window.alert("significant_comms_seconds must be greater than delayed_comms_seconds.");
        return;
      }
      if (
        Number.isNaN(proposedClientEventHistorySize)
        || proposedClientEventHistorySize <= 0
      ) {
        window.alert("client_event_history_size must be a positive integer.");
        return;
      }
      if (!proposedStateSaveFolder) {
        window.alert("state_save_folder must be provided.");
        return;
      }
      if (Number.isNaN(proposedRetentionCount) || proposedRetentionCount <= 0) {
        window.alert("retention_count must be a positive integer.");
        return;
      }
      if (Number.isNaN(proposedAutosaveInterval) || proposedAutosaveInterval <= 0) {
        window.alert("autosave_interval_seconds_since_change must be a positive integer.");
        return;
      }
      if (Number.isNaN(proposedValue) || proposedValue <= 0) {
        window.alert("Default Heartbeat Frequency must be a positive integer.");
        return;
      }
      if (
        proposedDelayed !== state.delayed
        || proposedSignificant !== state.significant
        || proposedClientEventHistorySize !== state.clientEventHistorySize
        || proposedStateSaveFolder !== state.stateSaveFolder
        || proposedRetentionCount !== state.retentionCount
        || proposedAutosaveInterval !== state.autosaveIntervalSecondsSinceChange
        || proposedHumanInLoopApproval !== state.humanInLoopApproval
      ) {
        const commsResp = await apiFetch("/api/settings/comms", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            delayed_comms_seconds: proposedDelayed,
            significant_comms_seconds: proposedSignificant,
            client_event_history_size: proposedClientEventHistorySize,
            human_in_loop_approval: proposedHumanInLoopApproval,
            state_save_folder: proposedStateSaveFolder,
            retention_count: proposedRetentionCount,
            autosave_interval_seconds_since_change: proposedAutosaveInterval,
          }),
        });
        if (!commsResp.ok) {
          window.alert("Failed to update server communication settings.");
          return;
        }
        const commsPayload = await commsResp.json();
        state.delayed = parseInt(commsPayload.delayed_comms_seconds, 10);
        state.significant = parseInt(commsPayload.significant_comms_seconds, 10);
        state.clientEventHistorySize = parseInt(commsPayload.client_event_history_size, 10);
        state.stateSaveFolder = String(commsPayload.state_save_folder || proposedStateSaveFolder);
        const updatedRetentionCount = parseInt(commsPayload.retention_count, 10);
        state.retentionCount = Number.isNaN(updatedRetentionCount) || updatedRetentionCount <= 0
          ? proposedRetentionCount
          : updatedRetentionCount;
        const updatedSnapshotCount = parseInt(
          commsPayload.state_snapshot_file_count,
          10
        );
        state.stateSnapshotFileCount = Number.isNaN(updatedSnapshotCount)
          || updatedSnapshotCount < 0
          ? state.stateSnapshotFileCount
          : updatedSnapshotCount;
        state.autosaveIntervalSecondsSinceChange = parseInt(
          commsPayload.autosave_interval_seconds_since_change,
          10
        );
        state.humanInLoopApproval = commsPayload.human_in_loop_approval === true;
        updatePendingApprovalVisibility();
      }
      if (proposedValue !== state.defaultHeartbeatFrequency) {
        const resp = await apiFetch("/api/settings/client", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ default_heartbeat_frequency: proposedValue }),
        });
        if (!resp.ok) {
          window.alert("Failed to update global client settings.");
          return;
        }
        const payload = await resp.json();
        const updatedFrequency = parseInt(payload.default_heartbeat_frequency, 10);
        if (!Number.isNaN(updatedFrequency) && updatedFrequency > 0) {
          state.defaultHeartbeatFrequency = updatedFrequency;
        }
      }
      closeGlobalSettingsModal();
      await fetchClients();
    }

    async function saveServerSettings() {
      const proposedDelayed = parseInt(delayedCommsSecondsInput.value, 10);
      const proposedSignificant = parseInt(significantCommsSecondsInput.value, 10);
      const proposedClientEventHistorySize = parseInt(
        clientEventHistorySizeInput.value,
        10
      );
      const proposedStateSaveFolder = String(stateSaveFolderInput.value || "").trim();
      const proposedRetentionCount = parseInt(retentionCountInput.value, 10);
      const proposedAutosaveInterval = parseInt(autosaveIntervalInput.value, 10);
      const proposedHumanInLoopApproval = humanInLoopApprovalInput.checked === true;
      if (Number.isNaN(proposedDelayed) || proposedDelayed <= 0) {
        window.alert("delayed_comms_seconds must be a positive integer.");
        return;
      }
      if (Number.isNaN(proposedSignificant) || proposedSignificant <= 0) {
        window.alert("significant_comms_seconds must be a positive integer.");
        return;
      }
      if (proposedDelayed >= proposedSignificant) {
        window.alert("significant_comms_seconds must be greater than delayed_comms_seconds.");
        return;
      }
      if (
        Number.isNaN(proposedClientEventHistorySize)
        || proposedClientEventHistorySize <= 0
      ) {
        window.alert("client_event_history_size must be a positive integer.");
        return;
      }
      if (!proposedStateSaveFolder) {
        window.alert("state_save_folder must be provided.");
        return;
      }
      if (Number.isNaN(proposedRetentionCount) || proposedRetentionCount <= 0) {
        window.alert("retention_count must be a positive integer.");
        return;
      }
      if (Number.isNaN(proposedAutosaveInterval) || proposedAutosaveInterval <= 0) {
        window.alert("autosave_interval_seconds_since_change must be a positive integer.");
        return;
      }

      const commsResp = await apiFetch("/api/settings/comms", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          delayed_comms_seconds: proposedDelayed,
          significant_comms_seconds: proposedSignificant,
          client_event_history_size: proposedClientEventHistorySize,
          human_in_loop_approval: proposedHumanInLoopApproval,
          state_save_folder: proposedStateSaveFolder,
          retention_count: proposedRetentionCount,
          autosave_interval_seconds_since_change: proposedAutosaveInterval,
        }),
      });
      if (!commsResp.ok) {
        window.alert("Failed to update server communication settings.");
        return;
      }
      const commsPayload = await commsResp.json();
      state.delayed = parseInt(commsPayload.delayed_comms_seconds, 10);
      state.significant = parseInt(commsPayload.significant_comms_seconds, 10);
      state.clientEventHistorySize = parseInt(commsPayload.client_event_history_size, 10);
      state.stateSaveFolder = String(commsPayload.state_save_folder || proposedStateSaveFolder);
      const updatedRetentionCount = parseInt(commsPayload.retention_count, 10);
      state.retentionCount = Number.isNaN(updatedRetentionCount) || updatedRetentionCount <= 0
        ? proposedRetentionCount
        : updatedRetentionCount;
      const updatedSnapshotCount = parseInt(
        commsPayload.state_snapshot_file_count,
        10
      );
      state.stateSnapshotFileCount = Number.isNaN(updatedSnapshotCount)
        || updatedSnapshotCount < 0
        ? state.stateSnapshotFileCount
        : updatedSnapshotCount;
      state.autosaveIntervalSecondsSinceChange = parseInt(
        commsPayload.autosave_interval_seconds_since_change,
        10
      );
      state.humanInLoopApproval = commsPayload.human_in_loop_approval === true;
      updatePendingApprovalVisibility();

      closeGlobalSettingsModal();
      await fetchClients();
    }

    function formatConfigValue(value) {
      if (value === null || value === undefined) return "";
      if (typeof value === "string") return value;
      if (typeof value === "object") {
        try {
          return JSON.stringify(value, null, 2);
        } catch (err) {
          return String(value);
        }
      }
      return String(value);
    }

    function renderCommandButtons(client, customCommandState = null) {
      commandButtons.innerHTML = "";
      COMMAND_OPTIONS.forEach(option => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "command-btn";
        btn.innerHTML = `<span>${option.label}</span><small>${option.description}</small>`;
        btn.addEventListener("click", () => queueCommand(option.value, client));
        commandButtons.appendChild(btn);
      });
      clientHeartbeatFrequencyInput.value = String(client.heartbeat_frequency ?? 30);
      renderCustomCommandSelect(customCommandState);
    }

    function renderCustomCommandSelect(customCommandState = null) {
      customCommandSelect.innerHTML = "";
      const defaultOption = document.createElement("option");
      defaultOption.value = "";
      defaultOption.textContent = "Select custom command...";
      customCommandSelect.appendChild(defaultOption);

      state.customCommands.forEach(command => {
        const option = document.createElement("option");
        option.value = command.fqdn || "";
        option.textContent = command.displayname || command.operation || command.fqdn || "--";
        if (command.reported_by_client === true) {
          option.style.color = "var(--ok)";
          option.style.fontWeight = "600";
        }
        customCommandSelect.appendChild(option);
      });

      const restoreFqdn =
        customCommandState
        && typeof customCommandState.selectedFqdn === "string"
        && state.customCommands.some(cmd => cmd.fqdn === customCommandState.selectedFqdn)
          ? customCommandState.selectedFqdn
          : "";
      customCommandSelect.value = restoreFqdn;
      updateCustomCommandSelectStyle();
      renderCustomCommandConfiguration(
        restoreFqdn,
        customCommandState ? customCommandState.values : null,
      );
    }

    function updateCustomCommandSelectStyle() {
      const selectedMeta = getSelectedCustomCommandMeta(customCommandSelect.value);
      if (selectedMeta && selectedMeta.reported_by_client === true) {
        customCommandSelect.style.color = "var(--ok)";
        customCommandSelect.style.fontWeight = "600";
        return;
      }
      customCommandSelect.style.color = "";
      customCommandSelect.style.fontWeight = "";
    }

    function getSelectedCustomCommandMeta(selectedFqdn) {
      return state.customCommands.find(cmd => cmd.fqdn === selectedFqdn) || null;
    }

    function toSchemaTooltip(schemaEntry, currentValue) {
      const description = String(schemaEntry.description ?? "").trim();
      return description || "No description provided.";
    }

    function isSchemaRequired(schemaEntry) {
      return schemaEntry.isRequired === true || schemaEntry.isrequired === true;
    }

    function hasMissingRequiredCustomCommandValues(selectedMeta) {
      if (!selectedMeta) return true;
      const schema = Array.isArray(selectedMeta.schema) ? selectedMeta.schema : [];
      for (const schemaEntry of schema) {
        const paramName = String(schemaEntry.parametername || "").trim();
        if (!paramName || !isSchemaRequired(schemaEntry)) continue;
        const input = Array.from(customCommandConfigBody.querySelectorAll("input")).find(
          item => item.dataset.parameter === paramName
        );
        const value = input ? String(input.value || "").trim() : "";
        if (!value) return true;
      }
      return false;
    }

    function updateCustomCommandActionAvailability() {
      const selectedMeta = getSelectedCustomCommandMeta(customCommandSelect.value);
      const canIssue = Boolean(selectedMeta) && !hasMissingRequiredCustomCommandValues(selectedMeta);
      sendCustomCommandBtn.disabled = !canIssue;
      sendCustomCommandBtn.title = canIssue
        ? "Configure and queue this command"
        : "Populate all required parameters before issuing this command";
    }

    function buildConfigValueCell(paramName, selectedMeta, overrideValue = null) {
      const input = document.createElement("input");
      input.type = "text";
      input.dataset.parameter = paramName;
      input.style.width = "100%";
      if (typeof overrideValue === "string") {
        input.value = overrideValue;
      } else {
        input.value = "";
      }
      return input;
    }

    function renderCustomCommandConfiguration(selectedFqdn, valueOverrides = null) {
      customCommandConfigBody.innerHTML = "";
      const selectedMeta = getSelectedCustomCommandMeta(selectedFqdn);
      if (!selectedMeta) {
        customCommandConfigPanel.classList.add("hidden");
        updateCustomCommandActionAvailability();
        return;
      }
      customCommandConfigPanel.classList.remove("hidden");
      const schema = Array.isArray(selectedMeta.schema) ? selectedMeta.schema : [];
      schema.forEach(schemaEntry => {
        const paramName = String(schemaEntry.parametername || "").trim();
        if (!paramName) return;
        const row = document.createElement("tr");

        const labelCell = document.createElement("td");
        const label = document.createElement("label");
        label.textContent = paramName;
        labelCell.appendChild(label);

        const valueCell = document.createElement("td");
        const overrideValue =
          valueOverrides && Object.prototype.hasOwnProperty.call(valueOverrides, paramName)
            ? String(valueOverrides[paramName] ?? "")
            : null;
        const input = buildConfigValueCell(paramName, selectedMeta, overrideValue);
        valueCell.appendChild(input);

        const infoCell = document.createElement("td");
        const info = document.createElement("span");
        info.className = "schema-icon";
        info.textContent = "i";
        info.title = toSchemaTooltip(schemaEntry, input.value);
        input.addEventListener("input", () => {
          info.title = toSchemaTooltip(schemaEntry, input.value);
          updateCustomCommandActionAvailability();
        });
        infoCell.appendChild(info);

        row.appendChild(labelCell);
        row.appendChild(valueCell);
        row.appendChild(infoCell);
        customCommandConfigBody.appendChild(row);
      });
      updateCustomCommandActionAvailability();
    }

    function captureCustomCommandState() {
      const selectedFqdn = customCommandSelect.value || "";
      const values = {};
      Array.from(customCommandConfigBody.querySelectorAll("input")).forEach(input => {
        const paramName = input.dataset.parameter;
        if (!paramName) return;
        values[paramName] = String(input.value || "");
      });
      return { selectedFqdn, values };
    }

    function captureOpenModalState() {
      return {
        preserveTab: true,
        customCommandState: captureCustomCommandState(),
        healthPanelOpen: !componentHealthPanel.classList.contains("hidden"),
        clientDataOpen: !clientDataPanel.classList.contains("hidden"),
      };
    }

    function renderEventsHistory(client) {
      const events = Array.isArray(client.events) ? client.events : [];
      const flattened = [];
      events.forEach(eventObj => {
        if (!eventObj || typeof eventObj !== "object") return;
        if ("event_time" in eventObj || "event_description" in eventObj) {
          const eventTime = String(eventObj.event_time || "");
          const direction = String(eventObj.event_direction || "sent").trim().toLowerCase();
          const eventLines = Array.isArray(eventObj.event_lines)
            ? eventObj.event_lines
                .map(line => String(line || "").trim())
                .filter(Boolean)
            : [];
          let description = eventLines.join("\n");
          if (!description) {
            description = String(eventObj.event_description || "").trim();
          }
          if (!description && ("classifier" in eventObj || "action" in eventObj)) {
            const classifier = String(eventObj.classifier || "command").trim();
            const action = String(eventObj.action || eventObj.command || "unknown").trim();
            description = `${classifier} ${action}`.trim();
          }
          flattened.push({
            eventTime,
            direction: direction === "received" ? "received" : "sent",
            description: description || "--",
            ts: new Date(eventTime).getTime(),
          });
          return;
        }
        Object.entries(eventObj).forEach(([eventTime, description]) => {
          flattened.push({
            eventTime,
            direction: "sent",
            description: String(description),
            ts: new Date(eventTime).getTime(),
          });
        });
      });

      if (flattened.length === 0) {
        eventsHistoryList.innerHTML = `
          <tr>
            <td>--</td>
            <td>--</td>
            <td>No event history yet.</td>
          </tr>
        `;
        historyTabBtn.classList.add("hidden");
        if (tabPanels.history.classList.contains("active")) {
          setActiveTab("summary");
        }
        return;
      }

      flattened.sort((a, b) => {
        const aTs = Number.isNaN(a.ts) ? 0 : a.ts;
        const bTs = Number.isNaN(b.ts) ? 0 : b.ts;
        return state.eventsSortDir === "asc" ? aTs - bTs : bTs - aTs;
      });

      eventsHistoryList.innerHTML = "";
      flattened.forEach(event => {
        const row = document.createElement("tr");
        const when = Number.isNaN(event.ts)
          ? event.eventTime
          : new Date(event.eventTime).toLocaleString();
        const arrow = event.direction === "received" ? "→" : "←";
        const whenCell = document.createElement("td");
        whenCell.textContent = when;
        const directionCell = document.createElement("td");
        directionCell.className = `history-direction-cell history-direction-${event.direction}`;
        directionCell.textContent = arrow;
        directionCell.title = event.direction === "received" ? "Received from client" : "Sent to client";
        const descriptionCell = document.createElement("td");
        descriptionCell.className = "history-description-cell";
        descriptionCell.textContent = event.description;
        row.appendChild(whenCell);
        row.appendChild(directionCell);
        row.appendChild(descriptionCell);
        eventsHistoryList.appendChild(row);
      });
      historyTabBtn.classList.remove("hidden");
    }

    async function queueCommand(command, client) {
      const target = client || activeClient;
      if (!target) return;
      if (command === "issue_unique_id") {
        const preservedCustomCommandState = captureCustomCommandState();
        await requestNewUniqueId(target, {
          preserveTab: true,
          customCommandState: preservedCustomCommandState,
          reopenModal: true,
          closeContextMenu: false,
        });
        return;
      }
      const ok = window.confirm(`Queue command "${command}" for client ${target.client_id}?`);
      if (!ok) return;
      const resp = await apiFetch(`/api/clients/${target.client_id}/commands`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pairs: [
            { key: "classifier", value: "command" },
            { key: "action", value: command },
            { key: "source", value: "ui" },
            { key: "requested_at", value: new Date().toISOString() },
          ],
        }),
      });
      if (!resp.ok) {
        window.alert("Failed to queue command.");
        return;
      }
      await fetchClients();
      const refreshed = state.clients.find(
        clientEntry => clientEntry.client_id === target.client_id
      );
      if (refreshed) {
        if (
          activeClient
          && modal.classList.contains("open")
          && activeClient.client_id === target.client_id
        ) {
          openModal(refreshed, captureOpenModalState());
        } else {
          openModal(refreshed);
        }
      }
    }

    async function queueCustomCommand() {
      const target = activeClient;
      if (!target) return;
      const preservedCustomCommandState = captureCustomCommandState();
      const selectedFqdn = customCommandSelect.value;
      const selectedMeta = getSelectedCustomCommandMeta(selectedFqdn);
      if (!selectedMeta) {
        window.alert("Please select a custom command.");
        return;
      }
      if (hasMissingRequiredCustomCommandValues(selectedMeta)) {
        window.alert("Populate all required parameters before issuing this command.");
        updateCustomCommandActionAvailability();
        return;
      }

      const pairs = [];
      const schema = Array.isArray(selectedMeta.schema) ? selectedMeta.schema : [];
      let missingRequired = null;
      const configuredValues = preservedCustomCommandState.values || {};
      schema.forEach(schemaEntry => {
        const paramName = String(schemaEntry.parametername || "").trim();
        if (!paramName) return;
        const value = String(configuredValues[paramName] || "").trim();
        if (isSchemaRequired(schemaEntry) && !value && !missingRequired) {
          missingRequired = paramName;
        }
      });
      Object.entries(configuredValues).forEach(([key, rawValue]) => {
        const paramName = String(key || "").trim();
        const value = String(rawValue || "").trim();
        if (!paramName || !value) return;
        pairs.push({ key: paramName, value });
      });
      if (missingRequired) {
        window.alert(`Missing required parameter: ${missingRequired}`);
        return;
      }

      pairs.push({ key: "classifier", value: "custom" });
      pairs.push({ key: "operation", value: selectedMeta.operation || "" });
      pairs.push({ key: "capability", value: selectedMeta.fqdn || "" });

      pairs.push({ key: "source", value: "ui" });
      pairs.push({ key: "requested_at", value: new Date().toISOString() });

      const ok = window.confirm(
        `Queue custom command "${selectedMeta.displayname}" for client ${target.client_id}?`
      );
      if (!ok) return;

      const resp = await apiFetch(`/api/clients/${target.client_id}/commands`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pairs }),
      });
      if (!resp.ok) {
        window.alert("Failed to queue custom command.");
        return;
      }
      await fetchClients();
      const refreshed = state.clients.find(
        clientEntry => clientEntry.client_id === target.client_id
      );
      if (refreshed) {
        openModal(refreshed, {
          ...captureOpenModalState(),
          customCommandState: preservedCustomCommandState,
        });
      }
    }

    async function saveClientHeartbeat() {
      const target = activeClient;
      if (!target) return;
      const preservedCustomCommandState = captureCustomCommandState();
      const proposedValue = parseInt(clientHeartbeatFrequencyInput.value, 10);
      if (Number.isNaN(proposedValue) || proposedValue <= 0) {
        window.alert("Client heartbeat frequency must be a positive integer.");
        return;
      }
      const resp = await apiFetch(`/api/clients/${target.client_id}/heartbeat-frequency`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ heartbeat_frequency: proposedValue }),
      });
      if (!resp.ok) {
        window.alert("Failed to update client heartbeat frequency.");
        return;
      }
      await fetchClients();
      const refreshed = state.clients.find(
        clientEntry => clientEntry.client_id === target.client_id
      );
      if (refreshed) {
        openModal(refreshed, {
          ...captureOpenModalState(),
          customCommandState: preservedCustomCommandState,
        });
      }
    }

    async function saveConfig() {
      if (!activeClient) return;
      if (state.configServiceFeatureAvailable === true) return;
      const configValue = configInput.value.trim();
      if (!configValue) {
        closeModal();
        return;
      }
      if (configValue) {
        await apiFetch(`/api/clients/${activeClient.client_id}/config`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ config: configValue }),
        });
      }
      closeModal();
      await fetchClients();
    }

    function extractAgentField(text, key) {
      if (!text) return "";
      const stringRegex = new RegExp(`key: \\"${key}\\"[\\s\\S]*?string_value: \\"([^\\"]*)\\"`);
      const stringMatch = text.match(stringRegex);
      if (stringMatch) return stringMatch[1];
      const bytesRegex = new RegExp(`key: \\"${key}\\"[\\s\\S]*?bytes_value: \\"([^\\"]*)\\"`);
      const bytesMatch = text.match(bytesRegex);
      if (bytesMatch) return bytesMatch[1];
      return "";
    }

    function getClientDisplayId(client) {
      const agentDesc = client && client.agent_description ? String(client.agent_description) : "";
      const serviceInstanceId = extractAgentField(agentDesc, "service.instance.id");
      if (serviceInstanceId) return serviceInstanceId;
      return client && client.client_id ? String(client.client_id) : "--";
    }

    function getClientHealthInfo(client) {
      const health = client && typeof client.health === "object" ? client.health : null;
      const healthyRaw = String((health && health.healthy) ?? "");
      let healthyLabel = "unknown";
      if (healthyRaw === "1" || healthyRaw.toLowerCase() === "true") healthyLabel = "healthy";
      if (healthyRaw === "0" || healthyRaw.toLowerCase() === "false") healthyLabel = "unhealthy";
      const summary = healthyLabel;
      const componentMap =
        client && typeof client.component_health === "object" && client.component_health
          ? client.component_health
          : health && typeof health.component_health_map === "object" && health.component_health_map
            ? health.component_health_map
            : {};
      return {
        summary,
        textClass: `health-text-${healthyLabel}`,
        componentMap,
        hasComponents: Object.keys(componentMap).length > 0,
      };
    }

    function renderComponentHealthMap(componentMap) {
      componentHealthBody.innerHTML = "";
      Object.entries(componentMap).forEach(([name, value]) => {
        const row = document.createElement("tr");
        const healthyRaw = String((value && value.healthy) ?? "");
        const healthy =
          healthyRaw === "1" || healthyRaw.toLowerCase() === "true" ? "yes"
          : healthyRaw === "0" || healthyRaw.toLowerCase() === "false" ? "no"
          : "--";
        const status = value && value.status ? String(value.status) : "--";
        const lastError = value && value.last_error ? String(value.last_error) : "--";
        if (healthy === "yes") {
          row.classList.add("health-row-ok");
        } else if (healthy === "no") {
          row.classList.add("health-row-bad");
        } else {
          row.classList.add("health-row-unknown");
        }
        row.innerHTML = `
          <td>${name}</td>
          <td>${healthy}</td>
          <td>${status}</td>
          <td>${lastError}</td>
        `;
        componentHealthBody.appendChild(row);
      });
    }

    function renderCapabilitiesList(capabilities) {
      if (!capabilities || capabilities.length === 0) return "--";
      return `<div class="cap-list">${capabilities
        .map(cap => `<span class="cap-pill">${cap}</span>`)
        .join("")}</div>`;
    }

    function computeNextExpected(client) {
      if (!client.last_communication) return null;
      const last = new Date(client.last_communication);
      if (Number.isNaN(last.getTime())) return null;
      const intervalSeconds = client.heartbeat_frequency ?? state.refreshSeconds;
      return new Date(last.getTime() + intervalSeconds * 1000).toISOString();
    }

    function hideContextMenu() {
      contextMenu.classList.remove("open");
      contextClient = null;
    }

    async function removeClient() {
      if (!contextClient) return;
      const ok = window.confirm(`Remove client ${contextClient.client_id} from the server?`);
      if (!ok) return;
      const resp = await apiFetch(`/api/clients/${contextClient.client_id}`, { method: "DELETE" });
      hideContextMenu();
      if (!resp.ok) {
        window.alert("Failed to remove client.");
        return;
      }
      await fetchClients();
    }

    async function requestNewUniqueId(target, options = {}) {
      if (!target) return;
      const ok = window.confirm(
        `Issue a new unique ID for client ${target.client_id}?`
      );
      if (!ok) return;
      const resp = await apiFetch(`/api/clients/${target.client_id}/identify`, {
        method: "POST",
      });
      if (options.closeContextMenu !== false) {
        hideContextMenu();
      }
      if (!resp.ok) {
        window.alert("Failed to issue new unique ID.");
        return;
      }
      await fetchClients();
      if (options.reopenModal !== true) return;
      const refreshed = state.clients.find(
        clientEntry => clientEntry.client_id === target.client_id
      );
      if (!refreshed) return;
      if (options.preserveTab === true) {
        openModal(refreshed, {
          ...captureOpenModalState(),
          customCommandState: options.customCommandState || null,
        });
        return;
      }
      openModal(refreshed);
    }

    async function issueNewId(event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      if (!contextClient) return;
      const target = contextClient;
      await requestNewUniqueId(target, {
        closeContextMenu: true,
        reopenModal: false,
      });
    }

    function scheduleRefresh() {
      if (state.timer) clearInterval(state.timer);
      state.timer = setInterval(fetchClients, state.refreshSeconds * 1000);
    }

    function loadStoredAuthToken() {
      try {
        return String(window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY) || "").trim();
      } catch (_error) {
        return "";
      }
    }

    function updateAuthTokenStatus() {
      authTokenStatus.textContent = state.authToken ? "Token: set" : "Token: not set";
    }

    function setAuthToken(token) {
      state.authToken = String(token || "").trim();
      try {
        if (state.authToken) {
          window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, state.authToken);
        } else {
          window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
        }
      } catch (_error) {
        // Ignore localStorage failures and continue with in-memory token use.
      }
      updateAuthTokenStatus();
    }

    function initializeAuthToken() {
      const storedToken = loadStoredAuthToken();
      state.authToken = storedToken;
      authTokenInput.value = storedToken;
      updateAuthTokenStatus();
    }

    async function apiFetch(resource, options = {}) {
      const fetchOptions = { ...options };
      const headers = {
        ...(options.headers || {}),
      };
      if (state.authToken) {
        headers.Authorization = `Bearer ${state.authToken}`;
      }
      fetchOptions.headers = headers;
      return fetch(resource, fetchOptions);
    }

    async function init() {
      initializeAuthToken();
      loadUiPreferencesFromCookie();
      state.columnFilters = normalizeColumnFilters(state.columnFilters);
      writeColumnControlsToInputs();
      renderClientTableHeader();
      await fetchUiFeatureMenu();
      await fetchGlobalSettingsHelp();
      await fetchSettings();
      await fetchClientSettings();
      await fetchCustomCommands();
      await fetchPendingApprovals();
      await fetchClients();
      scheduleRefresh();
    }

    // Export function handles via a factory so provider UI can bootstrap through
    // the same module/factory framework style used by config-service.
    window.ProviderUiFunctions = {
      create: function createProviderUiFunctions(_deps) {
        return {
          init,
          renderTable,
          totalPages,
          scheduleRefresh,
          toggleColumnsPanel,
          applyOptionalColumnSelection,
          updateStatePersistenceUsageDisplay,
          setAuthToken,
          setActiveTab,
          setActiveSettingsTab,
          saveConfig,
          sendRemoteConfigFiles,
          renderCustomCommandConfiguration,
          updateCustomCommandSelectStyle,
          queueCustomCommand,
          saveClientHeartbeat,
          renderEventsHistory,
          openGlobalSettingsModal,
          openPendingApprovalModal,
          closeGlobalSettingsModal,
          saveGlobalSettings,
          saveServerSettings,
          saveStateNowFromSettings,
          closePendingApprovalModal,
          savePendingApprovalDecisions,
          setAllPendingApprovals,
          hideHelpPopover,
          closeModal,
          handleCatalogSelectionMessage,
          openRemoteConfigCatalogPopup,
          toggleClientData,
          removeClient,
          issueNewId,
        };
      },
    };
