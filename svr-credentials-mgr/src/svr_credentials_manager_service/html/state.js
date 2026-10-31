/* Copyright 2026 opamp.info; Licensed under the Apache License, Version 2.0. */
window.CredentialManagerState = {
  create: function create() {
    return {
      names: [],
      definition: {},
      mappings: {},
      connectionFilters: {
        connectionName: "",
        assignedClient: ""
      },
      tlsVersions: [],
      activeKind: "opamp",
      activeOtherName: "",
      sectionDrafts: {},
      knownClientIds: [],
      assignmentConnectionName: "",
      assignmentDraftClientIds: [],
      appEnableDevFeatures: false
    };
  }
};
