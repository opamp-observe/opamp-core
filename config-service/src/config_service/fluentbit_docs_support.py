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

"""Retrieve and parse Fluent Bit documentation into Config Service catalogs."""

from __future__ import annotations

import copy
import json
import logging
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

SECTION_KIND = {
    "inputs": "input",
    "filters": "filter",
    "outputs": "output",
}
SECTION_FLAG = {
    "inputs": "-i",
    "filters": "-F",
    "outputs": "-o",
}
SECTION_LABEL = {
    "inputs": "input",
    "filters": "filter",
    "outputs": "output",
}
SECTION_INDEX_CANDIDATES = {
    "inputs": ("data-pipeline/inputs", "pipeline/inputs"),
    "filters": ("data-pipeline/filters", "pipeline/filters"),
    "outputs": ("data-pipeline/outputs", "pipeline/outputs"),
}
SIZE_PATTERN = re.compile(r"^\d+(?:[kKmMgG](?:[bB])?|[bB])?$")
DURATION_PATTERN = re.compile(r"^\d+(ns|us|ms|s|m|h|d)?$")
GENERIC_DESCRIPTION_TEMPLATE = "Fluent Bit {kind} plugin: {title}."
USER_AGENT = "Mozilla/5.0 (compatible; config-service-fluentbit-docs/1.0)"
FLUENTBIT_LATEST_RELEASE_URL = "https://api.github.com/repos/fluent/fluent-bit/releases/latest"
KEY_TAG_NAME = "tag_name"
SEMANTIC_VERSION_PATTERN = re.compile(r"^v?(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)$")
LOGGER = logging.getLogger("fluentbit_docs_support")
LOGGER.setLevel(logging.DEBUG)


@dataclass(frozen=True)
class PluginNameResolution:
    current_name: str
    expected_name: str | None
    evidence: str | None
    doc_url: str


@dataclass(frozen=True)
class ScrapedPluginPage:
    name: str
    title: str
    doc_url: str
    description: str
    fields: list[dict[str, Any]]
    extraction: dict[str, Any]


class _HtmlTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if data:
            self._chunks.append(data)

    def text(self) -> str:
        return "\n".join(self._chunks)


class _HrefCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href_stack: list[str | None] = []
        self._text_stack: list[list[str]] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "a":
            attrs_map = dict(attrs)
            self._href_stack.append(attrs_map.get("href"))
            self._text_stack.append([])
        elif self._text_stack:
            self._text_stack[-1].append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == "a" and self._href_stack:
            href = self._href_stack.pop()
            text = "".join(self._text_stack.pop()).strip()
            if href:
                self.links.append((href, re.sub(r"\s+", " ", text)))
        elif self._text_stack:
            self._text_stack[-1].append(" ")

    def handle_data(self, data: str) -> None:
        if self._skip_depth or not self._text_stack:
            return
        self._text_stack[-1].append(data)


