# Copyright 2026 mp3monster.org
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""CLI entrypoint for the OpAMP developer tools component."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .certificates import (
    DEFAULT_TRUST_ANCHOR_MODE,
    TRUST_ANCHOR_MODES,
    configure_keycloak,
    ensure_provider_tls_config,
    generate_self_signed_certificate,
)
from .components import (
    build_artifacts,
    build_diagrams,
    build_docs,
    build_pdf,
    build_sboms,
    discover_build_components,
    run_component_tests,
    run_e2e_tests,
    select_components,
)
from .config_sync import sync_config_service_json_assets
from .container_images import CONTAINER_RUNTIME_CHOICES, clean_project_images
from .hooks import apply_precommit_logic
from .javascript_complexity import (
    DEFAULT_MAX_COMPLEXITY,
    run_javascript_complexity_checks,
)
from .provider_ui import compact_provider_ui_assets
from .release_assets import (
    add_release_assets_arguments,
    build_release_assets,
    parse_release_component_keys,
    resolve_release_sbom_paths,
)
from .runtime import (
    DEFAULT_ERROR_EXIT_CODE,
    DEFAULT_ISSUES_EXIT_CODE,
    CommandRuntime,
)
from .schema_validation import validate_config_service_schemas
from .security import run_component_security_checks, run_repo_security_checks
from .versioning import set_repository_version
from .wheel_publish import (
    AWS_DEFAULT_ARTIFACT_KEY,
    AZURE_ARTIFACT_CONTAINER_DEFAULT,
    AZURE_AUTH_MODE_DEFAULT,
    AZURE_AUTH_MODES,
    AZURE_CONTAINER_DEFAULT,
    CLOUD_ORIGIN_CHOICES,
    DEFAULT_DIST_ROOT,
    DEFAULT_GITHUB_REPOSITORY,
    DEFAULT_RELEASE_PREFIX,
    UPLOAD_ORIGIN_CHOICES,
    WheelUploadOptions,
    push_latest_wheels_to_cloud,
    upload_latest_wheels,
)

INTERACTIVE_EXIT_MESSAGE = "Exiting developer CLI."
INTERACTIVE_RETURN_TO_MAIN_MESSAGE = "Returning to main menu."
INTERACTIVE_SUCCESS_MESSAGE = "Command complete. Returning to main menu."
INTERACTIVE_ISSUES_MESSAGE = "Command completed with reported issues. Returning to main menu."
INTERACTIVE_FAILURE_MESSAGE = "Command failed. Returning to main menu."
COMPONENT_BUILD_COMMANDS = frozenset({"artefact", "sbom", "secure"})
SIMPLE_BUILD_COMMANDS = frozenset(
    {"ui-compaction", "js-complexity", "docs", "diagrams", "release-assets"}
)
INTERACTIVE_ACTION_RUN = "run"
INTERACTIVE_ACTION_RETURN_TO_MAIN = "return-to-main"
INTERACTIVE_ACTION_EXIT = "exit"


