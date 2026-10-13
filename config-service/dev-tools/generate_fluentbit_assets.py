#!/usr/bin/env python3
# Copyright 2026 mp3monster.org
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generate, reconcile, enrich, and compile versioned Fluent Bit artifacts."""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_SERVICE_ROOT = REPO_ROOT / "config-service"
SRC_ROOT = CONFIG_SERVICE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# Developer tools load sibling scripts and the source package after establishing local paths.
# pylint: disable=wrong-import-position
import add_fluentbit_processors  # noqa: E402
import generate_runtime_schemas  # noqa: E402
from config_service.configuration_backup import create_configuration_backup  # noqa: E402
from config_service.fluentbit_catalog_reconciliation import (  # noqa: E402
    reconcile_catalogs,
    select_previous_version,
    write_summary_files,
)
from config_service.fluentbit_docs_support import (  # noqa: E402
    build_catalog_from_docs,
    resolve_current_stable_version,
)
from config_service.json_artifacts import load_json_artifact  # noqa: E402

LOGGER = logging.getLogger("generate_fluentbit_assets")
PACKAGE_ROOT = SRC_ROOT / "config_service"
DEFINITIONS_DIR = PACKAGE_ROOT / "json-definitions"
SCHEMAS_DIR = PACKAGE_ROOT / "json-schemas"
CATALOG_REGISTRY_PATH = PACKAGE_ROOT / "config" / "catalog-registry.json"
SERVICE_REGISTRY_PATH = PACKAGE_ROOT / "config" / "service-registry.json"
PARSER_REGISTRY_PATH = PACKAGE_ROOT / "config" / "parser-registry.json"
DEFAULT_SUMMARY_DIR = CONFIG_SERVICE_ROOT / "reports" / "fluentbit"
DEFAULT_BACKUP_DIR = CONFIG_SERVICE_ROOT / "backups"
KEY_CATALOGS_BY_TYPE = "catalogs_by_type"
KEY_DEFAULT_CHANGED = "default_changed"
KEY_DEFAULT_VERSIONS = "default_versions"
KEY_FLUENTBIT = "fluentbit"
KEY_PATH = "path"
KEY_PREVIOUS_DEFAULT = "previous_default"
KEY_REGISTRY_CHANGES = "registry_changes"
KEY_REMOVED_PATHS = "removed_paths"
KEY_REMOVED_REFERENCE = "removed_reference"
KEY_REPLACEMENT_DEFAULT = "replacement_default"
KEY_VERSION = "version"
KEY_BACKUP_PATH = "backup_path"
KEY_ACTION = "action"
KEY_PARSER_DEFINITIONS_BY_TYPE = "parser_definitions_by_type"
KEY_SERVICE_DEFINITIONS_BY_TYPE = "service_definitions_by_type"
ACTION_REMOVE_VERSION = "remove_fluentbit_version"
REMOVAL_SUMMARY_SUFFIX = "removal_summary"
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
def _write_json(path: Path, payload: dict) -> None:
    """Write one deterministic, human-readable JSON artifact to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _artifact_filename(version: str) -> str:
    """Build the stable top-level catalog filename for one Fluent Bit version."""
    return f"fluent-bit-{version}-all-plugins-catalog.json"


def _registry_ref(version: str) -> str:
    """Build the catalog-registry reference for one Fluent Bit version."""
    return f"json-definitions/{_artifact_filename(version)}"


def _registry_specs() -> tuple[tuple[Path, str], ...]:
    """Return every registry and Fluent Bit mapping changed during removal."""
    return (
        (CATALOG_REGISTRY_PATH, KEY_CATALOGS_BY_TYPE),
        (SERVICE_REGISTRY_PATH, KEY_SERVICE_DEFINITIONS_BY_TYPE),
        (PARSER_REGISTRY_PATH, KEY_PARSER_DEFINITIONS_BY_TYPE),
    )


def _validate_version_for_removal(version: str) -> str:
    """Validate and return a removal version that cannot escape artifact roots."""
    normalized_version = version.strip()
    if VERSION_PATTERN.fullmatch(normalized_version) is None:
        raise ValueError(
            "Fluent Bit removal versions must use semantic version form, for example 5.1.3."
        )
    return normalized_version