class _WebsitePluginPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.description = ""
        self.headers: list[str] = []
        self.rows: list[list[str]] = []
        self._skip_depth = 0
        self._in_h1 = False
        self._h1_chunks: list[str] = []
        self._in_heading = False
        self._heading_chunks: list[str] = []
        self._before_config = True
        self._in_paragraph = False
        self._paragraph_chunks: list[str] = []
        self._paragraphs: list[str] = []
        self._collect_tables = False
        self._row_depth = 0
        self._row_cells: list[str] = []
        self._row_has_header = False
        self._cell_depth = 0
        self._cell_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        attrs_map = dict(attrs)
        role = attrs_map.get("role")
        if tag == "h1":
            self._in_h1 = True
            self._h1_chunks = []
        elif tag in {"h2", "h3"}:
            self._in_heading = True
            self._heading_chunks = []
        elif tag == "p" and self._before_config:
            self._in_paragraph = True
            self._paragraph_chunks = []

        if self._cell_depth > 0:
            self._cell_depth += 1
        elif self._collect_tables and role in {"cell", "columnheader"}:
            self._cell_depth = 1
            self._cell_chunks = []

        if self._row_depth > 0:
            self._row_depth += 1
        elif self._collect_tables and role == "row":
            self._row_depth = 1
            self._row_cells = []
            self._row_has_header = False

        if role == "columnheader":
            self._row_has_header = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return

        if self._cell_depth > 0:
            self._cell_depth -= 1
            if self._cell_depth == 0:
                self._row_cells.append(_normalize_whitespace("".join(self._cell_chunks)))
                self._cell_chunks = []

        if self._row_depth > 0:
            self._row_depth -= 1
            if self._row_depth == 0 and self._row_cells:
                row = [item for item in self._row_cells if item]
                if row:
                    if self._row_has_header and not self.headers:
                        self.headers = row
                    elif row != self.headers:
                        self.rows.append(row)
                self._row_cells = []

        if tag == "h1" and self._in_h1:
            self.title = _normalize_whitespace("".join(self._h1_chunks))
            self._in_h1 = False
        elif tag in {"h2", "h3"} and self._in_heading:
            heading = _normalize_whitespace("".join(self._heading_chunks))
            if heading.lower() == "configuration parameters":
                self._collect_tables = True
                self._before_config = False
            elif self._collect_tables and heading:
                self._collect_tables = False
            self._in_heading = False
        elif tag == "p" and self._in_paragraph:
            paragraph = _normalize_whitespace("".join(self._paragraph_chunks))
            if paragraph and "supported event types:" not in paragraph.lower():
                self._paragraphs.append(paragraph)
                if not self.description:
                    self.description = paragraph
            self._in_paragraph = False

    def handle_data(self, data: str) -> None:
        if self._skip_depth or not data:
            return
        if self._in_h1:
            self._h1_chunks.append(data)
        if self._in_heading:
            self._heading_chunks.append(data)
        if self._in_paragraph:
            self._paragraph_chunks.append(data)
        if self._cell_depth > 0:
            self._cell_chunks.append(data)


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _docs_series(version: str) -> str:
    parts = str(version).split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return str(version)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_url_text(url: str, *, timeout: int) -> str:
    """Retrieve one HTTP(S) documentation resource as UTF-8 text.

    Parameters
    ----------
    url:
        Absolute HTTP(S) URL permitted for documentation retrieval.
    timeout:
        Maximum number of seconds to wait for the response.

    """
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported documentation URL scheme '{parsed_url.scheme}'")
    request = Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.read().decode("utf-8", errors="ignore")


def resolve_current_stable_version(
    *,
    timeout: int,
    text_fetcher: Callable[..., str] = fetch_url_text,
) -> str:
    """Resolve the current stable Fluent Bit version from the GitHub releases API.

    Parameters
    ----------
    timeout:
        HTTP timeout passed to the supplied text loader.
    text_fetcher:
        Injectable HTTP text loader used by tests and normal documentation retrieval.

    """
    release_text = text_fetcher(FLUENTBIT_LATEST_RELEASE_URL, timeout=timeout)
    try:
        release_payload = json.loads(release_text)
    except json.JSONDecodeError as exc:
        raise ValueError("Fluent Bit latest-release response is not valid JSON") from exc
    if not isinstance(release_payload, Mapping):
        raise ValueError("Fluent Bit latest-release response must be a JSON object")
    tag_name = release_payload.get(KEY_TAG_NAME)
    if not isinstance(tag_name, str):
        raise ValueError("Fluent Bit latest release did not provide a semantic tag_name")
    version_match = SEMANTIC_VERSION_PATTERN.fullmatch(tag_name.strip())
    if version_match is None:
        raise ValueError("Fluent Bit latest release did not provide a semantic tag_name")
    return version_match.group(1)


def fetch_page_text(url: str, *, timeout: int) -> str:
    html = fetch_url_text(url, timeout=timeout)
    parser = _HtmlTextExtractor()
    parser.feed(html)
    return parser.text()


