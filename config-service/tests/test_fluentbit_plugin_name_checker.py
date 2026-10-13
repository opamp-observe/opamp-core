#!/usr/bin/env python3
# Copyright 2026 mp3monster.org
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config_service.fluentbit_docs_support import (  # noqa: E402
    KEY_TAG_NAME,
    build_catalog_from_docs,
    extract_expected_name,
    fetch_url_text,
    parse_gitbook_redirects,
    parse_markdown_table,
    resolve_current_stable_version,
    rows_to_fields,
)

LATEST_VERSION = "5.1.3"


def test_fetch_url_text_rejects_non_http_schemes() -> None:
    """Documentation retrieval must not allow local or custom URL schemes."""
    with pytest.raises(ValueError, match="Unsupported documentation URL scheme"):
        fetch_url_text("file:///tmp/fluent-bit.md", timeout=10)


def test_resolve_current_stable_version_normalizes_github_release_tag() -> None:
    """The latest-release resolver should accept a semantic GitHub tag."""

    def fetch_release(_url: str, *, timeout: int) -> str:
        """Return one deterministic GitHub release payload for the resolver."""
        assert timeout == 17
        return json.dumps({KEY_TAG_NAME: f"v{LATEST_VERSION}"})

    assert (
        resolve_current_stable_version(timeout=17, text_fetcher=fetch_release)
        == LATEST_VERSION
    )


def test_resolve_current_stable_version_rejects_invalid_release_payloads() -> None:
    """Invalid JSON, response shapes, and tags should produce actionable errors."""
    payloads = ["not-json", "[]", "{}", json.dumps({KEY_TAG_NAME: "next"})]

    for payload in payloads:

        def fetch_release(_url: str, *, timeout: int, response: str = payload) -> str:
            """Return the current invalid fixture without making a network call."""
            assert timeout == 20
            return response

        with pytest.raises(ValueError, match="latest-release|semantic tag_name"):
            resolve_current_stable_version(timeout=20, text_fetcher=fetch_release)


def test_extract_expected_name_supports_config_block_and_log_patterns() -> None:
    input_text = """
    [INPUT]
        Name stdin
    """
    assert extract_expected_name(input_text, "inputs") == ("stdin", "[INPUT] Name")

    output_text = """
    [ info] [output:stdout:stdout.0] worker started
    """
    assert extract_expected_name(output_text, "outputs") == ("stdout", "[output:name]")


def test_parse_gitbook_redirects_collects_expected_plugin_names() -> None:
    payload = """
redirects:
    input/stdin:  ./pipeline/inputs/standard-input.md
    filter/grep:  ./pipeline/filters/grep.md
    output/stdout: ./pipeline/outputs/standard-output.md
"""
    mappings = parse_gitbook_redirects(payload)
    assert mappings["inputs"]["stdin"] == "./pipeline/inputs/standard-input.md"
    assert mappings["filters"]["grep"] == "./pipeline/filters/grep.md"
    assert mappings["outputs"]["stdout"] == "./pipeline/outputs/standard-output.md"


def test_markdown_table_rows_infer_size_and_boolean_fields() -> None:
    markdown = """
# Tail

## Configuration parameters

| Key | Description | Default |
| :--- | :--- | :--- |
| `buffer_chunk_size` | Set the buffer size according to the Unit Size specification. | `32k` |
| `enabled` | Enable the feature. | `true` |
"""
    headers, rows = parse_markdown_table(markdown, heading="## Configuration parameters")
    fields = rows_to_fields(
        rows,
        headers=headers,
        reference="https://docs.fluentbit.io/manual/data-pipeline/inputs/tail#configuration-parameters",
    )

    assert headers == ["Key", "Description", "Default"]
    assert fields[0]["name"] == "buffer_chunk_size"
    assert fields[0]["data_type"] == "size"
    assert fields[0]["validation_rule"] == {"kind": "size"}
    assert fields[1]["name"] == "enabled"
    assert fields[1]["data_type"] == "boolean"
    assert fields[1]["validation_rule"] == {"kind": "boolean"}


def test_markdown_table_rows_infer_duration_fields() -> None:
    markdown = """
# NGINX

## Configuration parameters

| Key | Description | Default |
| :--- | :--- | :--- |
| `scrape_interval` | The interval to scrape metrics from the NGINX service. | `5s` |
"""
    headers, rows = parse_markdown_table(markdown, heading="## Configuration parameters")
    fields = rows_to_fields(
        rows,
        headers=headers,
        reference="https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters",
    )

    assert headers == ["Key", "Description", "Default"]
    assert fields[0]["name"] == "scrape_interval"
    assert fields[0]["data_type"] == "duration"
    assert fields[0]["validation_rule"] == {"kind": "duration"}


def test_build_catalog_from_docs_auto_prefers_github_mapping(monkeypatch) -> None:
    github_yaml = """
redirects:
    input/stdin: ./pipeline/inputs/standard-input.md
"""
    markdown = """
# Standard Input

The _stdin_ input plugin reads from standard input.

## Configuration parameters

| Key | Description | Default |
| :--- | :--- | :--- |
| `threaded` | Run this input in its own thread. | `false` |
"""
    website_configure = "<a href='/manual/data-pipeline/inputs'>Inputs</a><a href='/manual/data-pipeline/filters'>Filters</a><a href='/manual/data-pipeline/outputs'>Outputs</a>"
    website_section = "<a href='/manual/data-pipeline/inputs/standard-input'>Standard Input</a>"

    def _fetch(url: str, *, timeout: int) -> str:
        if url.endswith("/.gitbook.yaml"):
            return github_yaml
        if url.endswith("/pipeline/inputs/standard-input.md"):
            return markdown
        if url.endswith("/administration/configuring-fluent-bit"):
            return website_configure
        if url.endswith("/data-pipeline/inputs"):
            return website_section
        if url.endswith("/data-pipeline/filters"):
            return ""
        if url.endswith("/data-pipeline/outputs"):
            return ""
        raise AssertionError(url)

    payload = build_catalog_from_docs(
        "5.0.7",
        source="auto",
        timeout=5,
        github_ref="master",
        text_fetcher=_fetch,
    )

    stdin = payload["plugins"]["inputs"]["stdin"]
    assert stdin["title"] == "Standard Input"
    assert stdin["doc_url"].endswith("/data-pipeline/inputs/standard-input")
    assert stdin["fields"][0]["name"] == "threaded"
