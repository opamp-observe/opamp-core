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

"""Enrich generated Fluent Bit plugin catalogs for use by config-service.

This module is the post-processing stage of the Fluent Bit asset-generation
pipeline. ``generate_fluentbit_assets.py`` first gathers versioned plugin
metadata from the Fluent Bit documentation, then calls :func:`update_catalog`
here to add metadata that cannot be derived reliably from individual plugin
pages. That enrichment includes shared processor definitions, router fields,
and canonical plugin names.

The resulting catalog manifests and per-plugin shards are source metadata for
the wider OpAMP solution. Config-service loads them to build its browser editor,
validate user configurations, and render native Fluent Bit YAML. The runtime
schema and documentation generators also consume the enriched catalogs, so this
module keeps those generated views aligned with the editor's model.

The script can also be run directly to reprocess existing local catalogs in
the canonical packaged source tree under ``src/config_service``.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "config-service" / "src"
DEFINITIONS_DIR = SRC_ROOT / "config_service" / "json-definitions"
# Allow this developer script to import config-service directly from a source checkout.
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config_service.fluentbit_docs_support import normalize_plugin_map  # noqa: E402
from config_service.json_artifacts import (  # noqa: E402
    KEY_FILE,
    KEY_PAYLOAD,
    KEY_POINTER,
    load_json_artifact,
    write_manifest_json_artifact,
)

LOG_LEVELS = ["off", "trace", "debug", "info", "warn", "error"]
DEFAULT_TIMEOUT = 20
LOGGER = logging.getLogger("add_fluentbit_processors")


def field(
    name: str,
    *,
    description: str,
    reference: str,
    data_type: str = "string",
    required: bool = False,
    default: Any | None = None,
    validation_rule: dict[str, Any] | None = None,
    enum_options: list[str] | None = None,
) -> dict[str, Any]:
    """Build one catalog field descriptor used by the editor and validators.

    Parameters
    ----------
    name:
        Native Fluent Bit property name represented by the field.
    description:
        Human-readable explanation shown by catalog-driven interfaces.
    reference:
        Fluent Bit documentation URL that defines the property.
    data_type:
        Logical editor type used to choose controls and schema conversion.
    required:
        Whether configurations must provide the property.
    default:
        Optional default copied into generated catalog metadata.
    validation_rule:
        Optional structured constraint consumed by validation and schema generation.
    enum_options:
        Optional choices used by enum controls and schema generation.

    Returns
    -------
    dict[str, Any]
        A catalog field payload with optional values omitted when not configured.

    """
    payload: dict[str, Any] = {
        "name": name,
        "required": required,
        "description": description,
        "reference": reference,
        "data_type": data_type,
        "validation_rule": validation_rule,
    }
    if default is not None:
        payload["default"] = default
    if enum_options:
        payload["enum_options"] = enum_options
    return payload


def processor_def(
    *,
    title: str,
    doc_url: str,
    description: str,
    fields: list[dict[str, Any]],
    supports_condition: bool = False,
) -> dict[str, Any]:
    """Build a shared processor descriptor for one telemetry signal.

    Parameters
    ----------
    title:
        Fluent Bit processor name written into YAML.
    doc_url:
        Upstream documentation page for the processor.
    description:
        Summary presented by catalog-driven UI and documentation.
    fields:
        Processor options constructed with :func:`field`.
    supports_condition:
        Whether this processor can include a conditional processing block.

    Returns
    -------
    dict[str, Any]
        Processor metadata ready for placement under ``common.processors``.

    """
    return {
        "title": title,
        "doc_url": doc_url,
        "description": description,
        "fields": fields,
        "supports_condition": supports_condition,
    }


def condition_object(reference: str) -> dict[str, Any]:
    """Describe the reusable conditional block supported by newer processors.

    Parameters
    ----------
    reference:
        Fluent Bit documentation URL for conditional processing semantics.

    Returns
    -------
    dict[str, Any]
        Catalog metadata for the condition operator and rule list.

    """
    return {
        "title": "condition",
        "description": "Optional conditional processing block for logs processors.",
        "reference": reference,
        "fields": [
            field(
                "op",
                description="How to evaluate the condition rules.",
                reference=reference,
                data_type="enum",
                required=True,
                validation_rule={"kind": "enum", "values": ["and", "or"]},
                enum_options=["and", "or"],
            ),
            field(
                "rules",
                description="Array of condition rules expressed as JSON objects with field, op, and value keys.",
                reference=reference,
                data_type="list",
                required=True,
                validation_rule={"kind": "list"},
            ),
        ],
    }


def processors_definition(version: str) -> dict[str, Any]:
    """Create version-aware processor metadata for logs, metrics, and traces.

    Parameters
    ----------
    version:
        Fluent Bit version whose feature compatibility should be represented.

    Returns
    -------
    dict[str, Any]
        Shared processor catalog attached to ``common.processors``.

    Notes
    -----
    Fluent Bit 3.2.10 does not receive conditional processor metadata. Keeping
    that distinction here prevents the UI from emitting unsupported YAML while
    allowing newer catalogs to expose the feature.

    """
    base_ref = "https://docs.fluentbit.io/manual/data-pipeline/processors"
    content_ref = "https://docs.fluentbit.io/manual/data-pipeline/processors/content-modifier"
    labels_ref = "https://docs.fluentbit.io/manual/data-pipeline/processors/labels"
    metrics_ref = "https://docs.fluentbit.io/manual/data-pipeline/processors/metrics-selector"
    otel_ref = "https://docs.fluentbit.io/manual/data-pipeline/processors/opentelemetry-envelope"
    sampling_ref = "https://docs.fluentbit.io/manual/data-pipeline/processors/sampling"
    sql_ref = "https://docs.fluentbit.io/manual/data-pipeline/processors/sql"
    filters_ref = "https://docs.fluentbit.io/manual/data-pipeline/processors/filters"
    c2d_ref = "https://docs.fluentbit.io/manual/4.2/data-pipeline/processors/cumulative-to-delta"
    tda_ref = "https://docs.fluentbit.io/manual/data-pipeline/processors/tda"

    supports_condition = version != "3.2.10"

    return {
        "description": "Shared Fluent Bit processors available to input and output plugins in YAML configuration.",
        "yaml_only": True,
        "supported_sections": ["inputs", "outputs"],
        "condition": condition_object("https://docs.fluentbit.io/manual/data-pipeline/processors/conditional-processing")
        if supports_condition
        else None,
        "signals": {
            "logs": {
                "allow_filters_as_processors": True,
                "processors": {
                    "content_modifier": processor_def(
                        title="content_modifier",
                        doc_url=content_ref,
                        description="Manipulates log or trace content and attributes.",
                        fields=[
                            field(
                                "action",
                                description="Content modifier action to perform.",
                                reference=content_ref,
                                data_type="enum",
                                required=True,
                                validation_rule={"kind": "enum", "values": ["convert", "delete", "extract", "hash", "insert", "rename", "upsert"]},
                                enum_options=["convert", "delete", "extract", "hash", "insert", "rename", "upsert"],
                            ),
                            field(
                                "context",
                                description="Context where the modification is applied.",
                                reference=content_ref,
                                data_type="enum",
                                required=True,
                                validation_rule={"kind": "enum", "values": ["attributes", "body", "otel_resource_attributes", "otel_scope_name", "otel_scope_version", "otel_scope_attributes", "otel_log_attributes"]},
                                enum_options=["attributes", "body", "otel_resource_attributes", "otel_scope_name", "otel_scope_version", "otel_scope_attributes", "otel_log_attributes"],
                            ),
                            field("key", description="Key targeted by the action.", reference=content_ref),
                            field("value", description="Value used by the action.", reference=content_ref),
                            field("pattern", description="Regular expression used by the extract action.", reference=content_ref),
                            field(
                                "converted_type",
                                description="Target type used by the convert action.",
                                reference=content_ref,
                                data_type="enum",
                                validation_rule={"kind": "enum", "values": ["string", "boolean", "int", "double"]},
                                enum_options=["string", "boolean", "int", "double"],
                            ),
                        ],
                        supports_condition=supports_condition,
                    ),
                    "opentelemetry_envelope": processor_def(
                        title="opentelemetry_envelope",
                        doc_url=otel_ref,
                        description="Wraps logs into an OpenTelemetry-compatible schema envelope.",
                        fields=[],
                        supports_condition=False,
                    ),
                    "sql": processor_def(
                        title="sql",
                        doc_url=sql_ref,
                        description="Runs a SQL query against the log stream.",
                        fields=[
                            field(
                                "query",
                                description="SQL statement executed against STREAM and ending with a semicolon.",
                                reference=sql_ref,
                                required=True,
                                data_type="code",
                                validation_rule={
                                    "kind": "code_syntax",
                                    "language": "sql",
                                    "parser": "lark",
                                    "dialect": "fluentbit_processor_sql",
                                },
                            ),
                        ],
                        supports_condition=False,
                    ),
                },
            },
            "metrics": {
                "allow_filters_as_processors": False,
                "processors": {
                    "labels": processor_def(
                        title="labels",
                        doc_url=labels_ref,
                        description="Manipulates labels on metrics.",
                        fields=[
                            field("insert", description="Insert operation expressed as 'key value'.", reference=labels_ref),
                            field("update", description="Update operation expressed as 'key value'.", reference=labels_ref),
                            field("upsert", description="Upsert operation expressed as 'key value'.", reference=labels_ref),
                            field("delete", description="Delete operation expressed as a label key.", reference=labels_ref),
                            field("hash", description="Hash operation expressed as a label key.", reference=labels_ref),
                        ],
                    ),
                    "metrics_selector": processor_def(
                        title="metrics_selector",
                        doc_url=metrics_ref,
                        description="Includes or excludes metrics using metric name and label matching.",
                        fields=[
                            field(
                                "action",
                                description="Whether matching metrics are included or excluded.",
                                reference=metrics_ref,
                                data_type="enum",
                                required=True,
                                validation_rule={"kind": "enum", "values": ["INCLUDE", "EXCLUDE"]},
                                enum_options=["INCLUDE", "EXCLUDE"],
                            ),
                            field(
                                "context",
                                description="Matching context.",
                                reference=metrics_ref,
                                data_type="enum",
                                required=True,
                                validation_rule={"kind": "enum", "values": ["metric_name", "delete_label_value"]},
                                enum_options=["metric_name", "delete_label_value"],
                            ),
                            field("metric_name", description="Metric name or regex used by the match operation.", reference=metrics_ref),
                            field("label", description="Label key/value pair used by delete_label_value matching.", reference=metrics_ref),
                            field(
                                "operation_type",
                                description="Metric-name matching mode.",
                                reference=metrics_ref,
                                data_type="enum",
                                validation_rule={"kind": "enum", "values": ["PREFIX", "SUBSTRING"]},
                                enum_options=["PREFIX", "SUBSTRING"],
                            ),
                        ],
                    ),
                    "cumulative_to_delta": processor_def(
                        title="cumulative_to_delta",
                        doc_url=c2d_ref,
                        description="Converts cumulative monotonic metrics to delta values.",
                        fields=[
                            field("drop_first", description="Compatibility option for first-sample handling when initial_value is unset.", reference=c2d_ref, data_type="boolean", default=True, validation_rule={"kind": "boolean"}),
                            field("drop_on_reset", description="Drop a sample when a reset is detected.", reference=c2d_ref, data_type="boolean", default=True, validation_rule={"kind": "boolean"}),
                            field(
                                "initial_value",
                                description="How the first sample for a new series is handled.",
                                reference=c2d_ref,
                                data_type="enum",
                                validation_rule={"kind": "enum", "values": ["auto", "keep", "drop"]},
                                enum_options=["auto", "keep", "drop"],
                            ),
                            field("max_series", description="Maximum number of series tracked in memory.", reference=c2d_ref, data_type="integer", default=65536, validation_rule={"kind": "range", "min": 0}),
                            field("max_staleness", description="How long to retain per-series state.", reference=c2d_ref, data_type="time", default="1h"),
                        ],
                    ),
                    "tda": processor_def(
                        title="tda",
                        doc_url=tda_ref,
                        description="Applies topological data analysis over a sliding window of metrics.",
                        fields=[
                            field("window_size", description="Number of samples kept in the sliding window.", reference=tda_ref, data_type="integer", default=60, validation_rule={"kind": "range", "min": 1}),
                            field("min_points", description="Minimum number of samples required before analysis runs.", reference=tda_ref, data_type="integer", default=10, validation_rule={"kind": "range", "min": 1}),
                            field("embed_dim", description="Delay embedding dimension.", reference=tda_ref, data_type="integer", default=3, validation_rule={"kind": "range", "min": 1}),
                            field("embed_delay", description="Embedding delay in samples.", reference=tda_ref, data_type="integer", default=1, validation_rule={"kind": "range", "min": 1}),
                            field("threshold", description="Distance threshold quantile or 0 for automatic scan.", reference=tda_ref, data_type="number", default=0, validation_rule={"kind": "range", "min": 0, "max": 1}),
                        ],
                    ),
                },
            },
            "traces": {
                "allow_filters_as_processors": False,
                "processors": {
                    "content_modifier": processor_def(
                        title="content_modifier",
                        doc_url=content_ref,
                        description="Manipulates trace span content and attributes.",
                        fields=[
                            field(
                                "action",
                                description="Content modifier action to perform.",
                                reference=content_ref,
                                data_type="enum",
                                required=True,
                                validation_rule={"kind": "enum", "values": ["convert", "delete", "extract", "hash", "insert", "rename", "upsert"]},
                                enum_options=["convert", "delete", "extract", "hash", "insert", "rename", "upsert"],
                            ),
                            field(
                                "context",
                                description="Trace context where the modification is applied.",
                                reference=content_ref,
                                data_type="enum",
                                required=True,
                                validation_rule={"kind": "enum", "values": ["span_name", "span_kind", "span_status", "span_attributes"]},
                                enum_options=["span_name", "span_kind", "span_status", "span_attributes"],
                            ),
                            field("key", description="Key targeted by the action.", reference=content_ref),
                            field("value", description="Value used by the action.", reference=content_ref),
                            field("pattern", description="Regular expression used by the extract action.", reference=content_ref),
                            field(
                                "converted_type",
                                description="Target type used by the convert action.",
                                reference=content_ref,
                                data_type="enum",
                                validation_rule={"kind": "enum", "values": ["string", "boolean", "int", "double"]},
                                enum_options=["string", "boolean", "int", "double"],
                            ),
                        ],
                    ),
                    "sampling": processor_def(
                        title="sampling",
                        doc_url=sampling_ref,
                        description="Applies probabilistic or tail sampling to trace telemetry.",
                        fields=[
                            field(
                                "type",
                                description="Sampling mode.",
                                reference=sampling_ref,
                                data_type="enum",
                                required=True,
                                validation_rule={"kind": "enum", "values": ["probabilistic", "tail"]},
                                enum_options=["probabilistic", "tail"],
                            ),
                            field("debug", description="Enable sampling debug output.", reference=sampling_ref, data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                            field("sampling_settings", description="Sampling settings object, such as percentage or decision_wait.", reference=sampling_ref, data_type="map", validation_rule={"kind": "map"}),
                            field("conditions", description="Array of tail-sampling condition objects.", reference=sampling_ref, data_type="list", validation_rule={"kind": "list"}),
                        ],
                    ),
                },
            },
        },
        "references": {
            "processors": base_ref,
            "filters_as_processors": filters_ref,
        },
    }


def _version_requires_input_tags(version: str) -> bool:
    """Return whether input tags must be explicit for the selected catalog version.

    Parameters
    ----------
    version:
        Fluent Bit semantic version read from the catalog.

    """
    return str(version).startswith(("3.", "4."))


def _router_reference(payload: dict[str, Any], version: str) -> str:
    """Resolve the best upstream router documentation URL for a catalog.

    Parameters
    ----------
    payload:
        Loaded catalog whose plugin documentation URLs reveal the manual layout.
    version:
        Fluent Bit version used when no suitable plugin URL is available.

    Returns
    -------
    str
        Version-appropriate router documentation URL.

    """
    plugins = payload.get("plugins", {})
    if isinstance(plugins, dict):
        for section in ("inputs", "filters", "outputs"):
            section_plugins = plugins.get(section, {})
            if not isinstance(section_plugins, dict):
                continue
            for plugin_def in section_plugins.values():
                if not isinstance(plugin_def, dict):
                    continue
                doc_url = str(plugin_def.get("doc_url") or "").strip()
                if "/data-pipeline/" in doc_url:
                    return doc_url.split("/data-pipeline/", 1)[0] + "/data-pipeline/router"
                if "/pipeline/" in doc_url:
                    return doc_url.split("/pipeline/", 1)[0] + "/pipeline/router"
    if str(version).startswith("3."):
        return f"https://docs.fluentbit.io/manual/{version.rsplit('.', 1)[0]}/pipeline/router"
    if str(version).startswith("4."):
        return f"https://docs.fluentbit.io/manual/{version.rsplit('.', 1)[0]}/data-pipeline/router"
    return "https://docs.fluentbit.io/manual/data-pipeline/router"


def _ensure_router_fields(payload: dict[str, Any], version: str) -> None:
    """Add or repair routing fields required by the configuration editor.

    Parameters
    ----------
    payload:
        Mutable Fluent Bit catalog containing input, filter, and output plugins.
    version:
        Fluent Bit version controlling input-tag requirements and documentation.

    Notes
    -----
    Inputs receive ``tag`` metadata, while filters and outputs receive ``match``
    and ``match_regex`` metadata. Existing fields are preserved and repaired so
    rerunning the generator is idempotent.

    """
    plugins = payload.get("plugins", {})
    if not isinstance(plugins, dict):
        return
    reference = _router_reference(payload, version)

    tag_field = field(
        "tag",
        description="Tag assigned to records emitted by this input plugin.",
        reference=reference,
    )
    match_field = field(
        "match",
        description="Tag match pattern used to route records to this plugin. Supports '*' wildcard matching.",
        reference=reference,
    )
    match_regex_field = field(
        "match_regex",
        description="Regular expression tag match used to route records to this plugin. Takes precedence over match when both are set.",
        reference=reference,
    )

    inputs = plugins.get("inputs", {})
    for plugin_name, plugin_def in inputs.items():
        fields = plugin_def.get("fields")
        if not isinstance(fields, list):
            continue
        existing_fields = {
            item.get("name"): item for item in fields if isinstance(item, dict)
        }
        existing = set(existing_fields.keys())
        if "tag" not in existing:
            tag_payload = dict(tag_field)
            if (
                _version_requires_input_tags(version)
                and str(plugin_name) != "forward"
            ):
                tag_payload["required"] = True
            fields.append(tag_payload)
        else:
            tag_existing = existing_fields.get("tag")
            if isinstance(tag_existing, dict):
                tag_existing["reference"] = reference
                if _version_requires_input_tags(version) and str(plugin_name) != "forward":
                    tag_existing["required"] = True

    for section in ("filters", "outputs"):
        section_map = plugins.get(section, {})
        if not isinstance(section_map, dict):
            continue
        for plugin_def in section_map.values():
            fields = plugin_def.get("fields")
            if not isinstance(fields, list):
                continue
            existing = {item.get("name") for item in fields if isinstance(item, dict)}
            if "match" not in existing:
                fields.append(dict(match_field))
            if "match_regex" not in existing:
                fields.append(dict(match_regex_field))


def _clear_legacy_flat_parts(path: Path) -> None:
    """Remove obsolete flat catalog fragments before writing sharded manifests.

    Parameters
    ----------
    path:
        Top-level catalog path whose old sibling fragments should be removed.

    """
    for stale_path in path.parent.glob(f"{path.stem}.*{path.suffix}"):
        stale_path.unlink(missing_ok=True)


def _normalize_plugin_names(
    payload: dict[str, Any],
    *,
    timeout: int,
    logger: logging.Logger,
    page_cache: dict[str, str],
) -> None:
    """Rekey plugin maps to the canonical Fluent Bit configuration names.

    Parameters
    ----------
    payload:
        Mutable catalog containing plugin maps grouped by pipeline section.
    timeout:
        Maximum documentation lookup time in seconds.
    logger:
        Logger receiving normalization counts and collision diagnostics.
    page_cache:
        Shared documentation cache that avoids repeated network requests.

    Notes
    -----
    Documentation page names and native Fluent Bit ``Name`` values can differ.
    Normalizing here ensures editor output uses names accepted by Fluent Bit;
    collisions are left visible rather than silently overwriting a plugin.

    """
    plugins = payload.get("plugins", {})
    if not isinstance(plugins, dict):
        return

    for section in ("inputs", "filters", "outputs"):
        section_plugins = plugins.get(section, {})
        if not isinstance(section_plugins, dict):
            continue
        normalized, resolutions, collisions = normalize_plugin_map(
            section_plugins,
            section,
            timeout=timeout,
            logger=logger,
            page_cache=page_cache,
        )
        plugins[section] = normalized
        rename_count = sum(
            1
            for item in resolutions
            if item.expected_name and item.expected_name != item.current_name and item.expected_name not in collisions
        )
        logger.info(
            "normalized plugin section version=%s section=%s checked=%s renamed=%s collisions=%s",
            payload.get("fluent_bit_version"),
            section,
            len(resolutions),
            rename_count,
            len(collisions),
        )


def update_catalog(
    path: Path,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    logger: logging.Logger | None = None,
    page_cache: dict[str, str] | None = None,
) -> None:
    """Enrich and rewrite one Fluent Bit catalog as deterministic shards.

    Parameters
    ----------
    path:
        Top-level catalog JSON artifact to load and rewrite.
    timeout:
        Maximum documentation lookup time used during plugin-name normalization.
    logger:
        Optional logger override for generation diagnostics.
    page_cache:
        Optional shared documentation cache reused across catalog versions.

    Notes
    -----
    The operation loads either a direct JSON payload or an existing manifest,
    enriches the assembled catalog, clears stale layouts, writes one shard per
    plugin, and replaces the top-level artifact with a manifest. Stable public
    filenames let registries keep pointing to the same catalog across rebuilds.

    """
    active_logger = logger or LOGGER
    active_page_cache = page_cache if page_cache is not None else {}

    # Enrich the fully assembled catalog before splitting it back into shards.
    data = load_json_artifact(path)
    version = str(data.get("fluent_bit_version"))
    _normalize_plugin_names(data, timeout=timeout, logger=active_logger, page_cache=active_page_cache)
    common = data.setdefault("common", {})
    common["processors"] = processors_definition(version)
    _ensure_router_fields(data, version)

    version_dir = path.parent / "fluent-bit" / version
    # Remove previous shard layouts so deleted or renamed plugins cannot linger.
    shutil.rmtree(version_dir, ignore_errors=True)
    _clear_legacy_flat_parts(path)

    base_payload = dict(data)
    plugins = dict(base_payload.get("plugins", {}))
    base_payload["plugins"] = plugins
    top_level_parts: list[dict[str, Any]] = []
    # Each section manifest points at small per-plugin files for fast selective loading.
    for section in ("inputs", "filters", "outputs"):
        section_plugins = dict(plugins.get(section, {}))
        nested_manifest = write_manifest_json_artifact(
            version_dir / f"{section}.json",
            base_file=f"{section}.base.json",
            base_payload={},
            parts=[
                {
                    KEY_POINTER: f"/{plugin_name}",
                    KEY_FILE: f"{section}/{plugin_name}.json",
                    KEY_PAYLOAD: plugin_def,
                }
                for plugin_name, plugin_def in sorted(section_plugins.items())
            ],
        )
        plugins[section] = {}
        top_level_parts.append(
            {
                KEY_POINTER: f"/plugins/{section}",
                KEY_FILE: f"fluent-bit/{version}/{section}.json",
                KEY_PAYLOAD: nested_manifest,
            }
        )

    write_manifest_json_artifact(
        path,
        base_file=f"fluent-bit/{version}/all-plugins-catalog.base.json",
        base_payload=base_payload,
        parts=top_level_parts,
    )


def parse_args() -> argparse.Namespace:
    """Parse optional Fluent Bit version filters from the command line.

    Returns
    -------
    argparse.Namespace
        Parsed arguments whose ``versions`` member is a list or ``None``.

    """
    parser = argparse.ArgumentParser(
        description="Add Fluent Bit processor and router metadata to plugin catalogs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="append",
        dest="versions",
        help="Fluent Bit version to process. Repeat for multiple versions. Defaults to all local catalog versions.",
    )
    return parser.parse_args()


def _available_versions() -> list[str]:
    """Discover catalog versions currently available in the source artifact tree.

    Returns
    -------
    list[str]
        Sorted Fluent Bit version tokens extracted from catalog filenames.

    """
    versions: set[str] = set()
    for path in DEFINITIONS_DIR.glob("fluent-bit-*-all-plugins-catalog.json"):
        token = path.name.removeprefix("fluent-bit-").removesuffix("-all-plugins-catalog.json")
        if token:
            versions.add(token)
    return sorted(versions)


def main() -> None:
    """Reprocess selected catalogs in the canonical packaged artifact tree."""
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
    page_cache: dict[str, str] = {}
    versions = args.versions or _available_versions()
    for version in versions:
        filename = f"fluent-bit-{version}-all-plugins-catalog.json"
        update_catalog(DEFINITIONS_DIR / filename, logger=LOGGER, page_cache=page_cache)


if __name__ == "__main__":
    main()