def extract_expected_name(page_text: str, section: str) -> tuple[str | None, str | None]:
    kind = SECTION_KIND[section]
    flag = SECTION_FLAG[section]
    patterns = (
        (
            re.compile(rf"\[{kind}\s*:\s*([a-z0-9_-]+)", re.IGNORECASE),
            f"[{kind}:name]",
        ),
        (
            re.compile(rf"\[{section[:-1]}\]\s+name\s+([a-z0-9_-]+)", re.IGNORECASE),
            f"[{section[:-1].upper()}] Name",
        ),
        (
            re.compile(rf"{re.escape(flag)}\s+([a-z0-9_-]+)", re.IGNORECASE),
            flag,
        ),
    )
    for pattern, label in patterns:
        match = pattern.search(page_text)
        if match:
            return match.group(1).strip().lower(), label
    return None, None


def resolve_expected_name(
    doc_url: str,
    section: str,
    *,
    timeout: int,
    page_cache: dict[str, str] | None = None,
    text_fetcher: Callable[..., str] = fetch_page_text,
) -> tuple[str | None, str | None]:
    if not doc_url:
        return None, None
    page_text = page_cache.get(doc_url) if page_cache is not None else None
    if page_text is None:
        page_text = text_fetcher(doc_url, timeout=timeout)
        if page_cache is not None:
            page_cache[doc_url] = page_text
    return extract_expected_name(page_text, section)


def collect_plugin_name_resolutions(
    section_plugins: Mapping[str, dict[str, Any]],
    section: str,
    *,
    timeout: int,
    page_cache: dict[str, str] | None = None,
    text_fetcher: Callable[..., str] = fetch_page_text,
) -> list[PluginNameResolution]:
    resolutions: list[PluginNameResolution] = []
    for current_name, plugin_def in sorted(section_plugins.items()):
        doc_url = ""
        if isinstance(plugin_def, dict):
            doc_url = str(plugin_def.get("doc_url") or "").strip()
        expected_name, evidence = resolve_expected_name(
            doc_url,
            section,
            timeout=timeout,
            page_cache=page_cache,
            text_fetcher=text_fetcher,
        )
        resolutions.append(
            PluginNameResolution(
                current_name=str(current_name),
                expected_name=expected_name,
                evidence=evidence,
                doc_url=doc_url,
            )
        )
    return resolutions


def conflicting_expected_names(resolutions: list[PluginNameResolution]) -> dict[str, list[str]]:
    collisions: dict[str, set[str]] = {}
    for resolution in resolutions:
        if not resolution.expected_name:
            continue
        collisions.setdefault(resolution.expected_name, set()).add(resolution.current_name)
    return {
        expected_name: sorted(current_names)
        for expected_name, current_names in collisions.items()
        if len(current_names) > 1
    }


def normalize_plugin_map(
    section_plugins: Mapping[str, dict[str, Any]],
    section: str,
    *,
    timeout: int,
    logger: logging.Logger | None = None,
    page_cache: dict[str, str] | None = None,
    text_fetcher: Callable[..., str] = fetch_page_text,
) -> tuple[dict[str, dict[str, Any]], list[PluginNameResolution], dict[str, list[str]]]:
    resolutions = collect_plugin_name_resolutions(
        section_plugins,
        section,
        timeout=timeout,
        page_cache=page_cache,
        text_fetcher=text_fetcher,
    )
    resolution_map = {item.current_name: item for item in resolutions}
    collisions = conflicting_expected_names(resolutions)
    normalized: dict[str, dict[str, Any]] = {}

    for current_name, plugin_def in sorted(section_plugins.items()):
        resolution = resolution_map[str(current_name)]
        target_name = str(current_name)
        if resolution.expected_name and resolution.expected_name != resolution.current_name:
            if resolution.expected_name in collisions:
                if logger:
                    logger.warning(
                        "skip plugin-name collision section=%s from=%s expected=%s conflicts=%s url=%s",
                        section,
                        resolution.current_name,
                        resolution.expected_name,
                        ",".join(collisions[resolution.expected_name]),
                        resolution.doc_url,
                    )
            else:
                target_name = resolution.expected_name
                if logger:
                    logger.info(
                        "normalize plugin name section=%s from=%s to=%s evidence=%s url=%s",
                        section,
                        resolution.current_name,
                        resolution.expected_name,
                        resolution.evidence,
                        resolution.doc_url,
                    )
        if target_name in normalized:
            raise ValueError(f"Duplicate normalized plugin name '{target_name}' in section '{section}'")
        normalized[target_name] = copy.deepcopy(plugin_def)

    return normalized, resolutions, collisions


