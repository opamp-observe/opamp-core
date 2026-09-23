# CLI Test Cases

This document is the maintained test-case index for the `cli` component.
Test modules should reference this file so the implementation and the documented coverage stay aligned.

## Unit Tests

### `cli/tests/test_main_unit.py`
- `test_split_script_directive_parses_output_name_and_command`
  - Verifies the `script` directive is split into an output filename and the remaining command text.
- `test_normalize_python_script_command_prefixes_python_launcher`
  - Verifies direct Python script targets are normalized to use an explicit Python launcher.
- `test_command_text_from_args_preserves_shell_quoting`
  - Verifies reconstructed command text preserves quoting semantics for shell execution.
- `test_materialize_ordered_actions_preserves_order_and_skips_missing`
  - Verifies guided action materialization preserves declared order and ignores undefined actions.
- `test_catalog_launch_config_path_enables_catalog`
  - Verifies generated runtime config for catalog launch enables the catalog feature.
- `test_process_tail_setting_round_trip`
  - Verifies process-tail settings are persisted and reloaded correctly.
- `test_main_writes_component_lifecycle_log`
  - Verifies the CLI component lifecycle log is created during execution.
- `test_status_command_reports_default_opamp_config_path`
  - Verifies `status` reports the default `config/opamp.json` path and successful load state.
- `test_status_command_reports_env_opamp_config_path`
  - Verifies `status` reports an `OPAMP_CONFIG_PATH` override and successful load state.
- `test_status_command_reports_invalid_opamp_config`
  - Verifies `status` reports invalid JSON instead of treating an unreadable config as loaded.
- `test_list_command_reports_config_options_when_available`
  - Verifies `list` includes the `config` command subtree when config-service support is available.
- `test_cli_config_view_prints_active_config_and_path`
  - Verifies `cli-config view` prints the active CLI config content and absolute path.
- `test_cli_config_summary_reports_key_counts`
  - Verifies `cli-config summary` reports demo profile and component counts.
- `test_cli_config_change_config_replaces_active_config`
  - Verifies `cli-config change-config` can load and persist a smaller replacement profile config.
- `test_cli_config_change_config_rejects_malformed_json_without_changing_settings`
  - Verifies malformed JSON is rejected and the active CLI config remains unchanged.
- `test_cli_config_change_config_rejects_missing_path_without_changing_settings`
  - Verifies a missing replacement path is rejected and the active CLI config remains unchanged.
- `test_interactive_cli_config_unknown_subcommand_uses_human_message`
  - Verifies interactive `cli-config` parse errors show command guidance instead of a raw exit code.
- `test_interactive_cli_config_change_failure_uses_human_message`
  - Verifies interactive `cli-config change-config` failures show a friendly follow-up instead of a raw exit code.
- `test_help_includes_setup_venv_command`
  - Verifies `help` advertises the repository virtual environment setup command.
- `test_top_level_commands_include_setup_venv`
  - Verifies `setup-venv` is always available as a top-level command.
- `test_parse_setup_venv_args_supports_options`
  - Verifies `setup-venv` parses `--venv`, `--dry-run`, and `--skip-node`.
- `test_setup_venv_dry_run_lists_python_and_node_steps`
  - Verifies dry-run setup prints Python and Node installer steps without executing them.
- `test_prompt_setup_venv_activation_opens_shell_when_accepted`
  - Verifies the setup flow can open an activated child shell when the user accepts the prompt.
- `test_prompt_setup_venv_activation_can_be_declined`
  - Verifies declining the activation prompt leaves the virtual environment ready without opening a shell.
- `test_prompt_setup_venv_activation_skips_prompt_without_tty`
  - Verifies non-interactive setup reports the ready virtual environment without prompting.
- `test_config_validate_single_file_writes_report`
  - Verifies `config validate` processes one file, prints `no error`, and writes a report file.
- `test_config_validate_directory_reports_each_file_with_spacing`
  - Verifies `config validate` processes a two-file directory and separates file sections with three blank lines.
- `test_config_metadata_adds_missing_header_values`
  - Verifies `config metadata` adds missing config-service header values for config type and version.
- `test_config_metadata_preserves_existing_header_values`
  - Verifies `config metadata` does not overwrite existing config-service header values.
- `test_rejected_guided_action_is_logged`
  - Verifies invalid guided actions are rejected and logged.
- `test_resolve_guided_action_matches_aliases`
  - Verifies guided-action alias resolution maps common aliases to the correct action.
- `test_start_and_stop_action_orders_are_stable`
  - Verifies the ordered `start` and `stop` action lists remain stable.
- `test_broker_stop_action_uses_cli_managed_process_records`
  - Verifies broker shutdown uses CLI-managed process records instead of the retired broker PID-file wrapper flow.
- `test_broker_start_action_includes_repo_root_for_shared_imports`
  - Verifies broker startup includes both `agent_broker` and the repository root on `PYTHONPATH` so repo-level `shared` imports resolve.
- `test_background_start_early_exit_reports_log_detail`
  - Verifies early background-process exits include the exit code, log path, and a useful final process log line in the console error.
- `test_script_mode_generates_broker_launcher_script`
  - Verifies `opamp-cli script ...` can generate a broker launcher script with the expected module command and config path.
- `test_demo_profile_loader_carries_elastic_agent_and_container_config`
  - Verifies demo profiles preserve Elastic Agent and container launch configuration.
- `test_container_start_action_uses_configured_runtime_command`
  - Verifies configured container entries produce the expected runtime `run` command.
- `test_dev_containers_command_is_listed_when_runtime_and_actions_available`
  - Verifies `dev-containers` is exposed only when a runtime-backed configured action exists.
- `test_execute_dev_container_workflow_launches_selected_action`
  - Verifies `dev-containers <target>` resolves aliases and launches the selected configured container.
- `test_start_demo_consumers_runs_container_then_elastic_agent_client`
  - Verifies the Elastic Agent Logstash demo starts the configured container before the plugin-driven Elastic Agent consumer.

## End-to-End Tests

### `cli/tests/test_main_e2e.py`
- `test_help_command_prints_usage`
  - Verifies `help` output is available from the CLI entrypoint and advertises setup plus container commands.
- `test_status_command_reports_runtime_paths`
  - Verifies `status` reports the effective OpAMP config path, managed-process state path, log path, and CLI log path.
- `test_list_command_reports_option_hierarchy`
  - Verifies `list` reports top-level commands, guided actions, and the `config` subcommands when available.
- `test_cli_config_summary_e2e_reports_default_config`
  - Verifies `cli-config summary` reports the default active CLI profile config through the real entrypoint.
- `test_direct_execution_runs_python_command`
  - Verifies direct command execution works through the CLI entrypoint.
- `test_script_generation_writes_os_native_script`
  - Verifies `script ...` generation creates an OS-native output script.
- `test_config_validate_single_file_e2e`
  - Verifies `config validate` succeeds for one file and writes a report file through the real entrypoint.
- `test_config_validate_directory_e2e`
  - Verifies `config validate` succeeds for a two-file directory through the real entrypoint.
- `test_config_metadata_directory_e2e_preserves_existing_header`
  - Verifies `config metadata` updates missing metadata while preserving files that already contain config-service header values.
- `test_unknown_guided_target_returns_error`
  - Verifies unknown guided targets fail cleanly with a non-zero exit path.