def build_parser(default_repo_root: Path | None = None) -> argparse.ArgumentParser:
    """Build the argparse command tree for direct and guided CLI usage.

    Parameters
    ----------
    default_repo_root:
        Repository root used to resolve component discovery and the default
        value for the global ``--repo-root`` option.

    """
    resolved_default_repo_root = (
        default_repo_root.resolve() if default_repo_root is not None else Path.cwd().resolve()
    )
    available_components = [
        component.key for component in discover_build_components(resolved_default_repo_root)
    ]
    parser = argparse.ArgumentParser(
        description="Developer CLI utility for OpAMP repository workflows."
    )
    parser.add_argument(
        "--repo-root",
        default=str(resolved_default_repo_root),
        help="Repository root path.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used for Python-based commands.",
    )

    command_parsers = parser.add_subparsers(dest="command_group", required=True)

    dev_parser = command_parsers.add_parser("dev", help="Developer maintenance commands")
    dev_subparsers = dev_parser.add_subparsers(dest="dev_command", required=True)
    dev_subparsers.add_parser("validate-schemas", help="Validate config-service JSON definitions and schemas")
    set_parser = dev_subparsers.add_parser("set", help="Set repository-maintained values")
    set_subparsers = set_parser.add_subparsers(dest="set_command", required=True)
    version_parser = set_subparsers.add_parser("version", help="Prompt for and set a new repository version")
    version_parser.add_argument("--version", help="Version in MAJOR.MINOR.PATCH format")
    sync_parser = dev_subparsers.add_parser("sync", help="Synchronize repository-managed assets")
    sync_subparsers = sync_parser.add_subparsers(dest="sync_command", required=True)
    sync_subparsers.add_parser(
        "config-service-json",
        help="Mirror config-service JSON definitions and schemas from src into packaged copies",
    )
    apply_parser = dev_subparsers.add_parser("apply", help="Apply repository automation")
    apply_subparsers = apply_parser.add_subparsers(dest="apply_command", required=True)
    apply_subparsers.add_parser("precommit-logic", help="Configure repository git hooks")
    clean_images_parser = dev_subparsers.add_parser(
        "clean-images",
        help="Remove images created by OpAMP development and regression builds",
    )
    clean_images_parser.add_argument(
        "--runtime",
        choices=CONTAINER_RUNTIME_CHOICES,
        default="",
        help="Container runtime override; defaults to OPAMP_CONTAINER_RUNTIME or auto-detection",
    )
    clean_images_parser.add_argument(
        "--include-legacy",
        action="store_true",
        help="Also remove unlabelled images whose repository starts with opamp-",
    )
    clean_images_parser.add_argument(
        "--force",
        action="store_true",
        help="Force removal of images that are referenced by containers",
    )
    clean_images_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List matching images without removing them",
    )
    upload_wheels_parser = dev_subparsers.add_parser(
        "upload-wheels",
        help="Publish the latest wheels from local, AWS, or Azure storage to GitHub",
    )
    upload_wheels_parser.add_argument(
        "--origin",
        choices=UPLOAD_ORIGIN_CHOICES,
        required=True,
        help="Wheel source: local host, latest AWS bucket, or latest Azure storage account",
    )
    upload_wheels_parser.add_argument(
        "--release",
        required=True,
        help="GitHub release tag and cloud source release folder name",
    )
    upload_wheels_parser.add_argument(
        "--dist-root",
        default=DEFAULT_DIST_ROOT,
        help="Host directory searched recursively for wheel files",
    )
    upload_wheels_parser.add_argument(
        "--storage-name",
        default="",
        help=(
            "Source AWS bucket or Azure account; uses the deployment marker, then AWS "
            "discovers the newest retained bucket"
        ),
    )
    upload_wheels_parser.add_argument(
        "--repository",
        default=DEFAULT_GITHUB_REPOSITORY,
        help="GitHub repository in owner/name format",
    )
    upload_wheels_parser.add_argument(
        "--github-token",
        default="",
        help="GitHub token; defaults to GITHUB_TOKEN or GH_TOKEN",
    )
    upload_wheels_parser.add_argument(
        "--prefix",
        default=DEFAULT_RELEASE_PREFIX,
        help="AWS or Azure object prefix before the release name",
    )
    upload_wheels_parser.add_argument(
        "--aws-region",
        default="",
        help="AWS region; defaults to AWS_REGION, AWS_DEFAULT_REGION, or eu-west-2",
    )
    upload_wheels_parser.add_argument(
        "--azure-container",
        default=AZURE_CONTAINER_DEFAULT,
        help="Azure release-wheel container searched before deployment artifacts",
    )
    upload_wheels_parser.add_argument(
        "--azure-artifact-container",
        default=AZURE_ARTIFACT_CONTAINER_DEFAULT,
        help="Azure deployment artifact container used when release wheels are absent",
    )
    upload_wheels_parser.add_argument(
        "--aws-artifact-key",
        default=AWS_DEFAULT_ARTIFACT_KEY,
        help="AWS deployment archive key used when release wheels are absent",
    )
    upload_wheels_parser.add_argument(
        "--azure-auth-mode",
        choices=AZURE_AUTH_MODES,
        default=AZURE_AUTH_MODE_DEFAULT,
        help="Azure CLI storage authentication mode",
    )
    upload_wheels_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show retrieval and GitHub destination without transferring files",
    )
    push_to_cloud_parser = dev_subparsers.add_parser(
        "push-to-cloud",
        help="Push the latest local wheel for each package to AWS or Azure",
    )
    push_to_cloud_parser.add_argument(
        "--origin",
        choices=CLOUD_ORIGIN_CHOICES,
        required=True,
        help="Cloud destination provider",
    )
    push_to_cloud_parser.add_argument("--release", required=True, help="Cloud release folder name")
    push_to_cloud_parser.add_argument(
        "--dist-root",
        default=DEFAULT_DIST_ROOT,
        help="Host directory searched recursively for wheel files",
    )
    push_to_cloud_parser.add_argument(
        "--storage-name",
        default="",
        help=(
            "AWS bucket or Azure account; uses the deployment marker, then AWS discovers "
            "the newest retained bucket"
        ),
    )
    push_to_cloud_parser.add_argument(
        "--prefix",
        default=DEFAULT_RELEASE_PREFIX,
        help="Cloud object prefix before the release name",
    )
    push_to_cloud_parser.add_argument(
        "--aws-region",
        default="",
        help="AWS region; defaults to AWS_REGION, AWS_DEFAULT_REGION, or eu-west-2",
    )
    push_to_cloud_parser.add_argument(
        "--azure-container",
        default=AZURE_CONTAINER_DEFAULT,
        help="Azure Blob Storage container receiving wheel files",
    )
    push_to_cloud_parser.add_argument(
        "--azure-auth-mode",
        choices=AZURE_AUTH_MODES,
        default=AZURE_AUTH_MODE_DEFAULT,
        help="Azure CLI storage authentication mode",
    )
    push_to_cloud_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show selected wheels and cloud destinations without uploading",
    )

    build_parser_cmd = command_parsers.add_parser("build", help="Build, test, and generate outputs")
    build_subparsers = build_parser_cmd.add_subparsers(dest="build_command", required=True)

    artefact_parser = build_subparsers.add_parser("artefact", help="Build wheel and source artefacts")
    _add_named_or_all_parsers(
        artefact_parser,
        noun="component",
        available_components=available_components,
    )
    artefact_parser.add_argument("--no-isolation", action="store_true", help="Pass --no-isolation to python -m build")

    sbom_parser = build_subparsers.add_parser("sbom", help="Generate SBOMs")
    _add_named_or_all_parsers(
        sbom_parser,
        noun="component",
        available_components=available_components,
    )
    sbom_parser.add_argument("--no-isolation", action="store_true", help="Pass --no-isolation to python -m build")

    secure_parser = build_subparsers.add_parser("secure", help="Run security checks")
    _add_named_or_all_parsers(
        secure_parser,
        noun="component",
        available_components=available_components,
    )

    test_parser = build_subparsers.add_parser("test", help="Run unit, Playwright, or e2e tests")
    test_subparsers = test_parser.add_subparsers(dest="test_scope", required=True)
    named_test_parser = test_subparsers.add_parser("named", help="Run tests for one component")
    named_test_parser.add_argument(
        "component",
        choices=available_components,
        help="Component directory name",
    )
    test_subparsers.add_parser("all", help="Run tests for all discovered components")
    test_subparsers.add_parser("e2e", help="Run end-to-end tests")

    pdf_parser = build_subparsers.add_parser("pdf", help="Generate the OpAMP PDF manual")
    pdf_parser.add_argument("--output", help="Optional PDF output path")
    ui_compaction_parser = build_subparsers.add_parser(
        "ui-compaction",
        help="Build compacted provider web UI JavaScript assets",
    )
    ui_compaction_parser.add_argument(
        "--html-dir",
        default="provider/src/opamp_provider/html",
        help="HTML asset directory path relative to repo root",
    )
    ui_compaction_parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Remove existing `.mini.js` files and exit",
    )
    js_complexity_parser = build_subparsers.add_parser(
        "js-complexity",
        help="Run JavaScript and TypeScript cyclomatic-complexity checks",
    )
    js_complexity_parser.add_argument(
        "--max-complexity",
        type=int,
        default=DEFAULT_MAX_COMPLEXITY,
        help="Maximum allowed cyclomatic complexity per function/method",
    )
    js_complexity_parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        help=(
            "Optional file or directory path relative to repo root. "
            "Repeat to override the default JavaScript/TypeScript source target set."
        ),
    )
    build_subparsers.add_parser("docs", help="Regenerate markdown quick references from JSON artifacts")
    build_subparsers.add_parser("diagrams", help="Render Mermaid diagrams to images")
    release_assets_parser = build_subparsers.add_parser(
        "release-assets",
        help="Build release wheels and SBOMs, then optionally publish them",
    )
    add_release_assets_arguments(release_assets_parser)

    cert_parser = command_parsers.add_parser("certificate", help="Certificate and auth helpers")
    cert_subparsers = cert_parser.add_subparsers(dest="certificate_command", required=True)
    generate_parser = cert_subparsers.add_parser(
        "generate",
        help="Guide the user through self-signed certificate creation",
    )
    generate_parser.add_argument("--cert-file", help="Certificate output path relative to repo root")
    generate_parser.add_argument("--key-file", help="Private key output path relative to repo root")
    generate_parser.add_argument("--common-name", help="Certificate common name")
    generate_parser.add_argument("--days", type=int, help="Certificate validity period in days")
    generate_parser.add_argument(
        "--dns-name",
        action="append",
        dest="dns_names",
        help="DNS subject alternative name. Repeat to add multiple values.",
    )
    generate_parser.add_argument(
        "--ip-address",
        action="append",
        dest="ip_addresses",
        help="IP subject alternative name. Repeat to add multiple values.",
    )
    generate_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing certificate and key output files",
    )
    generate_parser.add_argument(
        "--skip-dependency-install",
        action="store_true",
        help="Skip checking or installing the cryptography dependency",
    )
    ensure_tls_parser = cert_subparsers.add_parser(
        "ensure-provider-config",
        help="Ensure provider.tls config exists in an OpAMP JSON file",
    )
    ensure_tls_parser.add_argument("--config-file", help="Path to OpAMP config JSON")
    ensure_tls_parser.add_argument("--cert-file", help="TLS certificate path")
    ensure_tls_parser.add_argument("--key-file", help="TLS private key path")
    ensure_tls_parser.add_argument(
        "--trust-anchor-mode",
        choices=TRUST_ANCHOR_MODES,
        default=DEFAULT_TRUST_ANCHOR_MODE,
        help="Provider TLS trust mode",
    )
    cert_subparsers.add_parser("keycloak", help="Guide the user through local Keycloak setup")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint.

    When started without arguments, the command switches to a guided mode that
    shows the first level of command groups and prompts for the remaining
    required selections. Scripted calls still use normal argparse parsing.
    """
    arg_tokens = list(sys.argv[1:] if argv is None else argv)
    launch_root = Path.cwd().resolve()
    explicit_repo_root = _extract_repo_root_from_tokens(arg_tokens)
    repo_root = explicit_repo_root or launch_root
    _print_startup_context(repo_root=repo_root, used_default_repo_root=explicit_repo_root is None)
    global_option_tokens = _extract_global_option_tokens(arg_tokens)
    if not _has_command_tokens(arg_tokens):
        return _run_interactive_session(
            repo_root=repo_root,
            global_option_tokens=global_option_tokens,
        )
    parser = build_parser(repo_root)
    args = parser.parse_args(arg_tokens)
    return _run_parsed_command(args)


def _run_interactive_session(
    *,
    repo_root: Path,
    global_option_tokens: Sequence[str],
) -> int:
    """Run the guided menu loop until the user chooses to quit.

    Parameters
    ----------
    repo_root:
        Repository root used to discover components and build the parser for
        each prompted command.
    global_option_tokens:
        Explicit global CLI options that should be preserved across each
        guided command execution.

    """
    while True:
        action, command_tokens = _prompt_for_command_tokens(repo_root)
        if action == INTERACTIVE_ACTION_EXIT:
            print(INTERACTIVE_EXIT_MESSAGE)
            return 0
        if action == INTERACTIVE_ACTION_RETURN_TO_MAIN:
            print(INTERACTIVE_RETURN_TO_MAIN_MESSAGE)
            continue
        parser = build_parser(repo_root)
        args = parser.parse_args([*global_option_tokens, *command_tokens])
        exit_code = _run_parsed_command(args)
        print(_interactive_completion_message(exit_code))


def _run_parsed_command(args: argparse.Namespace) -> int:
    """Execute one parsed command and persist its issue/error logs.

    Parameters
    ----------
    args:
        Parsed command-line arguments that identify the operation to execute.

    """
    repo_root = Path(args.repo_root).expanduser().resolve()
    tool_root = repo_root / "dev-tools"
    command_slug = _command_slug_from_args(args)
    runtime = CommandRuntime(repo_root=repo_root, tool_root=tool_root, command_slug=command_slug)
    exit_code = 0
    try:
        issues_found = _dispatch(args, runtime)
        if issues_found:
            exit_code = DEFAULT_ISSUES_EXIT_CODE
    except Exception as exc:  # pylint: disable=broad-except
        runtime.record_error(f"{type(exc).__name__}: {exc}")
        exit_code = DEFAULT_ERROR_EXIT_CODE
    finally:
        runtime.write_logs()
        runtime.print_log_summary()
    return exit_code


def _dispatch(args: argparse.Namespace, runtime: CommandRuntime) -> bool:
    """Dispatch one parsed CLI request to its implementation.

    Parameters
    ----------
    args:
        Parsed command-line arguments that describe the selected workflow.
    runtime:
        Shared runtime that owns process execution, console reporting, and
        issue/error log capture for the current command.

    """
    if args.command_group == "dev":
        return _dispatch_dev_command(args, runtime)
    if args.command_group == "build":
        return _dispatch_build_command(args, runtime)
    if args.command_group == "certificate":
        return _dispatch_certificate_command(args, runtime)

    raise RuntimeError("unsupported command group")


def _dispatch_dev_command(args: argparse.Namespace, runtime: CommandRuntime) -> bool:
    """Dispatch one developer-maintenance command."""
    if args.dev_command == "validate-schemas":
        return validate_config_service_schemas(runtime)
    if args.dev_command == "set" and args.set_command == "version":
        return set_repository_version(runtime, version=args.version)
    if args.dev_command == "sync" and args.sync_command == "config-service-json":
        return sync_config_service_json_assets(runtime)
    if args.dev_command == "apply" and args.apply_command == "precommit-logic":
        return apply_precommit_logic(runtime)
    if args.dev_command == "clean-images":
        return clean_project_images(
            runtime,
            configured_runtime=args.runtime,
            include_legacy=args.include_legacy,
            force=args.force,
            dry_run=args.dry_run,
        )
    if args.dev_command == "upload-wheels":
        return upload_latest_wheels(
            runtime,
            WheelUploadOptions(
                origin=args.origin,
                release=args.release,
                dist_root=args.dist_root,
                storage_name=args.storage_name,
                repository=args.repository,
                github_token=args.github_token,
                prefix=args.prefix,
                aws_region=args.aws_region,
                azure_container=args.azure_container,
                azure_auth_mode=args.azure_auth_mode,
                azure_artifact_container=args.azure_artifact_container,
                aws_artifact_key=args.aws_artifact_key,
                dry_run=args.dry_run,
            ),
        )
    if args.dev_command == "push-to-cloud":
        return push_latest_wheels_to_cloud(
            runtime,
            WheelUploadOptions(
                origin=args.origin,
                release=args.release,
                dist_root=args.dist_root,
                storage_name=args.storage_name,
                prefix=args.prefix,
                aws_region=args.aws_region,
                azure_container=args.azure_container,
                azure_auth_mode=args.azure_auth_mode,
                dry_run=args.dry_run,
            ),
        )
    raise RuntimeError("unsupported dev command")


def _dispatch_build_command(args: argparse.Namespace, runtime: CommandRuntime) -> bool:
    """Dispatch one build-oriented command."""
    if args.build_command in COMPONENT_BUILD_COMMANDS:
        return _dispatch_component_build_command(args, runtime)
    if args.build_command == "test":
        return _dispatch_test_command(args, runtime)
    if args.build_command == "pdf":
        return build_pdf(runtime, python_exe=args.python, output=args.output)
    if args.build_command in SIMPLE_BUILD_COMMANDS:
        return _dispatch_simple_build_command(args, runtime)
    raise RuntimeError("unsupported build command")


def _dispatch_component_build_command(args: argparse.Namespace, runtime: CommandRuntime) -> bool:
    """Dispatch artefact, SBOM, or security commands with component selection."""
    components = select_components(
        runtime.repo_root,
        named_component=_selected_component_name(args),
    )
    if args.build_command == "artefact":
        return build_artifacts(
            runtime,
            components=components,
            python_exe=args.python,
            no_isolation=args.no_isolation,
        )
    if args.build_command == "sbom":
        return build_sboms(
            runtime,
            components=components,
            python_exe=args.python,
            no_isolation=args.no_isolation,
        )
    if args.scope == "all":
        return run_repo_security_checks(runtime, python_exe=args.python)
    return run_component_security_checks(
        runtime,
        component=components[0],
        python_exe=args.python,
    )


def _dispatch_test_command(args: argparse.Namespace, runtime: CommandRuntime) -> bool:
    """Dispatch one unit, UI, or end-to-end test command."""
    if args.test_scope == "e2e":
        return run_e2e_tests(runtime, python_exe=args.python)
    components = select_components(
        runtime.repo_root,
        named_component=args.component if args.test_scope == "named" else None,
    )
    return run_component_tests(runtime, components=components, python_exe=args.python)


def _dispatch_simple_build_command(args: argparse.Namespace, runtime: CommandRuntime) -> bool:
    """Dispatch one single-purpose build command without component selection."""
    if args.build_command == "ui-compaction":
        return compact_provider_ui_assets(
            runtime,
            html_dir=args.html_dir,
            clean_only=args.clean_only,
        )
    if args.build_command == "js-complexity":
        return run_javascript_complexity_checks(
            runtime,
            max_complexity=args.max_complexity,
            target_paths=args.paths,
        )
    if args.build_command == "docs":
        return build_docs(runtime, python_exe=args.python)
    if args.build_command == "diagrams":
        return build_diagrams(runtime)
    return _dispatch_release_assets_command(args, runtime)


def _dispatch_release_assets_command(args: argparse.Namespace, runtime: CommandRuntime) -> bool:
    """Dispatch the composite release-assets workflow."""
    component_keys = parse_release_component_keys(args.components)
    resolved_sbom_paths = resolve_release_sbom_paths(
        repo_root=runtime.repo_root,
        component_keys=component_keys,
        provider_sbom_path=args.provider_sbom_path,
        consumer_sbom_path=args.consumer_sbom_path,
        component_sbom_path_overrides=args.component_sbom_path,
    )
    return build_release_assets(
        runtime,
        repo=args.repo,
        component_keys=component_keys,
        dist_root=args.dist_root,
        resolved_sbom_paths=resolved_sbom_paths,
        manual_path=args.manual_path,
        skip_manual=args.skip_manual,
        skip_ui_compaction=args.skip_ui_compaction,
        skip_security_checks=args.skip_security_checks,
        python_exe=args.python,
        no_isolation=args.no_isolation,
        publish=args.publish,
        tag=args.tag,
        release_name=args.release_name,
        release_notes=args.release_notes,
        release_notes_file=args.release_notes_file,
        draft=args.draft,
        prerelease=args.prerelease,
        github_token=args.github_token,
    )


def _dispatch_certificate_command(args: argparse.Namespace, runtime: CommandRuntime) -> bool:
    """Dispatch one certificate or auth helper command."""
    if args.certificate_command == "generate":
        return generate_self_signed_certificate(
            runtime,
            python_exe=args.python,
            cert_file=args.cert_file,
            key_file=args.key_file,
            common_name=args.common_name,
            validity_days=args.days,
            dns_names=args.dns_names,
            ip_addresses=args.ip_addresses,
            force=args.force,
            skip_dependency_install=args.skip_dependency_install,
        )
    if args.certificate_command == "ensure-provider-config":
        return ensure_provider_tls_config(
            runtime,
            config_file=args.config_file,
            cert_file=args.cert_file,
            key_file=args.key_file,
            trust_anchor_mode=args.trust_anchor_mode,
        )
    if args.certificate_command == "keycloak":
        return configure_keycloak(runtime)
    raise RuntimeError("unsupported certificate command")


def _selected_component_name(args: argparse.Namespace) -> str | None:
    """Return the selected component name for named/all build commands."""
    if getattr(args, "scope", "") != "named":
        return None
    return getattr(args, "component", None)


def _prompt_for_command_tokens(repo_root: Path) -> tuple[str, list[str]]:
    """Prompt for one top-level command path in guided mode.

    Parameters
    ----------
    repo_root:
        Repository root used to discover buildable components for menu
        prompts that offer named component execution.

    """
    available_components = [
        component.key for component in discover_build_components(repo_root)
    ]
    print("No command was provided. Choose a command group to continue.")
    command_group = _prompt_for_selection(
        "Command groups",
        [
            ("dev", "Developer maintenance commands"),
            ("build", "Build, test, and generate outputs"),
            ("certificate", "Certificate and auth helpers"),
        ],
    )
    if command_group is None:
        return INTERACTIVE_ACTION_EXIT, []
    if command_group == "dev":
        command_tokens = _prompt_for_dev_tokens()
    elif command_group == "build":
        command_tokens = _prompt_for_build_tokens(available_components)
    else:
        command_tokens = _prompt_for_certificate_tokens()
    if command_tokens is None:
        return INTERACTIVE_ACTION_RETURN_TO_MAIN, []
    return INTERACTIVE_ACTION_RUN, command_tokens


def _prompt_for_dev_tokens() -> list[str] | None:
    """Prompt for one developer maintenance command token sequence."""
    command = _prompt_for_selection(
        "Dev commands",
        [
            ("validate-schemas", "Validate config-service JSON definitions and schemas"),
            ("set version", "Prompt for and set a new repository version"),
            ("sync config-service-json", "Mirror config-service JSON definitions and schemas"),
            ("apply precommit-logic", "Configure repository git hooks"),
            ("clean-images", "Remove project-managed Docker or Podman images"),
            ("upload-wheels", "Publish wheels from local, AWS, or Azure to GitHub"),
            ("push-to-cloud", "Push the latest local wheels to AWS or Azure"),
        ],
    )
    if command is None:
        return None
    if command == "validate-schemas":
        return ["dev", "validate-schemas"]
    if command == "set version":
        return ["dev", "set", "version"]
    if command == "sync config-service-json":
        return ["dev", "sync", "config-service-json"]
    if command == "apply precommit-logic":
        return ["dev", "apply", "precommit-logic"]
    if command == "clean-images":
        return _prompt_for_clean_images_tokens()
    if command == "upload-wheels":
        return _prompt_for_upload_wheels_tokens()
    return _prompt_for_push_to_cloud_tokens()


def _prompt_for_clean_images_tokens() -> list[str] | None:
    """Prompt for project image cleanup options."""
    runtime_name = _prompt_for_selection(
        "Container runtime",
        [
            ("auto", "Use OPAMP_CONTAINER_RUNTIME or auto-detect Docker/Podman"),
            ("docker", "Use Docker"),
            ("podman", "Use Podman"),
        ],
    )
    if runtime_name is None:
        return None
    tokens = ["dev", "clean-images"]
    if runtime_name != "auto":
        tokens.extend(["--runtime", runtime_name])
    if _prompt_yes_no("Include legacy unlabelled opamp-* images?", default=False):
        tokens.append("--include-legacy")
    if _prompt_yes_no("Force removal of images referenced by containers?", default=False):
        tokens.append("--force")
    if _prompt_yes_no("Dry run only?", default=False):
        tokens.append("--dry-run")
    return tokens


def _prompt_for_upload_wheels_tokens() -> list[str] | None:
    """Prompt for the required wheel release destination options."""
    origin = _prompt_for_selection(
        "Wheel release origin",
        [
            ("local", "Publish wheels already present on this host"),
            ("aws", "Retrieve wheels from the latest AWS S3 bucket"),
            ("azure", "Retrieve wheels from the latest Azure storage account"),
        ],
    )
    if origin is None:
        return None
    release = input("Release name or tag: ").strip()
    while not release:
        print("Release name or tag is required.")
        release = input("Release name or tag: ").strip()
    tokens = ["dev", "upload-wheels", "--origin", origin, "--release", release]
    if _prompt_yes_no("Dry run only?", default=False):
        tokens.append("--dry-run")
    return tokens


def _prompt_for_push_to_cloud_tokens() -> list[str] | None:
    """Prompt for a cloud wheel destination and release folder."""
    origin = _prompt_for_selection(
        "Wheel cloud destination",
        [
            ("aws", "Push wheels to the latest AWS S3 bucket"),
            ("azure", "Push wheels to the latest Azure storage account"),
        ],
    )
    if origin is None:
        return None
    release = input("Release name: ").strip()
    while not release:
        print("Release name is required.")
        release = input("Release name: ").strip()
    tokens = ["dev", "push-to-cloud", "--origin", origin, "--release", release]
    if _prompt_yes_no("Dry run only?", default=False):
        tokens.append("--dry-run")
    return tokens


def _prompt_for_build_tokens(available_components: list[str]) -> list[str] | None:
    """Prompt for one build-oriented command token sequence.

    Parameters
    ----------
    available_components:
        Discovered component keys that can be offered for named build, test,
        SBOM, or security operations.

    """
    command = _prompt_for_selection(
        "Build commands",
        [
            ("artefact", "Build wheel and source artefacts"),
            ("sbom", "Generate SBOMs"),
            ("secure", "Run security checks"),
            ("test", "Run unit, Playwright, or e2e tests"),
            ("pdf", "Generate the OpAMP PDF manual"),
            ("ui-compaction", "Build compacted provider web UI JavaScript assets"),
            ("js-complexity", "Run JavaScript and TypeScript cyclomatic-complexity checks"),
            ("docs", "Regenerate markdown quick references"),
            ("diagrams", "Render Mermaid diagrams to images"),
            ("release-assets", "Build release wheels, SBOMs, and optional GitHub assets"),
        ],
    )
    if command is None:
        return None
    if command in {"artefact", "sbom", "secure"}:
        return _prompt_for_named_or_all_tokens(
            command,
            available_components,
            include_no_isolation=command in {"artefact", "sbom"},
        )
    if command == "test":
        return _prompt_for_test_tokens(available_components)
    if command == "pdf":
        return _prompt_for_pdf_tokens()
    return _prompt_for_simple_build_tokens(command)


def _prompt_for_test_tokens(available_components: list[str]) -> list[str] | None:
    """Prompt for one test command token sequence."""
    test_scope = _prompt_for_selection(
        "Test scope",
        [
            ("named", "Run tests for one component"),
            ("all", "Run tests for all discovered components"),
            ("e2e", "Run end-to-end tests"),
        ],
    )
    if test_scope is None:
        return None
    tokens = ["build", "test", test_scope]
    if test_scope != "named":
        return tokens
    component = _prompt_for_component(available_components)
    if component is None:
        return None
    tokens.append(component)
    return tokens


def _prompt_for_pdf_tokens() -> list[str]:
    """Prompt for optional PDF build arguments."""
    output = input("Optional PDF output path (leave blank for default): ").strip()
    tokens = ["build", "pdf"]
    if output:
        tokens.extend(["--output", output])
    return tokens


def _prompt_for_simple_build_tokens(command: str) -> list[str]:
    """Return token sequences for single-step build commands."""
    if command == "js-complexity":
        return _prompt_for_js_complexity_tokens()
    return ["build", command]


def _prompt_for_js_complexity_tokens() -> list[str]:
    """Prompt for optional JavaScript/TypeScript complexity-check arguments."""
    tokens = ["build", "js-complexity"]
    max_complexity = input(
        f"Maximum cyclomatic complexity threshold (leave blank for {DEFAULT_MAX_COMPLEXITY}): "
    ).strip()
    if max_complexity:
        tokens.extend(["--max-complexity", max_complexity])
    raw_paths = input(
        "Optional file/folder path(s), comma-separated (leave blank for defaults): "
    ).strip()
    if raw_paths:
        for path in [item.strip() for item in raw_paths.split(",") if item.strip()]:
            tokens.extend(["--path", path])
    return tokens


def _prompt_for_certificate_tokens() -> list[str] | None:
    """Prompt for one certificate/auth helper command token sequence."""
    command = _prompt_for_selection(
        "Certificate commands",
        [
            ("generate", "Guide self-signed certificate creation"),
            ("ensure-provider-config", "Ensure provider.tls config exists in JSON"),
            ("keycloak", "Guide local Keycloak setup"),
        ],
    )
    if command is None:
        return None
    return ["certificate", command]


def _prompt_for_named_or_all_tokens(
    command: str,
    available_components: list[str],
    *,
    include_no_isolation: bool,
) -> list[str] | None:
    """Prompt for an ``all`` or ``named`` build subcommand selection.

    Parameters
    ----------
    command:
        Build subcommand being prepared, such as ``artefact`` or ``secure``.
    available_components:
        Discovered component keys that can be offered when named execution is
        available.
    include_no_isolation:
        Whether the prompt should ask if ``--no-isolation`` should be passed
        through to ``python -m build``.

    """
    scope_options = [("all", "Run against every discovered component")]
    if available_components:
        scope_options.insert(0, ("named", "Run against one component"))
    scope = _prompt_for_selection(f"{command} scope", scope_options)
    if scope is None:
        return None
    tokens = ["build", command]
    if include_no_isolation and _prompt_yes_no(
        "Pass --no-isolation to python -m build?",
        default=False,
    ):
        tokens.append("--no-isolation")
    tokens.append(scope)
    if scope == "named":
        component = _prompt_for_component(available_components)
        if component is None:
            return None
        tokens.append(component)
    return tokens


def _prompt_for_component(available_components: list[str]) -> str | None:
    """Prompt for one discovered component name.

    Parameters
    ----------
    available_components:
        Discovered component keys to display in the guided menu.

    """
    if not available_components:
        print("No build components were discovered.")
        return None
    return _prompt_for_selection(
        "Components",
        [(component, "") for component in available_components],
    )


def _prompt_for_selection(
    title: str,
    options: Sequence[tuple[str, str]],
) -> str | None:
    """Prompt for one selection by number or exact option text.

    Parameters
    ----------
    title:
        Menu title printed above the numbered options.
    options:
        Pairs of option value and human-readable description shown to the
        user.

    """
    while True:
        print(title + ":")
        for index, (value, description) in enumerate(options, start=1):
            suffix = f" - {description}" if description else ""
            print(f"  {index}. {value}{suffix}")
        print("  q. quit")
        response = input("Select an option: ").strip()
        if not response:
            print("Please choose one of the listed options.")
            continue
        normalized = response.lower()
        if normalized in {"q", "quit", "exit"}:
            return None
        if response.isdigit():
            selection = int(response) - 1
            if 0 <= selection < len(options):
                return options[selection][0]
        for value, _ in options:
            if normalized == value.lower():
                return value
        print("Please choose by number or exact option name.")


def _prompt_yes_no(prompt: str, *, default: bool) -> bool:
    """Prompt for one yes/no answer.

    Parameters
    ----------
    prompt:
        Human-readable question displayed to the user.
    default:
        Default boolean value applied when the user presses Enter without an
        explicit answer.

    """
    default_token = "Y/n" if default else "y/N"
    while True:
        response = input(f"{prompt} [{default_token}]: ").strip().lower()
        if not response:
            return default
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def _extract_repo_root_from_tokens(arg_tokens: Sequence[str]) -> Path | None:
    """Return an explicitly provided repo root, if present.

    Parameters
    ----------
    arg_tokens:
        Raw CLI tokens to inspect for ``--repo-root`` in either split or
        ``--repo-root=...`` form.

    """
    for index, argument in enumerate(arg_tokens):
        if argument == "--repo-root" and index + 1 < len(arg_tokens):
            return Path(arg_tokens[index + 1]).expanduser().resolve()
        if argument.startswith("--repo-root="):
            return Path(argument.partition("=")[2]).expanduser().resolve()
    return None


def _extract_global_option_tokens(arg_tokens: Sequence[str]) -> list[str]:
    """Return supported global CLI options in their original token form.

    Parameters
    ----------
    arg_tokens:
        Raw CLI tokens from which to preserve explicit global option values.

    """
    extracted: list[str] = []
    index = 0
    while index < len(arg_tokens):
        argument = arg_tokens[index]
        if argument in {"--repo-root", "--python"} and index + 1 < len(arg_tokens):
            extracted.extend([argument, arg_tokens[index + 1]])
            index += 2
            continue
        if argument.startswith("--repo-root=") or argument.startswith("--python="):
            extracted.append(argument)
            index += 1
            continue
        index += 1
    return extracted


def _has_command_tokens(arg_tokens: Sequence[str]) -> bool:
    """Return whether non-global command tokens were provided.

    Parameters
    ----------
    arg_tokens:
        Raw CLI tokens that may contain global options followed by a command
        path.

    """
    index = 0
    while index < len(arg_tokens):
        token = arg_tokens[index]
        if token in {"--repo-root", "--python"}:
            index += 2
            continue
        if token.startswith("--repo-root=") or token.startswith("--python="):
            index += 1
            continue
        return True
    return False


def _print_startup_context(*, repo_root: Path, used_default_repo_root: bool) -> None:
    """Display the repository root in use for the current CLI session.

    Parameters
    ----------
    repo_root:
        Repository root that will be used by the current CLI session.
    used_default_repo_root:
        Whether the root came from the launch directory instead of an
        explicit ``--repo-root`` argument.

    """
    if used_default_repo_root:
        print(f"Repository root: {repo_root} (current working directory)")
    else:
        print(f"Repository root: {repo_root}")


def _interactive_completion_message(exit_code: int) -> str:
    """Return the guided-mode completion message for one command run.

    Parameters
    ----------
    exit_code:
        Command exit code used to choose the appropriate guided-session
        status message.

    """
    if exit_code == 0:
        return INTERACTIVE_SUCCESS_MESSAGE
    if exit_code == DEFAULT_ISSUES_EXIT_CODE:
        return INTERACTIVE_ISSUES_MESSAGE
    return INTERACTIVE_FAILURE_MESSAGE


def _add_named_or_all_parsers(
    parser: argparse.ArgumentParser,
    *,
    noun: str,
    available_components: list[str],
) -> None:
    """Add ``named`` and ``all`` subparsers to one build parser.

    Parameters
    ----------
    parser:
        Parent parser that owns the subcommand being extended.
    noun:
        Singular noun used in help text for the named/all options.
    available_components:
        Discovered component keys that can be chosen for named execution.

    """
    subparsers = parser.add_subparsers(dest="scope", required=True)
    named_parser = subparsers.add_parser("named", help=f"Run against one {noun}")
    named_parser.add_argument(
        "component",
        choices=available_components,
        help="Component directory name",
    )
    subparsers.add_parser("all", help=f"Run against every discovered {noun}")


def _command_slug_from_args(args: argparse.Namespace) -> str:
    """Build a stable log-file slug from the parsed command hierarchy.

    Parameters
    ----------
    args:
        Parsed CLI arguments whose command tokens should be combined into a
        filesystem-safe log filename stem.

    """
    tokens = [
        getattr(args, "command_group", ""),
        getattr(args, "dev_command", ""),
        getattr(args, "set_command", ""),
        getattr(args, "sync_command", ""),
        getattr(args, "apply_command", ""),
        getattr(args, "build_command", ""),
        getattr(args, "scope", ""),
        getattr(args, "test_scope", ""),
        getattr(args, "certificate_command", ""),
    ]
    return "-".join(token for token in tokens if token)


if __name__ == "__main__":
    raise SystemExit(main())