def resolve_website_configure_url(
    version: str,
    *,
    timeout: int,
    text_fetcher: Callable[..., str] = fetch_url_text,
) -> str:
    for base in website_manual_root_candidates(version):
        url = f"{base}/administration/configuring-fluent-bit"
        try:
            text_fetcher(url, timeout=timeout)
        except (HTTPError, URLError):
            continue
        return url
    raise ValueError(f"Unable to resolve Fluent Bit docs root for version '{version}'.")


def website_manual_root_candidates(version: str) -> list[str]:
    roots: list[str] = []
    exact = str(version).strip()
    series = _docs_series(version)
    for suffix in (exact, series, ""):
        if suffix:
            candidate = f"https://docs.fluentbit.io/manual/{suffix}"
        else:
            candidate = "https://docs.fluentbit.io/manual"
        if candidate not in roots:
            roots.append(candidate.rstrip("/"))
    return roots


def parse_html_links(html: str, *, base_url: str) -> list[tuple[str, str]]:
    parser = _HrefCollector()
    parser.feed(html)
    return [(urljoin(base_url, href), text) for href, text in parser.links]


def discover_website_section_urls(
    version: str,
    *,
    timeout: int,
    text_fetcher: Callable[..., str] = fetch_url_text,
) -> dict[str, str]:
    configure_url = resolve_website_configure_url(version, timeout=timeout, text_fetcher=text_fetcher)
    html = text_fetcher(configure_url, timeout=timeout)
    links = parse_html_links(html, base_url=configure_url)
    section_urls: dict[str, str] = {}
    parsed_configure = urlparse(configure_url)
    root_prefix = f"{parsed_configure.scheme}://{parsed_configure.netloc}"

    for section, candidates in SECTION_INDEX_CANDIDATES.items():
        for href, _ in links:
            href_path = urlparse(href).path.rstrip("/")
            if any(href_path.endswith(f"/{candidate}") for candidate in candidates):
                section_urls[section] = f"{root_prefix}{href_path}"
                break
        if section in section_urls:
            continue
        manual_root = configure_url.removesuffix("/administration/configuring-fluent-bit")
        for candidate in candidates:
            derived = f"{manual_root}/{candidate}"
            try:
                text_fetcher(derived, timeout=timeout)
            except (HTTPError, URLError):
                continue
            section_urls[section] = derived
            break
    missing = sorted(set(SECTION_KIND) - set(section_urls))
    if missing:
        raise ValueError(f"Unable to resolve section index pages for: {', '.join(missing)}")
    return section_urls


def discover_website_plugin_urls(
    section_url: str,
    section: str,
    *,
    timeout: int,
    text_fetcher: Callable[..., str] = fetch_url_text,
) -> list[str]:
    html = text_fetcher(section_url, timeout=timeout)
    links = parse_html_links(html, base_url=section_url)
    section_path = urlparse(section_url).path.rstrip("/")
    discovered: list[str] = []
    seen: set[str] = set()
    for href, text in links:
        parsed = urlparse(href)
        path = parsed.path.rstrip("/")
        if not path.startswith(f"{section_path}/"):
            continue
        tail = path.removeprefix(f"{section_path}/")
        if not tail or "/" in tail:
            continue
        if text and text.lower() in {"inputs", "filters", "outputs"}:
            continue
        normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
        if normalized not in seen:
            seen.add(normalized)
            discovered.append(normalized)
    return discovered