def _removal_artifact_paths(version: str) -> tuple[Path, ...]:
    """Return all canonical generated artifacts owned by one Fluent Bit version."""
    return (
        DEFINITIONS_DIR / _artifact_filename(version),
        DEFINITIONS_DIR / f"fluent-bit-{version}-service-options.json",
        DEFINITIONS_DIR / f"fluent-bit-{version}-parser-options.json",
        DEFINITIONS_DIR / "fluent-bit" / version,
        SCHEMAS_DIR / f"fluentbit-{version}-config-schema.json",
        SCHEMAS_DIR / "fluentbit" / version,
    )


# Registry staging keeps all validation state in memory so no file changes before validation.
# pylint: disable=too-many-locals
def _prepare_registry_removal(
    version: str,
    *,
    replacement_default: str | None,
) -> tuple[list[tuple[Path, dict[str, Any]]], list[dict[str, Any]], bool]:
    """Validate and stage registry changes without writing them.

    Parameters
    ----------
    version:
        Fluent Bit version whose registry entries will be removed.
    replacement_default:
        Explicit new default required when ``version`` is a current default.

    Returns
    -------
    tuple
        Updated registry payloads, report entries, and whether any entry existed.
    """
    staged_payloads: list[tuple[Path, dict[str, Any]]] = []
    registry_changes: list[dict[str, Any]] = []
    found_registry_entry = False
    changed_default = False
    normalized_replacement = (
        _validate_version_for_removal(replacement_default)
        if replacement_default is not None
        else None
    )

    for registry_path, mapping_key in _registry_specs():
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        mappings_by_type = payload.get(mapping_key, {})
        fluentbit_mappings = (
            mappings_by_type.get(KEY_FLUENTBIT, {})
            if isinstance(mappings_by_type, dict)
            else {}
        )
        if not isinstance(fluentbit_mappings, dict):
            expected_mapping = f"{mapping_key}.{KEY_FLUENTBIT}"
            raise ValueError(
                f"Registry '{registry_path}' must define {expected_mapping} as an object."
            )

        removed_reference = fluentbit_mappings.get(version)
        found_registry_entry = found_registry_entry or removed_reference is not None
        default_versions = payload.get(KEY_DEFAULT_VERSIONS, {})
        current_default = (
            default_versions.get(KEY_FLUENTBIT)
            if isinstance(default_versions, dict)
            else None
        )
        default_changed = current_default == version
        if default_changed:
            changed_default = True
            if normalized_replacement is None:
                raise ValueError(
                    f"Fluent Bit {version} is a default in '{registry_path.name}'; "
                    "provide --replacement-default with a registered version."
                )
            replacement_is_invalid = normalized_replacement == version
            replacement_is_missing = normalized_replacement not in fluentbit_mappings
            if replacement_is_invalid or replacement_is_missing:
                raise ValueError(
                    f"Replacement default {normalized_replacement} is not registered in "
                    f"'{registry_path.name}'."
                )
            default_versions[KEY_FLUENTBIT] = normalized_replacement

        fluentbit_mappings.pop(version, None)
        staged_payloads.append((registry_path, payload))
        registry_changes.append(
            {
                KEY_PATH: str(registry_path.relative_to(PACKAGE_ROOT)),
                KEY_REMOVED_REFERENCE: removed_reference,
                KEY_DEFAULT_CHANGED: default_changed,
                KEY_PREVIOUS_DEFAULT: current_default,
                KEY_REPLACEMENT_DEFAULT: normalized_replacement if default_changed else None,
            }
        )

    if normalized_replacement is not None and not changed_default:
        raise ValueError(
            "--replacement-default is only valid when the removed version is a current default."
        )
    return staged_payloads, registry_changes, found_registry_entry


