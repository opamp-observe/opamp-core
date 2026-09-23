# Release Notes

## 5.1
### Consumer
* Address some gaps found in the decoupling work
* Addition of the Vector agent

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