def parse_website_plugin_page(html: str, *, doc_url: str, section: str) -> ScrapedPluginPage:
    parser = _WebsitePluginPageParser()
    parser.feed(html)
    expected_name, _ = extract_expected_name(_HtmlTextExtractor().text(), section)
    # Extract name again from real page text because the bare parser only collects structural data.
    page_text_parser = _HtmlTextExtractor()
    page_text_parser.feed(html)
    page_text = page_text_parser.text()
    expected_name, _ = extract_expected_name(page_text, section)
    plugin_name = expected_name or Path(urlparse(doc_url).path).name
    fields = rows_to_fields(
        parser.rows,
        headers=parser.headers,
        reference=f"{doc_url}#configuration-parameters",
    )
    return ScrapedPluginPage(
        name=plugin_name,
        title=parser.title or plugin_name,
        doc_url=doc_url,
        description=GENERIC_DESCRIPTION_TEMPLATE.format(kind=SECTION_LABEL[section], title=parser.title or plugin_name),
        fields=fields,
        extraction=_extraction_payload(parser.headers, doc_url, fields),
    )


def parse_gitbook_redirects(text: str) -> dict[str, dict[str, str]]:
    mappings: dict[str, dict[str, str]] = {section: {} for section in SECTION_KIND}
    pattern = re.compile(r"^\s*(input|filter|output)/([A-Za-z0-9_-]+)\s*:\s*(\./\S+)\s*$")
    section_map = {"input": "inputs", "filter": "filters", "output": "outputs"}
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        match = pattern.match(line)
        if not match:
            continue
        singular, plugin_name, path = match.groups()
        if path.endswith("/"):
            continue
        mappings[section_map[singular]][plugin_name.lower()] = path.strip()
    return mappings


def github_ref_candidates(version: str, explicit_ref: str | None = None) -> list[str]:
    if explicit_ref:
        return [explicit_ref]
    series = _docs_series(version)
    candidates = [f"v{version}", version, f"v{series}", series, "master", "main"]
    seen: set[str] = set()
    ordered: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    return ordered


def resolve_github_ref(
    version: str,
    *,
    timeout: int,
    explicit_ref: str | None = None,
    text_fetcher: Callable[..., str] = fetch_url_text,
) -> str:
    for candidate in github_ref_candidates(version, explicit_ref):
        url = f"https://raw.githubusercontent.com/fluent/fluent-bit-docs/{candidate}/.gitbook.yaml"
        try:
            text_fetcher(url, timeout=timeout)
        except (HTTPError, URLError):
            continue
        return candidate
    raise ValueError(f"Unable to resolve a GitHub docs ref for Fluent Bit version '{version}'.")


def github_raw_url(ref: str, path: str) -> str:
    normalized = path.removeprefix("./")
    return f"https://raw.githubusercontent.com/fluent/fluent-bit-docs/{ref}/{normalized}"


def parse_markdown_plugin_page(markdown: str, *, doc_url: str, expected_name: str, section: str) -> ScrapedPluginPage:
    title = expected_name
    description = ""
    lines = markdown.splitlines()
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break
    before_config = True
    paragraph_parts: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Configuration parameters"):
            before_config = False
            continue
        if not before_config:
            continue
        if (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith("{%")
            or stripped.startswith("|")
            or stripped.startswith("```")
        ):
            if paragraph_parts and not description:
                candidate = _normalize_whitespace(" ".join(paragraph_parts))
                if candidate:
                    description = candidate
                paragraph_parts = []
            continue
        paragraph_parts.append(stripped)
    if paragraph_parts and not description:
        description = _normalize_whitespace(" ".join(paragraph_parts))

    headers, rows = parse_markdown_table(markdown, heading="## Configuration parameters")
    fields = rows_to_fields(
        rows,
        headers=headers,
        reference=f"{doc_url}#configuration-parameters",
    )
    return ScrapedPluginPage(
        name=expected_name,
        title=title,
        doc_url=doc_url,
        description=GENERIC_DESCRIPTION_TEMPLATE.format(kind=SECTION_LABEL[section], title=title),
        fields=fields,
        extraction=_extraction_payload(headers, doc_url, fields),
    )


def parse_markdown_table(markdown: str, *, heading: str) -> tuple[list[str], list[list[str]]]:
    capture = False
    table_lines: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith(heading):
            capture = True
            continue
        if not capture:
            continue
        if line.startswith("## ") and table_lines:
            break
        if line.startswith("|"):
            table_lines.append(line)
        elif table_lines:
            break
    if len(table_lines) < 2:
        return [], []
    headers = [_strip_markdown_cell(cell) for cell in table_lines[0].strip("|").split("|")]
    rows: list[list[str]] = []
    for line in table_lines[2:]:
        cells = [_strip_markdown_cell(cell) for cell in line.strip("|").split("|")]
        if any(cells):
            rows.append(cells)
    return headers, rows


