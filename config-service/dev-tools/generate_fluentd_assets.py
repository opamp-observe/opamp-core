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

"""Generate canonical packaged Fluentd catalogs and service definitions."""

# Documentation defaults are configuration payload values, not network bind operations.
# ruff: noqa: S104

from __future__ import annotations

import json
import shutil
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "config-service" / "src"
JSON_DEFINITIONS_DIR = SRC_ROOT / "config_service" / "json-definitions"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config_service.json_artifacts import (  # noqa: E402
    KEY_FILE,
    KEY_PAYLOAD,
    KEY_POINTER,
    write_manifest_json_artifact,
)

FLUENTD_LOG_LEVELS = ["trace", "debug", "info", "warn", "error", "fatal"]
TIME_TYPES = ["float", "unixtime", "string"]
BUFFER_OVERFLOW_ACTIONS = ["throw_exception", "block", "drop_oldest_chunk"]
TRANSPORT_PROTOCOLS = ["tcp", "udp", "tls"]
TLS_VERSIONS = ["TLS1_1", "TLS1_2", "TLS1_3"]


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
    item: dict[str, Any] = {
        "name": name,
        "required": required,
        "description": description,
        "reference": reference,
        "data_type": data_type,
        "validation_rule": validation_rule,
    }
    if default is not None:
        item["default"] = default
    if enum_options:
        item["enum_options"] = enum_options
    return item


def directive_argument(
    *,
    name: str,
    description: str,
    reference: str,
    data_type: str = "string",
    required: bool = True,
    validation_rule: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "required": required,
        "description": description,
        "reference": reference,
        "data_type": data_type,
        "validation_rule": validation_rule,
    }


def with_common_plugin_fields(
    fields: list[dict[str, Any]],
    reference: str,
    *,
    include_label: bool = False,
) -> list[dict[str, Any]]:
    common = [
        field(
            "@id",
            description="Unique identifier for the plugin instance.",
            reference="https://docs.fluentd.org/configuration/plugin-common-parameters",
            data_type="string",
        ),
        field(
            "@log_level",
            description="Plugin-specific log level that overrides the global system log level.",
            reference="https://docs.fluentd.org/configuration/plugin-common-parameters",
            data_type="enum",
            default="info",
            validation_rule={"kind": "enum", "values": FLUENTD_LOG_LEVELS},
            enum_options=FLUENTD_LOG_LEVELS,
        ),
    ]
    if include_label:
        common.append(
            field(
                "@label",
                description="Routes emitted events to a named label.",
                reference=reference,
                data_type="string",
                validation_rule={"kind": "regex_string"},
            )
        )
    return common + fields


def plugin_def(
    *,
    title: str,
    doc_url: str,
    description: str,
    fields: list[dict[str, Any]],
    allowed_children: list[dict[str, Any]] | None = None,
    directive_arg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "title": title,
        "doc_url": doc_url,
        "description": description,
        "fields": fields,
    }
    if allowed_children:
        payload["allowed_children"] = allowed_children
    if directive_arg:
        payload["directive_argument"] = directive_arg
    return payload


def nested_variant(
    *,
    title: str,
    doc_url: str,
    description: str,
    fields: list[dict[str, Any]],
    directive_arg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "title": title,
        "doc_url": doc_url,
        "description": description,
        "fields": fields,
    }
    if directive_arg:
        payload["directive_argument"] = directive_arg
    return payload


def child(section: str, minimum: int = 0, maximum: int | None = 1) -> dict[str, Any]:
    return {
        "section": section,
        "cardinality": {
            "minimum": minimum,
            "maximum": maximum,
        },
    }


def clone(payload: Any) -> Any:
    return deepcopy(payload)


DOC_CONFIG = "https://docs.fluentd.org/configuration/config-file"
DOC_COMMON = "https://docs.fluentd.org/configuration/plugin-common-parameters"
DOC_SYSTEM = "https://docs.fluentd.org/deployment/system-config"
DOC_PARSE = "https://docs.fluentd.org/configuration/parse-section"
DOC_BUFFER = "https://docs.fluentd.org/configuration/buffer-section"
DOC_FORMAT = "https://docs.fluentd.org/configuration/format-section"
DOC_TRANSPORT = "https://docs.fluentd.org/configuration/transport-section"
DOC_STORAGE = "https://docs.fluentd.org/configuration/storage-section"
DOC_SERVICE_DISCOVERY = "https://docs.fluentd.org/configuration/service_discovery-section"
DOC_EXTRACT = "https://docs.fluentd.org/configuration/extract-section"
DOC_INJECT = "https://docs.fluentd.org/configuration/inject-section"