def _write_removal_summary(
    summary_dir: Path,
    payload: dict[str, Any],
    *,
    version: str,
) -> tuple[Path, Path]:
    """Write machine-readable and human-readable Fluent Bit removal reports."""
    version_slug = version.replace(".", "_").replace("-", "_").replace("+", "_")
    summary_stem = f"fluentbit_{version_slug}_{REMOVAL_SUMMARY_SUFFIX}"
    json_path = summary_dir / f"{summary_stem}.json"
    markdown_path = summary_dir / f"{summary_stem}.md"
    _write_json(json_path, payload)

    removed_paths = payload[KEY_REMOVED_PATHS]
    registry_changes = payload[KEY_REGISTRY_CHANGES]
    markdown_lines = [
        f"# Fluent Bit {version} Removal Summary",
        "",
        f"- Backup: `{payload[KEY_BACKUP_PATH]}`",
        f"- Replacement default: `{payload[KEY_REPLACEMENT_DEFAULT] or 'not required'}`",
        "",
        "## Removed artifacts",
        "",
    ]
    markdown_lines.extend(
        [f"- `{removed_path}`" for removed_path in removed_paths]
        or ["- No generated artifacts were present."]
    )
    markdown_lines.extend(["", "## Registry changes", ""])
    for registry_change in registry_changes:
        removed_reference = registry_change[KEY_REMOVED_REFERENCE] or "not registered"
        markdown_lines.append(
            f"- `{registry_change[KEY_PATH]}`: removed `{removed_reference}`; "
            f"default changed: `{registry_change[KEY_DEFAULT_CHANGED]}`"
        )
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")
    return json_path, markdown_path


# Removal records each artifact and registry mutation for the audit summary.
# pylint: disable=too-many-locals
def remove_version(
    version: str,
    *,
    replacement_default: str | None,
    summary_dir: Path,
    backup_path: Path,
) -> tuple[Path, Path]:
    """Remove one Fluent Bit version from canonical artifacts and registries.

    Parameters
    ----------
    version:
        Fluent Bit version to remove.
    replacement_default:
        New registered default when the removed version is currently a default.
    summary_dir:
        Directory receiving JSON and Markdown removal reports.
    backup_path:
        Completed pre-removal ZIP archive recorded in the reports.

    Returns
    -------
    tuple[Path, Path]
        JSON and Markdown removal-summary paths.
    """
    normalized_version = _validate_version_for_removal(version)
    normalized_replacement = (
        _validate_version_for_removal(replacement_default)
        if replacement_default is not None
        else None
    )
    staged_payloads, registry_changes, found_registry_entry = _prepare_registry_removal(
        normalized_version,
        replacement_default=normalized_replacement,
    )
    artifact_paths = _removal_artifact_paths(normalized_version)
    existing_artifact_paths = [path for path in artifact_paths if path.exists()]
    if not found_registry_entry and not existing_artifact_paths:
        raise FileNotFoundError(
            f"No canonical Fluent Bit configuration exists for version {normalized_version}."
        )

    removed_paths: list[str] = []
    for artifact_path in existing_artifact_paths:
        if artifact_path.is_dir():
            shutil.rmtree(artifact_path)
        else:
            artifact_path.unlink()
        removed_paths.append(str(artifact_path.relative_to(PACKAGE_ROOT)))

    for registry_path, registry_payload in staged_payloads:
        _write_json(registry_path, registry_payload)

    summary_payload = {
        KEY_ACTION: ACTION_REMOVE_VERSION,
        KEY_VERSION: normalized_version,
        KEY_BACKUP_PATH: str(backup_path),
        KEY_REPLACEMENT_DEFAULT: normalized_replacement,
        KEY_REMOVED_PATHS: removed_paths,
        KEY_REGISTRY_CHANGES: registry_changes,
    }
    summary_paths = _write_removal_summary(
        summary_dir,
        summary_payload,
        version=normalized_version,
    )
    LOGGER.info(
        "removed fluent bit configuration version=%s artifacts=%s summaries=%s",
        normalized_version,
        len(removed_paths),
        summary_paths,
    )
    return summary_paths


