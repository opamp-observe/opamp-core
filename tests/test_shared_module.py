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

"""Shared module test coverage.

Test-case reference: shared/README.md
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path

import pytest
from shared.observability import (
    DEFAULT_EXPORT_INTERVAL_SECONDS,
    load_observability_config_from_payload,
)
from shared.opamp_config import (
    AgentCapabilities,
    anyvalue_to_string,
    load_json_config,
    normalize_component_entry_points,
    parse_capabilities,
    resolve_component_callable,
)
from shared.packaging_warnings import build_cli_missing_warning
from shared.uuid_utils import generate_uuid7_bytes


class _FakeAnyValue:
    """Provide the protobuf ``AnyValue`` interface needed by conversion tests.

    Attributes:
        _kind: Protobuf oneof field name reported by :meth:`WhichOneof`.
        string_value: Supplied value when ``kind`` selects the string field, otherwise empty.
        bytes_value: Supplied value when ``kind`` selects the bytes field, otherwise empty.
        int_value: Supplied value when ``kind`` selects the integer field, otherwise zero.
        bool_value: Supplied value when ``kind`` selects the Boolean field, otherwise false.
        double_value: Supplied value when ``kind`` selects the double field, otherwise zero.
    """

    def __init__(self, kind: str, *, value: object) -> None:
        """Initialize one selected fake protobuf value field.

        Parameters:
            kind: Name of the protobuf oneof field to expose as selected.
            value: Value assigned to the selected field.
        """
        self._kind = kind
        self.string_value = value if kind == "string_value" else ""
        self.bytes_value = value if kind == "bytes_value" else b""
        self.int_value = value if kind == "int_value" else 0
        self.bool_value = value if kind == "bool_value" else False
        self.double_value = value if kind == "double_value" else 0.0

    def WhichOneof(self, name: str) -> str:
        """Return the selected value field using the protobuf-generated API shape.

        Parameters:
            name: Expected protobuf oneof group name, which must be ``value``.

        Returns:
            Field name supplied when the fake value was initialized.
        """
        assert name == "value"
        return self._kind


class _MissingAnyValueWhichOneof:
    """Represent an incompatible value object with no protobuf ``WhichOneof`` method."""


class _CallableHolder:
    """Expose a callable attribute for component callable-resolution tests."""

    @staticmethod
    def callback(value: object) -> None:
        """Accept an arbitrary value through a resolvable callable.

        Parameters:
            value: Unused test value accepted to model a component callback signature.

        Returns:
            ``None`` because the test double performs no component work.
        """
        del value


class _NonCallableHolder:
    """Expose a deliberately non-callable attribute for rejection tests.

    Attributes:
        value: String sentinel that must fail callable validation.
    """

    value = "not callable"


def test_parse_capabilities_logs_unknown_names(caplog: pytest.LogCaptureFixture) -> None:
    """Verify capability parsing retains known flags and reports ignored names.

    Parameters:
        caplog: Pytest fixture used to inspect capability-parser log records.
    """
    caplog.set_level("INFO")

    mask = parse_capabilities(["ReportsStatus", "UnknownCapability"], AgentCapabilities)

    assert mask == int(AgentCapabilities.ReportsStatus)
    assert "unknown capability ignored" in caplog.text
    assert "completed capability parsing" in caplog.text


def test_anyvalue_to_string_handles_missing_whichoneof(caplog: pytest.LogCaptureFixture) -> None:
    """Verify incompatible AnyValue objects return ``None`` with a diagnostic warning.

    Parameters:
        caplog: Pytest fixture used to inspect conversion warning records.
    """
    caplog.set_level("WARNING")

    result = anyvalue_to_string(_MissingAnyValueWhichOneof())

    assert result is None
    assert "missing WhichOneof" in caplog.text


def test_anyvalue_to_string_converts_supported_string_value() -> None:
    """Verify a selected protobuf string field is returned unchanged."""
    assert anyvalue_to_string(_FakeAnyValue("string_value", value="hello")) == "hello"


def test_normalize_component_entry_points_skips_invalid_items(caplog: pytest.LogCaptureFixture) -> None:
    """Verify entry-point normalization retains valid forms and logs skipped items.

    Parameters:
        caplog: Pytest fixture used to inspect entry-point normalization records.
    """
    caplog.set_level("INFO")

    normalized = normalize_component_entry_points([
        " module:callable ",
        123,
        {"enabled": False, "entry_point": "ignored:callback"},
        {"label": "Missing entry"},
        {"entrypoint": "pkg.module:callback", "label": "Module"},
    ])

    assert [item.entry_point for item in normalized] == ["module:callable", "pkg.module:callback"]
    assert "skipping component entry point item because it is not a dict" in caplog.text
    assert "skipping disabled component entry point" in caplog.text
    assert "without entry point keys" in caplog.text


def test_load_json_config_logs_invalid_json(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Verify malformed JSON produces an empty configuration and a diagnostic log.

    Parameters:
        tmp_path: Pytest-provided directory for the malformed configuration file.
        caplog: Pytest fixture used to inspect configuration parsing records.
    """
    caplog.set_level("INFO")
    path = tmp_path / "broken.json"
    path.write_text("{not-json", encoding="utf-8")

    payload = load_json_config(path)

    assert payload == {}
    assert "failed to parse JSON config" in caplog.text


