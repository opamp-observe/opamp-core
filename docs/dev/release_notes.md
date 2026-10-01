# Release Notes

## 5.1
### Consumer
* Address some gaps found in the decoupling work
* Addition of the Vector agent
* Added a browser-driven container regression for UI-requested shutdown across all six built-in consumer types, including provider disconnect and process-exit evidence.
* Fixed built-in custom command discovery for consumers without an agent-specific handler directory, allowing the shared shutdown handler to be advertised and executed.
* Fixed Fluentd monitor endpoint discovery so a local bind address no longer replaces the remote OpAMP provider hostname.

### Client Config Generator Service
* Added an independently packaged, schema-driven server plugin and standalone UI for generating Supervisor and Observer consumer configurations.
* Added versioned list, load, validate, and atomic-save API controls with configured-directory containment and read-only deployment support.
* Added provider deployment discovery, build/version registration, static help, documentation, and container validation for enabled and disabled deployments.

### CLI
* Improvements around the CLI to clean up log files
* make it easier to startup demos
* base configuration enhanced to provide additional demo scenarios
* Added `cli-config` commands to view, summarize, and safely switch the active CLI demo profile configuration, with autocomplete support and friendlier interactive error messages.
* Fixed Broker startup from the CLI and source-tree command line by ensuring repo-level shared modules are importable.
* Improved background startup failures so Broker and other managed processes report a useful log detail alongside the exit code and log path.

### 5.0
* Decoupling of the agent logic so that the consumer is easier to extend and implement users own custom plugins if wanted


## 4.1

### Consumer
* Refinement of the output configuratios for Fluent Bit 4.2
* Client (consumer) startup as an observer refined 

### CLI
+

### Configuration Service
* Enhanced JSON schema so called_enum_options is now enum_options, and the validation process only needs to validation kind, the enum values come from enum_options not values now.