def nested_sections_for(version: str) -> dict[str, Any]:
    sections: dict[str, Any] = {
        "parse": {
            "title": "parse",
            "description": "Nested parser section used by source, filter, and some output plugins.",
            "plugin_backed": True,
            "cardinality": {"minimum": 0, "maximum": 1},
            "reference": DOC_PARSE,
            "variants": {
                "json": nested_variant(
                    title="json",
                    doc_url="https://docs.fluentd.org/parser/json",
                    description="Parses each event as JSON.",
                    fields=[
                        field("time_key", description="Record key containing event time.", reference=DOC_PARSE),
                        field(
                            "time_type",
                            description="How to parse the time value.",
                            reference=DOC_PARSE,
                            data_type="enum",
                            default="float",
                            validation_rule={"kind": "enum", "values": TIME_TYPES},
                            enum_options=TIME_TYPES,
                        ),
                        field("time_format", description="Time format used when time_type is string.", reference=DOC_PARSE),
                        field("keep_time_key", description="Preserve the original time key in the record.", reference=DOC_PARSE, data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                    ],
                ),
                "regexp": nested_variant(
                    title="regexp",
                    doc_url="https://docs.fluentd.org/parser/regexp",
                    description="Parses records using a regular expression with named captures.",
                    fields=[
                        field("expression", description="Regular expression with named capture groups.", reference=DOC_PARSE, required=True, validation_rule={"kind": "regex_string"}),
                        field("time_key", description="Capture group used as the event time.", reference=DOC_PARSE),
                        field("time_format", description="Time format used when parsing the captured time string.", reference=DOC_PARSE),
                    ],
                ),
                "multiline": nested_variant(
                    title="multiline",
                    doc_url="https://docs.fluentd.org/parser/multiline",
                    description="Parses multiline records using firstline and format expressions.",
                    fields=[
                        field("format_firstline", description="Pattern matching the first line of a multiline event.", reference=DOC_PARSE, required=True, validation_rule={"kind": "regex_string"}),
                        field("format1", description="Primary regular expression for joined multiline content.", reference=DOC_PARSE, required=True, validation_rule={"kind": "regex_string"}),
                        field("format2", description="Optional second format expression.", reference=DOC_PARSE, validation_rule={"kind": "regex_string"}),
                    ],
                ),
                "none": nested_variant(
                    title="none",
                    doc_url="https://docs.fluentd.org/parser/none",
                    description="Passes the full input line through without parsing.",
                    fields=[
                        field("message_key", description="Key name that will hold the raw event payload.", reference=DOC_PARSE, default="message"),
                    ],
                ),
            },
        },
        "buffer": {
            "title": "buffer",
            "description": "Nested output buffer section controlling chunking, flushing, and retry behavior.",
            "plugin_backed": True,
            "cardinality": {"minimum": 0, "maximum": 1},
            "reference": DOC_BUFFER,
            "variants": {
                "file": nested_variant(
                    title="file",
                    doc_url="https://docs.fluentd.org/buffer/file",
                    description="Persistent on-disk buffer plugin.",
                    fields=with_common_plugin_fields(
                        [
                            field("path", description="Directory or file prefix used for buffer chunks.", reference=DOC_BUFFER, data_type="string", validation_rule={"kind": "regex_string"}),
                            field("chunk_keys", description="Chunk keys rendered into the <buffer ARG> directive argument.", reference=DOC_BUFFER, data_type="list", validation_rule={"kind": "list"}),
                            field("chunk_limit_size", description="Maximum chunk size before flush.", reference=DOC_BUFFER, data_type="size", default="8m"),
                            field("total_limit_size", description="Maximum total size across staged and queued chunks.", reference=DOC_BUFFER, data_type="size", default="512m"),
                            field("flush_interval", description="Interval between flush operations.", reference=DOC_BUFFER, data_type="time", default="60s"),
                            field("retry_timeout", description="Overall retry timeout before the chunk is discarded or handed to secondary output.", reference=DOC_BUFFER, data_type="time", default="72h"),
                            field(
                                "overflow_action",
                                description="Behavior when the buffer queue is full.",
                                reference=DOC_BUFFER,
                                data_type="enum",
                                default="throw_exception",
                                validation_rule={"kind": "enum", "values": BUFFER_OVERFLOW_ACTIONS},
                                enum_options=BUFFER_OVERFLOW_ACTIONS,
                            ),
                        ],
                        DOC_COMMON,
                    ),
                ),
                "memory": nested_variant(
                    title="memory",
                    doc_url="https://docs.fluentd.org/buffer/memory",
                    description="In-memory buffer plugin.",
                    fields=with_common_plugin_fields(
                        [
                            field("chunk_keys", description="Chunk keys rendered into the <buffer ARG> directive argument.", reference=DOC_BUFFER, data_type="list", validation_rule={"kind": "list"}),
                            field("chunk_limit_size", description="Maximum chunk size before flush.", reference=DOC_BUFFER, data_type="size", default="8m"),
                            field("total_limit_size", description="Maximum total in-memory buffer size.", reference=DOC_BUFFER, data_type="size", default="512m"),
                            field("flush_interval", description="Interval between flush operations.", reference=DOC_BUFFER, data_type="time", default="60s"),
                        ],
                        DOC_COMMON,
                    ),
                ),
            },
        },
        "format": {
            "title": "format",
            "description": "Nested formatter section controlling output serialization.",
            "plugin_backed": True,
            "cardinality": {"minimum": 0, "maximum": 1},
            "reference": DOC_FORMAT,
            "variants": {
                "json": nested_variant(
                    title="json",
                    doc_url="https://docs.fluentd.org/formatter/json",
                    description="Formats records as JSON.",
                    fields=[
                        field(
                            "time_type",
                            description="How time values should be serialized.",
                            reference=DOC_FORMAT,
                            data_type="enum",
                            default="float",
                            validation_rule={"kind": "enum", "values": TIME_TYPES},
                            enum_options=TIME_TYPES,
                        ),
                        field("time_format", description="Time format used when time_type is string.", reference=DOC_FORMAT),
                        field("localtime", description="Use local time when formatting timestamps.", reference=DOC_FORMAT, data_type="boolean", default=True, validation_rule={"kind": "boolean"}),
                        field("utc", description="Use UTC when formatting timestamps.", reference=DOC_FORMAT, data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                    ],
                ),
                "csv": nested_variant(
                    title="csv",
                    doc_url="https://docs.fluentd.org/formatter/csv",
                    description="Formats records as CSV using a fixed field list.",
                    fields=[
                        field("fields", description="Ordered list of record keys emitted as CSV columns.", reference=DOC_FORMAT, data_type="list", required=True, validation_rule={"kind": "list"}),
                        field("delimiter", description="Field delimiter used in the CSV output.", reference=DOC_FORMAT, default=","),
                    ],
                ),
                "ltsv": nested_variant(
                    title="ltsv",
                    doc_url="https://docs.fluentd.org/formatter/ltsv",
                    description="Formats records as LTSV key:value pairs.",
                    fields=[
                        field("delimiter", description="Delimiter used between LTSV fields.", reference=DOC_FORMAT, default="\t"),
                    ],
                ),
                "single_value": nested_variant(
                    title="single_value",
                    doc_url="https://docs.fluentd.org/formatter/single_value",
                    description="Formats one record field as a plain string output.",
                    fields=[
                        field("message_key", description="Record field written to the output stream.", reference=DOC_FORMAT, required=True),
                        field("add_newline", description="Append a newline after each formatted record.", reference=DOC_FORMAT, data_type="boolean", default=True, validation_rule={"kind": "boolean"}),
                    ],
                ),
            },
        },
        "transport": {
            "title": "transport",
            "description": "Nested connection transport settings for source, filter, and output plugins.",
            "plugin_backed": False,
            "cardinality": {"minimum": 0, "maximum": 1},
            "reference": DOC_TRANSPORT,
            "directive_argument": directive_argument(
                name="protocol",
                description="Transport protocol specified by the <transport ARG> directive.",
                reference=DOC_TRANSPORT,
                data_type="enum",
                validation_rule={"kind": "enum", "values": TRANSPORT_PROTOCOLS},
            ),
            "fields": [
                field("linger_timeout", description="SO_LINGER timeout in seconds.", reference=DOC_TRANSPORT, data_type="integer", default=0, validation_rule={"kind": "range", "min": 0}),
                field("version", description="Fixed TLS protocol version.", reference=DOC_TRANSPORT, data_type="enum", validation_rule={"kind": "enum", "values": TLS_VERSIONS}, enum_options=TLS_VERSIONS),
                field("min_version", description="Minimum TLS protocol version.", reference=DOC_TRANSPORT, data_type="enum", validation_rule={"kind": "enum", "values": TLS_VERSIONS}, enum_options=TLS_VERSIONS),
                field("max_version", description="Maximum TLS protocol version.", reference=DOC_TRANSPORT, data_type="enum", validation_rule={"kind": "enum", "values": TLS_VERSIONS}, enum_options=TLS_VERSIONS),
                field("insecure", description="Disable certificate verification for TLS.", reference=DOC_TRANSPORT, data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                field("cert_path", description="Path to the TLS certificate file.", reference=DOC_TRANSPORT, validation_rule={"kind": "regex_string"}),
                field("private_key_path", description="Path to the TLS private key file.", reference=DOC_TRANSPORT, validation_rule={"kind": "regex_string"}),
                field("private_key_passphrase", description="Passphrase for the TLS private key.", reference=DOC_TRANSPORT),
                field("ca_path", description="Path to the trusted CA certificate file.", reference=DOC_TRANSPORT, validation_rule={"kind": "regex_string"}),
            ],
        },
        "storage": {
            "title": "storage",
            "description": "Nested plugin state storage settings.",
            "plugin_backed": True,
            "cardinality": {"minimum": 0, "maximum": 1},
            "reference": DOC_STORAGE,
            "variants": {
                "local": nested_variant(
                    title="local",
                    doc_url="https://docs.fluentd.org/storage/local",
                    description="Stores plugin state on the local filesystem.",
                    fields=[
                        field("path", description="File path used to persist the plugin state.", reference=DOC_STORAGE, validation_rule={"kind": "regex_string"}),
                        field("persistent", description="Persist state to disk rather than keeping it in memory only.", reference=DOC_STORAGE, data_type="boolean", default=True, validation_rule={"kind": "boolean"}),
                    ],
                ),
            },
        },
        "service_discovery": {
            "title": "service_discovery",
            "description": "Nested output target discovery section.",
            "plugin_backed": True,
            "cardinality": {"minimum": 0, "maximum": 1},
            "reference": DOC_SERVICE_DISCOVERY,
            "variants": {
                "file": nested_variant(
                    title="file",
                    doc_url="https://docs.fluentd.org/service_discovery/file",
                    description="Loads target endpoints from a local file.",
                    fields=[
                        field("path", description="Path to the discovery file.", reference=DOC_SERVICE_DISCOVERY, required=True, validation_rule={"kind": "regex_string"}),
                    ],
                ),
                "static": nested_variant(
                    title="static",
                    doc_url="https://docs.fluentd.org/service_discovery/static",
                    description="Uses a fixed list of predeclared forwarding targets.",
                    fields=[
                        field("services", description="List of static service definitions.", reference=DOC_SERVICE_DISCOVERY, data_type="list", validation_rule={"kind": "list"}),
                    ],
                ),
                "srv": nested_variant(
                    title="srv",
                    doc_url="https://docs.fluentd.org/service_discovery/srv",
                    description="Resolves output targets from DNS SRV records.",
                    fields=[
                        field("service", description="Service label used in the SRV lookup.", reference=DOC_SERVICE_DISCOVERY, required=True),
                        field("hostname", description="Hostname portion used in the SRV lookup.", reference=DOC_SERVICE_DISCOVERY, required=True),
                    ],
                ),
            },
        },
        "extract": {
            "title": "extract",
            "description": "Nested extract section used to copy tag/time values from record keys.",
            "plugin_backed": False,
            "cardinality": {"minimum": 0, "maximum": 1},
            "reference": DOC_EXTRACT,
            "fields": [
                field("tag_key", description="Record field extracted into the event tag.", reference=DOC_EXTRACT),
                field("keep_tag_key", description="Preserve the original tag field in the record.", reference=DOC_EXTRACT, data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                field("time_key", description="Record field extracted into the event timestamp.", reference=DOC_EXTRACT),
                field("keep_time_key", description="Preserve the original time field in the record.", reference=DOC_EXTRACT, data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                field(
                    "time_type",
                    description="How the extracted time value should be interpreted.",
                    reference=DOC_EXTRACT,
                    data_type="enum",
                    default="float",
                    validation_rule={"kind": "enum", "values": TIME_TYPES},
                    enum_options=TIME_TYPES,
                ),
                field("time_format", description="Time format used when time_type is string.", reference=DOC_EXTRACT),
                field("timezone", description="Timezone used when parsing string timestamps.", reference=DOC_EXTRACT),
            ],
        },
        "inject": {
            "title": "inject",
            "description": "Nested inject section used to add metadata into emitted records.",
            "plugin_backed": False,
            "cardinality": {"minimum": 0, "maximum": 1},
            "reference": DOC_INJECT,
            "fields": [
                field("hostname_key", description="Record field used to inject the local hostname.", reference=DOC_INJECT),
                field("worker_id_key", description="Record field used to inject the Fluentd worker id.", reference=DOC_INJECT),
                field("tag_key", description="Record field used to inject the event tag.", reference=DOC_INJECT),
                field("time_key", description="Record field used to inject the formatted event time.", reference=DOC_INJECT),
                field(
                    "time_type",
                    description="How injected time values should be formatted.",
                    reference=DOC_INJECT,
                    data_type="enum",
                    default="float",
                    validation_rule={"kind": "enum", "values": TIME_TYPES},
                    enum_options=TIME_TYPES,
                ),
                field("time_format", description="Time format used when time_type is string.", reference=DOC_INJECT),
            ],
        },
        "record": {
            "title": "record",
            "description": "Nested record section used by record_transformer to define injected fields.",
            "plugin_backed": False,
            "cardinality": {"minimum": 0, "maximum": 1},
            "reference": "https://docs.fluentd.org/filter/record_transformer",
            "fields": [
                field("entries", description="Map of output record keys to literal values or embedded Ruby expressions.", reference="https://docs.fluentd.org/filter/record_transformer", data_type="map"),
            ],
        },
        "regexp": {
            "title": "regexp",
            "description": "Nested regexp rule used by grep filters.",
            "plugin_backed": False,
            "cardinality": {"minimum": 0, "maximum": None},
            "reference": "https://docs.fluentd.org/filter/grep",
            "fields": [
                field("key", description="Record field evaluated by the regexp rule.", reference="https://docs.fluentd.org/filter/grep", required=True),
                field("pattern", description="Regular expression applied to the field.", reference="https://docs.fluentd.org/filter/grep", required=True, validation_rule={"kind": "regex_string"}),
            ],
        },
        "exclude": {
            "title": "exclude",
            "description": "Nested exclude rule used by grep filters.",
            "plugin_backed": False,
            "cardinality": {"minimum": 0, "maximum": None},
            "reference": "https://docs.fluentd.org/filter/grep",
            "fields": [
                field("key", description="Record field evaluated by the exclusion rule.", reference="https://docs.fluentd.org/filter/grep", required=True),
                field("pattern", description="Regular expression that excludes matching records.", reference="https://docs.fluentd.org/filter/grep", required=True, validation_rule={"kind": "regex_string"}),
            ],
        },
        "store": {
            "title": "store",
            "description": "Nested store output used by out_copy.",
            "plugin_backed": True,
            "reuses_output_plugins": True,
            "cardinality": {"minimum": 1, "maximum": None},
            "reference": "https://docs.fluentd.org/output/copy",
        },
        "secondary": {
            "title": "secondary",
            "description": "Nested secondary output used for failed chunk retries.",
            "plugin_backed": True,
            "reuses_output_plugins": True,
            "cardinality": {"minimum": 0, "maximum": 1},
            "reference": DOC_BUFFER,
        },
    }

    if version == "1.19":
        sections["transport"]["fields"].insert(
            1,
            field(
                "receive_buffer_size",
                description="Maximum socket receive buffer size for TCP, UDP, and TLS transports.",
                reference=DOC_TRANSPORT,
                data_type="integer",
                validation_rule={"kind": "range", "min": 0},
            ),
        )

    return sections


def source_plugins(version: str) -> dict[str, Any]:
    return {
        "tail": plugin_def(
            title="tail",
            doc_url="https://docs.fluentd.org/input/tail",
            description="Reads log lines from files and emits them as Fluentd events.",
            fields=with_common_plugin_fields(
                [
                    field("tag", description="Tag assigned to emitted events.", reference="https://docs.fluentd.org/input/tail", required=True),
                    field("path", description="Path or glob of files to watch.", reference="https://docs.fluentd.org/input/tail", required=True),
                    field("exclude_path", description="List of file path patterns excluded from watching.", reference="https://docs.fluentd.org/input/tail", data_type="list", validation_rule={"kind": "list"}),
                    field("pos_file", description="Path to the position file used to resume tailing after restart.", reference="https://docs.fluentd.org/input/tail", validation_rule={"kind": "regex_string"}),
                    field("read_from_head", description="Read the target file from the beginning on startup.", reference="https://docs.fluentd.org/input/tail", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                    field("follow_inodes", description="Track inodes to avoid duplicate reads when files rotate.", reference="https://docs.fluentd.org/input/tail", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                    field("refresh_interval", description="How often Fluentd refreshes the watched file set.", reference="https://docs.fluentd.org/input/tail", data_type="time", default="60s"),
                    field("rotate_wait", description="Time to keep the old file handle open after rotation.", reference="https://docs.fluentd.org/input/tail", data_type="time", default="5s"),
                    field("path_key", description="Record key used to inject the tailed file path.", reference="https://docs.fluentd.org/input/tail"),
                ],
                DOC_COMMON,
                include_label=True,
            ),
            allowed_children=[child("parse"), child("storage")],
        ),
        "forward": plugin_def(
            title="forward",
            doc_url="https://docs.fluentd.org/input/forward",
            description="Accepts Fluentd Forward protocol traffic from remote senders.",
            fields=with_common_plugin_fields(
                [
                    field("port", description="TCP port used for forward input.", reference="https://docs.fluentd.org/input/forward", data_type="integer", default=24224, validation_rule={"kind": "range", "min": 1, "max": 65535}),
                    field("bind", description="Bind address for the forward listener.", reference="https://docs.fluentd.org/input/forward", default="0.0.0.0"),
                    field("source_hostname_key", description="Record key used to inject the remote sender hostname.", reference="https://docs.fluentd.org/input/forward"),
                    field("source_address_key", description="Record key used to inject the remote sender IP address.", reference="https://docs.fluentd.org/input/forward"),
                    field("skip_invalid_event", description="Drop invalid incoming forward events rather than raising an error.", reference="https://docs.fluentd.org/input/forward", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                ],
                DOC_COMMON,
                include_label=True,
            ),
            allowed_children=[child("transport")],
        ),
        "tcp": plugin_def(
            title="tcp",
            doc_url="https://docs.fluentd.org/input/tcp",
            description="Accepts raw TCP payloads and parses them into Fluentd events.",
            fields=with_common_plugin_fields(
                [
                    field("tag", description="Tag assigned to emitted events when extract/tag_key is not used.", reference="https://docs.fluentd.org/input/tcp", required=True),
                    field("port", description="TCP port used by the listener.", reference="https://docs.fluentd.org/input/tcp", data_type="integer", default=5170, validation_rule={"kind": "range", "min": 1, "max": 65535}),
                    field("bind", description="Bind address for the TCP listener.", reference="https://docs.fluentd.org/input/tcp", default="0.0.0.0"),
                    field("delimiter", description="Delimiter separating events within the TCP stream.", reference="https://docs.fluentd.org/input/tcp", default="\n"),
                    field("message_length_limit", description="Maximum accepted message size.", reference="https://docs.fluentd.org/input/tcp", data_type="size", default="8m"),
                    field("source_hostname_key", description="Record key used to inject the client hostname.", reference="https://docs.fluentd.org/input/tcp"),
                    field("source_address_key", description="Record key used to inject the client address.", reference="https://docs.fluentd.org/input/tcp"),
                ],
                DOC_COMMON,
                include_label=True,
            ),
            allowed_children=[child("parse"), child("transport"), child("extract")],
        ),
        "udp": plugin_def(
            title="udp",
            doc_url="https://docs.fluentd.org/input/udp",
            description="Accepts UDP payloads and parses them into Fluentd events.",
            fields=with_common_plugin_fields(
                [
                    field("tag", description="Tag assigned to emitted events.", reference="https://docs.fluentd.org/input/udp", required=True),
                    field("port", description="UDP port used by the listener.", reference="https://docs.fluentd.org/input/udp", data_type="integer", default=5160, validation_rule={"kind": "range", "min": 1, "max": 65535}),
                    field("bind", description="Bind address for the UDP listener.", reference="https://docs.fluentd.org/input/udp", default="0.0.0.0"),
                    field("message_length_limit", description="Maximum accepted datagram size.", reference="https://docs.fluentd.org/input/udp", data_type="size", default="4096"),
                    field("source_hostname_key", description="Record key used to inject the client hostname.", reference="https://docs.fluentd.org/input/udp"),
                    field("source_address_key", description="Record key used to inject the client address.", reference="https://docs.fluentd.org/input/udp"),
                    field("remove_newline", description="Trim trailing newline bytes from incoming payloads.", reference="https://docs.fluentd.org/input/udp", data_type="boolean", default=True, validation_rule={"kind": "boolean"}),
                ],
                DOC_COMMON,
                include_label=True,
            ),
            allowed_children=[child("parse"), child("transport"), child("extract")],
        ),
        "unix": plugin_def(
            title="unix",
            doc_url="https://docs.fluentd.org/input/unix",
            description="Receives Fluentd Forward protocol events over a Unix domain socket.",
            fields=with_common_plugin_fields(
                [
                    field("path", description="Path to the Unix domain socket.", reference="https://docs.fluentd.org/input/unix", required=True, validation_rule={"kind": "regex_string"}),
                    field("backlog", description="Socket listen backlog.", reference="https://docs.fluentd.org/input/unix", data_type="integer", default=1024, validation_rule={"kind": "range", "min": 1}),
                    field("tag", description="Optional tag override for incoming events.", reference="https://docs.fluentd.org/input/unix"),
                ],
                DOC_COMMON,
                include_label=True,
            ),
            allowed_children=[child("transport")],
        ),
        "http": plugin_def(
            title="http",
            doc_url="https://docs.fluentd.org/input/http",
            description="Accepts event payloads over HTTP.",
            fields=with_common_plugin_fields(
                [
                    field("port", description="TCP port used by the HTTP input.", reference="https://docs.fluentd.org/input/http", data_type="integer", default=9880, validation_rule={"kind": "range", "min": 1, "max": 65535}),
                    field("bind", description="Bind address for the HTTP listener.", reference="https://docs.fluentd.org/input/http", default="0.0.0.0"),
                    field("body_size_limit", description="Maximum accepted request body size.", reference="https://docs.fluentd.org/input/http", data_type="size", default="32m"),
                    field("keepalive_timeout", description="HTTP keepalive timeout.", reference="https://docs.fluentd.org/input/http", data_type="time", default="10s"),
                    field("respond_with_empty_img", description="Respond with a tracking pixel rather than an empty body.", reference="https://docs.fluentd.org/input/http", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                    field("add_http_headers", description="Store request headers in the record.", reference="https://docs.fluentd.org/input/http", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                ],
                DOC_COMMON,
                include_label=True,
            ),
            allowed_children=[child("parse"), child("transport")],
        ),
        "syslog": plugin_def(
            title="syslog",
            doc_url="https://docs.fluentd.org/input/syslog",
            description="Receives syslog messages over UDP or TCP.",
            fields=with_common_plugin_fields(
                [
                    field("port", description="Port used for the syslog listener.", reference="https://docs.fluentd.org/input/syslog", data_type="integer", default=5140, validation_rule={"kind": "range", "min": 1, "max": 65535}),
                    field("bind", description="Bind address for the syslog listener.", reference="https://docs.fluentd.org/input/syslog", default="0.0.0.0"),
                    field("tag", description="Base tag assigned to emitted syslog events.", reference="https://docs.fluentd.org/input/syslog", required=True),
                    field("message_format", description="Expected syslog message format.", reference="https://docs.fluentd.org/input/syslog", data_type="enum", default="rfc3164", validation_rule={"kind": "enum", "values": ["rfc3164", "rfc5424", "auto"]}, enum_options=["rfc3164", "rfc5424", "auto"]),
                    field("emit_unmatched_lines", description="Emit unparsable lines instead of dropping them.", reference="https://docs.fluentd.org/input/syslog", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                ],
                DOC_COMMON,
                include_label=True,
            ),
            allowed_children=[child("parse"), child("transport")],
        ),
        "exec": plugin_def(
            title="exec",
            doc_url="https://docs.fluentd.org/input/exec",
            description="Runs an external command and ingests its stdout as events.",
            fields=with_common_plugin_fields(
                [
                    field("command", description="Command line executed by the input plugin.", reference="https://docs.fluentd.org/input/exec", required=True),
                    field("tag", description="Tag assigned to emitted events.", reference="https://docs.fluentd.org/input/exec", required=True),
                    field("run_interval", description="Interval between command executions.", reference="https://docs.fluentd.org/input/exec", data_type="time", default="60s"),
                    field("encoding", description="Output encoding expected from the command.", reference="https://docs.fluentd.org/input/exec"),
                ],
                DOC_COMMON,
                include_label=True,
            ),
            allowed_children=[child("parse"), child("extract")],
        ),
        "sample": plugin_def(
            title="sample",
            doc_url="https://docs.fluentd.org/input/sample",
            description="Generates sample events for testing pipelines.",
            fields=with_common_plugin_fields(
                [
                    field("tag", description="Tag assigned to generated events.", reference="https://docs.fluentd.org/input/sample", required=True),
                    field("sample", description="Sample payload emitted at each interval.", reference="https://docs.fluentd.org/input/sample", data_type="string", required=True),
                    field("rate", description="Interval between generated events.", reference="https://docs.fluentd.org/input/sample", data_type="time", default="1s"),
                ],
                DOC_COMMON,
                include_label=True,
            ),
        ),
        "monitor_agent": plugin_def(
            title="monitor_agent",
            doc_url="https://docs.fluentd.org/input/monitor_agent",
            description="Exposes Fluentd runtime metrics and plugin state over HTTP.",
            fields=with_common_plugin_fields(
                [
                    field("bind", description="Bind address for the monitor endpoint.", reference="https://docs.fluentd.org/input/monitor_agent", default="0.0.0.0"),
                    field("port", description="Port used by the monitor endpoint.", reference="https://docs.fluentd.org/input/monitor_agent", data_type="integer", default=24220, validation_rule={"kind": "range", "min": 1, "max": 65535}),
                    field("tag", description="Optional tag used when monitor data is emitted as an event.", reference="https://docs.fluentd.org/input/monitor_agent"),
                    field("include_config", description="Include full plugin config in monitor responses.", reference="https://docs.fluentd.org/input/monitor_agent", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                    field("include_retry", description="Include retry state in monitor responses.", reference="https://docs.fluentd.org/input/monitor_agent", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                ],
                DOC_COMMON,
                include_label=True,
            ),
        ),
    }


def filter_plugins(version: str) -> dict[str, Any]:
    return {
        "grep": plugin_def(
            title="grep",
            doc_url="https://docs.fluentd.org/filter/grep",
            description="Keeps or drops records by matching field values with regular expressions.",
            directive_arg=directive_argument(
                name="match",
                description="Tag pattern selecting events for this filter.",
                reference=DOC_CONFIG,
                validation_rule={"kind": "regex_string"},
            ),
            fields=with_common_plugin_fields([], DOC_COMMON),
            allowed_children=[child("regexp", 0, None), child("exclude", 0, None)],
        ),
        "record_transformer": plugin_def(
            title="record_transformer",
            doc_url="https://docs.fluentd.org/filter/record_transformer",
            description="Adds, removes, or rewrites record fields.",
            directive_arg=directive_argument(
                name="match",
                description="Tag pattern selecting events for this filter.",
                reference=DOC_CONFIG,
                validation_rule={"kind": "regex_string"},
            ),
            fields=with_common_plugin_fields(
                [
                    field("enable_ruby", description="Enable embedded Ruby expressions inside the record section.", reference="https://docs.fluentd.org/filter/record_transformer", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                    field("auto_typecast", description="Cast evaluated strings into numeric or boolean types when possible.", reference="https://docs.fluentd.org/filter/record_transformer", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                    field("renew_record", description="Create a fresh output record rather than mutating the input record.", reference="https://docs.fluentd.org/filter/record_transformer", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                    field("remove_keys", description="Comma-separated list of record keys removed after transformation.", reference="https://docs.fluentd.org/filter/record_transformer", data_type="list", validation_rule={"kind": "list"}),
                    field("keep_keys", description="List of record keys preserved when renew_record is true.", reference="https://docs.fluentd.org/filter/record_transformer", data_type="list", validation_rule={"kind": "list"}),
                ],
                DOC_COMMON,
            ),
            allowed_children=[child("record")],
        ),
        "parser": plugin_def(
            title="parser",
            doc_url="https://docs.fluentd.org/filter/parser",
            description="Parses one field from each record and merges parsed content back into the event.",
            directive_arg=directive_argument(
                name="match",
                description="Tag pattern selecting events for this filter.",
                reference=DOC_CONFIG,
                validation_rule={"kind": "regex_string"},
            ),
            fields=with_common_plugin_fields(
                [
                    field("key_name", description="Record field containing the raw content to parse.", reference="https://docs.fluentd.org/filter/parser", required=True),
                    field("reserve_data", description="Keep original record fields alongside parsed content.", reference="https://docs.fluentd.org/filter/parser", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                    field("remove_key_name_field", description="Remove the source key after a successful parse.", reference="https://docs.fluentd.org/filter/parser", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                    field("emit_invalid_record_to_error", description="Route invalid records to the @ERROR label.", reference="https://docs.fluentd.org/filter/parser", data_type="boolean", default=True, validation_rule={"kind": "boolean"}),
                ],
                DOC_COMMON,
            ),
            allowed_children=[child("parse")],
        ),
        "stdout": plugin_def(
            title="stdout",
            doc_url="https://docs.fluentd.org/filter/stdout",
            description="Prints filtered records to stdout or Fluentd's own log stream.",
            directive_arg=directive_argument(
                name="match",
                description="Tag pattern selecting events for this filter.",
                reference=DOC_CONFIG,
                validation_rule={"kind": "regex_string"},
            ),
            fields=with_common_plugin_fields([], DOC_COMMON),
            allowed_children=[child("inject")],
        ),
    }


def output_plugins(version: str) -> dict[str, Any]:
    return {
        "stdout": plugin_def(
            title="stdout",
            doc_url="https://docs.fluentd.org/output/stdout",
            description="Writes matched records to stdout or the Fluentd log stream.",
            directive_arg=directive_argument(
                name="match",
                description="Tag pattern selecting events for this output.",
                reference=DOC_CONFIG,
                validation_rule={"kind": "regex_string"},
            ),
            fields=with_common_plugin_fields([], DOC_COMMON),
            allowed_children=[child("inject")],
        ),
        "file": plugin_def(
            title="file",
            doc_url="https://docs.fluentd.org/output/file",
            description="Writes matched records to files on disk.",
            directive_arg=directive_argument(
                name="match",
                description="Tag pattern selecting events for this output.",
                reference=DOC_CONFIG,
                validation_rule={"kind": "regex_string"},
            ),
            fields=with_common_plugin_fields(
                [
                    field("path", description="Output path or file prefix for generated files.", reference="https://docs.fluentd.org/output/file", required=True, validation_rule={"kind": "regex_string"}),
                    field("append", description="Append to existing output files.", reference="https://docs.fluentd.org/output/file", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                    field("compress", description="Compression algorithm for rotated chunks.", reference="https://docs.fluentd.org/output/file", data_type="enum", default="text", validation_rule={"kind": "enum", "values": ["text", "gzip", "zstd"]}, enum_options=["text", "gzip", "zstd"]),
                    field("symlink_path", description="Optional symlink pointing to the current output file.", reference="https://docs.fluentd.org/output/file", validation_rule={"kind": "regex_string"}),
                ],
                DOC_COMMON,
            ),
            allowed_children=[child("buffer"), child("format"), child("inject"), child("secondary")],
        ),
        "forward": plugin_def(
            title="forward",
            doc_url="https://docs.fluentd.org/output/forward",
            description="Forwards matched records to other Fluentd or Fluent Bit nodes.",
            directive_arg=directive_argument(
                name="match",
                description="Tag pattern selecting events for this output.",
                reference=DOC_CONFIG,
                validation_rule={"kind": "regex_string"},
            ),
            fields=with_common_plugin_fields(
                [
                    field("send_timeout", description="Write timeout for outgoing connections.", reference="https://docs.fluentd.org/output/forward", data_type="time", default="60s"),
                    field("recover_wait", description="Delay before reconnecting to a recovered node.", reference="https://docs.fluentd.org/output/forward", data_type="time", default="10s"),
                    field("heartbeat_type", description="Heartbeat transport used for node health checks.", reference="https://docs.fluentd.org/output/forward", data_type="enum", default="transport", validation_rule={"kind": "enum", "values": ["transport", "udp", "tcp", "none"]}, enum_options=["transport", "udp", "tcp", "none"]),
                    field("heartbeat_interval", description="Interval between heartbeats.", reference="https://docs.fluentd.org/output/forward", data_type="time", default="1s"),
                    field("require_ack_response", description="Wait for acknowledgements from the downstream node.", reference="https://docs.fluentd.org/output/forward", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                ],
                DOC_COMMON,
            ),
            allowed_children=[child("buffer"), child("secondary"), child("service_discovery"), child("transport")],
        ),
        "null": plugin_def(
            title="null",
            doc_url="https://docs.fluentd.org/output/null",
            description="Drops matched records.",
            directive_arg=directive_argument(
                name="match",
                description="Tag pattern selecting events for this output.",
                reference=DOC_CONFIG,
                validation_rule={"kind": "regex_string"},
            ),
            fields=with_common_plugin_fields([], DOC_COMMON),
            allowed_children=[child("buffer")],
        ),
        "copy": plugin_def(
            title="copy",
            doc_url="https://docs.fluentd.org/output/copy",
            description="Duplicates matched records to multiple nested store outputs.",
            directive_arg=directive_argument(
                name="match",
                description="Tag pattern selecting events for this output.",
                reference=DOC_CONFIG,
                validation_rule={"kind": "regex_string"},
            ),
            fields=with_common_plugin_fields(
                [
                    field("deep_copy", description="Deep copy records before passing them to each nested store.", reference="https://docs.fluentd.org/output/copy", data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
                ],
                DOC_COMMON,
            ),
            allowed_children=[child("store", 1, None)],
        ),
        "exec": plugin_def(
            title="exec",
            doc_url="https://docs.fluentd.org/output/exec",
            description="Passes buffered event chunks to an external command.",
            directive_arg=directive_argument(
                name="match",
                description="Tag pattern selecting events for this output.",
                reference=DOC_CONFIG,
                validation_rule={"kind": "regex_string"},
            ),
            fields=with_common_plugin_fields(
                [
                    field("command", description="External command invoked for each flushed chunk.", reference="https://docs.fluentd.org/output/exec", required=True),
                    field("remove_prefix", description="Prefix removed from the event tag before output.", reference="https://docs.fluentd.org/output/exec"),
                    field("remove_tag_prefix", description="Legacy alias for remove_prefix.", reference="https://docs.fluentd.org/output/exec"),
                ],
                DOC_COMMON,
            ),
            allowed_children=[child("buffer"), child("format"), child("inject"), child("secondary")],
        ),
        "exec_filter": plugin_def(
            title="exec_filter",
            doc_url="https://docs.fluentd.org/output/exec_filter",
            description="Transforms events by piping them through an external command and reading the command output back as events.",
            directive_arg=directive_argument(
                name="match",
                description="Tag pattern selecting events for this output.",
                reference=DOC_CONFIG,
                validation_rule={"kind": "regex_string"},
            ),
            fields=with_common_plugin_fields(
                [
                    field("command", description="External command used to transform incoming events.", reference="https://docs.fluentd.org/output/exec_filter", required=True),
                    field("in_format", description="Serialization format used for command input.", reference="https://docs.fluentd.org/output/exec_filter", data_type="enum", default="tsv", validation_rule={"kind": "enum", "values": ["tsv", "json", "msgpack"]}, enum_options=["tsv", "json", "msgpack"]),
                    field("out_format", description="Serialization format expected from command output.", reference="https://docs.fluentd.org/output/exec_filter", data_type="enum", default="tsv", validation_rule={"kind": "enum", "values": ["tsv", "json", "msgpack"]}, enum_options=["tsv", "json", "msgpack"]),
                    field("tag", description="Optional output tag override for events returned by the command.", reference="https://docs.fluentd.org/output/exec_filter"),
                ],
                DOC_COMMON,
            ),
            allowed_children=[child("buffer"), child("parse"), child("format"), child("inject"), child("secondary")],
        ),
        "relabel": plugin_def(
            title="relabel",
            doc_url="https://docs.fluentd.org/output/relabel",
            description="Routes matched events to another label without changing the record payload.",
            directive_arg=directive_argument(
                name="match",
                description="Tag pattern selecting events for this output.",
                reference=DOC_CONFIG,
                validation_rule={"kind": "regex_string"},
            ),
            fields=with_common_plugin_fields(
                [
                    field("@label", description="Target label receiving the matched events.", reference="https://docs.fluentd.org/output/relabel", required=True),
                ],
                DOC_COMMON,
            ),
        ),
    }


def root_sections(version: str) -> dict[str, Any]:
    return {
        "labels": {
            "title": "label",
            "description": "Named routing branch containing filter and output directives.",
            "fields": [
                field("name", description="Label name, including the leading @ character.", reference=DOC_CONFIG, required=True),
            ],
        },
        "workers": {
            "title": "worker",
            "description": "Worker scope used to restrict directives to a specific worker id or range.",
            "fields": [
                field("name", description="Worker selector used in the <worker ARG> directive, for example 0 or 0-1.", reference=DOC_CONFIG, required=True),
            ],
        },
        "includes": {
            "title": "@include",
            "description": "List of included configuration files or globs applied before runtime.",
            "fields": [
                field("path", description="Included file path, glob, or URL.", reference=DOC_CONFIG, required=True),
            ],
        },
    }


def service_options_for(version: str) -> list[dict[str, Any]]:
    options = [
        field("workers", description="Number of worker processes.", reference=DOC_SYSTEM, data_type="integer", default=1, validation_rule={"kind": "range", "min": 1}),
        field("root_dir", description="Root directory used for buffers, storage, and other generated files.", reference=DOC_SYSTEM, data_type="string", validation_rule={"kind": "regex_string"}),
        field("log_level", description="Global Fluentd log level.", reference=DOC_SYSTEM, data_type="enum", default="info", validation_rule={"kind": "enum", "values": FLUENTD_LOG_LEVELS}, enum_options=FLUENTD_LOG_LEVELS),
        field("suppress_repeated_stacktrace", description="Suppress repeated stacktraces in Fluentd logs.", reference=DOC_SYSTEM, data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
        field("emit_error_log_interval", description="Minimum interval between repeated error log messages.", reference=DOC_SYSTEM, data_type="time"),
        field("suppress_config_dump", description="Avoid dumping the full loaded config into startup logs.", reference=DOC_SYSTEM, data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
        field("without_source", description="Start Fluentd even when no source directives are configured.", reference=DOC_SYSTEM, data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
        field("process_name", description="Override the supervisor and worker process name.", reference=DOC_SYSTEM, data_type="string"),
        field("rpc_endpoint", description="RPC endpoint path or address used for runtime control.", reference=DOC_SYSTEM, data_type="string"),
        field("enable_get_dump", description="Enable the /api/plugins.json dump endpoint on monitor_agent.", reference=DOC_SYSTEM, data_type="boolean", default=False, validation_rule={"kind": "boolean"}),
    ]

    if version in {"1.16", "1.19"}:
        options.insert(
            1,
            field(
                "restart_worker_interval",
                description="Delay before restarting a failed worker.",
                reference=DOC_SYSTEM,
                data_type="time",
                default="0s",
            ),
        )

    if version == "1.19":
        options.append(
            field(
                "forced_stacktrace_level",
                description="Force stacktraces to be emitted at a specific log level.",
                reference=DOC_SYSTEM,
                data_type="enum",
                default="none",
                validation_rule={"kind": "enum", "values": ["none"] + FLUENTD_LOG_LEVELS},
                enum_options=["none"] + FLUENTD_LOG_LEVELS,
            )
        )

    return options


def build_catalog(version: str) -> dict[str, Any]:
    payload = {
        "catalog_type": "plugin-catalog",
        "schema_version": "1.0.0",
        "engine": "fluentd",
        "fluentd_version": version,
        "description": f"Curated Fluentd {version} plugin catalog for config-service, including nested section metadata.",
        "plugins": {
            "inputs": source_plugins(version),
            "filters": filter_plugins(version),
            "outputs": output_plugins(version),
        },
        "nested_sections": nested_sections_for(version),
        "root_sections": root_sections(version),
        "custom_plugins": {},
    }
    return payload


def build_service_definition(version: str) -> dict[str, Any]:
    return {
        "catalog_type": "service-options",
        "schema_version": "1.0.0",
        "engine": "fluentd",
        "fluentd_version": version,
        "section": "service",
        "render_as": "system",
        "cardinality": {
            "minimum": 0,
            "maximum": 1,
        },
        "description": "Global Fluentd system/service settings rendered as the <system> directive.",
        "options": service_options_for(version),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _clear_legacy_flat_parts(directory: Path, filename: str) -> None:
    manifest_path = directory / filename
    for stale_path in directory.glob(f"{manifest_path.stem}.*{manifest_path.suffix}"):
        stale_path.unlink(missing_ok=True)


def _write_catalog_artifact(directory: Path, engine_dir: str, version: str, payload: dict[str, Any]) -> None:
    filename = f"fluentd-{version}-all-plugins-catalog.json"
    manifest_path = directory / filename
    version_dir = directory / engine_dir / version

    shutil.rmtree(version_dir, ignore_errors=True)
    _clear_legacy_flat_parts(directory, filename)

    base_payload = deepcopy(payload)
    plugins = base_payload["plugins"]
    top_level_parts: list[dict[str, Any]] = []

    for section in ("inputs", "filters", "outputs"):
        section_plugins = deepcopy(plugins[section])
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
                KEY_FILE: f"{engine_dir}/{version}/{section}.json",
                KEY_PAYLOAD: nested_manifest,
            }
        )

    write_manifest_json_artifact(
        manifest_path,
        base_file=f"{engine_dir}/{version}/all-plugins-catalog.base.json",
        base_payload=base_payload,
        parts=top_level_parts,
    )


def main() -> None:
    JSON_DEFINITIONS_DIR.mkdir(parents=True, exist_ok=True)
    for version in ("1.19", "1.16", "1.8"):
        catalog_payload = build_catalog(version)
        service_payload = build_service_definition(version)
        _write_catalog_artifact(JSON_DEFINITIONS_DIR, "fluentd", version, catalog_payload)
        write_json(
            JSON_DEFINITIONS_DIR / f"fluentd-{version}-service-options.json",
            service_payload,
        )


if __name__ == "__main__":
    main()