def _strip_markdown_cell(value: str) -> str:
    cleaned = value.strip()
    cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = cleaned.replace("\\|", "|")
    cleaned = cleaned.replace("_none_", "none")
    return _normalize_whitespace(cleaned)


def infer_field_payload(name: str, description: str, default: Any, *, raw_default: str) -> dict[str, Any]:
    normalized_name = name.strip()
    references_parser = normalized_name in {"parser", "docker_mode_parser"} or normalized_name.endswith(".parser")
    data_type = "string"
    validation_rule: dict[str, Any] | None = None

    if isinstance(default, bool):
        data_type = "boolean"
        validation_rule = {"kind": "boolean"}
    elif isinstance(default, int) and not isinstance(default, bool):
        data_type = "integer"
        validation_rule = {"kind": "range"}
    elif isinstance(default, float):
        data_type = "number"
        validation_rule = {"kind": "range"}
    else:
        raw_default_lower = str(raw_default).strip().lower()
        desc_lower = description.lower()
        if SIZE_PATTERN.fullmatch(str(raw_default).strip()) or "unit size" in desc_lower:
            data_type = "size"
            validation_rule = {"kind": "size"}
        elif DURATION_PATTERN.fullmatch(str(raw_default).strip()) or " nanosecond " in f" {desc_lower} ":
            data_type = "duration"
            validation_rule = {"kind": "duration"}
        elif raw_default_lower in {"true", "false"}:
            data_type = "boolean"
            validation_rule = {"kind": "boolean"}
            default = raw_default_lower == "true"
        elif re.fullmatch(r"-?\d+", str(raw_default).strip()):
            data_type = "integer"
            default = int(str(raw_default).strip())
            validation_rule = {"kind": "range"}
        elif re.fullmatch(r"-?\d+\.\d+", str(raw_default).strip()):
            data_type = "number"
            default = float(str(raw_default).strip())
            validation_rule = {"kind": "range"}
        elif "possible values:" in desc_lower:
            enum_values = _enum_values_from_description(description)
            if enum_values:
                data_type = "enum"
                validation_rule = {"kind": "regex_string", "pattern": "^(" + "|".join(re.escape(item) for item in enum_values) + ")$"}
    field: dict[str, Any] = {
        "name": normalized_name,
        "required": False,
        "description": description,
        "reference": "",
        "data_type": data_type,
        "validation_rule": validation_rule,
    }
    if default is not None:
        field["default"] = default
    if references_parser:
        field["references_parser"] = True
    return field


def _enum_values_from_description(description: str) -> list[str]:
    match = re.search(r"possible values:\s*([^.;]+)", description, re.IGNORECASE)
    if not match:
        return []
    values_text = match.group(1)
    values = []
    for token in re.split(r",|\bor\b|\band\b", values_text):
        cleaned = token.strip().strip("`'\".")
        if cleaned:
            values.append(cleaned)
    return values


def rows_to_fields(rows: Iterable[list[str]], *, headers: list[str], reference: str) -> list[dict[str, Any]]:
    field_rows = list(rows)
    header_lookup = {name.lower(): idx for idx, name in enumerate(headers)}
    key_index = header_lookup.get("key", 0)
    description_index = header_lookup.get("description", 1 if len(headers) > 1 else 0)
    default_index = header_lookup.get("default")
    required_index = header_lookup.get("required")
    fields: list[dict[str, Any]] = []
    for row in field_rows:
        if key_index >= len(row):
            continue
        key = row[key_index].strip().strip("`")
        if not key:
            continue
        description = row[description_index].strip() if description_index < len(row) else ""
        raw_default = row[default_index].strip() if default_index is not None and default_index < len(row) else ""
        default = _parse_default_value(raw_default)
        field = infer_field_payload(key, description, default, raw_default=raw_default)
        field["reference"] = reference
        if required_index is not None and required_index < len(row):
            required_text = row[required_index].strip().lower()
            field["required"] = required_text in {"yes", "true", "required"}
        fields.append(field)
    return fields


