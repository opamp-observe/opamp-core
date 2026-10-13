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

"""Tests for local Fluent Bit catalog additions reporting."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from opamp_dev_tools import fluentbit_changes


class _FakeRuntime:
    """Provide a repository root and capture report console messages.

    Attributes
    ----------
    repo_root:
        Temporary repository containing generated catalog fixtures.
    messages:
        Informational messages emitted by the report command.

    """

    def __init__(self, repo_root: Path) -> None:
        """Initialize the runtime double.

        Parameters
        ----------
        repo_root:
            Temporary repository root used by the command.

        """
        self.repo_root = repo_root
        self.messages: list[str] = []

    def info(self, message: str) -> None:
        """Capture one informational CLI message.

        Parameters
        ----------
        message:
            Message emitted by the additions report.

        """
        self.messages.append(message)


def test_compare_fluentbit_catalogs_reports_plugins_and_attributes(tmp_path: Path) -> None:
    """Comparison should separate new plugins from fields on existing plugins."""
    _write_catalog_version(
        tmp_path,
        "5.9.0",
        {
            "inputs": {"tail": ["path"]},
            "filters": {"grep": ["regex"]},
            "outputs": {"stdout": []},
        },
    )
    _write_catalog_version(
        tmp_path,
        "5.10.0",
        {
            "inputs": {"tail": ["path", "refresh_interval"], "new_input": ["port"]},
            "filters": {"grep": ["regex"]},
            "outputs": {"stdout": []},
        },
    )

    report = fluentbit_changes.compare_fluentbit_catalogs(tmp_path)

    assert report[fluentbit_changes.KEY_CURRENT_VERSION] == "5.10.0"
    assert report[fluentbit_changes.KEY_PREVIOUS_VERSION] == "5.9.0"
    assert report[fluentbit_changes.KEY_COUNTS] == {
        fluentbit_changes.KEY_NEW_PLUGIN_COUNT: 1,
        fluentbit_changes.KEY_NEW_ATTRIBUTE_COUNT: 1,
        fluentbit_changes.KEY_REPRESENTATION_CHANGE_COUNT: 0,
    }
    assert report[fluentbit_changes.KEY_NEW_PLUGINS][0][fluentbit_changes.KEY_PLUGIN] == (
        "new_input"
    )
    assert report[fluentbit_changes.KEY_NEW_PLUGINS][0][fluentbit_changes.KEY_ATTRIBUTES] == [
        "port"
    ]
    assert report[fluentbit_changes.KEY_NEW_ATTRIBUTES][0] == {
        fluentbit_changes.KEY_SECTION: "inputs",
        fluentbit_changes.KEY_PLUGIN: "tail",
        fluentbit_changes.KEY_TITLE: "Tail",
        fluentbit_changes.KEY_ATTRIBUTE: "refresh_interval",
    }


def test_compare_fluentbit_catalogs_honors_explicit_versions(tmp_path: Path) -> None:
    """Explicit versions should allow comparison against a non-adjacent baseline."""
    for version, field_names in (
        ("3.2.10", ["path"]),
        ("4.2.4", ["path", "db"]),
        ("5.0.4", ["path", "db", "offset_key"]),
    ):
        _write_catalog_version(
            tmp_path,
            version,
            {"inputs": {"tail": field_names}, "filters": {}, "outputs": {}},
        )

    report = fluentbit_changes.compare_fluentbit_catalogs(
        tmp_path,
        current_version="v5.0.4",
        previous_version="3.2.10",
    )

    attribute_names = [
        item[fluentbit_changes.KEY_ATTRIBUTE]
        for item in report[fluentbit_changes.KEY_NEW_ATTRIBUTES]
    ]
    assert attribute_names == ["db", "offset_key"]


def test_compare_online_catalog_uses_nearest_earlier_local_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Online comparison should use transient docs and the nearest earlier local baseline."""
    _write_catalog_version(
        tmp_path,
        "5.0.4",
        {"inputs": {"tail": ["path"]}, "filters": {}, "outputs": {}},
    )
    online_catalog = _documentation_catalog(
        {"inputs": {"tail": ["path", "db"], "new_input": ["port"]}}
    )

    def fake_online_loader(
        repo_root: Path,
        **options: object,
    ) -> tuple[str, dict[str, object]]:
        """Return a deterministic upstream catalog and validate loader options."""
        assert repo_root == tmp_path
        assert options["version"] == "5.1.3"
        assert options["source"] == "github"
        assert options["github_ref"] == "v5.1.3"
        assert options["timeout"] == 19
        return "5.1.3", online_catalog

    monkeypatch.setattr(fluentbit_changes, "load_online_catalog", fake_online_loader)

    report = fluentbit_changes.compare_online_fluentbit_catalog(
        tmp_path,
        current_version="5.1.3",
        documentation_source="github",
        github_ref="v5.1.3",
        timeout=19,
    )

    assert report[fluentbit_changes.KEY_PREVIOUS_VERSION] == "5.0.4"
    assert report[fluentbit_changes.KEY_CURRENT_SOURCE] == (fluentbit_changes.ONLINE_CATALOG_SOURCE)
    assert report[fluentbit_changes.KEY_DOCUMENTATION_SOURCE] == "github"
    assert report[fluentbit_changes.KEY_COUNTS] == {
        fluentbit_changes.KEY_NEW_PLUGIN_COUNT: 1,
        fluentbit_changes.KEY_NEW_ATTRIBUTE_COUNT: 1,
        fluentbit_changes.KEY_REPRESENTATION_CHANGE_COUNT: 0,
    }


