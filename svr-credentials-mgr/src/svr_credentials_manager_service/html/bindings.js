/* Copyright 2026 opamp.info; Licensed under the Apache License, Version 2.0. */
(function bootstrap() {
  const state = window.CredentialManagerState.create();
  const functions = window.CredentialManagerFunctions.create({ state: state });
  const app = window.CredentialManagerApp.create({ state: state, functions: functions });

  const safe = function safe(action) {
    return async function wrappedAction() {
      try {
        await action.apply(null, arguments);
      } catch (error) {
        functions.status(error.message);
      }
    };
  };

  const tabs = Array.from(document.querySelectorAll(".connection-tab"));

  functions.element("reload-ui").addEventListener("click", function reloadUi() {
    const reloadUrl = new URL(window.location.href);
    reloadUrl.searchParams.set("reload", Date.now().toString());
    window.location.replace(reloadUrl.toString());
  });

  functions.element("add-test-clients").addEventListener("click", safe(app.addTestClients));

  functions.element("connection-items").addEventListener("click", safe(function handleConnectionTable(event) {
    const applyButton = event.target.closest(".apply-connection");
    if (applyButton) {
      return app.applyConnectionByName(applyButton.dataset.name);
    }
    const assignButton = event.target.closest(".assign-connection");
    if (assignButton) {
      return app.openAssignment(assignButton.dataset.name);
    }
    const removeButton = event.target.closest(".remove-connection");
    if (removeButton) {
      return app.removeConnectionByName(removeButton.dataset.name);
    }
    const connectionRow = event.target.closest(".connection-row");
    if (connectionRow) {
      return app.load(connectionRow.dataset.name);
    }
    return undefined;
  }));

  functions.element("connection-items").addEventListener("keydown", safe(function handleConnectionTableKeydown(event) {
    if (event.target.closest(".apply-connection, .assign-connection, .remove-connection")) {
      return undefined;
    }
    const connectionRow = event.target.closest(".connection-row");
    if (!connectionRow) {
      return undefined;
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      return app.load(connectionRow.dataset.name);
    }
    return undefined;
  }));

  functions.element("new-connection").addEventListener("click", safe(function createNewConnection() {
    return app.load("");
  }));
  functions.element("save-connection").addEventListener("click", safe(app.save));
  functions.element("save-connection-bottom").addEventListener("click", safe(app.save));
  functions.element("filter-connection-name").addEventListener("input", function filterConnectionsByName() {
    app.updateConnectionFilter("connectionName", functions.element("filter-connection-name").value);
  });
  functions.element("filter-assigned-client").addEventListener("input", function filterConnectionsByAssignedClient() {
    app.updateConnectionFilter("assignedClient", functions.element("filter-assigned-client").value);
  });

  tabs.forEach(function bindTab(tab, index) {
    tab.addEventListener("click", safe(function activateTab() {
      return app.activate(tab.dataset.kind);
    }));
    tab.addEventListener("keydown", safe(function navigateTabs(event) {
      let targetIndex;
      if (event.key === "ArrowRight") {
        targetIndex = (index + 1) % tabs.length;
      } else if (event.key === "ArrowLeft") {
        targetIndex = (index - 1 + tabs.length) % tabs.length;
      } else if (event.key === "Home") {
        targetIndex = 0;
      } else if (event.key === "End") {
        targetIndex = tabs.length - 1;
      } else {
        return;
      }
      event.preventDefault();
      tabs[targetIndex].focus();
      return app.activate(tabs[targetIndex].dataset.kind);
    }));
  });

  document.querySelectorAll(".pem-selector").forEach(function bindPemSelector(input) {
    input.addEventListener("change", safe(function uploadSelection() {
      return app.upload(input);
    }));
  });

  functions.element("copy-from").addEventListener("change", safe(function copyFields() {
    return app.copyFrom(functions.element("copy-from").value);
  }));

  functions.element("other-name").addEventListener("change", function updateOtherConnectionName() {
    app.preserve();
    functions.element("other-name").value = functions.element("other-name").value.trim();
    state.activeOtherName = functions.element("other-name").value;
    app.show();
  });

  functions.element("assign-selected-clients").addEventListener("click", function assignSelectedClients() {
    app.assignSelectedClients();
  });
  functions.element("unassign-selected-clients").addEventListener("click", function unassignSelectedClients() {
    app.unassignSelectedClients();
  });
  functions.element("assignment-cancel").addEventListener("click", function cancelAssignment() {
    app.closeAssignment();
  });
  functions.element("assignment-save").addEventListener("click", safe(app.saveAssignment));

  functions.element("assignment-dialog").addEventListener("click", function closeOnBackdrop(event) {
    if (event.target.id === "assignment-dialog") {
      app.closeAssignment();
    }
  });

  document.addEventListener("keydown", function closeOnEscape(event) {
    if (event.key === "Escape" && !functions.element("assignment-dialog").classList.contains("hidden")) {
      app.closeAssignment();
    }
  });

  safe(app.initialize)();
})();