def _update_catalog_registry(version: str) -> None:
    """Register a generated Fluent Bit catalog in the editable registry."""
    payload = json.loads(CATALOG_REGISTRY_PATH.read_text(encoding="utf-8"))
    catalogs = payload.setdefault(KEY_CATALOGS_BY_TYPE, {}).setdefault(KEY_FLUENTBIT, {})
    catalogs[version] = _registry_ref(version)
    CATALOG_REGISTRY_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _catalog_registry_entries() -> dict[str, str]:
    """Load Fluent Bit version-to-artifact mappings from the local registry."""
    registry_payload = json.loads(CATALOG_REGISTRY_PATH.read_text(encoding="utf-8"))
    catalogs_by_type = registry_payload.get(KEY_CATALOGS_BY_TYPE, {})
    if not isinstance(catalogs_by_type, dict):
        return {}
    fluentbit_catalogs = catalogs_by_type.get(KEY_FLUENTBIT, {})
    if not isinstance(fluentbit_catalogs, dict):
        return {}
    return {
        str(version): str(reference)
        for version, reference in fluentbit_catalogs.items()
        if str(version).strip() and str(reference).strip()
    }


def _resolve_catalog_path(version: str, registry_entries: dict[str, str]) -> Path | None:
    """Resolve an assembled catalog manifest from the canonical packaged artifacts."""
    relative_reference = registry_entries.get(version, _registry_ref(version))
    candidate_path = PACKAGE_ROOT / relative_reference
    return candidate_path if candidate_path.is_file() else None


def _load_previous_catalog(
    target_version: str,
    *,
    requested_version: str | None,
) -> tuple[str | None, dict[str, Any] | None]:
    """Load the requested or nearest earlier catalog used for reconciliation.

    Parameters
    ----------
    target_version:
        Fluent Bit version being scraped.
    requested_version:
        Explicit fallback version, or ``None`` to select the nearest earlier
        version registered locally.

    Returns
    -------
    tuple[str or None, dict or None]
        Resolved version label and assembled catalog payload.
    """
    registry_entries = _catalog_registry_entries()
    previous_version = requested_version or select_previous_version(
        target_version,
        registry_entries.keys(),
    )
    if previous_version is None:
        return None, None
    previous_path = _resolve_catalog_path(previous_version, registry_entries)
    if previous_path is None:
        if requested_version:
            raise FileNotFoundError(
                f"Previous Fluent Bit catalog '{previous_version}' is not available locally."
            )
        LOGGER.warning(
            "previous fluent bit catalog is registered but unavailable version=%s",
            previous_version,
        )
        return None, None
    previous_payload = load_json_artifact(previous_path)
    if not isinstance(previous_payload, dict):
        raise ValueError(f"Previous Fluent Bit catalog must be an object: {previous_path}")
    return previous_version, previous_payload


# The keyword-only arguments intentionally mirror independently selectable command-line options.
# pylint: disable=too-many-arguments,too-many-locals
def generate_version(
    version: str,
    *,
    source: str,
    timeout: int,
    github_ref: str | None,
    register: bool,
    generate_schemas_flag: bool,
    inherit_previous: bool = True,
    previous_version: str | None = None,
    summary_dir: Path = DEFAULT_SUMMARY_DIR,
) -> None:
    """Scrape, reconcile, enrich, report, and optionally compile one catalog.

    Parameters
    ----------
    version:
        Fluent Bit version to generate.
    source:
        Documentation source selector accepted by the scraper.
    timeout:
        HTTP timeout in seconds.
    github_ref:
        Optional GitHub documentation ref override.
    register:
        Whether to update the editable catalog registry.
    generate_schemas_flag:
        Whether to compile runtime schemas after catalog generation.
    inherit_previous:
        Whether undetermined metadata can use the previous local catalog.
    previous_version:
        Explicit fallback version, or ``None`` for automatic selection.
    summary_dir:
        Directory receiving JSON and Markdown reconciliation reports.
    """
    LOGGER.info("building fluent bit catalog version=%s source=%s", version, source)
    resolved_previous_version: str | None = None
    previous_payload: dict[str, Any] | None = None
    if inherit_previous:
        resolved_previous_version, previous_payload = _load_previous_catalog(
            version,
            requested_version=previous_version,
        )
    payload = build_catalog_from_docs(
        version,
        source=source,
        timeout=timeout,
        github_ref=github_ref,
        logger=LOGGER,
    )
    payload, summary = reconcile_catalogs(
        payload,
        previous_payload,
        previous_version=resolved_previous_version,
    )
    json_summary_path, markdown_summary_path = write_summary_files(
        summary,
        summary_dir,
        target_version=version,
    )
    LOGGER.info(
        "wrote fluent bit scrape summaries json=%s markdown=%s previous_version=%s",
        json_summary_path,
        markdown_summary_path,
        resolved_previous_version,
    )
    filename = _artifact_filename(version)
    catalog_path = DEFINITIONS_DIR / filename
    _write_json(catalog_path, payload)

    add_fluentbit_processors.update_catalog(
        catalog_path,
        timeout=timeout,
        logger=LOGGER,
        page_cache={},
    )

    if register:
        _update_catalog_registry(version)
        LOGGER.info("registered fluent bit catalog version=%s", version)

    if generate_schemas_flag:
        generate_runtime_schemas.generate_runtime_schemas(
            config_types=["fluentbit"],
            versions=[version],
        )
        LOGGER.info("generated runtime schemas version=%s", version)