def test_online_report_command_writes_transient_comparison(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The command should route online options and write both report formats."""
    runtime = _FakeRuntime(tmp_path)
    captured: dict[str, object] = {}
    report = {
        fluentbit_changes.KEY_FORMAT: fluentbit_changes.REPORT_FORMAT,
        fluentbit_changes.KEY_CURRENT_VERSION: "5.1.3",
        fluentbit_changes.KEY_PREVIOUS_VERSION: "5.0.4",
        fluentbit_changes.KEY_CATALOG_ROOT: fluentbit_changes.CATALOG_RELATIVE_PATH.as_posix(),
        fluentbit_changes.KEY_SCOPE_NOTE: fluentbit_changes.ONLINE_REPORT_SCOPE_NOTE,
        fluentbit_changes.KEY_CURRENT_SOURCE: fluentbit_changes.ONLINE_CATALOG_SOURCE,
        fluentbit_changes.KEY_PREVIOUS_SOURCE: fluentbit_changes.LOCAL_CATALOG_SOURCE,
        fluentbit_changes.KEY_DOCUMENTATION_SOURCE: "auto",
        fluentbit_changes.KEY_COUNTS: {
            fluentbit_changes.KEY_NEW_PLUGIN_COUNT: 0,
            fluentbit_changes.KEY_NEW_ATTRIBUTE_COUNT: 0,
            fluentbit_changes.KEY_REPRESENTATION_CHANGE_COUNT: 0,
        },
        fluentbit_changes.KEY_NEW_PLUGINS: [],
        fluentbit_changes.KEY_NEW_ATTRIBUTES: [],
        fluentbit_changes.KEY_REPRESENTATION_CHANGES: [],
    }

    def fake_compare(repo_root: Path, **options: object) -> dict[str, object]:
        """Capture comparison arguments without accessing the network."""
        captured["repo_root"] = repo_root
        captured["options"] = options
        return report

    monkeypatch.setattr(fluentbit_changes, "compare_online_fluentbit_catalog", fake_compare)

    issues_found = fluentbit_changes.report_fluentbit_changes(
        runtime,
        current_version="5.1.3",
        previous_version="5.0.4",
        output_dir="reports",
        online=True,
        documentation_source="auto",
        github_ref="main",
        timeout=23,
    )

    assert issues_found is False
    assert captured["repo_root"] == tmp_path
    assert captured["options"] == {
        "current_version": "5.1.3",
        "previous_version": "5.0.4",
        "documentation_source": "auto",
        "github_ref": "main",
        "timeout": 23,
    }
    markdown_path = tmp_path / "reports" / "fluentbit_5_1_3_vs_5_0_4_additions.md"
    assert "Current catalog: live upstream documentation" in markdown_path.read_text(
        encoding="utf-8"
    )


def test_report_fluentbit_changes_writes_both_formats(tmp_path: Path) -> None:
    """Command execution should write JSON and Markdown and print each addition."""
    _write_catalog_version(
        tmp_path,
        "1.0.0",
        {"inputs": {"tail": ["path"]}, "filters": {}, "outputs": {}},
    )
    _write_catalog_version(
        tmp_path,
        "2.0.0",
        {
            "inputs": {"tail": ["path", "db"]},
            "filters": {"modify": ["add"]},
            "outputs": {},
        },
    )
    runtime = _FakeRuntime(tmp_path)

    issues_found = fluentbit_changes.report_fluentbit_changes(
        runtime,
        output_dir="reports",
    )

    json_path = tmp_path / "reports" / "fluentbit_2_0_0_vs_1_0_0_additions.json"
    markdown_path = tmp_path / "reports" / "fluentbit_2_0_0_vs_1_0_0_additions.md"
    assert issues_found is False
    assert (
        json.loads(json_path.read_text(encoding="utf-8"))[fluentbit_changes.KEY_FORMAT]
        == fluentbit_changes.REPORT_FORMAT
    )
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# Fluent Bit 2.0.0 additions since 1.0.0" in markdown
    assert "`filters` | `modify`" in markdown
    assert "`inputs` | `tail` | Tail | `db`" in markdown
    assert any("NEW PLUGIN filters/modify" in message for message in runtime.messages)
    assert any("NEW ATTRIBUTE inputs/tail/db" in message for message in runtime.messages)


def test_report_with_no_additions_describes_empty_sections(tmp_path: Path) -> None:
    """A stable catalog should produce explicit no-addition Markdown messages."""
    plugins = {"inputs": {"tail": ["path"]}, "filters": {}, "outputs": {}}
    _write_catalog_version(tmp_path, "1.0.0", plugins)
    _write_catalog_version(tmp_path, "1.1.0", plugins)

    report = fluentbit_changes.compare_fluentbit_catalogs(tmp_path)
    markdown = fluentbit_changes.render_change_report_markdown(report)

    assert "No new plugins were identified." in markdown
    assert "No new attributes on existing plugins were identified." in markdown
    assert "No wildcard/concrete representation changes were identified." in markdown


def test_wildcard_changes_are_not_reported_as_new_attributes(tmp_path: Path) -> None:
    """Wildcard/concrete substitutions should be reported as representation changes."""
    _write_catalog_version(
        tmp_path,
        "1.0.0",
        {
            "inputs": {
                "kafka": ["rdkafka.client.id", "rdkafka.bootstrap.servers"],
                "tail": ["db.{option}"],
            },
            "filters": {},
            "outputs": {},
        },
    )
    _write_catalog_version(
        tmp_path,
        "2.0.0",
        {
            "inputs": {
                "kafka": ["rdkafka.{property}"],
                "tail": ["db.sync"],
            },
            "filters": {},
            "outputs": {},
        },
    )

    report = fluentbit_changes.compare_fluentbit_catalogs(tmp_path)

    assert report[fluentbit_changes.KEY_NEW_ATTRIBUTES] == []
    assert (
        report[fluentbit_changes.KEY_COUNTS][fluentbit_changes.KEY_REPRESENTATION_CHANGE_COUNT] == 2
    )
    reasons = {
        change[fluentbit_changes.KEY_REASON]
        for change in report[fluentbit_changes.KEY_REPRESENTATION_CHANGES]
    }
    assert reasons == {
        fluentbit_changes.REASON_CURRENT_WILDCARD,
        fluentbit_changes.REASON_PREVIOUS_WILDCARD,
    }
    markdown = fluentbit_changes.render_change_report_markdown(report)
    assert "## Catalog representation changes" in markdown
    assert "`rdkafka.{property}`" in markdown
    runtime = _FakeRuntime(tmp_path)
    fluentbit_changes._print_report_summary(runtime, report)  # pylint: disable=protected-access
    assert any("REPRESENTATION CHANGE" in message for message in runtime.messages)


def test_unmatched_current_placeholder_is_not_a_representation_change() -> None:
    """An unmatched placeholder remains eligible for candidate-addition reporting."""
    change = fluentbit_changes._find_representation_change(  # pylint: disable=protected-access
        "unrelated.{property}",
        {"existing.attribute"},
    )

    assert change is None


@pytest.mark.parametrize(
    ("current_version", "previous_version", "message"),
    [
        ("9.9.9", "", "is not available"),
        ("2.0.0", "9.9.9", "Previous Fluent Bit catalog version"),
        ("1.0.0", "2.0.0", "must be earlier"),
    ],
)
def test_resolve_version_pair_rejects_invalid_selections(
    current_version: str,
    previous_version: str,
    message: str,
) -> None:
    """Version selection should reject missing or reversed comparisons."""
    with pytest.raises(ValueError, match=message):
        fluentbit_changes.resolve_version_pair(
            ["1.0.0", "2.0.0"],
            current_version=current_version,
            previous_version=previous_version,
        )


def test_discovery_and_loading_reject_incomplete_catalogs(tmp_path: Path) -> None:
    """Missing catalog roots and malformed fields should fail clearly."""
    missing_root = tmp_path / "missing"
    with pytest.raises(FileNotFoundError, match="catalog directory not found"):
        fluentbit_changes.discover_fluentbit_versions(missing_root)

    _write_catalog_version(
        tmp_path,
        "1.0.0",
        {"inputs": {"tail": ["path"]}, "filters": {}, "outputs": {}},
    )
    plugin_path = (
        tmp_path / fluentbit_changes.CATALOG_RELATIVE_PATH / "1.0.0" / "inputs" / "tail.json"
    )
    plugin_path.write_text(
        json.dumps(
            {
                fluentbit_changes.KEY_TITLE: "Tail",
                fluentbit_changes.KEY_FIELDS: [{}],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unnamed field"):
        fluentbit_changes.load_catalog_plugins(
            tmp_path / fluentbit_changes.CATALOG_RELATIVE_PATH,
            "1.0.0",
        )


@pytest.mark.parametrize(
    ("manifest_payload", "message"),
    [
        ({}, "Expected object"),
        ({fluentbit_changes.KEY_ARTIFACT_MANIFEST: {}}, "no parts list"),
        (
            {fluentbit_changes.KEY_ARTIFACT_MANIFEST: {fluentbit_changes.KEY_PARTS: ["invalid"]}},
            "invalid part",
        ),
        (
            {fluentbit_changes.KEY_ARTIFACT_MANIFEST: {fluentbit_changes.KEY_PARTS: [{}]}},
            "part is incomplete",
        ),
    ],
)
def test_loading_rejects_malformed_manifests(
    tmp_path: Path,
    manifest_payload: dict[str, object],
    message: str,
) -> None:
    """Composite manifest validation should explain each malformed structure."""
    version_root = tmp_path / "1.0.0"
    version_root.mkdir()
    for section_name in fluentbit_changes.CATALOG_SECTIONS:
        (version_root / f"{section_name}.json").write_text(
            json.dumps(manifest_payload),
            encoding="utf-8",
        )

    with pytest.raises(ValueError, match=message):
        fluentbit_changes.load_catalog_plugins(tmp_path, "1.0.0")


def test_loading_rejects_non_list_fields_and_non_object_json(tmp_path: Path) -> None:
    """Plugin field shape and JSON root validation should reject unusable catalogs."""
    version_root = tmp_path / "1.0.0"
    version_root.mkdir()
    manifest_payload = {
        fluentbit_changes.KEY_ARTIFACT_MANIFEST: {
            fluentbit_changes.KEY_PARTS: [
                {
                    fluentbit_changes.KEY_POINTER: "/tail",
                    fluentbit_changes.KEY_FILE: "tail.json",
                }
            ]
        }
    }
    (version_root / "inputs.json").write_text(
        json.dumps(manifest_payload),
        encoding="utf-8",
    )
    plugin_path = version_root / "tail.json"
    plugin_path.write_text(json.dumps({fluentbit_changes.KEY_FIELDS: {}}), encoding="utf-8")

    with pytest.raises(ValueError, match="fields must be a list"):
        fluentbit_changes.load_catalog_plugins(tmp_path, "1.0.0")

    plugin_path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="root must be an object"):
        fluentbit_changes.load_catalog_plugins(tmp_path, "1.0.0")


def test_absolute_output_directory_is_preserved(tmp_path: Path) -> None:
    """Absolute report destinations should not be rebased beneath the repository."""
    absolute_output = (tmp_path / "absolute-reports").resolve()

    resolved_output = fluentbit_changes._resolve_output_directory(  # pylint: disable=protected-access
        tmp_path / "repository",
        str(absolute_output),
    )

    assert resolved_output == absolute_output


def test_semantic_version_key_rejects_non_numeric_versions() -> None:
    """Version sorting should reject labels that are not dotted numeric versions."""
    with pytest.raises(ValueError, match="Unsupported Fluent Bit version"):
        fluentbit_changes.semantic_version_key("latest")


def test_resolve_version_pair_requires_two_versions() -> None:
    """Automatic comparison should require a current and a baseline catalog."""
    with pytest.raises(ValueError, match="At least two"):
        fluentbit_changes.resolve_version_pair(["1.0.0"])


@pytest.mark.parametrize(
    ("available_versions", "current_version", "previous_version", "expected"),
    [
        (["3.2.10", "4.2.4", "5.0.4"], "5.1.3", "", "5.0.4"),
        (["3.2.10", "4.2.4", "5.0.4"], "5.1.3", "v4.2.4", "4.2.4"),
    ],
)
def test_resolve_online_previous_version(
    available_versions: list[str],
    current_version: str,
    previous_version: str,
    expected: str,
) -> None:
    """Online baseline selection should support automatic and explicit local versions."""
    assert (
        fluentbit_changes.resolve_online_previous_version(
            available_versions,
            current_version=current_version,
            previous_version=previous_version,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("current_version", "previous_version", "message"),
    [
        ("5.1.3", "4.9.9", "is not available"),
        ("5.1.3", "5.1.3", "must be earlier"),
        ("1.0.0", "", "No retained local"),
    ],
)
def test_resolve_online_previous_version_rejects_invalid_baselines(
    current_version: str,
    previous_version: str,
    message: str,
) -> None:
    """Online comparisons should reject missing, equal, or later local baselines."""
    with pytest.raises(ValueError, match=message):
        fluentbit_changes.resolve_online_previous_version(
            ["3.2.10", "5.1.3"],
            current_version=current_version,
            previous_version=previous_version,
        )


def test_documentation_catalog_loader_rejects_malformed_plugins() -> None:
    """Online catalog validation should reject missing sections and invalid plugin shapes."""
    with pytest.raises(ValueError, match="Expected object 'plugins'"):
        fluentbit_changes.load_documentation_catalog_plugins({})

    incomplete_catalog = {fluentbit_changes.KEY_PLUGINS: {"inputs": {}}}
    with pytest.raises(ValueError, match="Expected object 'filters'"):
        fluentbit_changes.load_documentation_catalog_plugins(incomplete_catalog)

    invalid_plugin = _documentation_catalog({"inputs": {"tail": []}})
    invalid_plugin[fluentbit_changes.KEY_PLUGINS]["inputs"]["tail"] = "invalid"
    with pytest.raises(ValueError, match="must be an object"):
        fluentbit_changes.load_documentation_catalog_plugins(invalid_plugin)

    invalid_fields = _documentation_catalog({"inputs": {"tail": []}})
    invalid_fields[fluentbit_changes.KEY_PLUGINS]["inputs"]["tail"][
        fluentbit_changes.KEY_FIELDS
    ] = {}
    with pytest.raises(ValueError, match="fields must be a list"):
        fluentbit_changes.load_documentation_catalog_plugins(invalid_fields)


def _write_catalog_version(
    repo_root: Path,
    version: str,
    sections: dict[str, dict[str, list[str]]],
) -> None:
    """Write one minimal composite catalog version for a unit test.

    Parameters
    ----------
    repo_root:
        Temporary repository root that receives the canonical catalog path.
    version:
        Version directory created for the fixture.
    sections:
        Section, plugin, and field-name mappings written to manifests and shards.

    """
    version_root = repo_root / fluentbit_changes.CATALOG_RELATIVE_PATH / version
    version_root.mkdir(parents=True, exist_ok=True)
    for section_name in fluentbit_changes.CATALOG_SECTIONS:
        plugin_fields = sections.get(section_name, {})
        parts: list[dict[str, str]] = []
        for plugin_name, field_names in plugin_fields.items():
            relative_file = f"{section_name}/{plugin_name}.json"
            plugin_path = version_root / relative_file
            plugin_path.parent.mkdir(parents=True, exist_ok=True)
            plugin_path.write_text(
                json.dumps(
                    {
                        fluentbit_changes.KEY_TITLE: plugin_name.replace("_", " ").title(),
                        fluentbit_changes.KEY_FIELDS: [
                            {fluentbit_changes.KEY_NAME: field_name} for field_name in field_names
                        ],
                    }
                ),
                encoding="utf-8",
            )
            parts.append(
                {
                    fluentbit_changes.KEY_POINTER: f"/{plugin_name}",
                    fluentbit_changes.KEY_FILE: relative_file,
                }
            )
        (version_root / f"{section_name}.json").write_text(
            json.dumps(
                {fluentbit_changes.KEY_ARTIFACT_MANIFEST: {fluentbit_changes.KEY_PARTS: parts}}
            ),
            encoding="utf-8",
        )


def _documentation_catalog(
    sections: dict[str, dict[str, list[str]]],
) -> dict[str, object]:
    """Build one minimal in-memory documentation catalog fixture.

    Parameters
    ----------
    sections:
        Section, plugin, and field-name mappings included in the fixture.

    """
    plugins: dict[str, object] = {}
    for section_name in fluentbit_changes.CATALOG_SECTIONS:
        plugin_records: dict[str, object] = {}
        for plugin_name, field_names in sections.get(section_name, {}).items():
            plugin_records[plugin_name] = {
                fluentbit_changes.KEY_TITLE: plugin_name.replace("_", " ").title(),
                fluentbit_changes.KEY_FIELDS: [
                    {fluentbit_changes.KEY_NAME: field_name} for field_name in field_names
                ],
            }
        plugins[section_name] = plugin_records
    return {fluentbit_changes.KEY_PLUGINS: plugins}
