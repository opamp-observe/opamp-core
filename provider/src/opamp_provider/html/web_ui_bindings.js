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

  function bindUi() {
    document.getElementById("prevBtn").addEventListener("click", () => {
      state.page = Math.max(1, state.page - 1);
      renderTable();
    });
    document.getElementById("nextBtn").addEventListener("click", () => {
      state.page = Math.min(totalPages(), state.page + 1);
      renderTable();
    });
    pageJump.addEventListener("change", () => {
      const val = parseInt(pageJump.value, 10);
      if (!Number.isNaN(val)) {
        state.page = Math.min(Math.max(1, val), totalPages());
        renderTable();
      }
    });

    refreshInput.addEventListener("change", () => {
      const val = parseInt(refreshInput.value, 10);
      if (!Number.isNaN(val) && val >= 5) {
        state.refreshSeconds = val;
        scheduleRefresh();
      }
    });

    pageSizeInput.addEventListener("change", () => {
      const val = parseInt(pageSizeInput.value, 10);
      if (!Number.isNaN(val) && val >= 5) {
        state.pageSize = val;
        state.page = 1;
        renderTable();
      }
    });
    toggleColumnsBtn.addEventListener("click", () => {
      toggleColumnsPanel();
    });
    columnToggleInputs.forEach(input => {
      input.addEventListener("change", () => {
        applyOptionalColumnSelection();
      });
    });
    retentionCountInput.addEventListener("input", () => {
      updateStatePersistenceUsageDisplay();
    });
    applyAuthTokenBtn.addEventListener("click", () => {
      setAuthToken(authTokenInput.value);
    });
    clearAuthTokenBtn.addEventListener("click", () => {
      authTokenInput.value = "";
      setAuthToken("");
    });
    authTokenInput.addEventListener("keydown", event => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      setAuthToken(authTokenInput.value);
    });

    tabButtons.forEach(btn => {
      btn.addEventListener("click", () => setActiveTab(btn.dataset.tab));
    });
    settingsTabButtons.forEach(btn => {
      btn.addEventListener("click", () => setActiveSettingsTab(btn.dataset.settingsTab));
    });
    saveConfigBtn.addEventListener("click", saveConfig);
    if (modalResizeHandle) {
      modalResizeHandle.addEventListener("pointerdown", beginModalResize);
    }
    if (selectRemoteConfigsBtn) {
      selectRemoteConfigsBtn.addEventListener("click", openRemoteConfigCatalogPopup);
    }
    if (sendRemoteConfigFilesBtn) {
      sendRemoteConfigFilesBtn.addEventListener("click", sendRemoteConfigFiles);
    }
    customCommandSelect.addEventListener("change", () => {
      renderCustomCommandConfiguration(customCommandSelect.value);
      updateCustomCommandSelectStyle();
    });
    sendCustomCommandBtn.addEventListener("click", queueCustomCommand);
    setClientHeartbeatBtn.addEventListener("click", saveClientHeartbeat);
    eventsSortBtn.addEventListener("click", () => {
      state.eventsSortDir = state.eventsSortDir === "desc" ? "asc" : "desc";
      eventsSortBtn.textContent = state.eventsSortDir === "desc" ? "↓" : "↑";
      eventsSortBtn.title = state.eventsSortDir === "desc" ? "Sort descending" : "Sort ascending";
      if (activeClient && modal.classList.contains("open")) {
        renderEventsHistory(activeClient);
      }
    });
    hideClientDataBtn.addEventListener("click", () => {
      clientDataPanel.classList.add("hidden");
      clientDataYaml.textContent = "";
      toggleDataBtn.classList.remove("hidden");
      toggleDataBtn.textContent = "View Data";
    });
    hideHealthDataBtn.addEventListener("click", () => {
      componentHealthPanel.classList.add("hidden");
    });

    document.getElementById("helpBtn").addEventListener("click", () => {
      window.open("/help", "_blank");
    });
    if (featureMenuSelect) {
      featureMenuSelect.addEventListener("change", handleFeatureMenuSelection);
    }
    globalSettingsBtn.addEventListener("click", openGlobalSettingsModal);
    pendingApprovalPill.addEventListener("click", openPendingApprovalModal);
    pendingApprovalPill.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openPendingApprovalModal();
      }
    });
    closeGlobalSettingsBtn.addEventListener("click", closeGlobalSettingsModal);
    cancelGlobalSettingsBtn.addEventListener("click", closeGlobalSettingsModal);
    saveGlobalSettingsBtn.addEventListener("click", saveGlobalSettings);
    saveServerSettingsBtn.addEventListener("click", saveServerSettings);
    saveStateNowBtn.addEventListener("click", saveStateNowFromSettings);
    closePendingApprovalBtn.addEventListener("click", closePendingApprovalModal);
    cancelPendingApprovalBtn.addEventListener("click", closePendingApprovalModal);
    savePendingApprovalBtn.addEventListener("click", savePendingApprovalDecisions);
    setAllApproveBtn.addEventListener("click", () => setAllPendingApprovals("approve"));
    setAllBlockBtn.addEventListener("click", () => setAllPendingApprovals("block"));

    document.getElementById("closeModal").addEventListener("click", closeModal);
    document.getElementById("cancelBtn").addEventListener("click", closeModal);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        hideHelpPopover();
        if (pendingApprovalModal.classList.contains("open")) {
          closePendingApprovalModal();
          return;
        }
        if (globalSettingsModal.classList.contains("open")) {
          closeGlobalSettingsModal();
          return;
        }
        closeModal();
      }
    });
    document.addEventListener("click", event => {
      if (!activeHelpPopover) return;
      const target = event.target;
      if (activeHelpPopover.contains(target)) return;
      if (activeHelpIcon && activeHelpIcon.contains(target)) return;
      hideHelpPopover();
    });
    document.addEventListener("keydown", (event) => {
      if (!modal.classList.contains("open")) return;
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      const targetTag = String(event.target?.tagName || "").toLowerCase();
      if (targetTag === "input" || targetTag === "textarea" || targetTag === "select") {
        return;
      }

      const visibleTabs = tabButtons.filter(btn => !btn.classList.contains("hidden"));
      if (visibleTabs.length === 0) return;
      const currentName = activeTabName();
      const currentIndex = visibleTabs.findIndex(btn => btn.dataset.tab === currentName);
      const baseIndex = currentIndex >= 0 ? currentIndex : 0;
      const delta = event.key === "ArrowRight" ? 1 : -1;
      const nextIndex = (baseIndex + delta + visibleTabs.length) % visibleTabs.length;
      const nextTabName = visibleTabs[nextIndex].dataset.tab;
      if (!nextTabName) return;
      event.preventDefault();
      setActiveTab(nextTabName);
    });

    toggleDataBtn.addEventListener("click", toggleClientData);
    removeClientBtn.addEventListener("click", removeClient);
    issueIdBtn.addEventListener("click", issueNewId);
    document.addEventListener("click", event => {
      if (!contextMenu.contains(event.target)) hideContextMenu();
    });
    window.addEventListener("resize", () => {
      hideContextMenu();
      clampOpenModalCardToViewport();
    });
    window.addEventListener("scroll", hideContextMenu);
    window.addEventListener("message", handleCatalogSelectionMessage);

    init();
  }

  global.ProviderUiBindings = {
    create: function createProviderUiBindings(_runtime) {
      return {
        bind: bindUi,
      };
    },
  };

  if (global.ProviderUiFramework && typeof global.ProviderUiFramework.bootstrap === "function") {
    global.ProviderUiFramework.bootstrap();
  } else {
    bindUi();
  }
})(window);