def _parse_default_value(value: str) -> Any:
    cleaned = value.strip().strip("`")
    if not cleaned or cleaned.lower() in {"none", "_none_", "n/a"}:
        return None
    if cleaned.lower() == "true":
        return True
    if cleaned.lower() == "false":
        return False
    if re.fullmatch(r"-?\d+", cleaned):
        return int(cleaned)
    if re.fullmatch(r"-?\d+\.\d+", cleaned):
        return float(cleaned)
    return cleaned


def _extraction_payload(headers: list[str], doc_url: str, fields: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "ok" if fields else "no_configuration_parameters",
        "reference": f"{doc_url}#configuration-parameters",
        "table_header": headers,
    }


def common_sections(version: str, *, manual_root: str) -> dict[str, Any]:
    pipeline_ref = f"{manual_root}/administration/configuring-fluent-bit/yaml/pipeline-section"
    return {
        "inputs": {
            "fields": [
                {
                    "name": "name",
                    "required": True,
                    "description": "Name of the input plugin.",
                    "reference": f"{pipeline_ref}#inputs",
                },
                {
                    "name": "tag",
                    "required": False,
                    "description": "Tag name associated to all records coming from this plugin.",
                    "reference": f"{pipeline_ref}#inputs",
                },
                {
                    "name": "log_level",
                    "required": False,
                    "description": "Set the plugin's logging verbosity level.",
                    "reference": f"{pipeline_ref}#inputs",
                    "data_type": "enum",
                    "enum_options": ["off", "trace", "debug", "info", "warn", "error"],
                },
            ]
        },
        "filters": {
            "fields": [
                {
                    "name": "name",
                    "required": True,
                    "description": "Name of the filter plugin.",
                    "reference": f"{pipeline_ref}#filters",
                },
                {
                    "name": "match",
                    "required": False,
                    "description": "A pattern to match against the tags of incoming records.",
                    "reference": f"{pipeline_ref}#filters",
                },
                {
                    "name": "match_regex",
                    "required": False,
                    "description": "A regular expression to match against the tags of incoming records.",
                    "reference": f"{pipeline_ref}#filters",
                },
                {
                    "name": "log_level",
                    "required": False,
                    "description": "Set the plugin's logging verbosity level.",
                    "reference": f"{pipeline_ref}#filters",
                    "data_type": "enum",
                    "enum_options": ["off", "trace", "debug", "info", "warn", "error"],
                },
            ]
        },
        "outputs": {
            "fields": [
                {
                    "name": "name",
                    "required": True,
                    "description": "Name of the output plugin.",
                    "reference": f"{pipeline_ref}#outputs",
                },
                {
                    "name": "match",
                    "required": False,
                    "description": "A pattern to match against the tags of incoming records.",
                    "reference": f"{pipeline_ref}#outputs",
                },
                {
                    "name": "match_regex",
                    "required": False,
                    "description": "A regular expression to match against the tags of incoming records.",
                    "reference": f"{pipeline_ref}#outputs",
                },
                {
                    "name": "log_level",
                    "required": False,
                    "description": "Set the plugin's logging verbosity level.",
                    "reference": f"{pipeline_ref}#outputs",
                    "data_type": "enum",
                    "enum_options": ["off", "trace", "debug", "info", "warn", "error"],
                },
            ]
        },
    }


def empty_catalog(version: str, *, manual_root: str) -> dict[str, Any]:
    return {
        "catalog_type": "fluent-bit-plugin-catalog",
        "catalog_scope": "all_plugins",
        "schema_version": "1.1.0",
        "fluent_bit_version": version,
        "fluent_bit_series": _docs_series(version),
        "generated_at": utc_timestamp(),
        "release_notes": f"https://fluentbit.io/announcements/v{version}/#release-notes-v{version}",
        "plugins": {
            "filters": {},
            "inputs": {},
            "outputs": {},
        },
        "common": common_sections(version, manual_root=manual_root),
    }