def test_resolve_component_callable_rejects_non_callable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify component resolution rejects an import attribute that is not callable.

    Parameters:
        monkeypatch: Pytest fixture used to replace module importing with a controlled holder.
    """
    monkeypatch.setattr("importlib.import_module", lambda module_name: _NonCallableHolder)

    with pytest.raises(TypeError):
        resolve_component_callable("dummy.module:value")


def test_safe_import_config_module_logs_import_error(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify optional configuration imports fail safely and record the import error.

    Parameters:
        monkeypatch: Pytest fixture used to force the optional import failure.
        caplog: Pytest fixture used to inspect safe-import diagnostic records.
    """
    module_path = (
        Path(__file__).resolve().parents[1]
        / "shared"
        / "src"
        / "shared"
        / "print_config.py"
    )
    spec = importlib.util.spec_from_file_location("shared_print_config_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    caplog.set_level("INFO")

    def _raise_import_error(module_name: str) -> types.ModuleType:
        """Raise the controlled import failure expected by the safe-import test.

        Parameters:
            module_name: Requested module name, unused because every import must fail.

        Raises:
            ImportError: Always, to exercise the optional-import fallback.
        """
        del module_name
        raise ImportError("boom")

    monkeypatch.setattr("importlib.import_module", _raise_import_error)

    imported_module = module._safe_import_config_module("missing.module")

    assert imported_module is None
    assert "failed to import config module" in caplog.text


def test_build_cli_missing_warning_returns_none_when_cli_exists() -> None:
    """Verify no packaging warning is produced when the repository CLI project exists."""
    warning = build_cli_missing_warning(
        component_label="shared check",
        repo_root=Path(__file__).resolve().parents[1],
    )

    assert warning is None


def test_generate_uuid7_bytes_returns_16_bytes() -> None:
    """Verify shared UUIDv7 generation returns the protocol-required 16-byte value."""
    value = generate_uuid7_bytes()

    assert isinstance(value, bytes)
    assert len(value) == 16


def test_load_observability_config_from_payload_applies_all_endpoint_defaults() -> None:
    """Verify the shared OTLP endpoint supplies every signal-specific default."""
    config = load_observability_config_from_payload(
        {
            "otlp-endpoints": {
                "ALL": "http://collector:4317",
            }
        }
    )

    assert config.all_endpoint == "http://collector:4317"
    assert config.resolved_logs_endpoint == "http://collector:4317"
    assert config.resolved_metrics_endpoint == "http://collector:4317"
    assert config.resolved_traces_endpoint == "http://collector:4317"
    assert config.export_interval_seconds == DEFAULT_EXPORT_INTERVAL_SECONDS


def test_load_observability_config_from_payload_preserves_signal_overrides() -> None:
    """Verify signal-specific endpoints and export intervals override shared defaults."""
    config = load_observability_config_from_payload(
        {
            "otlp-endpoints": {
                "ALL": "http://collector:4317",
                "metrics": "http://metrics:4318",
                "export_interval": 45,
            }
        }
    )

    assert config.resolved_logs_endpoint == "http://collector:4317"
    assert config.resolved_metrics_endpoint == "http://metrics:4318"
    assert config.resolved_traces_endpoint == "http://collector:4317"
    assert config.export_interval_seconds == 45
