# Copyright 2026 opamp.info
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

"""Catalog service indexing test coverage.

Test-case reference: catalog-service/docs/TEST_CASES.md
"""

from __future__ import annotations

from pathlib import Path
import time

from catalog_service.config_metadata import (
    KEY_CONFIG_TYPE,
    KEY_CONFIG_VERSION,
    KEY_SCM_CONFIG_VERSION,
    KEY_SCM_SOURCE_NAME,
)
from catalog_service.config import CatalogServiceConfig, CatalogSource
from catalog_service.service import CatalogFileIndexService


def test_catalog_service_scans_configured_folders_and_header_metadata(tmp_path: Path) -> None:
    source_dir = tmp_path / "catalog-src"
    source_dir.mkdir(parents=True, exist_ok=True)

    with_header = source_dir / "agent-a.yaml"
    with_header.write_text(
        "\n".join(
            [
                "# config-service: config_type=fluentbit",
                "# config-service: version=5.0.4",
                "env:",
                "  _metadata.config_version: 5.0.4",
                "  _metadata.SCM_config_version: release-27",
                "  _metadata.SCM_source_name: team-a-repo",
                "service:",
                "  flush: 1",
            ]
        ),
        encoding="utf-8",
    )

    without_header = source_dir / "agent-b.conf"
    without_header.write_text("<source>\n  @type forward\n</source>\n", encoding="utf-8")

    json_catalog = source_dir / "catalog.json"
    json_catalog.write_text(
        "\n".join(
            [
                "{",
                '  "engine": "fluentbit",',
                '  "version": "5.0.4",',
                '  "config": {',
                '    "env": {',
                '      "_metadata.config_version": "5.0.4",',
                '      "_metadata.SCM_config_version": "json-release-12",',
                '      "_metadata.SCM_source_name": "catalog-json"',
                "    }",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    ignored = source_dir / "ignored.txt"
    ignored.write_text("# config-service: version=skip\n", encoding="utf-8")

    config = CatalogServiceConfig(
        enabled=True,
        menu_label="Catalog",
        route_path="/catalog",
        help_path="/catalog/help",
        ui_base_css_path="/config-service/ui/assets/config_ui.css",
        web_port=8090,
        sources=(CatalogSource(folder="catalog-src", extensions=(".yaml", ".conf", ".json")),),
        raw_payload={},
    )
    service = CatalogFileIndexService(repo_root=tmp_path, config=config)

    payload = service.scan()

    assert payload["total"] == 3
    assert "config_type" in payload["columns"]
    assert "engine" in payload["columns"]
    assert "version" in payload["columns"]
    assert "config_version" in payload["columns"]
    assert "SCM_config_version" in payload["columns"]
    assert "SCM_source_name" in payload["columns"]

    rows = payload["rows"]
    row_a = next(row for row in rows if row["filename"] == "agent-a.yaml")
    row_b = next(row for row in rows if row["filename"] == "agent-b.conf")
    row_c = next(row for row in rows if row["filename"] == "catalog.json")

    assert row_a["folder"] == "catalog-src"
    assert row_a["metadata"][KEY_CONFIG_TYPE] == "fluentbit"
    assert row_a["metadata"]["version"] == "5.0.4"
    assert row_a["metadata"][KEY_CONFIG_VERSION] == "5.0.4"
    assert row_a["metadata"][KEY_SCM_CONFIG_VERSION] == "release-27"
    assert row_a["metadata"][KEY_SCM_SOURCE_NAME] == "team-a-repo"
    assert row_a["last_edited"]

    assert row_b["metadata"] == {"config_type": "fluentd"}
    assert row_c["metadata"] == {
        "config_type": "fluentbit",
        "engine": "fluentbit",
        "version": "5.0.4",
        "config_version": "5.0.4",
        "SCM_config_version": "json-release-12",
        "SCM_source_name": "catalog-json",
    }


def test_catalog_service_refreshes_metadata_when_file_changes(tmp_path: Path) -> None:
    source_dir = tmp_path / "catalog-src"
    source_dir.mkdir(parents=True, exist_ok=True)
    config_file = source_dir / "agent-a.yaml"
    config_file.write_text(
        "\n".join(
            [
                "# config-service: config_type=fluentbit",
                "env:",
                "  _metadata.SCM_config_version: release-27",
                "service:",
                "  flush: 1",
            ]
        ),
        encoding="utf-8",
    )

    config = CatalogServiceConfig(
        enabled=True,
        menu_label="Catalog",
        route_path="/catalog",
        help_path="/catalog/help",
        ui_base_css_path="/config-service/ui/assets/config_ui.css",
        web_port=8090,
        sources=(CatalogSource(folder="catalog-src", extensions=(".yaml",)),),
        raw_payload={},
    )
    service = CatalogFileIndexService(repo_root=tmp_path, config=config)

    first_payload = service.scan()
    cached_payload = service.scan()
    assert cached_payload is first_payload
    first_row = first_payload["rows"][0]
    assert first_row["metadata"]["SCM_config_version"] == "release-27"

    config_file.write_text(
        "\n".join(
            [
                "# config-service: config_type=fluentbit",
                "env:",
                "  _metadata.SCM_config_version: release-28-extra",
                "service:",
                "  flush: 5",
            ]
        ),
        encoding="utf-8",
    )

    refreshed_payload = service.scan()
    refreshed_row = refreshed_payload["rows"][0]
    assert refreshed_payload is not first_payload
    assert refreshed_row["metadata"]["SCM_config_version"] == "release-28-extra"


def test_catalog_service_background_refresh_updates_cache_without_ui_scan(tmp_path: Path) -> None:
    source_dir = tmp_path / "catalog-src"
    source_dir.mkdir(parents=True, exist_ok=True)
    config_file = source_dir / "agent-a.yaml"
    config_file.write_text(
        "\n".join(
            [
                "# config-service: config_type=fluentbit",
                "env:",
                "  _metadata.SCM_config_version: release-27",
                "service:",
                "  flush: 1",
            ]
        ),
        encoding="utf-8",
    )

    config = CatalogServiceConfig(
        enabled=True,
        menu_label="Catalog",
        route_path="/catalog",
        help_path="/catalog/help",
        ui_base_css_path="/config-service/ui/assets/config_ui.css",
        web_port=8090,
        sources=(CatalogSource(folder="catalog-src", extensions=(".yaml",)),),
        raw_payload={},
    )
    service = CatalogFileIndexService(repo_root=tmp_path, config=config)

    initial_payload = service.scan()
    assert service.cached_payload() is initial_payload
    service.start_background_refresh(interval_seconds=0.05)
    try:
        config_file.write_text(
            "\n".join(
                [
                    "# config-service: config_type=fluentbit",
                    "env:",
                    "  _metadata.SCM_config_version: release-29-background-refresh",
                    "service:",
                    "  flush: 7",
                ]
            ),
            encoding="utf-8",
        )

        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            cached_payload = service.cached_payload()
            if cached_payload:
                cached_row = cached_payload["rows"][0]
                if cached_row["metadata"]["SCM_config_version"] == "release-29-background-refresh":
                    break
            time.sleep(0.02)
        else:  # pragma: no cover - assertion guard
            raise AssertionError("expected background refresh to rebuild cached payload")
    finally:
        service.stop_background_refresh()


def test_catalog_service_readonly_file_view_is_limited_to_configured_sources(tmp_path: Path) -> None:
    source_dir = tmp_path / "catalog-src"
    source_dir.mkdir(parents=True, exist_ok=True)
    allowed = source_dir / "agent-a.yaml"
    allowed.write_text("service:\n  flush: 1\n", encoding="utf-8")
    blocked = tmp_path / "outside.yaml"
    blocked.write_text("service:\n  flush: 5\n", encoding="utf-8")

    config = CatalogServiceConfig(
        enabled=True,
        menu_label="Catalog",
        route_path="/catalog",
        help_path="/catalog/help",
        ui_base_css_path="/config-service/ui/assets/config_ui.css",
        web_port=8090,
        sources=(CatalogSource(folder="catalog-src", extensions=(".yaml",)),),
        raw_payload={},
    )
    service = CatalogFileIndexService(repo_root=tmp_path, config=config)

    payload = service.read_file_text(str(allowed))
    assert payload["filename"] == "agent-a.yaml"
    assert "flush: 1" in payload["text"]

    try:
        service.read_file_text(str(blocked))
    except PermissionError:
        pass
    else:  # pragma: no cover - assertion guard
        raise AssertionError("expected readonly access to reject non-catalog files")