def build_catalog_from_website(
    version: str,
    *,
    timeout: int,
    logger: logging.Logger | None = None,
    text_fetcher: Callable[..., str] = fetch_url_text,
) -> dict[str, Any]:
    active_logger = logger or LOGGER
    section_urls = discover_website_section_urls(version, timeout=timeout, text_fetcher=text_fetcher)
    manual_root = next(iter(section_urls.values())).split("/data-pipeline/")[0].split("/pipeline/")[0].rstrip("/")
    payload = empty_catalog(version, manual_root=manual_root)
    for section, section_url in section_urls.items():
        for plugin_url in discover_website_plugin_urls(section_url, section, timeout=timeout, text_fetcher=text_fetcher):
            html = text_fetcher(plugin_url, timeout=timeout)
            page = parse_website_plugin_page(html, doc_url=plugin_url, section=section)
            payload["plugins"][section][page.name] = {
                "title": page.title,
                "doc_url": page.doc_url,
                "fields": page.fields,
                "extraction": page.extraction,
                "description": page.description,
            }
            active_logger.info("scraped plugin version=%s section=%s plugin=%s url=%s", version, section, page.name, plugin_url)
    return payload


def build_catalog_from_github(
    version: str,
    *,
    timeout: int,
    github_ref: str | None = None,
    logger: logging.Logger | None = None,
    text_fetcher: Callable[..., str] = fetch_url_text,
) -> dict[str, Any]:
    active_logger = logger or LOGGER
    ref = resolve_github_ref(version, timeout=timeout, explicit_ref=github_ref, text_fetcher=text_fetcher)
    redirects_text = text_fetcher(github_raw_url(ref, ".gitbook.yaml"), timeout=timeout)
    mappings = parse_gitbook_redirects(redirects_text)
    section_urls = discover_website_section_urls(version, timeout=timeout, text_fetcher=text_fetcher)
    manual_root = next(iter(section_urls.values())).split("/data-pipeline/")[0].split("/pipeline/")[0].rstrip("/")
    payload = empty_catalog(version, manual_root=manual_root)

    for section, section_map in mappings.items():
        section_url = section_urls[section]
        for plugin_name, markdown_path in sorted(section_map.items()):
            markdown = text_fetcher(github_raw_url(ref, markdown_path), timeout=timeout)
            doc_url = f"{section_url}/{Path(markdown_path).stem}"
            page = parse_markdown_plugin_page(
                markdown,
                doc_url=doc_url,
                expected_name=plugin_name,
                section=section,
            )
            payload["plugins"][section][plugin_name] = {
                "title": page.title,
                "doc_url": page.doc_url,
                "fields": page.fields,
                "extraction": page.extraction,
                "description": page.description,
            }
            active_logger.info(
                "scraped github plugin version=%s ref=%s section=%s plugin=%s source=%s",
                version,
                ref,
                section,
                plugin_name,
                markdown_path,
            )
    return payload


def build_catalog_from_docs(
    version: str,
    *,
    source: str,
    timeout: int,
    github_ref: str | None = None,
    logger: logging.Logger | None = None,
    text_fetcher: Callable[..., str] = fetch_url_text,
) -> dict[str, Any]:
    if source == "website":
        return build_catalog_from_website(version, timeout=timeout, logger=logger, text_fetcher=text_fetcher)
    if source == "github":
        return build_catalog_from_github(
            version,
            timeout=timeout,
            github_ref=github_ref,
            logger=logger,
            text_fetcher=text_fetcher,
        )
    if source == "auto":
        try:
            return build_catalog_from_github(
                version,
                timeout=timeout,
                github_ref=github_ref,
                logger=logger,
                text_fetcher=text_fetcher,
            )
        except Exception as exc:
            (logger or LOGGER).warning("github scrape fallback version=%s reason=%s", version, exc)
            return build_catalog_from_website(version, timeout=timeout, logger=logger, text_fetcher=text_fetcher)
    raise ValueError(f"Unsupported Fluent Bit docs source '{source}'.")