def parse_args() -> argparse.Namespace:
    """Parse Fluent Bit scraper, reconciliation, and artifact options."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate or remove versioned Fluent Bit catalog and runtime-schema assets. "
            "Generation supports the docs website, the fluent-bit-docs GitHub repo, or "
            "automatic fallback."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    operation_group = parser.add_mutually_exclusive_group()
    operation_group.add_argument(
        "--version",
        action="append",
        dest="versions",
        help=(
            "Fluent Bit version to generate. Repeat for multiple versions; "
            "omit both operations to generate the current stable release."
        ),
    )
    operation_group.add_argument(
        "--remove-version",
        help="Fluent Bit version to remove from canonical artifacts and registries.",
    )
    parser.add_argument(
        "--replacement-default",
        help="Registered version to make the default when removing a current default.",
    )
    parser.add_argument(
        "--source",
        choices=("auto", "website", "github"),
        default="auto",
        help="Documentation source to scrape.",
    )
    parser.add_argument(
        "--github-ref",
        help="Optional GitHub branch/tag/ref to use when --source github or auto prefers GitHub.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="HTTP timeout in seconds for docs fetches.",
    )
    parser.add_argument(
        "--no-register",
        action="store_true",
        help="Do not update the packaged config/catalog-registry.json.",
    )
    parser.add_argument(
        "--no-schemas",
        action="store_true",
        help="Do not generate runtime schemas after writing catalogs.",
    )
    parser.add_argument(
        "--previous-version",
        help=(
            "Use this local Fluent Bit catalog for missing metadata instead of auto-selecting "
            "the nearest earlier version."
        ),
    )
    parser.add_argument(
        "--no-inherit",
        action="store_true",
        help="Do not carry forward undetermined metadata from an earlier local catalog.",
    )
    parser.add_argument(
        "--summary-dir",
        type=Path,
        default=DEFAULT_SUMMARY_DIR,
        help="Directory for JSON and Markdown scrape summary reports.",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help="Directory for the mandatory pre-change configuration ZIP backup.",
    )
    parsed_args = parser.parse_args()
    if parsed_args.replacement_default and not parsed_args.remove_version:
        parser.error("--replacement-default can only be used with --remove-version")
    return parsed_args


def main() -> None:
    """Back up configuration, then generate or remove requested Fluent Bit assets."""
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
    versions = args.versions
    if not args.remove_version and not versions:
        versions = [resolve_current_stable_version(timeout=args.timeout)]
        LOGGER.info("resolved current stable Fluent Bit version=%s", versions[0])
    backup_path = create_configuration_backup(PACKAGE_ROOT, args.backup_dir)
    LOGGER.info("created configuration backup path=%s", backup_path)
    if args.remove_version:
        remove_version(
            args.remove_version,
            replacement_default=args.replacement_default,
            summary_dir=args.summary_dir,
            backup_path=backup_path,
        )
        return
    for version in versions or []:
        generate_version(
            version,
            source=args.source,
            timeout=args.timeout,
            github_ref=args.github_ref,
            register=not args.no_register,
            generate_schemas_flag=not args.no_schemas,
            inherit_previous=not args.no_inherit,
            previous_version=args.previous_version,
            summary_dir=args.summary_dir,
        )


if __name__ == "__main__":
    main()
