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

    const state = {
      clients: [],
      pendingApprovals: [],
      customCommands: [],
      eventsSortDir: "desc",
      sortKey: "client_id",
      sortDir: "asc",
      page: 1,
      pageSize: 20,
      refreshSeconds: 30,
      delayed: 60,
      significant: 300,
      minutesKeepDisconnected: 30,
      clientEventHistorySize: 50,
      stateSaveFolder: "runtime",
      retentionCount: 5,
      stateSnapshotFileCount: 0,
      autosaveIntervalSecondsSinceChange: 600,
      defaultHeartbeatFrequency: 30,
      diagnosticEnabled: false,
      statePersistenceEnabled: false,
      humanInLoopApproval: false,
      advertisedCapabilities: [],
      opampUseAuthorization: "none",
      tlsEnabled: false,
      httpsCertificateExpiryDate: null,
      httpsCertificateDaysRemaining: null,
      httpsCertificateExpiringSoon: false,
      catalogFeatureUrl: "",
      configServiceFeatureAvailable: false,
      remoteConfigSelectionsByClient: {},
      columnFilters: {},
      columnOrder: [],
      visibleColumns: {},
      columnControlsCollapsed: true,
      authToken: "",
      timer: null,
    };

    const clientBody = document.getElementById("clientBody");
    const lastUpdated = document.getElementById("lastUpdated");
    const agentCount = document.getElementById("agentCount");
    const amberCount = document.getElementById("amberCount");
    const redCount = document.getElementById("redCount");
    const pendingApprovalPill = document.getElementById("pendingApprovalPill");
    const pendingApprovalCount = document.getElementById("pendingApprovalCount");
    const pageNum = document.getElementById("pageNum");
    const pageTotal = document.getElementById("pageTotal");
    const pageJump = document.getElementById("pageJump");
    const refreshInput = document.getElementById("refreshInput");
    const pageSizeInput = document.getElementById("pageSizeInput");
    const toggleColumnsBtn = document.getElementById("toggleColumnsBtn");
    const columnControls = document.getElementById("columnControls");
    const columnToggleInputs = Array.from(
      document.querySelectorAll("input[data-column-toggle]")
    );
    const clientTableHeaderRow = document.getElementById("clientTableHeaderRow");
    const clientTableFilterRow = document.getElementById("clientTableFilterRow");
    const authTokenInput = document.getElementById("authTokenInput");
    const applyAuthTokenBtn = document.getElementById("applyAuthTokenBtn");
    const clearAuthTokenBtn = document.getElementById("clearAuthTokenBtn");
    const authTokenStatus = document.getElementById("authTokenStatus");
    const authTokenGroup = document.getElementById("authTokenGroup");
    const modal = document.getElementById("modal");
    const modalCard = document.getElementById("modalCard");
    const modalResizeHandle = document.getElementById("modalResizeHandle");
    const modalFields = document.getElementById("modalFields");
    const modalTitle = document.getElementById("modalTitle");
    const requestedConfigPanel = document.getElementById("requestedConfigPanel");
    const configInput = document.getElementById("configInput");
    const currentConfigOutput = document.getElementById("currentConfigOutput");
    const remoteConfigEnhancedPanel = document.getElementById(
      "remoteConfigEnhancedPanel"
    );
    const remoteConfigCatalogHint = document.getElementById(
      "remoteConfigCatalogHint"
    );
    const remoteConfigSelectionBody = document.getElementById(
      "remoteConfigSelectionBody"
    );
    const remoteConfigEmptyState = document.getElementById(
      "remoteConfigEmptyState"
    );
    const remoteConfigSelectionTable = document.getElementById(
      "remoteConfigSelectionTable"
    );
    const selectRemoteConfigsBtn = document.getElementById(
      "selectRemoteConfigsBtn"
    );
    const sendRemoteConfigFilesBtn = document.getElementById(
      "sendRemoteConfigFilesBtn"
    );
    const remoteConfigStatus = document.getElementById("remoteConfigStatus");
    const componentHealthPanel = document.getElementById("componentHealthPanel");
    const componentHealthBody = document.getElementById("componentHealthBody");
    const hideHealthDataBtn = document.getElementById("hideHealthDataBtn");
    const clientDataPanel = document.getElementById("clientDataPanel");
    const clientDataYaml = document.getElementById("clientDataYaml");
    const hideClientDataBtn = document.getElementById("hideClientDataBtn");
    const toggleDataBtn = document.getElementById("toggleDataBtn");
    const commandButtons = document.getElementById("commandButtons");
    const customCommandSelect = document.getElementById("customCommandSelect");
    const customCommandConfigPanel = document.getElementById("customCommandConfigPanel");
    const customCommandConfigBody = document.getElementById("customCommandConfigBody");
    const sendCustomCommandBtn = document.getElementById("sendCustomCommandBtn");
    const clientHeartbeatFrequencyInput = document.getElementById(
      "clientHeartbeatFrequencyInput"
    );
    const setClientHeartbeatBtn = document.getElementById("setClientHeartbeatBtn");
    const saveConfigBtn = document.getElementById("saveConfigBtn");
    const historyTabBtn = document.getElementById("historyTabBtn");
    const eventsHistoryList = document.getElementById("eventsHistoryList");
    const eventsSortBtn = document.getElementById("eventsSortBtn");
    const contextMenu = document.getElementById("contextMenu");
    const removeClientBtn = document.getElementById("removeClientBtn");
    const issueIdBtn = document.getElementById("issueIdBtn");
    const globalSettingsBtn = document.getElementById("globalSettingsBtn");
    const featureMenuGroup = document.getElementById("featureMenuGroup");
    const featureMenuSelect = document.getElementById("featureMenuSelect");
    const globalSettingsModal = document.getElementById("globalSettingsModal");
    const statePersistenceGroup = document.getElementById("statePersistenceGroup");
    const advertisedCapabilitiesBody = document.getElementById(
      "advertisedCapabilitiesBody"
    );
    const closeGlobalSettingsBtn = document.getElementById("closeGlobalSettingsBtn");
    const cancelGlobalSettingsBtn = document.getElementById("cancelGlobalSettingsBtn");
    const saveGlobalSettingsBtn = document.getElementById("saveGlobalSettingsBtn");
    const saveServerSettingsBtn = document.getElementById("saveServerSettingsBtn");
    const settingsTabServerOpampConfigBtn = document.getElementById(
      "settingsTabServerOpampConfigBtn"
    );
    const defaultHeartbeatFrequencyInput = document.getElementById(
      "defaultHeartbeatFrequencyInput"
    );
    const delayedCommsSecondsInput = document.getElementById(
      "delayedCommsSecondsInput"
    );
    const significantCommsSecondsInput = document.getElementById(
      "significantCommsSecondsInput"
    );
    const minutesKeepDisconnectedInput = document.getElementById(
      "minutesKeepDisconnectedInput"
    );
    const clientEventHistorySizeInput = document.getElementById(
      "clientEventHistorySizeInput"
    );
    const humanInLoopApprovalInput = document.getElementById(
      "humanInLoopApprovalInput"
    );
    const statePersistenceEnabledInput = document.getElementById(
      "statePersistenceEnabledInput"
    );
    const stateSaveFolderInput = document.getElementById("stateSaveFolderInput");
    const retentionCountInput = document.getElementById("retentionCountInput");
    const stateSnapshotFileCountOutput = document.getElementById(
      "stateSnapshotFileCountOutput"
    );
    const autosaveIntervalInput = document.getElementById("autosaveIntervalInput");
    const saveStateNowBtn = document.getElementById("saveStateNowBtn");
    const saveStateNowStatus = document.getElementById("saveStateNowStatus");
    const delayedCommsSecondsLabel = document.getElementById(
      "delayedCommsSecondsLabel"
    );
    const significantCommsSecondsLabel = document.getElementById(
      "significantCommsSecondsLabel"
    );
    const minutesKeepDisconnectedLabel = document.getElementById(
      "minutesKeepDisconnectedLabel"
    );
    const clientEventHistorySizeLabel = document.getElementById(
      "clientEventHistorySizeLabel"
    );
    const humanInLoopApprovalLabel = document.getElementById(
      "humanInLoopApprovalLabel"
    );
    const statePersistenceEnabledLabel = document.getElementById(
      "statePersistenceEnabledLabel"
    );
    const stateSaveFolderLabel = document.getElementById("stateSaveFolderLabel");
    const retentionCountLabel = document.getElementById("retentionCountLabel");
    const autosaveIntervalLabel = document.getElementById("autosaveIntervalLabel");
    const httpsCertificateExpiryGroup = document.getElementById(
      "httpsCertificateExpiryGroup"
    );
    const httpsCertificateExpiryOutput = document.getElementById(
      "httpsCertificateExpiryOutput"
    );
    const defaultHeartbeatFrequencyLabel = document.getElementById(
      "defaultHeartbeatFrequencyLabel"
    );
    const settingsTabButtons = Array.from(
      document.querySelectorAll(".settings-tab-button")
    );
    const pendingApprovalModal = document.getElementById("pendingApprovalModal");
    const pendingApprovalBody = document.getElementById("pendingApprovalBody");
    const closePendingApprovalBtn = document.getElementById("closePendingApprovalBtn");
    const cancelPendingApprovalBtn = document.getElementById("cancelPendingApprovalBtn");
    const savePendingApprovalBtn = document.getElementById("savePendingApprovalBtn");
    const setAllApproveBtn = document.getElementById("setAllApproveBtn");
    const setAllBlockBtn = document.getElementById("setAllBlockBtn");
    const serverOpampConfigPathOutput = document.getElementById(
      "serverOpampConfigPathOutput"
    );
    const serverOpampConfigOutput = document.getElementById(
      "serverOpampConfigOutput"
    );
    const providerVersionText = document.getElementById("providerVersionText");
    const providerPluginsList = document.getElementById("providerPluginsList");
    const settingsTabPanels = {
      server: document.getElementById("settings-tab-server"),
      client: document.getElementById("settings-tab-client"),
      version: document.getElementById("settings-tab-version"),
      "server-opamp-config": document.getElementById("settings-tab-server-opamp-config"),
    };
    const tabButtons = Array.from(document.querySelectorAll(".tab-button"));
    const tabPanels = {
      summary: document.getElementById("tab-summary"),
      commands: document.getElementById("tab-commands"),
      config: document.getElementById("tab-config"),
      history: document.getElementById("tab-history"),
    };

    const COMMAND_OPTIONS = [
      { value: "restart", label: "Restart Agent", description: "Request a graceful restart." },
      {
        value: "forceresync",
        label: "Force Resync",
        description: "Request full state re-reporting via ReportFullState flag.",
      },
      {
        value: "issue_unique_id",
        label: "Issue New Unique ID",
        description: "Request a replacement OpAMP instance UID for this client.",
      },
    ];
    const AUTH_TOKEN_STORAGE_KEY = "opamp_ui_bearer_token";
    const UI_PREFS_COOKIE_NAME = "opamp_ui_prefs";
    const UI_PREFS_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365;

    let activeClient = null;
    let contextClient = null;
    let pendingApprovalDecisions = {};
    let activeHelpPopover = null;
    let activeHelpIcon = null;
    let draggingColumnKey = "";
    let skipSortClickForColumn = "";
    const DEFAULT_GLOBAL_SETTINGS_HELP = {
      delayed_comms_seconds: {
        label: "Delayed Communications Threshold (seconds)",
        tooltip: "Seconds before a client is marked delayed (amber). This overrides the config file value.",
      },
      significant_comms_seconds: {
        label: "Significant Communications Threshold (seconds)",
        tooltip: "Seconds before a client is marked late (red). Must be greater than delayed_comms_seconds. This overrides the config file value.",
      },
      minutes_keep_disconnected: {
        label: "Disconnected Retention Window (minutes)",
        tooltip: "Minutes to keep disconnected clients in provider state before purge. This overrides the config file value.",
      },
      client_event_history_size: {
        label: "Client Event History Size",
        tooltip: "Maximum number of recent per-client events retained by the provider. Older events are dropped when this limit is exceeded.",
      },
      human_in_loop_approval: {
        label: "Human In Loop Approval",
        tooltip: "When enabled, unknown agents are staged for manual review and must be approved before normal processing continues.",
      },
      state_persistence_enabled: {
        label: "Enable State Persistence",
        tooltip: "When enabled, provider state snapshots can be saved/restored using state persistence settings.",
      },
      state_save_folder: {
        label: "State Save Folder",
        tooltip: "Folder used for persisted provider state snapshots.",
      },
      retention_count: {
        label: "State Snapshot Retention Count",
        tooltip: "Number of latest provider state snapshot files to retain.",
      },
      autosave_interval_seconds_since_change: {
        label: "Autosave Interval Since Change (seconds)",
        tooltip: "Seconds between autosaves after non-heartbeat OpAMP state changes.",
      },
      default_heartbeat_frequency: {
        label: "Default Heartbeat Frequency (seconds)",
        tooltip: "Default heartbeat interval in seconds applied to clients when globally updated.",
      },
    };

    // Expose provider UI runtime handles using the same module-style pattern as
    // config-service (`create(...)` factories + dependency injection).
    window.ProviderUiState = {
      create: function createProviderUiState() {
        return {
          state,
          el: {
            clientBody,
            lastUpdated,
            agentCount,
            amberCount,
            redCount,
            pendingApprovalPill,
            pendingApprovalCount,
            pageNum,
            pageTotal,
            pageJump,
            refreshInput,
            pageSizeInput,
            toggleColumnsBtn,
            columnControls,
            columnToggleInputs,
            clientTableHeaderRow,
            clientTableFilterRow,
            authTokenInput,
            applyAuthTokenBtn,
            clearAuthTokenBtn,
            authTokenStatus,
            authTokenGroup,
            modal,
            modalCard,
            modalResizeHandle,
            modalFields,
            modalTitle,
            requestedConfigPanel,
            configInput,
            currentConfigOutput,
            remoteConfigEnhancedPanel,
            remoteConfigCatalogHint,
            remoteConfigSelectionBody,
            remoteConfigEmptyState,
            remoteConfigSelectionTable,
            selectRemoteConfigsBtn,
            sendRemoteConfigFilesBtn,
            remoteConfigStatus,
            componentHealthPanel,
            componentHealthBody,
            hideHealthDataBtn,
            clientDataPanel,
            clientDataYaml,
            hideClientDataBtn,
            toggleDataBtn,
            commandButtons,
            customCommandSelect,
            customCommandConfigPanel,
            customCommandConfigBody,
            sendCustomCommandBtn,
            clientHeartbeatFrequencyInput,
            setClientHeartbeatBtn,
            saveConfigBtn,
            historyTabBtn,
            eventsHistoryList,
            eventsSortBtn,
            contextMenu,
            removeClientBtn,
            issueIdBtn,
            globalSettingsBtn,
            featureMenuGroup,
            featureMenuSelect,
            globalSettingsModal,
            statePersistenceGroup,
            advertisedCapabilitiesBody,
            closeGlobalSettingsBtn,
            cancelGlobalSettingsBtn,
            saveGlobalSettingsBtn,
            saveServerSettingsBtn,
            settingsTabServerOpampConfigBtn,
            defaultHeartbeatFrequencyInput,
            delayedCommsSecondsInput,
            significantCommsSecondsInput,
            minutesKeepDisconnectedInput,
            clientEventHistorySizeInput,
            humanInLoopApprovalInput,
            statePersistenceEnabledInput,
            stateSaveFolderInput,
            retentionCountInput,
            stateSnapshotFileCountOutput,
            autosaveIntervalInput,
            saveStateNowBtn,
            saveStateNowStatus,
            delayedCommsSecondsLabel,
            significantCommsSecondsLabel,
            minutesKeepDisconnectedLabel,
            clientEventHistorySizeLabel,
            humanInLoopApprovalLabel,
            statePersistenceEnabledLabel,
            stateSaveFolderLabel,
            retentionCountLabel,
            autosaveIntervalLabel,
            httpsCertificateExpiryGroup,
            httpsCertificateExpiryOutput,
            defaultHeartbeatFrequencyLabel,
            settingsTabButtons,
            pendingApprovalModal,
            pendingApprovalBody,
            closePendingApprovalBtn,
            cancelPendingApprovalBtn,
            savePendingApprovalBtn,
            setAllApproveBtn,
            setAllBlockBtn,
            serverOpampConfigPathOutput,
            serverOpampConfigOutput,
            providerVersionText,
            providerPluginsList,
            settingsTabPanels,
            tabButtons,
            tabPanels,
          },
          constants: {
            COMMAND_OPTIONS,
            AUTH_TOKEN_STORAGE_KEY,
            UI_PREFS_COOKIE_NAME,
            UI_PREFS_COOKIE_MAX_AGE_SECONDS,
            DEFAULT_GLOBAL_SETTINGS_HELP,
          },
        };
      },
    };
