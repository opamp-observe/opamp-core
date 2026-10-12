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

"""Unit tests for packaged CLI version metadata."""

from __future__ import annotations

from opamp_cli import component_version


def test_component_version_text_reads_packaged_resource() -> None:
    """Packaged metadata should be returned for the CLI version surface."""
    assert component_version.component_version_text() == "0.6.0"


def test_component_version_text_falls_back_for_invalid_json(monkeypatch) -> None:
    """Damaged package metadata should produce a stable non-failing value."""

    class _InvalidVersionResource:
        """Provide invalid JSON through the importlib resource interface."""

        def joinpath(self, _resource_name: str) -> _InvalidVersionResource:
            """Return the same fake resource for the requested child name."""
            return self

        def read_text(self, *, encoding: str) -> str:
            """Return malformed JSON while accepting the resource encoding parameter."""
            assert encoding == "utf-8"
            return "not-json"

    monkeypatch.setattr(
        component_version.resources,
        "files",
        lambda _package_name: _InvalidVersionResource(),
    )

    assert component_version.component_version_text() == component_version.UNKNOWN_VERSION


def test_component_version_text_falls_back_for_missing_version(monkeypatch) -> None:
    """A valid metadata object without a version should use the stable fallback."""

    class _MissingVersionResource:
        """Provide metadata without a version through the resource interface."""

        def joinpath(self, _resource_name: str) -> _MissingVersionResource:
            """Return the same fake resource for the requested child name."""
            return self

        def read_text(self, *, encoding: str) -> str:
            """Return valid JSON that deliberately omits the version field."""
            assert encoding == "utf-8"
            return '{"component": "cli"}'

    monkeypatch.setattr(
        component_version.resources,
        "files",
        lambda _package_name: _MissingVersionResource(),
    )

    assert component_version.component_version_text() == component_version.UNKNOWN_VERSION


def test_component_version_text_falls_back_for_non_object_json(monkeypatch) -> None:
    """Valid JSON with the wrong top-level type should use the stable fallback."""

    class _ListVersionResource:
        """Provide a JSON list through the importlib resource interface."""

        def joinpath(self, _resource_name: str) -> _ListVersionResource:
            """Return the same fake resource for the requested child name."""
            return self

        def read_text(self, *, encoding: str) -> str:
            """Return valid non-object JSON while checking the requested encoding."""
            assert encoding == "utf-8"
            return "[]"

    monkeypatch.setattr(
        component_version.resources,
        "files",
        lambda _package_name: _ListVersionResource(),
    )

    assert component_version.component_version_text() == component_version.UNKNOWN_VERSION
